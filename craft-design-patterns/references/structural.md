# Structural patterns: Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy

Seven patterns about how classes and objects are put together. Read this file when you are about to
wrap, front, share, nest or stand in for an object and need to pick which wrapper it is, or when you
are reviewing a class named `XAdapter`, `XProxy`, `XDecorator`, `XFacade` or `XManager` and want to
know whether the name is honest.

Citations: "GoF" is Design Patterns (1994), chapter 4 and the per-pattern pages; "HF" is Head First
Design Patterns 2e, with chapter numbers. Statements marked (adaptation) are not claims of the books:
they translate an idea to today's languages or are checks drawn up from the notes. Creational
patterns, principles and selection live in sibling reference files of this skill; the other behaviour
patterns are in `behavioral-1.md` and `behavioral-2.md`; function and sum-type forms of every pattern
are in `modern-idioms.md`. In every pattern entry the "Verify" bullets, misuse signs and smell lists come from the notes' own inferred sections, so treat them as the note-takers' checks, not the books' text, even where a bullet carries no label.

## Contents

1. The one rule for this family: intent, not structure
2. Quick chooser and comparison table
3. Adapter
4. Bridge
5. Composite
6. Decorator
7. Facade
8. Flyweight
9. Proxy
10. Neighbour comparisons in detail (Adapter/Bridge/Facade, Composite/Decorator/Proxy, Decorator/Strategy)
11. Review questions for any wrapper

---

## 1. The one rule for this family: intent, not structure

The structural patterns look alike on a diagram because they use the same two mechanisms: inheritance
and composition of objects. An Adapter, a Decorator and a Proxy can all be "a class that holds a
reference to another object and forwards calls". GoF ch. 4 discussion says the difference is
intent, and that choosing from the shape of a UML diagram alone is a mistake. So before naming
anything, answer one question about the wrapper:

| If the wrapper's job is to ... | It is a |
|---|---|
| change the interface of something that already exists so your code can use it | Adapter |
| let an abstraction and its implementations vary independently (decided up front) | Bridge |
| let a group of objects, and a single object, be used the same way (part-whole tree) | Composite |
| add behaviour to an object while keeping its interface, stackably | Decorator |
| give a subsystem a new, smaller front door | Facade |
| share many fine-grained objects by splitting off the state that varies | Flyweight |
| stand in for an object and control access to it (lazy, remote, permission, smart reference) | Proxy |

Head First says the same of the three wrappers (HF ch. 7, ch. 11): an adapter wraps an object to
change its interface, a decorator wraps it to add behaviour, a facade wraps a set of objects to
simplify, a proxy wraps to control access.

---

## 2. Quick chooser and comparison table

| Pattern | Interface relation to the wrapped thing | Purpose | Typical smell that calls for it |
|---|---|---|---|
| Adapter | different (it converts) | make an existing incompatible interface usable | vendor-API calls and `instanceof ThirdPartyType` scattered at call sites |
| Bridge | abstraction keeps its own interface; a separate implementor interface sits behind it | vary abstraction and implementation independently | class names that are cross products (`PdfInvoiceReport`, `CsvInvoiceReport`); platform switches in high-level classes |
| Composite | same for leaf and group | uniform treatment of part-whole trees | `if (x is Group) recurse else ...` at every call site |
| Decorator | same | add responsibilities, stackable, at run time | a subclass per feature combination; a base class growing boolean flags |
| Facade | new, simpler | simplify use of a subsystem; reduce coupling to it | the same multi-step call sequence copy-pasted across clients |
| Flyweight | same-ish; varying state passed in by the caller | share large numbers of fine-grained objects | memory profile dominated by huge numbers of near-identical objects |
| Proxy | same | control access to the subject | clients that must wait on, authenticate to, or locate something before using it |

Chooser by symptom:

- Third-party or legacy class does not match the interface my code expects: Adapter.
- Two independent axes of variation tangled in one hierarchy (shape x renderer, notification kind x
  channel): Bridge.
- Tree of things where groups and items must answer the same questions (size, price, render,
  validate): Composite.
- Cross-cutting add-ons (logging, retry, caching, compression, auth) around one interface: Decorator.
- Big subsystem, most callers need the same five-line happy path: Facade.
- Hundreds of thousands of objects, most state identical: Flyweight, after measuring.
- Object is remote, expensive, restricted, or needs bookkeeping on each access: Proxy.

---

## 3. Adapter

**Intent.** Convert the interface of a class into the interface clients expect, so classes with
incompatible interfaces can work together (GoF Adapter; HF ch. 7). Also known as Wrapper.

**Problem that signals it.** You have code written against interface A and a class (library, legacy
module, other team's service) that offers B. You cannot or should not edit either. The GoF example is
a drawing editor whose `Shape` needs a bounding box given as two corners, while the toolkit's
`TextView` offers origin plus width and height and has no concept of a manipulator.

**Use when.**
- An existing class is useful but its interface does not match the one your code needs.
- You are building a reusable class that must cooperate with unrelated classes whose interfaces you
  cannot predict.
- (Object adapter only) You need several existing subclasses and cannot adapt each by subclassing; an
  object adapter adapts the parent class and thus all its subclasses.

**Do not use when.**
- You own both sides and can simply change one interface: edit it. An adapter is a permanent layer.
- The language already matches shapes structurally (TypeScript, Go interfaces) and the shapes are the
  same; then a type that has the right methods just works (adaptation).
- The mapping is so large it amounts to a new abstraction over a whole subsystem: that is a Facade or
  a port, not an adapter.

**Structure.** Client uses Target; Adapter implements Target and holds an Adaptee; Adapter translates
each Target call into one or more Adaptee calls. Class adapter (multiple inheritance) versus object
adapter (composition) is the main fork.

**Consequences and costs.**
- Object adapter: one adapter serves the adaptee and all its subclasses and can add behaviour to all
  of them; overriding adaptee behaviour needs a subclass of the adaptee. Class adapter: commits to
  one concrete adaptee, can override its behaviour directly, one object instead of two, no extra
  indirection. In languages without multiple inheritance (Java, TypeScript) the object adapter is the
  default (HF ch. 7).
- Effort is proportional to the size of the Target interface, not the Adaptee's. Still cheaper than
  reworking every call site (HF ch. 7).
- Adapters often supply missing functionality, not just renames: the GoF `TextShape` implements
  manipulator creation itself. HF's Turkey-as-Duck adapter calls `fly()` five times to compensate for
  short flights, and the reverse adapter flies a duck only one call in five. Mapping can need
  semantic compensation.
- Gaps happen. HF adapts the old `Enumeration` to `Iterator`: `remove()` throws an unsupported-
  operation error because the adaptee is read-only. That is acceptable when the target interface
  anticipated it, the client is careful and the gap is documented. Fail loudly; a silent no-op hides
  the gap.

**Implementation choices.**
- How much adapting: from renaming operations to supporting a different set of operations; depends
  on how far Target is from Adaptee.
- Pluggable adapter (GoF): build the adaptation into a reusable widget by finding a narrow interface
  for the adaptee (the smallest set of operations the widget needs, e.g. "get children" and "present
  a node"). Three ways to implement: abstract operations in the widget with a subclass per structure;
  a delegate object implementing the narrow interface; parameterised adapters that store lambdas
  (`getChildren`, `createNode`). The last needs no subclassing.
- Two-way adapter: implements both interfaces so old and new code that expect different interfaces
  can share one object (GoF; HF ch. 7).
- Pass the adaptee in through the constructor so subclasses of it can be adapted.

**Sketch.**
```ts
interface Shape { boundingBox(): Rect; isEmpty(): boolean }
class TextShape implements Shape {             // object adapter
  constructor(private text: TextView) {}
  boundingBox() { const o = this.text.origin(), e = this.text.extent();
                  return rect(o.x, o.y, o.x + e.w, o.y + e.h) }
  isEmpty() { return this.text.isEmpty() }
}
```

**Neighbours and how to choose.**
- Bridge: similar shape to an object adapter, but Bridge is designed up front so both sides can vary;
  Adapter is a retrofit of things already designed (GoF).
- Decorator: keeps the interface and adds behaviour, so it is transparent and nests; a pure adapter
  changes the interface and does not.
- Proxy: same interface, controls access.
- Facade: defines a new simpler interface over many objects; an adapter reuses an old interface for
  one needed contract. HF notes an adapter may wrap several classes and a facade may simplify one
  class; the difference is intent.
- At service boundaries the same idea is the anti-corruption layer or port-and-adapter in hexagonal
  architecture (adaptation).

**Verify.**
- The client compiles against Target only; no Adaptee type appears in Target's signatures or beyond
  the adapter (otherwise the boundary leaks).
- The Target's contract tests pass unchanged against the adapter; a fake Adaptee can be injected.
- Unsupported operations fail loudly and are documented.
- The adapter holds translation only; if business rules have crept in, it has become a service.
- Misuse signs: adapters stacked to translate between three styles (introduce one canonical Target);
  an `XAdapter` that renames nothing (an unnecessary layer).

---

## 4. Bridge

**Intent.** Decouple an abstraction from its implementation so the two can vary independently (GoF
Bridge, also known as Handle/Body; HF appendix).

**Problem that signals it.** A hierarchy grows along two independent dimensions. The GoF example is a
portable `Window` for two window systems: subclassing gives `XWindow` and `PMWindow`; every new kind
of window (icon window) needs one class per platform, a third platform needs a new class for every
window kind, and client code that creates windows names a platform class. HF's version: a TV remote
whose abstraction (the remote's UI) will be refined over time while implementations (TV brands) also
vary.

**Use when.**
- You want to avoid a permanent binding between abstraction and implementation, for instance when the
  implementation is chosen or switched at run time.
- Both abstractions and implementations should be extensible by subclassing and combined freely.
- Changes in the implementation should not affect clients (no recompilation, in the book's terms).
- You see a proliferation of classes like the cross-product above.
- You want to share an implementation among several objects (a reference-counted string
  representation) and hide that from clients.

**Do not use when.**
- There is one stable implementation and no reason to hide it: the bridge is ceremony. (The book does
  describe a one-implementor degenerate bridge, useful only so implementation changes do not touch
  clients.)
- The Implementor interface would mirror the Abstraction's one-to-one; then no layering benefit is
  gained.
- You only vary one algorithm of a context; that is Strategy.

**Structure.** Abstraction (and RefinedAbstractions) holds a reference to an Implementor interface;
ConcreteImplementors realise it. The Implementor's interface need not match the Abstraction's: it
typically offers only primitive operations and the Abstraction builds higher-level ones on top.

**Consequences and costs.**
- Decouples interface from implementation; implementation can be configured and even changed at run
  time; compile-time dependencies on the implementation disappear; encourages layering.
- Improves extensibility: extend each hierarchy independently. N abstractions and M implementations
  cost N+M classes, not N x M.
- Hides implementation details from clients.
- Cost: more complexity (HF appendix lists it as the drawback), two hierarchies to understand.

**Implementation choices.**
- Only one Implementor: degenerate bridge (the "Cheshire Cat" or pimpl idiom).
- Who picks the Implementor: the abstraction in its constructor (a collection picks a linked list for
  small sizes and a hash table for large); start with a default and switch on usage; or delegate to a
  factory object (Abstract Factory) so the abstraction is coupled to no concrete implementor.
- Sharing implementors with reference counts (Handle/Body).
- Multiple inheritance cannot make a true bridge because the binding is static (GoF).

**Sketch.**
```ts
interface Renderer { rect(x:number,y:number,w:number,h:number): void; text(s:string,x:number,y:number): void }
abstract class Shape { constructor(protected r: Renderer) {} abstract draw(): void }
class Button extends Shape { draw() { this.r.rect(0,0,80,24); this.r.text("OK",8,16) } }
new Button(new SvgRenderer()).draw();     // implementation chosen at run time
```

**Neighbours and how to choose.**
- Adapter: retrofit versus up-front design. GoF's phrasing: Adapter makes things work after they are
  designed; Bridge makes them work before they are. Neither is inferior.
- Strategy: Strategy varies one algorithm inside a context; Bridge varies a whole implementation
  hierarchy under an abstraction hierarchy.
- Abstract Factory can create and configure a particular Bridge.
- In today's code this is "accept an interface in the constructor": the same shape as injecting a
  database driver, renderer, logger or storage backend. If the implementor has one primitive, a
  function-typed field suffices; Rust or C++ generics give a compile-time bridge (adaptation).

**Verify.**
- You can add a ConcreteImplementor without touching the abstraction hierarchy, and a
  RefinedAbstraction without touching implementors.
- A fake Implementor lets the abstraction be unit-tested.
- Clients never name an implementor class.
- No implementation type leaks out through the abstraction's interface.

---

## 5. Composite

**Intent.** Compose objects into tree structures to represent part-whole hierarchies, so clients treat
individual objects and compositions uniformly (GoF Composite; HF ch. 9).

**Problem that signals it.** Client code distinguishes primitives from containers even though the
user treats them the same. GoF: a drawing editor lets users group graphics into larger graphics
recursively. HF: menus that must contain submenus; the array-of-items design cannot hold a menu, so
a tree is needed (HF ch. 9).

**Use when.**
- The domain has part-whole hierarchies (file system, UI widgets, menus, org chart, expression tree,
  equipment with sub-assemblies, permission sets).
- Clients should ignore the difference between a group and a single item.
- One operation (price, size, render, validate) is naturally computed recursively over the tree.

**Do not use when.**
- Parts and wholes genuinely have different operations that callers must tell apart. Use the
  safety variant (below) or no Composite at all.
- The structure is a flat list; a loop will do.
- It would force an overly general component interface in which most operations make sense only for a
  few classes.

**Structure.** Component declares the operations common to leaf and composite (plus, in the
transparent version, child management). Leaf implements primitive behaviour. Composite stores
children and implements operations by forwarding to them, perhaps adding work before or after.

**Consequences and costs.**
- Hierarchies of primitive and composite objects; wherever a primitive is expected a composite can be
  used.
- Client code gets simpler: no tag-and-case code over the composition's classes.
- New kinds of components work with existing structures and clients.
- Can make the design overly general: the type system cannot restrict which components a composite
  may hold, so you need run-time checks.
- SRP trade-off (HF ch. 9): the Component interface mixes hierarchy management with the operations,
  trading single responsibility for transparency; the price is lost safety, because a client can
  call `add` on a leaf. HF says principles guide, and you must watch their effect on the design.

**Implementation choices (GoF lists nine).**
1. Explicit parent references simplify upward traversal and deletion and support Chain of
   Responsibility; keep the invariant by changing the parent only inside the composite's add/remove.
2. Sharing components is hard with single-parent links; Flyweight avoids storing parents by passing
   them in.
3. Maximise the Component interface with defaults so clients need not know leaf from composite; a
   leaf can be treated as a component with no children (the default child access returns empty).
4. Where to declare add/remove: in Component gives transparency but loses safety (make the default
   fail, for example throw, since silently ignoring hides bugs); only in Composite gives safety but
   loses transparency and may need a safe-downcast helper. The book emphasises transparency; HF's
   menu example throws an unsupported-operation error from defaults.
5. A child list in Component taxes every leaf with space; worthwhile only if leaves are few.
6. Child ordering matters for z-order or statement order; design child access carefully.
7. Caching traversal results (a composite caches its children's bounding box) needs parent links and
   an invalidation path.
8. Who deletes children (non-GC languages): the composite, except for immutable shared leaves.
9. Data structure for children: list, array, hash table, or one field per child.

HF's menu example also warns about a classic bug: the first composite `print()` printed only its own
header; a composite operation must recurse into children.

**Sketch.**
```ts
interface Equipment { power(): number; price(): number }
class Disk implements Equipment { power(){return 5} price(){return 40} }
class Chassis implements Equipment {
  private parts: Equipment[] = [];
  add(e: Equipment) { this.parts.push(e); return this }        // child ops only on the composite
  power() { return this.parts.reduce((s,p)=>s+p.power(), 0) }
  price() { return this.parts.reduce((s,p)=>s+p.price(), 0) }
}
```

**Neighbours and how to choose.**
- Decorator has the same recursive shape with one child; it adds responsibilities rather than
  aggregating. They are complementary: one Component base with composite subclasses, decorator
  subclasses and leaves lets you build behaviour by plugging objects together (GoF ch. 4).
- Iterator traverses composites; Visitor localises operations that would otherwise spread over the
  composite and leaf classes; Interpreter is a composite-shaped grammar; Builder often builds
  composites; Command's MacroCommand is a composite; Chain of Responsibility often uses the
  component-parent link.
- HF: Composite is a new approach, not an evolution of Iterator; they work well together.
- With sum types the tree is `Leaf | Group(children)` with an exhaustive match, and "a leaf cannot
  have children" is enforced by the type, resolving the safety-versus-transparency dilemma in favour
  of safety (adaptation).

**Verify.**
- An operation on the root equals the aggregate of the same operation on the leaves (total price is
  the sum). Test with nesting depth of at least three and with an empty composite (identity element,
  such as a sum of 0).
- Add and remove keep the parent invariant.
- A nested composite can be added with no client change.
- Unsupported leaf operations fail consistently or return documented neutral values.
- Guard cycles (a composite containing itself) and watch for shared children counted twice and deep
  recursion on very large trees (adaptation).

---

## 6. Decorator

**Intent.** Attach additional responsibilities to an object dynamically; a flexible alternative to
subclassing for extending functionality (GoF Decorator, also known as Wrapper; HF ch. 3).

**Problem that signals it.** Features multiply across a class. HF's Starbuzz: one subclass per
beverage-and-condiment combination explodes, and boolean flags in the base class fail when a new
condiment needs new code in the base, a drink where the condiment makes no sense inherits it anyway,
and a boolean cannot say "double mocha". Inheritance fixes behaviour at compile time for every
instance; the decorator attaches it per object, at run time.

**Use when.**
- Responsibilities must be added to individual objects, dynamically and transparently, and may be
  withdrawn.
- Subclassing is impractical: a large number of independent extensions would need a subclass per
  combination, or the class is closed to subclassing.
- You want to respect open-closed at a known point of variation (HF ch. 3 states the principle: open
  for extension, closed for modification, and warns that applying it everywhere is wasteful).

**Do not use when.**
- Only one or two fixed variants exist: subclass or add a parameter.
- Clients rely on the concrete type or on object identity of the thing being wrapped.
- The interface to wrap is large: every decorator must forward every method (adaptation: delegation
  features such as Kotlin `by`, or Go/TS embedding, reduce the boilerplate).
- You need to inspect or remove one specific inner decorator; a chain makes that hard.
- The component is heavyweight; see Strategy below.

**Structure.** Decorator conforms to Component's interface and holds a Component; ConcreteDecorators
add behaviour before and/or after forwarding (or instead of it). The decorator inherits to match type,
not to inherit behaviour (HF ch. 3).

**Consequences and costs.**
1. More flexible than static inheritance: add and remove at run time, avoid a class per combination,
   mix and match, and add the same decoration twice (double border, double mocha).
2. Avoids feature-laden classes high in the hierarchy: pay as you go; new decorators can be defined
   independently, even for unforeseen extensions.
3. A decorator and its component are not identical: do not rely on object identity, equality on the
   original reference, map keys or type tests. HF: `instanceof HouseBlend` for a discount stops
   working once wrapped.
4. Lots of little objects; easy to customise for those who understand it, hard to learn and debug.
   HF's "Confessions of a Decorator": many small classes (Java I/O is the example), typing problems
   when clients depend on concrete types, and more complex instantiation. Factories and builders
   centralise the construction of chains.
5. A client may hold a reference to an inner layer and miss the outer one.

**Implementation choices.**
- Conform to the component interface; share a common base for the decorators.
- Omit the abstract Decorator class when only one responsibility is ever added (retrofitting an
  existing hierarchy); keep it when several decorators share the forwarding.
- Keep Component lightweight: define an interface, do not store data in it, or every decorator
  carries the weight.
- Decorators must forward the component's other properties too, not only the one they enhance. HF's
  size exercise: the condiment decorator forwards `getSize()` to the wrapped beverage so size reaches
  the concrete drink through the chain.
- Order of wrapping matters (compress then encode; decode in reverse). Document it and test it.

**Sketch.**
```ts
interface Notifier { send(msg: string): void }
class Retrying implements Notifier { constructor(private inner: Notifier, private n = 3) {}
  send(m: string) { for (let i=0;;i++) try { return this.inner.send(m) } catch (e) { if (i>=this.n-1) throw e } } }
class Logging implements Notifier { constructor(private inner: Notifier) {}
  send(m: string) { console.log("send", m); this.inner.send(m) } }
const n: Notifier = new Logging(new Retrying(new EmailNotifier()));
```

**Neighbours and how to choose.**
- Adapter changes the interface; Decorator keeps it.
- Composite aggregates; Decorator adds. Decorator is a degenerate one-child composite but "misses the
  point" to call it that (GoF ch. 4).
- Proxy controls access; Decorator adds responsibilities. See section 10.
- Strategy: "skin versus guts". Decorator wraps from outside and the component knows nothing of it;
  Strategy is a narrow plug-in the component calls, and the component must be built for it. Choose
  Strategy when the component is intrinsically heavy (wrapping a full view just to add a border is
  too costly). Choose Decorator when the component is a small interface and you want unlimited
  stacking without touching it. GoF's MacApp example keeps lists of adorner and behaviour objects for
  that reason.
- A decorator is a higher-order function from a function to a function of the same signature in
  languages with first-class functions: middleware, Python `@decorator`, Go `http.Handler` wrappers
  (adaptation).

**Verify.**
- Every decorator is substitutable for its component: run the component's contract tests against
  decorated instances.
- Each decorator is tested alone against a fake inner component; a decorator that overrides nothing
  behaves identically to the bare component.
- One test fixes the order-sensitive case (wrap order A then B versus B then A).
- Multiple wrapping works (double mocha) and unrelated component methods are still forwarded.
- Grep: no `instanceof ConcreteComponent` on values that may now be decorated; chains are built in
  one place (factory or builder).
- Smells: decorators depending on undocumented stacking order; decorators exposing extra operations
  that clients must downcast to reach (breaks transparency); very deep chains that make stack traces
  hard to read.

---

## 7. Facade

**Intent.** Provide a unified, higher-level interface to a set of interfaces in a subsystem so the
subsystem is easier to use (GoF Facade; HF ch. 7).

**Problem that signals it.** Clients must drive many classes in a precise order. HF's home theatre:
watching a movie takes 13 manual steps across six classes, turning it off reverses them,
and every client duplicates the sequence and is coupled to every component. GoF: a compiler built from
scanner, parser, node builder and code generator, when most clients just want "compile this".

**Use when.**
1. You want a simple default interface to a complex subsystem. Subsystems grow complex as they
   evolve, and patterns tend to produce more, smaller classes, which helps reuse but burdens clients
   who need no customisation. Only clients that need more look past the facade.
2. There are many dependencies between clients and implementation classes: a facade decouples the
   subsystem from clients and other subsystems.
3. You want to layer subsystems: make each level's entry point a facade and let layers talk only
   through them.

**Do not use when.**
- The facade would only pass calls through one-to-one: it adds a layer for nothing (a pass-through
  "god class" collecting unrelated methods is a warning sign).
- Callers truly need the full power of the subsystem every time.
- You are translating one interface into another expected one: that is an Adapter.

**Structure.** Facade knows which subsystem classes handle a request and delegates. Subsystem classes
do the work and have no knowledge of the facade (one-way). Clients are not prevented from using the
subsystem directly; the facade offers ease of use, not enforced hiding (HF Q&A).

**Consequences and costs.**
- Shields clients from components, so fewer objects to deal with.
- Weak coupling between subsystem and clients; subsystem internals can change without affecting
  clients; helps layering and can remove circular dependencies; reduces compilation dependencies.
- You choose between ease of use and generality.
- The facade can grow into a dumping ground. Parameterising everything (scanner, builder,
  generator) adds flexibility but detracts from the mission of simplifying the common case.
- HF: a facade may add its own smarts (the popper must be on before popping; the staging order); a
  subsystem can have many facades; when a facade grows too complex, split it into several, forming
  layers.

**Implementation choices.**
- Reduce coupling further: make Facade an abstract class with one concrete subclass per subsystem
  implementation, or configure a single facade with different subsystem objects.
- Public versus private subsystem classes: the subsystem has a public interface (the facade plus
  classes any client may use) and a private one for extenders. Modern visibility features do this
  directly: package-private, module `internal`, Go `internal/`, Rust `pub(crate)`, restricted barrel
  exports (adaptation).
- Often there is one facade per subsystem, so it is commonly a singleton in the book; today a
  module-level or injected instance is enough (adaptation).

**Sketch.**
```
compile(source, target="risc"):            # facade: the five-line happy path
    tokens = Scanner(source)
    tree   = Parser().parse(tokens, ProgramNodeBuilder())
    tree.traverse(CodeGenerator.for(target, out))
```

**Neighbours and how to choose.**
- Adapter: reuses an old interface for one needed contract; Facade defines a new simpler interface
  over many.
- Mediator: both abstract existing classes, but Mediator centralises arbitrary two-way communication
  among colleagues who know it and adds behaviour none of them has; a facade only simplifies,
  adds no new functionality, and the subsystem does not know it.
- Abstract Factory can be paired with a facade to create subsystem objects without naming their
  classes, or used instead of a facade to hide platform-specific classes.
- Principle of Least Knowledge (HF ch. 7): a client with one friend, the facade, is a good outcome.
  Chained calls such as `a.getB().getC().doX()` are the matching smell.
- Service layers, SDK client wrappers, API gateways and backend-for-frontend services are facades at
  larger scale (adaptation).

**Verify.**
- An import or architecture rule shows clients depend only on the facade; subsystem classes do not
  import the facade (no cycle).
- Swapping a subsystem component requires edits only in the facade.
- The facade is tested on the happy path; the subsystem classes keep their own tests.
- Clients that bypass the facade to reach internals mean leaky layering; a facade clients must
  subclass to do anything useful is mis-designed (adaptation).

---

## 8. Flyweight

**Intent.** Use sharing to support large numbers of fine-grained objects efficiently (GoF Flyweight;
HF appendix).

**Problem that signals it.** Making every unit an object gives uniform design but needs far too many
objects. GoF: every character of a document as an object would need hundreds of thousands; one shared
object per distinct character needs about a hundred. HF: a landscape tool where each tree object
carries x, y, age and a heavy display routine makes large groves sluggish.

**Core idea: intrinsic and extrinsic state.** Intrinsic state lives in the flyweight, is
context-independent and therefore shareable (the character code). Extrinsic state depends on context,
cannot be shared, and is stored or computed by clients and passed in on each call (position, font).
The flyweight behaves as an independent object in each context but cannot assume anything about its
context.

**Use when (all must hold).**
- The application uses a large number of objects.
- Storage cost is high because of that number.
- Most object state can be made extrinsic.
- Many groups of objects can be replaced by few shared ones once extrinsic state is removed.
- The application does not depend on object identity.

**Do not use when.**
- Any of the five conditions fails, in particular when there are as many distinct extrinsic values as
  there were objects: nothing is gained.
- No memory problem has been measured (adaptation: measure the heap first; for small value types a
  struct or record often beats shared objects).

**Structure.** Flyweight interface takes extrinsic state in its operations; ConcreteFlyweight stores
only intrinsic state and must be shareable; UnsharedConcreteFlyweight (rows, columns) permits but
does not force sharing; FlyweightFactory creates and pools; clients get flyweights only through the
factory and hold or compute the extrinsic state.

**Consequences and costs.**
- A run-time cost for transferring, finding or computing extrinsic state, offset by space savings.
- Savings grow with the reduction in instance count, the amount of intrinsic state per object, and
  whether extrinsic state is computed rather than stored. Best case: lots of both kinds of state with
  extrinsic computed, saving twice.
- In a Composite DAG with shared leaves, a leaf cannot store a parent pointer; the parent is passed as
  extrinsic state, which changes how objects in the hierarchy communicate.
- HF: once implemented, a single logical instance can no longer behave independently of the others.

**Implementation choices.**
1. Removing extrinsic state is the crux. Ideal: derive it from a separate, much smaller structure (a
   run-length map of font attributes over runs of characters instead of a font per character).
2. Manage shared objects with a factory that looks up by key and creates on a miss. Sharing implies
   reference counting or garbage collection to reclaim; unnecessary if the set is small and fixed
   (ASCII): keep it permanently.

**Sketch.**
```
class Character(Glyph): code                   # intrinsic only; draw(window, ctx) receives extrinsic ctx
GlyphFactory.createCharacter(c): cache[c] ||= Character(c)
GlyphContext: index + compact (span -> Font) map     # the extrinsic store
```

**Neighbours and how to choose.**
- Composite plus Flyweight: a hierarchy as a DAG with shared leaves.
- GoF: State and Strategy objects are best implemented as flyweights when stateless.
- Abstract Factory supplies flyweights as a family; Strategy and State often are flyweights.
- Not Singleton (one instance of a class): a flyweight is one instance per distinct value of
  intrinsic state (adaptation).
- Today's forms: string interning, small-integer caches, symbols, enum-like constants, style and
  colour tables, texture atlases, and structure-of-arrays layouts that keep extrinsic data in arrays
  indexed by id (adaptation).

**Verify.**
- Measure before and after with a heap profile; keep the change only if the numbers move.
- Two requests with the same intrinsic key return the same instance; different keys do not.
- The flyweight is correct when used in two contexts alternately.
- Flyweights are immutable (or thread-safe): mutable fields on shared objects contaminate contexts.
  The pool is thread-safe and its key space is small; a pool that grows without bound is a leak,
  and weak references may be needed (adaptation).
- No logic compares flyweights by identity.

---

## 9. Proxy

**Intent.** Provide a surrogate or placeholder for another object to control access to it (GoF
Proxy, also known as Surrogate; HF ch. 11).

**Problem that signals it.** The client needs something that is awkward to reach directly. GoF: a
document with large raster images must open fast; an `ImageProxy` with the same interface stores the
file name and the image extent (so layout can ask for size without loading) and loads the real image
only on first draw. HF: a monitor needs to read gumball machines running in other processes, and a
reference into another heap is impossible.

**Use when (a reference more versatile than a plain pointer is needed).**
1. Remote proxy: local representative for an object in another address space. RPC stubs and generated
   API clients are this (adaptation).
2. Virtual proxy: creates expensive objects on demand.
3. Protection proxy: controls access where callers have different rights.
4. Smart reference: extra work on access (reference counting, load on first reference, check a lock
   before access).

HF's zoo adds firewall, caching, synchronisation, complexity-hiding ("facade proxy") and
copy-on-write proxies.

**Do not use when.**
- You want to add behaviour: that is a Decorator.
- You want to translate the interface: that is an Adapter.
- You are chaining many proxies: HF says wrapping something ten times means re-examine the design.
- The remote call would be hidden behind a local-looking interface that invites chatty fine-grained
  use; remote failure must stay visible (see Verify).

**Structure.** Subject interface; RealSubject; Proxy implements Subject, holds a reference (or just an
identifier) to the real subject and forwards when appropriate. The proxy often creates and manages
the real subject's lifetime.

**Consequences and costs.**
- A level of indirection with kind-specific uses: hide that the object is remote, create on demand,
  extra housekeeping on access.
- Copy-on-write: copying the proxy only increments a reference count; a mutating call makes it copy
  the subject first.
- Hidden latency and failure modes; identity surprises (the proxy is not the subject); lazy proxies
  move an error to the first use, which is a surprising place (ORM lazy-load after the session closed
  is the everyday case); lazy initialisation has thread-safety implications (adaptation).

**Implementation choices.**
- Language hooks (dated in form, still the idea): C++ operator overloading to make a pointer-like
  proxy cannot tell which operation is called, so it fails when the proxy must act on specific
  operations (load on draw, answer extent from cache); write the forwarding methods. Smalltalk
  message forwarding can forward any message but breaks identity checks and is slow.
- The proxy need not know the concrete subject type if it only uses the abstract interface; a virtual
  proxy that instantiates must know it.
- Referring to a subject that is not yet present or not local needs an address-independent identifier
  (file name, host and address, key or URL).
- HF protection proxy through a runtime-generated proxy class and one `invoke` handler: owner may
  call getters and set own data but not rate themselves; non-owner may call getters and rate but not
  edit; unknown methods return null (fail closed). HF's own caution applies: decide by method-name
  prefix is brittle, since a renamed method silently changes policy; prefer explicit allow-lists per
  role (this is a note-taker's caution on the book's example).
- Make clients get the proxy by having a factory build the subject and wrap it before returning it.
- HF virtual proxy for an image: while the image is absent the proxy returns a default size and paints
  a loading message, starts one background load guarded by a flag, and delegates once loaded; the
  field is marked volatile and set by a synchronised setter because two threads touch it.

**Sketch.**
```
class ImageProxy(Graphic):
    def __init__(s, path): s.path, s._img, s._extent = path, None, None
    def _real(s):  s._img = s._img or Image.load(s.path); return s._img
    def extent(s): s._extent = s._extent or s._real().extent(); return s._extent
    def draw(s, at): s._real().draw(at)
```

**Neighbours and how to choose.**
- Adapter gives a different interface; a proxy gives the same (a protection proxy that refuses some
  calls is effectively a subset).
- Decorator vs Proxy: see section 10. In short, a proxy normally manages its subject's lifecycle and
  may have no wrapped object yet; a decorator is handed a built component and stacks recursively.
- Facade vs proxy: the HF "complexity-hiding proxy" hides a set of classes and controls access; plain
  Facade only offers an alternative interface.
- Dynamic proxies: Java reflective proxies, JS `Proxy`, Python `__getattr__` delegation, C#
  `DispatchProxy`, generated stubs, ORM lazy relations, lazy values (a memoised thunk is the
  first-class-function form of a virtual proxy) (adaptation). The HF caution for the generic form:
  reflection overhead and harder debugging; use it when the same cross-cutting concern covers many
  interfaces.

**Verify.**
- The proxy passes the same contract tests as the real subject; results match except for the
  controlled aspect.
- Virtual: a spy shows the real subject is not created before first use and is created exactly once,
  including under concurrent first calls.
- Protection: assert allowed or denied for every role and method pair, including unknown and newly
  added methods, which must be denied.
- Remote: simulate timeouts, an unreachable host and partial failure; check every transferred type
  can be serialised (a run-time-only failure in the book's RMI example).
- No client code tests `instanceof` Proxy; no business logic lives in the proxy.

---

## 10. Neighbour comparisons in detail

### Adapter vs Bridge vs Facade (GoF ch. 4)

- Adapter and Bridge both add indirection and forward through an interface other than their own.
  Adapter resolves incompatibility between two existing interfaces and does not care how they are
  implemented or evolve. Bridge connects an abstraction to possibly numerous implementations and
  gives clients a stable interface while implementations vary.
- Timing differs: Adapter is a retrofit, found when two designed-apart classes must cooperate; Bridge
  is up-front design.
- A facade may look like an adapter for a set of objects, but it defines a new simpler interface;
  an adapter reuses an old one.

Decision rule from the notes: plug an existing or third-party class into an interface your code
expects, Adapter. Design an abstraction that will have several independent implementations
(platforms, drivers, backends) and let both hierarchies vary, Bridge. Provide a smaller front door
onto a big subsystem, Facade.

### Composite vs Decorator vs Proxy (GoF ch. 4)

- Composite and Decorator both use recursive composition for an open-ended number of objects. They
  are distinct but complementary: Composite is about representation (part-whole), Decorator about
  embellishment. From Decorator's viewpoint a composite is a ConcreteComponent; from Composite's
  viewpoint a decorator is a Leaf.
- Proxy and Decorator both hold a reference, forward calls and present the same interface. Proxy is
  not about attaching and detaching properties dynamically and is not designed for recursive
  composition. In a Proxy the subject defines the key functionality and the proxy provides or refuses
  access. In a Decorator the component supplies only part of the functionality and decorators supply
  the rest, so the total cannot be fixed at compile time and recursive composition is essential.
  A proxy focuses on one relationship, which can be expressed statically.
- HF adds practical tells: a proxy may have no wrapped object at all (remote: the subject is on
  another machine; virtual: it does not exist yet) and may instantiate the subject; decorators stack
  and never create their component. The "loading..." message of a virtual proxy looks like added
  behaviour, but its point is access control: the UI need not wait.
- GoF found hybrids (proxy-decorators) possible but had no real examples and says they divide into the
  useful patterns: compose the patterns rather than invent a new one.

### Decorator vs Strategy (skin vs guts)

Covered in section 6 and again in the behavioural comparison in `behavioral-2.md`.

### Class names as evidence (adaptation)

A class named `XProxy` that actually adds features is a Decorator. An `XAdapter` that renames nothing
is an unnecessary layer. A `Manager` or `Helper` "facade" that accumulates unrelated methods is a
dumping ground. A `Decorator` that only forwards is dead weight.

---

## 11. Review questions for any wrapper

Ask these when reviewing or writing one; each has an observable answer.

1. Which of the seven intents in section 1 does it serve? If two, split it.
2. Does the wrapper's interface equal the wrapped one (Decorator, Proxy, Composite), differ (Adapter),
   or shrink (Facade)? Does the name match?
3. Does anything compare wrapped objects by identity, equality on the original reference, or concrete
   type? Those break under Decorator, Proxy and Flyweight.
4. Who builds the wrapper chain, and is it one place?
5. Is the wrapper's order significant, and is there a test that fixes it?
6. What happens on failure, especially for lazy and remote wrappers?
7. Is the contract test of the wrapped type run against the wrapper?
8. Would deleting the wrapper make the code simpler? If yes, the wrapper was premature.
