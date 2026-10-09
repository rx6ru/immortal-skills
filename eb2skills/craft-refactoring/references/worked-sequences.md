# Worked sequences from the long case studies

Four replayable sequences. Each lists the order of moves, the trigger for each, and the lesson. Listings are not reproduced; the moves are language-neutral. Use these when a task is bigger than one catalogue entry and you need the shape of a whole campaign.

Contents
1. Statement printer (Refactoring 2e ch. 1): extract, split phase, polymorphism
2. Args parser (Clean Code ch. 14): introduce an abstraction beside the old code
3. ComparisonCompactor (Clean Code ch. 15): review pass on already-good code
4. SerialDate (Clean Code ch. 16): tests first on inherited code, then a top-to-bottom sweep
5. Lessons that recur
6. Generic campaign procedure

---

## 1. Statement printer (Refactoring 2e ch. 1)

Situation: one function builds a text bill from invoice and plays data: it loops, computes a charge with a switch on play type, accumulates volume credits, formats money and builds the string. Two changes are pending: an HTML version, and more play types with their own charging and credit rules. Rule applied: when you must add a feature and the structure is inconvenient, first refactor so the feature is easy to add, then add it. Duplicating the function for HTML would force every later rule change to be made twice.

Step zero: tests. Several invoices covering play types, output compared with hand-checked reference strings; self-checking, one keystroke, seconds long. After every step below: compile, test, commit locally; on a surprise failure revert and take a smaller step.

Stage A, decompose the long function
1. Extract Function on the switch: `amountFor(perf, play)`. Scope procedure: read-only variables become parameters; the single modified variable becomes the return value.
2. Rename inside it (`thisAmount` to `result`, `perf` to `aPerformance`), one rename at a time, testing after each.
3. Remove the `play` local: Replace Temp with Query (extract `playFor`, Inline Variable, then Change Function Declaration to drop the parameter in two steps).
4. Inline Variable on the amount.
5. Extract Function `volumeCreditsFor`; delete the now-misleading comment.
6. Replace the `format` function variable with a declared function, rename to `usd`, move the `/100` into it.
7. Remove the `volumeCredits` accumulator in four steps: Split Loop, Slide Statements, Extract Function, Inline Variable. Same four steps for `totalAmount`; when the best function name collides with the variable name, extract under a throwaway name, inline the variable, then rename.
Result: the main function is seven lines of layout. The repeated loops are a performance worry only in theory: ignore it while refactoring; tune later with a profiler.

Stage B, Split Phase (so HTML can reuse the calculations)
1. Extract the second-phase code into `renderPlainText(invoice, plays)`.
2. Add an intermediate `statementData` object as a first argument; move `customer`, then `performances` into it; the renderer no longer needs `invoice`.
3. Enrich each performance on a shallow copy (do not mutate input). Move `playFor`, `amountFor`, `volumeCreditsFor` into the enrichment, then the two totals; renderer reads `perf.play`, `perf.amount` and so on. Replace Loop with Pipeline on the totals.
4. Extract all first-phase code into `createStatementData`, in its own file.
5. Add the feature: `htmlStatement` calls the same data builder and a second renderer; share `usd`.
Code grew from 44 to 70 lines and that is fine: more code is bad only if all else is equal; here the lines buy separation and zero duplication. Camp-site rule: leave the code healthier than you found it; never perfect, but better.

Stage C, polymorphic calculator (Replace Conditional with Polymorphism by type)
1. Create `PerformanceCalculator` and instantiate it in the enrichment; pass the play in.
2. Move `amountFor` into it (copy, adapt references, make the original delegate, then inline callers); same for volume credits.
3. Replace Constructor with Factory Function first (a JS constructor cannot return a subclass), then add empty `TragedyCalculator` and `ComedyCalculator` selected by the factory (throw on unknown).
4. Move each leg of `amount` into its subclass, optionally making the superclass leg throw to prove it is unreachable; finally make the superclass method a "subclass responsibility" tombstone.
5. For volume credits most types share a rule, so keep it as the superclass default and let comedy extend via `super`.
Result: a new play type is one subclass plus one factory line; the type conditional lives in one place. Decision rule: the more functions depend on the same type discrimination, the more polymorphism pays; with a single switch it would not.

Verification the book implies: output byte-identical on the reference invoice at the end; every commit is one named refactoring; after Stage B the renderer reads nothing from the raw invoice or plays; after Stage C no switch on play type outside the factory; add tests against the intermediate structure once it exists; inputs are not mutated.

Caveat from the book: the example is too small to justify the refactoring in isolation; imagine it inside a large system. The preference for small functions is contested; the defence is the ease-of-change test.

## 2. Args parser (Clean Code ch. 14)

Situation: a command-line flag parser. A first version with booleans only was compact. Adding strings and then integers pushed it over the edge: many instance fields, sentinel strings, a `valid` flag set from many places, try/catch blocks, error handling per type spread around. Each new type needed new code in three places (parse the schema element, parse and convert the argument, add an accessor) and every type had similar methods: "that sounds like a class to me".

Trigger rule: stop adding features the moment you can see the next two additions will make the structure unmanageable, and refactor first. The author's stance: write it working, then clean it, in successive drafts; leaving it at "works" is professional suicide, and cleaning five minutes later is cheaper than cleaning later. Massive restructuring "in the name of improvement" is one of the best ways to ruin a program; keep the system working after every change.

Phases
- A, introduce the abstraction beside the old code. Append an empty base marshaler class and three empty subclasses (cannot break anything). Change the boolean map's value type to the base class and fix the few broken lines; a test failed immediately (an undefined flag now caused a null error), so fix that before any other step. Repeat for string and int. Interim state: all marshalling code in the base class, derivatives empty ("first get all behaviour into the base class under test, then push it down").
- B, push behaviour down. Make the base abstract, one abstract method at a time (first a default to compile and see tests fail, then make it abstract and implement). Move the value field down. Delete unused base methods.
- C, collapse three per-type maps into one. Add a fourth map keyed by argument; populate it alongside the old maps; switch readers one by one; inline helpers whose reason to exist is gone; delete each old map when unused. The result was "a bit disappointing": keep going.
- D, kill the type case (prefer polymorphism to if/else or switch). Obstacle: the int path used two instance variables (array and index), and passing both is a too-many-arguments smell; replace with a list and a shared iterator, pass just the iterator. Then add a uniform `set(iterator)` to each marshaler one at a time, forward from the dispatcher, and delete the old per-type setter. Passing an unneeded iterator to the boolean variant is deliberate: the common signature is the point.
- E, prove extensibility by adding a type test-first (a double): detect the schema token, write the marshaler, add error codes, add the accessor. "Pretty painless."
- F, extract error handling into its own exception type with code, argument id, parameter and message formatting (about 30 tiny steps). The author calls putting message text there a compromise.

Lesson from the process: while refactoring only the unit tests were run; an acceptance test caught a behaviour (`getBoolean` on a non-boolean argument returning false) they did not. Fix: one test that runs every acceptance test, so one command checks everything.

Dated points: heavy `instanceof`, `Object` returns and casts in intermediate and final code are themselves smells (modern designs use generics or sum types); the schema-string DSL is one design among many. The transferable asset is the procedure.

## 3. ComparisonCompactor (Clean Code ch. 15)

Situation: a well-written helper with about 20 tests and measured 100% coverage, still improved under the Boy Scout Rule. Moves, each followed by the tests:
1. Drop the field prefix `f` (encodings); a local now shadows a field, so rename the local.
2. Extract the opening conditional into a named predicate; invert a negative into a positive name; use if/else.
3. Rename the public method to describe what it really does (it formats, and may not compact).
4. Split formatting from compacting.
5. Make conventions consistent (functions that return values rather than set fields; accurate field names).
6. Expose a hidden temporal coupling (one function silently needed a value another computed). Passing the value as a parameter enforced the order but was "a bit arbitrary" (nothing explains why the argument exists, so the next programmer might undo it); better to revert and merge into one function that calls the first step first.
7. Tame boundary arithmetic: scattered `+1` and `-1` revealed an index that was really a length. Redefine it as a zero-based length, move the adjustment into small helpers, rename.
8. Test deadness by reasoning: after the redefinition one comparison "made no sense", which showed two conditions were always true. Comment them out, run the tests, delete.
The author reversed several earlier choices by the end ("one refactoring leads to another that leads to the undoing of the first").

Review order that works on mature code: read the tests and measure coverage; fix names and encodings; encapsulate conditionals; find mixed responsibilities; make hidden order dependencies explicit and self-explaining; find the right unit to remove off-by-one noise; test whether conditionals are dead. The existing suite is what made the work safe; no new tests were needed. If coverage were lower, add characterisation tests first (inferred).

## 4. SerialDate (Clean Code ch. 16)

Situation: inherited open-source date class. Rule: first make it work, then make it right. Reviewing and rewriting good code is professional review, not malice.

Phase 1, make it work
- Read the existing tests; find an unused method by "find usages". Measure coverage: only 91 of 185 statements. Write an independent, fuller suite; leave tests that should pass but do not commented out as a to-do list. Coverage reached 92%.
- Fix cheap obvious gaps (case-insensitive parsing). Bugs found: a boundary error (`>` should be `>=`) in "following day of week" and a broken nearest-day algorithm exposed by a branch that coverage showed never ran. Neighbouring functions had been "fixed" before: test neighbours of a bug. Replace error strings with exceptions to make two more tests pass.
Phase 2, make it right (tests after every edit)
- Delete the change-history header; rename the class (its name leaked its representation); replace inherited constants and int month codes with an enum (an hour of work touching every user, and it removed validity checks); other closed int sets also become enums; delete unused things and redundant comments; push implementation details down to the subclass.
- The base class must not know its derivatives. Tracing a client that needed implementation limits found the abstract class instantiating its own subclass; fix with an Abstract Factory with a replaceable instance.
- Move behaviour to the type that owns it (parsing and printing names onto the day and month enums, quarter and last-day onto month). Flag argument: two format overloads differing by a boolean become two methods. Duplicate code merged; explaining variables for the leap-year rule; one consistent pattern for the three "day of week" functions after thinking about what they really do.
- Static versus instance: methods operating on the object's own data become instance methods; `addDays` reads as mutation, so rename to `plusDays` so it reads as a pure function returning a new value.
- Make logical dependencies physical: the day-of-week algorithm depended on the weekday of ordinal 0; make it an explicit abstract method. Replace the interval switch with polymorphism on the enum.
- Cautionary chain: moving, renaming and rewriting tests for two string helpers, then finding only tests used them, so deleting them and their tests. Check for real callers first.
- Final pass: shorten class comment; move enums and static helpers to their own files; abstract methods first; replace magic number 1 with named constants.
Outcome: bugs fixed, shorter code; reported coverage fell to 84.9% only because the class shrank.
Contested calls the author himself notes: deleting a manually set serialization version identifier (reviewers disagreed), wildcard imports and removing `final` (minority positions), and a static factory with a setter (global mutable state).

## 5. Lessons that recur

- Introduce the new structure empty beside the old one, migrate one variant at a time, delete the old code only when unused.
- Intermediate states can look worse; keep the whole suite green and keep going.
- A parameter added only to force call order is a weak fix; collapse the ordered steps instead.
- Off-by-one noise means a variable has the wrong meaning.
- Find who really calls a function before polishing it.
- Mechanical, small commits make reverting cheap.
- Naming is partitioning: giving each kind of code its own place.

## 6. Generic campaign procedure

1. Keep a full automated safety net; if thin, write characterisation tests first (`legacy-code-and-tests.md`).
2. Spot the smell: the same triple repeated per variant, parallel maps or lists indexed by variant, flags driving branches (`smells-to-refactorings.md`).
3. Stop feature work and name the missing abstraction.
4. Add it empty, next to the old code.
5. Migrate one variant at a time through a thin shim; red means fix before anything else.
6. Move behaviour into the abstraction (base first, then push into variants); delete old code when unused.
7. Merge parallel structures into one keyed collection; inline helpers that no longer pay.
8. Replace type tests with polymorphic dispatch; use a uniform signature even if a variant ignores a parameter.
9. Validate by adding a new variant test-first; it should touch few, isolated places.
10. Extract cross-cutting concerns (errors, formatting) into their own module; note compromises.

Source: Refactoring 2e ch. 1; Clean Code ch. 14, 15, 16.
