---
name: arch-system-design
description: Procedure and references for designing a system from a problem statement - clarifying requirements, non-functional requirements with numbers, back-of-envelope estimation, the scaling ladder from one server to multi-region, reusable building blocks (cache, CDN, queue, rate limiter, consistent hashing, ID generation, fan-out, WebSocket), the possible/better/feasible/resilient sizing method, and worked designs to adapt (feed, chat, URL shortener, notifications, file sync, video, autocomplete, crawler, key-value store). Use when asked to "design X", review or document an architecture, estimate QPS, storage or server counts, translate nines into downtime, decide where to add a cache, queue, replica, shard or CDN, or write a design doc. For recording decisions use arch-decisions-and-tradeoffs; for depth on replication, transactions, pipelines, APIs or SLOs use the specific arch skills.
---

# System design from a problem statement

## Purpose

Use this to go from a vague "design a system that does X" (or "is this architecture sound?") to a design whose claims are backed by numbers: scoped
requirements, estimates that say which components are needed, the simplest structure that meets them, and a failure analysis. It stops the two usual
errors: jumping to a favourite architecture before the numbers exist, and adding distributed machinery that no number justifies. It hands off to the
specific arch skills when one component needs depth.

## Choose what applies

| The request or situation | Do this | Read |
|---|---|---|
| "Design X" with an open-ended problem statement | Full procedure below (steps 1-8) | `references/design-procedure.md` |
| Requirements are vague, missing numbers, or only functional | Step 1 and the NFR table | `references/requirements-and-nfrs.md` |
| "How many servers / how much storage / what QPS / how much will it cost" | Estimation recipe (step 2) | `references/estimation.md` |
| "Will this scale?", a system is slow, overloaded or a SPOF | Diagnose with the scaling ladder (step 3) | `references/scaling-ladder.md` |
| Need to pick or review a component (cache, CDN, queue, limiter, hash scheme, ID scheme, push mechanism, fan-out) | Building-block entry | `references/building-blocks.md` |
| Sizing from SLOs, "does this fit on N machines", multi-DC capacity arithmetic | Iterate possible, better, feasible, resilient with arithmetic | `references/nalsd-method.md` |
| The problem resembles feed, chat, notifications, URL shortener, crawler, video, file sync, autocomplete, KV store, ID service, rate limiter | Start from the closest worked design | `references/worked-designs.md` |
| OLTP vs analytics, system of record vs derived data, cloud vs self-host, monolith vs distributed, privacy constraints | Foundational choices first | `references/foundational-choices.md` |
| "Describe/document the architecture" or "justify this style choice" | Four-dimension description | `references/architecture-framing.md` |
| A small, local change ("add caching to this endpoint", "retry this call") | Check only the one relevant rung/block and its verify list; do not produce a full design | `scaling-ladder.md` section 2, `building-blocks.md` |

This does not apply, or another skill leads, when:
- The task is recording or governing a specific decision (ADR format, trade-off analysis, fitness-function catalogue): use `arch-decisions-and-tradeoffs`.
- The question is whether and how to split or merge services, or migrate a monolith: `arch-decomposition`.
- The question is replication lag, quorum details, sharding mechanics, clocks, consensus: `arch-replication-and-consistency`; isolation anomalies and transactions: `arch-transactions`.
- Storage engines, data models, encoding: `arch-data-storage`. Batch, streams, CDC, derived-data sync: `arch-data-pipelines`.
- REST/gRPC/GraphQL choice, gateways, versioning: `arch-api-design`; threat modelling, OAuth, rate-limit security: `arch-api-security`.
- Defining SLIs/SLOs and alerts: `arch-reliability-slos`; rollouts, overload, incidents: `arch-production-operations`; scaling model fitting (USL): `arch-scalability-analysis`.
- Distributed workflows, sagas, data ownership across services: `arch-distributed-workflows`.
- It is a code-level design question (classes, modules): the craft skills, not this one.

## How to apply

### Step 1: scope and requirements
1. List what is in and out of scope. Ask only for answers that would change the architecture; for the rest write an assumption with its sensitivity ("if DAU is 10x, the cache becomes mandatory").
2. Cover: features, users and DAU, growth, clients, limits (max group size, file size, friends), ordering/ranking, media, traffic shape and skew, existing stack to reuse, regions, retention and deletion obligations.
3. Write the non-functional table: latency as a percentile with a measurement point, freshness, availability, durability, consistency per data type, recovery scope, compliance. Every row gets a number or an explicit assumption (`requirements-and-nfrs.md` section 2).
4. Name the load parameters (requests/s, GB/day, read:write ratio, followers per user, peak concurrency) and ask whether the average or an extreme sets the load.

### Step 2: estimate before drawing detail
Recipe (SDI ch. 2): users, then DAU, then actions per user per day, then QPS = events/day / 86,400 (about 10^5), then peak = 2 x average, then
storage = bytes per record x records per day x retention, then cache, servers, bandwidth. Round hard, label units, write assumptions.
Compare the result with one machine's capacity and with the latency numbers before deciding anything (`estimation.md`).

Two quick conversions: 1M requests/day is about 12 QPS; 99.9% availability is about 8.8 hours of downtime a year (full nines table in `estimation.md`).

### Step 3: start simple and climb the ladder only as numbers demand
Start from the simplest design that meets the numbers (often one server plus a replica). Add a rung when you can name the number or incident that requires it:

| Trigger | Rung |
|---|---|
| Single point of failure in the web tier | Load balancer, 2+ web servers |
| DB is a SPOF or read-bound | Leader/follower replication, route writes to leader, reads to followers |
| Same data read repeatedly, read-heavy | Read-through cache (TTL, eviction, invalidation decided) |
| Static/media assets, distant users | CDN with origin fallback |
| Need to add servers or autoscale | Make the web tier stateless; sessions in a shared store |
| Distant users or region outage | Multiple data centers with geo routing and cross-DC data sync |
| Slow or third-party work in the request path | Queue plus workers (retries, dedupe, backlog metric) |
| Cannot see what is happening | Logs, metrics, automated deploys per tier |
| Write load or data size beyond one DB at its largest | Shard (last, hardest; choose key for even spread) |

Counter-pressure (DDIA ch. 1-2): prefer a single node until a named reason applies (fault tolerance, scale, latency, compliance); plan at most about one order of
magnitude ahead; microservices solve a people problem, not a load problem. Full ladder with triggers, costs and verification: `scaling-ladder.md`.

### Step 4: draw the flows and pick building blocks
1. Split the system into a write path and a read path (feed publishing vs retrieval; upload vs stream; send vs receive).
2. For each hop choose a block using the cues in `building-blocks.md` section 19. Defaults that came up repeatedly:
   - Sharded or cached node pools that change size: consistent hashing with virtual nodes; never `hash(key) % N` on a pool that resizes.
   - Public API: rate limiter at the gateway, 429 with Retry-After; token bucket if bursts are legitimate; atomic counters in a shared store.
   - Skewed fan-out (followers, group size): push for the common case, pull or merge-at-read for the heavy tail.
   - Server push to clients: WebSocket for bidirectional chat-like traffic; long polling when updates are infrequent and one-way.
   - Unique sortable 64-bit IDs without a coordinator: Snowflake-style (time, node, sequence); UUID if order and size do not matter.
   - Slow or third-party work: one queue per task type, bounded retries, dedupe by event ID (exactly-once is not achievable), persist before send.
   - Large files: chunk, hash blocks, dedupe, delta sync, resumable and pre-signed uploads, cold tier for old data.
3. Label each store system of record or derived and give each derived store a rebuild path (`foundational-choices.md` section 2).
4. For consistency choose per data type: strict (money, inventory) vs always-on writes (carts, feeds). Quorum rule: W + R > N gives strong consistency; the cost is latency or availability on partition (`building-blocks.md` section 14; precision in `arch-replication-and-consistency`).

### Step 5: size it with the iterative method (when the numbers are hard or the system is large)
Ask in order: is it possible (without magic)? can it be simpler or better? is it feasible at scale within budget? is it resilient to a node and a data center
failing? After each iteration do the arithmetic for storage, IOPS, RAM, network; compare to a stated reference machine; list SPOFs; then pick the next scaling move
(streaming vs batch, lookup store plus joiner, shard by the key known at read/write time, replicate shards on different machines, multi-DC with consensus).
Keep rejected designs and why. Worked arithmetic: `nalsd-method.md`.

### Step 6: deep-dive only where risk lives
Pick the one to three components that decide success (key generation for a shortener, fan-out for a feed, politeness for a crawler, presence for chat). For each: options,
choice, cost, and what would make you switch. Do not polish components that are not on the critical path.

### Step 7: failure and operations pass
For every component write: what fails, what the user sees, how it recovers. Cover single server, queue consumer, cache, DB leader, third-party provider, data center, and
overload (retry storms: backoff with jitter, circuit breaker, load shedding). Add the metrics that drive scaling and alerts (peak QPS, latency percentiles, queue depth, error rate, cache hit ratio). Hand SLO and alert design to `arch-reliability-slos`.

### Step 8: write it up
Use the document skeleton in `design-procedure.md` section 7: scope, NFR table, assumptions and number sheet, diagram and flows, deep dives with alternatives, failure table,
operations, rejected designs, next scale step. Hand the two or three decisions that matter most to `arch-decisions-and-tradeoffs` for ADRs. Every recommendation names what it gives up.

## Verify

Check the design as an artifact; a design you cannot check against these is not finished.

1. Re-derive every number from its stated assumptions, with units. Confirm peak is stated (2 x average or a justified figure), storage includes retention, replicas and indexes,
   and the result is compared to one machine's capacity. Show the number sheet to the user.
2. Requirement-check table: each NFR row maps to the component or property that satisfies it (`nalsd-method.md` section 4). Any row with no owner is a gap.
3. SPOF audit: list every component (web, LB, DB, cache, queue, DC, third party) with the effect of its loss and the recovery. No unexplained "single instance".
4. Statelessness test: could any web server be killed with no user-visible session loss? If the design says yes, name where the state lives.
5. Data-store audit: every store labelled system of record or derived; every derived store has a rebuild path; no analytics on the OLTP primary; no important data only in a cache.
6. Cache and CDN audit: TTL, eviction, invalidation on write, behaviour when the cache is down, CDN fallback to origin.
7. Shard audit: key chosen for even distribution, skew measured or estimated, hot-key plan, cross-shard joins avoided on hot paths, resharding method named.
8. Async audit: each queue has a backlog metric that drives scaling, a retry cap with alerting, dedupe on a stable event ID, and durable persistence before send.
9. Overload audit: retries use backoff with jitter; there is a rate limit or load shedding at the edge; failure of the limiter itself has a stated open/closed policy.
10. Trade-off audit: for each major choice the document names the alternative rejected and what the choice costs. A choice with no stated cost has not been analysed.
11. If you also implement a component, test its distinguishing property: rate limiter (window-edge burst, concurrent increments are atomic, 429 plus headers, store-down behaviour); ID generator (uniqueness across nodes, monotonic per node, sequence overflow, clock regression); consistent hashing (moved fraction near 1/n on resize, load spread); queue consumer (duplicate event ID sends once; retry cap reached triggers alert); resumable upload (resumes at the right byte).

Evidence to give the user: assumptions table, number sheet, diagram, failure table, rejected alternatives, and the list of assumptions most likely to be wrong with what changes if they are.

Done means:
- Requirements are numeric or marked as assumptions; open questions that would change the architecture are called out.
- Every sizing claim is traceable to a formula and an assumption.
- The design is the simplest one that meets the numbers; each added rung has a named trigger.
- Failure behaviour is written down per component; no unexamined SPOF.
- Alternatives and costs are stated for the major decisions; significant ones are handed to an ADR.
- Hand-offs to specific arch skills are listed for components that need depth.

## Proportion and limits

- Match depth to the request. A question about one endpoint needs one rung check, not a document. A greenfield platform design warrants steps 1-8. State at the top which depth you chose.
- Do not estimate to false precision: order of magnitude and assumptions matter more than digits. Replace book numbers with measurements the moment you have them.
- The designs are interview-scale simplifications from a 2020 book and a 2018 SRE workbook. Treat them as pattern libraries; production variants need the specific arch skills.
- The latency table (2010 figures), the nines table and the powers-of-two table are all reconstructed by the note-taker because the book's images did not survive extraction (marked in `estimation.md`); use them for ratios. The machine reference points (64 GB, 200 IOPS, 25 ms consensus) are illustrative assumptions.
- The book's "master/slave" is leader/follower in current usage. Its CAP framing (CA cannot exist, choose CP or AP) is a simplification; use `arch-replication-and-consistency` before making a consistency claim in writing.
- Sources disagree on tempo: SDI climbs the ladder toward sharding and services; DDIA warns against premature scaling and distribution. Rule: climb when a number or incident requires it; otherwise record "next step when X".
- Cloud-vs-self-host cost claims are contested; decide on skills and load predictability. Cloud-native vendor examples are dated; the storage/compute separation principle is what endures.
- Fundamentals of Software Architecture is present only as chapter 1 plus a table of contents; no style ratings or deeper claims are drawn from it.
- Over-engineering is a named red flag in the source: if every rung is in the design and the numbers do not need them, remove rungs.

## References

- `references/design-procedure.md`: the four-step process, scoping checklist, flow decomposition, wrap-up checklist, what to do when nobody can answer questions, design document skeleton. Read at the start of any open-ended design.
- `references/requirements-and-nfrs.md`: NFR table template, percentile and latency vocabulary, fault and failure, hardware fault numbers, scalability architectures, maintainability, retry storms, the home-timeline case. Read when requirements lack numbers or you must choose targets.
- `references/estimation.md`: number tables (marked reconstructed), procedure, formula templates, rules of thumb, estimates from every worked design, sanity checks. Read for any capacity or cost question.
- `references/scaling-ladder.md`: every rung with trigger, change, costs and checks; symptom-to-rung diagnosis; counter-pressure toward single nodes; cloud-era adaptation. Read when deciding what to add or review a system's growth path.
- `references/building-blocks.md`: catalogue of components with when, when not, parameters and verification (rate limiter algorithms table, consistent hashing, ID options, fan-out, push mechanisms, quorum, trie, chunked storage). Read when selecting or reviewing a component.
- `references/nalsd-method.md`: the five-question iterative method with the full ad-dashboard arithmetic and the replayable checklist. Read for resource sizing from SLOs or multi-DC capacity.
- `references/worked-designs.md`: eleven designs with requirements, numbers, decisions, alternatives, failure handling, verification. Read when the problem resembles one of them.
- `references/foundational-choices.md`: OLTP/OLAP, system of record vs derived, cloud vs self-host, single node vs distributed, microservices, privacy as architecture input. Read before choosing the overall shape.
- `references/architecture-framing.md`: structure, characteristics, decisions, principles; the two laws; vitality; match of practice to style. Read when describing or reviewing an architecture rather than designing from scratch.

## Sources

- System Design Interview, 2nd ed. (Xu, 2020): ch. 1 scaling ladder; ch. 2 estimation; ch. 3 framework; ch. 4 rate limiter; ch. 5 consistent hashing; ch. 6 key-value store; ch. 7 ID generator; ch. 8 URL shortener; ch. 9 web crawler; ch. 10 notification system; ch. 11 news feed; ch. 12 chat; ch. 13 autocomplete; ch. 14 video platform; ch. 15 file sync.
- The Site Reliability Workbook (2018): ch. 12 Introducing Non-Abstract Large System Design.
- Designing Data-Intensive Applications, 2nd ed. (Kleppmann and Riccomini, 2026): ch. 1 trade-offs in data systems architecture; ch. 2 defining nonfunctional requirements.
- Fundamentals of Software Architecture, 1st ed. (Richards and Ford, 2020): preface and ch. 1 (excerpt only; remaining chapters known from the table of contents).
