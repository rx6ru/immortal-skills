# Orchestrating subagents (adaptation)

Contents: 1 Status of this file; 2 When to delegate; 3 Topology; 4 Order of work; 5 Brief template; 6 Roles; 7 Integration and verification; 8 Shared record and assumption drift; 9 What to do when delegated work is late; 10 Checklist

Status of this file: the books are about human teams. Each rule below is tied to the book idea it comes from, and the translation to a lead agent coordinating subagents is an adaptation. The notes contain no measurements of agent parallelism; treat the specifics as hypotheses and measure the first cycle (time spent briefing and reconciling against time saved).

Sources: MMM ch. 2, 3, 4, 6, 7, 12, 13, 19; PP ch. 2, ch. 8 section 41.

## 2. When to delegate

Delegate only when all hold:
1. The subtask is independent: it can be done without a decision that is still open elsewhere. The maximum useful number of workers is the number of independent subtasks (MMM ch. 2).
2. The brief is short enough to write in a few lines of goal, inputs, constraints and done-condition. If the briefing is as large as the work, do the work. Briefing is the training cost, and it cannot be partitioned.
3. The result can be checked cheaply against something external (a spec, a test, an interface), not only by reading it.

Do not delegate:
- Sequentially constrained work. A single fault hunt, an integration step, a decision that every later step depends on. Adding workers does not shorten a flat line (ch. 2).
- The design of something that must be coherent. Give one owner the design; delegate the support (see section 6).
- The first hour of a late task. Brooks's law applies to agents in the mechanisms, if not in the numbers: briefing time, repartitioning and reconciliation overhead.

## 3. Topology

- Use a star: the lead agent (or the human) holds the whole design and makes the decisions; subagents report to the lead, not to each other. The number of pairwise paths grows as n(n-1)/2, so a mesh costs more as agents are added. The surgical team's value is a radically simpler communication pattern (ch. 3).
- Keep the lead's context for decisions. The surgeon spends almost no time on administration (ch. 3); the lead should not be doing the routine work that a toolsmith, clerk or tester role can do.
- Recursion is allowed for large tasks: a master design partitioned at points where interfaces are minimal, each part with its own owner who reports on design to the master (ch. 19, architects). Add a level only when the lead cannot hold the interface set in mind.

## 4. Order of work

1. The lead settles or freezes the external interface first: data shapes, function signatures, file formats, error behaviours. Brooks: the architect writes the external specification; implementers may start scaffolding in parallel (data structures, module boundaries, tools) against stated cost and performance objectives while the spec firms up, but may not redefine the interface silently (ch. 4).
2. Do not hand two subagents halves of one undecided design and expect a coherent result. Split work after the interface is decided, or give both halves to one worker.
3. A thin end-to-end skeleton (stubs that run) goes in before the pieces. Subagents then replace stubs one at a time, and the system always runs (ch. 16, ch. 19; see `delivery-strategy.md`).
4. Integrate one component at a time, rerunning all earlier tests after each (ch. 13). Do not merge several subagent results at once and then debug the combination.

## 5. Brief template

Write a brief that a stranger could act on, which is the "training" cost paid once. Contents:

1. Goal in one sentence, and why it matters (the reason lets the worker make small decisions).
2. Inputs: files, interfaces and decisions already made (link to the shared record, do not retell).
3. Constraints: budgets (time, size, dependency, API shape), things that must not change.
4. Deliverable form: exactly what to return (patch, file path, findings list), and the format.
5. Done-condition that can be checked: tests that must pass, command to run, observable result.
6. Out of scope, and what to do if the worker discovers the interface is wrong: report it, do not patch around it.
7. What to report: what was done, what was not, what is uncertain.

## 6. Roles worth delegating (from the surgical team)

| Role | Brief it as | Why (book idea) |
|---|---|---|
| Tester / adversary | Write tests from the spec, not from the implementation; try to break the result | Independent product test is the project manager's daily adversary (ch. 6); developers will not report that they do not understand a spec, they will invent through the gaps (ch. 13) |
| Spec reviewer | Read the spec cold and list ambiguities, gaps, missing cases | An outside group should scrutinise the spec for completeness and clarity before code (ch. 13) |
| Copilot / critic | Read everything, advise, own nothing, no authority | Redundancy and a sounding board without diluting authority (ch. 3) |
| Researcher | Compare alternative strategies or find an existing package | Copilot researches alternatives (ch. 3); buy-before-build (ch. 16) |
| Toolsmith | Build the script, fixture or generator the lead wants | Toolsmith serves one surgeon's needs (ch. 3, 12) |
| Language / framework expert | Short study of a technique or API behaviour | Language lawyer (ch. 3) |
| Writer | Draft docs for the lead to own | Editor reworks the surgeon's draft; the surgeon writes it (ch. 3) |
| Clerk | Version control, CI logs, artefact store | Program clerk: all runs visible, all work team property (ch. 3) |

## 7. Integration and verification of delegated work

- Verify against an external check, not the subagent's own report. Brooks's theme: milestones are sharp events, and people soften bad news without intending to deceive when milestones are fuzzy (ch. 14). A subagent saying "done" is a status claim; the test result is the evidence.
- Keep a controlled baseline: one protected "current" version for integration, each worker in a playpen copy, promotion through an integration step with an owner who authorises change (ch. 12, ch. 13). In repository terms: worker branches or worktrees, a gate before merge.
- Scaffolding is normal: stubs, fixtures, miniature data files, test data generators. Brooks suggests that scaffolding code may amount to half as much as product code (ch. 13, rule of thumb).
- Regression: each merge reruns the whole prior suite, because each added piece can break earlier ones (ch. 13; ch. 11: a fix has a 20 to 50% chance of introducing another defect).
- Reuse with care: code written for one use becomes reusable only when treated as a product (generalised, tested, documented). Label subagent output as non-reusable unless built to that standard (ch. 17, 19).
- Define a stable test environment before blaming code: a flaky environment erodes the incentive to find your own bug (ch. 12, "dependable is not the same as accurate").

## 8. Shared record and assumption drift

Teams drift: as work proceeds, each part slowly changes its own function, size, speed and assumptions about inputs and outputs, and the neighbour depends on the old ones (ch. 7). With parallel agents this happens within a single session.

- Keep one shared contract (spec or interface file) and one decision log in the repository that every brief links to. Number and date entries so a worker can check what it lacks (ch. 7 workbook; ch. 6 telephone log).
- Any change that touches an interface (speed, size, input range, error behaviour) is announced to all affected workers and weighed by the lead; it is a spec change, not a local choice.
- Every clarification a subagent asks for is answered once and recorded where others see it, not only to the asker (ch. 6).
- Do not treat the current implementation as the spec unless doing characterisation: it carries accidental behaviour (ch. 6, "curios").
- State what is unspecified as well as what is specified, so no one assumes it is covered (ch. 6).
- Write the plan into the repository (objective and constraints, spec and acceptance tests, schedule and milestones, budget and limits, who or which agent owns what). Writing exposes gaps; the files are shared by all workers (ch. 10, five documents).

## 9. When delegated work is late or wrong

- Measure against the binary milestone. Do not wait for a final report.
- Do not add more agents to a late task as the first response. First trim scope or reschedule (see `staffing-and-partitioning.md`, late-project list).
- If the cause is a spec gap, fix the spec once and rebrief; do not let several workers each guess.
- Prefer one honest re-plan to repeated small slips ("take no small slips").
- Report to the user: what was delegated, what came back, what was verified, what was discarded.

## 10. Checklist

- Count independent subtasks; concurrent workers do not exceed it.
- Interface frozen or versioned before parallel implementation; one named owner.
- Skeleton runs before pieces arrive.
- Each brief has goal, inputs, constraints, deliverable form, checkable done-condition, escalation rule.
- Test author works from the spec, independent of the implementer.
- One component integrated at a time, full prior suite rerun each time.
- Decision log and shared contract exist and are linked from every brief.
- Subagent claims verified by running something, not by reading the claim.
- Time spent on briefing and reconciling was recorded, for the next plan.
