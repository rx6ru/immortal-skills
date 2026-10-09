# Hazards, classic problems and deadlock

Sources: Clean Code ch. 13 and app. A; Why Programs Fail ch. 4 (schedules). Marked (adaptation) where beyond the notes.

## Contents
1. Vocabulary
2. Why intuition fails: interleavings and atomicity
3. The three classic problems
4. Dependencies between calls (check-then-act)
5. Deadlock: scenario and the four conditions
6. Choosing which condition to break
7. Starvation and livelock
8. Diagnosis table

(The lost update in application code, the password-file tool, is the last paragraph of section 2.)

## 1. Vocabulary

- **Bound resource**: a resource of fixed number or size (database connections, fixed buffers, pool threads).
- **Mutual exclusion**: only one thread may use the shared data or resource at a time.
- **Starvation**: a thread or group is prevented from progressing for a very long time or forever (for example fast threads always go first).
- **Deadlock**: two or more threads each hold a resource another needs and wait forever.
- **Livelock**: threads proceed in lockstep, each trying to progress but getting in another's way, so they keep trying without progress.
- **Atomic operation**: uninterruptible; no other thread can observe it half-done.
- **Critical section**: code that must not run concurrently for correctness.

## 2. Why intuition fails: interleavings and atomicity

The core example: a field `lastIdUsed` and `getNextId() { return ++lastIdUsed; }`. Starting at 42 with two threads, the outcomes are (43, 44), (44, 43), and the surprising (43, 43) with the field left at 43. That third result is a lost update: read-modify-write is not atomic.

Number of interleavings. One source line `return ++lastIdUsed;` compiles to 8 instructions in the book's bytecode. For T threads each running N instructions with no branching the count is (N*T)! / (N!)^T. Values from the notes: N=2,T=2 gives 6; N=2,T=3 gives 90; N=3,T=3 gives 1680; N=8,T=2 gives 12,870. If the field is a 64-bit `long`, reads and writes become two operations each and the book reports 2,704,156 paths (that figure equals the formula at N=12; the study notes' "N=16" does not reproduce it, since N=16 gives about 601 million, so quote the book's number and not the derivation). Most interleavings are harmless; a few are not. Lesson: you cannot find these by thought experiment or by luck, and the failing paths are a tiny fraction of the total, which is why failures are rare and irreproducible.

Why a lost update happens: thread 1 reads 42 and is preempted; thread 2 runs the whole method (field becomes 43, returns 43); thread 1 resumes, adds 1 to its stale 42, stores 43. One increment vanished.

Atomicity traps (Clean Code app. A):
- Increment, decrement and compound assignment (`++`, `+=`) are not atomic in any common language. A common misconception is that pre/post increment is atomic.
- Assigning a constant to a 32-bit field is atomic in the book's JVM example. Assigning a 64-bit `long` or `double` is two 32-bit writes in the spec, so a reader can see half of each of two different values (it may be atomic on a given CPU, but not guaranteed). (Language specifics vary; check the memory model of your language. Adaptation.)
- Synchronisation shrinks the space of behaviours you must reason about, which is its real value besides exclusion.

What the agent must know day to day, rather than bytecode: (1) where the shared objects and values are, (2) which code can cause concurrent read/update problems, (3) how it is guarded.

The same defect in application code, from Why Programs Fail ch. 4: two parallel runs of a password-file tool each read the file, modify it and write it back. If both read before either writes, the last writer wins and the other update is lost. Fixes for that known bug: lock the file; or record the last-update time at read and check it again before writing, re-reading if it changed (optimistic check). The same pattern applies to any shared resource: shared variables, files, rows.

## 3. The three classic problems

The notes say most concurrency problems are variations of these three. Recognise the shape, then reach for the known remedy.

### Producer-consumer
- Shape: producers put work into a bounded queue; consumers take it. Producers signal "not empty"; consumers signal "not full"; each may have to wait. The queue is a bound resource.
- Hazards: consumers blocked forever after producers stop (shutdown; the notes' example). Further hazards (adaptation): lost wake-up signals, unbounded queue growth if you remove the bound, work lost on stop.
- Remedies (the first sentence is adaptation): use the platform's blocking bounded queue or channel rather than wait/notify; give the queue a defined end-of-stream or poison pill; decide what happens when the queue is full (block, drop, or reject) on purpose.
- Related design (Pragmatic Programmer ch. 5): the hungry-consumer model, where N independent consumers pull from one shared work queue instead of a central scheduler pushing work. A slow consumer simply takes less; no scheduler becomes the bottleneck. See `temporal-coupling-and-workflow.md`.
- Verify: a test that stops producers mid-stream and checks consumers exit; a test with a slow consumer that checks producers block or shed according to the policy.

### Readers-writers
- Shape: a shared resource that is mostly read and occasionally written. Writers must wait for zero readers.
- Hazards: continuous readers starve writers; giving writers priority hurts throughput and blocks many readers.
- Remedy: balance correctness, throughput and freedom from starvation explicitly (the notes' stance). Choosing a read-write lock policy deliberately (fair, reader-preferring or writer-preferring) and testing for writer starvation is adaptation. Often a better remedy is to avoid the contention: swap in an immutable snapshot that readers hold while the writer builds a new one (adaptation, consistent with the "use copies" principle).
- Verify: a test with a steady stream of readers shows a pending writer eventually completes within a bound.

### Dining philosophers
- Shape: n threads each need two shared resources (forks); naive grab-left-then-right deadlocks. Livelock and efficiency problems also arise in the fixes. It models enterprise processes that compete for several resources.
- Remedies: the four deadlock conditions below; a global resource order is the usual one.
- Verify: a test where all threads start at once with a barrier and a timeout.

The notes recommend learning these algorithms and writing your own solutions as exercise, so real instances are recognisable. In product code, use library queues and locks.

## 4. Dependencies between calls (check-then-act)

Each method being thread-safe does not make a sequence of calls safe. Example (Clean Code app. A): an iterator with synchronised `hasNext()` and `next()`. A client loop `while (it.hasNext()) it.next();` is a check-then-act across two calls: thread 1 sees `hasNext()` true and is preempted; thread 2 takes the last value; thread 1 then calls `next()` past the end and fails. It fails only on the final iteration, rarely, and long after release: "the kind of bug that happens long after a system has been in production." The same applies to `if (!map.containsKey(k)) map.put(k, v)`.

Options, in order of preference:
1. **Avoid needing more than one method** on a shared object. Redesign the interface so the combined step is a single operation (`getNextOrNull()`, `putIfAbsent`). Clean Code calls this a stance, not always feasible.
2. **Server-based locking**: the owner offers one method that takes the lock, does all the calls and releases. Reasons it is preferred: less repeated code, one locking policy in one place, fewer chances for one forgetful caller to break everything, smaller visible scope of shared variables, and the freedom to swap in an unsynchronised server for single-threaded use.
3. **Adapted server**: if you cannot change the owner, wrap it in an intermediary that exposes the combined operation under a lock, or switch to a library type that offers atomic compound operations (an extension of option 2).
4. **Client-based locking**: every client wraps the call sequence in a lock on the server. It duplicates code and depends on every user remembering. The notes tell a war story of an accounting system where one forgetful call site among hundreds of uses caused a rare lockup, found only after weeks of work. Use it when the third-party class cannot be changed and cannot be wrapped, and review every call site.
5. **Tolerate the failure** (client catches the exception and cleans up): sometimes harmless, but the notes call it like rebooting at midnight to clean up memory leaks; not a default.

Rule: when correctness depends on two calls being atomic, make the pair one method on the owner of the state.

Verify: search for lock statements in client code (`synchronized(x)`, `with lock:` around calls to another object) as the smell; write a stress test that runs the compound operation from many threads and asserts the invariant (for example, total items consumed equals items produced, no exceptions).

## 5. Deadlock: scenario and the four conditions

Scenario (Clean Code app. A): two finite pools, say 10 database connections and 10 message-queue connections. One operation acquires them in one order and another in the opposite order. If 10 threads of one kind hold all the database connections and 10 of the other hold all the queue connections, and all are preempted before the second acquisition, everyone waits forever. (The book's labels for which operation takes which order are swapped in its walk-through; the shape is what matters.) Symptoms: a freeze every other week, hard to reproduce; adding debug output changes the timing and "fixes" the problem, so the instrumented code ships and masks the bug.

Deadlock needs all four conditions (the notes' list; break any one and deadlock is impossible):

1. **Mutual exclusion**: resources are limited and cannot be shared (database connection, file open for write, record lock, semaphore).
   - Break: use resources that allow simultaneous use (an atomic variable instead of a lock); raise the resource count to at least the number of competing threads; check that all needed resources are free before seizing any.
   - Limits: most resources are limited and unshareable; the identity of the second resource often depends on the result of the first.
2. **Hold and wait**: a thread holds resources while waiting for others.
   - Break: refuse to wait. Check each resource before seizing; if one is busy, release everything and start over (try-lock with back-off).
   - Side effects: starvation (a thread needing a rare combination never gets it, low CPU use) and livelock (threads acquire and release in lockstep, high but useless CPU use). Inefficient but almost always implementable and "better than nothing".
3. **No preemption**: nobody can take a resource from its holder.
   - Break: when a thread finds a resource busy, ask the owner to release it; an owner that is itself waiting releases everything and restarts.
   - Cost: fewer restarts than option 2, but managing requests is tricky.
4. **Circular wait**: T1 holds R1 and wants R2, T2 holds R2 and wants R1 (a "deadly embrace").
   - Break: a global ordering of resources, with every thread acquiring in that order. The most common approach, often just a convention written in a comment and enforced in review.
   - Costs: the acquisition order may differ from the use order, so a resource is held longer than needed; sometimes no order is possible because the second resource's identity comes from operating on the first.

Fixing the example: make the two operations take the pools in the same fixed order.

No free lunch: each strategy trades efficiency, complexity or fairness. Isolating thread-related code (see `design-principles.md`) lets you experiment with strategies.

## 6. Choosing which condition to break

| Situation | Usual choice | Check |
|---|---|---|
| You control all code that takes the locks and the set of locks is known | Global order (condition 4); document it next to the lock declarations | Review: every function that takes two locks takes them in the documented order |
| The second resource is only known after using the first | Try-lock with release-and-retry (condition 2) with random back-off to limit livelock; or restructure to avoid needing both | Stress test measures retries; no thread starves |
| Resources can be counted and provisioned | Provision at least as many as concurrent users of the pair (condition 1) | Pool sizes configured and asserted at startup (adaptation) |
| Calls out to foreign code or callbacks while locked | Do not hold the lock across the call (condition 2); copy what you need, release, then call | Search for callbacks, listeners or I/O inside lock scope |
| Pool tasks that wait on other tasks of the same pool | Never block a pool thread on another pool task; use a non-blocking continuation or a separate pool | Run the test on a pool of size 1 with a timeout |
| Nested locked sections | Avoid calling one locked section from another | Search for lock-taking functions called from lock scope |

The last-but-one row comes from the parallelism chapter in Functional Programming in Scala: with a fixed-size pool of one thread, an outer task that waits for an inner task submitted to the same pool can never finish, and the notes state that any fixed-size pool can be made to deadlock this way. See `describing-parallel-work.md`.

## 7. Starvation and livelock

- Starvation arises from priority policies (fast threads first, writers waiting for continuous readers) and from retry strategies (condition-2 back-off for a thread needing a rare combination). Symptom: low CPU use with some work never completing. Remedy: fairness policies or bounded retries; verify with a test asserting every submitted job completes within a bound.
- Livelock arises when threads repeatedly acquire and release in step. Symptom: high CPU use with no progress. Remedy: randomised back-off or an ordering rule.

## 8. Diagnosis table

| Symptom | Likely cause | First move |
|---|---|---|
| Totals slightly low, duplicate IDs, counters off | Lost update from non-atomic read-modify-write | Find the read-modify-write; use an atomic or lock; write a stress test asserting the total |
| Exception on the last element or at an edge, rare | Check-then-act across two calls | Merge the pair into one operation on the owner |
| Freeze, no CPU | Deadlock | Dump all thread stacks; find the cycle; apply the four-condition table |
| Freeze, high CPU | Livelock or spin | Look at retry loops; add randomised back-off |
| Some jobs never run, others fine | Starvation | Check priority policy and fairness |
| Passes with logging on, fails without | Timing-sensitive race (an observation effect) | Observe by a second independent means (stress under a race detector); see `testing-concurrent-code.md` |
| Only fails on one platform | Scheduling policy differs per platform | Run on every target platform early |
| Hang in tests only on small pools | Pool-thread blocking on pool work | Test with a pool of one |
