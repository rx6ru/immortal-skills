# Orchestration vs choreography

Read this when you must decide how a multi-service workflow is coordinated, when someone argues
"choreography because it is the most decoupled" or "orchestration because it is simpler", or when
you inherit a choreographed flow whose error handling is spread across services.

Contents: definitions; orchestration (example, advantages, disadvantages); choreography (example,
advantages, disadvantages); semantic vs implementation coupling; workflow state in choreography
(three options); choosing; worked decision; verify.

## Principle first

Never reach for an absolute. The decision is a trade-off analysis per workflow, not a house style
(Hard Parts ch. 11). Coordination is the third dynamic-coupling dimension (see
`quanta-and-dynamic-coupling.md`); it is entangled with communication and consistency, which the
saga catalogue in `saga-patterns.md` handles together.

## Orchestration

- An orchestrator (mediator) owns workflow state, optional behaviour, error handling and
  notification. It holds no domain behaviour beyond the workflow it mediates; domain services keep
  their bounded context, data and behaviour.
- In microservices use one orchestrator per workflow, never a global one. A global orchestrator
  behaves like an enterprise service bus: an undesirable coupling point.
- Example (electronics retailer): Order Placement Orchestrator makes a synchronous call to Order
  Placement (records the order), a synchronous call to Payment, an asynchronous call to Fulfillment
  (no strict timing need; it batches a few times a day), and an asynchronous call to Email. Use
  asynchronous where the result does not gate progress, synchronous where it does.
- Error scenario 1, payment rejected: the orchestrator tells Email (async) and updates the order
  state in Order Placement. Error scenario 2, backorder after payment: the orchestrator refunds the
  payment and updates order state. Observation: even elaborate error paths add no communication
  links beyond those the happy path already uses.

| Advantages | Disadvantages |
|---|---|
| Centralised workflow: one place for state and behaviour as complexity grows | Responsiveness: everything flows through the mediator, a possible bottleneck |
| Error handling: the state owner can decide | Fault tolerance: single point of failure for the workflow; redundancy adds complexity |
| Recoverability: can retry on short outages | Scalability: more coordination points, less parallelism |
| State management: workflow state is queryable | Service coupling: the orchestrator couples to domain components |

## Choreography

- No central coordinator. Each service takes part like a dance partner; the architect plans the
  moves in advance but nothing coordinates at runtime.
- Example: the request reaches Order Placement, which sends an async message to Payment, which
  messages Fulfillment, which messages Email. It looks simpler (fewer services, a chain of
  messages), but the difficulty sits in boundary and error conditions.
- Error 1, payment fails: Payment sends failure messages to Email and back to Order Placement; one
  new link. Error 2, backorder after several steps: each service has its own transaction, so
  Fulfillment must broadcast compensating events that Email, Payment and Order Placement subscribe
  to. Every error scenario adds communication links the happy path did not have.

| Advantages | Disadvantages |
|---|---|
| Responsiveness: fewer choke points, more parallelism | Distributed workflow: no owner, boundary conditions are harder |
| Scalability: no coordination points | State management: no central state holder |
| Fault tolerance: no single mediator, multiple instances | Error handling: domain services need workflow knowledge |
| Service decoupling: no mediator | Recoverability: nobody to retry or remediate |

## Semantic coupling vs implementation coupling

- Semantic coupling is inherent in the problem (assigning a ticket must match skills, then
  schedules and locations). Implementation coupling is how you model it. An architect cannot reduce
  semantic coupling by implementation but can make it worse.
- More workflow steps mean more potential error and optional paths, which means more need for
  coordination. Complexity of the workflow does not disappear when you remove the orchestrator; it
  moves into the services.
- Related lesson on partitioning: a workflow smeared across technical layers is harder than one in
  a domain-partitioned component. Model the workflow semantics as closely as possible in the
  implementation. Technical partitioning can still be justified (for example connection pooling
  cost) but adds complexity.

## Workflow state in choreography: three options

| Option | How | Advantages | Disadvantages |
|---|---|---|---|
| Front controller | The first service in the chain keeps workflow state in addition to its domain work; others call back to update or query | A pseudo mediator inside choreography; querying order state is trivial | Adds workflow state to a domain service; more communication; chatter hurts performance and scale |
| Stateless choreography | Keep no transient workflow state; rebuild a snapshot by querying each service on demand | High performance and scale; extremely decoupled | State is built on the fly; complexity grows quickly with complex workflows |
| Stamp coupling | Put workflow state in the message contract; each service updates its part and passes it on | Services pass state without querying a state owner; no front controller | Larger contracts; no just-in-time status queries; still no single place to ask |

For orchestration the orchestrator is the state owner (some designs use stateless orchestrators for
higher scale, with state externalised). Stamp coupling is expanded in `contracts.md`.

## Choosing

- Choreography fits workflows that need responsiveness and scale and have simple error scenarios or
  rare errors. It is the style of the Phone Tag, Time Travel and Anthology sagas, and can degrade
  into the Horror Story when other forces are mixed in.
- Orchestration fits complex workflows with boundary and error conditions; it costs scale and saves
  a great deal of complexity. It is the style of the Epic, Fairy Tale, Fantasy Fiction and Parallel
  sagas.
- As semantic complexity rises, the value of an orchestrator rises proportionally. Low complexity,
  high scale and rare errors point to choreography.

Procedure:

1. List the workflow's steps, optional paths and error paths.
2. List the quality concerns the business raised (control, state query, error handling, scale,
   responsiveness).
3. For each concern mark which style serves it, both, or neither. It is not zero-sum: state query
   can be done by an orchestrator, by querying services, or by stamp coupling.
4. Pick, record consequences, and set triggers for reconsidering (for example "if scale
   requirements change").

Counting guide (inferred): if a workflow has more than one or two error paths, or needs
compensation, choreography needs an explicit justification.

## Worked decision (ticket workflow)

Workflow: customer submits a ticket (gets a number); Ticket Assignment finds an expert; the ticket
is routed to the expert's mobile; Notification tells the customer an expert is coming; the expert
completes it; Ticket Management tells Survey to survey the customer. One architect favoured
choreography, the other orchestration; both were modelled and neither won on its own. The concern
table settled it:

| Concern | Better style |
|---|---|
| Lost or misrouted tickets (top business priority): workflow control | Orchestration |
| Query ticket status at any time | Both (orchestrator queries state; choreography queries services or uses stamp coupling) |
| Cancellations and reassignments (expert availability, lost mobile connection, delays): error handling | Orchestration; choreography scores poorly |

Complex workflows must live somewhere: in an orchestrator or scattered through services. Decision:
orchestration for the primary ticket workflow, with the consequence that a single orchestrator may
limit scale; reconsider if scalability requirements change.

## Verify

- Document every error and optional path per workflow and, for choreography, the extra links each
  one adds. Look for cyclic service-to-service dependencies.
- Confirm the orchestrator is per workflow, contains no domain logic, and has a high-availability
  and scale plan (redundant instances, possibly stateless with externalised state).
- An operator can answer "where is request X and what is its state?" for any in-flight request,
  within a stated time. If the answer needs reading several services' logs, the design lacks a state
  owner.
- Kill the orchestrator mid-workflow in a test environment and confirm in-flight workflows resume
  or are detectably stuck. For choreography, drop one message and confirm something notices.
