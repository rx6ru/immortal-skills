# Exactly-once, idempotency and end-to-end correctness

Read this when a pipeline or API retries, when a sink is not naturally idempotent (counters, emails, payments), when someone says "Kafka gives us exactly-once", or when you must enforce a constraint or a multi-shard operation without a distributed transaction.

Contents: 1 What exactly-once means; 2 Fault-tolerance techniques; 3 Idempotent sinks; 4 The idempotency key technique; 5 Why scope matters (end-to-end argument); 6 Multishard requests without atomic commit; 7 Timeliness vs integrity; 8 Integrity recipe; 9 Loosely interpreted constraints; 10 Coordination-avoiding systems; 11 Checklist; 12 Warning signs; 13 Verify.

Source: DDIA 2e ch. 12 (fault tolerance) and ch. 13 (correctness). Items marked (inferred) are labelled so in the notes. SQL and sketches are adaptations unless stated.

## 1. What exactly-once means

On failure you either drop the message (loss) or retry (risk of processing twice). Double processing is corruption: a double charge, a double count. "Exactly-once" means the final effect equals a fault-free run, which the book calls effectively-once and considers the better name. The best tool is an idempotent operation. Operations that are not naturally idempotent (increment) need extra metadata, such as the set of operation IDs that have updated a value, and fencing on failover.

## 2. Fault-tolerance techniques

Batch gets this free: inputs are immutable, each task writes its own output, and output becomes visible only on success. Streams cannot wait for completion.

| Technique | How | Where | Caveat |
|---|---|---|---|
| Microbatching | split the stream into small batches (about a second) and treat each as a mini batch job | Spark Streaming | small batches cost overhead, large ones add latency; implies tumbling windows by processing time; larger windows need state carry-over |
| Checkpointing | periodic snapshots of state, triggered by barriers in the stream; on restart use the latest checkpoint and discard output after it | Flink | no forced window size |
| Atomic commit | output messages, state changes, database writes and input offset advance happen all or nothing; transactions internal to the framework, amortised over many messages | Google Cloud Dataflow, VoltDB, Kafka transactions | not XA across heterogeneous systems |
| Idempotence | store the source message offset with the written value and skip if already applied | external writes | needs the same messages replayed in the same order (a log broker), deterministic processing, no concurrent updaters, and fencing on failover |

Key warning: microbatching and checkpointing give exactly-once only inside the framework. Once output leaves (a database write, an email, a publish to an external broker), a restarted task repeats the side effect. External effects need atomic commit or idempotence.

## 3. Idempotent sinks

Sink types and how to make each safe under at-least-once delivery:

| Sink | Technique (adaptation unless noted) |
|---|---|
| Relational table, upsert by natural key | `INSERT ... ON CONFLICT (key) DO UPDATE` with the source value; a rerun writes the same row. Replays can arrive out of order, so guard the update with a version or source offset (`... DO UPDATE SET v = excluded.v, ver = excluded.ver WHERE excluded.ver > t.ver`) or an old event overwrites a newer one |
| Relational counter | store applied event IDs or source offsets with the value and skip if already applied (the book's offset-with-value idea) |
| Key-value store | conditional put or compare-and-set; store the last applied offset with the value |
| Object store output | write to a path derived from the batch or run ID; rewriting the same path replaces identical content |
| Email, payment, other external call | pass an idempotency key to the provider if it supports one; otherwise record "sent" state before and after in your own store and accept a window of uncertainty; decide which error (duplicate or miss) is cheaper |
| Stream processor with state | keep a set of processed request IDs in state, derived from the log |

Conditions the offset technique needs: same messages in same order on replay, deterministic processing, no concurrent updaters of the same key, fencing tokens when a failed task may still be running (see leases and fencing in `arch-replication-and-consistency`).

## 4. The idempotency key technique

Problem: a client sends a non-idempotent request, loses the response, and retries. Each hop (TCP, web server, database transaction) sees a new attempt.

Steps:
1. The client generates a unique ID per logical operation before the first attempt (a UUID in a hidden form field, or a hash of the relevant fields). Every retry reuses it.
2. Pass the ID through every hop to the database.
3. The database has `UNIQUE(request_id)` on a requests table. In one transaction, insert the request row and apply the updates; a duplicate ID makes the insert fail and the transaction abort, so the effect happens once.

```sql
ALTER TABLE requests ADD UNIQUE (request_id);
BEGIN;
INSERT INTO requests(request_id, from_acct, to_acct, amount) VALUES (:id, :f, :t, :amt);
UPDATE accounts SET balance = balance + :amt WHERE account_id = :t;
UPDATE accounts SET balance = balance - :amt WHERE account_id = :f;
COMMIT;
```

Why a unique constraint and not "check, then insert" in application code: relational databases maintain uniqueness correctly even at weak isolation levels, while check-then-insert is vulnerable to write skew and phantoms unless transactions are serializable. In key-value stores use a conditional put; in a stream processor use the processed-ID set in state.

Bonus: the requests table is an event log usable for event sourcing or CDC. Balance updates need not be in the same transaction; a downstream consumer can derive them provided the event is processed exactly once, which the request ID enforces.

Worked failure the technique addresses: a client sends COMMIT and loses the connection. It cannot tell whether the transaction committed. Retrying a non-idempotent transfer (plus 11, minus 11) can move 22. The simple "bank transfer transaction" is therefore not correct as written. Two-phase commit does not fix it, because the browser-to-web-server hop is still unprotected: a user who resubmits a POST after a timeout creates a new request on the server and a new transaction in the database. Post/Redirect/Get hides the browser warning but does not help on timeout.

Details to get right (inferred):
- Reuse the key across retries; do not regenerate it per attempt.
- Keep stored keys at least as long as the longest plausible retry window.
- Return the original result on a duplicate rather than a bare error, so a retrying client learns the outcome.
- A key with different payload than the stored one is a client bug; reject it.

## 5. Why scope matters (end-to-end argument)

Principle (Saltzer, Reed and Clark, 1984, as cited in DDIA 2e): a function can be completely and correctly implemented only with the knowledge and help of the application at the endpoints; lower-level versions are performance enhancements. Applications:
- Duplicate suppression: TCP dedupes within one connection, a transaction within one connection, a stream processor within its framework. User resubmission needs an end-to-end ID.
- Integrity: Ethernet, TCP and TLS checksums miss bugs at the endpoints and on-disk corruption; use end-to-end checksums.
- Encryption: WiFi passwords and TLS do not protect against a compromised server; only end-to-end encryption and authentication do.

Low-level features are still worth having because they reduce the rate of higher-level faults. They are not sufficient. A serializable database does not make the application free of loss or corruption: it will not stop an application bug from writing wrong data or deleting data, which is one argument for immutable, append-only data (faulty code cannot destroy good data; immutability is not a cure-all). The book admits that the right reusable abstraction for high-level fault tolerance has not been found yet.

## 6. Multishard requests without atomic commit

Transfer with a fee: the payer, payee and fee accounts may live on different shards. Two-phase commit would impose a total order with other transactions and cut throughput. Alternative:

1. The client assigns a unique request ID and appends the request to the log shard of the source account. This single append is the atomic step.
2. The source account's stream processor holds the account state and the set of processed request IDs, all derived from the log. On an unseen ID it checks funds; if enough, it reserves the amount locally and emits events carrying the same request ID: outgoing payment (to its own log), incoming payment (destination log), incoming fee (fees log). If funds are insufficient it emits a declined event.
3. The outgoing event returns to the source processor, which recognises the reserved payment by ID, executes it, and ignores duplicates.
4. The destination and fee processors apply incoming events independently, deduplicating by request ID.

Requirements: each account's events processed strictly in log order with at-least-once delivery; deterministic processors. After a crash the same request is reprocessed, yields the same decision and the same outputs with the same IDs, and downstream dedupes. The user learns the result by subscribing to the source log and waiting for the outgoing-payment or declined event. Result: each request applied exactly once to payer and payee without an atomic commit protocol.

## 7. Timeliness vs integrity

"Consistency" mixes two properties:
- Timeliness: users observe up-to-date state. A violation is temporary staleness, fixed by waiting or retrying. Linearizability is a strong form; read-after-write is a weaker, useful one.
- Integrity: absence of corruption: no data loss, no contradictory or false data; derived data correctly reflects its source (an index missing records is not useful). A violation is permanent and needs detection and repair.

Timeliness violations give eventual consistency; integrity violations give perpetual inconsistency. Integrity usually matters far more: a credit card statement missing a recent transaction is normal; a statement whose sums do not add up is catastrophic. ACID bundles both, which hides the distinction. Event-based dataflow decouples them: no timeliness unless you build a consumer that waits for a result event, but integrity through effectively-once processing and idempotence without distributed transactions.

## 8. Integrity recipe

Four ingredients for integrity without atomic commit:
1. Represent the write as a single message, atomically appended (fits event sourcing).
2. Derive all other state updates from that message with deterministic derivation functions.
3. Pass a client-generated request ID through all levels for end-to-end dedupe.
4. Keep messages immutable and allow periodic reprocessing of derived data, so bugs can be recovered from.

## 9. Loosely interpreted constraints

Strict uniqueness-style constraints (balance not negative, stock available, no overlapping bookings) need consensus or funnelling through one shard. But many businesses already tolerate violations and have an apology process: oversold stock (reorder, discount, apologise; a forklift accident forces this workflow anyway), airline and hotel overbooking, bank overdraft fees with per-day withdrawal limits, settlement between organisations.

A compensating transaction is a later change that corrects a mistake (also what sagas do). The cost of an apology in money or reputation is a business decision.

Decision rule: is the cost of an occasional violation plus apology lower than the latency and availability cost of synchronous coordination on every write? If yes, write optimistically and check the constraint afterwards. Still validate before actions that are expensive or impossible to undo (shipping, cash payout, an email that cannot be unsent). If the violation is irreversible or catastrophic (money paid out, legal or safety consequences), require a synchronous check for that step only. These applications still need integrity (no lost reservation, no vanishing money), just not timeliness of enforcement.

## 10. Coordination-avoiding systems

Dataflow keeps integrity of derived data without atomic commit, linearizability or synchronous cross-shard coordination, and most applications tolerate loose constraints. So coordination-avoiding designs are possible, for example multi-leader replication across datacenters with asynchronous replication, each datacenter operating independently: weak timeliness, strong integrity. Serializable transactions remain useful at small scope while maintaining derived state; heterogeneous XA is not needed; add synchronous coordination only before unrecoverable operations. Coordination reduces apologies for inconsistency but lowers performance and availability, which increases apologies for outages. The sweet spot is a business judgement.

## 11. Checklist for an end-to-end design

1. Generate the idempotency key on the client at intent time; reuse it on retry.
2. Carry it through every hop (API, service, queue, database or events).
3. Enforce it with a uniqueness constraint (or the processed-ID set) at the final writer, atomic with the effect.
4. Make downstream consumers deterministic and dedupe on the key (at-least-once delivery plus idempotent processing is effectively-once).
5. Keep messages immutable; keep the ability to reprocess.
6. Add end-to-end integrity checks (checksums or hashes, reconciliation, periodic audits, restore tests); see `integrity-auditing-and-privacy.md`.
7. For constraints: shard by conflict key and process sequentially, or loosen and compensate.

## 12. Warning signs

- Retry logic on non-idempotent operations; browser or mobile retry without a request ID.
- "Idempotency" relying only on connection or transaction scope.
- Check-then-insert uniqueness in application code below serializable isolation.
- Non-idempotent sinks behind at-least-once delivery (counters, emails).
- "The framework is exactly-once" while the sink is an external system.
- Strict synchronous constraint enforced where the business already apologises (over-engineering), or a lax asynchronous check before an irreversible action (under-engineering).
- Reliance on "TCP, TLS or a serializable database guarantees it" as end-to-end correctness.

## 13. Verify

- Duplicate test: send the same request twice sequentially and twice concurrently; assert exactly one effect and that the second response reports the first outcome.
- Crash test: kill the process between commit and response; the retry must produce one effect. Do the same between a sink write and an offset commit.
- Key reuse: assert the client retry path reuses the key rather than minting a new one (unit test on the retry code).
- Retention: show stored keys outlive the maximum retry window.
- Replay test: replay the log into a scratch sink and compare with the live sink; no duplicates, no gaps.
- For constraints: show where each constraint is enforced (single shard, synchronous check, or compensating process with named owner) and the business's stated tolerance for the loose ones.
