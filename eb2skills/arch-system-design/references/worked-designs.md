# Worked designs to adapt

Eleven designs from System Design Interview (SDI) chapters 4-15, plus pointers to the two other worked cases (home timelines in
`requirements-and-nfrs.md` section 8; the ad click-through dashboard in `nalsd-method.md`). Each entry gives requirements, numbers, key decisions with
the alternatives that were rejected, failure handling, and what to verify. They are interview-scale designs: use them as a pattern library and a source of
questions, not as production specifications. Lines marked (inferred) are verification ideas added by the note-taker.

## Contents
1. Rate limiter (SDI ch. 4)
2. Key-value store (ch. 6)
3. Unique ID generator (ch. 7)
4. URL shortener (ch. 8)
5. Web crawler (ch. 9)
6. Notification system (ch. 10)
7. News feed (ch. 11)
8. Chat system (ch. 12)
9. Search autocomplete (ch. 13)
10. Video platform (ch. 14)
11. File storage and sync (ch. 15)
12. Which design to start from
13. Cross-design patterns

## 1. Rate limiter (SDI ch. 4)
- Requirements: server-side API limiter; flexible rules (IP, user ID, other properties); large request volume; distributed; users told when throttled. Accuracy, low latency, low memory, high fault tolerance (limiter failure must not take the system down).
- Numbers: none needed beyond algorithm parameters; examples from industry: 300 tweets per 3 hours; 300 read requests per user per 60 s.
- Decisions: place at a gateway/middleware (client-side rejected: forgeable). Counters in Redis (INCR, EXPIRE) not a disk DB. Algorithm by need (table in `building-blocks.md` section 5): token bucket for bursts, sliding-window counter for cheap accuracy, fixed window leaks 2x at edges, sliding log exact but memory-heavy. Atomicity via Lua script or sorted sets; centralised Redis rather than sticky sessions.
- Failure: Redis down: decide fail-open or fail-closed explicitly. Rules in config with a worker-refreshed cache.
- Verify: edge-burst test, concurrency test, 429 plus headers, throttle metrics.

## 2. Key-value store (ch. 6)
- Requirements: put/get; small values (under 10 KB); big data; high availability; automatic scaling; tunable consistency; low latency. Based on Dynamo, Cassandra, BigTable.
- Single node: an in-memory hash table, with compression and hot-data-only in memory, runs out of capacity, hence distribute.
- Decisions: AP with eventual consistency chosen (CP for banks). Partition and replicate on a consistent-hash ring (first N distinct physical servers clockwise, across DCs). Tunable N/W/R quorum. Vector clocks for conflicts (client reconciles). Gossip failure detection. Sloppy quorum and hinted handoff for transient failures. Merkle-tree anti-entropy for permanent failures. Write path commit log, memtable, SSTable; read path memtable, Bloom filter, SSTables.
- Summary table (reconstructed by the note-taker): big data, dataset partition, incremental scalability, heterogeneity: consistent hashing; high-availability reads: replication plus multi-DC; highly available writes: versioning and vector clocks; tunable consistency: quorum; temporary failures: sloppy quorum plus hinted handoff; permanent failures: Merkle tree; DC outage: cross-DC replication; failure detection: gossip.
- Every node has the same responsibilities, so there is no SPOF.
- Verify: see `building-blocks.md` section 14.

## 3. Unique ID generator (ch. 7)
- Requirements: unique, numeric, within 64 bits, ordered by date, at least 10,000 IDs/s.
- Options compared: multi-master auto-increment, UUID, ticket server, Snowflake. Chosen: Snowflake (1+41+5+5+12 bits). See `building-blocks.md` section 8 for the table and layout.
- Watch: clock synchronisation (NTP), fixed node IDs, epoch overflow after about 69 years, tuning bit widths.

## 4. URL shortener (ch. 8)
- Requirements: shorten and redirect; 100M new URLs/day; shortest possible; characters 0-9a-zA-Z (62); no delete or update; HA, scalable, fault tolerant.
- Numbers: 1,160 writes/s; 11,600 reads/s (10:1); 365 billion records over 10 years; 36.5 TB at 100 B each (the book itself prints 365 TB, which is a factor of 10 off: 3.65x10^11 x 10^2 B = 3.65x10^13 B); key length 7 (62^7 is about 3.5 trillion; 62^6 about 56.8 billion is not enough).
- API: `POST api/v1/data/shorten` with longUrl returns the short URL; `GET api/v1/{shortUrl}` redirects.
- 301 vs 302: 301 (permanent) lets browsers cache and skip your server, lowering load but losing click analytics; 302 (temporary) sends every click through you, enabling analytics at higher load. Choose by priority.
- Key generation, two approaches:
  - A: hash plus collision resolution: take the first 7 characters of CRC32/MD5/SHA-1 output; on collision append a predefined string to the long URL and rehash. Each attempt costs a DB lookup (mitigate with a Bloom filter). Pros: fixed length, no ID generator. Cons: collisions; DB check per request.
  - B (chosen): base-62 conversion of a unique numeric ID, digits 0-9 then a-z (10-35) then A-Z (36-61) (example: 11157 = 2x62^2 + 55x62 + 59 becomes "2TX"; the ID 2009215674938 becomes "zn9edcu"). Pros: no collisions, no per-request collision check. Cons: variable length; needs a distributed ID generator (`building-blocks.md` section 8); sequential IDs make the next URL guessable (the note flags this as inferred).
- Shorten flow: look up the long URL; if present return the stored short URL (idempotent); otherwise get a new ID, encode, insert (id, short URL, long URL).
- Redirect flow: check cache; on miss read DB; not found means invalid; populate the cache. Reads dominate, so cache is the key.
- Extensions: rate limiter against abuse, stateless web tier, DB replication and sharding, analytics.
- Verify: encode/decode round trip; same long URL gives same short URL; invalid alias returns 404; redirect path hits the cache; collision test for approach A. (inferred)

## 5. Web crawler (ch. 9)
- Requirements: search indexing; 1 billion pages/month; HTML only; new and edited pages; store HTML up to 5 years; ignore duplicates. Qualities: scalability, robustness (bad HTML, unresponsive servers, crashes, malicious links), politeness, extensibility.
- Numbers: about 400 pages/s, peak 800/s; 500 TB/month; 30 PB over 5 years.
- Components: seed URLs (split by locality or topic), URL frontier, HTML downloader (robots.txt, DNS resolver), content parser, content-seen check (hash), content storage (mostly disk, popular in memory), URL extractor (relative to absolute), URL filter, URL-seen (Bloom filter or hash table), URL storage.
- Decisions: BFS with a FIFO queue (DFS depth can be huge). Frontier solves politeness and priority: back queues each hold one host (queue router maps host to queue; a worker downloads sequentially with a delay), front queues prioritise (PageRank, traffic, update frequency; random pick biased to high priority). Freshness by recrawling according to update history. Hybrid memory/disk frontier storage.
- Downloader performance: distributed crawl, DNS cache (lookups take 10-200 ms and block threads), geographically distributed crawlers, short timeouts. Obey robots.txt (cached, refreshed).
- Robustness: consistent hashing to spread load across downloaders; save crawl state; exception handling; data validation. Extensibility: pluggable modules. Problem content: duplicates (hash), spider traps (cap URL length, spot hosts with unusually many pages; no universal automatic fix), data noise (ads, spam).
- Verify: per-host request rate never exceeds the delay; no URL fetched twice within Bloom-filter tolerance; restart resumes from saved state; trap hosts are capped. (inferred)

## 6. Notification system (ch. 10)
- Requirements: push (iOS, Android), SMS, email; soft real-time; triggered by clients or scheduled; users can opt out. Volume per day: 10M push, 1M SMS, 5M email.
- Providers are third parties (APNS, FCM, Twilio/Nexmo, SendGrid/Mailchimp); integrations must be pluggable (FCM is unavailable in China).
- First design and its problems: services call one notification server; SPOF, hard to scale, performance bottleneck.
- Improved: move DB and cache out; several autoscaled notification servers; one queue per notification type; workers per queue calling providers. Notification servers expose authenticated send APIs, validate, fetch data and templates, enqueue.
- Reliability: persist to a notification log; retry a bounded number of times then alert; no exactly-once: dedupe by event ID.
- Extras: templates, opt-in settings table checked before every send, per-user rate limiting, appKey/appSecret authentication, queue-depth monitoring, open/click analytics. Contact info: email and phone in the user table; device tokens in a device table (user has many devices).
- Verify: see `building-blocks.md` section 4.

## 7. News feed (ch. 11)
- Requirements: mobile and web; publish and see friends' posts; reverse-chronological (ranking excluded); up to 5,000 friends; 10M DAU; images and video.
- Flows: publishing (web servers authenticate and rate-limit posts, post service stores in DB and cache, fanout service, notification service) and retrieval (news feed service reads post IDs from the feed cache, hydrates user and post objects from caches, falls back to DB, media from CDN).
- Key decision: fan-out on write vs on read; chosen hybrid (push for most users, pull for celebrities). Table in `building-blocks.md` section 9. Consistent hashing spreads hot-key load.
- Fanout steps: fetch friend IDs from a graph database; filter by settings; put friend list and post ID on a queue; workers write to the feed cache; the cache holds IDs only with a per-user length cap (users rarely scroll thousands of posts).
- Five cache layers: feed, content, social graph, action, counters.
- Verify: feed fetch p99; fan-out lag; celebrity post does not spike the queue; mute filtering; cache cap. (inferred)

## 8. Chat system (ch. 12)
- Requirements: 1:1 and group (max 100); mobile and web; 50M DAU; text under 100,000 characters; online indicator; multi-device; push; history forever.
- Protocol: WebSocket for send and receive (alternatives polling and long polling rejected); plain HTTP for sign-up, login, profile. Stateless services (login, signup, profile, service discovery) behind a LB; stateful chat servers hold connections; third-party push.
- Storage: relational DB (replicated and sharded) for profiles, settings and friends; key-value store for message history (huge volume, mostly recent reads, occasional random access, long tail poorly served by relational indexes). Messages: 1:1 primary key message_id (not created_at, since two messages may share a timestamp); group primary key (channel_id, message_id) with channel_id as the partition key. message_id must be unique and sortable: a per-channel local sequence generator is enough because ordering matters only within a conversation (alternative: global Snowflake).
- Flows: sender to chat server, ID generator, message sync queue, KV store; if recipient online forward to their chat server over WebSocket, else push notification. Multi-device sync by per-device `cur_max_message_id`. Small groups copy each message into every member's inbox (simple sync, fine for small groups, not for huge ones).
- Presence: heartbeat with timeout; pub/sub per friend pair; huge groups fetch on demand.
- Failure: chat server down: service discovery assigns a new one and the client reconnects; retries with queues for resend.
- Verify: ordering within a channel; offline delivery after reconnect; heartbeat timeout; failover without duplicates; connections per server. (inferred)

## 9. Search autocomplete (ch. 13)
- Requirements: prefix match, top 5 by historical frequency, no spell check, English lowercase, 10M DAU, under about 100 ms.
- Numbers: about 24,000 QPS, peak about 48,000; about 0.4 GB new data/day.
- Baseline: frequency table with a SQL `LIKE 'prefix%' ORDER BY frequency DESC LIMIT 5` query (reconstructed form); fine small, a bottleneck at scale. Chosen: trie with top-5 cached per node and a capped prefix length; offline weekly rebuild from aggregated logs; trie DB plus trie cache; serve from the cache; filter layer for banned terms; shard by a shard map (not by first letter).
- Details in `building-blocks.md` section 13. Extensions: multi-language (Unicode nodes), per-country tries (possibly in CDNs), trending queries (stream processing, weight recent queries).

## 10. Video platform (ch. 14)
- Requirements: upload and watch; mobile, web, smart TV; 5M DAU, 30 min/day; international; most formats; encryption; max 1 GB; build on existing cloud CDN and blob storage.
- Numbers: 150 TB/day storage; CDN egress about $150,000/day (dominant cost).
- Components: client, CDN, API servers (all but streaming), metadata DB (sharded and replicated) and cache, original storage (blob), transcoding servers, transcoded storage, completion queue and handler.
- Upload flow: two parallel processes: upload the video (original storage, transcoding, transcoded storage to CDN, completion event updates metadata) and update metadata concurrently.
- Streaming: continuous delivery of small pieces over a protocol (MPEG-DASH, Apple HLS, Smooth Streaming, HDS) from the nearest CDN edge.
- Transcoding: container plus codec; DAG model (stages run sequentially or in parallel: inspection, encodings, thumbnail, watermark); six-part architecture (preprocessor with GOP segments, DAG scheduler, resource manager with task, worker and running queues, task workers, temporary storage, encoded output).
- Optimisations: speed (GOP-aligned parallel resumable chunk uploads, upload centers near users, queues between stages); safety (pre-signed upload URL, DRM, AES encryption with authorisation, watermark); cost (long tail: popular videos on CDN, others from own storage, fewer encodings of unpopular content, on-demand encoding of short videos, regional distribution only where needed).
- Error playbook: recoverable (retry then error code) vs non-recoverable (stop, error). Upload error retry; split error pass the whole video to the server; transcoding error retry; preprocessor error regenerate the DAG; scheduler error reschedule; resource-manager queue down use the replica; worker down retry on another; API server down stateless re-route; metadata cache down replicas and replacement; metadata DB leader down promote a follower; follower down use another and replace.
- Live streaming needs lower latency, different protocol, less parallelism, faster error handling; takedowns via upload-time detection or user flags.
- Verify: each rendition plays on target devices; chunk resume; idempotent completion handler; CDN hit ratio and egress cost; uploads only via valid pre-signed URLs. (inferred)

## 11. File storage and sync (ch. 15)
- Requirements: upload/download, multi-device sync, revisions, sharing, notifications; encrypted at rest; max file 10 GB; 10M DAU; reliable (loss unacceptable), fast sync, low bandwidth. Out of scope: real-time collaborative editing.
- Numbers: 500 PB allocated; upload QPS about 240, peak 480.
- Build-up: see the ladder replay in `scaling-ladder.md` section 5.
- APIs (HTTPS and auth): upload with `uploadType=resumable`, download by path, list revisions.
- Components: block servers (split, compress, encrypt, upload; block hash in metadata), object storage, cold storage, LB, API servers, metadata DB (users, devices, namespaces, files, file versions, blocks), metadata cache, notification service (pub/sub), offline backup queue.
- Consistency: strong, because a file must not look different to different clients. Relational DB for native ACID, cache replicas kept consistent, invalidate on write.
- Flows: upload as two parallel requests (metadata "pending" then "uploaded" after storage callback; content through block servers); download by notification or pull on reconnect, then metadata, then blocks.
- Notification: long polling (traffic one-way and infrequent, no bursts) rather than WebSocket.
- Saving storage: dedupe by hash, cap versions, cold storage.
- Failure handling per component (LB secondary, block servers re-picked, cross-region storage replicas, stateless API, cache replicas, DB leader promotion, notification reconnects, replicated offline queue).
- Alternative: direct-to-storage client upload (rejected, see `building-blocks.md` section 12).

## 12. Which design to start from

| Your problem resembles | Start with |
|---|---|
| Public API needing abuse protection | Rate limiter |
| Distributed store, sharding, replication choice | Key-value store |
| Need unique sortable keys | ID generator; URL shortener for key encoding |
| Read-heavy lookup with a cache path | URL shortener |
| Bulk fetching with politeness and dedupe | Crawler |
| Outbound messages through unreliable providers | Notification system |
| Social timeline, skewed follower counts | News feed |
| Bidirectional real-time messaging | Chat |
| Low-latency typeahead | Autocomplete |
| Large media with processing pipeline and heavy egress | Video platform |
| File sync, chunking, versions, offline clients | File storage and sync |
| Resource sizing from SLOs on a data pipeline | NALSD (`nalsd-method.md`) |

## 13. Cross-design patterns

- Separate the write path from the read path and design each (feed, chat, video upload vs stream).
- Queue-decouple anything slow or third-party (notifications, transcoding, fan-out, trie building).
- Cache IDs or snapshots, hydrate on read.
- Precompute for the common case and handle the heavy tail separately (hybrid fan-out, popular-only CDN).
- Identify the cost driver early (CDN egress for video; disk IOPS in NALSD) and design around it.
- Every design finishes with a component-by-component failure table.
