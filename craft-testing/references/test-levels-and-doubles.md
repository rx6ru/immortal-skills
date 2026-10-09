# Test levels and test doubles

Where each kind of test belongs, what it should and should not cover, and how to isolate a unit from its dependencies. Use when deciding "unit or integration or end-to-end?", "mock it or use the real thing?", or when a suite is slow, brittle or untrustworthy because tests sit at the wrong level.

## Contents

1. Two maps: quadrants and pyramid
2. Level table
3. Choosing the layer to automate (decision procedure)
4. Unit tests and doubles
5. Isolating a unit: breaking dependences
6. Component tests (service level)
7. Integration tests and their stubs
8. End-to-end tests
9. Presentation-layer tests
10. Decision guideline tables
11. Pitfalls
12. Verify

---

## 1. Two maps: quadrants and pyramid

Quadrants (Marick; Crispin and Gregory; Mastering API Architecture ch. 2). The numbers are labels, not an order; start where your risk is (a ticketing system with traffic spikes starts with Q4).

| | Supports the team | Critiques the product |
|---|---|---|
| Business-facing (external quality) | Q2: tests with the business that what is built serves its purpose; automated, sometimes manual | Q3: functional requirements, exploratory and scenario testing; historically manual, increasingly automatable |
| Technology-facing (internal quality) | Q1: unit and component tests; automated | Q4: security enforcement, SLA integrity, autoscaling, performance, resilience |

Pyramid (Mike Cohn, same chapter):

- Base, most numerous: unit tests (Q1). Small, isolated, test doubles at the boundary.
- Middle: service tests (Q1, Q2, Q4). Several units together; component, contract and integration tests live here. Costlier because of larger scope and less isolation.
- Top: UI or end-to-end tests (Q2, Q3, Q4). For an API the "UI" is not graphical, so these are end-to-end tests. Largest scope, slow, brittle, highest confidence.

Trade-off axes: confidence versus isolation versus scope, speed and maintenance. Small tests are fast and isolated but give no whole-system confidence; large ones give confidence but are slow and costly. The inverted shape, heavy on end-to-end ("ice cream cone"), is called a fallacy that gives a false sense of security; the authors side with Fowler that shapes other than the pyramid are not recommended.

Pragmatic Programmer ch. 8 uses a fishing image for the same idea: fine nets (unit tests) catch minnows, coarse nets (integration tests) catch sharks, and when a fish escapes you patch the hole (add a test).

## 2. Level table

| Level | Scope and what is real | Catches | Does not catch | Speed and cost | Doubles used |
|---|---|---|---|---|---|
| Unit | one function, class or small cluster; real logic | logic errors, boundaries, contract violations | wiring, configuration, real I/O behaviour | fastest; cheapest | stubs/mocks/fakes at the boundary |
| Component | one deployable service in-process: request parsing, auth, deserialise, logic, serialise, respond | behaviour of the service as a whole: status codes, auth failures, empty collections, content negotiation | behaviour of real neighbours | fast | persistence and outbound calls replaced |
| Contract | one interaction between a consumer and a producer | drift between what a consumer expects and what a producer returns | scenarios (sequences), business flows | fast, runs locally | producer's own dependencies replaced; consumers use a generated stub |
| Integration | your code plus one real external dependency's boundary | wrong URL, payload, mapping, SQL, handling of responses | the dependency's internal behaviour | medium; containers add time | real container, contract-generated stub, or recorded stub |
| End-to-end | several real services of your own domain through the front door | wiring across services, core journeys | edge cases (too costly here) | slowest; brittle | third-party services outside your domain stubbed |
| Performance (Q4) | like-for-like environment | SLO violations, sudden lag, capacity | functional defects | expensive | none or minimal |

Fewer tests as you go up. Keep the totals pyramid-shaped (Mastering API Architecture ch. 2).

## 3. Choosing the layer to automate (decision procedure)

Synthesised from Why Programs Fail ch. 3 and Mastering API Architecture ch. 2.

1. Does the behaviour sit in a unit with a callable interface where it can fail alone? Use a unit test. Easiest to run and assess, but only valid if the unit fails in isolation; if the failure depends on cross-unit interplay, move up a layer.
2. Otherwise, is there a functionality-layer interface (library API, scripting interface, service endpoint) that reaches it? Use that. Results are machine-readable and robust to UI change.
3. Otherwise (the problem lies in the presentation, or presentation and logic are not separated, or the lower layers are inaccessible) use the presentation layer, with the cautions in section 9.
4. If core logic calls UI or other environment functions directly (circular dependence), break the dependence first (section 5), then test below the UI.

Four criteria for comparing layers (Why Programs Fail ch. 3): ease of execution, ease of interaction, ease of result assessment, lifetime of the test (robustness against program changes).

Rule of thumb from the same chapter: the friendlier an interface is to humans, the less friendly it is to computers.

## 4. Unit tests and doubles

Vocabulary from Mastering API Architecture ch. 2: a stub returns hardcoded canned responses; a mock is preprogrammed and also used to verify behaviour (that a call happened with the expected arguments). Why Programs Fail ch. 3 describes a third, the alternate implementation behind an abstraction that behaves automatically (an "automated presentation" whose confirmation prompt always returns true); in modern vocabulary this is a fake (adaptation of the notes' own inferred mapping).

| Double | Use for | Danger |
|---|---|---|
| Stub | feeding a fixed answer to the unit | stale snapshot, wrong shape: the test passes while production fails |
| Mock | verifying an outgoing interaction that is itself the behaviour (a message was sent) | couples the test to implementation; breaks on refactoring that preserves behaviour |
| Fake (working light implementation) | replacing something slow or external with a behaviourally faithful stand-in | equivalence is assumed; in-memory databases may differ from the real one |

Rules for the agent (adaptation, consistent with the sources):

1. Replace only what is slow, nondeterministic, outside your control or outside the unit's purpose. Keep the rest real; the more you replace, the less the test proves.
2. Prefer asserting on outcomes (returned value, resulting state) to asserting on calls. Verify calls only when the call is the behaviour.
3. A hand-typed stub nobody validates can be wrong: Mastering API Architecture ch. 2 shows a stub with a misspelled key and a duplicate id passing tests. Prefer stubs generated from a contract or recorded from the real thing (section 7).
4. Instrumented doubles may be inefficient (dual standard) but must stay readable.
5. Time, randomness, identifiers, environment: pass them in (`testability-design.md`).

## 5. Isolating a unit: breaking dependences

When a unit depends on something you cannot run in a test (a dialog, a network, a global), Why Programs Fail ch. 3 gives the dependence inversion procedure to remove it:

1. Introduce an abstract interface for the dependency (call it B') and make the real implementation B an implementation of B'.
2. Make the unit A depend on B' instead of B.
3. Add alternate implementations of B' for tests (an automated one whose `confirm_overwrite` returns true; the user-facing one asks), so A no longer needs B.

Cost: a small stub class for tests plus passing the dependency in (parameter or constructor). A quick hack is an "automated" mode flag; the interface approach is better because it generalises.

The example: `print_to_file` calls `confirm_loss` when the file exists, and the presentation calls the functionality too, a circular dependence that blocks testing the core alone. Fix by parameterising the function with a presentation object.

Design principles behind it: high cohesion (group what operates on common data) and low coupling (units that share no data exchange little); forbid circular dependences since they couple everything involved. Time spent improving the design repays itself in coding, testing and debugging. MVC is the model case: a model with observers (views, controllers) lets you add a controller that drives the model automatically or a view that logs every change (details in `testability-design.md`).

Sketch in TypeScript (adaptation):

```ts
interface Prompter { confirmOverwrite(path: string): boolean }
function printToFile(path: string, doc: Doc, ui: Prompter, fs: Fs) {
  if (fs.exists(path) && !ui.confirmOverwrite(path)) return;
  fs.write(path, render(doc));
}
// test: ui = { confirmOverwrite: () => true }; fs = inMemoryFs();
```

## 6. Component tests (service level)

Mastering API Architecture ch. 2. Validates multiple units working together as the service: parse request, authenticate and authorise, deserialise, business logic, serialise, respond. Dependencies (database access) are replaced; no external calls. Unlike a contract test it checks behaviour (creating an attendee calls the stubbed store), not just response shape.

API checklist:

- correct status code and correct data;
- null or empty parameter is rejected;
- `Accept: XML` returns the expected format;
- insufficient entitlements gives the right denial (valid credential 200, invalid 403 in the book's example);
- empty dataset: decide between 404 and an empty array, then test the decision (the book's example returns an empty array);
- the `Location` header points to a newly created resource.

Use component tests for behaviour sequences (add an attendee, then list it); contract tests are not for scenarios. If contract testing is not available, component tests can check conformance to the specification, but that is error-prone and tedious; contracts should be the golden source (`contract-testing.md`). Tooling examples: REST-Assured in Java, `net/http/httptest` in Go, otherwise a small client wrapped in a test DSL.

## 7. Integration tests and their stubs

Definition: tests across the boundary between your module and an external dependency, verifying the interaction (URL, payload) is correct and responses are handled.

Sources of the stand-in (Mastering API Architecture ch. 2). The book prefers a contract-generated stub, and otherwise recordings; it presents Testcontainers as a further option for real dependencies, and a hand-rolled stub as viable but risky. The numbering below is not a ranking beyond that:

1. A stub server generated from a contract: local, accurate, and kept in step with the contract.
2. A real dependency in a container (Testcontainers): run the production image; real database instead of mocks (mocks can encode wrong assumptions) or an in-memory database such as H2 (assumes equivalence with the real one); also Kafka, Redis, NGINX. Costs test time; integration tests are fewer so it is usually worth it.
3. Recorded interactions: a recorder captures request and response into mapping files, a stub server (WireMock, language-agnostic; camouflage for TypeScript) replays them. Keep recordings in sync; strip personal data if recorded against production.
4. A hand-rolled stub server: viable, risk of inaccuracy.

Stubs are point-in-time snapshots and rot: tests pass against a stale stub while production fails.

Boundary rule: a Testcontainers test stays integration when it verifies only the interaction across the boundary. Do not test the container's own behaviour (after publishing to Kafka do not subscribe to check; trust Kafka and verify that in end-to-end tests). Containers are not a replacement for contracts, which also give collaboration and a stub for consumers.

## 8. End-to-end tests

Mastering API Architecture ch. 2 and Pragmatic Programmer ch. 8.

- Define a boundary. Use real versions of your own services; stub entities outside your domain (a cloud object store, to avoid outages and network flakiness); omit components the test does not use.
- Use realistic payloads. One incident cited: tests used tiny payloads while consumers sent payloads larger than the buffers.
- Keep security on (TLS, authentication) or the tests are unrepresentative.
- Scenario tests (Q3) cover core user journeys only, not edge cases; write them in a behaviour-driven style (register an attendee for a talk, then the attendee count increases on retrieval). Correctness over speed.
- Performance end-to-end tests (Q4) need a like-for-like environment or the results mislead; assert SLO compliance, detect sudden lag from accidental blocking code, and measure capacity against figures from business requirements. Tools in the book: Gatling, JMeter, Locust, K6.
- Brittle and hard to coordinate; containers help local runs, but still obey the pyramid. Do not replicate third-party consumers' UIs.
- If end-to-end cannot be automated, keep a run book of manual tests executed before each production release; the book notes this slows delivery considerably.

## 9. Presentation-layer tests

Why Programs Fail ch. 3 (tools named there are dated; the principles are not).

| Level of script | Strength | Weakness |
|---|---|---|
| Low-level events (coordinates, key presses, waits) | can be recorded and replayed | unreadable; breaks on window position, font, screen size, language, speed, an unexpected extra dialog |
| System level (a virtual machine controlling the whole environment) | complete control, can inject hardware faults | needs well-defined machine images; administration overhead |
| Named controls ("menu item Open", "text field 1") | readable, robust to size and position | breaks when controls are renamed or reordered |

Use the presentation layer only when the problem occurs there, or the presentation is easily used by computers, or there is no other choice. Prefer named controls to coordinates. Recorded low-level scripts suit one debugging session in one environment, not long-lived suites. A test that works once but fails when run twice (the file now exists, so a prompt appears) shows state not restored.

Adaptation: Playwright and Selenium-style locators by role or label are the modern equivalent of named controls. Decouple logic from the screen so it can be tested without a GUI; if that is hard, the coupling is the finding (Pragmatic Programmer ch. 8, challenge question).

Do not embed a home-grown scripting language in an application for test automation; embed an existing interpreter or expose a component interface (Why Programs Fail ch. 3). Security note: automation interfaces can be abused.

## 10. Decision guideline tables

Condensed from Mastering API Architecture ch. 2 "ADR guideline" tables.

| Decision | Ask | Recommendation in the source |
|---|---|---|
| Testing strategy | Is there regular access to someone who can say how the API should behave? Are skills available? Do workplace rules prescribe a strategy? | Use quadrants plus pyramid; without a business person, at minimum the pyramid |
| Contract testing | Ready to add another layer to learn? Centralised or in-project contracts? Who are the consumers and will they engage? | Use it; many external consumers means producer contracts; internal APIs work toward consumer-driven contracts (`contract-testing.md`) |
| Integration testing | For each integrated service, what level? Can you craft accurate stubs or should you record? Can you keep them current and recognise a wrong interaction? | Prefer contract-generated stubs, else recordings; local integration tests give confidence when refactoring an integration |
| End-to-end testing | How complex is the setup? Do you know which tests provide value? Special requirements? | Automate at least core user journeys, ideally runnable locally, otherwise in the pipeline; else a manual run book |

## 11. Pitfalls

- Everything mocked: the test proves the wiring of the mocks. Keep real the logic you want to test.
- Integration or contract tests used to test other services' behaviour. Test your boundary only.
- Stale stubs. Version stubs with the contract or re-record on a schedule.
- Inverted pyramid: most confidence placed in a few slow journeys.
- End-to-end tests for edge cases: push them down to unit or component level.
- Unit tests that cannot fail alone because the unit's behaviour only appears in combination (Why Programs Fail ch. 3): add a higher-layer test.
- The same assertion at every level. Each level should add something the one below cannot show.

## 12. Verify

- For each test file, can you state its level and what real thing it touches? A test labelled unit that opens a socket is not.
- Count tests per level; the shape is roughly pyramid-like.
- Run the unit tests with the network disabled; they pass.
- Grep for fixed sleeps and absolute coordinates in UI tests.
- Break the production code at the boundary you claim to test (wrong URL, renamed field); the integration or contract test must fail.
- For stubs: show where each stub's content comes from (generated, recorded on a date, hand-written). Hand-written stubs are flagged.
