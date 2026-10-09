# Analytical data across services: warehouse, lake, mesh

Read this when reporting, BI or machine-learning needs data that now lives in many service-owned
databases: "build a data warehouse", "dump everything in a lake", "each team should publish its
data", or when an analytics pipeline keeps breaking when operational schemas change.

Contents: the problem; warehouse; lake; mesh (four principles, data product quantum, coupling
rules); comparison; choosing; worked example; verify. Storage formats and engines are in
`arch-data-storage`; pipeline mechanics in `arch-data-pipelines`.

## The problem

Operational data (OLTP, transactions, systems of record) and analytical data (aggregations,
reporting, BI, ML training) have different purposes, formats and contract needs. Splitting databases
per service (see `data-ownership.md`) makes gluing data back together for analytics harder. This
chapter (Hard Parts ch. 14) also demonstrates trade-off analysis of a new capability.

## 1. Data warehouse

- Data is extracted from many sources, transformed to one schema (typically a star schema:
  dimensional modelling, denormalised), and loaded by regular ETL or replication jobs. Analysis runs
  inside the warehouse by data analysts; output is BI reports and dashboards through a SQL-like
  interface.
- Star schema: fact tables hold quantifiable data (hourly rate, time to repair, distance to client);
  dimension tables hold descriptive attributes (specialties, names, locations). Purposely
  denormalised for simple queries, fewer joins and fast aggregation; usually grows very complex.
- It is technical partitioning: domain partitioning is lost and must be rebuilt in queries; it
  needs specialists.
- Failings: integration brittleness (schema tied to domain semantics; a domain change forces a
  schema change and an import logic change); extreme partitioning of domain knowledge (architects,
  developers, DBAs and data scientists must coordinate every data change); complexity (a separate
  ecosystem tightly coupled to the operational domains); limited functionality for its purpose
  (large infrastructure investment, requested reports often unsupported); synchronisation creates
  bottlenecks and affects operational systems; operational and analytical contracts differ and the
  pipelines make them brittle.

| Advantages | Disadvantages |
|---|---|
| Centralised consolidation of data | Extreme partitioning of domain knowledge |
| A dedicated analytics silo provides isolation | Integration brittleness |
| | Complexity |
| | Limited functionality for the intended purpose |

Verdict in the case study: fits older monolithic architectures better than modern distributed ones,
and does not suit many ML cases.

## 2. Data lake

- A reaction to the warehouse: keep the centralised model and pipelines but load first and transform
  on demand (extract-load-transform) instead of transform-then-load. Store raw or native form,
  perhaps with some snapshot formatting. ML models often work better on semi-raw data. Used mostly
  by data scientists who discover data and compose aggregations as needed.
- Remaining problems: hard to discover the right assets (domain relationships evaporate; domain
  experts are still needed); PII and sensitive data (combining data can identify people, unstructured
  dumping risks exposure); still technically, not domain, partitioned (ingestion, transformation,
  loading and serving partitions); pipeline brittleness and coupling remain (less transformation
  but still cleansing); quality and integrity testing pushed downstream; staleness from batch loads
  and upstream changes.

| Advantages | Disadvantages |
|---|---|
| Less structured than a warehouse | Sometimes hard to understand relationships |
| Less up-front transformation | Requires ad-hoc transformations |
| Better suited to distributed architectures | |

Critical point: both patterns separate data from its domain context. What is needed is macro-level
domain partitioning with a clean operational/analytical separation.

## 3. Data mesh

A sociotechnical approach to sharing, accessing and managing analytical data in a decentralised
way, serving reporting, ML training and insights; ownership aligns with business domains and
consumption is peer to peer. It derives from domain-oriented decoupling in microservices plus the
service mesh and sidecar idea: operational versus analytical data is an orthogonal coupling.

Four principles:

1. Domain ownership of data: owned and shared by the domains most familiar with it (originating or
   first-class consumers), peer to peer, with no central lake, warehouse or data team in between.
2. Data as a product: domains provide data that delights consumers, with organisational roles and
   success metrics. This introduces the data product quantum (DPQ) to serve discoverable,
   understandable, timely, secure, high-quality data.
3. Self-serve data platform: declarative creation of data products, discoverability (search and
   browse), lineage and knowledge graphs, better developer and consumer experience.
4. Computational federated governance: organisation-wide compliance, security, privacy, quality and
   interoperability met consistently across domains. Decisions are federated among domain data
   product owners; policies are automated and embedded as code in each data product and executed by
   a platform-supplied sidecar in each DPQ at the point of access (read or write).

### Data product quantum

- A quantum built next to, and coupled with, a service (like a sidecar in a service mesh). The
  service holds behaviour and transactional data; the DPQ holds code and data that act as the
  interface to the analytical and reporting side. Operationally independent but highly coupled to
  its service; owned by the same domain team.
- Types: source-aligned (native) DPQ, analytical data on behalf of its collaborating quantum
  (typically a microservice); aggregate DPQ, aggregating from several inputs, synchronously or
  asynchronously; fit-for-purpose DPQ, custom for a requirement (reporting, BI, ML).
- A cooperative quantum is operationally separate and communicates with its cooperator
  asynchronously and eventually consistently; contract coupling with its cooperator is tight and
  generally looser with the analytics quantum. The analytical quantum has static coupling to the DPQs
  it needs and may call them synchronously (a SQL interface) or asynchronously.
- Coupling rules: the DPQ and its communication belong to the service quantum's static coupling (the
  data plane must be available, as a broker must). The data sidecar should be orthogonal to the
  service's implementation changes and keep its own contract with the data plane. Dynamic coupling:
  use an eventual, asynchronous, saga-style pattern (Parallel aeo or Anthology aec) between service
  and data plane; never require transactional synchronisation of operational and analytical data;
  keep communication to the data plane asynchronous to protect the service's operational
  characteristics.

| Advantages | Disadvantages |
|---|---|
| Highly suitable for microservices | Requires contract coordination with the DPQ |
| Follows modern architecture and engineering practice | Requires asynchronous communication and eventual consistency |
| Excellent decoupling of analytical from operational data | |
| Carefully formed contracts allow loosely coupled evolution of analytics | |

When it fits: modern distributed architectures with contained transactionality and good isolation,
where domain teams control the amount, cadence, quality and transparency of the data they share.
Harder where analytical and operational data must be in step at all times; then consider eventual
consistency with very strict contracts.

## Comparison

| | Warehouse | Lake | Mesh |
|---|---|---|---|
| Model | extract-transform-load, star schema | extract-load-transform on demand | domain-owned data products served peer to peer |
| Partitioning | technical | technical | domain |
| Typical users | analysts, BI | data scientists | any consumer via DPQs |
| Main failure | brittleness, split domain knowledge, cost | discovery, PII, pipeline coupling, staleness | needs async and eventual consistency, contract coordination, platform maturity |

## Choosing (adaptation of the comparison)

| Situation | Lean toward |
|---|---|
| Few systems, a monolith or near-monolith, mostly BI reports | Warehouse (the notes say it fits older monolithic architectures) |
| ML and exploratory work that wants raw or semi-raw data, centralised team available | Lake, with PII handling designed in |
| Many domain teams on microservices, analytics blocked on a central data team, platform capacity exists | Mesh |
| Small organisation with one or two services | None of these: query a read replica or a periodic export; a mesh is organisational machinery with a real cost |

The last row is adaptation: the notes do not size the organisation threshold, so treat it as
judgement and state the assumption to the user.

## Worked example (expert supply planning)

Goal: plan expert supply by skill-set demand per geography over time. State: every new service ships
with a DPQ owned by its domain team; Ticket Management has two services with DPQs plus a Tickets DPQ
(an aggregation of ticket views, its own quantum). A platform team supplies self-serve capabilities
and monitors downtime and governance incompatibility. A federated governance group (domain product
owners plus security, legal, risk and compliance experts and the platform product owner) standardises
data-sharing contracts, asynchronous transport and access control; the platform upgrades the DPQ
sidecars uniformly.

Design: a new Experts Supply DPQ consumes asynchronously from the Tickets DPQ (long-term ticket
history), the User Maintenance DPQ (daily snapshots of expert profiles) and the Survey DPQ (survey
results log). First product: supply recommendations from an ML model, daily.

Quality decision: incomplete feeds skew trends, and no data for a day is better than incomplete
data because the day can be exempted. ADR: each source supplies an entire day's data or none;
contracts between the feeds and the supply DPQ are loose to prevent brittleness; consequence: too
many exempt days reduce trend accuracy. Fitness functions: (1) complete daily snapshot, checked by
message timestamps on arrival (with the typical volume, a gap longer than one minute marks the day
exempt); (2) a consumer-driven contract test between the Tickets DPQ and the supply DPQ so internal
changes in the Ticket domain do not break it.

## Verify

- Every service that feeds analytics has a DPQ (or equivalent output port) with an explicit contract,
  and consumer-driven contract tests from the analytic consumers run against it.
- Chaos test: take the DPQ or data plane down and confirm the service's latency and availability do
  not change. There must be no synchronous or transactional dependency from service to DPQ.
- Governance policies (PII masking, access control) run as code in the sidecar; keep a compliance
  report that lists data products with unclassified PII.
- Per-feed completeness checks exist and exempted days are visible to consumers.
- For a warehouse or lake: list the pipelines that break on an operational schema change, and the
  PII locations; if the answer is "unknown", that is the first finding to report.
