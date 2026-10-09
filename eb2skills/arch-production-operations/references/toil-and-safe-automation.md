# Toil and safe automation

Sources: SRE Workbook ch. 6 (Eliminating Toil), ch. 10 (the destructive-automation case), ch. 15 (config-induced toil), ch. 8 (data on repeated pages).

## Contents

1. Definition and traits
2. Measuring toil
3. Taxonomy of toil sources
4. Strategies (decision options)
5. Guardrails every automation needs
6. Case: datacenter network repair automation
7. Case: retiring filer-backed home directories
8. Legacy systems: four paths
9. Procedure for deciding whether and how to automate
10. Verification checklist
11. Warning signs

## 1. Definition and traits

Toil is the repetitive, predictable, constant stream of tasks related to maintaining a service. Google caps operational work at 50% of SRE time; even if 50% is wrong for you, an upper bound plus quantification is the first step. Traits form a spectrum, and a source of toil need not have all of them:

| Trait | Note |
|---|---|
| Manual | A person logs in and deletes log files at 95% disk |
| Repetitive | It will recur |
| Automatable | A runbook of the form "log in, run command, restart Y if..." is pseudocode. Better: automate detection and remediation; better still, fix the software so it cannot break this way. Automatability is the most subjective trait and changes as the team gets comfortable letting the robots work |
| Nontactical or reactive | Floods of disk-full or server-down alerts mask severe alerts |
| No enduring value | Closing the ticket does not prevent recurrence |
| Grows at least as fast as its source | Hardware repair scales with the fleet; ancillary config changes need not |

Also weigh morale: boring work, stagnation, burnout turnover.

Principle: reward root-cause fixes over workarounds that mask problems. Example: a script to truncate logs on 20,000 broken machines would have hidden a root cause (a patched network driver spamming logs). The better path was to find the offending kernel line, file a bug against the kernel test suite, and justify it with cost (about $1 per hour per server times about 1,000 broken machines is $1,000 per hour).

## 2. Measuring toil

Intuition is not repeatable, objective or transferable, and reduction efforts span quarters or years, so use an objective measure to rank candidates and justify cost.

1. Identify toil with the people who do the work and stakeholders.
2. Pick a unit: minutes or hours (include context-switch cost), or for fragmented work a consistent bucket such as an applied patch, a completed ticket, a manual production change, a predictable email exchange, a hardware operation.
3. Track continuously before, during and after the reduction effort; automate the tracking so measuring is not itself toil. Google teams track toil as bugs and rank by cost to fix versus time saved.

Cost-benefit before automating: time saved should at least match time to build plus maintain. "Unprofitable" projects can still pay off indirectly: more project time (which reduces toil further), morale and attrition, fewer context switches, process clarity, skill growth, shorter training, fewer human-error outages, better security, faster user response. Break-even example from on-call data (ch. 8): a project of 3 working weeks is 120 hours; a page costs about 4 hours, so break-even is after 30 pages.

## 3. Taxonomy of toil sources

1. Business processes (most common): ticket-driven work such as onboarding users, configuring or securing machines, software updates, adding or removing servers. Insidious because it "works" and is spread evenly, so nobody screams. Even without automation, simplify the process; it is easier to automate later.
2. Production interrupts: time-sensitive janitorial tasks (free disk, restart leaking apps, replace drives, kick unresponsive systems, manual capacity tweaks).
3. Release shepherding: release requests, rollbacks, emergency patches, repetitive config changes even with automated pipelines.
4. Migrations: data stores, cloud vendors, SCM, libraries, tooling; done by hand "because it is one-time" yet repetitive (adapting backup tooling for a new database is refactoring to swap an interface).
5. Cost engineering and capacity planning: reserved instances, contracts, launch and holiday preparation, checking upstream and downstream limits, footprint choices.
6. Troubleshooting for opaque architectures: distributed microservices without tracing or dashboards. Dependency arithmetic: each critical dependency of availability P lowers availability by a factor P; a 99.99% service with nine critical 99.99% dependencies is about 0.9999^10, or roughly 99.9% (three nines).
7. Configuration toil (ch. 15): replication toil and complexity toil; see `configuration-design.md`.

## 4. Strategies (decision options)

- Identify and measure; rank by cost to fix and time saved; treat toil reduction as its own project if overloaded.
- Engineer toil out of the system (preferred): eliminate at the source; work with product developers for operationally friendly software.
- Reject the toil first: compare the cost of responding with the cost of not responding, or deliberately delay so tasks accumulate for batch processing, reveal patterns and reduce interrupts.
- Use SLOs to reduce toil: skip operational tasks that do not threaten the error budget; an SLO on overall service health scales better than per-device handling.
- Start with human-backed interfaces ("engineer behind the curtain"): accept structured requests via a defined API or form while humans still do some of the work. This reduces free-form requests, tells customers what you need, and avoids a big-bang automation before the domain is mapped. A ticket form with a fallback queue works as a quick GUI.
- Provide self-service: web form, script, API or docs for PRs to config, degrading gracefully to a ticket for special cases or failure. Even 80-90% self-service is a huge reduction.
- Get management and colleague support: short-term capacity dips; use objective toil metrics to push back on new demands.
- Promote toil reduction as a feature, coupling it with security, scalability or reliability benefits customers value.
- Start small and improve; automate a few high-priority items and reinvest the saved time. Success metric example: MTTR.
- Increase uniformity ("pets versus cattle"): treat links, switches, machines, racks and clusters as interchangeable with the same interface (drain, undrain, shut down). High initial cost, lower maintenance and disaster-recovery cost.
- Automate toil response without transcribing the human workflow literally: break it into composable, reusable components; do not erase human understanding; use the automation effort to re-evaluate and simplify the workflow.
- Use open-source or third-party tools, especially for one-off migrations.
- Use feedback: surveys and UX studies for less-expert users; measure automation by latency, error rate, rework rate and human time saved across all groups; compare before and after.

## 5. Guardrails every automation needs

Assess risk inside the automation (ch. 6), then apply the destructive-automation lessons from the postmortem case (ch. 10; see `postmortems.md`).

1. Validate input, even from upstream systems. An API that treated an empty filter as "no filter" sent every machine in a fleet to be wiped; empty must mean "act on nothing".
2. Safeguards equivalent to the indirect alerts a human would see: timeouts, metric checks, the number of current outages. Monitoring must be machine-consumable. Even naive reads can spike device load. Safety checks can come to dominate the workload as automation scales.
3. Defence in depth for risk assessment: a pre-action check plus a second check with upper limits on affected links or devices. Exceeding the limit opens a tracking bug. Tune over time; it also detects abnormal repair rates caused by outages or bugs.
4. Blast-radius cap and rate limit: a destructive operation refuses to touch more than N nodes, never spans namespace or class boundaries, and proceeds at a limited rate.
5. Idempotent or fail-safe on repeat: re-running a half-failed workflow must not widen the effect.
6. Cross-check against planned work, and ask an approval service for destructive operations.
7. A big red button that disables the automation, and an alert when more than X% of the fleet is removed.
8. Default to a human operator on an unsafe condition.
9. A failure budget for anti-toil automation (like an error budget) and manager support.
10. Strike or escalation policy tracked by software: first failure gets a cheap reset (reboot, reinstall), a second within a window escalates to replacement or a human.
11. Verification before restoring traffic (bit-error-rate test, cable audit in the network case).
12. Test the automation with novice users. A technician once started concurrent drains on every waiting line card, causing congestion and loss.

## 6. Case: datacenter network repair automation

Context: Clos fabrics (Saturn, then Jupiter, more than 6x larger, capacity doubling about every 12 months) multiplied switches and failures; each failure was less impactful but volume overwhelmed staff. The manual workflow: check safe to drain, drain, reboot or replace line card, undrain; repetition caused human error.

- Design 1 (Saturn): reuse existing alerting and ticketing; automated risk assessment before drain; strike policy (first failure reboot and reinstall, second replace card). A technician "prep" button drained for them.
- Design 2 (Jupiter): rewrite with more redundancy and bolder automation. Auto-drain the whole switch, automate install and configure, automate verification (bit-error-rate test and cable audit reused from fabric deployment tooling) before undrain, and recover without a technician unless unavoidable. If a second failure occurs within six months request new hardware, else power-cycle (two distinct methods), verify, install, undrain; failed sanity checks go to a technician with instructions.

Lessons (a-i):
- (a) The UI must not add overhead (the prep button lacked progress feedback and desynced from real state). Design so the switch is ready before the technician arrives.
- (b) Do not rely on human expertise.
- (c) Build reusable components, avoid monoliths.
- (d) Do not overthink: about 3 years were spent collecting data on 650+ memory-error problems to diagnose hardware versus software; a simple drain, reboot, reinstall, replace-if-recurs policy plus one quarter of data showed most errors transient.
- (e) Imperfect automation can be good enough (BERT skipped for management links carrying no customer traffic).
- (f) Automation is not fire-and-forget (Saturn outlived its end of life); prefer policy-based automation that separates intent from engine.
- (g) Defence in depth for risk assessment (section 5.3).
- (h) Get a failure budget and manager support.
- (i) Think holistically: simplify the workflow first, test with the people doing the work, and make sure automation creates no new toil (spurious tickets) or problems for other teams.

## 7. Case: retiring filer-backed home directories

Replaced NFS/CIFS home directories and team shares with version control, Drive-style storage and object storage. Data gathering first (a BigQuery tool analysed who accessed what: 2.5B files, 300 TB, 60,000 POSIX users, 400 volumes, 124 appliances, 60 sites), then breaking use cases into pieces mapped to specialised alternatives, phased rollout starting with the least-affected users, a self-service portal handling leave, departure and holds, and automated archiving with care to avoid false positives in notifications. Took about 2 years to feature-complete; home directories went from 65,000 to about 50.

Lessons: challenge assumptions and retire expensive business processes, adding justification beyond toil (a security model carried the case); build self-service, but a custom portal was expensive and config-in-VCS with pull requests is cheaper; human-backed interfaces; melt snowflakes (change reality to fit the code: modify or delete nonconforming shares); organisational nudges (escalation for new share requests, recognition for retiring shares, cookbooks for self-onboarding); moving up the stack from a general filesystem to application-specific solutions trades flexibility for scalability, latency tolerance and security.

## 8. Legacy systems: four paths

1. Avoidance: accept the technical debt and drift toward sysadmin work.
2. Encapsulation or augmentation: a shell of abstracted APIs, automation, config management, monitoring, tests. "Refinancing high-interest debt into low-interest debt"; a stopgap.
3. Replacement or incremental refactoring behind a common abstracting interface; migrate with canary or blue-green; build production-sized datasets of historical inputs and outputs because the spec is the historical usage.
4. Retirement or custodial ownership: stragglers take custodial ownership of remnants.

## 9. Procedure: decide whether and how to automate

1. Name the task, its unit of measure and current weekly cost (section 2). If you cannot measure it, start by measuring.
2. Ask whether to reject, delay or batch it (section 4); then whether the source can be engineered away.
3. If it must stay, decide where on the ladder it sits: human-backed interface, self-service, partial automation, full automation. Pick the cheapest rung that removes most of the cost.
4. Compare build plus maintain cost with time saved, including indirect benefits listed in section 2.
5. Design the automation as small composable components with the guardrails in section 5. Write the failure budget and the escalation path before the first run.
6. Roll out on a small slice first (see `canarying-and-rollouts.md`), watch the strike and limit counters, and track the toil measure against the baseline.
7. Review at a fixed interval: has the process, hardware or policy underneath it changed?

## 10. Verification checklist

- Toil measured in a consistent unit and tracked before and after; ROI estimated.
- Each automation has: a pre-action safety check, a secondary limit-based guard, a human fallback, a strike or escalation policy, verification before restoring traffic, a kill switch, and a test run by a novice user.
- Empty-input, repeat-run, and over-limit cases are covered by tests (these are the cases that bit the fleet-wipe incident).
- Percentage of requests handled by self-service tracked (target in the notes: roughly 80-90%).
- Automation does not open tickets for other teams or mask a root cause.
- An owner and a review date exist.

## 11. Warning signs

Runbooks that read as scripts; ticket queues spread evenly so nobody feels the pain; workaround scripts masking root causes; migrations done by hand because "one-time"; unlimited data collection delaying an obvious action; automation without a failure budget, depth limits or human fallback; UIs requiring operator expertise; automation that opens tickets for others.
