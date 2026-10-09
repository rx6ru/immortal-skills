# STRIDE per category, mapped to the OWASP API Security Top 10

Contents: the mapping table; one entry per STRIDE category (threat, how it shows in an API, mitigation, where to enforce, verify); misconfiguration; the OWASP list as a lookup.

Source: Mastering API Architecture ch. 6. The OWASP list the book uses is the 2019 edition; it is revised periodically, so check the current edition before quoting it to the user. Items marked "Adaptation" are additions for modern code, not the book's claims. Items marked "(inferred)" are the note-taker's inference.

## Mapping

| STRIDE | Violates | OWASP API category in the book | Core mitigation |
|---|---|---|---|
| Spoofing | Authentication | Broken User Authentication | Authenticate every request using a correct flow (`oauth2-and-oidc.md`) |
| Tampering | Integrity | Injection; Mass Assignment | Validate at gateway and again in the service; allow-listed bindable fields |
| Repudiation | Non-repudiation | Insufficient Logging and Monitoring | Log and monitor at gateway and services; retrievable over time |
| Information disclosure | Confidentiality | Excessive Data Exposure; Improper Assets Management | Return only needed fields; inventory every exposed API and version |
| Denial of service | Availability | Lack of Resources and Rate Limiting | Rate limiting, load shedding, DDoS protection, load testing |
| Elevation of privilege | Authorisation | Broken Object Level Authorization; Broken Function Level Authorization | Check authorisation on every object and function (`authorization-enforcement.md`) |
| (cross-cutting) | Hardening | Security Misconfiguration | TLS 1.2+, CORS, header allow-list, fail-closed defaults, IP allow lists |

## Spoofing

- Threat: a caller pretends to be another user or system.
- In an API: missing or weak authentication on some route; accepting HTTP Basic so a third party handles user passwords; API keys used to assert who the end user is; ID tokens or unvalidated tokens accepted.
- Mitigate: authenticate every request; use OAuth2 with the grant that matches the client type; keep tokens short lived; validate every token (`token-validation-checklist.md`).
- Verify: call each route with no credential, a malformed one, an expired one and one issued for a different audience; all must be rejected with 401 and no data.

## Tampering

Two distinct threats.

### Payload injection

- Any user input can be an injection vector, not only SQL.
- Defence in depth, both lines required: (1) validate requests at the gateway against the OpenAPI contract (for example a name field letters only, age a positive integer, a free-text profile with a restricted character set); (2) still sanitise and validate in the backend, because the gateway rule may be permissive and may be bypassed ("trust, but verify"). Use prepared statements.
- The book's example: a profile free-text field that legitimately allows punctuation receives `Hax; DROP ALL TABLES; --`. The gateway passes it; only the prepared statement stops it.
- Adaptation (parameterised query in two languages):

```ts
// TypeScript (node-postgres): value travels separately from SQL text
await db.query("UPDATE attendee SET profile = $1 WHERE id = $2", [profile, id]);
```
```python
# Python (DB-API): same idea
cur.execute("UPDATE attendee SET profile = %s WHERE id = %s", (profile, id))
```

- Verify: send hostile strings to every free-text and identifier field; test the service directly (bypassing the gateway) to prove the backend validates independently. Grep for string concatenation or template literals that build SQL, shell commands or query filters from request data.

### Mass assignment

- Threat: client JSON is bound straight onto an entity (ORM or Active Record object), so an attacker overwrites fields that should be read-only. Example: a GET shows a `devices` list; the attacker PUTs an altered `devices`.
- Cannot be solved at the gateway. Fix in the implementation: never bind server-owned properties, use separate request DTOs with an explicit allow-list of fields, and do not expose the database model as the API.
- Verify (inferred): write tests that POST or PUT extra and read-only fields (role, owner, id, price, devices) and assert they are ignored or rejected and unchanged afterwards. Grep for "bind whole body to model" patterns: `Object.assign(entity, req.body)`, `Model(**request.json)`, `@RequestBody Entity` that is the persisted class, `update_attributes(params)` without strong parameters.

## Repudiation

- Threat: an actor denies an action and there is no trace.
- Mitigate: log requests, payloads and responses in enough detail for compliance. The gateway is the central point to capture it, services add their own. Know how to store, search and extract logs across time. Test the logging periodically, in the way disaster recovery and business continuity plans are tested.
- Related: inject a correlation identifier at the gateway (for example B3 trace headers) and propagate it upstream so logs and traces from one request can be joined.
- Care: do not log credentials, tokens or unnecessary PII (Adaptation); the log store is itself an information-disclosure target.
- Verify: perform an action as a known test user, then retrieve the record by correlation id and show who, what, when and the outcome. Repeat on a restored or archived log window.

## Information disclosure

### Excessive data exposure

- Threat: the API returns whole objects and relies on the client to hide fields. Browser developer tools show everything. Example: a list endpoint that returns passport numbers. APIs first written for internal, trusted clients are often exposed publicly later.
- Mitigate: return only the fields the consumer needs, built from an explicit response DTO. Gateway response validation against the contract is a last-resort safety net; responsibility stays with the API builders. Also avoid leaking server versions and stack traces in error responses.
- Verify: for each endpoint, diff the actual response fields against the documented contract; assert that a low-privilege token never sees sensitive fields; trigger an error and check the body carries no stack trace or version string.

### Improper assets management

- Threat: old or forgotten versions stay reachable, for example an early version that returns all fields, or a forgotten `/beta/attendees`.
- Mitigate: keep a registry of everything the gateway exposes; alert on requests to unexpected endpoints; use an API management portal as the catalogue; retire versions through a lifecycle process (see `arch-api-design` for versioning and deprecation).
- Verify: compare the routes the running service actually answers with the routes in the catalogue or OpenAPI document; any difference is a finding. Check gateway route tables for paths with no owner.

## Denial of service

- Distinguish rate limiting (rejecting based on properties of an individual request source: user, client app, IP, client id, or all equally) from load shedding (rejecting based on overall system state: database at capacity, no worker threads left). Many servers and gateways ship with neither, so failure behaviour is undefined until you load test.
- Place limits at the gateway and also on internal calls: internal limits catch "friendly-fire" DoS, where circular dependencies between services create runaway call loops, and give you error signals.
- Very large attacks need a specialist: CDN or cloud DDoS protection attached to the public name or IP.
- Decide fail open or fail closed deliberately for each edge component (an overloaded firewall may default to allow-all). Financial APIs: fail closed. A public weather API may fail open. An emergency medical history service might prefer open. No universal answer; record the choice.
- Algorithms, headers and distributed pitfalls: `rate-limiting.md`.
- Verify: load test to find the real limits, then show the 429 behaviour and the shed behaviour; kill the limiter's store and observe the chosen failure mode.

## Elevation of privilege

- Broken Object Level Authorization: can user A read object B by changing an id?
- Broken Function Level Authorization: can an ordinary user call an admin function?
- Both are fixed by checking authorisation at every endpoint, on every object and function. Detail, placement and tests: `authorization-enforcement.md`.

## Security misconfiguration (the gateway is the front door, so review it closely)

A misconfigured control can be worse than none, because users then behave as if they were safe.

| Control | Rule | Verify |
|---|---|---|
| TLS termination | Terminate at the gateway for central certificate management; require TLS 1.2 or later; older versions have known issues, so enabling them is a conscious, recorded exception | Run a scanner such as `nmap --script ssl-enum-ciphers` or `testssl.sh` (Adaptation) and confirm older protocol versions are refused |
| CORS | Browsers send an OPTIONS pre-flight and obey the origin allow-list the server returns; configure narrowly, name origins, avoid wildcard with credentials (narrow configuration is inferred) | Send a request with a foreign `Origin` header and check the response does not echo it as allowed |
| Header allow-list | Attackers add unknown or malformed headers; keep an allow-list and strip everything else, including spoofed internal headers such as `X-Assert-Role: Admin` or `X-Impersonate: Admin` | Send those headers from outside; confirm backends never see them |
| IP allow lists | Use where the consumer set is known (partner back ends, admin routes) | Call from a non-listed address |
| Defaults | Fail-closed defaults; verbose errors off | Review config for debug flags and default credentials |

## The OWASP list as a lookup (names as used in the book's mapping)

Broken Object Level Authorization; Broken User Authentication; Excessive Data Exposure; Lack of Resources and Rate Limiting; Broken Function Level Authorization; Mass Assignment; Security Misconfiguration; Injection; Improper Assets Management; Insufficient Logging and Monitoring. This is the 2019 list; the book says to check for updates. Use it both as inspiration when hunting threats and as a source of mitigations; it is not exhaustive.

## Update: the 2023 edition of the list

The book predates the 2023 revision (not in the notes; from the published OWASP list, so confirm against owasp.org before quoting). Mapping from the 2019 names above:

| 2023 entry | Relation to the 2019 list | Where to look |
|---|---|---|
| API1 Broken Object Level Authorization | Same | `authorization-enforcement.md` |
| API2 Broken Authentication | Renamed from Broken User Authentication | `oauth2-and-oidc.md`, `token-validation-checklist.md` |
| API3 Broken Object Property Level Authorization | Merges Excessive Data Exposure and Mass Assignment | Output and input DTOs, sections above |
| API4 Unrestricted Resource Consumption | Renamed from Lack of Resources and Rate Limiting; also covers cost per call (SMS, paid upstreams) and payload size limits | `rate-limiting.md` |
| API5 Broken Function Level Authorization | Same | `authorization-enforcement.md` |
| API6 Unrestricted Access to Sensitive Business Flows | New: legitimate flows (buying, booking, sign-up) abused at scale by automation | Per-flow limits and bot defences; rate limit by account or device, not only IP |
| API7 Server Side Request Forgery | New | See below |
| API8 Security Misconfiguration | Same | Misconfiguration table above |
| API9 Improper Inventory Management | Renamed from Improper Assets Management | Assets section above |
| API10 Unsafe Consumption of APIs | New: trusting data from third-party APIs you call | Validate responses from upstreams like any input; set timeouts; do not follow redirects blindly |

Injection and Insufficient Logging and Monitoring are no longer separate entries in 2023; the controls in this file for them still apply.

SSRF (Adaptation, not from the book): any endpoint that fetches a URL supplied by the caller (webhooks, image import, link preview) can be pointed at internal addresses or cloud metadata services. Allow-list destination hosts, resolve DNS and reject private, loopback and link-local ranges after resolution, do not follow redirects to unchecked hosts, and deny the workload network access to metadata endpoints it does not need (the default-deny policy in `edge-and-zero-trust.md` helps). Verify: submit `http://127.0.0.1/`, a private-range address and a hostname resolving to one, and confirm each is refused.
