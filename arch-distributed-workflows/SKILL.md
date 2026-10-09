---
name: arch-distributed-workflows
description: Decision procedures for coordinating work and data across services that each own their data. Covers data ownership (single, common, joint), ACID vs BASE, eventual-consistency patterns, reading data a service does not own, orchestration vs choreography, the eight transactional saga patterns with selection and compensation, saga state machines, strict vs loose service contracts, idempotency keys and effectively-once processing, and analytical data (warehouse, lake, mesh). Use when a business operation spans several services, two services write the same table, someone proposes a distributed transaction, a shared database, a saga, or "choreography because it is decoupled", or when retries, duplicates and half-finished workflows appear. Not for isolation levels inside one database (arch-transactions) or for splitting a monolith (arch-decomposition).
---

# Distributed workflows and data across services

## Purpose

Once each service owns its data, work that used to be one database transaction becomes a
workflow across boundaries, and every choice about it (who owns a table, how a read crosses a
boundary, whether calls block, who coordinates, what happens on failure, how strict the message
format is) trades one quality for another. This skill gives you the options, the costs of each, and
a way to choose and check, so you do not default to a familiar pattern (a distributed transaction,
an orchestrator everywhere, or events everywhere) without seeing what it gives up.

Principle that runs through everything: the dimensions are entangled. Making a call asynchronous
changes consistency and coordination too. Analyse communication, consistency and coordination
together for one workflow, then decide.

## Choose what applies

Start from what the user asked or what the code shows.

| Situation | Go to |
|---|---|
| Two or more services write the same table; "who owns this data"; splitting a shared schema | `references/data-ownership.md` |
| A service needs data another service owns (a join disappeared) | `references/distributed-data-access.md` |
| One request must update several services; "can we keep a transaction"; ACID vs BASE; unsubscribe/delete flows | `references/eventual-consistency-patterns.md` |
| Orchestrator vs choreography; workflow state; "who knows where the request is" | `references/orchestration-vs-choreography.md` |
| Picking or reviewing a saga; the workflow was made async for speed; atomic requirement across services | `references/saga-patterns.md` |
| Designing the saga state table, compensation, retries, error states, saga discoverability | `references/saga-state-and-compensation.md` |
| Message formats between services or to mobile clients; gRPC vs REST vs name/value; contract tests; payloads too large | `references/contracts.md` |
| Reporting, BI or ML needs data from many services; warehouse vs lake vs data mesh | `references/analytical-data.md` |
| Duplicates, retries, "exactly once", 2PC/XA, keeping a search index or cache in step, uniqueness across shards, stale vs corrupt data | `references/end-to-end-correctness.md` |
| Counting quanta, "are these really independent services", placing a workflow on the three dimensions | `references/quanta-and-dynamic-coupling.md` |
| Reviewing a design or pull request in this area | `references/review-checklists.md` |

This skill does not apply when:

- Everything runs in one process and one database. Use the database's transaction; adding a saga or
  event flow there is cost with no benefit.
- The question is a lost update, write skew or isolation level inside a single database: use
  `arch-transactions`.
- The question is whether and how to split a system, service size, or breaking up a shared database
  as a migration: use `arch-decomposition` (this skill takes over once the services exist and must
  cooperate).
- The question is replication lag, leader failover or sharding mechanics: use
  `arch-replication-and-consistency`.
- The work is stream or batch pipeline mechanics (windows, CDC tooling, brokers): use
  `arch-data-pipelines`.
- The request is a one-off call from one service to one other, with no shared state and no
  workflow. A plain request and a retry with an idempotency key is enough.

## How to apply

Work in this order; stop as soon as the question is answered. A small request ("which pattern for
this call") deserves a short answer with the trade-off stated, not the whole procedure.

### 1. Establish the facts

1. Name the services and the data each owns. Draw tables inside the service that writes them.
2. Count quanta (`references/quanta-and-dynamic-coupling.md`): services sharing a database or a
   mandatory broker or UI are one deployable unit for scale and availability purposes. If you find
   one quantum, say so before promising independence.
3. For the workflow in question, list steps, optional paths, error paths, and the quality concerns
   the business raised (control, state query, error handling, scale, responsiveness).

### 2. Settle ownership, then access

1. Rule: the service that writes a table owns it. Resolve single ownership first, then common, then
   joint.
2. Common (most services write): create a dedicated owning service; senders use a persistent queue,
   fire-and-forget unless they need a return value.
3. Joint (a couple of services in one domain write): pick one of the four techniques.

| Joint-ownership technique | Pick when | Main cost |
|---|---|---|
| Table split | columns separate cleanly; consistency can lag | no ACID across the two parts; sync on create/delete |
| Data domain | services must stay separate for scale/fault/volatility; shared schema tolerable | schema changes need coordinated deploys; write governance |
| Delegate | one entity dominates; other writes tolerate eventual consistency | coupling; non-owner writes slow and unreliable |
| Service consolidation | writers need atomic transactions and are inseparable | coarser scale and fault isolation; bigger deploys |

4. A service may connect to one schema only. If it already sits in a data domain, a second domain is
   not available to it, which removes the data-domain option.
5. Read access to foreign data:

| Access pattern | Pick when | Main cost |
|---|---|---|
| Inter-service call | low volume, latency tolerable, simplest | 3 latencies (network, security, data), availability coupling |
| Replicated cache | small (under about 500 MB x instances), mostly static, read-heavy | startup dependency, volume and update-rate limits, config effort |
| Column replication | reporting/aggregation, large volume, weak consistency | lag, sync machinery, ownership blur |
| Data domain | strict consistency/integrity, large data, shared schema acceptable | wider bounded context, security, write governance |

6. Hypothesis method: pick the likely winner, then deliberately look for its negatives before
   committing; then run a proof of concept on unknowns (new product, licence, deployment limits).

### 3. Decide how the business request converges

1. Challenge atomicity with the business: is all-or-nothing across these services really required,
   or can the user be told "done" while a back-office step catches up? Most steps are not needed by
   the user (a survey, a notification, analytics).
2. If a single ACID transaction is truly required and the data is jointly owned by inseparable
   writers, consolidating the services is a legitimate answer.
3. Otherwise choose how convergence happens:

| Pattern | Pick when |
|---|---|
| Orchestrated request-based | the user must get a complete answer; latency tolerable; accept compensations |
| Event-based | fast response, decoupled services; accept dead letter handling and soft state |
| Background synchronisation | closed or legacy systems only; never inside a microservice boundary |

### 4. Choose coordination and saga pattern

1. Orchestration vs choreography: more error paths, more need for state query and recovery points to
   orchestration; simple linear high-throughput flows with rare errors point to choreography. Use one
   orchestrator per workflow, with no domain logic in it. Never choose either "because it is more
   decoupled" or "because it is simpler" without the concern table.
2. Place the workflow in the saga matrix:

| Pattern (letters) | Comm. | Consistency | Coord. | Coupling | Complexity | Scale | Choose for |
|---|---|---|---|---|---|---|---|
| Epic (sao) | sync | atomic | orchestrated | very high | low | very low | atomic is mandatory, simple flow; or merge the services |
| Phone Tag (sac) | sync | atomic | choreographed | high | high | low | simple, few errors, idempotent steps |
| Fairy Tale (seo) | sync | eventual | orchestrated | high | very low | high | balanced, popular choice once atomicity is dropped |
| Time Travel (sec) | sync | eventual | choreographed | medium | low | high | one-way ingest; on-ramp to Anthology |
| Fantasy Fiction (aao) | async | atomic | orchestrated | high | high | low | avoid; use Parallel |
| Horror Story (aac) | async | atomic | choreographed | medium | very high | medium | avoid; drop atomicity (Anthology) |
| Parallel (aeo) | async | eventual | orchestrated | low | low | high | complex flow needing scale |
| Anthology (aec) | async | eventual | choreographed | very low | high | very high | simple linear flow, top throughput |

3. Procedure: (a) can consistency be eventual? if yes consider seo, sec, aeo, aec; (b) complex flow:
   orchestrated (seo, aeo), simple and high throughput: choreographed (sec, aec); (c) need scale or
   parallelism: asynchronous, otherwise start synchronous because it is easier to debug; (d) atomic
   mandatory: Epic knowingly, or consolidate; avoid aao and aac.
4. Never speed up an atomic flow by making it asynchronous and choreographed in isolation; that
   produces the Horror Story.

### 5. Design failure handling

1. Write the saga state table: START, transition states with actions, error states, CLOSED. Every
   state needs exits for success, failure and timeout.
2. Prefer state management plus retry (keep the user unaffected, retry behind the scenes, escalate
   after a deadline) for steps the user does not need to act on. Use compensating updates only for
   steps that must be undone, and then treat the compensation as a tested feature: it can fail, and
   side effects may already have propagated.
3. Make every handler idempotent and put an idempotency key on every retried operation
   (`references/end-to-end-correctness.md`).
4. Make saga membership discoverable (annotation or manifest plus a scanner).

### 6. Choose the contracts

1. Decide strict or loose per integration point from three factors: co-change frequency, the
   consumer's deployment speed, and the rate of change of the information. Then pick technology.
2. Strict: schema, versions, deprecation policy. Loose: name/value pairs plus consumer-driven
   contract tests in the provider pipeline, plus an extension mechanism.
3. Send only what the consumer needs. Use stamp coupling only for standard documents or workflow
   state in choreography.

### 7. Analytical data

Do not build a warehouse for a distributed system by default. Compare warehouse, lake and mesh
(`references/analytical-data.md`); under a mesh each service gets a data product quantum fed
asynchronously and eventually, never transactionally.

### 8. Record

Write an ADR per significant choice (template in `arch-decisions-and-tradeoffs`) containing the
dimensions weighed, what is given up, and the trigger to reconsider.

## Verify

Produce evidence, not assertions. Pick the items that match the change.

1. Ownership: run a script or query that lists, for each table, the roles that can write it; show
   one writer per table or a named data domain. Scan repositories for writes to foreign tables.
2. Quanta: show the dependency inventory (manifests, container files, broker and database
   bindings) and the resulting quantum count; start each service with only its declared
   dependencies.
3. Convergence: for each cross-service business transaction, show the stated maximum staleness and
   a test that measures it.
4. Failure injection, one test per row: each participant down in turn; the compensating action
   failing; a message delivered twice; a message dropped; messages arriving out of order for async
   flows; coordinator or orchestrator killed mid-flow.
5. Idempotency: send the same request twice and concurrently; kill the process between commit and
   response and retry; assert exactly one effect, and that the key survives client retries.
6. State machine: table-driven tests for every transition, illegal and duplicate events, and a
   query that lists sagas stuck in an error state with their age.
7. Contracts: consumer-driven contract tests run in the provider pipeline and block deploys; unknown
   fields are tolerated on loose contracts; list fields no consumer reads.
8. Replicated cache or replica: stop the owner after warm-up and confirm the consumer works; cold
   start without the owner behaves as documented; memory equals size times maximum instances.
9. Analytical side: take the data plane down and confirm the service is unaffected; completeness
   check per feed.
10. Review with `references/review-checklists.md` and quote the answers you could not establish.

Done means:

- Every table has one owner (or a named data domain) and every foreign read uses a named pattern.
- Each cross-service workflow is placed on communication, consistency and coordination, with the
  saga pattern named and its ratings checked against the business needs.
- No design sits in aao or aac without an explicit, recorded exception.
- Every failure path has a state, a retry or compensation, an owner for repair, and a test.
- Every retried operation is idempotent by key enforced at the final writer.
- Contract strictness is stated per integration point, with the matching tests.
- The decisions are recorded with what they give up.

## Proportion and limits

- Fewer moving parts is a feature. If the services share one database and always deploy together,
  merging them removes the problem; a saga across them adds problems.
- Do not run the whole procedure for a single call between two services. Ownership, a timeout, a
  retry with an idempotency key, and a contract choice are usually enough.
- Orchestration costs scale and creates a single point of failure to mitigate; choreography costs
  visibility and recoverability. Neither is free; the right one depends on the workflow, and a
  system will often use both in different workflows.
- Replicated caches and data domains have hard limits (size, volatility, one-schema rule); the
  figures in the notes (about 500 MB, latencies of 30 to 300 ms and similar) are indicative from the
  source, so measure in your environment.
- Data mesh is organisational as well as technical; it needs platform capacity and several domain
  teams. For small systems it is overhead.
- The source is an early-release text; it contains small inconsistencies (for example the
  Fantasy Fiction coupling wording) and tool names and product names are examples, not
  recommendations. The principles (ownership by writer, entangled dimensions, challenge atomicity,
  idempotency by key) are the durable part.
- The Kleppmann chapters argue one school of thought (ordered log, deterministic derivation,
  coordination avoidance); treat them as strong guidance, not consensus. Where the business cannot
  tolerate even rare violations, synchronous coordination for that step is correct.
- Where this skill and the source disagree with vendor behaviour (isolation level names, product
  defaults), test the real system.

## References

- `references/quanta-and-dynamic-coupling.md`: read to count quanta, tell static from dynamic
  coupling, and place a workflow on the three dimensions.
- `references/data-ownership.md`: read when tables have more than one writer; the four joint
  techniques with trade-off tables.
- `references/eventual-consistency-patterns.md`: read for ACID vs BASE and the three convergence
  patterns.
- `references/distributed-data-access.md`: read when a service needs data it does not own; four
  patterns, sizing and decision procedure.
- `references/orchestration-vs-choreography.md`: read to choose a coordination style and handle
  workflow state.
- `references/saga-patterns.md`: read to pick among the eight sagas and for the ratings matrix.
- `references/saga-state-and-compensation.md`: read when building the state machine, retries and
  compensation, and saga discoverability.
- `references/contracts.md`: read when choosing contract strictness, consumer-driven contracts or
  judging payloads.
- `references/analytical-data.md`: read for warehouse, lake and mesh and the data product quantum.
- `references/end-to-end-correctness.md`: read for 2PC/XA costs, idempotency recipes, constraints
  without consensus, timeliness vs integrity and keeping derived data in step.
- `references/review-checklists.md`: read when reviewing a design or change in this area.

Related skills: `arch-decisions-and-tradeoffs` (ADR template, trade-off method, fitness
functions), `arch-decomposition`, `arch-transactions`, `arch-data-pipelines`,
`arch-replication-and-consistency`, `arch-api-design`.

## Sources

- Software Architecture: The Hard Parts, ch. 2 (discerning coupling, quanta, the three dynamic
  dimensions).
- Software Architecture: The Hard Parts, ch. 9 (data ownership, distributed transactions, BASE,
  eventual-consistency patterns).
- Software Architecture: The Hard Parts, ch. 10 (distributed data access).
- Software Architecture: The Hard Parts, ch. 11 (orchestration and choreography, workflow state).
- Software Architecture: The Hard Parts, ch. 12 (the eight transactional sagas, state machines,
  compensation, saga management).
- Software Architecture: The Hard Parts, ch. 13 (contracts, consumer-driven contracts, stamp
  coupling).
- Software Architecture: The Hard Parts, ch. 14 (warehouse, lake, data mesh).
- Designing Data-Intensive Applications 2e, ch. 8 (distributed transactions, 2PC, XA, exactly-once
  by idempotence).
- Designing Data-Intensive Applications 2e, ch. 13 second half (derived data, end-to-end argument,
  constraints, timeliness vs integrity, auditing).
