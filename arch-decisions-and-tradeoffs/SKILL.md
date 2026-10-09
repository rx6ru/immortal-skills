---
name: arch-decisions-and-tradeoffs
description: Provides a method for making, recording and governing architecture decisions - trade-off analysis (entangled dimensions, coupling, scenarios, bottom line), architecture characteristics as criteria, the architecture quantum, ADR templates and lifecycle, and fitness functions that enforce a decision in CI. Use when the user asks "should we use X or Y", "what are the trade-offs", "is this best practice", "write an ADR", "document why we chose", "justify this to the business", "describe the architecture", "enforce layering / stop dependency cycles", when a design is presented as having no downside, when a structural or hard-to-reverse choice is about to be made in code, or when a past decision keeps being re-argued. Covers the decision process and its record; the content of specific decisions (how to split a monolith, which saga, which database) belongs to sibling arch skills.
---

# Architecture decisions and trade-offs

## Purpose

Use this when a choice is structural, costly to reverse, or affects how other people write code.
It replaces "pick the best practice" with a repeatable sequence: name the options, find what is
coupled to what, rate the options against the characteristics that matter in this context, test them
with scenarios, state the bottom-line trade-off, record it, and add an automated check so the
decision keeps holding. The output is a decision someone else can audit and a rule that cannot rot
silently.

Two working assumptions run through everything here (Fundamentals of Software Architecture ch. 1;
Hard Parts ch. 1): every architecture choice trades something away, so an option with no stated
downside is an unfinished analysis; and the reason for a choice outlasts the mechanics of it, so the
reason has to be written down.

## Choose what applies

| Situation | Do this | Read |
|---|---|---|
| "X or Y?" on a structural choice (style, communication, data ownership, shared library vs service, build vs adopt a platform piece) | Run the trade-off procedure below; end with a bottom-line statement and an ADR | `references/tradeoff-analysis-method.md` |
| The user asks for an ADR, or a decision was just made in the conversation and meets the "needs an ADR" test | Write the ADR in the repository's existing format, or pick one with the chooser below | `references/adr-guide.md` |
| A decision keeps being reopened, or a newcomer asks "why is it like this" | Write a retrospective ADR for the past decision; answer by linking to it | `references/adr-guide.md` |
| Requirements say "fast", "scalable", "agile", "secure" with no numbers | Turn each into a named characteristic with a measurable definition, scope and source; cap the list | `references/architecture-characteristics.md` |
| "Do we need to break this up / go distributed?" at the level of justification | Map the actual symptoms to the five modularity drivers; consider a modular monolith first | `references/architecture-characteristics.md`, then `arch-decomposition` for how |
| Need to know what a change touches, or whether "microservices" really are independent | Count architecture quanta; draw the static coupling diagram | `references/coupling-and-quanta.md` |
| A rule exists only in a document or in reviewers' heads (layering, no cycles, banned dependency, latency budget) | Add a fitness function to CI or monitoring | `references/fitness-functions.md` |
| A proposal is described as "best practice", "industry standard", a silver bullet, or you notice you are advocating | Run the pitfall checks before continuing | `references/decision-pitfalls.md` |
| You are about to recommend or record a decision and have only looked for support for it, a decision is being made fast with no dissent, or a retrospective ADR is being written after an incident | Run the bias countermeasures: look for counter-evidence, add "what would change this decision?", consult people who differ | `references/decision-pitfalls.md` (2.5, 2.6) |
| Asked to "describe the architecture" | Report four things: structure (style), characteristics, decisions (rules), design principles (guidelines) | this file, "Describe an architecture" |
| Asked to write team rules or standards | Decide rule vs guideline for each item; rules get a variance path and a fitness function | this file, "Rule or guideline" |

This skill does not apply when:

- The choice is local and cheap to reverse (a variable name, a private helper's shape, which of two
  equivalent library calls). Decide and move on; see `craft-module-design` for module-level design.
- The user has already decided and asked for implementation. Implement it; mention a trade-off only
  if it is serious and not yet acknowledged, and offer an ADR in one line instead of writing one
  unasked.
- The question is which specific pattern to use inside an already-chosen direction (which saga,
  which decomposition pattern, which isolation level, which API style). Use the sibling skill for
  the content and return here only for the record and the governance.
- A system-from-scratch design is wanted: start with `arch-system-design`, which hands decisions
  back here.

## How to apply

### 1. Decide whether this is an architecture decision

Treat it as one if any of these hold (Communication Patterns ch. 12; Hard Parts ch. 1; Mastering
API Architecture intro):

- it changes how developers write the software, or constrains what they are allowed to do;
- it is hard or expensive to change later;
- it is long-lasting or spans several components or systems;
- it has effects outside the team;
- it keeps being revisited, or new team members keep asking about it;
- it is complex enough that the reasoning will not be obvious from the code;
- you are adopting another team's or company's decision (write your own record and reference theirs).

An architecture decision should guide a technology choice more often than make it: "use a reactive
UI framework" is an architecture decision, "use React" is a technical one. Name a specific
technology in the decision only when a characteristic (scalability, performance, availability)
depends on that specific technology (Fundamentals ch. 1).

### 2. Run the trade-off analysis

The underlying method has three steps: find what is entangled, analyse how it is coupled, assess
trade-offs by the impact of change (Hard Parts ch. 2, ch. 15). As an operating procedure:

1. **State the decision and the options.** Make the list mutually exclusive (compare like with like:
   a message queue against the messaging capability of an integration hub, not against the whole hub)
   and exhaustive (no credible category missing). Check for options that became available recently.
2. **List what is entangled.** Coupling test: if someone changes X, might Y have to change? Static
   side: runtime, frameworks and transitive libraries, databases and other stores, brokers, anything
   needed to boot the part. Dynamic side: communication (sync or async), consistency (atomic or
   eventual), coordination (orchestrated or choreographed). Add dimensions specific to this system.
3. **Pick criteria from this context.** Start from the system's recorded architecture
   characteristics and business drivers, not from a generic list. A generic matrix can favour one
   option and the real context the other, because context changes which criteria carry weight.
4. **Rate each option on its own, then side by side.** Ratings are qualitative (low/medium/high or
   0-5). Write a one-line rationale per cell.
5. **Fix the most fundamental dimension first** (often sync vs async), because it removes later
   options; then iterate on the decisions that follow from it.
6. **Model two to four domain scenarios against each option**: a likely change to existing behaviour,
   a likely extension, and a complex or failure workflow. Scenarios expose costs a ratings table
   hides (for example, separate services look better until a workflow needs all of them at once and
   pays in coordination, performance and consistency).
7. **Reduce to a bottom line.** One sentence of the form "is A more important than B?" in outcome
   terms a non-technical owner can answer, with the full table available behind it.
8. **Record and guard.** Write the ADR including negative consequences and a revisit trigger; add a
   fitness function for each consequence that can be checked mechanically.
9. **Replace speculation with a measurement where that is cheap**: a spike, a benchmark, a test on
   the actual system turns a qualitative rating into a number for this system.

For a small decision, steps 1, 3, 6 (one scenario) and 7 in a few sentences are enough. The full
procedure, worked examples and table shapes are in `references/tradeoff-analysis-method.md`.

### 3. Make criteria measurable

A characteristic that cannot be measured cannot be decided on or governed.

- Composite words hide several characteristics. "Agility" is maintainability + testability +
  deployability; decompose until each part has an observable measure (Hard Parts ch. 1, ch. 3).
- Keep the explicit list short: no more than seven chosen characteristics, with a top three agreed
  with stakeholders. Feasibility, maintainability, security and simplicity are implicit and do not
  count against the seven unless promoted (Communication Patterns ch. 12).
- Give each an ID, the part of the system it applies to, and its source requirement, so ADRs can
  cite it (for example `AC02 Fault tolerance - Payment interface - REQ 025/026`).
- Operational characteristics are scoped to an architecture quantum, not to the whole system. Two
  parts that share a database or are joined by a synchronous call cannot have independent
  scalability or availability targets (Hard Parts ch. 2).

### 4. Check coupling before believing a diagram

An architecture quantum is an independently deployable artifact with high functional cohesion, high
static coupling and synchronous dynamic coupling. To count quanta: list every deployable and every
operational dependency; merge anything that shares a dependency it needs in order to run (a shared
database is the usual one, a tightly coupled UI is another); count the disjoint sets that could each
be started alone in a production-like environment. Monoliths, service-based systems with one
database, and event-driven systems with one shared database are all a single quantum. Use the count
to decide the blast radius of a change and to reject claims that characteristics can be tuned per
service when the services are one quantum. Details and the style-by-style table:
`references/coupling-and-quanta.md`.

### 5. Write the ADR

Format chooser. The sources give three templates that differ in size and status vocabulary; none is
wrong, so choose by context:

| Context | Format |
|---|---|
| The repository already has ADRs | Match the existing template, numbering and status words exactly |
| Recording a decision already made, small team, record-only | Short form: Title, Status, Context (with alternatives), Decision (with justification), Consequences (with trade-offs) |
| The ADR is the vehicle for making the decision, several stakeholders, or the choice is contested | Extended form: Title, Status, Context, Evaluation criteria, Options (scored), Decision, Implications, Consultation |

Rules that hold in every format:

- The title states the decision, not the topic: "012 Use orchestration for the primary ticket
  workflow", not "Workflow coordination". A directory listing then reads as the list of decisions.
- Context answers why the decision is needed now and in what environment: assumptions, constraints,
  drivers. A sentence or two plus the alternatives, not an essay.
- Options are the ones actually considered, each with its trade-offs, including trade-offs that did
  not map to a criterion (they matter on a later revisit).
- The decision is short and carries its reason. If advice was received and not followed, say why.
- Consequences list negatives as well as positives. An ADR with no negative consequence is
  incomplete.
- An ADR is immutable once decided, except for its status. To change a decision, write a new ADR and
  set the old one to "Superseded by ADR-NNN" with the date.
- Store ADRs with the product (for a repository, `docs/adr/` linked from the README), not with a
  project, ticket or pull request, and link to them from the code and diagrams they explain.
- Detail is proportional to the ramifications. Show inputs and method for any calculation so it can
  be repeated.

Templates, status vocabularies, the options scoring table, a review checklist and worked examples:
`references/adr-guide.md`.

### 6. Govern with fitness functions

Documenting a rule does not enforce it. A fitness function is any mechanism that gives an objective
integrity assessment of one or more architecture characteristics: a structural test, a metric
threshold, a monitor, a chaos experiment, or a manual pipeline stage.

1. For each rule or consequence in the ADR, ask what observable fact would show it has been broken.
2. Choose the mechanism: structure (cycles, layer access, forbidden imports) as a test in the build;
   operational targets (latency, elasticity, queue depth) as load tests or monitors; third-party
   risk as a dependency scan in the pipeline; things that need human judgement as a manual stage.
3. Give it an objective pass condition, a number or true/false.
4. Run it continuously, on every change to code, schema, deployment configuration or the fitness
   functions themselves. A check that runs only on demand validates nothing.
5. Reference the ADR in the check's name or failure message so a failing build explains why the rule
   exists.

To tell a fitness function from an ordinary test, ask whether domain knowledge is needed to run it.
Validating an address needs domain knowledge and is a functional test; checking that no package
cycle exists does not and is a fitness function. Catalogue with implementations per language:
`references/fitness-functions.md`.

### Rule or guideline

- A **decision** is a rule: it constrains absolutely ("only the service layer may touch the
  database"). Give it a variance path, meaning a named way to request an exception that is granted
  or refused on its justification and trade-offs, and a fitness function.
- A **design principle** is a guideline: it steers and leaves judgement ("prefer asynchronous
  messaging between services; synchronous calls are allowed where they fit better"). No variance
  process, usually no hard-failing check.

Write a rule when a violation would defeat a characteristic; write a guideline when you cannot
enumerate the conditions in advance (Fundamentals ch. 1).

### Describe an architecture

Report four dimensions: the structure (style or styles), the characteristics it must support, the
decisions (rules, with links to ADRs), and the design principles. Naming the style alone ("it is
microservices") describes only the first. When reading an unfamiliar repository, existing ADRs,
dependency-rule tests and CI gates are where the second, third and fourth are found; say explicitly
when they are absent.

## Verify

Check the analysis:

- The options compared are the same kind of thing, and a search of the option space turned up no
  missing category. Evidence: the option list with one line on each eliminated candidate.
- Every criterion traces to a business driver, a requirement or a recorded characteristic ID.
  A criterion with no source is a personal preference; remove it or find its source.
- Every option has at least one stated disadvantage. If the chosen option has none, the analysis is
  not finished.
- At least one scenario is a change or failure case taken from this domain, and each scenario is
  evaluated against every option.
- The bottom line is a single either/or statement in outcome terms, and it follows from the table.
- Any number in the analysis (cost, latency, load) has its inputs and method shown, or is labelled
  an estimate.
- Bias check: the analysis names at least one piece of evidence against the chosen option and the
  condition that would change the decision, and says which sources were found that disagree.

Check the ADR (run against the file; each item has an observable answer):

- Title states the decision and has an identifier; filename matches.
- Status is one of the repository's allowed values, with a date.
- Alternatives are named; at most three scored in depth; each has trade-offs.
- Criteria are present (extended form) and cite characteristic IDs where a list exists.
- Consequences contain at least one negative and at least one follow-up or revisit trigger.
- A superseded ADR differs from its prior version only in its status line: check with
  `git diff` or `git log -p -- docs/adr/NNN-*.md`.
- It is linked: `grep -rn "ADR-NNN\|adr/NNN" .` finds a reference from a README, code comment,
  diagram or the fitness function that guards it.

Check the governance:

- Each rule stated in a Decision section has a matching automated check, or a written reason why it
  cannot be automated and a manual stage instead. List rule to check as a two-column table for the
  user.
- The check fails when the rule is broken. Prove it once: introduce a deliberate violation on a
  scratch branch (an import across a forbidden layer, a cycle), run the check, see it fail, revert.
  Show the failing output.
- The check is wired into the pipeline that runs on every change, not left as a script. Evidence:
  the CI configuration line that invokes it.
- Each promised operational characteristic has a numeric threshold and a place where it is measured.

Check the quantum claim, when one was made: each candidate independent unit can be started with only
its declared dependencies present (inferred from the definition in Hard Parts ch. 2), and no data
store or required runtime component is shared with another unit.

Done means:

- the decision, the alternatives and the reason are in a file stored with the product;
- the negatives are written down and a human has seen the bottom-line trade-off;
- every mechanically checkable rule has a check that has been seen to fail and to pass;
- anything left unverified or estimated is labelled as such in the reply to the user.

## Proportion and limits

- Cost. A full analysis with scored options and consultation takes real effort and produces a
  long document.
  Spend it where the decision is hard to reverse. For reversible choices a three-line record in the
  pull request description is enough; for trivial ones, nothing.
- Too much process gets bypassed. Gating every change on an approved ADR, or building many
  interlocking fitness functions that block teams, produces workarounds. Add a check when a rule
  matters and has been or is likely to be broken, not for every sentence in a document.
- Qualitative ratings are not measurements. Hard Parts ch. 15 holds that comparing two architectures
  is almost always qualitative; Communication Patterns ch. 12 and app. A score options out of five
  and total them. Use the scores to make reasoning visible and comparable, write a rationale per
  score, and do not let a small difference in totals decide: unweighted totals ignore that context
  makes some criteria dominant. If the total and the scenario analysis disagree, say so and resolve
  it explicitly.
- Option count. One source asks for an exhaustive option space, another for at most three options
  to avoid choice overload. A workable reading (adaptation): enumerate widely to check nothing is
  missing, eliminate quickly with one recorded line each, and score at most three in depth.
- Status vocabulary is contested (Proposed/Accepted/Rejected/Superseded versus
  Draft/Decided/Superseded versus "every recorded ADR is approved"). Follow the repository; see
  `references/adr-guide.md` for how to choose in a new one.
- Source limits. The copy of Fundamentals of Software Architecture behind this skill contained only
  the front matter, chapter 1 and the first page of chapter 2. Its later material (characteristic
  catalogues, style ratings, risk storming, connascence) is not reproduced here; where such an item
  appears it is cited to the book that actually carried it in the notes. Tool names in the sources
  (JDepend, ArchUnit, NetArchTest) date from around 2020-2022; equivalents for other languages in
  the references are adaptations.
- Context expires. Styles became dominant under constraints of their time (licence cost, shared
  infrastructure, manual operations). Re-examine a decision older than about three years, or
  whenever one of its recorded assumptions stops being true.
- As an agent you cannot do the consultation yourself. Draft the ADR with status Draft or Proposed,
  list who should be consulted and what question each should answer, and leave the status change to
  the user.

## References

- `references/tradeoff-analysis-method.md` - read when running a real "X or Y" analysis: the full
  procedure, MECE check, scenario modelling, bottom-line distillation, table shapes, worked examples.
- `references/architecture-characteristics.md` - read when choosing or defining criteria, making a
  vague quality measurable, building the characteristics register, or justifying modularity with the
  five drivers.
- `references/coupling-and-quanta.md` - read when judging independence of parts, counting quanta,
  drawing a static coupling diagram, or reasoning about the three dynamic coupling dimensions.
- `references/adr-guide.md` - read before writing or reviewing an ADR: three templates, statuses and
  lifecycle, per-section guidance, options scoring table, storage, review checklist, worked ADRs.
- `references/fitness-functions.md` - read when turning a rule into an automated check: definition,
  classification, catalogue of examples with what each governs and how to run it in CI.
- `references/decision-pitfalls.md` - read when a proposal sounds too good, when you or the user are
  advocating, when a decision process is stuck, or to review a decision for bias (confirmation,
  hindsight, groupthink) and process errors.

## Sources

- Software Architecture: The Hard Parts - ch. 1 (no best practices, ADRs, fitness functions,
  definitions), ch. 2 (coupling, architecture quantum, dynamic coupling dimensions), ch. 3
  (modularity drivers, business case), ch. 15 (build your own trade-off analysis), app. A (ADR and
  trade-off table index).
- Fundamentals of Software Architecture, 1st ed. - preface and ch. 1 (four dimensions, decisions vs
  principles, expectations of an architect, the two laws), first page of ch. 2, and the table of
  contents as a map only.
- Communication Patterns - ch. 8 (battling bias), ch. 9 (ethos, pathos, logos; reasoning and counterarguments), ch. 10
  (products over projects, abstractions over text, perspective-driven documentation), ch. 12 (ADRs,
  architecture characteristics, documentation as code), app. A (ADR templates).
- Mastering API Architecture - introduction (evolutionary framing, ADR format and worked example,
  ADR guideline tables, C4 levels).
