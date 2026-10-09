# Choosing a database type for a service

Use this file when a service, or a data domain inside one, needs a database and the question is which type: relational, key-value, document, column-family, graph, NewSQL, cloud-native or time-series. It gives the evaluation characteristics, a per-type profile, a selection procedure, the aggregate-orientation concept and a worked decision record. Deciding whether to split a shared database at all is covered in `arch-decomposition`; this file only summarises the drivers so you can see where type choice enters.

Contents
1. When the type question arises
2. Evaluation characteristics
3. Profiles by database type
4. Aggregate orientation and its limits
5. Selection procedure
6. Mapping to storage engines
7. Worked decision: survey data to a document store
8. Verification

Sources: Architecture: The Hard Parts ch. 6 (database type selection; the star-rating charts were images and are not in the notes, so the profiles below are reconstructed from prose and the ratings are qualitative); DDIA 2e ch. 3 and ch. 4 for the engine mapping.

---

## 1. When the type question arises

Why data is hard to pull apart: it is the company's most important asset and is tightly coupled to application functionality, so seams are hard to find. Microservices require each service to own its data; service-based architecture allows a shared database. The six reasons to split a database (data disintegrators) are: change control (how many services does a table change hit?), connection management (each service instance has its own connection pool and a shared database saturates), scalability, fault tolerance (a shared database is a single point of failure), architectural quanta (the database is part of static coupling), and **database type optimisation** (one database means one type for all data; splitting lets reference data go to a key-value store, survey data to a document store). The two reasons to keep data together are data relationships (foreign keys, views, triggers, stored procedures) and database transactions (multi-table ACID). Work through those with `arch-decomposition`; come back here once a data domain stands alone and needs a type.

Ownership rule the notes use: a service owns the data it writes; read-only access is not ownership; other services ask the owner via a contract, which also abstracts callers from the schema.

## 2. Evaluation characteristics

Score each candidate against:
1. Ease of learning curve.
2. Ease of data modelling.
3. Scalability and throughput.
4. Availability and partition tolerance.
5. Consistency (ACID versus BASE/tunable).
6. Programming language support, product maturity, SQL support, community.
7. Read versus write priority (a scale, not a binary).

## 3. Profiles by database type

| Type | Products | Learning | Modelling | Scale and throughput | Availability / partitions | Consistency | Read/write fit |
|---|---|---|---|---|---|---|---|
| Relational | PostgreSQL, Oracle, MS SQL, MySQL | Easiest, widely taught | Flexible: key-value, document, graph-like possible; arbitrary-depth graphs hard | Mostly vertical on big machines; replication and failover are complex | Favours consistency over availability and partitions | Strongest: ACID | Balanced; design for reads or writes |
| Key-value | Riak KV, DynamoDB, Redis, MemcacheDB | Easy but needs unlearning (no "get all keys") | Aggregate-oriented; query by key only, client must know the key (session_id, user_id, order_id); changing an aggregate means rewriting all | Very high (no joins or order by) | Varies; tunable per query (Riak quorum all/one/quorum) | Tunable; strong consistency costs latency; majority quorum is a good compromise | Read priority; sessions, cached user preferences |
| Document | MongoDB, Couchbase, AWS DocumentDB | Easy (JSON/XML familiar) | Aggregates (orders, tickets); forgiving because parts are queryable and indexable | Easy to scale; complex indexes reduce it; sharding adds complexity and needs a sharding key | Configurable high availability; replicated shard clusters are complicated | Some ACID within a collection (edge cases); tunable quorum | Read priority (secondary indexes) |
| Column family (wide column) | Cassandra, Scylla, SimpleDB | Hard (row key, super columns) | Needs iterations on row-key design; CQL helps | Highly scalable horizontally, reads and writes | Cluster-native; replication factor 3 default; node loss is transparent | Tunable per operation (ANY to ALL); higher levels lower availability | Write-heavy and sparse data (SSTables, commit log, memtables) |
| Graph | Neo4j, Infinite Graph, TigerGraph | Steep | Hard: relations are explicit directed edges; start with properties on relations, later convert them to nodes; changing a relationship type is expensive (visit both nodes, create new edge, delete old) | Read scale via replicas; write throughput constrained (hard to shard); traversal very fast | Distributed ones use leader promotion | Many support ACID (Neo4j) | Read heavy |
| NewSQL | VoltDB, ClustrixDB, SingleStore, CockroachDB | Easy (SQL) | Familiar, plus shard design and geo placement | Horizontal, multiple active nodes | High; CockroachDB survives disk, machine and datacentre failure | Strong ACID | Like relational, with geo distribution to optimise reads or writes |
| Cloud native | Snowflake, Datomic, Redshift, Azure CosmosDB | Varies (Redshift relational-like; Snowflake separates storage/compute; Datomic uses immutable facts) | Varies; Snowflake/Redshift warehouse-style, Datomic schema-less entities | Automatic scaling for a price: cost is the trade-off | High but varies (Redshift single AZ unless multi-cluster; Snowflake cross-region replication) | ACID in these three | Warehouses read-priority; Datomic both (EAVT index) |
| Time series | InfluxDB, kdb+, TimescaleDB, Amazon Timestream | Easy concept; append-only needs unlearning | Timestamped, tagged points; one fact per tag (`ticket_status=Open, ticket_id=374737`, not `ticket_info=Open.374737`) | Timescale scales like PostgreSQL; Influx clusters with meta and data nodes | Better with replication factor or meta/data nodes | ACID if the engine is relational; else tunable any/one/quorum | Append-only, read-heavy; not general purpose |

Ecosystem notes (from the same chapter): relational has the most mature but vendor-splintered ecosystem and is weaker on reactive streams; document is the most popular NoSQL with many drivers; cloud-native options are newer and harder to hire for, need a cloud account, and lower DBA load; column-family has active communities and SQL-like CQL.

## 4. Aggregate orientation and its limits

Aggregate-oriented databases (domain-driven design term) operate on related data as one unit, such as a ticket or a customer with dependents. All the NoSQL families in the chapter are aggregate-oriented.
- Benefits: easy distribution (copy the whole aggregate across the cluster), fewer joins and better read/write performance, less impedance mismatch.
- Costs: hard to get aggregate boundaries right and hard to change them later; analysis across aggregates is hard.

Also from the chapter:
- Sharding is horizontal partition across nodes by a sharding key (partitioning is the same idea on one server). Details in `arch-replication-and-consistency`.
- "Schema-less" is a myth: data always has a schema, implicit or elsewhere, and the application must handle multiple schema versions (see `data-models.md` section 4 and `encoding-and-schema-evolution.md`).

## 5. Selection procedure

The chapter's procedure is derived from its text (the exact steps are a reconstruction). Apply in order:

1. Describe the data domain: entities, how they are read together, how they change.
2. Identify the dominant access pattern: by key; by relationships; by time window; analytical scans; mixed.
3. State consistency needs: strict ACID across several records, or tunable/eventual acceptable.
4. State scale, throughput and availability needs with numbers where possible (`arch-system-design` covers estimation).
5. State team skills, hiring, and operating model (managed service or self-run).
6. State how often the shape will change, and who pays for a change.
7. Shortlist the types whose strengths match steps 2 to 4; reject those whose weak points hit a hard requirement.
8. If the shortlist includes anything other than the database type already in use, require a business justification. Each new type costs operations and skills. In the case below, the winning argument was the cost of change to the business, not engineering taste.
9. Model the data both ways (for example single aggregate and multiple aggregates) before deciding; write the decision as an ADR (`arch-decisions-and-tradeoffs`).

Default rule (adaptation, consistent with the notes' emphasis on justification and DDIA's emphasis on simplicity): if relational meets the requirements, start there; the burden of proof lies with the alternative. Do not treat the type profile table as ratings to sum; use it to find disqualifying weaknesses.

Quick pointers (from the profiles):
- Session store, cache, lookup by key at very high rate: key-value.
- Entity with nested parts rendered or loaded whole, frequent shape change: document.
- Heavy write volume, sparse wide rows, horizontal scale, tunable consistency: column family.
- Relationships and multi-hop traversal are the product: graph.
- Relational semantics but need horizontal scale or geo distribution: NewSQL.
- Elastic, usage-priced analytics or serverless operation: cloud-native warehouse.
- Append-only timestamped measurements: time series.
- Everything else, or unsure: relational.

## 6. Mapping to storage engines

The type profile connects to engine internals in `storage-engines-and-indexes.md`:
- Column-family stores (Cassandra, Scylla, HBase) are LSM-based: strong writes, costlier range scans and deletion lag.
- PostgreSQL, InnoDB and SQL Server are B-tree based: predictable reads and range scans, random write cost.
- Warehouses use column-oriented storage (`analytical-storage.md`).
- Do not confuse the wide-column data model (row-oriented) with column-oriented storage.
- Document stores load and rewrite whole documents, so keep documents small (`data-models.md`).

## 7. Worked decision: survey data to a document store

Setting (a running case in the book, "Sysops Squad"): a system's survey data domain sits in relational tables; developers want a JSON document store, the data architect objects that relational has always worked and that adding database types is a cost.

How the decision was reached:
1. The data architect required a business justification, not a technical preference.
2. The product owner supplied it: survey changes are frequent and marketing wants flexibility, but each change, even one new question, takes days because of querying and aggregating relational data for the UI; marketing has stopped filing change requests. The driver is flexibility and time to change.
3. Developers and the database team collaborated on modelling both ways: (a) single aggregate, a survey document with an embedded questions array (one get renders the survey; questions are duplicated across survey documents); (b) multiple aggregates, a survey with question references and separate question documents (reuse, no duplication; harder to render and retrieve).
4. Facts decided it: only five survey types (one per product category), changes mostly add or remove questions, complexity lives in the UI, so accept duplication and choose (a).

Decision record, in short form:
- Context: customers get one of five survey types after work completes, shown on a web page; stored relationally; the team wants a JSON document store.
- Decision: use a document database, because marketing needs flexibility and timeliness and it simplifies the survey UI and eases change.
- Consequences: with a single aggregate, several documents change when a common question is updated, added or removed; the survey function must be shut down during migration from the relational to the document store.

Note how the consequences section records the cost accepted. The full ADR template is in `arch-decisions-and-tradeoffs`.

Related evidence pattern from the same case for splitting the database at all: logs showed ticketing queries timing out whenever reporting ran (reporting's parallel threads consumed the connections); projected connection counts exceeded what one database offers by about 2,000; a single database down meant all services down; and the shared database forced one quantum. Worked connection arithmetic and the five-step split process are in `arch-decomposition`.

## 8. Verification

- The decision names the dominant access pattern and the disqualifying weaknesses considered, not only the benefits.
- A business or measurable justification exists for any new database type, written in an ADR with consequences.
- The data model was drafted in at least two forms and the trade-off recorded (aggregate boundaries are hard to change later).
- No service holds credentials for another service's database; cross-domain data goes through the owner's contract (check connection strings and grants).
- Consistency requirement is stated and the chosen product's setting (ACID scope, quorum level) matches it. Test it by a failure-injection or concurrent-write test appropriate to the claim (inferred).
- Schema change path is known: how a shape change reaches stored data and old readers.
- Exit cost recorded for cloud-native and proprietary choices.
