# Requirements and non-functional requirements (with numbers)

How to turn a vague problem into requirements that a design can be checked against. Sources: DDIA 2e ch. 2 (performance,
reliability, scalability, maintainability), System Design Interview ch. 3 and ch. 2 (scoping, availability nines), SRE Workbook
ch. 12 (requirements as SLOs). For defining SLIs, SLO documents and alerting in depth, go to `arch-reliability-slos`.

## Contents
1. Functional vs non-functional
2. Writing an NFR table
3. Performance vocabulary and rules
4. Reliability vocabulary and fault numbers
5. Scalability: load parameters and architectures
6. Maintainability: operability, simplicity, evolvability
7. Overload, retries and metastable failure
8. Case study: home timelines (read-time query vs write-time fan-out)
9. Requirement-driven selection cues
10. Verification checklist

## 1. Functional vs non-functional

Functional: what the screens and operations do. Non-functional: fast, reliable, secure, legally compliant, maintainable. They are
often unwritten, but "an app that is unbearably slow or unreliable might as well not exist" (DDIA ch. 2). Security is out of scope
of the DDIA chapter; see `arch-api-security`. Treat privacy and retention law as inputs too (see `foundational-choices.md`).

## 2. Writing an NFR table

Every non-functional line gets a number, a window or percentile, and a measurement point. Template:

| Concern | Requirement (number) | Measured where | Source of the number |
|---|---|---|---|
| Latency | 99.9% of dashboard queries answered in < 1 s | client side | SRE Workbook ch. 12 example |
| Freshness | 99.9% of the time data is < 5 min old | pipeline output vs event time | same |
| Availability | e.g. 99.9% (about 8.77 h/year of downtime; see `estimation.md`) | at the load balancer / client | negotiated |
| Load | average and peak QPS, peak = 2x average unless known | LB metrics | estimate |
| Data | bytes/record x records/day x retention | storage metrics | estimate |
| Durability | data loss tolerance (none, minutes, hours) | restore test | domain |
| Consistency | which reads may be stale, by how much | per data type | domain |
| Recovery | what happens if a node, a rack or a data center is lost | failure test | |
| Compliance | retention limit, deletion path, residency | audit | legal |

Rules:
- If the requester gave no numbers, propose them as assumptions and label them (design-procedure.md section 6).
- Pick SLO numbers that give you an error budget to compare designs against: the SRE Workbook uses the SLO to judge each
  design iteration (a design that cannot meet the SLO is rejected or changed).
- Durability and availability are different requirements: DDIA ch. 2 stresses that minutes or hours of outage are often tolerable
  but permanent data loss or corruption is catastrophic. Write them as separate lines.

## 3. Performance vocabulary and rules

Exact terms (DDIA ch. 2):
- Response time: elapsed time from request to answer as the client sees it, all delays included.
- Service time: time actively processing the request. Queueing delay: time waiting (CPU, network buffers).
- Latency: catch-all for time the request is latent (not actively processed), such as network latency. Jitter: variation in network delay.
- Throughput: requests/s or bytes/s processed. Response time matters to users, throughput drives resource cost.

Behaviour: response time is low at low throughput and rises sharply as throughput nears capacity (hockey stick). Random delay
sources: context switch, packet loss and TCP retransmit, GC pause, page fault to disk. Head-of-line blocking: a few slow
requests hold up fast ones behind them, and queueing delay is not in service time, so measure response time on the client side.

Rules:
1. Response time is a distribution. Report p50 plus a tail percentile (p95, p99, p999); never only the mean. The mean helps to
   estimate throughput limits but not the typical user experience.
2. Choose the tail percentile by fan-out and value. Amazon sets internal targets at p99.9 because the slowest requests come
   from the customers with the most data (the most valuable). p99.99 was judged too expensive (dominated by random events outside your control).
3. Tail-latency amplification: when one user request fans out into several backend calls, the user waits for the slowest. The
   fraction of slow user requests exceeds the fraction of slow backend calls, so tail percentiles matter most in services called many times per user request.
4. Never average percentiles. To aggregate across machines or time windows, add the histograms. Efficient approximations: HdrHistogram, t-digest, OpenHistogram, DDSketch; compute over a rolling window (for example the last 10 minutes recomputed each minute).
5. SLO = target (for example median < 200 ms, p99 < 1 s, 99.9% of valid requests succeed). SLA = contract with consequences if an SLO is missed.
6. Be sceptical of famous "100 ms costs X% revenue" numbers: DDIA lists several (Google, Bing, Akamai, Yahoo) and flags them as
   contradictory or confounded. Use "faster is better", not a specific figure, unless you have your own measurement.

## 4. Reliability vocabulary and fault numbers

- Reliable: continues to work correctly even when things go wrong: does what the user expects, tolerates user mistakes, performs well enough under expected load, prevents abuse.
- Fault: a part stops working correctly. Failure: the whole system stops providing the required service. The same event is a
  fault at one level and a failure at another (a disk failure is a fault to a multi-disk system).
- Fault-tolerant is always bounded: "tolerates 2 disks" or "1 of 3 nodes". A single point of failure (SPOF) is a component whose fault escalates to system failure.
- Prefer tolerating faults over preventing them, except where prevention is the only option (a security breach cannot be undone).
- Fault injection / chaos engineering: deliberately trigger faults to keep fault-tolerance machinery exercised; many critical bugs
  come from poor error handling.

Hardware numbers (specific studies, dated; the argument survives even if the figures drift):
- Magnetic disks fail 2-5% per year, so a 10,000-disk cluster sees about one failure a day. SSDs 0.5-1% per year, with uncorrectable errors about once a year per drive.
- About 1 in 1,000 machines has a CPU core that sometimes computes wrong results. Even with ECC RAM, over 1% of machines hit an uncorrectable memory error per year.
- Datacenter loss happens (power, network misconfiguration, fire, flood).
- Faults correlate (rack, data center), so redundancy within one machine or rack is weaker than it looks. Cloud systems prefer software
  fault tolerance across machines and availability zones, which also allows rolling upgrades.

Software faults are correlated across nodes (same software, same bug), which makes them worse than hardware faults. Examples: the leap-second bug
of 30 June 2012, an SSD firmware bug at exactly 32,768 hours, runaway processes exhausting resources, a dependency returning corrupt data,
cascading failures. Mitigations: examine assumptions and interactions, thorough testing, process isolation, let processes crash and restart, avoid feedback loops (retry storms), monitor production.

Humans: in the study DDIA cites, operator configuration changes were the leading cause of outages (hardware only 10-25%).
"Human error" is a symptom of the sociotechnical system. Measures: tests (hand-written and property-based/random-input), fast rollback of
configuration changes, gradual rollouts, clear monitoring and observability, interfaces that make the right thing easy, blameless
postmortems. Go to `arch-production-operations` for rollout and postmortem detail.

## 5. Scalability: load parameters and architectures

"X is scalable" is meaningless on its own. Ask: if load grows in this particular way, what are our options, how do we add resources, and when do we hit the limits of this architecture?

Step 1, name the load parameters: requests/s, GB/day of new data, checkouts/hour, peak concurrent users, read:write ratio, cache hit rate, items per user (followers). Decide whether the average or a few extremes (a celebrity with millions of followers) is the bottleneck.

Step 2, ask the two questions: (1) load up, resources fixed: how does performance change? (2) load up: how much more resource keeps performance within the SLO at minimum cost?

Scalability architectures:

| Architecture | Description | Pros | Cons |
|---|---|---|---|
| Shared-memory (vertical, scale up) | Bigger machine, threads share RAM | Simplest | Cost grows faster than linear; 2x hardware does not give 2x load; cores are no longer getting faster individually |
| Shared-disk | Several machines with own CPU/RAM, shared disk array (NAS/SAN) | Traditional on-premises warehousing | Contention and locking limit scalability |
| Shared-nothing (horizontal, scale out) | Each node has its own CPU, RAM, disk; software coordinates over the network | Can scale linearly, best price/performance, elastic, multi-region fault tolerance | Needs explicit sharding; all distributed-systems complexity |

Cloud-native databases separate a storage service from compute nodes. That resembles shared-disk but avoids its problems because the storage exposes a database-specific API rather than a filesystem or block device.

Principles:
- No generic scaling recipe: 100,000 req/s of 1 kB is a different system from 3 req/min of 2 GB although both are 100 MB/s.
- An architecture built for one load level will not survive 10x; expect to rethink at every order of magnitude, and do not plan more than about one order of magnitude ahead.
- Break the system into smaller independent components (sharding, services, stream processing); the hard part is where to draw boundaries.
- Do not complicate: a single-machine database beats a complicated distributed setup if it suffices; autoscaling is attractive but predictable load makes manual scaling quieter; 5 services are simpler than 50.
- Premature scaling is waste or lock-in. For a new product with few users the goal is simple and flexible.
- Linear scalability (2x resources handles 2x load) is the good case; super-linear cost growth is more likely than sub-linear. For the quantitative scalability model (Amdahl, USL) go to `arch-scalability-analysis`.

## 6. Maintainability

Most software cost is maintenance. Three principles:
1. Operability: easy for the organisation to keep the system running. "Good operations can often work around the limitations of bad software, but good software cannot run reliably with bad operations." Systems help by exposing metrics, not depending on individual machines, having a simple operational model ("if I do X, Y happens"), good defaults, self-healing with manual override, predictable behaviour. Automation cuts both ways: leftover manual cases are the hardest, and failed automation is harder to troubleshoot.
2. Simplicity: complexity raises bug risk and slows everyone. Simplicity is subjective (simple interface vs simple implementation). The essential/accidental complexity split is flagged as flawed because the boundary moves with tooling. The best tool is abstraction.
3. Evolvability: loosely coupled, simple systems are easier to change. The main obstacle is irreversibility (for example a database migration with no way back): minimise irreversible steps and take them carefully.

## 7. Overload, retries and metastable failure

Near overload, queues grow, clients time out and retry, load rises, and the system can stay overloaded even after the original load drops (metastable failure, retry storm). Mitigations (DDIA ch. 2):
- Client side: exponential backoff with randomisation (jitter); circuit breaker or token bucket to stop sending to a failing service.
- Server side: load shedding (reject proactively near overload) and backpressure (tell clients to slow down).
- The queueing and load-balancing algorithm matters.

Make this a requirement line whenever a design includes retries (queues, third-party calls, clients). The rate limiter in `building-blocks.md` and the notification retry rules in `worked-designs.md` are instances. Depth: `arch-production-operations` (managing load).

## 8. Case study: home timelines

Illustrates "choose by load parameters". Assumptions (DDIA ch. 2): 500M posts/day (about 5,800 posts/s average, spikes to 150,000/s); average user follows 200 and has 200 followers; extreme skew (celebrities above 100M followers).

- Approach A, query on read: join posts, follows and users for the viewer, order by time, limit 1000. If 10M users are online polling every 5 s, that is 2M queries/s, each merging about 200 followees, i.e. 400M lookups/s. Worse for users following tens of thousands.
- Approach B, materialise timelines (write-time fan-out): precompute a per-user timeline cache; on each post insert it into every follower's timeline; clients subscribe to pushes. Cost: 5,800 posts/s x 200 followers is about 1.16M timeline writes/s, large but far below 400M lookups/s. The cache is a materialised view: faster reads, more write work, and derived data that must be kept up to date.
- Fan-out = factor by which one request becomes many downstream requests. Spikes: enqueue deliveries; posts appear later but reads stay fast.
- Extremes: a user following very many high-volume accounts can have some timeline writes dropped and be shown a sample (lossy timeline). A celebrity cannot be dropped: store celebrity posts separately and merge them in at read time (hybrid push/pull).
- Lesson: the read-time vs write-time choice depends on the read:write ratio and the skew of the fan-out; hybrid handles the heavy tail. System Design Interview ch. 11 reaches the same hybrid (see `worked-designs.md`).

## 9. Requirement-driven selection cues

| Requirement signal | What it pushes toward |
|---|---|
| Reads far outnumber writes, repeated reads of same data | Cache, read replicas, precomputed views |
| Strict correctness (money, inventory) | Strong consistency, CP behaviour on partition, transactions |
| Always-on writes, tolerable staleness | AP, eventual consistency, conflict resolution |
| Freshness measured in minutes, huge volumes | Streaming or lookup-store designs, not coarse batch (NALSD iteration 2) |
| Hard tail-latency target on fanned-out calls | Percentile targets at p99/p99.9; reduce the number of calls per user request |
| Global users | Multi-data-center, geo routing, regional data placement |
| Legal deletion rights | Data minimisation, deletion path for derived copies |
| Few engineers, few teams | Keep it a monolith or few services; microservices solve a people problem |

## 10. Verification checklist

- Every NFR line has a number, a percentile or window, and a measurement point.
- Latency is measured client side with histograms; no averaged percentiles.
- Worst-case fan-out (celebrity, large group) is identified and has a queue, drop or merge policy.
- SPOFs listed; loss of a node, rack and AZ analysed; rolling upgrade and rollback procedure exists; fault injection planned.
- Retries have backoff with jitter, circuit breakers and load shedding.
- Durability (backups restorable) is covered separately from availability.
- The design does not plan scale more than about one order of magnitude ahead.
