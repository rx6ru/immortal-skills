# The scaling ladder

How a system grows from one server to many users and regions, rung by rung, and how to tell which rung is missing. Source: System
Design Interview ch. 1 (the ladder and its end-state), ch. 15 (the same ladder replayed for file storage), DDIA 2e ch. 1-2 (counter-pressure:
single node first, one order of magnitude ahead, cloud-native layering). Each rung is added only when a specific bottleneck or risk appears.

## Contents
1. Principles
2. The rungs (trigger, change, buys, costs, verify)
3. Diagnosing: symptom to missing rung
4. Counter-pressure: when not to climb
5. The ladder replayed (file sync)
6. End-state checklist
7. Cloud-era adaptation

## 1. Principles

- Climb one rung at a time, driven by a measured or estimated bottleneck (`estimation.md`).
- Availability rungs (load balancer, replication) come before the most complex rung (sharding).
- Make the web tier stateless before autoscaling it.
- Remove every single point of failure (web, DB, cache, load balancer, data center).
- Book's one-line end state: stateless web tier; redundancy at every tier; cache as much as you can; multiple data centers; static
  assets on a CDN; shard the data tier; split tiers into services; monitor and automate.

## 2. The rungs

Entry format: trigger; change; buys; costs and caveats; verify.

### Rung 0: single server
Web app, database and cache on one machine. Client resolves the domain by DNS (third party, paid), gets the IP, sends HTTP, gets HTML or JSON.
- Fine to start. Everything is coupled; any failure is total. DDIA adds that one node often covers more than expected.

### Rung 1: separate the web tier and the data tier
- Trigger: one box is not enough, or the tiers need independent scaling.
- Buys: independent scaling of each tier.
- Database choice: default to relational (MySQL, PostgreSQL, Oracle; decades of proof, joins). Consider NoSQL (key-value, graph, column, document;
  usually no joins) when you need super-low latency, the data is unstructured or non-relational, you only serialise/deserialise JSON/XML/YAML, or the data volume is massive. Depth: `arch-data-storage`.

### Rung 2: vertical vs horizontal scaling
- Vertical (scale up): simple, fine at low traffic; hard ceiling, no failover, expensive at the top. It goes surprisingly far
  (the book cites 24 TB RAM machines, and a 2013 site serving 10M monthly uniques from one master DB).
- Horizontal (scale out): the answer for large systems and the only one that gives redundancy.

### Rung 3: load balancer
- Trigger: a single web server is a SPOF and a capacity limit.
- Change: users hit the LB's public IP; web servers get private IPs only (unreachable from the internet).
- Buys: failover (traffic moves to the surviving server; add a fresh one), elastic capacity (add servers to the pool).
- Costs: the LB itself becomes a SPOF; run a redundant pair (the Drive design has the secondary monitor the primary by heartbeat).

### Rung 4: database replication
- Trigger: database is a SPOF; read load is high.
- Change: leader accepts writes only, followers serve reads only (the book says master/slave). Reads outnumber writes, so more followers than leaders.
- Buys: read performance (parallel reads), reliability, availability.
- Failure handling: one follower dies and is the only one, reads go to the leader temporarily; several followers, reads go to the others; leader dies, promote a follower (caveat: the follower may be behind, so missing data must be recovered by scripts).
  Multi-leader and circular replication exist but are more complex.
- Verify: writes route to the leader, reads to followers; a failover drill has a data-recovery story for replication lag.
- Depth: `arch-replication-and-consistency` (lag anomalies, failover hazards).

### Rung 5: cache tier
- Trigger: repeated reads of the same data make pages slow.
- Pattern: read-through. Check the cache; hit returns; miss queries the DB, stores in the cache and returns.
- Use when data is read often and modified rarely. The cache is volatile memory: never the only copy of important data.
- Considerations: expiry not too short (constant reloads) nor too long (stale); consistency (DB and cache are not updated in one transaction, harder across regions); a single cache server is a SPOF, so use several across data centers and over-provision memory for a buffer; eviction (LRU most popular, LFU, FIFO alternatives).
- Detail in `building-blocks.md`.

### Rung 6: CDN for static content
- Flow: user requests a URL on the CDN domain; the nearest node serves it; on a miss it pulls from the origin (web server or object store), which may send a TTL header; cached until the TTL expires.
- Considerations: cost (charged per transfer; do not put rarely used assets on the CDN); expiry; fallback (clients must detect a CDN outage and go to the origin); invalidation (vendor API, or object versioning such as `image.png?v=2`).

### Rung 7: stateless web tier
- Trigger: need to scale the web tier horizontally or autoscale.
- Change: move session data out of web servers into a shared store (RDBMS, Memcached/Redis, NoSQL; the book picks NoSQL as easy to scale).
- Why: stateful servers need sticky sessions, which add overhead, make adding/removing servers hard and make failure handling hard. Stateless is simpler, more robust, and enables autoscaling.
- Verify: kill any web server; no user loses a session.

### Rung 8: multiple data centers
- Trigger: international users; availability.
- Change: geoDNS routes users to the nearest DC (split x%/(100-x)%); on a DC outage route 100% to the healthy one.
- Challenges: traffic redirection; data synchronisation (replicate across DCs, asynchronous as Netflix does, because failover traffic may hit a DC without the user's data); test and deploy at every location with automated deployment.

### Rung 9: message queue
- Trigger: decouple components so they scale independently, or work is slow/asynchronous.
- Change: producers publish, consumers subscribe; either can be down while the other works. Example: photo-processing jobs published by web servers, workers consume; add workers when the queue grows, remove when it is mostly empty.
- Depth on delivery semantics: `arch-data-pipelines`.

### Rung 10: logging, metrics, automation
- Error logs (per server or aggregated); metrics at host level (CPU, memory, disk I/O), aggregated level (DB tier, cache tier) and business level (DAU, retention, revenue); automation (CI on every check-in; automated build, test, deploy).
- Needed once big; cheap to start early. Depth: `arch-reliability-slos`, `arch-production-operations`.

### Rung 11: shard the database
- Trigger: DB overloaded as data grows; vertical limits hit.
- Change: shards share a schema and hold disjoint data; route by a hash of the shard key (`user_id % 4` as an illustration).
- The shard-key choice is the most important decision: it must spread data evenly and let queries route to one shard.
- Problems: resharding when a shard fills or distribution is uneven (use consistent hashing, see `building-blocks.md`); celebrity/hotspot keys (give a hot key its own shard, possibly sub-partition); cross-shard joins (denormalise so queries hit one table); also move non-relational workloads to a NoSQL store to lighten the relational DB.
- Depth: `arch-replication-and-consistency` (sharding), `arch-data-storage`.

### Rung 12: beyond millions
Keep iterating; optimise; split into smaller services (but see section 4).

## 3. Diagnosing: symptom to missing rung

| Symptom or review finding | Likely missing rung |
|---|---|
| One server death takes the site down | 3 (load balancer, 2+ web servers) |
| DB death loses availability or data | 4 (replication) |
| Same rows read repeatedly, DB CPU high on reads | 5 (cache) |
| Static assets slow for distant users, origin bandwidth high | 6 (CDN) |
| Cannot add web servers because of sessions on the box | 7 (stateless tier) |
| One region's outage or distant users' latency | 8 (multi-DC) |
| Request path blocked by slow or unreliable work (email, image processing, third parties) | 9 (queue plus workers) |
| Cannot tell what is wrong or how loaded each tier is | 10 (logs, metrics, automation) |
| Write load or data size exceeds one DB even at the largest size | 11 (sharding) |
| Uneven shard load | 11 follow-ups: re-pick key, hot-key shard, consistent hashing |

## 4. Counter-pressure: when not to climb

DDIA ch. 1-2 pushes the other way, and both views are useful.
- Prefer a single node until you have a reason to distribute. Reasons (DDIA): inherent distribution (multiple users/devices),
  fault tolerance/HA, scalability beyond one machine, latency (regions near users), elasticity, specialised hardware, legal
  compliance (data residency), sustainability. Costs of distribution: every network call can fail or time out and on timeout you do not
  know whether it was processed; network calls are much slower than in-process; debugging is harder; cross-service consistency becomes the application's problem.
- Single-node databases (DuckDB, SQLite and similar) cover many workloads.
- Plan at most about one order of magnitude ahead; architectures get rethought at each order of magnitude.
- Microservices are "primarily a technical solution to a people problem": independent teams. In a small company with few teams
  they are probably overhead. Rung 12's "split into services" needs that justification.
- Autoscaling is attractive but predictable load makes manual scaling quieter.

Decision rule: add a rung only when you can name the number or the incident that requires it. If you cannot, record it as a
"next step when X" in the design document instead.

## 5. The ladder replayed (file sync, SDI ch. 15)

1. Single server: web server plus MySQL plus a drive directory with a namespace directory per user.
2. Disk full: shard storage by user_id.
3. Fear of data loss: move files to object storage (S3) with same-region and cross-region replication.
4. Add a load balancer and web servers behind it; metadata DB off the server, replicated and sharded; object storage replicated across two regions.

Takeaway: the ladder is a method, not a sequence of products. Apply it again per subsystem.

## 6. End-state checklist (review a design against it)

- Any SPOF: web, DB, cache, LB, DC?
- Web tier stateless (kill test)?
- Cache TTL and invalidation defined; CDN fallback to origin defined?
- DB failover has a story for replication lag and lost writes?
- Queue depth drives worker count; retries bounded; dead-letter path?
- Shard key distribution measured; hot-key plan; no cross-shard joins on hot paths?
- Logs, metrics and automated deploys per tier?

## 7. Cloud-era adaptation (DDIA ch. 1; vendor examples are dated, the principle is not)

- Cloud-native systems separate storage from compute and build on object stores. Local VM disks are an ephemeral cache; virtual disks emulate
  block devices over the network. Treat object storage as the durable bulk layer.
- Higher-level managed services fit narrower use cases; if one fits, use it, else build from lower-level pieces.
- Capacity planning becomes financial planning; performance optimisation becomes cost optimisation. Know cloud quotas and limits before hitting them.
- Before building a rung yourself (CDN, queue, cache, LB, rate limiter), check whether a managed service or your gateway already
  provides it (SDI ch. 4: prefer a commercial gateway if engineering capacity is short).
