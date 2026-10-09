# Operational overload: measuring it and recovering

Sources: SRE Workbook ch. 17 (Identifying and Recovering from Overload), the interlude defining operational work (after ch. 7), ch. 8. This is about a team drowning in pages, tickets and interrupts, not about servers under load (see `managing-load.md`).

## Contents

1. Definitions
2. How load becomes overload
3. Quantify before you act
4. Case 1: half the team leaves
5. Case 2: perceived overload
6. Symptoms
7. Strategies to reduce overload
8. Decision aid
9. Verification
10. Caveats

## 1. Definitions

- Operational load: ongoing maintenance that keeps services running, of three types: pages, tickets and ongoing operational responsibilities. Pages and urgent tickets are interrupts that preempt project work.
- Operational overload: the team cannot progress key priorities because urgent issues keep preempting project work; it also raises the error rate.
- Perceived overload: the subjective feeling of too much work, usually after several organisational or work changes in a short period with little chance to talk to leadership. It has the same effects as real overload.
- Google caps operational work at 50% of an engineer's time; the overload threshold varies by team, and a team must be confident that over the long term it can finish the engineering projects that reduce load.
- Work buckets (interlude): operational work (on-call, customer requests or tickets, incident response, postmortems) and project work (strategic engineering that makes the system more efficient, scalable or reliable or reduces toil; temporary, with a clear deliverable), plus overhead (meetings, training, email). There should be a feedback loop from sources of operational load to projects that remove them. Google rule: at least 50% project work; about one-third operational and two-thirds project is "about right". Periodic reviews with a rubric track the balance. Operational underload is also a risk (see `on-call.md`).

## 2. How load becomes overload

- Triggers: long illness, people leaving or transferring, new organisation-wide programs, system changes that make technical work harder.
- Unpredictability: a "disk full" ticket may hide a deep GC problem; a pager storm of 20+ pages may be bad monitoring. A long-looking queue feels unmanageable even if each item is quick.
- Interrupts plus external stressors (fear of disappointing teammates, job insecurity, conflict, illness, poor sleep) turn even small workload into perceived overload. If nothing is prioritised, every task seems equally urgent.

## 3. Quantify before you act

Do not assume the workload must change first. Count tickets and pages over time (has it changed?). Take a one-time snapshot by asking every member to list all their work. Then examine psychological stress factors (organisational changes, reprioritisation). Reprioritising reduces perceived overload; real overload needs load reduction.

## 4. Case 1: half the team leaves (storage SRE)

Two-thirds of the team, including the manager and a senior engineer, transferred; remaining expertise was siloed; new hires and interns would help only after a costly ramp-up. Psychological barriers to shedding work: the sunk-cost fallacy and the feeling that adding automation to an overwhelming pile is impossible.

Steps taken:
1. Gather the team in a room, list every responsibility (backlog, operational work, tickets), and triage every item to redefine real priorities and minimise, hand off or eliminate the low-priority ones.
2. Identify low-effort automation that would cut load notably; document common problems to enable self-service.
3. Close as many backlog tickets as reasonable: most were obsolete, redundant or not urgent; some were non-actionable monitoring artefacts (fix the monitoring instead); for non-critical work in progress, document progress to preserve context and set it aside.
4. When in doubt, drop but mark for second-phase triage; later almost none were worth resuming.

Result: two days (one intensive triage, one documenting processes and building automation) cleared months of interrupts. Lasting practices: triage interrupts every two weeks; the tech lead periodically checks the queue for overload risk; at most 10 open tickets per team member (the team's own number). If exceeded the lead can remind the team to close stale tickets, sync with the overloaded person and offload tickets, prompt them to work the queue, organise a one-day team ticket fix-it, or assign work to fix ticket sources.

## 5. Case 2: perceived overload (Zürich)

A team split between a healthy site and an overloaded one. Simultaneous triggers: onboarding noisier, less-integrated services; two people left (the tech lead manager and another). Compounding problems: untuned monitoring for new services led to a gradual, unnoticed rise in pages per shift; SREs felt helpless with unfamiliar services; handing a service back had never been done so was not considered; the rotation shrank to 5; new ticket alerts converted previously ignored email into tickets (hidden technical debt); a new ticket SLO (handle tickets within 3 days) forced on-callers into follow-up right after shifts (at least one extra day per shift), denying rest and creating worse side effects than the backlog it targeted; a new manager shared across three teams did not feel the stress.

Chain: months of ticket overload, grumpiness, sickness, others pick up work, trust erodes, psychological safety falls, collaboration stops, and perceived overload became objective overload. Page count had barely changed from earlier years.

Response: a dedicated, respected manager with a participatory style; team-building based on Google's Project Aristotle findings. Goals by horizon:
- Short term (within a month): relieve stress and restore safety. Round tables to vent and brainstorm; a better load metric (time an on-caller needs to resolve tickets after the shift, with tickets auto-assigned to on-callers, instead of page count); audit and remove spamming alerts (keep only user-facing problem alerts); silence alerts generously with rules (silenced until fixed; time-boxed, typically a day, up to a week; alerts not fixable within minutes get a tracking ticket); a dedicated single-team manager; rebalance with experienced SREs; social events.
- Mid term (three months): limit operational work to on-call time; return one service to its dev team; cross-train; remote-site SREs cover some shifts; backfill open roles; tackle each alert as silences expire (weekly production meeting reviews repetitive or no-action pages); listening events.
- Long term: align service SLOs with backend SLOs; make services uniform (lower cognitive load, reusable automation); review old services against current production standards; quarterly planning.

Effects: quieter shifts within months, collaborative incident handling, and an anonymous survey after about a year reporting the team effective and safe. Lesson: perceived overload is overload; tend to stress first because overload causes stress that prevents tackling overload.

## 6. Symptoms

Decreased morale (rants; run surveys and active-listening sessions); long hours or working while sick (leaders model contractual hours and staying home sick); more frequent illness; an unhealthy task queue (review size, owners, what can be delayed or dropped; missed deadlines or no time for the review means interrupts accrue faster than handled); imbalanced metrics (long time to close a single issue, high share of time on toil, many days to close on-call issues). The team chooses measures together; managers do not impose a metric without understanding each person's work habits.

## 7. Strategies to reduce overload

- More control reduces perceived overload; resist micro-management and involve the team in prioritisation.
- Identify psychosocial stressors per person and team, sorted into controllable (backlog size, silencing pages) and not (illness).
- Tell partner developer teams you are overloaded; they may help or take over projects.
- Once safety exists, give individual responsibility: point people or technical leads per technology; transparent, where possible democratic decisions.
- Prioritise and triage within one quarter; schedule interrupt-free time for hard tasks (automation, root causes of interrupts); drop work if necessary (return a service to dev).
- Protect yourself later: establish workload metrics and review whether they measure the right things; keep a lightweight triage process or long-term SLO alignment; while overloaded prioritise projects that pay down repetitive toil even more than usual; everyone shares responsibility for noticing early warning signs.

## 8. Decision aid (synthesis in the notes)

1. Measure: pages, tickets, open tickets per person, post-shift ticket time, toil share, days to close; a one-time task-list snapshot; a morale survey.
2. If the numbers are unchanged but the team feels overloaded, treat as perceived overload: listen, reprioritise, restore control and safety.
3. If numbers are up, run a room-wide triage: list everything; close, obsolete, delegate, self-serve or automate; mark uncertain drops for second-phase triage; cap tickets per person.
4. Silence noisy alerts with time boxes; retune on expiry.
5. Offload (hand a service back), borrow on-call relief, backfill.
6. Install early-warning triggers: ticket cap, biweekly triage, quarterly planning.

## 9. Verification

- A baseline of pages, tickets and open tickets per person exists and is reviewed on a schedule.
- Every silence has an expiry and a tracking ticket.
- A triage cadence and ticket cap are recorded and the lead checks them.
- A rule exists for what happens when load exceeds the threshold (hand back, reduce scope, backfill).
- No new ticket SLO or metric is introduced without estimating the follow-up time it creates for on-callers.

## 10. Caveats

The ticket cap of 10 and the 3-day ticket SLO are team-specific numbers, and the book shows the 3-day SLO backfiring. The chapter is qualitative; its psychology references (job demand and control, Project Aristotle) support the themes of control and psychological safety.
