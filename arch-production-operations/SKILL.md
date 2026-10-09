---
name: arch-production-operations
description: Practices for running and changing systems in production safely - canary and staged rollouts (population, duration, metrics, rollback), deploy-versus-release and feature flags, configuration design and safe config pushes, load balancing, load shedding, autoscaling and retry interactions, toil reduction with guarded automation, simplicity reviews, on-call and pager load, incident response roles, and blameless postmortems. Use when designing or reviewing a release pipeline, rollout or rollback plan, canary, feature-flag setup, config schema or config-push mechanism, autoscaler, shedding or retry policy, a script that mutates production, an on-call rotation or alert set, an incident, or a postmortem; or when asked "how do we ship this safely" or "why did this outage cascade". SLO and burn-rate alert maths belong to arch-reliability-slos; API versioning and gateways to arch-api-design.
---

# Production operations

## Purpose

Most outages are triggered by changes, not by hardware: in the postmortem data in the notes, binary pushes and configuration pushes together account for 68% of triggers. This skill makes the agent treat every change to a running system (binary, config, flag, automation run, scaling rule) as something that needs a bounded blast radius, an automatic way back, and a way to tell good from bad before everyone is exposed. It also covers how to run the people side when things break: on-call load, incident roles, and postmortems that produce fixes.

## Choose what applies

Find the row that matches the request, read the reference for the full procedure, and use the inline rules below for the common cases.

| Situation | Use | Reference |
|---|---|---|
| Writing or reviewing a deploy or release pipeline, rollout plan, rollback plan | Section A (safe change), canary spec | `references/canarying-and-rollouts.md` |
| "Canary", "blue-green", "dark launch", "feature flag", "gradual rollout", "A/B" | Strategy table in the reference | `references/canarying-and-rollouts.md` |
| Config format, config schema, template language, config repo, config push tool | Section A plus config rules | `references/configuration-design.md` |
| Autoscaler, load balancer, load shedding, retries, timeouts, deadlines, "traffic spike", "cascading failure", "thundering herd" | Section B (load) | `references/managing-load.md` |
| Manual runbook, repeated ops task, ticket queue, "should we automate this", a script that deletes, drains, restarts or reimages | Section C (automation) | `references/toil-and-safe-automation.md` |
| Proposed rewrite, new dependency, new service, "too complex", cyclic or duplicated dependencies | Simplicity review | `references/simplicity.md` |
| Alert list, pager load, rotation size, shift design, playbooks, onboarding on-call | Section D (on-call) | `references/on-call.md` |
| Team drowning in tickets or pages, burnout, "we cannot get to project work" | Overload triage | `references/operational-overload.md` |
| A live or just-ended incident, "who does what", roles, status updates | Section E (incident) | `references/incident-response.md` |
| Writing or reviewing a postmortem or action items | Section F (postmortem) | `references/postmortems.md` |
| "Where should we invest in reliability?" | Use own incident data first, statistics as a prior | `references/outage-statistics.md` |
| SRE engagement model, team splits, adoption of a common tool across teams | Brief notes | `references/organisational-notes.md` |

This does not apply, or belongs elsewhere, when:

- The question is how to define SLIs, SLOs, error budgets or burn-rate alerts: use `arch-reliability-slos`. Here you only consume the budget (to size a canary, gate a release freeze).
- The question is API style, versioning policy, gateways or mesh selection: use `arch-api-design`. Here you only cover how a version is released and observed.
- The question is scaling curves and capacity modelling: use `arch-scalability-analysis`.
- Batch and stream pipelines (freshness, exactly-once): use `arch-data-pipelines`.
- The system is a single-user script, a prototype, or has no production users: most of this is overkill (see Proportion and limits).
- Pure code-level error handling inside a function: use `craft-error-handling`.

## How to apply

### A. Make a change safely (release, config, flag, data push)

1. Classify the change: binary, environment, library, service config, feature flag, user config, data. If several kinds can only ship together, say so; that coupling is the first thing to fix because it blocks independent rollback.
2. Separate deploy from release where you can. Ship code dark behind a flag or a zero-weight route, then expose it in steps. Reason: deployment risk is technical, release risk is business, and mixing them forces choreographed releases across teams.
3. Choose the exposure mechanism by situation:

| Situation | Mechanism |
|---|---|
| Loosely coupled minor or patch change, good monitoring | Canary with weighted routing (gateway, mesh, cell, region) |
| Refactor you want to validate with no user impact; reads or idempotent traffic (mirrored writes duplicate side effects: inferred caution) | Mirroring (dark launch) |
| Consumer and producer released together | Blue-green |
| Monolith with no routing layer | Feature flags first |
| Breaking API change | Live and deprecated versions side by side, not a rollout |
| Billing or other stateful side-effect path | Small real-traffic canary; not synthetic load or traffic teeing |
| Config change | Same ladder: stage it, hermetic artifact, auto-revert if control is lost |

4. Size the first stage by blast radius, not convenience. Exposure x failure fraction x time-to-rollback should be a small share of the period's error budget (this product is the notes' inferred check, not the book's). Example from the book: a candidate that fails 20% of requests, shown to 5% of traffic, causes 1% errors.
5. Pick at most about a dozen metrics, ranked by how well they show user-visible trouble (request failure ratio and latency first; CPU is noisy). Exclude 4xx from the verdict, cover key URLs with probes. Stage 1 uses only the clearest signals; add weaker metrics in later, larger stages.
6. Compare canary with control simultaneously, per population, never service-wide and never before/after. Keep the metric window no longer than the stage, run one canary at a time, and add an absolute SLO check beside the relative one because canary and control share infrastructure.
7. Make rollback the default response: detect, roll back, fix, roll forward. Do not keep rolling forward while debugging. If rollback is impossible (lockstep, incompatible API or schema), redesign the change so it is possible, or use a flag to switch the feature off.
8. Config specifically: validate generated data right after evaluation (schema plus domain checks, unknown fields rejected), run the same checks in precommit and CI, keep evaluation free of side effects so the same inputs give the same output, log both the commit and the application of a change, give every snippet one owner, and make the questions asked of users few, with safe defaults.
9. Do not release at times when nobody can respond (weekends, end of day), and pause a rollout while an anomaly is unexplained.

### B. Review a load-management design (balancing, shedding, autoscaling, retries)

1. List every tool that reacts to load and, for each, the signal it reads and what it changes. Any pair where one reads what the other changes is a possible feedback loop; test or damp it. The notes' case: a balancer that read CPU saw a shedding region as "efficient" (rejected requests are cheap) and sent it more traffic.
2. Autoscaler: set min and max with quota to reach max; scale on a capacity or health-aware metric so unhealthy instances do not dilute the average; add a cool-down; scale up fast and down slowly; keep a kill switch the on-call knows; analyse dependency headroom before turning it on.
3. Order thresholds so the system scales before it sheds. Shed responses must be visible to the balancer as "full" and to monitoring.
4. Keep a per-location minimum of instances so failover capacity exists even if the autoscaler concentrates capacity.
5. Retries: jittered truncated exponential backoff, a cap or budget, retry at one layer only, and a deadline on every RPC with servers dropping work whose client has gone.
6. Monitor demand where it first appears (the edge); connections refused before reaching a backend are otherwise invisible.

### C. Decide whether and how to automate operational work

1. Measure first in a consistent unit (minutes, tickets, changes); track it automatically. Without a baseline you cannot show the automation helped.
2. Ask in order: can the task be rejected or batched, can the source be engineered away (fix the software, remove the config), can it be a human-backed form or self-service, only then full automation. Prefer root-cause fixes over scripts that mask a problem.
3. Compare cost to build and maintain against time saved; count indirect benefits (fewer human-error outages, shorter training, morale).
4. Before any automation touches production, require the guardrails: input validation (an empty filter means "nothing", never "everything"), a blast-radius cap and rate limit, idempotent or fail-safe on re-run, a second limit-based check, escalation to a human on any unsafe condition, verification before restoring traffic, a kill switch, and an alert on the fraction of fleet affected.
5. Build small composable parts, not a transcript of the human runbook; use the work to simplify the process.

### D. Review an on-call setup or alert set

1. Each paging alert must be actionable by a human within its response-time tier, symptom- or SLO-based, linked to a playbook entry, and trialled in non-paging mode for about a week before it pages.
2. Budget: at most 2 incidents per 12-hour shift; track a trailing average (the notes use 21 days) and ticket the lead when it crosses a warning threshold.
3. File a bug per paging alert; aim for a root cause for every page; do a systemic fix when the break-even is reachable (project hours divided by hours per page).
4. Staffing minimums from the notes: 5 per site (6 with a spare) for multisite 24/7, 8 (9 with a spare) for single-site; shifts up to 12 hours; a scheduler that never edits a published schedule.
5. If load is high, go to `references/operational-overload.md` and quantify before reorganising.

### E. During an incident

1. Declare early and name an incident commander in the first minutes; the commander holds every role not delegated. Split off an ops lead and a communications lead as responders arrive, and a scribe.
2. Priority order: assess impact, mitigate, find root cause, then fix and write up. Reach for a generic mitigation (rollback, drain, failover, flag off, traffic shift) before understanding the cause; you only need to know where the problem is.
3. One channel, one shared working doc once three or more people are working, updates on a fixed cadence, and rotate people on long incidents.
4. After mitigation, hold further rollouts until the root cause is known. Assign the postmortem owner before closing.

### F. Postmortems

1. One owner, collaborators from every involved team, published within about a week, shared widely by default.
2. Separate trigger from root cause; quantify impact with sources; state detection and mitigation gaps.
3. Describe systems and process, never named people; no emotive wording.
4. Action items: grouped by theme, each with type (prevent, mitigate, detect, repair, investigate), priority, single owner, tracking bug and a measurable end state; at least one prevent item; at least one P0 or P1 for user-affecting outages; "train people" is never the only prevention.

## Verify

Show the user evidence, not assertions. Pick the checks that match what you did.

Release or canary design:
- Canary spec filled in (stages, durations, metrics, verdict, rollback, budget arithmetic) and consistent with the release cadence.
- Metrics are labelled by population and queryable; the metric window does not exceed the stage; 4xx handling stated.
- Rollback exercised once in a non-production run, with the time it took. Fault injection against the canary system (make the candidate fail a set share of requests or slow some) and confirmation that the verdict fires.
- Flag defaults tested with the flag service unreachable; list of flags past their intended removal date.
- API-spec diff gate in the pipeline fails on breaking changes unless overridden.

Config:
- Evaluate twice in different environments and compare the output byte for byte (the hermetic test, labelled inferred in the notes).
- A bad value (wrong unit, nonexistent path, unknown field) is rejected at commit time by a test you ran, not just described.
- A refactor of config source produces an empty diff in generated output.
- Rollback re-applies an earlier artifact, not a fresh evaluation.

Load:
- Load or staging test with one location pushed past the shed threshold: traffic leaves it. A dependency made slow: the autoscaler stops at its max and does not pile on. Kill-switch drill performed. Retry timestamps show jitter.

Automation:
- Tests for empty input, repeat run, over-limit input and unsafe condition; the toil measure before and after.

On-call and incidents:
- Pages and incidents per shift over the trailing window against the budget; alerts without a runbook, owner or bug; staffing against the minimums.
- Incident review questions: declared early? commander named in minutes? one channel and doc? generic mitigation available and rehearsed? postmortem owner assigned?

Postmortem:
- Run the checklist in `references/postmortems.md` against the draft and report failed boxes; search for personal names in cause and action sections and for vague verbs ("improve") with no end state.

Done means:
- Every change path has a bounded exposure, a verdict that does not depend on a person watching a graph, and a tested way back.
- Feedback loops between load tools have been named and tested or damped.
- Automation has guardrails and a measured baseline.
- Alerts, rotation and postmortem items have owners, tiers and trackers.
- The user has seen the evidence above, with any item you could not check listed as unchecked.

## Proportion and limits

- Scale the ceremony to the blast radius. A one-person internal tool needs a rollback command and a smoke test, not a multi-stage analysis. The full canary spec, staged config pipeline and incident-role structure pay off when many users or many teams are affected, or when a bad change is costly to reverse.
- Canary statistics are deliberately simple in the source ("steering clear" of deep statistics). If the traffic is too low to give a signal in the available time, say so and fall back on smaller steps, probes, mirroring or a manual check, rather than pretending a verdict is meaningful.
- Percentages and thresholds (50% ops cap, 2 incidents per shift, 10 tickets per person, 21-day trailing average, team sizes, SRE ratios) are Google or single-team heuristics. Use them as starting points and calibrate to the team. The notes themselves show a 3-day ticket SLO backfiring.
- Tool names (Jsonnet, ksonnet, Argo Rollouts, LaunchDarkly, GCLB, App Engine, Spinnaker) are dated examples; the properties they illustrate are the guidance. Today's equivalents include Flagger, Kustomize, CUE, Starlark, service-mesh traffic splits and cloud load-balancer weights.
- Outage shares (binary 37%, config 31%) come from one very large company's postmortems; test them against the user's own incidents before using them to argue for investment.
- Automating a rare, high-risk operation can cost more than doing it carefully by hand; the ROI test in section C applies.
- Config languages are a strategy for rising complexity, not a starting point: if a team has a few small files, removing config and adding validation beats introducing a DSL.
- Some chapters are organisational and Google-shaped (engagement models, team lifecycles); `references/organisational-notes.md` is brief on purpose.

## References

- `references/canarying-and-rollouts.md`: read for any release, rollout, canary, flag, blue-green or mirroring design; has the strategy table, canary spec template, metric rules and API lifecycle mapping.
- `references/configuration-design.md`: read when designing or reviewing configuration, a config language, validation, or config rollout.
- `references/managing-load.md`: read for balancing, shedding, autoscaling, retries and deadlines, and for the case studies of cascades and feedback loops.
- `references/toil-and-safe-automation.md`: read before automating operations or when measuring and ranking toil; has the guardrail list and the network-repair and decommission cases.
- `references/simplicity.md`: read when judging a rewrite, a new dependency or growing variety; has the complexity proxies and the cycle and amplification checks.
- `references/on-call.md`: read for alert quality, pager load, rotation design, playbooks and onboarding.
- `references/operational-overload.md`: read when a team is overloaded or burning out and you need to measure and triage.
- `references/incident-response.md`: read during or when designing incident process: roles, declaration, communication, drills, case lessons.
- `references/postmortems.md`: read when writing or reviewing a postmortem; has the bad-versus-good analysis, template skeleton and checklist.
- `references/outage-statistics.md`: read when prioritising reliability investment or designing postmortem taxonomy.
- `references/organisational-notes.md`: read for SRE engagement, team structure, customer reliability engagement, and change management among people.

## Sources

- SRE Workbook (Beyer et al., 2018) ch. 6 Eliminating Toil; ch. 7 Simplicity and the operational-work interlude; ch. 8 On-Call; ch. 9 Incident Response; ch. 10 Postmortem Culture; ch. 11 Managing Load.
- SRE Workbook ch. 14 Configuration Design and Best Practices; ch. 15 Configuration Specifics; ch. 16 Canarying Releases; ch. 17 Identifying and Recovering from Overload; App. C Postmortem Analysis.
- SRE Workbook ch. 18 SRE Engagement Model, ch. 19 Reaching Beyond Your Walls, ch. 20 SRE Team Lifecycles, ch. 21 Organizational Change Management (brief organisational reference only).
- Mastering API Architecture (Gough, Bryant, Auburn, 2022) ch. 5 Deploying and Releasing APIs.
