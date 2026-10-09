# SLO document: template, filled example, review checklist

Sources: SRE Workbook app. A (example document), ch. 2 section on SLO documents, ch. 3 (calculation rules).

Use this when asked to write, review or update the document that records a service's SLIs, SLOs and the reasoning behind them. The error budget policy is a separate document, see `error-budget-policy-template.md`.

## 1. Template

```
# <Service> SLO document

Status:        Draft | Published
Author(s):     <names>
Reviewers:     <technical accuracy>
Approvers:     <business decision; someone who can trade features for reliability>
Date:          <date written>
Approval date: <date>
Revisit date:  <date, about 12 months out; monthly while the SLO is new>

## Service overview
What the service does, who uses it, its components, request and data flow,
critical dependencies, and the SLO window (for example "four-week rolling").

## SLIs and SLOs
| Component | Category | SLI (specification and exact formula) | SLO |
|-----------|----------|----------------------------------------|-----|
| ...       | Availability | count(requests without 5XX) / count(all requests), measured at <vantage point> | 99.x% |
| ...       | Latency  | requests with duration <= T1 / all; requests with duration <= T2 / all | 90% < T1; 99% < T2 |
| ...       | Freshness / Correctness / Coverage (pipelines) | ... | ... |

## Rationale
How each number was chosen: measured period, rounding rule, or "picked by the author and verified the
service runs at or above it". State whether it has been checked against user experience.

## Error budget
Per objective: budget = 100% minus goal, with a worked example in absolute event counts.
Which document enacts the policy, and when (any single objective exhausting its budget).

## Clarifications and caveats
Measurement point and what it misses; what counts as an error; calculation rules (what "down" means,
maintenance, prober locations, confirmation probes); known blind spots; assumptions not yet validated.
```

## 2. The worked example from the notes (game service)

Overview: Android and iPhone users play each other. The app sends moves to an API over REST. A data store holds the state of current and previous games. A score pipeline reads that table and produces league tables (today, this week, all time) exposed in the app, through the API and on a public HTTP server. Window: four-week rolling.

| Component | Category | SLI | SLO |
|---|---|---|---|
| API | Availability | proportion of successful requests at the load balancer; anything other than 500 to 599 is success | 97% |
| API | Latency | proportion of requests fast enough at the load balancer, two thresholds: at most 0.4 s and at most 0.85 s, each its own ratio | 90% under 400 ms; 99% under 850 ms |
| HTTP server | Availability | same definition, on "web" requests | 99% |
| HTTP server | Latency | thresholds 0.2 s and 1.0 s | 90% under 200 ms; 99% under 1,000 ms |
| Score pipeline | Freshness | proportion of league-table records read that were updated recently, using data-request metrics from the API and HTTP server; recently = within 1 minute, or within 10 minutes | 90% within 1 min; 99% within 10 min |
| Score pipeline | Correctness | proportion of records injected by a correctness prober that give the right data when read from the league table | 99.99999% |
| Score pipeline | Completeness | proportion of hourly pipeline runs in which 100% of the games in the data store were processed | 99% |

Rationale used there: availability and latency numbers came from measurement over a four-week period (2018-01-01 to 2018-01-28); availability SLOs were rounded down to the nearest 1% and latency timings rounded up to the nearest 50 ms; all other numbers were picked by the author after verifying the services ran at or above them. The document says plainly that no attempt had yet been made to verify the numbers correlate strongly with user experience, and a footnote explains why to say so anyway: future readers can then decide to invest in evidence.

Error budget in that document: each objective has its own budget (100% minus the goal). Example: 1,000,000 API requests in the previous four weeks at 97% availability gives a 3% budget, 30,000 errors. HTTP server 99% on 1,000,000 requests gives 10,000 errors. The policy is enacted when any single objective has exhausted its budget.

Caveats section in that document: request metrics are measured at the load balancer and may miss requests that never reached it; only HTTP 5XX counts as an error; the correctness prober injects about 200 tests per second, so the correctness budget is 48 errors per four weeks (200 per second over 2,419,200 seconds is about 483.8 million probes, times 1e-7).

Notice the patterns worth copying: each SLI is a ratio of good to total events at one named vantage point; latency is expressed as two thresholds, not an average; pipelines get freshness, correctness (through a synthetic prober) and completeness; every SLI states what counts as good precisely enough to compute.

## 3. Calculation rules to write down before collecting data

From the Evernote case (`case-studies.md`): write the rules in advance. What is "down": a failed check marks a node unconfirmed down; a geographically separate second prober re-checks; only a second failure counts, and the node stays down while consecutive probes fail. Whether maintenance windows count as downtime (Evernote: yes, because hundreds of millions of users cannot know published windows). Prober cadence (every minute) and locations. Which endpoint is probed (a status-page endpoint that exercises most of the stack and returns 200 when healthy).

## 4. Review checklist (run it against any SLO document)

1. Header has an approver who can trade features against reliability, an approval date and a revisit date.
2. Overview names components, the window, and critical dependencies.
3. Every SLI row has an executable numerator and denominator and names the measurement point. Can each be computed from existing metrics?
4. Latency rows have at least two thresholds; no averages.
5. SLO values sit at or below currently measured performance, so there is budget rather than instant violation. If the service already misses its SLO, the document says so and links the recovery plan.
6. Rationale states data provenance (measured period, rounding rule, ad hoc picks) and states what has not been validated against users.
7. Error budget section gives each objective's budget in absolute events for a recent window.
8. The window matches the policy's window.
9. Caveats list measurement blind spots, what counts as an error, and calculation rules.
10. Pipelines have correctness and freshness (or coverage) SLIs, not availability alone.
11. The document is linked from the dashboard and from alert annotations, and is short enough that on-call will read it.

## 5. Notes for generating a first draft as an agent

- Fill numbers only from data you can point to. If there is no history, write the SLO as a proposal marked "ad hoc, no data yet" and add a task to collect four weeks of data; do not invent measured values.
- Derive the window-dependent budgets with `scripts/burn_rate.py` rather than by hand.
- Leave names, approvers and dates as explicit placeholders for the humans; an SLO nobody approved is not yet an SLO.
