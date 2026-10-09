# Strictness, laziness and streams

Source: FPiS ch. 5 (all sections), plus ch. 3.4.2 for the problem it solves. Items marked (adaptation) or (inferred in notes) are not the book's own claims.

## Contents

1. The problem: one pass per stage
2. Strict versus non-strict
3. Thunks and memoisation
4. Lazy sequences
5. Describing versus evaluating
6. Early exit and lazy right fold
7. Fusion
8. Infinite sequences
9. unfold and corecursion
10. When to use laziness
11. Pitfalls
12. Verify

## 1. The problem: one pass per stage

With strict lists, `list.map(...).filter(...).map(...)` completes one stage before the next starts, making a full pass and a full intermediate list per stage (the book's card-deck analogy: remove odd cards and flip queens in one pass, not two). The goal is to keep the compositional style but get a single pass, no temporary collections, automatically, through non-strictness. The authors stress that the larger payoff is modularity, not just speed.

## 2. Strict versus non-strict

Non-strictness is a property of a function: it may choose not to evaluate some arguments. Strict means it always evaluates all of them (the default in most languages: `square(fail())` fails before `square` runs).

You already use non-strict constructs: `&&`, `||` (second operand only if needed) and `if` (strict in the condition, non-strict in the branches). `if` can be seen as `if2(cond, onTrue, onFalse)` with the branch arguments unevaluated.

Formal note: a function is strict if `f(x)` is bottom (error or non-termination) whenever `x` is.

## 3. Thunks and memoisation

A thunk is an unevaluated expression represented as a zero-argument function. Force it by calling it. Scala's by-name parameter is sugar that wraps the argument in a thunk.

The gotcha the book calls crucial: a by-name argument is re-evaluated at each reference. Passing a side-effecting expression to a function that references it twice runs the side effect twice. Fix with caching: evaluate on first use and cache. Rule: if you reference a lazy parameter more than once, cache it.

Other languages (inferred in notes): a thunk is a zero-arg lambda (`() => expr`, Python `lambda: expr`, Go `func() T`, Rust `impl FnOnce() -> T`). Memoisation is a small `Lazy<T>` wrapper: Kotlin `lazy {}`, Swift `lazy var`, C# `Lazy<T>`, Rust `OnceCell`/`LazyLock`, a JS closure that stores the value. Built-in non-strictness: short-circuit operators, ternary and if, generators (`yield`), iterators in Rust, Java `Stream`, C# LINQ, Python generators. Haskell is lazy by default; most other languages are strict, so laziness must be explicit.

Where thunks pay off in ordinary code (inferred in notes): default values (`getOrElse(default)` takes it lazily), fallbacks (`orElse`), expensive log messages, and any argument that is costly or effectful but only sometimes needed.

## 4. Lazy sequences

A lazy list is like a list but its head and tail are thunks: `Cons(head: () => A, tail: () => Stream<A>)` plus `Empty`. Forcing is explicit. To peek at a stream: `take(n).toList`.

Smart constructors: functions that build a data type while enforcing an invariant or giving a better signature, named by convention as the lowercase of the constructor. `cons(head, tail)` memoises both so a node's thunk runs at most once; otherwise calling `headOption` twice would recompute an expensive head twice. `empty` is typed as the base type for inference. Pitfall: building the raw `Cons` directly bypasses memoisation, so always use the smart constructor.

Basic operations: `toList` (force everything, for inspection), `take(n)`, `drop(n)`, `takeWhile(p)`.

## 5. Describing versus evaluating

The theme of the chapter (and of the book): separate the description of a computation from running it. Earlier instances in the book: first-class functions (code captured, run later), Option (error recorded, handling decided elsewhere), a value standing for a charge in ch. 1. A lazy sequence describes a computation producing a sequence without running it until elements are demanded. You can describe a larger expression than you need and evaluate only part of it.

Transferable principle (the book states the theme; wider examples are inferred): build a value that describes work (query plan, pipeline, task graph, retry policy, batch of charges) and interpret it in one place at the edge.

## 6. Early exit and lazy right fold

- `exists(p)` as `p(head) || tail.exists(p)`: `||` is non-strict, so traversal stops at the first match and the tail is never computed.
- A lazy `foldRight(z, f)` where `f` takes its second argument by name: if `f` ignores it, recursion stops. Then `exists(p) = foldRight(false, (a, b) => p(a) || b)`. With a strict fold you would hand-write a recursive `exists`; laziness makes the code reusable. This also answers the earlier question of why `product` via a strict foldRight cannot stop at 0 (ch. 3, exercise 3.7).
- Derived through it: `forAll` (stop at first failure), `takeWhile`, `headOption`, `map`, `filter`, `append` (non-strict in its argument), `flatMap`.
- Reuse example: `find(p) = filter(p).headOption`. `filter` transforms "the whole stream" lazily, so `find` stops at the first match. You compose small combinators without worrying about doing extra work.

In a strict language use `any`/`all`/`find` with early exit, or a generator-based pipeline; the strict `reduce` cannot stop.

## 7. Fusion

Evaluating `Stream(1,2,3,4).map(+10).filter(isEven).toList` interleaves the stages: produce one mapped element, test it in filter, emit or drop it, then move to the next. Intermediate streams are never fully instantiated, "exactly as if we had interleaved the logic using a special-purpose loop". Streams are first-class loops that can be combined with higher-order functions. Only enough memory for the current element is needed; the garbage collector can reclaim a rejected element immediately, which matters for large elements.

The ch. 3 problem, `hasSubsequence(sup, sub)`, becomes `tails(sup) exists (startsWith sub)` with `tails` produced by unfold. It performs the same number of steps as a hand-written nested loop with early breaks. The book's thesis in one example: compose from simple parts and keep the efficiency of the specialised version.

## 8. Infinite sequences

Because operations are incremental, they work on infinite sequences (`ones = cons(1, ones)`): `take(5)`, `exists(odd)`, `takeWhile(== 1)`, `forAll(!= 1)` all return. But `forAll(== 1)` on `ones` never answers (it shows up as a stack overflow, not an infinite loop). Rule: an expression that inspects only a finite prefix can take infinite input; others diverge. Basic generators: `constant(a)`, `from(n)` (integer overflow wraps after about four billion), `fibs`.

## 9. unfold and corecursion

```
unfold(state, step):
    step(state) returns (element, nextState)  -> emit element, continue from nextState
    step(state) returns nothing               -> end
```

Runnable sketch (Python generators; the assertions passed under `python3 -I`):

```python
from itertools import islice

def unfold(state, step):          # step(state) -> (element, next_state) or None
    while True:
        nxt = step(state)
        if nxt is None:
            return
        elem, state = nxt
        yield elem

fibs = unfold((0, 1), lambda s: (s[0], (s[1], s[0] + s[1])))
assert list(islice(fibs, 8)) == [0, 1, 1, 2, 3, 5, 8, 13]

pulled = []
def source():                     # unbounded, records what was pulled
    n = 0
    while True:
        pulled.append(n); yield n; n += 1

assert next(x * x for x in source() if x > 0 and x % 2 == 0) == 4 and pulled == [0, 1, 2]  # find terminates
pulled.clear()
assert list(islice(source(), 2)) == [0, 1] and pulled == [0, 1]                           # take(2) pulls two
```

`fibs`, `from`, `constant`, `ones` can all be written via `unfold` (the Fibonacci state is the pair of the last two values). `map`, `take`, `takeWhile`, `zipWith` and `zipAll` (continue while either side has elements, with an Option marking exhaustion) can be written with it too. So `unfold` is the general producer.

Corecursion: recursion consumes data and terminates by recursing on smaller input; corecursion produces data and need not terminate as long as it is productive, meaning it can always evaluate more of the output in finite time (also called guarded recursion; productivity is cotermination). `unfold` is productive if `step` terminates.

Memory note from the book: the self-referential definition `ones` shares its cell, so it runs in constant memory, but `unfold`-based versions lose that. Sharing is "extremely delicate and not tracked by the types" and even `xs.map(x => x)` destroys it. Do not rely on it.

`tails` (all suffixes, ending with the empty stream) is `unfold`; `scanRight` generalises it but cannot be done by `unfold` alone, because each element depends on later ones (the notes give a right fold carrying a pair, marked inferred). The result for `Stream(1,2,3).scanRight(0)(+)` is `[6, 5, 3, 0]`, linear in n if intermediate results are reused.

Where unfold shows up (inferred in notes): Fibonacci, pagination, tree walks, retry and backoff schedules, ID generation. In practice this is a generator with explicit state: Rust `std::iter::successors`/`from_fn`, Kotlin `generateSequence`, Python generator functions, C# `yield return`, JS generators. (Library names are an adaptation; check the version in use.)

## 10. When to use laziness

| Need | Technique |
|---|---|
| Chained transforms on large data where only a prefix or first match is needed | Lazy pipeline: stream, generator, iterator adapters |
| The same pipeline on small data | Strict map/filter; simpler |
| Argument expensive or side-effecting and only sometimes needed (defaults, fallbacks, log messages) | Pass a thunk (by-name) |
| Compute once, use many times | Memoise (lazy value, `Lazy<T>`, caching in the smart constructor) |
| Sequence from a state transition (Fibonacci, pagination, tree walks, retry schedule, ids) | `unfold(state, step)` |
| Short-circuit a fold | Give the right fold a lazily evaluated combining argument; in strict languages use `any`/`all`/`find` or an early-exit loop |
| Infinite or unbounded source (event feed, counter) | Stream or generator consumed with `take`, `takeWhile`, `find` |

Judgement (adaptation): in languages with ubiquitous lazy iterators (Rust, Python, Java 8+, C#, Kotlin Sequence, JS iterators) the library has most of this. The skill is to prefer lazy pipelines for multi-stage transforms on big data and to write generators as unfold-like state machines rather than building intermediate lists. Do not introduce a lazy sequence abstraction of your own where the language already has one.

## 11. Pitfalls

- A by-name or thunk argument evaluated repeatedly: duplicated side effects or cost; cache it.
- Side effects or mutation inside thunks: evaluation order becomes hard to predict. Keep lazy computations pure (inferred in notes, consistent with the purity premise).
- Space leaks: holding a reference to the head of a stream while traversing it retains everything evaluated so far, because memoisation keeps nodes alive (inferred in notes).
- Non-termination or stack overflow on infinite input when a terminal operation such as `toList` or an always-true `forAll` is applied. Always bound infinite sequences.
- Lazy `exists` and right folds are not stack-safe for huge streams whose elements all fail the test (book footnotes).
- Raw constructors bypassing the smart constructor (loses memoisation).
- Forgetting that `toList`, `foreach` and `reduce` are where work happens. Errors and costs appear there, not where the pipeline was built. Debugging a lazy pipeline starts at the terminal operation.

## 12. Verify

- Laziness test: feed the pipeline a source with a side-effect counter, or one that throws or diverges after the needed prefix. Assert it returns and the counter equals the expected number of elements consumed. `find` on an infinite source must terminate; `take(2)` must not force the third element.
- Fusion test: count calls to the map function and the filter predicate. For n elements each is called at most once per element, interleaved.
- Memoisation test: a thunk with a counter runs once even when forced twice.
- Equivalence: `stream.map(f).filter(p).toList == list.map(f).filter(p)` on random lists.
- unfold laws (inferred in notes): `unfold` with a state function that stops on a condition matches the equivalent loop; `take(n)` of an infinite generator has length n; the suffix sequence from `tails` equals the list of suffixes.
