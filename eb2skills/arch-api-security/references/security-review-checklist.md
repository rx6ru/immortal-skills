# Security review checklist for an API

Contents: how to run a review; per-endpoint checklist; gateway and edge checklist; token and identity checklist; availability checklist; logging checklist; internal and zero-trust checklist; evidence table; reporting format.

Sources: derived checklists in Mastering API Architecture ch. 6 and ch. 7, ch. 9 decision aid, and System Design Interview ch. 4 verification notes. Each item points to the reference holding the detail. Items beyond the notes' own lists are adaptation.

## How to run a review

1. Establish the consumers (public clients, third parties, internal services) and the assets (PII, money, admin functions). This sets which items matter most.
2. Build the route inventory: every route from router, OpenAPI file, gateway config, ingress. A route absent from the inventory but present in the code is already a finding.
3. Walk the per-endpoint table for each route. Fill every cell with yes, no, or not applicable plus a reason.
4. Walk the edge, token, availability, logging and internal sections once for the whole system.
5. Rank findings with the DREAD rubric (`threat-modelling-procedure.md`) when the user needs priorities.
6. Report findings with evidence (below). Separate "verified by test or scan" from "read in code" from "assumed".

## Per-endpoint

| Question | Fail signal | Detail |
|---|---|---|
| Authenticated? | Route reachable with no or an invalid credential | `token-validation-checklist.md` |
| Scope required for route and verb? | Any valid token works | `authorization-enforcement.md` |
| Object-level check (owner or tenant) on every id taken from the request? | Lookup by id alone | `authorization-enforcement.md` |
| Function-level check for privileged operations? | Admin route protected only by being hidden or by client UI | `authorization-enforcement.md` |
| Input validated against the contract at the edge and again in the service? | Only one of the two | `stride-and-owasp-api.md` (tampering) |
| Parameterised queries and no string-built commands? | Concatenated SQL, shell, filter expressions | `stride-and-owasp-api.md` |
| Fetches a caller-supplied URL? (Adaptation, OWASP 2023 SSRF) | Any URL accepted, internal addresses reachable | `stride-and-owasp-api.md` |
| Request body bound to an explicit input DTO with allow-listed fields? | Whole body bound to a persisted entity | `stride-and-owasp-api.md` (mass assignment) |
| Response built from an explicit output DTO? | Entity serialised directly; internal or sensitive fields visible | `stride-and-owasp-api.md` (data exposure) |
| Errors scrubbed? | Stack trace, server version, SQL error in body | `stride-and-owasp-api.md` |
| Rate limited, with a key that matches the threat? | No limit, or IP-only on an authenticated route | `rate-limiting.md` |
| Logged with a correlation id, without secrets? | No audit trail, or tokens and passwords in logs | `stride-and-owasp-api.md` (repudiation) |
| Listed in the API inventory and owned? | Beta, old-version or debug routes with no owner | `stride-and-owasp-api.md` (assets) |

## Gateway and edge

| Question | Detail |
|---|---|
| TLS 1.2 or later only; older versions disabled; certificates managed centrally? | `stride-and-owasp-api.md` |
| CORS configured narrowly, with named origins? | `stride-and-owasp-api.md` |
| Header allow-list in place; spoofable internal headers stripped? | `stride-and-owasp-api.md` |
| IP allow lists where the consumer set is known? | `stride-and-owasp-api.md` |
| DDoS protection (CDN or specialist) attached to public names? Load limits known from a load test? | `rate-limiting.md` |
| Fail-open or fail-closed decided and written down for each security component? | `edge-and-zero-trust.md` |
| Gateway has an owning team, an SLO, redundancy, tested failover? | `edge-and-zero-trust.md` |
| No business logic in gateway plug-ins; no loopback traffic; no stack of single-purpose gateways? | `edge-and-zero-trust.md` |
| Direct access to backends from outside the gateway blocked or independently protected? | `edge-and-zero-trust.md` |

## Tokens and identity

| Question | Detail |
|---|---|
| Right grant for each client type (public client: code with PKCE; machine: client credentials)? | `oauth2-and-oidc.md` |
| Implicit and password grants disabled, or a recorded exception? | `oauth2-and-oidc.md` |
| PKCE on every authorization-code client; redirect URIs matched exactly? (Update, later than the book) | `oauth2-and-oidc.md` |
| HTTP Basic refused for third-party access? | `oauth2-and-oidc.md` |
| Signature, `exp` (required to be present), `nbf`, `iss`, `aud`, scope checked on every request; algorithm pinned; keys taken only from the configured issuer key set? | `token-validation-checklist.md` |
| ID tokens rejected at the resource server? | `token-validation-checklist.md` |
| Access token lifetime in minutes; refresh tokens rotated with reuse detection; revocation tested? | `oauth2-and-oidc.md` |
| No secrets or PII in JWS claims; `sub` is a stable id? | `oauth2-and-oidc.md` |
| API keys 256-bit random, rotated, scoped per app, not used to identify end users? | `oauth2-and-oidc.md` |
| Identity provider is a product, not home-grown? | `oauth2-and-oidc.md` |

## Availability

| Question | Detail |
|---|---|
| Rate limits and load shedding both exist? Internal calls limited too? | `rate-limiting.md` |
| Atomic counter updates (Lua script or equivalent); shared store across limiter nodes? | `rate-limiting.md` |
| 429 plus rate-limit headers; clients told how to back off? | `rate-limiting.md` |
| Limiter store failure handled by a deliberate choice, with the API staying up? | `rate-limiting.md` |

## Logging and monitoring

| Question | Detail |
|---|---|
| Requests, payload details sufficient for compliance, and responses logged at the gateway and services? | `stride-and-owasp-api.md` |
| Logs searchable and extractable across time, and tested like a recovery plan? | `stride-and-owasp-api.md` |
| Alerts on authentication failures, 403 spikes, unexpected endpoints, throttle rate per rule? | `rate-limiting.md`, `stride-and-owasp-api.md` |

## Internal traffic and zero trust

| Question | Detail |
|---|---|
| Internal calls authenticated (mutual TLS or tokens) and not merely trusted for being internal? | `edge-and-zero-trust.md` |
| Default-deny network policy with explicit allows; each mesh route matched by a network allow? | `edge-and-zero-trust.md` |
| Platform beneath the sidecar secured (do not trust any network)? | `edge-and-zero-trust.md` |
| Dependencies and vendor products tracked for published vulnerabilities, and impacted software can be rebuilt quickly? | `threat-modelling-procedure.md` |

## Evidence the user can check

| Claim | Acceptable evidence |
|---|---|
| "Authentication is required everywhere" | Route table plus a test calling every route unauthenticated |
| "Object-level authorisation works" | Cross-user tests per object route, named and passing |
| "Mass assignment prevented" | Tests posting read-only fields; DTO classes in the diff |
| "TLS is hardened" | Scanner output listing accepted protocol versions |
| "Rate limiting works" | Concurrency test results, a captured 429 with headers, the store-failure test |
| "Headers stripped" | A request with spoofed headers and the backend log showing absence |
| "Network default-deny" | A blocked connection from an unlisted pod and a permitted one from a listed pod |
| "Logs are usable" | A retrieval of a test action by correlation id |

## Reporting format

For each finding: route or component; STRIDE letter and OWASP category; what was observed and how (test, scan, or code reading); impact; DREAD score if requested; recommended fix with the reference file to read; how to verify the fix. List what you could not check (for example WAF settings that live outside the repository) so the user knows the review's edges.
