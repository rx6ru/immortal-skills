# Review checklists for distributed data and workflow designs

Read this when you review a design document, a pull request or an existing system that coordinates
work or shares data across services, and want a ready list of questions with observable answers.
Each list maps to a reference file with the reasoning.

Contents: ownership review; data access review; cross-service transaction review; coordination
review; saga review; contract review; analytical data review; retries and idempotency review;
decision-record review; signals that the design should be reconsidered.

## Ownership review (`data-ownership.md`)

1. For every table, name the one service allowed to write it. Evidence: database grants or the list
   of repositories containing writes to it.
2. Any table written by two services is classified as common or joint and has a chosen technique
   (table split, data domain, delegate, consolidation, or a dedicated owning service).
3. No service connects to more than one schema (the one-schema rule), and any shared schema is a
   named data domain with a write-governance rule.
4. Tables outside every service box in the diagram are shared data domains and are justified.
5. The ADR states the consequences for the non-owner (performance, fault tolerance, staleness).

## Data access review (`distributed-data-access.md`)

1. Every read of foreign data uses a named pattern: remote call, column replication, replicated
   cache or data domain.
2. Remote-call reads show a latency budget that includes network, security and data latency and an
   answer to "what happens when the owner is down".
3. Replicas and caches are read-only for the consumer, and the owner is the only writer.
4. Replicated cache: size times maximum instance count is computed; update rate is low; the startup
   dependency is documented; the product, licence and deployment constraints are checked.
5. Column replication: the sync channel, the lag the business accepts, and who may update the replica
   are written down.

## Cross-service transaction review (`eventual-consistency-patterns.md`, `end-to-end-correctness.md`)

1. Each business transaction that used to be one database transaction has a stated new consistency
   model and maximum staleness window.
2. No handler writes to a database and a second system as two independent steps (dual write). If it
   does, there is an outbox-style row, CDC, or an accepted and documented divergence risk.
3. XA or two-phase commit across heterogeneous systems appears only with a justification and a
   recovery runbook for in-doubt transactions.
4. Background synchronisation is used only for closed systems; it never writes into another
   service's tables inside a microservice architecture.
5. Event-based flows have durable subscriptions, a dead letter queue with an alert, and idempotent
   handlers.

## Coordination review (`orchestration-vs-choreography.md`)

1. The workflow's steps, optional paths and error paths are listed.
2. The concern table (control, state query, error handling, scale, responsiveness) exists and the
   style choice follows it.
3. Orchestrator: one per workflow, no domain logic, redundancy or externalised state, and a scale
   limit that is acknowledged.
4. Choreography: each error scenario's extra message links are drawn; there is a way to answer "what
   state is request X in" (front controller, stamp coupling or query-all), and nobody relies on
   "the events will sort it out".

## Saga review (`saga-patterns.md`, `saga-state-and-compensation.md`)

1. The workflow is placed in the matrix: communication, consistency, coordination. The row's ratings
   match what the business needs for coupling, complexity, responsiveness and scale.
2. aao and aac designs are flagged; any "make it async for speed" change on an atomic flow is
   challenged.
3. Atomic consistency has been challenged with the business and the answer is written down.
4. A state table exists (start, transition states, actions, end), with error states, retries,
   escalation and a maximum duration.
5. Compensation is designed as a feature: side effects already propagated are listed; failure of the
   compensating action is handled; users are not blocked waiting for back-office steps.
6. Saga membership is discoverable (annotation, manifest, registry) and checked in CI.

## Contract review (`contracts.md`)

1. Each integration point is labelled strict or loose with a reason (co-change rate, consumer
   deployment speed, rate of change of the information).
2. No contract carries fields no consumer reads. Stamp coupling is justified by a standard document
   or by workflow state in choreography, and payload times peak rate is estimated.
3. Loose contracts have consumer-driven contract tests in the provider pipeline and a way to extend
   without breaking.
4. Strict contracts have a deprecation policy and a limit on supported versions.

## Analytical data review (`analytical-data.md`)

1. The chosen approach (warehouse, lake, mesh, or a simpler export) matches the architecture and the
   organisation's capacity, and the reason is written down.
2. Operational services have no synchronous dependency on the analytical side.
3. PII locations are known for lakes and data products; governance runs as code where a mesh is used.
4. Completeness checks per feed exist and the partial-data policy is explicit.

## Retries and idempotency review (`end-to-end-correctness.md`)

1. Every retried or redelivered operation has an idempotency key that is generated once by the
   originator and carried through every hop.
2. The final writer enforces it with a uniqueness constraint (or conditional put, or a seen-id state
   store) inside the same transaction as the effect.
3. Retries are capped, back off, and apply only to transient errors.
4. External side effects are idempotent or keyed by the same id.

## Decision-record review

1. Records the entangled dimensions that were weighed, not only the winner.
2. Lists what the choice gives up and the trigger for reconsidering it (for example "if scale
   requirements change").
3. Uses the ADR template from `arch-decisions-and-tradeoffs`.

## Signals to reconsider the whole design

- Services that always change and deploy together, or that share one database and one transaction,
  are probably one service (consolidation).
- A choreographed flow whose compensation events keep multiplying: move toward an orchestrator.
- An orchestrator that is growing domain logic: move that logic back to the services.
- Data replicated into many services "for performance" with no owner of the sync: stop and reassign
  ownership.
- Distributed transactions being added to fix inconsistencies that appeared after a split: check
  whether the split cut through a transactional boundary.
