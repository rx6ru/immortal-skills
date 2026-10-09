# Conflicts, concurrency detection and quorums

Sources: DDIA 2e ch. 6 (conflicts, quorums, detecting concurrent writes), ch. 9 (LWW trap), ch. 10
(leaderless and linearizability); System Design Interview 2e ch. 6 (N/W/R, vector clocks). Items marked
(inferred) are extrapolations in the study notes.

## Contents
1. What "concurrent" means
2. Conflict strategies and when each is acceptable
3. Merge rules by datatype; OT vs CRDT
4. Subtle conflicts (invariants)
5. Detecting concurrency: version numbers and version vectors
6. Quorums: arithmetic, tuning, and where they do not hold
7. Sloppy quorums
8. The two books disagree on quorum strength
9. Verification

## 1. Concurrent

Two writes are concurrent when neither was aware of the other when made. It is not about wall-clock
overlap: a slow or interrupted network can make events far apart in time still concurrent. For any two
operations A and B, exactly one holds: A happened before B (B knows about or builds on A), B happened
before A, or they are concurrent. Causally ordered writes: the later one overwrites the earlier.
Concurrent writes: a conflict that must be resolved. A last-write-wins timestamp cannot distinguish
"later" from "concurrent".

## 2. Strategies

| Strategy | How | Cost or failure mode |
|---|---|---|
| Conflict avoidance | Route all writes for a record to the same leader (user's home region); odd/even ID generators per leader | Breaks when the designated leader changes (failure, user moves); impossible for offline clients |
| Last write wins (LWW) | Highest timestamp wins; ties broken by comparing values | Concurrent write order is effectively random; acknowledged writes silently discarded; with time-of-day clocks a fast-clock node's old write beats a later one. Acceptable only for insert-only or immutable-key data; logical clocks fix the skew part |
| Siblings with manual resolution | Keep all concurrent values (CouchDB-style); return them all on read; application or user merges and writes back | Set-valued API; burden on developer; naive merge hazards (below) |
| Automatic convergent merge | Merge function so replicas that saw the same writes reach the same state in any order ("strong eventual consistency") | Needs datatype-aware merge; cannot enforce constraints such as a maximum list length |

Sibling-merge hazards: a union merge of two shopping carts resurrects items that one side removed
(a Book and DVD reappear); concurrent resolvers can create new conflicts (B/C vs C/B merging into
B/C/C/B).

Decision rule: avoid conflicts if the design allows. If updates must not be lost, use siblings, CRDTs
or OT, not LWW. For invariants (uniqueness, balances, bookings) use single-leader or serializable
transactions.

LWW and clocks (DDIA ch. 9): a client writes x=1 at node 1 with timestamp 42.004; another increments
to x=2 at node 3 whose clock is 3 ms behind, giving 42.003. Node 2 keeps x=1 and drops the increment,
from skew under 3 ms. Fix: give each overwrite a timestamp greater than the value it replaces, which
needs an extra read. Cassandra and ScyllaDB skip it and use client-clock timestamps. Consequences:
writes silently disappear (a lagging-clock node cannot overwrite a faster-clock node's value until the
skew elapses, with no error); LWW cannot separate quick sequential writes from concurrent ones; ties
need tiebreakers that can also violate causality.

## 3. Datatype merge rules; OT and CRDTs

| Type | Merge rule |
|---|---|
| Text | Track inserted and deleted characters; deterministic order for same-position inserts |
| Set or list | Track insertions and deletions (the cart merge gives only Soap when the removals are tracked) |
| Counter | Track increments and decrements per replica and sum |
| Map | Merge per key with the value type's rule; keys are independent |

Two algorithm families:
- Operational transformation (OT): operations carry indexes; an operation is transformed against
  concurrently applied ones (insert at index 3 becomes index 4 after a character is inserted at
  index 0). Used in Google Docs-style real-time editing and ShareDB.
- CRDTs: each element has a unique immutable ID; operations say "insert after element X" (nil for the
  start); concurrent inserts at the same place are ordered by ID; no transformation needed. Present
  in Redis Enterprise, Riak, Azure Cosmos DB, Automerge, Yjs. Hybrids exist.

## 4. Subtle conflicts

Obvious: the same field set to two values. Subtle: a meeting room booked twice, where two inserts
each pass the availability check at their own replica but together violate "no overlap". There is no
easy merge for these; they need a single serialisation point (`arch-transactions`; for enforcing
constraints over derived data see `arch-data-pipelines`).

## 5. Detecting concurrency

### One replica, version numbers (shopping cart walk-through)
1. The server increments a per-key version on each write and stores it with the value.
2. A client must read before writing. The read returns all non-overwritten values (siblings) and the
   latest version number.
3. The write carries the version from the prior read and a value merging all siblings read. The
   response returns the remaining siblings so writes can chain.
4. The server overwrites all values with version less than or equal to the write's version and keeps
   higher-version values (they are concurrent).
A write with no version is concurrent with everything and overwrites nothing. The server never
interprets values.

### Many replicas, version vectors
Keep a version number per replica and per key; each replica also tracks versions it has seen from
others. The set of versions is a version vector (Riak 2.0's dotted version vectors, called causal
context). It travels to clients on read and back on write, so it is safe to read from one replica and
write to another; siblings may appear, and nothing is lost if merged correctly. Version vectors and
vector clocks differ subtly; version vectors are the right structure for comparing replica state.

### Vector clock comparison (System Design Interview ch. 6)
A vector clock is a set of [server, counter] pairs. On a write via server Si, increment its counter or
add [Si, 1]. X is an ancestor of Y (no conflict) if every counter in Y is at least the matching counter
in X. They conflict if some counter is lower in one and higher in the other. Example: D3
[(Sx,2),(Sy,1)] and D4 [(Sx,2),(Sz,1)] conflict; the client resolves and writes D5
[(Sx,3),(Sy,1),(Sz,1)]. Downsides: the client must implement resolution; vector size grows, so cap
its length and drop the oldest pairs (this can blur ancestry; Dynamo reported no problem in
production).

Lamport and hybrid logical clocks cannot tell concurrent from ordered; use vectors when you must
detect concurrency (`ids-and-clocks.md`).

## 6. Quorums

Parameters: n replicas per value, w write acknowledgements required, r replicas queried per read.
When w + r > n, the read and write sets overlap in at least one node, so a read normally sees the
latest successful write. Typical: n odd (3 or 5), w = r = ceil((n+1)/2).
- n=3, w=2, r=2 tolerates 1 unavailable node; n=5, w=3, r=3 tolerates 2.
- Requests go to all n replicas; w and r are how many replies you wait for. Not reaching w or r is an
  error.
- Read-heavy: w = n, r = 1 gives fast reads, but one failed node blocks all writes.
- w + r <= n: lower latency and higher availability, more stale reads.
- Quorums need to overlap, not to be majorities. A cluster can have more than n nodes (sharded), each
  value on n of them. In practice quorums rarely exceed 4 of 7 or 5 of 9.

### Where w + r > n still does not guarantee freshness
- A node with the new value fails and is restored from a replica holding an old value, leaving fewer
  than w copies of the new value.
- Rebalancing or shard moves leave nodes disagreeing on who the n replicas are; quorums stop
  overlapping.
- A read concurrent with a write may or may not see it; one read can see new and the next old.
- A write that succeeded on fewer than w replicas is not rolled back, so a "failed" write can still be
  read later.
- Wall-clock timestamps (Cassandra, ScyllaDB): a fast-clock node's writes silently win.
- Concurrent writes processed in different orders on different replicas.
Treat w and r as tuning the probability of stale reads, not as a guarantee. Dynamo-style databases
suit use cases that tolerate eventual consistency.

### Monitoring staleness
Leader-based: lag is leader position minus follower position, easy. Leaderless: there is no fixed
order, so staleness is hard to measure; hint counts are a weak signal. Quantify "eventual" for
operability.

## 7. Sloppy quorums
Any reachable node accepts the write even if it is not one of the key's n home replicas (Riak/Dynamo;
consistency level ANY in Cassandra/ScyllaDB). A stand-in node stores the data and hands it back when
the home node returns (hinted handoff). Availability improves; there is no guarantee later reads see
the value. In System Design Interview ch. 6 the design instead takes the first W healthy servers on
the ring for writes and first R healthy for reads.

## 8. The two books disagree on quorum strength

System Design Interview ch. 6 states that W + R > N gives strong consistency (typical N=3, W=R=2).
DDIA 2e ch. 10 says to assume a leaderless Dynamo-style system is not linearizable even with quorum
reads and writes, because of the edge cases above and time-of-day timestamps.
Reconciliation: the interview chapter's "strong" means "reads overlap the latest acknowledged write in
the normal case", which is weaker than linearizability. Use W + R > N to reduce staleness. If you need
a recency guarantee (a lock, a uniqueness check, a read after another client's completed write), use a
leader-based or consensus-based store (`linearizability-and-consensus.md`). Making quorums
linearizable costs performance: the reader performs synchronous read repair before returning, and the
writer reads the latest timestamp from a quorum before choosing one. Even then only registers are
covered; linearizable compare-and-set needs consensus.

## 9. Verification
- Concurrent-write test: two clients write the same key through different replicas or regions
  simultaneously; assert the outcome matches the chosen strategy (siblings preserved, CRDT converged,
  or documented LWW loss).
- Property tests on vector comparison: ancestor, descendant and concurrent cases (inferred).
- If using LWW with wall clocks, monitor clock offsets and write a test that skews one node's clock
  and shows which writes are lost, so the loss is known and accepted.
- Check no config has w + r <= n while the code assumes fresh reads.
- Convergence test: after healing a partition, all replicas hold the same state (repair mechanisms
  listed in `replication-strategies.md`).
