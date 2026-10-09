# Parallel and async work as a description

Contents: 1 The idea; 2 Steps of the design with the moment each happens; 3 The API surface; 4 Laws and what each buys; 5 The deadlock and the non-blocking representation; 6 Generalising to flatMap/join; 7 Applying in a codebase (procedures); 8 Pitfalls; 9 Verify; 10 Language notes.

Sources: FP in Scala ch. 7 (all), ch. 13.5 (async interpreters). The design-method view of the same chapter belongs to `fp-api-design-with-laws`; this file is the practical effects view. (inferred) marks adaptation.

## 1. The idea

Separate describing a computation from running it. Parallel work is a pure value `Par<A>` built from a few primitives; one function `run` interprets it against a resource (a thread pool). Nothing happens until `run`. The API is treated as an algebra: types, operations and laws.

Why not use the raw primitives as the API (book critique, usable as a checklist for judging any low-level API):
- A runnable that returns nothing meaningful and thread start/join give results only through side effects, so they cannot be composed generically.
- A thread maps one-to-one onto scarce OS threads. You want as many logical tasks as feels natural and map them to physical workers later.
- A blocking `get` on a future blocks the caller and there are no combinators (no map, no flatMap). Futures are a fine implementation substrate, not a user-facing API.

## 2. Design moments (what to copy from the process)

1. Start from the smallest example: sum a list by splitting in half and summing the halves (a probe for the API, not a recommendation to parallelise sums). Read the needed types and operations off it: a container `Par<A>`, `unit(a)`, and a combine-two function.
2. Notice that calling `get` inside the program is the problem. If `unit` starts work eagerly and you call `get` on the left half before building the right half, there is no parallelism. Worse, substituting a name by its definition changes whether things run in parallel, so referential transparency is lost. Resolution: never wait mid-computation; combine without waiting using `map2(pa, pb, f)`, and call run once at the end.
3. Strict vs lazy arguments: with strict `map2` and left-to-right evaluation, the entire left subtree is built (and possibly started) before the right one exists, which is unfair, and building a strict description of the whole tree can use more memory than the input list.
4. Notice that `map2` is conflating two concerns: combining two independent results, and deciding that something runs on another thread. `map2(unit(1), unit(1))(+)` obviously should not fork. Split them: `fork(par)` marks "evaluate in a separate logical thread" and is the sole scheduling primitive. `map2` can then be strict, and `lazyUnit(a) = fork(unit(a))` is derived.
5. Decide whether `fork` acts at construction or at `run` by asking what information each choice needs. If fork starts threads it needs a globally accessible pool, which kills per-subsystem control and testability. If fork only marks, and `run` spawns, fork needs nothing and `Par` is pure data. Choose that. General rule (book 7.1): if an operation would need a global resource (pool, connection, clock), make it a description and push resource access into the interpreter.
6. Write the API sketch with informal meanings, then pick a representation. Book: `Par<A> = Executor -> Future<A>`; `run(executor, par) = par(executor)`. A Par is a function waiting for its interpreter. The Par API is pure even though the underlying Future is not; the impurity is only reachable through `run`.
7. Before adding a primitive, express it from existing ones by following types (below).

## 3. API surface

Primitives (book): `unit`, `map2`, `fork`, `run`. Derived (all expressible without a new primitive):
- `lazyUnit(a) = fork(unit(a))`
- `asyncF(f) = a => lazyUnit(f(a))`
- `map(pa, f) = map2(pa, unit(()), (a, _) => f(a))`. `map2` is strictly more powerful than `map`: map derives from map2, not the reverse. The aim is the smaller primitive set.
- `sequence(list of Par) -> Par of list`: fold with `map2`.
- `parMap(xs, f) = fork(sequence(xs.map(asyncF(f))))`. The outer `fork` makes `parMap` return immediately even for a huge list: one async task spawns N tasks and collects.
- `parFilter`, parallel maximum over an indexed sequence, parallel word count over a list of strings (generalise as far as you can), `map3/4/5` from `map2`.

Why not make `parMap` a primitive: the book notes it is hard to get right, especially with timeouts. Primitives encapsulate tricky logic once; reusing them avoids duplicating it. Adding a primitive for speed is legitimate, but while exploring you want to learn which operations are truly primitive.

Also noted: `delay(par)` is the naive "fork" that merely defers instantiation of its argument. It does not fork. Keep it as a separate combinator with its own name.

```ts
// Description form in TypeScript: a Task is a thunk, so nothing starts at construction.
type Task<A> = () => Promise<A>;
const unit = <A>(a: A): Task<A> => () => Promise.resolve(a);
const map2 = <A, B, C>(ta: Task<A>, tb: Task<B>, f: (a: A, b: B) => C): Task<C> =>
  () => Promise.all([ta(), tb()]).then(([a, b]) => f(a, b)); // both started when run
const sequence = <A>(ts: Task<A>[]): Task<A[]> => () => Promise.all(ts.map(t => t()));
const parMap = <A, B>(xs: A[], f: (a: A) => B): Task<B[]> =>
  sequence(xs.map(x => () => Promise.resolve().then(() => f(x))));
// run happens once, at the edge:  const result = await parMap(items, g)();
```

Note the JS runtime has no pool to size; the "fork" there is a scheduling hop (microtask/queue), and CPU-bound parallelism needs worker threads. See `language-mappings.md`.

## 4. Laws and what each buys

Define equality first: two Pars are equal if, for any valid executor, running them yields the same value. For effectful descriptions, equality is via an interpreter, not structural equality of closures.

1. Map identity: `map(unit(x), f) == unit(f(x))`, generalised and simplified by substituting identity to `map(y, id) == y`. Guarantees `map` is structure preserving: it cannot throw before applying f, cannot special-case values, cannot inspect the value's type. It is a "free theorem": from `map(y, id) == y` the more complex law follows (and vice versa). Lesson: a law that mentions fewer operations is stronger evidence of what the operation is.
2. Map fusion: `map(map(y, g), f) == map(y, f after g)`. Buys an optimisation (one task instead of two). With Par as an opaque function you cannot pattern-match to apply it; if Par were reified as data, an optimiser could rewrite. Trade-off: opaque function representation is easy to implement and not analysable; data representation is analysable.
3. Law of forking: `fork(x) == x` for all x and all executors. Buys: fork is only a scheduling annotation, so adding or removing it never changes meaning, and general combinators such as `parMap` are sound. The type system cannot tell you where fork is safe, so the law must hold by construction.
4. Why laws matter: hidden assumptions stop you treating components as black boxes, which makes composition impossible.
5. Choosing laws: reason from the conceptual model; invent plausible laws and see whether they can hold; or extract the laws the implementation satisfies. The last is weakest, since it is easy for laws to reflect a buggy implementation.

When a law fails, either fix the implementation or weaken the law and document the precondition (for example "requires an unbounded pool"). The second option still pays: it surfaces implicit assumptions. Prefer fixing when the law is what composability depends on.

Procedure for testing a law (book): take off the implementer hat, put on the debugger hat, try to break it with corner cases and adversarial interpreters (pool of size 1, bounded pool, throwing function, empty input).

## 5. The deadlock and the non-blocking representation

Representation in the first cut: `fork` submits a task that itself calls `a(executor).get()`. The outer task occupies a pool thread while blocking for the inner task, using two threads where one would do. On a fixed pool of size 1 the law `fork(a) == a` deadlocks: the outer task holds the only thread and waits for an inner task that cannot start. Any fixed-size pool can be made to deadlock this way (book Exercise 7.9). The deadlock was predicted from the law, not found by a failing use case. A naive fix, `fork(fa) = es => fa(es)`, avoids the deadlock but does not fork; it is the `delay` combinator.

Root cause: a value cannot be taken out of a blocking future without blocking a thread. The fix is a non-blocking representation where `fork` and `map2` never call a blocking method:
- `Future<A>` has one method: `apply(k: A -> void): void`, a continuation. It is hidden from users so the API stays pure.
- `run` creates a latch, passes a callback that stores the result and releases the latch, awaits it. `run` necessarily blocks (it must return an A), so only call it where you want to wait. The book suggests an API could omit `run` and expose callback registration instead.
- `unit(a)`: apply simply calls `k(a)`.
- `fork(a)`: apply submits a task to the executor that runs `a(es)(k)`. This is where real parallelism begins.
- `map2`: a rendezvous that is race-free (the book uses an actor processing one message at a time) holding whichever result arrived first; when both are present it calls `k(f(a, b))`.

Result: `parMap` over a range of 100,000 elements on a 2-thread pool completes, and the fork law holds for fixed pools. The book's point is not this specific implementation ("not necessarily the best") but that laws exposed a design problem early, possibly before a thread resource leak would have been found in production.

Local side effects (mutable cells, latches) inside the implementation are acceptable because they are unobservable through the API.

Gap in the book (Exercise 7.10): the non-blocking version swallows exceptions because the latch is never released. In any language, make errors travel through the same channel as values and make sure the continuation always fires. First-cut `map2` also ignores timeouts; combined futures must subtract elapsed time from the budget of the second (Exercise 7.3).

## 6. Generalising a combinator

Worked chain (book 7.5): `choice(cond: Par<bool>, t, f)` is easy with blocking. Ask "what is arbitrary?" Booleans and exactly two branches are: generalise to `choiceN(n: Par<int>, list of Par)`. The list is arbitrary too: generalise to a map from keys. The container is only used as a function from key to Par, so take the function: `chooser(pa, choices: A -> Par<B>) -> Par<B>`. Now see that the second computation need not exist before the first result is known: that is `flatMap`. Decompose: `flatMap = map then join`, with `join(Par<Par<A>>)`. Each of `join` and `flatMap` defines the other, so either can be primitive. Rename once generalised.

Consequence worth knowing: `choice` cannot be built from `map`/`map2`/`unit` alone; it needs flatMap. A `map2` made from `flatMap` has a different meaning (sequential dependency) than the independent `map2`. Use `map2`/`zip`-style combinators when computations are independent, because they can run in parallel; use `flatMap` when the second depends on the first.

## 7. Applying in a codebase

Procedure for new fan-out code (language independent, partly adaptation):
1. Write the plain sequential version first.
2. Mark where "something happens concurrently". Invent signatures so the example reads as one expression: a constructor for plain values (`unit`), a combiner (`map2`/`zip`/`all`), a scheduling marker (`fork`), and one interpreter (`run`).
3. Ensure combinators return descriptions and only the interpreter touches the world.
4. For each ambiguous choice, list what resource or information each meaning needs; prefer the one with no global state.
5. Keep scheduling in one primitive. Derive the convenient variants.
6. Write the laws as tests (section 9) before relying on the library.
7. Keep primitives minimal; promote a derived function to a primitive only for measured reasons.

Review rule: `await`/`get`/`join` inside a task that runs on the same bounded pool as the task it waits on is a deadlock candidate. In async/await runtimes it is the equivalent of blocking the event loop or sync-over-async.

## 8. Pitfalls

- Calling `run`/`get`/`await` in the middle of a combinator: breaks composition and referential transparency, can deadlock.
- Strict construction of the whole description tree can cost more memory than the input; use fork or lazy construction to keep descriptions light.
- Eager futures (JS promises, `CompletableFuture`) start work on construction. Wrap them in a thunk to restore "map2 does not secretly start things". Then `fork(x) == x` is replaced by documenting what starts when (book cross-language note, inferred).
- A law that merely mirrors the implementation proves nothing.
- Timeouts and exceptions: design them in from the start (see section 5).
- Equality of descriptions via closures: define through running under the same resource.

## 9. Verify

Write these as tests against your own library (adapt names):
- `map(y, id) == y` and `map(unit(x), f) == unit(f(x))` over several executors/modes.
- `map(map(y, g), f) == map(y, f after g)`.
- `fork(x) == x` with a pool of size 1 (exact book test), then 2, then N. A hang here is the deadlock; use a timeout in the test harness so it fails instead of blocking CI.
- `parMap(xs, f)` equals sequential `map` including order; empty list; single element.
- A throwing `f` makes the run fail with that error rather than hang.
- 100k forks on a 2-thread pool complete; observed thread count stays bounded.
- Timeouts: a short budget on a chain of combined tasks fails within about the budget, not N times it.

## 10. Language notes (inferred, from the book's cross-language note and adaptation)

TypeScript: `Promise` is eager; use `() => Promise<A>` or a Task/Effect type. Kotlin: `Deferred` from `async` is eager; suspend lambdas are descriptions; use structured scopes. Rust: futures are lazy until polled; `join!`/`try_join!` is `map2`; beware blocking calls inside async tasks. Python: coroutines are lazy until awaited; `asyncio.gather` is `sequence`/`parMap`; do not call `run_until_complete` inside a running loop. Java: `CompletableFuture` is eager; wrap in `Supplier<CompletableFuture<A>>`. Go: functions returning channels, `errgroup`; no generic combinators. Details in `language-mappings.md`.

Related: `effect-descriptions-and-interpreters.md` (async interpreter), `testing-effectful-code.md`, `craft-concurrency` (threads, locks, deadlock theory), `fp-api-design-with-laws` (the design method).
