# Edge hardening, gateway security and zero trust

Contents: what the gateway should do; gateway pitfalls with security impact; failure management; zonal architecture; zero trust principles; mesh plus gateway; network policies; migration crossings; verification.

Sources: Mastering API Architecture ch. 3 (gateway security functions, failure management, pitfalls), ch. 6 (misconfiguration, takeaways), ch. 9 (zonal architecture to zero trust). Items labelled "Adaptation" are not the book's claims. The related ch. 10 section on zero trust is referred to in the notes but was not among the notes read for this skill.

## What a gateway contributes to security

Edge stack layers (CDN, WAF, load balancer, gateway) may be separate products owned by different teams or combined in one. For a small organisation the gateway is the first line of defence; enterprises also have CDN, WAF and DMZ.

| Gateway function | Purpose | Detail in |
|---|---|---|
| TLS termination | Central certificate management; TLS 1.2 or later | `stride-and-owasp-api.md` |
| Authentication and coarse authorisation | Validate tokens, enforce scopes per route | `token-validation-checklist.md`, `authorization-enforcement.md` |
| IP allow and deny lists | Narrow consumers where the set is known | `stride-and-owasp-api.md` |
| WAF (built in or integrated) | Known-pattern request filtering | (this file) |
| Rate limiting and load shedding | Abuse and overload | `rate-limiting.md` |
| API contract validation | Reject requests (and as last resort responses) that violate the OpenAPI contract | `stride-and-owasp-api.md` |
| Header allow-list | Strip unknown and spoofed headers | `stride-and-owasp-api.md` |
| Logging, metrics, correlation ids | Detection and non-repudiation | `stride-and-owasp-api.md` |
| API inventory | Find forgotten versions | `stride-and-owasp-api.md` |

The gateway gives high-level mitigation for many threats at once, but it is not the whole defence. As the system becomes more distributed, consider each service and inter-service communication too.

## Pitfalls that have security consequences

- Business logic in the gateway (the "gateway as ESB" pitfall): plug-ins are fine for authentication, authorisation, filtering and logging; business rules there couple the gateway to services, are fragile and force lockstep deployments. Fine-grained entitlement checks belong in the service.
- Gateway loopback: routing service-to-service traffic out through the public gateway and back in. Traffic leaves the network (performance, security exposure, egress cost), the gateway becomes a bottleneck and a single point of failure, and traces become confusing. Use internal service discovery or a service mesh for internal calls.
- Turtles all the way down: a hierarchy of gateways, or one per concern (a transport-security gateway, an auth gateway, a logging gateway). Symptoms: high cost of change, unclear ownership ("who owns tracing?"), extra hop latency. Security rules scattered like this are hard to audit.
- Routing on request payload: leaks the domain schema into gateway config and costs deserialisation time. Mainly a design concern, but it also makes the gateway parse more untrusted input than it needs to (inferred).
- Do not let the monolith route to the new services in a migration; use the gateway so TLS, authentication and rate limiting are configured at the edge without redeploying the app.
- Build versus buy: generally adopt a gateway rather than build one. Security components are costly to get right (inferred).

## Failure management of the edge

- The gateway is on the critical path. An edge outage makes the whole system unavailable. Typical single points of failure in order: DNS, global or regional layer-4 load balancers, firewall or WAF, then the gateway. More functionality in the gateway means more risk, and its configuration changes with every release.
- Security components may fail open (pass traffic when failing). That is acceptable where availability dominates and unacceptable for financial or government services. Challenge the assumption and decide per service.
- Detect: collect metrics, logs and traces; give every gateway an accountable owning team with on-call; publish SLOs; hold blameless post-mortems.
- Mitigate: high availability through multiple instances (spread across locations or availability zones and regions); a load balancer in front with health checks and failover that are tested regularly, especially for active/passive or leader/node modes. Typical failover problems: lost client state and sticky sessions, poor geographic redirection, cascading failure (a faulty leader election deadlocking all backends).

## Zonal architecture

- Segment infrastructure into logical groups with the same security policy, limiting blast radius. Example in the notes: Log4Shell (CVE-2021-44228) exploited a host; if untrusted requests land in a zone with little high-value data, the blast radius is small and security operations have time to react. Zones cascade, each traversal adds defence in depth, and zones are separated by perimeters (zone interface points) implemented by security or network devices.
- Four typical zones (Canadian ITSG-22): Public Zone (internet, open); Public Access Zone (mediates between operational systems and the public zone, often holds the DMZ); Operations Zone (routine operations; sensitive information but not large repositories or critical apps without extra controls); Restricted Zone (business-critical services and large sensitive repositories, reached from the public zone via the public access zone and operations zone).
- Weakness: "castle and moat". Once inside the perimeter movement is easier because internal traffic is trusted. Cloud weakens the assumptions: location is abstracted, supply chain attacks tamper at build time, provider staff may be malicious. A homogeneous security approach across deployments reduces assumption risk and learning cost.

## Zero trust ("never trust, always verify")

Devices are not trusted by default, even on the corporate network or VPN, or if verified before. Identity and integrity are mutually authenticated regardless of location. Access depends on device identity and health plus user authentication.

Eight principles (UK NCSC-style guidance, as given in the notes):
1. Know your architecture: users, devices, services, data.
2. Know your user, service and device identities.
3. Assess user behaviour, device health and service health.
4. Use policies to authorise requests.
5. Authenticate and authorise everywhere.
6. Focus monitoring on all access: users, devices, services.
7. Do not trust any network, including your own.
8. Choose and design services for zero trust.

Designs that authenticate once at the edge and trust inside conflict with several of these. NIST SP 800-207 (2020) is the reference cited.

## Service mesh plus gateway for zero trust

- The mesh gives uniform modelling of components and traffic, workload identity and certificate management (proving identity), and tracing and monitoring at every point including pod health.
- All ingress gets a strong challenge (OAuth2, `oauth2-and-oidc.md`). In-cluster traffic uses mutual TLS for authentication and authorisation assertions.
- Remaining gap: "do not trust any network". The sidecar is coupled to the application, but nothing is asserted about the platform underneath, so secure that layer as well.

## Service-level authorisation inside the mesh

Source: Mastering API Architecture ch. 4 (read for this skill although it is not one of the listed chapters).

- Ingress and service-to-service traffic need different controls. External callers: authentication focused on users, roles and capabilities, one-way TLS, owned by the gateway and networking team. Internal callers: authentication of services as well as users, authorisation by service identity or network segment plus user roles, mutual TLS that can be made mandatory (strict mode), owned by the platform team.
- Service identity comes from the mesh: each workload gets a certificate (SPIFFE X.509 identity in the Consul example), and the inbound sidecar enforces who may call whom without code changes. A library-based approach differs per language and can be bypassed by leaving the library out.
- Consul-style intentions: first a default deny-all (source `*`, destination `*`, deny), then one explicit allow per required edge; keep them in version control and review any `*` allow. Open Policy Agent is a common alternative policy engine.
- Credentials forwarded downstream: a service that terminates a request and calls another must copy tracing headers, but decide deliberately which auth headers to forward. Forwarding the wrong credential lets one service impersonate another service or user. A bearer token may be sent downstream over secure transport, but the receiving service will check its `aud`, so a token minted for the gateway may be rejected (the book defers token exchange; this skill does not cover it).
- Verify: strict mTLS is on (a plain-text call is refused), a caller not on the allow list is refused, and every allowed edge succeeds.

## Microsegmentation with network policies

- A Kubernetes NetworkPolicy (enforced by a plug-in such as Calico) isolates pods from the platform. Zero-trust default: deny all ingress and egress for every pod (an empty pod selector with both policy types).
- Then add explicit allows: DNS egress (UDP 53) for pods that need service discovery (the mesh uses central DNS); egress from a named source to the namespace it must call (in the case study, the legacy conference system to the `attendees` namespace); ingress from the mesh gateway to target services.
- Every mesh routing rule needs a matching network allow, or the request is blocked even though discovery works. Apply these consistently at release time (another argument for an opinionated platform).
- Multicluster mesh peering lets on-prem and cloud data planes share a combined control plane, giving zero trust across networks and a path to migrate remaining services.

Adaptation: a minimal default-deny manifest. It applies only in its own namespace (repeat per namespace), needs a network plug-in that enforces policies, and once applied the pods lose DNS, so add the allow rules above before or with it. Parsed and checked as valid YAML with the fields the Kubernetes API expects; not applied to a cluster.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-all, namespace: attendees }
spec:
  podSelector: {}
  policyTypes: [Ingress, Egress]
```

## Crossing networks during migration

Start at the edge and work inward: build or duplicate the gateway in the new environment while the old one stays untouched, prove it in isolation, then experiment with routing. With few routes, route from the new gateway to the old (for example a simple HTTP redirect). With many routes crossing networks, or when traffic must not leave once inside, use VPN peering or endpoints or a multicluster mesh. Involve information security: these paths disrupt perimeter defence and zonal architecture. Measure cross-network latency against the SLA before moving a chatty service (inferred).

## Verification

- Scan the public endpoint for TLS versions and ciphers; confirm older versions are refused.
- Send spoofed internal headers from outside; confirm they never reach backends.
- From a pod with no allow rule, attempt to reach another namespace and the internet; confirm the default-deny blocks it, then confirm each explicit allow works and nothing broader does.
- Bypass the gateway (call a service directly from another network segment); confirm the service still rejects an unauthenticated or unauthorised call, or cannot be reached at all.
- Confirm the mesh enforces mutual TLS in the namespace (plain-text call is refused).
- Kill a gateway instance and the limiter store; compare behaviour with the written fail-open or fail-closed decision.
- Check that every public route appears in the API inventory.
