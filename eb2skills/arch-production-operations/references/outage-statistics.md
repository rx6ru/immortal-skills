# What outage statistics say about where to invest

Source: SRE Workbook App. C (Results of Postmortem Analysis), with cross-references to ch. 15, ch. 16 and App. B as cited there. Data: a sample of thousands of Google postmortems over seven years (2010-2017), using a template that records both a trigger and a root-cause category.

## Table C-1: top eight outage triggers

| Trigger | Share |
|---|---|
| Binary push | 37% |
| Configuration push | 31% |
| User behavior change | 9% |
| Processing pipeline | 6% |
| Service provider change | 5% |
| Performance decay | 5% |
| Capacity management | 5% |
| Hardware | 2% |

Binary plus configuration pushes are 68% of triggers, consistent with the "changes are roughly 70% of outages" claim used to justify tying release freezes to the error budget. Hardware is 2%.

## Table C-2: top five root-cause categories

| Root-cause category | Share |
|---|---|
| Software | 41.35% |
| Development process failure | 20.23% |
| Complex system behaviors | 16.90% |
| Deployment planning | 6.74% |
| Network failure | 2.75% |

These sum to 87.97%; the remaining roughly 12% falls in categories the notes do not list.

Trigger and root cause differ: the trigger is the event that set the outage off (for example a push), the root cause is the underlying defect category. Record both.

## How the book uses the numbers

- Ch. 15: configuration changes dominate outage root causes over time, so validate generated config immediately, in precommit, with schema and domain checks (`configuration-design.md`).
- Ch. 16: most incidents are triggered by binary or configuration pushes, so canary and stage rollouts and separate components that change at different rates (`canarying-and-rollouts.md`).
- App. B: changes are about 70% of outages, which justifies tying release freezes to the error budget.

## Implications (synthesised in the notes)

- Put safeguards on change paths first: progressive rollout, canary with automatic rollback, config validation, fast revert. Prefer these to hardware redundancy when deciding where outages come from.
- Treat processing pipelines, provider or dependency change, user behaviour change, performance decay and capacity management as the second tier (each roughly 5-9%).
- A postmortem template should have separate trigger and root-cause fields drawn from a fixed vocabulary so trends can be computed (`postmortems.md`).

## Caveats and how to use them

The sample is Google scale and the categories are Google's taxonomy. The percentages are shares of postmortem-reported outages, not of all incidents or of downtime minutes. Use them to rank your own investment hypotheses, then test against your own postmortems: tag each of your last N incidents by trigger and category and see whether changes dominate there too. If they do, spend effort on the change path before anything else; if not, follow your own data.

Adaptation: when a user asks "where should we spend reliability effort?", answer from their incident history first and offer these shares as a prior, not a verdict.
