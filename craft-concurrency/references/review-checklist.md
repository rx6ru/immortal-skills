# Review checklist for concurrent code

Use for a diff or a design that touches threads, tasks, locks, queues, atomics or shutdown. Each item has an observable answer; record the answer in your review rather than "ok". Item sources are the Clean Code concurrency chapter and appendix unless stated.

## Contents
1. Is it needed
2. Structure and separation
3. Shared state
4. Compound operations
5. Locking and deadlock
6. Resources and bounds
7. Ordering and initialisation
8. Shutdown
9. Tests
10. Red-flag searches

## 1. Is it needed
1. Is there a stated reason (a measured I/O wait, a design decoupling)? Observable: a timing test, or a sentence in the PR.
2. Is the time I/O-bound or CPU-bound, and does the mechanism match? Observable: pool size and kind fit the answer (threads beyond cores do not speed CPU-bound work).
3. Could the same result come from restructuring (batching, fewer round-trips, an algorithm change)? Observable: the alternative considered and dismissed with a reason.

## 2. Structure and separation
4. Where are threads or tasks created, bounded and stopped? Observable: one named class or module; no thread creation scattered in logic.
5. Does the business logic run without any thread in a test? Observable: a test that calls it directly.
6. Does the code managing threads do anything else? Observable: no connection handling, parsing or shutdown policy inside the thread-management class beyond scheduling.
7. Is the worker count configurable? Observable: a parameter, not a literal.

## 3. Shared state
8. List every piece of shared mutable state. Observable: the list in the review, with the guard for each (lock name, atomic, owner task, or "immutable").
9. For each, could it be removed: not shared, immutable, copied, owned by one task? Observable: reason given if not.
10. Is access to each confined to one small class? Observable: no other module reads or writes the fields.
11. Are module-level or static mutable variables and singletons with mutable data present? Observable: grep result.
12. Are standard thread-safe types used where they exist, rather than hand-written wait/notify? And any non-thread-safe types (formatters, connections, ordinary containers, handlers) shared across threads? Observable: types named.

## 4. Compound operations
13. Any check-then-act (`contains` then `put`, `hasNext` then `next`, `if not exists then create`, read-modify-write)? Observable: each is a single operation on the owner, or under one lock.
14. Any increment, `+=` or 64-bit read/write assumed atomic? Observable: atomic type or lock is used.
15. In async code, is there an `await` between the check and the act on the same state? Observable: none, or the state is guarded across the await (adaptation).
16. Is client-based locking present (callers taking the lock of another object)? Observable: a grep for lock statements in callers; if present, justification (third-party class that cannot be wrapped) and every call site reviewed.

## 5. Locking and deadlock
17. Which locks exist and in what order are they taken when more than one is needed? Observable: order documented where declared; every multi-lock function follows it.
18. Is a lock held while calling foreign code, callbacks, listeners or doing I/O? Observable: none, or the design requires it and is noted.
19. Is one locked section called from another? Observable: none, or re-entrancy is deliberate.
20. Are critical sections only the shared-state operation? Observable: no computation or logging not needed for correctness in lock scope.
21. Which of the four deadlock conditions is broken for each multi-resource path? Observable: named (global order, try-lock with release, count provisioned, preemption).
22. Do pool tasks block on other tasks of the same pool? Observable: none, or test on pool size one passes.

## 6. Resources and bounds
23. Is there any unbounded creation of threads, tasks or queue entries? Observable: bounded pool, concurrency limit or bounded queue; policy when full is explicit.
24. Are bounded resources (connections, buffers) acquired in a consistent order and released on all paths? Observable: release in finally/defer/context manager.
25. Starvation: can a low-priority or rare-combination job wait forever? Observable: a test or argument that every submitted job completes in a bound.

## 7. Ordering and initialisation
26. Is any method order required ("call init first")? Observable: object is valid after construction, or types encode the order (`temporal-coupling-and-workflow.md`).
27. Are there calls that must be paired but are two separate public steps? Observable: merged or protected.
28. Does the serial order of steps reflect real dependencies? Observable: dependencies named for each serial edge (workflow analysis).

## 8. Shutdown
29. How does each worker learn to stop, and who waits? Observable: cancellation token, poison pill, closed channel or deadline; a join with timeout.
30. Can a producer stop while a consumer waits forever, or a parent wait on a stuck child? Observable: test that stops mid-stream and finishes within a timeout.
31. What happens to in-flight work? Observable: documented drain or abandon policy.

## 9. Tests
32. Logic tests with no threads? Observable: yes/no.
33. Stress test with more threads than cores, many iterations, an invariant check, and a timeout? Observable: parameters and run count.
34. Did a bug-fix test fail before the fix? Observable: the failing run shown.
35. Race detector or sanitizer run? Observable: command and result (Go `-race`, ThreadSanitizer, `jcstress`; adaptation).
36. Pool size one test where tasks wait on tasks? Observable: result.
37. Any known flaky test in this area being re-run until green? Observable: none; a failure was treated as a candidate race and investigated.
38. Test failures log their parameters (seed, thread count)? Observable: yes/no.

## 10. Red-flag searches (inferred, quick to run)
- Lock statements in caller code: `synchronized (` on objects owned elsewhere, `with other.lock:`.
- Sleep calls used to "wait for the other thread" in production code.
- Thread or task creation inside loops handling requests.
- `catch`/`except` blocks around a racy call that ignore the error.
- Mutable globals, class-level dicts or lists, singletons with setters.
- Blocking calls (`get()`, `.result()`, `join`, `block_on`, sync I/O) inside async functions or inside pool tasks.
- Lock acquisition in more than one order across files.
- `TODO: thread safety`, "not thread safe" comments next to shared use.

## Verdict format
Report: items failed (number and fix), items not applicable (why), and the test evidence (section 9). If any of items 8, 13, 17, 23 or 29 cannot be answered from the code, the change is not ready.
