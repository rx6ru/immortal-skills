# Hard cases: nondeterminism, concurrency, Heisenbugs, memory errors, regressions

Sources: WPF ch. 4.3 (inputs, schedules, debugging tools), ch. 10.8 (system assertions), ch. 13 (schedules, changes), ch. 14.7, ch. 1; PP ch. 3 "Debugging". Concurrency design and testing are covered by the sibling `craft-concurrency`; this file covers how to debug.

## Contents
1. Nondeterministic failures: the general approach
2. Jargon for what you are facing
3. Schedule-dependent failures (races)
4. Failures that vanish when observed (Heisenbugs)
5. Memory errors and undefined behaviour
6. Time, randomness and environment dependence
7. Regressions (it worked before)
8. Long-running or field failures you cannot reproduce
9. Crashes far from their cause
10. "It must be the compiler, OS, library"
11. Verify

## 1. Nondeterministic failures: the general approach

A run is deterministic if you control all its input; otherwise the failure appears regardless of your wishes. So the first move is to find the uncontrolled input and bring it under control (`reproduce.md` section 4): threads and scheduling, time, randomness, network, environment, hardware, and your own observation tools.

1. Measure first: run the failing test N times and record the failure rate. A rate gives you a test for any later change (adaptation).
2. List the uncontrolled inputs. Pin them one at a time and see which pinning makes the failure deterministic. The one that does is relevant (adaptation of the narrowing procedure in WPF ch. 4.3).
3. Where you cannot pin an input, record it and replay it (seed, schedule, message log, clock).
4. Raise the failure rate before you debug: more load, more threads, smaller timeouts, repeated loops, stress options. A failure that happens 1 in 1,000 runs cannot be bisected; one that happens 1 in 3 can (adaptation).
5. Use record-and-replay or a reverse debugger to capture one failing execution and then explore it freely (`observe-and-trace.md`).
6. Use a passing and a failing recorded run as the two worlds for isolation (`simplify-and-isolate.md`).

Do not blame cosmic rays and walk away. Physical bit flips are real but extremely rare; consider them only when all other alternatives are proven irrelevant and the influence can be demonstrated (WPF ch. 4.3.8).

## 2. Jargon for what you are facing

| Term | Meaning |
|---|---|
| Bohr bug | Repeatable under a possibly unknown but well-defined set of conditions |
| Heisenbug | Disappears or changes when you probe it |
| Mandelbug | Causes so complex it looks chaotic or nondeterministic (the speaker believes it is really a Bohr bug) |
| Schroedinbug | Shows up only when someone notices it never should have worked; then stops working for everyone |

The practical lesson: most "random" failures are Bohr bugs with an input you have not yet identified.

## 3. Schedule-dependent failures (races)

A correct program behaves identically under any schedule. Failures that depend on thread or process scheduling are among the worst to face (WPF ch. 4.3.7).

Pattern from the book: two parallel invocations of a password-file utility each read the file, modify, and write back. If both read before either writes, the last writer wins and the other update is lost. The same shape applies to any read-modify-write on a shared resource: lock it, or record the last-update time when reading and recheck it before writing, re-reading if it changed.

How to find and pin one:
1. Treat the schedule as an input: record and replay it (deterministic replay tools; at the program level, controlled yield points, a test scheduler, or a sleep injected at the suspect point to widen the window as a quick probe (adaptation)).
2. Generate alternative schedules (random perturbation) until one passes. You now have a failing and a passing schedule.
3. Apply dd to the difference between them: the book's ray tracer example had about 3.8 billion single "move a switch by one yield point" differences and isolated in about 50 tests that the failure happens iff one thread switch occurs just after the read of a shared counter rather than just before it, which was exactly where the race had been introduced. When every outcome is PASS or FAIL, dd is logarithmic.
4. Relate the isolated switch to a program location and find the unsynchronised read-modify-write.
5. Complement with analysis: verify that all shared-variable accesses are synchronised (static), run a thread sanitizer or race detector (adaptation), and run massive random or stress tests.

Caveat: the book's example is artificial; recording one program's schedule is feasible, recording a set of communicating processes and OS scheduling is still hard. The principle holds for any recordable nondeterminism: seeds, timing, event order.

Verification for a race fix (adaptation): the failure rate under the stress setup that previously failed is zero over a count that would have failed with high probability before (state the number of runs), the race detector is clean, and a test with the forced bad interleaving passes.

## 4. Failures that vanish when observed (Heisenbugs)

Observation can change behaviour. Causes (WPF ch. 4.3.9, ch. 8): timing changes from logging, flushing or debugger pauses; differences between the debugging and production environment combined with undefined behaviour; recompilation for debugging exposing toolchain differences; buggy tools.

Rules:
- Whenever you suspect a Heisenbug, observe the program by at least two independent means.
- Look for undefined behaviour: uninitialised variables, out of bounds access, use after free (section 5). The book's example: a function returning an uninitialised local returns 0 standalone (the OS gives zeroed memory) but leftovers under a debugger.
- When a bug vanishes after an unrelated change, diff the executables and toolchain, not only the source. The book's story: adding a print statement made the bug vanish and removing it did not bring it back, because the print forced a different linker, and the original linker had a bug that resolved a symbol to a bad address.
- Prefer observation with low perturbation: buffered or off-thread logging, a ring buffer dumped on failure, record and replay, post-mortem inspection of a core dump or crash report.
- Capture and replay tools themselves can change timing enough to mask a race (WPF ch. 4.3.3).

Languages with defined semantics (Java, C#, and in general memory-safe languages) remove the undefined-behaviour class but still have timing, ordering, floating point, locale and environment dependences.

## 5. Memory errors and undefined behaviour

In C, C++ and unsafe Rust, memory errors are time bombs: use after free, double free and overflow fail millions of instructions later, far from the cause. WPF ch. 10.8: apply memory checkers first, before reasoning about values, at the slightest suspicion. Tool classes: allocator self-checks, guard-page allocators (an overrun faults at once, giving a core file or debugger stop at the faulting access), shadow-memory checkers (flag reads of uninitialised memory and accesses outside allocated blocks, and report where the block was allocated), instrumenting compilers. Modern analogues (adaptation): AddressSanitizer, MemorySanitizer, UndefinedBehaviorSanitizer, ThreadSanitizer, Valgrind, Miri.

Corrupted variable? Look at its neighbourhood (PP): if an integer holds a huge value like `0x6e69614d`, dump the surrounding memory as characters; a string sprayed over the counter points to the writer. A hardware or software watchpoint on the corrupted location stops at the writer (`observe-and-trace.md` section 5).

Safer dialects and language features make whole classes impossible (non-null types, bounds-checked arrays, region analysis); consider the language feature as part of the fix (`prevent-recurrence.md`).

## 6. Time, randomness and environment dependence

- Make time a parameter. Date-dependent symptoms often hide buffer or format defects ("works only on Wednesdays": the weekday string needed more room than the buffer had). Test with all values of the time input, including leap days, month ends, zone changes (the last as adaptation).
- Capture and replay the seed; make it injectable.
- Environment differences: power source, memory, locale, case-sensitive filenames, path separators, line endings, PATH precedence (PP and WPF stories). Diff the environments and move differences across one at a time (`anomalies-and-causes.md`).

## 7. Regressions (it worked before)

You already have a passing world: the earlier version. Use it.
1. Write the automated test that fails now and passed then; verify on both endpoints.
2. Search the change history: `git bisect` (with `git bisect run`) over commits for an ordered, always-buildable history (adaptation); dd-style subset testing when changes are unordered or finer than a commit (`simplify-and-isolate.md` section 8).
3. Group changes that depend on each other, run each test in a scratch directory, treat build or apply failures as unresolved.
4. Interpret the result carefully: the isolating change is a cause, not necessarily a defect. In the book's case an upstream tool changed a help string and the downstream program parsed that text by exact prefix; the right fix was in the downstream program. Decide which side is wrong by asking what each is supposed to guarantee.
5. Also cover changes outside the repository: dependency upgrades, OS and toolchain updates, configuration, data. If you "changed only one thing" and it broke, that one thing is the suspect (PP).

## 8. Long-running or field failures you cannot reproduce

- Collect product facts and a crash dump automatically if privacy allows; tell users what is collected (WPF ch. 2). Prefer a stack trace and the last events.
- Capture only what you need, from a reproducible state (a checkpoint, or since the last committed transaction), rather than the whole history (WPF ch. 4).
- Use a "second chance" approach: leave monitoring off, and after the first failure enable it at the locations involved (WPF ch. 4.6).
- Use sampled telemetry with statistical predicates (`anomalies-and-causes.md`), or range tracking learned on a healthy interval and alerting on the first out-of-range value.
- Keep cheap assertions on in production, with friendly recovery, so the next occurrence leaves clues (`observe-and-trace.md` section 12).

## 9. Crashes far from their cause

The later an infection is detected, the more of its origin is lost; an invalid record that travels far before crashing reproduces the crash but not its source. Pull detection earlier: assertions and preconditions at boundaries; validating data on the way in; sanitizers; a data-invariant check on the object that gets corrupted, wrapped around its mutators (bisects by class and method). Then use the backward loop (`locate-and-fix.md`).

## 10. "It must be the compiler, OS, library"

Hoofprints mean horses, not zebras (PP tip 26). Assume your code calls the library incorrectly before assuming the library is broken. Read the documentation and write the smallest program that calls the library alone. If that still fails, you have an upstream report (simplified, with version and environment) and probably a workaround to write (`locate-and-fix.md` section 7). A sign that the toolchain is at fault: the failure appears or disappears with a build option or tool upgrade rather than with a source change; confirm by diffing builds.

## 11. Verify

- The uncontrolled input was identified and pinned, or recorded and replayed.
- The failure rate before and after is reported with the number of runs.
- For races: the race detector or forced interleaving test passes, in addition to a green stress run.
- For Heisenbugs: the failure was observed by at least two independent means, or a post-mortem artefact was used.
- For memory errors: a sanitizer or checker run is clean on the failing test.
- For regressions: the isolating change was checked against the question "is this a defect or an exposed assumption?" before choosing where to fix.
