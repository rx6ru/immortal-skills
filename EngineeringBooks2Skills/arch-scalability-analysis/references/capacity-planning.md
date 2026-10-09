# Capacity planning and forecasting

Source: USL booklet "Capacity Planning with the USL" and conclusions; SRE Workbook ch. 11 (autoscaling constraints, case studies) and ch. 12 (capacity arithmetic only); DDIA 2e ch. 2 (load parameters, timeline fan-out numbers, "do not plan too far ahead"). Items marked (adaptation) are mine. Full design-from-requirements method belongs to `arch-system-design` (nalsd-method.md); operating load balancers, shedding and autoscalers belongs to `arch-production-operations` (managing-load.md).

Contents
1. Questions this answers
2. Why the USL and not the alternatives
3. Forecast rules
4. Maximum versus usable capacity: the procedure
5. Worked headroom example
6. Back-of-envelope capacity arithmetic
7. Fan-out and load parameters
8. Constraints to put around an autoscaler
9. When estimates are badly wrong: Pokemon GO
10. Checklist for a capacity statement

## 1. Questions this answers

How soon will the system perform badly as load grows? How many servers do we need for the expected peak? Is it near a failure point? Are we overprovisioned, and by how much? What can one more node or thread buy?

## 2. Why the USL and not the alternatives

| Approach | Problem (per the source) |
|---|---|
| Load tests | costly, slow, workload always artificial |
| Benchmarks | artificial, push to maximum throughput and beyond, where latency percentiles are almost always awful, so max throughput is not usable capacity |
| Queueing theory (Erlang C) | needs service times (observed response time includes queue wait, so hard to get) and true utilisation (hard to measure) |
| USL | black box, data is easy to get (throughput plus load or size), regression is easy, model is simple |

The USL can be combined with queueing tools such as the Square Root Staffing Rule to estimate capacity and quality of service.

## 3. Forecast rules

1. Predicted maximum is `X(Nmax)` with `Nmax = sqrt((1 - sigma)/kappa)`; it exists only when kappa > 0. With kappa = 0 the cap is the asymptote lambda/sigma.
2. Do not trust anything beyond twice the measured throughput or twice the measured size, whichever comes first. Trust less if the data shows levelling off or retrograde signs. Bring in other signals such as CPU utilisation. Systems that fit the USL cleanly often hit rough waters later.
3. Treat USL forecasts as optimistic, best case. Many real systems degrade worse than predicted at larger size.
4. Prefer the maximum throughput within the SLO over the absolute maximum.
5. Validate the forecast horizon with a hold-out fit (measuring-and-fitting.md section 6).
6. Report a range, not a point: fit with both methods, with and without the last few points, and give the spread (adaptation).

DDIA 2e adds: an architecture designed for one load level will not survive 10x; do not plan more than about one order of magnitude ahead, and expect to rethink at each order of magnitude. Scaling investment made before the bottleneck dimension is known is wasted or locks in inflexibility; a new product should be simple and flexible first.

## 4. Maximum versus usable capacity: the procedure

1. Fit the USL to throughput against concurrency (or size).
2. Take the latency requirement as a mean response time target R (an SLO on percentiles needs more than the mean, see percentiles-and-load.md; the USL gives means only, and quantiles would need queueing theory).
3. Predict mean response at candidate loads with `R(N) = (1 + sigma*(N-1) + kappa*N*(N-1))/lambda`.
4. Solve for the largest N meeting the target (eq. 10 in usl-model.md; `--latency-target` in the script).
5. Usable throughput is X at that N. Compare with current throughput to get headroom, and with X(Nmax) to see how much of the peak you can actually use.
6. State the confidence: how far beyond the measured range the answer sits.

Warning from the source: "CPU is only 10 percent and the chart looks linear" is not evidence of headroom, because throughput and latency degrade nonlinearly. You usually have less headroom than you think.

## 5. Worked headroom example

Source scenario: pretend only N = 1 to 10 of the Cisco data is measured in production; observed throughput at N = 10 is 7,867 req/s.

- Fit predicts a maximum of 16,049 req/s at 46 threads (the full data later gave 12,341 at 35, so the small-sample forecast was optimistic). Current load is about half the predicted maximum.
- Forecast at N = 20 is 12,572 req/s, under twice the observed 7,867 (15,734), so acceptable by the 2x rule. The author's judgement: no more than about 12,500. The real maximum was 12,211.
- Predicted mean response at 20 threads is 0.00159 s. Requirement: mean at most 1.5 ms. Solving eq. 10 with R = 0.0015 gives N = 17, about 11,450 req/s.
- Current 7,867 is about two thirds of that usable capacity; usable throughput is about 1.46 times current (the notes' "grow about 145 percent" is read as the ceiling being 145 percent of current; clarification marked inferred in the notes).

Running `scripts/usl_fit.py` on those ten points reproduces these numbers (peak 16,052 at N = 46.9, 12,573 at N = 20, N = 17.4 and about 11,450 at N = 17 for R = 1.5 ms). See worked-example.md.

## 6. Back-of-envelope capacity arithmetic

When there is no system to measure yet, the SRE Workbook's non-abstract design method turns a requirement into resources with explicit units. Only the arithmetic habits are summarised here; the iterative design method is in `arch-system-design`.

Habits:
- Write units and use scientific notation to avoid unit errors; round up.
- State the assumed standard machine (the book's example: 16 cores, 64 GB RAM, 1 Gbps network; a 4 TB HDD gives about 200 IOPS). These are the book's illustrative assumptions, not facts about your hardware.
- Compute per-resource: storage per day, IOPS, network, RAM. Compare each to one machine; every check that fails forces a scaling move (shard, replicate, batch versus stream).
- Convert requirements to SLOs first (for example 99.9 percent of dashboard queries under 1 s; data under 5 minutes old) so each design can be checked against them.

Numbers from the AdWords click-through-rate example (illustrative):

| Step | Arithmetic | Result |
|---|---|---|
| Query log volume | 5x10^5 queries/s * 8.64x10^4 s/day * 2x10^3 B | 86.4 TB/day, rounded up to about 100 TB/day with indexes |
| Disks for one write per entry | 5x10^5 / 200 IOPS | 2,500 disks (hundreds even if batched 10:1) |
| RAM-only | 100 TB / 64 GB | 1,563 machines |
| Join traffic into LogJoiner | 10^4 clicks/s * 2 KB | 20 MB/s = 160 Mbps |
| Consensus op rate | 25 ms per op (assumed, DCs a few hundred km apart) | 40 sequential ops/s per process |
| Tasks needed | (2x10^4 clicks/s + 10^6 queries/s) / 40 | about 25,500 tasks (replication doubled the load) |
| Memory per task | 4x10^12 B / 25,500 | about 157 MB |
| Machines per DC | about 4 TB RAM / 64 GB | 64 machines |

The reasoning and assumptions matter more than the final numbers. Imperfect but reasonable assumptions are fine; value comes from combining many rough results and from noticing the step at which a design stops being feasible.

## 7. Fan-out and load parameters

Choose load parameters for the system in front of you: requests per second, GB of new data per day, checkouts per hour, peak concurrent users, read:write ratio, cache hit rate, items per user. Ask whether the average or a few extremes are the bottleneck.

Fan-out is the factor by which one request becomes many downstream requests. DDIA's home-timeline example:

| Approach | Load | Note |
|---|---|---|
| Query on read: join posts, follows, users per refresh | 10M online users polling every 5 s is 2M queries/s; with about 200 followees each, 400M lookups/s | cost scales with reads |
| Materialise timelines (write-time fan-out) | 5,800 posts/s * about 200 followers is about 1.16M timeline writes/s | far lower, but timelines become derived data that must be updated |

Skew breaks the average: a celebrity with millions of followers cannot be handled by dropping writes, so keep celebrity posts separate and merge at read time (hybrid), while a user following many high-volume accounts can be given a sampled timeline. The lesson for capacity work: the choice between read-time compute and write-time precompute depends on the read:write ratio and the skew of fan-out; compute both loads before choosing. Derived-data maintenance is covered in `arch-data-pipelines`.

## 8. Constraints to put around an autoscaler

From SRE Workbook ch. 11 (operating details in `arch-production-operations`; here only what affects capacity numbers):

- Set minimum and maximum bounds and enough quota to reach the maximum.
- Be more sensitive to rises than drops: add quickly, remove slowly. Failing to scale up means overload.
- Keep the service far from its key bottleneck, and leave reaction time because creating instances is never instant. User-facing services reserve spare capacity for both overload protection and redundancy.
- Scale on a capacity metric seen by the load balancer or a healthy-only metric; averages over all instances count non-serving instances and may never trigger.
- Do a dependency analysis first: some services scale less than linearly, and a scaled-up service can overload a backend or starve others sharing quota.
- Autoscale before load shedding starts, otherwise you shed traffic you could have served.
- Keep a minimum per location so failover has spare capacity.
- Have a kill switch and a manual override.
- Predictable load may be better served by manual scaling (DDIA: fewer operational surprises).

## 9. When estimates are badly wrong: Pokemon GO

Niantic load-tested to 5 times its most optimistic estimate; real launch traffic was about 50 times the estimate. True client demand was 200 percent higher than previously observed once the frontend was moved. Refused connections did not appear in inbound-request monitoring. Lessons relevant to capacity work: measure load as close to the client as possible (otherwise you under-provision); count refused or shed requests in demand; expect retries to multiply load, so use jittered, capped, truncated exponential backoff; have an administrative way to limit traffic while the backend recovers. The retry-storm mechanism is described in percentiles-and-load.md section 5.

## 10. Checklist for a capacity statement

- [ ] N, throughput unit and what is held constant are defined.
- [ ] Data points: how many, over what range, steady-state means.
- [ ] Coefficients with fit quality and a hold-out score.
- [ ] Peak (or asymptote) AND usable capacity at the stated latency target.
- [ ] Current operating point as a fraction of usable capacity.
- [ ] Forecast horizon within 2x of measured; if not, labelled as low confidence.
- [ ] Signals the model cannot see (core count, bandwidth, queue caps) checked separately.
- [ ] A re-measurement trigger (after a release, at 1.5x the traffic, etc.) (adaptation).
