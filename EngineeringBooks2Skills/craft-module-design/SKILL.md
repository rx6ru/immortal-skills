---
name: craft-module-design
description: Provides decision rules and review checks for designing modules, classes, interfaces and layers so complexity stays low, covering deep modules, information hiding, layering, split-or-merge, coupling, DRY, Law of Demeter, configuration, objects versus data, cohesion, third-party boundaries, dependency injection, performance-aware design. Use when asked to design a class, module or internal API; decide where code should live or whether to split or merge; review a design or PR for structure; untangle a god class, a wrapper layer that only forwards, leaky abstractions, getter chains, config sprawl or duplicated knowledge; wrap a library or SDK; wire dependencies; or when a small change touches many files. Naming and comments belong to craft-clean-code, GoF pattern choice to craft-design-patterns, restructuring mechanics to craft-refactoring, service-level structure to the arch skills.
---

# craft-module-design

## Purpose

Use this skill to decide the shape of code before and while you write it: which module owns which
knowledge, what each interface exposes, where layers sit, and what depends on what. It replaces "make
it work, then stop" with a small, bounded design step whose single criterion is whether the system
becomes easier or harder to understand and change. It also gives you observable tests, so a design
claim ("this is decoupled", "this hides the format") can be shown instead of asserted.

The governing rule: complexity is anything in the structure of the code that makes it hard to
understand and modify. Every named principle below is a means to reduce it. When a principle and that
test disagree in a concrete case, the test wins (APOSD preface).

## Choose what applies

| Situation | Use | Reference |
|---|---|---|
| Asked to design a new class, module, package or internal API | Procedure A, then design-it-twice for the interface | `design-it-twice.md`, `deep-modules-and-information-hiding.md` |
| Reviewing a design or PR for structure; "is this well designed?" | Procedure B (red-flag pass) | `complexity-and-red-flags.md` |
| "Should this be one function/class/file or several?" "This class is too big" | Procedure C | `together-or-apart.md`, `objects-data-and-classes.md` |
| A layer or wrapper mostly forwards calls; a parameter is threaded through many functions; considering a decorator | Layer rules | `layers-and-abstraction.md` |
| A small change needs edits in many files; a fix breaks something distant; the same rule is written in several places | Coupling rules, change-impact test | `coupling-orthogonality-dry.md` |
| Long chains like `a.b().c().d()`; code asks an object for parts and decides for it | Law of Demeter, tell-don't-ask | `coupling-orthogonality-dry.md`, `objects-data-and-classes.md` |
| Adding a config option, flag or parameter; deciding code versus configuration | Knob rule (below) | `deep-modules-and-information-hiding.md`, `coupling-orthogonality-dry.md` |
| Adding a new variant or a new operation to a family of types; class hierarchy versus tagged union | Axis-of-change table | `objects-data-and-classes.md` |
| Getters/setters, DTOs, ORM entities with business rules, inheritance versus composition | Object/data rules | `objects-data-and-classes.md` |
| Integrating a library, SDK, vendor service or another team's API; the dependency is not ready yet | Boundary procedure | `boundaries-and-construction.md` |
| Business code calls `new` on concrete services, uses lazy-init singletons, or cannot be tested without a server | Construction/use separation | `boundaries-and-construction.md` |
| Modifying existing code to add a feature or fix a bug | Procedure D | `complexity-and-red-flags.md` |
| Something must be fast, or is too slow | Performance procedure | `performance-design.md` |

This skill does not apply, or applies only lightly, when:

- The task is a one-line fix, a rename, or a throwaway script or prototype. Do not turn it into a
  redesign; at most note a red flag you saw.
- The question is about names, comments, formatting or function-level readability: use
  `craft-clean-code`. Three red flags (vague name, hard to pick a name, hard to describe) are still
  useful here as signals that a module boundary is wrong.
- The question is how to treat a specific error (throw, return, mask, crash): use
  `craft-error-handling`. Here, only remember that every exception and special return value is part
  of the interface and makes the module shallower.
- You need the mechanics of a restructuring in safe steps: use `craft-refactoring`. Choosing which
  GoF pattern fits: `craft-design-patterns`. Services, data stores, deployment topology: start at
  `arch-router`.
- The code is in an area nobody touches. Complexity is weighted by how often people work there;
  ugly code in a dead corner is low priority.

## How to apply

### The three questions (use everywhere)

Ask these of any design or change, once per plausible future modification (one question per
symptom named in APOSD ch. 2; the phrasing as questions is derived in the notes):

1. How many places must change? (change amplification)
2. What must someone know to make the change safely, and can they find it from where they stand?
   (cognitive load)
3. Is there anything they must know that nothing would lead them to? (unknown unknowns; weigh this
   one highest, because it is discovered only through bugs)

The two causes behind bad answers are dependencies (code that cannot be understood or changed alone)
and obscurity (important information that is not obvious). You cannot remove all dependencies; make
the remaining ones few, explicit and tool-checkable (a named constant, a type, an API) instead of
an unwritten agreement between two places.

### Procedure A: design a new module or interface

1. List the knowledge involved: formats, protocols, algorithms, data layouts, policies, vendor
   details, assumptions. Each item is a design decision.
2. Assign each decision to exactly one module. Group by knowledge, not by the order things happen at
   run time; "read, then parse, then write" as three classes usually puts one format in three places.
3. Write the interface from the caller's side first. Sketch the calling code for the two or three
   main uses. Make the common case one obvious call with defaults; put rare needs behind separate
   methods or options so the common caller never reads about them.
4. Make the interface somewhat general-purpose: shape it around the underlying capability (text with
   positions, a keyed store, a queue), not around the first caller's feature. Implement only the
   functionality needed now. Check both directions: no method named after a caller's feature, and no
   caller forced into loops or glue to do an ordinary thing.
5. Pull complexity down: if a hard case relates to this module's job, handle it inside instead of
   exporting an exception, a flag or a config parameter, because a module has more users than
   authors.
6. For a significant interface, produce a second, genuinely different design and compare (see
   `design-it-twice.md`). Record what you rejected and why.
7. Decide what the module depends on and how it receives it: pass collaborators in (constructor or
   parameter); construct concrete implementations in one wiring place.
8. Run the Verify section before calling it done.

### Procedure B: red-flag review pass

Read the code or design looking for these; each is a sign that it is probably more complicated than
it needs to be. When one appears, look for an alternative that removes it, try more than one, and
if you keep it, be able to say why it is acceptable here.

| Red flag | How to recognise it | First move |
|---|---|---|
| Shallow module | Interface not much simpler than the body; documentation would be longer than the code; caller must know what the body does anyway | Give it more to do behind the same interface, merge it, or inline it |
| Information leakage | One decision (format, protocol, schema, constant) known in more than one module, through an interface or by the back door | Move the knowledge to one owner; merge small tightly tied classes; or extract an owner whose interface stays abstract |
| Temporal decomposition | Modules named for phases (reader/parser/writer, step1/step2) that share knowledge | Regroup by knowledge behind a higher-level interface |
| Overexposure | Common use requires passing or learning about a rarely used feature | Defaults; move rare features to separate methods |
| Pass-through method | Body is one call with nearly the same signature | Expose the callee, redistribute responsibility, or merge the classes |
| Pass-through variable | A parameter threaded through functions that do not use it | Shared object or a small immutable context; not a global |
| Repetition | The same non-trivial code or the same fact appears repeatedly | Find the missing abstraction; or restructure so it runs once |
| Special-general mixture | A general mechanism contains code for one particular use | Move the specific part up into its user |
| Conjoined methods | One piece cannot be understood without reading the other | Rejoin, or re-cut where each side stands alone |
| Vague name / hard to pick a name / hard to describe | You cannot name or describe the thing briefly and precisely | The design is unclear; reconsider what the unit is responsible for |
| Non-obvious code | A reader cannot quickly guess behaviour and be right | Add information by design, convention or (per `craft-clean-code`) naming and comments |

Coupling signs from the other sources belong in the same pass: train-wreck call chains, globals and
singletons holding mutable state, objects that need `init()` after construction, a unit test that
must build half the system, vendor types in signatures across many modules, business classes that
construct their own collaborators, classes whose description needs "and".

### Procedure C: together or apart

Splitting is not free: it adds components and interfaces, glue code to manage them, distance between
related code, and sometimes duplication. Decide by relatedness, not by size.

1. Do the pieces share knowledge (a format, a data structure, a protocol)? Keep together, or extract
   one owner.
2. Would combining remove an intermediate hand-off or let something happen automatically? Together.
3. Is the same code repeated? Extract if the snippet is long and the signature simple; otherwise
   restructure the flow so it runs in one place.
4. Is one piece a general mechanism and the other specific to one user? Apart, with the specific
   part in the higher layer.
5. Does reading one require reading the other? Together.
6. Are they independent and each understandable alone? Apart is fine.
7. For a class, run the responsibility tests: can you name it without `Manager`/`Processor`/`Util`;
   describe it in about 25 words without "and"/"or"/"but"; list exactly one kind of change that
   would force an edit; do most methods use most fields? A failure means two responsibilities, so a
   split is likely to produce two units that each hide something.

On size, the sources disagree, and you should not pick silently. Clean Code (ch. 10) wants classes
small, measured in responsibilities, arguing that many small well-labelled classes have no more
moving parts than a few large ones and let a reader ignore what is not affected. APOSD (ch. 4, 9)
answers that every unit costs an interface, small units tend to be shallow, and length alone is
rarely a reason to split; a long method with a simple signature that does one thing completely is
fine. The rule that reconciles them: never split or merge to hit a size. Split when the pieces have
different reasons to change or different knowledge and each result is independently understandable;
merge when they share knowledge or must be read together. After any split, each new unit must pass
the "understand it from its interface alone" test; if it fails, the split was along the wrong line.

### Decision rules used most

**Expose or hide?** Hide what callers do not need; expose what some caller's correctness or tuning
depends on (a file system hides block allocation but must expose when data reaches stable storage).
An interface that omits something callers need is a false abstraction, which is worse than a wide
one. `private` plus a getter and setter per field hides nothing.

**Knob rule (parameter, flag, config option).** The sources pull apart: APOSD ch. 8 says avoid
configuration parameters because they push work up to every user; Pragmatic Programmer ch. 5 says
move details (policies, vendor choices, deployment settings) out of code into metadata. Decide by
who knows the right value. If the module can compute or measure it, do that and export nothing. If
it is a fact about the deployment or a business policy that changes independently of the code and
that someone outside genuinely owns, put it in configuration, with a default and validation at load.
A knob added because the author did not want to decide is a punt.

**Forwarding method: legitimate or pass-through?** Demeter-driven delegation (Pragmatic Programmer
ch. 5, Clean Code ch. 6) and the pass-through red flag (APOSD ch. 7) meet here. A forwarding method
earns its place when it changes the abstraction: the caller states what it wants (`account.name()`,
`ctx.createScratchFile(name)`) and the object hides where that comes from. It does not when the
wrapper mirrors the lower API method for method. If obeying Demeter produces `getXOfYOfZ` methods,
ask what the caller was trying to do and move that behaviour, instead of exporting the structure
one hop at a time. Chains over plain data structures and fluent builders are not violations.

**Decorator or wrapper?** Before adding one, in order: add the feature to the underlying class if it
is general or wanted by most users; merge it into the single use case that needs it; merge it into
an existing decorator; ask whether it needs to wrap at all. Wrapping is the right tool for genuinely
cross-cutting behaviour (transactions, auth, logging, caching) that would otherwise be pasted into
many business methods (Clean Code ch. 11), and for multiple implementations of one interface.

**New variants or new operations?** Polymorphic objects make new types cheap and new operations
expensive; plain data with functions (or sum types with exhaustive matching) do the opposite. Look at
which axis the existing code is built on before adding a case, and choose the form whose cheap axis
is the likely change. Avoid hybrids that are half object and half data structure.

**Interface in front of a dependency?** Put one there, named for the concept and injected, when the
dependency is volatile, external, slow or non-deterministic, or when you want to forbid part of what
it can do. Do not for stable standard-library types used locally. One interface with many
implementations is deep; an interface that only mirrors one class adds a layer with the same
abstraction.

**How general?** "Somewhat": the interface should not encode today's caller, but build no speculative
functionality. Restructuring a stable class for extensibility is worth doing when a change actually
forces you to open it, not before (Clean Code ch. 10).

### Procedure D: modifying existing code

1. Read the interface and design of the module you are about to touch.
2. Ask whether you would have designed it this way with the new requirement known from the start. If
   not, restructure first or as part of the change, so the result looks designed-in.
3. If that restructuring is too large for the task, find the nearly-as-clean smaller variant, and
   tell the user what you deferred. Do not silently patch around a design problem, and do not
   silently launch a large refactor the user did not ask for.
4. Make the minimal clean change, which is not always the minimal diff. Count the special cases,
   flags and extra parameters your change adds; each one is a prompt to look again.
5. Keep rationale in the code next to what it explains, not only in the commit message.

### Performance in design

Choose naturally efficient structures when they cost no extra complexity (hash lookup over ordered
map when order is not needed, contiguous storage over many small allocations, no network or disk
call inside a tight loop). Take on complexity for speed only with evidence that this path matters,
and keep it inside the module. When something is slow: measure with a baseline, look for a
fundamental fix (cache, algorithm, batching), and only then redesign around the critical path. Back
out changes that do not measurably help unless they also simplified the code. Details in
`performance-design.md`.

## Verify

Run the checks that match what you did, and report the evidence, not just the conclusion.

Change-impact and hiding
- Change-impact test: name two or three plausible changes (new format version, different storage,
  new variant, new policy value). For each, list the files that would change. Target: one module per
  decision. Show the list.
- Knowledge grep: search for the format constants, field names, magic values or parsing code of a
  decision (`rg` on the literal or symbol). Hits in more than one module are leakage.
- Representation-swap test: could the internal structure change (map to list, text to binary, SQL to
  in-memory) with no edit to callers or to tests outside the module? Where cheap, prove it by
  writing a second trivial implementation and running the same tests against both.
- Interface-only test: write the main calling snippet (or test) from the signatures and doc
  comments alone, without opening the body. If you had to open it, note what was missing: the
  interface is under-specified or the abstraction is false.

Depth and layers
- Count public methods, parameters, required call orders and special cases a caller must handle,
  before and after. A redesign should reduce these without reducing functionality.
- Common-case check: the main use is one call with defaults; any argument nearly every caller sets
  to the same value is a missing default.
- Forwarding ratio: list public methods whose body is a single call with the same parameters. More
  than a few in one class means the layer is not adding an abstraction.
- Layer sentence: state in one sentence how each layer's abstraction differs from the one below.
- Parameter trace: every parameter is used by the function that receives it, not only forwarded.

Split and merge
- For every extracted function or class: a reader understands it from signature and description
  alone, and the parent reads naturally knowing only that. Single-use helpers with long parameter
  lists that pass state around are suspect.
- For a class: field-usage matrix (which methods touch which fields); a field subset used by a
  method subset is another class trying to get out. 25-word description without "and".

Coupling
- Dependency direction: imports of a vendor package appear only in its adapter
  (`rg -l '\b(import|from|require)\b.*vendorpkg' src --glob '!src/adapters/**'` prints nothing;
  adapt the package and path, see `boundaries-and-construction.md`); domain modules import no framework,
  transport or persistence types; no import cycles (use the ecosystem's dependency-graph or import-lint tool, e.g. `madge`
  or `import-linter`; tool names are adaptations, not from the books).
- Unit-test probe: the module can be tested by constructing it with fakes for its direct
  collaborators, with no network, clock, database or container. Needing to build a deep object graph
  is the measurement of its coupling.
- Chain scan: search for call chains crossing two or more object types (first pass:
  `rg '\)\.\w+\([^()]*\)\.\w+\('`, which finds three or more chained calls on one line); for each,
  either the middle objects are plain data, fluent or stream steps, or the behaviour should move.
- Construction scan: search business code for `new ConcreteService(`, `if (x == null) x = new`, and
  service-locator or singleton lookups; concrete implementation names should appear only in the
  wiring code.
- Single source: for a duplicated fact you removed, the derived artefacts are generated or computed
  from one source by the build, not hand-edited.

Performance
- Before/after benchmark on the same workload, with numbers. For a critical path: count
  conditionals, calls and allocations on it.

Done means:
- Each design decision has one owning module, and you can show it with a search or a file list.
- The main use case of each new interface is one obvious call; nothing rare is mandatory.
- No red flag from Procedure B is left unexplained in code you wrote or changed.
- New code can be unit-tested with fakes for its direct collaborators only, and such a test exists.
- For any significant interface, the rejected alternative and the reason are written down (design
  note, PR description or a comment near the interface).
- Contested calls (size, knobs, wrappers, generality) were decided by the rules above and you can
  state which consideration decided it.
- The change did not grow beyond what the user asked; deferred design problems are reported.

## Proportion and limits

- Budget: design effort of roughly 10 to 20 percent of the work, spread as small continual
  investments. That figure is the author's judgement with no measurement behind it; treat it as a
  sense of scale. A whole-system up-front design is rejected as firmly as no design.
- Apply design-it-twice to significant decisions (a module boundary, a public interface, a data
  model), not to every function.
- Each mechanism here has a cost: an interface plus adapter adds indirection; Demeter adds
  forwarding methods; DI containers add runtime wiring failures (plain constructor passing is
  enough for small systems); metadata-driven designs can turn into an untested private programming
  language; reversibility layers cost abstraction for options that may never be used. Spend them
  where the decision is uncertain and expensive to change.
- Every principle has a stated limit: hiding something callers need creates a false abstraction;
  pulling everything down ends in one giant class; generalising past the present need makes the
  interface hard to use; merging until one class remains is as wrong as classitis.
- Dated material: the Java I/O, EJB, CORBA, RMI and C-header examples and the 2018 latency numbers
  are illustrations only; the reasoning carries over, the specifics do not.
- Contested positions you may meet: APOSD is sceptical of test-driven development as a design method
  (features-first increments instead of abstraction-sized ones) while valuing unit tests highly
  because they make restructuring safe; see `craft-testing` for the other views. Getters and setters
  are required by some frameworks and cheap in languages with properties and records; the question
  that matters is whether representation leaks, not whether accessor syntax exists.
- Follow the codebase's established conventions when they conflict with a preference from this
  skill and the difference is not causing one of the three symptoms.

## References

- `references/complexity-and-red-flags.md`: read when reviewing a design, explaining why something
  is complex, prioritising clean-up, or modifying existing code; full red-flag catalogue and the
  fifteen principles.
- `references/deep-modules-and-information-hiding.md`: read when designing or judging an interface;
  depth, leakage, defaults, general-purpose interfaces, pulling complexity down, configuration
  parameters.
- `references/layers-and-abstraction.md`: read when a layer forwards, when threading data through a
  call stack, when considering a decorator or middleware, or when placing cross-cutting concerns.
- `references/together-or-apart.md`: read for any split-or-merge decision on functions, classes or
  modules, including the size disagreement and worked cases.
- `references/coupling-orthogonality-dry.md`: read when changes ripple, knowledge is duplicated,
  call chains are long, or you are deciding between code, configuration, events and a shared board.
- `references/objects-data-and-classes.md`: read for object versus data structure, new type versus
  new operation, accessors, DTOs and active records, cohesion and single responsibility, open-closed
  restructuring, inheritance versus composition.
- `references/boundaries-and-construction.md`: read when integrating third-party code, defining an
  interface for something that does not exist yet, or separating wiring from use.
- `references/design-it-twice.md`: read before committing to a significant interface or
  decomposition; procedure, comparison criteria, note template, worked example.
- `references/performance-design.md`: read when performance is a requirement or a complaint.

## Sources

- A Philosophy of Software Design (1st ed.): preface and ch. 1-9, 11 (complexity, strategic work,
  deep modules, information hiding, general-purpose modules, layers, pulling complexity down,
  together or apart, design it twice); ch. 10 only as it bears on interfaces; ch. 16 (modifying
  existing code); ch. 19 (inheritance, agile, tests, patterns, accessors); ch. 20 (performance);
  ch. 21 and the summaries of principles and red flags.
- The Pragmatic Programmer (1st ed.): ch. 2 (DRY, orthogonality, reversibility, domain languages);
  ch. 5 (decoupling and the Law of Demeter, metaprogramming, temporal coupling, views and events,
  blackboards); appendix B (answers to the related exercises).
- Clean Code (1st ed.): ch. 6 (objects and data structures), ch. 8 (boundaries), ch. 10 (classes),
  ch. 11 (systems).
