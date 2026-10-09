# The six component-based decomposition patterns

Contents: Overview; Pattern 1 Identify and Size; Pattern 2 Gather Common Domain Components; Pattern 3 Flatten; Pattern 4 Determine Dependencies; Pattern 5 Create Component Domains; Pattern 6 Create Domain Services; Fitness-function inventory; Implementation sketches; Verify.

Source: Architecture: The Hard Parts ch. 5 (with ch. 4 for context). Numbers in the "Sysops Squad" lines come from the book's running case.

## Overview

Use these when the monolith has some structure (namespaces or directories) and you want to turn it into separately deployed domain services. Apply them in order for the initial migration, then individually as day-to-day changes touch the monolith, because the system keeps moving while you migrate.

| # | Pattern | Output |
|---|---|---|
| 1 | Identify and Size Components | Inventory table; outliers split |
| 2 | Gather Common Domain Components | Duplicated domain logic consolidated (after a Ca check) |
| 3 | Flatten Components | Code only in leaf nodes; shared code tagged |
| 4 | Determine Component Dependencies | Dependency diagram, total-coupling metric, feasibility verdict |
| 5 | Create Component Domains | Domain namespaces and an approved domain list |
| 6 | Create Domain Services | Deployed domain services (service-based architecture) |

A component is a leaf-node namespace or directory with a clear role. The namespace `penultimate.ss.ticket.assign` corresponds to the directory `ss/ticket/assign`, and the component is "Ticket Assign". The mapping to other ecosystems is direct: a Go package directory, a Python package, a TypeScript folder with an index, a Rust module.

Each step in the book creates an "architecture story": a work item recording a structural refactoring done for a business driver (for example "decouple Payment to support adding payment types"). It differs from a technical-debt story because it must be done soon to support a characteristic the business needs. Create one per step.

Fitness functions below are automated checks run in CI/CD on each build or deployment. They are what keeps the structure from regressing while the migration is in flight.

---

## Pattern 1: Identify and Size Components

Use when: starting any component-based migration. Do not use when: the code has no namespaces or directories to speak of (use tactical forking instead, see `is-it-decomposable.md`).

Purpose: catalogue every component and size it. Services are built from components, so a component that is too large (too much, more coupled, harder to split) or too small must be seen first.

Size metric: number of statements, summed over all files in the component's directory. A statement is one complete action ended by a terminator (a semicolon in Java, C, C++, C#, Go, JS; a newline in F#, Python, Ruby). Lines, files and classes are style-dependent. Tools usually count per file, so aggregate yourself.

Guideline: component sizes should fall within one to two standard deviations of the mean, and the share of code per component should be fairly even.

Steps:

1. Walk the source tree and list each leaf directory as a component.
2. Rename vaguely named ones (a name like "Ticket Manager" says nothing). Use one consistent dotted-namespace style.
3. Record the inventory: name, namespace, percent of total, statements, files. Files count means little by itself but hints at structure (18,409 statements in 2 files means it needs contextual classes).
4. Flag outliers by percent and by deviation. A "simple" feature with a very large count (a wishlist at 12,000 statements) signals hidden complexity.
5. Split an oversized component by functional decomposition or domain-driven analysis into sub-domains. If no clear sub-domains exist, leave it alone.

Fitness functions:

1. Maintain the inventory: read last known component list from a datastore, rebuild from the tree, diff; on add/remove update the store and alert the architect. This keeps every later pattern current.
2. No component above X percent of the codebase. Threshold depends on size: about 30% for a 10-component app, about 10% for a 50-component app (the book's pseudo-code uses 10%). The goal is to flag significant outliers.
3. No component more than N standard deviations from the mean size. Mean = total / count; sample standard deviation = sqrt(sum of squared differences / (n - 1)); alert if |size - mean| / sd > N (the book's example uses 3).

Sysops Squad: 82,931 statements across 18 components. Reporting held 27,765 (33%, 162 files). It contained three report categories (ticket, expert, financial) plus shared code (utilities, calculators, shared queries, distribution, formatters). Split into four components: Reporting Shared (5,309; 7%), Ticket Reports (6,955; 8%), Expert Reports (7,734; 9%), Financial Reports (7,767; 9%). The root `ss.reporting` became a sub-domain, not a component. Re-measured sizes were balanced. (Recomputed: 5,309 / 82,931 is 6.4%, 6,955 is 8.4%, 7,734 is 9.3%, 7,767 is 9.4%; the book's rounded 7/8/9/9 differ slightly for the first. The four parts sum to the original 27,765.)

Verify: the inventory exists in a file or datastore under version control; the size-outlier checks run in CI and currently pass (or have named, justified exceptions); a split component was re-measured after the split.

Costs: statement counting is imperfect. It says how much a component does, not how hard it is. Use it to find questions, not to answer them.

---

## Pattern 2: Gather Common Domain Components

Use when: the inventory shows several components doing nearly the same domain job (notification, formatting, validation, auditing). Do not use for infrastructure functionality (logging, metrics, security), which is operational and handled differently (see `reuse-patterns.md`, sidecar).

Purpose: consolidate duplicated domain logic into one component so the distributed result has fewer duplicate services. Small differences between the copies can usually be reconciled in one component. The consolidated component later becomes a shared library or a shared service (trade-offs in `reuse-patterns.md`).

Finding candidates is mostly manual. Hints:

- A class used across components, or common inheritance. Example: an `SMTPConnection` class used by five classes in different namespaces means email notification is scattered.
- Similar names, such as `ticket.audit`, `billing.audit`, `survey.audit`, all inserting an audit row. Consolidate into `ss.shared.audit`.

Critical check before consolidating: afferent coupling. Consolidation raises the single component's Ca. Compare the total Ca before and after. If the total is unchanged, overall incoming coupling did not worsen. If the new component would become a dependency of too many things, treat it as a risk.

Steps:

1. List suspected duplicates (by shared leaf names, shared classes, similar behaviour).
2. For each group, sum the Ca of the members and compare with the Ca the merged component would have.
3. Reconcile behaviour differences; merge; update callers.
4. Remove the old components from the inventory.

Fitness functions (aids to manual judgement; both read exclusion lists so you can suppress false positives):

1. Same final node name in two component namespaces (such as `.notify`, `.audit`) and not in the exclusion list (generic names like `.calculate` or `.validate`): alert.
2. Same source file name appearing in more than one component and not excluded: alert.

Sysops Squad: Customer Notification, Ticket Notify and Survey Notify all send information to a customer with very similar code. Ca before: 2 + 2 + 1 = 5. After merging into `ss.notification`: Ca = 5 (same five callers). High incoming coupling on one component but no increase overall, so consolidate.

Verify: total Ca before equals total Ca after (or the increase is argued); no duplicate leaf names remain unexplained.

---

## Pattern 3: Flatten Components

Use when: any component sits above another in the namespace tree, or classes live in non-leaf directories. Purpose: make every component unambiguously a candidate service building block. If `ss.survey` and `ss.survey.templates` both hold code, it is unclear whether they are one service or two.

Definitions:

- Component: classes grouped in a leaf-node namespace performing specific functionality.
- Root namespace (also called a sub-domain): a node extended by another node. It is not a component.
- Orphaned classes: classes sitting in a root namespace, belonging to no defined component.

Two ways to flatten (choose by complexity, volatility and cohesion of the code):

- Move the leaf's code up into the root, so the root becomes a single component.
- Break the orphans out into new leaf components by functional decomposition or domain analysis; the root becomes a sub-domain.

Shared code sitting in a root (interfaces, abstract classes, utilities) is also orphaned. Move it into its own leaf, for example `ss.survey.shared`. Name shared components with a company-unique word (`.sharedcode`, `.commoncode`) so you can compute two metrics:

- Percent of statements in shared components. If about 45% of the code is shared, the distributed result will have too many shared libraries (a maintenance problem) and feasibility is poor.
- Number of shared components, which is roughly the number of shared libraries or services you will end up with.

Fitness function: no source code in a root namespace. For every component path, if any non-final node contains code, alert.

The decision of where to consolidate or break up is subjective; only the governance (no orphans) is automatable.

Sysops Squad: `ss.ticket` had 45 orphaned classes beside `ss.ticket.assign` and `ss.ticket.route`. Assignment is complex and changes often, so Assign and Route stayed separate and the 45 orphans were broken into Ticket Shared, Ticket Maintenance and Ticket Completion (completes the ticket and starts the survey). `ss.survey` (5 classes) and `ss.survey.templates` (7 classes): survey rarely changes and the template split had no reason, so the seven classes moved up into `ss.survey`, one component.

Verify: the orphan fitness function passes; the shared-code percentage is computed and reported; no "hills" (component on component) remain.

---

## Pattern 4: Determine Component Dependencies

Use when: after flattening, before committing to the migration. Purpose: predict the service dependency graph and answer three questions up front: is breaking the monolith apart feasible, what is the rough effort, and is it a rewrite or a refactor.

A component dependency exists when a class in one component calls a class in another. Only inter-component dependencies matter here; mess inside a component is irrelevant to this question.

Metrics per component: CA (incoming), CE (outgoing), CT = CA + CE (total coupling).

How to read the dependency diagram:

| Diagram look | Feasible? | Effort | Rewrite or refactor |
|---|---|---|---|
| Few dependencies between components | Yes | Golf ball: straightforward | Refactor: move existing code into separately deployed services |
| Typical business app: many dependencies but some regions easy | Maybe | Basketball: much harder | Mix of refactor and rewrite |
| Dense spaghetti of dependencies | No | Airliner | Total rewrite ("run the other way") |

Component coupling is one of the biggest feasibility factors; teams that go straight to microservices without this analysis struggle. The diagram is also a radar for where the coupling lives and a first draft of the service dependency matrix.

Refactoring opportunity: a component's CA may be driven by a few callers that need little of it. If component A has CA = 20 and 14 callers use only a small part, split it into A1 (the small part, CA = 14) and A2 (the bulk, CA = 6).

Filter before judging: class-level references to shared entities, interfaces and helpers will become shared libraries, not services. Remove those edges from the picture and look at what is left. In the case study the remaining dependencies were minimal, so the components were largely self-contained.

Fitness functions:

1. No component with more than N total dependencies (CA + CE; variants for incoming-only and outgoing-only). Choose N from the application's overall coupling. The book's example alerts above 15 as relatively high. An alert triggers a conversation or a split.
2. A forbidden-dependency test per restriction ("component X must not depend on component Y"). ArchUnit form from the book: `noClasses().that().resideInAPackage("..ss.ticket.maintenance..").should().accessClassesThat().resideInAPackage("..ss.expert.profile..")`.

Verify: the diagram is at component level, generated from the code (not hand drawn); CA/CE/CT are tabulated; the verdict (golf, basketball, airliner) is stated with the reason; shared-library edges were filtered openly, not silently.

---

## Pattern 5: Create Component Domains

Use when: components are flat, deduplicated and understood. Purpose: group components into logical domains so coarse domain services can be formed. A service usually corresponds to many components.

Domains are expressed in the namespace hierarchy: `ss.customer.billing.payment.MonthlyBilling` means domain `customer`, sub-domain `billing`, component `payment`, class `MonthlyBilling`.

Older monoliths predate domain-driven design, so you often need to add a domain node (`ss.billing.payment` becomes `ss.customer.billing.payment`). Move code, rename namespaces, and keep the move mechanical so tests keep passing.

Validation step: draw the groups. Every component must fit and each group must be cohesive. Leftovers or poor fits mean you need more input from the business side (product owner or sponsor). This is not a purely technical call.

Fitness function: all namespaces under the root must belong to the approved domain list, so teams cannot create domains by accident. ArchUnit form: `classes().should().resideInAPackage("..ss.ticket..").orShould().resideInAPackage("..ss.customer..").orShould().resideInAPackage("..ss.admin..")`.

Sysops Squad (with the product owner): five domains. Ticket (ticket processing plus surveys plus knowledge base), Reporting (already aligned), Customer (profile, billing, support contract), Admin (users and experts maintenance), Shared (login and notification). Notable moves: KB Maint and KB Search under `ss.ticket.kb.*`; Survey to `ss.ticket.survey`; Billing and Support Contract under `ss.customer.*`; Login and Notification under `ss.shared.*`; Expert Profile renamed to `ss.admin.experts` to avoid a needless Expert sub-domain.

Verify: every component lives under exactly one approved domain; the domain list is enforced in CI; a stakeholder who knows the business has signed off the grouping.

---

## Pattern 6: Create Domain Services

Use when: all component domains are identified and refactored. Purpose: physically extract each domain into a separately deployed domain service. The result is a service-based architecture: the UI calls coarse domain services over a single shared database. Variants (split UI, split database, API gateway) exist; the basic form is the start.

Ordering rule: do not start extracting services until all component domains have been identified and refactored. Otherwise already built services need rework when components shift (example from the case: Survey moved into the Ticket domain after a Ticket service existed).

Why stop here first: the team learns each domain before deciding whether any needs to become microservices. Starting finer inherits data decomposition, distributed workflows and transactions, and operational automation before they are needed.

Extraction means a new project workspace and deployable per domain, with the UI now calling the functionality remotely. Stage it domain by domain, one component at a time.

Fitness function: all components in a given domain service start with the same namespace prefix, one rule per service (`classes().should().resideInAPackage("..ss.ticket..")`). It stops services from decaying into unstructured monoliths, which matters if they will later be split again.

Sysops Squad result: five separately deployed services (Ticket, Customer, Reporting, Admin, Shared) over one database. Next steps are data (`decomposing-data.md`) and then deciding whether any service should be finer (`service-granularity.md`).

Verify: each service builds and deploys alone; the prefix rule passes; no service imports another service's internal packages (only calls its remote interface); the shared database is still shared, and that is stated as the next work item.

---

## Fitness-function inventory (install by the end)

| Function | Governs | Pattern |
|---|---|---|
| Component inventory diff | Awareness of structure | 1 |
| Max percent of codebase per component | Component size | 1 |
| Max standard deviations from mean size | Component size | 1 |
| Common leaf names across components | Hidden duplication | 2 |
| Common source file names across components | Hidden duplication | 2 |
| No code in root namespaces | Flatness | 3 |
| Max total dependencies per component | Coupling | 4 |
| Forbidden component dependencies | Specific boundaries | 4 |
| Allowed domain list | Domain structure | 5 |
| Per-service namespace prefix | Service integrity | 6 |

General fitness-function theory and the ADR format belong to `arch-decisions-and-tradeoffs`.

## Implementation sketches (adaptation)

The book's examples use Java and ArchUnit. Equivalents: `dependency-cruiser` rules or ArchUnitTS in TypeScript, `import-linter` contracts in Python, a test using `go list` output in Go. Check the tool exists in the repository before assuming it.

Component size and orphan check for a Python tree (standard library only; counts `ast` statements per leaf directory; checked on a toy tree):

```python
import ast, pathlib, statistics, sys
def statements(p):
    try: return sum(isinstance(n, ast.stmt) for n in ast.walk(ast.parse(p.read_text())))
    except SyntaxError: return 0
root = pathlib.Path(sys.argv[1]); sizes = {}
for f in root.rglob("*.py"):
    comp = f.parent.relative_to(root); sizes[comp] = sizes.get(comp, 0) + statements(f)
total, mean = sum(sizes.values()), sum(sizes.values()) / len(sizes)
sd = statistics.stdev(sizes.values()) if len(sizes) > 1 else 0
for c, n in sorted(sizes.items(), key=lambda kv: -kv[1]):
    print(c, n, f"{100*n/total:.1f}%", f"z={(n-mean)/sd:+.1f}" if sd else "")
for d in sizes:                        # code in a directory that also has code below it
    if any(o != d and d in o.parents for o in sizes): print("ORPHANS in non-leaf:", d)
```

For other languages, `lizard` reports per-file counts that you can aggregate by directory, though it counts lines of code rather than statements; say so when you report, since the book prefers statements.

## Verify (whole sequence)

- Each pattern's output artifact exists (table, diagram, domain list), is generated from code where possible, and is stored with the repo.
- The listed fitness functions run in CI; at least one deliberately broken change (a new class in a root namespace, a forbidden import) makes the build fail. A check that has never failed has not been shown to work.
- Test results are unchanged by pure restructuring steps (patterns 1, 2, 3 and 5 should not change behaviour).
