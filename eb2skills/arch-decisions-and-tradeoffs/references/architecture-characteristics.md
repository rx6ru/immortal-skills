# Architecture characteristics as decision criteria

How to choose, define, record and use architecture characteristics ("-ilities", quality attributes)
so that decisions are judged against something explicit. Sources: Communication Patterns ch. 12;
Hard Parts ch. 1, ch. 2, ch. 3; Fundamentals ch. 1.

## Contents

1. What a characteristic is
2. Selecting characteristics
3. The characteristics register
4. Making a characteristic measurable
5. Scope: characteristics belong to a quantum
6. The five modularity drivers
7. Mapping symptoms to drivers (worked example)
8. Modularity without distribution
9. Characteristics over time
10. Verify

## 1. What a characteristic is

- The success criteria of the system that are generally orthogonal to its functionality: needed for
  the system to work properly without depending on what it does. One of four dimensions of an
  architecture, with structure, decisions and design principles (Fundamentals ch. 1).
- Also called system quality attributes or quality characteristics. They work like high-level
  non-functional requirements and act as the compass for project, architecture and design decisions
  and as the basis of ADR evaluation criteria (Communication Patterns ch. 12).
- They are derived from documented requirements, functional and non-functional, and from analysis
  sessions (domain-driven design work, event storming, domain storytelling).

## 2. Selecting characteristics

Procedure (Communication Patterns ch. 12):

1. Gather candidates from requirements and analysis. Lists to draw candidates from: the example list
   in Communication Patterns (accessibility, availability, configurability, continuity meaning
   recovery from disaster, extensibility, portability, privacy, scalability), ISO/IEC 25010, and
   published worksheets. The notes do not reproduce the larger catalogue from Fundamentals ch. 4;
   do not attribute a specific list to it.
2. Choose no more than seven. A product owner will want all of them; a system cannot be optimised
   for all, and each additional one constrains the design.
3. Treat these as implicit, not counted in the seven but promotable when they become a real driver:
   feasibility, maintainability, security, simplicity. Cost may be handled with feasibility or
   separately.
4. Define each chosen characteristic in a shared list so the word means the same to everyone.
5. Agree a top three with stakeholders, with the reasoning written down. The three need not be
   ordered.
6. Record all candidates considered, including the near-misses, so a later reader sees what was
   weighed and dropped.
7. Record the selection itself as an ADR, and supersede that ADR when the selection changes.

## 3. The characteristics register

Columns (Communication Patterns ch. 12, Table 12-1): ID, characteristic, applicable to, source.

| ID | Characteristic | Applicable to | Source |
|---|---|---|---|
| AC01 | Auditability | Media service | REQ 014 (record access and use of all media) |
| AC02 | Fault tolerance | Payment interface, external media interface, customer API, customer UI | REQ 025, REQ 026 |
| AC03 | Extensibility | External media interface | REQ 029 (simple to add a new external media source) |

Also keep:

- the part of the system each applies to, refined to specific components once they are known;
- the source: requirement ID, output of an analysis session, or additional reasoning;
- an ID, so ADRs and diagrams can cite the characteristic;
- dates: created, last updated, next review;
- the top three priorities.

Suggested location in a repository (adaptation): `docs/architecture/characteristics.md`, with the
selection ADR linked from it.

## 4. Making a characteristic measurable

"High performance" cannot be specified or checked. A characteristic used as a criterion or governed
by a fitness function needs an objective value (Hard Parts ch. 1).

- If you cannot say how to measure it, the definition is too vague.
- **Composite characteristics** are not measurable as stated and must be decomposed. Agility
  decomposes into maintainability, testability and deployability, or into deployability,
  testability and cycle time, each of which can be observed.
- Two terms often confused (Hard Parts ch. 2, ch. 3): **scalability** is staying responsive as user
  load grows gradually; **elasticity** is staying responsive through sudden, erratic bursts.

Template for a measurable statement (adaptation):

```
<ID> <Characteristic> for <scope>:
  measure:    <what is observed, in what unit>
  threshold:  <number or true/false>
  measured:   <where: CI job, load test, production monitor>
  source:     <requirement or driver>
```

Example: `AC07 Elasticity for ticket creation: p95 response time under a burst from 20 to 3000
concurrent users; threshold agreed with owner; measured by scheduled load test; source REQ 031.`
The burst figure comes from the concert-ticket illustration in Hard Parts ch. 3; the rest of the
line is illustrative.

## 5. Scope: characteristics belong to a quantum

Operational characteristics such as performance, scale, elasticity and reliability are set per
architecture quantum (Hard Parts ch. 2). Consequences for criteria:

- If two services share a database, they are one quantum, and "service A needs high elasticity,
  service B does not" cannot be delivered independently.
- A synchronous call temporarily couples the characteristics of caller and callee. A caller that
  scales to ten times the load of the service it calls synchronously is held back by the slower
  one; a queue between them lets each scale on its own.
- So "applicable to" in the register should name a quantum or a set of components inside one, and a
  differing target for two parts is itself an argument to separate them.

See `coupling-and-quanta.md` for the definition and counting procedure.

## 6. The five modularity drivers

Hard Parts ch. 3. Use these as the criteria when the question is whether breaking a system into
smaller deployable parts is justified.

Business drivers: speed to market (agility), and competitive advantage, which is speed to market
plus scalability plus availability/fault tolerance. Typical triggers: mergers and acquisitions
(user volume, extensibility), competition, growth in demand, automation initiatives, and shifts in
the technical environment such as containers, cloud and continuous delivery.

Relationship: maintainability, testability and deployability give agility, which gives speed to
market; adding scalability and fault tolerance gives competitive advantage.

### Maintainability

- Meaning: ease of adding, changing or removing features and of making internal changes such as
  patches and framework or library upgrades. Composite and hard to measure objectively.
- Practical metrics: component coupling, component cohesion, cyclomatic complexity, component size
  in statements, and whether the code is partitioned technically or by domain. One published
  maintainability-level formula weights incoming coupling heavily, so the higher the incoming
  coupling, the lower the maintainability (the exact formula was not recovered in the notes).
- How to judge an option: scope of change. For a small requirement such as adding an expiry date to
  a wish-list item, a layered monolith needs an application-level change across user interface,
  back end and database (three or more teams); a service-based system needs a change in one domain
  service; microservices need a change in one function-level service.

### Testability

- Meaning: ease of testing, usually through automation, and completeness of testing.
- Monolith pattern: thousands of tests run for a small change, unrelated failures, low completeness.
  Modular pattern: smaller targeted suites, easier test maintenance.
- Caveat: as services call each other more, a change to one pulls others into the test scope and
  testability falls quickly.
- How to judge: "what is the test scope of a change to X?"

### Deployability

- Meaning: ease, frequency and risk of deployment, balanced against how much change users can absorb.
- Monolith pattern: ceremony (code freezes, mock deployments), high risk, releases weeks or months
  apart.
- Caveat: more inter-service communication raises deployment risk. If services must be deployed
  together in a set order, they belong back in one deployable unit; otherwise the result is a
  distributed big ball of mud.
- How to judge: can this part be deployed alone, how often, and what else must be redeployed or
  retested with it?

### Scalability and elasticity

- Elasticity depends on mean time to startup, which comes from small services and lightweight
  runtimes. Elasticity is mostly a function of granularity (size of the deployment unit);
  scalability is mostly a function of modularity (separate deployment units).
- Qualitative ratings as given in Hard Parts ch. 3: layered monolith low on both (everything scales
  together, poor startup time); service-based better on scalability than elasticity (domain-level
  scaling, coarse services, fair startup time); microservices highest on both (function-level,
  excellent startup time).
- Caveat: more synchronous calls per transaction harms both. Keep synchronous communication minimal
  when high scale or elasticity is needed.

### Availability and fault tolerance

- Meaning: parts of the system stay responsive when other parts fail (payment runs out of memory,
  search and ordering still work).
- Monolith pattern: low. Load-balanced copies are expensive and do not help when the defect is in
  every copy.
- Modularity isolates a catastrophic failure to one deployment unit.
- Caveat: a service synchronously dependent on a failing service gets no fault tolerance.
  Asynchronous communication is what delivers it.

Summary of the caveats: every driver's benefit is eroded by synchronous inter-service communication.
An option that splits a system while keeping dense synchronous calls pays the cost of distribution
without the benefit.

## 7. Mapping symptoms to drivers (worked example)

Hard Parts ch. 3. The reusable move is: symptom, then evidence, then driver. Only then options.

| Business symptom | Evidence found | Driver |
|---|---|---|
| Changes are slow and break other things; codebase too large to navigate | Developers cannot find where to make a change | Maintainability |
| Testing is painful | More than 30% of test cases commented out or obsolete; no tests for a critical workflow; whole suite runs for any change | Testability, both ease and completeness |
| Monthly releases with piled-up change combinations, code freezes, mock deployments | High deployment risk | Deployability. One view called it a pipeline problem, the other also an architecture problem because smaller scopes reduce risk; both agreed the pipeline must change too |
| System unavailable, crashes | Metrics showed survey and reporting functions bring the system down, not core ticketing | Availability/fault tolerance: isolate those functions |
| Freezes with more than 25 customers creating tickets at once; freezes when operational reports run in the day | Analysis by a developer | Scalability and database load: separate reporting, scale the customer-facing part |

Agent adaptation for gathering evidence in a repository: count skipped or disabled tests; read the
CI history for suite duration and for how often unrelated tests fail; read deployment frequency from
tags or release history; look for incident notes naming the failing area; use search to see how many
directories a typical recent change touched. Report these as evidence, not as conclusions.

An executive-level analogy from the same chapter: a monolith is a full glass; a second server
running the same application is a second glass holding the same water and does not help; splitting
the application into two parts across two glasses leaves room in each.

## 8. Modularity without distribution

Modularity does not imply distribution (Hard Parts ch. 3). Maintainability, testability and
deployability can be partly achieved inside one deployable:

- a modular monolith with components partitioned by domain;
- a microkernel, where plug-ins shrink the scope of testing and deployment.

Consider these before services. They do not deliver independent scalability or fault isolation,
which need separate deployment units. If only the first three drivers apply, the modular option
should be on the option list.

## 9. Characteristics over time

- Characteristics change. Scalability may enter later; security may be promoted when personal data
  or a new law arrives. Revisit as the product moves from initial product to growth to optimisation,
  at business milestones, or on a fixed interval (Communication Patterns ch. 12).
- Architecture vitality: an architecture defined three or more years ago should be re-evaluated
  against business and technology change. Most architectures decay structurally as code and design
  changes erode the required characteristics. Include test and release environments in the
  assessment: if tests take weeks and releases months, the architecture is not agile whatever the
  diagram says (Fundamentals ch. 1).
- Style and engineering practice have to match. A style that assumes automated provisioning, testing
  and deployment produces heavy friction when run with manual operations and little testing
  (Fundamentals ch. 1). When rating an option, rate it as it would be run by this team with its
  current practices.
- Operational concerns such as elastic scale are often better handled by the platform or operations
  than built defensively into the application architecture; misallocating them creates accidental
  complexity (Fundamentals ch. 1).

## 10. Verify

- Every characteristic has an ID, a source requirement or reasoning, a scope, and a next-review date.
- There are no more than seven explicit characteristics, and a top three is recorded with reasons.
- Each characteristic used as a criterion has a measure and a threshold, or is flagged as not yet
  measurable with the decomposition still to do.
- No composite word (agility, quality, robustness) is used as a criterion without its parts.
- Each ADR's criteria cite characteristic IDs.
- Scope names in the register correspond to real components or quanta in the codebase (check the
  names exist).
- For a modularity business case: each claimed benefit maps to a row of symptom, evidence and
  driver, and the evidence is something a reader could re-check.
