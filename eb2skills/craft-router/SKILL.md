---
name: craft-router
description: "Index of the craft-* skills (software engineering practice at the level of code and projects) that maps a task to the one or two skills worth loading and the order to use them in. Use when a coding, review, cleanup, bug-fix, test, planning or documentation task could fall under several craft skills, when a request is broad (\"improve this code\", \"review this PR\", \"take over this module\", \"get this project into shape\"), or when unsure whether a problem is about naming, structure, patterns, error policy, refactoring mechanics or tests. Skip it when one craft-* skill obviously fits; load that skill directly. For service and data architecture use arch-router; for functional style use fp-router."
---

# Craft skills: which one, and in what order

## Purpose

The craft skills come from ten books that overlap. This index keeps you from loading four skills
for one task or picking the wrong one. Find the row that matches what you were asked to do, load
the named skill, and stop there unless the task really spans two.

## Pick by what you were asked to do

| The task in front of you | Load | Why this one |
|---|---|---|
| Write a new function or file; "make this readable"; names, comments, formatting; review a diff for quality | `craft-clean-code` | Code-level readability and the smell checklist |
| Design a class, module or internal API; decide where code lives; split or merge; a change touches many files; wrap a library | `craft-module-design` | Structure, information hiding, coupling |
| "Should this throw, return null, or return a result?"; validation; resource leaks; assertions | `craft-error-handling` | Error policy is a design decision of its own |
| Restructure working code without changing behaviour; rename, extract, move; untested legacy code | `craft-refactoring` | Step-by-step mechanics that keep tests green |
| Something fails and the cause is unknown; flaky test; regression; huge failing input | `craft-debugging` | Reproduce, minimise, hypothesise, verify the fix |
| A pattern is named or implied: type switches, object creation in clients, subclass explosion, listeners, undo | `craft-design-patterns` | Choose by what varies; also when to remove a pattern |
| Write, review or repair tests; is the suite enough to refactor; mocks versus real | `craft-testing` | What to test and how to keep tests useful |
| Threads, async, locks, races, deadlocks inside one program | `craft-concurrency` | Shared state and schedule-dependent bugs |
| "How long will this take?"; break down a large task; coordinate subagents; vague requirements; rewrite proposals | `craft-planning-and-estimation` | Scope, sequence, staffing, honest status |
| Diagram, README, design doc, PR description, status update | `craft-technical-communication` | Readers and what they need |

## When a task spans several

Use the smallest sequence that covers the request.

| Request | Sequence |
|---|---|
| Fix a bug | `craft-debugging` to find and validate the cause; `craft-testing` only for the regression test's design if it is not obvious |
| Add a feature to awkward code | `craft-refactoring` to make the change easy, then make the change; consult `craft-module-design` only if you are choosing a new structure |
| Review a pull request | `craft-clean-code` for the line-level pass; `craft-module-design` if the PR adds or reshapes an interface; `craft-testing` for the tests |
| Take over an unfamiliar or legacy module | `craft-testing` and `craft-refactoring` (legacy sections) to get a safety net, then `craft-module-design` to judge the structure |
| "Make this extensible / pluggable" | `craft-module-design` first to check a simpler seam is not enough, then `craft-design-patterns` |
| Flaky test | `craft-debugging` to reproduce; `craft-concurrency` if the cause is shared state or scheduling |
| Plan and then build something large | `craft-planning-and-estimation` to scope and sequence; the building skills as each piece comes up |

## Boundaries between easily confused skills

- Readability inside a function is `craft-clean-code`; the shape of the interface between functions
  and modules is `craft-module-design`.
- Deciding *what* structure to move toward is `craft-module-design` or `craft-design-patterns`;
  getting there safely is `craft-refactoring`.
- Deciding how code should respond to failure is `craft-error-handling`; finding out why it is
  failing now is `craft-debugging`.
- Concurrency in one process is `craft-concurrency`; consistency across databases and services is
  `arch-transactions` and `arch-replication-and-consistency`.
- Typed results, folds and purity as a style are the `fp-*` skills; `craft-error-handling` covers
  the policy choice in any style.

## Verify you routed well

- You can state in one sentence what the user asked for and which row it matched.
- You loaded at most two craft skills for a single request, or you can say why a third was needed.
- The work you did answers the request as asked; a skill's wider checklist did not turn a small
  request into a large one.

## Proportion

Most requests need one skill or none. A one-line fix or a rename does not need a skill at all. Use
this index when the choice is unclear, not as a required first step.

## Sources

Clean Code; A Philosophy of Software Design; Refactoring (2nd ed.); The Pragmatic Programmer; The
Mythical Man-Month; Why Programs Fail; Design Patterns; Head First Design Patterns (2nd ed.);
Communication Patterns; with testing and concurrency material from Functional Programming in Scala
and Mastering API Architecture.
