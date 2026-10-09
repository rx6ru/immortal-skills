# Load parameters, response-time distributions and scaling decisions

Source: DDIA 2e ch. 2 (scalability, describing performance, reliability numbers relevant to scale) and SRE Workbook ch. 11 (retry and feedback failures). Items marked (inferred) are labelled so in the notes; (adaptation) is mine. Complements the USL, which gives mean throughput and mean latency only. SLO design itself is in `arch-reliability-slos`.

Contents
1. Describe load before scaling
2. Two scaling questions
3. Performance vocabulary
4. Percentiles: what to report and how to compute
5. Overload behaviour: queueing, retries, metastable failure
6. Tail latency amplification
7. Scale-up versus scale-out
8. Principles for scaling decisions
9. Reliability numbers that affect scale planning
10. Review checklist

## 1. Describe load before scaling

Pick load parameters that match the system: requests per second, GB per day of new data, checkouts per hour, peak concurrent users, read:write ratio, cache hit rate, items per user (followers). Then ask whether the average or a few extremes are the bottleneck. 100,000 requests/s of 1 kB and 3 requests/min of 2 GB are both 100 MB/s and need entirely different designs; there is no generic scaling recipe.

## 2. Two scaling questions

1. Load goes up and resources stay fixed: how does performance change?
2. Load goes up: how many more resources keep performance at target?

The goal is to stay within the SLA at minimum cost. Linear scalability (2x resources handles 2x load at the same performance) is good; sublinear cost from economies of scale occurs sometimes, but super-linear cost is much more likely (for example more data making each write costlier). This is the same question the USL answers quantitatively.

## 3. Performance vocabulary

| Term | Meaning |
|---|---|
| Response time | elapsed time from request to answer as the client sees it, all delays included |
| Service time | time actively processing the request |
| Queueing delay | time waiting for CPU, in network buffers, etc. |
| Latency | catch-all for time the request is latent (not actively processed), e.g. network latency |
| Throughput | requests or bytes per second; has a maximum for given hardware |
| Jitter | variation in network delay |

Sources of random delay: context switch, packet loss and TCP retransmit, GC pause, page fault to disk. Response time is low at low throughput and rises sharply near capacity (the hockey stick). Head-of-line blocking: a few slow requests hold up fast ones behind them, and queueing delay is not in service time, so measure response time on the client side.

Note for USL users: the book's "response time" is a distribution; the USL's R is the mean.

## 4. Percentiles: what to report and how to compute

- Response time is a distribution, not a number. The mean estimates throughput limits but says nothing about how many users saw a delay.
- Report the median (p50) as typical and a tail percentile (p95, p99, p999) for outliers. State the measurement point (client side).
- Choose the tail percentile by fan-out and business value. Amazon's internal targets use p99.9 because the slowest requests come from customers with the most data, who are the most valuable. Optimising p99.99 was judged too expensive: dominated by random events outside your control, with diminishing returns.
- Compute over a rolling window (for example 10 minutes recomputed each minute). Naive: keep all values and sort. Efficient approximations: HdrHistogram, t-digest, OpenHistogram, DDSketch.
- Averaging percentiles is mathematically meaningless. To aggregate across machines or time resolutions, add the histograms.
- SLO: a target (for example median under 200 ms, p99 under 1 s, at least 99.9 percent of valid requests non-error). SLA: a contract with consequences if the SLO is missed.
- Treat quoted effects of latency on revenue with scepticism. The book lists Google 2006 (400 to 900 ms, about 20 percent traffic drop), Google 2009 (400 ms added, 0.6 percent fewer searches), Bing 2009 (2 s slower, 4.3 percent ad revenue drop), Akamai (100 ms, up to 7 percent conversion drop, confounded because the fastest pages are 404s) and Yahoo (20 to 30 percent more clicks on fast results when the gap is at least 1.25 s). The shape "faster is better" holds; specific numbers are unreliable.

## 5. Overload behaviour: queueing, retries, metastable failure

Metastable failure (retry storm): near overload queues grow, clients time out and retry, load rises, and the system stays overloaded even after the original load drops until it is reset. Mitigations:
- client-side exponential backoff with randomisation (jitter)
- circuit breaker or token bucket to stop sending to a failing service
- server-side load shedding (reject proactively near overload) and backpressure (tell clients to slow down)
- choice of queueing and load-balancing algorithm

Pokemon GO (SRE Workbook ch. 11): the client retried once immediately and then used constant backoff, so short error bursts synchronised retries and produced a thundering herd up to 20 times the previous global peak. The fix added jitter and truncated exponential backoff.

Feedback loops between load tools: the Dressy case had load shedding that made rejected requests cheap, a utilisation-aware balancer read the falling CPU per request as efficiency and sent more traffic, so one region ended up with 400 requests/s while the others dropped to 40. The fix was to count each error as more than 100 percent CPU in the balancer. Lesson for scaling reviews: examine how every load tool interacts with the others and monitor the intersection. Operating detail is in `arch-production-operations`.

Set RPC deadlines. Without a deadline, resources are held for in-flight requests up to a huge default, causing latency, memory exhaustion and crashes. Servers end requests that run too long; clients cancel requests that are no longer useful.

## 6. Tail latency amplification

When one user request fans out to several backend calls, even in parallel, it waits for the slowest one. The probability that at least one call is slow grows with the number of calls, so a larger fraction of user requests are slow than the fraction of slow backend calls. High percentiles matter most in services called many times per user request. Implication for capacity: a per-call p99 target is not a per-user-request p99 target; derive the backend percentile from the fan-out (adaptation: for independent calls the chance all n are fast is the per-call fast fraction to the n-th power, so n = 100 calls each at 99 percent fast leaves only about 37 percent of requests entirely fast).

## 7. Scale-up versus scale-out

| Architecture | Description | Pros | Cons |
|---|---|---|---|
| Shared-memory (vertical, scale up) | bigger machine, threads share RAM | simplest | cost grows faster than linear; bottlenecks mean 2x hardware does not give 2x load; cores are no longer getting faster individually |
| Shared-disk | several machines with own CPU/RAM, shared disk array via NAS/SAN | traditional on-prem data warehousing | contention and locking overhead limit scalability |
| Shared-nothing (horizontal, scale out) | each node has its own CPU, RAM, disk; coordination in software over the network | can scale linearly; best price/performance hardware; elastic; multi-region fault tolerance | needs explicit sharding; all distributed-systems complexity |

Modern cloud-native databases separate a storage service from the compute nodes that share it. It resembles shared-disk but avoids its problems because storage exposes a database-specific API rather than a filesystem or block device.

## 8. Principles for scaling decisions

- "X is scalable" is meaningless. Ask what the options are if load grows in this particular way.
- Premature scaling is wasted effort or locks in inflexibility. For a new product with few users aim at simple and flexible; start worrying about scaling techniques once success reveals the bottleneck dimension. "You are not Google or Amazon" depends on the app.
- An architecture for one load level will not survive 10x. Plan about one order of magnitude ahead, not more.
- Break the system into smaller independent components (the idea behind microservices, sharding, stream processing, shared-nothing); the hard part is the boundaries.
- Do not make it more complicated than necessary. A single-machine database beats a distributed setup if it suffices; autoscaling is attractive but predictable load makes manual scaling quieter; 5 services are simpler than 50.

## 9. Reliability numbers that affect scale planning

Dated studies; the argument (rates at scale are not negligible, failures correlate) survives even if the numbers do not.
- Magnetic disks fail 2 to 5 percent per year, so a 10,000-disk cluster sees about one failure a day. SSDs fail 0.5 to 1 percent per year, with uncorrectable errors about once a year per drive.
- About 1 in 1,000 machines has a CPU core that sometimes computes wrong results; even with ECC more than 1 percent of machines hit an uncorrectable memory error per year.
- Software faults are correlated across nodes (same software, same bugs) and cause more failures than hardware; cascading failures spread overload.
- Fault tolerance is bounded to specified numbers and types of faults. Cloud systems prefer software fault tolerance across machines and availability zones, which also allows rolling upgrades.
- A study found operator configuration changes were the leading cause of outages, hardware only 10 to 25 percent.

## 10. Review checklist

- [ ] Load parameters are named and measured, including skew (largest fan-out, largest tenant).
- [ ] Response time is recorded on the client side as histograms; percentiles are never averaged.
- [ ] Targets state the percentile and the measurement point.
- [ ] Fan-out paths: worst-case fan-out known; a queue, drop or backpressure policy exists.
- [ ] Retries use backoff with jitter; circuit breakers and load shedding exist; RPC deadlines set.
- [ ] SPOFs identified; loss of a node, rack or zone is survivable (inferred).
- [ ] The design is not sized more than about 10x beyond current load.
