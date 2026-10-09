---
name: craft-concurrency
description: "Procedures and checklists for writing, reviewing and testing concurrent code inside one program (threads, thread pools, async tasks, actors, channels, locks, atomics): when concurrency is worth adding, keeping thread policy apart from logic, shrinking shared mutable state, choosing a locking approach, preventing deadlock, removing temporal coupling, describing parallel work as values, and testing nondeterministic code. Use when a user asks to parallelise or speed up something, add threads or async, fix a race, flaky test, hang or deadlock, review code that shares state across threads or tasks, or design a worker pool, queue or shutdown path. Not for distributed-system consistency or database isolation (see arch-replication-and-consistency, arch-transactions)."
---

# Craft: concurrency inside a program

## Purpose

Concurrency bugs live on rare execution paths, so intuition and a single green test run prove little. Use this skill to decide whether concurrency is justified at all, to shape the code so that very little of it is concurrency-aware, to pick the cheapest safe mechanism, and to test with deliberate schedule pressure instead of hope. The aim is a small, isolated, tested concurrent core, not a clever one.

## Choose what applies

| Situation in front of you | Do this | Read |
|---|---|---|
| "Make it faster / parallelise it" | Find out whether time goes to waiting (I/O) or computing (CPU) before touching code; then step 1 below | `references/design-principles.md` (section 1) |
| New code that must run work concurrently | Steps 1 to 6 below; keep the concurrent part as a thin shell around plain logic | `references/design-principles.md`, `references/choosing-a-mechanism.md` |
| Existing shared mutable state, counters, caches, maps | Reduce it first (immutability, copies, partitioning), then guard what remains | `references/design-principles.md` (section 3), `references/hazards-and-deadlock.md` (section 4) |
| Two calls on a shared object must go together (check-then-act, `hasNext`/`next`, `contains`/`put`) | Make the pair one operation on the owner of the state | `references/hazards-and-deadlock.md` (section 4) |
| Hang, freeze, "stuck every few weeks", pool exhaustion | Treat as deadlock or starvation; identify which of four conditions holds and break one | `references/hazards-and-deadlock.md` (sections 5 and 6) |
| Flaky test, "passes on rerun", lost updates, wrong totals | Assume a race until shown otherwise; reproduce under schedule pressure | `references/testing-concurrent-code.md` |
| Code with "call A before B", `init()` after constructor, hidden global state, serial steps with no real dependency | Temporal coupling: fix ordering and state validity, then look for real parallelism | `references/temporal-coupling-and-workflow.md` |
| Choosing between threads, pool, async/await, actors, channels, atomics, locks | Use the chooser | `references/choosing-a-mechanism.md` |
| Designing a library or internal API for composable async or parallel work (futures, tasks, `map2`, `fork`) | Describe work as values, run it in one place, state laws | `references/describing-parallel-work.md` |
| Reviewing a diff that touches threads, locks, queues, tasks or shutdown | Run the checklist | `references/review-checklist.md` |
| Producer-consumer, readers-writers, dining-philosophers shapes | Recognise the shape, then use the known remedies | `references/hazards-and-deadlock.md` (section 3) |
| Distributed consensus, replication lag, database isolation levels, saga coordination | Does not apply; this skill covers one program's memory and schedule | `arch-replication-and-consistency`, `arch-transactions` |
| Single-threaded script or request handler with no shared state and no performance problem | Does not apply; adding concurrency here is cost without gain | none |
| Plain debugging with no concurrency suspicion | Does not apply | `craft-debugging` |

## How to apply

Work through these in order. Stop as soon as the problem is solved; most tasks need only steps 1 to 3.

1. **Justify the concurrency.** Concurrency decouples what is done from when. It helps throughput only when there is wait time that another task can use (I/O, remote calls), and it costs extra code and extra failure modes. Measure first: write or find a timing test with a stated budget, and note whether the time is I/O wait or CPU work. If CPU-bound on one core, more threads on the same core will not help; a better algorithm or more cores will. If nothing is slow and no design reason exists (independent activities, responsiveness), do not add it.
   - Arithmetic template for the benefit: if reading takes 1 s of waiting and parsing takes 0.5 s of CPU, one worker spends 1.5 s per item; three workers overlap the reads with the parses and approach 2 items per second, about 3x in the idealised case. This holds only if items can be handled in any order and independently. Do this calculation before building.
2. **Keep thread policy in one place.** The code that creates, schedules, bounds and stops threads or tasks should do nothing else. Put the business logic in plain, thread-ignorant functions or classes that the concurrent shell calls. Hide the policy behind a small interface (for example `schedule(job)`), so switching from thread-per-request to a bounded pool, or to async tasks, touches one class. Why: concurrency problems are hard enough without also untangling non-concurrency problems, and thread-free logic can be tested without threads.
3. **Shrink shared mutable state, in this order of preference.**
   1. Do not share: give each task its own inputs in parameters and locals, each handling an independent partition of the data.
   2. Share immutable data.
   3. Copy: give each task a read-only copy, or let each build its own result and merge in one place. Copying often costs less than locking; measure instead of assuming.
   4. Pass messages (queue, channel, actor mailbox) so one owner mutates the state.
   5. Guard what is left with the smallest lock scope or a single atomic. Keep every access to that state in one small class.
4. **Use the platform's concurrent building blocks.** Prefer provided thread-safe queues, maps with atomic compound operations, atomics, executors and channels over hand-written wait/notify. Know that many standard types are not thread-safe, and that individually safe methods do not make a sequence of calls safe. Mechanism chooser in `references/choosing-a-mechanism.md`.
5. **Make compound operations atomic on the owner.** If correctness needs two calls together, create one method on the state's owner that does both under the lock (server-based locking). Client-based locking (every caller takes the lock) breaks as soon as one caller forgets, and the code ends up duplicated. If you cannot change the owner, wrap it in an adapter that exposes the combined operation.
6. **Prevent deadlock by design.** When code needs more than one lock or bounded resource, break one of the four conditions: mutual exclusion, hold-and-wait, no preemption, circular wait. The usual choice is a global acquisition order, written down. Keep critical sections small, and do not call unknown code or do I/O while holding a lock unless the design needs it. Details and trade-offs in `references/hazards-and-deadlock.md`.
7. **Design the shutdown path now.** Decide how workers learn to stop (cancellation token, poison pill, closed channel, timeout), who waits for whom, and what happens to in-flight work. Shutdown is where parents wait on deadlocked children and producers stop while consumers block forever; getting it working early costs less than it takes later.
8. **Make thread count and scheduling configurable.** Pool size, number of workers, and iteration counts should be parameters so tests can vary them and tuning needs no code change.

### Decision rules used most

| Question | Rule | Why |
|---|---|---|
| Add a lock or restructure? | Restructure (don't share, copy, immutability, ownership) when you can; lock when the state is truly shared and small | Every lock is a place that can be forgotten, ordered wrongly or held too long |
| Atomic or lock? | Atomic for one variable's update; lock for an invariant across several variables | A compare-and-swap loop cannot protect an invariant spanning two fields |
| Big critical section "to be safe"? | No. Guard exactly the shared-state operation | Larger sections raise contention and hurt throughput; the notes give no measured threshold, so measure |
| Unbounded task or thread creation per request? | Use a bounded pool or concurrency limit | Unbounded creation can exhaust the runtime under load |
| Catch the exception from a racy call and move on? | Treat as a last resort | It leaves the race in place and hides it; the notes call it sloppy |
| A failure appeared once and vanished | Treat as a candidate threading bug and investigate | Races can show one run in a thousand or a million; dismissing them lets more code build on a bad base |
| Must call X before Y, or `init()` after construction | Redesign so the object is valid whenever it can be called | A second thread can call in the gap |

### Worked example: "fetch these 200 pages faster"

1. Measure: one fetch is mostly network wait, and parsing is cheap. I/O-bound, so concurrency can help. State the budget (for example, all 200 within N seconds) and record the current time.
2. Separate: `parse(page)` and `summarise(results)` stay plain functions. A small `fetch_all(urls, scheduler)` is the only concurrent code.
3. Share nothing: each task gets its own URL and returns its own result; the main flow merges results after all finish. The only hand-off is "next URL", via a queue or by partitioning the list in advance.
4. Bound: a pool or concurrency limit (configurable, started small, tuned by measurement) instead of 200 simultaneous tasks.
5. Compound steps: no shared cache with check-then-insert; if one is needed, use the map's atomic put-if-absent or give a single owner task.
6. Stop: a failing fetch must not leave the others hanging; decide whether to cancel the rest, and how errors reach the caller.
7. Verify: tests for `parse` and `summarise` without threads; a stress test with a fake slow fetcher (random delays), more workers than cores, repeated runs, a timeout; compare timing against the step 1 budget.

### Symptom to first move

| Symptom | First move | Detail |
|---|---|---|
| Counts or totals slightly wrong under load | Look for read-modify-write on shared state | `hazards-and-deadlock.md` section 2 |
| Rare exception at a boundary (last item, empty queue) | Look for check-then-act across calls | `hazards-and-deadlock.md` section 4 |
| Process freezes with no CPU | Dump all thread stacks and find the cycle | `hazards-and-deadlock.md` section 5 |
| Process spins with no progress | Look for retry loops in lockstep | `hazards-and-deadlock.md` section 7 |
| Test passes locally, fails in CI, or passes on rerun | Treat as a race; stress and perturb | `testing-concurrent-code.md` |
| Bug disappears when logging is added | Timing-sensitive; observe by a second means | `testing-concurrent-code.md` section 6 |
| Tasks that wait for tasks hang on a small pool | Never block a pool thread on pool work | `describing-parallel-work.md` section 4 |

### Common mistakes to avoid

- Fixing the symptom with a sleep or a retry; it moves the failure to a rarer schedule rather than removing it.
- Making every method of a class synchronised and calling it done; callers' multi-call sequences stay racy.
- Putting the lock in the caller because it is the quick edit; the next caller forgets it.
- Declaring a single green run proof; report repeated runs.
- Leaving instrumentation (debug output, yields) in the fix, which can mask the bug or cost speed.
- Adding threads to CPU-bound work on one core.

## Verify

Concurrency cannot be proven correct by testing; the goal is to make failures likely to show up before production. Do these and show the evidence.

1. **Logic tested without threads.** Show that the thread-ignorant core has ordinary tests that run with no threads or tasks started. If it cannot be tested that way, the separation in step 2 has not happened.
2. **Stress test with schedule pressure.** Write a test that runs the concurrent code with more workers than CPU cores, many iterations, and perturbation (random sleeps or yields at candidate points, or a race detector / sanitizer). Run it repeatedly, for instance 1000 times in a loop, and report the failure count, not one pass. The book's own example of a trivial lost-update bug failed in only about 1 of 10 runs at a million iterations, so a single run proves nothing. In CPython a plain hammer loop did not expose a read-then-write counter race at all until a yield was placed between the read and the write (see `references/testing-concurrent-code.md` section 3), so a stress test that has never failed on a known-racy version is not evidence.
3. **Prove the test can fail.** For a race you are fixing, first show the test failing against the unfixed code (or with a deliberately injected yield between read and write). A test that has never failed has not demonstrated that it can detect the bug.
4. **Race detector or sanitizer where the ecosystem has one**, as a gate in CI (adaptation: Go `-race`, ThreadSanitizer for C/C++/Rust, `jcstress`/Lincheck for JVM). Report that it ran and what it said.
5. **Hangs fail fast.** Every concurrent test has a timeout so a deadlock is a failing test, not a stuck job. Try pool size 1 (and 2) for any code that submits tasks which wait for other tasks; the fixed-size pool of one is the cheapest deadlock probe.
6. **Configuration sweep.** Run with one worker, several, and many; with fast and slow collaborators; on each target platform or runtime if feasible. Log the exact parameters of any failure so it can be replayed.
7. **Static checks you can do by search.** Search for synchronisation blocks in client code (client-based locking smell); for shared module-level mutable variables; for locks acquired in more than one order; for unbounded executors; for blocking calls inside async code or inside pool tasks that wait on other pool tasks.
8. **Review with the checklist** in `references/review-checklist.md` and state the answers, not "looks fine".

Done means:
- the reason for concurrency is stated with a measurement or a design reason;
- thread policy lives in one named place, and the logic beneath it runs without threads in tests;
- every piece of shared mutable state is listed, with its guard or the reason it needs none;
- each multi-call protocol on shared state is a single operation on the owner;
- lock order (or the broken deadlock condition) is documented where the locks are taken;
- the shutdown path exists and has a test;
- the stress test failed before the fix (for a bug) and passes N repeated runs with N reported;
- no failure was explained away as a one-off.

## Proportion and limits

- A tiny script or a request handler with no shared state does not need this apparatus. Apply steps 1 and 2 as questions and stop.
- Do not hand-roll lock-free structures, custom thread pools or wait/notify protocols when a library type exists. The book's advice to hand-write solutions to the classic problems is for learning to recognise them; in product code use the library.
- Source material is Java-5 era (2008). The specific classes and tools it names (executors, `ConcurrentHashMap`, ConTest) are dated, but its principles (isolate, minimise sharing, atomic compound operations, break one deadlock condition, test under perturbation) carry over. Newer styles such as async/await, actors, channels, structured concurrency and virtual threads push further toward not sharing state at all; `references/choosing-a-mechanism.md` maps the ideas, flagged as adaptation.
- Claims such as "small critical sections are better", "atomics nearly always beat locks" and "copies are cheaper than locks" are stated in the notes without measurements, and the authors tell the reader to experiment. Treat them as defaults to test, particularly under heavy contention on a single location or when an invariant spans several variables.
- "Avoid using more than one method on a shared object" is a stance, not always achievable. The fallback is server-based locking or an adapter.
- Hand-inserted yields are a weak instrument (you must guess where, and they cost speed if left in); the automated version (a no-op hook in production, random delay in tests) is better but still simplistic. Even with all measures, a failure with a one-in-a-billion cross-section can survive.
- Code in the source listings has typos (an inverted `putIfAbsent` condition, a missing `return`); take the ideas, not the listings.

## References

- `references/design-principles.md`: read first for any new concurrent design; why/when to add concurrency, separation of thread policy, limiting data, copies, independence, the client/server refactoring, throughput arithmetic.
- `references/hazards-and-deadlock.md`: read when diagnosing a race, hang or starvation, or when a design takes more than one lock; vocabulary, the three classic problems, interleaving arithmetic, atomicity traps, the four deadlock conditions and what breaking each costs.
- `references/choosing-a-mechanism.md`: read when picking between threads, pools, async/await, actors, channels, atomics and locks, or translating the advice to a given language (adaptation, flagged as such).
- `references/temporal-coupling-and-workflow.md`: read when code depends on call order, hidden state or serial habit; finding real parallelism in a workflow; work queues and the hungry-consumer model; blackboard coordination.
- `references/describing-parallel-work.md`: read when designing a composable async or parallel API: describe-then-run, fork as the only scheduling primitive, laws, the bounded-pool deadlock, generalising combinators.
- `references/testing-concurrent-code.md`: read before writing or fixing tests for threaded code, including the reproduction tactics for schedule-dependent failures and flaky tests.
- `references/review-checklist.md`: read when reviewing a diff or finishing your own; a numbered list with observable answers.

## Sources

- Clean Code (Martin, 2008) ch. 13 "Concurrency" and appendix A "Concurrency II" (Schuchert): defence principles, execution models, synchronisation rules, deadlock conditions, testing rules, client/server and throughput examples.
- The Pragmatic Programmer (Hunt and Thomas, 1999) ch. 5 sections "Temporal Coupling" and "Blackboards" (tips 39 to 41 and 43): workflow analysis, services and the hungry consumer, designing for concurrency.
- Clean Code ch. 17, heuristic G31 (hidden temporal coupling), used in `references/temporal-coupling-and-workflow.md`.
- Functional Programming in Scala (Chiusano and Bjarnason, 2015) ch. 7 "Purely functional parallelism": describing parallel computation as a value, fork as the scheduling primitive, laws, the fixed-pool deadlock.
- Why Programs Fail (Zeller, 2009) ch. 4 "Reproducing Problems": schedules as an input, lost-update example, record and replay, Heisenbugs and observation effects.
