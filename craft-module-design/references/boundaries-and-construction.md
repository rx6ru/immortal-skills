# Boundaries and construction

How to integrate code you do not control, and how to keep the building and wiring of objects apart
from the code that uses them.

Contents
1. Why boundaries need design
2. Wrapping a broad third-party interface
3. Learning tests and boundary tests
4. Writing the interface you wish you had
5. Procedure: adopting a library, SDK or service client
6. Separating construction from use
7. Mechanisms: main, factories, dependency injection
8. Keeping the domain free of frameworks
9. Growing a system; deferring decisions; standards
10. When not to
11. Verification

## 1. Why boundaries need design (Clean Code ch. 8)

You rarely control all the code in a system: libraries, open-source packages, other teams'
components. Providers want their interface broad, to serve many users; you want it narrow, fitted to
your need. Boundaries are where change arrives from outside. The working rule: depend on something
you control instead of something you do not, and keep the number of places that refer to
third-party code very small.

The Pragmatic Programmer reaches the same practice from reversibility (ch. 2): hide third-party
products behind a well-defined abstract interface so a vendor can be replaced, and from
orthogonality: a library that forces special handling throughout your code has leaked into it.

## 2. Wrapping a broad third-party interface

A general container or client offers far more than a given use needs. If your design says "nobody
deletes entries" or "only sensors go in here", the raw type cannot enforce that. Passing it around
spreads conversions and assumptions to every call site, and when the provider's interface changes,
every one of those sites changes.

Hide it in a class with an interface tailored to the application. The type and its quirks become an
implementation detail, the class can enforce the domain's rules, and misuse gets harder.

```python
# raw container passed around: anyone can clear it or put the wrong thing in
def reading(sensors: dict, sensor_id): return sensors[sensor_id].value

# narrow, domain-shaped
class Sensors:
    def __init__(self): self._by_id = {}
    def register(self, sensor): self._by_id[sensor.id] = sensor
    def get(self, sensor_id): return self._by_id[sensor_id]
```

The chapter is explicit that this is not "wrap every map". The advice is not to pass a boundary
interface around the system: keep it inside the class or small family of classes that use it, and
avoid accepting it in or returning it from public interfaces.

Where may vendor types appear? Only in the adapter or wrapper. Everything else uses your types.

## 3. Learning tests and boundary tests

Learning a third-party interface and integrating it at the same time is doubly hard: when something
fails you cannot tell whose defect it is. Instead write small tests that call the library the way
your application will. These are controlled experiments about what you want from it.

- The chapter's walk-through with a logging library goes guess, run, error, adjust, and ends with a
  handful of tests recording what works, including the surprises (an argument whose removal changes
  behaviour, a default constructor that leaves the object unconfigured). That knowledge is then
  encapsulated in the application's own logger class.
- They cost nothing extra, since you had to learn the interface anyway.
- Kept in the suite, they become boundary tests: run them against each new release of the
  dependency to detect behavioural changes. That makes upgrades less frightening, so you are not
  tempted to stay on an old version.
- A clean boundary should be supported by tests that exercise the interface the way production
  code does.

Adaptation (from the notes' caveats): learning tests are uncommon in practice. Related techniques
are interactive exploration, contract tests, conformance tests, recorded-response tests and version
pinning; for network services, consumer-driven contract tests (see `craft-testing` and
`arch-api-design`). Tests that hit real services can be slow or flaky, so separate them from the
fast suite.

## 4. Writing the interface you wish you had

When the other side is unknown or not yet designed, do not wait. Define your own interface for what
your code needs, in your terms. The chapter's example is a transmitter subsystem with no interface
yet; the team defined "transmit this stream on this frequency" and wrote their controller against
it.

- Client code stays readable and focused, and the interface is under your control.
- When the real interface arrives, write an adapter from yours to theirs. It is the single place to
  change as theirs evolves.
- The interface is a seam for testing: a fake implementation lets you test the client code now, and
  boundary tests check your use of the real thing later.

Caution (marked inferred in the notes): the wished-for interface can drift from reality. If the
real dependency has latency, partial failure or ordering semantics your interface hides, the
adapter will leak or the interface will be a false abstraction. Design it around the failure modes
you already know exist.

## 5. Procedure: adopting a library, SDK or service client

The chapter gives steps 1 to 3 and the boundary-test part of step 6; steps 4, 5, 7 and the
integration-test advice are adaptation consistent with its caveats.

1. Decide the narrow interface your code wants, named in domain terms.
2. Write learning tests to find out how the library provides it; record surprises as tests.
3. Implement an adapter behind your interface. Vendor imports stay inside it.
4. Translate vendor errors and data types at the adapter into yours.
5. Provide a fake of your interface for unit tests of the callers.
6. Keep the learning tests as boundary tests, and keep a small number of integration tests of the
   adapter against the real dependency; mocking the wrapper proves nothing about the adapter.
7. Sanity check: how much would change if this vendor were swapped? The answer should be the
   adapter and its tests.

Warning signs that this was skipped: vendor or library types (HTTP clients, ORM entities, SDK
request objects, raw maps or parsed JSON) in signatures across many modules; the same cast or
unwrapping at many call sites; an upgrade estimated as a multi-module effort; tests that mock deep
inside a vendor SDK; no tests pinning vendor behaviour the code relies on; debugging sessions where
you cannot tell whose bug it is; work blocked waiting on another team's interface.

## 6. Separating construction from use (Clean Code ch. 11)

Start-up (building objects and wiring them together) is a different concern from run-time logic.
Most applications mix them.

The typical symptom is lazy initialisation in run-time code: a getter that checks whether a
collaborator is null and, if so, constructs a concrete implementation. Its merits are real: no
construction cost until needed, and never a null. Its costs:

1. A hard-coded dependency on the concrete class and on everything its constructor needs.
2. Harder testing: a double must be put in place before the first call, and the method does two
   things, so both branches need tests.
3. The class cannot know the concrete choice is right in every context. Why should it know the
   global context at all?
4. One instance is harmless; dozens scatter the set-up strategy across the application with
   duplication.

Rule: do not let small convenient idioms break modularity. Have one consistent strategy for
resolving major dependencies.

## 7. Mechanisms: main, factories, dependency injection

In rising power:

1. Separation of main. All construction happens in `main` or modules it calls. The rest of the
   application assumes everything is built and wired. Dependencies cross the line in one direction
   only, away from main; the application does not know main exists.
2. Factories. When the application must decide when to create something (an order process creating
   line items), it calls a factory interface; the implementation lives on the main side. The
   application controls timing and can pass its own arguments, but not the construction details.
3. Dependency injection. An object does not instantiate or look up its dependencies. It is passive:
   it declares them as constructor arguments or setters, and an authoritative mechanism (main or a
   container) supplies them. A lookup by name through a registry is only partial injection,
   because the object still actively resolves the dependency.

Lazy creation is still available: a wiring mechanism can build on demand or hand out a factory or
proxy. The chapter's footnote calls lazy instantiation an optimisation, and perhaps a premature one.

Adaptation (stated in the notes as a generalisation): a composition root plus constructor
parameters works in any language; a container is optional. Passing a collaborator as a function
argument is the minimal form.

```ts
// business code: declares what it needs
class Checkout {
  constructor(private prices: PriceSource, private clock: Clock) {}
}

// composition root: the only place that names concrete classes
const checkout = new Checkout(new HttpPriceSource(config.priceUrl), systemClock);
```

Related Pragmatic Programmer points: avoid global data and disguised-global singletons, and pass
context explicitly (ch. 2); prefer constructors that leave an object fully initialised over a
constructor followed by a required `init()` (ch. 5).

## 8. Keeping the domain free of frameworks

The chapter's negative example is an early enterprise component model, now obsolete: business logic
had to subclass container types and implement many mostly empty lifecycle methods, with separate
interfaces, factories and deployment descriptors. Consequences: tight coupling to a heavyweight
container; isolated unit tests were hard; reuse outside the container was effectively impossible;
and behaviourless transfer objects duplicated data across types.

What survives: if domain logic must inherit from or implement framework types, a framework change
is a domain change and tests need the framework. Keep domain objects plain. Add persistence,
transactions, security and similar concerns from outside by wrapping, declaration or configuration
(see cross-cutting concerns in `layers-and-abstraction.md`).

Annotations on domain entities still couple the domain to the library. The chapter accepts this as
far less harmful than the old model and notes the mapping can live in external configuration for
those who want a pure object.

## 9. Growing a system; deferring decisions; standards

- Getting a system right the first time is a myth. Implement today's needs, then restructure and
  extend. At system level that only works if concerns are separated, which is what makes radical
  change economically feasible for software.
- Big design up front resists change, because people are reluctant to discard prior effort and
  early choices bias later thinking. This is not an argument against all up-front thought: have
  expectations of scope, goals and general structure, and keep the ability to change course.
- Start simple but well decoupled; add infrastructure (caching, security and so on) when it is
  needed.
- Modularity lets decisions be made by whoever is best placed, and late, when more is known. The
  notes add (inferred) that this suits decisions that are cheap to defer; decisions that are costly
  to reverse deserve deliberate, earlier attention.
- Adopt a standard or framework only when you can state the concrete value it adds here. Standards
  bring reuse, shared knowledge and easier hiring; they can also be heavier than the problem needs.
- A good interface largely disappears from view. Use the simplest thing that can work.

## 10. When not to

- Wrapping everything is over-engineering. Stable, ubiquitous standard-library types used locally
  need no wrapper. Wrap where the dependency is volatile, vendor-specific, wide, or exposes
  behaviour you want to forbid.
- A dependency-injection container adds indirection and failures that surface only at run time.
  For small systems plain constructor passing is enough.
- An interface with a single implementation and no test fake, created "in case", is a layer with
  the same abstraction as the thing behind it (see `layers-and-abstraction.md`). Create it when the
  dependency is volatile, external, slow or non-deterministic.
- A script or a prototype does not need a composition root.
- Naming varies across sources (adapter, facade, wrapper, port); the substance is a single point of
  contact.

## 11. Verification

- Import scan (marked inferred in the notes): imports of the vendor package appear in few files,
  ideally only the adapter. Adaptation, tested on Python and JavaScript sample files:
  `rg -l '\b(import|from|require)\b.*vendor_sdk' src --glob '!src/adapters/**'` should print
  nothing (replace `vendor_sdk` and the adapter path with your own; it matches `from x import`,
  `import x`, ES `import ... from "x"` and `require("x")`, and can false-match longer names that
  contain the package name).
- Signature scan: no vendor types in public signatures outside the adapter.
- Boundary tests exist, run in CI or at least on dependency upgrades, and fail when relied-on
  vendor behaviour changes.
- Callers run against a fake that implements your interface.
- The wrapper rejects uses the domain forbids (no way to clear the collection, for instance).
- Swap exercise: mentally or in a short spike, replace the vendor; the change stays in the adapter
  and its tests.
- Construction scan (inferred): search business code for direct construction of concrete services
  and for null-check lazy initialisation; search for service-locator and singleton lookups.
- Composition root: one place names the concrete implementations.
- Testability: domain logic can be tested with no container, server or network. If it cannot, the
  coupling is the defect.
- Domain purity: domain modules import no persistence, transport or security framework types and
  extend no framework base classes.
- Cross-cutting scan: transaction, logging, auth or cache boilerplate is not copy-pasted across
  business methods.
