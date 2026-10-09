# Correctness across systems without distributed transactions

Read this when an operation touches more than one system (database plus broker, two databases,
service plus search index) and you must decide whether to use a distributed transaction, how to make
retries safe, how to enforce a constraint such as uniqueness or "balance never negative", or how to
reason about stale versus corrupt data.

Contents: distributed transactions and why they disappoint; exactly-once as effectively-once;
idempotence recipes; the end-to-end argument; enforcing constraints; multi-shard requests without
atomic commit; timeliness versus integrity; apology-oriented design; keeping derived data in
step; trust but verify; verification. Sources: DDIA 2e ch. 8 (atomic commit, exactly-once) and ch.
13 second half. Isolation anomalies belong to `arch-transactions`; CDC, outbox and stream
processing mechanics to `arch-data-pipelines`.

## Atomic commit across nodes, and its price

Single node: write the data durably (write-ahead log), then append a commit record; the disk
finishing the commit record is the decision moment. Order matters: data first, commit record second.

Naively telling every node "commit" fails: some abort on a constraint, some requests are lost, some
nodes crash before the commit record is durable. A commit cannot be retracted once others saw the
data. Atomic commitment is needed: all commit or all abort.

### Two-phase commit (2PC)

Not two-phase locking (that is a serializability technique). 2PC is exposed to applications as XA
(Java JTA) and WS-AtomicTransaction.

1. Application obtains a globally unique transaction id from the coordinator and starts a
   single-node transaction on each participant under that id.
2. Phase 1: coordinator sends PREPARE. A participant that replies yes has persisted everything and
   checked constraints, and surrenders the right to abort. Point of no return one.
3. Coordinator decides commit only if all said yes and writes the decision to its own durable log.
   Point of no return two (the commit point).
4. Phase 2: coordinator sends COMMIT or ABORT, retrying forever. A crashed participant commits on
   recovery, since it voted yes.

Failure behaviour:

- After voting yes a participant is in doubt: it can neither commit nor abort alone and must wait
  for the coordinator. Timeouts do not help. On recovery the coordinator aborts transactions with no
  commit record. If the coordinator's log is lost, an administrator must intervene; losing only the
  tail may abort transactions that others committed, breaking atomicity.
- 2PC is blocking. Three-phase commit is nonblocking only under bounded network delay and pauses,
  which real systems do not guarantee, so it is mostly theoretical. The practical fix is a
  consensus-replicated coordinator.
- Cost: extra fsyncs and network round trips.

### Two kinds of distributed transaction

| | Database-internal | Heterogeneous (XA) |
|---|---|---|
| Participants | the same database software across shards and replicas (examples named: YugabyteDB, TiDB, FoundationDB, Spanner, VoltDB, CockroachDB, Kafka internally) | different technologies: databases from different vendors, message brokers |
| Protocol freedom | any protocol, with tailored optimisations | lowest common denominator (XA) |
| Reputation | work quite well | operational problems, poor performance, promise more than they deliver; many cloud services refuse to offer them |

### XA hazards

- The coordinator is usually a library in the application process with its log on the app server's
  local disk. If that host dies, prepared participants are stuck in doubt until it is restarted and
  the log re-read.
- Locks are held while in doubt (exclusive for writes, shared for reads under 2PL). A 20-minute
  coordinator outage means 20 minutes of locks; a lost log means locks until manual resolution, and
  other transactions touching those rows block.
- Orphaned in-doubt transactions occur in practice; even a database restart does not clear them. An
  administrator must inspect every participant and apply one outcome to all, usually during an
  outage. XA's "heuristic decision" escape hatch lets a participant decide alone, which is a
  euphemism for probably breaking atomicity.
- The coordinator and application are single points of failure; no cross-system deadlock detection;
  incompatible with serializable snapshot isolation (no cross-system conflict detection).

Database-internal systems avoid these by replicating the coordinator with automatic failover, having
coordinator and shards talk directly, replicating the shards, and coupling atomic commit with
distributed concurrency control.

Rule: use a database-internal distributed transaction if you need multi-shard atomicity; avoid XA
across heterogeneous systems unless you control every participant and accept the cost; otherwise use
the idempotence recipes below.

## Exactly-once means effectively-once

On failure you either drop the message (loss) or retry (risk of processing twice). Double
processing is corruption: double charge, double count. Exactly-once means the final effect equals a
fault-free run. The best tool is an idempotent operation. Operations that are not naturally
idempotent need metadata (the set of operation ids that already updated a value) and fencing on
failover.

Exactly-once between broker and database by atomic commit: acknowledge the message iff the database
transaction committed; both abort together and the broker redelivers. Every side effect must
participate in the protocol; an email server without 2PC support may send twice.

### Recipe: idempotent consumer with a processed-ids table (needs only a local transaction)

1. Every message carries a unique id. The database has a `processed_message_ids` table with a UNIQUE
   constraint.
2. On receipt begin a transaction. If the id exists, acknowledge and drop.
3. Otherwise insert the id and do the processing writes in the same transaction; commit.
4. After commit, acknowledge to the broker.
5. After acknowledgement, delete the id in a separate transaction (cleanup).

Crash analysis: before commit, the transaction aborts and the broker redelivers; after commit but
before ack, redelivery sees the id and drops; after ack but before cleanup, a stale id wastes space
only; a duplicate processed concurrently is stopped by the unique constraint. Limitation (inferred):
side effects outside the database (emails, external calls) are not covered unless they are
themselves idempotent or keyed by the message id.

### Recipe: client-generated request id (end-to-end idempotency key)

Duplicate suppression works only within its scope. TCP dedupes within one connection. A database
transaction is tied to a connection: if the client sent COMMIT and lost the connection it does not
know the outcome, and a blind retry of a non-idempotent transfer can move the money twice. 2PC
changes the connection mapping but not the browser-to-server hop: a user on a weak connection
resubmits a form and the server sees a new request and a new transaction.

1. The client generates a unique id per logical operation before the first attempt (a UUID in a
   hidden field, or a hash of the relevant form fields); every retry reuses it.
2. Pass the id through every hop to the database.
3. Put a UNIQUE constraint on `request_id` in a requests table; in one transaction insert the
   request row and apply the updates. A duplicate fails the insert and aborts the transaction.

```sql
ALTER TABLE requests ADD UNIQUE (request_id);
BEGIN;
INSERT INTO requests(request_id, from_acct, to_acct, amount) VALUES (:id, :from, :to, :amt);
UPDATE accounts SET balance = balance + :amt WHERE account_id = :to;
UPDATE accounts SET balance = balance - :amt WHERE account_id = :from;
COMMIT;
```

Why a unique constraint and not check-then-insert in application code: databases maintain
uniqueness correctly even at weak isolation, while check-then-insert is exposed to write skew and
phantoms unless the isolation is serializable. In key-value stores use a conditional put; in a
stream processor use a state store of seen ids. The requests table doubles as an event log for
event sourcing or CDC, and the balance updates can be derived downstream, provided the event is
processed exactly once.

Retry checklist (DDIA ch. 8): a retry after a lost acknowledgement duplicates the transaction
without an idempotency key; retries under overload make it worse, so cap them and back off; retry
only transient errors (deadlock, serialization failure, brief network loss, failover), never
permanent ones (constraint violation); side effects outside the database happen even when the
transaction aborts; a client that crashes while retrying loses its data.

## The end-to-end argument

A function can be completely and correctly implemented only with the knowledge and help of the
application at the endpoints; lower-level versions are performance enhancements. Applies to
duplicate suppression (TCP, a database transaction and a stream processor's exactly-once each cover
one segment), integrity checking (link and TLS checksums miss bugs at the endpoints and on-disk
corruption, so use end-to-end checksums), and encryption (TLS does not protect against a
compromised server). Lower layers still reduce the probability of faults; they do not make the
application safe. A serializable database does not remove the need for the application's own
end-to-end measures.

## Enforcing constraints (uniqueness, non-negative balance, stock, no overlapping bookings)

- Uniqueness in a distributed setting needs consensus: someone must decide which conflicting
  operation wins. Typically one leader decides; scale out by sharding on the value that must be
  unique (request id, hash of username). Asynchronous multi-leader replication cannot enforce strict
  uniqueness; rejecting a violation immediately requires synchronous coordination.
- Uniqueness through a log (username claim): append each claim to the log shard chosen by
  hash(username); one single-threaded stream processor per shard keeps a local set of taken names,
  marks a free name taken and emits success, or emits a rejection; the client watches the output
  stream for the outcome matching its request. General principle: route every write that may
  conflict to the same shard and process sequentially; the conflict definition and validation are
  arbitrary.

## Multi-shard request without atomic commit (transfer with a fee)

Payer, payee and fee accounts may live on different shards; 2PC would impose a global order and cut
throughput.

1. The client assigns a unique request id and appends the request to the log shard of the source
   account.
2. The source-account processor (which holds the account state and the set of processed request ids,
   all derived from its log) checks funds on an unseen id; if enough, it reserves locally and emits
   events carrying the same request id: an outgoing payment (back to its own log), an incoming
   payment (destination log), an incoming fee (fees log).
3. The outgoing event returns to the source processor, which recognises the reserved payment by id,
   executes it and ignores duplicates.
4. Destination and fee processors apply incoming events independently, deduplicating by id.

Requirements: per-account events processed in log order with at-least-once delivery; deterministic
processors. Atomicity comes from the single atomic append of the first request event; downstream
events eventually all appear, possibly duplicated, and are deduplicated. The user learns the result
by subscribing to the source log and waiting for the outgoing-payment or declined event.

## Timeliness versus integrity

"Consistency" mixes two things.

| | Timeliness | Integrity |
|---|---|---|
| Meaning | users see up-to-date state | no corruption: no lost data, no contradictory or false data; derived data correctly reflects its source |
| Violation | temporary staleness; fixed by waiting or retrying | permanent; needs detection and repair |
| Name for the failure | eventual consistency | perpetual inconsistency |

Integrity usually matters far more: a statement that omits yesterday's transaction is normal; one
whose sums do not add up, or a charge never paid to the merchant, is catastrophic. ACID bundles both.
Event-based dataflow separates them: no timeliness unless you build a consumer that waits for the
result event, but integrity is obtained without distributed transactions.

Recipe for integrity without atomic commit:

1. Represent each write as a single message, appended atomically (fits event sourcing).
2. Derive every other state update from that message with deterministic derivation functions.
3. Pass a client-generated request id through all levels for end-to-end deduplication.
4. Keep messages immutable and allow periodic reprocessing of derived data, so bugs can be
   recovered from.

## Apology-oriented design (loosely interpreted constraints)

Strict constraints cost consensus. Many businesses already tolerate violation and repair it:
overselling stock (reorder, apologise, discount), overbooking flights and hotels, bank overdraft
fees with per-day limits, settlement between organisations. A compensating transaction is a later
change that corrects a mistake. The cost of an apology (money, reputation) is a business decision.

Decision rule: is the cost of an occasional violation plus the apology lower than the latency and
availability cost of synchronous coordination on every write? If yes, write optimistically and check
afterwards. If the violation is irreversible or catastrophic (money paid out, shipping, legal or
safety), coordinate synchronously for that step only. These applications still need integrity (no
lost reservation, no vanishing money). Coordination reduces apologies for inconsistency but raises
apologies for outages; there is no zero, only a sweet spot.

## Keeping derived data in step

Principle: one place decides the order of writes; everything else derives from it by processing in
that order. Dual writes (application writes to the database and the index) race and diverge
permanently; partial failure leaves them inconsistent.

| Situation | Pick |
|---|---|
| An existing relational database is the truth; a search index, cache or warehouse must follow | Change data capture from its log, with idempotent consumers |
| Greenfield, audit and rebuildability matter, domain is event-shaped | Event sourcing: immutable events, deterministic derivation |
| Atomic "state change plus event", no CDC available | Insert the event row in the same local transaction and relay it (outbox-like; the mapping to the outbox name is inferred, the notes do not use it) |
| Cross-system atomic visibility mandatory and you control all participants | Distributed transaction, with eyes open |
| Application code writes two stores separately | Avoid |

Always: consumers idempotent, per-key ordering preserved, derived views rebuildable from the log or a
snapshot. Limits of a single total order: log sharding, multi-region leaders, microservices with
separate state, and offline clients each leave some events unordered. Cross-key causality ("unfriend,
then post") has no simple answer; options are logical timestamps or logging the state the user saw
and referencing it from later events. Unbundle a database into several systems only when no single
product meets the requirements; every extra component costs operations.

## Trust, but verify

Assumed guarantees are probabilities at scale: memory, disk and network corruption occur and
software has had bugs (databases that failed to maintain uniqueness; serializable modes with
anomalies). Audit by reading data back and checking it; restore backups periodically. Event sourcing
helps auditing because the same log and code version should give the same state; compare by
re-running derivations or hashing. Include as many stages as possible in each integrity check.
Heavier tools (signed logs, Merkle trees, blockchains) are not mainstream.

## Verify

- Send the same request twice, and concurrently, and assert one effect. Kill the process between
  commit and response and retry; assert one effect. Assert the key is reused across client retries
  and not regenerated. Check retention of stored ids exceeds the longest retry window (inferred).
- Redeliver every message twice in a consumer test and assert unchanged state.
- Search the code for a handler that writes to a database and another system in one request, and for
  check-then-insert uniqueness at non-serializable isolation.
- Fault-inject a coordinator crash in any 2PC/XA setup and observe in-doubt locks and recovery time.
- Run a reconciliation job that compares derived data with its source and alerts on drift; rehearse
  a restore from backup.
- For each constraint, record whether it is enforced synchronously, shard-sequentially or loosely
  with compensation, and who pays for the apology.
