# Specification (OpenAPI) and versioning

Contents: 1. What a specification is for; 2. Four practical uses of OpenAPI; 3. Spec-first or code-first; 4. Semantic versioning for APIs; 5. Three ways to upgrade a running service; 6. The API lifecycle; 7. Mapping a change to a release approach; 8. Conveying the version; 9. Breaking-change gate in CI; 10. Cross-organisation versioning; 11. Verify

Sources: Mastering API Architecture (MAA) ch. 1, ch. 5; DDIA 2e ch. 5.

## 1. What a specification is for

The book defines an API by four properties (MAA ch. 0): it abstracts the implementation; it is represented by a specification that introduces types, so tooling can generate consumer code in many languages; it has defined semantics, modelling the exchange; and good design lets it extend to customers and third parties.

OpenAPI (OAS) is a JSON or YAML description of structure, domain objects and security requirements, plus metadata (licensing), documentation and examples. Swagger was the original reference implementation; tools converged on OpenAPI. It underlies API marketplaces and developer portals. Check tool support: many tools support only one OAS version (v2 versus v3). The book reports a diff tool that detected no breaking changes when run on an older spec version, so confirm that your tool actually reads your spec version (try a deliberate break, section 11).

OAS conveys shape only, not behaviour under different conditions. It does not replace behavioural tests (contract and component tests, `api-testing-and-contracts.md`).

## 2. Four practical uses of OpenAPI

| Use | What to do | Caveat |
|---|---|---|
| Code generation | Generate client models/services (OpenAPI Generator: Java Spring/JAX-RS, TypeScript, others) and server stubs | Shape only; do not couple the API to the internal representation, and keep the ability to refactor internals without breaking the API |
| Validation | Validate requests and responses against the spec at runtime. At the gateway/DMZ it terminates non-conforming traffic (a security measure); in tests it checks conformance. Example tool: swagger-request-validator, built from a spec URL with an optional base-path override when behind a gateway or proxy, yielding a validation report | Gateway validation needs the spec to stay current |
| Examples and mocking | Examples feed docs and mock servers (developer portal "try it"). Letting producer and consumer try the API before the service exists is more valuable than reviewing a spec | Examples are strings and drift; validate them (openapi-examples-validator) |
| Change detection | Diff specs in the pipeline for backward compatibility (openapi-diff) | See section 9 |

## 3. Spec-first or code-first

The notes raise the question and answer it indirectly: design the API from the consumer's perspective, model behaviours, and test them. DDIA 2e describes the two workflows neutrally: code-first with a generated IDL (FastAPI) or IDL-first with generated server scaffolding and client SDKs (gRPC). Rule for the agent: if the repository is code-first, make sure the generated spec is committed or published so the diff gate has something to compare; if spec-first, the spec is the source and handlers must not leak internal models into it.

## 4. Semantic versioning for APIs

| Part | Meaning | Consumer impact |
|---|---|---|
| Major | Incompatible change | Consumer actively opts in; expect a migration guide and usage tracking |
| Minor | Backward-compatible addition | Consumers may receive it with no action |
| Patch | Bug fix, no new functionality | No action |

Versioning is a product decision, including how the version is conveyed. Not planning for versioning of exposed APIs is dangerous (MAA ch. 1).

## 5. Three ways to upgrade a running service

Unlike compile-time libraries, services upgrade in production, so three options exist and you want rules that support a mix (MAA ch. 1):
1. Release the new version at a new location; consumers upgrade when they want; the producer maintains and patches several versions.
2. Release backward-compatibly (additive); no consumer change. Even fixing a misnamed field breaks.
3. Break compatibility and require every consumer to upgrade in lockstep, with coordinated downtime. Sometimes unavoidable.

## 6. The API lifecycle (MAA Table 5-1, adapted from archived PayPal API standards)

| Stage | Meaning |
|---|---|
| Planned | Advertise that the API is coming; collect early feedback on shape and scope |
| Beta | Consumers integrate for feedback; the producer reserves the right to break compatibility (not a versioned API). Purpose: avoid accumulating many major versions early |
| Live | Versioned, in production; any change is a versioned change. Only one live API (the latest major/minor combination); when a new version goes live the previous live one becomes deprecated |
| Deprecated | Still usable, no significant new development. After a minor release the old one is deprecated only briefly (until production validation of the new one finishes), then retired because it is backward compatible. After a major release it stays deprecated for weeks or months: communicate, supply a migration guide, track usage metrics of the deprecated API |
| Retired | Removed from production, not accessible |

With semver plus this lifecycle the consumer only needs to care about the major version.

## 7. Mapping a change to a release approach

| Change | Approach |
|---|---|
| Major (breaking) | Run live and deprecated versions side by side for a long time; the consumer chooses when to upgrade; conveyed in the URL or a header |
| Minor or patch | Deploy without production traffic, then introduce with a release strategy (canary, mirroring); no consumer code change. Most releases should be this kind |
| Tightly coupled consumer and producer (same team, always move together) | Versioning and lifecycle matter less; release both together with traffic controlled at ingress, typically blue-green |

Release strategy details are in `release-strategies.md`.

## 8. Conveying the version

- In the URL (`GET /v1/attendees`): visible and practical; purists say a version is not part of the resource.
- In a header (`Version: v1`): can drive routing at cluster ingress.
- Server-side per API key (DDIA 2e): the version is stored per key and changed through an admin interface (Stripe style).
No consensus exists; choose one, write it in the standard, and keep it uniform.

## 9. Breaking-change gate in CI

Procedure (MAA ch. 1, ch. 5):
1. Keep the spec of the last released version available (artifact store or tag).
2. On every pull request, run a diff tool against it. The book's example: `docker run openapitools/openapi-diff original.json new.json`.
3. Expect results like these: renaming `givenName` to `firstName` is reported as breaking (missing property); adding a field `age` is reported as backward compatible.
4. Fail the build on a non-backward-compatible result unless a major version bump is intended and flagged (a conscious override).
5. Confirm the tool supports the spec version in use, otherwise it can silently report nothing.

Adaptation: any diff tool that understands your spec version works; the principle is spec in the pipeline, compare to the last release, fail on incompatibility. For protobuf use the equivalent linter/breaking-change check of your toolchain, and for registry-backed formats use the registry's compatibility mode (`compatibility-rules.md`).

## 10. Cross-organisation versioning (DDIA 2e)

A provider cannot force clients to upgrade, so compatibility must hold for a very long time and breaking changes require several API versions side by side. The assumption "servers upgrade first, clients second" fails for mobile apps and third-party clients, whose update timing you do not control.

## 11. Verify

- A spec file exists, validates, and is the artifact the pipeline diffs.
- Rename a field in a scratch branch: the pipeline fails with a missing-property finding. Add an optional field: it passes. (Run both and show the output; this proves the gate is wired to the right spec version.)
- Every field removal or rename in the change set has a matching major version bump or a documented deprecation window.
- The lifecycle stage of each endpoint is recorded (beta endpoints carry no compatibility promise; live ones do).
- Deprecated versions have usage metrics and a retirement date.
