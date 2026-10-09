---
name: craft-debugging
description: Systematic procedure for finding and fixing the cause of a failure instead of guessing, covering reproduce, minimise, hypothesise, observe, locate, fix and verify, with a delta-debugging script (scripts/ddmin.py). Use when a test fails and the cause is unclear, a bug report is vague, a failure is intermittent or flaky, a crash or wrong output appears far from its cause, something worked before and now fails (regression, bisect), a failing input is huge and needs shrinking, a quick fix attempt just failed, or the user says "debug this", "why does this fail", "find the root cause", "can't reproduce", "works on my machine". Not for designing error-handling policy (see craft-error-handling), writing the test suite itself (craft-testing), or designing concurrent code (craft-concurrency).
---

# Debugging: from failure to verified fix

## Purpose

Treat a failure as a chain to be traced, not a place to try edits. A defect (wrong code) causes an infection (wrong state), which propagates to a failure (wrong visible behaviour). Your job is to reproduce the failure on demand, shrink it, then follow the chain backward by hypothesis and experiment until you reach the first statement that turns sane state into infected state, and to prove the fix by rerunning the original failure. This skill replaces "change something and see" with a loop whose every step you can show.

## Choose what applies

| Situation | Do this | Read |
|---|---|---|
| Bug report or failure description, not yet reproduced | Build an automated reproduction first; check every reported symptom | `references/reproduce.md` |
| Report is vague, or you must write one for someone else | Ask for steps, logs, observed and expected behaviour, version | `references/reproduce.md`, `references/problem-tracking.md` |
| Failing input is large (file, log, request, test case) | Shrink it with ddmin, or isolate against a passing input | `references/simplify-and-isolate.md`, `scripts/ddmin.py` |
| Worked in the previous version, fails now | Bisect history or the change set against an automated test | `references/simplify-and-isolate.md` section 8, `references/hard-cases.md` section 7 |
| Cause unclear after a first look | Open a logbook and run the hypothesis loop | `references/scientific-method-and-logbook.md` |
| Wrong value seen, origin unknown | Backward infection loop; slice; dynamic trace | `references/deduce-and-slice.md`, `references/observe-and-trace.md` |
| You have passing and failing runs and no hypothesis | Compare coverage, states, configuration, versions | `references/anomalies-and-causes.md` |
| Intermittent, flaky, vanishes under logging, races, memory corruption | Pin or record the uncontrolled input; measure failure rate | `references/hard-cases.md` |
| Candidate cause found, about to edit | Two tests (infected? causal?), then fix-validation list | `references/locate-and-fix.md`, `references/fix-validation-checklist.md` |
| Fixed, want to stop it coming back | Post-fix questions, sibling search, hotspot history | `references/prevent-recurrence.md` |
| Trivial cause visible in the first error message (typo, missing import, obvious stack trace line) | Just fix it and rerun; use the full procedure only if that fails | none |
| The task is designing how errors are signalled, validated or contracted | Not this skill | craft-error-handling |
| The task is choosing test levels, doubles, coverage strategy | Not this skill beyond the regression test | craft-testing |
| The bug is a design flaw (architecture, wrong abstraction) | Debugging finds it; fixing it is design work | craft-module-design, craft-refactoring |

## How to apply

### The sequence (TRAFFIC)

Track, Reproduce, Automate, Find origins, Focus, Isolate, Correct. The middle of it, locating the defect, takes most of the time; the rest is usually mechanical when done in order.

1. **State the problem.** Write the expected versus actual behaviour, the exact version (commit, dependency versions), and the command that shows it. Put this at the top of your logbook (a scratch file or a running section in the conversation).
2. **Reproduce it, automated, with one command.** Run it and check that you see all the reported symptoms, not merely a failure. If you cannot reproduce, adopt circumstances from the reporter one at a time, cheapest and likeliest first; do not declare "cannot reproduce" after an unspecific attempt. For the layer to automate (unit, functionality, presentation) and for controlling time, randomness, network and schedules, see `references/reproduce.md`. If the failure is intermittent, run it N times and note the failure rate.
3. **Clean the field.** Compile or lint with warnings on and clear or explain warnings in the failing area; run a sanitizer or memory checker first if the language allows memory errors. A tool finds common defect patterns cheaper than you do.
4. **Shrink it.** If the input or the test is big, reduce it until every remaining part matters (`scripts/ddmin.py`, section below). A small case has less state to inspect, communicates better, and exposes duplicates.
5. **Hypothesise and test, in writing.** One row per experiment: hypothesis, prediction (written before running), experiment, observation, conclusion. A new hypothesis must explain every observation so far. See `references/scientific-method-and-logbook.md`.
6. **Trace backward.** Start at the infected value that defines the failure. List its possible origins (data and control dependences). Observe each one and judge sane or infected against the intended behaviour. Follow an infected origin; stop at an infected value whose origins are all sane. Take big steps at function boundaries, where only arguments and return values cross.
7. **Check each candidate twice.** (a) Is it infected, wrong against the intended behaviour? (b) Does it cause the failure: do you get the failure with it and not without it, by experiment? Only then is it on the chain.
8. **Choose the fix type.** A correction removes the defect. A workaround leaves it and must be labelled as one and kept open. Never a special case for the failing input.
9. **Predict, edit, validate.** Say how the change breaks each link in the chain, then apply it and run the checklist in `references/fix-validation-checklist.md`.
10. **Learn.** Regression test, sibling search, earlier check. See `references/prevent-recurrence.md`.

### Time-box the quick attempt

Simple problems deserve a simple attempt: read the error, think, fix. The risk is that you cannot tell in advance which problems are simple. Switch to the written loop after two failed speculative fixes, when you repeat a change you already tried, or when the failure is not reproducible on demand. (The book says about ten minutes; counting attempts suits an agent better.)

### Where to look first

When several candidates compete, rank them (WPF ch. 15):

1. Infections already shown by a failing assertion or observation.
2. Causes shown by experiment (isolation, dd, passing-versus-failing diff).
3. Anomalies: code run only in failing runs, values outside the range seen in passing runs.
4. Code smells reported by the compiler or a linter.
5. Whatever is in the backward slice of the infected value, nearest first. Anything outside the slice cannot (in a safe language) have caused it.

Tie-breaker from history: files with many earlier fixes or recent change are likelier (`references/prevent-recurrence.md`). A tie-breaker orders candidates; it does not replace step 7.

### Choosing the technique to find the next fact

| You need | Use | Cost |
|---|---|---|
| What can influence this value in any run | Static backward slice, find-references, call hierarchy | Free; imprecise (about 30% of a program) |
| What did influence it in this run | Trace or dynamic slice: log reads and writes, follow conditions | Instrumentation; far more precise (about 5% of executed statements) |
| Value at a point in a live run | Breakpoint or print with a stated prediction | Cheap |
| Who writes this variable | Setter breakpoint, field-set hook, hardware watchpoint; software watchpoint last | Watchpoints in software are 1,000 times slower or more |
| Whether a state is sane, repeatedly | Assertion or invariant predicate on entry and exit of mutators | Write once, runs everywhere |
| Which part of a big input matters | ddmin (simplify) or dd (isolate against a passing input) | Logarithmic when outcomes resolve |
| Which change broke it | `git bisect run` or dd over changes | Logarithmic over ordered history |
| Where passing and failing runs differ | Coverage comparison, nearest passing run, state diff | Needs several passing runs |
| Whether suspect X is really the cause | Build the world without X, change nothing else, rerun | One experiment per link |

### A short worked example

A sort routine prints `0 11` for the arguments `11 14` (the book's running case, WPF ch. 1 and 6). The loop in miniature:

1. Reproduce: `./sample 11 14` prints `0 11` every time; `./sample 9 7 8` passes.
2. Is the bad value real state or an output bug? Inspect `a[0]` at the print: it is 0. Real.
3. Hypothesis: the state is sane at entry to the sort. Prediction: `a=[11,14]`, `size=2`. Observation: `a=[11,14,0]`, `size=3`. Rejected, so the infection happened before the call.
4. Causality: set `size` to 2 at entry and resume. Output becomes `11 14`. The wrong size causes the failure.
5. Origin of `size`: the caller passes `argc`, which counts the program name. Chain: array of 2, sort called with 3, reads the element past the array (uninitialised, here 0), sorts it to the front, prints it.
6. Why `9 7 8` passes: same defect and the same out-of-bounds read; since the output is right, the stray value must have sorted to the end, past the printed elements (our inference; the book only says the chain also explains the passing run).
7. Correction: pass `argc - 1`. Rerun both cases. Changing the loop bound inside the sort would also silence this run, but it leaves the defect and breaks other callers (ignorant surgery).

### Using the script

`scripts/ddmin.py` shrinks a text input (by lines, or by characters) to a 1-minimal failing input: removing any one remaining line or character makes the failure disappear.

```
python3 scripts/ddmin.py failing_input.txt --cmd './repro.sh {}' -o minimal.txt          # lines
python3 scripts/ddmin.py minimal.txt --cmd './repro.sh {}' --mode chars -o tiny.txt      # then chars
python3 scripts/ddmin.py --self-test
```

The test command exits 0 when the failure still reproduces, 125 for unresolved (invalid candidate, a different failure), any other code for pass. This is the reverse of `git bisect run`, where 0 means good. Make it check the original failure signature (message, crash site), or the reducer wanders to a different bug. A wrapper of this shape works for a CLI that crashes on a file: run `prog "$1"` capturing stderr; exit 125 if it printed a parse or usage error; exit 0 only if stderr contains the original message; otherwise exit 1. Candidate files are passed as `{}` or as the last argument; the command runs with stdin closed and output discarded, so log from inside the wrapper if you need to. The script stops with a clear message if the full input does not fail (it prints the command's exit status) and warns if the empty input also fails (the command ignores the file or tests the wrong thing). Use lines first for structured or line-oriented text, then characters on the result; character cuts of JSON or source code are mostly invalid. For a version range prefer `git bisect run`. See `references/simplify-and-isolate.md` for the algorithm, its limits and the dd variant.

## Verify

Debugging is verified by evidence about the cause and about the cure. Before you report a fix:

- **Reproduction**: an automated command that fails with the reported symptoms before the change and passes after. Show both outputs. For intermittent failures, show the count: failure rate before, and N runs after with no failure, N large enough that the old rate would have shown it.
- **Chain**: one paragraph that states defect, infection (which value, under which condition), propagation and failure, and that also explains why other runs pass. If any link is a guess, say so, and do not call the fix proven.
- **Causality both ways**: with the suspect the failure occurs; with the suspect changed, only that, it does not. A fix passing is the last confirmation, not the first.
- **Not a symptom patch**: the change sits at the origin (first sane-to-infected transition), contains no literal from the failing test, no special-cased input, no swallowed error, no loosened assertion or edited expectation unless you can show that was the actual defect. If it is a workaround, it says so and the problem stays open.
- **Regression**: a test that fails on the old code (run it against the old code once) and passes on the new; the full suite passes; one defect per change.
- **Impact**: other callers and consumers of the changed code checked (forward slice, find-references).
- **Siblings**: a search for the same mistake pattern was run and its result listed.
- **Instrumentation removed or made safe**: debug prints removed or levelled, breakpoints and temporary hooks gone, no embedded debug consoles, and any assertion added was shown to fire.

Done means:
- [ ] The problem statement, the reproduction command and the version are recorded.
- [ ] The root cause is named with its chain, not just the location of the edit.
- [ ] The original failing scenario passes and the earlier infection point shows sane values.
- [ ] A regression test exists and was seen to fail without the fix.
- [ ] Full suite and static checks pass; no unrelated changes are mixed in.
- [ ] Sibling occurrences were searched for and handled or listed.
- [ ] What was not verified (environments, platforms, load) is stated.

### Habits to avoid when you are the agent

- Editing before you can run the failure. A fix you cannot test is a guess.
- Reading only the file the stack trace names. The trace shows how execution got here, not what happened earlier; the infection often began upstream.
- Adding a try/catch, a null guard or a default value at the symptom site. It hides the infection and the chain stays intact.
- Changing a test's expectation, a timeout or a retry count to make the run green without a causal argument.
- Stacking a second speculative edit on a first one that did not work. Revert, then reconsider the logbook.
- Trusting a cause you inferred but never switched off. The experiment is cheap; do it.
- Reporting "fixed" after one green run of an intermittent failure.

## Proportion and limits

- Do not run the full ceremony on a one-line error with an obvious message. Reproduce (rerun the failing test), fix, rerun. Escalate on the triggers above. The logbook can be five lines.
- Delta debugging costs runs: thousands for big inputs at many seconds each is hours. Cache, use lines before characters, cap runs (`--max-tests`), or take a 1-minimal result at coarse granularity. The result is 1-minimal, not the smallest possible.
- Heavy tools (reverse debuggers, dynamic slicers, state-level dd, binary instrumentation) are research-grade or costly in most stacks. The method does not need them: breakpoints, logs, assertions and the diff of a passing and a failing run reproduce the same reasoning by hand.
- The book is from 2009 and its tool examples (GDB 6, Valgrind, FindBugs, DIDUCE, CVS) are dated. The capabilities survive: sanitizers, rr and time-travel debuggers, structured logging, linters, `git bisect`, property-based shrinking, record-and-replay fixtures. Where this skill names a modern tool it is an adaptation, not a claim of the book.
- Some numbers are empirical results from specific systems and small benchmarks (coverage localisation, statistical debugging, cause transitions, bug-cache hit rates). They show the technique can work, not that it will in your codebase.
- Anomalies are not defects. A coverage difference, a violated inferred invariant or a warning is a hypothesis; it needs the experiment of step 7.
- Isolation finds an actual cause, which need not be an error (a regression can come from an innocent upstream change that exposed a fragile assumption downstream). Decide which side is wrong by asking what each side is supposed to guarantee.
- Finding causes can be automated; finding the defect cannot, because deciding that a state is wrong needs knowledge of what is correct. Expect to use judgement, tests and specifications at that step.
- Contested or inconsistent points: the notes give slightly different worst-case counts for ddmin (quadratic in both) and a minor mismatch in the number of tests in one dd example (5 or 6); treat "quadratic worst case, logarithmic when outcomes resolve" as the safe statement.
- Do not use this skill to hunt performance regressions by speculation; the same loop applies, but profile first (the book does not cover profiling).

## References

- `references/reproduce.md`: build the automated reproduction; what to ask a reporter; controlling time, randomness, network, schedules; layers to automate; breaking dependences; reproducing crashes.
- `references/simplify-and-isolate.md`: ddmin and dd stated precisely, test-function design, units of reduction, speed-ups, regression bisect, costs and traps.
- `references/scientific-method-and-logbook.md`: the hypothesis loop, logbook format, a worked loop, time-box rule, sources of hypotheses, mindset rules, algorithmic debugging.
- `references/observe-and-trace.md`: logging, debuggers, watchpoints, backward origin loop, dynamic slices, reverse debugging, assertions as probes, sanitizers, assertions in production.
- `references/deduce-and-slice.md`: reading code backward: control flow, dependences, slices (chop, backbone, dice), smells, limits of static reasoning.
- `references/anomalies-and-causes.md`: coverage and statistical anomalies, what a cause is and how to prove one, choosing the passing world, state diffing, cause transitions.
- `references/locate-and-fix.md`: priority order of where to look, the two tests per candidate, correction versus symptom patch versus workaround, warning signs of a bad fix.
- `references/fix-validation-checklist.md`: the item-by-item checklist before and after the edit, and what evidence to show.
- `references/hard-cases.md`: nondeterminism, races, Heisenbugs, memory errors, time and environment, regressions, field failures, blaming the platform.
- `references/prevent-recurrence.md`: post-fix questions, hotspot and history heuristics, process sources of defects, correlation versus cause, supporting tools.
- `references/problem-tracking.md`: report fields, severity and priority, states, duplicates, linking issues to commits and releases.

## Sources

- Zeller, Why Programs Fail, 2nd ed. (2009): ch. 1 (how failures come to be, TRAFFIC), ch. 2 (tracking problems), ch. 3 (making programs fail), ch. 4 (reproducing problems), ch. 5 (simplifying problems, ddmin), ch. 6 (scientific debugging), ch. 7 (deducing errors, slicing), ch. 8 (observing facts), ch. 9 (tracking origins), ch. 10 (asserting expectations), ch. 11 (detecting anomalies), ch. 12 (causes and effects), ch. 13 (isolating failure causes, dd), ch. 14 (cause-effect chains), ch. 15 (fixing the defect), ch. 16 (learning from mistakes), appendix A (formal definitions, glossary).
- Hunt and Thomas, The Pragmatic Programmer, 1st ed. (1999): ch. 3 "The Basic Tools", sections on debugging (tips 24-27), source code control, shell, plain text, text manipulation, code generators.
