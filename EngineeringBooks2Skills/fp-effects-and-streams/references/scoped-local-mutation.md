# Scoped local mutation and contextual purity

Contents: 1 The claim; 2 Procedure; 3 Compiler enforcement and its cost; 4 Which effects to track; 5 Decision rules; 6 Warning signs; 7 Verify; 8 Language notes.

Sources: FP in Scala ch. 14 (all). (inferred) marks adaptation. The wider treatment of pure/impure boundaries is in `fp-pure-core`; this file concerns mutation that stays inside a function and the choice of what to track.

## 1. The claim

A function is pure if calling it is referentially transparent for transparent arguments. Nothing in that definition forbids mutating local state. The book's example is an in-place quicksort: convert a list to an array, mutate the array in loops with swaps, convert back. No code outside holds a reference to the array, so no caller can observe the mutation; the whole function is pure even though each inner helper would be impure alone. Had the sort mutated its input list, every caller could observe it.

Statement to keep: a mutation inside a function is not a side effect if nothing outside refers to the mutated object. You can always mutate data you created locally, and any function may use side-effecting parts internally behind a pure interface. Prefer pure components anyway where they are as easy, because they are easier to get right and compose better.

## 2. Procedure

1. Allocate or copy the mutable structure inside the function. Never mutate arguments.
2. Mutate only that structure.
3. Do not store it in a field or global, return it, capture it in a closure that escapes, or hand it to a callback you do not control.
4. Convert to an immutable value (freeze, copy, `toList`, `List.copyOf`, `tuple(...)`, `collect`) before returning.

```ts
function sorted(xs: readonly number[]): number[] {
  const a = xs.slice();                 // 1. local copy
  a.sort((p, q) => p - q);              // 2. mutate only the copy
  return a;                             // 3/4. nothing else holds `a`; return it as the result
}
```

Builder idioms that follow the same rule: `StringBuilder` then `toString`, `list.append` in a loop then return, `Vec` built then returned (moved), Kotlin `buildList`, Go slice copied before return.

## 3. Compiler enforcement and its cost

The book shows how to make the compiler stop leaks, and says to treat it as another technique, not something to use every time local mutation appears (efficiency and notation cost).

Two invariants wanted: (1) holding a reference to a mutable object means nothing else can observe my mutating it; (2) a mutable object can never be observed outside the scope where it was created.

The mechanism (ST): an action type that carries a phantom tag S granting authority to mutate data tagged with S; references and arrays are created only by actions of this type; the runner accepts only actions polymorphic in S ("for every S"). Because the result type is fixed outside while S is bound inside, a result mentioning S (such as a reference tagged S) cannot typecheck, so it cannot escape. If you hold a reference you are inside the action that created it. Minimal primitives: a mutable reference (read, write), a mutable array (size, read, write, freeze, from-list), and the book asks the reader to design the same minimal set for a hash map.

Sidebar scenario for invariant 2: a file library reuses one buffer array and returns a read-only view backed by it. A caller who retains the view sees the contents change on the next read. Scoping the view prevents retention.

When the language lacks this (rank-2 polymorphism): use ownership (Rust's exclusive `&mut` and moves give both invariants natively), module/package privacy, or convention plus tests. Do not pay the notation cost for small helpers.

Why not just an IO type: `IO<List>` would claim an external effect. We want to distinguish effects safe to run (local mutation) from external ones.

## 4. Which effects to track (contextual purity)

Book 14.3: allocating an object is technically an effect (visible via reference equality), yet most programs cannot observe it. Generalised definition: an expression is referentially transparent with regard to a program if replacing each occurrence by its result does not change that program's meaning. An effect is non-observable by a program if it does not affect that. "Meaning" depends on context: whether stdout, identity, timing or memory count.

What counts as a side effect is a choice. Policy: track the effects that program correctness depends on. A program about reading and writing files: track file I/O in types. A program relying on reference equality: know it statically. A debug message in a function that otherwise computes a number: if stdout is irrelevant to correctness, tracking it is wasted effort; if the program is a utility whose output matters, track it. Memory allocation could be tracked, but with automatic memory management the cost outweighs the benefit.

Practical consequences (inferred from the book): caching, memoisation, logging and metrics can be added to pure code without changing its meaning for callers whose context ignores them. Decide which observations count (timing, logs, identity) and write it down.

## 5. Decision rules

1. Need in-place mutation for performance or algorithmic reasons (sorting, dynamic programming tables, buffers, large collection building, graph algorithms)? Use it inside a function whose inputs are copied and whose output is frozen. Keep the public interface pure.
2. Does the mutable object get shared with callers, stored in a field, captured by a returned closure/iterator/lazy sequence, or handed to a callback you do not control? Then it escapes: copy at the boundary, do not use local mutation, or use a scoped/ownership mechanism.
3. Want the compiler to enforce it? Only where the language gives you the means (Rust ownership; Haskell-style ST). Elsewhere rely on defensive copies, immutable return types, and review.
4. Which effects belong in types? Those correctness depends on for the callers' notion of meaning: file writes, DB, network, clocks if logic depends on time. Not debug logging or allocation.

## 6. Warning signs

- A "pure" function that mutates its argument, a field or a global: observable, not local.
- Returning a view, iterator or slice that aliases an internal mutable buffer.
- Closures capturing the mutable local and escaping (stored callbacks, returned generators, lazy sequences).
- Unsynchronised sharing of the "local" structure across threads: it is no longer local (inferred).
- Memoisation or caches inside "pure" functions are fine only if the cache is not observable: same results, thread-safe (inferred, follows from contextual purity).

## 7. Verify

- Caller cannot detect the mutation: property test that `f(xs)` leaves `xs` unchanged (compare with a deep copy taken before) and returns the same result on repeated calls.
- Result equals a simple reference implementation (for a sort, the library sort) for random inputs, including empty and singleton.
- Concurrent calls with shared inputs give consistent results (no shared mutable state).
- Escape review: search the function for the mutable local's name and confirm it appears only in assignments, mutations and the final copy/freeze; it is never passed to unknown code, stored, or returned as is. For a returned container, confirm it is a copy, not a view (`Collections.unmodifiableList` is a view, not a copy; `readonly`/`ReadonlyArray` in TypeScript is compile-time only).
- Where views of internal buffers are returned for speed, a test that retains the first result, calls again, and checks the first result is unchanged.

## 8. Language notes (from the book's cross-language note, inferred)

Local mutation behind a pure interface is idiomatic everywhere. Compiler help exists in Rust (ownership, `&mut` exclusivity, moving a `Vec` out) and Haskell (`runST`). Java, Kotlin, TypeScript, Python and Go lack it; use defensive copies, immutable return types, frozen dataclasses (`@dataclass(frozen=True)`; shallow only), and code review for escape.

Related: `fp-pure-core`, `resource-safety.md` (buffer reuse), `testing-effectful-code.md`.
