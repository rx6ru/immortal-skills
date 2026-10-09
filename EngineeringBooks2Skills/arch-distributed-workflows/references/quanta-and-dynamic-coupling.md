# Quanta and the three dynamic-coupling dimensions

Read this when you need to say how coupled two services really are, count how many independently
operable units a system contains, or place a workflow in the communication / consistency /
coordination space before choosing a saga.

Contents: coupling and the quantum; counting quanta; static vs dynamic coupling; the three
dimensions; the eight combinations; how to use this in practice; verification.

## Coupling and why "decouple everything" is not advice

- Two parts are coupled if a change in one might force a change in the other (Hard Parts ch. 2).
- Fully decoupled parts cannot cooperate. Coupling is applied in a dose, deliberately; the question
  is always "which coupling, how much, for what benefit".
- Microservices made this harder because the bounded context pulls the database inside the service
  boundary. Transactionality stops being something a shared relational database quietly handles
  and becomes a first-class design concern.
- Three-step method for any tangled problem (ch. 2): (1) find what is entangled, (2) analyse how
  the parts are coupled, (3) assess the trade-off by the impact of change on interdependent parts.
  Untangle so each dimension can be reasoned about alone, then re-entangle and look at the whole.

## The architecture quantum

Definition (ch. 2): an independently deployable artifact with high functional cohesion, high static
coupling, and synchronous dynamic coupling. A well-formed microservice inside a workflow is the
typical example.

Three tests:

1. Independently deployable. A monolith is one deployable, so one quantum. A shared database that
   has its own deployment cadence defeats independence unless everything deploys in lock step, so
   many "multi-service" systems are a single quantum.
2. High functional cohesion. Related behaviour and data of one domain or workflow (this overlaps the
   DDD bounded context). A giant monolith is deployable alone but not cohesive.
3. High static coupling inside the boundary, with synchronous dynamic coupling between its parts.

Why it matters: the quantum is the scope within which operational characteristics (scale,
elasticity, reliability, performance) are set. Two services in one quantum cannot have genuinely
independent scalability or availability.

## Counting quanta in a topology

1. List every deployable and every operational dependency: database, broker, orchestrator or
   mediator, UI, auth service, OS or runtime.
2. A dependency shared by services and needed for them to run is a coupling point that merges them
   into one quantum, transitively (a service that relies on a service that touches the shared
   database is in the set).
3. Count the disjoint sets, each of which could be bootstrapped alone in a production-like
   environment ("runs and operates", even if it cannot join every workflow).

Typical results:

| Topology | Quanta | Reason |
|---|---|---|
| Layered, modular monolith, microkernel | 1 | one deployable, one database |
| Service-based (separate UI, coarse services, one database) | 1 | single database |
| Event-driven with a mediator | 1 | shared database and request orchestrator |
| Broker-style event-driven with one shared relational database | 1 | shared database even without a mediator |
| Event-driven with two disjoint data stores and no static links between the sets | 2 | |
| Microservices that each own their data | up to one per service | each can have its own characteristics |
| Microservices behind a tightly coupled UI | 1 | UI breaks if any back end is down, so per-service tuning is lost |
| Two systems sharing a database | 1 | |

Fix for the coupled UI: asynchronous UI decoupling, or micro-frontends where each service emits its
own UI component onto a canvas and they communicate by events; a service plus its micro-frontend
forms one quantum.

Use the static quantum diagram of a legacy system to see what a change touches (test scope, risk)
and where decoupling is possible.

## Static vs dynamic coupling

- Static coupling: how dependencies resolve to bootstrap and operate the quantum: OS, frameworks
  and libraries (including transitive ones), database, message broker, container orchestration,
  contracts, any operational requirement. Test question: "is this needed to start this service?"
  The presence of a broker is static; calling another service through it is dynamic.
- Dynamic coupling: how quanta communicate at runtime during a workflow. Fitness functions here are
  continuous and monitor-based.
- Quanta can be coupled temporarily by the nature of a call. Example from the notes: Ticketing runs
  at ten times the elastic scale of Assignment; a synchronous call makes the workflow bog down at
  the slower service, an asynchronous call with a queue as buffer lets each scale independently.
  (Scalability is many concurrent users; elasticity is bursts in a short time.)

## The three dimensions of dynamic coupling

| Dimension | Values | What it governs |
|---|---|---|
| Communication | synchronous (caller blocks until response) or asynchronous (post to a queue, get an ack, continue; optional reply queue) | synchronisation, error handling, transactionality, scale, performance |
| Consistency | atomic (all or nothing) through the eventual-consistency spectrum | whether cross-service updates must all succeed together |
| Coordination | orchestration (a coordinator) or choreography (none) | where workflow logic, state and error handling live |

The dimensions pull on each other. Transactionality is easier with synchronous calls plus a
mediator; high scale is easier with eventual consistency plus asynchrony plus choreography.
Improving one in isolation (for example adding asynchrony for speed) changes the others. That is
the whole reason the saga catalogue is a matrix and not a menu.

Contracts are a fourth, cross-cutting dimension (ch. 13, see `contracts.md`).

## The eight combinations (saga names, detail in `saga-patterns.md`)

| Pattern | Communication | Consistency | Coordination | Coupling |
|---|---|---|---|---|
| Epic | sync | atomic | orchestrated | Very high |
| Phone Tag | sync | atomic | choreographed | High |
| Fairy Tale | sync | eventual | orchestrated | High |
| Time Travel | sync | eventual | choreographed | Medium |
| Fantasy Fiction | async | atomic | orchestrated | High |
| Horror Story | async | atomic | choreographed | Medium |
| Parallel | async | eventual | orchestrated | Low |
| Anthology | async | eventual | choreographed | Very low |

Reading rule: coupling falls as you move toward asynchronous, eventual and choreographed, and the
price is complexity of coordination and consistency handling.

## Using it in practice

- Counting quanta before a split: if the plan produces services that all share one database, you
  have one quantum with network calls added. Say so to the user; the scaling and availability
  benefits they expect will not appear.
- Before choosing a communication style: write down, for the one workflow, its position on all
  three axes, then look it up in the table above.
- Analytical side-channels (data products) are quanta of their own, coupled statically to their
  service and kept asynchronous and eventual (see `analytical-data.md`).

## Verify

- Boot test (inferred in the notes): start each candidate service with only its declared
  dependencies. If it cannot start, a hidden static coupling exists.
- Keep an automated dependency inventory: build-time dependencies (manifests, container files,
  package locks) for static coupling, and a runtime call graph from tracing for dynamic coupling.
  The notes describe a platform team doing exactly this to answer "if I change this, what must be
  tested".
- Draw the quantum count in the design document and name the shared element that merges any two
  services you claim are independent.
