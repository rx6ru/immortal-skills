# Building blocks catalogue

Reusable components, each with when it enters a design, when it does not, the numbers and parameters, trade-offs and how to verify it. Sources:
System Design Interview (SDI) chapters 1, 4-15; DDIA 2e ch. 1-2; SRE Workbook ch. 12. Items marked (inferred) are verification ideas the
note-taker added rather than statements in the book. Each entry ends with where to go for depth.

## Contents
1. Load balancer
2. Cache (read-through) and eviction
3. CDN
4. Message queue and workers
5. Rate limiter (algorithms table)
6. Consistent hashing
7. Sharding key choice
8. Unique ID generation
9. Fan-out (push, pull, hybrid)
10. Real-time delivery (polling, long polling, WebSocket)
11. Presence and heartbeats
12. Blob/object storage, chunking, delta sync, dedupe
13. Search suggestion (trie)
14. Quorum replication, vector clocks and repair
15. Failure detection and service discovery
16. "Seen" structures (Bloom filter, content hash)
17. Pipelines: DAG scheduler, notification queues
18. Read-path vs write-path: materialised views
19. Choosing quickly: need to block

## 1. Load balancer
- Use when: more than one web/app server, or one server is a capacity limit or SPOF.
- Do not use when: a single node meets the numbers and the outage risk is accepted.
- How: public IP for the LB; servers on private IPs; health checks drive failover; pool grows and shrinks.
- Trade-offs: the LB becomes a SPOF (run redundant LBs that monitor each other by heartbeat, as in the Drive design); stateful servers force sticky sessions (avoid: make the tier stateless).
- Verify: kill a server; traffic continues. Kill the active LB; the secondary takes over. (inferred)
- Depth: `arch-api-design` (gateways), `arch-production-operations` (load balancing and shedding).

## 2. Cache (read-through) and eviction
- Use when: data is read often and modified rarely; the same reads repeat; expensive results (DDIA's definition of a cache: remember expensive results).
- Do not use when: the cache would hold the only copy; strong consistency is required between cache and DB and you cannot invalidate on write.
- Pattern: check cache; hit returns; miss reads DB, populates cache, returns.
- Parameters: expiry/TTL (too short = constant reloads; too long = stale), size (over-provision for a buffer), eviction policy (LRU most popular, LFU, FIFO).
- Consistency: DB write and cache update are not one transaction. Drive's design requires strong consistency, so it keeps cache replicas consistent with the master and invalidates the cache on every DB write.
- Failure: one cache server is a SPOF; use several across data centers. A cache miss storm follows a node loss (compare consistent hashing).
- Layered caches (news feed): feed (IDs only), content (post data, hot cache for popular), social graph, action (liked/replied), counters.
- Browser caching of API responses (autocomplete): a private max-age header of an hour lets the client skip repeated calls.
- Verify: hit ratio tracked; TTL and invalidation path documented; DB-down behaviour known (stale serve or fail); no important data only in cache.
- Related: DDIA treats caches, indexes and materialised views as derived data (see `foundational-choices.md`).

## 3. CDN
- Use when: static or large media assets and distant users; egress from origin is costly or slow.
- Do not use when: assets are rarely requested (cost is per transfer) or content is personalised and not cacheable (dynamic caching is out of the book's scope).
- Parameters: TTL, invalidation (vendor API or versioned URLs such as `image.png?v=2`), origin fallback.
- Cost warning (SDI ch. 14): CDN egress dominates video platform cost (about $150,000/day in the estimate). Long-tail strategy: serve popular videos from the CDN, the rest from your own storage servers; encode fewer versions of unpopular content; do not distribute region-specific content to other regions; very large operators build their own CDN with ISP partnerships.
- Verify: clients fall back to origin when the CDN is down; hit ratio and egress cost per day tracked.

## 4. Message queue and workers
- Use when: slow or unreliable downstream work (third-party providers, media processing), decoupling so tiers scale separately, smoothing spikes (enqueue deliveries, appear later, reads stay fast).
- Do not use when: the caller needs the result synchronously and latency budget is tight.
- Pattern: one queue per task type or channel, so an outage of one downstream does not block others (notification system: iOS push, Android push, SMS, email).
- Reliability rules from the notification design:
  - Persist the request to a durable log before sending (delay and reordering are acceptable, loss is not).
  - Exactly-once delivery is not achievable in a distributed setting; reduce duplicates by deduplicating on event ID (drop if seen, else send).
  - Retry a bounded number of times by re-enqueueing; alert people if failure persists.
  - Watch queue depth: a large backlog means too few or too slow workers; scale workers on depth.
  - Authenticate who may call the send API (appKey/appSecret) and rate-limit per user (frequency capping).
- Verify: kill one provider and confirm the other channels flow; replay the same event ID and see a single send; queue-depth alarm exists; retries have a cap and a dead-letter or alert path. (inferred)
- Depth: `arch-data-pipelines` (delivery semantics, idempotent sinks), `arch-transactions` (idempotency and retries).

## 5. Rate limiter

Use when: protecting against abuse, DoS, accidental overload, cost of paid third-party calls; reviewing any public API without limits.
Do not use client-side as the only control: requests can be forged.

Placement: server-side middleware or API gateway (gateway also does TLS termination, auth, IP allow-listing). Over-limit requests receive HTTP 429.
Decision guidelines from the book: check your stack's efficiency for it; choose the algorithm you need (third-party gateways restrict choices); if you already have microservices and a gateway, add it there; if engineering capacity is short, prefer a commercial gateway.

| Algorithm | Mechanics | Parameters | Pros | Cons |
|---|---|---|---|---|
| Token bucket (used by Amazon, Stripe) | Bucket of fixed capacity; refill at a fixed rate; overflow discarded; each request takes a token, none left means drop | bucket size, refill rate | simple, memory-efficient, allows short bursts | two parameters are hard to tune |
| Leaking bucket (Shopify) | FIFO queue of fixed size; enqueue if room else drop; processed at a fixed outflow rate | queue size, outflow rate | memory-efficient, stable outflow | a burst fills the queue with old requests so recent ones are limited; two parameters |
| Fixed window counter | Counter per fixed window; drop at threshold until next window | window, limit | memory-efficient, easy to understand, quota-reset semantics | spikes at window edges let through up to 2x the quota (5/min: 5 in the last 30 s of one minute plus 5 in the first 30 s of the next = 10 in a 60 s span) |
| Sliding window log | Keep timestamps (Redis sorted set); drop older than window start; accept if log size is within limit | window, limit | exact in any rolling window | high memory: rejected requests' timestamps are also stored |
| Sliding window counter | Rolling count = current window count + previous window count x overlap percentage | window, limit | smooths spikes, memory-efficient | approximation assuming even spread in the previous window; Cloudflare measured 0.003% of 400M requests wrongly allowed or limited |

Sliding window counter example: limit 7/min, previous 5, current 3, 30% into the current minute: 3 + 5 x 0.7 = 6.5, round down to 6, allowed.
Bucket count (token bucket): one per endpoint per user (1 post/s, 150 friend-adds/day, 5 likes/s = 3 buckets per user); one per IP when throttling by IP; one global bucket for a global cap. Flash-sale burst traffic: use token bucket.

Architecture: counters live in an in-memory store (Redis), not a disk database: INCR (+1) and EXPIRE (TTL auto-delete) fit. Rules are config files (Lyft's open-source format: domain, descriptors, unit, requests per unit; e.g. marketing 5/day, login 5/minute) loaded by workers into a cache; middleware loads rules, reads counter and last-request time, and passes, or returns 429 and either drops the request or sends it to a queue for later.
Headers: `X-Ratelimit-Limit`, `X-Ratelimit-Remaining`, `X-Ratelimit-Retry-After`; throttle response is 429 plus Retry-After.

Distributed issues:
- Race condition: read counter, check, write +1 is not atomic (two concurrent requests both read 3 and both write 4). Locks fix it but slow the system; use a Redis Lua script (atomic) or sorted sets.
- Synchronisation across limiter servers: sticky sessions do not scale; use a centralised store (Redis) shared by all limiters.
- Latency: multi-DC or edge servers for far users (Cloudflare had 194 edge locations in 2020); sync counters with eventual consistency.
- Monitor: too strict drops valid traffic (relax rules); ineffective under sudden spikes (change algorithm, e.g. token bucket).
- Failure: the limiter must not take down the system if its cache is down. Decide fail-open or fail-closed deliberately (book requires fault tolerance; the choice itself is yours).
Extensions: hard vs soft limits; limiting at other layers (iptables at layer 3 vs layer 7 here). Client best practice: use a client cache, avoid bursts, catch errors and recover, exponential back-off in retries.
Verify: boundary burst test for fixed windows; concurrency test for atomic increment; Redis-down test; 429 with headers present; throttle-rate metric per rule. (partly inferred)
Depth: `arch-api-security` (rate limiting and load shedding design).

## 6. Consistent hashing
- Problem: `hash(key) % N` remaps most keys when N changes, causing a miss storm on the remaining servers.
- Property: on resize only about k/n keys move (k keys, n slots).
- Mechanics: hash space is a ring (for example SHA-1, 0 to 2^160-1); hash servers onto the ring; hash keys onto the ring; a key belongs to the first server clockwise. Add a server: only keys between it and its predecessor move to it. Remove: its keys go to the next server clockwise.
- Problems of the basic ring: uneven arc sizes, non-uniform key distribution. Fix: virtual nodes (each physical server at many positions). With 100 virtual nodes the standard deviation was about 10% of the mean; with 200 about 5% (experiment cited in the book). Cost: memory for vnode metadata. Capacity-proportional vnode counts handle heterogeneous hardware.
- Limits: it spreads keys, not load from a single extremely hot key, which still lands on one node.
- Used in: Dynamo-style partitioning, Cassandra, Discord, Akamai CDN, Maglev.
- Use when: nodes join/leave at runtime and remapping is costly (sharded caches, partitioned stores, affinity load balancing). Plain modulo is acceptable for a fixed N or when rebuilding is trivial.
- Verify: after adding/removing a node, the moved fraction is about 1/n; per-node load spread within target with enough vnodes; replica placement uses distinct physical nodes. (inferred)
- Depth: `arch-replication-and-consistency` (sharding, rebalancing).

## 7. Sharding key choice
- Must distribute evenly and let queries route to one shard. Measure skew.
- Autocomplete lesson: sharding by first letter gives uneven shards (many more words start with c than x); use a shard map manager that maps prefix ranges to shards based on historical distribution.
- Hot keys (celebrities): own shard or sub-partitions.
- Joins across shards: denormalise.
- Resharding: consistent hashing.

## 8. Unique ID generation

| Option | Pros | Cons |
|---|---|---|
| Multi-master auto-increment (step k) | numeric, scales with DB count | hard across data centers, IDs not time-ordered across servers, breaks when servers added/removed |
| UUID (128-bit) | no coordination, scales with web tier, negligible collision odds | 128 bits (need 64), not time-ordered, may not be numeric |
| Ticket server (Flickr-style central DB) | numeric, easy, fine for small/medium scale | SPOF; multiple ticket servers bring sync problems |
| Snowflake-style | 64-bit, time-sortable, no central coordination, 10,000+/s easily | needs clock sync; node IDs must be assigned uniquely |

Snowflake layout: 1 sign bit (0), 41 bits timestamp (ms since a custom epoch; about 69 years), 5 bits data center ID (32), 5 bits machine ID (32 per DC), 12 bits sequence (4096 per ms per machine, reset every ms).
Datacenter and machine IDs are fixed at startup; changing them risks ID conflicts. Pick a custom epoch near now to delay overflow. Tune section lengths: fewer sequence bits and more timestamp bits for low-concurrency long-lived systems.
Clock: design assumes synchronised, monotonic clocks (use NTP). Handling clocks that move backwards (refuse or wait) is an inference, not stated.
Selection rule: sortable 64-bit numeric IDs at scale with no coordination: Snowflake-style. No ordering needed and 128 bits fine: UUID. Tiny scale: database auto-increment or ticket server.
Chat variant: message IDs only need ordering within a channel or 1:1 pair, so a local sequence generator per channel suffices.
Verify: uniqueness across simulated machines; monotonic per machine; behaviour at ms rollover and sequence overflow (wait for the next ms); clock-skew test; audit of machine-ID assignment. (inferred)
Depth: `arch-replication-and-consistency` (ids and clocks).

## 9. Fan-out
Fan-out = factor by which one request becomes many downstream requests (DDIA).

| | Fan-out on write (push) | Fan-out on read (pull) |
|---|---|---|
| Computed | at post time, delivered into each follower's cache | at read time |
| Pros | real-time feed, fast reads | no wasted work for inactive users; no hot-key problem |
| Cons | heavy for accounts with many followers; wasted work on inactive users | slow reads, nothing precomputed |

Hybrid: push for most users; pull for accounts with huge follower counts (followers fetch them at read time and merge). Choose the threshold from the follower distribution. A user following very many accounts may get a lossy (sampled) timeline; a celebrity's posts must not be dropped.
Mechanics: fanout workers consume from a queue; cache stores IDs only (bounded per-user length) and hydrates from content caches; filter mutes and privacy settings before writing.
Verify: feed fetch p99, post-to-appearance lag, queue depth during a celebrity post, mute filtering, cache length cap. (inferred)

## 10. Real-time delivery

| Mechanism | How | Use when | Drawbacks |
|---|---|---|---|
| Polling | Client asks periodically | simplest; data changes constantly | wasteful, mostly "no" answers |
| Long polling | Hold request open until data or timeout, then re-request | updates are infrequent and one-directional (Drive notifications; Dropbox did this) | sender and receiver may hit different servers; server cannot tell the client left; inefficient for quiet users |
| WebSocket | Client-initiated, bidirectional, persistent, upgrade from HTTP, works on 80/443 | chat-like bidirectional traffic | persistent connections make connection management critical; stateful servers |

Chat design: WebSocket for both send and receive; plain HTTP for sign-up, login and profile. 1M concurrent connections at about 10 KB each is roughly 10 GB, so a single server could hold it, but one server is a SPOF.
Notification-server failure (Drive): one server may hold over 1M long-poll connections; when it fails they all reconnect elsewhere, which is slow. Expect a reconnect storm; throttle or stagger reconnects (inferred).

## 11. Presence and heartbeats
- Set online with a last-active timestamp on login, offline on logout. For disconnects use a heartbeat: client sends one periodically (example 5 s); if none within a timeout (example 30 s) mark offline. This avoids flapping on brief drops (tunnel).
- Fan-out presence changes by pub/sub with a channel per friend pair. For huge groups (100,000 members would mean 100,000 events per change) fetch status only on entering the group or on manual refresh.

## 12. Blob/object storage, chunking, delta sync, dedupe
- Use object storage for large files with cross-region replication; keep metadata (users, files, blocks, versions) in a separate ACID database (Drive) or a sharded/replicated DB plus cache (video).
- Block servers split files into blocks (max 4 MB in the Dropbox example), compress, encrypt, upload; each block's hash is in metadata; reconstruct by joining blocks in order.
- Delta sync: transfer only changed blocks; compression (gzip/bzip2 for text, others for media).
- Dedupe blocks by hash at account level (verify dedupe never crosses account boundaries (inferred)).
- Versions: immutable version rows; cap the number of versions and keep valuable ones (heavily edited documents could otherwise keep 1000+); move rarely used data to cold storage (Glacier-like).
- Resumable upload for large files; pre-signed upload URLs so clients upload directly to storage with scoped permission (S3; Azure calls it Shared Access Signature).
- Direct-to-storage client uploads are faster (one hop) but need chunking, compression and encryption re-implemented on every client platform and client-side encryption is untrustworthy because clients can be hacked; the book chose block servers.
- Conflicts: first version processed wins; the later writer gets a conflict and sees both copies to merge or override. Real-time co-editing is a separate hard problem.
- Verify: reconstruct from blocks equals original hash; delta sync uploads only changed blocks; two simultaneous edits produce a conflict; resumable upload resumes at the right byte. (inferred)
- Depth: `arch-data-storage`.

## 13. Search suggestion (trie)
- Trie: node per character, frequency at terminal nodes. Naive top-k costs prefix lookup O(p) plus subtree traversal O(c) plus sort O(c log c).
- Optimisations: cap prefix length (for example 50) so the lookup is O(1); cache the top-k at every node (space for time).
- Serving: read from a distributed trie cache; fall back to the trie DB; filter layer in front of the cache removes banned suggestions at serve time, and deletes physically in the DB so the next rebuild is clean.
- Updates: rebuild weekly from aggregated logs and swap (preferred); in-place updates are slow because every ancestor caches top-k.
- Data gathering offline: append-only analytics logs, aggregators by time window, workers build the trie, persist to Trie DB (document store snapshot or key-value store keyed by prefix) and snapshot to cache.
- Latency: target under about 100 ms; browser caching; sample logging of 1 in N requests.
- Trending/real-time needs a different path (stream processing, weight recent queries higher).
- Verify: p99 under target; top-k after rebuild equals the frequency table; banned terms never served; shard balance. (inferred)

## 14. Quorum replication, vector clocks and repair (key-value store, SDI ch. 6)
- CAP framing used by the book: partitions are unavoidable, so the real choice during a partition is CP (block writes to avoid divergence, e.g. banks) or AP (keep accepting, reconcile later). The book states that CA systems cannot exist in the real world; treat this as a simplification and read `arch-replication-and-consistency` for the precise view.
- N replicas, W write acks, R read responses. W+R > N gives strong consistency (typical N=3, W=R=2). R=1, W=N: fast reads. W=1, R=N: fast writes. W+R <= N: no strong guarantee. W=1 means the coordinator returns after one ack, not that one copy is written.
- Replicas: walk the ring clockwise and take the first N distinct physical servers; place in different data centers.
- Conflicts: vector clocks, [server, counter] pairs; X is an ancestor of Y if every counter in Y is at least that in X, otherwise they conflict and the client reconciles; cap the vector length (dropping oldest may blur ancestry; Dynamo reported no problem in production). Last-write-wins is a simplification not discussed in the book (inferred).
- Temporary failure: sloppy quorum takes the first healthy servers; a stand-in stores data and hands it back later (hinted handoff).
- Permanent failure: anti-entropy with Merkle trees; compare roots, descend into differing children, sync only differing buckets (about 1M buckets per 1B keys).
- Failure detection: gossip (see section 15).
- Storage path (Cassandra-like): write to commit log, then memtable, flush to SSTable; read memtable, then Bloom filter to choose SSTables, then read them.
- Choose: strict correctness (money, inventory): CP, W+R>N. Always-on writes (carts, profiles): AP, eventual, vector clocks. Read-heavy: R=1, W=N.
- Verify: property tests on vector-clock comparison; chaos tests that kill nodes (hinted handoff delivers; Merkle repair converges); check W+R>N on strong paths; replica placement across DCs or racks. (inferred)

## 15. Failure detection and service discovery
- Failure detection: need at least two independent sources before marking a node down. All-to-all multicast is simple but inefficient at scale. Gossip: each node keeps a membership list (id and heartbeat counter), bumps its own counter, sends heartbeats to random nodes who propagate; no counter increase for a period means offline, confirmed by other nodes.
- Service discovery (chat): a registry (the book uses ZooKeeper) of chat servers; picks the best server for the client by location and capacity; client then opens its persistent connection. On server failure discovery assigns a new server and the client reconnects.

## 16. "Seen" structures
- Bloom filter: cheap membership test with false positives. Uses: avoid a DB existence lookup for hash collisions (URL shortener approach A), URL-seen check in a crawler, choosing which SSTables to read.
- Content hash: compare hashes instead of full pages (about 29% of crawled pages are duplicates).
- Use when exactness is not required; know the false-positive tolerance. (inferred for the tolerance point)

## 17. Pipelines
- DAG media pipeline (video): preprocessor splits into GOP segments and builds the DAG from configuration; DAG scheduler splits it into stages of tasks in a task queue; resource manager holds task queue, worker queue and running queue with a task scheduler; task workers run tasks; temporary storage holds intermediates; outputs are renditions per resolution. Completion queue and handler update metadata and cache.
- Crawler frontier: front queues for priority, back queues for per-host politeness, hybrid memory/disk storage.
- Offline aggregation (autocomplete): logs, aggregator, builder, snapshot, cache.
- Depth: `arch-data-pipelines`.

## 18. Materialised views and derived data
Caches, trie snapshots, feed caches and search indexes are derived data: redundant, losable, rebuildable from a system of record, and needing a defined update process. Label every store as system of record or derived and give each derived one a rebuild path (`foundational-choices.md`).

## 19. Choosing quickly: need to block

| Need | Block |
|---|---|
| Survive web server loss | load balancer plus stateless tier |
| Survive DB loss | replication plus failover drill |
| Same reads repeat | read-through cache |
| Static or media for distant users | CDN with origin fallback |
| Slow or flaky downstream | queue, workers, retries, dedupe |
| Abuse or overload protection | rate limiter at gateway |
| Dynamic pool of cache/data nodes | consistent hashing with vnodes |
| Sortable unique ids without a coordinator | Snowflake-style |
| Feed with skewed followers | hybrid fan-out |
| Server push to clients | WebSocket (bidirectional) or long polling (infrequent one-way) |
| Large files, flaky mobile links | chunking, resumable upload, delta sync, pre-signed URLs |
| Low-latency prefix suggestions | trie with per-node top-k, offline rebuild |
| Cheap duplicate check | Bloom filter or content hash |
