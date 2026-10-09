---
name: arch-reliability-slos
description: Defines and operates reliability targets - choosing SLIs per service type, turning a spec into a measurable implementation, setting SLOs and windows, error budgets and policies, SLO documents, burn-rate alerting (multiwindow multi-burn-rate with exact arithmetic), monitoring design, availability maths with dependencies, pager load. Use when asked to "define SLOs", "set an error budget", "write an SLO doc or error budget policy", "alert on SLOs", write or review Prometheus/Datadog alert rules, fix noisy or late alerts, pick latency percentiles, decide metrics vs logs, estimate availability of a design with dependencies, or when a team argues reliability vs feature velocity. Not for incident response, canarying or postmortems (arch-production-operations) or pipeline internals (arch-data-pipelines).
---

# Reliability targets, error budgets and SLO alerting

## Purpose

This skill makes the agent turn "the service should be reliable" into numbers that someone owns, measures and acts on: SLIs shaped as good events over valid events, SLOs with a window, an error budget with a policy, and alerts that page for significant budget burn and stay quiet otherwise. It supplies the arithmetic (burn rates, windows, thresholds) so the agent computes it instead of guessing, and a script, `scripts/burn_rate.py`, that does the sums and checks them. It also keeps the agent honest about what a target is based on (measured, picked, or unvalidated).

## Choose what applies

| The request or situation | Do this | Read |
|---|---|---|
| "What should we measure?", new service, no SLIs | Procedure A (classify components, pick from the SLI menu, spec then implementation) | `references/choosing-slis.md` |
| "Set an SLO / target / window", numbers from history | Procedure B | `references/setting-slos-and-error-budgets.md` |
| "Write the SLO doc" | Fill the template, fill numbers only from data | `references/slo-document-template.md` |
| "Error budget policy", freeze or feature-vs-reliability dispute | Procedure C | `references/error-budget-policy-template.md` |
| Writing or reviewing alert rules for an SLO, noisy or late or never-firing alerts | Procedure D, run the script | `references/alerting-on-slos.md` |
| Low-traffic service, 90% target, 99.99% or 99.999% target | Procedure D steps 5 to 6 | `references/alerting-on-slos.md` sections 7, 8 |
| Dashboards, metric vs log, labels, monitoring-as-code, testing alert rules | Procedure E | `references/monitoring-design.md` |
| Design claims N nines, depends on other services or zones | Procedure F | `references/dependencies-and-availability-math.md` |
| How many pages is too many, vetting a new paging alert | Rules in `references/pager-load-targets.md` | same |
| Requirements written as "fast / reliable / scalable" | Turn into numbers | `references/percentiles-and-nfr-targets.md` |
| Rolling SLOs out across many services, cloud provider SLO, org readiness | Recipes | `references/case-studies.md` |
| Incident roles, postmortem format, canary analysis, toil | Not this skill | `arch-production-operations` |
| Freshness and correctness of data pipelines beyond SLI choice | SLI choice here; pipeline design elsewhere | `arch-data-pipelines` |
| Fitting a scaling curve or capacity forecast | Not this skill | `arch-scalability-analysis` |
| Whole-system design from a problem statement | Not this skill (use for the reliability NFR part) | `arch-system-design` |

This does not apply when the user wants a one-off health check, a tiny internal tool with no users to disappoint, or an alert on something that is not user-visible and needs no SLO (use a plain threshold ticket and say so).

## How to apply

### Core definitions to keep in mind

- SLI = good events / valid events, 0 to 100%. Error budget = 100% - SLO. Error ratio e = bad / total. Burn rate B = e / (1 - SLO).
- State for every SLI: numerator, denominator, threshold, measurement point. Specification (what users care about) is separate from implementation (how measured: logs, load balancer, prober, client). Start with the cheapest honest implementation and move toward the user when reviews show missed incidents.
- Not 100%: change is the main source of outages and each extra nine costs more. The owner who trades velocity against reliability must be named.

### Procedure A: choose SLIs (new service)

1. Pick one application; define who its users are; list their critical tasks.
2. Sketch components and flows; classify each as request-driven, pipeline, or storage.
3. Pick from the menu, at most about five SLI types total:

| Class | SLIs |
|---|---|
| Request-driven | availability, latency (two thresholds, for example 90% under X and 99% under Y), quality (only if graceful degradation exists) |
| Pipeline | freshness (weight by reads), correctness (known-answer prober or oracle), coverage |
| Storage | durability (check the slice users need, not just total bytes) |

4. Write each as spec plus first implementation; list its blind spots. Measure latency as the client sees it if possible.
5. Define error classification in advance (for example only 5xx counts) and calculation rules (what counts as down, maintenance, probe locations).

### Procedure B: set SLOs and windows

1. Compute the SLI over at least four weeks of history (or stand up an external prober first if there is none).
2. Round down: two significant figures for availability, latency to about 50 ms. Keep the number at or below current performance so there is budget rather than instant violation.
3. Back-test: which days would have missed, do they match incidents and ticket spikes?
4. Window: 4-week rolling by default (whole weeks keep weekends equal), weekly review, quarterly planning. Calendar windows only when business planning needs it, and say budgets are then speculative mid-period.
5. Record provenance (measured, rounded how, or ad hoc) and that user-experience correlation is unvalidated if so.
6. Compute budgets in absolute events: allowed bad events = (1 - SLO) x events in window.

### Procedure C: error budget policy

1. Confirm the four preconditions: stakeholders approve the SLO, defenders agree it is achievable, the organisation commits to using the budget, there is a refinement process.
2. Write the actions on exhaustion with owners, mildest effective first (reliability bugs first, then reliability-only work, then freeze with P0 and security exceptions, then emergency).
3. Enumerate exceptions (company-wide network failure, another team's frozen service, out-of-scope traffic such as load tests, miscategorised errors) and name the rule for dependency-caused misses.
4. Add proportional triggers (the example uses a postmortem with a P0 item when one incident takes over 20% of four-week budget) and a named escalation owner and revisit date.
5. The approval is the fitness test of the SLO: if ops cannot defend it without toil, or product finds users hurt before the policy triggers, adjust the SLO.

### Procedure D: alert on the SLO

1. Goal: notify a human for a significant event, one consuming a large fraction of the budget. Judge rules on precision, recall, detection time, reset time.
2. Use multiwindow, multi-burn-rate alerts. Starting set for 99.9% over 30 days:

| Severity | Long window | Short window | Burn rate | Budget consumed |
|---|---|---|---|---|
| Page | 1 h | 5 min | 14.4 | 2% |
| Page | 6 h | 30 min | 6 | 5% |
| Ticket | 3 d | 6 h | 1 | 10% |

   A rule fires when the error ratio over the long window AND over the short window both exceed B x (1 - SLO). The short window is long/12; it keeps the alert from outliving the problem.
3. Adapt to your SLO and window P: B = f x P / W for budget fraction f in window W; consumed = B x W / P; time to exhaustion = P / B; threshold = B x (1 - SLO); full-outage detection = (1 - SLO) x W x B. Run `python3 scripts/burn_rate.py --slo <pct> --window <e.g. 28d>`.
4. Do not use: error rate over a short window at the SLO line (alert fatigue), long windows alone (hours of reset), `for:` duration as the main condition (does not scale with severity, flapping never fires), a single burn rate (misses a 35x burn that empties the budget in 20.5 h).
5. Check extremes: if the threshold ratio B x (1 - SLO) exceeds 1, the rule can never fire (90% SLO with the 2%/1 h page). If a full outage exhausts the budget faster than a scrape plus notification (99.999% gives about 26 s), alerts cannot defend it; limit blast radius by design (1% canary gives about 43 minutes).
6. Low traffic: with 10 requests an hour one failure is a 10% hourly ratio. Options, usually combined: synthetic traffic, group related services, client retry with backoff and jitter plus fallback queues, lower the SLO or lengthen the window (a product decision). Use `--requests-per-hour`.
7. At scale use one parameter set for every service and bucket request classes (critical 99.99%, high 99.9%, low 99%, no SLO) instead of per-service tuning.
8. Add inhibition so one event is one page; use counters, not gauges.

### Procedure E: monitoring design

1. Alerts and dashboards from metrics; logs for root cause and exact reporting. Bounded dimensions (status code, method, version) become labels; unbounded IDs stay in logs behind a runnable query linked from the alert.
2. Dashboard order after the SLI panels: intended changes (version, flags, config version), dependencies (rate, errors, latency per peer), saturation (every resource), served-traffic status codes.
3. Monitoring config in version control with lint and review; loosely coupled collection, evaluation, storage, alerting, dashboards.
4. Test alert logic in three tiers: exported metrics, rule evaluation, routing. Use synthetic series (for example `promtool test rules` for Prometheus rules).
5. Each metric has a purpose; alert metrics move sharply only when the system is in a problem state.

### Procedure F: availability with dependencies

1. List critical dependencies per user journey; use measured availability, not claimed.
2. Serial critical dependencies multiply (0.9999 to the tenth is about 99.9%). Redundancy multiplies failure probabilities only under independence, which shared binaries, control planes, DNS and regions usually break.
3. A critical dependency needs an SLO at least as high as the journey. If it is lower: cache, degrade, queue, or choose another component. Never base your SLO on a provider's published number; share yours with the provider.
4. Decide, and write in the policy, whether dependency-caused misses freeze changes.

## Verify

Run these checks before presenting work, and show the output or numbers.

1. Arithmetic. For every alert rule table, run `python3 scripts/burn_rate.py --slo S --window W` (add `--rule long:short:burn:severity` for custom rows) and paste the table. The "consumed" column must match the intended fraction, no warning about an unfireable rule or a low-traffic single-failure trip may remain unexplained, and short window must equal long/12.
2. Self-test of the tool if you changed it: `python3 scripts/burn_rate.py --self-test` must end with "all self-tests passed".
3. SLI completeness. For each SLI, point to numerator, denominator, threshold, measurement point, and the metric names or queries that produce them. If the metric does not exist, list the task that creates it instead of writing a query against it.
4. Backtest. Replay at least four weeks of the SLI against the proposed SLO and rules: count days missed, pages and tickets that would have fired, and match them to known incidents. If no data exists, say that the target is ad hoc.
5. Synthetic alert tests. Write or describe tests: constant 14.4x burn pages; 1x burn only tickets; a 30-second full-outage blip does not page (1 h ratio 0.83% against the 1.44% threshold) while a five-minute one does; an outage that stops clears within the short window; nested burn rates give one page after inhibition.
6. Document review. SLO document checklist and policy checklist in the two template references: approver and revisit date present, window equal across documents, exceptions enumerated, rationale states data provenance.
7. Dependency claims. Show the product of critical dependency availabilities and the list of shared components for any redundancy claim.
8. Evidence for the user: the printed tables, the list of assumptions marked measured, picked or unvalidated, and the open decisions only humans can make (owner, approvers, freeze authority).

Done means:

- Every SLI is a good/valid ratio with its measurement point and blind spots written down.
- SLOs are below 100%, at or under measured performance, with window, owner and revisit date.
- A policy exists or is explicitly listed as missing, with named actions and escalation.
- Alert rules were derived with the formulas, checked for fireability, low traffic and extreme targets, and have a test plan.
- Provenance and unvalidated assumptions are stated, not hidden.
- Nothing in the output claims approval, measurement or incidents the agent did not see.

## Proportion and limits

- A small internal service, prototype or batch job rarely needs the full set. One availability SLI, one latency pair, a 4-week window and the three-row burn-rate set is enough; skip VALET, per-customer SLOs and aspirational SLOs.
- Without ownership and a policy, an SLO is a vanity dashboard. If nobody can trade features against reliability, say so and recommend fixing that before more metrics.
- The 4-week window, the burn-rate set, the 20% policy triggers, the 50 ms rounding and the 2-incidents-per-shift target are Google defaults from one book; tune them with evidence. The notes themselves call SLO-relaxation experiments a risk and per-customer SLOs noisy.
- The error budget treats one 4-hour outage and a steady 0.5% error rate alike though users feel them differently; consider a second SLI or a duration clause when that matters.
- The 2018 tool references are dated: OpenCensus is superseded by OpenTelemetry, and alert-testing tools now exist; the structure of the advice survives. Prometheus syntax in the references is illustrative.
- Contested or inconsistent items in the source: the printed ticket row (24 h at burn 3) versus the table's single 3-day row; the "1,000x" low-traffic burn rate that arithmetic says is 100x. Use the corrected figures and say so.
- Where the notes mark something inferred (for example load-test knee for capacity alerts), treat it as advice, not data.

## References

- `references/choosing-slis.md`: when picking or reviewing SLIs, measurement sources, latency grades, bucketing, VALET.
- `references/setting-slos-and-error-budgets.md`: when choosing numbers, windows, running reviews, using the decision matrix, prioritising reliability work.
- `references/slo-document-template.md`: when writing or reviewing an SLO document; contains the filled game-service example.
- `references/error-budget-policy-template.md`: when writing or reviewing the policy; contains the example's rules and exceptions.
- `references/alerting-on-slos.md`: when deriving, reviewing or debugging SLO alerts; all six approaches, tables, discrepancies, low-traffic and extreme cases.
- `references/monitoring-design.md`: when designing dashboards, metrics versus logs, config as code, alert tests.
- `references/dependencies-and-availability-math.md`: when a design depends on others or claims redundancy; downtime table.
- `references/case-studies.md`: when bootstrapping or scaling an SLO programme; Evernote, The Home Depot, organisational preconditions.
- `references/pager-load-targets.md`: when setting pager budgets, vetting paging alerts or sizing a rotation.
- `references/percentiles-and-nfr-targets.md`: when turning nonfunctional requirements into numbers; reliability vocabulary.
- `scripts/burn_rate.py`: budget, burn-rate and rule arithmetic; `--help` and `--self-test`.

## Sources

- The Site Reliability Workbook (Beyer et al., 2018) ch. 1: SRE and DevOps, organisational preconditions.
- SRE Workbook ch. 2: Implementing SLOs (SLIs, windows, policy, review, decision matrix, dependencies).
- SRE Workbook ch. 3: SLO engineering case studies (Evernote, The Home Depot).
- SRE Workbook ch. 4: Monitoring (metrics vs logs, purposeful metrics, testing alerts).
- SRE Workbook ch. 5: Alerting on SLOs (burn rates, six approaches, low traffic, extremes, scale).
- SRE Workbook ch. 8: On-call (pager load, alert vetting, staffing).
- SRE Workbook app. A and app. B: example SLO document and error budget policy.
- Designing Data-Intensive Applications 2e ch. 2: nonfunctional requirements (percentiles, faults, scalability).
