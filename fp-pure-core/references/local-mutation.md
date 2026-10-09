# Local mutation behind a pure interface

When and how a pure function may mutate data internally, and how to check that the mutation
cannot be seen. Citations are to Functional Programming in Scala, 1st ed. ("FPiS"), ch. 14 unless
stated. (inferred) marks generalisations made in the study notes; (adaptation) marks material
added for other languages.

## The rule

The definitions of referential transparency and purity say nothing against mutating local state.
A mutation that happens inside a function is not a side effect if nothing outside the function
refers to the mutated object. The book's example is an in-place quicksort: copy the input list
into an array, sort the array with loops, swaps and reassigned variables, copy the array back to
an immutable list. Each helper inside (swap, partition) would be impure if it stood alone. The
function as a whole is pure, because no caller holds a reference to the array.

The book's position is plain: data created locally can always be mutated safely, any function may
use side-effecting components internally while presenting a pure interface, and there is no shame
in doing so. The contrast case: a sort that mutates the list it is given, as many mutable
collection APIs do, has an effect every caller can observe.

Two qualifications:

- Prefer pure components where they serve, because they are easier to get right and compose
  better (FPiS ch. 14).
- The foreword of the book notes that an imperative implementation behind a functional interface
  is legitimate but often overused (FPiS front matter).

## Use when, do not use when

| Use local mutation when | Do not, or take extra care, when |
|---|---|
| An algorithm is naturally in-place: sorting, partitioning, dynamic-programming tables, graph traversals with visited sets | The immutable version is as fast and as clear |
| Building a large collection or string incrementally | The structure must be shared with the caller while still being filled |
| A buffer is reused within one call for speed | A view of the buffer would be returned or retained |
| The language lacks guaranteed tail calls and a loop with local variables is the idiomatic form (FPiS ch. 2, inferred matrix) | The mutable structure would be captured by something that outlives the call |
| A hot path where copying state per step is measurably costly (FPiS ch. 6 footnote) | Several threads would touch the "local" structure |

## Procedure

Language independent (FPiS ch. 14, as distilled in the notes):

1. Allocate the mutable structure inside the function, or copy the input into it. Never mutate an
   argument.
2. Mutate only that structure.
3. Never store it in a field or global, return it, capture it in a closure that escapes, or pass
   it to a callback whose behaviour you do not control.
4. Convert it to an immutable value (freeze, copy, build the immutable collection) before
   returning.

Adaptation for languages where the returned collection type is mutable anyway (Python lists, Go
slices, JavaScript arrays): step 4 becomes "hand over sole ownership". Return the structure and
keep no reference to it. The caller's later mutation of its own result is the caller's business;
what must not happen is the function, or anything it created, retaining access.

Sketch in TypeScript:

```ts
function sortedCopy(xs: readonly number[]): readonly number[] {
  const a = xs.slice();          // 1. copy the input
  a.sort((p, q) => p - q);       // 2. mutate only the copy
  return a;                      // 4. sole ownership passes to the caller; nothing retained
}
```

Sketch in Python of a table-filling algorithm:

```python
def lcs_length(a: str, b: str) -> int:
    row = [0] * (len(b) + 1)                 # created here, never escapes
    for x in a:
        prev = 0
        for j, y in enumerate(b, 1):
            cur = row[j]
            row[j] = prev + 1 if x == y else max(row[j], row[j - 1])
            prev = cur
    return row[-1]                           # an immutable int leaves
```

## Escape analysis: how mutable data gets out

Check each route. Any "yes" means the mutation is observable.

| Route | Example | Remedy |
|---|---|---|
| The argument is mutated | Sorting the caller's list in place | Copy first |
| Stored in a field, module variable or cache | Keeping the working buffer on `self` for reuse | Keep it local, or accept that the object is stateful and say so |
| Returned while a reference is retained | Returning an internal list and also keeping it | Return a copy, or drop the internal reference |
| Returned as a view | A read-only wrapper, slice or sub-list that aliases the buffer | Copy; a read-only view is not a copy |
| Captured by an escaping closure | A returned callback, iterator, generator or lazy sequence that reads the local structure later | Materialise before returning, or copy what the closure needs |
| Passed to an unknown callback | Calling a user-supplied function with the mutable structure | Pass a copy or an immutable value |
| Shared across threads or tasks | Spawning work that writes to the "local" array without exclusive access | It is no longer local; use the concurrency guidance in `craft-concurrency` (inferred) |

The book's sidebar example of the view route: a file library that reuses one byte array as its
read buffer and returns a read-only sequence backed by it. A caller that keeps the sequence sees
its contents change on the next read. The view was read-only and still leaked the mutation.

## Enforcing it with the type system

Loose reasoning is usually enough. The book presents compiler enforcement as another technique
available, with efficiency and notation costs, not something to use every time.

**The two invariants to enforce** (FPiS ch. 14):

1. If I hold a reference to a mutable object, nothing else can observe my mutating it.
2. A mutable object can never be observed outside the scope in which it was created.

**The scoped-state technique.** The book builds a type for local-effect computations with the
same structure as a state action, with these features:

- The state type parameter is never used as data. It is a token that tags the computation and
  every mutable reference or array created within it.
- Mutable cells and arrays can be created, read and written only through operations that return
  actions carrying the same tag. A freeze operation turns a mutable array into an immutable
  list.
- Only actions that are polymorphic in the tag can be run. Because the action must work for every
  possible tag, its result type cannot mention the tag, so a mutable reference cannot be returned
  out of the run. Holding a reference therefore proves you are inside the action that created
  it, which makes mutation safe.
- A different type from the external-effects type is used on purpose: a function returning "an
  external effect producing a list" would claim something false about a local sort. Effects that
  are safe to run locally are distinguished from external ones.

This relies on rank-2 polymorphism (a function that requires its argument to be polymorphic). The
book notes a loophole in its host language through wildcard types that lets a reference leak, and
that a leaked reference still cannot be used, so safety holds.

**What other languages offer** (inferred):

| Mechanism | Languages | Strength |
|---|---|---|
| Ownership and exclusive borrowing | Rust | Gives both invariants natively: a mutable borrow is exclusive and a value moved out leaves no alias |
| The same scoped-state type | Haskell | The original form of this technique |
| Module or package privacy plus convention | Java, Kotlin, Go, C#, Swift | Limits who can reach the structure; does not prevent a method from leaking it |
| Read-only types | TypeScript `readonly` and `ReadonlyArray` | Compile-time only; the underlying array can still be mutated by a holder of the mutable reference |
| Unmodifiable wrappers | Java `Collections.unmodifiableList` | A view, not a copy: the hazard in the sidebar above |
| Immutable copies | Java `List.copyOf`, Python `tuple(...)`, frozen dataclasses | Real separation at the cost of a copy |
| Value types | Swift structs and arrays (adaptation) | Copy semantics make aliasing less likely |

Decision rule from the notes: use a scoped-state type only where the language supports it; in
other languages rely on ownership, privacy, or convention plus tests. Do not pay the notation
cost for small helpers.

## Caches and memoisation

A cache inside a function that is otherwise pure is acceptable only if it is not observable: the
function returns the same results with or without it, and it is safe when called concurrently
(inferred, following from contextual purity). A cache that can return stale data, or that changes
results depending on call order, is an observable effect and belongs with tracked effects (see
`purity-and-substitution.md`).

## Warning signs

- A function described as pure mutates its argument, a field or a global.
- A returned view, iterator or slice aliases an internal mutable buffer.
- A closure that captures a mutable local is stored or returned.
- The "local" structure is shared across threads without synchronisation (inferred).
- A buffer is reused across calls "for performance" and is reachable from two calls at once.

## Verify

Tests (the first three are from the notes, inferred):

1. **Input unchanged**: deep-copy the argument, call the function, assert the argument equals the
   copy. As a property test over random inputs where a library is available.
2. **Repeatable**: two calls with equal input give equal results.
3. **Matches a reference**: the result equals a simple, obviously correct implementation on
   random inputs (for the sort, the standard library's sort).
4. **Concurrent calls**: several calls on shared inputs from different threads or tasks give the
   same results as sequential calls.
5. **No retained alias** (adaptation): mutate the returned value in the test, call the function
   again with the same input, and assert the second result is unaffected.

Review questions with observable answers:

- Where is the mutable structure created? Answer with a line number inside the function.
- List every place a reference to it is passed, stored or captured. Each must end before the
  function returns, or be a copy.
- What is the type of the returned value, and is it a copy, a transfer of sole ownership, or a
  view? A view is a finding.

Evidence for the user: the test names above and their results, and one sentence naming where the
mutable structure is created and how it is prevented from escaping.
