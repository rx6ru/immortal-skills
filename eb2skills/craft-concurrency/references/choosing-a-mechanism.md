# Choosing a mechanism

The books (Clean Code 2008, Pragmatic Programmer 1999) predate async/await runtimes, mainstream actors and channels. The selection logic below is derived from their principles; the language mappings are adaptation and are labelled as such. Verify API names against the version of the language in use.

## Contents
1. The selection questions
2. Chooser table
3. Mechanism notes: threads and pools, async/await, actors and mailboxes, channels, atomics, locks, immutable snapshots
4. Mappings by language (adaptation)
5. What stays true whatever the mechanism

## 1. The selection questions

Ask in this order. Each answer narrows the field.

1. **Is the time spent waiting or computing?** (Clean Code app. A.) Waiting (network, disk, database): many concurrent tasks help, and lightweight tasks are enough. Computing: you need real parallel execution (threads or processes on separate cores) and a bound near the number of cores; more tasks than cores will not speed it up.
2. **Does the work share mutable state?** If it can be partitioned so that tasks share nothing, any mechanism works and none needs a lock. If not, can one owner hold the state and receive messages? That points to actors, channels, or a single-writer queue.
3. **What is the shape?** Independent jobs submitted and awaited: executor or task group. A stream of work between stages: bounded queue or channel (producer-consumer). Mostly-read shared data: immutable snapshots or read-write lock (readers-writers). Several resources per job: ordering or try-lock (dining philosophers).
4. **Will tasks block while holding a pool thread?** Blocking inside a pool task that waits on another pool task can deadlock a fixed-size pool. In async runtimes, blocking calls in the event-loop thread stall every task on it (adaptation).
5. **How will it stop and how will it be tested?** If the mechanism makes cancellation and bounded concurrency easy to configure, prefer it.

## 2. Chooser table

| Need | Prefer | Avoid | Cost / watch |
|---|---|---|---|
| Counter or flag updated by many tasks | Atomic variable | Plain `x += 1`, a lock for one variable | Atomics protect one variable; they do not protect an invariant across two |
| Invariant across several fields | One lock owned by the class that owns the fields, or single-owner message loop | Atomics on each field separately | Keep the section small; document lock order if more than one lock |
| Map/cache shared across tasks with put-if-absent | Concurrent map with atomic compound operations | `contains` then `put` | Atomic compute functions must be short and side-effect free (adaptation) |
| Many independent I/O-bound jobs | Bounded pool or async tasks with a concurrency limit | Unbounded thread or task creation per request | Pick the limit by measurement; make it configurable |
| CPU-bound parallel work | Pool sized near core count; or a parallel map over partitions | More threads than cores expecting speed-up | Merge results in one place |
| Stages passing work along | Bounded queue or channel | Unbounded queue, wait/notify by hand | Define end-of-stream and full-queue policy |
| Mostly reads, rare writes | Immutable snapshot swapped atomically; else read-write lock | Writer-starving read locks without a policy | Copy cost on write |
| One task computes, others wait for its result | Future/promise/deferred | Polling a flag | Do not block pool threads waiting on futures from the same pool |
| Many consumers, uneven task cost | Shared work queue pulled by N workers (hungry consumers) | Central scheduler assigning work | Needs concurrency-safe queue |
| Coordinating facts that arrive in unpredictable order | Blackboard / message topic plus rules | Fixed workflow engine rewired per change | Harder to trace; see `temporal-coupling-and-workflow.md` |
| API that composes async work | Descriptions run by one interpreter | Calling `get`/`await` inside combinators | See `describing-parallel-work.md` |

## 3. Mechanism notes

### Threads and pools
- Create threads in one place behind a scheduling interface (Clean Code app. A). Bound the pool. Make size configurable; the right count is found by timing the system under several settings (Clean Code ch. 13).
- A pool also gives re-creation of dead workers, task results through futures, and one place to shut down.
- Do not block a pool thread on another task from the same pool. Verify with a pool of size one.

### Async/await (adaptation)
- Suits I/O-bound work: many tasks interleave on few threads. On a single-threaded event loop (JavaScript, Python `asyncio`) shared state is touched only between suspension points, which removes many races but not all. Runtimes that run tasks on several threads (Tokio's multi-thread runtime, .NET and Kotlin dispatchers backed by thread pools) lose that guarantee, so shared state there still needs real synchronisation. Even on one thread, a read, an `await`, then a write on the same state still loses updates if two tasks interleave at the `await`. Treat each `await` between a check and the dependent action as the same check-then-act hazard as in `hazards-and-deadlock.md` section 4.
- Blocking calls and CPU-heavy loops inside the event loop starve all other tasks. Offload them to a thread or process pool.
- Eager futures (JavaScript promises, Java `CompletableFuture`) start running when created; lazy ones (Rust futures, Python coroutines) start when polled or awaited. This matters for the describe-then-run style (see `describing-parallel-work.md`).
- Bound concurrency explicitly (semaphore, limited task group); `gather` over an unbounded list is the async version of unbounded thread creation.

### Actors and mailboxes
- An actor processes one message at a time and owns its state, so no lock is needed inside it. The FP in Scala chapter uses a minimal actor as a race-free rendezvous: two mutable slots hold the first-arriving result, and the actor handles one arrival at a time.
- Costs: ordering and request-reply designs need care; a message loop that waits on another actor can deadlock exactly like locks (adaptation).

### Channels (adaptation)
- Producer-consumer made first class. Decide capacity (bounded gives backpressure), who closes the channel, and what a receiver does on close. Shutdown is usually "close the channel; receivers drain and exit".

### Atomics and compare-and-swap
- Optimistic: read, compute, swap if unchanged, retry otherwise. Clean Code claims this is nearly always at least as fast as locking; treat it as a default to measure, and remember it covers single variables only.

### Locks
- Choose a lock when an invariant spans several variables. Use the platform's reentrant lock or monitor; semaphores for counted resources; latches or barriers to start or wait for N participants.
- Keep sections small; do not call unknown code or do I/O while holding the lock unless the design requires it; write the lock order down.

### Immutable data and copies
- Share immutable values freely; build new values rather than mutating. Pragmatic Programmer and Clean Code both push to limit what can be shared; the FP chapters push further. Copy cost versus lock cost: measure.

## 4. Mappings by language (adaptation)

| Idea | Java/Kotlin | Python | Go | Rust | TypeScript/JS |
|---|---|---|---|---|---|
| Bounded worker pool | `ExecutorService` fixed pool; Kotlin dispatcher with limited parallelism | `ThreadPoolExecutor`, `ProcessPoolExecutor` | worker goroutines reading a channel | thread pool crate, or scoped threads | worker threads; async with concurrency limit |
| Task result | `Future`, `CompletableFuture`, `Deferred` | `Future`, awaitable | result sent on a channel; `errgroup` | `JoinHandle`, futures | `Promise` |
| Atomic variable | `AtomicInteger`, `AtomicReference` | no true atomics for compound ops; use a lock or a queue | `sync/atomic` | `std::sync::atomic` | `Atomics` on shared buffers (rare) |
| Mutex for shared state | `ReentrantLock`, `synchronized` | `threading.Lock` | `sync.Mutex` | `Mutex<T>` inside `Arc` | rarely needed on one thread; needed with workers |
| Concurrent map | `ConcurrentHashMap` | a dict guarded by a lock (individual operations are atomic under the interpreter lock, sequences are not) | `sync.Map` or mutex-guarded map | `DashMap` crate or `Mutex<HashMap>` | not applicable on one thread |
| Message passing | blocking queues, actor libraries, Kotlin channels | `queue.Queue`, `asyncio.Queue` | channels | `mpsc`, crossbeam channels | `postMessage`, async queues |
| Race detector | `jcstress`, Lincheck | none comparable; stress tests | `go test -race` | ThreadSanitizer, Miri for unsafe code | none comparable |

In Python the interpreter lock makes some single operations atomic, but sequences such as read-then-write on a shared counter or check-then-insert on a dict are still racy. Do not rely on it for correctness (adaptation; confirm for your interpreter version; free-threaded builds from 3.13 have no such lock). The same lock means threads do not run Python bytecode in parallel on a standard build, so for CPU-bound work use `ProcessPoolExecutor` or native extensions, and keep threads for I/O waits.

## 5. What stays true whatever the mechanism

- Keep the concurrent shell thin and the logic thread-ignorant (Clean Code ch. 13).
- Compound operations on shared state belong to the owner of the state (Clean Code app. A).
- Break one of the four deadlock conditions deliberately (Clean Code app. A).
- Bound everything: thread count, queue size, concurrent in-flight tasks.
- Design shutdown at the start.
- Test under perturbation, repeated, with timeouts (`testing-concurrent-code.md`).
