# Observe and trace: logging, debuggers, assertions, origins

Sources: WPF ch. 8 (observing), ch. 9 (tracking origins), ch. 10 (asserting expectations); PP ch. 3 "Debugging" (tracing, data visualisation).

## Contents
1. Three principles of observation
2. Choosing a technique
3. Logging
4. Debuggers
5. Querying events: who changes this value
6. Hooking the interpreter or runtime
7. Tracking origins backward: the loop
8. Dynamic slices, reverse debugging, why-questions
9. Assertions as probes
10. Reference runs and relative debugging
11. System assertions (memory and sanitizers)
12. Assertions in production
13. Verify
14. Warning signs

## 1. Three principles of observation

1. Do not interfere. What you see must be an effect of the original run, not of your observing. Every technique perturbs a little (timing, buffering, memory layout). If the failure vanishes or changes once you observe, suspect interference (`hard-cases.md`).
2. Know what and when to observe. A run is a long sequence of huge states; you can only look at part of the state at some moments. Without a hypothesis you cannot choose either.
3. Proceed systematically. At every moment you should be able to say: the current hypothesis, what it predicts you will see, and how the observation changes the hypothesis. Poking around without that is quick-and-dirty debugging.

## 2. Choosing a technique

| Situation | Pick | Why |
|---|---|---|
| One question, interactive run possible | Debugger breakpoint plus print | No code change, fast start |
| Trace across many calls, long run, CI or server | Levelled logging to a separate channel | Repeatable, diffable between passing and failing runs |
| Same logging at many call sites, source must stay clean | Aspect, decorator, middleware, interceptor | One definition, pluggable |
| No source or no rebuild possible | Binary instrumentation, syscall tracing | Works on executables |
| Crash already happened | Core dump or crash report: backtrace, then inspect | State at the crash moment |
| Who changes this value? | Field-set hook, watchpoint (hardware first) | Stops at the writer |
| Test a hypothesis by changing a value | Debugger `set` and continue | Intervention without editing code |
| Timing-sensitive failure | Buffered or off-thread logging, record and replay | Avoids the Heisenbug |
| Corruption in C or C++ with strange far-away crashes | Memory checker or sanitizer first | Before reasoning about values |

## 3. Logging

Naive print logging has four drawbacks: it clutters code (so it gets deleted), it clutters output (so use a dedicated channel such as stderr or a file), it slows things down (timing changes), and buffered output is lost on a crash, exactly the last events you want. Flush on crash or use an unbuffered channel for crash-hunting.

Wish list: standard format with prefix (file, function, time), optional (off in production), variable granularity (levels and per-component), persistent (can be re-enabled later).

- Make log arguments lazy: when logging is off, arguments must not be evaluated (no cost, no side effects). Macros in C; level guards or lambdas in other languages, and pass format arguments rather than building strings first.
- Capture the source location automatically.
- Structured, levelled logging with a runtime configuration (root level high, one component at debug) replaces ad-hoc prints and scales.
- Reuse dump functions (`toString`, `__repr__`, Debug derive) for data structures.
- The same facility can be added without touching source by aspects, decorators or proxies; the advice must not alter program state.
- No source? Dynamic binary instrumentation inserts code at function entry and exit (a programmable strace). Heavy slowdown at instruction level.
- Log consistently (PP): a regular format can be parsed. Example: log every open and close of a resource, and a script finds the unbalanced open.

## 4. Debuggers

A debugger can run to a condition, show state, and change state (WPF ch. 8.3). Session recipe:

1. Build with debug information, load the program, set a breakpoint where your hypothesis can be checked.
2. Print values, show the backtrace, select caller frames to see their locals; `step` enters calls, `next` skips them.
3. Test a hypothesis by changing state (`set size = 2`, continue). If the failure disappears, the variable is a cause.
4. Use the backtrace to find where the wrong value came from, then fix in source and rerun.
5. Delete stale breakpoints.

More: conditional breakpoints (stop only when an infection condition holds); breakpoint command lists that print and continue (printf logging without touching the source); post-mortem debugging from a core dump or crash report (`where`, then inspect, or rerun in the debugger if there is no dump); embedded debuggers that the program opens on itself (Python `breakpoint()` or `pdb.set_trace()`, `debugger;`) which must never be enabled in production. Calling functions from the debugger can have side effects or hit breakpoints: only call simple, side-effect-free ones.

The lesson the book draws: do not step aimlessly. State the hypothesis, put the breakpoint where it can be checked, predict the values, compare. A debugger is toy-like and seductive; combine it with thinking.

## 5. Querying events: who changes this value

Many hypotheses are of the form "wherever X gets set". Options, cheapest first:

| Mechanism | Cost and use |
|---|---|
| Breakpoint at a known location, optionally with a condition | Cheap; one interrupt at the location |
| Breakpoint inside the setter or accessor | Cheap when all writes go through accessors |
| Field-set hook (aspect, property setter, proxy) | Cheap in managed languages; logs old and new values at every write |
| Hardware watchpoint | Free but only a few locations; set while the variable exists |
| Software watchpoint | 1,000 times slower or worse (check after every instruction); last resort for stray-pointer corruption |
| Event-query tool or recorded execution | For relational questions over history |

A condition on location plus data is cheap; "or" conditions need both mechanisms.

## 6. Hooking the interpreter or runtime

Interpreted runtimes expose hooks for tracing: Python `sys.settrace` gets (frame, event, arg) with events call, line, return, exception, and read access to locals; the JVM has field monitoring and instrumentation agents; JavaScript has `Proxy` and the inspector protocol; Ruby has `TracePoint` (the last two are adaptation). A five-line tracer prints a full line trace. To prototype your own observation technique, do it first in an interpreted language.

## 7. Tracking origins backward: the loop

The core procedure for locating infections (WPF ch. 9.5 and 15.1):

1. Start with the infected value that defines the failure.
2. Find its possible origins by following dependences: data and control, statically (`deduce-and-slice.md`) or dynamically.
3. Observe each origin and judge it: infected or sane?
4. If an origin is infected, repeat steps 2 and 3 on it.
5. When you reach an infected value all of whose origins are sane, the code that produced it is the defect.
6. Fix, and verify that the failure no longer occurs.

This always works with observation and judgement alone; the cost is the number of values to observe and judge. Reduce it with assertions (automated judging), with focus on likely origins (`locate-and-fix.md`), and by taking larger steps at function or package boundaries, where communication is limited to arguments and return values and sanity is easier to judge. If a state is sane, stop looking earlier; search forward from there for the moment it becomes infected. The chain ends because the program started from sane input; if you reach infected input, the defect is outside the program (bad input or specification) (inferred in the notes).

Do not assume the first infected value you find is the defect. It is the defect only if everything it read was sane.

## 8. Dynamic slices, reverse debugging, why-questions

- A static slice contains statements that may influence a value in any run (about 30% of a program on average); a dynamic slice contains those that did in one run (about 5% of executed statements). Computation from a trace: record writes and reads per executed statement, treat the controlling predicate as a variable read by everything it controls, and accumulate origins along the trace. General dynamic slicers are uncommon; an agent can approximate one: log the run, then follow reads and writes plus enclosing conditions backward from the bad value.
- Omniscient (reverse) debugging records every state change so you can move backward without restarting: start at the failure, step back checking for infection, follow it to the defect. Cost in the cited prototype: 10 times slower and about 100 MB per second of recorded data, so record windows or parts. Modern tools: rr, GDB reverse execution, time-travel debugging in WinDbg and browsers (adaptation). Best for hard-to-reproduce failures: record once, explore forever.
- "Why did" and "why didn't" questions: "why did S execute or have this value" is answered by the dynamic backward slice limited to the immediate data origin and controlling predicate; "why didn't S execute" by the nearest controlling predicate that blocked it, then "why did" on that. The answer often corrects the programmer's expectation, which is what the bug really was. Phrase your own questions that way and answer them from one concrete run.

## 9. Assertions as probes

Assertions automate the judging step: they are infection detectors that fire before the infection spreads and hides its origin. Written once, they serve debugging, documentation and testing.

Basics: a good assert reports file, line and the failed expression, can be switched off, and has no side effects (else behaviour changes when disabled). Java assertions are off by default (`-ea`); Python strips `assert` under `-O`.

Systematic use, not sprinkling:
- Data invariant: write a `sane()` predicate for the object (valid ranges, structural properties such as "tree is acyclic, root is black") and assert it on entry and exit of every public mutator. It does not need to hold mid-method.
- Precondition at entry (caller's duty), postcondition at exit (callee's duty), with saved copies of entry values when the postcondition refers to them. Cheap oracles: inverse function, round trip, sortedness, conservation law.
- Diagnostic reading: precondition fails means the infection happened before this call; postcondition fails means within it; postcondition holds means this method is not the infection site. Contracts settle blame: violated precondition is the caller's bug.
- To avoid clutter, attach the checks in one place: an aspect, decorator, proxy, or test-only subclass over the mutators.
- A conditional breakpoint `break ... if !sane()` works without recompiling.
- Do not copy the implementation into the assertion; that is not an independent oracle (inferred).
- A specification can itself be wrong (the A320 landing case in the book): review the spec as well as the code.

Per-object invariants do not guarantee that the whole state is sane (relations across objects, global properties).

## 10. Reference runs and relative debugging

When another version, port or reimplementation is the oracle: run both on the same input and compare states or outputs at matching points; the first violated comparison localises the infection. Sources of references: the previous version, a changed environment (Y2K style date simulation), a port, a clone. Generalised: golden-file and snapshot tests, differential tests, diffing logs of a passing and a failing version, shadow traffic comparison (adaptation).

## 11. System assertions (memory and sanitizers)

In C and C++ memory errors are time bombs that fail millions of instructions later. Apply a memory checker first, at the slightest suspicion, before value-level reasoning (WPF ch. 10.8): allocator self-checks, guard-page allocators, Valgrind-style shadow memory (flags reads of uninitialised memory, accesses outside allocated blocks, leaks, and reports the allocation site), instrumenting checkers. Modern analogues (adaptation): AddressSanitizer, MemorySanitizer, UBSan, ThreadSanitizer, Miri for Rust unsafe code. They cost time and memory, so use them in test runs, not production. Managed-memory languages do not have these errors; they still have ordering, timing, locale and environment dependences.

## 12. Assertions in production

Never implement these as `assert` (it can be disabled) (WPF ch. 10.9):
- Critical results (life, health, money): validate with extra computation.
- External conditions and input: check syntax and semantics, and answer in the user's language ("a PIN has exactly four digits"), not "assertion failed". Disabled input checks are a security hole.

For the rest, the arguments for keeping them on: more active assertions catch more infections, failing fast shortens the defect-to-failure distance, field failures are hard to reproduce and an assertion gives clues, and an unnoticed wrong behaviour is more dangerous than a noticed abort. Do not shoot the messenger: install a global handler that reports a fatal error and offers recovery. Measure before disabling; drop only the expensive ones (deep invariant walks on every call) and keep cheap ones that guard result integrity.

## 13. Verify

- Each observation answers a prediction written in the logbook (predicted versus observed).
- The failure still occurs with logging on, and the program's real output channel is unchanged.
- Debug logging left in code is levelled, cheap when disabled, and side-effect free.
- A newly added assertion was violated on purpose once to see that it fires with a useful location and message; the build with assertions disabled gives the same output on passing runs.
- After the fix: the same failing input gives correct output, and the earlier infection point no longer shows the bad value.
- For each step of an origin chain you can name the infected value, its origins, and the sane-or-infected verdict for each.

## 14. Warning signs

- A debugging session without a stated hypothesis.
- Log lines lost in a crash because of buffering; debug output mixed into stdout and corrupting parsers or tests.
- Log arguments with side effects or expensive evaluation when disabled.
- Failure changes when observed.
- Stale breakpoints or watchpoints; debuggee functions with side effects called from the debugger; embedded debug consoles left in production.
- Stepping forward repeatedly and overshooting the infection: place the breakpoint at the origin of the value, not at the symptom, or record and replay.
- Skipping memory checkers in C or C++ and chasing phantom value corruption.
- Trusting a visualisation of large state when a programmatic check would be exact.
