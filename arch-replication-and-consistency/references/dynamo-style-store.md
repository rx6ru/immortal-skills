# Worked design: a Dynamo-style key-value store

Sources: System Design Interview 2e ch. 6 (key-value store, modelled on Dynamo, Cassandra and
Bigtable) and ch. 5 (consistent hashing), cross-read with DDIA 2e ch. 6 and ch. 10. The interview
book's closing summary table was missing from the extraction and is reconstructed here from its text.
Items marked (inferred) are extrapolations in the study notes.

## Contents
1. Requirements
2. Decisions and the problem each solves
3. Write and read paths
4. Failure handling
5. Where this design is weaker than it looks
6. Adapting it
7. Verification

## 1. Requirements
API: `put(key, value)` and `get(key)`. Small pairs (under 10 KB), big data, high availability (answer
quickly during failures), high scalability, automatic scaling (add and remove servers by traffic),
tunable consistency, low latency. A single-server version is an in-memory hash table; compression and
keeping only hot data in memory stretch it, but capacity runs out, so distribute.

## 2. Decisions and the problem each solves

| Capability | Technique |
|---|---|
| Big data, partitioning, incremental scalability, heterogeneity | Consistent hashing with virtual nodes (counts proportional to capacity); see `sharding.md` |
| Highly available reads | Replication to N servers, across data centres |
| Tunable consistency | Quorum with N replicas, W write acks, R read responses |
| Highly available writes, concurrent updates | Versioning with vector clocks and client-side reconciliation |
| Failure detection | Gossip protocol |
| Temporary failures | Sloppy quorum plus hinted handoff |
| Permanent failures | Merkle-tree anti-entropy |
| Data centre outage | Cross-data-centre replication |

Details:
- Replication is asynchronous to N servers (configurable): from the key's ring position walk clockwise
  and take the first N distinct physical servers, skipping vnodes of an already chosen server. Place
  replicas in different data centres (same-site nodes fail together).
- Quorum: a coordinator proxies between client and nodes. W=1 means the coordinator returns after one
  ack, not that only one copy is written. W+R>N is described as strong consistency (typical N=3, W=R=2);
  R=1 with W=N favours reads; W=1 with R=N favours writes; W+R<=N gives no strong guarantee. Lower W
  and R mean lower latency; higher values mean waiting for the slowest replica. See the caveat in
  section 5.
- Vector clocks: rules and example in `conflicts-and-quorums.md`.
- Failure detection needs at least two independent sources before marking a node down. All-to-all
  multicast is simple but inefficient at scale. Gossip: each node keeps a membership list with
  heartbeat counters, increments its own periodically, and sends heartbeats to random nodes who
  propagate them; a member whose counter has not increased for a set period is offline once other
  nodes confirm.
- Sloppy quorum: for writes take the first W healthy servers on the ring, for reads the first R
  healthy, ignoring offline ones. A stand-in stores the data and pushes it back when the failed node
  returns (hinted handoff).
- Merkle trees: divide the key space into buckets (e.g. 4), hash each key in a bucket, one hash per
  bucket, then hash children upward to the root. Compare roots; if equal the replicas are in sync; if
  not, descend into differing children to find the out-of-sync buckets and sync only those. Data
  transferred is proportional to the difference, not the data size. Real configurations: about 1
  million buckets per 1 billion keys (1,000 keys per bucket).

## 3. Write and read paths
Architecture: clients call get/put against any node, which acts as coordinator; nodes sit on a
consistent-hash ring; the system is decentralised so adding and removing nodes is automatic; data is
replicated on several nodes; there is no single point of failure because every node has the same
responsibilities (client API, failure detection, conflict resolution, repair, replication, storage).

Write path (Cassandra-like): 1) persist to the commit log; 2) save to the in-memory cache (memtable);
3) when memory fills or a threshold is reached, flush to an SSTable on disk (a sorted list of key-value
pairs).

Read path: check the memory cache; on a hit return it. On a miss use a Bloom filter to find which
SSTables might contain the key, read those, and return the result (caching it, per the standard
design). Storage-engine detail: `arch-data-storage`.

## 4. Failure handling summary
- Node unreachable briefly: sloppy quorum keeps writes flowing; hinted handoff repairs afterward.
- Node gone for good or replicas diverged: Merkle anti-entropy converges them.
- Data centre outage: replicas in other data centres serve reads.
- Divergent concurrent writes: vector clocks surface siblings; the client reconciles.

## 5. Where this design is weaker than it looks
- Quorum strength: DDIA warns that W+R>N does not give linearizability (see
  `conflicts-and-quorums.md` section 8). Do not use this store for locks, uniqueness or balances.
- Vector clock growth and client burden: cap length and drop oldest pairs; every client needs
  reconciliation logic. Last-write-wins is simpler but silently loses writes (the interview book does
  not discuss LWW; inferred) and depends on clocks (`distributed-failure-assumptions.md`).
- Gossip-based membership is weakly consistent: different nodes may disagree on membership. That is
  acceptable here because the data layer is already eventually consistent
  (`sharding.md`, routing table).
- Sloppy quorums trade the overlap guarantee for availability.

## 6. Adapting it
Decision guide from the chapter: strict correctness (money, inventory counts): choose CP, W+R>N,
accept unavailability on partition (or, better per DDIA, use a single-leader or consensus-backed
database). Always-on writes (carts, profiles): AP, eventual consistency, vector clocks or LWW (the LWW option
is the notes' inference, not the chapter's).
Read-heavy: R=1, W=N. Write-heavy: W=1, R=N. Prefer an existing database in this family over building
one unless the requirement is to study the design.

## 7. Verification (inferred)
- Property tests on vector-clock comparison (ancestor, descendant, conflict).
- Chaos test: kill nodes mid-write; confirm hinted handoff delivers after recovery and Merkle repair
  converges replicas.
- Configuration check: W+R>N on paths that need freshness; N, W, R written down per data class.
- Placement check: replicas of a key on distinct physical nodes and distinct data centres or racks.
- Staleness check: measure how long after a write all replicas agree (the practical meaning of
  "eventual" here).
