# Simplicity as an operational property

Sources: SRE Workbook ch. 7 (Simplicity, both parts). Epigraph: a complex system that works evolved from a simple system that worked (Gall's Law). Simple software breaks less and is easier and faster to fix, understand, maintain and test. For SREs simplicity is end to end: code, architecture, and tools and processes across the lifecycle.

## Contents

1. Measuring complexity
2. Why simplicity needs a champion
3. Case: typed schemas versus generic key/value bags
4. Case: rewrite or improve (Borg versus Omega)
5. Regaining simplicity
6. Design smells to look for when diagramming
7. Case: the ads "spiderweb" (uniformity standards)
8. Case: hundreds of microservices on a shared platform
9. Case: a DNS service that depended on itself
10. Review procedure
11. Verification
12. Warning signs

## 1. Measuring complexity

- Code level: cyclomatic complexity number (distinct paths; a block with no loops or conditionals is 1), well supported in IDEs. It cannot tell necessary from accidental complexity or show system-wide effects.
- System level: formal measures are rare, and counting entities and communication paths explodes. Practical proxies:
  - Training time: how long until a new member can go on call.
  - Explanation time: how long to explain the whole-service architecture on a whiteboard, including functionality and dependencies.
  - Administrative diversity: the number of ways and places to configure similar settings.
  - Diversity of deployed configurations: unique combinations of binaries, versions, flags and environments in production.
  - Age: by Hyrum's Law, over time users depend on every observable aspect of an API implementation, making behaviour fragile.
- Complexity grows in living systems unless countered, and countering is worthwhile.

## 2. Why simplicity needs a champion

Systems grow organically and every change touches neighbours (adding retries in one component can overload a database and destabilise the whole system). Complexity is an externality: the cost falls on those working around it, not on the person who introduced it. So you need an end-to-end champion. SREs fit because they see the whole system and its dependencies.

Actions: have engineers draw and redraw system diagrams before the first on-call and keep a canonical set in the docs; have an SRE review all major design docs and require docs to show how the design changes the system architecture; SREs may propose simplifying alternatives. Product developers usually know only a subsystem, so SREs draw the system-level diagrams. Adaptation for an agent: when a change adds a dependency, retry, config path or new service, state in the PR what the architecture looks like after the change and what could be removed.

## 3. Case: typed schemas versus generic key/value bags

A startup's core libraries used a generic key/value bag for every RPC request and response (flexible; shared serialization, encryption, logging). The cost fell on clients: keys, values and types were undocumented per service, and backward and forward compatibility was hard as parameters changed. Structured, typed schemas (Protocol Buffers, Thrift) look more complex than generic containers but give a simpler end-to-end system, because they force up-front design decisions and documentation. This generalises to JSON-blob or dict-typed APIs, untyped event payloads and "options" maps. See `arch-api-design` and `arch-data-storage` for schema evolution rules.

## 4. Case: rewrite or improve (Borg versus Omega)

Omega was to be a cleaner replacement for Borg. Problems: Borg kept evolving (a moving target); estimates of improving Borg were too pessimistic and of Omega too optimistic; migration cost was underestimated (millions of lines of config across thousands of services and many SRE teams; years of running both). Outcome: Omega's ideas were fed back into Borg and used to jump-start Kubernetes.

Decision rule for rewrites:
1. Count the full lifecycle: development toward a moving target, a full migration plan, dual-running costs.
2. Wide APIs with many users are very hard to migrate.
3. Do not compare the new system with the current one as-is; compare it with what the current system would be if you invested the same effort in improving it.
Rewrites are sometimes right, but the costs are usually underestimated.

## 5. Regaining simplicity

- Most simplification is removing things: drop an unused dependency or data fetch, or redesign (two consumers needing the same remote data: fetch once and forward).
- Simplification improves engineering time efficiency and cognitive load. Leadership must celebrate and prioritise it like feature launches; measure and celebrate code removal as you do addition (lines are "lines spent", not "produced").
- Treat it as a feature: staff it and reserve time, for example about 10% of engineering project time for simplicity projects (not a licence to add complexity in the other 90%); brainstorm known complexities as a team.
- As systems grow, splitting SRE teams reduces scope and motivation for cross-cutting simplification. Counter with a small rotating group with working knowledge of the whole stack (less depth) that pushes conformity and simplification.

## 6. Design smells to look for when diagramming

- Amplification: an error or timeout retried at several levels multiplies the total RPCs. Retry at one layer, with limits (`managing-load.md`).
- Cyclic dependencies: a component depends on itself, often indirectly. This can make cold start of the whole system impossible.
- Redundant lookups within one request (a "system smell", the analogue of duplicated functions as a code smell).
- Request-flow loops between servers.

## 7. Case: the ads "spiderweb" (uniformity standards)

Products from acquisitions were bolted onto Google infrastructure by rewriting requests between separate frontends and auction programs. Traffic was hard to observe, capacity hard to provision per component, and query-flow loops were possible (they added tests asserting no infinite loops in query flow). Ads-serving SREs, on call for the entire stack, drafted uniformity standards and worked incrementally with each dev team: one way to copy large data sets, one way to do external data lookups, common templates for monitoring, provisioning and configuration.

Mechanic for consolidating servers: add logic to common programs to satisfy all use cases, guard each behaviour with flags, then remove the flags and fold functionality into fewer backends. Afterwards a data lookup happened once in the unified auction server rather than once per targeting system. Lessons: integrate an already-running system incrementally; standards with SRE and developer buy-in give managers a clear blueprint they will endorse and reward.

## 8. Case: hundreds of microservices on a shared platform

Many product verticals had bespoke production stacks (own workflow, CI/CD, monitoring) with dedicated SRE teams, making it hard to move services or engineers. Teams converged onto one managed microservices platform run by one SRE group, which bakes in best practices and auto-configures previously underused reliability and debugging features. Rule: new in-scope services must use the platform; legacy services migrate or phase out. Services are "managed, not hosted": teams keep control and responsibility, with a UI, API and CLI for release and monitoring. Outcome: developers run hundreds of services without deep SRE engagement, and tiered SRE engagement emerged. Lesson: standardisation is a long-term investment; make each step deliver incremental productivity wins developers can see; do not ask for a huge refactor that pays off only at the end.

## 9. Case: a DNS service that depended on itself

Clients found a lookup service through a private DNS service; the DNS service was reached through a load balancer that found DNS server IPs using the lookup service: a circular dependency introduced unintentionally and noticed late. It worked day to day because the data to break the loop existed somewhere, but a cold start would have been impossible. Fix: a low-level component on every machine keeps a local list of current IPs of nearby lookup servers, plus an explicit allowlist of services permitted to use the DNS service, shrunk over time. Lessons: use explicit allowlists for a service's dependencies to prevent accidental additions; actively look for circular dependencies, especially in bootstrap and cold-start paths (DNS, auth, config, discovery).

## 10. Review procedure

1. Draw the request and dependency graph after the proposed change.
2. List what the change adds: dependencies, configuration paths, retries, new formats, new services.
3. For each, ask what could be removed instead (an unused fetch, a duplicate lookup, a second way of doing the same thing).
4. Check for amplification and cycles, in steady state and in cold start.
5. For a rewrite proposal, compare against an improved current system, and write the migration and dual-running plan before approving.
6. For anything with many near-identical variants, propose one standard way and a migration path with visible wins at each step.

## 11. Verification

Inferred checks in the notes: track training time, explanation time, the count of distinct deployed configurations and the number of configuration mechanisms; check that design reviews include SRE and updated architecture diagrams; check retry budgets are applied at a single layer; run a dependency-graph cycle check; do a cold-start (from zero) bring-up drill of foundational services; count distinct code paths for the same operation and times the same datum is looked up per request (from a trace); assert absence of cycles in the request-flow graph with a test.

Adaptation: a dependency-cycle check can be a CI job over a declared service graph (a topological sort that fails on a cycle); a duplicate-lookup check can compare span names per trace in a staging run.

## 12. Warning signs

Long time to first on-call; many ways to configure the same setting; many unique deployed configurations; generic untyped payload APIs; retries stacked at multiple layers; rewrites justified by comparison with the current state rather than an improved state; no one rewarded for deleting code.
