# Keeping derived data in sync

Read this when a second store (search index, cache, warehouse, denormalised copy, read model, notification system) must follow a primary store, or when you see an application writing to two systems in one handler. This is the decision guide with failure modes.

Contents: 1 System of record and derived data; 2 The options and their failure modes; 3 Decision table; 4 Change data capture in practice; 5 Outbox; 6 Event sourcing vs CDC; 7 Immutability, state and views; 8 Limits of a single order; 9 Unbundling vs integrated databases; 10 Warning signs; 11 Verify.

Sources: DDIA 2e ch. 12 (sync options, CDC, event sourcing), ch. 13 (total order, limits, unbundling). Items marked (inferred) are labelled so in the notes.

## 1. System of record and derived data

For any data held in more than one place, state which store is written first (the system of record) and which are derived from it. Funnel all input through one system that decides a total order of writes and derive everything else by processing writes in that order. This is state machine replication: the same deterministic events in the same order give the same state. Whether the order comes from CDC or from an event-sourcing log matters less than having one.

Derived updates driven by a log can usually be deterministic and idempotent, so recovery from faults is replay or retry. A derived store that nothing else writes to is entirely rebuildable. If you cannot rebuild it, it is not derived, and it needs its own backup and integrity story.

## 2. The options and their failure modes

| Approach | How it stays correct | Failure modes | Verdict |
|---|---|---|---|
| Periodic full dump (batch ETL) | rebuild from scratch | stale between runs | fine when staleness of hours is acceptable |
| Dual writes (app writes DB, then index, then cache) | nothing | (1) Race: two clients write A and B; the DB applies A then B, the index applies B then A; the stores disagree permanently and silently. (2) Partial failure: one write succeeds, the other fails. Fixing needs atomic commit, which is expensive. Root cause: no single leader defines the order | avoid for data that must agree |
| Distributed transaction (2PC or XA) across heterogeneous systems | atomic commit | poor fault tolerance and performance; any participant failing aborts the whole; no standard protocol across vendors; usually one datacenter | only if you control all participants and need immediate atomic visibility |
| CDC | the source database is the leader; derived stores are followers fed by its committed change stream | asynchronous lag; schema coupling; initial snapshot needed | default when a database already is the truth |
| Event sourcing | the app writes immutable events; state and views are derived | big redesign; no log compaction; schema evolution of events | when audit, provenance and rebuildability are central and you can design for it |
| Outbox | write the business row and an outbox row in one local transaction; CDC or a relay publishes the outbox | extra writes; maintaining outbox schema mapping | when you need an atomic "state change + event" and want a stable public event schema |

The book's stance: since no widely adopted good distributed transaction protocol exists, log-based derived data is the most promising approach. Do not stop at "eventual consistency is inevitable"; layer read-your-writes style guarantees on top where users need them, for example by letting a client wait for a result event.

Why a log beats a transaction here: asynchronous derivation contains faults. A slow or failed consumer lags and catches up while producers and other consumers continue. A distributed transaction spreads failure instead, because one participant failing aborts everything.

What the log must provide for this to hold: a stable order of state changes (every view derived from it processes events in the same order) and fault tolerance (one lost message leaves the derived dataset permanently out of sync). Both are demanding, but the book judges them cheaper and more robust to operate than distributed transactions.

## 3. Decision table

| Situation | Pick | Why |
|---|---|---|
| Existing relational or document database is the truth; need search, cache, warehouse in sync | CDC from the database log, idempotent consumers | Order decided by the database; no application change; derived store fully derived |
| Greenfield; audit, provenance and rebuild matter; domain naturally event-shaped | Event sourcing with deterministic derivation | One atomic write; replay; recovery from bugs by reprocessing |
| Need atomic state change plus event, you control the database, no CDC available | Outbox: insert the event row in the same local transaction and relay it (the outbox pattern is named in ch. 12; the "no CDC available" framing is inferred) | One local commit, no dual write |
| CDC consumers include other production services | Outbox table with a stable schema, or a data contract | Raw CDC exposes internal schema as a public API |
| Cross-system atomic visibility mandatory and you control every participant | 2PC, accepted with the costs | Documented trade-off |
| Application code writes two stores separately | Do not | Permanent divergence on races and partial failures |
| Plain queue with no replay available | Be aware you lose rebuild-from-log; add a snapshot path | The properties above assume a replayable ordered log |

Always: consumers idempotent or deduplicating by ID, per-key order preserved, and a way to rebuild the derived view from the log or a snapshot.

## 4. Change data capture in practice

Definition: observe all writes to a database and extract them as a stream that other systems apply in order. Implementations read the logical (row-based) replication log: Debezium (MySQL, PostgreSQL, Oracle, SQL Server, Db2, Cassandra and others), Kafka Connect connectors, Maxwell, GoldenGate, pgcapture, cloud services. Many databases now expose change streams natively. Cassandra exposes raw per-node commit logs and the consumer must merge them.

Properties and obligations:
- Usually asynchronous, so replication lag applies: derived views can be stale and read-your-writes can fail. A slow CDC consumer does not slow the source.
- Transport through an ordered log avoids the reordering of an unordered queue.
- Initial snapshot: the log is usually truncated, so a new derived system needs a consistent snapshot tied to a known log offset, then applies changes after that offset. Debezium's incremental snapshots use the DBLog watermark algorithm; other tools need manual procedure.
- Log compaction: keep only the latest record per key; a null value is a tombstone for deletion. Storage tracks the size of the current database, not the number of writes, and a new consumer can read the compacted topic from offset 0 for a full copy without snapshotting the source. Requires each change to carry the primary key and the whole new row version.
- Schema warning: CDC exposes the source database's internal schema as a public API. Dropping or renaming a column can break downstream production consumers. Mitigate with data contracts or the outbox pattern.

## 5. Outbox

Write the business change and an outbox row in a single transaction on the same database; a relay or CDC publishes outbox rows to the log. It looks like a dual write, but both writes are in one database, so they are atomic. Costs: maintaining the mapping from internal schema to outbox schema, and extra write volume. The chapter's idea of inserting a request row in the same transaction as the update (see `exactly-once-and-idempotency.md`) is a close relative.

Adaptation, a minimal shape in SQL:

```sql
BEGIN;
UPDATE orders SET status = 'paid' WHERE id = :id;
INSERT INTO outbox(event_id, aggregate_id, type, payload)
VALUES (:event_id, :id, 'OrderPaid', :json);
COMMIT;
-- a relay (or CDC on the outbox table) publishes rows in commit order;
-- consumers dedupe on event_id
```

The relay is at-least-once, so consumers must tolerate duplicates. Adaptation: if the relay polls the table by an increasing ID instead of reading the database's change log, a transaction with a lower ID can commit after a higher one, and the relay may skip it or publish out of commit order. Prefer CDC on the outbox table, or poll with a cursor that cannot pass uncommitted rows, when per-aggregate order matters.

## 6. Event sourcing vs CDC

| | CDC | Event sourcing |
|---|---|---|
| Level | low-level row after-images from an application that mutates and deletes freely | application-level immutable events expressing intent |
| Adoption | add to an existing database; the app may not know | redesign the application |
| Order | extracted from the replication log | event log order |
| Log compaction | works (later record for a key replaces earlier) | usually impossible; later events do not override earlier ones; need full history; snapshots only optimise reads and recovery |

Choose event sourcing only if you will keep the full history and do not plan on compaction. Choose CDC for existing systems.

## 7. Immutability, state and views

- State is the integral of the event stream; the change stream is the derivative of state. A mutable database and an append-only log are two views of one thing; the database is a cache of the log's tail.
- Advantages of immutable events: audit (mistakes corrected by a compensating entry, as in accounting); easier diagnosis and recovery from bad-code writes; they keep information that state loses (an item added to a cart and removed shows intent).
- Derive many views from one log. To add a feature, build a new read-optimised view alongside the old one, switch readers, then retire the old one. Normalisation versus denormalisation matters less: write in event or normalised form, denormalise in read views kept consistent by the translation pipeline.
- Concurrency: asynchronous views mean a user may not see their own write (use read-your-writes techniques); synchronous view update needs a distributed transaction or waiting, usually impractical. If each event is a self-contained description of a user action, one append is atomic. If log and state are sharded identically, a single-threaded consumer per shard needs no locks; events touching several shards need extra work (see `exactly-once-and-idempotency.md`, multishard section).
- Limits: high-churn small datasets make history huge and compaction critical. Legal deletion needs real removal; see `integrity-auditing-and-privacy.md`.

## 8. Limits of a single order

Total order broadcast is consensus, and most algorithms assume one node's throughput suffices. The single-log idea breaks when:
1. Throughput exceeds one leader: sharding the log leaves order across shards undefined.
2. Multi-region with a leader per datacenter: events from two datacenters have no defined order.
3. Microservices each with durable state: events from different services are unordered.
4. Clients update state optimistically or offline: clients and servers see events in different orders.

Concurrent events may be ordered arbitrarily. Multiple updates to one object are handled by routing by object ID to one shard. The hard case is a causal dependency across keys or systems. Example: a user removes a friend and then posts a message to friends; a notification service that joins messages with the friend list may process the message first and notify the removed friend. The book says there is no simple answer. Starting points:
- Logical timestamps give order without coordination, but recipients must still handle out-of-order delivery and carry the metadata.
- Log an event recording the state the user saw before deciding, give it a unique ID, and let later events reference it.
- Conflict-resolution algorithms fix out-of-order events for state, but not for external side effects such as sending a notification.

Review step (inferred): for each cross-system flow with a rule "A must precede B", name the log or shard that orders A and B. If there is none, this problem is present.

## 9. Unbundling vs integrated databases

Two ways to compose storage technologies:

| | Federated database (unify reads) | Unbundled database (unify writes) |
|---|---|---|
| Idea | one query interface over many engines (foreign data wrappers, Trino) | propagate every change to all derived systems via CDC or event logs |
| Hard part | mapping data models; manageable | keeping writes in sync across systems, including through faults |

Both are valid. Rule from the book: if one technology satisfies all requirements, use it; unbundle only when no single product does. Each extra component adds a learning curve, configuration and quirks, and an integrated product can give better and more predictable performance for the workloads it was designed for. Unbundling is about breadth (covering more workloads), not depth. Building for scale you do not need is premature optimisation. Typical justified case: a transactional database plus a specialised search index (the database's built-in full-text search may suffice for simple needs; search indexes are poor systems of record).

CREATE INDEX is the same as bootstrapping CDC: snapshot, build, then process the backlog of writes since the snapshot, then keep up. A new derived system is a reprocessing of existing data.

## 10. Warning signs

- A request handler writes to a database and to another store.
- Downstream services consume raw CDC of an internal table schema.
- Event sourcing planned together with log compaction.
- Derived data with no rebuild path and no verification job.
- Unbundling by default: many moving parts where one database would do.
- A cross-system rule "A before B" with no ordering mechanism.

## 11. Verify

- Grep for handlers that write to two stores in one request path (database client plus search, cache or queue client). Each hit needs an explanation: outbox, CDC, or accepted divergence with a repair job.
- Race test: issue two concurrent updates to the same key and show the derived store ends equal to the source. Run it repeatedly.
- Rebuild test: drop the derived store, rebuild from snapshot plus log (or compacted topic), and compare with the live version (reconciliation counts and checksums).
- Consumer idempotence: deliver each event twice and show the derived state is unchanged.
- Schema change drill: rename a column in a staging source and show downstream consumers either keep working (outbox or contract) or are caught by a contract test before release.
- Show the lag metric for the CDC connector and the alert on it.
