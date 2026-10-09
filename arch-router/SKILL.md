---
name: arch-router
description: "Index of the arch-* skills (architecture and systems) that maps a design, review or operations question to the skill worth loading and the order to use them in, by product stage, requirements and architecture style. Use when a request is broad (\"design this system\", \"review our architecture\", \"should we move to microservices\", \"make this scale\", \"make this reliable\"), when a question touches data, services and operations at once, or when unsure whether a problem belongs to storage, replication, transactions, pipelines, workflows, APIs, SLOs or operations. Skip it when one arch-* skill obviously fits; load that skill directly. For code-level practice use craft-router; for functional style use fp-router."
---

# Architecture skills: which one, and in what order

## Purpose

Thirteen arch skills cover overlapping ground from eight books. This index picks the one or two
that match the question, so a request about a race condition does not pull in a system-design
procedure, and a request to design a system does not skip the requirements step.

## Pick by the question being asked

| The question | Load |
|---|---|
| Design a system from a problem statement; estimate QPS, storage, servers; where does a cache, queue or shard go | `arch-system-design` |
| "X or Y?", "what are the trade-offs?", write an ADR, enforce a structural rule in CI | `arch-decisions-and-tradeoffs` |
| Split a monolith, merge services, how big should a service be, break up a shared database, share code across services | `arch-decomposition` |
| One business operation spans services; sagas; orchestration or choreography; who owns this table; service contracts | `arch-distributed-workflows` |
| Which database, data model, index, file or message format; change a schema without breaking readers | `arch-data-storage` |
| Read replicas, multi-region, failover, stale reads, shard keys, distributed locks, "do we need strong consistency" | `arch-replication-and-consistency` |
| Read-then-write races, lost updates, double spends, which isolation level, retries around transactions | `arch-transactions` |
| ETL, streams, queues and consumers, CDC, outbox, keeping an index or cache in sync, duplicates and reprocessing | `arch-data-pipelines` |
| Design, version, test or release an API; gateway or mesh; REST, gRPC or GraphQL | `arch-api-design` |
| Threat model, OAuth flow, token validation, rate limiting, authorisation checks | `arch-api-security` |
| Define SLIs and SLOs, error budgets, alert rules, monitoring | `arch-reliability-slos` |
| Rollouts, canaries, config changes, load shedding, autoscaling, incidents, postmortems, toil | `arch-production-operations` |
| Will more nodes help, where is the throughput peak, interpret a load test, check a scaling claim | `arch-scalability-analysis` |

## Pick by product stage

| Stage | What usually matters | Skills |
|---|---|---|
| Idea or prototype, few users | Clear requirements, a simple data model, one deployable unit | `arch-system-design` (procedure and requirements only), `arch-data-storage` |
| First real users | Correctness under concurrency, a safe release path, basic indicators | `arch-transactions`, `arch-production-operations`, `arch-reliability-slos` |
| Growth, load is a concern | Measured bottlenecks before new components; replicas, caches, queues | `arch-scalability-analysis`, `arch-system-design` (scaling ladder), `arch-replication-and-consistency` |
| Several teams, change is slow | Boundaries, ownership, contracts, decision records | `arch-decomposition`, `arch-decisions-and-tradeoffs`, `arch-api-design` |
| Many services | Cross-service consistency, pipelines, security at the edges, incident practice | `arch-distributed-workflows`, `arch-data-pipelines`, `arch-api-security`, `arch-production-operations` |

Treat the stage as a prior, not a rule: a prototype that handles money needs `arch-transactions`
on day one.

## Pick by requirement signal

| Signal in the requirements or the code | Skill |
|---|---|
| A number attached to latency, availability or throughput | `arch-reliability-slos` to make it measurable; `arch-system-design` to size for it |
| "Must never double-charge / oversell / lose a write" | `arch-transactions`; across services also `arch-distributed-workflows` |
| "Users in several regions" or "must survive a zone failure" | `arch-replication-and-consistency` |
| "Search", "analytics", "reporting" next to a transactional store | `arch-data-storage`, then `arch-data-pipelines` for keeping them in sync |
| "Third parties will call this" | `arch-api-design` and `arch-api-security` |
| "Teams must deploy independently" | `arch-decomposition`, with `arch-decisions-and-tradeoffs` to record why |
| Old and new versions run side by side during deploys | `arch-data-storage` (schema evolution), `arch-api-design` (compatibility) |

## Common sequences

| Request | Sequence |
|---|---|
| Greenfield design | `arch-system-design` for requirements, numbers and a first shape; the specific skill for each hard part; `arch-decisions-and-tradeoffs` to record the choices that are costly to reverse |
| "Should we go to microservices?" | `arch-decisions-and-tradeoffs` for the drivers, `arch-decomposition` for whether and how, `arch-distributed-workflows` for what the split will cost in data and workflows |
| Architecture review | `arch-system-design` (requirements and numbers stated?), then only the skills matching the risks you find |
| "It is slow under load" | `arch-scalability-analysis` to measure and model before changing anything; then storage, replication or operations skills according to the finding |
| Add a new store next to the database | `arch-data-storage` to choose it, `arch-data-pipelines` to feed it, `arch-transactions` if a dual write is being proposed |
| Reliability push | `arch-reliability-slos` for targets and alerts, `arch-production-operations` for rollouts, incidents and load behaviour |

## Boundaries between easily confused skills

- One database, concurrent transactions: `arch-transactions`. Several copies of the data:
  `arch-replication-and-consistency`. Several services each with their own data:
  `arch-distributed-workflows`.
- Choosing where data lives and its shape: `arch-data-storage`. Moving it between systems:
  `arch-data-pipelines`.
- How to decide and record: `arch-decisions-and-tradeoffs`. What to decide for a split:
  `arch-decomposition`.
- Targets and alert arithmetic: `arch-reliability-slos`. What to do about them in production:
  `arch-production-operations`.
- Sizing from requirements: `arch-system-design`. Modelling measured scaling behaviour:
  `arch-scalability-analysis`.
- Module and class structure inside one codebase is `craft-module-design`, not an arch skill.

## Verify you routed well

- You can name the question, the product stage and the requirement signals that led to your choice.
- Requirements and rough numbers are stated before any component is proposed.
- You loaded at most two or three arch skills, each for a named part of the problem.
- The answer is sized to the system in front of you; nothing was added because a skill described it.

## Proportion

Most systems are small. A single service with one relational database rarely needs more than
`arch-transactions` and a release practice. Reach for distributed-systems skills when a stated
requirement forces distribution, not in anticipation.

## Sources

Designing Data-Intensive Applications (2nd ed.); Software Architecture: The Hard Parts; Fundamentals
of Software Architecture (chapter 1 only); System Design Interview (2nd ed.); Mastering API
Architecture; The Site Reliability Workbook; Practical Scalability Analysis with the Universal
Scalability Law; Communication Patterns (decision records).
