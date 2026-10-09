# Reproduce: making the failure happen on demand

Sources: Why Programs Fail (WPF) ch. 2 (problem reports), ch. 3 (automation), ch. 4 (reproduction); Pragmatic Programmer (PP) ch. 3 "Debugging".

## Contents
1. Why reproduce first
2. Problem reports: what to ask for, what to write
3. Reproduce the environment
4. Reproduce the execution: control every input
5. Choose the layer to automate
6. Isolating a unit: breaking dependences
7. Reproducing crashes
8. Verify the reproduction
9. Warning signs

## 1. Why reproduce first

Two reasons (WPF ch. 4): you can only observe a failure you can trigger, and the only proof that a fix works is rerunning the original scenario and seeing it pass. Without reproduction you are limited to reasoning from code. The target (PP ch. 3) is a single command, not a fifteen-step recipe; building that command often reveals the fix.

A reproduction is also the automated pass/fail test that every later technique needs: simplification, cause isolation, bisection, the fix check. If the failure came from an automated local test, you already have it. If it came from a user or a log, building the test is your first task.

## 2. Problem reports: what to ask for, what to write

When the report is vague, ask for these in order of value to the developer (WPF ch. 2):

| Fact | Content | Note |
|---|---|---|
| Steps to reproduce (problem history) | Minimal steps plus the inputs and configuration they touch | Most valuable. Have a second party repeat them. |
| Diagnostic output | Logs of key events, stack trace at a crash | Second most valuable, especially after a long run of events |
| Experienced behaviour | What happened, stated neutrally | Often mirrors the steps |
| Expected behaviour | What should have happened | Usually the negation of the above |
| One-line summary | Component, symptom, trigger | Basis for severity and duplicate search |
| Product release | Exact version or build id | Needed to recreate the build |
| Environment, resources | OS, third-party versions, memory, disk | Only decisive when the problem truly depends on them |

A good report is well structured, reproducible, simple (irrelevant detail removed), general (stated for the widest conditions under which it still occurs), and neutral. If you must write one for someone else (an upstream library, a teammate): simplify the trigger first (see `simplify-and-isolate.md`), check whether it also happens on other versions or environments, and put component, symptom and trigger in the summary.

Report data is unreliable when relayed (PP ch. 3). A tester said a brush tool crashed; the programmer could not see it until they watched the tester paint in the opposite direction from the programmer's own tests. Interview the reporter, watch what they actually do, and do not let a coincidence become the theory. Another example (WPF ch. 4): a user's command failed only when typed, because they typed the letter l and capital O for the digits 1 and 0. Reproduce the user's actual input, not what you assume they typed.

Find a problem yourself while developing? Write a failing test instead of a ticket (WPF ch. 2): the test shows whether the problem is still present and makes the ticket redundant. Use a tracker only for things that cannot yet become a test. Cannot reproduce? Record each attempt, state which configuration difference you suspect, and ask a targeted question rather than closing silently (WPF ch. 2 "WORKSFORME").

In an agent session the "tracker" is the task description plus your logbook (`scientific-method-and-logbook.md`). Put the reproduction command and the exact observed symptom at the top.

## 3. Reproduce the environment

Execution = code (assumed constant) plus input plus environment (WPF ch. 4). Order of work:

1. Pin the code: the exact commit or build named in the report, plus dependency versions and lockfile (adaptation; the book assumes the code is constant). A source file you read that is not the code that ran is a classic trap: check the working directory, PATH, stale builds, and which binary or package version was actually executed (WPF ch. 7, PP ch. 3 note "run ./hello, not hello").
2. Try the reported version first. Check every symptom in the report: reproducing a crash is not reproducing the crash. Any deviation raises the risk that you are on a different bug.
3. If it does not reproduce, adopt circumstances from the reporter one at a time (config files, drivers, OS, preferences, data). Order them by (a) most likely to matter, from earlier reports, and (b) cheap to change and undo.
4. Stop when it reproduces or your environment equals the reported one. If it still passes, either the report is wrong or incomplete, or a difference you do not know about remains: ask for more facts.
5. Each adopted circumstance that flips the outcome is a cause candidate (see `anomalies-and-causes.md`).

Small environmental differences matter. In one reported case time-outs appeared only on battery power because the laptop CPU was throttled; all the tests had run on mains power (WPF ch. 4 "Mad Laptop").

The environment where it does not fail is a gift: it is the passing world you diff against (WPF ch. 12).

## 4. Reproduce the execution: control every input

If you observe and control all input, a run is deterministic. Otherwise it is nondeterministic and the failure appears regardless of your wishes. "Input" is anything that influences the run. General pattern (WPF ch. 4): insert a control layer between real input sources and the program. In capture mode it records what the real source returned; in replay mode it returns the recorded value instead of calling the source.

| Input category | How to control it | Notes and traps |
|---|---|---|
| Data (files, DB, config) | Copy it; also copy configuration and user-controlled data | Take all you need and only what you need; privacy. Reduce afterwards (`simplify-and-isolate.md`). |
| User interaction | Capture/replay; prefer named controls or the functionality layer to coordinates and delays | Low-level event scripts are single-session throwaways |
| Network / communications | Record and replay messages; you need not start from program start if a known state is reachable (e.g. after each committed transaction) | Capture overhead can mask races; later messages are likelier causes than earlier ones |
| Time | Make the clock an injected input; do not edit the system clock for each run | Date-dependent symptoms often hide buffer or format defects; test with all values of the time input (WPF ch. 4 "works only on Wednesdays": a 12-byte name in an 8-byte buffer) |
| Randomness | Record and replay the seed (or the entropy sources) | Let developers swap in a deterministic source; be cautious about letting end users do it for security-relevant randomness |
| Operating environment | Trace and replay at the program/OS boundary (system-call tracer, record/replay tools) | Data volume is the bottleneck; checkpoints plus replay-since-checkpoint reduce it |
| Schedules (threads, processes) | Treat the schedule as an input; record and replay it | See `hard-cases.md` |
| Physics (bit flips) | Only after every alternative is excluded and the influence can be shown | Do not blame cosmic rays and walk away |
| The debugging tools themselves | Observe by two independent means if a failure vanishes under observation | See `hard-cases.md` (Heisenbugs) |

Modern equivalents (adaptation, not from the book): strace/ltrace/eBPF for the OS boundary, rr or time-travel debuggers for deterministic process replay, HTTP record/replay fixtures for network input, injectable clock and seeded RNG parameters, container or VM snapshots for whole-environment control, `faketime`-style tools.

If you reproduce a nondeterministic failure only some of the time, measure it: run N times and report the failure rate (adaptation), and use that rate as the test of any later change.

## 5. Choose the layer to automate

Programs have a presentation layer (what a user touches), a functionality layer (the real work), and a unit layer (cooperating functions, classes, modules). WPF ch. 3: the friendlier an interface is to humans, the less friendly it is to computers.

Decision procedure:

1. Is there a unit-level API where the failing behaviour appears in isolation? Write a unit test. Easiest to run and assert on. It only works if the unit fails alone; if not, move up a layer.
2. Else, is there a functionality-layer interface (library API, command line, service endpoint, scripting interface) that reaches the failure? Use it. Results are machine-readable and robust against UI change.
3. Else the problem is in the presentation, or there is no separation, or the lower layers are inaccessible: drive the presentation layer. Prefer named-control scripts (browser automation by element role or id) to coordinates, avoid fixed sleeps (synchronise on state), and use a VM or container when you need total environment control.
4. A monolith whose core calls the UI directly cannot be tested alone: break the dependence first (section 6).

For a command-line tool the "presentation" is stdin, arguments and stdout, and is easy to automate; the layers blur.

Do not embed a home-grown scripting language in an application to enable automation; embed an existing interpreter or expose a library API (WPF ch. 3).

## 6. Isolating a unit: breaking dependences

Core code that calls presentation code (a dialog, a prompt) creates a cycle: presentation calls core, core calls presentation. You cannot test either alone. Procedure (dependence inversion, WPF ch. 3):

1. Introduce an abstract interface for the concrete dependency B.
2. Make the client A depend on that interface, with the dependency passed in (parameter or constructor).
3. Add an automated implementation (always answers "yes", or returns scripted values) alongside the real one.

Today this is dependency injection with a fake or stub (the book's wording is "dependence inversion"; the mapping is an adaptation). The quick alternative, a global "automated mode" flag, works once and spreads. Design benefit: high cohesion, low coupling and no cycles make later debugging and reproduction easier. A Model-View-Controller split lets you attach a test controller that drives the model and a logging view that records every change (WPF ch. 3).

## 7. Reproducing crashes

At a crash you have the active functions, arguments and variables. Test case extraction rebuilds a call that reproduces it (WPF ch. 4):

| Approach | Idea | Cost |
|---|---|---|
| Keep a copy of the call stack and arguments | Replay exactly | Overhead depends on copy depth; the "used fields" variant measured 13-50% |
| Use the failing state | After the crash, copy the (possibly altered) state and replay the failing call on it | Free until the crash; reproduced about 90% in the cited study; the altered state may not be a faithful surrogate |
| Wait for a second chance | Enable monitoring only at the places involved after the first crash | Reproducible only the second time |

Try the failing state first; if that does not reproduce, add light monitoring and wait. The key limit: the later an infection is detected, the more of the origin is lost. A null record that travels far before crashing reproduces the crash but not its cause. Early runtime checks (preconditions, assertions) make the reproduced crash point straight at the defect (see `observe-and-trace.md`).

Unit-level record: a wrapper (subclass, decorator, proxy) can log each call as compilable or runnable test code, with results recorded as assertions. The log is then a regression test, and the same recording drives a mock object that replays recorded answers (WPF ch. 4 "ControlledMap", mock objects). Unit-level recordings are more abstract and last longer than recorded user clicks. A unit that works alone but fails inside the app has unmonitored interaction: shared variables, other units' state, or time between calls.

## 8. Verify the reproduction

- The test fails with exactly the reported symptoms, all of them, on the reported version.
- It fails every time (or at a measured rate) over repeated runs; it cleans up after itself so a second run starts from the same state (the double-print example: the second run asks "overwrite?" and the script does not expect it).
- It runs with no human in the loop and returns a clear pass/fail, ideally with the failure signature (message, crash site) so that other failures are not mistaken for it.
- It is kept: after the fix it passes and stays in the regression suite.
- If you used replay or a mock, check that the replayed run produces the same outputs as the original.

## 9. Warning signs

- "Cannot reproduce" after an unspecific attempt: did you match every symptom and exhaust environment differences?
- You reproduced a similar but different failure.
- Test scripts with absolute screen coordinates, fixed waits, or that pass once and fail the second time.
- The failure disappears when you add logging, run under a debugger, or recompile (see `hard-cases.md`).
- Capture tooling that changes timing enough to hide a race.
- A report that nobody has tried to automate; a bug seen only by a third party and never reproduced.
