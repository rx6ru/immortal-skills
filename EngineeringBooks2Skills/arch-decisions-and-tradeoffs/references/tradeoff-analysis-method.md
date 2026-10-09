# Trade-off analysis method

How to analyse a consequential "X or Y" choice so that the result can be explained, challenged and
recorded. Main source: Hard Parts ch. 2 and ch. 15; supporting material from Hard Parts ch. 1 and
ch. 3, Fundamentals ch. 1, Communication Patterns ch. 9.

## Contents

1. Starting position
2. The three-step method
3. Operating procedure (eight steps)
4. Technique: mutually exclusive, exhaustive option lists
5. Technique: decide in context
6. Technique: model domain scenarios
7. Technique: bottom line over overwhelming evidence
8. Technique: qualitative first, quantify where cheap
9. Table shapes to reuse
10. Worked examples from the sources
11. Sizing the analysis
12. Verify

## 1. Starting position

- Each architecture problem is a specific mix of organisation, technology and constraints, so the
  answer usually cannot be looked up. The task is to assess the trade-offs on each side of the
  decision objectively (Hard Parts ch. 1).
- Aim for the least-worst combination of trade-offs, not the best design. "Best" implies every
  competing factor is maximised at once, which does not happen (Hard Parts ch. 1).
- Everything is a trade-off; if an option appears to have none, the trade-off has not been found yet
  (Fundamentals ch. 1, first law and corollary).
- Record why, because the structure shows how a system works but not why it was chosen over the
  alternatives (Fundamentals ch. 1, second law).
- When judging a style or an inherited piece of advice, ask which constraints made it attractive and
  whether they still hold. Shared, centrally orchestrated service architectures fitted a period in
  which infrastructure and licences were expensive and shared; cheap, programmable environments
  changed the constraint and with it the sensible default (Hard Parts ch. 1; Fundamentals ch. 1).

## 2. The three-step method

Hard Parts ch. 2 and ch. 15:

1. **Find what parts are entangled.** Problems that look like one decision are usually several
   dimensions braided together. Pull them apart so each can be considered on its own, then put them
   back together.
2. **Analyse how they are coupled.** Two parts are coupled if a change in one might force a change
   in the other.
3. **Assess trade-offs by the impact of change** on the interdependent parts.

Notes on each step:

- Step 1. The entangled dimensions are specific to the system; people who know the ecosystem
  (developers, architects, operations) can find them. The simplest probe is "if someone changes X,
  could Y have to change?" For distributed systems, the authors found three dimensions that every
  architecture they examined was sensitive to: communication, consistency and coordination (see
  `coupling-and-quanta.md`). Treat that as a starting set and add columns for your own system.
- Step 2. Model combinations in a lightweight way and skip infeasible ones. The aim is to decide
  which forces deserve trade-off analysis. The authors' own concern list, beyond the three
  dimensions: coupling, complexity, responsiveness/availability, scale/elasticity.
- Step 3. Set up something you can iterate on with what-if scenarios. Fix the most fundamental
  dimension first because it limits what follows, then repeat for the next decision. When the
  entangled decisions are done, what remains is ordinary design.

No first draft is right. Build sample topologies for the workflows involved and a matrix view of the
trade-offs, then revise.

## 3. Operating procedure

Synthesised in the notes from Hard Parts ch. 15, with the cross-references added.

1. **Define the decision and the option list.** Apply the mutually-exclusive and exhaustive checks
   (section 4).
2. **List entangled dimensions and coupling points.** Static: operating system or container base,
   frameworks and transitive libraries, persistence (databases, search engines, cloud services),
   integration points needed to start, messaging infrastructure. Dynamic: communication, consistency,
   coordination.
3. **Pick the characteristics that matter for this context** from business drivers and the recorded
   characteristics list (`architecture-characteristics.md`). Rate each option qualitatively alone,
   then in one matrix.
4. **Fix the most fundamental dimension**, then iterate on subsequent decisions.
5. **Model two to four relevant domain scenarios** (a change, an extension, a complex or error
   workflow) against each option.
6. **Distil to a bottom-line statement** for the business owner.
7. **Record an ADR** with consequences; add fitness functions to guard the consequences; state the
   conditions under which the decision should be revisited.
8. **Where feasible, replace speculation with a spike or test** to quantify.

Before step 1 for anything large, confirm there is a business reason at all. "Nothing else works" is
not a justification; the sequence in Hard Parts ch. 3 is: understand the benefits of the proposed
change, match them to problems the current system demonstrably has, then analyse and document the
trade-offs and present a business case.

## 4. Technique: mutually exclusive, exhaustive option lists

Hard Parts ch. 15.

- **Mutually exclusive.** Options must not overlap in capability, or the comparison is unfair. A
  plain message queue against a full enterprise service bus is invalid, because the bus contains a
  queue plus many other components. Compare the messaging capability only.
- **Exhaustive.** Cover the whole option space. Evaluating only a service bus and a simple queue for
  high-throughput messaging, without a log-based broker, misses a category.
- **Recheck for new arrivals** before a long-lived decision; the option space changes.

How to apply as an agent:

1. Write the capability being chosen as a noun phrase ("asynchronous delivery of order events to
   three consumers").
2. List candidates; for each, strike out capabilities outside that phrase.
3. Ask what category of solution is absent (in-process, library, managed service, different
   paradigm, "do nothing").
4. Keep "do nothing / keep the current design" as an explicit option whenever it is viable.

Tension with the advice to keep at most three options (Communication Patterns ch. 12, myth 2): the
exhaustive check is about not missing a category; the limit is about how many to analyse in depth.
Enumerate widely, eliminate with a recorded one-line reason, score at most three. (This reconciliation
is an adaptation, not a statement from either book.)

## 5. Technique: decide in context

Hard Parts ch. 15, "out of context" trap.

A generic comparison can point one way and the real situation the other. In the shared service
versus shared library example, a generic matrix favours the library overall; once the specific
drivers of the situation are added, the weights of the criteria change and so does the decision.

Rules:

- Balance the right set of trade-offs for the situation, not every trade-off available.
- Narrowing to the applicable context removes options and makes the decision simpler. This is the
  practical route to a simple design.
- Write the context into the table header or caption so the table cannot be reused elsewhere as if
  it were general.

## 6. Technique: model domain scenarios

Hard Parts ch. 15.

Generic drivers are too generic to decide with. Take the choice between one payment service and one
service per payment type:

| Scenario | What it shows |
|---|---|
| Change how credit card processing works | Separate services isolate the change: better maintainability, testability, deployability. Cost: duplicated code, to avoid static coupling between the services |
| Add a new payment type (reward points) | Separate services show an extensibility benefit |
| One order paid with several payment types | Separate services need coordination, which costs performance and data consistency; this cannot be designed away |

Result: the real trade-off is performance and data consistency (single service) against
extensibility and agility (separate services). Nothing in a generic ratings table states that.

Choosing scenarios:

- One that changes existing behaviour in a place that changes often.
- One that extends the system in a direction the business has signalled.
- One that crosses the proposed boundary, or fails halfway.
- Each must come from an actual driver or requirement; a scenario nobody expects is noise.

## 7. Technique: bottom line over overwhelming evidence

Hard Parts ch. 15.

Stakeholders cannot decide from a wall of ratings. Reduce the analysis to a few key points, possibly
aggregates of several trade-offs, framed as outcomes.

Example, synchronous call versus asynchronous queue for starting a credit approval:

| | Advantages | Disadvantages |
|---|---|---|
| Synchronous | Approval is guaranteed to have started before the customer's request ends | Customer waits for the process to start; the application is rejected if the coordinator is down |
| Asynchronous | No wait; submission does not depend on the coordinator being up | No guarantee the process has started |

Bottom line put to the owner: is a guarantee that approval starts immediately more important than
responsiveness and fault tolerance?

Form to use: "Choosing A gives us [outcome] and costs us [outcome]. Choosing B gives us [outcome] and
costs us [outcome]. Which matters more: [A's outcome] or [B's outcome]?" Keep the detailed table as
backing material, not as the message.

Related advice from Communication Patterns ch. 9: lead with context (why are we deciding, who is
affected) before technical detail; connect each point to the next; prepare answers to predictable
objections, in writing as a short FAQ.

## 8. Technique: qualitative first, quantify where cheap

- Two architectures usually differ in too many ways for a true quantitative comparison; almost none
  of the trade-off tables in Hard Parts are quantitative. Ground qualitative ratings in patterns
  seen across many examples and in local experiments (Hard Parts ch. 15).
- For your own system, objective test results can turn a qualitative judgement into a number. More
  concrete facts allow a more precise analysis (Hard Parts ch. 15, epilogue).
- Agent adaptation: when the repository allows it, measure instead of estimating. Examples: count
  the call sites affected by each option with a search; run the existing test suite under both
  configurations; time a prototype. State the command and the result next to the rating it supports.

## 9. Table shapes to reuse

Ratings per option (one per option first, then merged):

```
Context: <the situation this table is valid for>

| Criterion (source)          | Option A | Option B | Option C |
|-----------------------------|----------|----------|----------|
| AC02 fault tolerance        | low      | high     | medium   |
| AC05 deployability          | ...      | ...      | ...      |
| Complexity to operate       | ...      | ...      | ...      |
Rationale per cell: <footnotes or a following list>
```

Scenario matrix:

```
| Scenario (driver)                    | Option A            | Option B            |
|--------------------------------------|---------------------|---------------------|
| Change <frequent change> (REQ 014)   | touches 1 service   | touches 3 services  |
| Add <expected extension>             | ...                 | ...                 |
| <cross-boundary or failure workflow> | ...                 | ...                 |
```

Bottom line: the two-row advantages/disadvantages table in section 7 plus one question.

Presentation notes (Communication Patterns ch. 10): introduce a table with a sentence; one kind of
data per column; short cells; where a rating glyph is used (stars, Harvey balls, traffic lights),
give the numeral or a text equivalent as well so the table survives greyscale and screen readers.

## 10. Worked examples from the sources

**Dynamic coupling matrix (Hard Parts ch. 2, ch. 15).** Rating each combination of communication,
consistency and coordination, then merging into one matrix, showed two relationships: coupling level
and scale/elasticity move inversely and directly so; coupling and responsiveness/availability also
move inversely, less directly, because the more services a workflow involves, the more likely a
single failure breaks it. The matrix itself is in `coupling-and-quanta.md`; selecting among the
eight patterns belongs to `arch-distributed-workflows`.

**One topic or per-consumer queues (Hard Parts ch. 15).** A bidding system needs a new consumer
(bid history). Option 1: keep one publish/subscribe topic and add a subscriber. Option 2:
point-to-point queues per consumer.

| Option | Advantages |
|---|---|
| Point-to-point queues | Different contract per consumer; finer security access and data control; an operational profile per consumer (separate scaling, queue-depth monitoring) |
| Publish/subscribe topic | Extensibility: adding a consumer is easy |

Costs of the single topic that scenario analysis surfaced: one contract for everyone (coordinated
changes; consumers receive data they do not need), every consumer sees every field including
personal data, and consumers cannot be scaled or monitored separately. The decision then goes to the
interested parties (operations, enterprise architecture, business analysts): which set matters more?

**Migrating a monolith (Hard Parts ch. 3).** Symptoms were mapped to drivers with evidence before
any option was chosen (table in `architecture-characteristics.md`), and the resulting ADR lists the
costs alongside the benefits: feature delay, extra cost, operational burden during the transition,
and the database having to be broken apart (ADR text in `adr-guide.md`).

**Extracting a service (Mastering API Architecture intro).** The decision to pull the attendee
component out of a three-tier system is recorded with its costs: the call becomes out-of-process and
adds latency that has to be tested; the new service can become a single point of failure; several
consumers mean design, versioning and testing discipline are needed to avoid breaking changes.

## 11. Sizing the analysis

| Decision | Analysis |
|---|---|
| Reversible within a day, one component | Two options, one sentence each on what is given up; note in the pull request |
| Affects several components or how others code | Steps 1, 3, 5 (one or two scenarios), 6; short ADR |
| Hard to reverse, cross-team, contested, or costly | Full procedure, extended ADR with scored options and consultation list; spike if cheap |

Do not extract services, add a gateway or adopt a mesh ahead of need; take the step when the need
shows up (Mastering API Architecture intro). Unknown unknowns make large up-front designs wrong in
ways that cannot be predicted, so plan to iterate (Fundamentals ch. 1).

## 12. Verify

From Hard Parts ch. 15 (marked inferred in the notes) plus adaptation:

- Each trade-off table compares same-category items and states its context.
- Every decision has an ADR with explicit downsides and a revisit trigger.
- Scenarios are tied to actual business drivers, each traceable to a requirement, ticket or stated
  goal.
- Any claim of "no downside" or a silver bullet is flagged as incomplete analysis.
- The bottom line is one question a non-technical owner could answer, and the answer selects an
  option.
- Each rating has a rationale; each number has a reproducible source.
- If the recommendation would change under a different weighting of two criteria, that sensitivity
  is stated.
