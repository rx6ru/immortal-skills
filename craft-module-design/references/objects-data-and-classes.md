# Objects, data structures and classes

How to decide whether a type should be an object or a data structure, how to expose state, how to
tell when a class has too many responsibilities, and how to use inheritance.

Contents
1. Data abstraction
2. Objects versus data structures: the axis of change
3. Hybrids, DTOs, beans and active records
4. Accessors: three positions and a rule
5. Class size means responsibilities
6. Cohesion
7. Organising for change (open-closed)
8. Isolating from change (dependency inversion)
9. Inheritance and composition
10. Class layout and test access
11. Disputed points
12. Verification

## 1. Data abstraction (Clean Code ch. 6)

Fields are made private so that nobody depends on them and the representation stays free to change.
Generating a getter and setter for each field gives that freedom back. Hiding implementation is not
a layer of accessors; it is offering abstract operations that let users work with the essence of the
data without knowing its form.

- A point exposed as two fields `x` and `y` commits to rectangular coordinates. An interface that
  can report rectangular or polar coordinates and sets a pair atomically hides which form is stored
  and enforces an access policy.
- A vehicle that reports tank capacity and litres remaining exposes representation and leaves the
  arithmetic to callers. One that reports the fraction of fuel remaining expresses the concept.

```python
# caller does the maths and depends on the units
level = car.fuel_litres / car.tank_capacity_litres
# the concept; the representation can change
level = car.fuel_fraction_remaining()
```

## 2. Objects versus data structures: the axis of change

Objects hide their data behind abstractions and expose functions. Data structures expose their data
and have no meaningful functions. They are near opposites, and each makes one kind of change cheap.

- Data structures with separate functions: adding a new function is easy (nothing existing
  changes); adding a new data type is hard (every function changes).
- Objects with polymorphic methods: adding a new type is easy (no existing function changes);
  adding a new function is hard (every type changes).

"Everything is an object" is not a goal. Choose per part of the system.

| Likely change | Choose |
|---|---|
| New kinds of thing, stable set of operations | Objects with polymorphism |
| New operations over a stable set of kinds | Data structures with functions, or a sum type with pattern matching |
| Both change often | Accept the cost and isolate it; a visitor-style arrangement is one option with costs of its own; or fix one axis by design |

Adaptation noted in the notes: this is the "expression problem". Languages with algebraic data
types and exhaustive matching (sealed hierarchies, discriminated unions, enums with payloads) make
the data-plus-functions side safer, because the compiler lists every function that must handle a
new variant. Records and immutable value types are legitimate designs, not failures of object
orientation.

For an agent: before adding a case, look at which axis the existing code is built on. Adding a
variant to a type that is switched on in twenty places, or an operation to a hierarchy of twenty
classes, is the expensive direction; say so, and consider whether the structure should change
first. The appendix of the Pragmatic Programmer gives the related cue: a type code that selects
behaviour through a switch is a candidate for polymorphism.

## 3. Hybrids, DTOs, beans and active records

- Hybrid: half object and half data structure, with significant behaviour and also public fields or
  accessors that expose state. It is hard to add functions to and hard to add types to, and usually
  shows the designer was unsure which protection was needed.
- Data transfer object: fields and no functions. Useful for database rows and for parsing messages;
  often the first stage in turning raw input into application objects.
- Bean: private fields with accessors. The chapter calls this quasi-encapsulation with usually no
  other benefit.
- Active record: a data structure with navigational methods such as save and find, usually mapping
  a table. The mistake is adding business rules to it, which makes a hybrid. Treat it as data and
  put the rules in separate objects that hide it.

## 4. Accessors: three positions and a rule

- Clean Code ch. 6: do not expose representation through blanket accessors; expose abstract
  operations. But DTOs with public data are fine as data structures.
- APOSD ch. 19: better not to expose instance variables at all. Accessors are shallow one-line
  methods that add clutter, and exposed fields complicate the interface. `private` plus accessors
  is not information hiding (ch. 5).
- Pragmatic Programmer ch. 2: read attributes through accessor functions, so that a stored value
  can later become computed or cached without changing callers (uniform access).

These are compatible once you separate two questions.

1. Should this piece of state be visible outside at all? Only if a caller needs the concept. If
   callers fetch it in order to compute or decide something, move that computation or decision into
   the type ("tell, don't ask").
2. If it is visible, how? Through something that names the concept, not the storage, and that could
   be backed by a computation. In languages with properties, records or computed attributes that is
   syntactically free; elsewhere it is a method.

So: plain data types may expose fields openly and should carry no business behaviour; behavioural
types expose operations and the minimum of state, with setters especially rare. The notes add that
frameworks often require accessors and that modern property syntax changes the cost; the question
that matters is whether the abstraction leaks.

## 5. Class size means responsibilities (Clean Code ch. 10)

The chapter's rule is that classes should be small, with size counted in responsibilities, not
lines or methods. Even a five-method class is too big if it has two responsibilities.

Tests for too many responsibilities:

1. Name test. The name should describe the responsibility. If no concise name fits, the class is
   probably too large. `Processor`, `Manager` and `Super` in a name hint at aggregation.
2. Description test. Describe the class in about 25 words without "if", "and", "or" or "but".
3. Reasons-to-change test (single responsibility principle). A class should have one reason to
   change. List the kinds of change that would force an edit. More than one suggests a split.

The chapter's example is a dashboard class that both tracked the last-focused component and
reported version numbers: the version information changes with every release, the GUI management
for other reasons. Extracting a small `Version` class also made it reusable.

Why the principle gets violated: making code work and making it clean are different activities.
Concentrating on working first is appropriate; the failure is stopping there.

On whether small classes are the goal at all, see section 11 and `together-or-apart.md`. The three
tests remain useful under either view, because they detect mixed responsibilities, not size.

## 6. Cohesion

Definition used: a class should have a small number of instance variables, and each method should
use one or more of them. The more of the variables a method uses, the more cohesive it is with the
class. Every method using every variable is neither achievable nor desirable; aim high.

Signal to split: instance variables used by only a subset of the methods. There is usually another
class trying to get out.

A causal chain to recognise during restructuring:

1. You want to extract part of a large function, but it uses several local variables.
2. Instead of passing them as arguments, you promote them to instance variables.
3. The class now has fields that exist only so a few functions can share them; cohesion drops.
4. Those functions and fields are a class of their own. Split it out.

Stopping at step 3 is worse than where you started: data flow that was explicit has become hidden
shared state (the notes flag this in the chapter's own example, which also used static mutable
fields). Either finish at step 4 or pass the values explicitly.

The chapter's long example restructures a single 70-line prime-printing function into three
classes: one for the execution environment, one for laying numbers out in pages, one for generating
primes. Each has one reason to change. It was done without rewriting: a test suite pinned the exact
behaviour first, then many small changes were made with a run after each. The program got about
three times longer. The mechanics of such a restructuring belong to `craft-refactoring`.

## 7. Organising for change (open-closed)

Every edit to a class risks breaking the rest of it. A class that must be opened for each new
feature of some kind has a structural problem.

Example: a class that builds SQL text with a method per statement type and private helpers. It has
two reasons to change (a new statement type; a change to one type's details). A tell: private
methods that serve only a small subset of the class.

Restructured: an abstract base holding the table and columns with one abstract generate operation,
one subclass per statement type, statement-specific helpers moved into the subclass that needs
them, and shared pieces as small utility classes. Adding a new statement type then adds a class and
changes no existing one. That is the open-closed principle: open for extension, closed for
modification.

Timing, which is the important hedge: the primary spur should be change itself. If the class is
logically complete, or no new feature is foreseeable, leave it. When you find yourself opening the
class, consider fixing the design then.

Adaptation noted in the notes: the example uses inheritance; current practice often gets the same
effect with composition, strategy functions or pattern matching. What survives is that new variants
should be addable without editing existing tested code.

## 8. Isolating from change (dependency inversion)

Concrete classes carry implementation detail; interfaces carry concepts. A client that depends on a
concrete detail is exposed when it changes, and is hard to test.

Example: a portfolio that talks directly to a live stock-exchange client gets a different answer
every few minutes. Define an interface named for the concept (current price of a symbol), have the
real client implement it, and pass an implementation to the portfolio's constructor. A test passes
a stub with fixed prices.

Dependency inversion principle: depend on abstractions, not on concrete details. The chapter uses
testability as the proxy for low coupling: a system decoupled enough to be tested this way is also
more flexible.

When to do it: the dependency is volatile, external, slow or non-deterministic. See
`boundaries-and-construction.md` for the construction side.

## 9. Inheritance and composition (APOSD ch. 19)

- Interface inheritance (a shared contract with several implementations) gives leverage against
  complexity: one interface learned once serves many purposes. The more implementations an
  interface has, the deeper it is, and to support many it has to capture essentials and leave out
  differences, which is abstraction.
- Implementation inheritance (a parent supplies code that subclasses reuse or override) removes
  duplication but creates dependencies between the parent and every subclass. Parent state used by
  both sides is information leakage across the hierarchy: changing the parent may require reading
  all subclasses, and overriding may require reading the parent. Hierarchies that lean on it tend
  to be complex.

Guidance:

1. Prefer interface inheritance for polymorphism.
2. For shared code, consider composition first: small helper classes that the others use.
3. If you do inherit implementation, separate the state the parent manages from the state
   subclasses manage; subclasses use parent state read-only or through parent methods.

The Pragmatic Programmer appendix agrees from the other direction: prefer delegation ("has-a") to
subclassing, and notes that object-oriented features such as multiple inheritance and overriding
are additional ways to couple invisibly. Adaptation (inferred in the notes): mixins and traits
raise the same leakage questions.

Object-oriented mechanisms do not guarantee good design. Shallow classes, complicated interfaces
and exposed state are just as possible with them.

## 10. Class layout and test access (Clean Code ch. 10)

- Convention described: constants first, then private state, then public functions, with each
  private helper directly after the public function that uses it, so the file reads from headline
  to detail. Follow the host language's and codebase's convention; layout detail belongs to
  `craft-clean-code`.
- Keep variables and helpers private, but the chapter is not strict when a test needs access: it
  allows widening to package or protected scope as a last resort, after looking for a way to keep
  privacy. Many teams prefer to test only through the public interface; the notes record this as
  contested. Order of preference: test through the public interface; restructure so the logic sits
  behind its own interface; only then widen visibility.

## 11. Disputed points

- Small classes versus deep modules. Clean Code says small, then smaller, by responsibility; one
  subclass per SQL statement is its idea of a good result. APOSD says many tiny classes are shallow
  and scatter logic. The notes advise recording both and applying the reasons-to-change test
  instead of a size target. The full decision rule is in `together-or-apart.md`.
- Law of Demeter. A heuristic. Dogmatic use produces pass-through wrappers and method explosion on
  facades. The defensible core: do not reach through an object's structure to act on what it owns;
  tell it what to do. See `coupling-orthogonality-dry.md`.
- Anaemic domain model. Keeping rules in service objects separate from data classes is criticised
  elsewhere as anaemic, yet the chapter's advice for active records is exactly that arrangement.
  The notes resolve it by domain complexity: rich rules justify behaviour-bearing domain objects;
  simple create-read-update-delete code does not. The durable part is not to mix persistence
  mechanics with business rules in one class.
- Active record as a framework's chosen pattern is a deliberate trade; the warning applies mainly
  when business rules are rich.
- Open-closed restructuring is hedged by its own authors: do it when change arrives.

## 12. Verification

- Classify each type as object or data structure and check it matches: objects have private state
  and behaviour with abstract names (no raw representation in method names); data structures carry
  no business behaviour.
- Axis test (inferred in the notes): list the two likeliest changes, a new type and a new
  operation, and count the files each would touch. The cheaper one should be the likelier one.
- Representation-swap test: could internal field types change without any caller changing?
- Accessor count: accessors that only pass a field through; any type with an accessor pair per
  field and also substantial behaviour.
- Chain scan: for each chain across types, is the middle thing a data structure? If not, find the
  behaviour to move.
- Responsibility tests on every class you created or enlarged: concise name; 25-word description
  with no conjunctions; one nameable reason to change.
- Field-usage matrix (inferred): rows are methods, columns are fields. Most methods should touch
  most fields; a block structure shows the classes hiding inside.
- Open-closed check: add the next variant and confirm the diff touches only new files plus wiring.
- Dependency-inversion check: the class can be unit-tested with a stub and no network, clock or
  database.
- Hierarchy check (inferred): can the parent be modified without reading every subclass? Do
  subclasses touch parent fields directly?
- Before restructuring a class: tests that pin its current behaviour exist and are run after each
  small step.
