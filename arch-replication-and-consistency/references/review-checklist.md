# Review checklist: replication, sharding, clocks, coordination

Use this when reviewing a design document, an architecture diagram or code that touches replicated or
sharded data. Each question has an observable answer: a config value, a line of code, a test or a
metric. Items marked (inferred) are extrapolations in the study notes; the rest trace to DDIA 2e ch.
6, 7, 9, 10 and System Design Interview 2e ch. 5, 6, 7.

## Contents
1. Replication topology
2. Failover
3. Read paths and lag
4. Conflicts and multi-writer designs
5. Quorums
6. Sharding
7. Time and clocks
8. Locks, leases, leaders
9. Consistency level chosen
10. IDs
11. Testing evidence to ask for
12. Red-flag phrases

## 1. Replication topology
- [ ] Which replication family is used (single-leader, multi-leader, leaderless) and why? Is the reason
      one of latency, availability, read scaling, offline? If multi-leader within one region, what
      justifies the complexity?
- [ ] Sync, async or semisync? Where does the durability promise lie: what happens to an acknowledged
      write if the leader dies right now?
- [ ] Is there a backup and point-in-time recovery in addition to replication?
- [ ] What is the replication log format, and does it permit rolling upgrades and change capture
      (logical) or tie versions together (physical)?
- [ ] If statement-based: are NOW(), RAND(), triggers and autoincrement handled deterministically?

## 2. Failover
- [ ] Who detects failure, with what timeout, and what is the cost of a false positive?
- [ ] Is the promoted node the most up to date? What happens to unreplicated writes?
- [ ] Do identifiers (autoincrement, sequences) risk reuse after promotion, colliding with values held in
      other systems?
- [ ] How is the old leader fenced and demoted? Can two nodes accept writes (split brain)?
- [ ] Is automatic failover justified, or should it be manual?
- [ ] Is log retention bounded for a dead follower?

## 3. Read paths and lag
- [ ] Which reads go to followers? For each user-visible flow, is read-your-writes needed, and how is
      it provided (leader read, recent-write window, log position, same-region routing)?
- [ ] Cross-device: is last-write metadata centralised?
- [ ] Monotonic reads: is a user pinned to a replica, and what happens when it fails?
- [ ] Causally related writes on different shards: how is order preserved?
- [ ] What does the UX do if lag reaches minutes? Is lag measured and alerted?

## 4. Conflicts and multi-writer designs
- [ ] Can two writers modify the same record concurrently? Which strategy: avoidance, LWW, siblings,
      convergent merge?
- [ ] If LWW: is data loss acceptable, are timestamps from synchronised clocks, are clock offsets
      monitored?
- [ ] If merging sets or carts: do deletions survive the merge?
- [ ] Are there invariants (uniqueness, balance, no overlap)? Then multi-writer is wrong for them; where
      is the single serialisation point?
- [ ] All-to-all multi-leader: are causally dependent writes ordered (version vectors)?

## 5. Quorums
- [ ] n, w, r values per data class; is w + r > n where freshness is assumed?
- [ ] Does the code assume linearizability from quorums? (It should not.)
- [ ] Are sloppy quorums on, and does the application tolerate that?
- [ ] Repair paths present: read repair, hinted handoff, anti-entropy? Is staleness measurable?

## 6. Sharding
- [ ] Why shard at all: data volume or write throughput, versus read replicas on one node?
- [ ] Partition key: even data, even load, monotonic keys avoided or prefixed? What range queries
      become scatter/gather?
- [ ] Hash function stable across processes and versions (not a language built-in)?
- [ ] Not hash mod N for a changing node count?
- [ ] Rebalancing: fixed shard count (is it large enough?), or auto split; who triggers it; is a human
      in the loop; is it coupled to automatic failure detection?
- [ ] Hot key plan: isolation or salting, and read fan-out cost?
- [ ] Routing: what holds the shard map, how is it kept consistent, how is the cutover handled?
- [ ] Secondary indexes: local or global; consequences for write cost, read fan-out, staleness?
- [ ] Multi-shard writes: is there a distributed transaction or an accepted inconsistency?
- [ ] Tenant isolation requirements considered?
- [ ] Consistent hashing: vnode count, capacity weighting, replicas on distinct physical nodes?

## 7. Time and clocks
- [ ] Durations and timeouts use monotonic clocks?
- [ ] Any cross-node ordering decided by time-of-day timestamps (client clocks especially)?
- [ ] Are clock offsets monitored, and are drifting nodes ejected?
- [ ] Timeout values come from measured RTT distributions; adaptive detection considered?
- [ ] Is retry safe, i.e. is the operation idempotent given "timeout = unknown outcome"?
- [ ] Any code that treats a TCP ack as application success?

## 8. Locks, leases, leaders
- [ ] Every "only one X" has a token checked by the resource, or conditional writes?
- [ ] No code compares a remote expiry with the local clock, or assumes the check-to-act gap is short?
- [ ] Leader election and locks come from a coordination service, not hand-rolled?
- [ ] Consensus group: odd size, 3 or 5, small and slow-changing data, not on the hot path?
- [ ] Leader serving linearizable reads confirms leadership (quorum or lease)?
- [ ] Unclean leader election disabled where durability matters?

## 9. Consistency level chosen
- [ ] For each data class, the requirement is stated: linearizable, read-your-writes, causal, eventual?
- [ ] Linearizability is demanded only where a hard uniqueness, lock or cross-channel race exists; the
      cost (latency, minority-side unavailability, no throughput scaling) is accepted?
- [ ] Constraints that can be compensated are compensated rather than prevented?
- [ ] CAP is not used as a label to justify the choice; the partition behaviour is stated concretely.

## 10. IDs
- [ ] Which ordering does the ID need (none, causal, real time)? Is the scheme matched?
- [ ] Snowflake-style: clock regression handled, machine IDs unique, epoch overflow date known?
- [ ] No uniqueness or lock enforcement through timestamp ordering?

## 11. Testing evidence to ask for
- Failover drill results: lost-write count, time to recover, old leader demotion.
- Injected replica lag tests for read-your-writes, monotonic reads, consistent prefix (inferred).
- Pause test (`SIGSTOP`) and delayed-packet test against every lease-protected write.
- Network partition test (including one-way and partial) with expected behaviour per side.
- Clock skew test on LWW paths.
- Skewed (Zipf-like) load test for sharding; key-move fraction after node add/remove (inferred).
- Linearizability history check for any component claimed linearizable.

## 12. Red-flag phrases
- "Quorum reads make it strongly consistent."
- "We just take the highest timestamp."
- "The leader is whoever holds the lock" (without a token at the resource).
- "Failover is automatic" (with no stated handling of lost writes or split brain).
- "We'll shard by `hash(key) % N`."
- "Eventually consistent" with no figure for how long.
- "CA system" or "we picked CP/AP" with no description of behaviour during a partition.
- "It worked in testing" (with no fault injection).
