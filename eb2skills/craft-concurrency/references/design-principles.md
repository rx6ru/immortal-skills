# Design principles for concurrent code

Sources: Clean Code ch. 13 and app. A; Pragmatic Programmer ch. 5 (temporal coupling). Content marked (adaptation) goes beyond the notes.

## Contents
1. Why and when to add concurrency
2. Myths and the honest costs
3. The four defence principles
4. Separating thread policy: worked refactoring
5. Throughput arithmetic
6. Know your library
7. Synchronisation rules
8. Shutdown
9. Procedure: designing a concurrent component

## 1. Why and when to add concurrency

Concurrency is a decoupling strategy: it separates what gets done from when it gets done (Clean Code ch. 13). In a single thread, what and when are so entwined that one stack trace tells you the whole state. Decoupled, the program looks like many small collaborating computers rather than one main loop, which can improve structure as well as throughput. A request container is the everyday example: each request is handled in its own world, though the isolation is imperfect and handlers still must guard shared resources.

Performance motives named in the notes:
- Waiting dominates and can be shared: an aggregator that visits many sites one after another spends most of its time waiting on I/O.
- Queueing: a system that serves one user at a time makes the 150th user wait.
- Data can be processed in parallel on many cores or machines.

Decision procedure for "this is too slow" (Clean Code app. A, client/server example):
1. Pin the requirement in a test with a time budget (for example, "N client requests finish within 10 seconds"). Measure before and after.
2. Decide where the time goes. I/O bound: sockets, database, swap. Processor bound: numeric work, regular expressions, garbage collection.
3. Processor bound: more threads on the same CPU do not help; you need a better algorithm or more or faster hardware.
4. I/O bound: threads or async tasks help, because one task's waiting time is another's computing time.
5. Only then add concurrency, and remeasure.

Signals that concurrency is the wrong move: nothing measured is slow; the work is CPU-bound and you have one core; the design would have to share lots of mutable state; the task is small enough that thread overhead exceeds the gain.

## 2. Myths and the honest costs

Myths (Clean Code ch. 13) and their balanced truth:
- "Concurrency always improves performance." Only when substantial wait time can be shared among threads or processors, and arranging that is not trivial.
- "Design does not change." It can change radically, because what/when decoupling reshapes the system.
- "If I use a container or framework I need not understand concurrency." You must know what the container does and guard against concurrent update and deadlock yourself.

Sound bites worth keeping:
- Concurrency adds overhead, both runtime and code.
- Correct concurrency is complex even for simple problems.
- Concurrency bugs are not usually repeatable, so they get written off as one-offs.
- It often requires a fundamental change in design strategy.

## 3. The four defence principles

1. **Single responsibility: concurrency code is kept apart from other code.** It has its own life cycle (written, changed, tuned), its own harder challenges and many failure modes. In practice: thread-aware classes are small and focused; business logic sits in thread-ignorant plain objects that the thread-aware layer calls.
2. **Limit the scope of data.** Fewer critical sections means fewer places to forget a guard (one forgotten place breaks everything that touches the data), less duplicated guarding effort, and an easier time tracing failures. Apply encapsulation hard: severely limit access to anything that can be shared.
3. **Use copies of data.** Copy and treat as read-only, or give each thread its own copy and merge the results in one thread. Object creation and collection cost is usually less than locking. The notes state this without numbers: measure.
4. **Make threads as independent as possible.** Each thread handles one request using data from an unshared source, held in locals (the servlet `doGet` pattern: inputs arrive as parameters). Partition the data into independent subsets, each handled by an independent thread, possibly on different processors. Shared resources such as database connections are where independence eventually breaks down.

Why the order in SKILL.md (do not share, then immutable, then copy, then message-passing, then guard): each step down the list leaves more code that must be reasoned about under every interleaving. (Ordering is an adaptation that combines the four principles with the pragmatic advice on services.)

Related design rules from Pragmatic Programmer ch. 5 (tip 41, "Always design for concurrency"):
- Global and static variables must be protected from concurrent access; ask why you need the global at all.
- State must be consistent whatever the call order. Ask "when is it valid to query this object?" An object that is invalid between constructor and `init()` is safe only by coincidence that nobody calls in the gap.
- Retrofitting concurrency onto a non-concurrent design is much harder than designing for it; designing for it leaves the option to deploy stand-alone or distributed, and yields a cleaner design if you never use the option.

## 4. Separating thread policy: worked refactoring

Starting point (Clean Code app. A): a blocking server loop accepts a connection and calls `process(socket)`. The first fix for the failing throughput test wraps the body of `process` in a runnable started on a new thread per connection. It passes the test but is not finished:
- Thread creation is unbounded, so a flood of public users can hit the runtime limit and halt the system.
- `process` now mixes four things: connection management, client processing, threading policy and shutdown policy. It has several reasons to change.

Result of the refactoring:
- The server loop becomes: wait for a client connection, build a request processor from it, hand the processor to a scheduler; after the loop, shut the connection manager down.
- All thread policy sits behind a one-method interface (`schedule(processor)`).
- Thread-per-request is one implementation. A bounded pool of a configured size is a second implementation, plugged in with no other change. The bounded pool also fixes the unbounded-creation problem.
- Payoff: tuning or experimenting with the threading strategy touches one class, and everything else is testable without threads.

Sketch (adaptation, Python-flavoured; the same shape applies in any language):

```python
class Scheduler(Protocol):
    def schedule(self, job: Callable[[], None]) -> None: ...

class BoundedPool:   # bounds workers only; the pending-job queue is unbounded
    def __init__(self, workers: int):
        self._ex = ThreadPoolExecutor(max_workers=workers)
    def schedule(self, job): self._ex.submit(job)   # job errors are held in the Future, not raised

def serve(conns, make_job, scheduler: Scheduler):
    for c in conns:                 # no thread knowledge here
        scheduler.schedule(make_job(c))
```

Test with an inline scheduler (an object whose `schedule` calls `job()` directly) for the logic, and the real pool for the stress tests. (The sketch needs imports of `Protocol`, `Callable` and `ThreadPoolExecutor`.) Bound the pending queue too, or the unbounded-creation problem returns as an unbounded backlog (adaptation).

Rule stated by the notes: keep thread management in a few well-controlled places, and have the code that manages threads do nothing else.

Where trouble concentrates (Clean Code ch. 13 conclusion): multiple threads on shared data; a common resource pool; and boundary cases such as clean shutdown and finishing a loop iteration. Look there first. Testability and pluggability go together, so invest early in instrumentation and run the threaded code as long as possible before production.

## 5. Throughput arithmetic

Use this as a template to estimate benefit before building (Clean Code app. A, page-reading example).

Assumptions: reading a page takes 1 s of I/O at 0% CPU; parsing takes 0.5 s at 100% CPU. One thread: 1.5 s per page, so 13 pages is about 19.5 s. Three threads: each 1 s read overlaps with two 0.5 s parses, so about 2 pages per second, three times the single-thread rate, in the idealised case.

Preconditions: items can be fetched in any order and processed independently. In that example the only synchronised part is the hand-off of the next URL; each worker owns its own reader. Synchronise as little as possible.

## 6. Know your library

From Clean Code (Java 5 era; the idea generalises):
- Use thread-safe collections and executors provided by the platform; prefer nonblocking solutions where possible; remember that some library classes are not thread-safe (examples: a date formatter, database connections, ordinary containers, servlets).
- A concurrent map that offers atomic compound operations (put-if-absent) replaces the unsafe check-then-act sequence.
- Other building blocks: reentrant lock (acquire in one method, release in another), semaphore (a lock with a count), countdown latch (wait for N events, then release all waiters so threads start about together).
- Executors pool, resize and re-create threads, accept tasks that return results, and return futures. The future pattern: submit a task, do local work, then ask for the result, which blocks only if not ready. Use it when several independent operations can run in parallel and be awaited together.
- Atomic variables use compare-and-swap, an optimistic strategy (assume no conflict, detect it, retry) versus the pessimistic lock that is taken even without contention. The notes claim atomics are nearly always at least as fast. Keep this as a default to measure, not a law; it does not extend to invariants over several variables (adaptation).

Mappings for other languages are in `choosing-a-mechanism.md`.

## 7. Synchronisation rules

- Beware dependencies between synchronised methods: see `hazards-and-deadlock.md` section 4 for the three fixes.
- Keep synchronised sections small. Locks add delay and overhead. Critical sections must be guarded, but be few and small; big sections "to be safe" raise contention.
- Avoid calling one locked section from another, and keep shared objects and the scope of sharing as narrow as possible. Change the design of shared-data objects to suit clients, rather than forcing every client to manage the shared state.

## 8. Shutdown

Graceful shutdown of a long-lived system is hard to get right. Typical failures: a parent waits forever for a child that is deadlocked; a producer stops on a signal while its consumer blocks waiting for more and never sees the shutdown. Think about shutdown early, get it working early, expect it to take longer than you think, and review existing algorithms rather than inventing one.

Concretely, decide for each worker: what tells it to stop (cancellation flag or token, poison pill message, closed queue or channel, deadline), how it drains or abandons in-flight items, and who joins it. Test it: start work, request stop, assert that all workers exit within a timeout and no work is silently lost (adaptation).

## 9. Procedure: designing a concurrent component

1. State the goal with a measurable budget (latency, throughput) and where time goes (I/O or CPU).
2. List the shared mutable state that the straightforward design would have. Try to eliminate each entry using section 3.
3. Put logic in thread-ignorant units. Write their tests first without threads.
4. Define the scheduling interface and implement the simplest policy (single thread, inline). Run all tests.
5. Add the real policy (bounded pool, async runtime, actors) behind the interface; make worker count configurable.
6. For remaining shared state, make a single owner class; give compound operations as single methods; document the lock order if more than one lock exists.
7. Design shutdown.
8. Write stress tests (see `testing-concurrent-code.md`), then tune worker count by measurement.

Cost: the extra interface and the configuration. Skip steps 4 and 5 for a one-off script.
