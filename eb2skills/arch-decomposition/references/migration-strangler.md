# Migrating incrementally: seams, strangler fig, facades and cloud moves

Contents: 1. Set the destination and the goals; 2. Fitness functions by category; 3. Modules first; 4. Seams and legacy code; 5. Finding what to change first; 6. Strangler fig; 7. Facade, adapter, layer cake; 8. Breaking lock-step releases; 9. Cloud migration: the six Rs; 10. Hybrid traffic and security during migration; 11. Verify; 12. Limits.

Sources: Mastering API Architecture ch. 8 and ch. 9; Architecture: The Hard Parts ch. 4 (the "move to service-based first" advice); SRE Workbook ch. 7 (rewrite lesson). Gateway and mesh features are in `arch-api-design`; release mechanics (canary, flags) in `arch-api-design` and `arch-production-operations`; security design in `arch-api-security`.

## 1. Set the destination and the goals

An API is a module boundary and therefore a natural leverage point: high cohesion inside, loose coupling outside, information hidden behind a stable interface. That is why evolving a system through APIs works. Expose only business-focused endpoints; never leak internal abstractions, the data model or the schema. If an Attendee-like service exposed its datastore schema, replacing the datastore would force either error-prone translation code or changes in every consumer.

Pick an end state explicitly; without a destination any road works.

| End state | Choose when | Watch for |
|---|---|---|
| Monolith | Proof of concept, finding product-market fit; fastest at the start. Not inherently bad (not a big ball of mud) | Accidental coupling that shows late; mitigate with domain-driven design and possibly a hexagonal structure |
| SOA | Services over a network with sensible weight | Heavy tech (SOAP, WSDL, XML, vendor ESBs, smart pipes with business logic in middleware). Never put business logic in a gateway or ESB. Hardest part is right size and ownership |
| Microservices | Small independent services over well-defined APIs; smart endpoints, dumb pipes | Boundaries are the main challenge: use context mapping and event storming before building; use lightweight technology |
| Functions | Highly event-driven systems (event reactions, standard transformation pipelines) | Functions too small, so many must be orchestrated: high coupling; reusability against maintainability; team adjustment time |

The Hard Parts advice applies on top: if the target is microservices, go through service-based architecture first (`is-it-decomposable.md` section 8).

Goals come in two kinds. Functional goals (features, integrations) are driven by users and business. Cross-functional goals (the "-ilities": maintainability, scalability, reliability) are driven by technical leadership or forecast demand and mostly mean refactoring or a new platform. Write them down and communicate them; a wrong assumption is cheaper to find before coding, and a migration without shared goals and constraints becomes open-ended and drains people.

## 2. Fitness functions by category

A fitness function is a quantified, automated check on an architectural quality, run in the build pipeline like a unit or integration test. Add them as the migration proceeds and record each in an ADR.

| Category | Example |
|---|---|
| Code quality | Tests; keep cyclomatic complexity below a bound |
| Resiliency | Deploy to pre-production, run synthetic traffic, error rate below a threshold; use gateway or mesh fault injection to test availability scenarios |
| Observability | Services must publish the required metrics and not regress |
| Performance | Latency and throughput targets in the pipeline; the hard part is production-like data |
| Compliance | Evidence for audit and data requirements, specific to the organisation |
| Security | Dependency scan for known vulnerabilities; automated scan for OWASP-style issues |
| Operability | Minimum operating requirements, such as monitoring and alerting exist |

Automated deployment and continuous verification are prerequisites for evolutionary architecture. If they are missing, building them is the first migration task (the Sysops Squad case said the same about the release pipeline).

## 3. Modules first

Many "monolith" problems are really lack of code organisation. The book's example: a 4-million-line codebase with 24 years of technical debt, ad hoc coupling, fix one bug and create others. Modules (an architectural partition larger than a class or package) give well-defined boundaries that hide implementation. Sam Newman's advice, quoted in the notes: expose as little as possible from a module or microservice boundary, because hiding now lets you share later, and the reverse is hard.

Case study layout: controllers (REST endpoints) call a service layer (business logic) which calls DAOs (data access), dependencies unidirectional, each layer tested in isolation. A DAO module with an interface was later reused as a library when the business logic was split into three services ("monolith first" evolution). Review relationships with C4 component diagrams and enforce modules with language-level support (adaptation: package visibility, Go `internal/`, TypeScript path restrictions, Python import-linter contracts).

## 4. Seams and legacy code

A seam (Feathers, *Working Effectively with Legacy Code*) is a place where functionality is stitched together and behaviour can be substituted, usually by dependency injection against an interface. Seams enable test doubles.

Recipe for legacy code without tests (Nicolas Carlo, as cited): identify change points (seams), break dependencies, write tests, make changes, refactor. If a seam may be reused outside its subject, an inter-service API is a good fit, for example when the same operation is used across the codebase and you are splitting a service in two. For the mechanics of refactoring itself see `craft-refactoring`.

## 5. Finding what to change first

- Change leverage points: hot and painful code. Detect with version-control churn plus complexity tooling in the pipeline (Tornhill's approach); churn and complexity together correlate with trouble. Adaptation: `git log --since=6.months --name-only --format= | sort | uniq -c | sort -rn | head -30` gives file churn; join it with a complexity tool.
- Upgrade/maintenance hit list signals: high change-failure percentage in a subsystem; high volume of support issues; high churn; high complexity; low developer confidence about changing it. Add code-quality metrics. Such a subsystem is a candidate for an API abstraction plus strangler fig.
- Performance: use the SLAs as an upper bound to monitor, do not first hear about latency from customers, look for architectural causes (cross-region or internet service calls). Measure the existing system, hypothesise, test and verify; look at the whole system, not one component; automate the measurement in the build. (Chatty cross-service calls and extra hops are implied architectural causes; the notes mark that as inferred.)
- Breaking dependencies and coupled APIs: the anti-pattern is synchronised coordination of releases across parts of the system. It means the APIs are highly coupled.

## 6. Strangler fig

Introduce new components while the old stays; migrate gradually; eventually remove the old. Two mechanisms:

1. Feature flags in process. Works when the seam was an in-process interaction. Unrealistic when many consumers already call out of process, since you cannot make all of them implement flags.
2. Proxy or gateway facade routing to the legacy or the new implementation. Consumers keep the same API and do not know. Risks: the new component is a single point of failure and a bottleneck (mitigate); keep business logic out of the proxy or it is hard to remove at the end; keeping data coherent across the legacy and new sides while running side by side is hard.

Steps (condensed from the conference-system example):

1. Wrap the legacy behaviour behind an interface or API (the seam). Put tests around current behaviour first.
2. Build the new implementation behind the same interface.
3. Add routing: a feature flag in the controller for in-process callers, gateway routing for out-of-process callers.
4. Move users or traffic in batches; measure with fitness functions (error rate, latency) at each batch.
5. Retire the legacy path, remove the flag or route, delete the legacy code.

Data: while both sides run, decide which side owns each piece of data and how it is kept coherent; this is the hard part. See `decomposing-data.md` and `arch-distributed-workflows`.

## 7. Facade, adapter, layer cake

- A strangler fig is a kind of facade: it intercepts calls and hides complexity. An adapter converts representation or protocol (a SOAP RPC request into a REST call; a REST JSON front for gRPC). Protocol rewriting is hard to get right and can reduce cohesion and add coupling.
- A facade is simple (it routes); an adapter converts. If a gateway moves from facade to adapter, coupling immediately rises. Ask whether it is still the right component, and compare with the ESB trap.
- API layer cake (layered APIs: systems of engagement, differentiation, record). It echoes n-tier. Cohesion within tiers but coupling across tiers, since a feature touches every layer, which leads to shortcuts: duplicated logic across layers and layers being skipped. The authors recommend avoiding it.

## 8. Breaking lock-step releases

Two techniques from Feathers for changing legacy code safely:

- Sprout: write the new functionality elsewhere (a new, tested method or class) and call it from the legacy method at the insertion point.
- Wrap: create a new method with the same name and signature, rename the old one, and have the new one call it with new logic before or after.

Build legacy-code skills with katas and pairing.

## 9. Cloud migration: the six Rs

APIs sit closest to the user and are the ingress for most requests, so they get special attention. A gateway gives location transparency: deploy a service to the cloud and shift traffic gradually from old to new with limited or no consumer impact. In the case, the newest, highest-traffic service moved first, with the gateway doing the routing.

| R | Meaning | Fits when | Cautions |
|---|---|---|---|
| Retain / Revisit | Do nothing now | The return is not worth the effort, backed by business and technical evaluation | Record it in an ADR. Still communicate known dates (shutdowns, end of life, licence expiry) as deprecation warnings and check contract and SLA notice requirements. Watch latency from services ending up across network boundaries: high-traffic services slow every request; if the SLA would break, moving may not be possible |
| Rehost (lift and shift) | Move as is | Consolidating workloads or forced out of the current infrastructure; cheapest | The cloud does not behave like on-premises; confirm assumptions. Be careful with bespoke systems and custom hardware (local bus, dedicated network, block-device storage guarantees) |
| Replatform (lift, tinker, shift) | Rehost plus swap some components for cloud services with minimal rework | For example self-run MySQL to a managed database service | Chosen in the case study to avoid major rework and use database-as-a-service |
| Repurchase | Move to a different product, for example SaaS email | Commodity capability | Not for bespoke applications |
| Refactor / Re-architect | Re-imagine using cloud-native features, external behaviour unchanged | Strong business need for features, scale or performance blocked by the current environment | Most expensive, potentially most beneficial. If you already re-architected, replatform onto the cloud before making further architecture changes: one change at a time |
| Retire | Decommission | Big migrations often turn up a forgotten, unused system | The eventual goal in the case was to retire the legacy system |

Decision aid (derived in the notes): need out of the data centre fast and the application is standard, rehost or replatform; capability is a commodity, repurchase; the business is blocked by the architecture, re-architect but separately from the move; nothing is gained, retain with an ADR and deprecation dates; unused, retire. Cross-reference `is-it-decomposable.md` for the rewrite lesson.

API management as a migration tool: a "supercharged gateway" with edge policies (OAuth2 challenges, content validation, rate limiting), a developer portal, monetisation or chargeback. Most important here: a central point to discover APIs while you change things behind the scenes. Front the legacy system and the new API; as long as contracts do not change, you can evolve behind the management layer.

## 10. Hybrid traffic and security during migration

- Incremental migration blurs north-south (client to system) and east-west (service to service) traffic: one request may cross several clouds or data centres. Start at the edge and work inward: put an API gateway in the cloud first while the existing one stays untouched; build an isolated proof of concept entirely in the cloud first; only then experiment with routing in and out; allow time to learn the new infrastructure.
- Crossing boundaries: few simple routes, temporarily route from the new gateway to the old (for example a plain HTTP redirect). Many routes, or traffic that must not leave the network once inside, use VPN peering or endpoints or a multicluster service mesh. Involve information security, because this disrupts perimeter defence and zonal architecture.
- Zonal architecture limits blast radius by grouping infrastructure under shared policy (the four typical zones in the notes: public, public access, operations, restricted), but it is castle-and-moat: once inside, traffic is trusted. Cloud undermines its assumptions.
- Zero trust: never trust, always verify; no implicit trust by network location. The eight principles listed in the notes: know your architecture; know user, service and device identities; assess behaviour and health; authorise requests by policy; authenticate and authorise everywhere; monitor all access; do not trust any network, including your own; choose services designed for zero trust. NIST SP 800-207 is the reference. A mesh gives workload identity and certificates and tracing at every point: strong challenge (OAuth2) at ingress, mTLS inside the cluster.
- Microsegmentation: apply default-deny network policy to every pod (Kubernetes NetworkPolicy, enforced by a plug-in such as Calico), then add explicit allows (DNS egress, egress to specific namespaces, ingress from the mesh gateway). Each mesh routing rule needs a matching network-policy allow or the request is blocked even though discovery works. Apply consistently at release time.

## 11. Verify

- Goals, constraints and the end state are written down and linked from an ADR; each goal has a fitness function or a metric.
- Characterisation tests pass on the legacy path before the first change and on both paths during dual running.
- Review questions with observable answers: does the API expose the internal schema (diff the response shape against table columns)? Does a release require lock-step with another team (look at the last five releases)? Does the proxy contain business logic (search the gateway config and code for domain rules)? Is the module boundary exposing more than needed (list the public symbols)? Were seams tested before refactoring?
- At each traffic batch: error rate and latency compared with the baseline; a rollback route exists and has been exercised once.
- Retirement: the legacy route gets zero traffic for an agreed period (check access logs), then code and flag are deleted. The migration is not done until this happens.
- Cloud moves: cross-network latency for chatty calls measured against the SLA before moving; default-deny tested and each explicit allow tested; mTLS and the OAuth challenge confirmed at every ingress.

## 12. Limits

- Strangler with a proxy pays off when the old component is large, widely consumed and cannot be changed in place; for a small internal call, a direct replacement with tests is cheaper.
- Combining a re-architecture and a platform move in one step multiplies unknowns; the book advises separating them.
- The zero-trust and network-policy material is for Kubernetes-style platforms; the principles carry over, the objects do not.
