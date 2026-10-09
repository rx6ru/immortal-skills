# Resource safety

Contents: 1 What must hold; 2 The two rules; 3 Mechanism: bracket, onComplete, finalizers; 4 How pipelines forward cancellation; 5 Host-language forms; 6 Review checklist; 7 Tests; 8 Pitfalls.

Sources: FP in Scala ch. 15.1, 15.3.2, 15.3.3, 15.3.4, 15.3.5 (resource safety by construction); ch. 14.2 sidebar (buffer reuse). (inferred) marks adaptation.

## 1. What must hold

Resources: file handles, sockets, DB connections and cursors, locks, temp files, subprocesses, buffers. The aim is "resource-safe by construction": a resource is released as soon as it is no longer needed, whether the program ended normally, failed, or stopped early, and it is never used after release. User code should not call close.

Three ways a producer can stop (book 15.3.2):
- Exhaustion (normal end).
- Forced termination because the consumer stopped early (take, exists, first match, user cancel).
- Abnormal termination: an exception in the producer or the consumer.

In all three the underlying resource must be closed.

## 2. The two rules

Rule 1. A producer frees its underlying resources as soon as it knows it has no further values to produce, whether from exhaustion or from an exception.

Rule 2. Any process that consumes values from another process must ensure the producer's cleanup runs before the consumer halts. The runner cannot do it, because it does not know a composition was involved (for example a lines source piped into `take(5)` halts early). The responsibility lives in exactly one place: the pipe/zip combinator.

Consequences for code you write:
- Acquire and release are defined together, at the source.
- Combinators that can stop early (take, takeWhile, exists, first, limit, zip with a shorter side) are the ones that must propagate cancellation upstream before finishing.
- Consumers never reach into the source to close it.

## 3. Mechanism

Bracket pattern: `resource(acquire)(use)(release) = acquire, then use(r) and always release(r)`. In the book it is built from `onComplete`.

- `onComplete(cleanup)`: like append, but the cleanup runs whatever the termination reason, then re-raises the original reason (it does not swallow errors).
- Cleanup must run even when the process is being killed; the book marks the cleanup process as a finalizer (so a Kill signal does not abort the cleanup itself).
- `eval(fa)` promotes an effect to a process that emits its result; `eval_(fa)` runs for effect and emits nothing (used for close).
- The file source: `lines(name) = resource(open)(src => emit each line, Halt(End) at EOF)(src => eval_(close))`. Users of `lines` write no try/finally.
- Kill: when downstream halts, the pipe signals the upstream to kill itself (feeding Kill into its outermost await and draining output, then converting the Kill back to a normal end), and only then halts, preserving the first error. When upstream halts, its reason is fed to downstream. `tee` does the same for both inputs: when the tee halts, it kills both; when one input halts while the tee wants it, it kills the other. The book keeps the first error and appends cleanup so cleanup errors do not replace it.
- Dependency management in channels: obtaining and closing the connection happens inside the channel.

Exception safety principle: wrap every user-supplied function call in the few key combinators so a thrown exception becomes a termination reason. Then everything built from those combinators is safe.

## 4. Why this fixes the leaked-lazy-stream problem

Lazy I/O fails because closing depends on reaching the end of the traversal. In the bracket-in-source design, closing depends on the termination of the process, and every early exit is a termination routed through the cleanup. Hence early-stopping consumers are safe.

## 5. Host-language forms (adaptation, from the book's cross-language note plus common practice)

| Language | The bracket | Cancellation upstream | Watch for |
|---|---|---|---|
| Python | `with` / `contextlib.closing` / `try/finally` around the `yield` in a generator | Closing the generator raises `GeneratorExit` at the yield; its finally runs. It does not close the generator's input: each stage must call `close()` on its input in its own `finally` | A generator that is never closed or garbage-collected late (CPython hides this with reference counting, other interpreters and held references do not); generators returned past their `with`; a `finally` whose `close()` raises and replaces the original error |
| TypeScript/Node | `try/finally` in async generators; `stream.pipeline()` / `pipeline` from `stream/promises` destroys all streams on error | `return()` on the async iterator, which `for await` calls on `break`, `return` or throw, and which an async generator forwards to the iterator it is itself looping over; `AbortSignal` | `.pipe()` chains (errors do not propagate or destroy the other streams); manual `next()` loops that never call `return()` on early exit |
| Rust | RAII: `Drop` closes the file | Dropping the iterator drops upstream | Holding a reference to the iterator beyond use; `mem::forget`; async cancellation points |
| Kotlin | `use {}`; `Flow` with `flowOn`/`onCompletion`; `sequence {}` with try/finally | Coroutine cancellation | Catching `CancellationException`; returning a `Sequence` from inside `use` |
| Java | try-with-resources | `Stream.onClose`, `close()` of the stream | `Stream` from `Files.lines`/DB not in try-with-resources |
| Go | `defer` | `context.Context` cancellation checked by producer | Goroutine blocked on send after consumer left (leak); forgetting `ctx.Done()` in select |
| C# | `using` / `await using` | `IAsyncEnumerable` with `CancellationToken`, `[EnumeratorCancellation]` | Not disposing the enumerator |
| Swift | `defer`, `AsyncStream.onTermination` | Task cancellation | Retain cycles in termination handlers |

Push-based systems (observables, event emitters) need explicit unsubscription and backpressure to reach the same safety (inferred).

Bracket that keeps the original error (Python 3.11+ for `add_note`; checked: a plain `try/finally` whose `release` raises replaces the original `ValueError` with the `OSError`, this version keeps the `ValueError`):

```python
def bracket(acquire, use, release):
    r = acquire()
    try:
        result = use(r)
    except BaseException as e:
        try:
            release(r)
        except Exception as re:
            e.add_note(f"release also failed: {re!r}")   # secondary error attached, not substituted
        raise
    release(r)          # no earlier error: a release failure is now the error
    return result
```

Checked in TypeScript as well: an async generator over a fake file, wrapped by hand-written `take` and `map` async generators, closed the file exactly once for full consumption, `take(3)` of a source of 1e9 items, an error in the source, an error in a downstream `map`, a `break` in the consuming loop, and a manual `return()` on the top stage.

A hand-written equivalent of rule 2 in a language with iterators: the combinator `take(n, it)` calls `it.close()` (or relies on `finally` triggered by closing the generator) when it stops. Test it (section 7), because forgetting this in one combinator breaks the guarantee.

## 6. Review checklist

1. Acquisition and release defined together at one place (bracket/with/defer/RAII).
2. Release runs on end, on error, and on early cancel.
3. Every combinator that stops early signals cancellation upstream before it finishes.
4. A release error does not mask the original error (original is re-raised after cleanup, or release errors attached as secondary).
5. User code never calls close on something a source owns.
6. No lazy sequence escapes the resource's scope (`stream-pipelines.md` section 2).
7. Reused buffers: never expose a read-only view that aliases an internal buffer to code that can retain it (book 14.2 sidebar: a retained view changes on the next read).
8. Dynamic acquisition (open one file per item of another stream) also closes each handle as soon as its item is done, not at the end of the whole run.
9. No read after close: the resource wrapper rejects use after release.

## 7. Tests

Use a fake resource that counts acquisitions and releases and throws if used after release (`testing-effectful-code.md` has a sketch). For each scenario assert `released == acquired` and no use-after-release:
1. Full consumption.
2. Stop after n items (`take(n)`, `exists`, `break`).
3. Exception thrown by the source on the k-th read.
4. Exception in a downstream transformer.
5. Cancellation from outside (token/abort/cancel scope).
6. Release itself throws: caller sees the original exception, not the release error.
7. Two inputs (zip/tee): one ends first; the other is still released.
8. Nested/dynamic acquisition: N inputs open, each released.

Additionally run with a very large or infinite source plus `take(n)` to confirm early exit does not read the whole source.

## 8. Pitfalls

- Closing in the happy path only (after the loop, not in finally).
- Closing in a destructor/finalizer and relying on garbage collection: not timely (book).
- Returning an iterator out of a `with`/`use` block: the resource is closed before consumption.
- Producer goroutine/task still blocked trying to send after the consumer stopped.
- Swallowing the original exception in a finally block that raises its own.
- Mixing resource ownership: a transformer that opens a file lazily on first element, so release must be arranged in the transformer too. Keep opening in sources.
- Catch-all that treats cancellation as an ordinary error and continues.

Related: `stream-pipelines.md`, `testing-effectful-code.md`, `language-mappings.md`.
