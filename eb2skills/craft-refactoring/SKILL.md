---
name: craft-refactoring
description: "Procedures for changing the structure of existing code without changing its behaviour: the safety workflow (tests first, tiny steps, revert to green, two hats), a lookup from all 24 code smells to refactorings, a catalogue of about 60 refactorings with numbered mechanics, migration tactics for published interfaces, legacy code without tests, refactor-versus-rewrite guidance, and worked case studies. Use when asked to refactor, clean up, restructure, extract, rename, move, split or simplify code; when a feature is awkward to add to the current structure; when reviewing duplication, long functions, long parameter lists, feature envy, repeated switches or inheritance trouble; or when changing a signature with many callers. Naming and comment style: craft-clean-code; test design: craft-testing; patterns: craft-design-patterns."
---

# Refactoring existing code

## Purpose

Use this skill to restructure code in small, behaviour-preserving steps that you can verify after each one, instead of rewriting or making large unchecked edits. It tells you whether a refactoring is warranted now, which smell you are looking at, which named refactoring fixes it, the mechanics to follow, and the evidence that proves behaviour did not change. It also keeps a small request small: most tasks need two or three catalogue entries, not a campaign.

## Choose what applies

| The request or the code looks like | Do this | Read |
|---|---|---|
| "Refactor / clean up / restructure X", no further detail | Check the tests, name the smells you see, pick the 1-3 refactorings with the biggest payoff on the code you must touch | `workflow-and-safety.md`, then `smells-to-refactorings.md` |
| Adding a feature or fixing a bug and the structure fights you | Preparatory refactoring first (a separate step), then the change | `workflow-and-safety.md` section 3 |
| You can name the smell (duplication, long function, feature envy, ...) | Look it up, apply the listed refactoring | `smells-to-refactorings.md`, then the catalogue file it points to |
| Extract, inline, rename, change a signature, encapsulate a variable, group data, split phases | Basic catalogue | `catalog-basic.md` |
| Hide a record, collection or primitive; split or merge a class; delegate | Encapsulation catalogue | `catalog-encapsulation.md` |
| Move a function or field, slide statements, split a loop, loop to pipeline, delete dead code | Moving-features catalogue | `catalog-moving-features.md` |
| A variable reused or derived; field rename; reference versus value | Organizing-data catalogue | `catalog-organizing-data.md` |
| Nested ifs, repeated switch, null checks, implicit assumptions | Conditionals catalogue | `catalog-conditionals.md` |
| Flag arguments, setters, query/modifier mixing, parameters, constructors, command objects | API catalogue | `catalog-apis.md` |
| Duplicated subclasses, type codes, wrong inheritance | Inheritance catalogue | `catalog-inheritance.md` |
| No tests, or tests of unknown quality | Build the net first (characterisation tests), then refactor | `legacy-code-and-tests.md` |
| A rename or signature change with many or external callers, a published API, a database column | Parallel change (migration mechanics) | `catalog-basic.md` (Change Function Declaration), `workflow-and-safety.md` sections 6 and 8 |
| A large, multi-stage restructuring | Replay the shape of a worked case | `worked-sequences.md` |
| Deciding refactor or rewrite | Judgement criteria | `workflow-and-safety.md` section 12 |

This does not apply, or applies lightly, when:
- The code works, nobody needs to change or understand it, and it is not on your path: leave it.
- The change alters behaviour (a bug fix, a new feature, a performance optimisation): that is a different hat; refactor around it, not inside it.
- You cannot tell what the better structure is: do not guess; make the smallest clarifying change (a rename, an extraction) and learn.
- The request is about naming or comment style only: use `craft-clean-code`.
- The request is about module or API design from scratch rather than changing existing code: use `craft-module-design`.
- The question is how to write or organise tests: use `craft-testing`; this skill only says what a refactoring needs from them.

## How to apply

### Step 0: scope and hat
1. State the goal in one sentence: which change will become easy, or which reader confusion goes away. Refactoring is justified economically (faster change), not morally. If you cannot state a benefit, do not start.
2. Say which hat you are wearing. While refactoring: no behaviour changes, no new tests except for gaps, existing tests change only to follow an interface change. A noticed bug is recorded or fixed later in its own step.
3. Limit scope to what the task touches and the code you pass through. Do not rewrite neighbouring modules "while there".

### Step 1: safety net
1. Find the tests that cover the area and run them. Green? Note the baseline (commands, pass count).
2. Is the net good enough? The test is confidence: if someone introduced a defect in this code, would some test fail? Check by injecting a fault in the production code, seeing a test fail, and reverting.
3. No or weak tests: write characterisation tests for the behaviours you will touch (placeholder, run, paste actual, inject fault, revert), then continue. See `legacy-code-and-tests.md`.
4. Wrap nondeterminism (clock, randomness, environment) so the tests are repeatable.
5. If you cannot get any safety net, restrict yourself to tool-performed refactorings (IDE or language-server rename, extract, move) and say so in your report.

### Step 2: pick the refactoring
1. Name the smell (`smells-to-refactorings.md`) or the structural obstacle to the feature.
2. Choose the catalogue entry; read its mechanics. If it is new to you, read the example in the reference file.
3. Prefer the move that isolates first, then relocates: Extract Function, then Move Function. When the existing decomposition is wrong, inline then re-extract.
4. When two smells pull opposite ways (Divergent Change versus Shotgun Surgery, Hide Delegate versus Remove Middle Man), decide by actual change patterns and usage, not by taste. Both directions are cheap to reverse.

### Step 3: the step loop
1. Do one mechanical step from the entry (the entries list them numbered).
2. Compile or type-check, run the tests. Commit locally when green.
3. Red and the cause is not instantly obvious: revert to the last green state and redo with smaller steps. Do not debug forward. The trickier the situation, the smaller the steps.
4. Never start the next step on a red bar.
5. Use temporary, searchable names (`xxNEW...`, `zz_...`) for the new function or field while migrating; choose the final name last.
6. After each extraction look for cheap clarifications (renames).

### Step 4: finish
1. Remove the temporary names and forwarding shells that no longer have callers.
2. Delete dead code (do not comment it out); search first for dynamic or external callers.
3. Update comments and docs that the change made false. Put rationale in the code, not only in the commit message.
4. Review the full diff once as a reader: does it read as if designed with the feature in mind?

## Decision rules used most

| Question | Rule | Why |
|---|---|---|
| Refactor now? | Yes if it makes the current task easier, you met this ugliness before, or the area is visited often. No if untouched, rarely visited, or the better shape is unclear | Refactoring pays through change speed; unused code gains nothing |
| Rule of three | First time just do it, second time wince and do it, third time refactor | Avoids abstracting before the variation is known |
| Extract a function? | When the intent is clearer than the code, even for one line; name it for what, not how. If you cannot find a better name, do not | The measure is semantic distance, not length |
| Function or class for grouped derivations? | Class if the source data can change; transform only for read-only or immutable data | A transform stores derived fields that go stale |
| Polymorphism for a conditional? | Only when the same condition is switched in several places, or there is a base case with variants. A single switch stays | Overuse of polymorphism adds classes for no gain |
| Single exit versus guard clauses? | Clarity decides; guard clauses for unusual cases, if/else when both legs are normal | Single-exit is "not a useful rule" |
| Hide a delegate? | When clients are coupled to the delegate's interface; reverse when forwarding methods dominate | No fixed right amount; adjust as usage shows |
| Add a parameter or hook "for later"? | Not unless callers pass different values now or later change would be substantially harder | Speculative flexibility usually guesses wrong |
| Function or command object? | Function, except when you need undo, staged parameters, hooks, or to break up a function with many shared locals | The author picks a function 95% of the time |
| Inheritance or delegate? | Start with inheritance; switch when a second axis of variation, runtime variant change, or a false IS-A appears | Delegation adds dispatch and back-references |
| Parameter or query inside? | Pass less if the callee can easily determine it without new coupling; pass more to cut a dependency on a global or gain referential transparency | Allocation of responsibility; reversible |
| Performance worry | Ignore while refactoring; if a real slowdown appears, finish, then profile and tune hot spots | Programmers misjudge hot spots; clean code tunes better |
| Refactor and feature in one commit? | Default: separate commits. Contested: the author sees costs in splitting | Independent review and revert versus keeping context |

Disagreements to know about:
- Small functions: the book prefers very small, intention-named functions; the sources behind `craft-clean-code` include a school that finds many tiny functions harder to follow. The deciding test here is whether the new name lets a reader skip the body. If the name only restates the code, or the reader must jump through five functions to follow one idea, inline. See `craft-clean-code` for the arbitration between the two schools.
- Comments: Refactoring 2e wants comments replaced by well-named functions where possible and kept for "why" and uncertainty. Keep why-comments; do not delete them just because a refactoring is in progress.
- "Don't tell your manager" about refactoring time and skepticism about separate refactoring commits are the author's flagged contested positions; treat them as options, not rules.

## Verify

Verification is both "behaviour unchanged" and "structure actually better". Collect evidence for both.

Behaviour unchanged
1. Show the baseline test run before the first edit and the run after the last edit, identical outcome. If you added characterisation tests, show they failed once under an injected fault.
2. For each step in a long sequence, say the tests ran after it (or show the commit list: one named refactoring per commit).
3. Differential check for algorithm or query replacement (Substitute Algorithm, Separate Query from Modifier): run old and new on the same inputs, including empty, zero, negative, null and boundary values; keep the old as an oracle until they agree.
4. Hypothesis assertions: before replacing a stored value with a computation (Replace Derived Variable with Query, Move Field to a shared object), assert stored equals computed, run the suite and ideally logged real use, then switch.
5. Prove new paths are reached: after moving a conditional leg to a subclass, make the old leg throw, or break the new override once and see a test fail. Then restore it.
6. Search checks: no remaining references to the temporary name, the old function, the raw accessor, the removed field, or `=== sentinel` comparisons (grep or compiler). In dynamic languages also search string and reflective uses.
7. Public behaviour of published interfaces: old entry point still exists, delegates, and is marked deprecated; a test calls the old path.
8. Input data not mutated where the plan said copy (a test that clones the input and compares).
9. Performance: if the work was performance-motivated, before and after profiler numbers; if not, a note that none were taken.

Structure better (the smell's own test flips)
| Smell addressed | Observable check afterwards |
|---|---|
| Duplicated Code | One definition; a representative change edits one place |
| Shotgun Surgery | A representative change touches one module |
| Divergent Change | A change in one context touches no code of the other |
| Feature Envy | The function mostly references its own module's data |
| Data Clumps | Signatures shrank and deleting one field of the new object breaks its meaning |
| Mutable Data | Searching for writes finds only narrow functions; the new variable can be immutable |
| Repeated Switches | No switch on that condition outside the factory |
| Comments | Deleting the comment loses no information |
| Long Parameter List | Parameter count dropped and no flag literals at call sites |
| Mysterious Name | A newcomer can say what it does without opening the body |
Also ask: does the change leave the code as if the feature had been designed in? Did the change add flags, parameters or special cases (each a tactical smell)? Is any behaviour change hiding in the diff?

Done means
- Tests were green before the first edit and after the last, and between steps.
- Each commit (or step) is one named refactoring and has no behaviour change.
- The goal stated in Step 0 is met and evidence is shown.
- No temporary names, forwarders without callers, commented-out code, or stale comments remain.
- Known limits are reported: what was not covered by tests, what was left alone, what was deferred as a follow-up.

## Proportion and limits

- Cost: each step costs a test run. Keep the suite fast; if it is not, run the narrow tests per step and the full suite per group of steps, and say so.
- Over-engineering signs: refactoring unrelated code, introducing a class hierarchy for one switch, generalising for hypothetical callers, building a command object where a function works, a big-bang restructuring without commits in between. Back off to the smallest change that serves the goal.
- Under-refactoring is the commoner error: the sources say too little refactoring is far more frequent than too much, and a "minimal diff" habit degrades design step by step.
- Dated or contested: JavaScript, Mocha/Chai and Eclipse-era tooling in the books are of their time. The first-edition Pragmatic Programmer passage on automatic refactoring browsers and embedded tests is dated; the Clean Code case studies use Java 5-era idioms, heavy `instanceof` and error-code enums that modern designs replace with generics, sum types or result types. Smell thresholds are deliberately absent in the book: any number you apply is a local convention.
- Language limits: some mechanics assume closures (pipelines), classes with polymorphism, or properties. In a language without them, use the closest idiom and keep the safety rule.
- Teams: refactoring depends on short-lived branches and frequent integration; sweeping renames collide with long-lived branches. Check for open branches before a wide rename.
- Large-scale rewrites, architecture change and service decomposition are not covered here; see the `arch-*` skills (for example `arch-decomposition`).

## References

- `references/workflow-and-safety.md`: read first for any non-trivial refactoring: definitions, two hats, when and when not, step loop, commits, published interfaces, branches, databases, performance, yagni, tools, refactor versus rewrite, strategic modification.
- `references/smells-to-refactorings.md`: read when you see a code problem and need to know which refactoring applies; all 24 smells with recognition tests, cautions and checks.
- `references/catalog-basic.md`: Extract/Inline Function and Variable, Change Function Declaration, Encapsulate and Rename Variable, Introduce Parameter Object, Combine Functions into Class or Transform, Split Phase.
- `references/catalog-encapsulation.md`: Encapsulate Record and Collection, Replace Primitive with Object, Replace Temp with Query, Extract and Inline Class, Hide Delegate, Remove Middle Man, Substitute Algorithm.
- `references/catalog-moving-features.md`: Move Function and Field, Move Statements into Function or to Callers, Replace Inline Code with Function Call, Slide Statements, Split Loop, Replace Loop with Pipeline, Remove Dead Code.
- `references/catalog-organizing-data.md`: Split Variable, Rename Field, Replace Derived Variable with Query, Change Reference to Value and back.
- `references/catalog-conditionals.md`: Decompose and Consolidate Conditional, guard clauses, polymorphism, Special Case, Assertion.
- `references/catalog-apis.md`: Separate Query from Modifier, Parameterize Function, Remove Flag Argument, Preserve Whole Object, parameter/query swaps, Remove Setting Method, factory functions, function/command swaps, parallel change.
- `references/catalog-inheritance.md`: Pull Up/Push Down, type code to subclasses, Remove Subclass, Extract Superclass, Collapse Hierarchy, Replace Subclass or Superclass with Delegate.
- `references/legacy-code-and-tests.md`: read when tests are missing or doubtful: characterisation procedure, fixtures, boundaries, sufficiency checks, seams, inherited-code workflow.
- `references/worked-sequences.md`: read for multi-stage restructurings: the statement printer, the Args parser, ComparisonCompactor and SerialDate, with the generic campaign procedure.

## Sources

- Refactoring, 2nd edition (Fowler, 2018): ch. 1 first example; ch. 2 principles; ch. 3 bad smells; ch. 4 building tests; ch. 5 catalogue format; ch. 6-12 the catalogue.
- Clean Code (Martin, 2008): ch. 14 successive refinement; ch. 15 JUnit internals; ch. 16 refactoring SerialDate.
- The Pragmatic Programmer, 1st edition (Hunt and Thomas, 1999): ch. 6 (programming by coincidence, algorithm speed, refactoring, code that is easy to test, wizard code).
- A Philosophy of Software Design (Ousterhout, 2018): ch. 16 modifying existing code.
