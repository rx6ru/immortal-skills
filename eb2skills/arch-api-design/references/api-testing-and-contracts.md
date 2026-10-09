# API testing and contract testing

Contents: 1. Scope; 2. Quadrants and pyramid; 3. Contract testing; 4. Component tests; 5. Integration tests; 6. End-to-end tests; 7. Choosing what to build first; 8. Review checklist; 9. Verify

Sources: Mastering API Architecture (MAA) ch. 2, ch. 1, ch. 10; Hard Parts ch. 13 for consumer-driven contracts as fitness functions. General test craft (naming, FIRST, doubles in the abstract) belongs to `craft-testing`; this file covers what is specific to testing an API from the consumer's external standpoint.

## 1. Scope

Untested APIs drift from their documentation, introduce accidental breaking changes, time out, give poor error feedback, or violate SLOs. Budget rule: avoid irrelevant, duplicate, flaky or low-value tests; not everything must exist before the first release (MAA ch. 2).

## 2. Quadrants and pyramid

Test quadrants (Marick, Crispin and Gregory). The numbers are labels, not an order; start where your risk is (a ticketing system with traffic spikes starts at Q4).

| Quadrant | Faces | Purpose | Examples |
|---|---|---|---|
| Q1 | technology, supports the team | prevents defects | unit, component tests (automated) |
| Q2 | business, supports the team | checks what is built serves its purpose | tests with the business (automated, may be manual) |
| Q3 | business, critiques the product | finds defects in functional requirements | exploratory, scenario tests |
| Q4 | technology, critiques the product | non-functional | security enforcement, SLA integrity, autoscaling, performance, resilience |

Test pyramid (Cohn):
- Base: unit tests, most numerous, small and isolated, with test doubles at the boundary (stub: hard-coded canned answers; mock: preprogrammed and used to verify behaviour).
- Middle: service tests (component, contract, integration), costlier because of larger scope.
- Top: end-to-end tests. An API's "UI" is not graphical but the same logic applies: largest scope, slow, brittle, highest confidence.
- The "ice cream cone" (heavy on end-to-end) gives a false sense of security. The authors side with Fowler that other shapes are not recommended.

Rule for the strategy decision (MAA Table 2-1): use quadrants plus pyramid; if no business person is available to join the quadrant work, use at least the pyramid, which concentrates automation and finds bugs early. Someone must always guide product direction.

## 3. Contract testing

A contract is a shared definition of an interaction: if a request matches the contract's request, the producer returns a response matching the contract's response. It is a specific interaction with examples, not schema conformance (a schema is compatible or not).

What it gives:
- Tests generated from the contract verify the producer; breaking one means consumers will break.
- A stub server generated from the response definitions lets consumers build and test without the producer.
- Runs locally with no other services (a service test).
- Decouples consumer and producer builds: consumer codes against the stub, producer against generated tests; usable for stakeholder demos before the logic exists.
- The authors call it the most return for the effort.

Example shape (Spring Cloud Contract style): request `GET /conference/1234/attendees` with JSON content type; response 200 with `{ value: [ {id, givenName, familyName}, ... ] }`; this generates both a producer test and a stub.

Rules:
- Do not use contracts for scenarios (add an attendee then list it); that is a component test.
- Run the generated tests against the running producer with its external dependencies replaced by test doubles. Do not test other services' integrations in them.

Producer contracts versus consumer-driven contracts (CDC):

| | Producer contracts | Consumer-driven contracts |
|---|---|---|
| Who writes | Producer | Consumer writes the contract for functionality it wants and submits it (for example a pull request to the producer), producer discusses and accepts or rejects (maybe suggests PATCH instead of PUT) |
| Use when | Consumers are external or many (no single consumer can ask to change the whole API); easiest way to start | Consumers and producers are within reach, usually the same organisation; value comes from the discussion plus the agreed assertion |
| Cost | Setup and writing time | Same plus social coordination |

Guideline (MAA Table 2-2): use contract testing when building an API; it is worth the learning curve. Large external audience: producer contracts, which protect backward compatibility. Internal API: work toward CDC, starting with producer contracts and evolving. If contract testing is infeasible, the producer needs alternatives (careful request/response tests, tricky and time-consuming) and a way for consumers to test.

Frameworks: Pact is the default for HTTP and opinionated (enforces CDC; the consumer test generates a language-agnostic intermediate contract; many languages). Spring Cloud Contract uses hand-written contracts, supports either CDC or producer contracts, is language-agnostic via a container but best in Spring/JVM. Contract testing also exists for non-HTTP protocols. The authors found no actively maintained tool that generated contracts from OpenAPI at the time.

Where contracts live:
- With producer code in Git or an artifact repository: the producer controls accepted contracts, but they are hard to find across a large organisation.
- A central repository: visible, but contracts may land in modules producers never intend to fulfil.
- A broker (Pact Broker): shows validated contracts, who uses what, a network diagram, and CI/CD integration; the most comprehensive and recommended if the framework fits.

Contracts as governance: Hard Parts ch. 13 uses CDC tests as the fitness functions that keep loose contracts safe. Each consumer supplies the contract of what it needs, the provider includes it in its build, and a red contract blocks deployment (blocking is the notes' inferred verification step; the book's text says the provider keeps the contract test green in CI/CD). This needs CI discipline: ignored failing contract tests leave integrations broken. See `contract-strictness.md`.

## 4. Component tests

Validate several units working together inside the service: parse request, authn/authz, deserialise, business logic, serialise, respond. Dependencies (DB, DAO) are mocked; no external calls. Unlike a contract test, a component test checks behaviour (creating an attendee calls the mocked DB), not only response shape. Covers Q1 and Q2.

API checklist:
- correct status code and correct data;
- null or empty parameter rejected;
- `Accept: XML` (or another type) returns the expected format;
- insufficient entitlements produce the right response;
- empty dataset yields 404 or an empty array (decide, then pin it);
- `Location` header points at the new resource.

Tools: REST-Assured (JVM), `net/http/httptest` (Go), or a small DSL around an HTTP client. Example cases: valid credential gets 200, invalid gets 403, conference with no attendees returns an empty array. If contract testing is unavailable, component tests can check spec conformance, but that is error prone and tedious; contracts should be the golden source of agreed interactions.

## 5. Integration tests

Test across the boundary between your module and an external dependency: is the interaction correct (URL, payload), and are responses handled?

Ways to stand in for the dependency, best first:
1. A stub server generated from the dependency's contract (local and accurate).
2. Recorded interactions: capture request and response into mapping files and replay them with a stub server (WireMock, language-agnostic; camouflage for TypeScript). Keep recordings in sync and strip PII if recorded against production.
3. A hand-rolled stub. Viable but risks inaccuracy: the book shows a stub with a wrong key name, a duplicate id and a misspelled field.

Stubs are point-in-time snapshots and rot; tests can pass against a stale stub while production fails. Decide how you will keep stubs current and recognise an incorrect interaction.

Testcontainers: a library that orchestrates container lifecycle from tests; run the same image as production. Uses: a containerised gRPC stub published for early consumers; a real database instead of mocks (mocks can encode wrong assumptions) or an in-memory database such as H2 (assumes equivalence with the real one); Kafka, Redis, NGINX. It costs test time, but integration tests are few so it is usually worth it.

Boundary rule: Testcontainers stays integration, not end-to-end, if you verify only the interaction across the boundary. Do not verify the container's own behaviour (after publishing to Kafka, do not subscribe to check; trust Kafka and test that end-to-end). It does not replace contracts, which give testing, integration and collaboration, not just a stub.

Guideline (MAA Table 2-3): use generated stub servers from contract tests; otherwise integration tests with recordings; local integration tests give confidence especially when refactoring an integration.

## 6. End-to-end tests

A request enters the front door and flows through to the correct response.
- Define a boundary. Use real versions of your own services; stub entities outside your domain (for example AWS S3, avoiding outages and network flakiness); omit components the test does not use (an Attendee end-to-end test needs the DB and the Attendee service, not the legacy system). Do not replicate third-party consumers' UIs.
- Use realistic payloads. In a real incident tests used tiny payloads while consumers sent payloads larger than buffers.
- Scenario tests (Q3): core user journeys only, not edge cases; write them with BDD (register an attendee for a talk, the attendee count increases on retrieval). Speed is not the concern; correctness is.
- Performance tests (Q4): need a like-for-like production environment or the results mislead; assert SLO compliance, detect sudden lag (for example accidental blocking code), measure load capacity; targets come from business requirements; tools Gatling, JMeter, Locust, K6.
- Keep TLS and authentication on in end-to-end tests, otherwise they are unrepresentative and distort metrics.
- They are brittle and hard to coordinate; containers make local runs easier but the pyramid still applies.

Guideline (MAA Table 2-4): at minimum automate end-to-end tests for core user journeys, ideally runnable locally, otherwise in the build pipeline, balanced against setup time. If not automatable, keep a run book of manual tests executed in a test environment before each production release (this slows delivery considerably).

## 7. Choosing what to build first

| Situation | Start with |
|---|---|
| New API with several consumers | Producer contracts, plus component tests for behaviour |
| Internal API, consumers reachable | Producer contracts evolving to CDC |
| Consuming someone else's API | Integration tests with a contract stub or recordings; Testcontainers for owned infrastructure |
| Traffic-spike product | Q4 performance and resilience first |
| No business stakeholder available | Pyramid only |
| Refactoring an integration | Local integration tests first |

## 8. Review checklist (synthesised in the notes, marked inferred there)

1. Contracts (producer or CDC) exist per consumer interaction and generate producer tests plus consumer stubs.
2. Component tests cover status codes, auth failure, empty collections, content negotiation and Location.
3. Integration tests use real dependency containers or contract/recorded stubs, not hand-typed JSON nobody validates.
4. Only core journeys at the end-to-end level; security on; realistic payloads; performance tests in a like-for-like environment against SLOs.
5. Proportions follow the pyramid.

## 9. Verify

- Break a response field on purpose (rename it) in a scratch branch: the producer's contract test must fail. If it does not, the contract is not wired to the real handler.
- Delete a field the consumer uses from the contract's stub and confirm the consumer test fails; this shows the consumer really runs against the stub.
- Count tests per level and compare with the pyramid; report the numbers.
- List every stub or recording and its last verification date or source contract; flag any without one.
- Confirm end-to-end runs use TLS and authentication.
