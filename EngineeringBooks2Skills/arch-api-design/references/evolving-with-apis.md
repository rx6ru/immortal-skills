# Evolving a legacy system behind APIs

Contents: 1. Why APIs as the leverage point; 2. Pick an end state; 3. Goals and fitness functions; 4. Modules, seams and leverage points; 5. Patterns (strangler fig, facade, adapter, layer cake); 6. Finding pain points; 7. Breaking dependencies; 8. Reference sequence of steps; 9. Organisation and decision types; 10. Verify

Sources: Mastering API Architecture (MAA) ch. 8, ch. 10, ch. 0, ch. 3, ch. 5; Architecture: The Hard Parts ch. 13. Detailed decomposition and database-splitting methods are in `arch-decomposition`.

## 1. Why APIs are the leverage point

Successful systems must evolve. Changing software is hard when it has many users, inherent complexity or tight integration, and well-adopted systems have all three. An API is a module boundary and therefore a natural place for high cohesion and loose coupling.

- Cohesion: how much the elements inside a unit belong together. High cohesion lets the provider change internals (algorithms, datastore) as long as the external interface stays backward compatible. Beware designing a space-shuttle control panel for a car-sized business need in the name of future-proofing. A shared "utils" API across entities is the counter-example: a change in one entity's code forces a change to it and risks silent inconsistency.
- Loose coupling: a change in one component does not affect another's function or performance, and each knows little of the other's definitions. A loosely coupled API is easy to mock or virtualise in integration and end-to-end tests; a tightly coupled one forces the real provider or an embedded version into the tests.
- Information hiding: isolate the decisions most likely to change behind a stable interface. Expose only business- and domain-focused endpoints; never leak internal abstractions, the implementation data model or the schema. If the Attendee service exposed its datastore schema, swapping the datastore would need error-prone translation code or force every consumer to change.
- Expose as little as possible from a module or service boundary: hiding now lets you share later, the reverse is hard.

## 2. Pick an end state explicitly

| Option | Notes |
|---|---|
| Monolith | Not inherently bad. Fastest at the start (proof of concept, finding product-market fit). Risk: accidental coupling visible late; mitigate with domain-driven design and possibly hexagonal architecture |
| SOA | Classic SOA used heavyweight technology (SOAP, WSDL, XML, vendor ESBs with business logic in smart pipes). Avoid middleware promoting high coupling and low cohesion; never put business logic in a gateway or ESB. Hardest part is the right size and ownership of services |
| Microservices | Small independent services, smart endpoints and dumb pipes. Boundaries are the main challenge: use domain-driven context mapping and event storming first; use lightweight technology (REST, gRPC, AMQP, STOMP, WebSockets) |
| Functions | Good for highly event-driven systems (trading reacting to events, image-processing pipelines). Risk: functions too simplistic, so many must be orchestrated, which couples them; reusability versus maintainability; team adjustment time |

Without a destination any road works; write the target down. Do not do everything up front: extract services and add a gateway or mesh only when the need shows itself (MAA ch. 0).

## 3. Goals and fitness functions

Catalogue and communicate the motivation; wrong assumptions are cheaper to find before coding.
- Functional goals: features and integrations, driven by users and the business.
- Cross-functional goals (the "-ilities"): maintainability (tech leadership), scalability (forecasted demand), reliability (fewer, smaller failures); mostly refactoring or a new platform.
Without shared goals and constraints a migration becomes open-ended and drains resources and morale.

A fitness function is a unit- or integration-test-like quantified check on an architectural quality, run in the build pipeline (MAA Table 8-1):

| Category | Example |
|---|---|
| Code quality | Tests; minimise cyclomatic complexity |
| Resiliency | Deploy to pre-production, run synthetic traffic, keep the error rate under a threshold; use gateway or mesh fault injection to test availability scenarios |
| Observability | Services must publish required metrics and not regress |
| Performance | Latency and throughput targets measured in the pipeline; production-like data is the hard part |
| Compliance | Organisation-specific audit and data evidence |
| Security | Dependency scans for known vulnerabilities; automated scans for OWASP-style issues |
| Operability | Minimum operating requirements, for example monitoring and alerting exist |

Write an ADR for each fitness function you introduce (you may not manage all at once). Irreversible decisions are fine if made with care. Catalogue and ADR template: `arch-decisions-and-tradeoffs`.

## 4. Modules, seams and leverage points

- Many "monolith" problems are really missing code organisation. The author's example is a 4-million-line codebase with 24 years of technical debt and ad hoc coupling. Modules (an architectural partition larger than a method, class or package) give well-defined boundaries that hide implementation.
- Case-study layering: controllers (REST endpoints) to service (business logic) to DAO (data access), with unidirectional dependencies, each tested in isolation. A DAO module with an interface was later reused as a library when the business logic split into three services. Review with C4 component diagrams and enforce modules with language-level support.
- Seam (Feathers): a place where functionality is stitched together and behaviour can be substituted, usually through dependency injection against an interface, enabling test doubles. Recipe for legacy seams without tests (as cited in the notes): identify change points, break dependencies, write tests, make changes, refactor. If a seam may be reused outside its subject (the same operation across the codebase), an inter-service API is a good fit.
- Leverage points: find hot, painful code with version-control churn plus complexity tooling in the pipeline (churn and complexity correlate).
- Continuous delivery and continuous verification are prerequisites for evolutionary architecture (`release-strategies.md`).

## 5. Patterns for evolving with APIs

### Strangler fig
Introduce new components while the old stays; migrate gradually; eventually remove the old. Two mechanisms:
1. Feature flags in process, when the seam was an in-process interaction. Not realistic when many consumers already call out of process.
2. A proxy or gateway facade routing to the legacy or new implementation, with consumers seeing the same API. Risks: the new component is a single point of failure or bottleneck; keep business logic out of the proxy or it is hard to remove at the end; keeping data coherent across legacy and modern sides is hard (the notes cite Newman's Monolith to Microservices; data splitting: `arch-decomposition`).

### Facade versus adapter
The strangler fig is a type of facade (intercept calls, hide complexity). An adapter converts representation or protocol: a SOAP-RPC request to a RESTful call, or grpc-gateway presenting REST JSON in front of gRPC. Protocol rewriting is hard to get right and can reduce cohesion and add coupling. A facade is simpler (route); an adapter converts. If a gateway moves from facade to adapter, coupling immediately increases: ask whether it is still the right component (compare "gateway as ESB" in `gateways.md`).

### API layer cake
Layered APIs (presentation, application, datastore tiers). Trade-off: cohesion within tiers but coupling across them (a feature touches every layer), leading to shortcuts: duplicated logic across layers, skipped layers (presentation talking to the datastore tier). The authors recommend avoiding this pattern, and note the organisation can create it (Conway's law, section 9).

## 6. Finding pain points and opportunities

Catalogue problem components.
- Upgrade and maintenance hit-list signals: a high change-failure percentage for a subsystem; high volume of support issues; high churn; high complexity (static analysis, cyclomatic); low developer confidence about ease of change. Such a subsystem is a candidate for an API abstraction plus a strangler fig.
- Performance: SLAs are the upper bound to monitor; do not first hear about latency from customers. Look for architectural causes (cross-region or internet calls). Method: measure the existing system, hypothesise, test and verify; look at the whole system, not one component; automate measurement in the build. Chatty cross-service calls and extra hops are implied causes (marked inferred in the notes).
- Highly coupled APIs: the tell-tale anti-pattern is synchronised coordination of releases across parts of the system.

## 7. Breaking dependencies (Feathers techniques)

- Sprout: write new functionality elsewhere (a new, tested method or class) and call it from the legacy method at the insertion point.
- Wrap: create a new method with the same name and signature, rename the old one, and have the new one call it, adding new logic before or after.
Build legacy-code skills with katas and pairing. Refactoring mechanics: `craft-refactoring`.

## 8. Reference sequence of steps (the case study, MAA ch. 10)

1. Start: legacy application plus database.
2. Extract the Attendee functionality into a standalone API service (requirements driven); design and test its API.
3. Add an API gateway between users and both legacy system and new service: a facade controlling when legacy or modern is called.
4. Extract the Session service and add a service mesh for east-west traffic.
5. Run internal and external Attendee versions with feature flags choosing which serves a user.
6. Add a mobile client (makes threat modelling realistic).
7. Add the external partner system needing external authn/authz (OAuth2 authorization code with PKCE, client credentials; `arch-api-security`).
8. Replatform the Attendee service and gateway to the cloud, then optionally hybrid via a multicluster mesh and zero trust.

Condensed worked example from ch. 8: legacy monolith plus database; add a feature flag in the controller choosing the modern Attendee API or the legacy store; migrate users in batches; for out-of-process consumers use gateway routing (facade); measure with fitness functions (error rate, latency in the pipeline); retire the legacy path and remove the flag. Each step is a decision point: increased flexibility trades against architecture and infrastructure complexity. Draw a context or container diagram per step and attach it to its ADR (inferred in the notes).

## 9. Organisation and decision types

- Conway's law: a system's structure copies the organisation's communication structure. API systems are socio-technical. Align API and service ownership with team boundaries and design team interactions deliberately (inferred in the notes).
- Reversibility: Type 1 decisions are hard to reverse and deserve care; Type 2 decisions are easy to reverse and should not get a heavy process. Choosing API-enabling infrastructure such as a gateway or mesh is, especially in large enterprises, Type 1: research, requirements and ADRs.
- Async and future-facing items in the notes (AsyncAPI, HTTP/3, platform-based mesh) are dated; treat as directions to check, not facts.

## 10. Verify

Review questions from the notes, each with an observable check:
- Does the API expose the internal schema? Compare response models with database entities; any one-to-one mirror is a finding.
- Does a release require lockstep with another team? Check recent release history for coordinated deployments.
- Does the proxy or gateway contain business logic? Grep its configuration and plug-ins for domain terms.
- Are goals and fitness functions documented in ADRs, and are the functions running in CI?
- Does the module boundary expose more than needed? List public endpoints/symbols with no known consumer.
- Are seams tested before refactoring? Show the characterisation tests that exist for the code behind the seam.
- For a strangler migration: percentage of traffic on the new path, and the plan and date to delete the legacy path and the flag.
