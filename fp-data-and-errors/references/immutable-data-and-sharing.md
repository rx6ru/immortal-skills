# Immutable data and structural sharing

Source: FPiS ch. 3 (3.1, 3.3 and the warning signs). Items marked (adaptation) or (inferred in notes) are not the book's own claims.

## Contents

1. The idea
2. What sharing costs and saves
3. Operation costs on a singly linked list
4. Choosing a structure
5. When you cannot have persistent collections
6. Local mutation
7. Warning signs
8. Verify

## 1. The idea

A functional data structure is operated on only by pure functions, so it is immutable. Operations that look like add or remove return new values and leave the originals valid. Prepending to a list does not copy the list: the new value points at the old one (data sharing). A structure that never changes under existing references is called persistent.

Consequences the book draws:

- No defensive copying. A value can be handed to any component, and nobody can change it under another holder.
- Safe for loosely coupled components and for concurrent readers. (The concurrency point is a reasonable reading of "safe to share"; the notes only state it for loose coupling.)
- Cheap "versions": undo history, snapshots, comparing before and after (inferred in notes).

The book's footnote claims that, in the large, FP can reach greater efficiency than side-effect approaches because of the sharing of data and computation, and that defensive copying of mutable data is the cost avoided. This is an assertion without benchmarks in the notes. Use it as a reason to prefer immutability for shared data, not as a performance promise.

## 2. What sharing costs and saves

Sharing is only free for the operations the structure is built for. Cost depends on which operations you call, so choose the structure from the operations (section 4). The book's principle: writing purely functional structures that support different operations efficiently is all about clever use of sharing.

## 3. Operation costs on a singly linked list

| Operation | Cost | Why |
|---|---|---|
| prepend (cons), `tail`, `setHead` | O(1) | reuse the rest |
| `drop(n)` | O(n) | walk n cells |
| `dropWhile(p)` | proportional to elements dropped | |
| `append(a1, a2)` | O(length of a1) | copies a1, shares a2 completely; an array would copy both |
| `init` (all but last) | O(n) | cannot be avoided; every cell before the last must be rebuilt because replacing a tail forces copying all predecessors |

Practical reading: a loop that repeatedly appends to the end or removes the last element of a linked list is quadratic. Use a different structure.

## 4. Choosing a structure

| You need | Choose |
|---|---|
| Push/pop at one end, traverse in order | Singly linked list (persistent) |
| Random access, update, head/tail/init and append at both ends | A persistent tree-based vector (the book names Scala's `Vector` with near-constant-time ops for these) |
| Build once then read many times | Build with a local mutable builder and freeze (adaptation, consistent with the book's endorsement of invisible local mutation) |
| In-place random updates inside one algorithm and the array never escapes | Local mutable array behind a pure function |

Persistent collection libraries in other ecosystems (named in the notes, as examples to check for availability): Clojure's vectors, Immutable.js, the `im` crate in Rust, persistent collections for Scala and Kotlin, Haskell's `Data.Sequence`. Verify what the repository already depends on before adding one.

## 5. When you cannot have persistent collections

Fallback (inferred in notes): copy-on-write with a shallow copy: object or array spread in JS/TS, `copy()` on Kotlin data classes, `Arc` or `im` in Rust. Accept O(n) per update. Flag it in review when it happens inside a loop: that is an accidental O(n^2). In that case build the result with a local mutable builder and return it frozen.

Making the type immutable at the language level helps: `readonly` and `as const` in TypeScript, `frozen=True` dataclasses and tuples in Python, `val` and read-only collection interfaces in Kotlin, records in Java 17+, `let` bindings and non-`mut` references in Rust. (Adaptation; check the exact feature in the language version in use. Read-only views of mutable collections do not stop the owner from mutating.)

## 6. Local mutation

The book endorses mutation nobody outside the function can see (it accepts a local `while` loop with local variables as a stack-safe alternative to tail recursion, FPiS 1.1 as cited in ch. 2 notes). The rule: mutate only variables that are created inside the function and do not escape. Anything returned or stored must be treated as immutable from then on. Full treatment is in `fp-pure-core`.

## 7. Warning signs

- Defensive copies sprinkled around mutable structures: sign that immutability and sharing would simplify.
- `init`, remove-last or append-to-end on linked lists in a loop: O(n^2).
- Functions that mutate an argument and also return it: callers cannot tell whether the original is still valid.
- A "modifying" method on a shared value without a corresponding new value in the signature.
- Immutable wrappers that expose mutable internals (a frozen object holding a mutable array).

## 8. Verify

- Persistence test: take a value, call each "modifying" function, assert the original compares equal to a saved copy (deep equality, or compare serialised form).
- Alias test (adaptation): hold two references to the same input, run the operation through one, assert the other is unchanged.
- Performance sanity: run the update-in-a-loop path with n = 1e5 and check growth is not quadratic (time n and 2n; the second should be about double, not four times).
- Stack safety on deep structures: build a list or tree of 1e5 to 1e6 elements and run the main operations and the string conversion (see `folds-and-recursion.md`).
