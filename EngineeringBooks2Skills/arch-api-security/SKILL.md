---
name: arch-api-security
description: Threat-modelling and securing APIs, with a procedure and checklists for STRIDE over data flow diagrams, DREAD scoring, the OWASP API Security Top 10 mapped to mitigations, rate limiting and load shedding, API keys, OAuth2 grants, PKCE, JWT validation, scopes, OIDC, object- and function-level authorisation, gateway hardening and zero trust. Use when designing, reviewing or hardening an API or gateway; when the user asks for a threat model, a security review, "is this endpoint safe", "which OAuth flow", "how do I validate this JWT", "add rate limiting", BOLA, mass assignment, CORS or TLS settings; or when exposing an internal API to mobile apps or third parties. For API style, versioning and gateway selection see `arch-api-design`; this skill covers security only.
---

# API security

## Purpose

Use this skill to find what can go wrong with an API before choosing controls, then to pick, apply and test the control that closes each gap. It replaces "add auth and hope" with a loop: model the system, enumerate threats per element, rank them, mitigate with the right standard mechanism, and prove each mitigation with a test or a scan. The source material is two chapters on threat modelling and on authentication and authorisation, plus gateway, cloud-migration and rate-limiter chapters.

## Choose what applies

| The situation | Do this | Read |
|---|---|---|
| "Threat model this", new API or new consumer type, architecture change, exposing an internal API publicly | Run the six-step process with a data flow diagram | `references/threat-modelling-procedure.md` |
| "Review this API/PR/endpoint for security", audit before release | Walk the route inventory and checklists, collect evidence | `references/security-review-checklist.md` |
| Need to know what attack a category implies or how to fix injection, mass assignment, data exposure, logging, misconfiguration | Use the STRIDE and OWASP table | `references/stride-and-owasp-api.md` |
| "Add rate limiting", abuse, DoS, overload, 429s, cost from paid upstream calls | Pick an algorithm and placement, then test | `references/rate-limiting.md` |
| "Which OAuth2 flow/grant", login for mobile/SPA/third party, API keys, refresh tokens, OIDC, SSO | Use the grant chooser | `references/oauth2-and-oidc.md` |
| "Validate this JWT", token middleware, 401 versus 403, expiry, audience | Apply the ordered checks and write the negative tests | `references/token-validation-checklist.md` |
| Users see other users' data, admin endpoints, roles, scopes versus permissions | Enforce at object and function level | `references/authorization-enforcement.md` |
| Gateway, ingress, TLS, CORS, header filtering, fail-open versus closed, mesh mTLS, network policies, cloud move | Harden the edge; move from zonal to zero trust | `references/edge-and-zero-trust.md` |
| Internal-only service, one trusted caller, prototype with no sensitive data | Apply the small subset in "Proportion and limits"; do not run the full process | this file |
| The question is REST versus gRPC versus GraphQL, versioning, contract tests, gateway product choice, deployment strategy | Not this skill | `arch-api-design`, `arch-production-operations` |
| Database isolation anomalies, race conditions on data | Not this skill | `arch-transactions` |
| Application-level injection in non-API code (command line, batch scripts) | Use the injection guidance here as a pattern, but the API-specific controls do not apply | `references/stride-and-owasp-api.md` |

## How to apply

### A. Threat model (when the request is open-ended or the API is going external)

1. State a few objectives in business words (avoid unauthorised access, prevent PII leakage, meet an availability target). Ask the user if you cannot infer them; objectives drive which threats matter.
2. Build the inventory from the repository: routes, OpenAPI, gateway or ingress config, consumers, data stores, outbound calls. Mark which callers are outside your control.
3. Draw a data flow diagram with five element types (external entity, process, data store, data flow, trust boundary). A flow that crosses a boundary gets the most attention. Use several small diagrams over one large one.
4. For each process and each data flow, ask the six STRIDE questions and write either a concrete threat or "not applicable because ...". Map each to an OWASP API category (`references/stride-and-owasp-api.md`).
5. Score with DREAD: five factors, 1 to 10, average. Write the meaning of each score level first, because scores are subjective and a rubric is what makes them comparable between runs.
6. Assign a mitigation and an owner per threat, then validate: each mitigation needs a named test or observation. Plan re-runs for architecture changes.

Worked scoring from the source: DoS against a gateway with no rate limiting scored D8 R8 E5 A10 Disc10, average 8.2, the top item; the fix was rate limiting plus load shedding.

### B. Pick the authentication mechanism

1. Name the callers: end user on first-party client, end user through a third party, system acting on its own.
2. Apply:
   - No human involved: client credentials (or an API key where OAuth2 is unavailable; key of 256 bits, meaning 32 random bytes from a secure random source).
   - Human, client can keep a secret (server-side web app): authorization code.
   - Human, client cannot (mobile, SPA): authorization code with PKCE. PKCE is required for public clients. Update (not in the 2022 book): use PKCE with every authorization code client, confidential ones too, with method S256, and match redirect URIs exactly.
   - Device with no browser: device authorization, only if needed.
   - Implicit: the book says legacy only; Update: current guidance (RFC 9700) advises against it, so disable it. Resource owner password: forbid. HTTP Basic for third parties: refuse.
3. Need user identity in the client: add OIDC (scope `openid`) from an off-the-shelf identity provider. Never build your own, and never use the ID token as an access token.
4. Keep access tokens short (minutes), refresh tokens secret and rotated with reuse detection.
5. Starting with client credentials is often the easiest way to introduce OAuth2 into an existing system.

### C. Validate tokens on every request

Check, in order: TLS, token format and pinned algorithm, signature against the expected issuer's key, `exp` (and require that it is present), `nbf`, `iss`, `aud`, token is an access token, scope for this route. Then do fine-grained authorisation in the service. Full table, sketch and test list: `references/token-validation-checklist.md`.

### D. Authorise at the object and the function

Scope is what the user consented to let the client do; entitlement is what the user may do. Effective permission is the intersection. The gateway can enforce coarse scopes per route; ownership and role checks stay in the service, taken from the validated token identity and never from a client-supplied field. Prefer queries that include the owner or tenant so a forgotten check cannot leak rows. Detail and test matrix: `references/authorization-enforcement.md`.

### E. Limit rate and shed load

1. Separate the two controls: rate limiting keys on the source (user, client, IP, all), load shedding keys on system state (database full, no workers).
2. Place both at the gateway or middleware, never on the client. Also limit internal calls (catches runaway call loops between services).
3. Algorithm quick pick: token bucket as default (bursts allowed, small memory); leaking bucket when the downstream needs a flat rate; fixed window for quotas, accepting up to twice the quota across a boundary; sliding window log when exactness beats memory; sliding window counter for a cheap smooth approximation.
4. Use a shared in-memory store with atomic updates (a Lua script, not read-then-write). Return 429 with limit, remaining and retry-after headers.
5. Decide fail open or fail closed for the limiter and every other edge security component, per service, and write it down.

Detail, numbers and tests: `references/rate-limiting.md`.

### F. Harden the edge and the inside

At the gateway: TLS 1.2 or later terminated centrally, narrow CORS, header allow-list that strips spoofed internal headers, IP allow lists where useful, contract validation, logging with correlation ids, an inventory of everything exposed. Inside: do not trust traffic for being internal; mutual TLS in the mesh, default-deny network policies with explicit allows, and per-service checks. Keep business logic out of gateway plug-ins. Detail: `references/edge-and-zero-trust.md`.

## Decision rules used most

| Rule | Reason |
|---|---|
| Validate at the gateway and again in the service | The gateway rule may be permissive or bypassed; one layer is not a defence |
| Fix mass assignment in the implementation, with input DTOs | The gateway cannot know which fields are server-owned |
| Return only the fields the consumer needs | Clients cannot be trusted to hide data; dev tools show everything |
| Authorisation on every route, deny by default | A single unchecked route is the vulnerability |
| Scope is not entitlement | Consent and permission are different sets; both must hold |
| Short access tokens, rotated refresh tokens | Stolen tokens stay valid until expiry; revocation has a window |
| Never put secrets in JWS claims | Signed is not hidden; anyone holding the token can read it |
| Use `sub` as a stable id, not email | Emails and usernames change |
| Decide fail-open or fail-closed explicitly | Defaults are often allow-all; the right answer depends on the service (financial: closed; public weather: may be open) |
| Misconfigured security is worse than none | Users behave as if protected |
| Re-run the model when the architecture changes | The model reflects a snapshot |

## Mistakes to avoid when changing code

- Adding authentication middleware and calling the job done: authentication says who, not what they may touch. Add the object and function checks in the same change.
- Writing a JWT check that verifies only the signature. Add expiry, issuer, audience and scope, and the tests that fail without them.
- Putting the whole request body into an ORM model "for convenience". Add an input type listing the accepted fields.
- Implementing a limiter as read, compare, write. Use an atomic operation; the race admits more than the limit under load.
- Relying on the gateway alone. Write the service so it would still refuse a bad request if the gateway were bypassed.
- Echoing internal errors to callers while debugging and leaving it on.
- Treating the hidden or undocumented route as protected. Routes are found by scanning; inventory them and guard them.

## Verify

Do not report an API as secure from reading code alone. For every control you add or recommend, state the check that proves it and run it where you can.

1. Build a route table (route, authenticated, scope, object check, function check, validated input, output DTO, rate limited, logged, inventoried). Blanks are findings.
2. Write automated negative tests and run them:
   - Authentication: no token, altered token, expired, signed but with no `exp`, wrong issuer or audience, ID token as access token, `alg` swapped; plus one positive control.
   - Authorisation: user A requests user B's object; ordinary user calls an admin route; scope present but not entitled; entitled but scope missing.
   - Tampering: hostile strings in every free-text field against the service directly; read-only and extra fields in POST and PUT are ignored.
   - Data exposure: diff actual response fields with the contract; trigger an error and confirm no stack trace or version string.
   - Rate limiting: parallel burst at limit minus one admits exactly that many; 429 with headers; store failure matches the documented mode; one key's exhaustion does not affect another.
   - Edge: scanner shows only TLS 1.2 or later; spoofed `X-Impersonate`-style headers never reach the backend; foreign `Origin` is not allowed; direct access to a backend bypassing the gateway still fails.
   - Network: from an unlisted pod, connections to other namespaces fail; listed ones succeed.
3. Compare the routes the running service answers with the catalogue; any extra route is a finding.
4. Retrieve a test action from the logs by correlation id.
5. Present evidence: the route table, test names with results, scanner output, and a list of what you could not verify (WAF or CDN settings outside the repository, identity provider settings).

Done means:
- Objectives, diagram, threat table with scores and rubric exist (or the user declined the full model and the subset was stated).
- Every route has an authentication and authorisation decision recorded and tested.
- Each high-ranked threat has a mitigation and a passing check, or an explicit accepted-risk note with owner.
- Fail-open or fail-closed choices are written down and tested.
- The user has been told which claims are verified, which are read from code, and which are assumed.

## Proportion and limits

- Small or internal APIs: if the API is internal, called by one trusted service, with no sensitive data, do a short pass: authentication and authorisation on each route, parameterised queries, input DTOs, no stack traces, a rate limit at the nearest proxy. Skip DREAD and the full diagram. The book's reason for modelling at all is to put effort where the threats are and avoid security theatre.
- Cost: a full model is time-consuming (it gets easier with practice). Do it when going external, when handling PII or money, or after a structural change; do not rerun it for a field rename.
- Scoring is subjective. DREAD is no longer used by its originator, though widely used; DREAD-D drops discoverability because obscurity is not protection; CVSS fits known vulnerabilities in dependencies. Use whichever the user's organisation already uses and be consistent.
- Dated material: the OWASP list in the source is the 2019 edition; a 2023 edition exists and `references/stride-and-owasp-api.md` gives the mapping. The implicit grant and password grant are historical; later OAuth guidance (RFC 9700) consolidates on code flow with PKCE for all clients, exact redirect matching and, for high-value APIs, sender-constrained tokens. Those later points are marked "Update" in the reference files because the 2022 book does not state them. Algorithm picks for rate limiting come from one interview-style source (numbers like Cloudflare's 0.003% are reported, not re-measured); validate against your own traffic.
- Contested or context-dependent: fail-open versus fail-closed has no universal answer; client credentials versus API keys depends on whether the environment can run OAuth2; whether to return 403 or 404 for foreign objects is policy (adaptation); how much to enforce at the gateway versus the service depends on how distributed the system is.
- Not covered: cryptographic implementation, secrets management, supply-chain tooling, mobile client hardening, and token exchange for propagating identity downstream.

## References

- `references/threat-modelling-procedure.md`: read when asked for a threat model or when scoring risks; has the six steps, DFD elements, DREAD rubric template and output format.
- `references/stride-and-owasp-api.md`: read when mapping a threat to a mitigation or checking injection, mass assignment, data exposure, logging, assets, misconfiguration.
- `references/rate-limiting.md`: read when designing or testing limits; algorithms, buckets, Redis atomicity, headers, failure mode, test table.
- `references/oauth2-and-oidc.md`: read when choosing a grant, using API keys, handling refresh tokens, scopes or OIDC; ends with a table of what changed since the book.
- `references/token-validation-checklist.md`: read when writing or reviewing token middleware and its tests.
- `references/authorization-enforcement.md`: read when checking object-level and function-level access and writing the test matrix.
- `references/edge-and-zero-trust.md`: read when configuring a gateway or ingress, mesh mTLS, network policies, or migrating from perimeter security.
- `references/security-review-checklist.md`: read when asked to review or audit; has per-endpoint and system checklists and the evidence format.

## Sources

- Mastering API Architecture ch. 6 (operational security: threat modelling for APIs): process, STRIDE, DREAD, OWASP mapping.
- Mastering API Architecture ch. 7 (API authentication and authorization): keys, OAuth2, JWT, scopes, OIDC, SAML.
- Mastering API Architecture ch. 9 (API infrastructure to evolve toward cloud): zonal architecture, zero trust, network policies, migration crossings.
- Mastering API Architecture ch. 3 (API gateways): gateway security functions, failure management, pitfalls.
- System Design Interview ch. 4 (design a rate limiter): algorithms, architecture, distributed issues.
