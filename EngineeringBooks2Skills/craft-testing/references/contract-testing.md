# Contract testing

Using a written, executable definition of an interaction between a consumer and a producer to test both sides without running both. Use when two services (or a client and an API) must stay compatible, when a consumer wants a reliable stub, when a producer wants to know what a change would break, or when integration tests rely on hand-typed JSON that nobody validates.

Scope note: this file is the testing view (Mastering API Architecture ch. 2). Designing, specifying and versioning the API itself, breaking-change detection and OpenAPI belong to `arch-api-design`. A different use of the word "contract" appears in `what-to-test.md` section 5 and `craft-error-handling` (design by contract inside a program); do not confuse the two.

## Contents

1. Terms
2. Why contracts earn their cost
3. Contract versus schema
4. What a contract looks like
5. Producer contracts versus consumer-driven contracts
6. Choosing between them
7. Procedure to adopt
8. Frameworks and storage
9. Boundaries: what not to put in a contract test
10. Costs and pitfalls
11. Verify

---

## 1. Terms

- Consumer: sends the request. Producer (provider): sends the response. One service can be both.
- Contract: a shared definition of one interaction. If a request matches the contract's request, the producer returns a response matching the contract's response.

## 2. Why contracts earn their cost

Mastering API Architecture ch. 2 calls contract testing the most bang for the buck among API tests.

- The interaction is written down and enforceable. Tests generated from the contract verify the producer: breaking a contract test means consumers will break.
- A stub server generated from the response definitions gives consumers something to test against.
- It runs locally with no other services needed, so it is a fast service-level test.
- It decouples the building of consumer and producer: the consumer codes against the stub, the producer against the generated tests. The stub can be used for stakeholder demos while the logic is unfinished.
- It supports collaboration, since a contract is also a conversation artefact.
- The ecosystem is mature.

## 3. Contract versus schema

Conforming to a schema (OpenAPI) is a yes or no on shape and types. A contract is a specific interaction with concrete examples (this request yields this response). Schema checks complement contracts; they do not replace them.

## 4. What a contract looks like

The book's example (Spring Cloud Contract's Groovy DSL, fresh paraphrase): a request `GET /conference/1234/attendees` with a JSON content type; a response `200` with a body whose `value` is a list of objects each having `id`, `givenName`, `familyName`. From it the framework generates both a producer test and a consumer stub.

Fresh sketch of the same idea in a neutral notation (adaptation):

```yaml
interaction: list attendees of a conference
request:  { method: GET, path: /conference/1234/attendees, accept: application/json }
response: { status: 200, body: { value: [ { id: "a1", givenName: "Ada", familyName: "Lovelace" } ] } }
```

## 5. Producer contracts versus consumer-driven contracts

| | Producer contracts | Consumer-driven contracts (CDC) |
|---|---|---|
| Who writes | the producer defines the accepted interactions | the consumer writes the contract for the functionality it wants and submits it (for example as a pull request) |
| Fits when | consumers are external or many (the book's example: a large public platform API where no single consumer can ask to change the whole API; changes need careful orchestration and a migration plan); easiest way to start | consumers and producers are within reach, usually the same organisation |
| Social side | little | the discussion is the value: the producer may accept, reject or counter-propose (the book's example: suggest PATCH instead of PUT) |
| Protects | backward compatibility for outside callers | the functionality each known consumer actually uses |

Variants: the consumer may also write a basic producer implementation, or TDD the functionality and write the contract before the pull request. Details are team-specific.

## 6. Choosing between them

Decision guideline (Mastering API Architecture ch. 2, Table 2-2), condensed:

1. Use contract testing when building an API; the learning curve is worth it.
2. Large external audience: use producer contracts, to protect backward compatibility.
3. Internal API: work toward CDC, starting with producer contracts and evolving.
4. If contract testing is infeasible, the producer needs alternatives (careful request and response tests, tricky and time-consuming) and consumers need some way to test.

Questions to ask first: are you ready to add another testing layer developers must learn? Centralised or in-project contracts? Extra tools or training? Do you know who will use the API, only inside your organisation, and are they willing to engage?

## 7. Procedure to adopt

1. List the consumers and their interactions. Start with the highest-risk or most-used ones.
2. Pick producer contracts or CDC (section 6).
3. Write one contract per interaction with concrete examples, including at least one error response that consumers handle.
4. Generate the producer-side test; run it against the producer with its external dependencies replaced by test doubles. Fix the producer or the contract until it passes.
5. Publish the stub generated from the contract for consumers. Consumers replace hand-written stubs in their integration tests with it.
6. Run producer verification in the producer's pipeline, so a change that breaks a contract fails the build before release.
7. Decide where contracts live (section 8) and how a consumer proposes a new one.

## 8. Frameworks and storage

Frameworks named in the source:

- Pact: the default for HTTP, opinionated (enforces CDC); the consumer test generates a language-agnostic intermediate contract; many languages.
- Spring Cloud Contract: hand-written contracts, supports either CDC or producer contracts, language-agnostic through a container but best in a Spring/JVM stack.
- Contract testing also exists for non-HTTP protocols.

Where to keep contracts:

| Option | Pros | Cons |
|---|---|---|
| With producer code in Git, or in an artifact repository | producer controls which contracts it accepts | hard to find across a large organisation |
| Centralised repository | visibility | contracts can land in modules producers never intend to fulfil |
| Broker (for example the Pact Broker) | shows validated contracts, who uses what, a network diagram, CI/CD integration | needs a compatible framework; most comprehensive and recommended when it fits |

The notes record that no actively maintained tool for generating contracts from OpenAPI was found at the time of writing; check whether that has changed before building one by hand (adaptation).

## 9. Boundaries: what not to put in a contract test

- Do not use contracts for scenarios (add an attendee, then list it). Use component tests for behaviour sequences (`test-levels-and-doubles.md` section 6).
- Do not test other services' integrations inside the contract tests; replace the producer's dependencies with test doubles.
- Do not treat a contract as a performance or security test.
- A contract is not a replacement for end-to-end checks of core journeys.

## 10. Costs and pitfalls

- Setup time and the effort of writing contracts.
- Another layer for developers to learn.
- Contracts that nobody updates become a second source of drift; make the producer pipeline fail on a mismatch.
- A CDC process needs consumers and producers who can talk; across organisations, use producer contracts.
- A stub generated once and never regenerated is as stale as a hand-typed one (stale stubs: tests pass, production fails).

## 11. Verify

- Every consumer interaction you care about has a contract (or you can say why not).
- Producer verification runs in CI and fails when you change a response field name; try it: rename a field in the producer, run the contract test, expect red, revert.
- Consumer tests use the generated stub, not a separately typed copy of the JSON. Grep consumer tests for inline JSON bodies that duplicate a contract.
- The stub in use matches the contract's current version (version or hash recorded).
- No contract mixes in a multi-step scenario.
- For a breaking change, the broker or repository shows which consumers would break before you merge (if a broker is used).
