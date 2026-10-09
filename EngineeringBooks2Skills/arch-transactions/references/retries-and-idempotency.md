# Retries and idempotency

Source: DDIA 2e ch. 8 (handling errors and aborts; exactly-once via idempotence; exactly-once with atomic commit). Code is adaptation.

## Contents
1. Why abort-and-retry is the model
2. The five retry caveats, as review items
3. A retry wrapper that respects them
4. Exactly-once processing with a deduplication table
5. Crash analysis of the recipe
6. What the recipe does not cover
7. Verify

## 1. Why abort-and-retry is the model

A transaction that cannot guarantee atomicity, isolation or durability is abandoned rather than left half-done; that makes the abort safe to retry. Serializable isolation and lost-update detection add another class of aborts (serialization failure, deadlock) that are expected in normal operation, not exceptional. Leaderless-replication stores are best effort and do not undo what they already did, so the application recovers there.

Common failure: ORMs such as ActiveRecord and Django (as of the book) usually do not retry aborted transactions. The exception bubbles to the user and the input is thrown away, which wastes the point of having rollback.

## 2. The five retry caveats

Each is a review item.

1. Commit succeeded but the acknowledgement was lost (client timeout, connection drop). A blind retry runs the transaction twice. Needs application-level deduplication (an idempotency key or message ID, section 4).
2. Overload or high contention. Retries add load to an overloaded system. Cap the number of retries, use exponential backoff, and treat overload errors differently from conflicts.
3. Retry only transient errors: deadlock, serialization or isolation failure, brief network loss, failover. Never retry permanent errors such as a constraint violation; it will fail again.
4. Side effects outside the database (an email, a payment call) happen even if the transaction aborts, and happen again on retry. Either make them idempotent, move them after commit (outbox or message handled idempotently), or put all parties under one atomic commit protocol (`distributed-transactions-2pc.md`).
5. A client crash while retrying loses the data it was trying to write. If the write matters, persist the intent (a queue or a request record) before the retry loop.

## 3. A retry wrapper that respects them

Adaptation. The wrapper below was run (Node 22 with type stripping) against stub helpers: it retried two serialization failures then succeeded, did not retry a constraint violation (called once), and stopped at the cap. `db`, `Tx`, `sleep` and `jitteredBackoff` stand for your driver and utilities; the two error classifiers are yours to write.

```ts
declare const db: { transaction<T>(o: { isolation: string }, work: (tx: Tx) => Promise<T>): Promise<T> };
declare function sleep(ms: number): Promise<void>;
declare function jitteredBackoff(attempt: number): number;       // ms, e.g. random(0, min(cap, base * 2 ** attempt))
declare function isSerializationFailure(e: unknown): boolean;
declare function isDeadlock(e: unknown): boolean;

async function runTx<T>(work: (tx: Tx) => Promise<T>, maxAttempts = 5): Promise<T> {
  for (let attempt = 1; ; attempt++) {
    try {
      return await db.transaction({ isolation: "serializable" }, work); // whole body re-runs
    } catch (e) {
      const transient = isSerializationFailure(e) || isDeadlock(e); // not constraint errors
      if (!transient || attempt >= maxAttempts) throw e;
      await sleep(jitteredBackoff(attempt));   // backoff + jitter
    }
  }
}
```

Rules the wrapper encodes:
- The work function must re-read its inputs on each attempt; the premise changed, which is why it aborted.
- The work function must not do irreversible side effects inside the transaction body.
- Classify errors by the engine's error codes, not by message text (adaptation: PostgreSQL SQLSTATE `40001` serialization failure and `40P01` deadlock detected; MySQL error 1213 deadlock; `23505` unique violation is permanent). The failure can surface at COMMIT, so the `await` must cover the commit, as `db.transaction` does here.
- A failed commit whose outcome is unknown (connection dropped during COMMIT) is not a transient conflict; do not retry it blindly, use the idempotency key (caveat 1).
- Surface a clear error to the caller when attempts run out.
- If the caller itself may time out and retry the whole request, the request needs an idempotency key (caveat 1).

## 4. Exactly-once processing with a deduplication table

Goal: a consumer processes each message effectively once, using only a local database transaction (no distributed transaction).

1. Every message carries a unique ID. The database has a `processed_message_ids` table with a UNIQUE constraint on the ID.
2. On receipt, begin a database transaction. If the ID is already present, acknowledge the message to the broker and drop it.
3. Otherwise insert the ID and perform the processing writes in the same transaction; commit.
4. After commit, acknowledge to the broker.
5. After the acknowledgement, delete the ID in a separate transaction (cleanup).

Sketch (SQL, adaptation):

```sql
BEGIN;
INSERT INTO processed_message_ids (id) VALUES (:msg_id);   -- UNIQUE violation => duplicate, abort and ack
UPDATE accounts SET balance = balance + :amount WHERE id = :acct;
COMMIT;
-- then ack to the broker; later: DELETE FROM processed_message_ids WHERE id = :msg_id;
```

Why the insert and the work must share one transaction: the unique-ID row and the effects then commit or abort together.

PostgreSQL alternative (adaptation): `INSERT ... ON CONFLICT (id) DO NOTHING` and check the affected-row count; 0 rows means duplicate, so ack and stop without raising an error that aborts the transaction. At read committed a concurrent duplicate waits for the first transaction to finish, then sees the conflict; at higher levels the engine may raise a serialization failure instead, which the retry wrapper turns into a duplicate on the next attempt (verify on your version).

Variant (book): if you do have atomic commit across broker and database, acknowledge the message only if the database transaction committed, and abort both together so the broker redelivers. That requires every side effect to take part in the commit protocol; an email server that does not will send the email again on retry. Internal distributed transactions of a sharded database can still help scale the recipe (ID on one shard, data on others, atomic across shards). Kafka Streams uses a similar approach (see `arch-data-pipelines`).

## 5. Crash analysis of the recipe

| Crash point | What happens |
|---|---|
| before commit | transaction aborts, broker redelivers, processing runs again from scratch |
| after commit, before ack | broker redelivers, ID found, message dropped and acknowledged |
| after ack, before cleanup | stale ID row remains; wastes space only |
| retry while the first attempt has not yet aborted (concurrent duplicates) | the UNIQUE constraint stops the second insert, so effects are not applied twice |

## 6. What the recipe does not cover

(inferred by the notes) Side effects outside the database are not covered unless they are idempotent themselves or keyed by the message ID: pass the ID as the idempotency key to the external API, or record the intent in the same transaction and let a separate sender deliver it at least once with an idempotent receiver.

The cleanup in step 5 means the dedup window is bounded by broker redelivery behaviour: a redelivery arriving after cleanup would be processed again. Choose the cleanup delay to exceed the longest redelivery or retry window you have (adaptation).

## 7. Verify

- Fault-inject each crash point in the table above (kill the consumer between steps) and assert the effect happened exactly once.
- Send the same message twice concurrently; assert one effect and one unique-violation.
- Make the wrapper's transaction fail with a serialization error twice, then succeed; assert the body re-read its inputs and the effect applied once.
- Make a constraint violation occur; assert it is not retried.
- Simulate a lost commit acknowledgement (commit, then drop the connection before the client reads the reply); assert the retry with the same key does not duplicate.
- Show the retry cap and backoff configuration to the user.
