# Stream processing correctness

Read this when writing or reviewing a stream job: time semantics, windows, late events, joins, state, constraints enforced through a log, or the use cases (CEP, analytics, materialised views).

Contents: 1 What a stream job does; 2 Uses; 3 Time; 4 Windows; 5 Joins; 6 State and recovery; 7 Ordering and partitioning; 8 Constraints through a log; 9 Reads as events; 10 Warning signs; 11 Verify.

Source: DDIA 2e ch. 12, ch. 13. Items marked (inferred) are labelled so in the notes.

## 1. What a stream job does

Three things: (1) write to a database, cache or index to keep derived data in sync (the stream consumer should be the only writer to that store); (2) push to humans (alerts, notifications, dashboards); (3) transform into output streams (read-only inputs, append-only output). Partitioning, parallelism, map and filter work as in batch. Differences: the input never ends, so no sort-merge joins; recovery cannot restart from the beginning of a multi-year job.

## 2. Uses

| Use | Notes |
|---|---|
| Monitoring and alerting (fraud, trading, machines) | needs patterns and correlations |
| Complex event processing (CEP) | like a regular expression over event sequences; declarative queries stored long term, events flow through and drive internal state machines; emits a complex event on a match. Roles of query and data are reversed compared with a database |
| Stream analytics | aggregates over windows (rates, rolling averages, comparison with last week, percentiles). May use probabilistic structures (Bloom filters, HyperLogLog, percentile sketches) for memory, but approximation is an optimisation, not inherent to streams |
| Materialised view maintenance | caches, indexes, warehouses, event-sourced app state; the window is all of history, so analytics frameworks with bounded windows fit poorly (Kafka Streams and ksqlDB use compaction) |
| Search on streams | stored queries, documents evaluated against them (Elasticsearch percolator) |

Incremental view maintenance (IVM): database materialised views usually refresh by periodic batch (`REFRESH MATERIALIZED VIEW`), which recomputes everything and is stale in between. Triggers work only for naturally incremental cases. IVM compiles a query into operators that process only changes (Materialize, RisingWave, ClickHouse, Feldera); recent events are buffered in memory and merged with the stored view at read time. Consider IVM before hand-writing a stream job that maintains a view of a SQL query.

## 3. Time

Event time is when the thing happened; processing time is when the system saw it. Batch uses timestamps embedded in events, so reruns are deterministic. Many stream frameworks default to processing time for windows, which is acceptable only if lag is negligible.

Causes of divergence: queueing, network faults, broker contention, consumer restarts, reprocessing or backfill, out-of-order arrival (server B's event reaches the broker before server A's, though A happened first). Effect of using processing time: redeploy for a minute, catch up on the backlog, and the request rate appears to spike. Rule: use event time for correctness.

Stragglers: you can never be sure a window is complete. Policy options:
1. Ignore late events, count them as a metric, and alert when the dropped count rises.
2. Publish a correction (an updated value, possibly retracting the earlier output).
An optional watermark message ("no more events earlier than t") can close windows; with several producers track each individually, which is harder when producers come and go.

Whose clock: mobile devices buffer events offline for hours or days and their clocks cannot be trusted. Log three timestamps: event time (device clock), send time (device clock), receive time (server clock). Offset is approximately receive minus send; corrected event time is event time plus offset (assumes small network delay and a constant offset). The same issues exist in batch but are more noticeable in streaming.

Decision to make before coding: which time field defines the window, and what is the straggler policy. Write both in the job's documentation.

## 4. Windows

| Window | Definition | Implementation | Use |
|---|---|---|---|
| Tumbling | fixed length, no overlap, each event in one window | round the timestamp down | per-minute counts, reports |
| Hopping | fixed length with overlap (5 minutes, hop 1 minute) | compute 1-minute tumbling windows, then aggregate adjacent ones | smoothing |
| Sliding | all events within an interval of each other | time-sorted buffer, evict expired events | proximity |
| Session | no fixed duration: one user's events with gaps shorter than the inactivity timeout (for example 30 minutes) | per-key state | web analytics sessionisation |

State: counters are constant size; sliding windows and stream joins buffer events, so plan memory and disk for large windows and high throughput. Unbounded window state is a standing risk.

## 5. Joins

| Join | Inputs | State kept | Notes |
|---|---|---|---|
| Stream-stream (window join) | two activity streams, for example search and click joined by session ID | both sides' events within the window, indexed by key | the click may arrive days later, or before the search; choose a window (for example an hour); emit "clicked" on match and "not clicked" when the search expires. Embedding search details into the click event is not equivalent, since it loses searches that were never clicked. Needed for click-through rate |
| Stream-table (enrichment) | activity stream plus a database table (user profiles) | local copy of the table (in-memory hash table or local index): a hash join | a remote lookup per event is slow and can overload the database; keep the copy fresh by subscribing to the table's CDC changelog; table-side window is all of history, newer overwrites older |
| Table-table (view maintenance) | two changelogs (posts, follows) | each side's current state | the home-timeline cache is the materialised join of posts and follows: new post goes to every follower's timeline; delete removes; follow adds recent posts; unfollow removes. Product rule: (u v)' = u' v + u v' |

Time dependence: ordering across streams or partitions is undefined, so which version of the joined state applies? Example: a sale needs the tax rate at the time of sale. If order is undefined the join is nondeterministic and a rerun may give different output. Fixes:
- Put a version ID on the joined record (slowly changing dimension), for example the tax-rate version stored on the invoice. Deterministic, but log compaction becomes impossible since all versions must stay.
- Or denormalise: write the applicable rate into every sale event.

## 6. State and recovery

State rebuilt after failure from one of:
- A remote datastore (slow per-message queries).
- Local state replicated periodically (Flink snapshots to a distributed file system; Kafka Streams changelog topic with compaction, similar to CDC; VoltDB processes each message redundantly on several nodes).
- Rebuild from the input streams (short windows replay; a local replica of a table can be rebuilt from a compacted CDC stream).

The choice depends on network versus disk latency and bandwidth. Fault tolerance techniques (microbatching, checkpoints, transactions) are in `exactly-once-and-idempotency.md`.

## 7. Ordering and partitioning

- Route events that need ordering to one partition by key.
- Within a partition a single-threaded consumer processes in order. If log and state are sharded the same way, no locking is needed.
- Events touching several partitions need extra design (section 8, and the multishard transfer in `exactly-once-and-idempotency.md`).
- Partition count caps parallelism (`messaging-and-logs.md`).

## 8. Constraints through a log

Uniqueness in a distributed setting requires consensus: someone must decide which conflicting operation wins. Typically a single leader decides; scale out by sharding on the value that must be unique. Asynchronous multi-leader replication cannot enforce strict uniqueness. To reject a violating write immediately, synchronous coordination is unavoidable.

Username claim via a log:
1. Append each claim as a message to the log shard chosen by hash of the username.
2. One single-threaded stream processor reads that shard, keeps a local database of taken names; if free, mark taken and emit success; else emit rejection to an output stream.
3. The client watches the output stream for the outcome of its request.

General principle: route all writes that may conflict to the same shard and process them sequentially; the conflict definition and validation logic can be arbitrary. Scale by adding shards. When the business can tolerate occasional violations followed by an apology, see the loosened-constraint rule in `exactly-once-and-idempotency.md`.

## 9. Reads as events

Stream processors' internal state can be exposed to queries. Going further, represent read requests as events through the same processor as writes; serving a read becomes a stream-table join and the processor emits results to an output stream. Reads must be routed to the shard that holds the data. Benefit: logging reads records what the user saw (shipping date and stock status shown before buying), giving causal tracking and provenance. Cost: extra storage and I/O. Worth it when you already log reads operationally. If a database offers multishard joins natively, that is simpler than building them on a stream processor.

## 10. Warning signs

- Windowing by processing time, or spikes after redeploys.
- No policy for late events; no metric for dropped late events.
- Stream-table join through a remote database call per event.
- Sliding window or join state without a size bound or capacity estimate.
- Joins whose result depends on cross-partition arrival order.
- Device timestamps trusted without correction.

## 11. Verify

- Replay test: run the job twice over the same recorded input, including a shuffled arrival order across partitions; the output should match if the job is deterministic (inferred). If not, find the time-dependent join.
- Backlog test: pause the consumer, let a backlog build, resume; windowed counts must equal counts from an uninterrupted run (event-time correctness).
- Late-event test: inject events later than the watermark or allowed lateness; show the chosen policy (dropped and counted, or corrected output).
- State-size check: report state size per key and total for the largest window under peak throughput; compare with capacity.
- Replay a window from offset X into a scratch output and compare with live output.
- Monitors to show: consumer lag, dropped-late-event count, checkpoint duration (inferred), state size (inferred).
