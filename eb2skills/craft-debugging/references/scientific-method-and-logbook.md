# The hypothesis loop and the logbook

Sources: WPF ch. 6 (scientific debugging), ch. 1 (TRAFFIC), ch. 12 (causes); PP ch. 3 "Debugging" (mindset, rubber ducking, binary search).

## Contents
1. Why a method
2. The loop
3. Logbook format and rules
4. A worked loop
5. Quick-and-dirty first, with a budget
6. Where hypotheses come from
7. Hierarchy of reasoning techniques
8. Mindset rules
9. Algorithmic (declarative) debugging
10. Verify

## 1. Why a method

When a program fails, your mental model of it has failed too. You can no longer trust "it obviously works like this". Treat the failing program like an unexplained natural phenomenon and explore it independently of the model (WPF ch. 6). The method needs no prior experience with similar bugs and is reproducible, so the cause is eventually found.

The same chain underlies everything: a defect (wrong code) causes an infection (wrong state) which propagates to a failure (wrong visible behaviour). Debugging is finding the transition from a sane state to an infected state, searching both in space (which part of the state) and in time (when). Two moves drive the search: separate sane from infected, and separate relevant from irrelevant (WPF ch. 1).

## 2. The loop

1. Observe the failure (reproduced, ideally minimal).
2. Invent a hypothesis consistent with all observations so far.
3. Derive a prediction: something you can check and that would be false if the hypothesis were false.
4. Test it with an experiment or an extra observation. Write the prediction before running it.
5. Prediction holds: refine the hypothesis (make it more specific). Prediction fails: create an alternative hypothesis.
6. Repeat until the hypothesis cannot be refined further.

The end product is a diagnosis: a theory that explains every observation including the failure and predicts that the failure disappears after the fix. A hypothesis that no experiment could reject is useless.

A refuted hypothesis is as informative as a confirmed one. In the book's sort example, learning that the array already had the wrong size at function entry shifted the search from the function body to its caller.

## 3. Logbook format and rules

Keeping hypotheses in your head is like playing Mastermind from memory. Write them down, or explain them to someone. For an agent the logbook is a scratch file or a running section in the conversation.

Columns that work:

| # | Hypothesis | Prediction (written first) | Experiment | Observation | Conclusion |
|---|---|---|---|---|---|

Header: problem statement (or ticket id), expected versus actual behaviour, the reproduction command, the exact code version.

Rules:
- Prediction before experiment. Otherwise you will fit the prediction to the result.
- One row per experiment, including the ones that failed. This stops you re-running rejected experiments and lets you resume after a break.
- A new hypothesis must include all earlier hypotheses that passed, exclude all that failed, and explain every earlier observation, successful and failed (WPF ch. 6.8). Before accepting one, list the observations and check that it accounts for each.
- Keep the first row as the failure itself: "hypothesis: the program works; prediction: output X; observation: Y; rejected". It puts the observation in the same format as the rest.
- Record the version (commit) beside every observation; code changes between experiments make rows incomparable.

## 4. A worked loop

The book's example: a sort program prints `0 11` for the arguments `11 14`.

| Hypothesis | Prediction | Experiment | Result |
|---|---|---|---|
| H0 The program works | prints `11 14` | run it | prints `0 11`: rejected |
| H1 `a[0]` really is zero at the print (not an output bug) | `a[0] == 0` there | inspect in a debugger | confirmed (cheap check against a costly wrong trail) |
| H2 State is still sane at entry to the sort | `a=[11,14]`, `size=2` at entry | breakpoint at entry | `a=[11,14,0]`, `size=3`: rejected, the caller passed a bad size |
| H3 `size=3` causes the failure | setting size to 2 at entry gives `11 14` | change the value, resume | as predicted: confirmed |
| H4 Passing `argc` instead of `argc-1` causes it | fixing the call gives correct output | change the code, rebuild | correct output: confirmed |

The pattern is reusable: (1) confirm the symptom is real state, not an output artefact; (2) bisect where the state first becomes infected; (3) confirm causality by manipulating the suspect state and re-running; (4) trace the infected value to code and confirm causality again by changing the code. The diagnosis is proven by showing both alternatives: with the suspect the failure occurs, without it the failure does not. Removing this failure does not prove the program correct; regression checks still apply (`fix-validation-checklist.md`).

## 5. Quick-and-dirty first, with a budget

Simple problems deserve simple handling: read the error, think, fix. The risk is that you cannot tell in advance which problems are simple. The book's rule: after about 10 minutes of informal debugging without finding the defect, switch to the explicit method: write the problem statement, open the logbook, make the steps exact, take a break if needed.

Agent adaptation (the book counts minutes; this counts attempts): switch to the logbook after two failed speculative fixes, or as soon as you catch yourself repeating a change you already tried, or when the failure is not reproducible on demand.

## 6. Where hypotheses come from

Five sources (WPF ch. 6.8). Use all of them; fewer iterations come from better hypotheses.

| Source | Gives you | Where it is developed |
|---|---|---|
| Problem description | What is wrong and, when simplified, what is relevant | `reproduce.md`, `simplify-and-isolate.md` |
| Program code | The abstraction over all runs; what could and could not influence a value | `deduce-and-slice.md` |
| The failing run | Actual facts: code executed, state as it evolves | `observe-and-trace.md` |
| Alternate (passing) runs | Anomalies, and differences to narrow down | `anomalies-and-causes.md` |
| Earlier hypotheses | Constraints on the next one (include, exclude, explain) | this file |

## 7. Hierarchy of reasoning techniques

| Technique | Runs | Direction | Yields |
|---|---|---|---|
| Deduction | 0 | general to particular; from code to what can happen | Claims true for all runs, if the abstraction holds (static analysis) |
| Observation | 1 | facts of one run | What did happen; cannot be denied unless the observation is flawed |
| Induction | n | many runs summarised into an abstraction | Properties that held across runs (coverage, invariants) |
| Experimentation | n controlled | runs chosen to refine or reject hypotheses | A precise diagnosis |

Each level uses those below it. Debugging is about the past of one run, so dynamic techniques are the most useful; deduction is the cheap first pass.

## 8. Mindset rules

- Fix the problem, not the blame; whoever's bug it is, it is your problem (PP tip 24). Do not panic; if your first thought is "that's impossible", you are wrong: it happened (PP tip 25).
- The easiest person to fool is yourself: turn off ego defences and project pressure.
- Assume your code is wrong before assuming the compiler, OS or library is (PP: "select is broken" story, tip 26). If it is the third party, you must still eliminate your code before reporting. If you changed one thing and it broke, that thing is the suspect, however far-fetched the route.
- Do not assume, prove: in this context, with this data, with these boundaries (PP tip 27). Surprise is proportional to the trust you placed in the code; re-examine the part you were sure about.
- Explain the problem aloud, line by line, to a rubber duck or a colleague: stating the assumptions you take for granted often exposes the clue. In an agent session, write the explanation in the logbook.
- Binary search when there is no obvious starting point: check symptoms at two far apart points, then the middle, and recurse into the half that contains the problem. Bisect code, history, input or configuration.
- Work on code that compiles without warnings, with warning levels high; let the tools find what they can before you do (PP).
- Look at the data: print name=value pairs, draw the structure, plot it. A picture makes the bug jump out (PP).
- If the infection can be recognised by a property ("tree has a cycle"), have the machine check it (assertions) rather than eyeballing large state (WPF ch. 8).

## 9. Algorithmic (declarative) debugging

For code with little shared state (pure functions, recursive functions), walk the execution tree top down: is the result R correct? If not, ask whether each of its origins (sub-calls) returned a correct result. Recurse into an incorrect one; when all sub-results are correct, the defect is in the computation that produced R from them (WPF ch. 6.7). In the book's insertion sort example this narrowed to one branch of `insert` that appended instead of prepended.

Works best for functional code where each call is judged from arguments and result alone. It does not scale to imperative code with shared state and millions of calls, and judging large data by hand is impractical. Agent use: for pure-ish functions, check each intermediate return against its documentation or tests; unit tests and type contracts are partial oracles.

## 10. Verify

- There is a written problem statement with expected versus actual behaviour and a reproduction command.
- Every experiment row has a prediction that was written before the run.
- The current hypothesis explains every observation so far, including those from rejected hypotheses.
- Causality was shown both ways: with X the failure occurs, without X it does not.
- The diagnosis predicts that the fix removes the failure, and that prediction was tested.
- You did not treat "failure gone" as proof of correctness.
