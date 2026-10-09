# Case studies and adoption: Evernote, The Home Depot, organisational preconditions

Sources: SRE Workbook ch. 3 (Evernote, The Home Depot), ch. 8 (Evernote on-call changes), ch. 1 (SRE and DevOps preconditions and warning signs).

Use as replayable recipes when bootstrapping an SLO for a first service, rolling SLOs out to many services, working with a cloud provider, or judging whether an organisation can support error budgets.

## 1. Evernote: a first SLO built in a replayable way

Context: more than 220 million users, 12 billion pieces of content, 750+ MySQL instances; moved from its own datacentres to GCP; adopted the SLO and error budget model after trying "you wrote it, you run it" and "you wrote it, we run it for you". Reason for the model: SLO and error budget give development and operations a common frame of reference, so both reach similar decisions from the same facts and subjectivity drops. It accepts them as separate specialisations with a common goal.

Recipe for SLO v1:

1. Start from the customer promise. The most important common need: the service is available so users can access and sync content across clients. First pass: simple uptime.
2. Definition: 99.95% uptime over a calendar month for certain services and methods. The number came from discussions with support and product teams and user feedback. Calendar month, deliberately, to keep service reviews focused and organised.
3. What to measure: a built-in status page endpoint that exercises most of the stack and returns 200 if healthy.
4. How to measure: an external prober independent of your own environment (so the load balancing stack and both cloud and application failures are covered), run by a third party to avoid arguments about random internet issues. Probe every minute from several locations in North America and Europe. Definition of down: a failed check marks the node unconfirmed down; a second, geographically separate prober re-checks; only if that fails is the node down for SLO calculation, and it stays down while consecutive probes fail.
5. Calculation rules written in advance. Example: maintenance windows count as downtime, because hundreds of millions of users cannot know published windows.
6. Use: the SLO and error budget allocate resources. Monthly review with the Evernote and Google teams of last month's performance and a deep dive on outages, producing action items beyond the normal root cause analysis. Six-month SLO review cycle (the balance between changing SLOs too often and letting them go stale); revised twice in about nine months.
7. Principle: perfect is the enemy of good. An SLO covering every interaction would take months; one covering most interactions was chosen as a proxy for quality of service. Balance what you want to measure with what is possible.
8. Result example: while chasing a complex bug, product development asked to split the weekly release across multiple windows, each potentially customer-impacting. Applying an SLO calculation to the question cut release windows from five to two.
9. Next version: probe individual API calls and add an in-client view of performance.

### Do not build on the provider's SLO

Deriving your SLO from the provider's published SLO (GCP Compute Engine's 99.95%) hides regional or footprint-specific problems because the provider's global rollup can be green while you suffer. Instead share your SLO and real-time performance with the provider, have both teams use the same dashboards (so provider alerts say "load balancing slow today, causing 5% impact to your SLO"), and agree beforehand that high SLO impact is a top-priority incident with a shared conference bridge, with the provider's customer reliability engineers monitoring the jointly defined SLO.

### Evernote's on-call changes (Workbook ch. 8)

Migrating to the cloud broke on-premises alerting that assumed redundancy and controlled infrastructure (a few dropped packets meant a database exception meant a host about to fail). They restated paging from first principles as SLOs and alerted on higher-level indicators (API responsiveness) instead of low-level ones (InnoDB row lock waits). Alert classes: P1 immediate and SLO-impacting, P2 next business day, P3 informational. Details in `pager-load-targets.md`.

## 2. The Home Depot: SLOs as a common language across hundreds of services

Context: 2,200+ stores, 400k associates, 1.5 billion transactions a year; a move from centrally supported monolithic packages to microservices owned end to end by small teams. SLOs became the common language between development and operations and between dependent services. Questions each service had to answer: how reliable (3, 3.5 or 4 nines? planned downtime?), latency at upper bounds, capacity and overload behaviour, track record against SLOs. Before: scattered dashboards with no history, troubleshooting that started at the user-facing service and worked backward, planned downtime that surprised dependents, and only the support-desk ticket count as a reliability measure.

Four-pronged strategy:

1. Common vernacular: define SLOs in company context and measure consistently.
2. Evangelism: training material, road shows, an internal blog, t-shirts and stickers, early adopters as demonstrators, a catchy acronym (VALET), a training programme (from a one-hour primer through half-day workshops to a four-week immersion with an SRE team). Executive buy-in first, then team by team. A weekly SLO report in VALET format went to senior leadership, including business metrics (purchase orders created as volume, failed as errors) with commentary on lessons.
3. Automation: collect SLIs automatically for anything deployed to production to lower adoption friction.
4. Incentive: annual goals for development managers to set and measure SLOs; SLO implementation counted in performance reviews.

### VALET

| Letter | Meaning | Rules |
|---|---|---|
| Volume | how much business volume the service can handle | track average or peak requests per second or volume per period; SLO set for expected peak (for example Black Friday) |
| Availability | is it up when needed | |
| Latency | does it respond fast | percentiles not averages, at least p90, user-facing preferably p95 or p99; services choose where to measure but supplement white-box with black-box monitoring |
| Errors | rate of failures | HTTP codes only; never signal error in the body of a 2xx; service-caused 5xx, client-caused 4xx; track both, only 5xx counts for the SLO; for batch, records failed |
| Tickets | does the service need manual intervention to complete a request | kept for historical reasons |

Infrastructure utilisation was deliberately not an SLO (users do not care while traffic is handled and no capacity risk exists); it is still monitored for capacity planning. Every microservice publishes availability and latency SLOs for its APIs that other services call. VALET impact was recorded automatically during destructive tests in staging. Batch mapping: volume = records processed; availability = share of time the job completed by its deadline; latency = job runtime; errors = records failed; tickets = manual fixes and reprocessing.

Automation architecture: a reporting store (BigQuery) fed by frontend web logs and other monitors producing hourly VALET metrics, with new services auto-registered and a chatbot reporting the last hour, comparison with the previous week and services out of SLO; a VALET service storing and reporting SLOs at daily, weekly and monthly granularity, fed through an integration-layer API so non-cloud platforms can contribute; a VALET dashboard to register services, set objectives per category and choose metric types (p99 versus p90, daily volume versus peak rate). Accepted trade-off: SLOs used as a trending tool, not wired to the alert thresholds of the various monitoring platforms. Growth: about 50 services tracked in a spreadsheet at the start of a year, about 800 by year-end, around 50 new per month. The authors stress you can get the benefit without such automation.

Aspirations: an error budget culture (stop feature pushes when out of SLO, debating weekly versus monthly and rolling versus fixed windows to protect velocity), per-endpoint and per-consumer VALET, an end-user latency SLO (third-party tags, internet, CDN, render time), automated deploy gates checking VALET before rolling to the next server, zone or region, a dependency call-tree showing where VALET was missed, and SLOs set by business owners.

## 3. Lessons that transfer

- SLO culture is a journey (years at the Home Depot; zero to 800 services in under a year with executive buy-in, evangelism, easy adoption, incentives and patience).
- Start simple (uptime, one prober) and revise. The two companies' SLIs differ markedly; tailor to environment.
- Define "down", maintenance handling and measurement location before collecting data.
- Share SLOs with dependency providers; do not base yours on theirs.
- Give product managers a small menu of understandable options with cost attached (the uptime tiers in `dependencies-and-availability-math.md`).
- Make SLOs part of manager goals and reviews to sustain adoption.
- Regular review cadence (monthly service review; six-monthly SLO review; weekly or monthly at THD).

## 4. Organisational preconditions and warning signs (Workbook ch. 1)

SRE is a concrete role and practice set that implements much of the DevOps philosophy; they are not in competition. Principles relevant here:

- Accidents are normal and come from missing safeguards, not one person's mistake; punishing the "mistake maker" teaches people to hide. Optimise recovery speed over prevention of every accident.
- Changes should be small, frequent, automatically tested and reversible. Measurement establishes reality objectively and gives functions a shared basis for conversation.
- Move fast by reducing the cost of failure: lower time to recover from common faults raises developer velocity.
- Share ownership with developers; use the same tooling regardless of title.

Incentives: do not tie incentives narrowly to launch or reliability numbers (Goodhart's law); avoid blame-passing incentives; support blameless postmortems. Support can be withdrawn from "irredeemably operationally difficult" products to motivate fixes, but only an organisation big enough to afford it (a 20-person startup with one product cannot), so smaller teams take a DevOps-style shared approach. A separate organisation is optional; what is needed is a community of practice, job ladders and parity of esteem.

Warning signs:

- Renaming a group DevOps or SRE with no change in position, then shaming it when nothing improves; you cannot buy DevOps.
- Operations treated as a cost centre, with savings wiped out by one big outage.
- A pay or esteem gap between operations and development; shipping before it is ready and dumping maintenance on operations.

Checks (inferred in the notes): is there an SLO owned by someone who can trade features against reliability? Is toil measured against a ceiling? Do postmortems produce changes? Do development and operations share tooling and pipelines? Are changes small, tested and rollbackable?

Caveat: Google-specific mechanics (support withdrawal, a separate SRE organisation, production readiness reviews) depend on size and management backing. Principles carry over; mechanics need adaptation.
