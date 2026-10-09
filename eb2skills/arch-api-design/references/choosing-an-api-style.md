# Choosing an API style per exchange

Contents: 1. Decide per exchange, not per company; 2. Questions to answer first; 3. REST; 4. gRPC / RPC; 5. GraphQL; 6. Transport facts that affect the choice; 7. Decision table; 8. Offering more than one style; 9. Async and event-driven exchanges; 10. Remote calls are not local calls; 11. Verify

Sources: Mastering API Architecture (MAA) ch. 0, ch. 1, ch. 10; DDIA 2e ch. 5; Hard Parts ch. 13.

## 1. Decide per exchange, not per company

The book's recurring conclusion is that the question is not "REST versus gRPC" but which fits this particular exchange between this producer and this consumer (MAA ch. 1). One system normally contains several exchanges with different answers. In the running case study the Attendee service has two consumers: the legacy conference system (same organisation, close coordination, east-west) and an external CFP system (other team, needs loose coupling, north-south). They get different decisions.

Vocabulary used throughout the skill:
- North-south: ingress from external clients over the internet. Identity must be checked before traffic enters; usually handled by an API gateway (see `gateways.md`).
- East-west: service-to-service traffic inside your own group of applications. Mostly trusted to a degree but still secured; handled by service discovery, a mesh, or libraries (see `service-mesh.md`).
- One north-south request typically fans out to several east-west calls, so slow internal exchanges show up as slow external responses.

## 2. Questions to answer first (MAA Table 1-3 discussion points)

1. North-south or east-west?
2. Do we control the consumer code?
3. Is there a strong business domain spanning several services, or do consumers need to compose their own queries (hint toward GraphQL)?
4. What are the versioning constraints?
5. How often does the underlying data model deploy or change?
6. Is traffic high enough that bandwidth or parse time matters, and has that been measured?

## 3. REST

Use when: external or third-party consumers, unknown consumers, browsers, public APIs. Reasons given: low barrier to entry, strong domain model, loose coupling, low dependency on the producer's internals.

What the style asks of the producer (MAA ch. 1): model resources; keep requests stateless; give cacheability hints (HTTP headers); use a uniform interface (verbs and resources); keep layers invisible (the consumer cannot tell whether a database or other services sit behind it). Representation goes in the body, metadata in headers (`Accept`, `Content-Type`). Returning a content type the consumer cannot parse (a PDF from a data API) is valid REST but useless to a program.

Richardson Maturity Model, as the book uses it:

| Level | Meaning | Guidance |
|---|---|---|
| 0 | One URI, HTTP as transport, effectively RPC | Avoid for resource APIs |
| 1 | Individual resources with identity (`/attendees/1`) | Minimum |
| 2 | Correct HTTP verbs per effect; GET guaranteed not to change state | Target this: understandable resource model, lower coupling, hides backing-service detail |
| 3 | Hypermedia: responses list next actions | Not required. Rare in modern services, chatty, and service-to-service consumers short-circuit it with an upfront spec. Can help flexible UIs |

Do not use REST as the default when: two services you own exchange very high traffic and measurements show payload or protocol cost matters; or consumers need to build their own cross-service queries (see GraphQL).

Detailed conventions (create, naming, collections, pagination, filtering, errors) are in `rest-design-standard.md`.

## 4. gRPC / RPC

Use when: east-west, you control both sides, proven or expected high traffic, large payloads, a need for streaming or async capabilities. Recommended for higher-traffic internal services, with the caveat that any performance decision should be measured.

Facts that shape the choice:
- RPC exposes a method of one process to another and does not project a domain model to the consumer. It conveys exact method-level functionality, so coupling is higher. That is acceptable east-west where performance matters.
- gRPC needs a schema (`.proto`) and generates client stubs and server base classes in many languages.
- State is implementation dependent in RPC and can accumulate. That is fast but costs reliability and routing simplicity. REST is stateless by definition.
- gRPC rides HTTP/2 (binary framing, compression, multiplexing many requests over one connection) with binary payloads by default. The advantage grows with payload size and request volume.
- Compatibility is stricter than JSON: fields are identified by number on the wire. See `compatibility-rules.md` for the exact rules.
- Browsers cannot call it without extra tooling. Use `grpcurl` or a gRPC UI for manual testing.
- Mesh and gateway note: L4 load balancing pins all requests of a multiplexed keep-alive connection to one backend, so gRPC needs L7-aware balancing (a mesh or L7 proxy) (MAA ch. 4).

## 5. GraphQL

Use when: mobile or other constrained clients, UIs, reporting-style access, many interconnected services that consumers must filter or join, or a gateway needs one consumer-facing API over several backends.

Facts:
- It is a query-language layer over existing services or datastores; the client asks for exactly the fields it needs, across several APIs. One GraphQL schema gives one version across APIs, so consumers do not juggle per-API versions.
- It is complementary to REST, not a replacement. A facade over legacy systems is possible, but a facade over well-designed APIs is simpler to build and maintain.
- Without it, consumers query several APIs sequentially, learn each structure, and waste bandwidth on unused fields.
- Cost to watch (from the gateway discussion): aggregation in the consumer-facing layer tempts business logic into the gateway. See `gateways.md`.

Hard Parts ch. 13 adds the contract view: GraphQL gives read-only aggregated views and lets each consumer define its own type (a wishlist consumer asks only for `name`), which is looser than RPC.

## 6. Transport facts that affect the choice

- JSON is verbose and parse time into domain objects varies by language, sometimes much worse than binary. "Human readable" is a weak argument when tracing tools exist and nobody reads full payloads; offset it with better logging and error handling (MAA ch. 1).
- HTTP/2 multiplexes: 20 attendee fetches on one connection instead of 20 TCP connections under HTTP/1.
- HTTP/3 maps the same HTTP semantics onto QUIC over UDP and removes HTTP/2 head-of-line blocking; ingress proxies and network components need upgrading (MAA ch. 10, a 2022 snapshot; check current support).
- High-traffic services (the Attendee id appears everywhere) multiply payload and protocol costs in money or time.
- Legacy ("vintage") components in the path: understand their performance impact before integrating.

## 7. Decision table

| Situation | Choose | Why |
|---|---|---|
| External consumers, unknown clients, public API | REST (resource-oriented, level 2) | Low barrier, loose coupling, strong domain model |
| Two services under one team's control, hot path, measured payload/latency cost | gRPC | Binary, HTTP/2, generated stubs |
| Mobile or UI that needs custom shapes across many services | GraphQL over REST/gRPC backends | Client picks fields; one schema, one version |
| Need streaming | gRPC streaming, or a broker | gRPC has async/streaming capabilities |
| Consumers not under your release control (mobile store, partners) | Loose contract plus consumer-driven contract tests (`contract-strictness.md`) | Slow deploy channel punishes strict contracts |
| Process spanning several services that must survive crashes | Workflow engine or broker (see section 9) | A DB transaction cannot span services |
| Not sure, nothing measured | REST at level 2 | Cheapest to consume and evolve; switch the hot internal edge to gRPC when measurement says so |

## 8. Offering more than one style from one service

Possible, hard, and often wrong, because there is no golden specification from which all are generated (MAA ch. 1):
- `openapi2proto` orders fields alphabetically, so adding a backward-compatible field in the OpenAPI document renumbers existing proto fields and breaks binary compatibility. Several tools only support OpenAPI v2.
- `grpc-gateway` generates a REST reverse proxy from `.proto` using `google.api.http` annotations, best-effort mapping, familiar mostly to Go teams.
- Conceptually, forcing a hypermedia domain model into function calls (or the reverse) conflates RPC with APIs, and the evolution and versioning of both specifications become coupled.

The book's decision for the case study: design the east-west gRPC API independently of the north-south REST representation so each evolves freely. Record that choice in an ADR (template in `arch-decisions-and-tradeoffs`). Actively decide whether coupling the REST domain to the RPC domain adds value; if a gateway translating protocols is used, it becomes an adapter and coupling rises (see `gateways.md`, `evolving-with-apis.md`).

## 9. Async and event-driven exchanges

(DDIA 2e ch. 5, MAA ch. 10)
- A broker buffers when the recipient is down or slow, redelivers after a consumer crash, needs no service discovery, delivers one message to many recipients, and decouples sender from recipient. Two distribution patterns: queue (one consumer gets each message) and topic (all subscribers get it).
- Brokers are encoding-agnostic. Use protobuf, Avro or JSON with a schema registry that stores every valid schema version and checks compatibility. AsyncAPI is the messaging counterpart to OpenAPI; specify and contract-test async APIs too (MAA ch. 10, emerging as of 2022).
- A consumer that republishes messages must preserve unknown fields (see `compatibility-rules.md`).
- Durable execution engines (Temporal, Restate as of 2025) give exactly-once-like semantics for multi-service workflows by replaying a log and skipping steps that already succeeded. Constraints: external services still need idempotent APIs with unique ids; code must be deterministic; reordering calls in workflow code is unsafe, so deploy changed workflow code as a new version. Rule of thumb (inferred in the notes): durable execution when a business process spans services and must complete or compensate despite crashes; plain RPC with retries and idempotency keys when steps are few and idempotent; broker choreography when decoupling matters more than central control. Saga design itself belongs to `arch-distributed-workflows`.

## 10. Remote calls are not local calls

When an in-process interface is remodelled as an out-of-process API (a frequent architect task), add these to the design (DDIA 2e ch. 5, MAA ch. 0):
1. Requests and responses can be lost; the remote can be slow or down; plan retries.
2. A timeout leaves the outcome unknown: was the action processed?
3. Retries can duplicate the action unless the protocol is idempotent or deduplicates (idempotency keys).
4. Latency varies from sub-millisecond to seconds.
5. Parameters must be encoded to bytes; no pointers; large or mutable objects are hard.
6. Cross-language types differ (JavaScript numbers above 2^53).
Also the eight fallacies (network reliable, latency zero, bandwidth infinite, network secure, topology fixed, one administrator, transport free, network homogeneous) are why a reliability layer is needed (see `service-mesh.md`).

## 11. Verify

- For each exchange, the chosen style is written down with the answers to the section 2 questions (an ADR or a table row in the design doc).
- Any performance reason given for gRPC or binary encoding cites a measurement, not a belief.
- A service that offers two styles has two independently versioned specifications, or a written reason why they are coupled.
- External-facing contracts are REST/JSON (or have a written reason otherwise) and have an OpenAPI document that passes the checks in `specification-and-versioning.md`.
