# Canarying and rollouts

Sources: SRE Workbook ch. 16 (Canarying Releases), ch. 8 (on-call: rollback and mitigation), App. C; Mastering API Architecture ch. 5 (Deploying and Releasing APIs). Tool names (Argo Rollouts, LaunchDarkly, App Engine, Spinnaker) are 2018-2022 examples; the logic carries to Flagger, Kubernetes weighted routing, service-mesh splits, cell or region rollouts and flag platforms.

## Contents

1. Vocabulary
2. Release engineering principles
3. Deployment versus release
4. Separating things that change at different rates
5. Why canary, and what it needs
6. Error-budget arithmetic for a canary
7. Choosing population and duration
8. Choosing and evaluating metrics
9. Shared infrastructure, non-interactive systems, monitoring data
10. Strategies compared
11. API lifecycle and change type
12. Feature flags: rules
13. Metric-driven promotion (Argo-style) and a canary spec to fill in
14. Rollout signals and application-level gotchas
15. Rollback and mitigation speed
16. Opinionated platforms
17. Verification checklist

## 1. Vocabulary

- Release engineering: everything that takes code from the repository to running in production.
- Canarying: a partial, time-limited deployment of a change plus an evaluation that decides whether to proceed. The slice that gets the change is the canary; everything else is the control. The canary is usually much smaller than the control. It is A/B testing applied to a change (ch. 16).
- A canary process proves its value when it flags bad candidates with high confidence and passes good ones without false positives.

## 2. Release engineering principles (ch. 16)

Reproducible builds (same inputs, same artifact weeks apart); automated builds; automated tests; automated deployments done by computers; small self-contained deployments. Why: less toil, review and version control apply because the automation is code, fewer mistakes, and a pipeline you can monitor. Questions the pipeline should answer: how long a release takes to reach production, how often releases succeed (no severe defects or SLO violations), what could catch defects earlier, which steps can be parallelised. More frequent releases mean fewer changes per artifact, which makes rollback cheaper and bug fixes faster.

Target: ship as fast as possible while meeting reliability goals; 100% reliability is never the right target. Use SLOs and error budgets to measure release impact rather than arguing against change.

## 3. Deployment versus release (API Architecture ch. 5)

- Deployment: new code runs in production but real interactions do not exercise it yet. Release: the feature is switched on for users in a controlled way, with business impact.
- If the two cannot be separated, releases must be choreographed across teams, causing downtime and pressure. Warning sign: a legacy system where upgrading UI and server together means downtime and slow rollback.
- Start by separating deploy from release for existing software: feature flags for monoliths with no routing layer, traffic management (gateway or mesh) for APIs. Check first: is it possible in the live systems, how tightly are consumer and producer coupled, and can the pipeline enforce compatibility checks.

## 4. Separating things that change at different rates (ch. 16)

Binary or code; environment (JVM, kernel, OS); libraries; service config and flags; feature or experiment config; user config. If there is one way to deploy, none of them can change independently. A feature-flag or experiment framework decouples feature launch from binary release: turn features on one at a time, and disable a misbehaving one until the next build. Apply the idea to every change type, not only software.

Why it matters: most incidents are triggered by binary or configuration pushes (App. C: 37% binary push, 31% configuration push, so 68%; see `outage-statistics.md`). Safeguards belong on the change path.

## 5. Why canary, and what it needs

Tests and load tests are artificial and test environments differ from production, so some defects reach production. A release that goes everywhere at once sends the defect everywhere. A canary exposes a slice of real traffic first and gains confidence as exposure grows.

Requirements:
1. A way to deploy to a subset of the population, with the share of load on the canary proportional to its population share.
2. An evaluation process that judges good or bad.
3. That evaluation wired into the release process (automatic pause or rollback, or a page to a human).

Without a canary and without rollback, you must find and patch the defect during the outage, which prolongs user impact. With a canary, split traffic between labelled versions (traffic splitting, load-balancer backend weights, proxy config, even round-robin DNS) and compare per-version metrics. The service-wide aggregate barely shows the bug because the canary is small, so service-wide dashboards are the wrong place to look.

## 6. Error-budget arithmetic for a canary

Book example: the candidate fails 20% of requests. Global deploy exposes 20% failure. A 5% canary population gives 20% x 5% = 1% overall error rate. Budget impact is proportional to exposed traffic. Detection plus rollback takes about the same time either way, so the canary buys the same information at a fraction of the cost.

Model assumptions the authors state: uniform load; the whole remaining error budget beyond organic unavailability may be spent on canaries (count only release-induced unavailability); worst case is a 100% failure rate in the exposed slice; availability may dip below the SLO during a canary. The model does not cover incidents such as data leaks. Use the simplest model that meets the need; over-modelling leads to endless tuning.

The authors add a footnote: if the canary is small enough that its fraction equals (actual availability minus the SLO), you can canary continuously with confidence.

Inferred budget check (not in the book): exposure x failure fraction x time to rollback should be a small fraction of the period budget. With a 99.9% SLO over 30 days the budget is 43.2 minutes. A 5% canary failing 20% for 30 minutes costs about 1% x 30 = 0.3 minutes; the same defect exposed globally for 30 minutes costs about 20% x 30 = 6 minutes.

## 7. Choosing population and duration

- Duration must fit release cadence. Daily releases cannot have week-long canaries if only one canary runs at a time; weekly releases allow long canaries; around 20 releases a day demand very short ones.
- Run one canary at a time. Overlapping canaries contaminate each other's signal.
- The four dimensions pull against each other:

| Dimension | Consideration |
|---|---|
| Size and duration | Large and long enough to be representative. A handful of queries is no signal for a diverse query mix. A higher processing rate shortens the time needed to rule out random artifacts. |
| Traffic volume | Enough that the system has a chance to react negatively. More homogeneous requests need less volume. |
| Time of day | Contention, DB write conflicts and locking only show under heavy load; an off-peak canary can miss them. |
| Metrics | Simple ones (query success) evaluate quickly; others (queue depth) need more time or population. |

- Calibrate from history: once you have past canary metrics, pick parameters from typical failure rates, not hypothetical worst cases.
- Gradual (multi-stage) canary: stage 1 is small and uses only the clearest indicators (crashes, request failures). Later stages are larger and can add imperfect-but-valuable metrics as sample size grows.

## 8. Choosing and evaluating metrics

- One metric is not enough: ten times the latency or ten times the memory is also a failure.
- Metrics must indicate problems. Start from the SLIs; good SLIs attribute strongly to service health. Define "acceptable" per metric: too strict gives false positives, too loose lets bad canaries through, and the definition must be revisited as the service evolves.
- Stack-rank candidates by how well they indicate user-perceivable problems and use the top few, perhaps no more than a dozen. Unmaintained metrics erode trust in the release process.
- Frontend example: HTTP return codes and latency are best. CPU usage is noisy (more CPU does not necessarily hurt users), and noisy canaries get disabled or ignored, which defeats them.
- 4xx caveat: a 404 spike may be bad shared URLs (user behaviour) or the server wrongly dropping a resource. Exclude 4xx from the canary verdict and cover specific URLs with black-box probes. (API Architecture ch. 5 adds a context point: a run of 403s may be an attacker probing, and many 401s from a partner may mean a stolen token. That is a security signal, not a canary verdict.)
- Representative and attributable: the metric change must come from the canaried change, not from outliers in a big fleet (oversubscribed machines, different kernels, congested network segments). Counter with a larger canary and by checking metric variance. Isolate metrics: system-wide CPU is poor (other processes), CPU time serving requests is better, CPU time per request while scheduled is better still. A saturated neighbour is a monitoring problem, not a canary failure. A metric that can swing wildly with no service impact is a bad canary metric.
- Avoid before/after comparison. It replaces the old system fully and compares over time; time is the largest source of metric change (a Monday release compares a business day with a weekend). It can detect faster, but recovery time is similar and more users suffer. If unavoidable, compare the same time of week and distrust small deltas.

## 9. Shared infrastructure, non-interactive systems, monitoring data

- Canary and control usually share backends, frontends, networks and data stores. Request 1 handled by the canary can change the content of request 2 that lands on the control. So a "stop and investigate" verdict does not prove the canary is at fault, and a bad canary can damage the control so both move together. Use absolute measures (the SLOs) next to A/B deltas.
- Non-interactive systems: the canary must last at least one work-unit processing time (rendering and video encoding can be long). Make sure the workers handling one work unit across stages all come from the same pool (canary or control). Metrics: end-to-end time per work unit plus application-specific output quality. See `arch-data-pipelines`.
- Monitoring must break metrics down by canary versus control; whole-service monitoring would show only the 1% in the example, indistinguishable from background noise.
- The metric window must not exceed the canary duration. An errors-per-hour metric used to judge a 30-minute canary inherits errors from before the canary began and produces a false "bad" verdict.

## 10. Strategies compared

| Strategy | What it does | Use when | Cost or limit |
|---|---|---|---|
| Canary | Route a small share (say 1%) to the new version, watch technical signals and business KPIs, shift progressively | Loosely coupled minor or patch change; good monitoring; want to cap blast radius; want business-KPI validation | Needs good monitoring to detect fast. Only one extra instance, cheaper than blue-green. Plain Kubernetes splits only by pod ratio (1% means 99 plus 1 pods), so use gateway or mesh weights |
| Traffic mirroring (dark launch) | Duplicate live requests to the new version, discard its responses, evaluate out of band | Validate a refactor's correctness, latency or CPU with no user impact | Shows operational behaviour, not business impact. Inferred caution: mirrored writes and side effects duplicate, so mirror idempotent or read traffic, or stub downstream. Book also warns stateful systems (shared cache inflates hit rate) |
| Blue-green | Two full environments; verify green, flip the router; blue stays as rollback | Consumer and producer coupled and released together; simple persistent services | Double resources; rollback needs care with data and schema changes. It is effectively a before/after canary unless you split traffic gradually between blue and green, in which case green=control, blue=canary |
| Feature flags | Code ships off; a flag in an external store selects the branch per user or globally | Existing monolith with no routing layer; migrating users in batches | Flag service is a cross-cutting single point of failure; see section 12 |
| A/B or multivariate | Same split mechanism, say 50/50, compare user metrics | Comparing two designs | Needs enough traffic and a metric that reflects the question |
| Artificial load | Synthetic traffic against the candidate | Useful supplement | Good code coverage, poor state coverage; hard for mutable systems (caches, cookies, affinity); misses organic traffic shifts; dangerous for billing paths (real charges), so risky paths go untested |
| Traffic teeing | Copy live traffic, discard responses, optionally diff | Representative checks | Harder than a canary; unsafe for stateful systems |
| Parallel versions plus lifecycle | Live and deprecated majors side by side | Breaking (major) API change | Not a rollout technique; consumers choose when to upgrade |

Decision aid (ch. 16, adapted): continuous releases get a short, small canary with an automatic verdict; a flaky metric goes into a later stage, not stage 1; a stateful or billing path gets a real-traffic canary with a small population, not artificial load or teeing; shared infrastructure adds absolute SLO checks.

## 11. API lifecycle and change type (API Architecture ch. 5)

Lifecycle: Planned (advertise, gather early feedback); Beta (consumers integrate; producer may break compatibility; not a versioned API); Live (versioned; only one live API, the latest major/minor; any change is a versioned change); Deprecated (usable, no new development; after a minor release deprecated only briefly until production validation finishes, then retired because it is backward compatible; after a major release it stays deprecated weeks or months with a migration guide and usage metrics); Retired (removed). With semver and a lifecycle the consumer only cares about the major version.

| Change | Release approach |
|---|---|
| Major (breaking) | Live and deprecated side by side for a long time; version in the URL (`/v1/...`) or a header that drives routing at ingress |
| Minor or patch | Deploy with no production traffic, then canary or mirror; no consumer code change. Add a pipeline gate: run an OpenAPI diff and fail the build on a non-backward-compatible spec unless consciously overridden |
| Tightly coupled consumer and producer (same team, always move together) | Release together with traffic controlled at ingress, typically blue-green |

Most releases should be minor or patch. Full API-design guidance lives in `arch-api-design`.

## 12. Feature flags: rules

- Flag state lives in a config store outside the app; code ships with the feature off. Migrate a small batch of users, toggle back if wrong, continue to 100%.
- The flag service is a single point of failure: degrade gracefully with a last-known-value cache or safe defaults (default off in the book's example).
- Give flags unique names and remove the flag code when the migration ends. The book cites Knight Capital (a reused flag plus a failed deployment, about $460M loss).
- Verify (inferred): flag defaults tested with the flag service down; a stale-flag inventory with cleanup tickets; both branches tested.
- Flags also let you disable feature X without touching feature Y, which makes the mitigation decision simple during an incident.

## 13. Metric-driven promotion and a canary spec to fill in

Argo Rollouts (API Architecture ch. 5) extends Kubernetes with a Rollout resource (a Deployment plus a strategy). Example steps: weight 20, manual pause, 40, pause 10, 60, pause 10, 80, pause 10. An analysis template queries Prometheus; the example success condition is a success rate of at least 0.95, and the Rollout progresses only when it holds. The authors caution that success rate alone is simplistic because some failures are client errors, not infrastructure faults. Equivalents: Flagger, Spinnaker, cloud deployment services.

Fill this in before building or reviewing a canary (adaptation; each line maps to a section above):

```
change types covered:      binary | config | flag | data | environment
population per stage:      5% -> 25% -> 100%        (why these sizes)
duration per stage:        >= one representative cycle; < release cadence
split mechanism:           weighted routing / cell / region / flag cohort
metrics (<= ~12, ranked):  stage 1: crashes, request failures (ratio), p99 latency
                           later:   memory, queue depth, business KPI
exclusions:                4xx from verdict; probes for key URLs
verdict:                   relative (canary vs control) AND absolute (SLO)
metric window:             <= stage duration
on fail:                   automatic halt/rollback; page if rollback fails
only one canary at a time: enforced by (lock / pipeline concurrency)
budget check:              exposure x failure x time-to-rollback <= x% of budget
```

## 14. Rollout signals and application-level gotchas

- Instrument the three pillars: metrics, structured logs, and traces (a unique header added as close to the request origin as possible, propagated everywhere; across queues, in the message envelope). OpenTelemetry is the open standard cited.
- Metrics choice: RED (rate, errors, duration) or the four golden signals (latency, traffic, errors, saturation). Applied mechanically they lose context; add API context (5xx is service failure, 4xx is client, run of 403s or 401s can be an attack).
- Set a baseline range and alert outside it. Early indicators (rising GC pause time, the "strange engine noise") precede client-visible symptoms (API latency, the "check-engine light"). Avoid false positives such as a low-traffic alert firing on weekends.
- Response caching hides failures: a canary looked fine, the full rollout proceeded, then the caller's proxy cache expired and 500s appeared everywhere. During rollout validation, send `Cache-Control: no-cache, no-store` on GETs. Lesson: any gateway, proxy or CDN in front can make rollout metrics lie.
- Header propagation: a service that terminates a request and calls another must copy tracing headers downstream. Decide deliberately which auth headers are safe to forward.
- Two log types help debugging: journal (sparse, important events) and diagnostics (failures). Put a log-type field in structured logs.
- Do not roll out on weekends or when nobody can respond. A Google Home rollout reached 100% on a Saturday with devs unavailable (see `incident-response.md`). Pause a rollout while an anomaly is unexplained.

## 15. Rollback and mitigation speed (SRE Workbook ch. 8)

- Low tolerance for new bugs: detect, roll back, fix, roll forward. Not detect, keep rolling forward, fix, roll forward again. It needs predictable, frequent releases so rollback is cheap.
- A "quick fix" still needs test, build and rollout time. Book numbers: 99.99% availability is about 15 minutes of budget per quarter (plain arithmetic on a 90-day quarter gives about 13), and a roll-forward build may take longer; 99.999% is about 80 seconds per quarter and needs self-healing.
- Avoid changes that cannot be rolled back (API-incompatible changes, lockstep releases). Use feature isolation so one feature can be disabled alone. If the rollout was gradual, draining requests away from bad elements takes seconds versus minutes for a rollback.
- Rollback is not sufficient alone for data corruption.

## 16. Opinionated platforms

Without a conscious decision, each team re-solves tracing, headers, caching and logging. A platform team can offer a paved path so these are solved once, at the price of developer freedom. Decide: can languages be narrowed to a few, can developers be treated as customers of an internal product with a feedback channel, which features add value out of the box (auto-configured OpenTelemetry), and how do existing teams receive new platform features. New apps get the latest stack by default.

## 17. Verification checklist

- Metrics are labelled canary or control and queryable per population.
- Verdict uses relative and absolute criteria; metric window <= canary duration; <= about a dozen metrics, each tied to an SLI or user symptom; 4xx handled.
- Only one canary active; rollback is automatic or a single command and has been exercised.
- Stage sizes and durations are justified from history or stated assumptions.
- The canary system itself is tested with injected faults (the book's toy service fails 20% of requests or slows 5% of them to check the verdict fires).
- Flag defaults tested with the flag service down; stale flags tracked.
- Pipeline fails on breaking API-spec diffs unless overridden.
- No rollout step runs at a time when responders are unavailable.
