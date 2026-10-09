# Foundational choices before the component design

Decisions that shape a whole design and are cheap to make early and expensive to reverse. Source: DDIA 2e ch. 1 (operational vs analytical,
system of record vs derived data, cloud vs self-hosting, single node vs distributed, microservices and serverless, law and society), with
cross-references to the System Design Interview scaling ladder. Items marked (inferred) are review questions the note-taker proposed.

## Contents
1. Operational vs analytical
2. System of record vs derived data
3. Cloud vs self-hosting
4. Single node vs distributed
5. Microservices and serverless
6. Privacy and law as architectural inputs
7. Review questions

## 1. Operational vs analytical

| Property | OLTP (operational) | OLAP (analytical) |
|---|---|---|
| Main read pattern | Point queries by key | Aggregate over many records |
| Main write pattern | Create/update/delete individual records | Bulk import (ETL) or event stream |
| Human user | End user of web or mobile app | Internal analyst, decision support |
| Machine use | Check if an action is authorised | Detect fraud/abuse patterns |
| Queries | Fixed, predefined by the application | Arbitrary ad hoc exploration |
| Volume | Lots of small queries | Few, each complex |
| Data represents | Latest state (now) | History of events over time |
| Size | GB to TB | TB to PB |

- Do not give users ad hoc SQL on the OLTP database: permissions leak and expensive queries hurt other users.
- Why a separate warehouse: data silos across systems; OLTP schemas are poor for analytics; analytic queries degrade OLTP performance; network, security or compliance may block access.
- Warehouse = separate read-only database with a copy of all OLTP data, loaded by ETL (extract by periodic dump or change stream, transform to an analysis-friendly schema, clean, load). ELT transforms after loading. SaaS sources are reached via vendor APIs, often through connector services.
- Data lake = centralised repository of copies of any potentially useful data as plain files with no imposed schema; more flexible and usually cheaper (object storage), often an intermediate stop before the warehouse. "Raw data is better": each consumer transforms for its needs. Data scientists need it because feature engineering and NLP/vision do not fit SQL.
- Reverse ETL pushes analytic outputs (such as a trained model) back into operational systems.
- Product analytics / real-time analytics (Pinot, Druid, ClickHouse): analytical workload embedded in a user-facing product, ingesting in real time with low-latency answers. Traditional OLAP is batch-ingest and high-throughput.
- HTAP: one system for both, avoiding ETL. Caveats: many are an OLTP engine plus a separate analytic engine behind one interface; and good practice is one database per operational service but one warehouse for cross-system queries, so HTAP does not replace the warehouse. Choose HTAP when the same application needs both large scans and low-latency single-record reads/updates (example: fraud detection).
- Depth on engines and formats: `arch-data-storage`; pipelines: `arch-data-pipelines`.

Rule: if a design has a dashboard or report on production data, add a warehouse or replica and feed it by pipeline; do not point analytics at the OLTP primary.

## 2. System of record vs derived data

- System of record (source of truth): the authoritative version; new data is written here first; each fact is represented exactly once (typically normalised); on any discrepancy it is correct by definition.
- Derived data: the result of transforming data from another system; it can be lost and re-created from the source. Examples: caches, denormalised values, indexes, materialised views, transformed representations, trained ML models. Redundant by definition but essential for read performance; many derived views can come from one source.
- Analytical systems are usually derived; operational services mix both.
- The distinction is about how you use a tool, not the tool: a database is not inherently one or the other.
- Be explicit about which data derives from which. You need a process to update derived data when the source changes; many databases assume they are the only database, which makes that hard (that is why pipelines and change data capture exist: `arch-data-pipelines`).

Design rule: label every store in a diagram SoR or derived; each derived store needs an owner, a rebuild path and a staleness bound (the staleness bound is an inference, the rest from the book). This is what makes cache design (`building-blocks.md` section 2) and feed fan-out safe.

## 3. Cloud vs self-hosting

Spectrum: bespoke in-house build and run, off-the-shelf self-hosted (on-premises hardware or IaaS VMs), managed cloud service/SaaS. Rule of thumb: core competency in-house, commodity bought.

| Factor | Favours cloud service | Favours self-hosting |
|---|---|---|
| Skills | You do not know how to deploy/operate the system; hiring operations staff is costly | You already operate it competently |
| Load shape | Highly variable (elastic; bursty analytics) | Predictable and steady; machines often cheaper |
| Data size (analytics) | Large datasets needing lots of parallel compute briefly | Small datasets: difference insignificant |
| Control/tuning | You accept vendor limits | You need to tune for the workload, see OS metrics and logs, add features, or need extreme latency |
| Risk | You accept outage dependency and lock-in | You want to avoid lock-in, geopolitical lockout, or trusting the provider with security/compliance |

Cloud downsides: a missing feature means you ask politely; during an outage you wait; bugs and performance problems are hard to diagnose without OS or server-log access; shutdowns, price changes or product changes force a migration; there are no standard APIs, hence lock-in (compatible APIs mitigate it); sanctions can lock you out; you must trust the provider with data security, which complicates regulation compliance. Hybrid is common. The cost claims are contested (the authors cite both sides): decide by skill and load predictability.

Cloud native = designed to exploit cloud services; it builds higher-level services on lower-level ones (object stores such as S3, with a limited API, hide machines and tolerate machine failure); higher-level abstractions fit narrower use cases (use one if it fits; otherwise build from lower-level pieces). Separation of storage and compute: local VM disks are ephemeral cache, virtual disks add emulation overhead and make every I/O a network call, so cloud-native systems use object storage for durable bulk data. Multitenancy shares hardware for better utilisation and needs careful isolation. The vendor examples (Aurora, Snowflake, BigQuery) are dated; the principle (disaggregate storage from compute) is the part to keep.

Operations in the cloud era: automation over manual one-offs; ephemeral over long-running servers; learning from incidents. Customers still choose and integrate services, migrate between them, secure the application, manage inter-service interactions, monitor load and diagnose outages. Capacity planning becomes financial planning; performance optimisation becomes cost optimisation. "The need for operations is as great as ever."

## 4. Single node vs distributed

Prefer a single node (with a replica for availability if needed) until a specific reason applies:
- inherent distribution (multiple users or devices); requests between cloud services;
- fault tolerance/HA (redundancy across machines or data centers);
- scalability beyond one machine;
- latency (regions near users); elasticity;
- specialised hardware (disk-heavy object store, CPU/RAM analytics, GPUs);
- legal compliance (data residency); sustainability (shift jobs to times and places with renewable power).

Costs of distribution: every network call can fail or time out, and on timeout you do not know whether the request was processed, so retries may be unsafe; network calls are much slower than in-process calls; observability is mandatory (metrics, individual events, tracing); cross-service consistency becomes the application's problem and distributed transactions are rarely used between microservices. A simple single-threaded program can beat a 100-plus core cluster (the COST paper), and moving computation to the data is sometimes cheaper.

Cloud vs supercomputing (HPC): HPC jobs checkpoint and stop the whole cluster on a node failure; services must keep serving. HPC has high trust and specialised interconnects; cloud tenants distrust one another and use IP/Ethernet. This book's focus is always-on services.

## 5. Microservices and serverless

- Service-oriented/microservices: one well-defined purpose per service, an API over the network, one team per service. Pros: independent deploys, per-service hardware, implementation hidden behind the API. Each service typically has its own database; sharing a database makes the schema part of the API and lets one service's queries hurt another.
- Cons: testing needs dependents running; each service needs deploy, scale, log, monitor and on-call infrastructure; API evolution breaks clients, often discovered late (mitigate with OpenAPI or gRPC schemas: `arch-api-design`).
- "Microservices are primarily a technical solution to a people problem": letting teams progress independently. Valuable in a large company; with few teams it is likely overhead, so build the simplest thing. Splitting or merging services: `arch-decomposition`.
- Serverless/FaaS: the provider allocates hardware per request and bills for execution time. Costs: execution time limits, restricted runtimes, cold-start latency. It still runs on servers; the label for some services (BigQuery, some Kafka offerings) means autoscaling plus usage-based billing.

## 6. Privacy and law as architectural inputs

- Systems storing personal data fall under GDPR (since 2018), CCPA, the EU AI Act; automated decisions (loans, insurance, hiring, policing) carry responsibility beyond the business.
- Design tension: the right to erasure versus immutable or append-only logs and derived datasets (including ML training data). Deleting mid-file in immutable files or from derived data is a new engineering problem; the law names no technologies and gives no clear guidelines on what architecture is compliant.
- The cost of storing data includes liability, reputational damage on a leak, fines and compelled disclosure; location and IP logs can expose sensitive behaviour. Data minimisation (Datensparsamkeit): store only what is worth it and delete the rest; it matches GDPR (explicit purpose, no repurposing, no longer than necessary).
- Business standards: PCI (payment processors, audited), SOC 2 Type 2 (vendors, third-party audits).

Design consequence: every personal-data field gets a purpose, a retention limit and a deletion path that includes derived copies, backups and logs (inferred). Pipeline-level treatment: `arch-data-pipelines` (integrity, auditing and privacy).

## 7. Review questions (mostly inferred)

- For each datastore: system of record or derived? Is there a rebuild path for every derived store?
- Is any analytics query hitting the OLTP primary? Is any user-facing path blocked on a warehouse?
- For each network hop or service split: what fails on timeout, is a retry safe, who owns consistency across the boundary?
- Can one node plus a replica hold the data and load with headroom? If not, which specific reason to distribute applies?
- Does every stored personal-data field have a purpose, a retention limit and a deletion path including derived copies, backups and logs?
