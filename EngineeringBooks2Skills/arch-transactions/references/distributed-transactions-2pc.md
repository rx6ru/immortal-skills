# Distributed transactions and two-phase commit

Source: DDIA 2e ch. 8 section on distributed transactions and atomic commit; DDIA 2e ch. 10 (atomic commit as a face of consensus); Architecture: The Hard Parts ch. 9 (what a business request across services loses). Sagas, compensation and the eight saga patterns live in `arch-distributed-workflows`.

## Contents
1. When a transaction is distributed
2. Why naive commit fails
3. Two-phase commit: protocol, two points of no return
4. Coordinator failure and in-doubt participants
5. Blocking, three-phase commit, consensus
6. Database-internal vs heterogeneous (XA) transactions
7. XA problems in detail
8. What NewSQL systems fix
9. Atomic commit versus consensus
10. When a request spans services (ACID vs BASE)
11. Decision rules
12. Verify

## 1. When a transaction is distributed

A transaction is distributed when more than one node takes part: several shards, a global secondary index on another node, or several different systems. Single-leader replication is not distributed in this sense (the transaction runs on the leader; followers apply the log).

Concurrency control (serial execution per shard, 2PL, distributed SSI conflict checks) extends in broadly similar ways. The new problem is atomic commit: all participants commit or all abort.

## 2. Why naive commit fails

On a single node, the data is written durably to the log first and then a commit record is appended; the moment the commit record reaches disk is the decision. Before it, a crash rolls back; after it, the transaction is committed. One device makes it atomic, and the order (data, then commit record) matters.

"Send commit to every node" fails because some nodes hit a constraint violation or conflict and abort, some commit requests are lost and time out, and some nodes crash before the commit record is durable. The result is inconsistency, and a commit cannot be retracted because other transactions may already have seen the data.

## 3. Two-phase commit (2PC)

Not 2PL. Used inside some databases and exposed to applications as XA (Java JTA) or WS-AtomicTransaction.

Roles: a coordinator (transaction manager; often a library in the application process, or a separate service) and participants (the database nodes).

Protocol:
1. The application asks the coordinator for a globally unique transaction ID.
2. The application starts an ordinary single-node transaction on each participant, tagged with that ID, and does all reads and writes there. A failure here lets the coordinator or any participant abort.
3. Commit, phase 1: the coordinator sends PREPARE (with the ID) to all participants. If any fails or times out, the coordinator sends ABORT to all.
4. A participant that gets PREPARE must be certain it can commit under all circumstances: write all data to disk (crash, power loss and a full disk are no excuse later) and check conflicts and constraints. Replying yes is a promise to commit if told to, and it surrenders the right to abort. First point of no return.
5. The coordinator collects the votes; it decides commit only if all said yes, and writes that decision to its own durable log. This is the commit point and the second point of no return.
6. Phase 2: the coordinator sends COMMIT or ABORT to all, retrying forever if it fails or times out. A participant that crashed commits on recovery, since it voted yes and cannot refuse.

Single-node commit merges the two points of no return into one log write; 2PC separates the participant's promise from the coordinator's decision. The extra fsyncs and network round trips are its general cost.

## 4. Coordinator failure and in-doubt participants

- A participant can abort safely any time before it votes yes.
- After voting yes it is in doubt (uncertain): it cannot abort alone (the coordinator may have decided commit and others committed) and cannot commit alone (another participant may have aborted). It can only wait. Timeouts do not help. Participants asking each other is not part of 2PC.
- On recovery the coordinator reads its log; transactions without a commit record are aborted. So the commit point reduces to an ordinary single-node atomic commit on the coordinator.
- If the coordinator's log disk is lost, an administrator must resolve manually. If only the tail of the log is lost, the coordinator may abort transactions that were already committed, which violates atomicity.

## 5. Blocking, three-phase commit, consensus

- 2PC is a blocking atomic commit protocol: it is stuck until the coordinator recovers.
- Three-phase commit is nonblocking but assumes bounded network delay and bounded process pauses; in real systems with unbounded delays and pauses it cannot guarantee atomicity. The notes call it mostly theoretical.
- The practical fix: replace the single-node coordinator with a fault-tolerant consensus protocol (see `arch-replication-and-consistency`).

## 6. Database-internal vs heterogeneous

| | Database-internal | Heterogeneous (XA) |
|---|---|---|
| Participants | same database software across shards or replicas (YugabyteDB, TiDB, FoundationDB, Spanner, VoltDB, Cassandra, MySQL NDB Cluster, CockroachDB; Kafka internally) | different technologies: databases from different vendors, message brokers |
| Protocol freedom | any protocol, with tailored optimizations | lowest common denominator (XA) |
| Reputation | work quite well | operational problems, poor performance, promise more than they deliver; many cloud services refuse to offer them |

## 7. XA problems in detail

- XA (X/Open, 1991) is a C API for talking to a coordinator, not a network protocol; the Java binding is JTA through JDBC and JMS drivers. Supported by PostgreSQL, MySQL, Db2, SQL Server, Oracle and brokers (ActiveMQ, HornetQ, MSMQ, IBM MQ).
- The coordinator is usually a library in the application process with its log on the application server's local disk. If the host dies, prepared participants are stuck in doubt until the application server restarts and the library rereads the log. The database cannot contact the coordinator directly; all communication goes through the client library.
- Locks held while in doubt. A prepared transaction keeps its row locks (exclusive for writes, shared for reads under 2PL) until resolved. A 20-minute coordinator outage means 20 minutes of locks; a lost log means locks forever until manual resolution. Others touching those rows are blocked, possibly even for reads, making large parts of the application unavailable.
- Orphaned in-doubt transactions occur in practice (log lost or corrupted by a bug). They cannot be auto-resolved, and even a database reboot does not clear them, since correct 2PC preserves the locks across restart. Only an administrator can resolve them: examine every participant, find whether any committed or aborted, apply the same outcome to the rest, under pressure during an outage.
- Heuristic decisions are XA's escape hatch: a participant unilaterally commits or aborts an in-doubt transaction. This is a euphemism for probably breaking atomicity; emergency use only.
- Structural limits: the coordinator and its disk log are a single point of failure as critical as the databases; the application is a single point of failure even if the coordinator is replicated; lowest-common-denominator means no cross-system deadlock detection; incompatible with SSI (no cross-system conflict detection protocol).

## 8. What NewSQL systems fix

Many databases use 2PC for multi-shard writes without XA's problems because their designers control the whole stack:
1. Replicate the coordinator with automatic failover.
2. Coordinator and shards talk directly, with no application code in between.
3. Replicate the participating shards so a shard fault is less likely to force an abort.
4. Couple atomic commit with distributed concurrency control (deadlock detection, consistent reads across shards).

Consensus is the usual tool for replicating the coordinator and shards. Isolation levels vary by system; snapshot isolation and SSI across shards are both possible.

## 9. Atomic commit versus consensus

Consensus accepts any proposed value. Atomic commit must abort if any participant voted abort, though it may abort on timeouts. Consensus-based commit: everyone sends their vote to all; propose commit only if all voted commit; run consensus. In consensus any node can start an election and a quorum suffices; in 2PC only the coordinator asks for votes and it needs all participants to say yes. Consensus-based commit removes the single point of failure.

## 10. When a request spans services (ACID vs BASE)

Each service's own database can be ACID. A business request that spans services is a distributed transaction and the request as a whole is not ACID:
- Atomicity is bound to each service, not to the request.
- Consistency: a failure in one service leaves tables out of sync; foreign keys cannot be enforced across separate commits.
- Isolation: data committed by one service is visible to everyone before the whole request completes.
- Durability holds per service only.

BASE (basic availability, soft state, eventual consistency) is the label for this regime; "soft state" means the in-progress state of the business request is unknown and is hard to determine under async or parallel workflows. The Hard Parts example: customer 123 unsubscribes; the profile service deletes its row and confirms, but contract and billing rows remain, so the data is out of sync.

Consequence for design: before choosing a pattern across services, state which operations need atomicity (and so a shared transaction boundary, perhaps by merging services or owning the data in one service) and which can live with eventual consistency (events, orchestration with compensation, background sync). The patterns and their trade-off tables are in `arch-distributed-workflows` (eventual-consistency patterns and sagas); data ownership rules are there too. Table-level fact worth keeping here: the service that writes a table owns it, and a business operation whose pieces need one atomic transaction is a reason to co-locate those pieces in one service and one database.

## 11. Decision rules

| Need | Choose |
|---|---|
| Multi-shard atomicity | a database with internal distributed transactions (coordinator replicated, shards replicated, direct communication) |
| Atomicity across two different vendors' databases, or database plus broker | avoid XA; use a local transaction plus idempotent consumer (`retries-and-idempotency.md`), or a pattern from `arch-distributed-workflows` |
| Several writes that must be atomic and are inseparable | keep them in one service and one database transaction |
| Exactly-once between broker and database, both supporting the protocol | acknowledge only if the transaction committed, abort both together; expect cost and operational risk |
| Fault-tolerant coordinator wanted | consensus-based commit or a database that already provides it, not a hand-built coordinator |

Do not build your own two-phase protocol. The failure analysis above (in-doubt state, durable logs, forever-retry in phase 2) is why.

## 12. Verify

- List every place the code writes to two systems in one logical operation (two databases; database plus queue; database plus external API). For each, name the mechanism that keeps them consistent: one transaction, XA, idempotent consumer, outbox, saga. If the answer is "hope", flag it.
- If XA is in use: find where the coordinator log lives, whether it is on durable replicated storage, and what the runbook says for orphaned in-doubt transactions and heuristic decisions. Check for monitoring of prepared transactions that stay open (adaptation: PostgreSQL exposes prepared transactions in a system view; check the equivalent in the engine in use).
- Fault-inject a coordinator crash between prepare and commit in a test environment; observe lock hold time and who is blocked (inferred test from the notes).
- For cross-service business requests, document: consistency model (ACID inside a service, BASE across), the compensation for each step, and the maximum staleness window; test failure in every participant, including failure of a compensating action.
