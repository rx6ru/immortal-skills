---
name: arch-decomposition
description: Decision procedures for breaking a system apart or merging parts, with checks to verify the result. Covers whether a codebase is decomposable (business drivers, coupling and instability metrics), tactical forking versus the six component-based decomposition patterns, service granularity (reasons to split against reasons to merge), splitting a shared database, sharing code across services (copy, library, service, sidecar), strangler-fig migration, cloud moves, and complexity checks. Use when asked to split a monolith, extract or merge services, choose microservices versus monolith, fix a distributed monolith or chatty services, break up a shared database, pick shared library versus shared service, migrate legacy incrementally, or decide rewrite versus refactor. For sagas and data ownership see arch-distributed-workflows; for API design see arch-api-design.
---

# Architectural decomposition

## Purpose

Splitting a system is easy to start and expensive to undo, and the usual failure is a distributed monolith: the same coupling, now across a network. This skill makes the agent ask for evidence before splitting, pick the migration route that fits the codebase it actually has, weigh reasons to split against reasons to merge, and leave automated checks behind that keep the structure from decaying. It also covers the opposite move: merging services that were cut wrongly.

## Choose what applies

| The request or the situation | Do this | Read |
|---|---|---|
| "Should we move to microservices / split the monolith?" with no stated problem | Run the business-case gate first (step 1 below); do not start designing services | `references/is-it-decomposable.md` |
| A monolith with some package or directory structure to be turned into services | Component-based decomposition, patterns 1 to 6 in order | `references/component-decomposition-patterns.md` |
| A tangled codebase with no usable components and a deadline | Tactical forking, with its costs stated | `references/is-it-decomposable.md` section 7 |
| "Is this codebase even salvageable?" or "rewrite or refactor?" | Coupling and instability metrics, component dependency picture, rewrite lesson | `references/is-it-decomposable.md` sections 6 and 9; `references/component-decomposition-patterns.md` pattern 4 |
| "Should this service be split?" or "should these two be one?" or services are chatty, fail together, deploy together | Disintegrator versus integrator analysis | `references/service-granularity.md` |
| Services share one database; schema changes break others; connection pool exhaustion | Data disintegrators and integrators, then the five-step process | `references/decomposing-data.md` |
| Which database type for a service's data | Selection procedure; business justification | `references/decomposing-data.md` section 7 (and `arch-data-storage` for depth) |
| Several services need the same code (validators, auth, logging, DB access) | Reuse chooser | `references/reuse-patterns.md` |
| Replacing a legacy component while it is in use; adding a gateway in front of legacy; lift and shift | Seams, strangler fig, six Rs | `references/migration-strangler.md` |
| Reviewing a design for sprawl: too many services, cycles, retries at every layer | Complexity proxies and checklist | `references/simplicity-checks.md` |
| Need a full end-to-end illustration to adapt | Replayable case | `references/worked-example-sysops-squad.md` |
| Cross-service transactions, sagas, who owns which data, eventual consistency | Not here | `arch-distributed-workflows` |
| Choosing REST/gRPC, gateway features, versioning | Not here | `arch-api-design` |
| Writing the ADR itself, fitness-function theory | Not here (this skill only says what to record) | `arch-decisions-and-tradeoffs` |
| Pure code-level tidying inside one module with no deployment boundary change | This skill does not apply | `craft-refactoring`, `craft-module-design` |
| A small system, a single team, no pain that a split would relieve | Do not decompose; say why | step 1 below |

## How to apply

### 1. Business-case gate (always first)

1. Ask or find the driver. The book's business drivers are speed to market (agility) and competitive advantage (speed plus scalability plus availability). "Nothing else works" and "microservices are modern" are not drivers.
2. Map each complaint to one of five technical drivers: maintainability, testability, deployability, scalability, availability/fault tolerance. For each, find evidence in the repository, version control, pipeline or incident history. Table in `is-it-decomposable.md` section 2.
3. Check the cheaper options for maintainability, testability and deployability: a modular monolith (domain-partitioned components with enforced boundaries) or a microkernel. They cannot give independent scaling or fault isolation; if the evidence is only about those two, distribution is justified.
4. State what the split will cost: slower features during the migration, more deployables, a database to split, a pipeline to change. Put it in an ADR (`arch-decisions-and-tradeoffs`).

If no driver has evidence, report that and stop. That is a complete and correct answer.

### 2. Pick the route

1. Is the code decomposable? Compute per-component Ca, Ce, instability I = Ce/(Ce+Ca), abstractness A and distance D = |A + I - 1|, or at least the component dependency graph. Mostly zone of pain or uselessness suggests the structure is not worth moving as is; most components near the main sequence with a few outliers suggests it is feasible.
2. No identifiable components and a need to move fast: tactical forking (clone per target, delete what each does not need). Accept duplication, leftover code and fixed up-front boundaries.
3. Identifiable components: component-based decomposition. Target service-based architecture first (coarse domain services, one shared database), then refine. Do not start with fine-grained services; you inherit data splitting, distributed workflows and operational load before you need them.
4. Do not "eat the elephant" by extracting whatever looks easy. That is the path to a distributed monolith.

### 3. Component-based sequence

Apply in order; each step has a fitness function (full list in `component-decomposition-patterns.md`):

1. Identify and size components (statements per component; flag more than about 1 to 2 standard deviations from the mean or an outsized percent; split outliers by sub-domain).
2. Gather duplicated domain components, after checking that total afferent coupling does not rise.
3. Flatten: code only in leaf directories; shared code in its own clearly named component; compute the percent of code that is shared (about 45% is a bad sign for the library count).
4. Determine dependencies: CA, CE, CT = CA + CE. Few dependencies means refactor (golf ball); many with easy regions means mixed (basketball); dense spaghetti means rewrite (airliner). Filter shared-library edges openly.
5. Create domains (namespace hierarchy), validated with a business stakeholder; an allowed-domain list enforced in CI.
6. Create domain services only after all domains are settled; enforce a namespace prefix per service.

### 4. Granularity: split or merge

For each proposed split or merge, collect evidence and run both lists.

Reasons to split: service scope (weak cohesion), code volatility (commit history), scalability differences (requests per minute per function), fault tolerance (crash history), security (sensitive operations), extensibility (known, planned variants).
Reasons to merge: an ACID transaction needed across the pieces, workflow or choreography (calls in both directions, latency, shared fate), shared domain code (above roughly 40% of combined code, or changing often, or unversionable fixes), data relationships (mutual table dependencies).

Decision rules that carry most cases:

- Every resulting piece must be nameable and cohesive; if the leftover is "other", the cut is wrong.
- Two-way synchronous calls for one user action: merge. Latency is hops times per-hop cost.
- Need for atomicity across the pieces: merge, unless the business accepts the compensation cost.
- Security as the only reason: first check whether a design-level control (access-control library, encryption, gateway and mesh policy) meets it; splitting deployment units is the expensive way.
- Volatility as the only reason: check the version-control history, and consider separate components inside one deployable first.
- Extensibility: a bet on the future; do not use it as the main reason until a pattern of expansion is confirmed (the notes' advice), or the domain makes expansion certain (payment methods).
- Present the collision as a business question ("to get X we lose Y; which matters more?") and record the answer.

### 5. Data

Treat the database as a coupling point and as a decision of its own.

1. Evidence for splitting: how many services a schema change touches; connection waits and projected connections (services x instances x pool size against the limit); blast radius of downtime; quantum; type fit.
2. Evidence against: foreign keys, views and transactions that would be severed.
3. Five steps: group tables into data domains; move them to schemas; give each service access only to its own schema and replace cross-schema access with calls to the owner; move schemas to separate servers; cut over. Synonyms are scaffolding only. Steps 1 to 3 are logical, 4 and 5 physical.
4. Connection quotas: start even, measure use per service, rebalance headroom to services that wait, remember that quotas share fairness not capacity.
5. A new database type needs a business reason, not taste.
6. Bring in the data owner or DBA from the start.

### 6. Shared code

| Candidate | Use | Why |
|---|---|---|
| Logging, monitoring, discovery, auth plumbing across many services | Sidecar and mesh, owned by an infrastructure group | Consistency without domain coupling; never domain objects |
| Tiny static one-off (marker annotation) | Replicate | No sharing, no logic to go wrong |
| Homogeneous stack, low to moderate change | Shared library: small, versioned, custom deprecation, never LATEST | Compile-time safety; favour change control over dependency management |
| Polyglot stack and volatile logic | Shared service | No duplication, change without redeploy; pay in latency, scale and fault coupling |
| Domain objects such as Customer | Contracts, not sharing | Central domain services become brittle and complex |

Test any volatility argument against the repository history before accepting it. Reuse pays when the thing changes slowly.

### 7. Migrating a live component

1. Choose the end state and write goals (functional and cross-functional), each with a fitness function.
2. Put modules and tests around the existing behaviour (seams, characterisation tests).
3. Strangler fig: route through a facade (feature flag in-process, gateway for out-of-process callers), move traffic in batches, compare error rate and latency to baseline, then delete the legacy path. Keep business logic out of the proxy. A gateway that converts protocols (adapter) raises coupling.
4. For cloud moves choose among retain, rehost, replatform, repurchase, refactor, retire; do not combine a re-architecture with the platform move.

## Verify

Show evidence for each of these, not assertions.

1. Business case: the driver-to-evidence table exists, and cheaper alternatives are named with the reason they fall short.
2. Route: the metrics table (component, Ca, Ce, I, A, D) or dependency graph was generated from the repository, outliers named, verdict stated.
3. Structure checks run in CI and are shown to fail on a deliberate violation: orphan code in a non-leaf directory, a forbidden dependency, a component above the size limit, a service with a foreign namespace prefix, a new dependency cycle. A check never seen failing is unproven. Tool options by ecosystem: ArchUnit (Java), dependency-cruiser or madge (TypeScript), import-linter (Python), a `go list`-based test (Go).
4. Behaviour: the existing test suite is green after each pure restructuring step; characterisation tests exist before touching untested legacy code.
5. Granularity: for each service, a one-sentence name with no "and other"; for each proposed split, the main user paths' hop count and latency arithmetic; the answer to "does one user action need synchronous calls both ways?".
6. Data: after logical separation, grep and catalogue queries show no cross-schema foreign key, view, synonym or foreign credentials; per-service connection waits near zero under projected load; a failure drill shows only the owner's consumers fail.
7. Reuse: no floating version specifiers in manifests; no domain classes in the sidecar or infrastructure libraries; a version-skew report against the deprecation policy.
8. Migration: both paths pass the same tests during dual running; rollback tried once; legacy route at zero traffic before deletion.
9. Complexity: dependency cycle check passes; the count of deployables, pipelines and hops before and after is written next to the benefit.
10. Record: an ADR per decision with context, decision and non-empty consequences.

Done means:
- the driver and evidence are written down, or the answer was "do not decompose" with reasons;
- the chosen route matches the codebase and is justified by measured data;
- boundaries are enforced by automated checks that were seen to fail;
- every split and merge names the forces on both sides and what was given up;
- data access crosses boundaries only through the owner;
- behaviour is verified unchanged, and the user is shown the tables, the check results and the ADRs.

## Proportion and limits

- Small system, one team, no pain a split would relieve: stay modular inside one deployable. Every service adds a pipeline, dashboards, on-call surface and network hops.
- A request to "extract one service" still needs steps 1 and 4 in miniature (driver; both force lists; data ownership), but not the full six-pattern sequence. Scale the work to the size of the change.
- Thresholds in the notes (10% or 30% of code, 40% shared code, 15 dependencies, 30/70 workflow split, 300 ms per hop, 2,000 connections, 10% of time for simplicity) are examples from one case. Use measurements from the system at hand and say so.
- The book is from 2021/22 and its case is a business application on a shared database. Event-driven systems, data platforms and teams already on a managed platform shift some trade-offs (for instance, platform-provided sidecars and shared tooling); apply the same questions.
- Contested or judgement-heavy points: tactical forking against component-based (forking is faster and uglier; choose by whether components exist and by tolerance for duplication); library granularity (change control against dependency count; matters more as services grow); extensibility as a split reason (a bet on the future); whether stopping after logical data separation is acceptable (adaptation; state it in the ADR).
- Some formulas were reconstructed in the notes (distance from the main sequence, abstractness form). Use them as ranking aids, not precise scores. The database-type ratings were charts the notes could not recover.
- Statement counting and import graphs approximate; use them to find questions.

## References

- `references/is-it-decomposable.md`: business case gate, five drivers with measures, coupling and instability metrics, decision tree, forking versus component-based, rewrite lesson. Read first for any "should we split" request.
- `references/component-decomposition-patterns.md`: the six patterns with steps, fitness functions, case numbers, a small size/orphan check script. Read when executing a monolith-to-domain-services migration.
- `references/service-granularity.md`: six disintegrators, four integrators, tables, decision procedure, trade-off statement, worked decisions. Read when deciding to split or merge a service.
- `references/decomposing-data.md`: data drivers, five steps with SQL, connection quota example, database types, survey case. Read when a database is shared or a new store is proposed.
- `references/reuse-patterns.md`: replication, library, service, sidecar with trade-off tables, versioning rules, when reuse adds value. Read when two or more services need the same code.
- `references/migration-strangler.md`: end states, fitness-function categories, modules and seams, strangler fig, facade versus adapter, six Rs, zero trust during migration. Read for live migrations and cloud moves.
- `references/simplicity-checks.md`: complexity proxies, diagram smells (amplification, cycles), case lessons, pre- and post-split checklist. Read when reviewing a design for sprawl or before approving a new service.
- `references/worked-example-sysops-squad.md`: the running case as a sequence with ADR skeletons and a replay template. Read when you need a model of the whole flow.

## Sources

- Ford, Richards, Sadalage, Dehghani, Software Architecture: The Hard Parts (early release 2021/22), ch. 3 Architectural Modularity.
- The same, ch. 4 Architectural Decomposition.
- The same, ch. 5 Component-Based Decomposition Patterns.
- The same, ch. 6 Pulling Apart Operational Data.
- The same, ch. 7 Service Granularity.
- The same, ch. 8 Reuse Patterns.
- Gough, Bryant, Auburn, Mastering API Architecture (2022), ch. 8 Redesigning Applications to API-Driven Architectures.
- The same, ch. 9 Using API Infrastructure to Evolve Toward Cloud Platforms.
- Beyer et al., The Site Reliability Workbook (2018), ch. 7 Simplicity.
