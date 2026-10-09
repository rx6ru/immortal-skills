# Batch vs stream vs request/response

Read this when the first question is "which processing mode does this work belong in?" or when someone proposes a nightly job, a streaming rewrite, an RPC lookup, or a lambda-style double pipeline.

Contents: 1 The three modes; 2 Decision questions; 3 Decision table; 4 Reference data: lookup vs local copy; 5 Precompute vs compute on read; 6 One engine for history and live data; 7 Reprocessing and migration; 8 Worked examples; 9 Warning signs; 10 Verify.

## 1. The three modes

| | Online (request/response) | Batch | Stream |
|---|---|---|---|
| Input | one request | bounded, read-only, immutable | unbounded sequence of events |
| Output | response to a waiting caller | generated from scratch each run, usable after the job ends (in most frameworks) | continuously updated output, append-only |
| Metric that matters | latency, availability | throughput; minutes to days; often periodic | delay between event and effect |
| Recovery from a bug | fix code; data the buggy code wrote stays wrong | roll back code and rerun; or keep old output and switch back | replay the log from an earlier offset into a new output |
| Cost | always-on capacity | whole input reprocessed on any change; hours of latency | state management, time semantics, fault-tolerance machinery |

(DDIA 2e ch. 11 and ch. 12.) The batch advantage comes from two properties: inputs are immutable and the job has no side effects outside its output. Together they make a mistake reversible, which makes the team willing to change things (the book calls this human fault tolerance). If a design gives those properties up (a job that writes straight into a production database), it also gives up the advantage.

Stream processing is batch with the "bounded" assumption removed. Sorting cannot work on unbounded input because the last record could sort first, so stream systems replace sort-merge with windows, local state and buffering.

## 2. Decision questions

Ask these in order. Stop at the first decisive answer.

1. Does a caller wait for the answer and need the authoritative value at that moment? Use request/response (the read path). The result can still be delivered through an output stream the client waits on (DDIA 2e ch. 13).
2. How stale can the result be? Hours or days acceptable and data volume large: batch. Seconds to minutes: stream. Anything between is a negotiation over cost; say the number out loud before choosing. (Batch with a short period is not stream processing; it still reprocesses everything each run unless the framework is incremental.)
3. Is the input naturally unbounded and event-shaped (clicks, sensor readings, database changes)? Then batch is an artificial slicing into days or hours; check whether the slicing itself causes trouble (events landing in the wrong bucket, jobs that must wait for the day to close).
4. Will you need to reprocess history with the same logic (new feature, bug fix, new model)? Then the design needs replay: a log with retention, or raw data in an object store, plus event-time semantics so reruns give the same answer.
5. Is the work a restructure of the whole dataset (new derived model, new schema, retrain)? Batch, or a replay of the log through the stream engine.
6. Can one machine do it? If the working set fits one machine, Unix tools or a local analytical engine are simpler than a cluster (see `batch-processing.md`).

## 3. Decision table

| Need | Use | Why |
|---|---|---|
| Reprocess large history, build a new derived view, restructure a model | Batch, or replay of the log through the stream engine | Reads the accumulated history in bulk; output can be swapped in when ready |
| Low delay propagation of changes into search index, cache, warehouse | Stream processing fed by CDC or an event log | Keeps derived data close to the source without dual writes |
| Caller needs authoritative answer now | Request/response | Only the read path gives it |
| Reference data needed while processing events | Subscribe to its changes and keep a local copy (stream-table join) | No network call per event; survives outage of the source |
| Large volumes, freshness not important (reconciliation, forecasting, model training, reports) | Batch | Cheapest per unit, retries are trivial |
| Pattern detection over event sequences, rolling metrics | Stream with windows | Needs results while events still arrive |
| Expensive per-message work, order irrelevant | Work queue (AMQP/JMS-style broker) | Per-message load balancing |

## 4. Reference data: lookup vs local copy

Example from DDIA 2e ch. 13: a purchase processor needs an exchange rate.

| | RPC to the rate service | Stream join with local copy |
|---|---|---|
| Latency | network round trip | local lookup, possibly in process |
| When the rate service is down | purchases fail | unaffected |
| Time dependence | yes (rate at call time) | yes (rate at event time, if you keep history) |

Choose the local copy when the data changes slowly compared with the lookup rate, the caller must keep working when the other service is down, and latency matters. Choose RPC when the authoritative current value is required at call time or the data is too large to replicate (the second clause is inferred in the notes). Keeping the copy fresh means subscribing to the source's change stream, not polling. Either way, a replay later can yield different output unless you keep rate history or write the applicable rate into the event; see `stream-processing-correctness.md` section on time-dependent joins.

## 5. Precompute vs compute on read

Write path: work done as data arrives. Read path: work done when someone asks. A derived dataset (index, cache, materialised view) is where they meet and shifts work from reads to writes. Search illustrates the range: no index means cheap writes and expensive reads; precomputing every possible query is impossible; an index is the middle; a cache of popular queries is the next step. The home-timeline fan-out (on write for ordinary accounts, on read for celebrities) is the same trade-off.

Rule (stated as inferred in the notes): precompute when reads are frequent, the read patterns are predictable and bounded, and the write amplification is affordable. Compute on read when the query space is large or unpredictable, or writes are very frequent relative to reads.

The write path can be extended to the end user with server-sent events or WebSockets so that clients subscribe to changes instead of polling. Expect the obstacle to be tooling: most databases, libraries and protocols assume request/response and few support "subscribe" (DDIA 2e ch. 13).

## 6. One engine for history and live data

The lambda architecture (a batch layer plus a separate speed layer whose outputs are merged) is described as having had many problems and fallen out of use (DDIA 2e ch. 13). The alternative, sometimes called kappa, uses one system for both reprocessing and live events, and needs three things:

1. Replay of historical events through the same engine: a replayable log, or a stream processor that can read from a file system or object store.
2. Exactly-once (effectively-once) semantics so a rerun gives the output of a fault-free run.
3. Event-time windowing, because processing time means nothing on replay.

Apache Beam running on Flink or Google Cloud Dataflow is the book's example. Choose a unified engine when you must reprocess history with the same logic as live processing; otherwise keep two simple things rather than one clever thing. Do not write the same business logic twice in two codebases and merge the outputs.

## 7. Reprocessing and migration

Stream processing reflects changes with low delay; batch reprocessing derives new views from accumulated history. Without reprocessing, schema evolution is limited to adding optional fields or record types; with it, the data can be restructured into a different model.

Gradual migration (the book's railway "dual gauge" analogy):
1. Keep the old view maintained.
2. Derive the new view from the same log or history, side by side.
3. Move a small share of readers to the new view; watch performance and bugs.
4. Ramp up; drop the old view when the share reaches 100 percent.

Every step is reversible, which is why this is less risky than an in-place schema migration of a mutable store. It needs the source (log or raw history) to be retained long enough to rebuild from.

## 8. Worked examples

A. "We need daily revenue by region." Freshness: next morning is fine. Volume: large. Output consumed by analysts. Pick batch against the warehouse or lakehouse, scheduled by a workflow scheduler; no stream machinery.

B. "Show a customer their order status within seconds, and keep the search index in sync." Two parts. Order status from the order database (request/response). Index sync: CDC from the orders database through a log into the indexer; consumers idempotent. Do not have the order handler write to the index.

C. "Fraud rules over the last 10 minutes of transactions per card." Stream with a sliding or hopping window on event time; state per card; a policy for late events (drop and count, or correct). Decision needed before any code: what happens to a transaction that arrives 20 minutes late?

D. "A model must be retrained weekly and predictions refreshed nightly." Batch end to end; orchestrate with a workflow scheduler; evaluate on a held-out set before promotion (see `pipeline-reliability.md`).

## 9. Warning signs

- A daily batch where users expect near-real-time behaviour.
- A stream job reading "now" from the wall clock for windows (spikes after a redeploy).
- A batch job calling the production OLTP database per record.
- Two codebases implementing the same transformation for batch and speed layers.
- A migration plan that rewrites the only copy of the data in place.
- Streaming adopted because it sounds modern for data that changes once a day.

## 10. Verify

- State the freshness requirement as a number (for example "99% of events reflected within 5 minutes") and show the mode chosen can meet it, with the measurement point named.
- Show the rebuild path: how would you regenerate this derived data from the source? If no path exists, the design is not finished.
- For a stream design, show the replay test: run the job on a window of recorded input twice, compare outputs, and confirm they are equal (needs event-time semantics).
- For a batch design, show a rerun on the same input produces the same output and that failed tasks leave no partial output visible.
