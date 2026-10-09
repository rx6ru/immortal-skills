---
name: arch-api-design
description: Guidance for designing, specifying, testing, versioning, deploying and evolving APIs between services and to external consumers - REST, gRPC or GraphQL per exchange, resource modelling, pagination and errors, OpenAPI and breaking-change detection, schema compatibility, contract testing, API gateways, service mesh, canary and blue-green releases, feature flags, and strangler-style migration of a legacy system behind APIs. Use when someone asks "REST or gRPC?", wants a new endpoint or API designed or reviewed, is changing or renaming a field, adding versioning, writing consumer-driven or contract tests, choosing between a proxy, gateway and mesh, planning a rollout, or splitting a monolith behind an API. Threat modelling, OAuth2, rate limiting and token handling belong to `arch-api-security`.
---

# API design, testing, release and evolution

## Purpose

Treat an API as a long-lived boundary that several teams and releases depend on, not as a by-product of one function. With this skill the agent picks the exchange style on evidence (who consumes it, how much traffic, who controls the release), writes changes that cannot silently break consumers, and proves that with tests and pipeline gates rather than by assertion. It also keeps infrastructure (gateway, mesh, flags) proportionate: added only for a named need, with its failure modes designed in.

## Choose what applies

| The request or the code looks like | Do this | Read |
|---|---|---|
| "REST or gRPC or GraphQL?", a new service-to-service or public API | Answer the six exchange questions, choose per exchange | `references/choosing-an-api-style.md` |
| New endpoints, resource shapes, pagination, error format, naming | Apply the REST standard; follow the repository's existing standard if there is one | `references/rest-design-standard.md` |
| Adding, renaming, removing or retyping a field; "is this breaking?"; version numbers; deprecation | Compatibility check, diff gate, version bump decision | `references/specification-and-versioning.md`, `references/compatibility-rules.md` |
| OpenAPI file missing, stale or unused; code generation; request validation | Use the four spec uses; wire the diff gate | `references/specification-and-versioning.md` |
| Protobuf, Avro, JSON Schema, message formats, schema registry, rolling upgrade | Direction rules and per-format rules | `references/compatibility-rules.md` |
| Tests for an API, "add contract tests", Pact, stubs, Testcontainers, e2e | Pick levels with the pyramid, contracts first | `references/api-testing-and-contracts.md` |
| How strict should the interface between two services be; payload carries more than needed | Strict vs loose vs consumer-driven; stamp coupling | `references/contract-strictness.md` |
| Edge routing, "do we need an API gateway?", gateway selection or incidents | Proxy vs LB vs gateway; six drivers; anti-patterns | `references/gateways.md` |
| Service-to-service reliability, mTLS between services, "do we need a service mesh?" | Mesh vs libraries; styles; pitfalls | `references/service-mesh.md` |
| Rollout, canary, blue-green, dark launch, feature flags, release metrics | Separate deploy from release; pick strategy by coupling | `references/release-strategies.md` |
| Legacy monolith, strangler fig, extracting a service, "make this system API-driven" | Goals, fitness functions, seams, facade | `references/evolving-with-apis.md` |
| An ADR is needed for one of these decisions | Use the guideline table's questions as the Context and Consequences checklist; ADR template is in `arch-decisions-and-tradeoffs` | `references/guideline-tables.md` |

This skill does not apply when:
- The question is about authentication, authorisation, OAuth2 grants, JWT validation, rate-limit algorithms or threat modelling: use `arch-api-security` (this skill only says where a gateway or mesh enforces them).
- The API is an in-process interface between modules with no network boundary: use `craft-module-design`. (Remodelling an in-process API as out-of-process is in scope.)
- The task is service decomposition, service granularity or splitting a shared database: use `arch-decomposition`. Orchestration, sagas and workflow state across services: `arch-distributed-workflows`.
- The task is SLO definitions, alert arithmetic or incident practice: `arch-reliability-slos`, `arch-production-operations`.
- General test craft (naming, FIRST, doubles in the abstract): `craft-testing`.
- A single internal endpoint in a small app with one known consumer deployed together with it: apply only the error-format and compatibility basics; skip gateways, mesh, contracts and release machinery.

## How to apply

### A. Design or review an exchange

1. Name the producer, each consumer, who owns each, and whether the path is north-south (external) or east-west (internal). Record whether you control the consumer's release timing (a mobile store or partner does not give you that).
2. Answer the exchange questions (traffic pattern, control of consumer code, need for consumer-built queries, versioning limits, change frequency, measured payload or latency pressure).
3. Choose the style:

| Condition | Style |
|---|---|
| External or unknown consumers | REST at maturity level 2 (resources plus correct verbs; hypermedia not required) |
| Internal, both sides yours, high traffic, performance measured | gRPC |
| Consumers (often mobile or UI) compose their own queries across services | GraphQL over existing APIs |
| Nothing measured, mixed audience | REST first, switch a hot internal edge to gRPC when measurements demand it |

4. If the same service must offer two styles, give each its own independently evolving specification; do not generate one from the other (field renumbering and coupled versioning are the reasons).
5. Decide contract strictness from three factors: how often the two sides change together, the consumer's deploy latency, and the rate of change of the information. Slow deploy channel or independent teams: loose contract plus consumer-driven tests. Co-changing teams: strict, versioned schema. Send only what the consumer needs.
6. Write the decision in an ADR with the guideline-table questions as the discussion points.

### B. Shape REST resources (details in `rest-design-standard.md`)

1. Resource URIs with opaque ids; no personal data in URLs because paths are logged and cached.
2. Create returns 201 with a Location header.
3. Collections return a wrapper object with an opaque next link from day one (converting a bare array later breaks consumers).
4. One shared error shape; accurate status codes; never an error inside a 2xx; no stack traces externally; document what 5xx means for non-idempotent operations.
5. Take names from a shared domain dictionary; a rename later is a breaking change.

### C. Change an existing API without breaking consumers

1. Classify the change with the compatibility rules for the format in use:

| Change | JSON/REST | Protobuf/gRPC | Avro |
|---|---|---|---|
| Add optional field or request parameter | Compatible; consumers must ignore unknown fields | Compatible with a new tag number | Compatible only with a default |
| Remove a field | Breaking for any reader of it | Compatible if tag is reserved and never reused | Compatible only if it had a default |
| Rename | Breaking | Compatible (names are not on the wire) | Alias; backward compatible only |
| Change type or meaning | Breaking | Only some conversions are allowed; widening int32 to int64 lets new code read old data but old code truncates new values | Only where Avro can convert |
| Make an optional thing mandatory | Breaking | Breaking | Breaking |

2. Check the direction. Servers upgrading first needs backward-compatible requests and forward-compatible responses; public APIs and mobile clients must assume old clients forever.
3. Breaking change: bump the major version, keep the old one live as deprecated, publish a migration guide, track usage of the deprecated version, retire on a date. Non-breaking: minor or patch, released with a canary or mirror, no consumer action.
4. Preserve unknown fields on every read-modify-write or republish path.
5. Put the diff of the spec against the last released spec in CI; fail on incompatibility unless a major bump is intended.

### D. Test the API

1. Unit tests form the base. Above them, in order of value for effort: contract tests (producer contracts for many or external consumers, consumer-driven when consumers are reachable), then component tests of the service in isolation, then integration tests of each outbound dependency, then end-to-end tests of core journeys only.
2. Contracts generate producer tests and consumer stubs. They cover single interactions, not scenarios.
3. Component tests cover status codes, bad input, auth failure, empty collections, content negotiation and the Location header.
4. Integration tests prefer contract-generated stubs, then recordings, then real dependencies in containers; never trust hand-typed stubs that nobody revalidates.
5. End-to-end tests keep TLS and authentication on, use realistic payloads, and stub only things outside your domain.

### E. Put infrastructure in only when a named need exists

1. Ingress: use the simplest thing that meets the known requirements. A reverse proxy handles one backend with TLS; a load balancer adds multiple backends and discovery; a gateway is justified by composition, authn/z, retries, rate limiting, observability, lifecycle management or monetisation. Drivers: reduce coupling, simplify consumption, protect from abuse, observe consumption, manage as products, monetise.
2. Internal traffic: single mandated language and simple routing mean libraries; polyglot stacks with cross-cutting needs (mTLS, retries, circuit breaking, identity-based allow lists, traffic splitting) justify a mesh. If only ingress is the pain, buy a gateway, not a mesh.
3. Both are hard-to-reverse decisions: do requirements analysis and write an ADR. Buy or adopt, do not build.
4. Keep business logic out of both. Plug-ins are for cross-cutting concerns.
5. Never route internal calls out through the public gateway and back in.
6. Plan their failure: HA, tested failover, config rollback, an owning team, a decision on fail-open or fail-closed.

### F. Release

1. Separate deployment (code running) from release (users affected). Start with existing software: add feature flags to a monolith, traffic weights at a gateway or mesh for services.
2. Pick the strategy:

| Situation | Strategy |
|---|---|
| Loosely coupled minor or patch, good monitoring | Canary with weights at gateway or mesh |
| Refactor correctness or performance check without user impact | Mirroring (read or idempotent traffic only) |
| Consumer and producer released together | Blue-green |
| Monolith without a routing layer | Feature flags |
| Compare two designs on user metrics | A/B split |
| Breaking major change | Parallel versions plus lifecycle |

3. Gate promotion on metrics (error rate by status class, latency against baseline, saturation, business KPI), automate halt and rollback, and make validation GETs bypass caches so a cached good answer cannot hide a broken build.
4. Flags: unique names, safe defaults when the flag service is down, removal ticket at creation.

### G. Evolve a legacy system

1. Write goals (functional and cross-functional) and the target end state (monolith, SOA, microservices or functions) before touching code.
2. Express the "-ilities" as fitness functions in the pipeline and record each in an ADR.
3. Find the seam: a module boundary where behaviour can be substituted. Test it before changing what is behind it (sprout or wrap for untested legacy code).
4. Put a gateway facade in front, route by path or host to old and new, and move traffic gradually. Keep business logic out of the facade. Delete the legacy path and the flags at the end.
5. If the gateway starts converting protocols, it has become an adapter and coupling rises; ask whether it is still the right component.
6. Avoid stacking API layers by tier (presentation, application, data); features then touch every layer.

## Verify

Run what applies and show the output to the user.

1. Spec gate: in a scratch branch rename one field and add another optional field. The pipeline must report the rename as breaking and the addition as compatible. If it reports nothing for the rename, the tool is reading the wrong spec version or the wrong file.
2. Round trip: encode with the new schema, decode and re-encode with the previous release's reader, decode with the new reader; the new field must survive. Keep golden fixtures from each released version and decode them all with the current code.
3. Contracts: mutate a producer response (rename a field) and confirm the contract test fails; mutate the stub and confirm the consumer test fails.
4. Count tests per level and report the shape; flag an end-to-end-heavy suite.
5. Search the gateway or mesh configuration and plug-ins for business logic and payload-based routing; search for internal calls to the public hostname.
6. Failure drills in staging: kill a gateway instance; take the flag service away and confirm defaults; trip a circuit breaker and observe the fallback; deny an edge not on the mesh allow list and confirm rejection.
7. Rollout drill: deploy a build that returns 500s to the canary and confirm automatic halt and rollback; check that a trace id spans all hops.
8. Error handling review: every error uses the shared shape, no stack traces in external responses, no 2xx errors, and the 5xx meaning is documented for non-idempotent operations.
9. Paperwork: the exchange decision, any gateway, mesh or flag introduction, and each fitness function has an ADR.

Done means:
- Style and contract strictness were chosen per exchange with reasons recorded.
- A spec exists and is diffed against the last release in CI, with a demonstrated failure on a breaking change.
- Every change is classified breaking or compatible, with version and deprecation handled accordingly.
- Contract, component and integration tests exist at the pyramid proportions, and the mutation checks above fail when they should.
- Any gateway, mesh or flag has a named driver, an owner, a failure plan and no business logic inside.
- A rollback path was exercised, not just described.

## Proportion and limits

- Skip infrastructure that no requirement names. A gateway or mesh is itself a hot-path component with its own outage, upgrade and ownership cost; the book treats choosing one as hard to reverse.
- Contract testing has a learning and writing cost. It pays most with several consumers or external audiences; for one consumer in the same repository and release, component tests plus a type-checked client may be enough (adaptation, not from the books).
- Full hypermedia, multiple parallel API styles, GraphQL in front of every service and per-service gateways are rarely worth it.
- The notes are a 2022-2025 snapshot. Tool names (Istio CRDs, Consul intentions, Cilium, Argo Rollouts, LaunchDarkly, Pact, openapi-diff, Traffic Director, SMI) will have changed; keep the principle, check the current tool. HTTP/3, AsyncAPI and sidecarless meshes were emerging then.
- The book is partly opinionated: it favours gRPC for east-west traffic and REST for external, it advises against the layer-cake pattern, and it prefers buying over building. Where the repository already has a settled standard, follow it unless it causes a failure you can demonstrate.
- Performance claims for formats (gRPC versus JSON) must be measured; the sample byte sizes in the notes are for one record.
- The three sources emphasise different things: DDIA stresses data-format compatibility, Hard Parts the coupling cost of contracts, the API book operational tooling. Use all three lenses on a change that crosses formats, teams and rollout.

## References

- `references/choosing-an-api-style.md`: when choosing REST, gRPC or GraphQL for an exchange, offering several styles, async options, remote-call pitfalls.
- `references/rest-design-standard.md`: when shaping resources, collections, pagination, filtering, errors, naming.
- `references/specification-and-versioning.md`: when working with OpenAPI, semver, the API lifecycle, deprecation, or the CI breaking-change gate.
- `references/compatibility-rules.md`: when a schema or message format changes (JSON, protobuf, Avro) or a rolling upgrade is involved; checklist and test matrix.
- `references/api-testing-and-contracts.md`: when planning or reviewing API tests, contracts, stubs, containers, end-to-end and performance tests.
- `references/contract-strictness.md`: when deciding how tight a contract between services should be, or trimming oversized payloads.
- `references/gateways.md`: when deciding on, selecting, configuring or debugging an API gateway.
- `references/service-mesh.md`: when deciding on or operating a service mesh or library-based reliability layer.
- `references/release-strategies.md`: when planning deployments, canaries, flags, rollout metrics and observability.
- `references/evolving-with-apis.md`: when migrating or modernising a system behind APIs, including fitness functions and seams.
- `references/guideline-tables.md`: when you need the book's decision tables as ADR checklists.

## Sources

- Mastering API Architecture, ch. 0 (framing, traffic patterns, C4, ADRs): evolution, vocabulary, case study.
- Mastering API Architecture, ch. 1: REST, gRPC, GraphQL, REST standard, OpenAPI, versioning, modelling exchanges.
- Mastering API Architecture, ch. 2: test quadrants and pyramid, contract, component, integration, end-to-end testing.
- Mastering API Architecture, ch. 3: API gateways, taxonomy, failure, anti-patterns, selection.
- Mastering API Architecture, ch. 4: service mesh, implementation styles, features, pitfalls, selection.
- Mastering API Architecture, ch. 5: deployment versus release, lifecycle, canary, mirroring, blue-green, observability, platforms.
- Mastering API Architecture, ch. 8: cohesion, coupling, fitness functions, seams, strangler fig, facade and adapter.
- Mastering API Architecture, ch. 10: case-study sequence, decision types, future directions.
- Designing Data-Intensive Applications 2e, ch. 5: encoding formats, compatibility rules, REST and RPC, durable execution, brokers.
- Architecture: The Hard Parts, ch. 13: contract strictness, consumer-driven contracts, stamp coupling.
