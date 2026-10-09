---
name: arch-data-pipelines
description: "Guidance for moving and transforming data outside the request path: batch jobs, stream processing, message brokers and logs, change data capture, outbox and event sourcing, keeping search indexes, caches and warehouses in sync, event-time windows and joins, exactly-once and idempotent sinks, pipeline SLOs and failure handling, auditing, and deletion in derived data. Use when designing or reviewing an ETL/ELT job, a Kafka or queue consumer, a nightly or streaming pipeline, a sync between a database and another store, a retry or duplicate-delivery problem, stale or corrupt pipeline output, or a request to \"use CDC\", \"add an outbox\", \"make this idempotent\" or \"reprocess history\". Storage engines and encodings are in arch-data-storage; isolation levels in arch-transactions; SLO arithmetic in arch-reliability-slos."
---

# Data pipelines: batch, streams, derived data

## Purpose

Work that happens outside the request path (jobs, consumers, syncs between stores) fails in quiet ways: duplicates after a retry, two stores that disagree forever, windows that move when you redeploy, output that is visible half-written, data that is fresh but wrong. This skill gives the agent a way to pick the processing mode and the sync mechanism, to build in the few properties that prevent those failures (immutable input, one decided order, idempotent sinks, event time, a rebuild path), and to show evidence that they hold.

## Choose what applies

| The task or code looks like | Do this | Read |
|---|---|---|
| "Should this be a nightly job, a stream, or a service call?" | Run the decision questions on freshness, boundedness, replay, authority | `references/batch-vs-stream-vs-request.md` |
| Batch job, ETL, Spark/Flink/warehouse SQL, workflow DAG, spot instances, big joins | Batch procedure below; check the output-publish rule | `references/batch-processing.md` |
| Batch output must reach a production database, search index or serving store | Never write record by record; log buffer or build-and-swap | `references/batch-processing.md` section 11 |
| Choosing queue vs log, partitions, retention, consumer groups, DLQ, ordering, lag | Messaging procedure below | `references/messaging-and-logs.md` |
| A second store (index, cache, warehouse, read model) must follow a primary store | Derived-data decision table; no dual writes | `references/derived-data-sync.md` |
| Handler writes to the database and also publishes or indexes | Replace with outbox or CDC | `references/derived-data-sync.md` sections 2, 5 |
| Windows, late events, stream joins, sessionisation, stream-table enrichment | Stream procedure below | `references/stream-processing-correctness.md` |
| Retries, duplicates, "exactly-once", payments, counters, emails, API idempotency keys | Sink and key procedure below | `references/exactly-once-and-idempotency.md` |
| Constraint enforcement across shards or services without 2PC | Shard by conflict key, or loosen and compensate | `references/exactly-once-and-idempotency.md` sections 6, 9; `references/stream-processing-correctness.md` section 8 |
| Pipeline in production: SLOs, rollout, stale or corrupt data, on-call, maturity review | Reliability procedure below | `references/pipeline-reliability.md` |
| Personal data in pipelines, deletion requests, audits, decisions about people | Integrity and privacy rules below | `references/integrity-auditing-and-privacy.md` |
| Warehouse vs lake vs data mesh; analytics over per-service databases | Compare on partitioning and coupling | `references/analytical-data-architectures.md` |

This does not apply, or another skill leads, when:
- The question is about a single database's behaviour under concurrent transactions (isolation anomalies, lock choices): use `arch-transactions`.
- It is about replication topologies, quorums, sharding keys or consensus themselves rather than moving data between systems: use `arch-replication-and-consistency`.
- It is about storage engine internals, index types, columnar formats or schema evolution rules for encodings: use `arch-data-storage`.
- It is about sagas, orchestration vs choreography or service contracts: use `arch-distributed-workflows`.
- Data is small and changes rarely: a cron script and one query is the right size. See Proportion and limits.

## How to apply

### A. Choose the processing mode

1. Write the freshness requirement as a number and a percentile ("99% of events visible within 5 minutes"). Without it, every mode looks acceptable.
2. If a caller waits and needs the authoritative value, it is request/response. Deliver async results through an output stream the client waits on if needed.
3. If hours of staleness are fine and volume is large, use batch. If the input is naturally unbounded and the requirement is minutes or seconds, use a stream.
4. If you will need to reprocess history with the same logic, require replay (a retained log or raw files in an object store) and event-time semantics. Do not write the logic twice for batch and speed layers.
5. Check whether one machine suffices: if the working set (distinct keys, not records) fits memory or a local engine handles it, do not build a cluster pipeline.

### B. Build a batch job

1. Treat input as immutable and output as derived: a rerun on the same input must give the same output, and a bug fix means rerun, not repair in place.
2. Make the retry unit a task, not the job. Delete partial output on failure; run on spot capacity if cost matters.
3. Publish atomically: write to a unique run location, then switch a pointer or manifest. Object-store rename is not atomic, and directories are only key prefixes.
4. Chain jobs with a workflow scheduler; start a job only when all its inputs have succeeded.
5. For joins and grouping, expect a shuffle on the key; check partition skew when slow.
6. Deliver to serving systems through a log buffer with a completion signal, or build a new dataset and swap it in. Never one write per record against production.

### C. Choose transport and design consumers

1. Per-message expensive work, no ordering need: a work queue. Ordering per entity, replay, several independent consumers, derived data: a partitioned log with partition key = entity ID.
2. Decide the loss policy and the backpressure policy for each stream in writing.
3. Plan partitions (they cap consumer parallelism), retention (longer than the worst consumer outage plus detection time) and a lag alert.
4. Assume at-least-once delivery. Make consumers idempotent and add a poison-message path: N attempts, then a monitored dead letter queue with enough context to repair and republish.
5. Never rely on order across partitions or across load-balanced consumers.

### D. Keep derived data in sync

Decide in this order:
1. Name the system of record. Everything else is derived and must be rebuildable.
2. Existing database is the truth: CDC (or outbox if consumers include production services, or you need a stable event schema). Greenfield with audit needs and event-shaped domain: event sourcing. Otherwise a periodic rebuild may be enough.
3. Reject dual writes: two stores written from application code can diverge permanently under a race or a partial failure, and nothing will notice.
4. Use 2PC across heterogeneous systems only when you control every participant and need immediate atomic visibility, accepting that one participant failing aborts everything.
5. For a new derived system: take a consistent snapshot tied to a log offset, then apply changes after it (or read a compacted topic from the start).
6. Expose a contract, not the raw table schema, to consumers outside the owning team.

### E. Write stream jobs that are correct on replay

1. Window on event time. Choose the window type by need: tumbling for reports, hopping for smoothing, sliding for proximity, session for user activity.
2. Write the late-event policy: drop and count (alert on the count), or emit corrections.
3. Enrich from a local copy kept fresh by the table's change stream, not a remote call per event. If the join depends on the version of reference data at event time, store a version ID or write the applicable value into the event, or reruns will differ.
4. Bound window and join state; estimate memory at peak throughput.
5. Check whether incremental view maintenance covers the need before hand-writing a stateful job for a SQL view.

### F. Make effects happen once

1. Framework exactly-once covers only the inside of the framework. Any effect that leaves it (database write, email, external publish) needs an idempotent write or an atomic commit.
2. Client generates a unique key per logical operation before the first attempt, reuses it on every retry, and passes it through every hop.
3. The final writer enforces it atomically with the effect: a unique constraint on a requests table in the same transaction (not check-then-insert in code), a conditional put, or a processed-ID set in processor state.
4. Retain keys longer than the longest retry window; return the original outcome on duplicates.
5. For a constraint across shards: route conflicting writes to one shard and process sequentially, or accept violations followed by compensation when the business tolerates it. Check synchronously only before irreversible steps.

### G. Operate it as a service

1. Define freshness, correctness (golden data through production) and, if tiered, isolation SLOs, measured end to end by something outside the pipeline.
2. Gate each stage on its inputs: stale data is almost always better than wrong data.
3. Roll out in stages: unit, small dry run, staging with output diff against known-good, canary on a data subset, ramp by share of data.
4. Plan the two failures that dominate: delay (stall and resume, notify) and corruption (stop the spread, then restore or reprocess selectively).
5. Write a playbook entry per alert; score the maturity matrix and fix the weakest rows.

### H. Privacy and integrity

1. For each field collected, state purpose and retention; add a purge job.
2. Inventory every store that holds a subject's data before promising deletion; give immutable logs a retention limit or per-subject keys (crypto-shredding), and make reprocessing honour a deletion list.
3. Schedule reconciliation of derived stores against the source and restore tests of backups.
4. For automated decisions about people, require an appeal path, an owner and a check for proxy features.

## Verify

Pick the checks that match the work and show their output to the user.

| Property | Check |
|---|---|
| Rerun is safe | Run the job twice on the same input; outputs identical; no duplicate rows |
| No partial output visible | Read the target mid-run: old version or nothing, never half |
| Task failure tolerated | Kill a task or consumer mid-run; sink has no duplicates and no gaps |
| Duplicate delivery tolerated | Deliver every message twice; derived state unchanged |
| Retry with key is single-effect | Send the same request twice, sequentially and concurrently, and crash between commit and response; one effect |
| No dual write | Search for handlers touching two stores; each is outbox, CDC, or has a repair job |
| Derived data is rebuildable | Drop the derived store, rebuild from snapshot plus log, compare counts and checksums |
| Replay determinism | Run a recorded window twice, and with partitions reordered; same output |
| Event-time correctness | Pause the consumer, build a backlog, resume; windowed counts equal an uninterrupted run |
| Late-event policy works | Inject an event beyond allowed lateness; observe drop-and-count or correction |
| Poison path works | Send a malformed message in test; it reaches the DLQ and the stream continues |
| Lag alert exists | Show consumer lag, CDC connector lag, DLQ depth and their alerts |
| Freshness SLO is measured | Show the number, the window and the external measurement point |
| Corruption response | Inject bad data in staging; show quarantine, blocked downstream reads, selective reprocess and time taken |
| Deletion propagates | Delete a test subject; query every inventoried store, including a rebuilt derived one |
| Backup is real | Restore the latest backup in a scratch environment and run the integrity checks |

Done means:
- The processing mode is justified by a stated freshness number and a rebuild path.
- No effect leaves the system without an idempotency mechanism, and the test for it has been run.
- Order is decided in one place for each derived store, and the derived store has been rebuilt at least once from its source.
- Windows use event time, with a written late-event policy and bounded state.
- Failure of a task, a consumer and a duplicate delivery have each been exercised, with results shown.
- For production pipelines: SLOs with numbers, a staged rollout plan, alerts with playbooks, and a deletion or retention statement for any personal data.

## Proportion and limits

- A small, slowly changing dataset needs a script and a query, not a log, a stream engine and CDC. The book itself warns that unbundling into many specialised systems is a form of premature optimisation: use one database if it meets all the requirements, and add components only when no single product does.
- Batch is not inferior. If hours of staleness are acceptable, batch gives reversibility and cheap retries that stream systems must work hard to recreate.
- Strict synchronous constraint enforcement can be over-engineering where the business already compensates (oversold stock, overbooking). Equally, a loose asynchronous check before an irreversible action is under-engineering. Ask what an occasional violation plus apology costs against the cost of coordination.
- The log-and-derive approach assumes a replayable ordered log. With a plain queue you lose rebuild-from-log; plan a snapshot path.
- Cross-system causal ordering has no simple answer (the book says so). Do not claim a design solves it unless a named log or shard orders the events involved.
- The chapter on philosophy of streaming is one opinionated school (log-centric dataflow), not consensus. Lambda architecture is described as having fallen out of use; kappa-style unification needs replay, effectively-once semantics and event-time windows, so do not adopt it without all three.
- Product names (Kafka, Flink, Spark, Debezium, Hadoop, Airflow) will date; the durable ideas are ordered log, deterministic derivation, idempotent consumers, end-to-end IDs, event time.
- Ethics and privacy material is EU-centric and argumentative; it prompts questions and does not replace legal review. Mechanisms for appeal, bias testing and derived-store deletion are extensions beyond the book's text.
- Sizing numbers in the notes (for example the retention fill-time example, one-minute gap rule) are illustrations, not defaults. Derive your own from measured rates.

## References

- `references/batch-vs-stream-vs-request.md`: first stop when the mode is undecided; includes lookup-vs-local-copy, precompute-vs-compute-on-read, lambda vs kappa, migration by side-by-side views.
- `references/batch-processing.md`: batch engines, storage, scheduling, workflows, fault handling, shuffle and joins, delivering results to serving systems.
- `references/messaging-and-logs.md`: queue vs log, consumer groups, redelivery and reordering, DLQ, offsets, retention, lag, replay, sizing checklist.
- `references/derived-data-sync.md`: decision guide with failure modes for dual writes, 2PC, CDC, outbox, event sourcing; snapshots, compaction, schema warning; limits of single order; unbundling.
- `references/stream-processing-correctness.md`: event vs processing time, stragglers, windows, joins, state, constraints through a log, reads as events.
- `references/exactly-once-and-idempotency.md`: fault-tolerance techniques, idempotent sinks by sink type, idempotency key procedure, end-to-end argument, multishard requests, timeliness vs integrity, loose constraints.
- `references/pipeline-reliability.md`: SLOs for pipelines, lifecycle, hotspotting, delay and corruption response, maturity matrix, event-delivery case study.
- `references/integrity-auditing-and-privacy.md`: auditing, designing for auditability, deletion in immutable and derived data, data handling rules, decisions about people, consent.
- `references/analytical-data-architectures.md`: warehouse, lake and data mesh with DPQ coupling rules and a worked case.

## Sources

- Designing Data-Intensive Applications 2e, ch. 11 Batch Processing.
- Designing Data-Intensive Applications 2e, ch. 12 Stream Processing.
- Designing Data-Intensive Applications 2e, ch. 13 A Philosophy of Streaming Systems (data integration, unbundling, dataflow, correctness, auditing).
- Designing Data-Intensive Applications 2e, ch. 14 Doing the Right Thing.
- Site Reliability Workbook ch. 13 Data Processing Pipelines (including the event-delivery case study).
- Software Architecture: The Hard Parts ch. 14 Managing Analytical Data.
