# Setting SLOs, windows and error budgets, and running them

Contents: 1 preconditions; 2 why not 100%; 3 starter SLOs from history (with the arithmetic); 4 windows; 5 stakeholder agreement; 6 error budget use and prioritisation; 7 the decision matrix; 8 reviewing quality (recall, precision, remedies); 9 reports and dashboards; 10 advanced topics; 11 warning signs.

Sources: SRE Workbook ch. 2 (main), ch. 3, ch. 1, ch. 8 (budget arithmetic), app. A; DDIA 2e ch. 2.

## 1. Preconditions: when an error budget approach works at all

All four must hold, otherwise compliance is just another KPI:

1. The SLOs are approved by all stakeholders as appropriate for the product.
2. The people who defend the SLO agree it is achievable under normal circumstances.
3. The organisation commits to using the error budget for decisions, written as an error budget policy (`error-budget-policy-template.md`).
4. There is a process for refining the SLO.

Typical starting states: greenfield; in production with monitoring but an unspoken 100% goal; an SLO below 100% but "without teeth". If an agent is asked to "define SLOs" for a team that has none of the four, deliver the SLO document and the policy together and name the missing owner as an open item.

## 2. Why 100% is the wrong target

- Simultaneous component failure has non-zero probability even with redundancy.
- The user's end-to-end chain (ISP, device) is not 100% anyway; each additional nine costs more and adds less utility.
- Never changing means stagnation, and change is the largest source of outages.
- A 100% SLO leaves only reaction; the notes call it an operations team SLO, not an engineering culture one.
- Once the target is below 100%, an owner empowered to trade velocity against reliability must own it: the CTO in a small organisation, the product owner or manager in a larger one.

## 3. Starter SLOs from history

Method (Workbook ch. 2):

1. Compute the current SLI over the last four weeks at least.
2. Round down to a manageable number: two significant figures for availability; latency to about 50 ms granularity, since users do not perceive smaller differences (depends on the service; a reporting service differs from a real-time game).
3. Back-test: on how many days would the proposed SLO have been missed? Do the misses correlate with known incidents? Should anyone have acted? If there are no logs or metrics, first stand up a low-fidelity external prober (ping or HTTP GET), then collect.
4. Record that the numbers are observational, not user-validated (see `slo-document-template.md`).

Worked numbers (4 weeks of API data): 3,663,253 total requests, 3,557,865 successful (97.123%), p90 = 432 ms, p99 = 891 ms. Proposed SLOs: availability 97%; 90% of requests under 450 ms; 99% under 900 ms. Budgets over four weeks: 97% availability allows 109,897 failures (3% of 3,663,253); 90% under 450 ms allows 366,325 slow requests; 99% under 900 ms allows 36,632.

Current performance is acceptable as a start if you have a good iteration process, but do not let it cap you: customers come to expect what they get. Tighter values can be tracked as aspirational SLOs (section 8).

Budget arithmetic to keep at hand:

| Quantity | Formula | Example |
|---|---|---|
| Error budget | 100% minus SLO | 99.9% gives 0.1% |
| Allowed bad events in a window | budget x events in window | 3,000,000 requests at 99.9% gives 3,000 errors |
| Share of budget used by an incident | bad events in incident / allowed bad events | 1,500 errors burns 50% |
| Allowed full-outage time | (1 - SLO) x window | 99.9% over 30 days is 43.2 minutes |

Other anchors from the notes: 99.99% is about 15 minutes of error budget per quarter (Workbook ch. 8; the arithmetic over 90 days gives 13 minutes), 99.999% about 80 seconds per quarter (78 s by arithmetic). A 99.98% target is about 26 minutes of downtime per quarter.

## 4. Choosing the window

- Rolling windows track user memory: a month-end outage is not forgotten on the 1st. Use an integer number of weeks so the window always contains the same number of weekends; a 30-day window alternates between 4 and 5 weekends and adds spurious variance if weekend traffic differs.
- Calendar windows suit business planning (quarterly headcount) but mid-period you cannot know remaining traffic, so budget forecasts are speculative. Evernote chose a calendar month deliberately to keep service reviews organised.
- Shorter windows give faster decisions and small corrections (which bugs to fix now). Longer windows suit strategic decisions, and need data commensurate with the size of the project being judged (a highly available database versus rollback automation versus a second zone).
- Recommended default: 4-week rolling window, weekly summaries for task prioritisation, quarterly summaries for project planning.
- Do not average over 30-day windows if weekend effect matters (listed warning sign); and keep the policy's window equal to the SLO's window.

For alert rules the window length P enters the arithmetic directly, see `alerting-on-slos.md`; `scripts/burn_rate.py --window 28d` handles any P.

## 5. Getting agreement

Three parties must agree: product managers (the threshold is good enough, and going below it is worth engineering time), product developers (they will take risk-reducing steps when the budget is exhausted), and the production or SRE team (the SLO is defensible without heroics, excess toil or burnout).

Approving the error budget policy is the test of whether the SLO fits:

- Operations says the SLO cannot be defended without toil: argue to relax it.
- Developers or product say the reliability work would slow features unacceptably: argue to relax it. The product manager must understand that a lower SLO also lowers the situations operations responds to.
- Product says the SLO yields a bad experience for many users before the policy triggers: the SLO is not tight enough.
- No agreement: iterate on SLIs and SLOs and decide what is missing: more data, more resources, or a changed SLI or SLO. If the budget is exhausted but stakeholders disagree that enforcement is appropriate, go back to policy approval.

Defending an SLO needs alerting that notices threats before the budget is gone (`alerting-on-slos.md`).

## 6. Using the budget to decide

- Express incidents as a percentage of budget consumed and rank them. Worked examples (97% SLO, budget 109,897 errors per 4 weeks): a bad API release returning 100% NullPointerExceptions for 4 hours is 14,066 errors, 13% of budget; a singly homed state database server failing with a 20-hour restore from backup is about 72,000 errors, 65%.
- Rank reliability projects by expected budget burn per year. Example: one server failure in five years versus two to three bad releases a year that need rollback means bad pushes cost about twice the budget of database failures, so fix the release process first. The comparison needs honest frequency estimates; mark guesses.
- A flawless service that needs little oversight can move to a less hands-on support tier (keep incident response and oversight), freeing engineering time.
- Caveat: the budget treats one 4-hour outage, four 1-hour outages and a constant 0.5% error rate alike, though user unhappiness differs (a long outage may hurt fewer users than constant errors). Thresholds vary per service; if the difference matters, add a second SLO or an outage-duration clause to the policy (adaptation, not from the book).
- Evernote used an SLO calculation to cut release windows for a risky multi-window release from five to two (`case-studies.md`).

## 7. SLO decision matrix

| SLOs | Toil | Customer satisfaction | Action |
|---|---|---|---|
| Met | Low | High | Relax release and deployment processes to raise velocity, or step back from the engagement and spend engineering on services needing more reliability |
| Met | Low | Low | Tighten SLO |
| Met | High | High | If alerting yields false positives reduce sensitivity; otherwise temporarily loosen SLOs (or offload toil) and fix the product or improve automated fault mitigation |
| Met | High | Low | Tighten SLO |
| Missed | Low | High | Loosen SLO |
| Missed | Low | Low | Increase alerting sensitivity |
| Missed | High | High | Loosen SLO |
| Missed | High | Low | Offload toil and fix the product or improve automated fault mitigation |

Satisfaction needs evidence, not impressions: support tickets, forum and social posts, in-product happiness sampling, surveys, product manager conversations (a cheap start is asking the product manager to add reliability to existing customer talks).

## 8. Reviewing whether the SLO tracks user happiness

Quality check: count manually detected outages and tickets. Verify that known incident periods show steep budget drops and that SLO-missed periods line up with incidents and ticket spikes. Quantify with Spearman's rank correlation between tickets per day and budget lost per day, and look at outliers (for example 5 tickets with 10% budget lost, or 40 tickets with 0% lost).

Terms: recall is the share of significantly user-impacting events that the SLI captured; precision is the share of SLI-captured events that were significantly user-impacting. Uncovered outages or ticket spikes, or SLI dips with no user impact, mean the SLO lacks coverage. That is normal; evolve it.

Remedies:

- Change the SLO: compute what threshold would have notified on the missed dates, replay it over historic SLIs to see what else it would capture, do not buy recall by wrecking precision, relax it for false-positive days.
- Change the SLI implementation, if moving the threshold only trades false positives for false negatives: measure closer to the user (load balancer or client instead of server), exercise more functionality (a health handler or JavaScript-executing test instead of a bare GET), increase coverage.
- Add an aspirational SLO: a tighter target tracked alongside, explicitly "no action required" in the policy, so the team is not in perpetual emergency.
- Iterate: cheap, quick changes first to reduce uncertainty; pick the best return.

Review cadence: monthly while starting, quarterly or less when mature (SLO document); Evernote used a monthly service review plus a six-month SLO review, revised twice in about nine months.

## 9. Reports and dashboards

- Compliance report per service: all quarterly SLOs met over the past year (objectives met out of total), trend against the previous quarter and the same quarter last year.
- Error budget dashboard: budget remaining mid-quarter, with incident annotations (one example event consumed about 15% of budget in two days). Rank top incidents by budget burned.
- Put the SLI panels first on the service dashboard, since they are what an on-call opens when an SLO alert fires (`monitoring-design.md`).

## 10. Advanced topics

- Modelling dependencies: see `dependencies-and-availability-math.md`.
- Experimenting with relaxed SLOs: only when budget is available; deliberately degrade (for example add latency) to measure the effect on business metrics such as conversion, and repeat periodically. Risk: no measurable loss may mean users lack alternatives, not that they are satisfied; they leave when a competitor appears. The notes call crossing this line something to do extremely thoughtfully.
- Per-class SLOs and request buckets: `choosing-slis.md` section 9.

## 11. Warning signs

- SLO with no policy and no owner; an SLO of 100%.
- SLO set only from today's numbers and never revisited.
- More than about five SLI types.
- A single latency threshold that hides the tail.
- SLO achieved only through heroics or toil.
- Incidents or ticket spikes invisible in the SLI.
- Targets copied from a cloud provider's published SLO instead of derived from your own users (`case-studies.md`).
- Multiplying availabilities as if failures were independent.
- Incentives tied narrowly to reliability numbers (Goodhart's law, Workbook ch. 1): people then game the number.
