# Blameless postmortems: template, review checklist, culture

Sources: SRE Workbook ch. 10 (Postmortem Culture), ch. 8 (follow-up rigor), ch. 9, App. C. A truly blameless postmortem culture makes systems more reliable; introducing it is a cultural change as much as a technical one, so start with a basic procedure and tune.

## Contents

1. The incident behind the examples (a code-review lesson)
2. The bad postmortem: flaws, why they hurt, fixes
3. The good postmortem: structure and content
4. Action items
5. Review checklist (paste-ready)
6. Blameless language
7. Incentives, sharing and culture-failure patterns
8. Tools, templates and trend analysis
9. Postmortem template skeleton
10. Verification

## 1. The incident behind the examples

Satellites are proxy and cache racks in colocation sites. Decommission overwrites all drives via an irreversible disk-erase. A rack decommission partly failed after disk-erase, and engineers re-ran the workflow. On the second run the "get machines" call returned an empty list (already decommissioned), and an API bug treated an empty filter as "no filter" rather than "act on no machines". All satellite machines worldwide went to disk-erase within minutes. Users were routed to core datacenters with slightly higher latency; good capacity planning meant few noticed during about two days to reinstall. Three years later a similar incident had a far smaller blast radius and rate, thanks to the original action items.

Patterns to check in code review: an empty list or filter treated as match-all; "run once" workflow semantics that do not cover new workflow instances; a destructive action with no rate limit, no cross-check and no blast-radius cap. See also `toil-and-safe-automation.md` section 5.

## 2. The bad postmortem: flaws and fixes

Features of the bad document: four owners; shared only with the team; published four months after the incident; the executive summary blames a named person; only the duration quantified; background and glossary blank; recovery blank; shallow root cause ("careless ignorance"); "went well" is "alerting caught it"; "lucky" is "I can't believe we survived this one"; action items vague, equal priority, mostly unowned and untracked.

| Flaw | Why it hurts | Fix |
|---|---|---|
| Missing context (jargon, blank background and glossary) | The audience extends beyond the team | Background and Glossary sections, links to longer docs |
| Key details omitted (only duration given) | A reader must learn something new. "If you don't know how to measure it, you can't know it's fixed" | Quantify size and impact; even a well-informed estimate beats none. Dig root cause and trigger to low-level detail. Say what happened, how it was mitigated, how users were affected |
| Action items lack key characteristics | Mostly mitigative, no preventive item; "train humans not to run unsafe commands" is the one preventive item (changing humans is less reliable than changing systems); all same priority; vague verbs ("improve") with no success criterion; one tracking bug only | See section 4 |
| Finger-pointing (named individuals in root cause, went-poorly and action items) | Risk aversion, fear of public shaming, cover-up of facts critical to preventing recurrence | Describe what, not who; actions improve the system, not people |
| Animated or subjective language ("careless ignorance", "ridiculous", exclamation marks) | Drama distracts and erodes psychological safety | Factual, multiple perspectives, respectful; verifiable data to justify severity |
| Missing ownership (four owners, unowned items) | Nobody completes it | One owner (single point of contact for the postmortem, follow-up and completion) plus collaborators; every action item has an owner |
| Limited audience | The value of a postmortem is proportional to the learning it creates; honest postmortems restore shaken trust | Default to whole-company distribution, even customers; mature cultures add machine-readable tags for analytics |
| Delayed publication (4 months; the incident recurred meanwhile) | Details are forgotten; people waiting for an explanation fill the gap with imagination | Publish within about a week |

The Ben Treynor Sloss rule: every postmortem after a user-affecting outage must have at least one P0 or P1 bug, exceptions personally reviewed. "A postmortem without subsequent action is indistinguishable from no postmortem."

## 3. The good postmortem: structure and content

Header: title; owner (postmortem owners plus named service-owner contacts); shared with (all engineering); status; incident date with exact start and end times and timezone; published date (4 days after the incident in the example).

Sections in order:
1. Executive summary: impact and root cause in two or three lines, no names.
2. Problem summary table: duration (main outage plus residual until closed), products affected, percentage of product affected, user impact (queries dropped over 40 minutes, average QPS, percent of global traffic; latency increase for about 2 days), revenue impact (unknown, estimates with wide error bars flagged), detection (the black-box alert), resolution (moved all frontend traffic to core at the cost of latency).
3. Background (optional; pointer to the glossary).
4. Impact: user impact (with the caveat that monitoring understated the crater because monitoring stopped for satellites still serving; an appendix explains the estimate), revenue impact, team impact (about 48 hours all-hands; downstream cache hit rate drops).
5. Link to the incident document.
6. Root causes and trigger, kept separate. Trigger: manual re-execution of a decommission workflow. Root cause: a longstanding input-validation bug; the release call was not idempotent because an empty list from step 2 was read in step 3 as "no hostname constraint"; hidden for a long time because the step was marked "run once", which does not apply across separate workflow instances.
7. Timeline and recovery efforts (link to the timeline log; raw logs linked, not pasted).
8. Lessons learned: went well, went poorly (split into outage and recovery), where we got lucky.
9. Action items grouped by theme, each in a table with: action item, type, priority, owner, tracking bug.
10. Glossary, appendix Q&A, graphs.

Why it is better (use as a positive checklist): clarity (glossary, themed actions); quantifiable metrics with links to sources; concrete action items (owner, tracking number, priority, measurable end state such as "add alert when more than X% of machines are taken"); blamelessness; depth (multi-team impact, root cause plus trigger, data-driven conclusions); promptness (under a week); conciseness (long logs summarised, raw versions linked).

"Went poorly" items in the example are worth noticing as system observations: no sanity checks in the admin server (all commands should be idempotent or fail-safe on repeat); the metadata database accepted a missing constraint; the workflow did not cross-check planned decommissions; no rate limiting; peering links overloaded by the traffic shift; slow reinstalls; a monitoring config-delta safety check that tripped on re-adding 29% but not on removing 23%, delaying monitoring re-enable by 30 minutes. A time-to-detect gap is called out: machines removed at 16:38 but paging only began at about 17:10.

## 4. Action items

- Types used: investigate, prevent, mitigate, repair, detect. Include at least one prevent item; mitigative-only lists leave the failure possible.
- Each has: a type, a priority, a single owner, a tracking bug in the shared tracker, and a verifiable end state. Ban "improve" and "make better".
- Never make "train humans" the sole preventive action. Plan for a future where everyone is as fallible as today.
- At least one P0 or P1 for any user-affecting outage.
- Vetted and approved by service tech leads.
- Examples from the case (as a pattern library): audit every system that can turn live servers into paperweights (investigate); file bugs for bad-input rejection in all of them (prevent); disallow single operations spanning namespace or class boundaries (mitigate); cap the number of nodes an admin operation may touch (mitigate); ask a safety-check service to approve destructive work (prevent, P0); reject operations missing an expected-present constraint (prevent, P0); a big red button to disable the workflows (mitigate, P0); alert when more than X% of machines are taken away (detect); monitoring safety checks must not allow a push that cannot be rolled back; disaster-recovery tests for restoring after disk-erase.
- From the on-call chapter, the follow-up questions: Can this specific bug recur? Can bugs like it, here and in other systems? What tests would have caught it? What ticket alerts could have prompted action before it paged? What informational alerts could have surfaced it on a console? Have I maximised the impact of the fixes? A three-level fix pattern: point fix (rebalance now), systemic fix (automation that always spreads servers across enough failure domains), and monitoring fix (a ticket alert when diversity falls below expected before it affects service).

## 5. Review checklist (paste-ready)

- [ ] Single owner; collaborators from all involved teams; shared company-wide by default; published within about a week.
- [ ] Executive summary: impact and root cause in 2-3 lines, no names.
- [ ] Quantified impact (duration, share of product or traffic, QPS, revenue estimate with error bars, detection method, resolution), estimates flagged as estimates, data linked.
- [ ] Background and glossary for non-domain readers.
- [ ] Root cause and trigger separated; low-level mechanism explained; why it stayed latent.
- [ ] Timeline and recovery section filled; raw logs linked.
- [ ] Went well, went poorly and where we got lucky: about systems and process, no individuals, no emotive wording.
- [ ] Action items: grouped by theme; each has type, priority, single owner, tracking bug, verifiable end state; at least one prevent item; at least one P0/P1 bug for user-affecting outages; no "improve"; no "train humans" as the sole prevention; tech-lead vetted.
- [ ] Time-to-detect and time-to-mitigate gaps called out.
- [ ] Follow-through: items tracked to closure and rewarded; recurring-incident check done.

## 6. Blameless language

A leading question ("You're the manager; why aren't you making sure everyone finishes the training?") puts people on the defensive. Rewrite as an observation plus systemic options: require training before joining the rotation, remind people escalation is not a sin, and do not rely on training alone because it is forgotten under pressure. Include all incident participants in authoring; single-team authorship misses contributing factors. Gather feedback through a clear review process and communication plan.

## 7. Incentives, sharing and culture-failure patterns

- Reward outcomes: reward action-item closeout and not just writing; reward organisation-wide positive change (peer bonuses, reviews, promotion); hold owners up as leaders; gamify (leaderboards, burndowns; "FixIt" weeks twice a year with small tokens for the most items closed).
- Share openly (do at least one): announce drafts on channels or all-hands; cross-team reviews and postmortem reading clubs; a monthly cross-functional group reviewing the process and template; Wheel of Misfortune re-enacting a past postmortem with the original IC; weekly outage report and periodic "greatest hits".
- Avoiding association ("glad I'm not involved"): review high-visibility postmortems for blameful prose; share good examples and how participants were rewarded.
- Failing to reinforce culture (a VP asks "someone must have known this was a bad idea, why didn't you listen?"): redirect to a systemic question: were there warning signs we could have heeded, and why were they dismissed; investigate the source of misleading information instead of blaming. Individuals act in good faith on the best information.
- Lacking time: poor postmortems with incomplete items make recurrence likelier; "postmortems are letters you write to future team members"; keep a consistent quality bar, prioritise, track completion and review, and give time to implement the plan.
- Repeating incidents: ask whether items take too long to close, whether feature velocity trumps reliability fixes, whether the right items are captured, whether the service is overdue for refactor, whether Band-Aids cover a serious problem. If systemic, bring the collaborators from each similar incident together.

## 8. Tools, templates and trend analysis

- Use a standard template across domains; customise with team metadata (hardware make and model for a datacenter team; OS versions for mobile). Capture data into tables so a repository can parse it.
- Google tooling pushes into the postmortem the IC and roles, timeline and chat logs, affected services, severity and detection mechanism. Items are filed as bugs in a central tracker so closure per postmortem can be monitored. Trend analysis: postmortems per month, mean incident duration, time to detect, time to resolve, blast radius. Tooling cannot write the root-cause analysis; it frees authors for that.
- Keep separate fields for trigger and root-cause category drawn from a fixed vocabulary, so trends can be computed (see `outage-statistics.md`).

## 9. Postmortem template skeleton

```
Title / Owner (1) + collaborators / Shared with / Status / Incident start-end + tz / Published
Executive summary: impact; root cause
Problem summary: duration | products | % affected | user impact | revenue impact (+error bars)
                 | detection | resolution
Background / glossary
Impact: users, revenue, team
Trigger | Root cause (category from fixed list) | why latent
Timeline (link to log)
Went well | Went poorly (outage / recovery) | Where we got lucky
Action items by theme: item | type | priority | owner | tracking bug | end state
Appendix: data, graphs, Q&A
```

## 10. Verification

- Run the checklist in section 5 against the draft and show the user which boxes fail.
- Grep the draft for individual names in cause, went-poorly and action sections; for "improve", "better", "ensure" with no measurable end state; for exclamation marks and intensifiers.
- Confirm every action item has an owner and a tracker link, and that closure is reviewed on a schedule.
- For destructive automation named in the postmortem, check that the fixes cover empty input, repeat runs, rate and blast-radius limits, an approval step, a kill switch and alerting on fleet fraction affected.
