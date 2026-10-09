# Analytical data architectures: warehouse, lake, mesh

Read this when deciding how analytical data (reports, BI, ML training) reaches consumers from operational services, especially when each service owns its own database. The analytical-data coordination of services (contracts, ownership) is also covered in the sibling skill `arch-distributed-workflows`; this file focuses on the pipeline side.

Source: Software Architecture: The Hard Parts ch. 14. Items marked (inferred) are labelled so in the notes.

## 1. Why this is a separate problem

Operational data (OLTP, transactions, systems of record) and analytical data (aggregations, reporting, BI, ML training) differ in purpose, format and contract needs. Splitting one database into per-service databases makes it harder to glue data back together for analytics. Three approaches exist; the chapter also shows the trade-off method applied to a new capability (data mesh).

## 2. Data warehouse

- Data is extracted from many sources, transformed to a single schema (typically a star schema: dimensional, denormalised), loaded by regular ETL or replication jobs, and analysed inside the warehouse. Users are analysts; outputs are BI reports and dashboards; SQL-like interface.
- Star schema: fact tables hold quantifiable data (hourly rate, time to repair, distance); dimension tables hold descriptive attributes (specialties, names, locations). Denormalised on purpose for simple queries and fast aggregation; usually becomes very complex.
- It is technical partitioning: domain partitioning is lost and must be rebuilt in queries; needs specialists.
- Failings: integration brittleness (schema coupled to domain semantics, so a domain change forces a schema change and an import logic change); extreme partitioning of domain knowledge across architects, developers, database administrators and data scientists; complexity (a separate, highly coupled ecosystem); limited functionality for its purpose (large pre-cloud infrastructure cost; requested reports often unsupported); synchronisation creates operational and organisational bottlenecks and can affect operational systems; transformation inside pipelines makes contracts brittle.
- Advantages: centralised consolidation; a dedicated analytics silo gives isolation.
- Verdict in the book's case: fits older monolithic architectures better than modern distributed ones; does not suit many ML cases.

## 3. Data lake

- A reaction to the warehouse: keep the centralised model and pipelines but load and transform on demand instead of transform then load. Data is stored raw or nearly so; ML models often work better on semi-raw data. Users are data scientists who discover data and aggregate or compose as needed.
- Remaining problems: hard to discover the right assets (domain relationships evaporate, domain experts still needed); PII and sensitive data (combining data can identify people, unstructured dumping risks exposure); still technically rather than domain partitioned; pipeline brittleness and coupling remain (less transformation but still cleansing); quality and integrity testing pushed downstream; staleness from batch loading and upstream changes.
- Advantages: less structured than a warehouse; less up-front transformation; better suited to distributed architectures.

Critical point: both patterns separate data from its domain context. What is needed is macro-level domain partitioning with a clean separation of operational and analytical data.

## 4. Data mesh

A sociotechnical approach to sharing, accessing and managing analytical data in a decentralised way for reporting, ML training and insights; ownership aligned with business domains; peer-to-peer consumption. It follows from domain-oriented decoupling of microservices; operational versus analytical data is an orthogonal coupling, more complex than operational coupling.

Four principles:
1. Domain ownership: data is owned and shared by the domains most familiar with it, with no central lake, warehouse or data team as intermediary.
2. Data as a product: domains provide data that delights consumers; roles and success metrics exist; the data product quantum (DPQ) serves discoverable, understandable, timely, secure, high-quality data.
3. Self-serve data platform: declarative creation of data products, discoverability (search and browse), lineage and knowledge graphs, better developer and consumer experience.
4. Computational federated governance: organisation-wide compliance, security, privacy, quality and interoperability met consistently; federated decisions by domain data product owners; policies automated and embedded as code in each data product and executed by a platform-supplied sidecar at the point of access.

Data product quantum: built adjacent to, but coupled with, a service (like a sidecar). The service holds behaviour and transactional data; the DPQ holds code and data that form the interface to the analytical side. Operationally independent, highly coupled to its service, owned by the same domain team.

| DPQ type | Purpose |
|---|---|
| Source-aligned (native) | analytical data on behalf of its collaborating quantum, typically a microservice |
| Aggregate | aggregates from several inputs, synchronously or asynchronously |
| Fit-for-purpose | custom for a requirement (reporting, BI, ML) |

Coupling rules:
- The DPQ is a cooperative quantum: operationally separate, communicating with its cooperating service asynchronously with eventual consistency; tight contract coupling with its cooperator, looser contract coupling with the analytics quantum.
- The data sidecar should be orthogonal to the service's implementation changes and keep a separate contract with the data plane.
- Dynamic coupling rule: the sidecar always uses an eventual, asynchronous saga-style pattern (the parallel and anthology saga families in the book); never require transactional synchronisation of operational and analytical data, and keep communication with the data plane asynchronous to protect the service's operational characteristics.
- The data plane must be available (static coupling), as a broker is.

Advantages: suits microservices; follows modern architecture practice; excellent decoupling of analytical from operational data; carefully formed contracts allow loosely coupled evolution. Disadvantages: needs contract coordination with the DPQ; needs asynchronous communication and eventual consistency.

Use when: modern distributed architectures with contained transactionality and good isolation, and domain teams control the amount, cadence, quality and transparency of shared data. Harder where analytics and operational data must be in sync at all times (consider eventual consistency with very strict contracts). Prerequisite worth stating (inferred): a platform team and governance group with enough maturity to keep the self-serve and policy-as-code promises.

## 5. Comparison

| | Warehouse | Lake | Mesh |
|---|---|---|---|
| Model | extract, transform, load; star schema | extract, load, transform on demand | domain-owned data products served peer to peer |
| Partitioning | technical | technical | domain |
| Users | analysts, BI | data scientists | any consumer via DPQs |
| Main failure | brittleness, split domain knowledge, cost | discovery, PII, pipeline coupling, staleness | needs async and eventual consistency, contract coordination, platform maturity |

How to choose: a monolith or a small number of systems with analyst-driven reporting leans warehouse; exploratory ML on raw data leans lake; many domain teams with microservices and a need to decouple analytics from operational schemas leans mesh. In all three, the pipeline questions from the rest of this skill apply: freshness SLO, idempotent loads, contract and schema evolution, privacy and deletion. For storage formats and table layout see `arch-data-storage`.

## 6. Worked case: expert supply planning

Goal: plan expert supply by skill demand per geography over time. Every new service ships with a DPQ owned by its domain team. A new Experts Supply DPQ consumes asynchronously from a Tickets DPQ (long-term ticket history), a User Maintenance DPQ (daily snapshots of expert profiles) and a Survey DPQ (survey result log); the first product is an ML-based supply recommendation produced daily. A platform team supplies self-serve capabilities and monitors downtime and governance incompatibility; a federated governance group (domain product owners plus security, legal, risk, compliance and the platform owner) standardises sharing contracts, async transport and access control, and upgrades sidecars uniformly.

Data quality concern: incomplete feeds skew trend analysis; no data for a day is better than incomplete data, because that day can be exempted. The decision recorded: each source provides a complete daily snapshot or nothing, and contracts between source feeds and the Expert Supply DPQ are loosely coupled to avoid brittleness. Consequence: too many exempt days reduce trend accuracy.

Fitness functions given:
1. Complete daily snapshot: check message timestamps on arrival; with typical volume, any gap greater than one minute marks the day as exempt.
2. A consumer-driven contract test between the Ticket DPQ and the Expert Supply DPQ, so internal evolution of the ticket domain does not break the supply product.

This is the same stale-beats-wrong principle as in `pipeline-reliability.md`.

## 7. Verify (inferred in the notes)

- Each service has a DPQ with an explicit contract; consumer-driven contract tests exist from analytical consumers.
- No synchronous or transactional dependency from the service to its DPQ: a chaos test taking the DPQ down shows service latency and availability unaffected.
- Governance policy runs as code in sidecars; compliance dashboards show PII handling.
- Completeness fitness functions exist per feed, and the exempt-day rule is automated.
