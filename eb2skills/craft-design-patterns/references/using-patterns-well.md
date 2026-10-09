# Using patterns well: proportion, introduction, removal, vocabulary

Sources: HF ch. 13 (Better Living with Patterns), ch. 1 (meta-claims), ch. 12 Q&A; GoF ch. 1 (1.1, 1.8), ch. 6 (Conclusion), ch. 3 discussion. Items marked "(adaptation)" or "(inferred)" are not claims of the books.

Contents
1. What counts as a pattern
2. When to introduce a pattern (procedure)
3. When a pattern earns its place even though something simpler works
4. Refactoring toward patterns
5. Removing a pattern
6. Pattern-itis and its symptoms
7. Anti-patterns
8. Shared vocabulary: how to use pattern names
9. Beginner, intermediate, Zen
10. Reviewing a design for pattern use (checklist)
11. Organising and finding patterns
12. Limits of the material

## 1. What counts as a pattern

Definition (HF ch. 13): a pattern is a solution to a problem in a context.
- Context: the situation in which it applies; it must recur.
- Problem: the goal plus the constraints present in the context.
- Solution: a general design anyone can apply that resolves the goal and the constraints.
- Forces: the pattern community's word for goal plus constraints. A pattern is useful only when the solution balances both sides.

The definition is necessary but not sufficient. The book's counter-example: locking your keys in the car and breaking a window to get to work fits problem, context and solution, but is not a pattern, because it is not a recurring problem with a reusable solution, it is not described so that others can apply it, and it has no name. A real pattern is recurring, transferable, named and balances its forces.

GoF's four essential elements (1.1): name, problem, solution (a template, not a concrete design or implementation), consequences. Consequences are often unvoiced but critical for evaluating alternatives: space and time, language and implementation issues, and the effect on flexibility, extensibility and portability.

Rule of Three (HF ch. 13): you do not have a pattern until it has been applied successfully in at least three real-world solutions. GoF included only designs used more than once in different systems.

What patterns are not: not libraries or frameworks (they are higher-level and you adapt them), not a method (they supplement design methods and are most useful in turning an analysis model into an implementation model, because a flexible design contains objects with no real-world counterpart), not a complete language (GoF concedes its catalogue is not an Alexandrian pattern language), and not laws. Patterns are guidelines you may alter, as long as you document how your version differs.

Level of abstraction: patterns are not linked lists or hash tables (reusable as-is in a class), and not whole-application designs. They are "descriptions of communicating objects and classes that are customized to solve a general design problem in a particular context" (GoF 1.1). One person's pattern is another's primitive.

Language dependence (GoF 1.1): a pattern compensates for something the language does not give you directly. The catalogue assumed Smalltalk and C++. In a procedural language, inheritance and polymorphism would themselves be patterns; multi-methods reduce the need for Visitor. Richer language features shrink or absorb patterns (see modern-idioms.md).

## 2. When to introduce a pattern (procedure)

HF ch. 13 gives a five-step test; the extra checks are drawn from the chapter's review questions and its guru advice (partly inferred in the notes).

1. Confirm a simple solution will not meet the need. Consider a plain function, a parameter, a lookup table, one more class, or a language feature first. KISS is the goal; the aim is never to apply a pattern.
2. List the problem and its constraints (the forces) in writing.
3. Match it to a pattern you know, or survey candidates through their intent and applicability sections. Use selection-guide.md.
4. Check that the consequences are livable and look at the effect on the rest of the design: extra classes, extra layers (complexity and some inefficiency), what becomes hard to change.
5. Then apply it, using the application procedure in selection-guide.md.

Extra checks:
- Is the variation real? Two realised variants or a firm near-term second one. A Strategy, factory or Abstract Factory with one implementation is a smell (beginner mind).
- Does the pattern name the concrete change request it makes cheaper? "In case we need it" is not an answer.
- Will the next maintainer understand the design faster with the pattern than without?

Guideline from the chapter's guru: start from principles, write the simplest code that does the job, and let patterns emerge. Introduce a pattern when you are sure it is needed for a problem in the design, or quite sure it is needed to meet a future requirement change.

"If you don't need it now, don't do it now." Do not build architectures ready for change from every direction; hypothetical reasons only add complexity. The GoF authors' advice, as HF reports it: Helm, aim for practical extensibility, not hypothetical generality; Johnson, go for simplicity and if a simpler solution without a pattern exists, take it; Gamma, patterns are tools not rules, so tweak and adapt them.

## 3. When a pattern earns its place even though something simpler works

One case (HF ch. 13): when you expect aspects of the system to vary, meaning an identified area of change. Count only practical change that is likely to happen.

GoF ch. 6 adds a lifecycle view (Foote). If analysis shows that a dimension will change, such as platform, algorithm or look and feel, design for it early. Otherwise do not introduce a pattern speculatively in a prototype; wait for the pain of the expansionary phase (section 4) and refactor toward the pattern.

How to decide in a concrete case (adaptation of those two statements):

| Signal | Action |
|---|---|
| The requirement or a stakeholder names a second variant, or the product is already shipping in two environments | build the seam now |
| The variation sits in an interface that is expensive to change later (a published API, a persisted format, a plug-in boundary) | build the seam now |
| You are guessing at what might change | write the simple version and note the likely seam in a comment |
| The same conditional or `new` appears for the third time | refactor toward the pattern now |

## 4. Refactoring toward patterns

GoF ch. 6 (Foote's cycle):
1. Prototyping phase: class hierarchies mirror the problem domain; reuse is white-box, by inheritance.
2. Expansionary phase: new requirements add classes, operations and hierarchies until the software becomes inflexible; hierarchies no longer match any domain; classes accumulate unrelated operations and variables.
3. Consolidating phase: refactoring splits classes into special- and general-purpose parts, moves operations up and down, rationalises interfaces, often replaces inheritance with composition so black-box reuse replaces white-box reuse. Frameworks often emerge.

The cycle is unavoidable and repeating. Patterns capture the structures that result from refactoring: using them early prevents later refactoring, and if you only recognise the fit afterwards, the pattern is the target of the refactoring.

Directions the books name:
- Inheritance (white-box) toward composition and delegation (black-box).
- Domain-mirroring hierarchies toward a general/special-purpose split.
- Conditionals toward polymorphic objects (State, Strategy).
- Concrete `new` scattered in code toward factories.

HF ch. 13: "Refactoring time is patterns time." Treat these as signals: repeated conditionals on the same field, concrete `new` scattered across code, copy-pasted variation.

| Signal | Likely target | Where |
|---|---|---|
| `if (state == ...)` in several methods | State | behavioral-2.md |
| `new Concrete` selected by a type string in business logic | Simple Factory or Factory Method | creational.md |
| Same step sequence copied between subclasses | Template Method | behavioral-2.md |
| Subclass per feature combination | Decorator | structural.md |
| Switch on request type in the invoker | Command | behavioral-1.md |
| Direct calls to concrete listeners | Observer | behavioral-2.md |
| Platform branches in application logic | Bridge or Abstract Factory | structural.md, creational.md |

For the safe mechanics of moving code in small steps with tests (extract class, replace conditional with polymorphism, and so on), use `craft-refactoring`. Write a characterisation test before changing legacy code; this skill tells you the target, that one tells you how to get there.

Ordering advice (adaptation): extract the interface first with a single implementation, move the callers to the interface, then add the second implementation. Each step leaves the tests green.

## 5. Removing a pattern

HF ch. 13: "No one ever talks about when to remove a pattern." Remove it when the system has become complex and the planned flexibility is not needed, that is, when a simpler solution without the pattern would be better.

Signals (derived from the checklist in the chapter):
- One implementation and no variation in sight.
- Layers of indirection that carry no behaviour (a forwarding wrapper, a factory that returns one class).
- A Decorator chain deeper than the behaviour needs.
- A deviating implementation still labelled with the canonical name without a note.
- A Singleton introduced by reflex, or a Facade nobody uses.
- Nobody on the team can say which change request the pattern made cheaper.

Procedure (adaptation; use `craft-refactoring` for the mechanics):
1. Confirm with the history and the roadmap that no second variant is planned.
2. Cover the behaviour with tests at the level of the public interface.
3. Inline the indirection one layer at a time: replace the interface with the single concrete class, replace the factory call with the constructor, fold the wrapper into the wrapped class, flatten the hierarchy.
4. Keep the tests green after each step.
5. Delete what is now unused and record the decision in the commit message or design note, so the next person does not reintroduce it.

Periodically look for patterns that no longer pay for themselves (HF decision procedure, step 6). Removal is a design activity, not an admission of failure.

## 6. Pattern-itis and its symptoms

HF ch. 1 calls it "Pattern Fever" (using patterns for Hello World). Over-use produces over-engineered code. The downsides of patterns the book lists: additional classes and objects, more layers (complexity and inefficiency), and sometimes outright overkill when design principles alone give a simpler solution. In that case use the simpler solution. The upsides: time-tested, documented, recognised by other developers.

GoF's own warning (1.8): patterns buy flexibility with extra levels of indirection, which complicates the design and may cost performance; apply them only when the flexibility is actually needed, and use the consequences sections to weigh benefits and liabilities.

Smell list:
- A pattern for "Hello World": factory, strategy or observer around code with one use.
- A Singleton by reflex (HF: "Maybe I need a Singleton here" is intermediate-level thinking).
- A single-implementation interface plus a factory for it, with no test seam as reason.
- Deep Decorator or wrapper chains whose behaviour fits in one function.
- Pattern names forced into class names with no matching structure.
- A "compound pattern" claimed for a one-off combination (compound-and-mvc.md).
- Treating Open-Closed as a goal everywhere (HF: wasteful, hard-to-understand code).
- Inheritance replaced by composition everywhere regardless of whether the behaviour varies (GoF: delegation is good only when it simplifies more than it complicates).

The same failure appears in the books' own examples: the duck simulator's combination of six patterns is "forced and artificial", with parts that are "big-time overkill" (HF ch. 12 Q&A). Designing by "taking a problem and applying patterns until you have a solution" is wrong.

## 7. Anti-patterns

Definition (HF ch. 13): an anti-pattern tells you how to go from a problem to a bad solution. Documenting recurring bad solutions prevents repeating them.

A complete anti-pattern description must:
1. Say why the bad solution is attractive (otherwise no one would choose it).
2. Say why it is bad in the long term.
3. Point to other applicable patterns or a refactored solution.

It has a name, problem, context, forces, supposed solution, refactored solution and examples. Types: development, object-oriented, organisational, domain-specific.

Worked example, Golden Hammer: problem, choosing technologies, with the belief that one technology must dominate; context, a new system that does not fit the familiar technology; forces, a team committed to what it knows, unfamiliar technology seen as risky, easy estimates with the familiar; supposed solution, use the familiar technology anyway, obsessively; refactored solution, expand knowledge through training and study groups; example, keeping a homegrown cache when open-source ones exist. It is also a description of the failure mode this whole reference warns about for patterns themselves.

Use when reviewing: for each smell you flag, say why someone would have chosen it (the attraction), what it costs later, and what to do instead. A review comment with all three is usable; a comment that only says "anti-pattern" is not.

Other pattern domains exist beyond GoF's (HF "zoo"): architectural, application (MVC sometimes passes for one), domain-specific (concurrent, real-time), enterprise, business process, user-interface, organisational. If the problem lies there, other skills apply (`arch-*`, `craft-concurrency`).

## 8. Shared vocabulary: how to use pattern names

Naming a pattern conveys a whole design with its qualities and constraints. HF's example: a long, rambling description of "a broadcast class that keeps track of listeners" versus the word Observer. GoF (6.1): patterns raise the level of discussion above notation and language, make a system seem less complex, and let you describe a system as the sequence of patterns applied. GoF's authors say they use patterns in "arguably naive" ways: to pick class names, to think about and teach design, and to describe designs.

Where to use the vocabulary (HF's five ways):
1. Design meetings: stay in the design longer, avoid bogging down in implementation detail.
2. With other developers.
3. Architecture documentation: less text, clearer picture.
4. Code comments and naming conventions: put participant names into class names (`TeXLayoutStrategy`, `MotifFactory`) and say in a comment which pattern a group of classes forms.
5. Groups of interested developers (study groups, talks).

Rules for good use (adaptation, consistent with the books):
- Use the name when the structure and intent match. If you deviate, say how in one line ("Observer, but with a pull-style update and no unsubscribe") so readers do not assume the canonical form.
- When writing a pull-request description or design note, give the pattern, the variation point it serves, and the alternative you rejected.
- Do not use a name as decoration. A `Factory` suffix on a class that is not a factory misleads.
- Say the intent, not just the structure: Strategy and State have the same structure and differ in intent, so a name settles the question only if it is the right one. See behavioral-2.md.

## 9. Beginner, intermediate, Zen

| Stage | Behaviour (HF ch. 13) | Failure mode |
|---|---|---|
| Beginner | uses patterns everywhere ("I need a pattern for Hello World"); good for practice | believes more patterns means better design |
| Intermediate | sees where patterns are and are not needed; starts to adapt them | still fits "square patterns into round holes" ("Maybe I need a Singleton here") |
| Zen | sees patterns where they fit naturally; looks for the simple solution; thinks in principles and trade-offs; understands subtle differences in intent between related patterns; remains a beginner mind | none; does not let pattern knowledge dominate decisions |

Use this as a self-check before you add a pattern: which voice is writing this?

## 10. Reviewing a design for pattern use (checklist)

Ask these and expect observable answers. (Derived from HF ch. 13's review questions and GoF ch. 6's takeaways; partly inferred in the notes.)

1. What is the problem and what are the forces? One sentence each.
2. What is the simplest solution, and why does it fail? Name the failing requirement.
3. Which pattern, which variation point (Table 1.2 phrase), which realised variants?
4. What are the consequences you accepted (extra classes, indirection, restricted extension) and are they stated?
5. Does the code show the pattern (names, comments) and does it match the intent? If it deviates, is the deviation noted?
6. Can a variant be added by adding a class without editing existing code? Show it.
7. Can the pattern be tested with a fake? Show it.
8. Is any part of the pattern dead (unused variant, empty hook, forwarding layer)? Remove it.
9. Would a new teammate understand the design faster with the pattern than without?
10. If the language has a feature that replaces the pattern (closure, iterator protocol, sum type, module), is the class version still better, and why? (modern-idioms.md)

Evidence to give the user: the one-sentence problem, the pattern and variation point, the list of classes added and removed, the results of the add-a-variant and fake-injection checks, and the cost you accepted.

## 11. Organising and finding patterns

- By purpose (GoF): creational (object instantiation), structural (composing classes or objects into larger structures), behavioural (how classes and objects interact and distribute responsibility). The classification helps you compare a member to its group and narrow a search. Many patterns fit more than one; the intent is often the key to which group a pattern belongs to (Decorator is structural although it adds behaviour, because its focus is dynamic composition by wrapping).
- By scope (GoF): class patterns (inheritance, fixed at compile time: Template Method, Factory Method, Adapter class form, Interpreter) and object patterns (composition, established at run time; the majority).
- Other groupings: used together, alternatives to each other, similar structure with different intent.
- Workflow the book recommends for a catalogue: get familiar with all patterns and their relationships; when a need arises, read motivation and applicability to confirm fit; review consequences for unintended effects; read structure and participants and work it into the design with alterations; then read implementation notes and sample code for gotchas.
- Finding relevant patterns is nearly impossible without practical experience (GoF ch. 6). Read the catalogue before you need it.

## 12. Limits of the material

- Dated: examples are Smalltalk, C++ and Java from 1994 and 2020. The principles survive; much of the class scaffolding is absorbed by language features today.
- Reference lists and links in the books are dated and not reproduced here.
- Singleton is the pattern where the later consensus most clearly disagrees with the book's original presentation (creational.md, section 8).
- The books do not give measured evidence that patterns reduce defects or cost. The justification offered is experience reuse, shared vocabulary and the trade-offs the pattern makes explicit. Treat the claims as heuristics and check them against the code in front of you.
