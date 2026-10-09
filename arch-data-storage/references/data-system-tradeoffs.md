# Data system trade-offs: where data lives and how the system is shaped

Use this file for the first-level questions about a data architecture, before any product is named: which stores are authoritative and which are derived, whether the workload is operational or analytical, cloud or self-hosted, one node or many, and what privacy law does to the design.

Contents
1. Operational vs analytical (OLTP, OLAP, HTAP, warehouse, lake)
2. System of record vs derived data
3. Cloud vs self-hosting, and cloud-native architecture
4. Single node vs distributed
5. Microservices and serverless as data decisions
6. Law, privacy and data minimisation as design inputs
7. Review questions with observable answers

Sources: DDIA 2e ch. 1 unless noted.

---

## 1. Operational vs analytical

Operational systems (backend services plus their data infrastructure) create data and read/modify it in response to user actions. Analytical systems hold a read-only copy of operational data, shaped for analysis. "Transaction" in OLTP here only means low-latency reads and writes; the formal meaning is in `arch-transactions`.

| Property | OLTP (operational) | OLAP (analytical) |
|---|---|---|
| Main read pattern | Point queries by key | Aggregates over many records |
| Main write pattern | Create/update/delete single records | Bulk import (ETL) or event stream |
| Queries | Fixed, defined by the application | Arbitrary, ad hoc |
| Volume | Many small queries | Few, each complex |
| Data represents | Latest state | History of events over time |
| Typical size | GB to TB | TB to PB |

Why not run analytics on the OLTP database (DDIA 2e ch. 1): data is spread across silos; OLTP schemas and layouts suit analytics poorly; expensive scans degrade user-facing latency; network, security or compliance rules may block access. Giving users ad hoc SQL on an OLTP primary also risks permission leaks and expensive queries hurting others.

Variants:
- **Data warehouse**: separate read-only database with a copy of all OLTP data, loaded by ETL (extract by periodic dump or change stream, transform to an analysis-friendly schema, clean, load). ELT transforms after loading. SaaS sources are reached through vendor APIs, often via connector services (Fivetran, Singer, Airbyte are named).
- **Data lake**: copies of any potentially useful data as plain files with no imposed schema (Avro/Parquet, text, images, sensor data, feature vectors). Cheaper and more flexible; usually object storage. Exists because data scientists need feature engineering, NLP and vision work that SQL handles badly. The "sushi principle" is that raw data is better: each consumer transforms it for its own needs. A lake is often a stop before the warehouse.
- **Reverse ETL**: pushing analytic outputs (for example a trained recommendation model) back into operational systems.
- **Product / real-time analytics** (Pinot, Druid, ClickHouse): analytical queries embedded in a user-facing product, with real-time ingestion and low-latency answers. Traditional OLAP is batch-ingested and throughput-oriented.
- **HTAP**: one system for both, avoiding ETL. The book's caveats: many HTAP products are an OLTP engine plus a separate analytic engine behind one interface, and good practice is one database per operational service but one warehouse across them, so HTAP does not replace the warehouse. Choose HTAP when the same application needs large scans and low-latency single-record read/update together (fraud detection is the example).

Decision rule: keep OLTP and analytics apart by default; reach for HTAP only for the one-application, both-patterns case; keep raw data in a lake when consumers differ; feed analytics from a change stream when daily reruns are too slow (pipeline mechanics are in `arch-data-pipelines`).

Do not apply when: the data is small. The chapter's position is that general-purpose systems handle small volumes comfortably ("keep it in a spreadsheet" level), and specialisation pays only as scale grows. A single Postgres with a read replica or a scheduled export is a legitimate analytics setup for a small product (adaptation, not the book's claim).

## 2. System of record vs derived data

- **System of record** (source of truth): holds the authoritative version; new data is written here first; each fact is represented once, usually normalised; on any discrepancy it is right by definition.
- **Derived data**: produced from another system by a repeatable process; can be lost and recreated. Examples: caches, indexes, denormalised values, materialised views, search indexes, trained models. It is redundant by definition and exists to speed reads. One source can feed many derived views.
- The distinction is about how a tool is used, not which tool it is: a database can be either.
- Analytical systems are usually derived. Operational services often mix both.
- You need a defined process that updates derived data when the source changes. Many databases assume they are the only one, which makes this hard; that gap is why change data capture and pipelines exist (`arch-data-pipelines`).

Apply by labelling every store in a design diagram as SoR or derived, and for each derived one naming (a) its source, (b) its refresh mechanism, (c) its rebuild path, (d) its acceptable staleness. A store with no label is a design gap. A derived store with no rebuild path is effectively a second system of record whether you meant it or not.

## 3. Cloud vs self-hosting

Spectrum: build and run in-house, then off-the-shelf self-hosted (on-premise hardware or IaaS VMs), then managed cloud service or SaaS. Rule of thumb in the chapter: keep core competencies and competitive advantages in-house; buy commodity. Deployment tooling such as Kubernetes is out of scope.

| Factor | Favours a cloud service | Favours self-hosting |
|---|---|---|
| Skills | You do not know how to operate it, and hiring ops staff is costly | You already operate it competently |
| Load shape | Highly variable; bursty analytics that idles between queries | Predictable and steady; buying machines is often cheaper |
| Data size (analytics) | Large data needing much parallel compute briefly | Small data: the difference is insignificant |
| Control | You accept vendor limits | You must tune, read OS metrics and logs, add features, or need extreme latency |
| Risk | You accept outage dependency and lock-in | You want to avoid lock-in, geopolitical lockout, or trusting a provider with security and compliance |

Cloud downsides to put in the decision record: a missing feature can only be requested; outages are waited out; performance bugs are hard to diagnose without OS or server-log access; shutdowns, price or product changes force migration; no standard APIs means lock-in (compatible APIs mitigate it); sanctions can lock you out; the provider holds your data, which complicates compliance. Hybrid is common. The book presents the cost claims as contested, so decide on skills and load predictability, not slogans.

### Cloud-native architecture
Cloud native means designed to exploit cloud services, with claimed benefits over merely managed self-hosted software: better performance on the same hardware, faster failure recovery, quick scaling, larger datasets.

| Category | Self-hosted examples | Cloud-native examples |
|---|---|---|
| OLTP | MySQL, PostgreSQL, MongoDB | Aurora, Azure SQL Hyperscale, Spanner |
| OLAP | Teradata, ClickHouse, Spark | Snowflake, BigQuery, Azure Synapse |

Key ideas:
- Higher-level services are built on lower-level ones (Snowflake on S3). A higher-level abstraction fits a narrower use case; if one fits, use it, otherwise assemble from lower pieces.
- **Separation of storage and compute** (disaggregation): traditionally the local disk is assumed durable. In the cloud, VM-local disks are an ephemeral cache. Virtual disks (EBS and equivalents) emulate block devices over the network, which adds overhead and makes every I/O a network call. Cloud-native systems therefore use object storage for durable bulk data (built for large files, hundreds of KB to GB). Because rows are small, they keep small values in a separate service and put larger blocks of many values in the object store. Cost: analysis code must run outside the object store, so data crosses the network.
- **Multitenancy**: shared hardware gives better utilisation and easier scaling, but needs careful performance and security isolation.
- Operations change shape: capacity planning becomes financial planning, performance tuning becomes cost optimisation, and you must know provider quotas and limits before you hit them. The need for operations remains.

Verify: if choosing a managed service, can you state the exit path (export format, compatible API), the quota that would bite first, and who gets paged for a provider outage?

## 4. Single node vs distributed

Valid reasons to distribute: inherent distribution (many users/devices); calls between cloud services; fault tolerance (redundancy survives machine or datacentre loss); scalability beyond one machine; latency (regions near users); elasticity; specialised hardware; legal data residency; sustainability.

Costs of distribution:
- Any network call can fail or time out, and on timeout you do not know whether it was processed; retries may be unsafe.
- A network call is vastly slower than an in-process call. More nodes are not always faster: a simple single-threaded program on one machine can beat a 100+ core cluster (the COST paper).
- Debugging needs observability (metrics, individual events, tracing).
- With one database per service, cross-service consistency becomes the application's problem; distributed transactions are rarely used in microservices.

Rule: a task on one machine is often much simpler and cheaper, and hardware has grown. Single-node databases (DuckDB, SQLite, KùzuDB are named) cover many workloads. Do not distribute until you can name which reason above applies. When you cannot avoid it, hand off to `arch-replication-and-consistency`.

## 5. Microservices and serverless as data decisions

- Typically each microservice owns its database. A shared database makes the schema part of every service's API (hard to change) and lets one service's queries hurt another.
- The book's framing: microservices are mainly a technical solution to a people problem, letting teams progress independently. In a small organisation with few teams they are likely unnecessary overhead.
- Costs: testing needs dependents running; each service needs deploy, scale, log, monitor and on-call infrastructure; API evolution breaks clients, often late. Compatibility rules are in `encoding-and-schema-evolution.md`.
- Serverless/FaaS bills per execution and allocates hardware per request. Costs: execution time limits, restricted runtimes, cold starts. The label is also used for autoscaling usage-billed data services (BigQuery, some Kafka offerings).
- HPC differs from cloud services: batch jobs checkpoint and stop the whole cluster on failure, trusted interconnects, specialised topologies. Always-on services cannot stop everything, which is why this book's techniques look different.

## 6. Law, privacy and data minimisation

- Treat privacy law as an architecture input: GDPR (since 2018), CCPA, the EU AI Act are named. Payment and vendor standards: PCI, SOC 2 Type 2.
- The design tension: erasure rights versus immutable logs, append-only storage and derived datasets (including ML training data). Deleting mid-file in immutable files, or from every derived copy, is a new engineering problem, and the law names no technology and gives no architecture that counts as compliant. LSM engines can keep a deleted record in lower levels until tombstones propagate (see `storage-engines-and-indexes.md`).
- Storing data has a cost: liability, leak damage, fines, compelled disclosure; location and IP logs can expose sensitive behaviour.
- **Data minimisation** (Datensparsamkeit): store only what is worth it, for a stated purpose, no longer than necessary. It opposes speculative hoarding.

Apply: for each personal-data field record purpose, retention limit, and deletion path including derived copies, backups and logs. For event-sourced designs see the crypto-shredding option in `data-models.md`.

## 7. Review questions with observable answers

1. Does every datastore in the diagram carry a SoR/derived label, and does every derived store have a named rebuild procedure that someone has run?
2. Is any analytics or reporting query pointed at the OLTP primary (check connection strings, BI tool configs, cron jobs)? Is any user-facing request path blocked on the warehouse?
3. For each service boundary or network hop: what happens on timeout, is the retry idempotent, who owns cross-boundary consistency?
4. Can one node plus a replica for availability hold the data and load with headroom? If not, which specific reason to distribute applies, written down?
5. Does every personal-data field have purpose, retention and deletion path across derived copies?
6. Is the cloud-vs-self-host choice justified against the skills, load shape, control and lock-in factors, with an exit path?

Items 1, 2, 5 and parts of 3 and 4 are inferred review questions from the chapter's content, not lists the book gives.
