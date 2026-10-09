# Service contracts: strict, loose, consumer-driven, stamp coupling

Read this when you choose or review how two services (or a service and a client such as a mobile
app) exchange data: "use gRPC everywhere", "should we publish a JSON schema", "this message carries
the whole customer object", or when contract changes keep breaking consumers.

Contents: what a contract is; the strict-to-loose spectrum; trade-off tables; consumer-driven
contracts; stamp coupling; decision rule; worked example; verify. Versioning and breaking-change
tooling for public APIs live in `arch-api-design`.

## What counts as a contract

Hard Parts ch. 13 broadens the word: the format used by parts of an architecture to convey
information or dependencies. It covers integration points (SOAP, REST, gRPC, XML-RPC), but also
transitive library and framework dependencies, caches, and any inter-part communication. Contracts
sit across the three dynamic-coupling dimensions like time does: orthogonal to them.

Decide the contract type (tight or loose) first. The implementation technology (gRPC, REST,
messaging) is then a developer's choice, provided it passes the fitness functions. "gRPC because it
is fast" confuses an implementation with a coupling decision.

## The spectrum

- Strictest: remote method invocation that mimics a local call (names, types, order, everything).
  The RPC family, including gRPC, defaults strict.
- Looser: REST (model resources, not procedures; adding engine data to an airplane resource does not
  break a seat query), and GraphQL (consumer-defined, read-only aggregated views instead of costly
  orchestration; each consumer defines its own Profile type, so Wishlist asks only for `name`).
- Loosest: name/value pairs in JSON or YAML with no schema or types.
- It is a spectrum, not a binary. Even JSON can be made strict by attaching a schema (types,
  required fields, minimums).

Contracts are glue that changes often and is used by many parts, which is the danger zone for
coupling. Strict contracts create brittleness; use them only where the strictness pays.

Anti-pattern: over-specifying a contract in case the consumer needs more later (the Wishlist
contract carries every Profile field). It introduces breaking changes where none were needed. Keep
contracts at the level the consumer needs to know, balancing semantic coupling against needless
fragility.

## Trade-offs

Strict contracts:

| Advantages | Disadvantages |
|---|---|
| Guaranteed fidelity (schema verifies values, types, metadata) | Tight coupling: both services change when the contract changes |
| Versioned: supports gradual change and selective old versions | Versioning becomes an integration nightmare without a deprecation strategy or with too many versions |
| Easier to verify at build time (schema tooling is type checking at integration points) | |
| Better documentation (explicit parameters and types) | |

Loose contracts:

| Advantages | Disadvantages |
|---|---|
| Highly decoupled | Contract management: misspelled names and missing pairs that a schema would catch |
| Easy to evolve; implementation changes freely | Needs fitness functions (typically consumer-driven contracts) to prove the contract still carries enough |

Loose contracts do not erase semantic coupling: if the meaning of the data changes, teams still
have to coordinate. Implementation cannot reduce semantic coupling.

Example: two services each keep their own bounded-context Customer and exchange name/value JSON.
Gains: each team evolves its internal representation aggressively; one team can change platform
because name/value pairs are a lingua franca. Cost: fidelity. The strict alternative (same stack,
RMI or gRPC) gives high fidelity at the price of tight coupling.

## Consumer-driven contracts (CDC)

Invert push to pull: the consumer writes a contract of exactly the items it needs and gives it to
the provider; the provider includes it in its build and keeps the contract test green in CI/CD.
Multiple consumers with overlapping needs each supply their own. Each team can be as strict or loose
as it needs, and fidelity is checked at build time by tooling. Fitness functions can encode more than
a schema, for example acceptable value ranges.

| Advantages | Disadvantages |
|---|---|
| Loose coupling between services | Needs engineering maturity: ignored failing contract tests leave integrations broken |
| Variable strictness per consumer | Two interlocking mechanisms (name/value pairs plus CDC) instead of one schema tool |
| Evolvable | |

Decision hinges on team maturity and on decoupling (loose) versus complexity-plus-certainty
(strict). See `craft-testing` for how contract tests sit among test levels.

## Stamp coupling

Definition: passing a large data structure between services when each uses only a small part.

- Legitimate when an industry-standard document exists (for example a travel itinerary passed
  through many systems that each update their section).
- Often accidental and harmful: Wishlist needs only the customer name by id, but the contract
  carries all of Profile; Profile changes an unrelated field (state) and Wishlist's contract
  breaks.
- Bandwidth is not infinite. Worked numbers: 2,000 requests per second at 500 KB each is about
  1,000,000 KB per second; sending only the name (about 200 bytes) is about 400 KB per second.
- Stamp coupling for workflow state: in choreography, put workflow state (status, transaction state,
  errors) in the contract; each service updates its part and passes it on, and the final receiver
  reads status and errors. For atomic consistency, services must re-broadcast the contract to
  previously visited services to restore consistency. Coupling rises, but semantic coupling has to
  live somewhere, and this gives choreography's throughput with complex flows.

| Advantage | Disadvantages |
|---|---|
| Allows complex workflows within choreographed solutions | Creates (sometimes artificially) high coupling between collaborators |
| | Can cause bandwidth problems at high scale |

## Decision rule

Choose strictness by three factors: how often the two sides must change together (semantic coupling),
how quickly the consumer can deploy, and how fast the information itself changes.

1. Identify each integration point; estimate co-change frequency and each side's deployment speed.
2. Co-changing, same team or release train, high fidelity needed: strict, with a schema, versions and
   an explicit deprecation policy.
3. Slow-changing information, independent teams, or slow deployment channels (mobile app stores):
   loose name/value pairs plus CDC fitness functions plus an extension mechanism.
4. Send only what the consumer needs. Do not add fields "for the future".
5. Use stamp coupling only for standards-based documents or for workflow state in choreography, and
   check payload times peak request rate against network capacity.

## Worked example (ticket workflow)

- Orchestrator to Ticket Management and to Ticket Assignment: tight. They are semantically coupled,
  change together, and new things to manage mean assignment must sync.
- Orchestrator to Notification and to Survey: loose. Slow-changing information, no benefit from
  brittle coupling.
- Orchestrator to the expert mobile app: it would nominally be tight like assignment, but the app
  ships through a public app store with slow approval, so loose gives flexibility and a slower rate
  of change. ADR recorded: loose name/value contract plus an extension mechanism for temporary
  short-term additions; consequences: more validation logic must live in both the orchestrator and
  the app; revisit if the store allows faster deployment.

## Verify

- CDC tests from every consumer run in the provider's pipeline, and a failing contract test blocks
  deployment (this is the evidence that loose contracts are still carrying enough).
- Contract diff check in CI for removed or renamed fields on strict contracts; schema compatibility
  check where a schema exists.
- Unneeded-field check: list contract fields no consumer reads. Each is a stamp-coupling smell.
- Bandwidth estimate in the design review: payload size times peak request rate against capacity.
- For loose contracts with an extension mechanism, a test showing an unknown field is ignored (not
  rejected) by every consumer, and that required fields are validated on both ends.
