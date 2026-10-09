# Testing concurrent code

Sources: Clean Code ch. 13 (seven rules) and app. A (Monte Carlo, instrumentation); Why Programs Fail ch. 4 (schedules, Heisenbugs, record and replay). Items marked (adaptation) or (inferred) go beyond the notes.

## Contents
1. Ground rules
2. The seven rules
3. A test that proves a race exists
4. Making failures likely: Monte Carlo, perturbation, instrumentation
5. Reproducing a schedule-dependent failure
6. Heisenbugs and observation effects
7. Controlling other nondeterminism: time, randomness
8. Test design recipe
9. Evidence to report

## 1. Ground rules

- You cannot prove concurrent code correct by testing. Good tests reduce risk. Write tests that can expose problems; run them often, with varied programmatic configurations, system configurations and load.
- Investigate every failure, even when the next run passes. Assume one-offs (a cosmic ray, a glitch) do not exist. Physical causes are real but extremely rare; consider them only when all alternatives are proven irrelevant (Why Programs Fail ch. 4). Ignoring rare failures lets more code accumulate on a faulty approach.
- Concurrency bugs are rarely repeatable, so they are dismissed as one-offs. Count them as defects.

## 2. The seven rules (Clean Code ch. 13)

1. **Treat spurious failures as candidate threading issues.** Bugs may show once in a thousand or million runs.
2. **Get non-threaded code working first.** Put logic in thread-ignorant units that the threads call and test them outside threads. Do not chase threading bugs and non-threading bugs at once.
3. **Make threaded code pluggable.** Allow one thread, several, varied during execution; real versus test-double collaborators; doubles that are fast, slow and variable; tests configurable for number of iterations.
4. **Make threaded code tunable.** The right thread count comes from trial and error. Time the system under configurations; make the count easy to change, perhaps at run time, perhaps self-tuning on throughput and utilisation.
5. **Run with more threads than processors.** Frequent task switching exposes missing critical sections and deadlocks.
6. **Run on different platforms.** The authors saw a failure-demonstrating test fail less on a Windows virtual machine than on OS X; threading policy differs per operating system. Run on every target platform early and often.
7. **Instrument code to force failures.** Failing paths are a tiny fraction of paths, so the chance of hitting one is low. Insert calls that perturb scheduling (sleep, yield, wait, priority changes).

## 3. A test that proves a race exists

Pattern from Clean Code app. A, with a trivial counter class `takeNextId() { return nextId++; }`:

1. Record the start value.
2. Run two threads that each call the method once; start both, then join both.
3. Expect the end value to be start + 2.
4. Repeat until the observed result differs. If it differs, the bug is proven (that is the pass condition for a "this class is broken" demonstration). If the loop finishes without difference, fail with a message saying the test did not expose the issue.

Lesson: the failure was rare. At a million iterations the bug appeared in only about 1 of 10 runs; reliable failure took over a hundred million iterations, and the number differed across machines, operating systems and runtime versions. If a trivial bug is that hard to catch, harder ones are worse, so do not rely on iteration count alone; use perturbation (section 4).

For a fix: write the test first, watch it fail against the unfixed code (using perturbation so it fails quickly), then make it pass, then run it repeatedly.

Sketch (adaptation, Python):

```python
def hammer(make, op, check, threads=16, iters=2000, rounds=200):
    for r in range(rounds):
        obj = make()
        def work():
            for _ in range(iters): op(obj)
        ts = [Thread(target=work) for _ in range(threads)]
        for t in ts: t.start()
        for t in ts: t.join(timeout=30)
        assert not any(t.is_alive() for t in ts), "possible deadlock"
        check(obj, threads * iters)     # invariant, e.g. counter == total
```

Needs `from threading import Thread`. Caveat found by running it (CPython 3.14, GIL build): against a counter whose `inc` is `self.n += 1` or read-then-write with no call in between, this loop reported no lost updates in 20 rounds, even with `sys.setswitchinterval(1e-6)`. The interpreter switches threads only at certain points, so the unfixed code looked correct. With `time.sleep(0)` placed between the read and the write, the same loop failed immediately. So in Python a green hammer run is weak evidence unless the test has first been seen to fail on a deliberately racy version, which is exactly the "prove the test can fail" rule in SKILL.md. Free-threaded builds (3.13+) and other languages behave differently; check by the same experiment.

## 4. Making failures likely

### Monte Carlo testing
Write tests with tunable parameters (thread count, iteration counts, sleeps and load). Run them repeatedly on a CI server with randomly varied parameters. Any failure means the code is broken. Start early so CI runs them. Log the exact conditions of each failure so it can be reproduced. Run on every target deployment platform and under varying machine load, simulating production load where possible. Longer without failure means either the code is correct or the tests are inadequate; you cannot distinguish the two from the passes alone.

### Schedule perturbation (jiggling)
- Hand-coded: insert a yield or sleep inside a critical-looking region between a read and an update. If the test then fails, the code was already broken; the yield only exposed it. Weaknesses: you must guess where, it costs production speed if left in, and it is shotgun.
- Automated: a no-op hook (`jiggle()`) at candidate points whose production implementation is empty and whose test implementation randomly does nothing, sleeps or yields. Run the test about a thousand times with random jiggling; passing means at least due diligence. Splitting code into thread-ignorant units and thread-control classes makes the instrumentation points easy to find.
- Tool-assisted: the notes describe an IBM instrumentation tool that perturbs scheduling; failure rate on the book's example went from about 1 per 10 million iterations to about 1 per 30. It is dated; the transferable idea is schedule perturbation.

Modern equivalents (adaptation): Go `-race`; ThreadSanitizer for C, C++ and Rust; `jcstress` and Lincheck for the JVM; deterministic-schedule model checkers where available (for instance `loom` for Rust); randomised stress with pool size less than thread count; timeouts on every test.

### Other levers
- More threads than cores (rule 5).
- Slow and fast test doubles for collaborators (rule 3).
- Small pools (size one and two) for code that submits tasks which wait on other tasks.
- Varying machine load by running other work at the same time.

## 5. Reproducing a schedule-dependent failure

From Why Programs Fail ch. 4: execution is code plus input; to reproduce a run you must observe and control all input. The thread or process schedule is one of the inputs, along with data, user interaction, communications, time, randomness and the operating environment. With the input fully controlled the run is deterministic; otherwise it is nondeterministic and the problem appears or not regardless of your will.

The general pattern is a control layer between the real input sources and the program, with a capture mode (record what comes back from the real source) and a replay mode (return the recorded value).

For schedules:
- Treat the schedule as an input; record and replay it. Costs: data volume and performance impact. Recording one program's thread schedule is feasible; recording a whole set of communicating processes including OS scheduling is still hard (as of the book).
- Complementary detection: program analysis that verifies all shared-variable accesses are synchronised, and massive random testing.
- Practical approach (adaptation): make the concurrency policy pluggable (see `design-principles.md`) and swap in a deterministic scheduler in tests, for example an inline scheduler that runs jobs in a fixed order you choose, or a test-controlled executor you step by hand. Use this to write one deterministic test for each interleaving you can name (reader sees half-updated state; second thread runs between check and act).
- When the failure occurred in a report, write down the failure rate you observe under stress, and use the same stress configuration to confirm the fix (inferred: report the rate before and after, not one pass).

## 6. Heisenbugs and observation effects

- A Heisenbug disappears or changes when probed. Adding logging, running under a debugger or recompiling changes timing. The book's debugging-environment example is uninitialised memory in C; in memory-safe languages the usual cause is timing.
- Instrumenting a deadlock with debug output can "fix" it by changing timing, and the instrumented code then ships and masks the bug (Clean Code app. A).
- Capture tools with high data volume change the program's performance and can mask the problem (Why Programs Fail ch. 4).
- Rule: when you suspect a Heisenbug, observe the program by at least two independent means (for example stress test under a race detector and a thread-dump taken during a hang).
- When a bug vanishes after an unrelated change, compare builds and toolchain, not only source (the book's print-statement story).

## 7. Controlling other nondeterminism

- Time: make the clock an input (inject a clock) so tests can run under any time and advance it by hand. Do not change the system clock between runs. Tests for timeouts and retries become deterministic.
- Randomness: capture and replay the seed; allow tests to swap in a deterministic source; be cautious about letting end users disable randomness in security contexts.
- Record the seed and thread count of every stress run so a failure can be replayed.

## 8. Test design recipe

1. Unit-test the thread-ignorant logic with no threads (rule 2).
2. For each piece of shared state, write an invariant ("total equals sum of increments", "no item delivered twice", "queue never exceeds capacity", "every submitted job completes").
3. Write the hammer test: N threads (more than cores), M iterations, check the invariant after join, with a timeout.
4. Add perturbation hooks or run under a race detector.
5. Run the hammer in a loop with random parameters (Monte Carlo) in CI; log parameters on failure.
6. Add deterministic tests for known interleavings via a controllable scheduler.
7. Add shutdown tests: request stop with work in flight; assert all workers exit within a timeout.
8. Add a small-pool test (size one) for any code that submits tasks which wait on other tasks.
9. Run on each target platform; keep the failing seeds as regression tests.

## 9. Evidence to report

- the invariants asserted and how many runs (rounds, threads, iterations);
- whether the test was seen to fail on the unfixed code, and with which perturbation;
- whether a race detector ran and its result;
- failures seen, with parameters, and what was done about each;
- platforms or runtimes covered;
- what is not covered (for example, "not run under high machine load").
