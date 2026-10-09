# Sharding (partitioning), consistent hashing, routing and secondary indexes

Sources: DDIA 2e ch. 7 (parts A and B); System Design Interview 2e ch. 5 (consistent hashing). Items
marked (inferred) are extrapolations in the study notes. Defaults quoted (10 GB, 16 or 256 ranges) are
the book's examples as of its writing.

## Contents
1. Sharding vs replication; vocabulary
2. Whether to shard
3. Multitenancy
4. Choosing the scheme: key-range, hash, compound keys
5. Consistent hashing
6. Hot spots and skew
7. Rebalancing: automatic vs manual
8. Request routing
9. Secondary indexes
10. Decision tables
11. Verification

## 1. Vocabulary
Replication keeps the same data on several nodes; sharding splits the dataset into pieces on different
nodes. Normally each record belongs to exactly one shard, and each shard is replicated; a node can
lead some shards and follow others, but each shard has one leader. The sharding scheme is mostly
independent of the replication scheme.

Names for a shard: partition (Kafka), range (CockroachDB), region (HBase, TiDB), vBucket (Couchbase),
vnode (Riak), token range (Cassandra), tablet (Bigtable, YugabyteDB, ScyllaDB). PostgreSQL
"partitioning" splits a table into files on one machine; it is not sharding and has nothing to do with
network partitions.

## 2. Whether to shard
- Main reason: data volume and write throughput. If only reads are the problem, use read replicas.
- A single machine can do a lot now; if data and writes fit, prefer an unsharded database.
- Costs: you must choose a partition key (records with the same key co-locate), and the scheme is hard
  to change; works well for key-value access, poorly for relational data needing secondary indexes or
  joins across shards; multi-shard writes need distributed transactions, which are slower and a
  potential bottleneck (`arch-transactions`).
- Sharding also appears inside one machine: a single-threaded process per core (Redis, VoltDB,
  FoundationDB).

## 3. Multitenancy
A tenant is a SaaS customer with a self-contained dataset. Give each tenant (or group of small
tenants) its own shard.
- Benefits: resource isolation (noisy neighbour); permission isolation (an access-control bug is less
  likely to leak across tenants); cell-based architecture for fault isolation; per-tenant backup and
  restore; compliance (GDPR/CCPA export and delete act on one shard); data residency (assign a tenant
  shard to a region); gradual schema rollout one tenant at a time (hard to do transactionally).
- Challenges: a tenant must fit on one node (else shard inside the tenant); many tiny tenants cost
  per-shard overhead, so group them and then move tenants as they grow; cross-tenant features and
  joins get harder.
- Choose it when isolation, compliance or per-customer operations matter and tenants are small and
  independent.

## 4. Choosing the scheme
Goal: spread data and query load evenly, and rebalance when nodes join or leave. Skew is unfair
distribution; a hot shard has disproportionate load; a hot key is one key with extreme load. The
partition key may be the key or its first part; in relational tables it is a column and not
necessarily the primary key.

### 4.1 Key-range
Contiguous key ranges per shard (volumes of an encyclopedia); boundaries adapt to the data. Chosen
manually (Vitess) or automatically (Bigtable, HBase, MongoDB range option, CockroachDB, RethinkDB,
FoundationDB; YugabyteDB offers both).
- Keys are sorted within a shard (B-tree or SSTable), so range scans are cheap and keys work as a
  concatenated index, e.g. sensor readings by time.
- Failure mode: adjacent writes hit one shard. A timestamp key sends all current writes to this
  month's shard. Fix: prefix with something that spreads (sensor ID, then timestamp). Cost: a
  time-range query across many sensors needs one range query per sensor.
- Rebalancing: pre-split an empty database (HBase, MongoDB; needs knowledge of the key distribution),
  then split a shard at a size threshold (HBase default 10 GB) or persistently high write throughput
  (so a hot but small shard can split), and merge adjacent shards after deletes. Splitting is
  expensive (rewrites data like compaction) and lands on the shard exactly when it is under load, so
  it can worsen overload.

### 4.2 Hash-based
Use when you do not need neighbours together (e.g. tenant IDs). Hash the partition key to spread skew.
The hash need not be cryptographic (MongoDB MD5, Cassandra/ScyllaDB Murmur3). Language built-in hashes
(Java `Object.hashCode`, Ruby `Object#hash`) can differ between processes for the same key, so they
are unsuitable.

| Variant | How | Notes |
|---|---|---|
| hash(key) mod N nodes | Index by node count | Avoid: changing N moves most keys |
| Fixed number of shards much larger than nodes | e.g. 1,000 shards on 10 nodes, shard = hash(key) % 1000, with a shard-to-node map | Adding a node moves whole shards (cheap, key-to-shard mapping unchanged; old assignment serves during transfer). Pick a count with many divisors; give bigger machines more shards. Used by Citus, Riak, Elasticsearch, Couchbase. Limits: nodes cannot outnumber shards; a wrong guess means costly resharding (extra disk, sometimes downtime); hard when dataset size varies widely (shards too big make rebalancing and recovery costly, too small add overhead) |
| Hash-range | Each shard owns a contiguous range of hash values (e.g. 16-bit hash 0 to 65,535 split into ranges); split and merge by size or load | Shard count adapts. Range queries on the partition key become scatter-gather; with a compound key whose first column is the partition key, range queries on later columns stay on one shard. Used by YugabyteDB, DynamoDB, optional in MongoDB; warehouses use similar ideas (BigQuery partition plus cluster columns, Snowflake micro-partitions with cluster keys, Delta Lake) |
| Cassandra/ScyllaDB variant | Hash space split into ranges proportional to node count with random boundaries (16 per node in Cassandra, 256 in ScyllaDB) | Imbalances average out; a new node takes parts of existing ranges, so a fair share moves with minimal data |

### 4.3 Compound keys
First key part identifies the shard; the rest sets sort order within it. Range queries within one
partition key stay efficient even when the partition key itself is hashed.

## 5. Consistent hashing

Definition (DDIA): a mapping from keys to shards with roughly equal keys per shard and minimal key
movement when the shard count changes. "Consistent" here is unrelated to replica or ACID consistency.

The problem (System Design Interview ch. 5): `serverIndex = hash(key) % N` works while N is fixed. Add
or remove a server and most keys remap, not only those on the failed server, which causes a
cache-miss storm on the survivors. With consistent hashing only about k/n keys move (k keys, n slots).

Ring mechanics:
1. Hash space is a hash function's output range (e.g. SHA-1, 0 to 2^160-1) joined into a ring.
2. Hash servers (by IP or name) onto the ring with the same function, no modulo.
3. Hash keys onto the ring.
4. Lookup: from the key's position go clockwise to the first server.
- Add a server: only keys between the new server and its anticlockwise predecessor move to it.
- Remove a server: its keys go to the next server clockwise.

Two problems with the bare ring: arc sizes cannot be kept equal as servers come and go (removing one
server can double a neighbour's share), and key distribution can be non-uniform. Fix: virtual nodes.
Each physical server appears at many ring positions; a key goes to the first virtual node clockwise,
which maps to a real server. More vnodes means lower standard deviation: about 10 percent of the mean
at 100 vnodes and about 5 percent at 200 (an experiment cited in the interview book). Cost: vnode
metadata memory. Weight vnode counts by capacity for heterogeneous hardware. Replica placement walks
clockwise and takes the first N distinct physical servers (skip vnodes of a server already chosen).

Variants: rendezvous (highest random weight) hashing and jump consistent hashing, where a new node
takes individual keys scattered from all others instead of subranges. Cassandra's scheme resembles the
original ring. Used in Dynamo, Cassandra, Discord, Akamai CDN and Maglev.

It spreads keys, not load on one key: a single extremely hot key still lands on one node.

Sketch (Python, adaptation, not from the book):

```python
import bisect, hashlib
def h(s): return int(hashlib.sha1(s.encode()).hexdigest(), 16)
class Ring:
    def __init__(self, nodes, vnodes=100):
        self.ring = sorted((h(f"{n}#{i}"), n) for n in nodes for i in range(vnodes))
        self.keys = [k for k, _ in self.ring]
    def owner(self, key):
        i = bisect.bisect(self.keys, h(key)) % len(self.ring)  # first vnode clockwise
        return self.ring[i][1]
```

Use a stable hash like the above, never a per-process built-in hash.

## 6. Hot spots and skew
Even key distribution is not even load. A celebrity key can send a storm to one shard.
- Range and hash-range schemes can isolate a hot key in its own shard or machine.
- Application-level key splitting: append or prepend random digits to a known-hot key (two digits give
  100 sub-keys) to spread writes. Costs: reads must query all sub-keys and merge, so read load per
  shard is not reduced; you need bookkeeping of which keys are split and a process to convert keys to
  and from hot status; load changes over time; keys can be hot for reads or writes needing different
  strategies. Some cloud services automate this (heat management, adaptive capacity).

## 7. Rebalancing: automatic vs manual
Spectrum: fully automatic (DynamoDB adds and removes shards within minutes), manual (administrator
configures), hybrid (Couchbase and Riak propose an assignment, an administrator commits it).
- Automatic: less toil, autoscaling. Risks: rebalancing is expensive (rerouting plus bulk data
  movement) and can overload network and nodes; splits may not keep up near maximum write throughput.
- Dangerous combination with automatic failure detection: an overloaded slow node is judged dead, load
  moves away, other nodes overload and are falsely suspected: cascading failure.
- Recommendation: keep a human in the loop for rebalancing; rebalance manually ahead of known surges
  (Cyber Monday, big ticket sales).

## 8. Request routing
Given a key, which node holds its shard? It resembles service discovery, except that app servers are
stateless while only a replica of the key's shard can serve a sharded database request. Three
topologies:
1. Client contacts any node (round-robin load balancer); the node serves it or forwards it to the
   owner and relays the reply.
2. A shard-aware routing tier forwards requests and serves none itself.
3. Shard-aware clients connect directly to the right node.
All need an up-to-date shard-to-node mapping. Open problems: who decides assignment (a single
coordinator is simplest but needs fault tolerance, and coordinator failover risks two coordinators
making contradictory assignments), how routers learn of changes, and the cutover period when a shard
moves from node A to node B while requests to A are still in flight (A should reject or forward, or
fence by epoch or version; inferred).

| Where the authoritative mapping lives | Examples | Consistency | Notes |
|---|---|---|---|
| Separate coordination service using consensus | HBase and SolrCloud on ZooKeeper; Kubernetes on etcd | Strong; guards against split brain | Nodes register; routers and clients subscribe to changes |
| Own config servers plus routing daemons | MongoDB (config servers, mongos) | Strong | Same architecture built in |
| Built-in Raft | Kafka, YugabyteDB, TiDB, ScyllaDB | Strong | No external dependency |
| Gossip among nodes | Riak | Weak; parts of the cluster can disagree on ownership | Acceptable only because leaderless stores already give weak guarantees |

Rule: use consensus-backed metadata when requests must reach exactly one owner (leader-based shards);
gossip is tolerable only when the data layer tolerates stale routing. IP addresses change far more
slowly than shard assignments, so plain DNS usually suffices for finding machines. This is about
single-key OLTP lookup; analytical databases fan queries out in parallel instead.

## 9. Secondary indexes
A secondary index finds all records with a value, so matching records are scattered across shards.
Do not hand-roll a secondary index in application code over a key-value store: races and partial
write failures desynchronise index and data (multi-object atomicity is needed, see `arch-transactions`).

### Local (document-partitioned)
Each shard indexes only its own records. A write touches one shard. A read that includes the partition
key goes to one shard; otherwise it is scatter/gather across all shards, with tail-latency
amplification (the slowest shard sets the response time) and no read-throughput scaling, since every
shard sees every query. Used by MongoDB, Riak, Cassandra, Elasticsearch, SolrCloud, VoltDB.

### Global (term-partitioned)
One index covering all shards, itself sharded by the indexed term (by term range for range scans, or by
hash of the term for even spread). A single-condition read hits one index shard for the postings list,
though fetching the records still touches the primary shards holding them. Multi-condition AND queries
must intersect postings lists across index shards over the network: fine when lists are short. A write
may update several index shards, so keep in sync via a distributed transaction (CockroachDB, TiDB,
YugabyteDB do it synchronously) or update asynchronously (DynamoDB global indexes are async and can be
stale, like replication lag).

| Question | Local | Global |
|---|---|---|
| Write cost | One shard | Possibly many; needs distributed transaction or async |
| Index consistent with data | Trivially | Only with a distributed transaction; otherwise stale |
| Read by index, all results | Scatter/gather | One index shard (plus record fetches) |
| Tail latency and throughput scaling | Poor | Better |
| Multi-condition AND | Each shard intersects locally | Cross-shard intersection |
| Choose when | Write-heavy, queries usually include the partition key, or search-engine style filtering | Read-heavy, selective single-term lookups, short postings lists, and staleness or transaction cost is acceptable |

## 10. Decision table

| Situation | Choose | Watch |
|---|---|---|
| Fits on one machine, read-heavy | No sharding; replicas | Cross-shard complexity otherwise |
| Range scans on key needed | Key-range | Hot shard on monotonic keys; expensive splits |
| Adjacency irrelevant, want uniform load | Hash of key | Range queries scatter; use compound key |
| Known stable data size | Fixed shard count well above node count | Wrong guess is costly |
| Unknown or variable size | Hash-range or key-range with auto split | Split cost |
| Nodes join and leave, minimal movement | Consistent hashing family | Hot keys need separate handling |
| Per-customer isolation or compliance | Tenant per shard or cells | Large tenants, tiny-tenant overhead, cross-tenant queries |
| One super-hot key | Dedicated shard or key salting | Reads fan out and merge |

## 11. Verification (inferred unless noted)
- Monitor per-shard QPS, bytes and CPU; alert on max-to-mean ratio; track top-N keys.
- Load-test with skewed (Zipf-like) key distributions, not uniform ones.
- After adding or removing a node in a ring or mod scheme, measure the fraction of keys moved: about
  1/(n+1) when going from n to n+1 nodes for a ring (the interview book states k/n of k keys), nearly
  all for mod N. (My run of the sketch above: 20,000 keys, 10 to 11 nodes, 100 vnodes moved 11 percent
  against 91 percent for mod N.) With 100 or more vnodes, per-node load standard deviation
  should be within your target (the interview book cites about 10 percent at 100).
- Replica placement test: replicas of a key sit on distinct physical nodes (and racks or data centres).
- For local indexes check hot queries include the partition key, or measure p99 fan-out latency versus
  shard count; for global indexes measure index staleness and postings-list length distribution.
- Cutover test: move a shard under traffic and assert no write lands on the old owner afterward.
