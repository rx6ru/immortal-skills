# Pager load targets and vetting paging alerts

Sources: SRE Workbook ch. 8 (on-call: pager load, alert rules, follow-up, data quality, staffing numbers), ch. 3 (Evernote classes).
Scope boundary: this file covers how many pages are acceptable and how to vet a paging alert so the SLO alerts in `alerting-on-slos.md` stay sustainable. Incident response, postmortems and rotation design in depth belong to `arch-production-operations`.

## 1. Targets and definitions

- Pager load = the number of paging incidents an on-call engineer receives over a typical shift (per day or week). One incident is one problem however many alerts fire.
- Target: at most 2 incidents per on-call shift, with a shift of 12 hours. SREs spend at least 50% of time on project work. Too much pager load needs corrective action.
- Psychological safety matters; out-of-hours on-call should be compensated (time off or cash, capped at a share of salary so people do not take shifts for the money).
- Shift length: 12 hours or less if the rotation receives one or more pages a day; 24 hours without reprieve is not sustainable. A single site can split a week between two engineers (day and overnight) or use shorter shifts such as three days on, four off.
- Minimum rotation size: 5 people per site for multisite 24/7, 8 for single-site 24/7. Add one spare each: 6 per site (multisite) or 9 (single site).
- Monitor trends: a 21-day trailing average of pager load is useful; send a ticket alert to leads or managers when load crosses a pre-agreed warning threshold; discuss trends at production meetings.

## 2. Response-time tiers: set per alert

| Incident | Response time | Impact on the engineer |
|---|---|---|
| Revenue-impacting network outage | 5 minutes | within arm's reach of a charged, authenticated laptop with network; cannot travel; must coordinate with the secondary |
| Customer order batch processing stuck | 30 minutes | can run a quick errand or short commute |
| Backups of a pre-launch service failing | ticket, work hours | none |

Engineers should not have to work within minutes unless there is good reason. Audit every page: should it be an automated repair (a computer fixing it beats a human) or a ticket? This is where the page versus ticket choice in the burn-rate tables comes from: pages for budget burning fast, tickets for burns leaving days.

Evernote's alert classes: P1 handle immediately (immediately actionable, pages on-call, leads to triage, SLO-impacting); P2 next business day (generally not customer-facing or of limited scope; email the team and notify the event channel); P3 informational (dashboards and passive email, including capacity data). Every P1 and P2 gets an incident ticket (triage, remediation tracking, SLO impact, occurrence count, postmortem link).

## 3. Rules for a paging alert

- Every alert is immediately actionable: it needs a human action the system cannot do itself, with high signal-to-noise.
- If using SLO-based burn-rate alerting, all teams must agree the SLO matters and prioritise accordingly. With SLO plus symptom-based alerting, relaxing thresholds is rarely the right response to being paged.
- Page on error ratio, not error rate: in the team-dynamics scenario, one developer insisted on paging by absolute error rate, which was noisy and unactionable and led others to ignore duplicate pages.
- Review new alerts like code: the whole team reviews additions; each alert has a playbook entry (severity and impact, debugging suggestions, mitigation actions). Playbook entries that are a deterministic list of commands run every time the alert fires should be automated instead.
- Vet in production before promoting to a page: run in test mode (for example email the author) for at least one cycle of periodic conditions (rollouts, provider maintenance, weekly peaks); about a week is probably right. Use the trigger rate in that window to predict pager budget consumption, and approve or reject explicitly as a team. If a new alert pushes the team over budget, stability needs attention. New alerts also act as regression tests after bugs are fixed.

## 4. What drives pager load

Three factors: production bugs, alerting, human processes.

- Production: number of existing bugs, new bugs introduced, speed of identifying and of mitigating them. "Bug" is broad: logic errors, binary misconfiguration, wrong capacity planning, misconfigured load balancers, vulnerabilities, architectural gaps such as missing health checking, self-healing or load shedding.
- Alerting: thresholds, new paging alerts, and alignment of the service's SLO with its dependencies' SLOs.
- Human: rigour of fixes and follow-up, data quality about pages, attention to trends, human-actuated production changes.

Levers:

- Pre-existing bugs: keep systems no more complicated than needed, update dependencies regularly (new bugs risk), run destructive testing or fuzzing, run load tests beyond unit and integration tests.
- New bugs: for each production bug ask how it could have been detected before production, and do that follow-up. Staging with production-like synthetic traffic; canaries. Low tolerance: detect, roll back, fix, roll forward, not keep rolling forward. That needs predictable, frequent releases so a rollback is cheap. Beware bugs that appear only with changed client behaviour (peak events, unusual request mixes, unexpected use).
- Error budgets: when SLO violations exceed an agreed fraction of the quarterly budget, halt feature rollouts to stabilise.
- Identification delay: pages link to consoles that highlight out-of-spec behaviour; correlate black-box and white-box signals; keep playbooks current (the on-call updates them when the page fires); a searchable change-log timeline; small frequent releases; canarying; asking for help.
- Mitigation delay: roll back if safe (not enough alone for data corruption); a quick fix still needs test, build and rollout time. At 99.99% the budget is about 15 minutes per quarter (13 by arithmetic over 90 days) and a roll-forward build may take longer; 99.999% (about 80 seconds) needs self-healing. Avoid non-rollbackable changes. Feature flags per feature so one can be disabled without another. Drain traffic away from bad elements (seconds) when the rollout was gradual.
- Rigour of follow-up: aim to find a root cause for every page; "transient" is not a cause; if unknown, add logging or monitoring so next time it is known. Prefer systemic fixes to point fixes. Break-even example: a project costing three working weeks (120 hours) pays back after 30 pages when a page costs about 4 hours to handle. Three levels for a failure-domain concentration: rebalance now; automation that always spreads across enough domains; a ticket alert when diversity falls below expectation before service is hurt.
- Follow-up questions: prevent this bug again? prevent similar bugs here and elsewhere? what tests would have caught it? what ticket alerts could have prompted action before the page? what informational alerts could have surfaced it on a console?

## 5. Data about pages

File a placeholder bug for every paging alert; the on-call links the alert to the bug when it proves symptomatic of an existing issue. That gives bugs ranked by pages caused, components ranked by pages, correlation with request rate or signups, an auto-populated known-issues list for support, and auto-prioritisation by page count. Keep a documented data-collection policy and use non-paging alerts to flag pages not handled according to it.

Questions the data should answer: which bug to fix first; which component pages most; which manual repetitive actions on-call performs; how many alerts have unidentified root causes.

## 6. Scenarios worth remembering

- A team with a budget of 2 incidents per shift but regularly 5 for a year, a third of shifts over budget, people leaving: causes were many owned components, hard dependencies on edge and backbone networks whose failures they could only escalate, simultaneous feature delivery, and a migration off an old framework (the rate of change itself raised load). Lever: operational-overload evidence presented to senior management, then full attention on pager load.
- Human error was the second most common cause of new bugs in the same team; changes should come from automation that runs extra pre-change checks, driven by human-written intent configuration.
- Part-time and flexibility: shifts shorter than a week; schedulers that honour preferences and recent load and never change a published schedule; swap policy with peer review.

## 7. Checklist for an SLO-based paging setup

1. Every paging alert is symptom or SLO based, immediately actionable, linked to a playbook entry, vetted about a week in non-paging mode, and its pager-budget impact estimated.
2. Budget: at most 2 incidents per 12-hour shift; 21-day trailing average tracked; warning threshold ticket alert.
3. Each page creates or links a bug; root cause found or instrumentation added; systemic fix considered via the break-even calculation.
4. Staffing at least 6 per site (multisite) or 9 (single site); shifts 12 hours or less.
5. Response-time tier set deliberately per alert (5 minutes, 30 minutes, ticket).
6. Burn-rate rules use the multiwindow set with inhibition so one incident is one page.
