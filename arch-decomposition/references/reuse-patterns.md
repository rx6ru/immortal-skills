# Sharing code across services: replicate, library, service, sidecar

Contents: 1. Framing; 2. Chooser; 3. Code replication; 4. Shared library; 5. Shared service; 6. Sidecar and service mesh; 7. When reuse adds value; 8. Worked cases; 9. Verify; 10. Limits.

Source: Architecture: The Hard Parts ch. 8 (with ch. 5 pattern 2 and ch. 7 shared-code integrator). Mesh and gateway mechanics are in `arch-api-design`; the general trade-off method is in `arch-decisions-and-tradeoffs`.

## 1. Framing

Reuse is trivial in a monolith (import it). In a distributed system it is hard. Slogans such as "reuse is abuse", "share nothing" and WET (the opposite of DRY) appeared, but shared code is unavoidable. It comes in two kinds: domain code (formatters, calculators, validators, auditing) and infrastructure code (security, logging, metrics). There are four techniques, each with trade-offs. Settle which technique by analysis, not by preference: in the book's case one developer wanted one shared DLL, another wanted many libraries and authorisation as a shared service, and the architect's answer was to analyse library granularity and library-versus-service trade-offs.

## 2. Chooser

Ask in this order:

1. Is it purely operational plumbing (logging, monitoring, discovery, authentication/authorisation, circuit breaking) that many services need consistently? Sidecar and mesh. Never for domain objects.
2. Is it static, trivial and one-off (a marker annotation, a small utility that will not change)? Replication, but only after looking at the other three.
3. Is the environment homogeneous (one language or platform) and does the shared code change at a low to moderate rate? Shared library: fine-grained, versioned, with a custom deprecation policy.
4. Is the environment polyglot and does the shared functionality change often? Shared service. Accept latency, scalability coupling, fault coupling and runtime-change risk.
5. Before sharing at all, check the rate of change in version control. If domain code changes fast, prefer duplication behind a contract over coupling.
6. Domain objects (Customer, Address) belong behind contracts, not in a sidecar or a central service.

| Technique | Binding | Best when | Cost |
|---|---|---|---|
| Replication | Copy | Tiny, static, one-off | Every defect is a change in every copy |
| Library | Compile time | Homogeneous, low to moderate change | Version sprawl, per-language copies |
| Service | Run time | Polyglot, high volatility | Latency, scale and fault coupling, runtime risk |
| Sidecar | Deployed with each service | Operational cross-cutting concern | One sidecar per platform; can grow large |

## 3. Code replication

Copy the code into every service. It was popular in early microservices (share nothing, a misreading of bounded context) and the notes say it "quickly fell apart" in practice.

Use when: simple, highly static, one-off code unlikely to change for defects or features, such as annotations or marker interfaces. Example: a `@ServiceEntrypoint` annotation with no logic that tags the service's entry-point class and carries metadata (service type, domain, bounded context). Also workable during monolith migration: replicate a static utility class into each service so each can trim or evolve it (like tactical forking).

Do not use when: the code has any logic that could be wrong or change. A bug in replicated code means touching every service.

Trade-offs: advantages are that bounded context is preserved and nothing is shared. Disadvantages: code changes are hard to apply, copies drift apart, and there is no versioning across services.

## 4. Shared library

An external artifact (JAR, DLL, wheel, npm package, crate, Go module) bound to the service at compile time. The two difficulties are granularity and versioning.

Granularity is a trade between dependency management and change control:

- Coarse (one big shared package): dependencies are easy (one per service) but change control is bad. Any change forces every service to adopt a new version eventually, with unnecessary retesting and redeploys and a large test scope.
- Fine (security, formatters, annotations, calculators as separate packages): change control is good (a change to one class hits only the services using it) but the dependency matrix explodes. Imagine 200 services and 40 libraries: a distributed monolith.
- Advice: avoid big coarse-grained libraries. Prefer smaller functionally partitioned libraries, that is, favour change control over dependency management. Carve static functionality (formatters, authentication/authorisation) out so it is not dragged into the version churn of volatile code. With few services the choice matters little; with many it matters a lot.

Versioning:

- Always version shared libraries. With versioning, one service of ten can take a new validation rule alone; without it all ten retest and redeploy.
- "Versioning is simple" is the book's ninth fallacy of distributed computing. Hidden complexities:
  1. Communicating a change: how do other teams learn that version 1.5 exists, what changed, and who is affected? Artifact repositories help; people still have to coordinate.
  2. Deprecation: custom deprecation per library is preferred, based on rate of change. A rarely changing security library keeps two or three versions; a weekly-changing calculator library keeps about ten, otherwise consumers upgrade every week. Cost: someone must track each policy. Global deprecation (for example a maximum of four back-versions for all) is easy to govern but forces churn for fast-moving libraries and hurts velocity.
  3. A serious defect or breaking change invalidates the deprecation policy: all services must adopt the new version at once. Another reason to keep libraries small.
  4. Never depend on the LATEST tag: emergency hotfixes break because something in LATEST is incompatible.

Trade-offs: advantages are versioned change, compile-time checking (fewer runtime errors) and good agility. Disadvantages: dependencies are hard to manage, code is duplicated in heterogeneous codebases (the library per language), deprecation and version communication are hard.

Use when: a homogeneous environment with low to moderate change in the shared code. Because it is bound at compile time, performance, scalability and fault tolerance are unaffected, and versioning limits the risk to other services.

## 5. Shared service

Shared functionality deployed as its own service, called at run time. Use composition (callable operations), not inheritance. The benefit: change the shared behaviour without redeploying consumers. Costs:

- Change risk: it is a runtime change, so a simple change can take down the whole system. Versioning is harder: endpoint versions (`/1.0/discountcalc`, `/1.4/...`) make consumers change configuration; when to cut a new endpoint is subjective; and access over REST, messaging and gRPC must be versioned in step.
- Performance: network latency plus security latency per call. Mitigations: gRPC; asynchronous messaging with request queue, reply queue and correlation id.
- Scalability: the service must scale as fast as its busiest consumers.
- Fault tolerance: when it is down, dependents are non-operational. Multiple instances mitigate but do not remove the trade-off.

Trade-offs: advantages are good fit for high volatility, no code duplication in heterogeneous codebases, bounded context preserved, no static code sharing. Disadvantages: versioning, latency, availability and scalability coupling, runtime-change risk.

Use when: highly polyglot and the functionality changes often. Beware runtime side effects.

## 6. Sidecar and service mesh

Context: in microservices, duplication is preferred to coupling. Each service keeps its own representation of Customer and exchanges loose name/value JSON. In a service-based architecture, coupling is more likely acceptable. It depends. But operational capabilities (monitoring, logging, authentication and authorisation, circuit breakers, service discovery) need consistency; leaving them to each team means nobody can verify they were done and unified upgrades are impossible.

Mechanics: derived from the hexagonal (ports and adapters) idea of separating domain logic from technical adapters. Split each service into a domain part and an operational part. The operational part is a sidecar component attached to every service, owned jointly by the teams or by a central infrastructure group. When every service includes it (enforced by fitness functions), the sidecars connect through a service plane, forming a service mesh, which gives dashboards, scaling control and consistent governance. It also restrains polyglot sprawl: one sidecar per platform rather than every team building monitoring for every platform.

Orthogonal coupling: two independent concerns that must intersect (monitoring and catalog checkout). A sidecar reuses the operational aspect across domain-oriented seams. Recognising orthogonal coupling helps you find intersection points with least entanglement.

Rules:

- Only for operational coupling, plumbing with no domain responsibility. Never put domain shared components (Address, Customer classes) in it, because that recouples services and one team's change forces coordination. If ever done, it is an architect-level decision with trade-off analysis; contracts handle such coupling.
- Utility libraries needed by some teams: the trade-off is how many teams need it versus the overhead added to every service. Stated heuristic: if fewer than half the teams use it, it is not worth the sidecar overhead; leave it out and reassess.
- Test that every service has the sidecar via fitness functions; the infrastructure team owns it and service teams are its customers.

Trade-offs: advantages are a consistent way to create isolated coupling, consistent infrastructure coordination, and flexible ownership (per team, central, or mixed). Disadvantages: a sidecar must be built per platform and may grow large and complex.

Use when: spreading a cross-cutting concern across a distributed architecture. It is the architectural counterpart of the Decorator pattern.

## 7. When does reuse add value?

Reuse is among the most abused abstractions: organisations treat it as a goal without weighing trade-offs, a lesson of 2000s orchestration-driven SOA that maximised reuse. Insurance example: each division has its own view of Customer; unifying into a single central Customer service was a disaster for two reasons: the one entity had to be complex enough for every domain and became hard to use for simple things, and any change made for one domain rippled to all and needed coordinated testing.

The book's formulation: reuse is found through abstraction but made worthwhile by a slow rate of change. Successful reuse targets (operating systems, open-source frameworks and libraries) change slowly and predictably. Internal domain capabilities and fast-moving technical frameworks are bad coupling targets.

Modern reuse target: a platform per domain capability behind a well-defined API that hides implementation, so the internals can move fast. It does not protect against semantic changes in what is exchanged, so use careful encapsulation and contracts (`arch-distributed-workflows`, contracts).

## 8. Worked cases

Common infrastructure logic. Symptom: duplicate log lines because a shared message-dispatch library logs and so does the service. Decision: sidecar plus mesh for operational coupling, maintained by a shared infrastructure team; sidecar provides monitoring, logging, discovery, authentication, authorisation. Consequences: no domain classes in the sidecar; teams work with the infrastructure team to add shared operational libraries when enough teams need them; the pipeline tests the sidecar in each service through fitness functions. A utility such as a JSON-to-XML converter needed by about 5 of 16 or 17 teams stays out.

Shared domain functionality (ticket database logic). Ticketing was split into Creation (customer-facing), Assignment and Completion, all sharing queries and updates on the ticketing tables. One developer proposed a shared data service, another a shared DLL. The architect hypothesised the service and probed. Against: every query becomes a network call (performance), if the data service is down all three are down and Creation is customer-facing (fault tolerance), runtime-change risk, scaling coordination. For: data abstraction, central connection pooling (minor with three services), change control. Repository history showed the shared database logic barely changes, which undermined the volatility argument. Decision: shared library. Consequences: changes to it force test and deploy of the ticketing services (less agility); each instance manages its own connection pool. The reusable move: test the volatility assumption against version control history before accepting it.

## 9. Verify

- Dependency graph: count libraries times services; report which services are how many versions behind against each library's deprecation policy.
- Build files contain no floating or LATEST version specifiers (grep the manifests: `latest`, `*`, open ranges).
- No domain class (Customer, Address, Order) lives in the sidecar or infrastructure libraries (dependency rule test).
- A fitness function fails the build if a service lacks the sidecar.
- Shared service: consumer contract tests per supported version; measured added p99 latency; the availability of the service is accounted for in its callers' availability budgets.
- Replicated code is annotated with where the master copy is and why replication was chosen, and has no logic.

## 10. Limits

- Library granularity advice is "prefer change control", a judgement the book illustrates with 200 services and 40 libraries; with five services one library may be fine.
- Heuristics such as "fewer than half the teams" and "keep 2 to 3 versions of slow libraries, about 10 of fast ones" are the book's illustrations. Calibrate to the actual team count and release rate.
- Language ecosystems differ: Go and Rust vendoring, npm lockfiles and Python pins already give per-service versions; the coordination problem (who upgrades when) remains.
