# Language mappings

Contents: 1 Capability checklist; 2 Idiom map by topic; 3 Per-language notes (TypeScript, Python, Rust, Kotlin, Java, Go, Swift, C#); 4 Degradations; 5 When the functional form costs more than it gives.

Sources: the cross-language notes in FP in Scala ch. 13, 14, 15 and ch. 7 (all marked inferred in the notes), extended with adaptation. These mappings are the skill's adaptation, not claims from the book; check library names and versions against the project before using them.

## 1. Capability checklist

Before choosing a form, check what the host provides.

| Capability | Needed for | If missing |
|---|---|---|
| First-class functions, closures | Effect thunks, interpreters, combinators | Use interface objects |
| Generics | `map2`/`flatMap` signatures | Use erased/any types plus tests |
| Sum types / tagged unions / enums with data | Free structure, Process states, trampoline nodes | Class hierarchy with a visitor, or tag field plus switch |
| Higher-kinded types | Generic `Free[F, _]`, monad-generic combinators | Write per-type versions; use interfaces (ports) instead of a generic monad |
| Guaranteed tail calls | Recursion without a stack | Loops or trampolines |
| Lazy evaluation | Delayed description | Thunks (`() => A`) |
| Deterministic destruction / `using` | Resource safety | try/finally in the source |

## 2. Idiom map by topic

| Idea | TypeScript | Python | Rust | Kotlin | Java | Go |
|---|---|---|---|---|---|---|
| Description of an effect | `() => Promise<A>` thunk, or an Effect-style library type | zero-arg callable; coroutine not yet awaited | `impl Future` (lazy until polled); closures | `suspend` function / lambda; Arrow-style effect types | `Supplier<A>`; `Supplier<CompletableFuture<A>>` | `func() (A, error)` |
| Run at the edge | `await task()` in `main` | `asyncio.run(main())` | `block_on` / `#[tokio::main]` | `runBlocking`/application entry | `main` calls `.get()` once | `main` |
| Interpreter / port | interface + fake class | `Protocol` + fake class | trait + test impl (generic or `dyn`) | interface + fake | interface + fake | interface + fake struct |
| `map2` / independent combine | `Promise.all` over thunks run once | `asyncio.gather` | `join!` / `try_join!` | `coroutineScope { async ...; await }` | `thenCombine` | `errgroup` |
| `sequence` / `parMap` | `Promise.all(xs.map(...))` | `gather(*...)` | `join_all` | `awaitAll` | `allOf` | `errgroup` + results slice |
| Fork / scheduling marker | microtask hop; `worker_threads` for CPU work | `run_in_executor` | `spawn` / `spawn_blocking` | `launch(Dispatchers...)` | `supplyAsync(executor)` | `go` |
| Trampoline | tagged union + loop | tagged classes + while loop | enum + loop (or growing-stack crates) | `DeepRecursiveFunction`; sealed class + loop | sealed interface + loop | rarely needed (growable stacks) |
| Bracket | try/finally; `using` (explicit resource management, where supported) | `with`, `contextlib` | `Drop` (RAII) | `use {}` | try-with-resources | `defer` |
| Stream pipeline | async generators; `stream.pipeline()` | generators + `with` | iterator adapters | `Flow`, `Sequence` | `Stream` (in try-with-resources) | channels + `context` |
| Cancellation | `AbortSignal` | task cancel; `GeneratorExit` on close | drop the future/iterator | structured concurrency cancel | interrupt / `CompletableFuture.cancel` | `context.Context` |
| Frozen result | `readonly`, `Object.freeze` | tuple, frozen dataclass | move the `Vec` out | `toList()`, `buildList` | `List.copyOf` | copy the slice |

## 3. Per-language notes

TypeScript
- `Promise` is eager and unlike an IO value: it already runs. Keep descriptions as thunks or use an effect library (Effect-style or fp-ts-style `Task`). Do not store a `Promise` where you mean "a program to run later".
- Discriminated unions model instructions and trampoline nodes. GADT-style typed answers need casts in the interpreter; accept that or use an interface with one method per operation (tagless style).
- Async generators with `try/finally` give source-owned cleanup; `break` in `for await` triggers the generator's `return()`, which runs the finally.
- Event-loop caveat: a blocking synchronous call inside a task starves other tasks, which is the single-thread analogue of the bounded-pool deadlock.

Python
- Coroutine objects are lazy until awaited; plain functions that call I/O are eager. A callable `() -> A` is the simplest description.
- Recursion limit (default around a thousand frames) makes stack safety a daily concern: use loops, generators, or an explicit work stack. A trampoline is easy with a small class hierarchy.
- Generators plus `with`/`try/finally` provide the source. `generator.close()` is the Kill: it raises at the `yield`, so `finally` runs. That finally closes only that generator's own resources: a transformer wrapping another generator must call `close()` on its input in its own `finally` (`stream-pipelines.md` section 3). Beware generators returned from inside a `with` block.
- `asyncio.gather` and `TaskGroup` for fan-out; never call a blocking function inside a coroutine.

Rust
- Futures are lazy descriptions already; `async fn` returns one. Ownership gives scoped mutation natively and `Drop` gives resource safety; dropping an iterator drops upstream, so `take(5)` closes the source.
- No higher-kinded types: write ports as traits with generics; avoid trying to port `Free[F, _]`; use enums for instruction sets.
- No guaranteed tail calls: use loops; a trampoline is an enum plus `loop`.
- Hazards: blocking calls inside async tasks starve the executor; cancellation by dropping a future happens at await points, so cleanup that must run belongs in `Drop` or a guard.

Kotlin
- `suspend` functions are lazy lambdas; `async` in a scope is eager. Structured concurrency gives cancellation and scope-bound lifetimes (a form of the "resource lives as long as the scope" rule). `Flow` is cold (a description) until collected; `use {}` brackets resources.
- Sealed classes for instruction sets and trampolines; `DeepRecursiveFunction` for deep recursion.
- Do not catch `CancellationException` and continue.

Java
- `CompletableFuture` is eager; `Supplier` wrappers restore laziness. Fixed thread pools plus `get()` inside tasks reproduce the book's deadlock exactly (a pool of one thread is the test).
- Sealed interfaces and records (recent versions) give sum types; before that use visitor-style hierarchies.
- try-with-resources for brackets; `Stream` from files must be closed.
- `Collections.unmodifiableList` is a view, not a copy; use `List.copyOf` for freezing.

Go
- No generics-heavy combinators needed; functions returning channels, `errgroup`, `context.Context` for cancellation, `defer` for release. Growable stacks mean deep recursion seldom crashes but still uses memory.
- Hazards: goroutines blocked on send after the consumer stopped (leak); forgetting to select on `ctx.Done()`.
- The pure-core/shell split and interface-based fakes apply directly; free structures usually cost more than they give.

Swift
- An `async` function call does nothing until awaited, but `Task { }` and `async let` start immediately (eager); actors isolate mutable state; `defer` and `AsyncStream.onTermination` for cleanup. Value semantics make scoped local mutation natural (copy-on-write) (adaptation).

C#
- `Task` is hot (eager); store `Func<Task<A>>` for description. `using`/`await using` for brackets; `IAsyncEnumerable` with cancellation tokens for pipelines. Records and pattern matching for sum types.

## 4. Degradations

When a feature is missing, keep the principle and weaken the form:

| Missing | Keep | Weaken |
|---|---|---|
| Lazy futures | "Constructing starts nothing" | Wrap in thunk; document what starts when; the law `fork(x) == x` becomes a documented rule |
| Higher-kinded types | One interpreter per target | No generic `runFree`; use a tag switch and a driver loop |
| Sum types | Instruction sets as data | Class hierarchy with a method per instruction; or tag plus switch with exhaustive default that throws |
| Tail calls | Constant stack | Loop with accumulator, or trampoline |
| Pattern matching | Reassociation step in the trampoline | `instanceof`/tag checks in a loop |
| Deterministic destruction | Release in one place | try/finally in sources; lint for unclosed handles |
| Immutable collections | Scoped local mutation, freeze at return | Defensive copies; frozen wrappers; tests that callers cannot detect mutation |

## 5. When the functional form costs more than it gives

Be honest about this at review time.
- Languages with idiomatic exceptions and mutation (Go, Python scripts, much Java and C#): a free-structure interpreter or full effect type adds boilerplate and unfamiliar stack traces. Ports and fakes, plus pure cores and source-owned cleanup, capture most of the value.
- Frameworks that own scheduling (Node event loop, Rust runtimes, Kotlin coroutines): inventing a second scheduler and Par type duplicates what exists. Use framework primitives and apply the laws as review checks.
- Teams unfamiliar with the style: each step up the ladder needs justification and documentation.
- Hot paths: interpretive overhead matters; keep them direct.
- Trampolining costs allocation per step. Use only where deep recursion is real.

Related: `effect-descriptions-and-interpreters.md`, `stack-safety.md`, `parallelism-as-description.md`, `stream-pipelines.md`, `resource-safety.md`.
