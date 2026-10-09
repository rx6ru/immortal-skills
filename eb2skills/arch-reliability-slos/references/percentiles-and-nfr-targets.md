# Writing nonfunctional requirements with numbers: response time, reliability terms, scalability questions

Sources: DDIA 2e ch. 2 (all sections), SRE Workbook ch. 2 (SLO definition).
Deeper scalability modelling is in `arch-scalability-analysis`; designing a whole system from requirements is `arch-system-design`.

Use when turning "fast", "reliable", "scalable" into measurable targets, describing latency in a requirements document, or reviewing a design for fault tolerance and overload behaviour.

## 1. Response time is a distribution

- Response time: elapsed time from request to answer as the client sees it, with all delays. Service time: time actively processing. Queueing delay: waiting (for CPU, in network buffers). Latency: catchall for time the request is latent (not being processed), for example network latency. Jitter: variation in network delay. Throughput: requests or bytes per second; there is a maximum for given hardware.
- Response time stays low at low throughput and rises sharply near capacity (hockey stick).
- Random delay sources: context switch, packet loss and retransmit, GC pause, page fault, even rack vibration.
- Head-of-line blocking: a few slow requests hold up fast ones behind them. Queueing delay is not in service time, so measure response time on the client side.
- Mean is useful for estimating throughput limits and poor for "typical" experience. Report the median (p50) and tail percentiles (p95, p99, p999). High percentiles are tail latencies.
- Choose the tail percentile by fan-out and business value. Amazon sets internal targets at p99.9 because the slowest requests come from customers with the most data. Optimising p99.99 was judged too expensive.
- Tail latency amplification: with a fan-out of many backend calls the request waits for the slowest, so a higher fraction of user requests is slow than the fraction of slow backend calls. High percentiles matter most for services called many times per user request.
- Computing percentiles: rolling window (for example 10 minutes) recomputed each minute; approximations such as HdrHistogram, t-digest, OpenHistogram, DDSketch. Never average percentiles; add histograms.
- User-impact statistics for latency are contradictory and confounded (examples given range from 0.6% fewer searches for 400 ms added to a 7% conversion drop for 100 ms, the latter confounded by fast pages being error pages). Treat as "faster is better" and be sceptical of specific numbers; do not cite them as justification in a requirements document without a source.

## 2. SLO and SLA wording

An SLO is a target such as median under 200 ms, p99 under 1 s, at least 99.9% of valid requests non-error. An SLA is a contract with consequences when missed (for example a refund). Defining good availability metrics is not trivial, which is the point of `choosing-slis.md`. Write requirements in the SLO form: a ratio, a threshold, a window and a measurement point.

## 3. Overload and metastable failure

Near overload, queues grow, clients time out and retry, load rises, and the system can stay overloaded even after the original load drops, until reset. Mitigations: client-side exponential backoff with randomisation (jitter); a circuit breaker or token bucket to stop sending to a failing service; server-side load shedding (reject proactively near overload) and backpressure (tell clients to slow down); attention to the queueing and load balancing algorithm. Load-test by raising throughput until the response-time knee and set capacity alerts below it (this last is marked inferred in the notes).

## 4. Reliability vocabulary

- Reliable means continuing to work correctly even when things go wrong: does what the user expects, tolerates user mistakes and unexpected usage, performs well enough under expected load, prevents abuse.
- Fault: one part stops working correctly. Failure: the system as a whole stops providing the required service (the SLO is missed). The same event is a fault at one level and a failure at another.
- Fault tolerant: keeps service despite certain faults, always bounded to specified numbers and types (two disks, one of three nodes). Single point of failure: a component whose fault escalates to system failure.
- Fault injection and chaos engineering: deliberately trigger faults to keep the machinery exercised; many critical bugs are poor error handling. Prefer tolerating faults to preventing them, except where prevention is the only option (a security breach cannot be undone).
- Hardware numbers (specific, dated studies): magnetic disks fail 2% to 5% a year, so a 10,000-disk cluster has about one failure a day; SSDs 0.5% to 1% a year; about 1 in 1,000 machines has a CPU core that sometimes computes wrong; even with ECC more than 1% of machines hit an uncorrectable memory error a year. At scale faults are normal operation.
- Redundancy works best when faults are independent but they correlate (rack, datacentre). Prefer software-level fault tolerance across machines and availability zones, which also enables rolling upgrades with no downtime.
- Software faults are highly correlated across nodes and cause more failures than hardware: leap-second hang, firmware bug failing at exactly 32,768 hours, runaway processes, a dependency returning corrupt data, cascading failures. Bugs lie dormant until an assumption about the environment stops being true. Mitigate by examining assumptions, thorough testing, process isolation, letting processes crash and restart, avoiding feedback loops such as retry storms, and monitoring.
- Humans: operator configuration changes were the leading cause of outages in one study, hardware only 10% to 25%. "Human error" is a symptom of the sociotechnical system. Measures: thorough tests including property and random-input testing, fast rollback of configuration changes, gradual rollouts, clear monitoring, interfaces that encourage the right thing. Hold blameless postmortems; be suspicious of simplistic answers like "Bob should have been careful" or "rewrite it in another language".
- Permanent data loss or corruption is categorically worse than an outage of minutes; keep a data-loss plan (restorable backups) distinct from the availability plan.

## 5. Scalability questions to put in requirements

"X is scalable" is meaningless on its own. Ask: if load grows in this particular way, what are the options? How do we add resources? When do we hit the current architecture's limits?

- Pick load parameters: requests per second, new data per day, checkouts per hour, peak concurrent users, read to write ratio, cache hit rate, items per user (followers). Ask whether average or a few extremes are the bottleneck.
- Two questions: with load up and resources fixed, how does performance change? With load up, how much more resource keeps performance? Goal: stay within SLO at minimum cost.
- Linear scalability: twice the resources handle twice the load at the same performance. Super-linear cost is much more likely than sub-linear.
- Do not plan more than about one order of magnitude ahead; an architecture for one load will not survive 10x. Premature scaling investment is wasted or locks in an inflexible design.
- Keep it simple: a single-machine database beats a complicated distributed one if it suffices; for predictable load manual scaling gives fewer operational surprises than autoscaling.

Architectures: shared-memory (vertical): simplest but cost grows faster than linear. Shared-disk: contention and locking limit scaling. Shared-nothing (horizontal): can scale linearly, elastic, multi-region fault tolerance, but needs explicit sharding and all distributed-systems complexity.

Fan-out example (timelines): 5,800 posts per second times 200 followers is about 1.16 million timeline writes a second at write-time fan-out, versus 400 million lookups a second when computing on read; hybrid for celebrities. Marks the principle that the choice depends on read to write ratio and skew.

## 6. Maintainability as a requirement

Operability (easy for the organisation to keep the system running; good operations can work around limits of bad software but not the reverse), simplicity (manage complexity with abstraction), evolvability (loose coupling; minimise irreversibility). Write them as checks: metrics exposed, no dependence on individual machines, documented operational model, safe defaults, rollback paths.

## 7. Requirements checklist

- Nonfunctional requirements have numbers: p50 and tail targets with percentile and measurement point, availability percentage with window, data-loss tolerance, maximum load.
- Latency recorded client-side with histograms.
- For each fan-out path, worst-case fan-out is stated with a queue, drop or backpressure policy.
- Single points of failure listed; loss of a node, rack or zone survives; rolling upgrade and rollback tested; fault injection planned.
- Retries use backoff and jitter, with circuit breakers and load shedding available.
- Backups are restorable and tested, separately from availability.
- Scale planning stops at about 10x.
