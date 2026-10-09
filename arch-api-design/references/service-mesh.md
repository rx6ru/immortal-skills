# Service mesh: service-to-service traffic management

Contents: 1. Mesh or libraries; 2. What a mesh is; 3. Five reasons to use one; 4. North-south versus east-west; 5. Implementation styles; 6. Feature configurations; 7. Failure and pitfalls; 8. Selecting; 9. When not to adopt; 10. Verify

Sources: Mastering API Architecture (MAA) ch. 4 (both parts), ch. 3, ch. 5, ch. 10; DDIA 2e ch. 5 (load balancing options). Tool details (Istio CRDs, Consul intentions, Cilium, Traffic Director, SMI) are 2022 snapshots; the principles persist. Check the current API of whichever mesh the codebase uses.

## 1. Mesh or libraries

Every application makes service-to-service calls, and the traditional answer is a language-specific library or SDK. Both can work. Decision (MAA Table 4-1):
- Single mandated language or framework, simple routing for REST/RPC: use language libraries.
- Always the simplest solution for the requirements, with an eye on the immediate future and known requirements.
- Advanced cross-functional requirements (authn, authz, rate limiting), particularly across different languages and stacks: a mesh may be best.
- Do due diligence on existing mandates.

## 2. What a mesh is

A pattern for managing all service-to-service communication in a distributed system. It differs from a gateway in two ways: it is optimised for east-west traffic inside a cluster or data centre, and the caller is typically a more-or-less known internal service rather than an external device. It is not "mesh networking" (a lower-level IoT topology); it sits on top of existing network protocols.

- Control plane (operators define routes, policies, telemetry; always deployed separately in a mesh) and data plane (does the work). In Kubernetes, an operator writes custom resources (for example "the Attendee service may call the Session service"), applies them with kubectl or a CD pipeline, and a mesh controller instructs the data plane, which is a sidecar proxy beside each service. Traffic passes through the sidecars transparently.
- The proxy accepts all inbound and initiates all outbound requests. Mapping is typically one to one, so a mesh proxy does not aggregate calls across services (unlike a gateway). It provides identity verification, rate limiting, timeouts and retries, metrics, logs, traces. Some meshes add a service catalog, a portal and policy auditing.
- A full proxy keeps two network stacks (client side and server side), so it can observe, change or drop traffic in both directions, at the cost of more resources and latency.
- Meshes are often deployed several times, one per network segment or business domain. They reach outside through a mesh, terminating or transit gateway, which lacks full API gateway functionality; whether that is north-south or east-west is debatable and affects security policy.
- The mesh operates between OSI L3 and L7. In Kubernetes it can override default service-to-IP resolution, add transparent cross-cluster routing, L3/L4 and L7 security (identity, authorisation), L7 load balancing (important for multiplexed keep-alive protocols such as gRPC/HTTP2, where L4 balancing pins all requests of a connection to one backend), and service-level observability.

## 3. Five reasons to use a mesh

1. Fine-grained routing, reliability and traffic management. Internal services are more numerous and change faster than external APIs, so a gateway per internal service would cost too much compute and maintenance.
   - Transparent routing and name normalisation: hard-coded IPs force redeployments; the mesh looks up locations dynamically and maps one logical name (`sessions-service`) to different real locations in prod and staging.
   - Reliability: retries, timeouts, circuit breakers, bulkheads and fallbacks implemented consistently across languages, with health information shared mesh-wide. Example: after a keynote thousands of attendees check schedules; configure timeouts and retries plus a circuit breaker so repeated failures of Attendee to Session fail fast, and the mobile app falls back to the full schedule instead of the personal one.
   - Advanced routing: traffic shaping (delaying some traffic to a desired profile, for example by service identity or a header such as free versus paying tier) and traffic policing (monitoring against a contract and discarding or marking violators, which stops a malfunctioning internal service from flooding others or a fragile data store). Services may also self-shape. Splitting and mirroring shift traffic gradually between versions (`release-strategies.md`).
2. Transparent observability at L7 and L4 without embedding agents in every application. Limits: still instrument services for business KPIs; the mesh gives call count, latency and error rate, you add business metrics.
3. Security: the data plane sits in the path of all traffic, so it can enforce identity (for example SPIFFE), certificates and rotation, mutual TLS, and service-level authn/authz without code changes. Library approaches differ per language and are easy to bypass by omitting the library.
4. Cross-language cross-cutting concerns implemented once ("infrastructure dependency injection"), so Attendee can be rewritten in another language and keep consistent behaviour.
5. Separate ingress from service-to-service management. The north-south/east-west line is fuzzy, depending on what counts as "your systems"; some argue the distinction is largely obsolete.

## 4. North-south versus east-west (MAA Table 4-3)

| | Ingress (north-south) | Service to service (east-west) |
|---|---|---|
| Traffic source | External (user, third party, internet) | Internal (within the trust boundary) |
| Destination | Public/business-facing API or website | Service or domain API |
| Authentication | User focused | Service (machine) and user focused |
| Authorisation | User roles and capabilities | Service identity or network segment, plus user roles |
| TLS | One-way, often enforced | Mutual, can be mandatory (strict mTLS) |
| Implementations | API gateway, reverse proxy | Service mesh, application libraries |
| Owner | Gateway, networking, ops | Platform, cluster, ops |
| Users | Architects, API managers, developers | Developers |

So the control planes need different capabilities: the Session team states that only the legacy app and the Attendee service may call it; the Attendee team does not state which external systems may call its public API (the gateway or networking team does).

## 5. Implementation styles

The 8 fallacies of distributed computing still hold, and the "standardized RPC" prerequisite for microservices says TCP/IP alone is not enough; you need a networking layer that offsets them (retries, timeouts, discovery, circuit breaking, identity). Keep reminding teams that the network is unreliable and latency is not zero.

1. Libraries (Finagle, Netflix OSS/Hystrix; both now deprecated). Full application and traffic insight, easy context propagation. Language specific; polyglot means porting, building, maintaining and upgrading each library in lockstep; subtle behaviour differences per runtime; hidden total cost.
2. Sidecars (Airbnb Synapse/Nerve, Netflix Prana, Linkerd, Envoy, Istio). A companion proxy per service instance sharing the network namespace; the service talks only to its local proxy. Adding a central control plane gives access control and metrics that need cross-service coordination. Most common; the book recommends it for the modest-scale case study. Cost at scale: 20 services x 5 pods is 100 proxies; memory per proxy grows with the number of services it must know (Istio tuned from about 1 GB to 60-70 MB per proxy; still about 2 GB per node in the 100-proxy, 3-node example). Plan the resource budget and scope proxy configuration to the peers each service needs.
3. Proxyless gRPC (2021): the gRPC library is the data plane, configured by an external control plane over the open xDS APIs; hybrids with sidecars are supported. Good for very large meshes, high-performance gRPC with fewer hops, environments where a second process cannot run, and migrating away from a mesh. Excluded in the case study because REST is also used internally.
4. Sidecarless or kernel (eBPF, Cilium): programs attached to kernel events run for every container on a node, cannot be bypassed by an app, and cut latency; Cilium can run one shared Envoy per node. Young technology in 2022; the principle is moving the data plane to node-level infrastructure to cut per-pod cost.

Taxonomy (MAA Table 4-4):

| Aspect | Library / proxyless | Sidecar proxy | OS / kernel |
|---|---|---|---|
| Language support | Single-language libraries, platform agnostic | Language agnostic, wide platform | Language agnostic, OS level |
| Runs | Inside the app | Separate process alongside | In the kernel |
| Upgrade | Rebuild and redeploy the app | Redeploy sidecars (often zero downtime) | Update or patch the kernel program |
| Observability | Full app and traffic insight, easy context propagation | Traffic only; context propagation needs language support | Traffic only; same caveat |
| Security threat model | Library runs in the app process | Sidecar shares process and network namespace | App talks to the OS via syscalls |

Any non-library mesh cannot propagate trace headers by itself: applications must forward them.

Other load-balancing and discovery options from DDIA 2e ch. 5, for orientation: hardware LB (simple, special hardware), software LB such as NGINX or HAProxy (best for simple deployments, a separate hop), DNS with several IPs (simple, but caching gives stale IPs when servers churn), service discovery such as etcd or ZooKeeper (dynamic environments, extra system to run), service mesh (mTLS and observability handled, but complex; choose in highly dynamic Kubernetes-style environments).

## 6. Feature configurations (what each looks like; Kubernetes examples)

Choose one mesh in a real stack; the book shows three only for teaching.

- Routing (Istio): enable automatic sidecar injection per namespace. A VirtualService holds routing rules for when a host is addressed; a DestinationRule holds policy after routing (load balancing, connection pool, outlier detection) and defines subsets by pod labels (v1, v2). Declaring both subsets is the foundation for canary routing (add weighted routes).
- Observability (Linkerd): telemetry on after install; golden metrics (request volume, success rate, latency distributions) for HTTP, HTTP/2 and gRPC, TCP bytes, per service, per caller/callee pair, per route (service profiles); topology graph; live request sampling. Automate detection of invalid service-to-service traffic in production rather than relying on people looking at dashboards.
- Segmentation (Consul): replace firewall rules and routing tables with intentions by service name, enforced by the inbound sidecar; caller identity is the mTLS client certificate (SPIFFE X.509 per service). An intention has a source (or `*`), a destination (or `*`), allow or deny, and an optional description. Pattern: apply default deny-all first (`* -> *` deny), then add explicit allows per required edge (legacy to attendee, legacy to sessions, attendee to sessions, sessions to attendee). Anything else is dropped. OPA is a popular alternative policy engine, for example with Istio.

## 7. Failure and pitfalls

The mesh is on the hot path of nearly every request. An outage takes down everything in its blast radius, and the more functionality you depend on, the bigger the risk. Because mesh configuration drives releases it changes constantly, so detect and roll back bad configuration quickly. Reuse the gateway single-point-of-failure mitigations (`gateways.md`). The control plane is the most vulnerable component: secure, monitor and run it HA.

| Anti-pattern | Description | Fix |
|---|---|---|
| Mesh as ESB | Plug-ins or Wasm filters tempt teams to transform payloads or run business logic in the mesh | Keep smarts out of infrastructure |
| Mesh as gateway | Adopting a mesh only to use its ingress gateway; those are less rich than an API gateway and you pay mesh cost without mesh benefits | Pick a real API gateway for ingress and API management |
| Too many networking layers | A mesh stacked on existing abstractions: stripped headers, extra proxy hops, duplicated functions (circuit breaking in two layers) | Coordinate dev, platform/SRE and network teams; decide which layer owns which function |

## 8. Selecting a mesh

Start from requirements (current pain and roadmap), not vendor marketing: incremental release, reliability, multi-language support, observability, security, maintainability, extensibility. Generally adopt and standardise on open source or commercial rather than building; pitfalls are underestimated total cost, opportunity cost (a custom mesh is competitive advantage only for cloud and platform vendors), the operational cost of several implementations solving the same problem, and losing track of a fast-moving landscape. Legacy estates usually contain partial meshes (libraries in one department, an ESB elsewhere, simple proxies): inventory them. Choosing to implement a mesh, and which one, is a hard-to-reverse decision (MAA ch. 4, ch. 10). The checklist is Table 4-5 in `guideline-tables.md`.

Direction of travel (2022 view, dated): mesh capabilities are being pushed back into shared libraries (gRPC) or the kernel, and may merge into vendor platform offerings. If so prefer the mesh integrated into your vendor stack; the Service Mesh Interface was archived later.

## 9. When not to adopt a mesh (derived in the notes)

- The scale and need are modest and a few libraries or the existing platform suffice (single language, simple routing).
- You only need ingress: buy an API gateway.
- The team cannot operate a control plane.
- Existing networking layers already provide the functions (avoid duplication).
- Polyglot with REST internally rules out proxyless gRPC.

## 10. Verify

- No internal call traverses the public gateway address (check egress and inter-AZ traffic and traces).
- Strict mTLS is on, and a caller that is not on the allow list is rejected: for each allowed edge test success, for a non-listed edge test rejection. Intentions or policies live in version control; every `*` allow is reviewed.
- Circuit breaker and fallback behave under a load spike (performance or chaos test in a like-for-like environment); the mobile or caller fallback is observed, not assumed.
- Sidecar resource budget computed (proxies x memory per proxy) and compared with node capacity.
- The control plane runs HA and has monitoring, and a mesh configuration change can be rolled back quickly (rehearse it).
- Services forward trace headers; confirm one trace id spans two hops.
