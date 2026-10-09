# Describing parallel work as values

Source: Functional Programming in Scala ch. 7 (and the Part 2 introduction). The book works in Scala; language mappings and anything marked (inferred) or (adaptation) are not the book's claims. Use this file when designing a small library or internal API for composing asynchronous or parallel work. For ordinary application code that just uses a pool or async/await, `design-principles.md` and `choosing-a-mechanism.md` are enough.

## Contents
1. The idea
2. Design steps, each tied to the moment it happens in the chapter
3. The laws and what they buy
4. The deadlock the law revealed
5. Generalising a combinator
6. Pitfalls
7. Tests to write
8. Mapping to other languages (adaptation)
9. When not to use this

## 1. The idea

Separate describing a computation from running it. A parallel computation is a pure value (`Par[A]` in the book); an interpreter (`run`) is the only place that touches threads. Benefits claimed: combinators compose without anyone calling a blocking wait in the middle; the policy for threads is chosen by whoever runs the description; the API can be given laws that the implementation must satisfy and that tests can check.

Why not expose the platform primitives directly (book's critique, usable as a checklist for any low-level API):
- A runnable that returns nothing, and thread start/join, give results only through side effects, so they do not compose.
- A thread maps one-to-one to a scarce OS thread; you want as many logical tasks as is natural and map them to physical ones later.
- A blocking `get` on a future blocks the caller, and futures offer no combinators. They are fine as an implementation substrate, not as the user-facing API.

## 2. Design steps

1. **Start from the simplest concrete use case.** Sum a list of integers by splitting in half, summing each half, and adding. Parallelising a sum is probably slower in practice; it is a design probe. Do not begin with the implementation API. Design the ideal API from examples and work backward.
2. **Read the needed types and functions off the example.** From `sum(left) + sum(right)` you need a container for a result, a function to wrap a constant (`unit`) and a way to get the value out. Legislate signatures before representation.
3. **Explore the semantic choice and let a trace expose the consequence.** If starting work eagerly in `unit` and calling `get` on both halves, then substituting the definitions gives a program with the same value but no parallelism: calling `get` early breaks referential transparency and parallelism. So return the container and combine without waiting: `map2(pa, pb)(f)`. Delay the one blocking call to the very end.
4. **Notice when one combinator conflates two concerns; split them.** `map2` combined two results and also had to decide whether to run asynchronously. Introduce `fork(a)`: "run this in a separate logical thread". Now `map2` can be strict, no combinator carries a global parallelism policy, and a lazy unit is derived: `lazyUnit(a) = fork(unit(a))`. First example of derived versus primitive.
5. **Decide meaning by asking what information the implementation needs.** If `fork` started threads it would need a thread pool, which would have to be globally accessible. If `fork` only marks and `run` does the spawning, it needs nothing and the description stays pure. Choose: `run` is responsible. Rule from the notes: when unsure about a meaning, continue designing; the trade-offs may become clear later.
6. **Write the API sketch with informal meanings, then pick a representation.** The book's provisional representation: a function from an executor to a future. A description is a function awaiting its interpreter's resource. Revise if a needed capability is missing.
7. **Implement the first cut and record its weaknesses.** `fork` blocked a pool thread waiting for the inner task (found harmful in step 9). `map2` ignored timeouts. The API stays pure even though the future inside is impure; effects are visible only when `run` is called.
8. **Explore what is expressible from the existing primitives before adding new ones.** `map` from `map2` and a constant (so `map2` is strictly more powerful); `asyncF(f)` from `lazyUnit`; `sequence` from `map2` by folding; `parMap(ps)(f) = fork(sequence(ps.map(asyncF(f))))`, where the outer `fork` makes `parMap` return at once. Reasons to keep `parMap` derived: tricky logic such as timeouts and races lives in the primitives once. Reasons to add a primitive anyway: efficiency from knowing the representation.
9. **State laws, derive consequences, try to break them** (sections 3 and 4).
10. **Change the representation when a law demands it.** The blocking future was the root cause; the replacement is a non-blocking future with a callback (continuation), with `run` as the only blocking operation. Mutable variables, latches and an actor inside the implementation are acceptable because nothing outside can observe them.
11. **Generalise combinators** (section 5). Keep the primitive set minimal; promote a derived function only for measured reasons.

## 3. The laws and what they buy

Define equality first: two descriptions are equal if, for any valid executor, they produce the same value. Equality on effectful descriptions is defined through an interpreter, not by comparing closures.

| Law | Statement | What it buys |
|---|---|---|
| Map identity | `map(y)(id) == y` | `map` only applies the function: it cannot special-case values, inspect types, or fail before applying `f`. From it a free theorem gives `map(unit(x))(f) == unit(f(x))` |
| Map fusion | `map(map(y)(g))(f) == map(y)(f after g)` | Two maps can become one, saving a second computation; follows from identity by parametricity |
| Forking | `fork(x) == x` for all `x` and all executors | `fork` is purely a scheduling annotation; add or remove it without changing meaning; general combinators like `parMap` are sound |

How to choose laws: (a) reason from the conceptual model, (b) invent plausible laws and see if they can hold, (c) read the implementation and extract what it satisfies. (c) is the weakest, since laws can merely mirror a buggy implementation. Why laws matter: hidden assumptions prevent treating components as black boxes, which makes composition impossible.

When a law fails you can (1) fix the implementation or (2) refine the law to state the condition, for example require an unbounded pool. Even (2) is valuable because it documents an assumption that was implicit.

## 4. The deadlock the law revealed

Putting on the debugger hat to break `fork(x) == x`: with a fixed pool of one thread, the outer task occupies the only thread and waits for an inner task that can never start. The notes state that any fixed-size pool can be made to deadlock this way. The deadlock was predicted from the law, not found by a failing use case. A naive fix, making `fork` just call its argument, stops the deadlock but no longer forks; it survives as a different combinator, `delay`.

The real fix is a representation change: never call a blocking wait inside a task. With callbacks, `fork` and `map2` only schedule continuations. The book's check: `parMap` over 100,000 elements on a two-thread pool runs with no deadlock.

Gap the book leaves: the callback version swallows exceptions (a latch is never released). In any language, make errors propagate to the caller of `run` and make the continuation always fire.

## 5. Generalising a combinator

The book's chain from a specific to a general operation:
1. `choice(cond)(t, f)` runs the condition, then one of two options.
2. Ask what is arbitrary. Boolean and two options are arbitrary: `choiceN(n)(list)`.
3. The list is arbitrary: `choiceMap(key)(map)`. The container is only used as a function from key to description.
4. Generalise to the function: `chooser(pa)(f: A => Par[B])`. Implement the earlier ones with it.
5. Look critically: the second computation need not exist before the first result is known. That is `flatMap`. Rename after generalising.
6. Decompose: `flatMap` is `map` then `join` (`Par[Par[A]]` to `Par[A]`). Each defines the other.

Use: when you have several near-duplicate combinators, ask for each argument "what is arbitrary here?", replace containers by functions, compare with a known shape, then rename. A `choice`-like operation cannot be built from `map`, `map2` and `unit` alone; the dependency between computations is what `flatMap` adds, and independent combination (`map2`) means something different from sequential dependency.

## 6. Pitfalls

- Calling `run`/`get`/`await` inside a combinator breaks composition and can deadlock a bounded pool. Only the outermost `run` should block.
- Blocking in a pooled task that waits for another pooled task deadlocks fixed-size pools.
- Building a strict description of the whole tree can use more memory than the input; keep descriptions lightweight through `fork` and laziness.
- A law that merely mirrors the implementation proves nothing.
- Timeouts: a combined future must subtract the time the first one used from the budget of the second (book exercise, left open).
- Exceptions swallowed in callback style.
- Representation choice: an opaque function representation is easy but cannot be analysed or optimised; a data representation can be rewritten (for example to fuse maps), at the cost of an interpreter (the book's footnote).

## 7. Tests to write

(Some inferred.) Check the laws with a property-based tool or a loop over values, each under an executor of size 1, size 2 and a larger size, with a timeout:
- `map(y)(id) == y` and `map(unit(x))(f) == unit(f(x))`;
- `fork(x) == x` under a pool of one thread;
- fusion on a few functions;
- `parMap(xs)(f)` equals the sequential `xs.map(f)` result-wise, and `sequence` preserves order;
- a deliberately throwing `f` surfaces to the caller;
- 100,000 forks on a two-thread pool finish and the thread count stays bounded.

## 8. Mapping to other languages (adaptation)

The technique needs first-class functions, generics for signatures like `map2`, and a way to defer evaluation.
- TypeScript: a `Promise` is eager, so a description is a thunk `() => Promise<A>` or a task/effect type; `Promise.all` is `sequence`/`parMap`.
- Python: coroutines are lazy until awaited; `asyncio.gather` is `sequence`; use `asyncio.Semaphore` to bound.
- Rust: futures are lazy until polled; `join!` is `map2`; the executor is the interpreter.
- Java: `CompletableFuture` is eager; wrap in a `Supplier<CompletableFuture<A>>` for descriptions.
- Kotlin: suspend lambdas are descriptions; `async` inside a scope starts work.
- Go: functions returning channels; `errgroup` for join and error propagation.

Where the host type is eager (promises, `CompletableFuture`), "unit is not running yet" and "`map2` secretly starts nothing" cannot hold unless wrapped; then replace the forking law by documenting what starts when.

## 9. When not to use this

If the code just needs to fetch three URLs concurrently, use the language's gather or task group and stop. The describe-then-run design pays when you are building a reusable combinator layer, need the same description run under different pools or test interpreters, or need laws to hold. It costs an interpreter, a representation to maintain, and some obscurity for readers unfamiliar with the style.
