# Limits of the model and honesty checks for scaling claims

Source: USL booklet, "Linear scalability and how to spot bogus claims", "Probing the USL's Limits", "Superlinear Scaling", "Other Scalability Models", conclusions. Items marked (adaptation) are mine.

Contents
1. What the USL cannot see
2. Forecast stance versus diagnosis stance
3. Superlinear results
4. Models and charts to reject
5. Auditing a scaling claim (arithmetic)
6. Auditing a scaling chart
7. Claim-by-claim table of bogus statements
8. Reporting scaling results honestly
9. Pitfall list for the analyst

## 1. What the USL cannot see

- It has no parameter for the number of servers or capped resources, which matter greatly in queueing theory. It cannot foresee regime shifts: threads exceeding physical cores (a fit that is good until one thread per core, then an abrupt change), a network bandwidth ceiling, queue or resource saturation.
- Example: throughput against connections to about 200 flatlines abruptly; a USL fitted to the first dozen points projected about 150,000 against a real plateau near 80,000.
- It is a macro model of the system as a whole, like the ideal gas law: breaks at the extremes, far more usable than a bottom-up micro model of instructions and caches.
- It usually models extremely well up to the point of inflection. Analyse only up to the knee or peak. After retrograde scaling begins the system's factors have changed, so one model cannot explain it, and you should not be pushing further anyway.
- Noisy real data may not look like the USL at all; regression can return unphysical values or fail to converge. Clean-room data can still misfit.
- Use extra data for the limits the model cannot see: CPU utilisation, core counts, bandwidth, queue depths.
- "Any model is better than none": it gives a frame of reference (the system should scale better than it does; these measurements look wrong). Never trust an arbitrary curve through a scatterplot unless you know why it is the right curve.

## 2. Forecast stance versus diagnosis stance

Two rules in the source look contradictory; they answer different questions.

| Question | Stance | Reason |
|---|---|---|
| How much can I count on at larger scale? | Treat the USL forecast as optimistic, best case; do not go beyond 2x the measured range | many systems degrade worse than predicted at larger size; model blind to caps |
| Is this system scaling worse than it should? | Treat the USL as a pessimistic baseline the system ought to beat | the underlying repairman model is the worst case for queueing delay |

Decide which question you are answering and say so in the write-up.

## 3. Superlinear results

Repeated observation: negative sigma, a curve rising above the linear line and then bending back. Gunther reproduced and explained it on a large Hadoop TeraSort benchmark. Real mechanisms exist: a resource scales disproportionately with load, for example adding nodes adds memory, so more of an unscaled dataset fits in RAM per node; any resource more efficient shared than used alone. The boost may be repaid later by a drop back below linear. Some clusters behave differently at size 1 (no crosstalk, not distributed) and 2 (special-cased) than at 3 or more (generic algorithms): measure at larger sizes.

Check these before believing it:
1. Dataset held fixed while nodes grow (dimensions varied against each other).
2. Concurrency inflated by idle threads, shifting all points to the right.
3. Warm-up or cache state differing between runs.
4. Too few points at small N, with special-cased sizes 1 and 2 dominating.

In most cases sigma should be positive.

## 4. Models and charts to reject

- "Quadratic scalability" (downward parabola through rise-level-decline data): may fit but predicts negative throughput at some size.
- Vendor charts that plot latency against throughput with a smoothed or parabolic line (New Relic scalability chart, AppDynamics parabola, Cockcroft headroom plots): they assume throughput is a free parameter that determines latency. With kappa nonzero latency is two-valued in throughput and not quadratic in it. A rational fit of eq. 7 to the Isilon data (below) badly underestimated the latency at the last point.
- Fitting a curve you chose because it looks right, without a mechanism.

## 5. Auditing a scaling claim (arithmetic)

1. Per-node throughput: divide throughput by N. Linear means it stays constant.
   - Source example: 182k TPS at 3 nodes is about 60,700 per node; 449k TPS at 12 nodes is about 37,400 per node, a 39 percent drop. Linear would have given 728k at 12 nodes.
2. Efficiency: `X(N) / (N * X(1))`.
   - Source example: 1 node at 1,800 TPS, 4 nodes ideal 7,200, measured 5,180: 72 percent.
3. Draw the ideal line on every chart. Without it the eye sees the curve as more linear than it is. People are usually surprised by the size of the loss when they do the arithmetic.
4. Compounding: small sublinear effects compound nonlinearly at larger scale.
5. Convert any "scaling factor per node" to a curve: "each node adds 97 percent of the previous node's increment" is geometric, implies a ceiling, and is not linear (a 3 percent loss in the Amdahl sense gives a maximum speedup near 33).
6. Ask whether the claim defines N, what was held constant, how many data points exist and whether the claim covers latency.

## 6. Auditing a scaling chart

| Check | Trick to catch |
|---|---|
| Numbers on both axes | graphs without numbers |
| Linear scales | nonlinear axes |
| Axes start at zero, especially Y | real example: x axis started near 1.45 and y near 100,000, so a curve looked linear |
| Ideal line drawn | curve looks straighter than it is |
| Throughput per node or efficiency shown | hides the loss |
| Points, not just a smooth line | smoothing hides noise and sparse data |
| Latency percentiles at each load | peak throughput quoted with awful latency |
| N defined; data, drivers and servers varied consistently | spurious linear or superlinear shapes |
| Whether the last point is the whole story | the Isilon last row (5.7 ms at 253k ops/s against 2.0 ms at 231k) holds the information about the approach to saturation |

## 7. Claim-by-claim table of bogus statements

| Statement | Why it fails |
|---|---|
| "Shared-nothing, so linearly scalable" | means only that there is no single hard cap, not that it scales linearly |
| "Adding a node adds a predictable amount of capacity" | predictable is not linear |
| "Linearity factor of 97 percent" | a curve, not a line; implies a ceiling |
| "Scales to a million TPS" | throughput without latency, N, or per-node efficiency |
| "CPU at 10 percent, so lots of headroom" | latency and throughput degrade nonlinearly; CPU is one of several limits |
| "It scales linearly" with no numbers behind it | the word is claimed constantly and delivered rarely; people who know scalability rarely use it |

## 8. Reporting scaling results honestly

"Benchmarking is good, publishing results is better, explaining results is best." A good write-up contains:
- definition of N, throughput, per-unit constants, hardware, software versions, run duration
- the data table (or a link) and the chart with the ideal line, numbered axes starting at zero
- coefficients with fit quality and a hold-out error, and which method was used
- the diagnosis: which of contention or crosstalk dominates and the suspected cause
- the forecast horizon and its confidence, and signals the model cannot see
- what was not tested

The same method applies to threads against cores, connection-pool sizing, database workers, cluster nodes, parallel-query degree, and even team size.

## 9. Pitfall list for the analyst

- Fitting after the knee (regime changed).
- Fitting too few points, or points clustered at low N.
- Treating max throughput as capacity.
- Extrapolating past 2x the measured range.
- Averaging percentiles when combining latency data (percentiles-and-load.md).
- Regressing latency against throughput.
- Using a negative-sigma fit for a planning decision.
- Reporting one set of coefficients without saying how they were obtained.
- Changing several dimensions (drivers, nodes, data) at once.
- Declaring victory after a change without refitting.
