---
name: arch-transactions
description: Reasoning about correctness of concurrent reads and writes against a database - what ACID does and does not guarantee, every isolation anomaly (dirty read/write, read skew, lost update, write skew, phantom) with the level that prevents it and the application-level remedy, snapshot isolation/MVCC, serializable via serial execution, 2PL or SSI, retries and idempotency, two-phase commit and XA costs. Use when reviewing or writing code that does read-then-write, check-then-insert, counters, balances, stock, bookings, uniqueness; when choosing READ COMMITTED vs REPEATABLE READ vs SERIALIZABLE; when a race, double-spend or lost update is suspected; when adding retries to transactions; or when a design writes to two systems at once. Not about replication lag or linearizable stores (`arch-replication-and-consistency`) or sagas across services (`arch-distributed-workflows`).
---

# Transactions and isolation

## Purpose

Most concurrency bugs in application code come from believing the database is protecting an invariant when it is not: a SELECT followed by an UPDATE, a count followed by an INSERT, an ORM load-mutate-save. This skill lets you name the anomaly in front of you, pick the cheapest remedy that really stops it on the engine in use, and prove it with an interleaving test. It also covers retries (aborts are normal at higher isolation) and what atomic commit across systems costs.

## Choose what applies

| What you are looking at | Do this | Read |
|---|---|---|
| Code reads rows, decides, then writes (counter, balance, stock, roster, booking, username, quota) | Identify the anomaly (lost update, write skew, phantom), pick a remedy from the ladder | `references/anomalies-and-isolation-levels.md`, then `references/choosing-an-isolation-level.md` |
| Asked "which isolation level should we use?" or "is READ COMMITTED enough?" | Start from the invariants, not the level; check the engine's real behaviour | `references/choosing-an-isolation-level.md` |
| A report, backup or multi-query view gives inconsistent totals | Read skew: run it as one snapshot transaction | `references/anomalies-and-isolation-levels.md` (read skew) |
| Reviewing a PR or auditing a codebase for races | Scan for the smells, write interleaving tests | `references/code-review-checklist.md` |
| Serializable is chosen or proposed and you must know its cost (aborts, lock waits, deadlocks) | Match implementation to workload | `references/serializability-implementations.md` |
| Writing or reviewing a retry loop, a consumer of a queue, a "charge once" endpoint | Idempotency key plus dedup table, transient-only retries | `references/retries-and-idempotency.md` |
| One operation writes to two databases, or a database and a broker, or spans shards | Decide mechanism; avoid XA across heterogeneous systems | `references/distributed-transactions-2pc.md` |
| "Is this ACID?", "what does consistency mean here?", durability claims, serializable vs linearizable | Define terms precisely | `references/acid-base-and-linearizability.md` |
| A single-row update with no read dependency; independent writes on disjoint data | Nothing to do: the default level is fine | (this file) |
| Stale reads from replicas, failover, quorum settings, clocks, consensus | Out of scope here | `arch-replication-and-consistency` |
| Business workflow across services needing compensation (sagas), data ownership between services | Out of scope here | `arch-distributed-workflows` |
| Threads, locks and deadlocks inside one process | Out of scope here | `craft-concurrency` |
| Dual writes, outbox, change data capture, exactly-once stream processing | Brief mention here only | `arch-data-pipelines` |

## How to apply

### A. Diagnose a write path (do this first)

1. Name the transaction boundary: where it begins and ends, and the engine and isolation level it runs at (config file, connection string, ORM settings). If you cannot find the level, say so; assume the engine default and state the assumption.
2. List what it reads and what it writes. If no write depends on a read (or reads are all inside the written row), concurrency is harmless; stop.
3. State the invariant that a concurrent twin of this transaction could break, in one sentence ("sum of spends never exceeds balance").
4. Classify using the shape of the code:

| Shape | Anomaly |
|---|---|
| read value, compute in app, write the same row back | lost update |
| read a set of rows (count, sum, search), write a different row based on it | write skew |
| search for the absence of rows, then insert | phantom (write skew caused by absence) |
| several reads in one transaction must agree with each other | read skew |
| see another transaction's uncommitted data | dirty read (read uncommitted or no transactions) |

5. Pick the remedy with the ladder below. Prefer one that cannot be forgotten at another call site.

### B. Remedy ladder

| Anomaly | First choice | Then | Last resort |
|---|---|---|---|
| Lost update | atomic operation in the statement (`SET n = n + 1`) | version column with conditional `UPDATE ... WHERE version = :seen`, check rows affected; or `SELECT ... FOR UPDATE` | a level that auto-detects, with retry (only if the engine does and a test proves it; MySQL/InnoDB repeatable read does not) |
| Write skew | serializable isolation with retry | `FOR UPDATE` on the rows the decision read (they must exist); constraint or trigger | materialize conflicts |
| Phantom (check absence, insert) | unique constraint when the invariant is uniqueness | serializable with retry | materialize conflicts: lock rows for room/slot pairs |
| Read skew | snapshot isolation for that transaction | serializable | explicit locks |

Why this order: atomic operations and constraints are enforced by the database for every code path; explicit locks and conditional writes rely on each call site doing the right thing; materialized conflicts leak concurrency control into the data model and are easy to get wrong.

### C. Isolation level facts to hold in mind

| Level | Dirty read | Read skew | Phantom | Lost update | Write skew |
|---|---|---|---|---|---|
| Read uncommitted | possible | possible | possible | possible | possible |
| Read committed | prevented | possible | possible | possible | possible |
| Snapshot isolation | prevented | prevented | prevented | depends on engine detection | possible |
| Serializable | prevented | prevented | prevented | prevented | prevented |

- Level names are not portable: PostgreSQL "repeatable read" is snapshot isolation; Oracle "serializable" is snapshot isolation (write skew possible); MySQL/InnoDB "repeatable read" does not detect lost updates; Db2 "repeatable read" is serializable; PostgreSQL "serializable" is SSI; MySQL and SQL Server "serializable" use two-phase locking. These are dated vendor facts: confirm for the version in use.
- Snapshot isolation never blocks readers behind writers; two-phase locking does (and is slower under contention).

### D. If serializable is the answer

1. Confirm what the engine's "serializable" really is (SSI, 2PL, or serial execution), and its failure mode: SSI aborts at commit under contention; 2PL waits and deadlocks; serial execution needs short transactions.
2. Add a retry wrapper around the whole transaction (re-read inputs on each attempt, transient errors only, capped, backoff with jitter).
3. Keep read-write transactions short and keep slow work (HTTP calls, human waits) outside them.
4. Index the columns used in predicates (2PL locks the scanned index range, falling back to the whole table when no index fits).

### E. If the operation spans systems

1. Ask whether it must be atomic. If yes and the data can live in one database, put it there (one transaction beats any protocol).
2. Multi-shard in one database product: use the product's internal distributed transactions.
3. Different vendors or database plus broker: avoid XA (in-doubt locks, orphaned transactions, single points of failure); use a local transaction with a dedup table and an idempotent consumer, keyed by message ID.
4. Otherwise it is an eventual-consistency design: see `arch-distributed-workflows`.

### F. Worked diagnosis (on-call roster)

Code: `n = SELECT count(*) FROM doctors WHERE on_call AND shift = 1234; if n >= 2: UPDATE doctors SET on_call = false WHERE id = :me`.
1. Boundary and level: one transaction per request at the engine default (say, snapshot isolation under the name "repeatable read").
2. Reads a count over many rows; writes one row (a different row per doctor). The write depends on the read.
3. Invariant: at least one doctor on call per shift.
4. Shape: set read, different row written, so write skew. Lost-update detection and atomic operations do not apply (different rows); snapshot isolation does not stop it.
5. Remedy: run the transaction at serializable and retry; or lock first with `SELECT ... WHERE on_call AND shift = 1234 FOR UPDATE` (the rows exist, so the lock works).
6. Test: two connections, barrier after the count, both update, commit both; assert at least one doctor on call. It must fail at snapshot isolation and pass (possibly after one retry) at the fix.

## Verify

Tests and checks to run before claiming a path is safe:

1. Write one interleaving test per invariant at risk, using two real connections and a barrier so both transactions read before either writes. Run it first at a weak level (it must fail, proving the test can detect the bug), then at the configured level (it must pass). Test shapes per anomaly are in `references/code-review-checklist.md` section 3. When testing a lock-based remedy (`FOR UPDATE`), put the barrier before the read, since the lock stops the second worker from reaching an after-read barrier (harness in section 4 of that file).
2. Under serializable, a passing run may include an aborted transaction; the test must apply the retry and assert the final invariant, not the absence of errors.
3. Counter check: N concurrent calls through the real code path produce initial plus N.
4. Retry check: inject a serialization failure on attempt 1; confirm the body re-read its inputs and the effect applied once. Inject a constraint violation; confirm it is not retried.
5. Idempotency check: deliver the same message twice (also concurrently); cut the connection after commit and before the reply, then retry; both give one effect.
6. Engine check: record engine, version and level, and cite the documentation or test that shows the level prevents what you rely on. Do not rely on the level's name.
7. For cross-system writes: name the mechanism for each (single transaction, internal distributed transaction, dedup consumer, outbox, saga). "Both calls usually succeed" is not a mechanism.

Evidence to show the user: a table of write paths (invariant, protection, test name), the test output at weak and chosen levels, the isolation level with file and line, retry settings, and any invariant left unprotected with the cost of closing it.

Done means:
- every cross-row or absence-based invariant has a named protection (constraint, atomic op, lock, serializable) and a failing-then-passing test;
- the isolation level used is stated for the engine and version, not by name alone;
- retries exist for serialization failures and deadlocks, are bounded, and are idempotent for side effects;
- no transaction waits on a user or spans requests;
- no ad hoc two-phase protocol and no XA across heterogeneous systems without a written justification.

## Proportion and limits

- Do not raise every transaction to serializable. It adds aborts or lock waits and needs retry code. Use the cheap remedies (atomic op, constraint, version column) for single-row cases, and reserve serializable for cross-row invariants.
- Read-only and disjoint transactions need no special care. A low-traffic internal tool with one user at a time does not need interleaving tests; a payment, stock or booking path does, and the book notes attackers can fire concurrent bursts deliberately.
- Serializable choice is contested at the margin: whether SSI's overhead over plain snapshot isolation is worth it is argued both ways in the source's references; decide by measured abort rate on your workload.
- Serial execution (VoltDB/Redis style) suits small in-memory datasets with short transactions; cross-shard transactions there are very slow (about 1,000 writes per second reported for VoltDB).
- Vendor behaviour, defaults and product lists in the references are dated; the anomalies and the reasoning are not. Re-verify engine-specific claims.
- 3PC is mostly theoretical; do not propose it. Do not hand-build consensus or a coordinator.
- Some source claims are the notes' own synthesis and are marked "(inferred)" in the references (for example the ordering of remedies and the pairing of tests with anomalies). Treat them as guidance, not as the book's rules.

## References

- `references/anomalies-and-isolation-levels.md`: the precise anomaly table, vendor naming traps, each anomaly with how it looks in code, remedies with SQL sketches, materialized conflicts, how MVCC snapshots work (versions, visibility, bloat). Read when diagnosing or when you must explain what a snapshot sees.
- `references/choosing-an-isolation-level.md`: decision table from invariant to level/remedy, level costs, serializable vs workarounds, worked choices (counter, booking, roster, balance). Read when asked to choose.
- `references/serializability-implementations.md`: serial execution, 2PL with predicate and index-range locks, SSI, comparison table, operating notes. Read when serializable is on the table or its cost matters.
- `references/retries-and-idempotency.md`: the five retry caveats, a tested retry wrapper with error-code classification, dedup-table recipe with crash analysis. Read when writing or reviewing retries or queue consumers.
- `references/distributed-transactions-2pc.md`: 2PC protocol, in-doubt state, XA problems, NewSQL fixes, ACID vs BASE across services, decision rules. Read when two systems or several shards must commit together.
- `references/acid-base-and-linearizability.md`: ACID defined letter by letter, durability, single vs multi-object, serializability vs linearizability. Read for definitions and requirement classification.
- `references/code-review-checklist.md`: repository scan procedure, fifteen smells with fixes, interleaving tests, a harness sketch (run against SQLite as a stand-in; barrier placement for lock-based remedies), review questions. Read when reviewing code or writing the tests.

## Sources

- Designing Data-Intensive Applications, 2nd ed., ch. 8 (Transactions): ACID, weak isolation, lost updates, write skew, serializability, distributed transactions, idempotence.
- Designing Data-Intensive Applications, 2nd ed., ch. 10 (Consistency and Consensus), partA and partB: only the linearizability vs serializability distinction, when linearizability is needed, and atomic commit versus consensus.
- Software Architecture: The Hard Parts, ch. 9 (Data Ownership and Distributed Transactions): the ACID vs BASE part and the cross-service consequences.
