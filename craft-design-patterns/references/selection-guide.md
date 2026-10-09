# Selection guide: from "what varies" to a pattern

Sources: GoF ch. 1 (sections 1.4 to 1.8), ch. 2 (Lexi case study), ch. 6; Head First Design Patterns 2e (HF) ch. 1, 4, 13. Where a point is my adaptation rather than the books' claim, it is marked "(adaptation)" or "(inferred)".

Contents
1. Why start from variation, not from a pattern name
2. The six ways to select (GoF 1.7)
3. What each pattern lets you vary (Table 1.2)
4. The eight causes of redesign
5. Smell to cause to pattern lookup
6. The 23 intents, with classification and where to read more
7. Selection procedure (step by step)
8. Application procedure (step by step)
9. Inheritance, composition or generics for the variation point
10. How much flexibility: application, toolkit or framework
11. Worked selections: Lexi (GoF ch. 2) and the duck and pizza examples (HF)
12. Trigger phrases and the first candidates to examine

## 1. Why start from variation, not from a pattern name

A pattern is a recorded design that lets one aspect of a system change without touching the rest. Both books teach selection by asking what will change, because that is the only question that tells you whether any pattern is needed. Picking "the pattern I know" first leads to the failure that HF ch. 13 calls beginner mind: patterns used for their own sake.

Four elements make something a pattern (GoF 1.1): a name, the problem and context in which it applies, a solution that is a template (an arrangement of roles, not finished code), and consequences (costs and trade-offs). The consequences are the part people skip and the part that decides whether the pattern fits. Read them before you commit.

## 2. The six ways to select (GoF 1.7)

Use whichever fits what you have in hand. When you start from a codebase or a requirement, approaches 5 and 6 are the usual entry points (adaptation; GoF does not rank the six).

1. Consider how patterns solve design problems: finding objects, granularity, interfaces, inheritance versus composition (see principles.md).
2. Scan the intent lines (section 6 below) and narrow by purpose (creational, structural, behavioural) and scope (class or object).
3. Study how patterns relate (for example Composite is traversed with Iterator and extended with Visitor).
4. Compare patterns of like purpose: the near-neighbour discussions in creational.md, structural.md and behavioral-2.md.
5. Examine a cause of redesign (section 4) and take the patterns listed for it.
6. Ask what should be variable in the design, which is approach 5 turned around: not what might force a change, but what you want to be able to change without redesign. Use section 3.

Class versus object scope (GoF 1.5): class patterns relate classes by inheritance and are fixed at compile time (Factory Method, Template Method, Interpreter, the class form of Adapter). Object patterns relate objects by composition and can change at run time. Most patterns are object patterns. Prefer the object form when you need run-time flexibility; the class form when the choice is fixed per type and you want simple default behaviour.

## 3. What each pattern lets you vary (GoF Table 1.2)

| Purpose | Pattern | Aspect that can vary |
|---|---|---|
| Creational | Abstract Factory | families of product objects |
| | Builder | how a composite object gets created |
| | Factory Method | subclass of object that is instantiated |
| | Prototype | class of object that is instantiated |
| | Singleton | the sole instance of a class |
| Structural | Adapter | interface to an object |
| | Bridge | implementation of an object |
| | Composite | structure and composition of an object |
| | Decorator | responsibilities of an object without subclassing |
| | Facade | interface to a subsystem |
| | Flyweight | storage costs of objects |
| | Proxy | how an object is accessed; its location |
| Behavioural | Chain of Responsibility | object that can fulfil a request |
| | Command | when and how a request is fulfilled |
| | Interpreter | grammar and interpretation of a language |
| | Iterator | how an aggregate's elements are accessed and traversed |
| | Mediator | how and which objects interact with each other |
| | Memento | what private information is stored outside an object, and when |
| | Observer | number of objects that depend on another; how dependents stay up to date |
| | State | states of an object |
| | Strategy | an algorithm |
| | Template Method | steps of an algorithm |
| | Visitor | operations applicable to object(s) without changing their class(es) |

How to use it: write the sentence "the thing that must be able to change without editing the rest is ___" and find that phrase in the right-hand column. If no phrase matches, you probably do not need a pattern, or the variation is not yet understood.

## 4. The eight causes of redesign

Redesign costs you class redefinition, client changes and retesting. Each cause below is a way a design commits too early. The fix column is the move; the patterns column is where to look.

| # | Cause | What it looks like | Fix | Patterns |
|---|---|---|---|---|
| 1 | Creating an object by naming its class | `new ConcreteX(...)` in client code | create objects indirectly | Abstract Factory, Factory Method, Prototype |
| 2 | Dependence on specific operations | a request is satisfied in one hard-coded way | avoid hard-coded requests so the way they are satisfied can change at build or run time | Chain of Responsibility, Command |
| 3 | Dependence on hardware or software platform | OS or API calls and platform branches in application code | limit platform dependencies | Abstract Factory, Bridge |
| 4 | Dependence on object representation or implementation | clients know how an object is stored, located or implemented | hide that information so changes do not cascade | Abstract Factory, Bridge, Memento, Proxy |
| 5 | Algorithmic dependencies | an algorithm will be extended, optimised or replaced and dependants must change with it | isolate the algorithms likely to change | Builder, Iterator, Strategy, Template Method, Visitor |
| 6 | Tight coupling | classes cannot be reused alone; you cannot change a class without understanding many others | abstract coupling and layering | Abstract Factory, Bridge, Chain of Responsibility, Command, Facade, Mediator, Observer |
| 7 | Extending functionality by subclassing | every subclass has fixed overhead and needs deep parent knowledge; simple extensions multiply classes | composition and delegation; define one new class and compose it with existing ones | Bridge, Chain of Responsibility, Composite, Decorator, Observer, Strategy |
| 8 | Inability to alter classes conveniently | no source (third-party library), or a change would ripple through many subclasses | wrap or add operations from outside | Adapter, Decorator, Visitor |

Reverse index (derived from the table): Abstract Factory 1,3,4,6; Factory Method 1; Prototype 1; Chain of Responsibility 2,6,7; Command 2,6; Bridge 3,4,6,7; Memento 4; Proxy 4; Builder, Iterator, Template Method 5; Visitor 5,8; Strategy 5,7; Facade 6; Mediator 6; Observer 6,7; Composite 7; Decorator 7,8; Adapter 8.

Caveat from GoF: heavy use of composition and delegation makes a design harder to read than a static one. Use it where the flexibility is real.

## 5. Smell to cause to pattern lookup

Derived from GoF ch. 1 (distillation), the Lexi case study and the HF chapters. Treat each row as a hypothesis to test against section 7, not as an instruction.

| What you see in the code | Cause | First candidates |
|---|---|---|
| `new ConcreteX` scattered through client code; type-string `if/else` that instantiates | 1 | factory function or Simple Factory, Factory Method, Abstract Factory (creational.md) |
| Several related objects that must stay consistent (look and feel, region, vendor) | 1, 3 | Abstract Factory |
| A giant `switch` on request type; a button or menu that must know every operation | 2 | Command; Chain of Responsibility when the receiver is not known |
| `#ifdef PLATFORM`, direct OS or vendor API calls in application logic | 3 | Bridge, Abstract Factory, Adapter |
| Clients that know storage format, location or remote versus local | 4 | Proxy, Bridge, Memento |
| An algorithm inlined in a class that others depend on; it will have variants | 5 | Strategy, Template Method; Builder for construction; Iterator for traversal; Visitor for operations over a structure |
| Nothing can be reused alone; touching one class forces understanding many | 6 | Facade, Mediator, Observer, Command |
| Subclass per combination of features (`BorderedScrollableView`) | 7 | Decorator |
| Subclass per platform of every class in a hierarchy; two dimensions of variation | 7, 3 | Bridge |
| Adding a method to a superclass breaks unrelated subclasses; do-nothing overrides | 7 | Strategy (HF ch. 1) |
| One class must notify an open-ended set of dependants and calls them directly | 6 | Observer |
| Repeated `if (state == ...)` in every method of one class | none of the eight; HF ch. 10 | State |
| Subclasses copy the same step sequence with small differences | 5 | Template Method |
| Third-party class with the wrong interface that you cannot edit | 8 | Adapter; Decorator or Visitor to add behaviour |
| Client orchestrates many subsystem classes in a fixed order in several places | 6 | Facade |
| Tree handled with type checks at call sites | 7 | Composite; Visitor if operations keep growing |
| Index-based child access exposed in an interface; getters that return internal collections | 5 | Iterator |
| `dynamic_cast` or type switches in analysis code over a stable node set | 5 | Visitor (GoF ch. 2); with sum types, an exhaustive match instead |
| Interface of a core class bloating with unrelated operations | 5 | move the operations out via Visitor or Strategy |
| Memory blowup from very many near-identical objects | none of the eight | Flyweight |

## 6. The 23 intents, with classification and where to read more

Intent wording is condensed from GoF 1.4. "Cr / St / Be" is the purpose; "C / O" is class or object scope.

| Pattern | Cr/St/Be | C/O | Intent | Read |
|---|---|---|---|---|
| Abstract Factory | Cr | O | interface for creating families of related objects without naming concrete classes | creational.md |
| Builder | Cr | O | separate construction of a complex object from its representation so one process can build different representations | creational.md |
| Factory Method | Cr | C | interface for creating an object; subclasses decide which class | creational.md |
| Prototype | Cr | O | create objects by copying a prototypical instance | creational.md |
| Singleton | Cr | O | one instance, one access point | creational.md |
| Adapter | St | C and O | convert a class's interface into the one clients expect | structural.md |
| Bridge | St | O | decouple an abstraction from its implementation so both vary independently | structural.md |
| Composite | St | O | tree structures for part-whole hierarchies, uniform treatment | structural.md |
| Decorator | St | O | attach responsibilities dynamically; alternative to subclassing | structural.md |
| Facade | St | O | one higher-level interface to a subsystem | structural.md |
| Flyweight | St | O | share objects to support very many fine-grained ones | structural.md |
| Proxy | St | O | surrogate that controls access to another object | structural.md |
| Chain of Responsibility | Be | O | give more than one object a chance to handle a request | behavioral-1.md |
| Command | Be | O | request as an object: parameterise, queue, log, undo | behavioral-1.md |
| Interpreter | Be | C | grammar representation plus an interpreter for sentences | behavioral-1.md |
| Iterator | Be | O | sequential access without exposing representation | behavioral-1.md |
| Mediator | Be | O | object that encapsulates how a set of objects interact | behavioral-1.md |
| Memento | Be | O | capture and restore state without breaking encapsulation | behavioral-1.md |
| Observer | Be | O | one-to-many dependency with automatic notification | behavioral-2.md |
| State | Be | O | behaviour changes with internal state; object appears to change class | behavioral-2.md |
| Strategy | Be | O | family of interchangeable encapsulated algorithms | behavioral-2.md |
| Template Method | Be | C | algorithm skeleton, steps deferred to subclasses | behavioral-2.md |
| Visitor | Be | O | operation over the elements of a structure, added without changing their classes | behavioral-2.md |

The GoF guide to readers says a beginner should start with the simplest and most common: Abstract Factory, Adapter, Composite, Decorator, Factory Method, Observer, Strategy, Template Method. Large systems use nearly all of them. For how each looks with closures, generics and sum types, read modern-idioms.md.

Scope warning (GoF preface): the catalogue has no concurrency, distributed or real-time patterns, no domain-specific patterns, and nothing about building user interfaces or device drivers. If the problem is one of those, a pattern from this skill is the wrong tool; see `craft-concurrency` or the `arch-*` skills.

## 7. Selection procedure (step by step)

1. State the problem and its forces in two or three sentences: the goal, plus the constraints that make the obvious solution fail. A pattern is a solution to a problem in a context, and the forces are the goal and the constraints (HF ch. 13). If you cannot write this, stop; you do not yet know what you are choosing for.
2. Try the simple solution first. Ask whether a plain function, a parameter, a data table or one extra class meets the need. KISS comes before any catalogue lookup (HF ch. 13).
3. Name the variation point in the sentence form from section 3. Count the realised variants: two or more existing variants, or a firm, near-term second one, make the variation real. A hypothetical one does not (HF ch. 13: practical change, not hypothetical change).
4. Find the cause of redesign (section 4) and its candidate patterns, or look up the variation phrase in section 3. Write down two or three candidates.
5. Compare neighbours by intent, not by class diagram. Many patterns share a structure and differ in purpose. Use the neighbour tables in SKILL.md and the pattern files.
6. Read the Consequences of each remaining candidate. List the extra classes, layers and indirections it adds, and what becomes harder (for example, Abstract Factory makes adding a product kind hard; Visitor makes adding an element class hard).
7. Check the language. If a closure, a generic, an iterator protocol, a sum type with exhaustive match, or a module already does the job, the class-based pattern is probably unnecessary (modern-idioms.md; GoF ch. 1.1 says a pattern compensates for something the language does not give you directly).
8. Choose, and record the choice: one sentence naming the pattern, the variation point, and what you rejected. Put the pattern name in class names or comments (section 8, step 4).
9. If nothing fits, fall back on the principles (principles.md): encapsulate what varies, program to an interface, favour composition. HF ch. 1 says explicitly that when no pattern matches you reason from the principles.

If two candidates survive, the evolution rule for creational patterns (creational.md) generalises: start with the simpler, more local one and move to the more flexible one when the need shows up.

## 8. Application procedure (step by step)

From GoF 1.8, extended with HF ch. 13 and verification steps.

1. Read the pattern once for overview; confirm fit from its applicability and consequences sections.
2. Study its structure, participants and collaborations until you can draw the roles for your case.
3. Read a sample implementation.
4. Choose names from your application's domain that embed the participant name, for example `TeXLayoutStrategy`, `SimpleLayoutStrategy`, `GUIFactory`, `MotifFactory`. This makes the pattern visible to the next reader.
5. Define the classes: interfaces, inheritance, instance variables for data and for object references. Find and modify the existing classes the pattern affects.
6. Define application-specific operation names and keep naming conventions consistent (GoF's example: a `Create` prefix always marks a factory method).
7. Implement the operations, using the pattern's implementation notes for gotchas.
8. Verify (see SKILL.md "Verify"): add a variant by adding a class without editing existing code; a test injects a fake; the participants appear in the names.
9. Note any deviation from the canonical form in a comment. Patterns are guidelines, not laws; HF ch. 13 asks you to document how your version differs so readers still recognise it.

## 9. Inheritance, composition or generics for the variation point

GoF 1.6 gives three ways to compose behaviour. The table is a decision aid built from that discussion.

| If the variation is... | Use | Why | Typical patterns |
|---|---|---|---|
| chosen or changed at run time, or per object | composition and delegation | the reference can be replaced at run time; black-box reuse respects encapsulation | Strategy, State, Decorator, Bridge, Observer |
| fixed per type at build time, with sensible default behaviour to override | inheritance | static, simple, easy to override part of the behaviour | Template Method, Factory Method |
| a type or operation to be fixed at compile time, performance matters | parameterised types (generics, templates) | no run-time indirection | the sort-by-comparison example: Template Method, Strategy or a generic argument all work |

Costs to weigh. Inheritance is white-box reuse: the parent defines part of the subclass's representation, so changes in the parent force changes in subclasses, and you cannot change the inherited behaviour at run time. Composition creates more objects and makes behaviour depend on how objects relate instead of on one class, and it needs carefully designed interfaces. Delegation is "a good design choice only when it simplifies more than it complicates" (GoF 1.6). Use inheritance to make new components and composition to assemble them; the two work together.

HF ch. 1 adds a refinement: after the varying part is pulled out, inheritance is still fine for the stable part (the duck subclasses still inherit `display` and `swim`).

## 10. How much flexibility: application, toolkit or framework

GoF 1.6 distinguishes where flexibility pays.

| You are writing | Priorities | Patterns that help | Note |
|---|---|---|---|
| An application | internal reuse, maintainability, extension | those that cut dependencies and layer the system; composition and low coupling for extension | isolate only what actually varies |
| A toolkit (reusable general classes, you call it) | broad applicability without imposing an application design | avoid assumptions about clients | harder than an application because you do not know the clients |
| A framework (reusable design, it calls you) | design reuse; inversion of control | extension-point patterns: Template Method, Factory Method, Observer (HF ch. 8 Hollywood principle), Strategy (adaptation; GoF does not list patterns per kind of software) | hardest to design; clients are very sensitive to interface changes, so coupling matters most |

A framework contains several patterns; a pattern never contains a framework. Patterns are more abstract (only examples of a pattern can be embodied in code), smaller, and less specialised than frameworks. HF ch. 1 adds that patterns are not libraries: they are higher-level than libraries and you adapt them to your application.

## 11. Worked selections

### Lexi document editor (GoF ch. 2)

The method used seven times: state goals and constraints, show why the obvious design fails, encapsulate the concept that varies in an object, then name the pattern.

| Problem | What varies | Pattern | Core move |
|---|---|---|---|
| Uniform text and graphics in a document structure, simple and complex elements alike | structure and composition | Composite | common `Glyph` interface; recursive composition |
| Replaceable line-breaking algorithm | an algorithm | Strategy | `Compositor` objects, `Composition` as context |
| Add or remove borders and scrollers without class explosion | responsibilities | Decorator | single-child transparent enclosure with the same interface |
| Several look-and-feel standards, switchable at run time | families of products | Abstract Factory | one factory object creates the whole widget family |
| Several window systems | implementation | Bridge | `Window` hierarchy for applications, `WindowImp` hierarchy for window systems; a factory picks the imp |
| Operations from menus, buttons, keys; undo and redo | when and how a request is fulfilled | Command | request as object with execute and unexecute; history list with a "present" marker |
| Spell check, hyphenation, more analyses later; traversal | traversal; operations over a structure | Iterator, Visitor | iterator holds traversal state; visitor holds the analysis and uses double dispatch |

Lessons the chapter draws that carry over:
- Design the interface of a Strategy and its context broadly enough that adding a new algorithm changes neither interface.
- Decide who contains whom so that existing classes need no edits (the border contains the glyph, not the reverse). A decorator holds exactly one child, so embellishment stays separate from composition classes such as Row and Column.
- When abstracting several platforms, the interface is a dilemma between the intersection of features (weak) and the union (huge and unstable). Choose the commonly used middle plus what your clients actually need.
- Before choosing Visitor, ask which hierarchy changes more often. Visitor suits a stable element set with an open-ended set of operations; adding an element class forces a change in every visitor.
- Index-based access exposed in an interface is biased toward arrays; an iterator hides the storage, and each iterator has its own state, so two traversals can run at once.
- Subclass per combination (border times scroller), per request times widget (command), or per platform times window (bridge) are the three explosions; each has its own remedy.
- Let the command decide whether it is undoable (`Reversible`), so a no-op change leaves no undo entry; otherwise the user must undo N meaningless steps.
- Configure the concrete choice at one place at start-up (a registry from names to factories avoids linking platform code that does not exist on this platform).

### Ducks and pizzas (HF ch. 1, 4)

Ducks: adding `fly()` to a `Duck` superclass made rubber ducks fly. Overriding with do-nothing methods failed because every new subclass has to be inspected forever; interfaces for flying destroyed reuse because the flying code is copied into every flying class. Fix by principle: separate what varies (fly, quack) from what does not, express each as an interface with interchangeable classes, give `Duck` a reference to each, and add setters so the behaviour can change at run time. That arrangement is Strategy. The chapter's point is the order: principles first, pattern name last.

Pizzas: `orderPizza` mixed a stable process (prepare, bake, cut, box) with a varying part (which concrete pizza). Step 1 moved the `if/else` into a Simple Factory (an idiom). Franchising needed regional variants under a fixed process, which led to Factory Method: an abstract `createPizza` in `PizzaStore`, a subclass per region. Ingredient consistency across regions led to Abstract Factory: an ingredient factory per region injected into the pizzas, which also collapsed the duplicated per-region pizza classes into one class per kind. Each step answered one new requirement and no more.

## 12. Trigger phrases and the first candidates to examine

| The prompt or review says | Examine first |
|---|---|
| "make this pluggable / extensible / testable" | the variation point; Strategy, Abstract Factory, dependency injection |
| "support multiple X (platforms, vendors, formats, themes)" | Bridge, Abstract Factory, Adapter, Strategy |
| "avoid hard-coding the class" | creational.md |
| "we need undo", "queue these", "log and replay" | Command |
| "notify all the listeners", "update the UI when this changes" | Observer, then compound-and-mvc.md |
| "add logging/caching/retry/auth around this without changing callers" | Decorator, Proxy |
| "integrate this library with the wrong interface" | Adapter, Facade |
| "this class has a status field and a switch in every method" | State |
| "should this be a singleton / global?" | creational.md, Singleton entry |
| "too many subclasses" | Decorator, Bridge, Strategy |
| "is this over-engineered?", "needless abstraction", "single-implementation interface" | using-patterns-well.md |
| "express this with closures / generics / sum types" | modern-idioms.md |
