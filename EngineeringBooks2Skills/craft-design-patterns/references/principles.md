# Design principles behind the patterns

Every named principle in GoF 1994 (ch. 1, 2, 6) and Head First Design Patterns 2e (HF), each with: statement, what it means in practice, how to check it in a repository, what it costs or where the books soften it, and which patterns embody it. Where the books disagree or hedge, the entry says so.

Contents
1. Index of the principles
2. Encapsulate what varies
3. Program to an interface, not an implementation
4. Favor composition over inheritance (and delegation)
5. Strive for loosely coupled designs
6. Open for extension, closed for modification
7. Depend on abstractions (Dependency Inversion)
8. Principle of Least Knowledge (Law of Demeter)
9. The Hollywood Principle
10. Single Responsibility and cohesion
11. Smaller named ideas used as principles
12. How the principles conflict, and how to arbitrate
13. Review table: symptom to principle to check

## 1. Index of the principles

| # | Principle | Source | One-line test |
|---|---|---|---|
| P1 | Identify what varies and separate it from what stays the same (GoF: encapsulate the concept that varies) | HF ch. 1; GoF ch. 1, 2 | Does a new requirement force edits in code that has nothing to do with it? |
| P2 | Program to an interface, not an implementation | GoF 1.6; HF ch. 1 | Can you swap an implementation without editing clients? |
| P3 | Favor object composition over class inheritance | GoF 1.6; HF ch. 1 | Is behaviour that varies fixed by a subclass choice? |
| P4 | Strive for loosely coupled designs between interacting objects | HF ch. 2 | How much does A know about B beyond an interface? |
| P5 | Classes should be open for extension but closed for modification (OCP) | HF ch. 3 | Can a new variant be added with only new code? |
| P6 | Depend upon abstractions, not concrete classes (DIP) | HF ch. 4 | Do high-level classes import concrete low-level classes? |
| P7 | Principle of Least Knowledge: talk only to your immediate friends | HF ch. 7 | Are there call chains like `a.getB().getC().do()`? |
| P8 | Hollywood Principle: don't call us, we'll call you | HF ch. 8 | Do low-level parts call back into high-level logic to start things? |
| P9 | A class should have only one reason to change (SRP); cohesion | HF ch. 9 | How many different reasons could force an edit to this class? |

Smaller ideas the books also state: class versus interface inheritance, delegation, black-box versus white-box reuse, abstract coupling, aggregation versus acquaintance, separation of concerns, KISS, "if you don't need it now, don't do it now", the Rule of Three (section 11).

The HF toolbox lists P1 to P3 from chapter 1; P4 in chapter 2; P5 in chapter 3; P6 in chapter 4; P7 and P8 in chapters 7 and 8; P9 in chapter 9. Chapters 10 and 11 (State, Proxy) add no principle.

## 2. Encapsulate what varies (P1)

Statement: take the parts that vary and encapsulate them, so you can alter or extend them without touching what stays the same. GoF phrases the theme as "encapsulate the concept that varies"; almost every pattern is a way to let some aspect of a system vary independently (HF ch. 1; GoF 1.7).

In practice:
- The practical test is change. If some code changes with every new requirement, pull it out behind an interface. In the duck example only `fly` and `quack` varied, so only those two went into their own class families; `Duck` itself was left almost alone.
- Variation can be anticipated; you do not have to wait for pain. HF ch. 1 says explicitly that the principles apply at any stage of the lifecycle. HF ch. 13 and GoF ch. 6 narrow that: anticipate practical change that is likely, not hypothetical change (see section 12).
- The "what varies" list in selection-guide.md (Table 1.2) is this principle expressed pattern by pattern.

Check: for each recent change request in the history, list the files edited. If unrelated stable code keeps being edited with the varying code, the boundary is in the wrong place. After the refactor, adding a variant should add a class and leave existing classes untouched.

Cost: every extraction adds indirection. Do it for variation that is real.

Embodied by: nearly all patterns; Strategy, State, Decorator, Observer, Factory Method most visibly.

## 3. Program to an interface, not an implementation (P2)

Statement: the declared type of a variable or parameter is a supertype (an abstract class, interface, trait or protocol), so any implementation can be assigned and the declaring class never needs to know the concrete one. HF stresses that "interface" here means supertype, not the Java keyword; an abstract class qualifies.

In practice (GoF 1.6):
- Two benefits of coding to the abstract interface only: clients do not know the specific types of the objects they use, and they do not know the classes that implement them. Implementation dependencies between subsystems shrink.
- You must instantiate concrete classes somewhere. That is the job of the creational patterns, which bind interface to implementation at the point of creation.
- HF contrasts three levels: a variable typed as the concrete `Dog`; typed as `Animal` but assigned `new Dog()`; and typed as `Animal` with the concrete object obtained at run time (`getAnimal()`).
- Terminology: a type is a name for an interface; a subtype contains the interface of its supertype; a protocol adds the allowed sequences of requests (relevant to State, Proxy, Iterator).
- Class inheritance versus interface inheritance: class inheritance defines an object's implementation in terms of another's; interface inheritance (subtyping) says when one object can be used in place of another. The two are easy to conflate because common languages combine them. Many patterns rely on the distinction: members of a Chain of Responsibility share a type but usually not an implementation; Command, Observer, State and Strategy typically use pure-interface abstract classes. GoF's remedy is to inherit only from abstract classes, which have little or no implementation, and to keep substitutability in mind whenever you subtype (the second half is my restatement).

Check (inferred): search client code for `new ConcreteClass`, and for concrete types in field declarations and signatures. The only legitimate places are factories and the composition root. Swap an implementation in a test without editing the client.

Cost: one more type per abstraction; when there will only ever be one implementation, the interface is noise.

Modern form (adaptation): structural typing in TypeScript and Go, traits in Rust, protocols in Swift, and function types for single-method interfaces give this principle without inheritance.

Embodied by: all creational patterns exist to support it; Strategy, Observer, Command, State use it directly.

## 4. Favor composition over inheritance (P3), with delegation

Statement: build behaviour by holding references to other objects rather than by subclassing (GoF 1.6; HF ch. 1).

| | Inheritance (white-box reuse) | Composition (black-box reuse) |
|---|---|---|
| Fixed when | compile time | run time, by reference |
| Visibility | subclass sees parent internals | only interfaces are visible |
| Strengths | language-supported, easy to use, easy to override some behaviour | respects encapsulation; any object replaceable by another of the same type; fewer implementation dependencies; small focused classes and hierarchies |
| Weaknesses | cannot change at run time; parent defines part of the subclass's representation, so "inheritance breaks encapsulation"; parent changes force subclass changes; unsuitable inherited bits hurt reuse | more objects; behaviour depends on relationships between objects rather than on one class; needs carefully designed interfaces |

GoF's remedy for inheritance dependencies: inherit only from abstract classes, which have little or no implementation. HF's guru adds a reason: the promise of OO is reuse, but more time goes on maintaining and changing software than on writing it, so weigh maintainability and extensibility above inheritance-based reuse.

Delegation (GoF 1.6): the receiving object forwards a request to a delegate. With inheritance an inherited operation can refer to the receiver through `this`/`self`; with delegation the receiver passes itself to the delegate if the delegate needs it. Patterns relying on it: State and Strategy (delegate to the current state or strategy object), Visitor (the operation is always delegated to the visitor), more lightly Mediator, Chain of Responsibility and Bridge. The GoF caveat is part of the principle: delegation is "a good design choice only when it simplifies more than it complicates", dynamic and parameterised software is harder to read than static software, and there is some run-time cost.

Inheritance remains correct in two cases (HF ch. 1 and GoF 1.6): for the stable part after the varying part has been extracted, and to create new components that compose with existing ones. Template Method and Factory Method are deliberate uses of inheritance.

Third option: parameterised types (generics, templates). They change the types or operations a class uses at compile time; neither inheritance nor generics changes anything at run time. The GoF sort example shows all three: an abstract comparison in subclasses (Template Method), an owned comparison object (Strategy), a generic argument naming the comparison.

Check: flag subclasses that override an inherited method to do nothing; classes named by combining two features; behaviour fixes that must be repeated across sibling classes; subclass hierarchies where a run-time change of behaviour is needed. Each is a candidate for an extracted collaborator (Strategy, Decorator, State).

Embodied by: Strategy, State, Decorator, Bridge, Observer, Composite, Abstract Factory (object composition) versus Factory Method and Template Method (inheritance).

## 5. Strive for loosely coupled designs (P4)

Statement: strive for loosely coupled designs between objects that interact (HF ch. 2).

Meaning: loose coupling does not mean no dependency. It means an object does not know or care much about the details of another. Observer is the model case; HF lists five ways it loosens coupling:
1. The subject only knows that an observer implements the Observer interface, not its concrete class or purpose.
2. Observers can be added, replaced or removed at run time without the subject noticing.
3. New observer types never require modifying the subject.
4. Subject and observers can be reused independently.
5. Changes on either side do not affect the other while the interface contract is honoured.

GoF frames the same idea as cause 6 of redesign (section 4 of selection-guide.md): tightly coupled classes cannot be reused in isolation and form a monolith; the techniques are abstract coupling and layering. Abstract coupling means class A holds a reference to an abstract class B, so A refers to a type of object rather than a concrete one.

Aggregation versus acquaintance (GoF 1.6): aggregation means one object owns or is responsible for another with the same lifetime; acquaintance means it merely knows another, a weaker and looser coupling that is made and remade often. Both are usually implemented with the same reference, so the difference is intent and is hard to see in code. Consequence: the run-time structure is not visible in the class diagram, so name the pattern in the code where objects communicate through Observer or Chain of Responsibility.

Check (inferred): count the concrete classes a class imports; check whether either side can be unit tested alone with a stub of the other.

Cost: more indirection and more places to look when tracing a call.

## 6. Open for extension, closed for modification (P5)

Statement: classes should be open for extension but closed for modification (HF ch. 3). The goal is to allow new behaviour without touching existing, tested code. Writing new code instead of editing old code lowers the chance of regressions.

Meaning: not contradictory when extension happens through composition and polymorphism. Observer (add observers without editing the subject) and Decorator (add behaviour by wrapping) are the worked examples. HF uses OCP violation as a diagnostic: a waitress who must be edited each time a new menu appears, a remote with an `if/else` per vendor class, and a state machine written as conditionals all violate it.

The books' own limit (HF ch. 3 Q&A): you cannot and should not make every part follow OCP. It takes effort and adds abstraction; applying it everywhere is "wasteful and unnecessary, and can lead to complex, hard-to-understand code". Concentrate on the areas most likely to change, using experience and domain knowledge.

Check: pick the most likely next requirement and walk through it. If it needs edits to existing tested classes beyond the composition root, find out whether this is a place you decided to keep open.

## 7. Depend on abstractions (P6, Dependency Inversion)

Statement: depend upon abstractions; do not depend upon concrete classes (HF ch. 4).

Meaning: stronger than "program to an interface". High-level components (classes whose behaviour is defined in terms of other, low-level components) must not depend on low-level ones; both depend on abstractions. After Factory Method, `PizzaStore` depended only on `Pizza`, and the concrete pizzas depended on `Pizza` too, so the dependency arrows were inverted. A store that instantiated every concrete pizza depended on 8 concrete classes (12 with a third region), and each new pizza added another.

"Inverting your thinking": do not design top-down from the store to the concrete pizzas. Start from the concrete variants, see that they are all one abstraction, define it, then design the high-level class against it, and use a factory to obtain the concrete objects.

Three guidelines to help (strive for, not obey):
1. No variable should hold a reference to a concrete class (if you use `new`, you hold one; use a factory).
2. No class should derive from a concrete class.
3. No method should override an implemented method of its base class (if you override, the base was not a real abstraction; implemented methods are for sharing among subclasses).

The honest caveat in HF: nearly every program violates these, and you should not use factories dogmatically. Instantiating `String` directly is fine because it is very unlikely to change; use the guideline for classes likely to change. In my reading, rule 3 sits uneasily with Template Method hooks and Factory Method defaults (both let subclasses override a method that has a body); read the guideline as aimed at overriding behaviour the base promised to all subclasses.

Check: dependency direction. High-level modules import interfaces; concrete classes are imported only by factories and the composition root. A lint or architecture test (adaptation: an import-rule check in your build) can enforce it.

Modern form (adaptation): dependency injection containers and constructor injection operationalise DIP; the container or composition root holds the only references to concrete classes.

Hollywood versus DIP (HF ch. 8): DIP is the much stronger, more general statement; the Hollywood Principle is a technique for building frameworks and components.

## 8. Principle of Least Knowledge (P7)

Statement: talk only to your immediate friends (HF ch. 7). The Law of Demeter is the same idea; HF prefers the name Least Knowledge because "law" suggests you must always apply it.

Rule: inside a method, invoke only methods that belong to
1. the object itself,
2. objects passed in as parameters,
3. objects the method creates or instantiates,
4. components of the object (objects held by instance variables).

Do not call methods on objects returned from calls to other objects.

Example: `return station.getThermometer().getTemperature()` couples the caller to `Station` and `Thermometer`. Add `station.getTemperature()` that asks its thermometer; the caller then depends on one class.

Limits:
- The cost is more delegating wrapper methods: more code, development time and a little run-time overhead, in exchange for fewer dependencies.
- Hiding the chain in a local variable or helper that is then passed on is "hacking around the principle": the coupling is the same. Judge the dependency, not the syntax.
- HF is pragmatic about common cases (`System.out.println()` technically violates it) and says explicitly that no principle is a law.
- Facade is the pattern-level application: a client with one friend, the facade, is good. If a facade grows too complex, split it into several facades or layers.

Check: search for chained getters; count the distinct types a method touches.

Contested point: the HF text asks without answering whether a collection's `values().iterator()` violates the principle. Treat fluent builders and stream pipelines as fine (they return the same abstraction or a new value, not a part of someone's internals) (inferred).

## 9. The Hollywood Principle (P8)

Statement: don't call us, we'll call you (HF ch. 8).

Purpose: prevent dependency rot, where high-level components depend on low-level ones which depend back on high-level ones, sideways and in circles, until nobody can follow the design. Low-level components may hook into the system, but the high-level component decides when and how they are called. In Template Method the abstract class calls its subclasses' steps and clients depend on the abstraction. Factory Method and Observer also work this way, and frameworks do in general (GoF calls this inversion of control: with a toolkit you write the main body and call the library; with a framework you reuse the main body and write the code it calls).

Limits: a low-level component can legitimately call a method of its superclass; the aim is to avoid explicit circular dependencies. The cost of frameworks is lost creative freedom (GoF 1.6).

Smell (inferred): subclasses that call back into base-class internals in an order-dependent way are fragile-base-class cases and violate the principle in spirit.

Check: draw the call arrows between layers; low-level components should not start the flow.

## 10. Single Responsibility and cohesion (P9)

Statement: a class should have only one reason to change (HF ch. 9).

Reasoning: every responsibility is an area of potential change, and changing code risks bugs. If an aggregate also handled iteration, it would change when the collection changes and when the traversal changes. Assign each responsibility to one class. Iterator removes traversal from the aggregate; Memento keeps saved state in a separate object.

Cohesion is the related, more general measure of how closely a class supports a single purpose. SRP-compliant classes tend to have high cohesion and be more maintainable.

Caveats from the book:
- Separating responsibilities is "one of the most difficult things to do" because we group behaviours naturally; watch for signals that a class changes in more than one way as the system grows.
- Composite deliberately trades SRP for transparency: the component interface carries both child management and leaf operations so clients treat nodes uniformly. The cost is safety (an `add` on a leaf fails at run time). Alternatives are separate interfaces, which need type tests (safety versus transparency).
- A State class that handled both a normal and a "winner" outcome to save duplication was rejected because the class then held two responsibilities.
- Singleton arguably mixes managing its own instance with doing its real job; the defence is a simpler overall design.

Check: write the class's responsibilities as "this class changes when ___". More than one distinct blank means a split is worth considering. (For wider structure and class-size guidance see `craft-module-design`.)

## 11. Smaller named ideas used as principles

| Idea | Statement and use | Source |
|---|---|---|
| Separation of concerns | the remote should only interpret button presses and make requests, not know how to turn on a hot tub; basis for Command | HF ch. 6 |
| Encapsulation of method invocation | wrapping a request in an object decouples invoker from receiver | HF ch. 6 |
| KISS | solve things in the simplest way; the goal is simplicity, not applying a pattern | HF ch. 13 |
| If you don't need it now, don't do it now | do not build architecture ready for change from every direction | HF ch. 13 |
| Practical versus hypothetical change | use a pattern when you expect change to happen, not only when it might | HF ch. 13; GoF ch. 6 (Helm: practical extensibility) |
| Rule of Three | something is a pattern only after it has been applied successfully in at least three real solutions; GoF includes only designs used more than once in different systems | HF ch. 13; GoF preface |
| Design for change | anticipate new or changed requirements; unanticipated change is expensive redesign | GoF 1.6 |
| Black-box and white-box reuse | composition versus inheritance | GoF 1.6 |
| Intersection versus union interface | when abstracting several platforms, avoid the weakest-system and the everything interface | GoF ch. 2 |
| Which hierarchy changes more often? | choose Visitor-like or class-method-like structure by asking it | GoF ch. 2 |
| Center your thinking on design, not on patterns | use a pattern when there is a natural need; use the simpler solution otherwise | HF ch. 13 |
| Document deviations | when you adapt a pattern, record how it differs from the classic form | HF ch. 13 |

## 12. How the principles conflict, and how to arbitrate

| Tension | The two sides | Rule for deciding |
|---|---|---|
| Anticipate variation versus do not build it yet | HF ch. 1: you can anticipate variation up front and apply the principles at any stage. HF ch. 13: if you do not need it now, do not do it now. GoF ch. 6: do not introduce a pattern speculatively in a prototype; but if analysis shows a dimension that will change, design for it early (platform, algorithm, look and feel) | Build the seam when the requirement names the second variant, or when the change is cheap now and expensive later (platform, public interface, serialised format). Otherwise write the simple code and refactor toward the pattern when the pressure appears. |
| Open-closed versus simplicity | OCP everywhere is wasteful; OCP at likely change points is valuable | List the two or three most likely changes and make only those points open. |
| Composition versus readability | composition gives run-time flexibility; GoF warns it is harder to understand | Prefer composition when the behaviour must change at run time or per object; otherwise inheritance with a clear template is easier to read. |
| Single Responsibility versus Composite transparency | uniform interface puts two jobs in one class | Choose consciously between transparency (same operations on leaf and composite) and safety (child operations only on the composite). With sum types you can have both (modern-idioms.md). |
| Least Knowledge versus wrapper bloat | fewer dependencies versus many delegating methods | Add the wrapper where the chain crosses a module boundary or is repeated; leave local, stable chains alone. |
| DIP guideline 3 versus hooks | do not override implemented methods, but Template Method hooks do | Hooks with defaults are an explicit extension point of the base class; accidental overrides of behaviour the base promised are the problem. |
| Singleton convenience versus coupling | global access versus hidden dependency | See creational.md; inject one instance instead of reaching for a global. |

## 13. Review table: symptom to principle to check

| Symptom in a diff or a design | Principle | Check or fix |
|---|---|---|
| New variant requires editing a stable class | P1, P5 | find the varying part, put it behind an interface |
| Client names concrete classes | P2, P6 | introduce a factory or inject the dependency |
| Do-nothing overrides; a behaviour fix repeated across siblings | P3 | extract the behaviour into a collaborator |
| One class used by dozens of others through a global | P4 | pass it in; hide it behind an interface |
| `if/else` chain per vendor, status or type in a high-level class | P5, P1 | polymorphism: Command, State, Strategy, factory |
| `a.getB().getC().act()` | P7 | add a delegating method on `a` |
| Subclass reaches into base-class internals to start the flow | P8 | make the base class call the subclass steps |
| A class changes for persistence reasons and for display reasons | P9 | split the class |
| Pattern with one implementation and no foreseeable second | KISS, YAGNI | remove it (using-patterns-well.md) |
