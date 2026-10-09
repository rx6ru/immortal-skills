# Folds, recursion and stack safety

Source: FPiS ch. 2 (2.4), ch. 3 (3.4, 3.4.1, 3.4.2), ch. 5 (the laziness part that fixes short-circuiting). Items marked (adaptation) or (inferred in notes) are not the book's own claims.

## Contents

1. Loops as state-passing functions
2. Tail position and what languages guarantee
3. Converting a loop: procedure
4. From duplicated recursion to a fold
5. The two folds compared
6. Library of derived functions
7. Cost of composing passes
8. Stack-safety checklist
9. Verify

## 1. Loops as state-passing functions

The functional loop is a local helper (named `go` or `loop` by convention) whose parameters are the loop state. To iterate, it calls itself with new state. To finish, it returns a value without recursing. A wrapper calls it with the initial state.

```
def f(n):
    def go(n, acc):
        if done(n): return acc
        return go(next(n), step(acc))
    return go(n, init)
```

Examples in the chapter: factorial with `go(n-1, n*acc)`; nth Fibonacci where the state is the previous two values; `findFirst` with a local `loop(n)`; `isSorted` walking adjacent pairs and returning at the first pair out of order.

The book calls hand-written `while` loops rarely necessary and bad form because they hinder compositional style. That is the book's taste; section 2 gives the stack-safety reason to still write loops in some hosts.

## 2. Tail position and what languages guarantee

A call is in tail position when the caller does nothing with its value except return it. `go(n-1, n*acc)` is tail; `1 + go(...)` is not. Scala compiles self-recursion in tail position into a jump, so no frame is added per iteration. The authors say you rely on this rather than treat it as an optimisation, because without it large inputs overflow the stack. `@annotation.tailrec` makes the build fail if the call is not actually eliminated. Only self-recursion in tail position is eliminated; mutual recursion is not (the book returns to this under trampolining, see `fp-effects-and-streams`).

Language guarantees (inferred in notes; check the version in use):

| Guarantee for self tail calls | Languages |
|---|---|
| Yes, with a keyword or by default | Scala (`@tailrec`), Kotlin (`tailrec`), Haskell, OCaml, Scheme, Erlang/Elixir; Clojure via explicit `recur` |
| No guarantee | Java, Python, Go, Rust, C#; JavaScript in practice (ES6 specifies it, effectively only Safari implements it) |

Where there is no guarantee, write the same state-passing function as a local `while` loop. The variables are local and invisible to callers, which the book accepts. Or use a built-in fold. Never leave deep non-tail recursion over user-sized input; that overflows the stack in every language.

## 3. Converting a loop: procedure

(Generalised procedure from the notes, marked inferred there.)

1. List every variable the loop mutates. They become the parameters of `go`.
2. The loop condition becomes the base case, which returns the accumulator or result.
3. The body's updates become the arguments of the recursive call.
4. The initial values go in the wrapper's call to `go`.
5. In a language without tail-call guarantees, stop here and keep the loop form with local variables, or express it as a fold.
6. Verify with an input large enough to blow an unoptimised stack, and with an equivalence test against the original.

## 4. From duplicated recursion to a fold

The book's central lesson in ch. 3.4. `sum` and `product` over a list have the same shape: they differ only in the value for the empty case (0 vs 1) and the combining operation (+ vs *). Recipe, stated explicitly:

1. Write two or three concrete recursive versions.
2. Mark what differs: the constant for the empty case, and the expression that combines the head with the recursive result.
3. Replace the constant with a parameter `z`. Replace the combining expression, which mentions the head and the recursive result, with a function parameter `f(head, recursiveResult)`. If a subexpression refers to a local variable introduced by the pattern, turn it into a function that takes that variable.
4. Re-express the originals as one-line calls.

Result:

```
foldRight(list, z, f):
    empty        -> z
    cons(x, xs)  -> f(x, foldRight(xs, z, f))
```

Reading: foldRight replaces the constructors. `Cons(1, Cons(2, Nil))` becomes `f(1, f(2, z))`. The result type need not equal the element type. Folding with the constructors themselves (`z = Nil`, `f = Cons`) rebuilds the list, which shows the fold is the structure of the type (exercise 3.8).

Habit to build (FPiS 3.4.1): whenever you write explicit recursion over a list, look for how to generalise it, and check the standard library before hand-rolling. Do not expect to memorise "when to use each" function up front.

Using the technique in any language (notes, inferred):

1. Write the naive recursive version for two or three cases.
2. Align them; find the empty-case value and the head-plus-recursive-result combination.
3. Use the built-in: `reduce`/`fold`/`foldl`/`foldr`/`aggregate`/`inject`/`Iterator::fold`/`Array.prototype.reduce`/`functools.reduce`.
4. Prefer the named specialised function when one exists (`map`, `filter`, `sum`, `any`, `groupBy`). The fold is the derivation; the named function is the API.

Pitfalls from the notes:

- A built-in `reduce` is usually a left fold: stack-safe, accumulating. The danger is a right fold you write as recursion (one frame per element). JavaScript's native `reduceRight` is an engine loop and did not overflow on 5 million elements in Node 22 (reviewer test); the earlier note saying it is not stack-safe did not reproduce. Another way to overflow on big arrays is spreading them into arguments (`Math.max(...xs)`).
- A strict fold cannot short-circuit. Use `any`/`all`/`find` or an early-exit loop.
- If the accumulator type differs from the element type, use the form with a separate initial value. (A `reduce` without an initial value forces them to be the same, and fails on empty input in some languages.)

## 5. The two folds compared

| | foldRight | foldLeft |
|---|---|---|
| Shape | `f(x1, f(x2, ... f(xn, z)))` | `f(...f(f(z, x1), x2)..., xn)` |
| Recursion | structural, replaces constructors | tail-recursive with an accumulator |
| Stack | one frame per element, not stack-safe on long lists | constant stack |
| Order | right-associated | left-associated; building with cons yields reverse order |
| Short-circuit | not with strict arguments (the combining function receives an already computed result, exercise 3.7) | no |
| Equal when | `f` associative with identity `z`: the two folds agree (monoid; ch. 10) | |

Facts from the exercises:

- `reverse` is a foldLeft with `Cons(a, acc)` as the step.
- `length`, `sum`, `product` are foldLeft or foldRight one-liners.
- You can write foldRight with foldLeft (reverse the list first, then foldLeft; or fold into a composed function). That gives a stack-safe foldRight.
- `append(a1, a2) = foldRight(a1, a2, Cons)`.
- `concat` of a list of lists in time linear in the total length: fold right with `append`, so each element is copied once.

Choose: use the left fold when you only need a result and have a long input. Use the right fold when you must preserve structure (rebuilding lists, `map` via fold) or want a non-strict combining function (see `laziness-and-streams.md`).

## 6. Library of derived functions

All derived by generalisation in 3.4.1:

- `map` (A to B, structure preserving), `filter`, `flatMap` (A to list of B, then concatenate; `flatMap([1,2,3], i => [i,i])` gives `[1,1,2,2,3,3]`), `zipWith` (pairwise combine of two lists).
- `filter` can be written with `flatMap` (return a one-element list to keep, empty to drop). Insight: flatMap is a more basic building block (it reappears in ch. 11).
- Named in the text: `take`, `takeWhile`, `forall`, `exists`, `scanLeft`, `scanRight` (the list of partial results).
- Trees: `size`, `maximum`, `depth`, `map`, all instances of the tree fold (see `algebraic-data-types.md`).

## 7. Cost of composing passes

Assembling operations from general blocks can cost extra passes. `map(...).filter(...).map(...)` traverses and allocates an intermediate list per stage, and `exists` via a strict fold cannot stop early. The book's example is `hasSubsequence` (its text examples are contiguous runs, even though the name says subsequence; implement what the signature and examples demand, which is the notes' reading). Concise-and-efficient is hard with strict lists and comes back in chapter 5 with laziness: `tails(sup)` exists-with `startsWith(sub)`, giving the same number of steps as a hand-written nested loop with early exits.

Rules (partly inferred in notes):

- Small data: eager `map`/`filter` chains are fine and simpler.
- Large data, long chains, or early termination: use lazy iterators or generators (Rust iterators, Java `Stream`, Python generators and `itertools`, JS generators, Kotlin `Sequence`, C# LINQ) or fuse the passes manually into one fold or loop. Details in `laziness-and-streams.md`.

## 8. Stack-safety checklist

- Is there a recursive call that is not in tail position over input whose size the caller controls? Rewrite to an accumulator loop or fold.
- Is a hand-written recursive right fold, or a recursive `toString`, used on user-sized data? (Python's default recursion limit is about 1000 frames, so recursion over 100k elements fails there at once.)
- Does the lazy `exists` or `forAll` (see laziness reference) run over a very large stream whose elements all fail the test? The book flags it as not stack-safe for large inputs.
- Does a recursion rely on a tail-call guarantee the host does not give?

## 9. Verify

- Large-input test: 100k to 1M elements through every recursive or fold-based function you added. With `@tailrec` or `tailrec` the compiler checks; elsewhere the large input is the check.
- Equivalence: fold-based version equals a naive reference loop on random lists.
- Fold laws from the notes (inferred): `foldRight(l, Nil, Cons) == l`; `reverse(reverse(l)) == l`; `length(append(a, b)) == length(a) + length(b)`; `map(id) == id`; `map(f compose g) == map(f) compose map(g)`; `flatMap(l, a => [a]) == l`; foldLeft and foldRight agree for associative `f` with identity `z`.
- Evaluation trace: substitute the definition by hand for a 3-element input and check the shape of the computation (`1 + (2 + (3 + 0))` for a right fold). The book uses this technique throughout.
- Mixed: `isSorted` agrees with a naive reference for random arrays and comparators.
