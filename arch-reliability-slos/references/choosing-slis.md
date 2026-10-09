# Choosing SLIs and turning a specification into a measurement

Contents: 1 SLI form; 2 specification vs implementation; 3 procedure for the first SLIs; 4 SLI menu by service type; 5 choosing a measurement source; 6 worked implementation choices (game example); 7 latency grades; 8 critical user journeys; 9 bucketing; 10 VALET as an alternative taxonomy; 11 checks.

Sources: SRE Workbook ch. 2, ch. 3, ch. 5 (bucketing), app. A; DDIA 2e ch. 2 (percentiles).

## 1. SLI form: good events over valid events

An SLI is a ratio, good events divided by valid (total) events, between 0% and 100%. 0 means nothing works, 100 means nothing is broken. The error budget is 100% minus the SLO. Examples from the notes:

- successful HTTP requests / all HTTP requests
- gRPC calls that completed OK in under 100 ms / all gRPC calls
- search results that used the whole corpus / all results (degraded results count as bad)
- stock-check requests that used stock data fresher than 10 minutes / all stock-check requests
- good user minutes / total user minutes

Why force this shape: one set of alert logic, SLO analysis, budget arithmetic and reports then serves every SLI, and any SLI can be fed to the burn-rate rules in `alerting-on-slos.md`. If an indicator does not fit (a raw CPU number, a queue depth), either turn it into "fraction of time or events within a threshold" or keep it as a debugging metric rather than an SLI.

State four things for every SLI: numerator, denominator (what is valid, and what is excluded), threshold, and where it is measured. Missing any of these makes two people compute different numbers.

## 2. Specification versus implementation

- SLI specification: the outcome users care about, independent of how it is measured. Example: "ratio of home page requests loaded in under 100 ms".
- SLI implementation: the specification plus a measurement method. One specification has several implementations that differ in quality (fidelity to what the user experienced), coverage (share of users and interactions seen) and cost.

Three implementations of the home page latency specification:

| Implementation | Sees | Misses | Cost |
|---|---|---|---|
| Server log latency column | requests that reach the backend | requests that never reach it (DNS, network, load balancer failures) | lowest, usually already there |
| JavaScript-executing probers in VMs | network reachability, rendering path | subsets of real users, real traffic mix | weeks |
| JavaScript instrumentation in the page reporting to telemetry | what real users experienced | needs code in the page and a reliable telemetry pipeline | months |

Rule: start with the cheapest implementation that is not misleading (logs or load-balancer metrics if present), get a feedback loop running, then move the measurement closer to the user when the review in `setting-slos-and-error-budgets.md` shows missed incidents. The first SLI does not need to be right; it needs to exist and be reviewed.

## 3. Procedure for the first SLIs

1. Choose one application (not the whole company).
2. Decide precisely who the users are (end customers, other services, internal analysts).
3. List the common user tasks or critical activities.
4. Draw an architecture sketch: components, request flow, data flow, critical dependencies. Classify each component as request-driven, pipeline or storage.
5. For each class pick SLIs from the menu below that are relevant and easy to measure; refine later.
6. Keep at most about five SLI types, for the most critical functionality. More SLIs dilute attention and multiply alert and policy decisions.
7. Write each as specification plus first implementation; record what the implementation cannot see.

## 4. SLI menu by service type

| Service type | SLI | Definition | Notes |
|---|---|---|---|
| Request-driven | Availability | proportion of requests with a successful response | decide what counts as success per protocol (see section 6) |
| Request-driven | Latency | proportion of requests faster than a threshold | use two thresholds (section 7) |
| Request-driven | Quality | proportion of responses served undegraded | only if graceful degradation exists, for example a generic avatar when the user-data store is down |
| Pipeline | Freshness | proportion of data updated more recently than a threshold | ideally weight by how often users read each item |
| Pipeline | Correctness | proportion of input records that produce correct output | needs known-answer data or an oracle |
| Pipeline | Coverage | batch: proportion of jobs processing above a target amount of data; streaming: proportion of incoming records processed within a window | |
| Storage | Durability | proportion of written records that can be read back | watch the slice: 99.9999% of bytes readable is useless if today's records are the unavailable ones |

Overlap is fine: a request service can have correctness, a pipeline can have availability, durability is a kind of correctness. See `arch-data-pipelines` for deeper pipeline SLO design.

## 5. Choosing a measurement source for a request-driven service

Options, from cheapest to closest to the user:

1. Application server logs or metrics. Easy, but blind to anything upstream of the app (load balancer drops, network).
2. Load balancer metrics. Already present in most stacks and closer to the user than app logs. The game example chose this.
3. Black-box probers. Catch reachability and whole-path failures, but only for the synthetic requests you write.
4. Client-side instrumentation. Closest to experience; costs code and a telemetry pipeline, (adaptation: clients that fail before they can report are invisible to it).

DDIA adds a reason to prefer the client side for latency: queueing delay and head-of-line blocking are not in server-side service time, so response time should be measured as the client sees it (DDIA 2e ch. 2). If you cannot, say in the SLO document that the number is server-side and underestimates.

## 6. Worked implementation choices (mobile game example, Workbook ch. 2 and app. A)

- API availability and latency: measured at the load balancer. HTTP 5XX counts against the SLO, every other status counts as success (so client errors such as 404 do not burn budget). The error classification is a policy decision; write it down.
- Latency, two ways to count slow requests: derive from a latency histogram (flexible, approximate near bucket edges) or keep explicit counters per threshold at the load balancer (for example 100 ms and 500 ms; accurate, but changing a threshold later cannot be applied retroactively).
- Pipeline freshness: the pipeline writes a watermark timestamp. Option 1, a periodic query that counts fresh versus total records, treats every stale record equally. Option 2, chosen: each reader of the league table checks the watermark at read time and increments "data requested" and "fresh enough" counters, so staleness is weighted by what users actually read.
- Pipeline coverage: the pipeline exports "records it should have processed" and "records processed". Blind spot: records it never knew about because of misconfiguration.
- Pipeline correctness: either inject known-input, known-output data and count matches, or sample input and output pairs and check them against an independent (usually costlier) oracle. The example used curated test data in the game-state database on every run, which must be representative of real data. The appendix A version is a correctness prober that injects synthetic records and reads them back.
- Starter queries over a 7-day window in Prometheus notation: availability = rate of non-5xx requests divided by rate of all requests; latency from `histogram_quantile` at 0.9 and 0.99 over the bucket rate. Treat the syntax as illustrative.

## 7. Latency: use grades, not one number

One threshold hides the tail. Use two or more: for example 90% of requests under 100 ms and 99% under 400 ms. If 10% of requests take 10 s, many users are unhappy while a single p90 target is satisfied. The same applies to any parameterised "how unhappy is the user" SLI, such as freshness (appendix A: 90% of reads use data less than 1 minute old, 99% less than 10 minutes old).

Percentile cautions (DDIA 2e ch. 2): never average percentiles across machines or time ranges, because it is mathematically meaningless; add the histograms and compute the percentile from the merged histogram. Mean latency alone cannot say whether 50%, 5% or 1% of requests were slow. A good SLI based on counts of "requests faster than threshold" avoids the percentile-averaging trap entirely, which is another reason to prefer the good-over-valid form.

## 8. Critical user journeys

A critical user journey (CUJ) is a sequence of tasks essential to a user, such as search a product, add to cart, complete purchase. Journeys rarely map onto existing per-request SLIs, because failure and distraction are hard to tell apart in logs. Procedure: define the journey first, then measure it by joining log events, JavaScript probing or client instrumentation. Once measurable it is just another SLI. The notes say journeys improve recall without affecting precision (see `alerting-on-slos.md` for the terms).

## 9. Bucketing by importance

Extra labels on SLIs let different interactions carry different SLOs:

- By tier: premium 99.99% availability, free 99.9%.
- By responsiveness: interactive requests that block page load, 90% complete in 100 ms; a CSV download, 90% start within 5 seconds.
- By request class, to keep alerting parameters uniform across services (Workbook ch. 5): CRITICAL 99.99%; HIGH_FAST 99.9% with 100 ms at p90 and 200 ms at p99; HIGH_SLOW 99.9% with 1,000 ms and 5,000 ms; LOW 99% with no latency target; NO_SLO for invisible traffic such as dark launches and alpha features.

Per-customer SLO tracking is possible but noisy for low-volume customers (100% by luck, or very low from one failure). It is useful in aggregate, as a count of customers within SLO.

## 10. VALET: an alternative taxonomy

The Home Depot standardised on VALET for microservices: Volume (how much load it can handle, tracked as average or peak requests per second, with the SLO set for expected peak), Availability, Latency (percentiles not averages, at least p90, user-facing preferably p95 or p99, white-box supplemented by black-box), Errors (HTTP codes only, 5xx counted for the SLO, 4xx tracked but not counted; for batch, records that failed), Tickets (manual interventions needed). Infrastructure utilisation was deliberately not an SLO, though still monitored for capacity. For batch jobs: Volume = records processed, Availability = share of time the job completed by its deadline, Latency = job runtime, Errors = records failed, Tickets = manual fixes and reprocessing. Use VALET when the need is a small, uniform vocabulary across hundreds of services; use the SLI menu when designing one service in depth. They are compatible. Details in `case-studies.md`.

## 11. Checks before accepting an SLI set

- Each SLI has numerator, denominator, threshold and measurement point written down, and can be computed from metrics that exist today or from a named task to create them.
- No more than about five SLI types for the application; each maps to a user task from step 3.
- Latency has at least two grades; no average-only latency.
- The error classification (for example only 5xx counts) is stated. Misclassification cuts both ways: errors wrongly excluded understate budget use, errors wrongly included burn budget with no user harm (the policy template in `error-budget-policy-template.md` handles both).
- The implementation's blind spots are listed (for example requests that never reach the load balancer).
- Pipelines have a freshness or coverage SLI and a correctness SLI, not availability alone.
- The SLI can be turned into a good/valid counter pair that the alerting rules can consume.
