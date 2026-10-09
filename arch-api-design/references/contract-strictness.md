# Contract strictness: strict, loose, consumer-driven, stamp coupling

Contents: 1. Spectrum; 2. Trade-off tables; 3. Consumer-driven contracts as the safety net; 4. Stamp coupling; 5. Decision procedure; 6. Worked example; 7. Verify

Source: Architecture: The Hard Parts ch. 13 (contracts); Mastering API Architecture ch. 1, ch. 2 for the tooling. The book's definition of contract here is broad: the format used by parts of an architecture to convey information or dependencies (integration points, but also transitive dependencies and caches). Do not confuse with a "contract test" (`api-testing-and-contracts.md`), which is one way to enforce a contract.

## 1. Spectrum

Contract strictness is a spectrum. In the book's examples, strictest first:
- Remote method invocation that mimics a local call (Java RMI): names, types, order.
- RPC family including gRPC (strict by default).
- REST: models resources, not procedures, so adding engine information to an airplane resource does not break a seat query.
- GraphQL: read-only aggregated views, each consumer defines its own type (a wishlist wants only `name`).
- Loosest: name/value pairs in JSON or YAML with no schema or types.

Even JSON can be made strict by attaching JSON Schema (types, required fields, minimums such as shares of at least 100).

Contracts are glue that changes often and is used by many parts, which makes them a danger zone for coupling. Strict contracts create brittleness; use them only where the strictness pays.

Anti-pattern: over-specifying a contract "just in case" the consumer needs more later. It creates breaking changes where none were needed. Keep contracts at need-to-know level.

## 2. Trade-offs

| | Advantages | Disadvantages |
|---|---|---|
| Strict (Table 13-1) | Guaranteed fidelity (schema verifies values, types, metadata); versioned, supporting gradual change and selective past versions; easier to verify at build time (schema tooling is type checking at integration points); better documentation | Tight coupling: both services change when the contract changes; versioning becomes an integration nightmare without a clear deprecation strategy or when too many versions are supported |
| Loose (Table 13-2) | Highly decoupled; easier to evolve (little or no schema, implementation evolves freely; semantic coupling still needs coordination) | Contract management: misspelled names, missing pairs and other defects a schema would catch; needs fitness functions, typically consumer-driven contracts, to confirm the contract still carries enough information |
| Consumer-driven (Table 13-3) | Loose coupling between services; variable strictness (fitness functions can encode more than schemas, for example acceptable value ranges); evolvable | Needs engineering maturity (CI discipline); two interlocking mechanisms (name/value pairs plus CDC) instead of one elaborate schema tool |
| Stamp coupling for workflow state (Table 13-4) | Allows complex workflows in choreographed solutions | Creates, sometimes artificially, high coupling between collaborators; bandwidth issues at high scale |

Microservices example: two services each keep their own bounded-context Customer and exchange name/value JSON. Gain: teams evolve internal representations aggressively and can change platform. Cost: contract fidelity. The alternative (same stack, RMI or gRPC) gives high fidelity but couples tightly, against microservices aims.

## 3. Consumer-driven contracts as the safety net

CDC inverts push to pull: the consumer writes a contract of the items it needs and gives it to the provider, who includes it in the build and keeps the contract test green in CI/CD. Several consumers with overlapping needs each supply their own. Each team can be as strict or loose as it needs, and fidelity is guaranteed at build time. Whether to choose it hinges on team maturity and on decoupling (loose) versus complexity plus certainty (strict). Tools and frameworks: `api-testing-and-contracts.md`.

## 4. Stamp coupling

Definition: passing a large data structure between services where each uses only a small part.
- Legitimate when an industry-standard document exists (a global travel-itinerary XML passed through many systems that update their sections).
- Otherwise usually an accident: an over-specified contract or wasted bandwidth.
- Coupling example: a wishlist needs only a customer name by id, but the contract carries the whole profile; the profile team changes an unrelated field (state) and the wishlist contract breaks.
- Bandwidth example from the book: 2,000 requests per second at 500 KB is 1,000,000 KB/s; sending only the name (about 200 bytes) is about 400 KB/s (the notes state "400 KB" for the second figure).
- Workflow use: in choreographed flows put workflow state (status, transactional state, errors) in the contract; each service updates its part and passes it on; the last reads the result. For atomic consistency the services must re-broadcast the contract to previously visited services. This raises coupling, but semantic coupling has to live somewhere. Workflow patterns themselves are in `arch-distributed-workflows`.

## 5. Decision procedure (synthesised in the notes)

1. List each integration point; estimate how often the two sides change together and how fast each side can deploy.
2. Change together, same team or release train, high fidelity needed: strict contract (schema, versioned) with an explicit deprecation policy.
3. Slow-changing information, independent teams, or a slow deploy channel such as a mobile app store: loose name/value contract plus CDC fitness functions plus an extension mechanism for short-term additions.
4. Send only what the consumer needs. Do not add "future-proofing" fields.
5. Use stamp coupling only for standards-based documents or for workflow state in choreography, after checking payload times peak requests per second against network capacity.

The deciding factors in the book's case: semantic coupling and co-change rate; deployment latency of the consumer; rate of change of the information.

## 6. Worked example (Sysops Squad ticketing)

- Orchestrator to Ticket Management and Ticket Assignment: tight; highly semantically coupled, they change together.
- Notification and Survey: loose; slow-changing information, no benefit from brittle coupling.
- Orchestrator to the expert mobile app: it would nominally be tight like assignment, but the app ships through a public app store with slow approval, so loose gives flexibility and a slower change rate.
- ADR outcome: loose name/value contract between orchestrator and mobile app, plus an extension mechanism for temporary additions. Consequence: revisit if the store allows faster deployment; more validation logic must live in both the orchestrator and the app. (ADR template: `arch-decisions-and-tradeoffs`.)

## 7. Verify

- Each integration point has a recorded strictness choice with the three deciding factors.
- For every loose contract there is a CDC test or equivalent check in the provider's pipeline, and a failing one blocks deployment.
- Contract diff checks detect removed or renamed fields for strict contracts (`specification-and-versioning.md`).
- Bandwidth check: payload size times peak requests per second is compared with network capacity in the design review.
- Unneeded-field check (inferred in the notes): list contract fields no consumer reads; each is a stamp-coupling smell to trim.
