# ACID, BASE, durability and the linearizability distinction

Source: DDIA 2e ch. 8 (why transactions, ACID, single vs multi-object) and ch. 10 (linearizability vs serializability box, when linearizability is needed); Architecture: The Hard Parts ch. 9 (ACID vs BASE). Depth on linearizability, consensus and clocks is in `arch-replication-and-consistency`.

## Contents
1. What transactions are for
2. ACID letter by letter
3. Durability details
4. Single-object vs multi-object
5. ACID vs BASE
6. Serializability vs linearizability
7. When linearizability is needed (the part relevant to transactions)
8. Verify

## 1. What transactions are for

Faults to survive: crash mid-write, crash of the application between steps of a sequence, network cuts (application to database, node to node), concurrent clients overwriting each other, readers seeing partially updated data, races. A transaction groups reads and writes into a logical unit: commit (all) or abort/rollback (none), and an aborted transaction can be retried. Partial failure becomes invisible, which simplifies error handling.

Transactions are not a law of nature. Some applications weaken or drop them for performance or availability, and the folklore that "transactions do not scale" is out of date: NewSQL systems (CockroachDB, TiDB, Spanner, FoundationDB, YugabyteDB) provide ACID with sharding and consensus. Not every system must be transactional. Simple single-record access patterns can do without; complex access patterns benefit greatly, and without transactions denormalized data drifts out of sync.

"ACID compliant" is mostly a marketing term, and "BASE" is vaguer still: it just means "not ACID".

## 2. ACID letter by letter

| Letter | What it really means | Whose job | Common confusion |
|---|---|---|---|
| Atomicity | abortability: on a fault mid-transaction (crash, network cut, disk full, constraint violation) the database discards all writes so far, leaving no partial state, so retry is safe | the database (log/undo) | not the multithreading sense (nobody sees a half-done state); that is isolation |
| Consistency | application-specific invariants hold before and after each transaction; they may be violated inside it | mostly the application; the database enforces only declared constraints (foreign key, uniqueness, check; triggers or materialized views for more) | the word has five meanings: replica consistency (eventual consistency), consistent snapshot, consistent hashing, CAP consistency (linearizability), ACID consistency |
| Isolation | concurrent transactions do not step on each other; textbook form is serializability | the database, at a configurable level | in practice almost everyone runs weaker levels; Oracle's "serializable" is snapshot isolation |
| Durability | after commit, data is not forgotten despite hardware faults or crashes | database plus hardware | no perfect durability exists |

Practical reading for an agent: the "C" is the part that your code owns. An invariant that is not declared as a constraint and not protected by an isolation level or lock is simply unprotected. Race example: two clients read counter 42 and both write 43; the increment from 42 to 44 became 43.

## 3. Durability details

- Single node: fsync to nonvolatile storage and a write-ahead log for crash recovery, with checksums on log entries to detect corrupt or incomplete entries (MySQL, MongoDB, PostgreSQL).
- Replicated: durable means copied to N nodes; the database waits for those writes before reporting commit.
- Neither is enough alone. Disk only: a dead machine makes data inaccessible until repaired or moved. Replication only: correlated faults (a power outage, an input that crashes every node) lose in-memory-only data, and asynchronous replication loses recent writes if the leader fails.
- Reality: SSDs sometimes violate fsync guarantees on power loss; firmware bugs (drives failing at exactly 32,768 hours); PostgreSQL misused fsync for over 20 years; filesystem and storage-engine interactions corrupt files; silent corruption can spread to replicas and recent backups (keep historical backups); 30 to 80 percent of SSDs develop at least one bad block within 4 years; an unpowered worn SSD can lose data in weeks to months.
- Conclusion: combine disk writes, replication and backups, and take guarantees with salt.

## 4. Single-object vs multi-object

- A multi-object transaction keeps several rows, documents or records in sync. The database must know which operations belong together; relational databases use the client's TCP connection (everything between BEGIN and COMMIT; a dropped connection aborts). A NoSQL "multi-put" is not a transaction.
- Single-object writes: storage engines almost universally give atomicity (crash-recovery log) and isolation (per-object lock) for a single key on a single node.
- Helper operations (atomic increment, compare-and-set, conditional write) prevent lost updates but are not transactions. Cassandra/ScyllaDB lightweight transactions and Aerospike strong-consistency mode give linearizable read plus conditional write on one object only.
- Multi-object transactions are needed for: foreign keys and graph edges across mutually referencing records; denormalized copies that must change together (the document model encourages duplicates); secondary indexes (separate objects that otherwise can disagree with the record, which ties to sharded secondary indexes).
- Without transactions it can be done, but error handling is harder and concurrency problems appear. Alternatives are discussed in the book's streaming chapters (see `arch-data-pipelines`).

## 5. ACID vs BASE

ACID holds inside a service with its own transactional database. A business request that spans services is a distributed transaction and loses all four properties across the request: atomicity per service only; consistency can break and foreign keys cannot span services' commits; isolation is lost since committed data is visible before the request completes; durability is per service. BASE (basic availability, soft state, eventual consistency) is the contrasting regime, traded for performance, scalability, elasticity, fault tolerance and availability. An architect cannot weigh when a distributed transaction is acceptable without understanding ACID precisely (the Hard Parts' claim). Details and patterns: `distributed-transactions-2pc.md` section 10 and `arch-distributed-workflows`.

## 6. Serializability vs linearizability

| | Serializability | Linearizability |
|---|---|---|
| Is a | isolation level for transactions (multi-object) | recency guarantee on single objects (a register) |
| Guarantees | outcome as if transactions ran in some serial order, which may differ from real time | if operation A finished before B started, B sees a state at least as new as A's |
| Prevents write skew and phantoms | yes | no (single object, no grouping) |
| Allows stale reads | yes | no |

- Both together is strict serializability (strong one-copy serializability). Single-node databases are typically both. Spanner and FoundationDB are strict serializable. CockroachDB is serializable with some recency guarantees on reads, not strict serializability (which would need expensive coordination).
- Consistency model and isolation level can be chosen largely independently.
- Practical consequence: a serializable database can still return a stale read relative to real time; a linearizable register store gives you no multi-row invariants. Check which one the requirement actually asks for. "Two users must not both get the last seat" is an isolation question (write skew or phantom) when seats are rows; "after I changed my privacy setting, nobody can see the photo I uploaded next" is a recency question across systems.

## 7. When linearizability is needed

From ch. 10, restricted to what matters for application transactions:

| Case | Why | Can you do without? |
|---|---|---|
| Locks, leases, leader election | exactly one holder; two would be split brain | no; use a consensus-backed coordination service, plus fencing tokens |
| Hard uniqueness (username, file path), no-negative balance, no oversell | one up-to-date value all nodes agree on; claiming is a compare-and-set from unset | often yes if you can overbook and compensate; foreign-key and attribute constraints do not need it |
| Cross-channel timing (queue message or notification outruns replication) | a second channel races the storage | yes if you control the channel: pass a version or timestamp in the message and read from the leader or a caught-up replica |

Warning sign: a bug that appears only when two channels race (queue plus store, notification plus fetch, upload plus permission change) points at a missing recency guarantee, not at an isolation level.

## 8. Verify

- For every invariant in the change, classify it: declared constraint, protected by isolation level, protected by lock or atomic op, or unprotected. Report any in the last category.
- Confirm which level the transaction actually runs at (see `anomalies-and-isolation-levels.md` section 2).
- If durability is a requirement, name the mechanism (fsync/WAL setting, number of synchronous replicas, backup retention) rather than saying "the database is durable".
- If the requirement is real-time recency across clients or systems, say so explicitly and check the store provides it (single-leader reading from a verified leader, or a consensus store); do not assume quorum reads give it.
