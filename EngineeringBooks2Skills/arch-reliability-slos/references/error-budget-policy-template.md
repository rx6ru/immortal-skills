# Error budget policy: template, choices, review checklist

Sources: SRE Workbook app. B (example policy), ch. 2 (policy section and stakeholder test), ch. 8 (halt rollouts when violations exceed an agreed fraction).

Use this when asked to write or review the document that says what happens when a service spends its error budget. Without it the SLO "has no teeth" and the budget is not a decision tool.

## 1. What the policy must do

State specific actions when the service has consumed its whole budget for the period, and who does them. The common menu from the notes, from mild to extreme:

1. The development team gives top priority to reliability bugs from the last four weeks.
2. The development team works only on reliability until the service is back within SLO, with high-level approval to push back on external feature requests and mandates.
3. Production freeze: halt certain changes until enough budget exists again.
4. Emergency: with high-level approval, deprioritise all external demands until exit criteria are met (back within SLO, plus steps to reduce the chance of a repeat: better monitoring and testing, removing dangerous dependencies, re-architecting away known failure types).

Pick the mildest level that changes behaviour. A freeze nobody enforces teaches everyone to ignore the policy; a freeze that stops security fixes is harmful, so name the exceptions.

## 2. Template (section order from the example)

```
# <Service> error budget policy
Status / Authors / Reviewers / Approvers / Date / Approval date / Revisit date (about one year out)

## Service overview
Release cadence the policy governs (example: backend daily, client weekly; both covered).

## Goals
1. Protect customers from repeated SLO misses.
2. Provide an incentive to balance reliability with other features.

## Non-goals
Not a punishment for missing SLOs. Halting change is undesirable; the policy gives teams permission
to focus exclusively on reliability when the data says reliability matters more than features.

## SLO miss policy
- At or above SLO: releases (including data changes) follow the normal release policy.
- Budget exceeded over the preceding <window>: halt all changes and releases other than P0 issues
  and security fixes until the service is back within SLO. (P0 = highest bug priority.)
- Depending on cause, the team may devote extra resources to reliability instead of features.
- The team MUST work on reliability if: (list)
- The team MAY continue non-reliability work if: (list)

## Outage policy
Proportional triggers that turn budget burn into postmortems and planned work.

## Escalation policy
Who decides disputes about how the budget is calculated or what the actions are.

## Background
Short primer for newcomers (what an error budget is, one worked number).
```

## 3. The worked example's rules

- Trigger: error budget exceeded over the preceding four-week window, the same rolling window as the SLO.
- Freeze scope: all changes and releases other than P0 issues or security fixes, until the service is back within SLO. It has a defined exit.
- The team must work on reliability if: a code bug or procedural error caused the service itself to exceed its budget; a postmortem reveals an opportunity to soften a hard dependency; or miscategorised errors failed to consume budget that would have caused an SLO miss (the budget was understated).
- The team may continue non-reliability work if: the outage came from a company-wide networking problem; the outage came from a service maintained by another team that has itself frozen releases to fix its reliability; the budget was consumed by users out of scope for the SLO (load tests, penetration testers); or miscategorised errors consumed budget though no users were impacted.
- Outage policy: a single incident that consumes more than 20% of the budget over four weeks requires a postmortem with at least one P0 action item addressing the root cause. A single class of outage that consumes more than 20% of the budget over a quarter requires a P0 item in the quarterly planning document for the following quarter.
- Escalation: disagreements about calculating the budget or about the actions go to the CTO.
- Background text: changes are a major source of instability (the example says roughly 70% of outages); a 99.9% SLO means 0.1% budget, which on 1,000,000 requests in four weeks is 1,000 errors.

The 20% thresholds and the 70% figure belong to that example. Treat the numbers as defaults to negotiate; the structure (two proportional triggers, enumerated exceptions, named escalation owner) is what to preserve.

## 4. Design choices to preserve

- Triggered over the same window as the SLO.
- Explicit freeze scope and explicit exit.
- Exceptions enumerated so the freeze is not applied for causes outside the team's control, and misclassification is handled in both directions.
- One policy covers every objective in the SLO document: any single objective exhausting its budget enacts it.
- Dependencies: two schools exist when a dependency causes the miss. One says do not freeze because it is not your fault; the other freezes regardless. The second makes users happier. Decide per service and record it in the policy (Workbook ch. 2).
- Approved by someone with authority over both feature and reliability priorities.

## 5. Acceptance test for the policy

The policy is accepted when product, development and operations all sign it and each of these holds (Workbook ch. 2):

- Operations can defend the SLO without toil or heroics under the policy.
- Development accepts the reliability work it triggers.
- Product accepts that users may have a poor experience until the policy triggers and finds that tolerable; if not, tighten the SLO.

## 6. Review checklist

1. Does each rule reference a measurable quantity (budget percent, window)?
2. Is what is frozen unambiguous, and who may override it?
3. Are exceptions complete enough to avoid arguments mid-incident?
4. Is it consistent with the SLO document (same window, same objectives)?
5. Is there a path for budget miscalculation disputes?
6. Are there alerts that warn before the budget is gone, so the policy is not the first signal (`alerting-on-slos.md`)?
7. Is there a revisit date, and is someone assigned to check whether the policy was applied the last time the budget ran out?
8. Does it avoid becoming a punishment? Non-goals should say so, and incentives should not reward hiding incidents (Goodhart's law note in `setting-slos-and-error-budgets.md`).

## 7. Writing a draft as an agent

Fill service names, cadence and window from the SLO document. Keep the example's thresholds only if the user accepts them, and list each as a "proposed default". Put the exceptions list in front of the user explicitly; those are the points where teams disagree. Never assert that someone approved the policy.
