---
name: arch-replication-and-consistency
description: Reasoning about copies of data and partial failure in distributed systems - replication topologies (single-leader, multi-leader, leaderless), failover, replication-lag anomalies, conflict resolution and quorums, sharding and rebalancing, consistent hashing, clocks and pauses, leases and fencing tokens, linearizability, CAP, consensus, ID generation. Use when designing or reviewing read replicas, multi-region writes, failover, "stale read after write" bugs, shard keys and hot partitions, a Dynamo-style store, leader election or distributed locks, last-write-wins timestamps, or when asked whether you need strong consistency or ZooKeeper/etcd/Raft. Not for single-database isolation levels and race conditions (arch-transactions), nor for workflow sagas across services (arch-distributed-workflows), nor for in-process threads (craft-concurrency).
---

# Replication, sharding and consistency

## Purpose

Use this skill to decide how data should be copied and split across machines, what the application can
and cannot assume about reads, clocks and leaders, and how to check the design against failure. It
changes the work from "pick a database that says it replicates" to naming the guarantee each user flow
needs, choosing the cheapest mechanism that gives it, and producing tests that fail when the guarantee
is broken.

## Choose what applies

| The task or signal | Do this | Read |
|---|---|---|
| "Add read replicas", "scale reads", "which replication mode?" | Section A below | `references/replication-strategies.md` |
| Users see their own edits vanish, content flickers on refresh, replies appear before posts | Name the anomaly, apply its remedy (section B) | `references/replication-lag-anomalies.md` |
| Writes in several regions, offline or collaborative editing, "active-active" | Section C | `references/replication-strategies.md`, `references/conflicts-and-quorums.md` |
| Two writers touch the same record; last-write-wins; shopping cart merge; "w + r > n" | Section C | `references/conflicts-and-quorums.md` |
| One database is too big or too hot; choosing a shard key; hot partition; rebalancing; shard routing; secondary index on a sharded store | Section D | `references/sharding.md` |
| Distributing cache or KV keys over servers; adding nodes causes a miss storm | Consistent hashing, section D | `references/sharding.md` |
| Leader election, "only one worker may run this", distributed lock, lease, singleton job | Section E | `references/locks-leases-fencing.md` |
| Timeouts, retries, clocks, GC pauses, "the network is fine", failure detector tuning | Section F | `references/distributed-failure-assumptions.md` |
| "Do we need strong consistency?", CAP argument, ZooKeeper/etcd/Raft choice, uniqueness across nodes | Section G | `references/linearizability-and-consensus.md` |
| Unique IDs across servers, time-sortable keys, Snowflake, logical timestamps | Section H | `references/ids-and-clocks.md` |
| Designing a distributed key-value store or reviewing Dynamo/Cassandra-style behaviour | Compose A, C, D, F | `references/dynamo-style-store.md` |
| Reviewing an existing design or pull request for any of the above | Run the checklist | `references/review-checklist.md` |

This skill does not apply when:
- The data lives on one node and nothing is replicated or sharded. Do not introduce replication or
  sharding to a service that fits on one machine; note that one machine often suffices.
- The question is which anomalies a single database's isolation level allows (dirty reads, write skew,
  lost updates inside a transaction): use `arch-transactions`. This skill covers when transactions
  cross shards or replicas only as far as routing and consistency are concerned.
- The problem is coordinating steps across services with compensation (sagas, orchestration): use
  `arch-distributed-workflows`.
- The problem is threads, locks and shared memory inside one process: use `craft-concurrency`.
- The question is overall system sizing or a first-pass design from a problem statement: start with
  `arch-system-design`, come here for the replication and sharding depth.
- Storage engines, indexes, encodings: `arch-data-storage`. Streams, CDC, derived data:
  `arch-data-pipelines`.

## How to apply

### Step 0. State the guarantee before the mechanism

For each data class or user flow, write down in one line what a reader may see after a write and what
must never be lost. Use these terms: eventual (the weakest); consistent prefix, monotonic reads and
read-your-writes (separate per-user guarantees, not a strict ladder); causal; linearizable (a recency
guarantee across clients, which subsumes the per-user ones). Also write the
durability promise: "an acknowledged write survives loss of the leader" is yes or no. Most designs need
different answers for different data (a profile edit versus a view counter versus a username claim).

### A. Pick the replication topology

1. Start from need: latency, availability or durability, read scaling, offline use. If none applies, do
   not replicate beyond backups.
2. Default to single-leader. It supports uniqueness, balances and serializable transactions, and is the
   simplest to reason about. Add async followers for read scale.
3. Pick the sync mode by durability need: async if followers are many or far and the last moments of
   writes may be lost; semisync (one synchronous follower, rest async) or majority quorum if an
   acknowledged write must exist on two or more nodes. All-synchronous halts writes whenever one node
   is down.
4. Move to multi-leader or leaderless only for multi-region write latency and outage tolerance, offline
   devices or real-time collaboration. Accept that they cannot enforce unique usernames, non-negative
   balances or non-overlapping bookings.
5. Treat failover as a designed procedure (detect, choose the most up-to-date node, reconfigure, demote
   the old leader), not a feature toggle. See the failure-mode list in `replication-strategies.md`;
   some operators prefer manual failover.
6. Keep backups and point-in-time recovery; replication also copies mistakes.

### B. Make reads honest about lag

For each flow reading from followers, find the anomaly and apply the remedy:

| Symptom | Guarantee | Cheapest remedy |
|---|---|---|
| User's own edit missing after reload | Read-your-writes | Read what the user may have edited from the leader; or leader for N minutes after their last write; or carry a log position and read from a replica that reached it |
| Same, across phone and desktop | Cross-device read-your-writes | Keep last-write position per user centrally; route a user's devices to one region |
| Data goes backward on refresh | Monotonic reads | Pin the user to one replica (hash of user ID) |
| Reply visible before the post | Consistent prefix | Co-locate causally related writes on one shard, or track dependencies |

If the lag could be minutes and that is unacceptable, either pick a store with the guarantee built in or
read from the leader. Do not paper over it in application code.

### C. Writers in several places

1. Prefer avoiding conflicts: route all writes for a record to one home leader.
2. If concurrent writes are possible, choose the resolution by what must not be lost:
   - Updates must not be lost: siblings returned to the app, or a CRDT / OT merge.
   - Data is insert-only or overwriting is truly harmless: last-write-wins, knowing it silently drops
     acknowledged writes and, with wall-clock timestamps, is wrecked by clock skew.
   - Invariants (unique, balance, no overlap): keep a single serialisation point; multi-writer cannot
     do it.
3. Detect concurrency with version numbers (one replica) or version vectors (many). Timestamps cannot
   tell "later" from "concurrent".
4. For quorums: with n replicas, w write acks and r read replicas, w + r > n makes read and write sets
   overlap. That lowers staleness; it does not give linearizability (edge cases: restore from stale
   replica, rebalancing, concurrent read, partial writes, clock skew). See the disagreement note below.
5. Make sure a repair path exists: read repair, hinted handoff, anti-entropy.

### D. Shard only when needed, then choose the key

1. Shard for data volume or write throughput; read throughput alone calls for replicas. Prefer a
   single-shard database while one machine suffices.
2. Choose the scheme by access pattern:

| Need | Scheme | Watch |
|---|---|---|
| Range scans on the key | Key-range | Monotonic keys (timestamps) create a hot shard: prefix with an entity ID |
| Even spread, adjacency irrelevant | Hash of key (hash-range or fixed shard count much larger than nodes) | Range queries scatter; use a compound key with the partition key first |
| Nodes join and leave often | Consistent hashing with virtual nodes (about 100 per server gave a load standard deviation near 10 percent of the mean, 200 near 5 percent, in the interview book's experiment) | A single hot key still lands on one node |
| Per-customer isolation, compliance, residency | Shard per tenant or cell | Large tenants, tiny-tenant overhead |

3. Never use `hash(key) mod N` with changing N (most keys move), and never a per-process built-in hash
   function.
4. Plan for skew: monitor per-shard load, salt known-hot keys (reads then fan out and merge), or give a
   hot key its own shard.
5. Rebalance with a human in the loop; automatic rebalancing plus automatic failure detection can cascade
   when an overloaded node is judged dead.
6. Routing: decide who holds the shard map. Consensus-backed metadata (ZooKeeper, etcd, built-in Raft)
   when each request must reach exactly one owner; gossip only when stale routing is tolerable. Handle
   the cutover while a shard moves.
7. Secondary indexes: local (cheap writes, scatter/gather reads) for write-heavy or partition-key-bearing
   queries; global (single-shard reads, expensive or stale writes) for read-heavy selective lookups.
   Never hand-build an index over a key-value store without atomic multi-object updates.

### E. "Only one" must be enforced at the resource

1. A lease alone is unsafe: a paused or delayed holder (GC, VM stall, packet in flight) can act after
   expiry.
2. Issue a fencing token with each grant (monotonically increasing: ZooKeeper `zxid`, etcd revision, a
   Raft term or log index). The protected resource rejects any token lower than one it has seen, or the
   store offers conditional writes (compare-and-set).
3. Get the lock or election from a coordination service; do not write your own. Procedure in
   `locks-leases-fencing.md`.
4. If a duplicate holder only wastes work, a plain lease is acceptable.

### F. Assume the environment is hostile

- A timeout means "outcome unknown"; make retried operations idempotent. Only an application-level reply
  proves success, not a TCP ack.
- Use monotonic clocks for durations; never decide cross-node order from time-of-day clocks. Monitor
  clock offsets and eject drifting nodes.
- A thread can pause at any line. Do not rely on a check made a moment ago.
- Declare a node dead by quorum, with hysteresis, since false suspicion under overload cascades.
- Test partial and one-way partitions, pauses (`SIGSTOP`) and clock skew, not only clean crashes.
- The practical model is partially synchronous with crash-recovery nodes; safety must hold in all
  cases, liveness only while a majority and the network behave.

### G. Decide whether you need linearizability or consensus

Ask three questions:
1. Is there a hard uniqueness, lock, lease or leader decision that cannot be compensated afterward?
2. Can a second channel (queue message, notification, human) race the store, with no way to pass a
   version through it?
3. Must order respect real time across clients who never talk to each other?

What each replication scheme gives (DDIA 2e ch. 10):

| Scheme | Linearizable? | Condition |
|---|---|---|
| Single leader, reads and writes via the leader | Potentially | The leader must be the real leader: a paused ex-leader still serving breaks it; async failover can lose acknowledged writes |
| Consensus-based (Raft, Zab, Paxos family) | Likely | Reads must confirm leadership (etcd does a quorum round); ZooKeeper reads may be stale unless synced |
| Multi-leader | No | Concurrent writes on several nodes, conflicts resolved afterward |
| Leaderless with w + r > n | Assume not | Edge cases in `conflicts-and-quorums.md`; time-of-day LWW (Cassandra, ScyllaDB) is almost certainly not |

If all answers are no, use weaker guarantees plus compensation or conflict resolution; they give
availability and lower latency. If any is yes, use a single leader that verifies its leadership or a
consensus-backed store (etcd, ZooKeeper, a Raft or Paxos database). The price: the minority side of a
partition is blocked, each operation needs a round trip to a quorum, adding nodes does not add
throughput, and consensus groups stay small (3 or 5, odd). For compare-and-set, locks, unique claims,
shared logs, atomic commit or fetch-and-add that must be fault tolerant, use a consensus service
instead of building one. Do not call a database "CP" or "AP" as a design argument; state what happens
on each side of a partition.

### H. IDs

Decide what ordering the IDs need (none, causal, real-time) and match the scheme: UUID when order is
irrelevant; Snowflake-style 64-bit (time, datacentre, machine, sequence) for sortable keys without
coordination, with clock-regression handling; hybrid logical clocks for causality-consistent
near-wall-clock stamps; version vectors to detect concurrency; a batched single-node generator when
real-time order across clients is required. IDs cannot enforce uniqueness or locks; that needs
consensus.

## Where the sources disagree

- Quorum strength. The system-design book treats W + R > N as strong consistency; the data-systems book
  says to assume leaderless quorum systems are not linearizable. Rule: use W + R > N to reduce
  staleness; if code depends on recency (locks, uniqueness, read after another client's write), use a
  leader or consensus store.
- CAP. One source builds the key-value design on a CP-or-AP choice and states that CA systems cannot
  exist; the other calls CAP of little practical value (narrow definitions, partitions are only some
  faults) and discourages CP/AP labels. Rule: use the CP/AP wording as shorthand for partition
  behaviour in conversation, decide with the section G questions, and describe latency costs too,
  because linearizable operations are slower even without faults.
- Vector clocks versus version vectors: the sources describe the same comparison idea with slightly
  different structures; for comparing replica state use version vectors, and note that Lamport and
  hybrid clocks cannot detect concurrency.

## Verify

Produce evidence, not assertions. For the change in front of you, run or specify as many as apply:

1. Failover drill: kill the leader under write load. Report acknowledged writes missing afterward, which
   replica was promoted and whether it was the most current, and whether the old leader refuses writes
   when it returns.
2. Lag injection: delay follower apply by tens of seconds in a test environment and assert
   read-your-writes (also across devices), monotonic reads and consistent prefix for the flows that
   need them.
3. Pause and delay test for every lease or lock: stop the holder past expiry, let another acquire, resume
   the first, and assert its write is rejected by the resource; hold a write in flight past expiry and
   assert rejection.
4. Partition test, including partial and one-way partitions: state expected behaviour on each side and
   compare.
5. Clock skew test for any last-write-wins or time-ordered path: show which writes are lost and confirm
   that the loss is accepted.
6. Concurrent-write test from two regions or replicas against one key; assert the chosen resolution
   (siblings preserved, CRDT converged).
7. Sharding: load test with skewed keys; report max-to-mean per-shard load and top keys; after adding a
   node report the fraction of keys moved (about the new node's share, 1/(n+1) going from n nodes, for a ring; nearly all for mod N); check replicas land on distinct
   physical nodes; confirm no write reaches the old owner after a shard move.
8. Linearizability claims: run a history checker (Jepsen's Knossos or Porcupine style) under faults.
9. IDs: uniqueness across simulated machines, rollover and sequence overflow, backward clock, unique
   machine IDs.
10. Read the diff against `references/review-checklist.md` and list unanswered questions to the user.

Done means:
- Each data class has a stated guarantee and durability promise, and the mechanism chosen provides it.
- Every read from a follower has a named anomaly status (not affected, or remedy applied).
- Every "only one" has a token or conditional write at the resource.
- No cross-node ordering depends on time-of-day clocks unless loss is accepted and offsets monitored.
- Shard key, scheme, rebalancing and routing choices are written down with the skew and hot-key plan.
- Fault-injection tests exist for failover, partition and pause cases, or their absence is reported as
  a risk.
- Any place the design weakens a source rule is called out to the user in one line.

## Proportion and limits

- Replication and sharding add failure modes. If one machine and a backup meets the load and
  availability target, say so and stop. "A single machine can do a lot nowadays."
- Do not demand linearizability, consensus or fencing for data where a duplicate or stale value is
  harmless; compensation (apologies, overbooking) is often cheaper.
- Do not build a Dynamo, a coordination service or a consensus protocol when a managed one fits. Use
  the references to evaluate and configure, not to reimplement.
- Product behaviours named in the notes (Cassandra, ZooKeeper reads, Kafka options, thresholds like a
  10 GB split size or 16/256 token ranges per node) are as of the books' writing; re-check the current
  docs and test the real system. The definitions (consistency guarantees, safety versus liveness,
  fencing, epochs) are the durable part.
- Items in the notes marked inferred (test ideas, some rules of thumb) are suggestions, not book
  claims; the references carry the same label.
- This skill does not cover the cost of operating these systems (on-call, capacity); see
  `arch-reliability-slos`, `arch-production-operations`.

## References

- `references/replication-strategies.md`: topology comparison, sync modes, follower setup, failover failure modes, log formats, leaderless repair; read for any replica design.
- `references/replication-lag-anomalies.md`: the four read anomalies, remedies, product questions, tests; read when stale reads appear.
- `references/conflicts-and-quorums.md`: conflict strategies, CRDT/OT, version vectors, quorum arithmetic and its limits, sloppy quorums; read for multi-writer designs.
- `references/sharding.md`: key choice, schemes, consistent hashing, hot keys, rebalancing, routing, secondary indexes, multitenancy; read before choosing a shard key.
- `references/distributed-failure-assumptions.md`: networks, timeouts, clocks, pauses, system models, verification techniques, assumption/defence table; read when reasoning about failure.
- `references/locks-leases-fencing.md`: why leases fail, fencing tokens, procedure to add them; read for leader election or singleton jobs.
- `references/linearizability-and-consensus.md`: definition, when needed, CAP debate, consensus, epochs, coordination services; read before choosing strong consistency.
- `references/ids-and-clocks.md`: ID schemes, Lamport/HLC/vector clocks, Snowflake, linearizable generators; read for ID or timestamp design.
- `references/dynamo-style-store.md`: worked key-value store design with every technique and its caveats; read when designing or auditing a Dynamo-style system.
- `references/review-checklist.md`: question list and red-flag phrases for design reviews; read when reviewing.

## Sources

- Designing Data-Intensive Applications 2e ch. 6 (Replication): topologies, lag anomalies, conflicts, leaderless quorums.
- DDIA 2e ch. 7 (Sharding): schemes, rebalancing, routing, secondary indexes, multitenancy.
- DDIA 2e ch. 9 (The Trouble with Distributed Systems): networks, clocks, pauses, fencing, system models.
- DDIA 2e ch. 10 (Consistency and Consensus): linearizability, CAP, ID generators and logical clocks, consensus, coordination services.
- System Design Interview 2e ch. 5 (Consistent Hashing), ch. 6 (Key-Value Store), ch. 7 (Unique ID Generator).
