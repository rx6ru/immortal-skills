# Smells to refactorings (Refactoring 2e ch. 3)

Contents
- How to use a smell
- Lookup table (all 24 smells)
- Per-smell entries: recognise, first move, cautions, check after
- Pairs that pull against each other
- Which move first
- Cross-references from the Clean Code case studies

## How to use a smell

A smell says "look here"; it does not prove a defect. The authors refuse numeric thresholds ("no set of metrics rivals informed human intuition"), so any number an agent applies (function length, parameter count) is a local convention, not from the book. Read the lookup table, find the nearest smell, try the listed refactorings, and judge cost against benefit. Many smells are faint. The 24 here include one change from the first edition: "Switch Statements" became **Repeated Switches**.

Knowing how to refactor (mechanics) is not knowing when. Smells are the when. A smell only justifies action when the code is on your path: you must change it, understand it, or you keep tripping over it (see "when to refactor" in `workflow-and-safety.md`).

## Lookup table

| Smell | Recognise it by | Refactorings |
|---|---|---|
| Mysterious Name | You must puzzle over what it does or how to use it; cannot think of a good name | Change Function Declaration (rename), Rename Variable, Rename Field |
| Duplicated Code | Same structure in more than one place | Extract Function; Slide Statements first for similar-but-not-identical; Pull Up Method for sibling subclasses |
| Long Function | Long; you feel the need to comment a block; many params/temps block extraction | Extract Function; Replace Temp with Query; Introduce Parameter Object; Preserve Whole Object; Replace Function with Command; Decompose Conditional; Replace Conditional with Polymorphism; Split Loop |
| Long Parameter List | Many parameters; confusing | Replace Parameter with Query; Preserve Whole Object; Introduce Parameter Object; Remove Flag Argument; Combine Functions into Class |
| Global Data | Data modifiable from anywhere; no way to find who touched it | Encapsulate Variable, then narrow scope into a class or module |
| Mutable Data | Updates here break assumptions there | Encapsulate Variable; Split Variable; Slide Statements + Extract Function; Separate Query from Modifier; Remove Setting Method; Replace Derived Variable with Query; Combine Functions into Class/Transform; Change Reference to Value |
| Divergent Change | One module changed in different ways for different reasons | Split Phase; Move Function; Extract Function; Extract Class |
| Shotgun Surgery | One change needs many small edits across many modules | Move Function; Move Field; Combine Functions into Class/Transform; Split Phase; Inline Function/Inline Class first |
| Feature Envy | A function talks more to another module's data than its own | Move Function; Extract Function on the envious part, then move |
| Data Clumps | Same 3-4 items appear together in many places | Extract Class; Introduce Parameter Object; Preserve Whole Object |
| Primitive Obsession | Money, ranges, phone numbers as bare numbers/strings | Replace Primitive with Object; Replace Type Code with Subclasses + Replace Conditional with Polymorphism; Extract Class + Introduce Parameter Object |
| Repeated Switches | The same switch or if/else cascade on the same condition in several places | Replace Conditional with Polymorphism |
| Loops | Loops where a pipeline would show the filter and map steps | Replace Loop with Pipeline |
| Lazy Element | Function named as its body reads; class that is one simple function | Inline Function; Inline Class; Collapse Hierarchy |
| Speculative Generality | Hooks, special cases, abstract classes, params for "someday"; only tests use it | Collapse Hierarchy; Inline Function; Inline Class; Change Function Declaration; Remove Dead Code |
| Temporary Field | A field set only in some circumstances | Extract Class; Move Function; Introduce Special Case |
| Message Chains | `a.getB().getC().getD()` in a client | Hide Delegate; or Extract Function on the user of the end object + Move Function down the chain |
| Middle Man | Half a class's methods just delegate | Remove Middle Man; Inline Function; Replace Superclass/Subclass with Delegate |
| Insider Trading | Modules trade too much data; subclasses know parents' internals | Move Function; Move Field; third module for shared interest; Hide Delegate; Replace Subclass/Superclass with Delegate |
| Large Class | Too many fields (duplication follows) or too much code | Extract Class; Extract Superclass; Replace Type Code with Subclasses |
| Alternative Classes with Different Interfaces | Two substitutable classes, different signatures | Change Function Declaration; Move Function; Extract Superclass |
| Data Class | Fields plus accessors only; others manipulate them in detail | Encapsulate Record; Remove Setting Method; Move Function; Extract Function then move; Split Phase result records are the exception |
| Refused Bequest | Subclass does not want inherited members | Push Down Method/Field (only if it causes problems); Replace Subclass/Superclass with Delegate if the interface is refused |
| Comments | Comments as deodorant for bad code | Extract Function; Change Function Declaration; Introduce Assertion |

Where to find mechanics: `catalog-basic.md` (extract, inline, change declaration, parameter object, class/transform, split phase), `catalog-encapsulation.md`, `catalog-moving-features.md`, `catalog-organizing-data.md`, `catalog-conditionals.md`, `catalog-apis.md`, `catalog-inheritance.md`.

## Per-smell entries

**Mysterious Name.** Naming is one of the two hard things, so renames are the commonest refactorings. If you cannot find a good name, that often signals a deeper design problem; wrestling with the name has led to significant simplification. Check after: a newcomer can say what it does without opening the body (inferred).

**Duplicated Code.** Every reader must compare copies for subtle differences, and every change must find all copies. Identical expression in two methods of a class: Extract Function and call from both. Similar but not identical: Slide Statements so similar parts sit together, then extract. Sibling subclasses: Pull Up Method. Check after: one definition; a change goes in one place.

**Long Function.** The longest-lived programs have short functions. Indirection pays off (explanation, sharing, choice) only through small functions, and call overhead is no longer a reason to avoid them; good names reduce the need to read bodies. Whenever you feel the need to comment a block, write a function named for the intention (what, not how), even if the call is longer than the code. Finding candidates: comments; conditionals (Decompose Conditional); a big switch (a function call per leg); loops (extract the loop and body; if you cannot name it, it probably does two things, so Split Loop). Obstacle of many params and temps: Replace Temp with Query, Introduce Parameter Object, Preserve Whole Object; still stuck, Replace Function with Command. Repeated switch on the same condition: Replace Conditional with Polymorphism.

**Long Parameter List.** Decision order: a parameter obtainable by asking another parameter: Replace Parameter with Query. Many values pulled from one structure: Preserve Whole Object. Parameters that always travel together: Introduce Parameter Object. A parameter that picks behaviour: Remove Flag Argument. Several functions share several parameter values: Combine Functions into Class (a set of partially applied functions).

**Global Data.** "Spooky action from a distance": data any code can change, with no way to find who did. Forms: global variables, class variables, singletons. First move always Encapsulate Variable, then restrict scope inside a class or module. Mutable globals are the nasty case; globals guaranteed immutable after start-up are relatively safe if the language enforces it. "The difference between a poison and something benign is the dose": even small doses stay encapsulated.

**Mutable Data.** Risk grows with scope; a variable alive for two lines is fine. Prefer never mutating (return copies) where the language makes that practical. Otherwise: Encapsulate Variable so updates go through narrow functions; Split Variable if it stores different things; Slide Statements + Extract Function to separate side-effect-free code from the update; Separate Query from Modifier; Remove Setting Method early (finding setter users exposes scope-reduction chances); Replace Derived Variable with Query when it can be computed; Change Reference to Value for structures. Check after: searching for writes finds only narrow functions.

**Divergent Change.** The test: "I change these three functions for every new database, these four for every new instrument" means two contexts are mixed. Boundaries are unclear early; you often discover the smell only after adding a few of each. Tool by shape: data flows in sequence (read from DB, then process): Split Phase with a data structure between; back-and-forth: create modules and Move Function; functions that mix both: Extract Function first; classes: Extract Class. Check after: a change in one context touches no code of the other.

**Shotgun Surgery.** The opposite of divergent change: one change causes many small edits across modules, and one is easy to miss. Gather with Move Function/Move Field; functions on similar data: Combine Functions into Class; functions that enrich a structure: Combine Functions into Transform; Split Phase. Tactic: inline first (Inline Function, Inline Class) to pull badly separated logic together, accept a temporary Long Function or Large Class, then extract sensibly ("not afraid of creating something large as an intermediate step"). Check after: a representative change touches one module.

**Feature Envy.** Modularising maximises interaction inside a zone and minimises it between zones. A function spending more time with another module: Move Function. Only part envious: Extract Function on that part, then move. Uses several modules: put it with the module that holds most of the data. Exceptions are deliberate: Strategy, Visitor and Self Delegation separate behaviour from data to fight Divergent Change. Do not "fix" a clear Strategy by moving behaviour back into data. Rule of thumb: put together what changes together.

**Data Clumps.** The same 3-4 items as fields in a couple of classes or parameters in many signatures. Order: Extract Class on the fields, then Introduce Parameter Object or Preserve Whole Object on signatures. Using only some of the new object's fields is fine as long as you replace two or more. Test: delete one value; if the others stop making sense, an object is waiting to be born. Prefer a class to a bare record: a class invites behaviour, which exposes Feature Envy.

**Primitive Obsession.** Reluctance to create domain types: money as a number, quantities ignoring units, `a < upper && a > lower`, a phone number as a string. Replace Primitive with Object; a primitive that is a type code driving conditionals: Replace Type Code with Subclasses then Replace Conditional with Polymorphism; clumps of primitives: Extract Class + Introduce Parameter Object.

**Repeated Switches.** A single switch is not a smell (the authors are "never unconditionally opposed to the conditional"). The smell is the same cascade in several places, so adding a case means finding all of them. Replace Conditional with Polymorphism. Check after: no switch on that condition outside the factory.

**Loops.** With first-class functions widely supported, pipelines show which elements are included and what is done to them. Replace Loop with Pipeline. Where the language lacks closures a loop may be the idiomatic form (inferred).

**Lazy Element.** A function named as its body reads, a class that is one simple function, something expected to grow that never did, or a class downsized by other refactorings. "Die with dignity": Inline Function, Inline Class, Collapse Hierarchy.

**Speculative Generality.** "I think we'll need this someday" produces hooks and special cases that make code harder to understand. If the machinery were used it would be worth it; if not, remove it. Signal: the only users are tests. Delete those tests too and Remove Dead Code.

**Temporary Field.** A field set only in some circumstances; readers expect every field to be used. Extract Class to give the orphans a home, Move Function for the code that concerns them, Introduce Special Case to remove the conditional for invalid cases.

**Message Chains.** The client is coupled to the navigation structure. Hide Delegate at some point in the chain, but applying it at every link turns every intermediate object into a Middle Man. Better: look at what the final object is used for, Extract Function on the client code that uses it, then Move Function down the chain. Several clients navigating the same path: add a method for it. Not all chains are terrible.

**Middle Man.** Delegation is normal encapsulation; half the methods merely delegating is too far. Remove Middle Man; for a few methods, Inline Function into callers; if the middle man has extra behaviour, Replace Superclass/Subclass with Delegate. Tension with Message Chains: Hide Delegate and Remove Middle Man are inverses, so balance by actual use.

**Insider Trading.** Modules exchanging data under the table. Reduce the trade to a minimum and keep it above board: Move Function/Move Field; a third module for common interests; Hide Delegate. Inheritance breeds collusion (subclasses know more about parents than parents like): Replace Subclass/Superclass with Delegate.

**Large Class.** Too many fields leads to duplicated code. Extract Class to bundle fields that go together (`depositAmount`, `depositCurrency`); common prefixes or suffixes among fields hint at a component; if the component fits inheritance, Extract Superclass or Replace Type Code with Subclasses may be easier. Too much code: first remove redundancy inside the class (500-line methods with common code become many small ones). Best clue for splitting: clients; if clients use subsets of features, each subset is a candidate class.

**Alternative Classes with Different Interfaces.** Substitution works only if interfaces match. Change Function Declaration to match signatures; Move Function until protocols match; resulting duplication: Extract Superclass.

**Data Class.** Public fields: Encapsulate Record immediately. Remove Setting Method on fields that should not change. Look at users of the getters and setters and Move Function behaviour into the class (Extract Function first if only part moves). Usually behaviour is in the wrong place. Important exception: a record used as the result of a distinct function invocation, such as the intermediate structure from Split Phase; its key property is that it is immutable (at least in practice), so it needs no encapsulation and derived info can be fields.

**Refused Bequest.** Traditional advice: push down unused members into a sibling so the parent holds only what is common. The authors do not insist: nine times out of ten the smell is too faint to be worth cleaning; do it only if it causes confusion. Stronger smell: the subclass reuses behaviour but refuses the superclass interface ("refusing implementation is fine, refusing interface gets us on our high horses"). Then do not fiddle with the hierarchy: Replace Subclass/Superclass with Delegate.

**Comments.** A "sweet smell", but often deodorant. Remove the smells first and the comments often become superfluous. A block needing a comment: Extract Function. Already extracted but still needs one: rename. A rule about required system state: Introduce Assertion. Legitimate comments: when you do not know what to do, and why you did something. Check after: deleting the comment loses no information.

## Pairs that pull against each other

| Pair | Balance by |
|---|---|
| Divergent Change vs Shotgun Surgery | Split what changes for different reasons; gather what changes for the same reason |
| Message Chains (Hide Delegate) vs Middle Man (Remove Middle Man) | Look at actual usage; keep common delegations, expose the rest |
| Speculative Generality / Lazy Element vs preparing for change | Build for understood needs; add flexibility when refactoring later would be substantially harder (see `workflow-and-safety.md`, yagni) |
| Feature Envy vs Strategy/Visitor | Deliberate separation of behaviour from data is legitimate when it fights Divergent Change; it costs indirection |

## Which move first

- Most structural smells: Extract Function to isolate the smelly piece, then Move Function to give it the right home.
- Data that travels together: Extract Class (fields), then Introduce Parameter Object or Preserve Whole Object (signatures), then move behaviour in.
- If the existing decomposition is wrong: Inline, then re-extract.
- Strength calibration: Refused Bequest is usually faint; Repeated Switches is a smell only when repeated; code used only by tests is dead.

## Cross-references from the Clean Code case studies

The Clean Code chapters name their triggers with the heuristic codes of its catalogue (details in `craft-clean-code`). Mapped to the moves above: F1 (too many arguments) triggered replacing an array plus index with a shared iterator; G23 (prefer polymorphism to if/else or switch) triggered removing a type case (Repeated Switches); G28/G29 (encapsulate conditionals, avoid negatives) map to Decompose Conditional; G31 (hidden temporal coupling) was fixed by merging ordered steps into one function; G14 (feature envy) and G17 (misplaced responsibility) map to Move Function; G15 (flag argument) to Remove Flag Argument; G9 (dead code) to Remove Dead Code; G5 (duplication) to Extract Function. See `worked-sequences.md`.

Source: Refactoring 2e ch. 3 (Beck and Fowler); Clean Code ch. 14-16 for the cross-references.
