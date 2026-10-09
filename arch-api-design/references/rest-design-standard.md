# REST design standard: resources, collections, pagination, filtering, errors, naming

Contents: 1. Why adopt a written standard; 2. Create and identify; 3. Naming; 4. Collections and pagination; 5. Filtering; 6. Errors; 7. Statelessness, caching, headers; 8. Review checklist; 9. Compatibility traps in JSON

Sources: Mastering API Architecture (MAA) ch. 1 (uses the Microsoft REST API Guidelines, with RFC-2119 MUST/SHOULD wording), ch. 2 (component test checklist), ch. 5 (cache and header gotchas); DDIA 2e ch. 5.

## 1. Why adopt a written standard

REST is loose. Anything it leaves unspecified (errors, pagination, naming, compatibility) gets decided ad hoc, produces inconsistency and causes accidental breaking changes. Adopting an existing guideline shortcuts the design decisions. The book uses the Microsoft REST API Guidelines; other standards are acceptable. Pick the one that fits the organisation's culture and existing API inventory, extend it with domain or industry amendments, adopt it early (retrofitting for consistency later breaks compatibility), and be critical of existing APIs: are they in a format consumers can understand, or does it need more work? (MAA Table 1-2, reproduced in `guideline-tables.md`.)

If the codebase already has an API standard, follow it and apply the rules below only where it is silent.

## 2. Create and identify

- Create with `POST /attendees`; respond `201 Created` with a `Location` header pointing to the new resource (for example `/attendees/1`).
- Keep personal data out of URLs (Microsoft guideline 7.9 as cited): paths and query parameters get cached and written to server logs. Use an opaque generated id, not an email address, as the resource id.
- Use the right verb for the effect (level 2): GET must not change server state; PUT and DELETE on the same URI. See `choosing-an-api-style.md` for the maturity levels.
- Model resources, not procedures. Hide the backing store; do not expose internal tables or abstractions (information hiding, MAA ch. 8).

## 3. Naming

- Even a rename is a breaking change. Names are therefore a design decision with a long tail.
- Start from the standard's short list of names and extend it with an organisation-wide common domain data dictionary. Reuse known industry terminology.
- Consistency across all company APIs lets consumers connect responses from different APIs.

## 4. Collections and pagination

- Return an object that wraps the array, not a bare array. Shape from the guideline: a `value` array plus an opaque next-page link (`@nextLink`). Reason: converting a bare array into an object later, to add pagination, breaks compatibility.
- Pagination means a partial result plus instructions (an opaque next link) for the next page. Design for it from day one, even if the first release returns everything.
- The next link is opaque to the consumer so the producer can change the paging mechanism without breaking clients.

Sketch:

```json
{ "value": [ { "id": "a1", "givenName": "Jim", "familyName": "Smith" } ],
  "@nextLink": "https://api.example.com/attendees?page=opaque-token" }
```

## 5. Filtering

- The guideline uses OData-style expressions: `GET /attendees?$filter=displayName eq 'Jim'`.
- You need not implement everything up front, but design in line with the standard so features can be added later without breaking consumers.
- If consumers need cross-service filtering and composition, GraphQL is stronger (see `choosing-an-api-style.md`).

## 6. Errors

Principle: consumers should be able to write one piece of code that handles all errors. Define the error format up front and share it across APIs.

| Rule | Reason |
|---|---|
| Use accurate status codes | Consumers build logic on them |
| Never return an error inside a 2xx | Breaks that logic and monitoring |
| Avoid relying on 3xx for errors | Some client libraries follow redirects automatically |
| 4xx: the message field says exactly what went wrong | Cuts the support load |
| 5xx: server failure; document what an unexpected failure means | Some clients retry automatically; in payments, does a 500 mean the charge happened or not? |
| Never leak stack traces or sensitive information to external consumers | The guideline's error structure has an InnerError for detail; strip it before external responses |

Operational note from ch. 5: a run of 403s may be an attacker probing and many 401s from a partner system may mean a stolen token or compromised vendor, so error classes are also monitoring signals.

## 7. Statelessness, caching, headers

- Requests are stateless: the consumer sends all context; the producer does not remember previous requests.
- Give cache hints with HTTP headers. Caches hide failures: in the book's incident, a canary looked fine, the rollout proceeded, then the caller's proxy cache expired and 500s appeared everywhere. During rollout validation, send `Cache-Control: no-cache, no-store` on GETs so a cached good response cannot mask a broken new version (see `release-strategies.md`).
- Services that terminate a request and call another service must copy tracing and correlation headers downstream. Decide deliberately which auth headers are safe to forward (security details in `arch-api-security`).

## 8. Review checklist for a REST API design

1. Resource-oriented URIs, no PII in them, opaque ids.
2. Create returns 201 plus Location.
3. Collections return a wrapper object with an opaque next link.
4. Filtering and ordering follow the chosen standard, even if unimplemented.
5. One error shape, accurate status codes, no 2xx errors, no stack traces externally.
6. Names come from the shared domain dictionary and the standard.
7. Documented meaning of 5xx for non-idempotent operations.
8. An OpenAPI document exists and the diff gate is in the pipeline (`specification-and-versioning.md`).
9. Component tests cover the checks in `api-testing-and-contracts.md` (status codes, auth failure, empty collection, content negotiation, Location).

## 9. Compatibility traps in JSON (DDIA 2e ch. 5)

- JSON has no int/float distinction and specifies no precision. Integers above 2^53 lose precision in IEEE-754 doubles (JavaScript). One social network returned post ids twice, as number and as decimal string. Send large ids as strings.
- No binary strings: Base64 adds about 33 percent and the schema must say to decode it.
- Only add optional request parameters and new response fields; clients must ignore unknown fields; never change the meaning or type of an existing field (full checklist in `compatibility-rules.md`).
