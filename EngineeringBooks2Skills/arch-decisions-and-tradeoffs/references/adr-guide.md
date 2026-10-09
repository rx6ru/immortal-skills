# ADR guide

How to write, store, review and maintain architecture decision records. Sources: Communication
Patterns ch. 9, ch. 10, ch. 12, app. A; Hard Parts ch. 1, ch. 3, ch. 15, app. A; Mastering API
Architecture intro; Fundamentals ch. 1.

## Contents

1. What an ADR is for
2. When to write one
3. Three templates and how to choose
4. Status vocabularies and lifecycle
5. Section-by-section guidance
6. The options scoring table
7. Content rules
8. Storage, naming and linking
9. Process: consultation and commitment
10. Getting ADRs adopted
11. Common mistakes
12. Review checklist
13. Worked examples from the sources
14. ADR guideline tables for "it depends" questions
15. Verify

## 1. What an ADR is for

A short record of an architectural decision and the reasoning behind it, written for all
stakeholders and usable during the decision process itself, not only afterwards. The format was
popularised by Michael Nygard. Typical length is one to two pages of plain text or Markdown
(Hard Parts ch. 1; Communication Patterns ch. 12).

Problems it prevents (Communication Patterns ch. 12):

- a later team reverses an early decision without knowing which requirement it served;
- the same decision is re-argued again and again;
- the same onboarding questions are answered verbally each time;
- the person who knew the reasoning leaves.

It is the practical answer to "why is more important than how": a system can be inspected to see how
it is built, but not why it was built that way over the alternatives (Fundamentals ch. 1). It is
also where trade-off analysis and counterarguments are kept: the record shows why alternatives were
discounted, and remains useful long after (Communication Patterns ch. 9).

## 2. When to write one

Any one of these is enough (Communication Patterns ch. 12):

- the decision changes how developers write the software;
- it is hard or expensive to change;
- it keeps being revisited;
- it keeps coming up from new team members;
- you are adopting another team's or company's decision: write your own ADR and reference theirs;
- it is long-lasting or affects several components or systems;
- it has an effect outside the team (use the Consultation section);
- it is complex or hard to understand;
- you would otherwise propose it informally or through an RFC. An ADR can replace the RFC or
  document it; a rejected RFC becomes a decided ADR that records the rejection.

Hard Parts ch. 1 puts it more briefly: write one for each consequential structural decision.

Not needed: decisions that are local, obvious from the code and cheap to reverse.

Agent behaviour: when a qualifying decision is made during a task and the repository has an ADR
directory, draft the ADR as part of the change. When there is no ADR practice, offer one in a line
and put the reasoning in the pull request description meanwhile.

## 3. Three templates and how to choose

### A. Short form (Hard Parts ch. 1)

```
# ADR: <short noun phrase naming the decision>

## Context
One or two sentences on the problem, then the alternatives considered.

## Decision
The decision, with detailed justification.

## Consequences
What follows once the decision is applied, and the trade-offs considered.
```

This format assumes every recorded ADR is approved, so it carries no status.

### B. Four-section form with status (Mastering API Architecture intro)

```
# ADR<NNN>: <title>

| Status       | Proposed / Accepted / Rejected / Superseded |
| Context      | the situation, forces, constraints; the problem and its bounds |
| Decision     | what we will do and how |
| Consequences | trade-offs, risks, follow-ups |
```

### C. Extended form (Communication Patterns ch. 9, ch. 12, app. A)

```
# <NNN> <Title: a statement of the decision made>

## Status
Draft | Decided | Superseded by ADR-XXX      (date of last status change)

## Context
Why the decision is needed and in what environment. Assumptions, constraints, decision drivers.

## Evaluation Criteria
What matters for this decision. Which architecture characteristics (by ID) apply.
Whether any constraint or driver should become a criterion.

## Options
Each option outlined and scored against the criteria, plus trade-offs outside the criteria.

## Decision
The choice and why. Short; the detail is in the other sections.

## Implications
Positive and negative consequences.

## Consultation
Advice received, who was invited (even if they did not respond), research and references and the
conclusions drawn. Optional. Placed last because it grows long; it happens before the decision.
```

### Choosing

| Situation | Template |
|---|---|
| The repository already has ADRs | Whatever is there. Consistency of the set matters more than the template |
| Recording a decision already taken; small team; nobody needs persuading | A, or B if a review step exists |
| The ADR will circulate for comment and approval | B at minimum |
| Several viable options, a contested or expensive choice, stakeholders outside the team, or criteria that must be visible | C |
| An ADR tool is in use | The tool's template; add missing sections as subsections |

The templates disagree on how much to separate. A and B fold alternatives and criteria into Context;
C breaks them out because, in that author's experience, they are otherwise omitted. If you use A or
B, still write the alternatives and what they were judged on; the short form does not excuse leaving
them out.

Both ends are legitimate purposes: a pure record, and a living document for collaboration,
persuasion and decision making. The same decision can be written in a detailed persuasive form and a
short record form (Communication Patterns ch. 12).

## 4. Status vocabularies and lifecycle

| Source | Statuses | Reasoning |
|---|---|---|
| Hard Parts ch. 1 | None; each recorded ADR is taken as approved | Keeps the format minimal |
| Mastering API Architecture intro | Proposed, then Accepted or Rejected, later Superseded | The ADR is published for comment and moved to accepted; rejected ADRs are kept because they record a change in perspective |
| Communication Patterns ch. 12 | Draft, then Decided, then Superseded by ADR-XXX | Most decisions choose one of several options instead of answering yes or no, so "accepted/rejected" fits poorly; the outcome is in the title and Decision section. Complex status sets are discouraged |

The notes also record that the classic Nygard set is Proposed, Accepted, Deprecated, Superseded.

How to decide:

- Existing repository convention wins.
- If ADRs are proposals that reviewers approve or turn down as a whole (the ADR is the pull
  request), Proposed/Accepted/Rejected reads naturally.
- If ADRs are worked on until an option is chosen, Draft/Decided reads naturally; a rejected proposal
  is recorded as a decided ADR whose decision is "do not adopt X".
- Whichever set is chosen, keep it small and write the allowed values at the top of the ADR index.

Lifecycle rules common to the sources that discuss them:

- An ADR is immutable once decided or accepted, except for its status line. Rejected ADRs are kept
  too.
- To change a decision, write a new ADR. Set the old one's status to "Superseded by ADR-NNN" and
  record the date.
- Decision making is iterative before the decision: revise the draft freely, update it with feedback,
  then finalise. After commitment, revisit only on new information, and then by superseding.

## 5. Section-by-section guidance

**Identifier and title.** Number plus the decision itself, not the topic: "001 Use event-driven
architecture". Use the same text for the filename. Reading the list of filenames should tell a
newcomer every decision made.

**Status.** One value from the chosen set, with the date it last changed.

**Context.** Answers "why does this decision need to be made, and in what environment?" Include
assumptions, constraints and decision drivers. State the problem and its bounds; it is not a blog
post. In the short forms, list the alternatives here.

**Evaluation criteria.** Often left out, and necessary to understand how options were compared.
Start from the product's architecture characteristics, since those are the agreed priorities, and
cite them by ID. Other sources of criteria: enterprise or business alignment, constraints (law,
data protection, licences, cost), security (data residency, encryption at rest), other functional
requirements.

**Options.** Aim for no more than three analysed in depth. Evaluate each against the criteria, and
also state each option's trade-offs whether or not they map to a criterion, because they may matter
when the decision is revisited.

**Decision.** A simple statement of the choice and why. Hard Parts asks for detailed justification
here; Communication Patterns keeps it short and puts the detail in criteria and options. Either way
the reader must find the reason without leaving the ADR. If advice was received and not followed,
give the reason here.

**Consequences / implications.** Always include negatives. Negatives warn the reader; positives
explain why the negatives were accepted. Include follow-up work the decision creates (for example
"latency of the new out-of-process call must be tested"), and the trade-offs that were weighed.
Add the conditions under which the decision should be revisited (Hard Parts ch. 15).

**Consultation.** Who was invited to give input, including those who stayed silent; advice received,
distinguished from opinion; research and references with the conclusions drawn. It keeps the
decision owner accountable for an informed decision. Not all advice has to be followed, since advice
can conflict.

## 6. The options scoring table

Communication Patterns app. A, Table A-1. One table per option, one row per criterion.

```
Option: <name>

| Criteria                 | Score       | Rationale        |
|--------------------------|-------------|------------------|
| AC01 <criterion>         | ★★★☆☆ 3/5   | why this score   |
| AC02 <criterion>         | ☆☆☆☆☆ 0/5   | why this score   |
| <constraint as criterion>| ★★★★☆ 4/5   | why this score   |
| <criterion>              | ★★☆☆☆ 2/5   | why this score   |

Total: 9/20
Other trade-offs: <anything not captured by the criteria>
```

- Score out of five; show stars or a Harvey ball and always the numeral too (Communication Patterns
  ch. 10: never more than five stars; glyphs need a text equivalent).
- The Rationale column is the point of the table. A score without a reason cannot be challenged.
- Total = 5 times the number of criteria; compare totals across options.

Caution, because the sources pull in different directions. Hard Parts ch. 15 treats architecture
comparison as qualitative and warns that context changes which criteria carry weight; a plain total
treats all criteria as equal. Use the total as a summary, not as the decision rule. If the option
with the highest total is not the one chosen, say why in the Decision section; that is a normal
outcome when one criterion dominates.

## 7. Content rules

Communication Patterns ch. 12, unless marked.

- **Show your work.** Include the inputs and method of any calculation, or link to the calculator
  used with the date, since prices change. The reader should be able to repeat it.
- **Control length.** Showing work makes the ADR long. Link to external data, or fold detail away
  (in Markdown, a `<details>` block with a `<summary>`).
- **Detail proportional to ramifications.**
- **Link both ways.** Reference ADRs from code, other documents and diagrams so a reader of the code
  finds the reasoning.
- **Tell the story of the decision** (Communication Patterns ch. 9): what happened before, the
  turning point where change became necessary, what will be done now, what will happen next. A
  couple of sentences in Context is enough.
- **Preempt objections.** Record why each alternative was discounted. For a contested decision, add
  a short FAQ of predicted objections. Some objections are subjective ("too slow to implement"): it
  may mean the criteria need revisiting, or it may be a difference of opinion.
- **Be transparent** (Communication Patterns ch. 9): state assumptions and any interest or bias that
  bears on the recommendation, and cite sources that disagree as well as those that agree.
- **Cite durable sources.** Link directly; for web sources that may change, cite an archived copy.
- **Attach the diagram that changed** (marked inferred in the notes for Mastering API Architecture):
  when a decision is an evolution step, redraw the context or container diagram for the step and
  link it from the ADR.

## 8. Storage, naming and linking

- **Store against the product or system, not the project.** Project-organised knowledge is lost or
  forgotten when the project ends, and later teams break things without knowing why decisions were
  made (Communication Patterns ch. 10, ch. 12).
- **Everyone affected must be able to read and contribute**, not only developers. A central,
  organisation-wide place lets teams learn from each other's decisions. If ADRs live in a
  repository, link the location from the README and make sure people outside the repository can
  still find and edit them.
- **Links must not break.** Have a process or tool that fixes links when ADRs move or are renamed.
- **Keep ADRs separate from, and linked to, the risk/assumption/issue/decision log** if one exists.
- **One fact, one place** (Communication Patterns ch. 10): do not restate an ADR's content in the
  README or design document; link or embed it.
- **Metadata** helps findability: product, author, type, tags as key-value front matter.
- **Documentation as code** (Communication Patterns ch. 12): keep sources in version control, review
  them like code, verify automatically (links, syntax), build and publish through the pipeline. Do
  not force non-developer authors into developer tooling; apply the principles gently for them.

Suggested repository layout (adaptation):

```
docs/
  adr/
    README.md                 index: allowed statuses, how to add one, list of ADRs
    0001-use-modular-monolith.md
    0002-postgres-as-system-of-record.md
  architecture/
    characteristics.md        the register that ADR criteria cite
```

## 9. Process: consultation and commitment

Corrective rules for common beliefs about decision making (Communication Patterns ch. 12):

| Belief | Use instead |
|---|---|
| Decision making is linear | Iterate on the draft; revisit past decisions; reuse earlier analysis |
| More choices are better | Choice overload is real; at most three options; use ratings and tables |
| The most senior person decides | The owner is the person with the most expertise or the most affected; the owner owns the process and the outcome |
| Every stakeholder should give feedback | Only those important to implementation give input and commit; some are consulted while drafting; some are only informed |
| Ask for every kind of feedback | Tailor the request per stakeholder: ask what is unclear, invite clarifying questions, ask for feedback once they understand. Update the ADR before it is decided; communicate after |
| Everyone must agree | They must commit, not agree. The owner decides after consultation and asks the relevant people to commit. Anyone who thinks it unsafe explains why and the owner works through it |
| The owner can be rational | Biases remain. Expecting dissent, as commit-not-agree does, reduces groupthink. Specific biases and countermeasures: `decision-pitfalls.md` 2.6 |

Review practice (Mastering API Architecture intro): an ADR records collective thinking, so discuss
before writing it; publish it where the key participants can comment; a reviewer checks both whether
they agree with the decision and whether an alternative was not considered, which is grounds for
rejection; circulate wider than the team for feedback.

Not every decision is made in the open. Tying a gate to an ADR (for example, no budget sign-off
until an ADR with suitable consultation is decided) brings decisions into view, but heavy process is
circumvented (Communication Patterns ch. 12).

Agent adaptation: you cannot consult people. Write the Consultation section as a list of who should
be asked and the specific question for each, mark the status Draft or Proposed, and tell the user
the ADR is awaiting their decision.

## 10. Getting ADRs adopted

Communication Patterns ch. 12:

- Show instead of telling: write ADRs for past decisions as well as new ones; answer questions by
  pointing at the ADR; cite the original ADR whenever a change is discussed.
- Make it easy: use the tools people already use; a template that is quick to fill; mark which
  sections are mandatory.
- Habits: raise decisions in the regular review so an ADR is created when needed; make reading the
  product's ADRs part of onboarding; when a question has no ADR to point to, consider writing one.

## 11. Common mistakes

| Mistake | Why it hurts | Fix |
|---|---|---|
| Title names a topic ("Database") | The index says nothing | Title is the decision |
| No alternatives listed | Reader cannot tell what was weighed; reviewer cannot spot a missed option | List them with one line each |
| No criteria | The comparison cannot be reconstructed | Add criteria, cite characteristic IDs |
| No negative consequences | Signals unfinished analysis; reader gets no warning | Add at least one, with what makes it acceptable |
| Context is an essay | The problem is buried | Problem, bounds, constraints, drivers |
| Editing a decided ADR | History is lost | New ADR; mark the old one superseded |
| Stored in a ticket, a pull request or a project space | Unfindable once the project ends | Store with the product; link from the README |
| Many options | Choice overload, shallow analysis | Eliminate early, score at most three |
| Unreproducible numbers | Cannot be re-checked when prices or loads change | Inputs, method, date |
| Decision records a technology where a constraint was meant | Over-specifies; blocks reasonable choices | State the constraint; name a product only if a characteristic depends on it (Fundamentals ch. 1) |
| ADR written, nothing enforces it | Compliance decays | Add a fitness function (`fitness-functions.md`) |
| Process so heavy it is bypassed | Decisions go back underground | Size the ADR to the decision |

Fundamentals ch. 19 names three decision anti-patterns (Covering Your Assets, Groundhog Day,
Email-Driven Architecture). Only the names appear in the available table of contents; their
definitions are not in the notes, so they are not described here. The second and third names
correspond in spirit to the re-litigation and lost-in-messages problems above (that link is an
inference).

## 12. Review checklist

Derived from Communication Patterns ch. 12 and app. A (partly inferred there), with items from the
other sources. Apply the items that the chosen template has sections for.

- [ ] Identifier and a title that states the decision; filename matches
- [ ] Status from the allowed set, with date; superseded ADRs otherwise unchanged
- [ ] Context says why now, the environment, assumptions, constraints, drivers
- [ ] Alternatives actually considered are listed
- [ ] Criteria are listed and tied to architecture characteristic IDs
- [ ] At most three options scored; each has a per-criterion rationale and a total
- [ ] Trade-offs outside the criteria are recorded
- [ ] Decision is short and gives its reason, including why any advice was not followed
- [ ] Consequences include at least one negative and any follow-up work
- [ ] A revisit trigger is stated
- [ ] Consultation lists who was invited and what advice was given; advice separated from opinion
- [ ] Calculations are reproducible: inputs, method, date
- [ ] Linked from code, diagrams or README; stored against the product
- [ ] Each enforceable rule in the decision names the check that enforces it
- [ ] Reviewer asked: is there an alternative that was not considered?

## 13. Worked examples from the sources

Paraphrased; use as models of shape and tone.

### Short form: migrate to a distributed architecture (Hard Parts ch. 3)

- **Title:** Migrate the support application to a distributed architecture.
- **Context:** A monolithic ticketing application covers registration, ticket entry and processing,
  operational and analytical reporting, billing and payment, and administration. It has
  scalability, availability and maintainability problems.
- **Decision:** Migrate to a distributed architecture. This will improve availability of core
  ticketing through fault tolerance; improve scalability for customer and ticket growth; separate
  reporting and its database load, which addresses the freezes; speed up features and fixes; reduce
  defects introduced by changes; and allow weekly or daily deployment.
- **Consequences:** New features are delayed while developers work on the migration; there is extra
  cost, amount to be determined; until the pipeline is changed, release engineers manage several
  deployment units; the monolithic database has to be broken apart.

What to copy: each benefit in the Decision is tied to a named driver and to an observed problem, and
the Consequences are all costs.

### Four-section form: extract a service (Mastering API Architecture intro)

- **Title:** ADR001 Separating attendees from the legacy conference system.
- **Status:** Proposed.
- **Context:** The owners want a mobile application and an integration with an external
  call-for-papers system without disrupting the current system. Both need access to attendees.
- **Decision:** Split the attendee component into a standalone service. This allows API-first
  development against it, invocation from the legacy system, and direct access by the external
  system for user information.
- **Consequences:** The call is now out of process and adds latency that must be tested. The service
  can become a single point of failure and needs mitigation. Several consumers mean good design,
  versioning and testing are needed to avoid accidental breaking changes.

What to copy: every consequence is a cost paired with the work it creates.

### Extended form: illustrative skeleton

The source's own extended example (an ADR numbered 044, "Use an event-driven distributed
architecture") was shown in figures not recovered in the notes. The skeleton below is an
illustration of the template, not a reproduction.

```
# 007 Use per-consumer queues for bid events

## Status
Draft (2026-01-15)

## Context
A fourth consumer (bid history) must receive bid events. Today all consumers subscribe to one
topic with one event schema. Assumption: consumers will keep diverging in the fields they need.
Constraint: bidder personal data may be read only by the capture and audit consumers.

## Evaluation Criteria
AC03 Extensibility; AC05 Privacy; AC02 Scalability per consumer; operational effort.

## Options
(one scoring table per option: single topic; per-consumer queues)
Other trade-offs: single topic needs one shared contract, so schema changes are coordinated.

## Decision
Per-consumer queues. Privacy and independent scaling outweigh the ease of adding consumers.

## Implications
+ Each consumer gets only the fields it may see; queue depth is monitored and scaled per consumer.
- Adding a consumer now needs a new queue and a publisher change.
- More infrastructure to operate.
Revisit if more than a handful of consumers are added per quarter.

## Consultation
To ask: operations (monitoring and scaling per queue), security (field-level access), product
(expected rate of new consumers).
```

The trade-off content is taken from the bid-system example in Hard Parts ch. 15; the identifiers,
dates and the revisit condition are invented for illustration.

### Titles as an index (Hard Parts app. A)

The case study's ADR list reads as a history of decisions: migrate to a distributed architecture;
migration using the component-based decomposition approach; use of a document database for customer
surveys; consolidated service for ticket assignment and routing; consolidated service for
customer-related functionality; using a sidecar for operational coupling; use of a shared library
for common ticketing database logic; single table ownership for bounded contexts; survey service
owns the survey table; use of in-memory replicated caching for expert profile data; use
orchestration for the primary ticket workflow; loose contract for the expert mobile application.
The full case is replayed in `arch-decomposition`.

## 14. ADR guideline tables for "it depends" questions

Mastering API Architecture uses a recurring three-row format for decisions whose answer depends on
context:

| Row | Content |
|---|---|
| Decision | The choice you face |
| Discussion points | What the decision depends on; questions to work through with the team |
| Recommendations | Specific advice to put into your ADR, with rationale |

Use it when writing guidance for others to decide with, as opposed to recording a decision already
made. The discussion points become the Context and Criteria of the eventual ADR. The individual
guideline tables live in `arch-api-design`.

## 15. Verify

- Run the review checklist against the file and report each unchecked item.
- `ls docs/adr` (or the repository's location): filenames are numbered, in sequence, and readable as
  decisions.
- For a superseding change, the diff of the old ADR touches only the status line; the new ADR names
  the one it supersedes.
- A search for the ADR identifier finds at least one inbound link from code, a diagram, a README or
  a CI check.
- Links inside the ADR resolve; if a link checker runs in CI, the ADR directory is in its scope.
- Each criterion ID exists in the characteristics register.
- Tell the user the ADR's status and what remains for a human: consultation, commitment, status
  change.
