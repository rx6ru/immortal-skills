# Worked example: the Sysops Squad migration, as a replayable sequence

Contents: Setting; Step table; Step details with ADR skeletons; Replay template; What to copy and what not to copy.

Source: Architecture: The Hard Parts ch. 3 to 8 (running case). The company is fictional. Use this as a pattern for the order of questions and the evidence collected, not as a template to copy numbers from.

## Setting

A monolithic trouble-ticket application for a company that sends experts to repair customers' electronics: customer registration, ticket entry and processing, operational and analytical reporting, billing and payment, administration. Problems: slow and risky changes, painful testing, infrequent risky releases, outages caused by non-core features, freezes under concurrent load and when reports run.

## Step table

| Date in notes | Question | Evidence | Result |
|---|---|---|---|
| Sep 30 | Should we decompose? | Symptoms mapped to drivers (below) | ADR: migrate to a distributed architecture; sponsors approved |
| Oct 29 | Which approach? | Abstractness/instability: most code along the main sequence, a few outliers; existing component boundaries good; shared code (logging, security, persistence calls) would be duplicated by forking | ADR: component-based decomposition (rejecting tactical forking) |
| Nov 2 | Pattern 1 | 82,931 statements, 18 components; Reporting 33% | Reporting split into four components |
| Nov 5 | Pattern 2 | Three notification components; Ca before 5, after 5 | Merged into one notification component |
| Nov 10 | Pattern 3 | 45 orphan classes in ticket, mixed survey sub-namespace | Ticket orphans become components; survey templates folded in |
| Nov 15 | Pattern 4 | Component dependency diagram, shared-library edges filtered | Components largely self-contained; proceed |
| Nov 15 | Should the database be decomposed? | Ticket queries time out when reports run; about 2,000 more connections than one database has; fault tolerance; quanta | Justified to the data architect; five-step process |
| Nov 18 | Pattern 5 | Product owner sessions | Five domains: Ticket, Reporting, Customer, Admin, Shared |
| Nov 23 | Pattern 6 | Staged extraction | Five deployed domain services over one database |
| Dec 16 | Polyglot persistence for survey? | Business case from the product owner; modelling options | ADR: document database for survey |
| (ch. 7) | Ticket assignment and routing: split? | Two-way synchronous coupling | ADR: consolidated service |
| (ch. 7) | Customer registration: split for security? | All-or-nothing registration requirement | ADR: consolidated customer service plus access-control library |
| (ch. 8) | Common infrastructure logic | Duplicate logs; operational coupling | ADR: sidecar plus mesh |
| (ch. 8) | Shared ticket database logic | Repository history: rarely changes | ADR: shared library |

## Step details

### Business case (Sep 30)

Symptom to driver mapping (reusable):

| Business symptom | Evidence found | Driver |
|---|---|---|
| Changes slow and break things; codebase too big to navigate | Developers cannot find where to change | Maintainability |
| Testing painful | More than 30% of test cases commented out or obsolete; no tests for a critical workflow; whole suite for any change | Testability |
| Monthly releases, piled-up untested change combinations, code freezes, mock deploys | High deployment risk (a pipeline issue and also an architecture issue; both must change) | Deployability |
| Outages | Metrics show survey and reporting bring the system down, not core ticketing | Availability/fault tolerance |
| Freezes with more than 25 concurrent ticket creators and during daytime reports | Analysis by a developer | Scalability and database load |

ADR skeleton (as in the notes): Context: monolithic ticket application with scalability, availability and maintainability issues. Decision: migrate to a distributed architecture to improve availability of core ticketing, scale for customer growth, separate reporting and its database load, speed up features and bug fixes, reduce bugs on change, allow weekly or daily deployment. Consequences: feature work slows while developers migrate; extra cost (to be determined); release engineers manage multiple deployment units until the pipeline changes; the monolithic database must be broken apart.

### Approach (Oct 29)

One architect favoured tactical forking. The other objected: duplicated shared code (logging, security, persistence) means the same change in several services, and the problems were maintainability, testability and reliability. ADR: component-based decomposition. Reasons: well-defined component boundaries; less duplication; forking needs boundaries up front while here services emerge from component grouping; the reliability, availability, scalability and workflow problems call for a safer, controlled, incremental route. Consequences: probably longer; developers collaborate on shared functionality and boundaries; forking would have split the team.

### Patterns 1 to 6 (Nov 2 to Nov 23)

Numbers and moves are in `component-decomposition-patterns.md` under each pattern. Sequence to notice: sizing finds the outlier; deduplication is guarded by a Ca check; flattening removes orphans and sets up shared-code metrics; the dependency picture decides feasibility; the domain grouping is validated with the product owner; services are extracted only after all domains are settled.

### Data decomposition (Nov 15)

The data architect would only agree on evidence. The evidence given: logs showed ticketing queries timing out when reporting ran, because reporting uses parallel threads and consumes all connections; a projection of services times instances showing about 2,000 more connections than a single database provides; fault tolerance (database down means all services down, while domain silos keep ticketing running when the survey database is down); quantum (the database is part of static coupling, so splitting makes core ticketing standalone). Her rule: services must not connect to multiple databases or schemas. Her remaining objection (the number of foreign keys and views) was answered by data domains and the five-step process in `decomposing-data.md`. Data domains: Customer, Survey, Payment, Profile, Knowledge Base, Ticketing.

### Polyglot (Dec 16)

See `decomposing-data.md` section 8: flexibility and time to change was the business driver; both aggregate models were drawn; the single-aggregate model was chosen because there were only five survey types and the complexity lay in the UI.

### Granularity (ch. 7) and reuse (ch. 8)

See `service-granularity.md` section 7 and `reuse-patterns.md` section 8.

### ADR shape used throughout

Context, Decision, Consequences, where Consequences always lists what is lost. For the template, statuses and review checklist, use `arch-decisions-and-tradeoffs`.

## Replay template for a new system

1. Write the symptom table: symptom, evidence you can show, driver. Drop rows with no evidence.
2. Compute the coupling table and component inventory. Decide approach with the table in `is-it-decomposable.md` section 7.
3. Run patterns 1 to 5 in order, installing fitness functions as you go. Stop and re-plan if pattern 4 says "airliner".
4. Extract domain services (pattern 6) only when the domain list is stable.
5. For each data domain, run the checklist in `decomposing-data.md` section 4. Involve the data owner from the start.
6. For each proposed finer split, run the disintegrator/integrator procedure in `service-granularity.md` and phrase the choice as a trade-off the business owner can decide.
7. For each shared piece of code, run the chooser in `reuse-patterns.md`; check rate of change in history first.
8. Write an ADR at each decision point with consequences.

## What to copy and what not to copy

Copy: the order of questions; asking for evidence from logs, version control and metrics; keeping the data architect and product owner in the loop; recording consequences. Do not copy: the thresholds (10%, 30%, 40%, 15 dependencies, 2,000 connections); the conclusion that five domain services is the right size; the choice of a document database; the assumption of a team large enough to run many services.
