---
name: fp-effects-and-streams
description: Guides writing programs as descriptions of effects run by a swappable interpreter, and processing sequences incrementally with resource safety. Covers effect/IO values, ports-and-adapters vs free-structure interpreters, fake interpreters for tests, trampolining and stack safety, parallel or async work described apart from running it (and non-blocking pitfalls), scoped local mutation, and source-transform-sink stream pipelines with early termination and no lazy I/O. Use when code mixes I/O with logic and is hard to test, a deep recursion or long loop overflows the stack, async code deadlocks or blocks pool threads, a file/socket/DB cursor leaks or is read after close, a function returns a lazy iterator over an open resource, or someone proposes an IO monad, Effect type, free monad or tagless-final. For pure/impure factoring see fp-pure-core.
---

# Effects as values, interpreters, and incremental streams

## Purpose

Use this skill to decide how much structure a program's effects need, and to build exactly that much: from a plain "read, compute, write" split up to an effect type, interpreters, and resource-safe stream pipelines. Its value is in the selection (most code needs only the cheap end of the ladder), in a short list of failure modes that are easy to introduce (blocked pool threads, stack overflow in loops, leaked handles, lazy iterators over closed resources), and in tests that expose them.

The book behind this is Scala; the ideas are language-independent. Examples here use TypeScript, Python, Rust and Kotlin. Where the host language cannot express something, `references/language-mappings.md` says what to do instead.

## Choose what applies

Start at the top of the table and stop at the first row that solves the problem. The rows are ordered from cheapest to most machinery.

| Situation | Use | Read |
|---|---|---|
| Function mixes decisions with printing, DB calls, clocks, HTTP | Extract pure functions, leave a thin shell of I/O calls. Often enough by itself. | `fp-pure-core` (primary); `effect-descriptions-and-interpreters.md` section 1 |
| Need tests without mocks; effects are a small stable set (console, clock, file, store) | Ports and adapters: an interface of operations, a real adapter and a fake adapter, chosen at the entry point | `effect-descriptions-and-interpreters.md` section 3, `testing-effectful-code.md` |
| Need to store, retry, schedule, race or run effects in parallel as ordinary values | An effect type (lazy thunk or the language's Task/IO/Effect) | `effect-descriptions-and-interpreters.md` sections 2, 4 |
| Need to log, serialise, dry-run, record or restrict a program, or run one program under several interpreters | Free-structure: operations as data plus an interpreter (inspection is by tracing a run; listing instructions up front needs independent steps, section 5.2a) | `effect-descriptions-and-interpreters.md` section 5 (has a runnable example) |
| Recursion or monadic loop may run thousands to millions of steps; stack overflow seen or feared | Accumulator loop first; trampoline if the recursion is genuinely non-tail or goes through composed functions | `stack-safety.md` |
| Parallel or async work: sum/map over many items, fan-out, timeouts, deadlock on a bounded pool | Describe the work as values; one scheduling primitive; one place that runs and blocks | `parallelism-as-description.md` |
| Reading/transforming/writing a sequence from file, socket, cursor, queue; large or unbounded data; early exit | Source, transformers, sink as a pipeline with resource handling in the source only | `stream-pipelines.md`, `resource-safety.md` |
| Something opened must be closed on normal end, error and early stop | Bracket/using/defer in one place; cancellation forwarded upstream | `resource-safety.md` |
| In-place mutation wanted for speed (sort, DP table, buffer, builder) | Mutate only a structure created inside the function, freeze before return | `scoped-local-mutation.md` |
| Which effects deserve tracking in types at all | Track what correctness depends on | `scoped-local-mutation.md` section 4 |
| Unsure how an idiom maps to the language in front of you | Mapping tables and degradations | `language-mappings.md` |

This skill does not apply, or applies lightly, when:
- The code is a one-off script, a migration run once, or glue under about a hundred lines. Plain imperative code with the I/O at the edges is the right size.
- The inner loop is performance critical. Interpretation allocates continuations; keep the hot path direct and put the effect structure around it.
- The framework already owns the effect model (async handlers, reactive pipelines, Rust async). Use its primitives; apply this skill's rules as review criteria (what starts when, who closes what), not as a new layer.
- The question is about designing a combinator library's API and laws: see `fp-api-design-with-laws`. Error and validation types: `fp-data-and-errors`. Threads, locks, deadlock theory inside a program: `craft-concurrency`.

## How to apply

### A. Pick the rung (procedure)

1. Locate every I/O call (print, read, network, DB, clock, random, file, global mutation). List them.
2. Move all decisions into functions that take plain values and return plain values. When "what should happen" is more than a primitive, return a small data value (enum, result, command) that the shell executes. The book's claim: any impure procedure splits into a supplier of inputs, a pure function, and a consumer of outputs, without changing behaviour.
3. Ask whether the remaining shell needs more than a function body. Move up a rung only for a stated reason:
   - Reason "test without the real world": ports and adapters, fakes (rung 2).
   - Reason "compose, retry, run in parallel, defer": effect values (rung 3).
   - Reason "inspect, serialise, forbid other effects, multiple interpreters with the same program": free-structure (rung 4).
4. Have exactly one place that runs the program and chooses the interpreter: the entry point. Everything else builds descriptions or takes the port as a parameter. The name of that function should say it is impure.
5. Write down, in the change description, which rung you chose and why. If you cannot name a concrete reason for rung 3 or 4, stay at rung 1 or 2.

### B. Effects as values: the two rules that prevent most bugs

1. A description must not have started. Anything that already runs when created (a JavaScript `Promise`, a Java `CompletableFuture`, a Kotlin `async` in a live scope) is not a description. Store a thunk (`() => Promise<A>`) or use a lazy type. Rust futures and Python coroutines are lazy until polled or awaited, but check that nothing in the constructor performs work.
2. Run only at the edge. A `run`, `await`, `join` or `.get()` in the middle of a combinator breaks composition (inlining changes parallelism) and can deadlock bounded pools.

### C. Stack safety (short form; details in `stack-safety.md`)

- Self tail recursion: rewrite as a loop with an accumulator. Do this first; it is cheaper than anything else.
- Mutual recursion, recursion through composed functions, or a monadic loop (`forever`, `while`-like `flatMap` chains): use a trampoline. A trampoline is a loop over a small data type: Done(value), More(thunk), Bind(sub, continuation). Rewrite left-nested binds to the right before stepping; that reassociation is what keeps stack depth constant and relies on the associativity law.
- Check that your interpreter is also stack-safe. A safe program run by a naive interpreter still overflows.

### D. Parallel work (short form; details in `parallelism-as-description.md`)

- Separate "combine two independent results" (a `map2`/`zip`/`all` combinator) from "where does this run" (one `fork`-like primitive). If every combinator decides scheduling, policy is baked in everywhere.
- Do not wait inside a pooled task for another pooled task. On a fixed pool this deadlocks. Only the outermost run may block.
- The law to protect: adding or removing the scheduling marker must not change the result, only the performance. Test it on a pool of size 1.
- Decide error propagation up front: errors must reach the caller of run and the continuation must always fire. The book left this as an exercise and its non-blocking version swallowed exceptions.

### E. Streams (short form; details in `stream-pipelines.md`, `resource-safety.md`)

- Model the work as source, zero or more transformers, sink. Transformers are pure (iterator in, iterator out) and know nothing about files. The source owns acquisition and release.
- Never return a lazy sequence that is backed by an open resource unless the consumer's lifetime is tied to the resource's (a scoped callback or context manager). Otherwise you get the four lazy-I/O problems: leak on early stop, read after close, effects triggered by forcing, and out-of-band knowledge about where the value came from.
- Any combinator that stops early (take, first, exists, limit) must cancel upstream before it finishes, so the source's release runs.
- Cleanup errors must not mask the original error (a plain `try/finally` whose cleanup raises does mask it in Python and Java; `resource-safety.md` has a bracket that does not).
- In Python, each generator stage must close its input in its own `finally`; reference counting hides the omission in CPython and a held reference exposes it.

### F. Local mutation (short form; details in `scoped-local-mutation.md`)

Copy the input, mutate only the copy, never let a reference to the mutable structure escape (return value, stored field, escaping closure, callback), freeze before returning. A function built this way is pure for its callers.

### G. Symptom triage

| Symptom in the code or bug report | Likely cause | First move |
|---|---|---|
| Stack overflow after thousands of iterations of a recursive or `flatMap`-chained loop | Nested binds or non-tail recursion | Accumulator loop, else trampoline; test with 1e6 steps |
| Hang under load or with a small pool, fine with a big pool | Pooled task waiting on another pooled task | Remove the inner blocking wait; size-1 pool test |
| "Too many open files", locked file, stale cursor, intermittent read-after-close | Close only on the happy path, or a lazy sequence escaping its scope | Bracket in the source; cancellation forwarded by early-stopping combinators |
| Test needs the network, clock or console to run | Effects interleaved with logic | Factor, then port plus fake |
| A "pure" function is observed mutating its argument | Mutation not local | Copy in, freeze out |
| Retried or stored "effect" runs at the wrong time or twice | Eager future used as a description | Wrap in a thunk; check what starts at construction |
| Algorithm changes keep requiring a rewritten loop | Counting, parsing and I/O fused in one loop | Source, pure transformers, sink |

## Verify

Show the user evidence for each claim, not assertion. Pick the checks that match the rung and the topics touched.

Effect structure
- A grep for I/O calls (`print`, `console.`, `fetch`, `open(`, `Date.now`, `random`, `sleep`, DB client use) outside the shell and the adapters finds nothing in the core. Report the command and result.
- Core functions are tested with plain values, no mocks, no fakes needed.
- Programs written against a port run under a fake adapter with scripted input; assertions are on captured output or recorded calls. The same program also runs under the real adapter in at least one smoke test.
- A function that returns `void`/`Unit`/`None` only to perform an effect is deliberate and located in the shell. In the core it is a smell.
- Exactly one call site runs the top-level description. Check by search.

Laws
- Effect type: `run(pure(a).flatMap(f)) == run(f(a))`; `m.flatMap(pure) == m`; associativity of flatMap, observed by running both groupings under a fake interpreter and comparing outputs. The trampoline's reassociation depends on associativity, so a failure here is a correctness bug.
- Parallel description: `fork(x) == x` result-wise, on pools of size 1, 2 and N; `map(y, id) == y`; `map(map(y, g), f) == map(y, f after g)`; `parMap(xs, f)` equals sequential `map` including order; throwing `f` surfaces its error at run.
- Stream transformers: `(p then q)(xs) == q(p(xs))` against the list equivalent; transformer applied to an empty and to a one-element input.

Stack and memory
- Run the program with a large step count (start at 1e6) on the real interpreter; it completes. Run it with a deliberately small stack so a regression fails fast instead of after minutes (for example `node --stack-size=100 file.js`, `deno run --v8-flags=--stack-size=100 file.ts`, or a Python `sys.setrecursionlimit(200)`). Include a left-nested chain of binds, not only a right-nested loop.
- For streams, feed a source far larger than memory or an infinite generator and stop early with `take(n)`; memory stays flat and the process finishes.

Resource safety (instrument acquire and release with counters in a fake resource)
- Release count equals acquire count for: full consumption, early stop after n items, exception in the source, exception in a downstream transformer, cancellation.
- No read after close (the fake throws if read after release).
- The exception seen by the caller is the original one, even when release also fails.

Concurrency
- 100k tiny forks on a 2-thread pool finish (no thread-per-task, no deadlock).
- Thread count stays bounded during the run.

Done means:
- The chosen rung is stated with its reason, and nothing higher was added.
- Effects run in one place; descriptions are lazy (nothing started at construction).
- The tests above that apply to the touched topics exist and pass, and at least one was seen to fail against a deliberately broken variant (for example a missing release, or `fork` replaced with a blocking wait on a pool of size 1).
- Language-specific degradations from `references/language-mappings.md` that were accepted (eager futures wrapped in thunks, no tail calls, no HKT) are noted in the change.

## Proportion and limits

- Cost of each rung: ports and adapters cost an interface and a fake per effect family. Effect values cost a runtime type and learning curve, and make stack traces harder to read. Free-structure costs the most: boilerplate (sum types for instructions, translation functions), interpretation overhead and allocation, and unfamiliarity. The book itself advises using the IO type directly as little as possible, because programs written inside it tend to be monolithic and hard to reuse; its purpose is to be the lowest common denominator at the edge.
- Free-structure earns its keep when the operation set is small and stable and you need several interpreters or need to inspect programs. Tagless/port style is lighter and enough for most testability needs; choose data (free) over interfaces when you must inspect or serialise the program (adaptation: the book contrasts only the free form; the tagless choice is a modern mapping).
- A pure interpreter only helps if the program is really expressed against the algebra. If most logic still calls the world directly, the fake covers little.
- Contextual purity: whether an effect "counts" depends on what callers observe. Logging, metrics, caches and allocation usually do not; file, DB, network and clock reads that the logic depends on do. Do not track what correctness does not depend on.
- Dated or contested: the book's Process and Par code is a teaching model, not production code (the book says as much); its lineage is libraries such as fs2 (inferred). Prefer your ecosystem's mature stream and effect libraries, and use this material to choose and review, not to hand-roll. The book's non-blocking Par has no error handling; do not copy it as is.
- JVM-era assumptions: trampolining matters where tail calls are not guaranteed (most mainstream runtimes). Rust, Go and some others change the calculus; see `references/language-mappings.md`.

## References

- `references/effect-descriptions-and-interpreters.md`: read when moving effects to the edge, building an IO/effect value, choosing between ports and adapters and a free-structure interpreter, or designing an instruction set. Section 5 has a runnable program with a real and a fake interpreter.
- `references/stack-safety.md`: read when a recursion or monadic loop can run deep, or before writing a trampoline or interpreter loop. It contains a trampoline checked on a million steps, including left-nested binds.
- `references/parallelism-as-description.md`: read when designing or reviewing parallel, async or fan-out code, deadlock on bounded pools, or fork/join combinators and their laws.
- `references/stream-pipelines.md`: read when reading, transforming and writing sequences from external sources, replacing monolithic loops, or reviewing a function that returns a lazy iterator.
- `references/resource-safety.md`: read for the acquire/release rules, cancellation forwarding, error-masking, and the review checklist for anything that opens a resource.
- `references/scoped-local-mutation.md`: read when using in-place mutation inside a pure interface, reviewing aliasing or escape, or deciding which effects to track.
- `references/testing-effectful-code.md`: read when writing the tests listed under Verify, with fake interpreters, property tests, and resource-safety instrumentation.
- `references/language-mappings.md`: read to translate any idiom here into TypeScript, Python, Rust, Kotlin, Java, Go, Swift or C#, and to see how it degrades.

## Sources

- Functional Programming in Scala 1st ed. ch. 7: purely functional parallelism (Par, fork, laws, non-blocking representation, generalising combinators to flatMap/join).
- FP in Scala ch. 13: external effects and I/O (factoring effects, IO type, trampolining, free monads and interpreters, async I/O, main program, why plain IO is insufficient for streaming).
- FP in Scala ch. 14: local effects and mutable state (ST, scoped mutation, contextual purity).
- FP in Scala ch. 15: stream processing and incremental I/O (lazy I/O problems, Process, resource safety rules, Tee, Sink, Channel).
