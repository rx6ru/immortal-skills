# Coupling and the architecture quantum

How to reason about what is coupled to what, how to count independently deployable units, and how
the three dynamic coupling dimensions interact. Source: Hard Parts ch. 1, ch. 2, ch. 15; one
vocabulary item from Mastering API Architecture intro.

## Contents

1. Coupling: definition and stance
2. Static and dynamic coupling
3. The architecture quantum
4. Procedure: count quanta
5. Quantum count by style
6. The static coupling diagram
7. Dynamic coupling: three dimensions
8. The eight combinations
9. Using coupling analysis in a decision
10. Fixed vocabulary
11. Verify

## 1. Coupling: definition and stance

- Two parts are coupled if a change in one might cause a change in the other (Hard Parts ch. 1,
  ch. 2). The working probe: "if someone changes X, could Y have to change?"
- "Decouple everything" is not usable advice. Parts that are fully decoupled cannot communicate.
  Coupling is neither good nor bad; the amount and the place are design choices to be made on
  purpose.
- Why this became harder with fine-grained services: when each service owns its database, data
  ownership and transactionality become architecture concerns. Earlier distributed systems could
  let many handlers share one relational database, which took care of integrity.
- The recurring question is how big parts should be and how they should communicate. Too small
  brings transaction and orchestration problems; too large brings scale and distribution problems.

## 2. Static and dynamic coupling

| | Static coupling | Dynamic coupling |
|---|---|---|
| Meaning | How parts are wired: what a part needs in order to start and operate | How parts call each other at run time |
| Includes | Operating system, frameworks and libraries through transitive dependencies, database or other data store, message broker, container orchestration, any operational requirement; contracts in the wide sense, including method signatures and addresses | Kind of communication, information passed, strictness of contracts |
| Question to ask | Is this dependency necessary to bootstrap this service? | Does this workflow need the other part to respond now? |
| Measurable | At build time; from manifests and dependency files | Continuously; from monitors, traces, call graphs |
| Short form | Operational dependencies | Communication dependencies |

Example: a service's own database is static coupling. Calling another service partway through a
workflow is dynamic coupling. The presence of a broker the service needs in order to run is static;
sending a message to another service through that broker is dynamic. Two services can be statically
independent while dynamically coupled inside one workflow.

## 3. The architecture quantum

Definition (Hard Parts ch. 2): an independently deployable artifact with high functional cohesion,
high static coupling and synchronous dynamic coupling. A well-formed microservice within a workflow
is the typical example.

Three tests:

1. **Independently deployable.** A monolith is one deployable and therefore one quantum. The test
   pulls shared coupling points such as databases and user interfaces inside the boundary. A shared
   database with its own release cadence defeats independent deployability unless everything is
   deployed in lock step, which is why many systems drawn as several services are one quantum.
2. **High functional cohesion.** Related behaviour and data of one domain or workflow, overlapping
   with the bounded context idea from domain-driven design. A large monolith deploys alone but is
   not cohesive, and the larger it grows the less cohesive it is.
3. **High static coupling, synchronous dynamic coupling.** The elements inside are tightly wired
   through contracts. Parts joined by synchronous calls behave, for that workflow, as one unit.

Why it matters for decisions:

- It gives architects, developers and operations one word for scope.
- It is the scope of architecture characteristics. Performance, scale, elasticity and reliability
  are set per quantum, so two parts in one quantum cannot have independent targets.
- It is a risk map: what is inside the quantum of a changed part is what has to be retested.

The quantum resembles a bounded context expressed in architectural terms, with the coupling types
added.

## 4. Procedure: count quanta

Hard Parts ch. 2.

1. List every deployable and every operational dependency: database, broker, orchestrator or
   mediator, user interface, authentication, operating system or runtime.
2. Any dependency that several services share and need in order to run is a coupling point that
   merges them into one quantum. Apply this transitively: services that rely on services that touch
   the shared database are included.
3. Count the disjoint sets that could each be bootstrapped alone in a production-like environment.
   The standard is that the set runs and operates, even if it cannot take part in every workflow.

Agent adaptation, where to find the inputs in a repository:

- deployables: container build files, deployment manifests, CI deploy jobs, process definitions;
- static dependencies: package manifests and lock files, database connection configuration,
  environment variable lists, compose or orchestration files showing shared services;
- shared stores: two deployables whose configuration points at the same database or schema;
- dynamic coupling: HTTP or RPC client usage, queue producers and consumers, tracing data if
  available.

State which of these were read and which were inferred.

## 5. Quantum count by style

Hard Parts ch. 2.

| Topology | Quanta | Reason |
|---|---|---|
| Monolithic styles: layered, modular monolith, microkernel | 1 | One deployable, one database |
| Service-based: separately deployed UI, coarse domain services, one database | 1 | The single database |
| Mediator-style event-driven | 1 | Shared database and the request orchestrator |
| Broker-style event-driven with one shared relational database | 1 | The database, even without a mediator |
| Event-driven with two disjoint data stores and no static dependencies between the sets | 2 | Two sets can each boot alone |
| Microservices, each with its own data | One per service possible | Each can carry its own characteristics |
| Microservices behind a tightly coupled UI | 1 | The UI breaks if any back-end part is down, so characteristics cannot be tuned per service, especially with synchronous calls |
| Two systems sharing a database | 1 | The database |

Remedy for the coupled UI case: decouple the UI asynchronously, or use micro-frontends in which each
service supplies its own UI component onto a shared canvas and components communicate by events.
Service plus its micro-frontend is then one quantum.

Service-based architecture with one database is a common intermediate step when decomposing a
monolith; see `arch-decomposition`.

## 6. The static coupling diagram

Purpose: for an existing system, show what a change touches (risk, test scope) and where decoupling
would have to happen (Hard Parts ch. 2, ch. 15).

What to gather per service or quantum:

- operating system and container dependencies;
- transitive dependencies through frameworks and libraries;
- persistence dependencies: databases, search engines, cloud environments;
- architecture integration points required to bootstrap;
- messaging infrastructure needed to communicate with other quanta.

Exclude other quanta whose only link is workflow communication; that is dynamic coupling and goes on
a different view.

There is no generic tool; build it by hand or from automation. Teams with automated environment
builds can emit the coupling documentation during the build. The case study's platform team derived
the static side from container manifests and dependency files, and the dynamic side from
observability logs assembled into a call graph, and used both to answer "if I change this, what must
be tested?"

Example static coupling of one service in the case study: language runtime, application framework,
fifteen to twenty libraries, a relational database, a container runtime, and the event broker.

## 7. Dynamic coupling: three dimensions

Hard Parts ch. 2.

| Dimension | Poles | Affects |
|---|---|---|
| Communication | Synchronous (caller blocks until the response) or asynchronous (post to a queue, get an acknowledgement, continue; optional reply channel) | Synchronisation, error handling, transactionality, scalability, performance |
| Consistency | Atomic (all or nothing) or somewhere on the eventual-consistency spectrum | Cross-service transactions are among the hardest problems; the general advice is to avoid them |
| Coordination | Orchestrated (a coordinator exists) or choreographed (none); a single-service reply needs neither | More complex workflows need more coordination |

The three pull on each other: transactionality is easier with synchronous communication and a
coordinator; higher scale is reachable with eventual consistency, asynchronous communication and
choreography.

A queue between two services is often omitted from diagrams as shorthand; when reading a diagram,
confirm whether an arrow is a blocking call.

Worked point from the case study: a ticketing service ran at ten times the elastic scale of an
assignment service. With a synchronous call, the workflow slowed to the pace of the slower service.
With an asynchronous call and a queue as buffer, each scaled on its own. Quanta can therefore be
coupled temporarily by the nature of a call.

## 8. The eight combinations

Hard Parts ch. 2, Table 2-1. The names are the book's saga pattern names.

| Pattern | Communication | Consistency | Coordination | Coupling |
|---|---|---|---|---|
| Epic Saga | synchronous | atomic | centralised | Very high |
| Phone Tag Saga | synchronous | atomic | distributed | High |
| Fairy Tale Saga | synchronous | eventual | centralised | High |
| Time Travel Saga | synchronous | eventual | distributed | Medium |
| Fantasy Fiction Story | asynchronous | atomic | centralised | High |
| Horror Story | asynchronous | atomic | distributed | Medium |
| Parallel Saga | asynchronous | eventual | centralised | Low |
| Anthology Saga | asynchronous | eventual | distributed | Very low |

Reading rule: coupling falls toward asynchronous, eventual and distributed, and the price is more
complexity in coordination and consistency. From the consolidated comparison (Hard Parts ch. 15):
coupling and scale/elasticity are directly inversely related; coupling and
responsiveness/availability are inversely related less directly.

This table is here as the worked instance of "find the dimensions, then tabulate the combinations".
For choosing among the eight, per-pattern ratings, state machines and compensation, use
`arch-distributed-workflows`.

Notes on wording: row five is named "Fantasy Fiction Story" in the source notes for ch. 2 and is
kept as recorded; one ch. 15 table says "centralised" where
ch. 12 says "orchestrated", and they mean the same pole.

## 9. Using coupling analysis in a decision

- **Blast radius.** Before a change, name the quantum it sits in; everything in that quantum is in
  the test and deployment scope.
- **Independence claims.** When a proposal says a part can scale, fail or deploy on its own, check
  the quantum count. A shared database or a synchronous dependency falsifies the claim.
- **Where to cut.** The coupling points that merge quanta (shared database, shared UI, synchronous
  chains) are the places a decomposition has to address first.
- **Cost of a split.** Splitting a quantum converts some static coupling into dynamic coupling, and
  with it brings the communication, consistency and coordination choices above. Remodelling an
  in-process interface as an out-of-process one adds latency, failure modes and versioning concerns
  (Mastering API Architecture intro).
- **Traffic vocabulary** (Mastering API Architecture intro): north-south traffic is ingress from
  external clients; east-west traffic is service to service inside the system. Extracting a service
  usually adds an east-west flow that did not exist; name it in the ADR consequences.

## 10. Fixed vocabulary

Definitions the source deliberately keeps simple (Hard Parts ch. 1). Use them consistently in ADRs.

| Term | Meaning |
|---|---|
| Service | A cohesive collection of functionality deployed as an independent executable |
| Coupling | Two artifacts are coupled if a change in one might require a change in the other |
| Component | A building block doing a business or infrastructure function; appears as a package, namespace or directory |
| Synchronous | The caller waits for the response before proceeding |
| Asynchronous | The caller does not wait; it may be notified through another channel |
| Orchestrated | A service exists whose main job is coordinating the workflow |
| Choreographed | No orchestrator; services share coordination |
| Atomic | The parts of a workflow keep a consistent state at all times; the opposite is the eventual-consistency spectrum |
| Contract | Any interface between two software parts: method calls, remote calls, dependencies |

## 11. Verify

- Quantum count: try to start each candidate unit in isolation with only its declared dependencies
  (marked inferred in the notes). In practice, bring it up alone in a local or CI environment and
  run its health check; record what else had to be present.
- No two units claimed to be separate quanta share a database, schema or required runtime component.
  Check configuration, not the diagram.
- A dependency inventory exists and is regenerated automatically: build dependencies for the static
  side, a runtime call graph for the dynamic side. This inventory is itself a fitness function (see
  `fitness-functions.md`).
- Every arrow on a diagram used in the decision is labelled synchronous or asynchronous.
- Where different operational targets are stated for two parts, the parts are in different quanta
  and are not joined by a synchronous call on the relevant path.
