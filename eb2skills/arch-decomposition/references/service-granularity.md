# Service granularity: when to split a service and when to merge services

Contents: 1. Framing; 2. Disintegrators (six); 3. Integrators (four); 4. Tables; 5. Decision procedure; 6. Trade-off statement for a sponsor; 7. Worked decisions; 8. Verify; 9. Limits.

Source: Architecture: The Hard Parts ch. 7 (both halves). Complements `component-decomposition-patterns.md` (start coarse) and `decomposing-data.md` (the data side of a split).

## 1. Framing

- Modularity is breaking a system into parts. Granularity is the size of the parts. Most distributed-system trouble is granularity trouble, not modularity trouble.
- Granularity is defined by what a service does, not by classes or lines. Two rough objective proxies: the number of statements, and the number of public interfaces/operations. Both are somewhat subjective; they are the best available.
- "Micro means small, single responsibility" is a subjective argument. Replace gut feel with disintegrators (reasons to break up) against integrators (reasons to keep together). The usual team mistake is looking only at disintegrators. The right granularity is the equilibrium between the two.
- Not every part of an application has to be a microservice.

## 2. Disintegrators: should this service be broken apart?

Each has a question, a way to measure, and a caveat.

1. Service scope and function. Question: is the service doing too many unrelated things? Measure: cohesion (how operations relate; LCOM exists but judgement is subjective), size (statements, public entry points). Example: Notification (SMS, email, postal letter) is already cohesive ("tell the customer"), so function alone does not justify a split. A Customer Profile service doing profile, preferences and website comments has weak cohesion and splits into three. Related to the Single Responsibility Principle, whose looseness is where teams go wrong.
2. Code volatility. Question: are changes isolated to one part of the service? Measure: change frequency from version control, per part. Example: SMS changes about every six months, email about every six, postal letter weekly. In one service every letter change forces test and redeploy of SMS and email and risks their downtime. Split into Electronic Notification (SMS plus email, related and cohesive) and Postal Letter Notification. Benefit: smaller test scope, lower deployment risk, no disruption to the stable parts.
3. Scalability and throughput. Question: do parts need to scale differently? Measure: demand per function. Example: SMS 220,000/min, email 500/min, letter 1/min. In one service, email and letter scale to SMS's needs, which costs money and hurts elasticity (start-up time). Split into SMS, Email and Letter.
4. Fault tolerance. Question: do errors in one part crash critical functions of the whole service? Example: email repeatedly runs out of memory and takes SMS and letter down with it, so isolate email. Rule: when you split, check that the leftover pieces still form a cohesive, nameable service. Combining SMS and letter leaves names like "Other Notification" or "Non-Email"; only the three-way split gives good names (and leaves room for a social-media notifier). Contrast: the volatility split was two services because the leftover (SMS plus email) was cohesive.
5. Security. Question: do some parts need stronger protection than others? Securing storage (separate schema, database or region for PCI data) is not enough; also secure the access paths. A Customer Profile service that includes credit-card maintenance exposes card operations to every caller of the profile service (for example someone just reading a name). Splitting card maintenance into its own service gives service-level access control. See the design-versus-architecture note in section 7 before choosing this.
6. Extensibility. Question: does the service keep gaining new contexts? Example: a Payment service handling credit card, gift card, PayPal, later reward points, store credit, ApplePay. In one service each addition retests and redeploys everything; split by payment method so each new method is a new service. Caveat: apply only when expansion is planned or inherent to the domain (payments yes; notification channels unlikely). Because guessing is hard, wait to use this as the main justification until a pattern of expansion is confirmed.

## 3. Integrators: should these services be put back together, or not split?

1. Database transactions. Question: is an ACID transaction required across what would be separate services? Example: Customer Profile plus a separate Password service. Splitting gives access control, but "register new customer" now spans two commits; if the second fails the data is inconsistent and needs complex, error-prone compensation (sagas, see `arch-distributed-workflows`). If the business needs a single ACID unit of work, consolidate.
2. Workflow and choreography (east-west calls). Question: do services need to talk to each other? Three consequences of chatty fine-grained services:
   - Fault tolerance: with synchronous chains, if C goes down everything that depends on it, directly or transitively, is down. The fault-tolerance gain of splitting is illusory when services are tightly dependent.
   - Performance: a screen needing data from 5 services through choreography is 5 hops; at 300 ms network plus security latency per hop that is +1,500 ms. Consolidating removes it.
   - Reliability and integrity: adding a customer across 5 services each with its own transaction: A, B, C commit, D fails, leaving partial data that may already have been read or broadcast. Needs compensation or state markers.
   - Rule of thumb: count requests that need a multi-service workflow versus purely atomic ones. If about 30% need workflow and 70% are atomic, separation may be fine; if reversed, consider merging. If a latency-critical request is in the 30%, merge anyway. Back-end work where no user waits gets more leeway.
3. Shared code. Question: do the services need to share code? Shared libraries bind at compile time (see `reuse-patterns.md`). Infrastructure cross-cutting code (logging, auditing, authentication, authorisation, monitoring) is not a reason to merge. Consider merging when:
   - Specific shared domain functionality (business logic) is a high fraction of the code, for example shared code above 40% of the combined codebase of the profile/preferences/comments functions, especially if it changes often.
   - Shared code changes frequently, forcing coordinated change, test and deploy of every user.
   - Defects or business-rule changes cannot be versioned: they must apply to all services at the same time.
4. Data relationships. Question: can the data these services use be broken apart too? Assume split services get tight bounded contexts (no shared database). Map functions to tables: owner (writes, and its own reads) versus access (read-only). If service B needs a table owned by C in every operation and C needs a table owned by B in every operation, they must ask each other for data constantly; a service cannot read another's table directly because the owner may drop or alter a column for its own reasons. Mutual dependency means consolidate. The book calls this the integrator with the fewest trade-offs, because reorganising table relationships just to enable a split is usually not feasible (a monolith migration occasionally allows it, see `decomposing-data.md`).

## 4. Tables

Disintegrator drivers (break a service apart):

| Driver | Reason for applying |
|---|---|
| Service scope | Single-purpose services with tight cohesion |
| Code volatility | Agility: smaller test scope, lower deployment risk |
| Scalability | Lower cost, faster responsiveness |
| Fault tolerance | Better overall uptime |
| Security access | Better access control to certain functions |
| Extensibility | Agility: ease of adding new functionality |

Integrator drivers (put services back together):

| Driver | Reason for applying |
|---|---|
| Database transactions | Data integrity and consistency |
| Workflow | Fault tolerance, performance, reliability |
| Shared code | Maintainability |
| Data relationships | Data integrity and correctness |

Forces with their evidence:

| Force | Pushes toward | Evidence to collect |
|---|---|---|
| Scope/function (weak cohesion) | Smaller | Cohesion, statements, entry points |
| Volatility | Smaller | Commits per period per part |
| Scalability/throughput | Smaller | Requests per minute per function |
| Fault tolerance | Smaller | Crash and out-of-memory history; check the leftovers |
| Security | Smaller | Data and function classification |
| Extensibility | Smaller | Known, planned variants |
| Database transactions | Larger | ACID required across the operation |
| Workflow/choreography | Larger | Share of requests crossing services; latency; transitive dependencies |
| Shared code | Larger | Percent of shared domain code; change frequency; unversionable fixes |
| Data relationships | Larger | Cross-ownership, mutual reads |

## 5. Decision procedure

1. State the proposed split and the driver(s) claimed for it.
2. Demand evidence for each claim: statements and entry points; change rates from version control; per-function throughput numbers; crash and error history; security classification; the roadmap for extension. Test volatility claims against the repository's history rather than accepting them (in the book's ticketing case the shared database logic that was said to change a lot barely changed; see `reuse-patterns.md` section 8).
3. Check that every resulting piece can be named well and is cohesive.
4. Run all four integrators: is ACID needed; what share of requests cross the boundary and how critical are they (do the latency arithmetic); how much domain code would be shared and how often it changes; what is the table ownership map and are there mutual reads.
5. Split only if the disintegrator benefits outweigh the integrator costs. Otherwise keep together or merge. Prefer a coarser split first, learn from it, then refine.
6. Where a driver can be met at lower cost inside the deployable, do that: separate namespaces/components for assignment, routing and shared code inside one service capture part of the volatility benefit without the workflow cost.

## 6. Trade-off statement for the business owner

Granularity trade-offs are business trade-offs. Use this form:

1. Pick one disintegrator and the integrator it collides with.
2. Phrase it: "We want to split to get <benefit>, but then we lose <benefit>. Which matters more to the business?"
3. Let the product owner or sponsor decide on business grounds; record the decision and its consequences in an ADR.

Three decisions from the book show it:

- Isolate volatile code (time to market) against losing a database transaction (integrity): the sponsor chose integrity, keep one service.
- Keep together for the transaction against making sensitive functionality less secure: the sponsor, burned by past security incidents, chose security and the team worked out how to mitigate the consistency problem.
- Split payment for extensibility against slower responsiveness when an order uses several payment types: only two or three more payment types were expected within a couple of years, so favour responsiveness, do not split. The deciding fact was the rate of the extensibility need.

## 7. Worked decisions

Ticket assignment and routing (one service or two). Developers argued for a split because assignment algorithms are complex and change two or three times a month. Analysis found: once an expert is found the ticket is routed immediately; if routing fails another expert must be chosen, so routing calls back into assignment. Split means heavy two-way, synchronous coordination, and neither can exist without the other. Same scaling profile, no back-pressure need. Decision: one consolidated service, with three internal components (assignment, routing, shared code) as separate namespaces. Consequence recorded: frequent algorithm changes and rare routing changes force testing and deployment of both; larger test scope and deploy risk.

Customer registration (profile, credit card, password and security question, purchased products). Options: one service; four; two (Profile plus Customer Secure). Facts: one registration API on the back end; the product owner required that no customer record ever exist without its matching credit-card and password records (all or nothing); card and password data were already tokenised and encrypted; the real need was to control access to sensitive data separately from profile reads. Decision: a single customer service plus an access-control library applied at the gateway and again inside each service via the mesh. Consequences: the library is mandatory in the gateway and mesh; any change in the four data areas raises test scope and deploy risk; everything scales as one unit. The trade-off named: transactionality against security.

Lesson from the second case: security can often be achieved through design (library, encryption, access control) rather than architecture (splitting deployment units). Before splitting for security, check whether a design-level control meets the need. If you keep services merged for security reasons, verify that the control exists and is tested.

## 8. Verify

- Every split proposal lists driver, evidence (a number or a repository fact), and the integrators checked, with the result for each.
- Each resulting service has a good name and a one-sentence purpose with no "and other".
- The "tightly bound" test: would the split require synchronous calls in both directions for one user action? If yes, the workflow integrator applies.
- The latency arithmetic for the main user paths is written down (hops times per-hop latency) next to the latency budget.
- The ADR has a non-empty consequences list, naming what was given up.
- If kept merged for security: the compensating control exists and has a test.
- After deployment: measure what was predicted (cross-service calls per request, p99 latency on the main paths, deploy frequency of the isolated part). A split whose benefit cannot be seen in a metric within a few release cycles should be reviewed.

## 9. Limits

- The 30/70 workflow split, the 40% shared-code share and the 300 ms per hop are illustrative figures from the book's examples, not universal thresholds. Use your own measurements.
- Extensibility is the weakest disintegrator because it is a guess about the future. Wait until a pattern of expansion is confirmed before using it as the main justification (the book's advice); splitting when the second or third variant actually arrives is an adaptation of that.
- If the organisation is small, each extra service adds on-call, pipeline and monitoring cost (see `simplicity-checks.md`). Count that cost on the integrator side.
