# Decision-guideline tables

Every "ADR Guideline" from the chapters this skill covers, kept in table form, in the book's three columns: the decision, the discussion points (questions to hold in the team), and the recommendations (what to put in your ADR, with the rationale). Use them as checklists when the answer is "it depends", and put the outcome in an ADR (template in `arch-decisions-and-tradeoffs`). Source for all: Mastering API Architecture (MAA), table numbers as in the book. The guidelines in chapter 7 (Table 7-1 do I need OAuth2, Table 7-2 which OAuth2 grants) are outside this skill; see `arch-api-security`. Chapters 6 and 9 (threat modelling, cloud migration) have no guideline tables of this kind in the notes.

Contents: Table 1-2 API standard; 1-3 modelling exchanges; 2-1 testing strategy; 2-2 contract testing; 2-3 integration testing; 2-4 end-to-end testing; 3-2 proxy, load balancer or gateway; 3-4 selecting a gateway; 4-1 mesh or libraries; 4-5 selecting a mesh; 5-2 separating release from deployment; 5-3 opinionated platforms; ADR format; supporting reference tables.

## Table 1-2: Choosing an API standard

| Decision | Which API standard should we adopt? |
|---|---|
| Discussion points | Do we already have company standards, and can they extend to external consumers? Do third-party APIs we expose (for example identity services) already follow a standard? What is the impact on consumers of having no standard? |
| Recommendations | Pick the standard matching organisational culture and the existing API inventory. Be ready to evolve it or add domain- or industry-specific amendments. Start early to avoid breaking compatibility later for the sake of consistency. Be critical of existing APIs: are they in a format consumers would understand, or is more effort needed? |

## Table 1-3: Modeling exchanges

| Decision | What format should we use to model the API for our service? |
|---|---|
| Discussion points | North-south or east-west? Do we control the consumer code? Is there a strong business domain across multiple services, or do we want consumers to build their own queries (hint: GraphQL)? What are the versioning considerations? What are the deployment and change frequencies of the underlying data model? Is it high traffic with bandwidth or performance concerns? |
| Recommendations | External consumers: REST (low barrier to entry, strong domain model, loose coupling and low dependency). Two services under close producer control, or proven high traffic: consider gRPC |

Detail: `choosing-an-api-style.md`.

## Table 2-1: Testing strategies

| Decision | When building your API, which testing strategy should be part of the development process? |
|---|---|
| Discussion points | Do all stakeholders have time to discuss regularly how the API should work (otherwise the product stalls waiting for decisions)? Are skills and experience available, or is there time to train? Do workplace practices or requirements already prescribe strategies? |
| Recommendations | Use test quadrants plus the test pyramid. If a business person is not readily available for the quadrant, at least use the pyramid (it concentrates automated testing and finds bugs early). Someone always has to guide product direction |

## Table 2-2: Contract testing

| Decision | Use contract testing? If so, consumer-driven or producer contracts? |
|---|---|
| Discussion points | Ready to add another testing layer developers must learn? Centralised or in-project contracts? Need extra tools or training? For the methodology: do you know who will use the API? Only within your organisation? Are consumers willing to engage to drive functionality? |
| Recommendations | Use contract testing when building an API; it is worth the learning curve. Large external audience: producer contracts (protect backward compatibility). Internal API: work toward consumer-driven contracts, starting with producer contracts and evolving. If contract testing is infeasible, producers need alternatives (careful request/response tests, tricky and time-consuming) and a way for consumers to test |

## Table 2-3: Integration testing

| Decision | Should integration testing be added to API testing? |
|---|---|
| Discussion points | For each integrated service, what level of integration test? Confident that mocking responses suffices? Can you craft stub requests and responses accurately, or should they be recorded? Can you keep stubs up to date and recognise an incorrect interaction? (Stale stubs mean passing tests and a production failure.) |
| Recommendations | Use generated stub servers from contract tests; otherwise integration tests with recordings. Local integration tests give confidence, especially when refactoring an integration |

## Table 2-4: End-to-end testing

| Decision | Use automated end-to-end tests? |
|---|---|
| Discussion points | How complex is the setup? Do you know which end-to-end tests provide value? Any special or advanced requirements? |
| Recommendations | At minimum automate end-to-end tests for core user journeys, ideally locally runnable, otherwise in the build pipeline. Balance against setup time. If not automatable, keep a run book of manual tests executed in a test environment before each production release (this slows delivery considerably) |

Detail for 2-1 to 2-4: `api-testing-and-contracts.md`.

## Table 3-2: Proxy, load balancer or API gateway

| Decision | Use a proxy, load balancer or API gateway for routing ingress? |
|---|---|
| Discussion points | Simple routing, a single endpoint to a single backend? Cross-functional needs (authn, authz, rate limiting)? API management needs (API keys or tokens, monetisation, chargeback)? An existing solution or organisation-wide mandate that traffic goes through certain edge components? |
| Recommendations | Always the simplest solution for the requirements, with an eye on the immediate future and known requirements. Advanced cross-functional requirements: API gateway. Enterprise: a gateway supporting API management. Check existing mandates and solutions first |

## Table 3-4: Selecting an API gateway

| Decision | How should we approach selecting an API gateway? |
|---|---|
| Discussion points (answer yes to each) | Prioritised all requirements? Identified existing gateway-like technology in the organisation? Know team and organisation constraints? Explored the future roadmap? Honest build-versus-buy costs? Aware of all available solutions? Consulted all stakeholders? |
| Recommendations | Focus on the six drivers: reduce coupling, simplify consumption, protect from overuse and abuse, observe consumption, manage as products, monetise. Ask: is a gateway already in use? Has a patchwork been assembled (for example a hardware load balancer with the monolith doing auth and routing)? How many edge components exist (WAF, load balancer, edge cache)? Consider team skills, staff availability and budget. Identify planned changes that affect traffic management. Calculate total cost of ownership of current gateway-like implementations and the candidates. Consult analyst and trend reports and reviews. Involve developers, QA, the architecture review board, the platform team and InfoSec |

Detail: `gateways.md`.

## Table 4-1: Service mesh or libraries

| Decision | Use a service mesh or a library for routing service traffic? |
|---|---|
| Discussion points | A single programming language in the organisation? Only simple service-to-service routing for REST/RPC? Cross-functional needs (authn, authz, rate limiting)? An existing solution or organisation-wide mandate to route through specific components? |
| Recommendations | Single mandated language or framework: use language libraries. Always the simplest solution for the requirements. Advanced cross-functional requirements, particularly across languages and stacks: a mesh may be best. Check existing mandates |

## Table 4-5: Selecting a service mesh

| Decision | How should we approach selecting a service mesh for our organisation? |
|---|---|
| Discussion points (answer yes to each) | Identified and prioritised all requirements? Identified current technology already deployed in this space in the organisation? Know all team and organisational constraints? Explored the future roadmap? Honestly calculated build-versus-buy costs? Explored the landscape and aware of all solutions? Consulted and informed all stakeholders? |
| Recommendations | Focus on reducing internal API and system coupling, simplifying consumption, protecting APIs from overuse and abuse, understanding how APIs are consumed, managing APIs as products. Is a mesh already in use, or has a collection of technology been assembled (libraries, SRE-deployed sidecars)? Consider team skill, people availability and budget. Identify planned changes affecting internal traffic. Calculate total cost of ownership of all current mesh-like implementations against future options. Consult analyst reports and reviews. Consult developers, QA, the architecture review board, the platform team and InfoSec |

Detail for 4-1 and 4-5: `service-mesh.md`.

## Table 5-2: Separating release from deployment (traffic management and feature flags)

| Decision | How do you go about separating release from deployment? |
|---|---|
| Discussion points | Is it possible in the systems live today? What is the degree of coupling between consumer and producer? Is there a build pipeline able to enforce the loose-coupling requirements of traffic-managed APIs (compatibility tested)? |
| Recommendations | Start by separating deploy and release of existing software (enables evolutionary architecture, simplifies the system). Feature flags are a good way; review recommended practices and pitfalls; flags can become a single point of failure. Review the coupling type between APIs and pick the release strategy for the situation |

## Table 5-3: Opinionated platforms

| Decision | Should you adopt an opinionated platform for deployments and releases? |
|---|---|
| Discussion points | Which languages are used; can you centre on a few? Can you empower developers as customers and run the platform as an internal product? Which constraints and features add value (for example monitoring and observability out of the box)? How do you update platform recommendations and push changes to teams already on it? |
| Recommendations | Treat developers as customers with a feedback channel. Make key features transparent (auto-configure a library for OpenTelemetry). New apps always get the latest stack; plan how existing users get new features |

Detail for 5-2 and 5-3: `release-strategies.md`.

## ADR format used by the book

| Section | Content |
|---|---|
| Status | Proposed, then Accepted or Rejected, later possibly Superseded |
| Context | The problem and its bounds, not a blog post |
| Decision | What will be done and how |
| Consequences | Trade-offs, risks, follow-ups (can be costly to get wrong) |

Practices: an ADR records collective thinking, so discuss before writing; publish where key participants can comment and move it to accepted; keep ADRs immutable, rejected ones included (they record a change in perspective); the reviewer checks both agreement and whether an alternative was missed; publish beyond the team. Worked example ADR001 (Separating attendees from the legacy conference system): split the Attendee component into a standalone service; consequences include added out-of-process latency to test, a possible single point of failure, and the need for design, versioning and testing discipline with multiple consumers. Worked example ADR501 (extracting Sessions): consequences include a bidirectional dependency between Attendee and Session, a possible single point of failure, and sharp usage spikes during a live conference. The full template and checklist live in `arch-decisions-and-tradeoffs`.

## Supporting reference tables (used elsewhere in this skill)

| Table | Where |
|---|---|
| 1-1 Richardson maturity model | `choosing-an-api-style.md` |
| 3-1 Reverse proxy, load balancer, gateway capabilities; 3-3 Gateway taxonomy | `gateways.md` |
| 4-3 Ingress versus service-to-service; 4-4 Library, sidecar, kernel taxonomy | `service-mesh.md` |
| 5-1 API lifecycle | `specification-and-versioning.md` |
| 8-1 Fitness function categories | `evolving-with-apis.md` |
| 13-1 to 13-4 Hard Parts contract trade-offs | `contract-strictness.md` |
