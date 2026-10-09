# Organisational notes (brief reference)

Sources: SRE Workbook ch. 18 (SRE Engagement Model), ch. 19 (Reaching Beyond Your Walls), ch. 20 (SRE Team Lifecycles), ch. 21 (Organizational Change Management). This is a short reference for questions about who does what and how to roll out change among people. Most numbers are Google heuristics.

## Contents

1. Engagement lifecycle and ground rules (ch. 18)
2. Scaling SRE teams (ch. 18, ch. 20)
3. Starting SRE without or with few SREs (ch. 20)
4. Working with customers (ch. 19)
5. Managing organisational change (ch. 21)

## 1. Engagement lifecycle and ground rules (ch. 18)

SRE cannot cover every service, so decide where to focus. Phases and what SRE does:
1. Architecture and design: publish best practices, early consulting, prototypes to validate assumptions (mistakes cost more later).
2. Active development: capacity planning, redundancy, spike and overload handling, balancing, sustainable ops.
3. Limited availability: measure reliability; define SLOs before general availability (product can still withdraw a product that cannot meet target); capacity model; automate turn-ups; share heavier ops with developers.
4. General availability: SRE does most ops, but a developer stays in the rotation to keep perspective.
5. Deprecation: SRE supports two systems; adjust headcount.
6. Abandoned: developers resume operational support; SRE best-effort.
7. Unsupported: shut down; remove references from prod config and docs.

Ground rules agreed between SRE and developers: a hard limit on operational work; an agreed, measured SLO to prioritise engineering for both teams; an agreed quarterly error budget governing release velocity and safety parameters such as spare capacity; developer involvement in daily operations so root causes get fixed. If the error budget is exhausted, both teams prioritise recovery; if well within SLO, spend spare budget on feature velocity.

Engagement hygiene: written goals with a success story and milestones; feedback cadence; plan for disengagement; maturity assessment before and after; yearly roadmaps with quarterly goals (in a stable environment no roadmap signals the team can merge, hand back or dissolve). Hand a service back if it is optimised enough, its importance has faded, or it is near end of life. Warning pattern: split old and new systems under separate owners with a communication gap.

## 2. Scaling SRE teams

- Google keeps the SRE-to-developer ratio under 10%; ratios range from about 1:5 (low-level infrastructure) to about 1:50 (consumer apps on standard-framework microservices), many near 1:10 (ch. 20).
- Organise by technology rather than by developer reporting lines, to avoid churn at reorgs. Shard a team rather than starting a fresh one. Singleton teams are less effective and vulnerable.
- Splitting for complexity: split on architectural lines; avoid orphaned components by designating one team for everything not in the other's charter. Delay splitting on-call rotations by three to six months after the split. Seed new teams with some of the best people. Keep new hires under one third of a new team.
- Geographic splits: six to eight hours apart works well; avoid a "night shift" site by balancing on-call, interesting projects and contact with developers; three shifts not recommended; budget travel; rotate responsibilities that should not be owned by everyone and never lock one to one site for years.
- Prioritise services by financial or reputational impact, not by being unreliable.

## 3. Starting SRE (ch. 20)

Three principles: SRE needs SLOs with consequences; SREs must have time to make tomorrow better than today; SRE teams must be able to regulate their workload. Without SREs you can still adopt: an explicit non-100% SLO, an error budget policy agreed with leadership, and measurement. Placing the first SRE: embed in product, in ops, or horizontal; stick with one coherent model. Avoid renaming Operations to SRE without applying the practices. Maturity checklist for a norming team: SLOs and budgets in place with the error budget policy exercised after significant incidents; sustainable, compensated on-call; toil documented and bounded; postmortem culture; regular exercises; developer team stays in rotation; quarterly stakeholder reports. Mature teams can reduce the SLO, hand back or stop feature work when overloaded.

## 4. Working with customers (ch. 19)

Premises: reliability is the most important feature; users, not your monitoring, decide reliability; on a platform, reliability is a partnership (a 99.999% platform with a 99% customer system gives at best 0.99 x 0.99999 = 98.99901%); everything important becomes a platform; customer struggle slows you down.

Five steps with a customer: (1) agree SLOs and SLIs as the shared language, because without a stated SLO the customer invents one and tells you only when you miss it; (2) audit monitoring and build shared dashboards (up to half of what customers alert on may not affect their SLOs); (3) measure for one to two months and renegotiate (apps believed to be five nines typically measure 99.5% to 99.9%); (4) design review and risk analysis ranked by error-budget consumption; (5) practise (Wheel of Misfortune, game days, joint postmortems). Choose customers by one principle: revenue coverage, feature coverage or workload coverage. The "up to half" and "99.5-99.9%" figures are anecdotal.

## 5. Managing organisational change (ch. 21)

Models: Lewin (unfreeze, change, freeze), McKinsey 7-S, Kotter's 8 steps, Prosci ADKAR (awareness, desire, knowledge, ability, reinforcement), Bridges and Kübler-Ross for emotional reactions, Deming PDCA (suited to process improvement, not organisational change). No single model is universal; Kotter and ADKAR were the most useful lenses.

- Reliability or scaling crisis driven from the SRE side (Waze message queue): urgency exists; form a small coalition; free time by reducing load first; migrate incrementally with dual-write to both systems and a central traffic switch; migrate low-traffic, high-importance flows first; declare the old system deprecated and mop up stragglers later. Result: 1000x load. Release process cycle: build the tool, show visible wins with volunteer teams, add a dashboard so developers can tie releases to metrics, then set a goal for all teams; later over 95% adoption.
- Tooling consolidation across many teams (ADKAR): centralised small team of 6-10 senior engineers, 100% dedicated; migration cost near zero ("just recompile") with clear benefits; trial with the grumpiest adopters first; adoption plan with champions, beta testers and sponsors; adoption is the first impact measure. Best-effort staffing failed.
- Lessons: incremental change is easier to manage, but keep a master plan; if the current solution cannot support the vision, building new can escape a local maximum (look for anything that does not scale horizontally or grows super-linearly with a core metric).
- Verification (inferred in the notes): track adoption (percent of services or teams on the new path, stragglers, deprecation date); migration reversible and dual-run capable; a central traffic switch; early-win flows identified; each ADKAR stage has an artefact.
