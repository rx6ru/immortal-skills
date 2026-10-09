# Incident response

Sources: SRE Workbook ch. 9 (Incident Response), ch. 8 (alert tiers, mitigation), ch. 10 (what a postmortem consumes), ch. 16 (rollback). Based on the Incident Command System (ICS, 1968, firefighters); the chapter presents Google's IMAG and PagerDuty's process.

## Contents

1. Definitions and principles
2. Roles
3. Priority order during an incident
4. Generic mitigations
5. Declaring an incident
6. Communication
7. Long incidents and handoffs
8. Case lessons
9. Preparation, training and drills
10. Alert tiers and severity (a worked setup)
11. How an agent helps during an incident
12. Verification and review questions

## 1. Definitions and principles

Resolving an incident means mitigating impact or restoring service. Managing an incident means coordinating responders and keeping communication flowing among them and to interested parties. Structure agreed beforehand reduces chaos, so responders think about the problem and not the process.

Principles: keep a clear line of command; designate clearly defined roles; keep a working record of debugging and mitigation as you go; declare incidents early and often. The "3 Cs": coordinate the response, communicate (responders, organisation, outside world), and keep control. When a response goes wrong, one of these is usually the culprit.

## 2. Roles

| Role | Duty |
|---|---|
| Incident Commander (IC) | Usually whoever declares the incident. Commands and coordinates, delegates roles. By default holds every role not yet delegated. May hand IC off and become Ops Lead |
| Operations Lead (OL) | Applies operational tools to mitigate or resolve |
| Communications Lead (CL) | Public face. Periodic updates to responders and stakeholders, manages inquiries |
| Others seen | External Communications Lead (support), scribe (records actions, owners, timestamps), incident manager |

CL and OL report to the IC and can each lead task forces that expand and contract; on a small incident the CL folds back into the IC. Case guidance: IC delegates routine problems to the OL and personally drives the novel cross-team problem. When three or more people work an incident, start a collaborative document listing theories, eliminated causes, error logs and suspect graphs. When discussion becomes too dense for chat, move detailed debugging to the shared document and let chat be the decision hub.

## 3. Priority order during an active incident

1. Assess impact. 2. Mitigate impact. 3. Root-cause analysis. 4. After the incident, fix the cause and write the postmortem. Customers do not care whether you understand the cause.

Caveat from the Google Home case: mitigation stopped impact on three occasions, but recurrence only stopped after the root cause was found. After the first mitigation, postpone further rollout until the root cause is known.

## 4. Generic mitigations

A generic mitigation is a blunt action by first responders that relieves user pain before the root cause is understood: roll back a recent release if the problem correlates with the release cycle; reconfigure the load balancer to avoid a region when errors are localised; drain a cluster; flip a feature flag; shift traffic. It may cause other disruption but stops the bleeding. In the GKE case a rollback of all images to known-good would have mitigated around 10:00 instead of 12:11, roughly 2 hours earlier, once the general location of the cause (not the cause itself) was identified: "you only need to know the location of the root cause".

Build mitigation tooling before incidents and mine postmortems for it. Check each service for: a rehearsed rollback, a drain, a failover, a feature flag, a traffic shift. Caution from the drain example: draining a cluster pushed errors to other cells, which was itself evidence of a quota problem, so watch where the load goes (see `managing-load.md`).

## 5. Declaring an incident

- Declare early. Managed incidents resolve faster. Early declaration prevents miscommunication between client and server developers, speeds root-causing, and brings in other teams and external communications sooner.
- Derive explicit incident criteria from past outages and known high-risk areas so "is this an incident?" is not ambiguous. In the PagerDuty case the effective declaration trigger looked like spread across teams (inferred in the notes).
- Warning signs of a missing declaration (Google Home): priority not escalated despite external reports; the bug tracker used as a communications channel; a rollout continuing with an unexplained anomaly; quota raises used as a repeated band-aid.
- In the GKE case no formal IC structure existed until 2 hours after the first page, and first responders ran uncoordinated investigations.
- Do not rely on heroic weekend work. Roll out during business hours or have a paid out-of-hours rotation.

## 6. Communication

- Pick and practise a communication channel in advance, one the team already knows; centralise it (war room: physical, IRC, chat, call). All responders in one place in real time.
- Keep the audience informed. Unless you announce an incident is being handled, people assume nothing is happening; if you forget to call it off, they assume it is ongoing. Send updates on a regular cadence.
- Have ready: a contact list; mailing lists or pager groups for "all hands on deck"; a pre-agreed process for drafting, reviewing and approving public posts and press (Google involves PR); two or three ready-to-use templates for public notices that on-call knows how to send.
- A good Comms Lead reports accurately to each audience (Belgium case): company leaders (extent and assurance), internal teams with storage concerns (when storage is back), external customers proactively, specific customers with tickets (workarounds and timelines).
- Record calls in major incidents so the timeline can be recreated (PagerDuty). Use a chat channel as the scribe's ledger and a static conference line for decisions.

## 7. Long incidents and handoffs

- Hand the IC role to the most experienced available person when the incident outgrows the first responder (GKE case: handed over early, before the normal shift handover).
- Rotate on-calls and the IC every few hours on long incidents (PagerDuty rotated every 4 hours over a 10+ hour incident, for rest and fresh ideas). When runbooks fail, spend time methodically trying new recovery options.
- Validate recovery with the on-call of every affected service before closing the call and channel. Assign the postmortem to the owning service's on-call before closing.

## 8. Case lessons

- Google Home (client bug fetched files 50x more than expected, exceeding server quota): no incident declared for days; rollout to 100% on a weekend; quota repeatedly raised. Lessons: avoid weekend rollouts, mitigate then root-cause before resuming, declare early, centralise communication.
- GKE CreateCluster outage in Europe (6 h 40 m; 41 users in chat; 7 task forces; 28 postmortem actions): a corrupt container image in a regional cache; first responders chased a decoy (DockerHub); no generic mitigation. Went well: documented escalation paths, quick customer-impact verification, prepared incident system. Better: formal IC sooner, logging, generic mitigations.
- Belgium datacenter lightning (four strikes in two minutes; disk-tray power supplies did not transfer on strikes 3 and 4): the persistent-disk SRE on-call, with the best visibility of customer impact, became IC and declared a major incident immediately. One objective (migrating VMs before reboot) had no procedure, so the IC assigned a dedicated ops member, realised new tools were needed and put more engineers under the ops team to build them. Data loss was limited to pending writes on powered-off machines.
- PagerDuty NTP clock drift (10+ hours, minimal customer impact): declaration took about 2 hours from the first alert; the process still worked: assemble every on-call whose service depends on NTP, rotate people every 4 hours, validate each service's recovery.

## 9. Preparation, training and drills

- Training: responders need a common pattern, language and expectations. Full ICS may be more than needed; pick parts: tell on-calls they can delegate and escalate, encourage mitigation first, define IC, Comms Lead and Ops Lead. Use a deck, hands-on exercises and past-incident reviews.
- Drills: company-wide disaster recovery testing (Google DiRT); Wheel of Misfortune role-play of specific incidents, ideally with the original IC attending; treating minor real problems as major to practise at low stakes; PagerDuty's Failure Friday (weekly manual failure injection, with a trainee IC acting as a real IC); time-bound simulation games for stress and communication practice.
- Everyone who may be swept in (SRE, developers, support, marketing) practises. Build scenarios from postmortems, use real tools, consider breaking a test environment for real troubleshooting. Run periodically and follow each with a report: what went well, what did not, what to improve. Closing gaps is the main value. Get leadership support for practice time.
- Procedures matter more as the circle of collaborators grows; ICS is simple to understand but hard to execute under panic, and practice builds muscle memory.

## 10. Alert tiers and severity (an example setup, Evernote, SRE Workbook ch. 8)

- P1: deal with immediately; immediately actionable; pages on-call; SLO-impacting. P2: next business day; generally not customer-facing or limited scope; email plus event channel. P3: informational; dashboards or passive email, includes capacity-planning information. Every P1 or P2 gets an incident ticket (triage, remediation tracking, SLO impact, occurrence count, postmortem link).
- On a page: assess user impact, triage into Sev 1-3. Sev 1 has a finite criteria list for the escalation decision; then the incident manager is paged, a scribe and a communications lead are chosen, channels opened, and an automatic postmortem shared company-wide. Sev 2 and 3: on-call handles the lifecycle and writes an abbreviated postmortem.
- Response-time tiers set deliberately per alert (SRE Workbook Table 8-1): a revenue-impacting network outage 5 minutes (the engineer must be within reach of a charged, authenticated laptop with network), stuck order batch processing 30 minutes, failing backups for a pre-launch service a ticket in work hours. See `on-call.md`.

## 11. How an agent helps during an incident

Adaptation, not from the book. If an agent is asked to assist in a live incident: restate impact in one line with numbers; propose the cheapest generic mitigation (rollback, flag, drain, traffic shift) before any code investigation; keep a timestamped log of theories tested and eliminated for the scribe; ask which role the user holds before issuing commands in a shared channel; do not propose a risky change without a rollback; remind about a postmortem owner at the end. In code review, check that mitigations exist (kill switches, flags, drain commands) and are documented.

## 12. Verification and review questions

- Was an incident declared at the first sign of multi-team involvement or sustained user impact? Was an IC named in the first minutes, and OL/CL assigned when about three or more responders joined?
- One communications channel, one shared working document, a scribe, updates on a fixed cadence?
- A generic mitigation ready and rehearsed for this service?
- Long incident: responders and IC rotated, IC handed to the most experienced person?
- Postmortem assigned before closure?
- Are incident criteria written down, contact lists and templates current, drills scheduled and followed by a report?
