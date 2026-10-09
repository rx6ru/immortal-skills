# Stream pipelines: source, transform, sink

Contents: 1 The problem with loops inside IO; 2 Why lazy I/O is rejected; 3 Stream transducers (Process); 4 Composition and fusion; 5 Generalising: the request protocol; 6 Sources, Process1, Tee, Sink, Channel; 7 Dynamic resource allocation; 8 Building pipelines in a host language; 9 Choosing the shape; 10 Verify; 11 Pitfalls.

Sources: FP in Scala ch. 13.7 (why plain IO is not enough), ch. 15 (all). (inferred) marks adaptation. Resource-handling rules are in `resource-safety.md`.

## 1. The problem with loops inside IO

IO and ST embed an imperative language in pure code; reasoning inside IO is imperative reasoning. Task from the book: is a file's line count above 40,000? The imperative version is incremental and terminates early, but:
1. Resource safety is manual: remember to close, including on exceptions. Handles are scarce; scanning a directory can exhaust them; garbage collection is not timely; the compiler does not help.
2. The algorithm is entangled with low-level iteration. Counting non-empty lines, or finding the line where first letters of consecutive lines spell a word, each require new loop state. Efficient code in IO means monolithic loops, and monolithic loops do not compose. Adding a 5-element moving average to a file converter (easy on in-memory lists) means rewriting the loop.

On an in-memory sequence each variant is a one-liner: zip with index and test `exists`; filter first; take, map to first letter, find the subsequence. The goal is to keep that style when the data comes from outside.

## 2. Why lazy I/O is rejected

Lazy I/O: return a lazy sequence of lines (inside an IO) that closes the file when the end is reached. Four problems:
1. Not resource-safe: the file is closed only if traversal reaches the end, but `exists` or `take` stop early, so the handle leaks.
2. The sequence can be traversed again after close: if memoised, memory balloons; if not, you read a closed handle.
3. Forcing has I/O effects, so two threads traversing it behave unpredictably.
4. Needs out-of-band knowledge of where the value came from; in composition you should only need its type.

Apply as a review rule: a function returning an iterator, generator, stream or lazy list backed by an open file, socket, cursor or transaction is suspect. Fixes: return a scoped callback (consumer runs inside the resource's lifetime), return a fully materialised value when small, or return a pipeline description that owns the resource when run (sections 3-6).

Examples that reproduce the hazard (adaptation): a Python generator that does `open()` and `yield`s lines without a `with`/`finally` and is returned to callers; a JavaScript async generator over a socket returned without teardown; a Java `Stream` from `Files.lines` that is not in try-with-resources; a database cursor returned from a repository method after the connection closes; Rust `impl Iterator` that borrows a file closed by the caller.

## 3. Stream transducers (the simple Process)

A stream transducer is a transformation from one stream to another. A stream is any sequence: lazily generated, supplied externally (file lines, requests, clicks).

`Process<I, O>` is a state machine with three states, driven by a separate driver:
- `Emit(head, tail)`: the driver outputs head and moves to tail.
- `Await(recv: Option<I> -> Process)`: the driver supplies the next input, or `None` at end of input.
- `Halt`: stop reading and emitting.

The process is agnostic to where input comes from and where output goes. Drivers: one that applies it to an in-memory stream; one that feeds from a file through an iterator and folds emitted values, closing the file in a `finally`. Solving the book's task: `processFile(f, count |> exists(_ > 40000), false)(_ || _)`.

Building blocks (each is small and generic):
- `liftOne(f)`: await, emit f(i), stop. `repeat`: restart on halt (careful: emit is strict, so never repeat a process that does not await first). `lift(f) = liftOne(f).repeat`.
- `filter(p)`, `take`, `drop`, `takeWhile`, `dropWhile`, `count`, `mean` (running average), `zipWithIndex`, `exists`.
- `sum` shows the common pattern: an inner `go(acc)` carrying state. Generalised as `loop(z)(f: (I, S) -> (O, S))`: one piece of state, a transition function, one output per input.
- `exists` variants: emit only the final result; emit all intermediate booleans then halt; do not halt. Because composition fuses, trimming the output of the last form is a separate combinator at no cost.

```python
# Pull-style host version (adaptation): transformers are iterator -> iterator functions that
# contain no I/O. Each one forwards cancellation to its input in `finally`, because Python
# does not: closing a generator runs only that generator's own finally, not its input's.
def _close(it):
    close = getattr(it, "close", None)      # plain iterators have no close
    if close:
        close()

def filter_(p, it):
    try:
        for x in it:
            if p(x): yield x
    finally:
        _close(it)

def take(n, it):
    try:
        if n <= 0: return
        for i, x in enumerate(it, 1):
            yield x
            if i >= n: return              # leaving here runs the finally: upstream is closed
    finally:
        _close(it)

def count(it):
    try:
        n = 0
        for _ in it:
            n += 1
            yield n
    finally:
        _close(it)

def exists(p, it):
    try:
        for x in it:
            if p(x):
                yield True
                return
        yield False
    finally:
        _close(it)
```

Without the `finally: _close(it)` the sketch appears to work in CPython, because reference counting frees the abandoned generator at once and its `finally` runs. That is an accident of the interpreter: it fails as soon as anything still holds a reference to the source (a variable, a traceback, a test harness) and on interpreters without reference counting. Checked on CPython: with `src` kept in a variable, a `take` without the forwarding left the fake file open (opened 1, closed 0); with it, the file was closed (1, 1), including under `take(filter_(...))`, an early `exists`, a source error and a downstream error. The source itself is the generator that does `open ... try: yield ... finally: close` (see `resource-safety.md`). A consumer that stops early with a plain `break` over the top stage must still close that stage (`contextlib.closing(stage)`), which `with` gives you.

## 4. Composition and fusion

`f |> g` feeds f's output to g's input and fuses the transformations: as soon as f emits, g processes it, with no intermediate stream. It is the analogue of function composition. `map(f) = this |> lift(f)`, so Process over a fixed input type is a functor. `++` (append) and `flatMap` make it a monad: `unit = Emit(o)`.

Laws to rely on and to test (book verification section, partly inferred):
- `(p |> q)(xs) == q(p(xs))` (fusion).
- `lift(f) |> lift(g) == lift(g after f)`.
- `|>` is associative; `++`/`flatMap` behave like list concatenation and monad laws as for lists.
- `p(xs)` equals the equivalent list function for filter, take and so on.

Line counting becomes `count |> exists(_ > 40000)`. Fahrenheit to Celsius skipping blank lines and comment lines is a pipeline of filter, filter, map. The 5-element moving average slots in as one more stage, with no loop rewrite.

## 5. Generalising: the request protocol

The simple Process assumes one input stream and a fixed protocol. Parameterise it by the request type F, as Free does:

`Process<F, O>` = `Await(req: F<A>, recv: Either<Throwable, A> -> Process<F, O>)` | `Emit(head, tail)` | `Halt(err)`.

Differences from Free: it can emit many values and terminates with Halt instead of Return. `recv` takes an either so it can handle errors, which is what enables resource safety. `Halt(End)` means normal termination (an exception used as a control signal), `Halt(Kill)` means forced termination, anything else is an error. An option-of-error encoding is an alternative design (book fn.6). In a real implementation `recv` should be trampolined (book fn.5; `stack-safety.md`).

Core operations
- `onHalt(f)`: replace the termination reason with a continuation; thrown exceptions are caught and become `Halt(e)`.
- `++`: continue with the next process only when the reason is End; else re-raise.
- `flatMap`: wrap the call of the user function so exceptions become Halt. Principle: catch and handle all exceptions inside the library rather than burden users; only a few key combinators can generate exceptions, so making those safe makes every program built from them safe.

## 6. Shapes of process

Pick the weakest shape that does the job.

| Shape | Request type F | Use for |
|---|---|---|
| Process1 (one input) | Only "get the next I" | Pure transformations: lift, filter, take, count, window |
| Tee (two inputs) | Left or right | Zip two sources, interleave, read 5 from left then 10 from right, let a left value decide how many to read on the right |
| Source | IO or effect type as F | Reading a file, socket, DB cursor |
| Sink | Process of functions that perform output for one element | File writer, network sender |
| Channel | Process of functions that perform per-element I/O and return a process | DB query executor, enrichment stage |

Sources: an effectful source is a process whose Await requests are effects. The interpreter (`runLog`) runs each request, passes `Right(result)` or `Left(exception)` to `recv`, collects emitted values, returns on `Halt(End)` and throws on other halts. The book's Exercise 15.10 generalises the runner to any monad with `attempt` and `fail`; it cannot be tail-recursive, so stack safety rests on the monad.

Tee: `zipWith(f) = awaitL(i => awaitR(i2 => emit(f(i, i2)))).repeat`; halts when either input is exhausted, like list zip. Being explicit about read order matters when inputs have effects; the alternative is leaving order unspecified so the driver can run both concurrently (needs the nondeterminism extension the book defers).

Sink: `p.to(sink) = join(zipWith(p, sink)((o, f) => f(o)))`. Full pipeline from the book: lines of a file, drop comments, convert, intersperse newlines, send to the file writer, drain, run. The user writes no exception handling; combinators guarantee closing on error or when the feeder signals done.

Channel: generalise `to` to `through`. The channel's dependencies (a connection to obtain and close) live inside it, so users do not manage them. Rows come back as a process so result sets get all the transducers.

## 7. Dynamic resource allocation

With `flatMap`, scenarios like "read a file of filenames, concatenate the files into one stream, convert, write one output" or "one output per input file" are nested generators in a for-comprehension. Resource safety is preserved: handles close automatically, even with exceptions, and exceptions surface at the runner. Use `once` to limit to one element and `drain` to ignore output.

## 8. Building pipelines in a host language (adaptation)

You rarely hand-write Process. The reusable idea is the division of labour:
- The source owns acquisition and release (bracket/using/defer/context manager in exactly one place).
- Transformers are pure functions on iterators/streams/flows. They never open or close anything.
- The sink owns its resource similarly.
- Combinators that stop early forward cancellation upstream (`resource-safety.md` rule 2).
- A driver at the edge runs the pipeline.

Host mappings (from the book's cross-language note): Unix pipes; Rust iterator adapters with Drop; Python generators with `with` and `contextlib.closing`; Node `stream.pipeline()`; Kotlin `Flow`, `use {}`, `sequence {}`; Go channels with `context` cancellation and `defer`; RxJS teardown; Reactive Streams backpressure; C# `IAsyncEnumerable` with `await using`; Akka/Pekko Streams; fs2, ZIO Streams, conduit, pipes in other ecosystems. Prefer a mature library in your language.

Pull vs push (inferred): Process as presented is pull-based (Await asks). Push systems (observables, event emitters) need explicit backpressure and unsubscription to reach the same safety.

Without sum types or HKT, model the state machine as an interface with `next(input) -> {emit, await, halt}` and a driver loop; or use the language's iterator protocol with try/finally in the source and keep transformations as iterator-to-iterator functions.

## 9. Choosing the shape of the solution

Decision rules (book summary, with adaptation):
1. Reading, transforming and writing sequences from external sources with large data or early termination: pipeline of source, transformers, sink. Do not write a monolithic while loop mixing counting, parsing and I/O.
2. Do not return lazy lists/iterators/generators from a function that holds an open resource, unless the consumer's lifetime is bound to the resource.
3. Data fits comfortably in memory, no early exit, source closed in one place: read it all and use ordinary collection functions. A pipeline is not needed (adaptation).
4. One-off script over a small file: the monolithic loop is acceptable; resource safety by `with` is still a good habit.

## 10. Verify

- Transformers tested on in-memory sequences with no I/O: `p(xs)` equals the list equivalent for random `xs`, empty input, one element.
- Fusion: `(p |> q)(xs) == q(p(xs))`.
- Early termination test: `take(n)` of a large or infinite source finishes, and the source's release ran (see `resource-safety.md` for the instrumented fake).
- Constant memory: feed a source much bigger than memory (generated), consume with a fold or `take`; peak memory flat.
- Stack: pipelines over millions of elements complete (the book omitted trampolining in listings and notes it should be there).
- Order of effects in Tee/zip: assert which side is pulled first when it matters.

## 11. Pitfalls

- Repeating a process that emits before awaiting: infinite emit loop (strict emit).
- Hidden buffering: a transformer that collects everything (sort, group-all) breaks constant memory; make it explicit.
- Transformers with side effects (logging, writes) defeat the "pure transformer" test strategy; make them sinks or effectful stages.
- A reused buffer returned as a view (ties to `scoped-local-mutation.md`): consumer retains the view and sees it change on the next read.
- Treating the book's Process as production code: it is a model of the idea.

Related: `resource-safety.md`, `testing-effectful-code.md`, `stack-safety.md`, `language-mappings.md`.
