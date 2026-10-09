# Serializability implementations

Source: DDIA 2e ch. 8 section on serializability. Product names and numbers are as the notes record them and are dated.

## Contents
1. What serializable promises and why it is the real answer
2. Actual serial execution
3. Two-phase locking (2PL)
4. Serializable snapshot isolation (SSI)
5. Comparison table and picking
6. Operating each one: what the application must do

## 1. What serializable promises

The outcome equals that of some serial execution of the transactions, even though they ran concurrently. If each transaction is correct on its own, the system stays correct. That prevents all the race conditions in `anomalies-and-isolation-levels.md`, including write skew and phantoms.

Why the book treats it as the answer rather than one option: weak levels are implemented inconsistently across products (repeatable read varies), you cannot tell from application code whether it is safe at a given level, and there are no practical race-detection tools (testing is timing-dependent; static analysis is still research).

Serializability is an isolation property for multi-object transactions. It is not the same as linearizability (a recency guarantee on a single object); see `acid-base-and-linearizability.md`. 2PL (this file) is not 2PC (atomic commit across nodes; `distributed-transactions-2pc.md`).

## 2. Actual serial execution

Run transactions one at a time on a single thread; no conflict detection is needed.

- Why it became feasible (2000s): RAM is cheap enough to hold the active dataset in memory, so no waiting on disk; OLTP transactions are short and small; long read-only analytics can run on a snapshot outside the serial loop.
- Used by: VoltDB/H-Store, Redis, Datomic.
- Interactive transactions kill it. A transaction that sends one statement, waits for the application, then sends the next leaves the single thread idle across the network. So serial-execution systems require single-statement transactions or stored procedures submitted whole.
- Stored procedures:
  - Pros: no network or disk round trips inside the transaction; fast on one thread.
  - Historic cons: vendor-specific languages (PL/SQL, T-SQL, PL/pgSQL) with poor ecosystems; hard to debug, version, deploy, test and monitor; a bad procedure hurts every tenant of the shared database; running untrusted code in the database process is a security risk.
  - Mitigation: general-purpose languages (VoltDB Java/Groovy, Datomic Java/Clojure, Redis Lua, MongoDB JavaScript).
  - If replicated by running the same procedure on each replica (state machine replication, as VoltDB does), the procedure must be deterministic (no wall-clock reads except through a deterministic API).
- Scaling: shard so each transaction touches one shard, then one thread per shard scales roughly linearly. Cross-shard transactions need lockstep coordination: the notes record VoltDB at about 1,000 cross-shard writes per second, orders of magnitude below single-shard, and more machines do not help. Many secondary indexes imply much cross-shard work; plain key-value data shards easily.
- Use only if all hold: every transaction small and fast (one slow one stalls everything); active dataset fits in memory; write throughput fits one core, or can be sharded with rare cross-shard transactions.

## 3. Two-phase locking (2PL)

The dominant serializability algorithm for about 30 years (strictly, strong strict 2PL). Used by MySQL/InnoDB and SQL Server serializable, and Db2 repeatable read.

- Rules: many readers may hold a shared lock on an object; any write needs exclusive access. A reader waits for an uncommitted writer (it cannot read an old version as MVCC would), and a writer waits for all readers. Writers block readers and readers block writers, in contrast to snapshot isolation.
- Mechanics: read acquires shared; write acquires exclusive; read-then-write upgrades shared to exclusive; all locks held until commit or abort. Growing phase (acquire), then shrinking phase (release at end); nothing is acquired after the first release.
- Deadlocks: the database detects them and aborts one transaction; the application retries. They are much more frequent than under lock-based read committed, and an aborted transaction redoes all its work.
- Performance: clearly worse throughput and response time than weak isolation, from lock overhead and above all lost concurrency, since any possible conflict makes someone wait. A transaction that scans a whole table (backup, analytics, integrity check) takes shared locks on it and blocks all writers for a long time. Latency is unstable and the high percentiles are bad under contention; one slow transaction can freeze the system. Mitigate with transaction timeouts and slow-query monitoring.
- Phantoms:
  - Predicate lock (conceptual): a lock belonging to all objects matching a search condition, including objects not yet existing. A reader takes a shared predicate lock on its WHERE condition; any insert, update or delete checks whether its old or new value matches an existing predicate lock and waits if so. With predicate locks 2PL is truly serializable but slow when many are held.
  - Index-range (next-key) lock: what real databases do. Approximate the predicate by a superset (all bookings of room 123, or all rooms for noon to 1pm) by attaching a shared lock to the index entries or range scanned. Less precise (locks more than needed) but far cheaper. With no usable index, the fallback is a shared lock on the whole table: safe, but blocks all writers.
  - Practical consequence (adaptation): a query that checks a condition should hit an index that matches it, otherwise the lock widens to the table.

## 4. Serializable snapshot isolation (SSI)

First described in 2008. Used in PostgreSQL (serializable), SQL Server Hekaton, HyPer, CockroachDB, FoundationDB, BadgerDB. Claim: full serializability for a small penalty over snapshot isolation.

- Optimistic: proceed without blocking; at commit check whether isolation was violated; abort and retry if so. Compare pessimistic 2PL (wait if anything might go wrong) and serial execution (extreme pessimism, a global lock compensated by speed).
- Built on snapshot isolation plus an algorithm that detects serialization conflicts and chooses transactions to abort.
- Core insight: write skew is a decision based on an outdated premise. The query result may be stale by commit time, and the database cannot know how the application uses it, so it assumes a causal dependency from reads to writes. Two cases are detected:
  1. Stale MVCC read. A transaction read a snapshot that ignored another transaction's uncommitted write; by the time the first commits, the writer has committed. The database tracks when a transaction ignores writes because of visibility rules and, at commit, aborts if any ignored writer has committed. The check is at commit, not at read: a read-only transaction need not abort, the writer might still abort, and long read-only snapshots survive.
  2. A write that affects an earlier read. Using index-range style tracking (or table level if no index), the database records that transaction X read a range; a writer into that range flags X. This is a tripwire, not a blocking lock. The information is kept until the reader and all concurrent transactions finish. In the book's example both transactions notify each other; the first to commit succeeds and the second must abort at its commit.
- Costs and tuning:
  - Tracking granularity: fine means precise aborts but bookkeeping overhead; coarse is faster but gives more false-positive aborts. PostgreSQL proves some reads of overwritten data are still serializable, to cut unnecessary aborts.
  - Abort rate is the key factor. Optimistic control performs badly under high contention (many aborts, and retries add load near maximum throughput) and better than pessimistic when there is spare capacity and low contention. Keep read-write transactions short; long read-only transactions are fine.
  - Reduce contention with commutative atomic operations (concurrent increments do not conflict unless read in the same transaction).
  - No lock waiting: writers do not block readers, read-only queries are lock-free on the snapshot, latency is more predictable. Not limited to one core (FoundationDB distributes conflict detection across machines).
  - Whether its overhead over plain snapshot isolation is worth it is contested in the literature the notes cite (one view: not worth it; another: good enough to drop plain snapshot isolation).

## 5. Comparison and picking

| | Serial execution | 2PL | SSI |
|---|---|---|---|
| Style | pessimistic extreme (global lock) | pessimistic | optimistic |
| Reads block writers / writers block readers | n/a (single thread) | yes / yes | no / no |
| Phantom handling | trivial | predicate or index-range locks | index-range tripwires checked at commit |
| Scales across cores | only by sharding with single-shard transactions | yes, but contention-bound | yes (FoundationDB distributes it) |
| Worst case | one slow transaction stalls all; cross-shard about 1k writes/s (VoltDB) | long reads freeze writers; deadlocks; latency tail | high contention causes abort storms |
| Needs | in-memory data, short transactions, stored procedures, low write rate or single-shard transactions | indexes on predicates, deadlock retry, timeouts | retry logic, short read-write transactions, low contention |
| Pick when | small hot dataset, simplicity first (Redis/VoltDB-style) | already on MySQL/SQL Server/Db2 serializable and contention is low | read-heavy mix with long read-only queries (PostgreSQL, CockroachDB, FoundationDB) |

The "pick when" row is the notes' synthesis, not a statement from the book.

## 6. Operating each one

- Whatever the implementation, the application loop is: begin, do work, commit; on serialization failure or deadlock, roll back and rerun the whole transaction from the start (re-reading, since the premise changed). See `retries-and-idempotency.md`.
- Under 2PL: add timeouts, watch lock waits and slow queries, make sure predicate queries have indexes, keep bulk scans off the OLTP primary.
- Under SSI: monitor the abort rate per transaction type; if one type aborts a lot, shorten it, split read from write, or replace its counter with an atomic increment.
- Under serial execution: keep transactions to one request or one stored procedure call, and keep the slow work (HTTP calls, emails) outside the procedure.
- Verify with the interleaving tests in `code-review-checklist.md`; a serializable level should turn each "invariant broken" test into "one transaction aborts, retry succeeds, invariant holds".
