---
name: craft-planning-and-estimation
description: Procedures for scoping, estimating, sequencing, staffing and reporting on software work, for one agent or a lead agent coordinating several. Covers estimation method and data, why effort is not linear in size or headcount, adding people or subagents to late work, conceptual integrity, specs and requirements, tracer bullets vs prototypes vs incremental build, milestones and honest status, second-system and feature creep, essence vs accident, build vs buy, and definition of done. Use when asked "how long will this take", to plan or break down a large task, to fan work out to subagents, when a plan is slipping, when requirements are vague, when someone proposes a rewrite or "v2", or when judging a tool's claimed speedup. Not for code-level design (craft-module-design), refactoring mechanics (craft-refactoring) or capacity numbers (arch-system-design).
---

# Planning and estimation

## Purpose

Most schedule and scope failures come from a few predictable errors: estimates that assume everything goes well, effort treated as interchangeable with progress, requirements treated as fixed, status reported as feelings instead of facts, and design split between several authors. Use this skill to catch those errors before they are built into a plan, and to respond correctly when a plan is already failing. The material comes from Brooks (The Mythical Man-Month, 1995 edition) and Hunt and Thomas (The Pragmatic Programmer, 1999); where Brooks retracted something in 1995 the skill says so, and the dated parts are marked.

The skill is about proportion. A one-file fix needs none of the planning machinery; a multi-day task with several workers needs most of it. Pick the rows that match the job.

## Choose what applies

| Situation | Do this | Read |
|---|---|---|
| Asked for an estimate ("how long", "how big", "is this feasible") | Classify the deliverable, estimate as a range with assumptions, keep the estimate separate from any wished-for date | `references/estimating.md` |
| Request is vague, or the user cannot say exactly what they want | Dig for the need behind the request, separate policy from requirement, show something small early | `references/requirements-and-specs.md`, `references/delivery-strategy.md` |
| Large task, unclear architecture, many unknowns | Build a thin end-to-end skeleton first, then grow it | `references/delivery-strategy.md` |
| One risky question (algorithm, library, UI feel, performance) | Prototype just that question, write down the lesson, discard the code | `references/delivery-strategy.md` |
| Lead agent about to hand work to subagents | Count independent subtasks, keep one owner of the design, brief narrowly, integrate one piece at a time | `references/orchestrating-subagents.md`, `references/staffing-and-partitioning.md` |
| Plan is slipping, or someone says "add more people/agents" | Measure the slip against a binary milestone, re-plan once, trim scope before adding workers | `references/staffing-and-partitioning.md`, `references/milestones-and-status.md` |
| Several people or agents must produce one consistent API, UI or design | Name one owner of the external interface, freeze or version it, log every clarification | `references/conceptual-integrity.md` |
| "Let's rewrite it", "v2 with everything we could not do before", a pile of feature requests | Run the second-system and premise checks, give each feature a budget and a named user | `references/scope-and-second-system.md` |
| A tool, framework, language or AI assistant is claimed to give a large speedup, or "should we build or buy" | Ask whether it attacks essence or accident, bound the gain, look for an existing product, require an independent happy user | `references/tools-and-build-vs-buy.md` |
| Need milestones, a status report, or a plan the user can check | Binary done-conditions, critical path, scheduled vs estimated dates, bad news early with options | `references/milestones-and-status.md` |
| About to say "done" | Run the done checks: full suite, regression test for each bug, clean build from scratch, stated limits | `references/done-and-verification.md` |
| Someone cites a Brooks rule ("1/3 1/6 1/4 1/4", "throw one away", exponent 1.5) | Check whether Brooks kept or retracted it | `references/brooks-propositions-revisited.md` |
| Need a specific Pragmatic Programmer tip | Look it up | `references/pragmatic-tips-index.md` |

This skill does not apply when:
- The change is small, the spec is clear and tests exist: do the work; use only the "done means" list below.
- The question is how to structure modules and interfaces: use `craft-module-design`.
- The question is how to change code safely without changing behaviour, or whether to refactor or rewrite at code level: use `craft-refactoring` (this skill only covers the planning side of rewrite decisions).
- The question is traffic, storage or latency capacity of a system: use `arch-system-design` or `arch-scalability-analysis`.
- The question is how to write the message, diagram or PR text itself: use `craft-technical-communication` (this skill covers what a status or plan must contain, not how to format it).
- The task is finding the cause of a failure: use `craft-debugging`. Debugging is largely sequential and cannot be sped up by adding workers, which matters for planning, but the method lives there.

## How to apply

### 1. Classify what is being delivered

Brooks separates four things that people call "a program" (Mythical Man-Month ch. 1). Name which one the user needs, because the effort differs by large factors.

| Deliverable | What it must satisfy | Rough effort vs the plain program |
|---|---|---|
| Program | Runs for its author, on their machine, once or for private use | 1x |
| Programming product | Generalised inputs, tested with a bank of cases including boundaries, documented so a stranger can use, fix, extend it | about 3x |
| Programming system component | Conforms to exact interfaces, stays within a resource budget, tested with its neighbours in all expected combinations | about 3x (more with many components) |
| Programming systems product | Both of the above | about 9x |

The multipliers are Brooks's rules of thumb, not measurements; he still held them roughly right in 1995. Use them to catch the common error of quoting a demo's effort for a production job. If the user says "script" and the context says "other teams will depend on it", say which one you are estimating.

### 2. Pin down what to build before sizing it

- Treat the first statement of a requirement as a hypothesis. Brooks: the hardest part is deciding precisely what to build, and clients cannot specify a modern product completely before trying versions of it.
- Separate need from solution and from policy. "Only supervisors may view the record" is a policy example; the requirement is "only authorised users may view it". Keep the policy configurable. Pragmatic ch. 7.
- Ask the few questions that change the design, then propose a mainline-only prototype or skeleton and ask what is wrong with it. More detail in `references/requirements-and-specs.md`.
- Record the quality bar as a requirement too: how good must this be? Ask, do not assume (Pragmatic Tip 7).

### 3. Estimate

Short form of the method (full version in `references/estimating.md`):

1. Decide how accurate the answer must be and quote in matching units (days for 1 to 15 days, weeks for 3 to 8 weeks, months for 8 to 30 weeks; beyond 30 weeks think hard before giving a number).
2. Find a comparable finished job and its actual cost. Estimate from tested, documented, integrated work, not from a demo or a sprint.
3. State scope and assumptions as part of the answer.
4. Build a rough model: list the components, how they combine, and the parameters that dominate (multiplied terms matter more than added ones).
5. Give a range and name what moves it. Do not give a coffee-machine number; "I will get back to you" is acceptable.
6. Include verification and integration explicitly. In Brooks's rule of thumb coding is only about one sixth of the schedule, with about half for test and debugging; treat that split as a warning against coding-only estimates, not as a formula (see "Proportion and limits").
7. Convert effort to time using productive hours, not nominal hours. Brooks cites teams realising about half the working week as programming.
8. Keep a record of estimate against actual and investigate any miss over 50% (Pragmatic challenge).
9. Never let the requested date replace the estimate. Present them separately and negotiate scope.

### 4. Choose the delivery strategy

| Situation | Strategy |
|---|---|
| Requirements or architecture unknown; need to find the target | Tracer bullet: a thin end-to-end path in production-quality structure that stays and grows |
| One specific risky question | Prototype it, state the question first, record the lesson, discard the code |
| User experience uncertain | Mock or mainline-only prototype the user can try; Wizard-of-Oz or state-machine mock is enough |
| Performance risk | Vertical slice: a small function set built fully, to expose performance problems early |
| Schedule or budget is a hard limit | Build-to-budget: grow from a running skeleton so there is always a shippable system, cut function not quality |
| Spec grows but no code runs | Stop specifying; build the tracer; keep detailed specs for interfaces and safety-critical parts |

Do not plan "build everything, test at the end", and do not plan a full throwaway build to be delivered if it works. Brooks retracted "plan to throw one away" in 1995 as a product of the waterfall model; the surviving advice is skeleton first, grow, show early. Details and the contrast with tracer vs prototype in `references/delivery-strategy.md`.

### 5. Partition and staff (people or agents)

Apply these rules, in this order:

1. Maximum useful workers is the number of truly independent subtasks. Minimum calendar time is set by the sequential chain. More workers cannot beat the chain.
2. Communication paths grow as n(n-1)/2, and each newcomer must be briefed (the training cost grows linearly). So prefer a star: one owner of the whole design, others in narrow support or implementation roles, each with a written brief.
3. Do not give two workers halves of one undecided design. Decide the interface first (one owner), then split implementation against it.
4. Adding workers to a late task makes it later, because of briefing, repartitioning and extra communication. Later studies that Brooks cites in 1995 found it always costlier, not always later, and that early addition is far safer than late. Details and the decision list in `references/staffing-and-partitioning.md`.
5. For a lead agent coordinating subagents, see `references/orchestrating-subagents.md`. That file is an adaptation of the team material; the notes contain no measurements for agents.

### 6. Set milestones that can be checked

- Every milestone is a concrete, binary, observable event decided in advance (tests pass, artefact built from a clean checkout, interface signed off), never "90% done" or "design complete".
- Draw the dependency chain, find the critical path and the slack on every other branch. Preparing the chart is where most of the value lies.
- Carry two dates per milestone: scheduled (the plan) and estimated (the current honest forecast), and keep the second unbiased.

### 7. Track and re-plan

When a milestone is missed:
1. Quantify the miss against the milestone, not a feeling.
2. Decide whether only the past part was misestimated or the whole estimate was uniformly low; default to the conservative assumption unless there is a specific local cause.
3. Choose one of: trim scope explicitly (best when delay is expensive), reschedule once with enough margin to avoid a second slip, or add capacity only under the conditions in `references/staffing-and-partitioning.md`.
4. Do not hold date, scope and staffing all fixed. The scope will then be trimmed silently by skipped design and skipped tests.
5. Report the slip when it happens, with options and their costs, and ask for a decision. Do not wait until the end of the task.

### 8. Finish

Apply `references/done-and-verification.md`. In short: the full test suite passes, each bug found has a regression test, the artefact builds from a clean state, limits and unverified areas are stated.

## Verify

Check the plan and the work with observable tests. Show the user the evidence.

Estimate and plan checks:
- The estimate states its deliverable class (program, product, component, systems product), its assumptions, a range, and the two or three parameters that move it most. If any is missing, the estimate is not finished.
- Test and integration are separate lines in the plan, not hidden inside "coding". Compare their share with half of the total; a much smaller share needs a stated reason (for example, strong automated tests already exist).
- The plan names the critical path. Count the independent subtasks; the number of concurrent workers must not exceed it.
- For T months of calendar time and M units of effort: compare T with 2.5 x M^(1/3) (Boehm, quoted by Brooks in 1995; the coefficient comes mostly from aerospace data). A plan under three quarters of that figure is a warning that no staffing level will rescue it; offer scope cuts.
- Every milestone has a one-line pass/fail test written before the work. Ask: could two honest people disagree about whether it happened? If yes, rewrite it.
- Each requirement is a need, not a UI widget or an architecture choice; policies are separate and linked; every noun has one glossary term.

Work checks, run in the repository:
- Fresh build: clone or copy to an empty directory, run the project's single build and test command, and show the result. If there is no single command, say so and name the manual steps. (Pragmatic Tip 61 and ch. 8.)
- Full suite, not a subset, before saying done. Show the pass count and anything skipped.
- For each bug fixed: show the test that failed before the fix and passes after. Pragmatic Tip 66.
- Integration happened one component at a time with the earlier tests rerun after each addition (Brooks ch. 13). Show the order and results.
- Scan for silent shortcuts: search the diff for TODO, stubs and commented-out code, and confirm each is deliberate, marked with a reason, and mentioned in the report (the "board up the broken window" rule).
- Compare the original request to the final result. List additions the user did not ask for; remove them or flag them.
- Status report test: could the user tell, from the report alone, what is finished (with proof), what is not, what changed from plan, and what decision is needed from them?

Done means:
- The deliverable class was named and matches what was built.
- The estimate or plan was given as a range with assumptions and was not replaced by a wished-for date.
- Milestones were binary and each is shown met or shown missed.
- The full suite passes; every fixed bug has a regression test; a clean-state build was run.
- Any slip was reported when seen, with options and their costs.
- Scope changes are recorded: who asked, what it cost in schedule, what was cut.
- What was not verified is stated.

## Proportion and limits

- Small, clear tasks: skip classification, estimation and milestones. Give a one-line estimate if asked and apply the done list. The cost of writing the five planning documents (objective, spec, schedule, budget, owners) is only repaid on work that spans sessions or workers.
- The 1/3, 1/6, 1/4, 1/4 split and the "half for testing" rule describe 1960s to 70s batch-era system programming and a sequential waterfall process; Brooks said in 1995 that the waterfall taints that rule. Modern automated tests spread verification through the work. What survives: writing code is a minority of the effort; specification, verification and integration dominate; they must be planned, not hoped for.
- The exponent 1.5 for effort against size is one study's figure; Boehm's data give 1.05 to 1.2 (Brooks, ch. 18 in 1995). Use it only for the direction: effort grows faster than size, and faster again with coupling.
- Productivity figures (statements per man-year) are dated and from assembly and PL/I; do not quote them as targets. The ratios (a seven-fold range with coupling, one to three to nine across application, compiler, operating system) are indicative.
- Brooks's Law is a first-order approximation, not a theorem. Well-partitioned work with low briefing cost can use more workers, especially if added early.
- Evidence for agents is thin. The notes support the mechanisms (briefing cost, merge cost, sequential constraints) but contain no measurements of agent parallelism. Treat the agent guidance as adaptation and measure the first cycle (time spent briefing and reconciling) before scaling a plan.
- Hustle and no-slip culture (ch. 14) can burn people out; use the mechanism (sharp milestones and early warning), not the pressure.
- Heavy specification can become the problem: Pragmatic ch. 7 warns of the specification spiral. Detail interfaces, safety-critical parts and library contracts; leave the rest to a running skeleton.
- Reversibility, abstraction layers and metadata all cost something (Pragmatic ch. 2 does not quantify it). Apply them where a decision is uncertain and expensive to change.

## References

- `references/estimating.md`: read when asked for an estimate, a schedule, feasibility or a sanity check on someone else's number. Method, data, rules and warning signs.
- `references/staffing-and-partitioning.md`: read when considering adding people or agents, splitting work, choosing team structure, or handling a late task. Task types, communication arithmetic, Brooks's Law and its refinements, surgical team, producer and technical director.
- `references/orchestrating-subagents.md`: read when a lead agent will delegate. Adaptation of the team material: brief template, topology, integration order, independent testing.
- `references/conceptual-integrity.md`: read when more than one author touches an interface or design, or when a spec must reach many implementers. Architect role, spec practice, record-keeping, frequency guessing.
- `references/requirements-and-specs.md`: read when requirements are vague, a spec is being written, or detail is growing without code. Digging for requirements, use cases, spec trap, glossary, documentation by reader need.
- `references/delivery-strategy.md`: read when choosing between tracer, prototype, skeleton, throwaway pilot, or planning integration and change. Includes the 1995 retractions.
- `references/milestones-and-status.md`: read when writing a plan to track, a status report, or handling hidden slippage. Milestones, critical path, scheduled vs estimated, status vs action, bad news.
- `references/scope-and-second-system.md`: read for rewrites, v2 plans, feature creep, size or latency budgets, and quality-level decisions.
- `references/tools-and-build-vs-buy.md`: read when evaluating a tool, language, methodology, library or AI assistant, or deciding to build, buy or reuse.
- `references/done-and-verification.md`: read before declaring completion, when designing tests for a plan, or when setting up automation to prove completion.
- `references/brooks-propositions-revisited.md`: read when quoting a Brooks claim, to see what he kept, revised or retracted by 1995.
- `references/pragmatic-tips-index.md`: read to find a Pragmatic Programmer tip by number or theme, with pointers to the sibling skills that cover the others.

## Sources

- The Mythical Man-Month, 20th Anniversary Edition (Brooks, 1995): prefaces and ch. 1 to 20, including ch. 16 (No Silver Bullet), ch. 17 (refired), ch. 18 (propositions), ch. 19 (after 20 years).
- The Pragmatic Programmer (Hunt and Thomas, 1999): ch. 1 (philosophy, communication), ch. 2 (estimating, tracer bullets, prototypes, domain languages), ch. 7 (requirements, specification trap, methods), ch. 8 (teams, automation, testing, documentation, expectations), the tip and checklist card (appendix X).
