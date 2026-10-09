# Anomalies and causes: comparing passing and failing runs

Sources: WPF ch. 11 (detecting anomalies), ch. 12 (causes and effects), ch. 13 (isolating causes), ch. 14 (cause-effect chains).

## Contents
1. Anomaly versus cause versus defect
2. Anomaly techniques
3. Cause: definition and the mandatory experiment
4. Actual cause and the closest passing world
5. Choosing the passing world
6. Narrowing by hand and by dd
7. Cause-effect chains on program states
8. Cause transitions
9. Verify
10. Warning signs

## 1. Anomaly versus cause versus defect

Three different strengths of evidence:
- Anomaly: behaviour that differs from normal (other runs). Abnormal does not mean incorrect, but defects are frequently anomalies. First look at the abnormal, then focus observation and assertions on it. An anomaly is a hypothesis, not a finding.
- Cause: a difference whose removal makes the failure disappear, shown by experiment. Causes are more valuable than anomalies or deduced suspects because the failure occurs only when the cause occurs, and they suggest fixes.
- Defect: code that is wrong relative to what was intended. A cause need not be a defect (section 6).

Three questions for any anomaly (WPF ch. 11.7): does it indicate an infection (trace its origins backward)? could it cause the failure (follow forward dependences)? could it be a side effect of the defect (trace back to the common origin)? Then set up an experiment to see whether the failure goes away without it.

## 2. Anomaly techniques

| You have | Technique | Cost and notes |
|---|---|---|
| A test suite with pass/fail and no hypothesis | Coverage comparison: rank lines by how many failing versus passing runs executed them | Cheap; needs diverse passing runs |
| One failing run and many passing ones | Nearest neighbour: compare with the single passing run whose coverage is most similar, not the union of all | Sharper than the union |
| Protocol or ordering bugs (resource not closed, wrong call order) | Compare call sequences per object | Catches temporal bugs that line coverage misses |
| Many runs (random or field), failure depends on return values or branch outcomes | Statistical predicates: counters for return sign, branch taken | Finds legal-but-unexpected values; thousands of runs |
| Rare failures in deployment | Sampled field instrumentation | Privacy and overhead; the cited experiment sampled 1 in 1,000 returns for under 4% overhead |
| Code and tests but no spec | Invariant inference from passing runs, or range tracking learned on a healthy interval | Review for test-input artefacts |
| A clear spec or oracle exists | Assertions instead (`observe-and-trace.md`) | Exact rather than statistical |

### Coverage comparison (spectrum-based localisation)

1. Collect runs classified pass/fail: at least one failing, several passing with varied inputs.
2. Record line coverage with an ordinary coverage tool.
3. For every line count passing and failing runs that executed it. Rank: executed in failing runs but in no or few passing runs is most anomalous. Lines run by no one, or equally by both, are not anomalies. Lines nobody ran point to a test gap.
4. Inspect the top lines and their path conditions.

Worked example: a median-of-three function, failing on (2, 1, 3). Every line of the failing run also ran in some passing run, but the faulty assignment ran in only one passing run: the least normal. Its path condition (y <= x < z) showed the assignment should have used x. A visualisation colours by the fraction of failing runs among those executing the line and brightens by the fraction of all runs executing it; the known ranking formula is from the wider literature, not the book. Reported results (20 defects, small programs): often only a few percent of code needed examination; may not generalise to large programs.

Limits (partly inferred): a defect that is missing code (omission) has no unique lines; a defect executed by every run cannot be distinguished; coincidental correctness (defect executed without infecting) weakens the signal; flaky tests and multiple defects degrade rankings.

### Statistical debugging

Instrument call sites with counters (return negative, zero, positive), run thousands of varied inputs, label pass/fail, keep predicates that held in all failing and no passing runs. In the book's compression-tool example two predicates survived (a file exists, and the line reader returned null); realistic passing runs left only the null return. Neither value was illegal: it was an anomaly, and following forward dependences showed the code did not expect null. More realistic runs sharpen the result; ~32,000 runs isolated all the bugs in the cited study.

### Invariant inference and range tracking

Instrument function entry and exit, run passing tests, test a library of invariant templates (value ranges, relations between up to three variables, sortedness, subsequence), delete those contradicted, report survivors ranked by support. Output may contain test-input artefacts (the example reported 7 <= n <= 13 only because the random inputs had those lengths). Closed vocabulary; cost cubic in variables in scope. Cheaper variant: record the value range of each variable during a healthy interval, then alert on the first out-of-range value (one simulator bug was found this way: a status field that was always 0 or 1 became 2). Manual version for an agent: log candidate properties at function boundaries across passing tests, keep those that always hold, see which the failing test violates (inferred).

## 3. Cause: definition and the mandatory experiment

A cause is an event preceding another (the effect) without which the effect would not have occurred: a difference between a world where the effect occurs and an alternate world where it does not. In programs you can actually build the alternate world.

To show that property P of a failing run causes failure F: build a world identical except that P is absent; run it; P is shown to be a cause if and only if F disappears too. Supplying the missing config file only counts if the failure then goes away.

The fallacy to avoid is post hoc ergo propter hoc: an anomaly or warning that precedes the failure is assumed to cause it. Warning sign: you are about to change something because it looks wrong and appeared near the failure, and you have not yet run the world without it.

Worked example (WPF ch. 12.3): output showed `a = 0`. Deduction suggested studying why the function returned zero. The cheap experiment of assigning `a = 1` before the print still printed 0, so the value was innocent; the integer format was applied to a double. The reusable move: before tracing where a bad value came from, force a different value at that point and check that the symptom changes.

Every link of a suspected chain needs its own experiment or at least an observation. "Obviously" is not evidence.

Redundant causes (inferred, from exercise 12.5): if two independent things would each produce the failure, removing one will not make it go away. Define the effect precisely and expect to remove several differences together.

## 4. Actual cause and the closest passing world

There are infinitely many true but useless causes (the whole statement, the whole program). The actual cause is the difference between the failing world and the closest possible world where the failure does not occur. Prefer the smaller difference: changing a format string beats deleting the print statement. This is Ockham's razor.

Strategy: (1) find any alternate world in which the failure does not occur; (2) narrow the initial difference to an actual cause with the scientific method. The alternate world need not be a corrected program: a different input, configuration, version or schedule will do.

Common context: whatever does not differ between the two worlds is never isolated as a cause. Keep the alternate world as similar to the failing one as possible.

## 5. Choosing the passing world

| Passing world available | Search space | Cause you isolate |
|---|---|---|
| An input that works | Difference between inputs | Failure-inducing input fragment |
| An older version that works | Code changes between versions | Failure-inducing change |
| Another machine, account or configuration that works | Configuration differences | Failure-inducing setting |
| A run with another schedule or seed that works | Schedule or randomness differences | Failure-inducing thread switch or event |
| A passing run's state at the same location | State differences | Failure-inducing variable values |

Example (WPF ch. 12.6): after an upgrade, a program quit when advancing a slide, and its author could not reproduce it. A fresh user account with default settings worked. Copying settings one by one from the failing account to the fresh one showed the hand-made keyboard layout was the cause.

## 6. Narrowing by hand and by dd

Manually: transfer differences one at a time or by halves. Automatically: dd (see `simplify-and-isolate.md`), which needs an automated test, a way to apply part of the difference, and a strategy. Natural deltas: lines, hunks, settings, commits, thread switches. Hard for images; split by structure or move property adjustments step by step.

Limits that apply to every dd result (WPF ch. 13.8):
1. The passing world decides where you search; choose one close to the failing one.
2. Decomposition into deltas may be impossible or produce many unresolved combinations.
3. Artefacts: a changed input may cause a different failure. FAIL only for the same signature (identical backtrace is the safe form); other failure is UNRESOLVED.
4. Several actual causes may exist; dd returns the first it finds.
5. The cause is seldom the defect. The alternate world need not be correct, and an error present in both worlds is not part of the difference. Removing the cause is a workaround; finding the defect needs the techniques of `locate-and-fix.md`.

## 7. Cause-effect chains on program states

For input that is processed in many places (a compiler pipeline), the isolated input difference points to no code. The idea: a run is a sequence of states; each state difference is the effect of earlier ones and the cause of later ones. Make the chain explicit (WPF ch. 14):

1. Capture states as memory graphs: base variables (globals, locals and arguments of every frame), then unfold references to a fixpoint; the graph handles aliasing. Managed languages make this easy; C and C++ make it hard (unions, dynamic arrays, invalid pointers).
2. Compare a failing and a passing state at the same code location with the same backtrace. Match values by type and content, ignoring addresses (two non-null pointers of the same type match). In the sort example only 8 of 19 values differed.
3. Isolate the relevant differences with dd: copy a subset of the failing state's values into the passing run at that point, resume, and classify: failure occurs is FAIL, absent is PASS, abort or inconsistent state is UNRESOLVED. In the example five tests produced "the failure occurs if and only if the third array element is zero", which pointed back at the wrong size.
4. Repeat at several points in the run (bottom, middle and near the top of the failing backtrace) and read off the chain. In the book's compiler case the chain was: command-line argument, then a new addition node in the syntax tree, then a cycle in the tree, then infinite recursion, then crash.

dd on state returns causes, not necessarily infections: a variable can differ and be infected yet not be reported because flipping it alone does not change the outcome. A reported cause is valid only in the mixed state used for the experiment, which may be unreachable from real input. External state (file descriptors, OS resources) lies outside program memory.

Manual analogue for an agent (inferred from the notes' own summary):
1. Capture the same state (logs, debugger dump, prints) at the same location in a passing and a failing run.
2. Diff them, discarding address-like or irrelevant differences.
3. Overwrite one candidate value in the passing run (debugger `set`, patched fixture, injected parameter) and see if the failure appears; halve the candidate set each time.
4. Repeat earlier and later in the run; where the relevant variable changes from A to B, look at the code between the two points.
5. If the transition statement looks innocent (`return x`), follow its data dependences one step backward and also check code that ran only in the failing run.
6. Always check whether the "cause" is really wrong against the specification.

## 8. Cause transitions

A cause transition is a point in time where one variable stops being a failure cause and another starts. Its code is where the failure can be fixed and is a likely defect. Algorithm (binary search in time): compute the relevant cause at two moments; if they differ, test the midpoint and recurse on both halves; stop at adjacent statements. In the sort example the transitions were: `argc` to the third array element (at the faulty call, the actual defect), then to a local variable, then to the first array element.

Limits (WPF ch. 14.6): transitions exist only in code executed in both runs. In the compiler case the last transition was a plain `return x`; the defect sat one dependence step earlier, in code that ran only in the failing run (a distributive-law transformation applied to sub-expressions that shared a child; the real fix passed a copy). Evidence from the cited study: narrowed the defect to at most 10% of code in 36% of runs, better than the anomaly methods; may not generalise.

The theoretical limit (WPF ch. 14.7): finding causes can be automated; finding the defect cannot, because deciding that a state is infected needs knowledge of what is correct.

## 9. Verify

- You have a failing run where X is present and a run identical except that X is absent in which the failure does not occur.
- The difference between the two is as small as you can make it; if it is a whole statement or module it is a cause but not yet the actual cause.
- For each inferred link in the chain there is an experiment or observation, not only reasoning.
- The hypothesis and its prediction were written before the experiment.
- For anomaly lists: the top entries were checked by experiment, and the "normal" profile came from enough typical runs (a property supported by 3 observations is weak).
- For a ranked suspect: patching it makes the failing test pass without breaking the passing ones.

## 10. Warning signs

- Treating an anomaly as proof of a defect.
- Few or homogeneous passing runs, so everything or nothing looks anomalous.
- Comparing against the union of all passing runs when one similar run would be sharper.
- Over-trusting invariants inferred from small unrepresentative input sets.
- Calling every crash FAIL during isolation, so the reducer wanders to another bug.
- Acting on a mined correlation without a causal story (see `prevent-recurrence.md`).
