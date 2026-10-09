# Linearizability, CAP, and consensus: do you need them, and what they cost

Sources: DDIA 2e ch. 10 (parts A and B), ch. 9 (leases), ch. 6 (failover); System Design Interview 2e
ch. 6 (CAP). Items marked (inferred) are extrapolations in the study notes. Tech-specific behaviours
(ZooKeeper, etcd, Cassandra, Kafka) may be dated; the principles are durable.

## Contents
1. Two philosophies
2. Linearizability: definition and test
3. Linearizability vs serializability
4. When you actually need it
5. Which replication schemes are linearizable
6. Cost, CAP, and the two books' disagreement
7. Decision guide
8. Consensus: properties, equivalent problems
9. How consensus runs a replicated service: epochs and quorums
10. Costs of consensus
11. Coordination services
12. Anti-patterns
13. Verification

## 1. Two philosophies

| | Eventual consistency | Strong consistency |
|---|---|---|
| Idea | Replication is visible to the app; the developer handles inconsistencies and conflicts | System behaves as one node; app need not know about replication |
| Typical | Multi-leader, leaderless | Single-leader with strong guarantees, consensus-based |
| Pros | Tolerates faults and partitions that strongly consistent systems turn into outages; works offline | Simpler for the developer |
| Cons | Hard for applications | Performance cost; some faults become outages |
| Pick when | Users edit offline (local-first) | Replicas in datacentres with fast reliable links, cost acceptable |

These topics are notoriously hard to implement; systems that behave fine without faults often collapse
under unlucky combinations of faults or message orderings.

## 2. Linearizability: definition and test

The system appears as if there is one copy of the data and every operation takes effect atomically at
one instant (its linearization point) between its start and end. It is a recency guarantee: a read
returns the most recent value, never from a stale cache or replica. Other names: atomic consistency,
strong consistency, immediate consistency, external consistency.

Rules (for a register: a key, row or document with read, write and compare-and-set):
- Reads that finished before a write began return the old value; reads that start after it finished
  return the new one; reads concurrent with the write may return either.
- Recency constraint: once any read returns the new value, every later read, by any client, must
  return the new value, even if the write has not completed. Otherwise values flip old, new, old.
- Operation order need not match send order, only real-time order for non-overlapping operations.
  A response can be delayed after the effect.
- The model has no transaction isolation; others can change values at any time. Use compare-and-set.

Example of a violation: Aaliyah reloads, sees the final score, tells Bryce; Bryce reloads after hearing
her and hits a lagging replica that shows the game in progress. Simultaneous reloads differing would be
fine; the violation is that his request began after hers completed. This is cross-client and ordered in
real time, unlike the per-client guarantees in `replication-lag-anomalies.md`. Linearizability is the
strongest consistency model in common use and subsumes read-after-write, monotonic reads and
consistent prefix.

Testing a claim: record request and response timestamps and check whether a valid sequential order
exists. Computationally expensive (Jepsen's Knossos; Elle for isolation anomalies).

## 3. Linearizability vs serializability

| | Serializability | Linearizability |
|---|---|---|
| Is a | Isolation level for multi-object transactions | Recency guarantee on single objects |
| Guarantees | Outcome as if transactions ran in some serial order (may differ from real time) | If A finished before B started, B sees state at least as new |
| Prevents write skew and phantoms | Yes | No |
| Allows stale reads | Yes | No |

Both together are strict serializability. Single-node databases are typically both. Spanner and
FoundationDB are strictly serializable; CockroachDB is serializable with some recency guarantees but
not strictly serializable. Consistency model and isolation level can be chosen mostly independently.
Isolation details: `arch-transactions`.

## 4. When you actually need it

| Use case | Why | Can you avoid it? |
|---|---|---|
| Locks and leader election | Exactly one holder; two holders is split brain | No; use ZooKeeper or etcd (consensus). Still fence |
| Hard uniqueness (username, email, path), non-negative balance, no oversell, single seat booking | Needs one up-to-date value all agree on; claiming a username is a compare-and-set from unset | Often, if interpreted loosely: overbook then compensate. Foreign-key and attribute constraints do not need it |
| Cross-channel timing | A second channel (queue, notification, a person) outruns replication. Video written to a file store, transcode job enqueued, transcoder reads a stale replica | Yes if you control the channel: pass a version or timestamp in the message, read from the leader. Linearizability is simplest, not the only answer |

Facts: ZooKeeper has linearizable writes but reads may be stale (served by any replica) unless synced;
etcd v3 gives linearizable reads by default. Oracle RAC uses a linearizable lock per disk page and so
needs a dedicated interconnect.

## 5. Which replication schemes are linearizable

| Scheme | Linearizable? | Conditions |
|---|---|---|
| Single-leader, all reads and writes via the leader | Potentially | Only if the leader is really the leader; a delusional paused ex-leader breaks it. Async replication plus failover can lose committed writes. Per-shard leaders are fine (single-object guarantee) |
| Consensus-based (Raft, Zab, Paxos family) | Likely | Not automatic: a node that serves reads without confirming it is still leader (no quorum round or lease) can be stale just after an election; etcd does a quorum round |
| Multi-leader | No | Concurrent writes on several nodes, async replication |
| Leaderless (w + r > n) | Assume not | Time-of-day LWW (Cassandra, ScyllaDB) is almost certainly not. Even with correct quorums: a write to n=3, w=3 in flight; reader A sees the new value on one of two nodes (1), later reader B hits two old nodes (0) though B started after A finished |

Making Dynamo quorums linearizable costs performance (synchronous read repair; writer reads the latest
timestamp from a quorum first). Riak skips synchronous read repair; Cassandra waits for read repair
on quorum reads but loses linearizability to time-of-day timestamps. Even then it covers read/write
registers only; compare-and-set needs consensus. Safest assumption: a leaderless Dynamo-style system is
not linearizable.

## 6. Cost, CAP, and the disagreement between the books

Scenario: network partition between regions. Multi-leader regions keep working and sync later.
Single-leader: clients that can only reach a follower region cannot write or do linearizable reads.
In general: need linearizability and replicas disconnected means they wait or error (unavailable, "CP");
do not need it and each replica serves independently (available, not linearizable, "AP").

The books differ in framing:
- System Design Interview ch. 6: you cannot have all of consistency, availability and partition
  tolerance; partitions are unavoidable, so "CA" systems cannot exist and the real choice during a
  partition is CP or AP (CP: block writes to avoid divergence, e.g. banks; AP: keep accepting reads and
  writes, possibly stale, and sync after healing). It then chooses AP for a key-value store.
- DDIA 2e ch. 10: CAP covers only linearizability and only network partitions (Google data: partitions
  cause under 8 percent of incidents); it says nothing about delays, dead nodes or other models. "Pick
  two of three" misleads because partitions are faults, not choices. Correct phrasing: either
  consistent or available when partitioned; with a healthy network you get both. CP/AP labels are
  flawed (formal "availability" differs from everyday meaning; many fault-tolerant systems fail CAP's
  definition; some are neither), so stop labelling databases CP or AP. PACELC (partition: A vs C; else
  latency vs consistency) inherits the same definitional problems.

How to use both: the interview framing is a quick way to state a behaviour during partitions to a
non-specialist. For design decisions, ask the questions below instead of the label.

The real reason most systems drop linearizability is performance: multi-core RAM is not linearizable
either; and the response time of linearizable reads and writes is at least proportional to the
uncertainty of network delay (Attiya and Welch), so linearizable systems are slower all the time, not
only during faults.

## 7. Decision guide: do I need linearizability?

Choose it (single leader with verified leadership, or a consensus-backed store) when:
1. You enforce a uniqueness, lock, lease or leader decision that cannot be compensated later.
2. A second channel can race the storage and you cannot pass versions through it.
3. A counter or ID must respect real-time order across clients who never communicate (a privacy change
   followed by an upload).

Accept weaker (causal, read-your-writes, eventual plus conflict resolution) when:
- the constraint can be violated and compensated (overbooking, apology workflow);
- you need multi-region write availability or low latency;
- only per-session guarantees are needed.

What you give up for it: availability on the minority side of a partition, latency (cross-region round
trip or quorum round per operation), throughput scaling (adding nodes does not help), and simple
multi-leader topologies.

## 8. Consensus

Many problems that are easy with one node and hard when fault tolerant are one problem: consensus.
These are fault-tolerant single-leader failover without split brain, a linearizable ID generator, and
compare-and-set for locks and uniqueness. Algorithms: Viewstamped Replication, Paxos (Multi-Paxos in
production), Raft, Zab. They assume non-Byzantine nodes. (Byzantine-tolerant consensus for blockchains
tolerates fewer than 1/3 faulty nodes; out of scope.)

FLP: no deterministic algorithm in the fully asynchronous model (no timeouts) can guarantee
termination if a node may crash. With timeouts or randomness consensus is solvable in practice. It
says "cannot always terminate", not "cannot agree".

Single-value consensus properties:
- Uniform agreement: no two nodes decide differently. (safety)
- Integrity: a node never changes its decision. (safety)
- Validity: the decided value was proposed by someone. (safety)
- Termination: every non-crashed node eventually decides. (liveness)
A dictator node satisfies the first three trivially; the difficulty is termination under failures,
which needs a majority functioning. Safety holds even if a majority fails or the network is awful; an
outage stops progress but cannot corrupt.

### The equivalent problems

| Formulation | Relation to consensus | Consensus number |
|---|---|---|
| Compare-and-set | Consensus from CAS: CAS(null, myValue), decided value is the register. CAS from consensus: run consensus on proposed new values; losers get an error | Infinity |
| Shared log (total order broadcast) | Consensus from log: first entry is the decision. Log from consensus: one instance per slot, propose in the earliest undecided slot, retry later if lost | Infinity |
| Fetch-and-add | From CAS: read, CAS(v, v+1), retry. To consensus works only for 2 proposers | 2 |
| Atomic commit | Propose commit only if all voted commit; abort on any abort vote or timeout | Infinity |

Atomic commit vs consensus: consensus accepts any proposed value; atomic commit must abort if any
participant voted abort, though it may abort on timeouts. 2PC's coordinator is a single point of
failure; consensus-based commit removes it. In consensus any node can start an election and needs only
a quorum; in 2PC only the coordinator asks for votes and needs every participant to say yes
(`arch-transactions`, 2PC file).

Uses of a shared log: state machine replication (the basis of event sourcing and database
replication); serializable transactions as deterministic stored procedures run in log order;
adapting to other problems (first entry wins for compare-and-set; per-seat consensus; fetch-and-add as a
sum of entries; fencing token as the entry's sequence number, as ZooKeeper's `zxid`). Sharded
strongly consistent databases usually run a log per shard, which scales but limits cross-shard
guarantees (consistent snapshots, foreign keys).

## 9. From single-leader to consensus: epochs
Manual failover violates termination and costs downtime. Consensus automates leader election and
escapes the circularity (a leader is needed for consensus, consensus for a leader) with epoch numbers
(Paxos ballot, VR view, Raft term): at most one leader per epoch, and a higher epoch wins a conflict.
1. A node that has not heard from the leader within a timeout starts an election with a higher epoch.
2. Vote 1: a quorum elects the leader (a node votes yes only if unaware of a higher-epoch leader).
3. Vote 2: for each log entry the leader gets quorum approval and confirms no higher-epoch leader
   exists; the entry is replicated synchronously to a quorum before the client is acknowledged.
4. The two quorums must overlap, so a successful proposal vote includes someone from the latest
   election. Quorums are usually, not always, majorities.
Subtleties: the new leader must honour entries the old leader may have committed (Raft only elects a
node whose log is at least as up to date as a majority; Paxos lets any node lead but it must first catch
up). Linearizable reads must go through a quorum round. Membership changes are an extension.

Unclean leader election (Kafka's option to let a stale replica lead) buys availability and fast
recovery but may overwrite already-written entries; drop the up-to-date requirement and "the theory of
consensus no longer applies".

## 10. Costs of consensus
Pros: single-leader replication done right: automatic failover, no lost committed data, no split brain
even with the ch. 9 faults. Any automatic failover without a proven consensus algorithm is likely
unsafe. It guarantees nothing about the rest of the system.

Costs:
- A strict majority is required: 3 nodes tolerate 1 failure, 5 tolerate 2.
- Every operation needs a quorum round trip; more nodes lower speed rather than raising throughput.
- The minority side of a partition is blocked.
- It relies on timeouts: too large slows recovery, too small causes spurious elections and flapping.
- Raft with one flaky link can bounce leadership repeatedly (mitigated by pre-vote); EPaxos is a
  leaderless variant more robust to slow nodes and links.

## 11. Coordination services (ZooKeeper, etcd, Consul)
Small, in-memory (durable on disk), slow-changing data replicated by consensus, for coordinating other
systems (Kubernetes uses etcd; Spark and Flink high availability use ZooKeeper). Fixed membership of 3
or 5 nodes serves thousands of clients; do not run consensus across thousands of data nodes.

| Feature | Needs consensus? | Notes |
|---|---|---|
| Locks and leases | Yes | One acquirer wins |
| Fencing tokens | Yes | Monotonic per log entry: `zxid`/`cversion`, etcd revision |
| Failure detection | No | Session heartbeats; ephemeral nodes released on timeout |
| Change notifications | No | Watches avoid polling |

Fit:
- Leader election for single-leader databases and job schedulers: good.
- Shard-to-node assignment: good (atomic operations, ephemeral nodes, notifications) when changes take
  minutes to hours; use libraries such as Apache Curator.
- Configuration: not required, convenient if the service exists; polling a file or URL also works.
- Fast-changing state (thousands per second): not suitable; use a regular database or Apache BookKeeper.
- Service discovery: often overkill; it needs availability and speed, not linearizability. Prefer
  caching (TTL, DNS-style). ZooKeeper observers serve stale reads and remain available in partitions.

Summary rule: if you need compare-and-set, a lock or lease, a uniqueness constraint, a shared log,
atomic commit or fetch-and-add fault tolerantly, use a coordination service or consensus database
instead of rolling your own. When not needed, use leaderless or multi-leader replication with logical
clocks and accept weaker consistency.

## 12. Anti-patterns
- "We use quorums so reads are strongly consistent."
- LWW with wall-clock timestamps described as ordered.
- Assuming ZooKeeper reads return the latest value without a sync.
- Home-grown failover (heartbeat plus promote) without epochs or fencing.
- A leader serving reads on a local belief of leadership without a quorum or lease check.
- Unclean leader election enabled when durability matters.
- An even number of consensus nodes (inferred: 4 tolerates the same failures as 3), consensus across
  hundreds of nodes, or a cross-region quorum with tight timeouts (inferred).
- A coordination service used as a general database or for high write rates.
- Lamport, HLC or UUIDv7 IDs treated as proof of real-time order or used to enforce uniqueness.
- Trying to shard a linearizable ID generator.

## 13. Verification
- Linearizability: run a history checker (Knossos- or Porcupine-style) under fault injection; confirm
  reads after a completed write never return older values, including after a leader change.
- Every lease-protected write carries a fencing token and the resource rejects lower ones (inferred).
- Quorum sizing: a majority of an odd number; timeouts above p99.9 network round trip plus pause
  (inferred from ch. 9).
- Cross-channel race: a test that writes, immediately enqueues a message, and has the consumer read
  through a lagging replica; the read must still see the data.
