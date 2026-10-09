# Coupling, orthogonality and DRY

How to keep knowledge in one place, keep unrelated things from affecting each other, keep decisions
reversible, and choose a decoupling mechanism.

Contents
1. DRY: one representation per piece of knowledge
2. The four sources of duplication and their remedies
3. Orthogonality
4. Reversibility
5. Decoupling and the Law of Demeter
6. Metadata and configuration-driven design
7. Code or configuration: reconciling the sources
8. Domain languages
9. Temporal coupling
10. Events, views and models
11. Blackboards
12. Choosing a mechanism
13. Lessons from the exercises
14. Verification

## 1. DRY: one representation per piece of knowledge (Pragmatic Programmer ch. 2)

Every piece of knowledge should have a single, unambiguous, authoritative representation in a
system. The reason: knowledge changes constantly, and every duplicate representation must be found
and changed in step. Sooner or later one is missed, and the system then contains two contradictory
statements of the same fact.

The principle is about knowledge (rules, facts, structure, decisions), not about lines that look
alike. It applies beyond code: specifications, documentation, schemas, build files, tests.

Deciding whether two similar things are a DRY violation: are they the same knowledge, that is, will
they change for the same reason? The notes mark this test as inferred from the knowledge framing,
since the book does not discuss false positives. It is the working rule: code that merely looks
similar but encodes two independent decisions may be left separate, and merging it couples things
that will later diverge.

This is the same idea as information leakage in APOSD (one decision known in several modules), seen
from the side of the fact instead of the module.

## 2. The four sources of duplication and their remedies

| Source | What it is | Remedy |
|---|---|---|
| Imposed | The environment seems to demand it: several representations of the same information, documents that restate code, language structure | Derive one from the other with a generator or filter that runs every build; keep "how" in code and "why" in comments; accept language-forced duplication where the compiler checks it |
| Inadvertent | A design mistake: unnormalised data, fields derivable from others | Normalise to the real model; compute instead of storing |
| Impatient | Shortcuts under time pressure: copy and paste, a literal instead of the shared constant | Parameterise or extract now; the shortcut costs more later |
| Interdeveloper | Different people or teams implement the same thing | Clear division of responsibility; make finding and reusing easier than rewriting; a known place for shared utilities; read each other's code |

Details that matter in practice:

- Multiple representations (a structure shared by client and server in different languages, a class
  mirroring a database table). Generate each from one metadata source. The process must be active,
  run on every build; a one-time conversion is duplication again. Adaptation: interface description
  files, API specifications, schema definitions and ORM models are the same problem; generate one
  from the other or check them against each other in CI.
- Documentation and code. The notes' example generated an acceptance test suite from the client's
  specification, so specification changes regenerated the tests.
- Derived fields. A line with a start, an end and a stored length duplicates knowledge; make length
  a computed value.
- Deliberate violation for performance. Caching a derived value is allowed later, as an
  optimisation, provided the duplication is hidden inside one unit that keeps it consistent, so the
  outside sees none. "Localise the impact."
- Uniform access. Callers should not be able to tell whether a value is stored or computed; that is
  what lets you add the cache later without touching them. In languages with properties this comes
  for free; elsewhere avoid exposing raw fields that may become derived.
- Unnormalised models. If a truck has a driver and a delivery route also has a driver, which one do
  you change when the driver is off sick? Model the real relationship once.
- Make reuse easy. If finding an existing utility is harder than writing a new one, people will
  write a new one.

## 3. Orthogonality (Pragmatic Programmer ch. 2)

Two things are orthogonal when a change in one does not affect the other. Database code is
orthogonal to the user interface if you can change either without touching the other. The
counter-image in the notes is a helicopter's controls, where each input has side effects that need
compensating inputs: in a non-orthogonal system there is no such thing as a local fix.

The aim is components that are self-contained, independent and have a single well-defined purpose.

What it buys:
- Productivity: changes are local, so development and testing time drop; components are easier to
  write, test and reuse; combining components that do not overlap gives more function per effort.
- Lower risk: a bad component is isolated and replaceable; fixes stay in their area; components can
  be tested alone; third-party dependencies are confined to small parts.

How to apply it:

- Design in layers or components where each uses only the abstractions beneath it. The test: if the
  requirements behind one function change dramatically, how many modules are affected? One is the
  ideal. (The book's footnote admits real changes touch several functions; each functional change
  should still land in about one module.)
- Do not rely on properties of things you do not control. A phone number used as a customer
  identifier breaks when numbering changes.
- When adopting a toolkit or library, check whether it forces changes on your code that should not
  be there. A mechanism that requires special creation or access everywhere, or forces every caller
  to handle remote-ness, is not orthogonal.
- Keep code decoupled ("shy" code): modules reveal nothing unnecessary and do not depend on others'
  internals. To change an object's state, ask the object to do it.
- Avoid global data. Every reference ties the code to everything else sharing it; even read-only
  globals cause trouble under concurrency. Pass context explicitly. Singletons are often globals in
  disguise.
- Avoid similar functions. Functions with the same opening and closing and a different middle point
  to a structural problem; a strategy-style parameter is one fix (see `craft-design-patterns`).
- Teams: the informal measure is how many people must be involved in discussing each requested
  change. More people, less orthogonal.

DRY and orthogonality work as a pair: DRY reduces duplication within a system, orthogonality
reduces interdependence between its parts.

Testing as a probe: writing a unit test is itself an orthogonality test. If building the test
requires pulling in a large part of the system, the module is not decoupled. Bug fixing is another:
does a fix touch one module or many, and does it cause new problems elsewhere? The book suggests
tagging bug fixes and periodically reporting how many files each touched, as a trend.

## 4. Reversibility (Pragmatic Programmer ch. 2)

Critical decisions (a database vendor, an architectural pattern, a deployment model) are often
expensive to undo, and requirements, vendors and policies change. Treat no decision as final.

Practices:

- Hide third-party products behind a well-defined abstract interface, so the database is simply
  something that provides persistence as a service.
- Keep architectural choices such as deployment topology configurable where that is cheap.
- Keep volatile choices in metadata.
- Where a requirement cannot be isolated behind an interface and must be sprinkled through the
  code, put it in metadata and have a mechanism insert it, so that it can also be removed
  mechanically.
- For each major dependency ask how long it would take to swap.

DRY, decoupling and metadata all reduce the number of irreversible decisions.

Cost: abstraction layers and indirection. The book does not quantify it. The notes' inferred rule
is to apply this where a decision is both uncertain and costly to change. Clean Code ch. 11 makes a
related point: postpone decisions until you have the most information, which is possible only when
concerns are separated; and the notes add (inferred) that this fits decisions that are cheap to
defer, while those that are costly to reverse (data stores, public contracts, the security model)
should be made deliberately and early enough. For those, see `arch-decisions-and-tradeoffs`.

## 5. Decoupling and the Law of Demeter (Pragmatic Programmer ch. 5; Clean Code ch. 6)

Organise code into modules that know little about each other, like cells: if one must be replaced,
the others carry on.

The Law of Demeter for functions: a method should call only methods belonging to

1. its own object,
2. parameters passed to the method,
3. objects it creates,
4. objects its own object holds directly.

It should not call methods on an object that one of those calls returned.

```ts
// reaches through three types; breaks if any of them rearranges
const tz = selection.getRecorder().getLocation().getTimeZone();
plot(date, tz);

// ask the near object; better still, the plotting code takes only what it needs
plot(date, selection.timeZone());
```

Why: the chain makes the caller depend on every class along it. If the far class changes where it
keeps the value, unrelated code breaks. The notes cite one study of C++ classes linking a larger
"response set" (functions directly invoked by a class's methods) to more errors; that is a
correlation in one language, not proof.

Signs of too many dependencies: a simple change ripples through unrelated modules; developers are
afraid to change code because they cannot tell what it affects; (historically) the link command for
a unit test is longer than the test.

How to fix a chain. Two levels:

- Mechanical: add a method to the near object that delegates.
- Better: ask why the caller wanted the far thing, and move that behaviour to the object that has
  the data ("tell, don't ask"). A caller that fetched a directory path through two objects in order
  to create a scratch file should ask the first object to create the scratch file.

Passing only what is needed is often the cleanest: a function that takes a time zone does not need
to know a selection exists.

Costs and exceptions:

- Demeter produces forwarding methods, with their own overhead and maintenance. APOSD ch. 7 calls
  one-for-one forwarding a red flag. The reconciliation: a delegating method is worth having when
  it expresses the caller's intent and hides structure; if compliance yields methods named like
  `getXOfYOfZ`, the structure is being exported one hop at a time and the behaviour should move
  instead. See `layers-and-abstraction.md`.
- Whether a chain violates the rule depends on what the links are. Chains through objects expose
  structure. Chains through plain data structures do not, since data structures exist to expose
  structure. Fluent builders and stream pipelines that return the same kind of object are not
  violations either. (Clean Code ch. 6; the Pragmatic Programmer notes mark the same caveat as
  inferred.)
- Splitting a chain across local variables does not remove the knowledge; it only spreads it over
  lines.
- You may couple modules tightly on purpose for a measured performance gain, as a database
  denormalises, provided the coupling is known and documented. The failure is accidental,
  undocumented coupling.
- It is a heuristic. Applied dogmatically it creates the wrapper layers this skill warns about.

## 6. Metadata and configuration-driven design (Pragmatic Programmer ch. 5)

Details change more often than abstractions: business rules, regulations, preferences, deployment
targets. Each change made in code risks a new defect. So keep the abstractions in code and the
details in metadata, where metadata means any data that describes the application: how it should
run, what resources it uses.

"Configure, don't integrate": make choices such as algorithm, database product, middleware and
interface style configurable, not only colours and prompts.

Benefits claimed: it forces decoupling and a more abstract design; behaviour can be customised
without rebuilding, including quick work-arounds in production; metadata can be expressed closer to
the problem domain; one engine can serve several projects.

Business policy is the prime candidate because it changes most. The notes' example: pay small
suppliers in 45 days and large ones in 90; make the supplier categories and the periods data. For
complicated, changing workflow, a rule-based system configured by writing rules; for simpler logic,
a small language.

When to read configuration: a long-running server should be able to reload it while running, at
the cost of implementation complexity; a small program that restarts quickly can read it at startup.

Warning sign: a change to a policy value or a deployment target requires editing and rebuilding
source.

Code or metadata, from the appendix exercise (the authors say there are no definitive answers):

| Item | Leaning |
|---|---|
| Communication port settings | Metadata, at as fine a granularity as practical |
| An editor's syntax highlighting per language | Metadata; a new keyword should not need a code change |
| An editor's support for graphics devices | Hard as pure metadata; use metadata to name a driver that is loaded dynamically, and keep it readable so a bad setting can be repaired by hand |
| A parser's state machine | Depends on volatility: fixed standard, hard-code; changing format, external tables |
| Unit-test sample values and expected results | Out of the code |

Rule: externalise what changes often or is owned by users or standards; keep code for stable
abstractions.

Cautions (marked inferred in the notes): metadata-driven designs can grow into a poorly tested
programming language of their own. Configuration needs validation at load, versioning, and tests
for every configuration you ship. Keep secrets and environment-specific values out of
version-controlled defaults.

## 7. Code or configuration: reconciling the sources

APOSD ch. 8 says to avoid configuration parameters because each one moves work to users and
administrators and is often a dodge. Pragmatic Programmer ch. 5 says to move details out of code
into metadata. These address different kinds of value.

| The value is | Do |
|---|---|
| Something the module could compute, measure or adapt (buffer sizes, retry intervals, thresholds) | Compute it inside; export nothing, or export an override with a computed default |
| A fact about the deployment (hosts, ports, credentials, which backend) | Configuration |
| A business policy that changes independently of releases and has an owner outside the code | Configuration or a rule table, with validation |
| A structural detail that changes with a standard or format | Tables if volatile, code if fixed |
| An undecided design question | Decide it; a knob is not a decision |

In every row where a setting remains: give it a default, validate it on load, and make sure the
typical user never has to learn it exists. The test from APOSD holds throughout: can whoever sets
this determine a better value than the code can?

## 8. Domain languages (Pragmatic Programmer ch. 2)

Write code in the vocabulary of the problem domain; sometimes go further and express part of the
problem in a small language of its own. The notes' example routes messages with a few declarative
lines naming a source, formats and destinations; a new rule is a few more lines.

- Data languages produce a structure the program uses (configuration). Imperative languages are
  executed and have control constructs.
- Implementation options in rising cost: a line-oriented format parsed with simple matching; a
  grammar fed to a parser generator; or an embedded language made of functions in an existing host
  language.
- Report errors in domain terms: name the bad value and list the valid ones.
- Trade-off: a simple format is easy to parse and can be cryptic; a fuller language is harder to
  build and easier to read and extend. The authors lean to the more readable option because
  applications outlive expectations.
- For extensibility make the grammar data: the appendix answer for a small command language uses a
  table of command, takes-argument flag and handler, so adding a command is one row and one handler
  and the loop does not change.
- Separate parsing from emission behind a small back-end interface when one description must
  produce several outputs, so a new output is one new module.

Cost (from the text and inferred): another language for others to learn, with tooling and debugging
needs. Justify it when domain rules change often or people who are not programmers must configure
the system. Clean Code ch. 11 makes the same case for domain-specific languages, including APIs in
the host language that read like domain prose.

## 9. Temporal coupling (Pragmatic Programmer ch. 5)

Time enters design as ordering and as concurrency. Assuming "this always happens before that"
without a real dependency creates temporal coupling. The parts that bear on module design:

- An object should be valid at every point at which it can be called. A class with a constructor
  that does not finish the job and an `init()` that must follow is relying on coincidence. Prefer
  constructors that fully initialise; state class invariants.
- Hidden state between calls is temporal coupling. The classic example is a tokeniser that keeps
  its position in hidden static state and is continued by passing a null argument, so two strings
  cannot be processed at once even in one thread. Return an iterator or handle that owns the state.
- "Call A before B" in documentation is an ordering constraint in the informal interface (see
  `deep-modules-and-information-hiding.md`). Remove it by design where possible, or make invalid
  orders impossible through types.
- Module-level mutable state forces protection under concurrency; first ask why it is global.
- Designing so that things can run concurrently gives deployment options and usually a cleaner
  interface even if you never run concurrently; retrofitting is much harder.

The appendix adds that modal designs bake in assumptions about what state the system is in, which
is temporal coupling hidden as user-interface style.

Concurrency mechanisms, workflow analysis and thread-safety are in `craft-concurrency`.

## 10. Events, views and models (Pragmatic Programmer ch. 5)

Once responsibilities are separated, objects still need to learn of each other's state changes
without knowing much about each other. Events do that: a message that something interesting
happened, sent without knowledge of the receivers.

- Publish/subscribe: receivers register for the events they want; the publisher notifies its
  subscribers; subscribers can unregister. Avoid the opposite design, one routine that receives
  every event and switches on type, which concentrates knowledge of many objects' interactions.
- Model/view separation: keep one model (the data and its operations) and any number of views that
  interpret it, each possibly with its own controller. The model has no knowledge of views. You can
  add views, reuse a viewer over several models, and add controllers. Views need not be graphical;
  a view can be a model for a higher-level view, forming a network of links.
- Publishers and subscribers are still coupled through shared interface definitions.

The appendix exercise replaces a slow report that scanned every flight for overbooking with
listeners notified when a flight becomes full. Lessons: replace polling and batch scans with
notification, and separate "what happened" from "what to do about it".

Warning signs (inferred in the notes): a model importing interface classes; a view mutating the
model directly; subscribers never unregistered; notification loops. Pattern mechanics are in
`craft-design-patterns`.

## 11. Blackboards (Pragmatic Programmer ch. 5)

A shared space where independent participants post facts and react to facts posted by others,
without knowing each other. It decouples producers and consumers completely, anonymously and
asynchronously, and replaces many pairwise interfaces with one.

Use when: heterogeneous contributors post partial facts, arrival order is unpredictable, and
conclusions come from combining facts. The notes' example is a loan application: data arrives from
different people and systems at different times, some of it depends on other data, and rules change
with regulation. A board plus a rules engine makes arrival order irrelevant, since posting a fact
triggers whichever rules apply.

Do not use when: the work items are independent, in which case a plain work queue is enough (the
appendix answer for parallel image processing, unless the result of one chunk affects others); or
(inferred) when a sender needs a specific reply from a known service, or when tracing a chain of
anonymous reactions would cost more than the coupling removed.

Large boards get cluttered; partition them by area of interest.

Adaptation: queues and topics, shared stores with change feeds and event logs are the current
equivalents, as is a shared scratchpad among cooperating agents (marked inferred in the notes).

## 12. Choosing a mechanism

Derived table from the notes (Pragmatic Programmer ch. 5):

| Need | Choose | Cost |
|---|---|---|
| An object needs data from a distant object | Ask the nearby object, or pass in only what is needed | Delegating methods |
| Behaviour varies by policy, locale or environment | Metadata plus a general engine | Loaders, validation, tests per configuration |
| Two independent things run in series | Make them asynchronous or services with a queue | State must be safe under concurrency |
| Many consumers of one object's state changes | Publish/subscribe; model and views | Shared interface definitions remain |
| Producers and consumers must not know each other; data order unpredictable | Blackboard plus rules | Harder to trace; needs partitioning |
| Measured performance need | Break Demeter knowingly and document it | Explicit coupling |

Reading down the middle rows (direct ask, events, blackboard), each step decouples more and makes
the flow harder to follow; take the first one that solves the problem.

## 13. Lessons from the exercises (Pragmatic Programmer app. B)

- Narrowest input: a splitter that takes a line of text is more orthogonal than one that takes a
  reader, because it ignores where lines come from. A component should accept the narrowest input
  that expresses its job, a value instead of a source. Check: can it be tested with a literal and no
  I/O set-up?
- Object orientation is not automatically more orthogonal than procedural code. It offers more ways
  to couple invisibly (multiple inheritance, exceptions, operator overloading, overriding parent
  methods). Audit each use.
- A library routine that prints a prompt and reads the terminal assumes an environment it does not
  control. Libraries should return errors or call an injected handler, not talk to the user.
- A logging helper that opens a fixed file passes its unit test and fails where disk writes are not
  allowed. Make sinks pluggable; a test in one environment says nothing about others.
- A type code that selects behaviour through a switch is a cue for polymorphism; a window hard-wired
  to width and height can delegate to a shape object ("has-a") instead of subclassing, with an
  interface so the compiler flags every affected class when the concept changes.
- Tangled conditionals on data become table lookups; repeated expressions are computed once.
- For Demeter: `showBalance(account)` may call the account's methods but should not call a method
  on the money object the account returned; give the account a method that does the job.

## 14. Verification

- Change test: pick a business rule or fact and count the places to edit. More than one is a DRY
  violation.
- Silent-disagreement question: if this fact changes, what would silently disagree?
- Search for literals, copied blocks, parallel type definitions, and document/code pairs.
- Generated artefacts are rebuilt by the build and carry a "generated, do not edit" marker; change
  the source, build, and confirm the outputs change (the generation checks are partly inferred).
- Orthogonality test: for a dramatic change behind one function, list affected modules.
- Unit-test probe: the module compiles and tests with only its direct collaborators stubbed.
- Chain scan (inferred): search for chains of three or more calls, for example
  `rg '\)\.\w+\([^()]*\)\.\w+\('` as a rough first pass (adaptation, tested on sample lines: it
  matches `a.getB().getC().getD()` and `x.f(1).g(2).h(3)`, but misses chains split across lines and
  property-only chains such as `a.b.c.d`), then classify each hit as data, fluent or stream
  pipeline, or a real violation.
- Two-hops question: if a class two hops away changes its internals, does this file change?
- Reference count per class or module, tracked over time (inferred): number of distinct other
  modules each one imports.
- Reversibility (inferred): a second trivial implementation of each key abstraction (in-memory
  store, fake client) runs the same tests.
- Configuration: every shipped configuration is validated on load and exercised by a test; no
  policy value change requires a rebuild.
- Temporal coupling: tests call public methods in different orders, repeated and interleaved (two
  instances in one thread), and state stays valid (inferred).
- Model/view (inferred): the model builds and tests with no view present; a second view can be
  added without editing the model.
- Bug-fix locality: number of files touched per fix, as a trend.
