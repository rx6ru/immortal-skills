# Complexity and simplicity checks for a decomposition

Contents: 1. Why this belongs in a decomposition review; 2. Measuring complexity; 3. Design smells to look for in diagrams; 4. Case lessons; 5. Regaining simplicity; 6. A pre-split and post-split checklist; 7. Verify; 8. Limits.

Source: SRE Workbook ch. 7 (Simplicity, both halves). Gall's Law is the epigraph there: a complex system that works evolved from a simple system that worked. The chapter says simple software breaks less and is easier to fix, understand, maintain and test.

## 1. Why this belongs in a decomposition review

Each extra service, library, configuration mechanism or hop is complexity. Complexity is an externality: its cost falls on the people who work around it, not on the person who introduces it. So the question "does the split pay for its added complexity?" needs a champion with an end-to-end view. In the book that is the SRE; for an agent it means taking the whole-system view when a request is framed as "extract this one service". Systems grow organically and every change touches neighbours: adding retries in one component can overload a database and destabilise the system.

## 2. Measuring complexity

Code level: cyclomatic complexity (number of distinct paths; a block with no loops or conditionals scores 1) is supported in IDEs. It cannot tell necessary from accidental complexity or show system-wide effects.

System level: formal measures are rare, and counting services and paths explodes. Practical proxies from the notes:

| Proxy | How to measure | What a high value means |
|---|---|---|
| Training time | Days until a new engineer can go on-call | Poor documentation or too many moving parts |
| Explanation time | Minutes to explain the whole architecture on a whiteboard, with functionality and dependencies | The picture does not fit in one head |
| Administrative diversity | Count of ways and places to configure similar settings | Inconsistent conventions |
| Diversity of deployed configurations | Unique combinations of binaries, versions, flags, environments in production | Hard to reason about what is running |
| Age | Years in service. Per Hyrum's Law, over time users depend on every observable behaviour, so behaviour is fragile | Changes break unknown dependants |

Agreed observations: complexity grows in living systems unless countered, and countering is worthwhile. Pick proxies, track them over time, improve them.

## 3. Design smells to look for in diagrams

Have engineers draw and redraw the system diagram, keep a canonical set in the docs, and require design documents to show how the change alters the architecture. While diagramming, look for:

- Amplification: an error or timeout retried at several levels multiplies the total number of RPCs. Apply retries at one layer and budget them.
- Cyclic dependencies: a component depends on itself, often indirectly. These can make a cold start of the whole system impossible, especially in bootstrap paths (DNS, authentication, configuration, discovery).
- Redundant lookups within one request (the same datum fetched once per subsystem): a system smell, the analogue of duplicated functions in code.
- Generic untyped payloads (key/value bags, JSON blobs, "options" maps): look simpler and push undocumented keys, types and compatibility problems onto every client. Structured, typed schemas (Protocol Buffers, Thrift; adaptation: OpenAPI or JSON Schema, typed events) look heavier but give a simpler end-to-end system because they force design decisions and documentation up front.

## 4. Case lessons

Rewrite versus improve (Borg and Omega). A cleaner replacement for a running system ran into: the old system kept evolving, estimates of improving the old were too pessimistic and of the new too optimistic, and migration was underestimated (millions of lines of configuration across thousands of services, years of dual running). Rules: cost the full lifecycle, including a moving target and dual running; wide APIs with many users are very hard to migrate; compare the new system with the old as it would be after the same investment in improving it. The good ideas were fed back into the old system. Relevance: a decomposition that is really a rewrite should face the same test.

Display Ads spiderweb. Acquired products had been bolted on by rewriting requests between separate frontends and auction programs, so traffic was hard to observe, capacity hard to provision, and query-flow loops possible (tests were added asserting no infinite loops). The people on call for the whole stack drafted uniformity standards and worked incrementally with each team: one way to copy large data sets, one way to do external lookups, common templates for monitoring, provisioning and configuration. Consolidation mechanic: add logic to common programs for all use cases, guard each behaviour with a flag, then remove the flags and fold functionality into fewer backends. After unification a lookup happened once in the unified auction server instead of once per targeting system. Lessons: integrate an already running system into your infrastructure incrementally; standards with both operations and development buy-in give managers a blueprint they will reward.

Hundreds of microservices on a shared platform. Many product verticals had bespoke production stacks (own workflow, CI/CD, monitoring), each with a dedicated team, so moving services or engineers was hard. They converged on one managed platform run by one group. Rule: new in-scope services must use it; legacy services migrate or are phased out. Services are managed, not hosted: service teams keep control and responsibility, the platform provides UI, API and CLI workflow tools. Result: teams run hundreds of services without deep specialist engagement, and engagement became tiered. Lessons: standardisation is a long-term investment; each step must give developers visible, incremental wins; do not demand a huge refactor that pays off only at the end.

A lookup service that depended on itself. Clients find a lookup service (Svelte) via a DNS-like system (pDNS), which is reached via a load balancer that finds pDNS servers using Svelte: a circular transitive dependency, unintentional and noticed late. It worked daily because the data to break the loop existed somewhere, but a cold start would have been impossible. Fix: a low-level component on every machine keeps a local list of nearby lookup servers; an explicit allowlist of services allowed to depend on pDNS was added and shrunk over time. Lessons: use explicit allowlists for a service's dependencies; actively look for cycles in bootstrap paths.

## 5. Regaining simplicity

- Most simplification is removal: drop an unused dependency or data fetch, or redesign (two consumers needing the same remote data: fetch once and forward).
- It is a feature. Staff it and reserve time: for example about 10% of engineering project time for simplicity projects (the other 90% is not a licence to add complexity). Celebrate deleted code like added code.
- As systems grow and teams split, motivation for cross-cutting simplification drops. Counter it with a small rotating group with working knowledge of the whole stack that pushes conformity and simplification.
- Standardise through incremental, visible wins.

## 6. Pre-split and post-split checklist

Before approving a new service or a split:

1. Does it remove a pain with evidence (section 2 of `is-it-decomposable.md`), or only follow fashion?
2. Count what it adds: deployables, pipelines, dashboards, on-call surface, configuration places, network hops on the main paths, shared libraries. Write the number.
3. Does it add a cycle or a retry layer? Draw the request flow before and after.
4. Does it use the shared platform and conventions, or does it add a new way to do something that already has one?
5. Is the payload typed and versioned?

After a decomposition:

6. Re-measure the proxies. Training time and explanation time should not have grown more than the benefit justifies.
7. Look for services that always deploy together, always fail together, or call each other in both directions. Those suggest the wrong cut (see `service-granularity.md`).
8. Look at the cold-start order: can the whole system start from nothing?

## 7. Verify

- Dependency graph cycle check in CI (for example `import-linter` or `madge --circular` for TypeScript; for service-level graphs, derive from service configuration or traces). Fails the build on a new cycle.
- Allowlist of permitted dependencies for foundational services (discovery, configuration, authentication), enforced in code or network policy.
- Trace sampling: number of times the same datum is fetched per request; number of retries per layer (should be one layer).
- A from-zero bring-up drill for foundational services, run at least once after the decomposition.
- Count of distinct code paths for the same operation; count of unique deployed configurations (images times flags times environments).
- Design reviews include an updated architecture diagram; a reviewer with whole-system knowledge has looked at it.

## 8. Limits

- The 10% figure and the idea of a dedicated champion come from a large, specialised organisation; scale the practice down (one person reviewing diagrams; a half-day a sprint for removal).
- Proxies are not targets; use them to start conversations and track direction.
- Simplicity can be used to argue against any change. The test is the cost comparison in the checklist, not a preference for fewer parts.
