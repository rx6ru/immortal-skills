# Creational patterns and their alternatives

Sources: GoF ch. 3 (opening, Abstract Factory, Builder, Factory Method, Prototype, Singleton, closing discussion); Lexi case study (ch. 2); HF ch. 4 (Simple Factory, Factory Method, Abstract Factory, Dependency Inversion), ch. 5 (Singleton), appendix (Builder, Prototype). Items marked "(adaptation)" or "(inferred)" go beyond the books' own claims.

Contents
1. What creational patterns are for
2. Choosing among them (decision table, evolution rule, worked comparison)
3. Plain constructor and Simple Factory (the baseline and the idiom)
4. Factory Method
5. Abstract Factory
6. Builder
7. Prototype
8. Singleton (and why to be suspicious)
9. Dependency injection as the alternative to most of this
10. Relationships between the patterns
11. Verification checklist for creational code

## 1. What creational patterns are for

They abstract the instantiation process so the system does not depend on how its objects are created, composed and represented. Two themes recur (GoF ch. 3): they encapsulate knowledge about which concrete classes the system uses, and they hide how instances are created and put together. The system then knows objects only through interfaces, which gives flexibility in what is created, who creates it, how and when, statically or dynamically.

Why they matter more as a system evolves: designs shift from a fixed set of hard-coded behaviours to a smaller set of fundamental behaviours that compose into complex ones, so creating an object with a given behaviour takes more than `new Class`.

"When you see `new`, think concrete" (HF ch. 4). Nothing is wrong with `new` itself. The problem is change: code that instantiates concrete classes chosen at run time, such as an `if/else` on a type string, has to be reopened every time a type is added, and tends to be copy-pasted. It cannot be closed for modification.

Class scope versus object scope: a class creational pattern varies the instantiated class by inheritance (Factory Method); an object creational pattern delegates instantiation to another object (Abstract Factory, Builder, Prototype; Singleton is listed with these).

The running example in GoF is a maze game whose `CreateMaze` hard-codes `new Room`, `new Door`, `new Wall`. The problem is not size but inflexibility: reusing the layout for an enchanted maze means editing the function. The four ways out are exactly the four patterns: virtual creation calls plus a subclass (Factory Method), a factory object passed in (Abstract Factory), a builder object told to add rooms and doors (Builder), and prototypical room, door and wall objects copied (Prototype). Singleton ensures one maze factory per game.

## 2. Choosing among them

### Decision table

| Situation | Prefer |
|---|---|
| The class never changes, or creation sits in an operation subclasses can already override | plain constructor call |
| Centralise creation logic for one product type; no subclassing needed | Simple Factory or a static factory function (an idiom) |
| A framework or base class has a fixed workflow and must create objects whose class only a subclass knows; you subclass anyway | Factory Method |
| A family of products that must be used together; the family is switched as a whole; the kinds of product are stable | Abstract Factory |
| One complex product assembled in steps; one assembly process, several representations (or many optional parts) | Builder |
| Product class chosen or configured at run time; avoid a creator hierarchy parallel to the product hierarchy; few state variations; dynamically loaded types; user-defined presets | Prototype |
| Exactly one instance is a correctness requirement and global access is acceptable | Singleton, with suspicion (section 8) |
| Starting a design | plain constructor or Factory Method; refactor toward the others when the need shows up |

### Evolution rule (GoF ch. 3 discussion)

Abstract Factory, Prototype and Builder are more flexible than Factory Method but also more complex. Designs often start with Factory Method and evolve toward the others as the designer discovers where more flexibility is needed. Generalised (adaptation): constructor call, then a factory function when a second variant appears, then a registry or injection binding when variants multiply, then a builder when assembly has many optional steps.

### Two ways to parameterise a system by the classes it creates

1. Subclass the creator (Factory Method). Drawback: you may need a new subclass just to change the product class, and changes can cascade when the creator is itself produced by a factory method.
2. Make an object that knows the product class a parameter of the system (Abstract Factory, Builder, Prototype). All three introduce a factory object. Abstract Factory's makes objects of several classes; Builder's builds a complex product incrementally through a correspondingly complex protocol; Prototype's builds a product by copying, so the factory object and the prototype are the same object.

### Worked comparison: the drawing editor's tool (GoF ch. 3 discussion)

A `GraphicTool` must create whichever `Graphic` the user selected from a palette.
- Factory Method: one `GraphicTool` subclass per `Graphic` subclass, each overriding `NewGraphic`. Easiest at first, but subclasses proliferate and each does little.
- Abstract Factory: a `GraphicsFactory` hierarchy with one factory per product. Little improvement; worthwhile only if a factory hierarchy already exists or is needed elsewhere.
- Prototype: each `Graphic` implements `Clone`, and the tool is configured with a prototype. Probably best here: fewer classes, and `Clone` is reusable (for example in a Duplicate command).

The lesson: count the classes each option adds, and check whether a capability you need anyway (cloning) can carry the creation.

## 3. Plain constructor and Simple Factory

Baseline: if the class never changes (HF: `String`) or instantiation happens in a method subclasses can already override, call the constructor. Do not add a factory to feel safe.

### Simple Factory (HF ch. 4; an idiom, not a GoF pattern)

- Intent: move the type-selecting `if/else` into a separate object or static function so the caller keeps only the stable process.
- Signal: `orderPizza(type)` mixes `new CheesePizza()` / `new GreekPizza()` branches with the stable steps prepare, bake, cut, box. New pizzas force edits to the same method.
- Use when: one product family member is chosen from a key, several callers need it, and nothing needs to subclass the creation.
- Do not use when: variants must plug into a fixed workflow by subclassing (Factory Method), or products come in matched sets (Abstract Factory).
- Structure: `factory.create(type)` returns an abstract product; the caller uses only the abstract type.
- Costs: the creation logic still has the `if/else`; it just lives in one place. A static factory cannot be subclassed to change creation behaviour. A string key is not type safe (a typo is a run-time error); use an enum, constants or a parameter object (HF Q&A).
- Sketch (TypeScript):
  ```ts
  type Kind = "cheese" | "veggie";
  const makePizza = (kind: Kind): Pizza => kind === "cheese" ? new CheesePizza() : new VeggiePizza();
  ```
- Neighbours: Factory Method adds subclass-chosen products inside a framework. A "static factory method" on a class (`Foo.fromJson(...)`) is the same idea, widely used and unrelated to subclassing.
- Verify: no caller names a concrete product; adding a product edits only the factory.

## 4. Factory Method

- Intent: define an interface for creating an object, but let subclasses decide which class to instantiate; a class defers instantiation to subclasses. Also known as Virtual Constructor.
- Problem that signals it: a framework knows when to create an object (File > New) but not which class. `Application` must create a `Document` it only knows abstractly. Or: a base class that hard-codes `new ConcreteHelper`, or a growing `switch(kind)` ending in `new X`.
- Use when: a class cannot anticipate the class of objects it must create; it wants its subclasses to specify the objects it creates; or classes delegate to one of several helper subclasses and you want to localise which one.
- Do not use when: the instantiated class never changes; you would subclass only to change which class is instantiated (pass a factory function or class instead); you cannot or do not want to subclass the creator.
- Structure: `Creator` declares `factoryMethod(): Product` (abstract, or with a default) and has operations that call it; `ConcreteCreator` overrides it to return a `ConcreteProduct`. The HF pizza version: `PizzaStore.orderPizza` (the stable workflow, ideally final) calls abstract `createPizza`; `NYPizzaStore`, `ChicagoPizzaStore` implement it. Which subclass you instantiate is the "decision".
- Consequences:
  - Application-specific classes no longer appear in the creator's code; it works with any `ConcreteProduct`.
  - Cost: clients may have to subclass the creator just to get a particular product. Fine if they subclass it anyway.
  - Provides hooks for subclasses: creating via a factory method is always more flexible than creating directly (a default dialog that subclasses can replace).
  - Connects parallel hierarchies: `Figure.createManipulator()` localises which manipulator class belongs with which figure; the parallel hierarchies can be partial if the method returns a default.
  - With one concrete creator it is still useful: it decouples product implementation from use (HF Q&A).
- Implementation choices (GoF):
  1. Abstract creator (subclasses must supply) versus concrete creator with a default (rule: create objects in a separate operation so subclasses can override how they are created).
  2. Parameterised factory methods: `create(id)` returns different products; subclasses add ids and delegate unknown ids to the parent. HF warns a string parameter is not type safe.
  3. Language specifics: in C++ do not call a factory method from the creator's constructor, because the subclass override is not yet available; use lazy initialisation through an accessor. In dynamic languages a method can return a class, or the class can be stored in a field so no subclassing is needed.
  4. Templates or generics (`StandardCreator<Product>`) avoid subclassing in C++.
  5. Naming conventions make factory methods recognisable.
- Sketch (TypeScript):
  ```ts
  abstract class Exporter {
    protected abstract createWriter(): Writer;                  // factory method
    export(doc: Doc) { const w = this.createWriter(); doc.rows.forEach(r => w.row(r)); return w.result(); }
  }
  class CsvExporter extends Exporter { protected createWriter() { return new CsvWriter(); } }
  ```
- Neighbours and choosing: Abstract Factory is often implemented with factory methods. Factory methods are usually called from Template Methods (the creator's workflow is a template, `createX` the hook). Prototype avoids subclassing the creator but needs `Clone`. Choose Factory Method when the variation is naturally "per subclass" and you already extend the base; choose injection of a factory function or Prototype when you would rather compose than subclass.
- Verify: a test subclass overrides the factory method to inject a fake product without editing the base class; the base class names no concrete product; the workflow method cannot be bypassed by subclasses (HF: franchisees skipped the shared process until creation was tied into one workflow; make the workflow final where the language allows).

## 5. Abstract Factory

- Intent: provide an interface for creating families of related or dependent objects without specifying their concrete classes. Also known as Kit.
- Problem that signals it: `if (platform == X) new XButton else new YButton` in many places; a Motif menu appearing in a Mac window because one `new` was missed (GoF ch. 2); near-identical per-region subclasses that differ in a few ingredients (HF: `NYCheesePizza` and `ChicagoCheesePizza`).
- Use when: the system should be independent of how products are created; it should be configured with one of several families; products of a family are designed to be used together and you must enforce that; you want to expose only interfaces for a library of products.
- Do not use when: there is only one product kind (use Factory Method or a function); the product set changes often (every new kind edits the factory interface and every concrete factory); products come from third-party hierarchies with no common abstract classes (introduce abstractions first, with Adapter or Bridge, as the Lexi window-system case showed).
- Structure: `AbstractFactory` declares one create operation per abstract product; each `ConcreteFactory` returns its family's concrete products; the client uses only the abstract factory and abstract products. Normally one concrete factory instance exists at run time.
- Consequences:
  1. Isolates concrete classes: names appear only in concrete factories.
  2. Makes exchanging product families easy: the concrete factory appears once; switch family by switching factory (and recreating the UI).
  3. Promotes consistency among products: only one family in use at a time.
  4. Cost: supporting new kinds of product is hard; the factory interface fixes the set, so a new kind edits the abstract factory and every subclass.
- Implementation choices (GoF):
  1. Concrete factories are usually singletons, one per family.
  2. Creating products: usually one factory method per product (needs a new subclass per family). Alternatives: a prototype-based factory (initialise with a prototype per kind and clone, so no subclass per family); a class-based factory that stores classes and calls `new` (where classes are first-class).
  3. Extensible factories: a single `make(kind)` takes an id. More flexible, less type safe: results are typed as the common base and clients may need downcasts that can fail.
  4. Where the factory comes from: a global, a static member, a local, or a Singleton, initialised after the choice is known and before first use. A registry mapping strings to factories avoids editing code to add a family and avoids linking platform-specific factories that may not exist (GoF ch. 2).
- Sketch (TypeScript), with the only selection point:
  ```ts
  interface UiKit { button(label: string): Button; scrollBar(): ScrollBar }
  const kits: Record<string, () => UiKit> = { motif: () => new MotifKit(), pm: () => new PmKit() };
  const kit = (kits[config.look] ?? kits.motif)();         // the only place a concrete kit is chosen
  function buildDialog(kit: UiKit) { return [kit.button("OK"), kit.scrollBar()]; }
  ```
  A function-based form (adaptation): pass `{ makeButton, makeScrollBar }` as a record of constructors.
- Factory also guarantees family consistency, which enables safe downcasts: in the maze, a `RoomWithABomb` can cast its walls to `BombedWall` because only the bombed factory builds them.
- Neighbours and choosing: Prototype when families are numerous or open-ended or products are best configured by value; Builder when constructing one complex product step by step; Factory Method when a single product and creator subclassing are acceptable. Compare table, HF ch. 4:

  | | Factory Method | Abstract Factory |
  |---|---|---|
  | Mechanism | inheritance: extend a creator, implement the method | composition: pass a factory object to code written against the abstract factory |
  | Creates | one product (may be parameterised) | a family of related products |
  | Intent | let a class defer instantiation to subclasses | create families without depending on concrete classes |
  | Creator code | usually real logic that uses the product | creation only |
  | Extending | add a subclass | adding a product type breaks the interface |

- Verify: grep that concrete product names occur only in concrete factories; build the whole client object graph with a fake or test factory; assert that each concrete factory returns a mutually consistent family and never null (HF); switching the factory changes all products at once.

## 6. Builder

- Intent: separate the construction of a complex object from its representation so the same construction process can create different representations.
- Problem that signals it: an RTF reader that must output ASCII, TeX and an editable widget, with the parsing algorithm duplicated per target; a parser or exporter that hard-codes its output type; a vacation planner whose days contain any combination of hotels, tickets and reservations (HF appendix).
- Use when: the algorithm for creating a complex object should be independent of the parts and how they are assembled; the construction must allow different representations.
- Do not use when (inferred): there is one representation and no reuse of the director, so it is ceremony; a plain constructor or an options object does the job.
- Structure: `Builder` has an operation per component a director might request (with empty default bodies, so concrete builders override only what they need); `ConcreteBuilder` assembles parts, tracks the representation, and provides a way to retrieve the product; `Director` drives the builder; the client configures the director with a builder and retrieves the product from the builder, not from the director.
- Consequences:
  1. Lets you vary a product's internal representation: the builder interface hides structure and assembly.
  2. Isolates construction code from representation: it lives once in a builder, and different directors can reuse it.
  3. Finer control over the construction process: step by step, the product retrieved only when finished, unlike one-shot patterns.
- Implementation choices (GoF): the assembly interface must serve all builders; an append-only model is often enough, but some builders need earlier parts (a door between existing rooms) or return child nodes to the director for bottom-up trees. There is usually no abstract product class, because products differ too much (text string versus widget); the client chose the builder so it knows what it gets.
- Sketch (TypeScript):
  ```ts
  interface HtmlBuilder { heading(t: string): void; para(t: string): void }
  function parse(src: string, b: HtmlBuilder) { for (const t of lex(src)) t.kind === "h" ? b.heading(t.text) : b.para(t.text); }
  class StringHtml implements HtmlBuilder { out = ""; heading(t: string) { this.out += `<h1>${t}</h1>`; } para(t: string) { this.out += `<p>${t}</p>`; } }
  class CountingHtml implements HtmlBuilder { n = 0; heading() { this.n++; } para() { this.n++; } }   // builds nothing
  ```
  The counting builder from the maze sample shows the process is decoupled from the product.
- Neighbours and choosing: Abstract Factory also builds complex objects, but it emphasises families and returns each product immediately; Builder builds one product step by step and returns it at the end. A Composite is what a builder often builds. HF notes Builder demands more domain knowledge from the client than a factory.
- Modern note: two different things share the name. GoF's director-plus-builder (algorithm times representation) survives as event or SAX-style handlers, tree and query builders. The popular fluent builder for assembling an immutable object with many optional fields is a different idiom, mostly replaced by named or default parameters, struct literals with spread, copy-with, and options objects (adaptation; the notes mark this as inferred).
- Verify: add a new output representation without editing the director; director code contains no product class names; an incomplete sequence is detected when the product is retrieved (inferred).

## 7. Prototype

- Intent: specify the kinds of objects to create using a prototypical instance, and create new objects by copying it.
- Problem that signals it: a framework cannot `new` application classes (a music editor's notes); a class-per-configuration explosion where classes differ only in values (whole note, half note); a palette or "templates" feature; types loaded at run time.
- Use when the system should be independent of how products are created, and: classes to instantiate are specified at run time; or you want to avoid a factory hierarchy parallel to the product hierarchy; or instances have only a few state combinations, so installing that many prototypes and cloning beats instantiating and configuring each time.
- Do not use when: `Clone` is hard to implement (existing classes, uncopyable internals, circular references) and no simpler route exists; the product class is fixed.
- Structure: `Prototype` declares `clone`; `ConcretePrototype` implements it; the client asks a prototype to clone itself. Typically a prototype manager (registry keyed by name) holds the prototypes.
- Consequences: all the benefits Abstract Factory and Builder have in hiding concrete classes, plus:
  1. Add and remove products at run time by registering and unregistering prototypes.
  2. New objects by varying values: new "kinds" are configured instances, so users can define classes without programming.
  3. New objects by varying structure: a composite can be a prototype if `clone` deep-copies.
  4. Reduced subclassing, mostly where classes are not first-class objects.
  5. Configure an application with classes dynamically.
  Main liability: every concrete prototype implements `clone`.
- Implementation choices (GoF):
  1. Prototype manager when the set is not fixed: an associative registry with register, unregister and browse.
  2. Implementing `clone`: shallow versus deep. Shallow copies share state with the original. "Cloning forces you to decide what, if anything, will be shared." Circular references need care. If save and load exist, clone can be save to a buffer and load.
  3. Initialising clones: a uniform `clone` cannot take varying parameters; use setters after cloning or an `initialize(...)` operation (in the maze, `Door.initialize(room1, room2)`). Release copies made by a deep clone before re-initialising.
  `clone` is declared on the base class but each subclass returns an instance of itself, so clients never downcast.
- Sketch (TypeScript):
  ```ts
  class Palette { private protos = new Map<string, Shape>();
    register(k: string, s: Shape) { this.protos.set(k, s); }
    make(k: string) { return this.protos.get(k)!.clone(); } }
  palette.register("whole-note", new Note({ duration: 4 }));   // a configured instance, not a new class
  ```
- Neighbours and choosing: competes with Abstract Factory; they combine (a factory can store prototypes and clone). Versus Factory Method: no creator subclassing, but products need `clone`. Designs heavy in Composite and Decorator benefit from cloning pre-built structures.
- Modern note (inferred): with immutable values the pattern largely vanishes; a prototype is a value you derive new values from (`{...preset, name}`). A registry of presets covers most cases. Java's `clone()` is widely considered flawed; prefer copy constructors or factories. Rust `Clone` is explicit and deep by default; Python has `copy.deepcopy`; JavaScript has `structuredClone`.
- Verify: mutate the clone and assert the original is unchanged; a clone of a subclass has the same dynamic type; a clone of a graph preserves internal sharing and cycles as intended; clone of objects that hold resources (files, sockets, ids) is deliberate.

## 8. Singleton (and why to be suspicious)

- Intent: ensure a class has only one instance and provide a global point of access to it.
- Problem that signals it: one print spooler, one window manager, a thread pool, a cache, a settings registry, a logger, a hardware driver. More than one instance would cause incorrect behaviour, resource overuse or inconsistent results. HF's example: a chocolate boiler controller where two boiler objects could fill an already boiling boiler.
- Use when: exactly one instance is a requirement of correctness or a physical resource, and a well-known access point is acceptable; the sole instance should be extensible by subclassing, with clients using an extended instance without change.
- Do not use when (inferred; the later consensus, not the books' own text): you only need one instance in practice (a startup decision) rather than one that may never be duplicated (an invariant). Create it once at startup and pass it in (section 9). Also not when it would hold mutable state shared by many classes, or when tests need isolated instances.
- Structure: a class with a private constructor, a private static instance field and a static `instance()` accessor (create on first call if lazy).

### What the books say, and where they differ

GoF lists five consequences as benefits: controlled access, reduced name space compared with globals, refinement by subclassing, a variable number of instances if you change your mind, and more flexibility than static operations. HF is more guarded: Singleton couples every user to the class, may break the single-responsibility principle, is hard to subclass, can be defeated by class loaders, reflection and serialisation, and "if you are using a large number of Singletons... take a hard look at your design". The notes record the later consensus (not in the books, inferred): it is widely treated as an anti-pattern because it is hidden global state with hidden dependencies, order-of-initialisation problems, hard testing and concurrency hazards, and because it mixes a uniqueness policy with the class's behaviour.

Rule for deciding: default to one object created at the composition root and injected. Use a hand-written Singleton only where the language or framework leaves no better way to share a process-wide resource, and keep its interface behind an abstraction so tests can substitute a fake.

### Implementation choices

1. Ensuring a unique instance (GoF): hide creation behind a class operation; a global or static object with automatic initialisation is not enough in C++ because you cannot guarantee only one is declared, values may not be known at static-initialisation time, constructor order across translation units is undefined, and every singleton is created whether used or not.
2. Subclassing (GoF): choose the subclass in `instance()` from an environment variable (hard-wires the subclasses); put the implementation in the subclass and choose at link time (fixed, no run-time choice); or use a registry of singletons by name (frees `instance()` from knowing subclasses). HF: the private constructor prevents extending; loosening it ends the Singleton; the static field is shared by derived classes; "what are you really gaining?".
3. Thread safety (HF ch. 5; the lazy `if (instance == null)` is a check-then-act race: two threads can each create an instance and each hold a different one):

   | Option | Use when | Notes |
   |---|---|---|
   | Synchronise `getInstance()` | not performance critical | trivial and correct; the lock is only needed the first time; the book says it can cost a factor of 100 (dated) |
   | Eager instantiation | always needed, or cheap to build | thread-safe because of class-load semantics; loses laziness |
   | Double-checked locking with `volatile` | `getInstance()` is on a hot path and laziness matters | broken before Java 5; overkill otherwise |
   | Single-element `enum` (Java) | you simply need a singleton in Java | removes thread-safety, class-loading, reflection and serialisation worries; cannot extend a class; created at class load |

   HF decision rule: choose the simplest correct option unless a measured performance constraint justifies more. For the boiler: synchronised method or eager construction.
4. Other languages (adaptation, partly inferred in the notes): a module-level value in Python, JavaScript and Go (package variable), `object` in Kotlin and Scala, `static let` in Swift, `OnceLock` or `LazyLock` in Rust, `sync.Once` in Go, a function-local `static` in C++11. Modules already give "one instance with a well-known name"; DI containers register a service with singleton lifetime without the class knowing.
- Sketch (TypeScript): prefer the second form.
  ```ts
  class Config { private static inst?: Config; private constructor(readonly values: Record<string,string>) {}
    static instance() { return (Config.inst ??= new Config(load())); } }
  const config = load();                                   // better: build once at the composition root
  const app = new App(config, new Db(config));
  ```
- Neighbours: concrete factories, builders and prototype managers are often singletons. A class with only static members is not equivalent: it cannot be subclassed or swapped, and static initialisation order across classes causes subtle bugs (HF Q&A).
- Verify: N threads call `instance()` behind a latch and all references are identical, repeated many times; no public or protected constructor exists (a reflection test where the language allows); deserialisation returns the same instance if it is serialisable; the instance can be reset or replaced in tests; nothing depends on initialisation order. For the boiler, state-machine invariants hold across concurrent callers through the single instance. For concurrency design of the surrounding code see `craft-concurrency`.

## 9. Dependency injection as the alternative to most of this

(Adaptation; the notes mention it as the modern counterpart of the creational patterns and of DIP.)

Dependency injection means a class receives the collaborators it needs (an object, or a factory function when it must create several or create late) instead of constructing them or fetching them from a global. One place, the composition root near start-up, knows which concrete classes are used and wires them. This covers:

| You were considering | Injection form |
|---|---|
| Singleton | build one object at the root, pass it to those that need it; "singleton" becomes a lifetime choice |
| Factory Method to swap a collaborator | constructor parameter of the interface type |
| Abstract Factory | inject the factory interface, or a record of constructor functions |
| Simple Factory to hide `new` | inject a `() => Product` or a class reference |
| Registry of factories (Lexi) | a map from key to factory function, populated at the root |

What it does not remove: you still need a decision point where concrete classes are named. Keep it to one module. Do not let the container leak into business classes by asking it for objects (a service locator brings back the hidden global state of a Singleton and has the same testability problems; the notes make this caution for the registry idea too).

## 10. Relationships between the patterns

- Abstract Factory is implemented with Factory Methods or with Prototypes; concrete factories are usually Singletons.
- Builder often builds a Composite; Builder can use another creational pattern to decide which components get built.
- Factory Methods are typically called from Template Methods.
- Prototype helps Composite- and Decorator-heavy designs; Prototype can use Singleton for its manager.
- Prototype competes with Abstract Factory and with Factory Method.
- In the Lexi window system, Abstract Factory is combined with Bridge: the factory chooses which implementation object the abstraction receives.
- Decorator chains are easy to forget to build; HF suggests hiding their assembly in a factory or builder (the compound-patterns chapter uses an Abstract Factory that returns pre-wrapped ducks). See compound-and-mvc.md.

## 11. Verification checklist for creational code

1. State the variation in one sentence ("which look and feel", "which exporter") and name two realised variants. If you cannot, use a plain constructor.
2. Dependency rule: concrete product names occur only in factories and the composition root. Check with a search for `new ` and for concrete types in signatures and fields.
3. Add-a-variant test: write the new variant and confirm that only new code, plus one registration, is needed.
4. Fake test: construct the client with a fake factory or builder and run its logic with no real dependencies.
5. Family consistency for Abstract Factory; no downcasts of factory results.
6. Clone independence for Prototype (mutation test, dynamic type, resources).
7. Singleton: identity under concurrency, reset in tests, no initialisation-order dependence, a stated reason why injection is not enough.
8. Complexity audit: count the classes the pattern added and what each buys. Creational patterns trade simplicity for flexibility and are justified only when the flexibility is used.
