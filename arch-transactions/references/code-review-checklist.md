# Code review checklist: transaction and concurrency bugs in application code

Source: DDIA 2e ch. 8 section 12 and the anomaly sections; items and tests marked (inferred) are the notes' synthesis, and the SQL/test code is adaptation. The book points to Kleppmann's Hermitage project for testing what a database does at each level.

## Contents
1. How to scan a repository
2. Smell catalogue (pattern, why it breaks, fix)
3. Interleaving tests, per anomaly
4. A test harness sketch
5. Review questions with observable answers
6. Evidence to show the user

## 1. How to scan a repository

1. Find the data access layer and the transaction boundary: search for `BEGIN`, `transaction`, `@Transactional`, `atomic()`, `with_transaction`, `db.tx`, `session.begin`, `BatchWrite`.
2. Find the configured isolation level and engine: connection string, pool or session settings, ORM config, migration files, docker-compose or IaC for the database.
3. Find read-then-write sequences: a SELECT/`find`/`get` whose result feeds a later UPDATE/INSERT/`save`/`put` in the same function or request.
4. Find retry code and ORM transaction wrappers: do they retry serialization failures and deadlocks?
5. Find writes to two systems in one function (database plus queue, cache, email, another service).
6. Rank by invariant: money, inventory, uniqueness, quotas, permissions and bookings first.

## 2. Smell catalogue

Entry: pattern; why it breaks; fix (see the referenced files for the full ladder).

**S1. Read, compute in application, write back (lost update).**
- Pattern: `x = get(id); x.count += 1; save(x)`; `SELECT balance` then `UPDATE ... SET balance = :computed`.
- Breaks: two requests read the same value; the later write overwrites the earlier one. ORMs generate this by default.
- Fix: `UPDATE t SET count = count + 1 WHERE id = :id`; or a version column with `WHERE version = :seen` and a check of rows affected; or `FOR UPDATE`; or an engine/level that detects lost updates plus retry.

**S2. Check then act on rows (write skew).**
- Pattern: `if (count(on_call) >= 2) { set(me, off) }`; `if (!exists(booking overlapping)) insert(booking)`; `if (balance(sum of items) >= amount) insert(spend)`.
- Breaks: both transactions pass the check on the same snapshot; each writes a different row; invariant broken. Snapshot isolation does not catch it.
- Fix: serializable plus retry; or lock the decision's rows (`FOR UPDATE`) if they exist; or a constraint; or materialized conflicts.

**S3. Check for absence then insert (phantom).**
- Pattern: `if (!findByName(name)) insert(user)`.
- Breaks: nothing to lock; both inserts proceed.
- Fix: a UNIQUE constraint and handle the violation; or serializable.

**S4. `FOR UPDATE` on an empty result.**
- Pattern: `SELECT ... WHERE room = 123 AND overlaps(...) FOR UPDATE` as the guard of an insert.
- Breaks: no rows match, so no lock is taken.
- Fix: lock a row that exists for the resource (the slot rows, or the parent room row), or serializable.

**S5. Locks taken in inconsistent order or in only some code paths.**
- Pattern: explicit `FOR UPDATE` in one handler but a bare UPDATE in another handler touching the same rows; two handlers locking A then B vs B then A.
- Breaks: the unprotected path still races; opposite order deadlocks (the database aborts one, and retry is needed).
- Fix: centralize the access in one function; order lock acquisition consistently; ensure retry exists.

**S6. No retry on serialization failure or deadlock.**
- Pattern: transaction wrapper that rethrows everything.
- Breaks: at serializable, SSI and 2PL abort by design; users see errors for normal contention.
- Fix: retry wrapper (`retries-and-idempotency.md` section 3).

**S7. Retry without idempotency key, cap or backoff.**
- Pattern: `while (true) { try { commit } catch { continue } }`; client retries a POST that charges money.
- Breaks: duplicate effect if the commit succeeded and the ack was lost; retry storms under overload; retries of permanent errors.
- Fix: idempotency key stored under a unique constraint in the same transaction; capped exponential backoff with jitter; classify transient errors.

**S8. Transaction spans a user interaction or several HTTP requests.**
- Pattern: transaction opened in a request handler, closed in a later one; "hold the row while the user fills the form".
- Breaks: locks held or versions pinned for human time; blocks writers under 2PL, bloats storage under MVCC, stalls everything under serial execution.
- Fix: one transaction per request; for multi-step flows use optimistic versioning or reservation rows with expiry (adaptation).

**S9. Side effect inside the transaction.**
- Pattern: send email or call a payment API between the database writes.
- Breaks: side effect happens even if the transaction aborts, and again on each retry.
- Fix: do it after commit via an outbox or idempotent message; or make the external call idempotent with a key.

**S10. Two-system write with no mechanism (dual write).**
- Pattern: `db.save(x); queue.publish(x)` or `db.save(x); cache.set(x)`.
- Breaks: a crash between them leaves them inconsistent; there is no atomicity across them.
- Fix: depends on the case; see `distributed-transactions-2pc.md` and `arch-data-pipelines` (outbox, change data capture).

**S11. Using a level name as if it were portable.**
- Pattern: code or docs say "we use REPEATABLE READ so we are safe from lost updates" and the engine is MySQL/InnoDB; "SERIALIZABLE" on Oracle.
- Breaks: the name does not mean the same thing across vendors.
- Fix: look up the engine's behaviour, and prove the property with the tests below.

**S12. Whole-table scans in the OLTP path at 2PL, or long transactions under MVCC/SSI.**
- Pattern: reports and backups run in the same database and transaction mode as writes.
- Breaks: 2PL: writers blocked for the duration. MVCC: old versions pinned (bloat). SSI: long read-write transactions abort often.
- Fix: run reporting as read-only snapshot transactions or on a replica; shorten read-write transactions.

**S13. Multi-object consistency assumed from a NoSQL multi-put or from separate single-object writes.**
- Pattern: three `put` calls expected to be atomic.
- Breaks: some succeed and some fail; no isolation.
- Fix: use a store with real multi-object transactions, or restructure so the invariant lives in one object, or accept and design for partial failure.

**S14. Quorum or timestamp-based store assumed to be linearizable.**
- Pattern: "we read with quorum so it is strongly consistent"; last-write-wins with wall-clock timestamps used to arbitrate uniqueness.
- Breaks: leaderless quorum reads can still go backwards; clock skew misorders writes.
- Fix: use a consensus-backed store or a single leader for hard uniqueness and lock decisions; see `acid-base-and-linearizability.md` section 7.

**S15. XA or 2PC across heterogeneous systems introduced "for safety".**
- Pattern: JTA transaction spanning a database and a broker.
- Breaks: in-doubt locks, orphaned transactions, coordinator as single point of failure.
- Fix: idempotent consumer with a dedup table, or restructure; see `distributed-transactions-2pc.md`.

## 3. Interleaving tests, per anomaly

Run each against the real database engine, with the real isolation level and driver configuration. For each, first run it at the weakest plausible level to see the invariant break (this proves the test can fail), then at the configured level and assert the invariant holds. Under serializable, a pass may mean "one transaction aborted and the retry saw the new state".

| Anomaly | Interleaving | Assertion |
|---|---|---|
| Lost update (counter) | N workers each do the real code path once, concurrently | final value equals initial plus N |
| Lost update (document edit) | A and B load version 1; A saves; B saves | B's save is rejected or merged; A's change not lost |
| Write skew (on-call) | A and B both read count = 2; A sets off; B sets off; commit both | count of on-call is at least 1 at the end |
| Phantom (booking) | A and B both check no overlap; both insert; commit | at most one booking exists for the slot |
| Username claim | A and B check name free; both insert | exactly one user row; the other got a unique violation |
| Double spend | A and B both sum spends and check against balance; both insert | total spent does not exceed balance |
| Read skew | R reads account 1; T moves money 1 to 2 and commits; R reads account 2 | R's total equals the true total |
| Retry correctness | inject a serialization failure on the first attempt | effect applied once; inputs re-read on the second attempt |
| Duplicate delivery | deliver the same message twice, also concurrently | one effect |
| Lost commit ack | commit succeeds, connection is cut before the reply, client retries with same key | one effect |

## 4. A test harness sketch

Adaptation. Python with one real connection per worker and a barrier to force the interleaving. The shape was run against SQLite in WAL mode as a stand-in driver (weak mode: both transactions commit and zero doctors stay on call; transactional mode: one write is refused, the retry sees the new state, one doctor stays on call). It has not been run against PostgreSQL; adapt `connect`, `begin` and `abort_errors` to your driver.

```python
import threading

def interleave(connect, begin, abort_errors, steps, sync="after_read", timeout=10):
    """steps: objects with read(conn) -> value and write(conn, value).
    sync="after_read": barrier between read and write, so both read before either writes
      (exposes lost update, write skew, phantom).
    sync="before_read": barrier before the read. Use it to test lock-based remedies: a
      FOR UPDATE read blocks the second worker, so an after-read barrier never fills."""
    barrier = threading.Barrier(len(steps))
    outcomes = [None] * len(steps)

    def worker(i, step):
        try:
            conn = connect()                     # separate connection per worker
            try:
                begin(conn)                      # e.g. execute "SET TRANSACTION ISOLATION LEVEL ..." (PostgreSQL:
                                                 # must be the first statement) or the driver's BEGIN
                if sync == "before_read":
                    barrier.wait(timeout)
                seen = step.read(conn)           # e.g. count the doctors on call
                if sync == "after_read":
                    barrier.wait(timeout)
                try:
                    step.write(conn, seen)
                    conn.commit()
                    outcomes[i] = "committed"
                except abort_errors:             # serialization failure, deadlock, busy-snapshot
                    conn.rollback()
                    outcomes[i] = "aborted"
            finally:
                conn.close()
        except BaseException as e:               # surface everything else; a swallowed error looks like a pass
            outcomes[i] = e

    threads = [threading.Thread(target=worker, args=(i, s)) for i, s in enumerate(steps)]
    for t in threads: t.start()
    for t in threads: t.join()
    for i, o in enumerate(outcomes):
        if isinstance(o, BaseException):
            raise o
        if o == "aborted":                       # what the retry wrapper does: rerun alone, re-reading
            conn = connect()
            try:
                begin(conn)
                steps[i].write(conn, steps[i].read(conn))
                conn.commit()
            finally:
                conn.close()
            outcomes[i] = "committed after retry"
    return outcomes    # then assert the invariant on a fresh connection
```

With psycopg 3: `connect=lambda: psycopg.connect(dsn)`, `begin=lambda c: c.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")`, `abort_errors=(psycopg.errors.SerializationFailure, psycopg.errors.DeadlockDetected)`.

The barrier is the point: it pins the schedule that exposes the race, so the test is deterministic instead of relying on timing luck. The barrier timeout turns a hang into a `BrokenBarrierError`, which usually means a lock is serializing the workers and `sync="before_read"` is the right setting. Run it for each level you care about and record which levels fail.

## 5. Review questions with observable answers

1. What engine and isolation level does this code run at? (Point to the config line.)
2. For each read-then-write, what protects the write: atomic op, version column, lock, constraint, serializable? (Point to the line.)
3. Does any guard depend on rows that might not exist?
4. What does the code do when the database returns a serialization failure or deadlock? (Point to the retry code.)
5. If the commit succeeded but the client never saw the reply, what happens on retry?
6. Does any side effect occur between BEGIN and COMMIT?
7. How long can a transaction stay open, and is anything slow (HTTP, user wait) inside it?
8. For every write to two systems, which mechanism makes them agree?
9. Which test in the suite fails if the protection is removed?

## 6. Evidence to show the user

- A table of write paths with invariant, protection and test name.
- The configured engine and level, with the file and line.
- Test output at the weak level (fails) and at the chosen level (passes), per anomaly.
- The retry configuration (classes of errors retried, cap, backoff).
- Open risks: any invariant left unprotected, and what it would take to close it.
