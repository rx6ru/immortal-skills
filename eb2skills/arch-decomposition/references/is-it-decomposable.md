# Is it worth decomposing, and can this codebase be decomposed?

Contents: 1. Business case gate; 2. The five drivers and how to measure each; 3. Options short of distribution; 4. Elephant migration anti-pattern; 5. Decision tree; 6. Coupling and instability metrics; 7. Component-based decomposition vs tactical forking; 8. Why service-based first; 9. Rewrite vs refactor; 10. Verify.

Sources: Architecture: The Hard Parts ch. 3 and ch. 4; SRE Workbook ch. 7 (rewrite lesson).

## 1. Business case gate

Decompose for a stated business driver, never because "nothing else works" or because the current design feels untidy. The book names two business drivers:

- Speed to market (agility).
- Competitive advantage, which it defines as speed to market plus scalability plus availability/fault tolerance.

Triggers it lists: mergers and acquisitions (user volume, extensibility needs), competition, demand growth, ML/AI automation, and shifts in the technical environment (containers, cloud, DevOps, continuous delivery).

Procedure (Hard Parts ch. 3):

1. List what modularity can buy: maintainability, testability, deployability, scalability, availability/fault tolerance.
2. Match each benefit to a problem the current system demonstrably has (evidence, not opinion).
3. Write down the trade-offs you accept.
4. Record an ADR (template lives in `arch-decisions-and-tradeoffs`) and present the business case to the sponsor.

Explaining it to a non-technical sponsor: a monolith is one full glass of water. A second server running the same app does not help, because it is the same water. Splitting the app across two glasses gives real headroom. (The notes use 50% more headroom for the two-way split.)

## 2. The five drivers and how to measure each

Agility is composite: maintainability + testability + deployability. Scalability and availability/fault tolerance complete the five.

| Driver | What improves | How to measure now | Caveat: distribution can make it worse |
|---|---|---|---|
| Maintainability | Ease of adding, changing, removing features and doing internal upgrades | Component coupling, component cohesion, cyclomatic complexity, component size (statements), technical vs domain partitioning. Ask "how many teams or layers must touch a typical change?" | More modularity narrows the scope of change (layered monolith: application-level; service-based: domain-level; microservices: function-level), but only if the cuts follow domains. The notes mention a von Zitzewitz maintainability level that weights incoming coupling heavily; the exact formula was not recovered, so use the idea (high incoming coupling lowers maintainability) not a number. |
| Testability | Ease and completeness of testing | "What is the test scope of a change to X?" Count the tests that must run. Look for commented-out or obsolete tests and missing coverage of critical workflows | When services call each other a lot, a change to A drags B and C into the test scope and testability falls fast |
| Deployability | Ease, frequency and risk of deployment | Release frequency, code freezes, mock deployments, number of untested change combinations piled into a release | Chatty inter-service traffic raises deploy risk. If services must be deployed as a set in a fixed order, they belong back together in one deployable (Stine's rule, quoted in the notes). Otherwise you get a big ball of distributed mud |
| Scalability / elasticity | Scalability: staying responsive as load grows gradually. Elasticity: staying responsive in sudden spikes | Demand per function; mean time to startup (MTTS) | Elasticity depends mainly on granularity (small units with fast startup); scalability mainly on modularity (separately deployable units). Many synchronous calls per transaction hurt both |
| Availability / fault tolerance | A crash in one part leaves other parts working | Which function actually brings the system down (use incident or metric evidence) | Services that depend synchronously on a failing service get no isolation. Asynchronous communication is what makes the isolation real. Running load-balanced copies of a monolith is expensive and does not help against a bug present in every copy |

Style comparison from the notes (qualitative): layered monolith is low on scalability and elasticity (everything scales together, poor MTTS); service-based is better at scalability than elasticity (domain-level scaling, coarse services); microservices are highest on both (function-level scaling, excellent MTTS).

Evidence-to-driver mapping to reuse (from the running case): changes are slow and break things -> maintainability; more than 30% of tests commented out or obsolete, or the whole suite runs for a tiny change -> testability; monthly releases with freezes -> deployability (and the pipeline may also need fixing); one rarely-core feature (reporting, survey) taking the system down -> fault tolerance; freezes when more than 25 customers create tickets or when daytime reports run -> scalability and database load.

## 3. Options short of distribution

Modularity does not imply distribution. Check these first when the driver is maintainability, testability or deployability:

- Modular monolith: components partitioned by domain, boundaries enforced, still one deployable.
- Microkernel: plug-ins shrink the test and deploy scope of a change.

Neither helps with independent scaling or fault isolation, so if the evidence is about those, distribution is on the table. Say which driver the cheaper option cannot satisfy.

## 4. Elephant migration anti-pattern

Picking off whatever looks easy first ("eat the elephant one bite at a time", for example peeling off a knowledge base and a survey feature) is unstructured. It tends to end in a distributed monolith. Take a whole-system view and use component-based decomposition or, for a codebase without components, tactical forking.

Note that extracting a "simple" piece can still be a large bite: pulling out reporting also forces a decision about the data it reads (split the tables, or feed a reporting database through data pumps).

## 5. Decision tree

1. Is the codebase decomposable at all? Use section 6 metrics, plus the component dependency view in `component-decomposition-patterns.md` (pattern 4). This is an architect's judgement; no single number decides.
   - Mostly zone of pain or zone of uselessness, or event handlers wired straight to database calls: repairing structure may not be worth it. The notes suggest considering another approach such as a rewrite (inferred from the text).
2. Decomposable, but an unstructured mess with no definable components: tactical forking.
3. Decomposable, with well-defined or loosely defined components: component-based decomposition (target: domain services, see section 8).

## 6. Coupling and instability metrics

Definitions (Martin; Yourdon/Constantine), as the notes give them:

- Afferent coupling (Ca): incoming connections to a code artifact (component, class, function).
- Efferent coupling (Ce): outgoing connections.
- Abstractness A: abstract artifacts (interfaces, abstract classes) divided by concrete artifacts. The book's equation image was missing; Martin's usual form is abstract over total, so state which form you used. A codebase that is one 10,000-line main scores near 0.
- Instability I = Ce / (Ce + Ca), range 0 to 1. Near 1: highly unstable, changes in what it depends on force changes here, breaks easily. Near 0: stable if mostly abstract, rigid if mostly concrete. High stability costs reuse and invites duplication.
- Distance from the main sequence D = |A + I - 1| (reconstructed; the equation image was missing). The ideal is the line A + I = 1.
- Zone of uselessness: upper right (too abstract to use). Zone of pain: lower left (low A, low I: concrete, rigid, brittle).

Read I and A together, never one alone.

Reading the result:

- Most components near the main sequence with a few outliers: decomposable.
- Most components clustered in the zones of pain or uselessness: probably not worth salvaging as it stands.
- Better internal structure makes the structure easier to move; a poor foundation makes moving risky.

Use of Ca when pulling apart: classes like `Address` look free in a monolith. Ca tells you how many places depend on them, and therefore what must be shared, duplicated or owned once services exist.

How an agent can compute this (adaptation, not from the book):

1. Choose the unit: the directory or package that corresponds to a component. Compute Ca and Ce at the component level (imports between components), not class level, for the feasibility question.
2. Tools that give import graphs: JDepend or ArchUnit (Java), `dependency-cruiser` or `madge` (TypeScript/JavaScript), `import-linter` or `pydeps` (Python), `go list -deps` or `go mod graph` (Go), `cargo modules` (Rust). Verify the tool exists in the repo's ecosystem before relying on it; a 30-line script over import statements is acceptable if none does.
3. Abstractness is meaningful mainly in languages with explicit interfaces and abstract classes (Java, C#, Kotlin). In TypeScript, Python and Go, count interfaces, protocols, abstract base classes; if the count is near zero everywhere, A carries no information and you should lean on Ca/Ce and cycles instead.
4. Report the table (component, Ca, Ce, I, A, D), name the outliers, and give the verdict with the reason. Do not present D as precise; two of its inputs are definitions the notes could only reconstruct.

## 7. Component-based decomposition vs tactical forking

Most migration difficulty comes from poorly defined components. A component here is a building block with a well-defined role and operations, manifested as a namespace or directory. Build services from groups of components, not from single components.

Tactical forking (Fausto De La Torre): split a big ball of mud by deleting, not extracting. Extraction in a tightly coupled system drags the whole monolith along, so keep the dependencies and delete what you do not need.

Steps:

1. Decide the target services and teams.
2. Clone the whole monolith once per target; each team gets a full copy.
3. Each team deletes code it does not need, refactoring as it goes; deleting is checked by compiling and running simple tests.
4. End state: coarse-grained services that partition the original behaviour.

Benefits: start at once with almost no up-front analysis; deleting is easier than extracting.
Costs: leftover latent code in each service; internal quality no better than the monolith, only smaller; inconsistent naming of shared code makes common code hard to find and keep consistent; boundaries must be fixed up front; the team splits into smaller teams that need more coordination. It is tactical, not strategic: quick migration of a critical system with an unstructured result.

| | Component-based | Tactical forking |
|---|---|---|
| Fits | Codebase with identifiable components | Big ball of mud, no components |
| Up-front analysis | High (components, dependencies, domains) | Almost none |
| Speed | Slower | Faster |
| Shared/duplicate code | Managed: shared functionality identified | Duplicated in each fork, hard to keep consistent |
| Boundaries | Emerge from component grouping | Fixed before starting (one fork per service) |
| Team | One collaborating team | Split teams, more coordination |
| Risk | Safer, incremental, controlled | Quick but unstructured |

Deciding rule: if the metrics show most code on the main sequence and existing component boundaries are good, component-based wins when the problems are maintainability, testability and reliability, because applying one change to several diverged forks is exactly the pain you are trying to remove. Choose forking only when there are no usable components, time pressure dominates, and the team accepts the clean-up debt.

## 8. Why service-based first

When migrating a monolith to microservices, move to a service-based architecture first: coarse domain services over a shared database. Reasons from the notes:

- It lets you decide which domains need finer granularity later (see `service-granularity.md`).
- It does not require splitting the database yet; partition by function first, then data (see `decomposing-data.md`).
- It needs no new operational automation or containerisation: deploy the same artifact type.
- It is a technical move: no business-stakeholder involvement, no organisational change, no change to test or deploy environments.

The common mistake is starting too fine-grained and inheriting all of the microservice costs (data decomposition, distributed workflows and transactions, operational automation) without needing them.

## 9. Rewrite vs refactor

Two inputs:

- The component dependency picture (`component-decomposition-patterns.md`, pattern 4) classifies the job as golf ball (refactor), basketball (mix of refactor and rewrite) or airliner (rewrite).
- The SRE Workbook rewrite lesson (ch. 7, Borg vs Omega): the replacement chases a moving target; improvement of the old system is underestimated and the new one overestimated; migration cost (dual running, thousands of services' configs, years) is underestimated; wide APIs with many users are very hard to migrate. Compare the new system with what the current one would be if you spent the same effort improving it, not with the current one as is. Rewrites are sometimes right but their cost is usually understated. In that case the good ideas were fed back into the old system.

## 10. Verify

- The ADR names the driver, the evidence, and the trade-offs accepted. Evidence is a measurement or an incident record, not "it is hard to change".
- Metrics were computed on the actual repository and the outliers are named; the verdict follows from them.
- The cheaper alternative (modular monolith, microkernel, pipeline fix) was considered and the reason it falls short is written down.
- The chosen approach matches the codebase: forking is not chosen for a codebase with good component boundaries, nor component-based for one with none.
- Start-of-migration fitness functions exist (see `component-decomposition-patterns.md`), because the monolith keeps changing during migration.
