# The eight transactional saga patterns

Read this when a workflow crosses services and you must pick (or review) how its transactions,
calls and coordination behave: "should this be a saga", "we made it async to speed it up", "which
saga pattern", "why is our distributed workflow so hard to debug".

Contents: what "saga" means here; the matrix; ratings table; per-pattern entries (Epic, Phone Tag,
Fairy Tale, Time Travel, Fantasy Fiction, Horror Story, Parallel, Anthology); selection
procedure; common mistakes; verify.

## What the term covers

Original idea (1987): limit database lock scope. The microservice usage (Richardson): a sequence of
local transactions, each publishing an event that triggers the next, with compensating updates on
failure. The book treats that as one of eight possible sagas (Hard Parts ch. 12). Because
distributed transactions lack atomicity (see `eventual-consistency-patterns.md`), the interesting
part is what happens on error.

## The matrix

Three binary dimensions: communication (synchronous or asynchronous), consistency (atomic or
eventual), coordination (orchestrated or choreographed). The names are mnemonics; the letters carry
the meaning (a for atomic, e for eventual, s for sync, a for async, o for orchestrated, c for
choreographed, written communication-consistency-coordination).

| Pattern | Letters | Communication | Consistency | Coordination |
|---|---|---|---|---|
| Epic Saga | sao | synchronous | atomic | orchestrated |
| Phone Tag Saga | sac | synchronous | atomic | choreographed |
| Fairy Tale Saga | seo | synchronous | eventual | orchestrated |
| Time Travel Saga | sec | synchronous | eventual | choreographed |
| Fantasy Fiction Saga | aao | asynchronous | atomic | orchestrated |
| Horror Story | aac | asynchronous | atomic | choreographed |
| Parallel Saga | aeo | asynchronous | eventual | orchestrated |
| Anthology Saga | aec | asynchronous | eventual | choreographed |

Key principle: the dimensions are entangled. Fixing one in isolation, for example adding
asynchrony for performance, interacts with the other two. Evaluate all three together.

## Ratings

| Pattern | Coupling | Complexity | Responsiveness / availability | Scale / elasticity |
|---|---|---|---|---|
| Epic (sao) | Very high | Low | Low | Very low |
| Phone Tag (sac) | High | High | Low | Low |
| Fairy Tale (seo) | High | Very low | Medium | High |
| Time Travel (sec) | Medium | Low | Medium | High |
| Fantasy Fiction (aao) | High | High | Low | Low |
| Horror Story (aac) | Medium | Very high | Low | Medium |
| Parallel (aeo) | Low | Low | High | High |
| Anthology (aec) | Very low | High | High | Very high |

Notes on the table: the prose on Fantasy Fiction says "extremely high" coupling while its table
says High (an inconsistency in the early-release text); treat it as high to very high. Epic's low
complexity comes from synchronous calls avoiding race conditions and deadlocks, even though its
error handling is hard.

## Pattern entries

### Epic Saga (sao)

- Shape: orchestrator calls services synchronously; all succeed or all revert. A monolith would be
  the origin of the 3-D space (0,0,0); this is the closest distributed imitation.
- Mechanics: typically compensating transactions, where a compensating update reverses another
  service's write (undo an update, re-insert a deleted row, delete an inserted row). The mediator
  watches for success and on a late failure asks earlier services to undo.
- Use when: atomic consistency is a hard business requirement and the workflow is simple.
  Consider consolidating the services into one so a single ACID transaction does the work.
- Do not use when: you need scale or elasticity (the mediator must confirm everyone), or the flow
  has many failure modes.
- Costs: orchestration plus transactionality hurts performance, scale and elasticity. Many
  architects default to it because stakeholders insist state changes synchronise regardless of
  technical constraints. Choosing a pattern because it is familiar or named creates accidental
  complexity; a pattern is recognition of commonality, not proof it is solvable.
- Neighbours: Parallel and Fairy Tale relax consistency; Phone Tag removes the mediator.

### Phone Tag Saga (sac)

- Shape: Epic without the mediator. The first-called service acts as the coordination point (a
  front controller); each service holds logic to send compensating requests back along the chain.
- Behaviour: the happy path can beat Epic (the last service can return the result, fewer choke
  points); the error path is slower and couples services as the call chain unwinds. Slightly better
  scale than Epic. Complexity rises linearly with workflow semantic complexity; for complex flows
  the front controller becomes as complex as a mediator. Stamp coupling can carry workflow state.
- Why it exists: synchronous calls guarantee each service finishes before the next, removing race
  conditions, which suits simple workflows with easy-to-resolve errors or idempotent, retryable
  services.
- Use when: simple workflow, few error paths, a bit more scale needed than Epic. Rare combination.

### Fairy Tale Saga (seo)

- Shape: synchronous, eventually consistent, orchestrated. The mediator coordinates request,
  response and errors but not transactions; each domain service owns its own transaction. The
  mediator can still manage compensating calls, but not inside an active transaction. If a service
  is down, a change can be held until it returns.
- Why it is popular: easy moving parts (a mediator, synchronous calls) with the loosest consistency
  restriction. Coupling is high (two of three dimensions are tight) but transactionality, the
  worst driver of coupling, is gone. Complexity very low. The mediator holds less time-sensitive
  state, so load balancing is better.
- Use when: eventual consistency is acceptable and you want a synchronous orchestrated flow. Balanced
  and popular for microservice workflows once atomicity is challenged.

### Time Travel Saga (sec)

- Shape: eventual, synchronous, choreographed. No mediator; each service owns its transaction,
  does its work and forwards it, like Chain of Responsibility or Pipes and Filters (a one-way series
  of steps). "Time travel" because everything is temporally decoupled and consistency arrives
  gradually.
- Use when: fire-and-forget, high-throughput one-way workflows such as data ingestion or bulk
  transactions. A good on-ramp to Anthology: synchronous is easier to reason about, implement and
  debug; if scale suffices, stop here.
- Do not use when: the workflow is complex. Each service must carry workflow state and handle
  errors, and synchronous calls make error handling slow. Needs extra effort to synchronise data.

### Fantasy Fiction Saga (aao)

- Shape: Epic made asynchronous. Transaction coordination with asynchrony is hard: the mediator
  tracks many pending transactions (Alpha pending, Beta starts, Gamma depends on Alpha's outcome),
  loses serial ordering and gains deadlocks and race conditions. Coupling and complexity high;
  responsiveness low and terrible if a service is down; high scale is virtually impossible in
  transactional systems.
- It exists mostly through the mistaken attempt to speed up Epic while keeping transactions. Use
  Parallel (aeo) instead.

### Horror Story (aac)

- Shape: asynchronous, atomic, choreographed: the strictest consistency with the loosest
  communication and coordination. Without a mediator each service must track undo information for
  several pending transactions, possibly out of order, and coordinate with its peers on errors
  (Alpha fails while Beta is pending, so undo must run in reverse order of firing, perhaps out of
  order). Coupling medium, complexity the worst (very high), responsiveness low from
  inter-service chatter, scale medium.
- Typical origin: an architect starts at Epic, finds it slow, then applies asynchrony and
  choreography as performance fixes, ignoring the entanglement. Fix: move to Anthology by dropping
  holistic transactionality. Flag any design landing here as a defect to resolve.

### Parallel Saga (aeo)

- Shape: Epic with two restrictions relaxed (asynchronous, eventual). A mediator for complex
  workflows; each service owns its transactional context; the mediator coordinates request and
  response and, on error, sends asynchronous compensating messages that may involve retries and
  data synchronisation. The burden of errors falls on the mediator; asynchrony brings race
  conditions, deadlocks and queue reliability issues.
- Ratings: coupling low (transaction coupling is confined to each service), complexity low, scale
  high (domain-level isolation lets, for example, public-facing services scale while back-office
  services prioritise security), responsiveness high; supports different performance footprints per
  service.
- Use when: a complex workflow needs high scale. The best generic replacement for Epic and Fantasy
  Fiction.

### Anthology Saga (aec)

- Shape: the opposite extreme of Epic. Message queues; each service keeps transactional integrity;
  no mediator, so services carry workflow context, error handling and coordination. Lowest
  coupling, highest scale, high responsiveness. Complexity is high for complex workflows and
  coordinating data-consistency errors is hard, prohibitive for complex or critical workflows.
  Stamp coupling can carry workflow state.
- Use when: simple, mostly linear, high-throughput flows. Pipes and Filters fits exactly.

## Selection procedure

1. Challenge atomicity. Does the business really need all-or-nothing across these services? In the
   ticket example the expert should not care whether the survey email was sent. If not required,
   choose among the eventual patterns (seo, sec, aeo, aec).
2. Judge complexity. Many optional or error paths, need to query state or recover: orchestrated
   (seo or aeo). Simple linear flow with high throughput: choreographed (sec or aec).
3. Judge the need for parallelism, responsiveness and scale. If needed: asynchronous (aeo, aec). If
   synchronous is adequate and simpler to debug: start there (sec, seo).
4. If atomicity is a hard requirement: choose Epic (sao) knowingly, for simple flows, and weigh
   consolidating the services into one so a single ACID transaction does the job. Avoid aao and aac.
5. Check the pick against the ratings table and record the entangled trade-offs in an ADR (template
   in `arch-decisions-and-tradeoffs`).

Quick map:

| Need | Start with |
|---|---|
| Eventual is fine, complex flow, want simplicity | Fairy Tale (seo) |
| Eventual is fine, complex flow, need scale | Parallel (aeo) |
| Eventual is fine, simple one-way flow, easy debugging | Time Travel (sec) |
| Eventual is fine, simple one-way flow, maximum throughput | Anthology (aec) |
| Atomic is mandatory, simple flow | Epic (sao), or merge the services |

## Common mistakes

- Choosing the pattern by name or familiarity (everyone knows the Epic saga).
- Adding asynchrony and choreography to an atomic flow to make it faster (this produces Horror
  Story).
- Assuming compensation always works (see `saga-state-and-compensation.md`).
- Treating "saga" as a library you drop in. Sagas are designed, coded and maintained; there is no
  transaction manager for them.
- Letting the end user be semantically coupled to a back-office step (the expert waiting on the
  survey).

## Verify

- For each cross-service workflow record its three dimensions and its rating row; reject or
  explicitly justify any aao or aac design.
- Compensation tests: force failure of each step, force failure of the compensating action itself,
  and inspect side effects already propagated downstream (analytics already consumed the data).
- Idempotency tests for retries; interleaving tests for asynchronous patterns (Alpha, Beta, Gamma
  arriving in each order).
- Registry check: every service that takes part in a saga declares it (see the annotation technique
  in `saga-state-and-compensation.md`), and the declarations match the architecture documents.
