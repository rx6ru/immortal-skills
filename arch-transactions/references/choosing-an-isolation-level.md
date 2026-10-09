# Choosing an isolation level and a remedy

Source: DDIA 2e ch. 8 (weak isolation levels, lost updates, write skew, serializability, section 12 decision rules). Items marked (inferred) are the notes' own synthesis rather than a direct statement of the book.

## Contents
1. Start from the invariant, not the level
2. Decision procedure
3. Level-by-level: what you get, what it costs
4. Weighing serializable against the workarounds
5. Defaults and what to verify about the database in front of you
6. Worked choices

## 1. Start from the invariant, not the level

Weak isolation exists because serializable costs performance, so databases default to a level that protects against some anomalies only. "Use an ACID database for financial data" does not settle the question: many ACID databases run weak isolation by default. Concurrency bugs are timing-dependent, so testing finds them rarely, and attackers can send bursts of concurrent requests on purpose to hit the race. So decide per invariant, write the decision down, and test it.

For each write path ask:
1. Which values does this transaction read, and which does it write?
2. Does the write depend on what was read (read-modify-write, check-then-act)?
3. Could a concurrent transaction change what was read before this one commits?
4. What invariant is violated if both go ahead? Is it on one row, on several rows, or about the absence of rows?

If the answer to 2 is no and the transaction touches disjoint data, concurrency is harmless and the default level is fine. Read-only transactions and disjoint transactions are safe in parallel.

## 2. Decision procedure

| Situation | Choose | Why |
|---|---|---|
| Independent single-row writes; no read-then-write dependency; no cross-row invariant | default level (read committed in PostgreSQL, Oracle, SQL Server) | nothing to race on; cheapest |
| Several reads in one request/report/backup/integrity check must agree | snapshot isolation (or serializable) for that transaction | read skew; read committed shows different rows at different times |
| Read-modify-write of one value (counter, balance, stock count) | first choice atomic DB operation; then conditional write on a version column; then `SELECT ... FOR UPDATE`; auto-detection only if your engine does it | atomic ops cannot be forgotten at a call site; detection depends on the engine (MySQL/InnoDB repeatable read does not detect) |
| Invariant across several rows ("at least one on call", "sum of spends within balance") | serializable, or lock the rows the decision reads, or a constraint | write skew is not stopped by snapshot isolation or by lost-update detection |
| Invariant is "no row exists matching X" (booking overlap, free username, empty square) | serializable, or a unique constraint, or materialized conflicts | `FOR UPDATE` has nothing to lock for an absent row |
| Invariant is plain uniqueness | unique constraint | the database enforces it for everyone, including code paths you forgot |
| Atomicity across several shards of one database | a database with internal distributed transactions | see `distributed-transactions-2pc.md` |
| Atomicity across heterogeneous systems (DB plus broker plus external API) | avoid XA; use idempotent consumers keyed by message ID | see `retries-and-idempotency.md` |
| Replicated store without single-leader transactions | conflict resolution by commutative operations, not locks | locks and compare-and-set assume one up-to-date copy |

The order "atomic op, conditional write, FOR UPDATE, auto-detection" is the notes' synthesis (inferred ordering; the book discusses each remedy and calls atomic operations usually the best).

## 3. Level-by-level

### Read committed
- Gets: no dirty reads, no dirty writes. Writes take row locks held to commit, so a second writer waits. Readers see the old committed version until commit, so a long writer does not stall readers (in the usual implementation).
- Does not stop: read skew, lost updates (the second write comes after the first commit, so it is not a dirty write), write skew, phantoms.
- Use when: operations are single-statement or independent.

### Snapshot isolation (repeatable read in some products)
- Gets: each transaction reads from the snapshot of data committed when it started. Readers never block writers and writers never block readers; writers still block each other on the same row.
- Cost: the database keeps several versions per row (MVCC); a long-running transaction pins old versions so cleanup cannot reclaim them (storage bloat, inferred). Index entries point at versions and are cleaned with them.
- Does not stop: write skew. Lost updates only if the engine detects them.
- Use when: reporting, backups, integrity checks, any multi-query consistent view, and as the base for SSI.

### Serializable
- Gets: the result equals some serial order, so a transaction that is correct alone stays correct under concurrency. Prevents every anomaly in the table.
- Cost depends on implementation (`serializability-implementations.md`).
- Obligation: the application must retry transactions the database aborts for serialization failure or deadlock.

## 4. Weighing serializable against the workarounds

Prefer serializable when:
- the invariant spans rows or depends on absence of rows, and there are several code paths that touch the same data (each workaround must be remembered at every call site);
- you cannot tell, from the application code, which anomaly is possible (the book's argument for serializability: weak levels are implemented inconsistently, and no practical race detector exists).

Accept the workaround when:
- the invariant is plain uniqueness (constraint) or a single-row counter (atomic op);
- the engine's serializable mode would make the hot path abort or wait too much (high contention under SSI, long reads under 2PL);
- you can name the exact rows to lock, and they exist.

Never settle for snapshot isolation alone for a cross-row invariant, and do not trust a level named "serializable" without checking the engine (Oracle's is snapshot isolation).

## 5. Defaults and what to verify about the database in front of you

Facts below are from the notes and are dated; re-check against the version in use.
1. Find the engine and the configured default level (connection string, ORM settings, pool defaults, session settings).
2. Look up what that engine does at the level you pick (the naming table in `anomalies-and-isolation-levels.md`).
3. If correctness depends on lost-update detection or on SSI, assert it with a test; do not rely on documentation memory.
4. Confirm the application retries serialization failures and deadlocks. Many ORMs (ActiveRecord, Django in the book's account) do not retry aborted transactions by default; the exception bubbles up and the user input is dropped.
5. Keep transactions inside a single request. A transaction must not wait on a human or span HTTP requests: it holds locks or pins versions, and under serial execution it stalls everything.

## 6. Worked choices

These apply the book's examples with the remedies above; the specific pairings are adaptation, not quotations of the book.

**Counter of unread messages (denormalized copy).** Update the message insert and the counter in one transaction (atomicity: both or neither). Increment atomically: `UPDATE users SET unread = unread + 1 WHERE id = :u`. Default level suffices for the counter once the increment is atomic. Reports that compare the counter to the message table need a snapshot.

**Seat or room booking.** The invariant is "no two bookings overlap": an absence check. Options in order: serializable with retry; a unique constraint if each bookable unit is a row with a unique key; materialized (room, slot) rows with `FOR UPDATE`. The plain "select overlapping, then insert" at snapshot isolation is unsafe.

**On-call roster.** Read the count, then remove self. Options: serializable; or `SELECT ... FOR UPDATE` on the on-call rows of that shift (rows exist, so locking works).

**Account balance with tentative spend rows.** Inserting a spend row, summing, and checking non-negative is write skew. Serializable, or lock the account row (one row everyone must lock first, so concurrent spends queue).

**Wiki page edit.** Version column and conditional write; on 0 rows affected, show the conflict to the user rather than silently overwrite. Free-text merge needs CRDT or operational transform, which is out of scope.

**Backup or integrity check scan.** Snapshot isolation, read-only transaction. At 2PL-based serializable a whole-table read blocks all writers; at SSI a long read-only transaction is fine.
