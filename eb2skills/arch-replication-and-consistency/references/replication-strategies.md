# Replication strategies: single-leader, multi-leader, leaderless

Sources: DDIA 2e ch. 6 (Replication), ch. 10 (leader election context). Items marked (inferred) are
extrapolations in the study notes, not claims of the book.

## Contents
1. Why replicate (and what replication does not do)
2. Single-leader: mechanics, sync/async, setting up followers, outages, failover, log formats
3. Multi-leader: when it is justified, topologies, sync engines
4. Leaderless: reads, writes, repair mechanisms
5. Comparison and picking
6. Verification

## 1. Why replicate

Four reasons: latency (data near users), availability and durability (survive node, zone or region
loss), read scalability (more machines serve reads), disconnected operation (offline or local-first).
If data never changed, replication would be a one-time copy. All the difficulty is propagating
changes. Everything below assumes the whole dataset fits on every node; splitting the dataset is
sharding (see `sharding.md`).

Replication is not backup. A mistaken DELETE or corruption replicates to every replica immediately.
Keep point-in-time backups and archived replication logs in addition; they also bootstrap new
followers, and cold history is cheaper in an object store than on primary storage.

## 2. Single-leader (primary-backup, active/passive)

Mechanics: one replica is the leader; all writes go to it; it writes locally and emits a replication
log. Followers apply the log in the same order. Clients read from the leader or any follower;
followers are read-only to clients. In a sharded database there is one leader per shard, and the
leaders can sit on different nodes. Raft-based systems (CockroachDB, TiDB, etcd) elect the leader
automatically.

### Synchronous, asynchronous, semisynchronous

| Mode | Behaviour | Gain | Cost |
|---|---|---|---|
| Synchronous (per follower) | Leader waits for that follower before acking the client | That follower is current; data survives leader loss | If that follower is down, slow or partitioned, writes block |
| Asynchronous | Leader does not wait | Writes continue even if all followers lag; good for many or geo-distributed followers | An acknowledged write can be lost if the leader dies before replicating it; followers lag |
| Semisynchronous | One follower sync, others async; if the sync one falters, promote an async one | Current copy on at least two nodes at all times | Some write latency |
| Majority sync | e.g. 3 of 5 including the leader sync | Common with consensus-style systems | Needs a majority alive |

Making every follower synchronous is impractical: more nodes means a higher chance that one is down,
and one outage halts writes. Normal lag is under a second but has no bound: minutes during recovery,
near-capacity load or network trouble.

Rule: async when followers are many or far away and losing the last moments of writes on leader
failure is acceptable; semisync or majority sync for data that must not be lost.

### Setting up a new follower without downtime
1. Take a consistent snapshot of the leader, without locking if the tooling allows.
2. Copy it to the new node.
3. Follower connects and requests all changes since the snapshot. The snapshot must be tied to an
   exact position in the replication log (PostgreSQL log sequence number; MySQL binlog coordinates or
   GTIDs).
4. When the backlog is applied it has caught up and streams on.

A plain file copy fails because data changes mid-copy. Archiving logs plus periodic snapshots to an
object store (WAL-G, Litestream) doubles as backup, disaster recovery and steps 1-2.

Object-store-backed databases (side discussion in ch. 6): cheap, multi-zone durable, conditional
writes (compare-and-set) enable transactions and leader election; but latency is higher than local
disk, per-call fees force batching, objects are immutable so random writes are costly. Architectures:
tiered storage (hot on SSD/memory, cold in object store); object store primary plus a low-latency
store for the log; zero-disk designs where disks are only caches.

### Node outages
- Follower failure is catch-up recovery: the follower knows its last processed transaction and asks
  the leader for everything after it. Cost: heavy load on both if the downtime was long or writes are
  heavy. Dilemma for the leader: keep the log until the slow follower returns (disk may fill) or
  delete it (follower must be rebuilt from backup).
- Leader failure is failover, manual or automatic. Automatic failover steps:
  1. Detect failure. There is no foolproof method; use a timeout (e.g. 30 s without response).
     Planned maintenance uses a safe handoff instead.
  2. Choose the new leader: election among remaining replicas, or appointed by a controller. Best
     candidate is the most up-to-date replica (with sync/semisync, the one the old leader waited for;
     with async, the highest log position). This is a consensus problem
     (`linearizability-and-consensus.md`).
  3. Reconfigure clients to write to the new leader, and make a returning old leader become a
     follower that recognises the new leader.

### Failover failure modes (review checklist)
- Async plus stale new leader: the old leader's unreplicated writes are normally discarded, so
  "committed" writes vanish.
- Discarded writes are dangerous when other systems depend on database state. A GitHub incident: a
  stale MySQL follower was promoted, its autoincrement counter lagged, it reused primary keys that
  were also keys in Redis, and private data reached the wrong users.
- Split brain: two nodes both believe they lead and accept writes. Without conflict resolution that
  corrupts data. A safety catch that shuts one node down can shut down both, or fire too late.
  Prevention is fencing (`locks-leases-fencing.md`).
- Timeout tuning: too long slows recovery; too short causes spurious failovers during load spikes or
  network glitches, which hurts an already struggling system.
- Because of these, some operators prefer manual failover even when automatic exists.
- Promote the most up-to-date follower. Losing a fraction of a second may be tolerable; being days
  behind is not.

### Replication log formats

| Format | Ships | Strength | Weakness | Seen in |
|---|---|---|---|---|
| Statement-based | The SQL statements | Compact, simple | NOW()/RAND() differ per replica; autoincrement and `UPDATE ... WHERE` depend on identical order; triggers and stored procedures with side effects diverge | Old MySQL; VoltDB makes it safe by requiring deterministic transactions |
| WAL shipping (physical) | Storage engine write-ahead log bytes | Exact replica; no extra log | Coupled to storage format, so leader and follower usually need the same version; upgrades need downtime | PostgreSQL, Oracle |
| Logical (row-based) | Row-level records: inserted row = new values, deleted row = key, updated row = key plus new values, plus commit records | Decoupled from storage engine, so mixed versions work; external consumers can parse it, which enables change data capture | Larger for bulk updates (inferred) | MySQL binlog; PostgreSQL logical replication |

Rolling upgrade recipe (requires a logical log): upgrade followers one by one, fail over to an
upgraded follower, then upgrade the old leader.

## 3. Multi-leader (active/active)

Several nodes accept writes; each is also a follower of the others; replication is usually async
(sync multi-leader is single-leader with forwarding). Within one region it is rarely worth its
complexity. Legitimate uses:
1. Multi-region: a leader per region, ordinary leader-follower within a region.
2. Offline clients: every device is a leader with a local database (calendar apps); the extreme case
   of a bad link, with lag of hours or days.
3. Real-time collaboration (Google Docs, Figma, Linear): each browser tab is a replica.

### Single-leader vs multi-leader across regions

| Axis | Single leader | Multi-leader |
|---|---|---|
| Write latency | Every write crosses to the leader's region | Local write; inter-region delay hidden |
| Regional outage | Fail over to another region | Each region continues; catch up later |
| Inter-region network trouble | Very sensitive | Tolerated |
| Consistency | Strong guarantees, serializable transactions, uniqueness, non-negative balance | Cannot guarantee unique usernames, non-negative balances or non-overlapping bookings: each leader accepts writes that are valid alone and conflict together. A fundamental limit |

Multi-leader is often retrofitted onto databases, causing pitfalls with autoincrement keys, triggers
and integrity constraints. Test the actual behaviour of your database.

### Topologies
- Circular and star: one failed node breaks the flow between others; manual reconfiguration usually
  needed.
- All-to-all: more fault tolerant but messages overtake each other: a leader can receive an UPDATE
  before the INSERT it depends on. Timestamps do not fix this (clock skew); version vectors do
  (`conflicts-and-quorums.md`).
- Loop prevention: each node has an ID; writes are tagged with IDs of nodes passed; a node ignores
  changes tagged with its own ID.

### Sync engines and local-first software
A sync engine captures local changes, stores or sends them later, merges collaborators' changes into
the local copy and updates the UI. Offline-first means editing works offline; local-first adds that
it keeps working if the vendor shuts down (open sync protocol, multiple providers; Git is the
non-real-time example).

Gains: instant UI (aim to respond within a 16 ms frame at 60 Hz); offline is just a large network
delay; simpler frontend since local reads and writes almost never fail. Limits: best when a user's
whole dataset can be downloaded; unsuitable for very large datasets (a whole e-commerce catalogue);
conflicts are inevitable and need automatic resolution; invariants cannot be enforced.

## 4. Leaderless (Dynamo-style)

Any replica accepts writes; the client or a non-ordering coordinator sends writes to several replicas
in parallel. Revived by Amazon's Dynamo; open source: Riak, Cassandra, ScyllaDB. Not the same as
DynamoDB, which is single-leader.

No failover: a write succeeds when enough replicas acknowledge; a down replica misses it. Reads query
several replicas in parallel and take the newest version.

### Catching up missed writes

| Mechanism | How | Limit |
|---|---|---|
| Read repair | Client sees a stale replica in a read and writes the newer value back | Only fixes values that are read often |
| Hinted handoff | Another node stores hints for an unavailable replica and replays them | Covers never-read values; adds load during recovery |
| Anti-entropy | Background process compares replicas and copies missing data, in no particular order | Slow, long delay |

Quorum arithmetic, sloppy quorums, concurrent-write detection: `conflicts-and-quorums.md`.

### Leaderless vs leader-based behaviour
- Leaderless strengths: no failover; request hedging (use the fastest responses) cuts tail latency;
  no distinction between normal and failure paths; resilient to gray failures (slow, degraded nodes)
  and overload.
- Leaderless costs: hint storage and handoff add load during stress; larger quorums raise the chance
  of hitting a slow replica; a large network interruption can prevent any quorum. Sloppy quorums
  (Riak/Dynamo; consistency level ANY in Cassandra/ScyllaDB) accept writes on any reachable node but
  give no promise later reads will see them.
- Multi-region leaderless (Cassandra/ScyllaDB): client picks a local coordinator, which forwards to
  all replicas in its region and one replica per other region. Consistency level options: quorum
  across all regions, quorum per region, or local-region quorum only (fast but staler). Riak limits n
  to one region and replicates across regions asynchronously like multi-leader.

## 5. Picking

| Need | Pick | Watch |
|---|---|---|
| Strong consistency, invariants, simplest reasoning | Single-leader with a sync or semisync follower | Failover risk, cross-region write latency, leader bottleneck |
| Read-mostly clients, read scaling | Single-leader plus async followers | Handle read-your-writes, monotonic and prefix anomalies (`replication-lag-anomalies.md`) |
| Multi-region writes with local latency; region outage tolerance | Multi-leader or leaderless | Conflicts, weak consistency, topology ordering; test your database |
| Offline or local-first; real-time collaboration | Sync engine with CRDT or OT, multi-leader per device | Per-user data must fit on the client; invariants impossible |
| Top availability and tail-latency resilience, eventual consistency acceptable | Leaderless quorum | Freshness not guaranteed; last-write-wins clock issues; needs repair and monitoring |
| Protection from user error and corruption | Backups and point-in-time recovery | Replication copies mistakes |

If the application cannot tolerate replication lag, the simplest model is a database that offers
strong consistency and ACID transactions so replication can be ignored. The NoSQL-era belief that
these cannot scale was overturned by NewSQL systems; weaker replication is still chosen for
resilience to network interruptions and lower overhead.

## 6. Verification
- Failover drill: kill the leader under write load; confirm the promoted node was the most current,
  count acknowledged writes missing afterward, and confirm the old leader returns as a follower and
  cannot accept writes.
- Check identifiers: after failover, do auto-increment or sequence values collide with values stored
  elsewhere (caches, other databases)?
- Monitor lag: leader log position minus follower position; alert on a threshold (inferred).
- Rolling upgrade rehearsal if you rely on mixed versions: confirm the log format is logical.
- For multi-leader and leaderless, test the real conflict behaviour with concurrent writes to the
  same key from two regions.
- Warning signs: users losing just-saved data; promoted follower behind; two nodes accepting writes
  after failover; duplicate IDs after failover; unbounded leader log retention for a dead follower.
