# immortal-skills

Skills for AI coding agents, distilled from classic software engineering books.

Each skill tells an agent three things: **when** it applies, **how** to apply it, and **how to verify** the result.

## Layout

```
eb2skills/                 Engineering Books to Skills
  <skill-name>/
    SKILL.md               when to use, procedures, verification
    references/            catalogues, decision guides, checklists (loaded on demand)
    scripts/               helper tools (three skills only)
```

## Skills

### Software craft

| Skill | Use it for |
|---|---|
| `craft-router` | Picking the right craft skill for a task |
| `craft-clean-code` | Names, functions, comments, formatting, code-smell checklist |
| `craft-module-design` | Modules, interfaces, layering, coupling, information hiding |
| `craft-error-handling` | Exceptions vs results, contracts, validation, resource cleanup |
| `craft-refactoring` | Safe restructuring: 24 smells, ~60 refactorings with step-by-step mechanics |
| `craft-debugging` | Reproduce, minimise, hypothesise, locate, fix, verify |
| `craft-design-patterns` | Choosing, applying and removing the 23 GoF patterns |
| `craft-testing` | What to test, test levels, doubles, property-based tests |
| `craft-concurrency` | Threads, async, locks, deadlock, testing concurrent code |
| `craft-planning-and-estimation` | Scoping, estimating, sequencing, honest status |
| `craft-technical-communication` | Diagrams, docs, PR descriptions, status updates |

### Architecture and systems

| Skill | Use it for |
|---|---|
| `arch-router` | Picking the right architecture skill by question, product stage or requirement |
| `arch-system-design` | Requirements, estimation, scaling ladder, building blocks, worked designs |
| `arch-decisions-and-tradeoffs` | Trade-off analysis, ADRs, fitness functions |
| `arch-decomposition` | Splitting or merging services, shared databases, strangler migration |
| `arch-distributed-workflows` | Sagas, orchestration vs choreography, data ownership, contracts |
| `arch-data-storage` | Data models, storage engines, indexes, schema evolution |
| `arch-replication-and-consistency` | Replication, sharding, quorums, clocks, consensus |
| `arch-transactions` | Isolation anomalies, isolation levels, retries, two-phase commit |
| `arch-data-pipelines` | Batch, streams, CDC, outbox, exactly-once, pipeline reliability |
| `arch-api-design` | REST/gRPC/GraphQL, versioning, contract tests, gateways, releases |
| `arch-api-security` | Threat modelling, OAuth2, token validation, rate limiting |
| `arch-reliability-slos` | SLIs, SLOs, error budgets, burn-rate alerting |
| `arch-production-operations` | Canaries, config changes, load, incidents, postmortems |
| `arch-scalability-analysis` | Universal Scalability Law, capacity planning, benchmark analysis |

### Functional style (language-independent)

| Skill | Use it for |
|---|---|
| `fp-router` | Picking the right fp skill and how far to take the style |
| `fp-pure-core` | Pure logic with effects at the edges, state as a value |
| `fp-data-and-errors` | Sum types, folds, typed errors, validation, laziness |
| `fp-api-design-with-laws` | Designing composable APIs, algebraic laws, law tests |
| `fp-effects-and-streams` | Effect descriptions and interpreters, stack safety, resource-safe streams |

## Tools

| Script | What it does |
|---|---|
| `eb2skills/craft-debugging/scripts/ddmin.py` | Shrinks a failing input to a minimal failing input |
| `eb2skills/arch-reliability-slos/scripts/burn_rate.py` | Computes error budgets and burn-rate alert thresholds |
| `eb2skills/arch-scalability-analysis/scripts/usl_fit.py` | Fits the Universal Scalability Law to benchmark data |

Python 3, standard library only. Each has `--help` and `--self-test`.

## Install

Link the skills into your agent's skills directory:

```sh
git clone https://github.com/rx6ru/immortal-skills.git
cd immortal-skills
for s in eb2skills/*/; do ln -s "$PWD/$s" ~/.claude/skills/"$(basename "$s")"; done
```

Uninstall:

```sh
find ~/.claude/skills -maxdepth 1 -type l -lname '*/eb2skills/*' -delete
```

## Sources

Clean Code · A Philosophy of Software Design · Refactoring (2nd ed.) · The Pragmatic Programmer · The Mythical Man-Month · Why Programs Fail · Design Patterns · Head First Design Patterns (2nd ed.) · Communication Patterns · Designing Data-Intensive Applications (2nd ed.) · Software Architecture: The Hard Parts · System Design Interview · Mastering API Architecture · The Site Reliability Workbook · Practical Scalability Analysis with the Universal Scalability Law · Functional Programming in Scala

The skills are written in original words and cite book and chapter. They are a working aid, not a substitute for the books.

## Notes

- Content that goes beyond a book (modern tools, other languages, updated security practice) is labelled as adaptation or update inside each skill.
- Code examples were run where the tooling was available. SQL was not run against PostgreSQL, alert rules were not checked with `promtool`, and diagrams were not rendered.
