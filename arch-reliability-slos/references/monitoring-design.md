# Monitoring design: metrics, logs, purposeful dashboards, monitoring as code, testing alerts

Sources: SRE Workbook ch. 4 (all), ch. 8 (alert vetting), ch. 5 (counters and windows); DDIA 2e ch. 2 (percentiles, histograms).

Use when designing or reviewing monitoring and alerting for a service, choosing between metrics and logs, adding labels, building dashboards, reviewing metric cardinality, or testing alert rules.

## 1. Purposes of monitoring

Alert on conditions needing attention; investigate and diagnose; display; trend (capacity and service health); compare before and after a change or between experiment groups. The relative importance of these purposes drives the trade-offs in choosing or configuring a system.

## 2. Feature checklist for a monitoring system

Speed
- Freshness bounds time-to-page. Stale data misleads incident response (cause and effect lag, so a change appears to have done nothing, or a false correlation is inferred). Data more than about 4 to 5 minutes stale significantly slows incident response. Decide speed requirements up front.
- Query speed matters for big aggregations. Useful capability: derive and store new time series from incoming data (recording rules) so common queries are fast.

Calculations
- Retain data for several months at least, for trends and growth. Aggregated data is enough for growth planning; detailed per-metric retention answers "has this happened before?" but costs more.
- Prefer monotonically increasing counters for events and resource consumption. They let the system compute windowed rates; long-window rates (up to a month) are the building block of burn-rate alerting (`alerting-on-slos.md`).
- Need percentiles (50, 95, 99), not just means. The mean says "slower"; percentiles say whether 50%, 5% or 1% of requests are slow. If the system lacks percentiles: compute mean as total seconds over request count, or log every request and scan or sample logs.
- Keep raw data in a separate system for offline analysis and complex reports.
- Aggregation rule (DDIA 2e ch. 2): averaging percentiles is meaningless; merge histograms, then take the percentile. Approximations like HdrHistogram, t-digest, OpenHistogram and DDSketch exist for large volumes.

Interfaces
- Concise time-series graphs, tables, heatmaps, histograms, log-scale graphs. Different views for different audiences (executives versus on-call). Same data types shown consistently across dashboards. The team must be comfortable drilling down and slicing by machine type, server version, request type.

Alerts
- Severity levels so the response is proportional (a ticket for a low error rate lasting over an hour; a page for 100% errors).
- Suppression: alert once on a global error rate when all nodes show the same high rate; suppress your alerts when a dependency's alert is firing; make sure suppression ends with the event.
- Build versus buy depends on the control you need.

## 3. Metrics versus logs

| | Metrics | Logs |
|---|---|---|
| Form | numerical samples at regular intervals | append-only event records (use structured logs) |
| Latency | near real time | delayed, processed in batch |
| Granularity | low | high |
| Accuracy | less | nearly always more accurate |

Practice from the notes: alerts and dashboards come from metrics; logs are for root cause and for accurate reporting that is not time-sensitive. Even for "alert on a single exceptional event", increment a counter when it happens and alert on the counter, so all alert configuration lives in one place.

### Decision rule

- A bounded-cardinality dimension needed for alerting or graphing (status code, RPC method, version, region) becomes a metric label.
- An unbounded identifier needed only during investigation (user ID, entity ID, with millions of values) stays in logs. Make the log query a runnable script and reference it in the alert text; optionally run it automatically when the alert fires, or poll logs on a small server for semi-fresh data.

### Three worked decisions

1. Move information from logs to metrics. A platform exposed HTTP status only in logs, so the dashboard had a single global error rate and debugging meant graph, grep, correlate by hand with no sense of scale. Fix: export status code as a metric label (`requests_total{status=404}` versus `{status=500}`); safe because the label set is small. Result: separate error lines per code, customers can hypothesise from codes, separate alert thresholds for client versus server errors, more accurate alerts.
2. Improve both logs and metrics. An ads team with about 50 services in several languages used logs as the source of truth for the SLO, with per-service log scripts full of special cases (the example rule counts a 5xx as an error only if a server-error field is set, no debug cookie is present, the URL is not a reports URL and the exception is not a particular type). Hard to maintain; metric alerts diverged from user-facing errors; every alert needed a triage step. Fix: a library hooked into each framework decides at request time whether the error affects users and writes the decision to both the log and the metric at once. Result: one control surface, reusable tooling and alert logic, alerts tied to the SLO and actionable, far fewer false positives.
3. Keep logs as the source. Per-incident questions about affected entity IDs cannot be metric labels. Fix: a script, linked from the alert email, runs the one-off log query. Slower than metrics, but it lowers cognitive load.

## 4. Managing the monitoring system

- Monitoring is a production service: give it the engineering care of one.
- Configuration as code: version control, change history, links to the task tracker, rollback, linting (for example promtool check for Prometheus), mandatory code review. Prefer intent-based, file-based systems over UI-only or CRUD APIs; tools like grafanalib make UI-configured pieces codable.
- Consistency: converge on one framework and one central dashboard service. Faster ramp-up when engineers change teams, easier cross-team debugging, discoverable dashboards. Make baseline monitoring effortless: all services export a consistent basic metric set through an instrumentation library (OpenCensus is the example; adaptation: OpenTelemetry is its successor) or a service mesh, so a new component gets baseline monitoring and dashboards automatically.
- Loose coupling: separate collection, rule evaluation, long-term storage, alert aggregation and dashboarding behind stable interfaces. Modern composition example: a Prometheus server for rule evaluation, a time-series store for long-term storage, Alertmanager for aggregation, Grafana for dashboards, versus a monolith. Instrumentation standards: statsd and the Prometheus format (being standardised as OpenMetrics). Example benefit: Google moved dashboards out of a system where dashboards shared configuration with alert rules into a separate dashboard service while migrating its monitoring backend, which let the dashboard service chart both and made migration gradual.

## 5. Metrics with purpose

When an SLO alert fires, the SLI panels are the first thing an on-call looks at. Put them on the landing page of the service dashboard. SLO dashboards say that you are violating, not why, so add panels in this order:

1. Intended changes: binary version, command-line flags (especially feature toggles), version of dynamically pushed configuration; if unversioned, the timestamp of the last build or package. The alert should link to a graph that lets the on-call correlate the outage with a rollout instead of trawling CI/CD logs. Logs are acceptable as the source since changes are infrequent, but surface them on dashboards.
2. Dependencies: monitor responses from direct dependencies even if you did not change anything: request and response sizes, latency, response codes (the four golden signals), labelled by response code, RPC method and peer job. Instrument the low-level RPC client library once instead of each caller, so new dependencies get monitoring free. For narrow-API dependencies (one `Get` or `Query` RPC with the command in the arguments), a single instrumentation point shows high-variance latency and ambiguous errors; either export dependency-specific metrics that unpack the requests or ask the owners to split the API into separate methods.
3. Saturation: usage of every resource, hard-limited (RAM, disk, CPU quota) or soft (file descriptors, thread-pool active threads, queue wait times, volume of logs written). Language-specific ones: Java heap, metaspace and GC; Go goroutine count. Alert when approaching exhaustion for resources with hard limits, or where crossing a threshold degrades performance. Track everything, including well-managed resources, for capacity planning.
4. Status of served traffic: break down by status code (unless the SLI already does); monitor all HTTP response codes even if not alert-worthy, since they can reveal incorrect client behaviour; monitor requests denied by rate or quota limits. This helps spot error-volume shifts during production changes.

Implementing purposeful metrics: each metric needs a purpose; resist exporting because it is easy. Alerting metrics should change dramatically only when the system enters a problem state. Debugging metrics need not obey that but must point at a possible cause. When writing postmortems, ask which additional metric would have diagnosed the problem faster.

## 6. Testing alerting logic

Alert rules may not fire for months or years, so you need confidence that the right people get notified with sensible messages. Aim for the testing standards of code. The notes say no broadly adopted tooling existed in 2018 (Google used an internal DSL that creates synthetic time series and asserts on derived series or alert state and labels). Adaptation: tools such as `promtool test rules` now provide this for Prometheus-format rules; the structure of three tiers still applies.

| Tier | What it checks |
|---|---|
| 1. Binary reporting | exported metric variables change as expected under given conditions |
| 2. Monitoring configuration | rule evaluation produces expected results; specific conditions produce expected alerts |
| 3. Alerting configuration | generated alerts are routed to the predetermined destination based on label values |

If a stage cannot be tested synthetically, build a running system that exports well-known metrics (requests, errors) and use it to validate derived series and alerts.

A concrete test for burn-rate rules: feed a series with a constant 1.44% error ratio and assert the page fires, feed 0.2% and assert only the ticket fires, feed 30 seconds of full outage and assert nothing pages (a five-minute full outage should page), feed an outage that then stops and assert the page clears within the short window. `scripts/burn_rate.py` gives the expected times.

## 7. Review checklist

- Can the on-call move from the alert link to the SLI panel, then to version, flags and config version, then dependency panel, then saturation panel, then status-code breakdown?
- Are alerts and dashboards driven by metrics, with logs used for investigation and exact reporting?
- Are there high-cardinality labels (user or entity IDs)? Remove them.
- Is latency recorded as histograms or per-threshold counters, with percentiles, not just means? Are counters used where rates are needed, not gauges?
- Is monitoring configuration in version control with lint and review?
- Are there tests at the three tiers, or a known-metrics canary system?
- Is data freshness under about 4 to 5 minutes for pageable signals?
- Do alerts link to a runbook entry and the SLO dashboard?
- Is each metric exported for a stated purpose?

## 8. Warning signs

Alerts built on log scripts with service-specific special cases; dashboard configuration coupled to alert rules; high-cardinality labels; averages only for latency; gauges where counters are needed; alert rules never exercised and routing never tested; stale data; metrics exported because they were easy.
