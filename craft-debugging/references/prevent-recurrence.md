# Prevent recurrence: learn from the defect

Sources: WPF ch. 16 (learning from mistakes), ch. 15.4.3-15.4.4, ch. 3.8 (preventing unknown problems), ch. 2 (tracking); PP ch. 3 "Debugging" (post-mortem questions), sections on source control, plain text, shell and text-manipulation tools.

## Contents
1. The post-fix questions
2. Where to put the learning
3. Using history to focus: hotspots and the bug cache
4. Mining fixes from a version archive
5. Process: where defects come from
6. Correlation is not cause
7. Tools that make the next debugging session shorter
8. Proportion
9. Verify

## 1. The post-fix questions

After every non-trivial fix, answer these (PP ch. 3, WPF ch. 15.4 and 16):

1. Why was this not caught earlier? Add the test that would have caught it, and tests for related cases (after a missing null check, test the other null paths too).
2. Would an assertion, type, lint rule or tighter parameter check have caught the infection closer to the defect? Keep the assertions you added while debugging; if an assertion would have caught this infection, write it (crash early).
3. Do the conditions that caused the bug exist anywhere else? Search for the idiom and fix every instance now; make sure you will know if it happens again. Replace the error-prone idiom with a helper if one fits.
4. If it took long, what would make the next fix easier: a testing hook, a log analyser, a reproduction script, better log messages?
5. If someone's wrong assumption caused it, tell the team (documentation, comment, commit message): if one person misunderstood, others may.
6. Is the reported problem a direct result of this defect or only a symptom? Is the bug really in your code, the compiler or the OS? Explained aloud, what would you say? If the suspect code passes its unit tests, are the tests complete? (PP's debugging checklist.)

## 2. Where to put the learning

| Finding | Action |
|---|---|
| A test should have caught it | Regression test for this failure plus siblings |
| The infection travelled far | Assertion, precondition or validation at the boundary where it first became visible |
| A class of error recurs | Static check or lint rule; compiler flags; language feature (non-null types, bounds checks, exhaustive matches) |
| The same idiom repeats | Helper that makes the mistake impossible |
| The code is hard to reason about (many dependences, global state) | Reduce coupling and information flow; fewer ways infections spread and easier review (WPF ch. 16.5) |
| The defect was in a specification or an assumption | Make the specification explicit and executable where possible (contracts, assertions); review specifications; early checking against client needs |
| A diagnostic back door shipped | Release-configuration review (the book's story of a serial-console feature left active in production, a lesson inferred in the notes) |
| QA missed it | Improve the suite; calibrate coverage (high branch coverage means little unless it covers the risky code); consider mutation testing: seed artificial defects, and undetected mutants suggest real ones can slip through too |

## 3. Using history to focus: hotspots and the bug cache

Defects are unevenly distributed (Pareto: roughly 80% in 20% of modules; in the studied systems some components had 4-5 times the density of others). So when you can choose where to look first, prior defect history is a tie-breaker, and when you allocate review or test effort, put it where the risk was. All figures below come from specific systems and are indicative; validate against your own history.

Four cues for where the next defect appears (the "bug cache", WPF ch. 16.7): recently changed components; recently added components; components with a recent defect; components logically coupled (changed together) with defective ones. A cache holding 10% of components, refreshed by these events, covered 73-95% of defects in seven open-source projects. Relative code churn predicted defect density with 89% accuracy in one study. Imports of risky headers and dependency-graph centrality also correlated with defects.

Commands an agent can run (adaptation, using the cues above):
- `git log --oneline -- path` and the count of commits whose message names a fix, per file.
- `git log --since=... --name-only` for recent churn; co-change pairs from files that appear together in fix commits.
- `git blame` and `git log -L` for the history of one function.

Use these to rank candidates and to decide how much extra care a change deserves in a hotspot. They never replace the two tests in `locate-and-fix.md`.

## 4. Mining fixes from a version archive

To measure anything you must identify fix changes (WPF ch. 16.2). Combine: problem identifiers in commit messages (gives severity and context, but only about half of closed reports could be matched in the studied projects), maintenance branches that take only fixes (precise, needs discipline), and keywords such as "fix" or "bug" in commit messages (lightweight, no context). For a new project, set conventions that tie each change to a task or problem number. Both-way linking (the tracker names the fixing change, the commit names the problem) is what makes later analysis and "which release has this fix" queries possible (WPF ch. 2). Tag every release; branch for maintenance and merge fixes back.

## 5. Process: where defects come from

Four questions (WPF ch. 16.3): which modules had the most defects, when were they introduced (requirements, design, coding), which error types occur most, and who introduced them. The last is sensitive: if people feel the archive is used against them they stop using it; focus on finding errors, not blame. Three stages introduce defects:

- Specification: incomplete, inconsistent, changing or missing specifications. Improve checking of the spec, increase precision, automate (executable contracts). Warning signs: frequent changes to a component, complex problem domains.
- Programming: structural complexity. Reduce information flow between components, document for humans, keep assertions, train on recurring mistake patterns, consider language features that avoid a known error class. Watch recent changes before release, change frequency, imports, complexity metrics (validate on your own history; the correlation differed across five projects), and dependency centrality.
- Quality assurance: all QA is limited. Test early and often, review code, improve analysis tools, calibrate coverage, and focus on risk: likelihood times severity, components that showed risk, components similar to risky ones, and code not yet covered. All of this holds only while the Pareto effect holds; if risk is evenly spread, spread QA evenly.

Space-shuttle style records (WPF ch. 16.8) store for each error when and how it was found, how it was introduced, how it slipped through each filter, how it was corrected, and whether similar errors may have slipped through the same holes. The aim is to find errors in the process, not just in code.

## 6. Correlation is not cause

Mined correlations are not causes (WPF ch. 16.7.5). Example: in one study a well-known senior developer's code was among the most defect-prone; the real reason was that the riskiest tasks go to the most experienced developers. Reassigning risky tasks to novices would have raised risk. Before acting on a correlation, ask for a theory of why it would be causal and how removing the feature would change the effect (the counterfactual test of `anomalies-and-causes.md` applied to process data). Never conclude "person X causes bugs" from raw counts (inferred in the notes).

## 7. Tools that make the next debugging session shorter

From PP ch. 3 (principles survive; the 1999 tools are dated):
- Source control for everything reproducible, always (even a one-week prototype): it is the project-wide undo, answers "who changed this line, what changed since last week, what broke the build", identifies releases so any release can be rebuilt, and supports maintenance branches. Automated, repeatable builds from the repository (with regression tests) are the hidden benefit. Check: a clean checkout builds and tests with one command; releases are tagged.
- Plain text for knowledge: configuration, logs, test data and fixtures in readable, self-describing text can be diffed, versioned and processed with generic tools, and survives the programs that wrote it. Check: could a stranger parse a record from a sample? does a diff show a meaningful change?
- The shell and one scriptable editor: ad hoc queries over files and logs are one-liners, repeated manual procedures become scripts, filtering and diffing logs of passing versus failing runs is a pipeline. Do not live only inside one GUI or IDE.
- A text-manipulation language (shell with awk and sed, Python, Ruby): glue, log analysis, data conversion, test-data generation; script a transformation once and put it in the build when it recurs. Scripts that rewrite sources should be reversible (back up, or rely on version control).
- Code generation from a single source of truth when the same fact (a schema, a message layout) is needed in several forms: generated forms are derived, so they cannot drift, and a dropped field becomes a compile error instead of a production failure. The generation must be part of the build and the output never hand-edited.
- Automated tests for debugging (WPF ch. 3.8): specify, test early, test first, test often, test enough (statement and branch coverage plus random inputs for extremes), have others test (authors are psychologically unsuited to test their own code), review (finds more defects per effort than testing), run anomaly detectors, assert.

## 8. Proportion

A two-line typo fix needs a regression test, a grep for siblings and a good commit message; it does not need a process study. Do the hotspot analysis and process questions when a failure was severe, recurred, or was hard to find. Do not turn a small request into a quality-programme proposal: offer it in a sentence at the end ("this file has had 6 fixes in a year; worth a review?").

## 9. Verify

- A regression test exists, failed before the fix and passes now, and sibling cases are covered.
- The grep for the same pattern was run and its results are listed (fixed or deliberately left).
- If an assertion, type or lint check was added, it was shown to fire on the old code.
- Any history-based claim cites the command that produced the numbers.
- Any process recommendation names the observed evidence and the proposed causal link, not just a correlation.
