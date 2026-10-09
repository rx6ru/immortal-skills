# On-call: design, pager load, alerting hygiene, staffing

Sources: SRE Workbook ch. 8 (On-Call), ch. 6 (toil and operational load), ch. 20 (maturity items). Numbers are Google heuristics from the notes; the team-specific ones are flagged. For alert maths (burn rates, windows) see `arch-reliability-slos`; for overload at the team level see `operational-overload.md`.

## Contents

1. Baseline rules
2. Response-time tiers
3. Pager load: what drives it
4. Reducing each driver
5. Rules for new and existing alerts
6. Follow-up rigor and data quality
7. Vigilance
8. Shifts, schedules, swaps, breaks, part-time
9. Staffing minimums
10. Onboarding a new on-call
11. Playbooks
12. Team dynamics scenarios
13. Checklist for designing or reviewing an on-call setup
14. Verification

## 1. Baseline rules

- SREs spend at least 50% of time on project work. Target at most 2 incidents per on-call shift (one incident is one problem however many alerts fire; one shift is 12 hours). Psychological safety is vital. Out-of-hours on-call should be compensated (time off or cash, capped at a share of salary so people do not take shifts for money). Too high a pager load demands corrective action.
- Pager load is the number of paging incidents an on-call engineer receives over a typical shift length. Operational underload also exists: too little ops work and engineers forget how the service works. Counter by taking more risk and moving faster (shorter release cycles, more DR testing); if perpetually underloaded, onboard more services or hand one back.

## 2. Response-time tiers

| Incident | Response time | Impact on the engineer |
|---|---|---|
| Revenue-impacting network outage | 5 min | Within reach of a charged, authenticated laptop with network; cannot travel; must coordinate with a secondary |
| Customer order batch processing stuck | 30 min | Can run a quick errand or short commute; secondary need not cover |
| Backups for a pre-launch service failing | Ticket (work hours) | None |

Engineers should not have to work within minutes without good reason. Audit every page: should it be automated repair (a computer fixing beats a human) or a ticket?

## 3. Pager load: what drives it

Three factors: production bugs, alerting, human processes.
- Production: number of existing bugs, new bugs introduced, speed of identifying them, speed of mitigating or removing them.
- Alerting: thresholds, introduction of new paging alerts, alignment of the service's SLO with the SLOs of its dependencies.
- Human: rigor of fixes and follow-up, quality of data about pages, attention to trends, human-actuated production changes.

"Bug" is broad: code logic errors, binary misconfiguration, wrong capacity planning, misconfigured balancers, new vulnerabilities, and architectural gaps (missing health checking, self-healing, load shedding).

Scenario: a team budgeted 2 incidents per shift but regularly got 5 for a year, one-third of shifts exceeded the budget, people left. Monitoring was already symptom-based. Causes: components from over 10 dev teams, hard dependencies on edge and backbone networks (pages outside their control whose only action is escalation), simultaneous feature delivery, and migration off a 10-year-old framework. Fix: a program manager and people manager proposed a project to senior management and the team gave it full attention. Lever: overload evidence (data) plus management approval.

## 4. Reducing each driver

- Pre-existing bugs: keep systems no more complicated than needed (`simplicity.md`); update dependencies regularly (mind new bugs); do regular destructive testing or fuzzing; load test beyond unit and integration tests.
- New bugs: for each production bug ask how it could have been detected before production and do the follow-up. Run staging with production-like synthetic traffic; canary in production. Detect, roll back, fix, roll forward (`canarying-and-rollouts.md`). Expand tests to non-daily behaviour: peak events, DST weeks, particular request mixes, unexpected use. Fix existing bugs before new features. When SLO violations exceed an agreed fraction of the quarterly budget, halt feature rollouts. Policy example: every outage has a tracking bug; one team found human error was the second most common cause of new bugs, so changes should be made by automation from human-written intent config, since automation can run extra pre-change tests.
- Identification delay (the longer to identify the cause, the more chances to recur): pages link to relevant consoles that highlight out-of-spec behaviour; correlate black-box and white-box alerts; keep playbooks current (on-caller updates them when the page fires); Wheel of Misfortune; small frequent releases; canarying; a searchable change-log timeline; ask for help.
- Mitigation delay: roll back if safe; a quick fix still needs test, build and rollout time; avoid non-rollbackable changes; use a flag per feature; drain requests away from bad elements instead of rolling back when the rollout was gradual. 99.99% leaves about 15 minutes of error budget a quarter as the book rounds it (about 13 by arithmetic on 90 days; a roll-forward build may take longer); 99.999% about 80 seconds, which requires self-healing.

## 5. Rules for new and existing alerts

- Every paging alert is immediately actionable by a human (something the system cannot do itself) with high signal to noise.
- With SLO-based (error-budget burn) alerting, all teams must agree the SLO matters. With SLO plus symptom-based alerting, relaxing thresholds is rarely the right response to being paged.
- Review new alerts like code: the whole team reviews additions; each alert has a playbook entry. Vet in production before promoting to paging (for example email the author instead of paging). Run in test mode for at least one cycle of periodic conditions (rollouts, provider maintenance, weekly peaks); a week is probably about right. Use the trigger rate in the test window to predict pager-budget consumption, then approve or disallow explicitly. If a new alert pushes you over budget, stability needs attention. New alerts behave like regression tests after old bugs are fixed.
- Evernote-style migration lesson: restate paging from first principles as explicit SLOs; alert on higher-level indicators (API responsiveness), not low-level ones (row lock waits).

## 6. Follow-up rigor and data quality

- Find a root cause for every page. If it is unknown, add logging or monitoring so next time you can; "cause unknown" should be rare. Do not dismiss pages as transient. Ask a colleague to review findings; investigate while evidence is fresh.
- Prefer systemic projects over point fixes. Break-even example: 3 working weeks (120 hours) versus about 4 hours per page is 30 pages.
- Follow-up questions and the three-level fix example are listed in `postmortems.md` section 4.
- Reserve a fraction of SRE and developer time for production bugs; on-callers typically do no project work during the shift but work on bugs that improve system health; production bugs rank above other project work.
- Data: file a placeholder bug for every paging alert; the on-caller links the alert to an existing bug when it is symptomatic of one. Reports: bugs by pages caused, components by pages, correlation with request rate, concurrent sessions or signups, an auto-populated known-issues list for support, auto-prioritised bugs by page count. Keep a documented data-collection policy, non-paging alerts flagging pages not handled per policy, and teammates nudging one another in handoffs.

## 7. Vigilance

Overload arrives by a thousand cuts. Discuss pager-load trends at production meetings (a 21-day trailing average is useful); ticket-alert leads or managers when load crosses a pre-agreed warning threshold; hold regular SRE-developer meetings on outstanding paging bugs.

## 8. Shifts, schedules, swaps, breaks, part-time

- Shift length at most 12 hours if the rotation gets at least one page a day; 24 hours without reprieve is not sustainable. A single site can split a week between two engineers (day and overnight), or use shorter shifts such as 3 days on and 4 off. Tired people err; labour laws apply.
- Automate scheduling. "Fair" is not uniform: the tool should rearrange shifts for changing needs, rebalance automatically, honour preferences ("no primary weekends in April") and recent load history, and never change an already published schedule.
- Short-term swaps: expect them; allow partial-day swaps; non-urgent swaps best-effort; account for commute against the response SLO (a 5-minute SLO plus a 30-minute commute needs cover). Let the team edit the rotation under a documented swap policy; peer review of changes is the good safety and flexibility trade-off.
- Long-term breaks: size the team so a temporary reduction does not overload others.
- Part-time: assume part-timers are not on call outside their working week. Fewer full days: shorter shifts (Monday to Thursday, Friday to Sunday). Fewer hours per day: split the shift (they take 9am-3pm, others rotate 3pm-9pm). Scale on-call compensation and share proportionally.

## 9. Staffing minimums

| Setup | Minimum | With one spare each |
|---|---|---|
| Multisite 24/7 | 5 per site | 6 per site |
| Single-site 24/7 | 8 | 9 |

Rough implication (inferred in the notes): with about one-third of time on operational work, at least about 3 people per rotation.

## 10. Onboarding a new on-call

Case: a new team of 7 had to be on-call in 3 months (normal is 3 to 9 months). Results: machine cost down 40%, fully automated canaried release, 99.98% availability target (about 26 minutes of downtime a quarter).

- Starter projects, mentoring and a training roadmap. A checklist of about two dozen things to practise before on-call, including: administering production jobs, reading debugging information, draining traffic from a cluster, rolling back a bad push, blocking or rate-limiting unwanted traffic, bringing up extra serving capacity, using monitoring, and explaining the architecture and dependencies.
- Deep dives; "explore a service from first principles"; be open about knowledge limits. Cross-team calls, weekly production meetings, reading daily handoffs and postmortems, DR testing scenarios written by the sister team, Wheel of Misfortune with rotating leaders and recorded sessions.
- Written on-call guidelines: read the previous shift's handoff first; minimise user impact first, then fix fully; send a handoff at the end; when to escalate; how to write postmortems.
- Ramp: month 2 shadow the outgoing team, month 3 become primary with the old team as backup. Psychological safety: escalating does not make you incompetent. For later single joiners: architecture diagrams and the checklist turned into semi-independent exercises.

## 11. Playbooks

A playbook is high-level instructions for responding to an alert: severity and impact, debugging suggestions, mitigations. Usually one entry per alert; it reduces stress, MTTR and human error. Debate: general entries per alert family (change slowly, plus an architecture diagram) versus step-by-step entries (cut variability and MTTR). Decide with the team the minimal structured details every entry must have, notice accumulation beyond that, and convert hard-won knowledge into automation or consoles. If a playbook is a deterministic list of commands run every time the alert fires, automate it (`toil-and-safe-automation.md`).

## 12. Team dynamics scenarios

"Survive the week": 30 engineers (25 feature developers, 5 ops) on one site, high pager volume, slow follow-up because developers prioritise features, a developer insisting on paging by error rate rather than error ratio (noisy, unactionable), and duplicate pages ignored. Proposal 1: empower the ops engineers as SREs who own site operations, share a reliability roadmap, drive issues to resolution and maintain monitoring rules, with developers as collaborators; action items assigned to the five who work with subject experts; they negotiate alerting changes and send code reviews to experts. A rename alone does not fix structural problems. Proposal 2: improve relationships (offsites, seating the whole rotation together), since people who know each other fix bugs, finish action items and avoid paging colleagues carelessly (a forgotten monitor on a switched-off nightly job paged someone at 3 a.m.).

## 13. Checklist for designing or reviewing an on-call setup (synthesis in the notes)

1. Every paging alert: symptom- or SLO-based, immediately actionable, linked playbook entry, tested about a week in non-paging mode, pager-budget impact estimated.
2. Budget: at most 2 incidents per 12-hour shift; measured by a 21-day trailing average; a warning-threshold ticket alert.
3. Each page leads to a placeholder bug linked to the alert; root cause or added instrumentation; a systemic fix if break-even is reachable.
4. Staffing: the minimums are 5 per site multisite and 8 single-site; the notes' checklist aims for the with-spare figures, 6 per site and 9 single-site; shifts at most 12 hours; automated scheduler that never edits published schedules; swap policy with peer review.
5. Onboarding: practice checklist, shadowing, Wheel of Misfortune, handoff guidelines.
6. Response-time tiers set deliberately per alert.

## 14. Verification

- Export the alert list and check each has a runbook link, an owner, a tier and a record of its trigger rate in test mode.
- Compute pages per shift and incidents per shift over 21 days; compare with the budget of 2 per 12 hours. Show the trend.
- Count alerts with no linked bug and pages with unknown cause.
- Check the schedule: shift lengths, minimum headcount, spare, no edits to published shifts, swap policy exists.
- Confirm every paging alert really needs a human within its tier's response time; if the system could repair itself, automate it, and if it can wait for work hours, make it a ticket.
