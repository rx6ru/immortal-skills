---
name: arch-data-storage
description: Guides choosing and shaping how data is stored and encoded - system of record vs derived data, OLTP vs analytics, relational vs document vs graph vs event-sourced models, normalisation, LSM vs B-tree engines, index types (secondary, covering, full-text, vector), columnar warehouses and lakes, encoding formats with schema-evolution compatibility rules, and picking a database type for a service. Use when asked to pick a database, design a schema or data model, add an index, choose Parquet/Avro/protobuf/JSON, change a field in a message or table without breaking old readers, review a migration, set up analytics next to a production database, or decide cloud vs self-hosted or single node vs distributed. Replication and sharding are in arch-replication-and-consistency; isolation levels in arch-transactions; moving data between systems in arch-data-pipelines.
---

# Data storage and encoding

## Purpose

This skill makes data-storage choices explicit and checkable. Before a database, model, index or format is picked, the agent states what each store is for (authoritative or derived, operational or analytical), matches the access pattern to a model and engine, and checks every format change for compatibility between old and new code. The reference files hold the detail; this file helps you pick the right one and verify the result.

## Choose what applies

| The request or the code looks like | Do this | Read |
|---|---|---|
| "Which database should we use?", new service needs storage, "should we add Mongo/Redis/Cassandra?" | Selection procedure; default to relational unless a requirement disqualifies it | `references/choosing-a-database.md` |
| New feature needs tables, collections or a graph; ORM models; "how should I model this?" | Model chooser, normalisation decision per field | `references/data-models.md` |
| Slow query, "add an index", composite or covering index, full-text or semantic search, choosing between write-heavy engines | Index and engine rules | `references/storage-engines-and-indexes.md` |
| Reports or dashboards hitting the production database, warehouse/lake design, Parquet, columnar, star schema | Separate analytics from OLTP; columnar layout | `references/data-system-tradeoffs.md` then `references/analytical-storage.md` |
| Adding, removing, renaming or retyping a field in protobuf, Avro, JSON, an event, a message or an API payload; picking a serialisation format | Compatibility checklist and tests | `references/encoding-and-schema-evolution.md` |
| Service-to-service calls, queues, workflows, "exactly once", rolling deploys with mixed versions | Pick the dataflow mode, apply its compatibility rules | `references/dataflow-modes.md` |
| Cloud vs self-hosted, managed vs run it ourselves, "do we need to distribute this?", microservices vs one database, GDPR/deletion and storage | Trade-off tables | `references/data-system-tradeoffs.md` |
| Event sourcing or CQRS proposed | Fit test and pitfalls | `references/data-models.md` section 8 |

This skill does not apply when:
- The question is about copies of data across nodes, failover, lag anomalies, sharding keys or consensus: use `arch-replication-and-consistency`.
- The question is about concurrent updates, isolation levels, lost updates or write skew: use `arch-transactions`.
- The question is about batch and stream processing mechanics, CDC, outbox or exactly-once sinks: use `arch-data-pipelines`.
- The question is whether and how to split a shared database or a monolith: use `arch-decomposition` (this skill only supplies the type choice after the split).
- API style, gateways, versioning policy: use `arch-api-design`.
- The data is a few thousand rows in a script or a prototype and the user asked for something small. Use the simplest store already in the project and skip the ceremony.

## How to apply

### Procedure A: label every store, then choose

1. List the stores involved (databases, caches, search indexes, warehouses, files, topics). Mark each as system of record (written first, one copy of each fact, correct by definition) or derived (rebuildable: caches, indexes, materialised views, denormalised copies, search indexes, models). The label describes how you use it, not the product.
2. For every derived store, write down source, refresh mechanism, rebuild path and acceptable staleness. If any of the four is missing, say so as a finding; do not invent a mechanism.
3. Classify each workload as OLTP (point reads and writes by key, fixed queries, latest state) or analytical (scans and aggregates over history, ad hoc). Keep them on separate stores by default. Use HTAP only when one application needs both large scans and low-latency single-record updates together.
4. Check scale before distributing. Prefer one node plus a replica for availability until a specific reason applies: fault tolerance, scale beyond a machine, latency to users, data residency, elasticity, specialised hardware. Name the reason in the design.
5. Then continue with procedure B (model), C (engine and indexes) or D (format), whichever the request needs.

### Procedure B: choose the model and the normalisation

1. Look at the dominant access pattern. Tree-shaped data loaded whole with rare cross-links: document. Many-to-one, many-to-many, referencing rows directly: relational. Variable-depth traversal as the core feature: graph. Warehouse/BI: star schema (fact table plus dimensions). Many read shapes over one history, audit, replay: event sourcing with derived views.
2. Treat "one-to-many" as one-to-few. If a parent may have thousands of children, do not embed them.
3. Decide normalisation per field, not per system. Keep a field referenced (normalised) when it changes often or when one change would touch many copies. Copy it (denormalise) only when reads dominate and a named process refreshes the copies, atomically or restartably. Normalised: fast writes, slower reads. Denormalised: the reverse, plus drift risk.
4. If using an ORM, count queries per request in a test. A count that grows with result size is the N+1 problem; fix with eager loading or a join.
5. Schema flexibility is a choice of when the schema is enforced (write vs read), not an absence of schema. If documents will change shape, plan the version field and the backfill.
6. For event sourcing: name events in the past tense, validate commands before appending, never let a view reject an event, embed external lookups (rates, clock) in the event, and plan erasure (personal data outside the log, or crypto-shredding).

### Procedure C: choose the engine and the indexes

Engine rule of thumb (a rule, not a law; benchmark with your workload and run long enough to include steady-state compaction):

| Workload | Lean toward |
|---|---|
| Heavy write ingestion, large compressible data, cheap snapshots | LSM engine (RocksDB, Cassandra, ScyllaDB, HBase) |
| Read-heavy, range queries, predictable latency, rich transactions | B-tree engine (PostgreSQL, InnoDB, SQL Server) |
| Scans and aggregates over history | Column-oriented storage and warehouse |
| Dataset fits RAM, latency critical, loss of recent writes acceptable or a durable log paid for | In-memory |
| Key lookups only, all keys fit in RAM | Hash index over a log |

For each index:
1. Name the query it serves. If you cannot, do not add it: every index is paid for on every write.
2. For a multicolumn index, order columns so the query predicates form a left prefix. An index on (last_name, first_name) serves last_name and last_name+first_name, not first_name alone.
3. Use a covering/included-column index only for hot read queries that justify duplicated data and slower writes.
4. Pick the index kind to the data: B-tree or LSM for ordered keys and ranges; spatial index or space-filling curve for 2-D ranges; inverted index for words, trigram for substring and regex; vector index (flat for exact or small, IVF or HNSW for large with approximate recall) for semantic search.
5. For LSM stores, choose size-tiered compaction for write-dominated loads and leveled for read-dominated ones; remember deletes become tombstones that persist until compaction reaches every level.

### Procedure D: change or choose a format

1. Identify the dataflow: database or event log (both directions needed, data outlives code), RPC/REST during rolling deploy (servers first: requests backward compatible, responses forward compatible), public API (assume old clients forever).
2. Apply the rule for the format:
   - Protobuf/Thrift: tag number is identity. Rename is safe on the wire (not for proto-JSON or code that names the field); never renumber; add with a new tag; on removal reserve the tag; widening an integer is unsafe for old readers.
   - Avro: add or remove only fields with defaults; nullable means a union with null (first if default is null); rename by alias and adding a union branch are backward-only; the writer's schema must be obtainable (file header, version plus registry, handshake).
   - JSON/REST: add only optional request params and new response fields; clients ignore unknown fields; never change a field's meaning or type; send integers above 2^53 as strings.
3. Make every read-modify-write path (ORM, republishing consumer) preserve unknown fields.
4. Never use language-native serialisation (pickle, Java Serializable) for stored or inter-service data: it is language-locked, unversioned, and a remote-code-execution risk on untrusted input.
5. Automate: schema in a registry or repository, a compatibility check in CI, golden fixtures from each released version.

### Procedure E: choose a database type for a service

Run the nine-step procedure in `references/choosing-a-database.md` (a reconstruction from the chapter's prose): describe the data, find the dominant access pattern, state the consistency need, state scale and availability numbers, state skills and operating model, state the change rate, shortlist by strengths and reject by disqualifying weaknesses, require a business justification for any new database type, then model it two ways and record the decision with its consequences in an ADR (`arch-decisions-and-tradeoffs`).

### Decision rules used most often

| Question | Rule | Why |
|---|---|---|
| Analytics on the production database? | Move to a separate read-only copy (replica export, warehouse, lake) | Scans hurt user-facing latency; OLTP schemas suit analytics poorly; access and compliance limits |
| Embed or reference a child collection? | Embed if few and loaded together; reference if unbounded | Documents are loaded and rewritten whole |
| Copy a field into many records? | Only if it rarely changes and a refresh process exists | Copies are derived data and drift |
| Store large raw history for analytics? | Keep raw data; build cubes and materialised views only for known hot queries | A cube cannot answer questions about attributes it does not contain |
| Hash index vs sorted structure? | Sorted unless every key fits in RAM and there are no range scans | Hash indexes cannot serve ranges and must fit in memory |
| Add a column to a large relational table? | Nullable column with default null first, backfill in batches, then switch readers | Adding a nullable column is cheap; rewriting every row and changing a column type are slow |
| Remove a field from a message? | Only if it had a default (Avro) or after reserving the tag (protobuf) | Old data and old readers still exist |
| Which format at an organisational boundary? | JSON with a schema (OpenAPI/JSON Schema) | Agreement across parties outweighs compactness |
| Workflow spanning services must survive crashes? | Durable execution or a saga, with idempotent external calls | A database transaction cannot span the services; replays need determinism |
| Personal data in immutable logs? | Keep it outside the log or encrypt per subject with a deletable key | Deleting from immutable files and derived copies is otherwise unsolved |

Common mistakes to look for in review: an index added "just in case"; a field renamed in a stored JSON document with no reader fallback; an Avro field added without a default; a protobuf tag reused after a field was dropped; analytics queries on the primary; a derived store that has silently become the only copy; a per-service database that another service still reads directly; a chosen database type justified by taste rather than a named requirement.

## Verify

Show the user evidence, not assertions. Pick the checks that match the work done.

1. Store inventory: a table of every store with SoR/derived label, source, refresh path, rebuild path, staleness. A derived store with no rebuild path is reported as a risk.
2. Workload separation: search configuration and code for analytics tools, cron reports and BI connection strings pointing at the OLTP primary; report any found.
3. Index justification: for each new index, the query it serves and the EXPLAIN output showing it is used; for multicolumn indexes, show the predicate is a left prefix. Run EXPLAIN on a representative query before and after.
4. Query-count test: for ORM-backed endpoints, a test that asserts the number of queries does not grow with result size.
5. Compatibility tests for format changes (all runnable in CI):
   - round trip: encode with the new schema, decode and modify with the old code, re-encode, decode with the new code; the new field must survive (achievable for protobuf and for JSON handled as a map; Avro drops writer-only fields on an old-schema read, so for Avro test that republishers pass bytes through or are upgraded first);
   - cross-version fixtures: current code decodes saved samples of every released version, and the previous release decodes samples from the new code;
   - registry or lint gate that fails on a reused protobuf tag or an Avro field added without a default;
   - a JSON payload with an integer above 2^53 round-trips through every language involved.
6. Event-sourcing replay: drop a view, rebuild from the log, compare to the original; any difference points to a hidden dependency on clock or external lookup. Confirm replay does not repeat side effects such as emails.
7. LSM/B-tree behaviour: a benchmark that runs long enough to reach compaction or vacuum steady state, with production-like size; record write stalls, peak disk, and p99 read latency.
8. ANN indexes: recall@k against an exact (flat) baseline before and after parameter changes.
9. Privacy: for each personal-data field, purpose, retention limit and the deletion path including derived copies, backups and logs.
10. Selection record: an ADR or short note stating the dominant access pattern, alternatives rejected and why, and the accepted costs.

Done means:
- every store is labelled and every derived store has a rebuild path;
- the model and normalisation choices are justified per access pattern, with refresh mechanisms for any denormalised copies;
- every index maps to a query and was checked in a query plan;
- every format or schema change was classified by dataflow direction, passed the compatibility checklist, and has an automated test;
- any database-type choice has a written justification and consequences;
- limits or unknowns (no benchmark run, no registry available, ratings unverified) are stated to the user.

## Proportion and limits

- Small data and early products: one relational database usually covers OLTP, modest analytics, JSON documents (most relational systems now support JSON) and even graph-ish queries. Adding a second database type adds operations and skills cost; require a reason.
- Distribution, event sourcing, CQRS, graph databases and polyglot persistence each carry operational cost; do not introduce them for hypothetical scale. The book's position is to keep to a single node until a named reason applies.
- Microservices are mainly a people-and-team solution; with few teams, per-service databases are overhead.
- Product names, page sizes, engine defaults and vendor behaviours in the references are dated (the source is from 2025/2026 and the database-type chapter from about 2021/22); the principles survive but check current docs before relying on a default.
- Contested areas: cloud vs self-hosting cost claims; HTAP claims; ORM value; GraphQL; schema-on-read vs schema-on-write (no clear winner). Present both sides and decide on the project's skills, load shape and change rate.
- Bloom filter, B-tree and compaction numbers are rules of thumb from the book (about 10 bits per key for 1% false positives; trees 3 to 4 levels deep); do not quote them as guarantees.
- The database-type star ratings in the source were images; the type profiles are reconstructed from prose and are qualitative.
- Data minimisation and erasure are design constraints, not afterthoughts; legal advice is out of scope.

## References

- `references/data-system-tradeoffs.md`: read first for OLTP vs analytics, warehouse/lake/HTAP, system of record vs derived data, cloud vs self-host, single node vs distributed, microservice and privacy implications.
- `references/data-models.md`: read when designing schemas or choosing relational, document, graph, event-sourced or DataFrame models; normalisation procedure; star schemas; query languages; GraphQL.
- `references/storage-engines-and-indexes.md`: read when choosing LSM vs B-tree, adding or reviewing indexes, using in-memory stores, or adding full-text, spatial or vector search.
- `references/analytical-storage.md`: read when building or reviewing warehouse, lake, Parquet, columnar layouts, sort keys, materialised views and cubes.
- `references/encoding-and-schema-evolution.md`: read for any format or schema change; holds the compatibility checklist, per-format rules and test recipes.
- `references/dataflow-modes.md`: read when data moves between processes by database, RPC/REST, workflow engines or brokers; RPC pitfalls, load balancing options, durable execution constraints.
- `references/choosing-a-database.md`: read when selecting a database type for a service; type profiles, selection procedure, worked decision record.

## Sources

- Designing Data-Intensive Applications, 2nd ed., ch. 1 (trade-offs in data systems architecture), ch. 3 (data models and query languages), ch. 4 (storage and retrieval), ch. 5 (encoding and evolution), glossary.
- Software Architecture: The Hard Parts, ch. 6 (pulling apart operational data), database type selection and the data decomposition drivers.
