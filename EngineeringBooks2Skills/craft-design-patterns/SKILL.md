---
name: craft-design-patterns
description: Guides choosing, applying, adapting and removing object-oriented design patterns (the 23 GoF patterns, compound patterns, MVC) by starting from what varies and the cause of redesign, with the principles behind them and checks that show a pattern earns its cost. Use when a request or review names a pattern (strategy, factory, builder, singleton, observer, decorator, adapter, command, state, visitor, MVC), asks to make code extensible, pluggable or testable, or shows `new ConcreteClass` in clients, type switches, status-flag conditionals, subclass-per-combination growth, a wrong-interface library class, hand-rolled listeners or undo; also for choosing between near-neighbour patterns, expressing one with closures or sum types, or judging pattern over-engineering. Module depth and API shape belong to craft-module-design; refactoring mechanics to craft-refactoring.
---

# Design patterns: select, apply, verify, remove

## Purpose

Use this to decide whether a pattern is needed at all, which one fits, how to put it into the code in front of you, and how to prove it helps. The method comes from two books: start from what will vary (not from a pattern name), try the simplest solution first, pick by intent, read the consequences, apply with visible names, and verify by adding a variant without editing existing code. Patterns are tools for change, so every recommendation here is tied to a change you can name.

## Choose what applies

| Situation | Go to |
|---|---|
| "Which pattern should I use for X?" or the pattern is not named | the selection procedure below, then `references/selection-guide.md` |
| `new ConcreteX` in client code, a type-string `if/else` that instantiates, platform or vendor branches, "make creation pluggable" | `references/creational.md` |
| "Should this be a singleton / global?", lazy shared instance, thread-safe initialisation | `references/creational.md` section 8 |
| Behaviour that varies by subclass, do-nothing overrides, an algorithm to swap at run time | Strategy: `references/behavioral-2.md`; principles in `references/principles.md` |
| Subclass per feature combination; two independent dimensions in one hierarchy (shape by renderer, platform by window kind); need to add behaviour around an object; wrong-interface class; a subsystem that is hard to use; lazy, remote or access-controlled objects; a tree handled with type checks; very many near-identical objects | `references/structural.md` (Decorator, Bridge, Adapter, Facade, Proxy, Composite, Flyweight) |
| Undo or redo, queues, logs, macros, one action from several UIs; request routing; tangled peer communication; tiny DSL; traversal; snapshots | `references/behavioral-1.md` (Command, Chain of Responsibility, Mediator, Interpreter, Iterator, Memento) |
| Notify many dependants; status-flag conditionals in every method; shared step sequence; adding operations to a stable tree | `references/behavioral-2.md` (Observer, State, Template Method, Visitor) |
| UI layering, model reused by several views, "fat controller", several patterns stacked | `references/compound-and-mvc.md` |
| Review question: "is this over-engineered?", single-implementation interface, pattern for its own sake, removing or documenting a pattern, naming patterns in a PR | `references/using-patterns-well.md` |
| Review question: "too coupled?", "violates open/closed?", inheritance versus composition | `references/principles.md` |
| The language has closures, generics, iterators, sum types, modules or an injection container | `references/modern-idioms.md` |
| This does not apply: the code is small, has one use and no foreseeable second variant; a plain function, a parameter or a data table solves it; a language feature already provides the pattern | write the simple version; see "Proportion and limits" |
| This does not apply: module depth, information hiding, file layout, API shape | `craft-module-design` |
| This does not apply: moving code safely in steps, legacy code without tests | `craft-refactoring` (use this skill only to pick the target structure) |
| This does not apply: concurrency, distributed or real-time design | `craft-concurrency`, `arch-*`; the GoF catalogue excludes these, and the notes flag them as out of scope |

## How to apply

### A. Selection procedure

1. Write the problem and its forces in two or three sentences: the goal, plus the constraints that make the obvious solution fail. If you cannot, you are not ready to choose.
2. Try the simple solution first (a function, a parameter, a table, one more class, a language feature). Patterns buy flexibility with indirection (more classes, more layers), so take them only when something simpler fails.
3. Name the variation point as "the thing that must change without editing the rest is ___". Count realised variants. Two or more existing, or a firm near-term second one, make it real. A hypothetical one does not.
4. Map it: use the "what varies" table (selection-guide.md section 3) or the eight causes of redesign (section 4 there) to get two or three candidates.
5. Compare near neighbours by intent, not by class diagram (table below). Many patterns share a structure.
6. Read each candidate's consequences. List what it adds (classes, layers) and what it makes hard.
7. Check the language: if a closure, generic, iterator, sum type or module already does it, use that (modern-idioms.md).
8. Choose, and write one sentence recording the pattern, the variation point and the alternative you rejected.
9. If nothing fits, reason from the principles (P1 to P3 below) instead of forcing a pattern.

### B. What varies to pattern (condensed)

| The thing that must vary | Pattern |
|---|---|
| which concrete class gets created; a whole family of classes | Factory Method, Prototype; Abstract Factory |
| how a complex object is assembled, with several representations | Builder |
| the sole instance of a class (the number of instances, exactly one) | Singleton (with suspicion) |
| the interface a client sees; the interface of a subsystem | Adapter; Facade |
| implementation versus abstraction, independently | Bridge |
| structure of a part-whole tree | Composite |
| responsibilities added to one object without subclassing | Decorator |
| how an object is accessed or where it lives; storage cost of many objects | Proxy; Flyweight |
| who handles a request; when and how a request runs | Chain of Responsibility; Command |
| how elements are traversed; how objects interact; what state is saved | Iterator; Mediator; Memento |
| how many dependants and how they stay current | Observer |
| behaviour by internal state; an algorithm; the steps of an algorithm | State; Strategy; Template Method |
| operations over a structure without changing its classes | Visitor |
| grammar of a small language | Interpreter |

The 23 intents with scope and files are in selection-guide.md section 6.

### C. Near neighbours: choose by intent

| Pair or group | Decide by asking | Source |
|---|---|---|
| Strategy versus State | Who changes the behaviour? Strategy: the client picks and keeps it. State: the context moves itself through defined transitions and the client is mostly unaware. Same structure | HF ch. 10 |
| Adapter, Decorator, Facade, Proxy | Adapter changes the interface to match the client. Decorator keeps the interface and adds behaviour. Facade simplifies a subsystem. Proxy keeps the interface and controls access. How many classes are wrapped does not decide it | HF ch. 7, 11 |
| Decorator versus Strategy | Strategy swaps the algorithm inside an object (one at a time). Decorator wraps the object from outside, can stack many, and the wrapper is-a component | HF ch. 3 |
| Template Method versus Strategy | Inheritance with a fixed skeleton and hooks (more coupled, shares code) versus composition swapping a whole algorithm at run time | HF ch. 8 |
| Factory Method versus Abstract Factory | One product through a subclass (inheritance), versus a family through an injected factory object (composition); the second makes adding a product kind costly | HF ch. 4 |
| Abstract Factory versus Builder | Families returned at once, versus one complex product assembled in steps and returned at the end | GoF ch. 3 |
| Abstract Factory versus Prototype | Known classes with subclassing allowed, versus open-ended presets cloned from registered instances | GoF ch. 3 |
| Composite versus Decorator | Similar structure; Composite represents part-whole trees, Decorator adds responsibilities around one child | GoF ch. 1 |
| Bridge versus Adapter | Bridge is designed up front so two hierarchies vary independently; Adapter is after-the-fact to fit an existing class | GoF digest |
| Command versus function pointer or closure | Use an object when you need undo, history, serialisation or macros; a closure is enough for a plain callback. GoF ch. 2 rejects the bare function pointer for three reasons (no undo story, hard to attach state, hard to extend); the closure advice is a modern adaptation | GoF ch. 2; closure note inferred |
| Iterator versus Visitor | Iterator separates how to walk from what to do; Visitor holds the operation per element type | GoF ch. 2 |

More detail in each pattern file's neighbour sections.

### D. Inheritance, composition or generics

- Run-time change or per-object variation: composition and delegation (Strategy, State, Decorator, Bridge, Observer).
- Fixed per type with sensible defaults to override: inheritance (Template Method, Factory Method).
- A type or operation fixed at compile time where speed matters: generics.
- Inheritance is white-box reuse (the parent defines part of the child's representation, so parent changes ripple and run-time change is impossible). Composition is black-box reuse but adds objects and needs careful interfaces. Use inheritance to make new components and composition to assemble them.

### E. Applying a chosen pattern

1. Read its applicability and consequences once more; confirm.
2. Draw the roles for your case (participants and collaborations).
3. Name classes from your domain with the participant name in them (`TeXLayoutStrategy`, `MotifFactory`). Use one naming convention for operations (for example a `create` prefix for factory methods).
4. Make the interface of the varying part broad enough that adding a variant changes neither the interface nor the context (the Strategy lesson from the document-editor case study).
5. Put the choice of concrete class in one place (a composition root or a registry), so concrete names appear nowhere else.
6. Add the second variant at once, in a test if nowhere else, to prove the seam works.
7. Record any deviation from the canonical form in a comment.

### F. Principles at a glance

| # | Principle | Test |
|---|---|---|
| P1 | Separate what varies from what stays the same | A new requirement edits unrelated stable code: boundary is wrong |
| P2 | Program to an interface (supertype), not an implementation | Clients name concrete classes: introduce a factory or injection |
| P3 | Favor composition over inheritance | Do-nothing overrides, fixes repeated across siblings, behaviour changes needed at run time |
| P4 | Loosely coupled designs between interacting objects | Can each side be tested with a stub of the other? |
| P5 | Open for extension, closed for modification, at likely change points only | Can the next likely variant be added with new code only? |
| P6 | Depend on abstractions; high-level code does not import low-level concrete classes | Check the import direction |
| P7 | Least Knowledge: talk to immediate friends | Chains like `a.getB().getC().act()` |
| P8 | Hollywood: the high-level part calls the low-level part | Subclasses starting the flow by calling base internals |
| P9 | One reason to change per class | List "changes when ___"; more than one blank means split |

Details, costs, and how they conflict are in `references/principles.md`.

## Verify

Run these checks and show their output; do not describe them in the abstract.

Before applying:
1. Show the one-sentence problem with its forces, the simple alternative you considered, and why it fails.
2. Show the variation point and the variants (two realised, or the named near-term second). If there is only one, say so and justify the seam or drop the pattern.
3. State the consequences you accepted: classes added, indirection, what becomes harder.

After applying:
1. Add-a-variant test: add one more variant (or confirm the second one you wrote) by adding a class and registering it. Count the existing files that needed edits. The target is zero outside the composition root.
2. Dependency check: search for concrete class names where they should not appear. For creational patterns, `grep -rn "new ConcreteName"` (or the language's constructor syntax) should return only factories, the composition root and tests. For P6, no import from a high-level module to a concrete low-level one.
3. Fake-injection test: construct the client with a fake of the abstraction and exercise its logic with no real dependency.
4. Run the full test suite before and after; behaviour must be unchanged unless the task changed it.
5. Names: participants appear in class names or comments, and the pattern's name appears where a reader would look for it.
6. Count: classes and layers added versus conditionals, subclasses or duplicated blocks removed. Report both numbers.

Pattern-specific checks (condensed from each pattern's Verify list; the full list is in the pattern's reference file):

| Pattern | Observable check |
|---|---|
| Strategy | swap the strategy at run time and the next call changes output; the context has no concrete strategy names; a new strategy needs no edit to existing classes |
| Factory Method | a test subclass overrides the factory method to inject a fake; the base class names no concrete product; no factory method call in a base constructor |
| Abstract Factory | each concrete factory returns a mutually consistent family and never null; swapping the factory swaps all products; no casts on factory results |
| Builder | a new output representation is added without editing the director; the director names no product classes |
| Prototype | mutate a clone and the original is unchanged; the clone has the same dynamic type; resources are not cloned by accident |
| Singleton | N threads get the identical instance; tests can reset or replace it; nothing depends on initialisation order; a reason is given why injection is not enough |
| Observer | the subject imports no concrete observer; unsubscribe stops notifications; nothing relies on notification order |
| Decorator | wrapper forwards every method of the interface; order of wrapping tested where it matters; wrapping is done in one factory |
| State | every (state, event) pair is covered by a test or table; the context has no `if` or `switch` on state; adding a state touches the new class, the context's field or getter, and the transitions into it |
| Command | execute then undo restores the prior state for each reversible command; no-op commands are not recorded |
| Visitor | the element set is stable; a new operation is one new class or function; the compiler or a test flags a missing case |
| Adapter | the client compiles against the target interface only; the target's contract tests pass against the adapter; unsupported operations fail loudly |
| Bridge | add an implementor without touching the abstraction hierarchy, and a refined abstraction without touching implementors; clients never name an implementor |
| Composite | an operation on the root equals the aggregate over the leaves, tested at depth three and with an empty composite; adding a nested composite needs no client change |
| Facade | clients import only the facade; subsystem classes do not import it; swapping a subsystem part edits only the facade |
| Flyweight | a heap profile before and after shows the saving; the same intrinsic key returns the same instance; flyweights are immutable and nothing compares them by identity |
| Proxy | the contract tests of the real subject pass against the proxy; a lazy subject is created once and not before first use; denied calls, including unknown methods, are tested |
| Chain of Responsibility | one request per kind plus an unknown kind; the unknown kind ends in an explicit failure or default, not silence |
| Interpreter | a golden test per grammar rule; `parse(print(ast))` equals the tree; deep or non-terminating input is bounded |
| Iterator | two live iterators on one collection do not interfere; mutation during iteration has a tested behaviour; resources are released on early exit |
| Mediator | colleagues are tested against a fake mediator; no colleague imports another; the mediator holds interaction rules, not domain logic |
| Memento | capture, mutate, restore gives a value-equal state; the snapshot does not alias mutable state; history size is bounded |
| Template Method | the template method is final or sealed; a minimal subclass records the call order; cleanup runs when a step throws |
| MVC | the model module has no UI imports; two views attach to one model; swapping the controller needs no view edit |

Evidence to give the user: the problem sentence, the chosen pattern and variation point, the classes added and removed, the add-a-variant and fake-injection results, the test run, and the cost accepted.

Done means:
- The problem and forces are stated and the simple alternative is explained.
- A real variation point exists and at least two variants are in the code or the tests.
- Adding a variant needs new code only (zero edits to existing classes beyond registration).
- Concrete class names appear only in factories or the composition root.
- Tests pass, including a fake-injection test.
- The pattern is visible in names, and any deviation is documented.
- The cost is stated and the pattern still pays for itself.

## Proportion and limits

- Cost: every pattern adds classes, layers and indirection (complexity and sometimes inefficiency). Only a real, current or firmly expected change justifies it. "If you don't need it now, don't do it now."
- When to build the seam early: the requirement names a second variant, or the variation sits at an interface that is costly to change later (a published API, a persisted format, a platform boundary). Otherwise write the simple code and refactor toward the pattern when pressure appears (repeated conditionals, a third copy, a subclass explosion).
- Contested: "anticipate variation" (HF ch. 1) versus "wait for pain" (GoF ch. 6, HF ch. 13). Rule for deciding: use named, practical change as the trigger, not hypothetical change.
- Contested: Singleton. GoF presents benefits only; HF lists coupling, SRP and class-loader problems; the later consensus (marked inferred in the notes) calls it hidden global state. Default to one object created at the composition root and injected.
- Contested: Open-Closed and Dependency Inversion guidelines. HF itself says do not apply them everywhere and that most programs violate its DIP guidelines. Apply at likely change points.
- Contested: Composite transparency versus safety, and Template Method inheritance versus Strategy composition. Decide by whether misuse should fail at compile time or at run time, and whether the variation must change at run time.
- Language: GoF says a pattern compensates for something the language lacks. Closures replace Strategy, Command and Template Method scaffolding, iterators and generators replace Iterator, sum types with exhaustive matching replace Visitor and often State and Interpreter, modules replace Singleton and some Facades, injection replaces most creational patterns. Keep the class form when you need history, serialisation, several operations on one object, an open set of cases, or when a framework expects it. Details in `references/modern-idioms.md`.
- Dated: examples are Smalltalk, C++ and Java; the catalogue excludes concurrency, distributed and domain-specific patterns. The principles last longer than the scaffolding.
- Removing a pattern is legitimate when its flexibility is unused (one implementation, forwarding layers, no change request it made cheaper). See `references/using-patterns-well.md`.

## References

- `references/selection-guide.md`: read first when starting from a requirement or a code smell; has the what-varies table, the eight causes of redesign, the smell lookup, the 23 intents, and the selection and application procedures with worked examples.
- `references/principles.md`: read for every named design principle (P1 to P9 and smaller ideas), their costs, how to check them in code, and how they conflict.
- `references/creational.md`: read for Simple Factory, Factory Method, Abstract Factory, Builder, Prototype, Singleton, and injection as the alternative; includes the decision table and verification.
- `references/structural.md`: read for Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy and the neighbour comparisons.
- `references/behavioral-1.md`: read for Chain of Responsibility, Command, Interpreter, Iterator, Mediator, Memento.
- `references/behavioral-2.md`: read for Observer, State, Strategy, Template Method, Visitor and the behavioural comparison discussion.
- `references/modern-idioms.md`: read when the language has first-class functions, closures, generics or sum types, to see each pattern in that form and when the class form is still right.
- `references/compound-and-mvc.md`: read when several patterns are combined, when designing or reviewing MVC-style UI structure, or when asked whether a combination is a "compound pattern".
- `references/using-patterns-well.md`: read when judging over-engineering, introducing or removing a pattern, refactoring toward one, reviewing, documenting, or naming patterns in code and PRs.

## Sources

- Gamma, Helm, Johnson, Vlissides, Design Patterns (GoF, 1994): ch. 1 Introduction (what a pattern is, catalogue, selection, principles, causes of redesign), ch. 2 case study (document editor), ch. 3 Creational Patterns (opening, Abstract Factory, Builder, Factory Method, Prototype, Singleton, discussion), ch. 6 Conclusion.
- Freeman and Robson, Head First Design Patterns 2e: ch. 1 Strategy and the first principles, ch. 4 Factory (Simple Factory, Factory Method, Dependency Inversion, Abstract Factory), ch. 5 Singleton, ch. 12 Compound Patterns and MVC, ch. 13 Better Living with Patterns; principles from ch. 2, 3, 7, 8, 9 via the book digests; the leftover-patterns appendix for Builder and Prototype.
- Behavioural and structural pattern content (Writer B's files) comes from the remaining chapters of both books.
