# API gateways: ingress traffic management

Contents: 1. Is a gateway needed; 2. What a gateway is; 3. Six reasons to use one; 4. Taxonomy; 5. Routing the strangler way; 6. Failure management; 7. Pitfalls; 8. Selecting a gateway; 9. History in brief; 10. Verify

Sources: Mastering API Architecture (MAA) ch. 3, ch. 8, ch. 10. Security functions of a gateway (TLS termination, authn/z, WAF, rate limiting detail) are developed in `arch-api-security`; this file covers the architectural side.

## 1. Is a gateway needed

Not always. Anything that provides ingress must route and give reliability, observability and security; a simple reverse proxy or load balancer can do it. The gateway is the commonest enterprise answer and usually the most scalable, maintainable and secure as consumers and providers multiply.

Capability matrix (MAA Table 3-1):

| Feature | Reverse proxy | Load balancer | API gateway |
|---|---|---|---|
| Single backend, TLS | yes | yes | yes |
| Multiple backends, service discovery | no | yes | yes |
| API composition, authorisation, retry logic, rate limiting, logging and tracing, circuit breaking | no | no | yes |

Rule (Table 3-2): choose the simplest solution that meets the requirements, with an eye on the immediate future and known requirements. Advanced cross-functional needs (authn, authz, rate limiting) point to a gateway. Enterprises should pick one that supports API management (APIM). Check existing solutions and organisation-wide mandates (traffic must go through certain edge components) first.

Do not add a gateway when: a single endpoint routes to a single backend with no cross-functional needs; or the only reason is that "everyone has one" and no listed driver applies.

## 2. What a gateway is

A management tool at the edge between consumers (single-page apps, mobile, internal systems, third parties) and backend services: a single entry point for a defined group of APIs.
- Two parts: a control plane (operators define routes, policies, telemetry) and a data plane (routes packets, enforces policies, emits telemetry). They may ship together or separately.
- It acts as a reverse proxy (protects servers; a forward proxy protects clients), can aggregate calls to backends, and applies cross-cutting concerns: authentication, rate limiting, timeouts and retries, metrics, logs, traces. Many add lifecycle management, a developer portal, account administration and governance.
- Deployment: small organisations usually run one logical gateway (several instances for HA) at the edge of the data centre or cloud. Enterprises run several: a perimeter gateway between the internet and the DMZ, plus per-product or per-line-of-business gateways, possibly different implementations by geography or governance.
- The edge stack has layers: CDN, WAF, load balancer, API gateway. They may be deployed separately, owned by different teams or vendors, or combined in one product.

Terminology (Posta, per notes): API gateway is L7 API management from a simple adapter to full lifecycle; edge proxy is a general L3/L4 reverse proxy with basic cross-cutting functions and no API-specific features; ingress controller is Kubernetes-specific control of what enters a cluster.

## 3. Six reasons to use a gateway

1. Reduce coupling (adapter or facade). Clients integrate with the gateway's API; backends can move location, architecture or language with minimal impact as long as the agreed contract holds. A facade offers a new simpler interface; an adapter reuses an old interface for interoperability. Supports loose coupling, cohesion and information hiding.
2. Simplify consumption (aggregate and translate). One consumer-facing API over several backends (GraphQL is often used). Risks: business logic coupling in the gateway; orchestrating concurrent calls saves time and avoids per-consumer implementation but spreads business logic and creates operation coupling (changing call order can change results if backends are not idempotent). Protocol translation (SOAP heritage systems as REST) is possible but costs design, implementation, testing for fidelity, and compute per request.
3. Protect from overuse and abuse: TLS termination, authn/z, IP allow and deny lists, WAF (built in or integrated), rate limiting, load shedding, API contract validation. For small organisations the gateway is the first line of defence. It needs observability to detect abuse, accidental or deliberate.
4. Observability. The edge sees every request: capture top-line metrics (errors, throughput, latency) as SLIs and business KPIs; inject correlation identifiers (for example Zipkin B3 headers) at the gateway and propagate them upstream to join logs and traces; build dashboards and alerts rather than just collecting data.
5. API lifecycle management (APIM): treat APIs as products. One vendor lifecycle has ten stages: Building, Testing, Publishing, Securing, Managing, Onboarding (OpenAPI/AsyncAPI docs, portal, sandbox), Analyzing, Promoting (marketplace), Monetizing, Retirement (deprecation and removal). Many tie to the gateway implementation, so the choice matters if you need APIM.
6. Monetise: developer portal with account management, plans, rate limits, payment integration; enterprise gateways include it.

## 4. Taxonomy (MAA Table 3-3)

| | Enterprise gateway | Microservices (micro) gateway | Service mesh gateway |
|---|---|---|---|
| Purpose | Expose, compose, manage internal business APIs | Expose, compose, manage internal business services | Expose internal services within a mesh |
| Publishing | API management or service team via admin API (mature organisations: delivery pipelines) | Service team via declarative code in the deployment process | Service team via declarative code with the mesh |
| Monitoring | Admin/ops meter calls per consumer, report errors | Developer: latency, traffic, errors, saturation | Platform: utilisation, saturation, errors |
| Debugging | L7 error handling; extra logging; reproduce in staging | L7 handling; detailed monitoring, traffic shadowing, canarying | L7 handling; detailed monitoring, traffic tapping |
| Testing | Multiple environments (QA, staging, prod), gated deploy, consumer-driven versioning (semver) | Canary routing, dark launch; contract testing for upgrades | Canary routing |
| Local development | Install script, Vagrant, Docker, gateway mocks | Via the orchestration platform (containers, Kubernetes) | Via the orchestration platform |
| UX | Web admin UI, developer portal, service catalog | IaC and CLI, simple portal and catalog | IaC and CLI, limited catalog |

Notes on each:
- Enterprise: full APIM, usually open-core with a commercial bias; dependent data stores must run HA, which adds to running cost and DR/BC plans.
- Micro gateway: routes ingress to backend APIs with few lifecycle features; often open source or lite versions of enterprise ones; uses the platform (Kubernetes) for state (lifecycle data, rate-limit counts, accounts); built on modern proxies such as Envoy so it integrates with meshes.
- Mesh gateway: core ingress into the mesh only; lacks comprehensive identity-provider and WAF integration; coupled to its mesh. If no mesh is planned it is a poor first gateway (see `service-mesh.md`).

## 5. Routing the strangler way (MAA ch. 3, ch. 8)

Do not let the monolith route to extracted services: tight coupling, all traffic through the monolith, routing config tied to monolith releases, bigger blast radius, and a slow release train blocks routing changes. Put an HA gateway in front with developer self-service access to routing configuration.

Routing shapes (Ambassador Edge Stack on Kubernetes in the book; concept generic):
- Prefix `/` goes to the legacy service (`name.namespace:port`); prefix `/attendees` with a rewrite of `/` goes to the new service (the rewrite strips the matched prefix). Prefixes can nest (`/attendees/affiliation`) or use regex. Over time the legacy app shrinks to a shell.
- Host-based alternative: hostname `attendees.example.com`, prefix `/`, to the new service. Many gateways also route by path or query string.
- TLS terminates at the gateway (certificates via an automated issuer); authn and rate limiting are configured there without redeploying the app.
- Do not route on request payloads. It leaks the coupled domain schema into gateway configuration (which must be kept in sync) and costs deserialisation time.

Extended migration steps are in `evolving-with-apis.md`.

## 6. Failure management

The gateway is on the critical path. An edge gateway outage makes the whole system unavailable; an upstream gateway outage takes down a core subsystem. Typical single points of failure in order: DNS, global or regional L4 load balancers, firewall/WAF, then the gateway. More functionality in the gateway means more risk, and its configuration changes constantly with releases.

- Security components may fail open (pass traffic when they fail). That can suit availability-dominated systems but is unacceptable for financial or government use. Challenge the assumption explicitly.
- Detect and own: collect metrics, logs and traces; give every gateway an accountable owning team with on-call (possibly 24/7/365); publish SLOs and codify them into SLAs; hold blameless post-mortems and share them widely. Further reading named in the notes: USE method, RED method, the four golden signals.
- Mitigate: run several instances (redundant hardware across locations on-prem; multiple AZs or regions in cloud). The load balancer in front needs health checks and failover that are regularly tested, especially for active/passive or leader/node modes. Typical failover problems: lost client state or sticky sessions, poor geographic redirect (EU users sent to a US west-coast site), and cascading failure (a faulty leader election deadlocks all backends).
- Roll gateway configuration out safely and be able to revert quickly; the operational side is in `arch-production-operations`.

## 7. Pitfalls (anti-patterns)

| Anti-pattern | What happens | Fix |
|---|---|---|
| API gateway loopback | Service-to-service traffic leaves through the public gateway and returns (a poor man's service discovery, hub and spoke). Traffic leaves the network (performance, security, cloud egress and inter-AZ cost), does not scale beyond a handful of services, makes the gateway a bottleneck and SPOF, confuses traces | Internal service discovery or a service mesh (`service-mesh.md`). The legacy app must not call the public hostname to reach the Attendee service |
| API gateway as ESB | Business logic placed in gateway plug-ins (Lua for NGINX/OpenResty/Kong, C then WebAssembly for Envoy, Groovy for Zuul). Fine for authn/z, filtering, logging; business logic couples the gateway to services, is fragile, forces lockstep deployments | Keep plug-ins to cross-cutting concerns; move logic to services |
| Turtles all the way down | Many hierarchical gateways, per line of business or per concern (transport-security gateway, auth gateway, logging gateway). Symptoms: high cost of change (coordinate many gateway teams for a simple upgrade), unclear ownership ("who owns tracing?"), extra hop latency | Fewer layers; assign each function to one layer and one owner |

## 8. Selecting a gateway

- Start from current pain points and roadmap requirements (the six reasons above), not marketing.
- Build versus buy: generally adopt open source or commercial; do not build. Pitfalls: underestimating total cost of ownership (engineering, maintenance, operations); ignoring opportunity cost (unless you are a cloud or platform vendor a custom gateway is no competitive advantage); not knowing the current product landscape.
- Choosing a gateway is, especially in large enterprises, a hard-to-reverse (Type 1) decision (MAA ch. 10): research, requirements and an ADR (`arch-decisions-and-tradeoffs`).
- Checklist (Table 3-4, full text in `guideline-tables.md`): requirements prioritised; existing gateway-like technology identified; team and organisation constraints known; roadmap explored; honest build-versus-buy costs; solutions landscape known; all stakeholders consulted (developers, QA, architecture review board, platform team, InfoSec). Look for an existing patchwork (a hardware load balancer plus a monolith doing auth and routing) and count the edge components already in place.

## 9. History in brief (why the products look as they do)

Hardware load balancers (1990s) led to software load balancers (HAProxy 2001, NGINX 2002) plus CDNs and WAFs, then application delivery controllers (compression, caching, SSL offload), which produced siloed team ownership across CDN, LB, InfoSec and app-server teams. First-generation API gateways (early 2010s: Kong, Apigee, 3scale, WSO2) added developer portals, SDLC management and L7 routing. Second generation (from about 2015: Zuul, Envoy and its descendants such as Emissary-ingress, Contour, Gloo; Traefik, Tyk, Kong) targeted microservices and developer self-service. If migrating to cloud with many edge layers, reconsider the layers and the teams that own them.

## 10. Verify

- Write down which of the six drivers apply. If none do, a proxy or load balancer was probably enough.
- Search routing configuration for payload-based rules and plug-ins containing domain logic; report each hit.
- Trace one internal call end to end: it must not pass through the public gateway address. Check egress or inter-AZ traffic and tracing spans for the gateway hostname on east-west calls.
- Failover test: kill one gateway instance and one AZ's worth of instances in a staging environment; show that health checks remove them and clients recover; record the sticky-session behaviour.
- Confirm fail-open or fail-closed behaviour of each security component is a recorded decision.
- Confirm an owning team, an on-call rota and published SLOs exist for the gateway.
- Confirm correlation ids are injected at the gateway and appear in downstream logs.
