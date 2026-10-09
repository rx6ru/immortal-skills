# Designing code to be testable

Making code easy to test, and reading difficulty of testing as a design finding. Use when you are about to write tests for code that mixes logic with UI, time, randomness, network, globals or singletons; when a test needs elaborate setup; when someone says "that is too hard to test"; or when designing a new module and you want testing to be cheap.

## Contents

1. The principle
2. Contract first, tests derived from it
3. Testing from the bottom up
4. Separate logic from presentation
5. Break dependences: inject, do not reach
6. Make nondeterminism explicit
7. Cohesion, coupling, no cycles
8. A test window: observability in production
9. Test location, harness and culture
10. Generated and copied code
11. Testability as an architectural criterion
12. Symptoms and the move that fixes each
13. Verify

---

## 1. The principle

Design to test (Pragmatic Programmer ch. 6, Tip 48): design the contract and the code so that you can test them, for a module or a single routine. Designing to pass a test forces you to consider boundary conditions, and writing tests before the code lets you try the interface before committing to it. The chip analogy: components are designed to be tested at the factory, at installation and in the field, and software can be too.

The corollary in Clean Code ch. 9 ("Timely"): when tests are written after the code, the code is often hard to test, and you may decide some of it is "too hard to test" and not design for testability. Treat that sentence as a smell: either the design needs to change, or you have not yet found the seam.

Refactoring 2e ch. 4 makes the matching architectural statement: testability is a legitimate criterion for judging architectures. Clean Code 2e's outline lists a "Simpler Testing" section inside the classes chapter (heading only; content not in the notes).

## 2. Contract first, tests derived from it

1. State what the routine requires (preconditions) and promises (postconditions, invariants).
2. Derive the tests from the contract: reject violations of preconditions, accept the boundary, check the postcondition across the range (`what-to-test.md` section 5).
3. Implement.

The shape of the test helper in the book's square-root example: call the routine with a value and the expected result; if it throws and the input violates the precondition, that is expected; otherwise fail; then compare against the expected value within a tolerance.

## 3. Testing from the bottom up

Test the parts before the whole. If module A uses LinkedList and Sort, test LinkedList's contract, then Sort's, then A's. A failing A then points at A or its use of its parts. This avoids "time bombs" that sit unnoticed and explode later (Pragmatic Programmer ch. 6). The same reasoning (a bug visible only with the UI present was probably created by the UI code) holds for validating logic before attaching the interface (Pragmatic Programmer ch. 8).

## 4. Separate logic from presentation

- Start with code that has no UI, persistence or external services; separate business logic from UI mechanics once the logic is non-trivial (Refactoring 2e ch. 4).
- Decouple so application logic can be tested without a GUI present. If that is too hard, ask what it says about the GUI and the coupling (Pragmatic Programmer ch. 8).
- Programs have three layers: presentation, functionality, units (Why Programs Fail ch. 3). Automating the middle layer is usually the sweet spot: results are easy to access and evaluate. A monolith with presentation and functionality tangled can (a) be tested through the presentation at a price, (b) be redesigned to separate them, or (c) be decomposed so units are reached directly.

Model-view-controller is the model case (Why Programs Fail ch. 3). The model holds data and services and keeps a list of observers; views display and controllers handle input and call services. Testing benefits:

- add a new controller that drives the model automatically (test automation);
- register a special view that logs every model change (observation);
- test each observer and the model alone.

A caveat from the same chapter's exercise: observers still depend on a concrete model, so apply dependence inversion there too.

## 5. Break dependences: inject, do not reach

Dependence inversion (procedure in `test-levels-and-doubles.md` section 5): introduce an interface for the thing you cannot run in a test, depend on the interface, supply an automated implementation in tests. The thing is typically a dialog, a clock, a file system, a network client, a database, a global.

Adaptation checklist for common obstacles:

| Obstacle | Seam to introduce |
|---|---|
| Direct calls to a UI prompt from core logic | an interface the core receives; the test supplies one that answers automatically |
| `new` of a collaborator inside a method | constructor or parameter injection; a single place that builds the object graph (composition root) |
| Singleton or global state | pass the instance; reset between tests; see `craft-module-design` for construction versus use |
| Static calls to I/O | wrap behind an interface or pass a function |
| Hidden temporal coupling between calls | make order explicit by passing each result to the next step (Clean Code G31) |
| Method that can only be tested through private state | expose behaviour, not state; test the observable outcome |

## 6. Make nondeterminism explicit

Clean Code ch. 9 opens with an embedded timer that its author first tested by typing and watching; he would now mock the operating system's timing functions, schedule commands that set flags, step the clock forward and assert the flags flip at the right time. Property testing in Functional Programming in Scala ch. 8 makes the random source an explicit seeded value so generation is reproducible.

Rule (adaptation): anything that varies between runs is an input.

- Time: take a clock or a "now" value; tests set and advance it.
- Randomness: take a seed or a random source.
- Identifiers: take a generator function.
- Environment and configuration: take them as arguments.
- Concurrency: pluggable executors; see `craft-concurrency` for testing threaded code.

Passing them explicitly also removes order dependence between tests and makes failures reproducible (Repeatable in F.I.R.S.T.). The pure-core idea, with effects at the edges, is developed in `fp-pure-core`.

## 7. Cohesion, coupling, no cycles

Two design principles that reduce dependences, and so make testing easier (Why Programs Fail ch. 3):

- High cohesion: group what operates on common data.
- Low coupling (information hiding): units that do not share data exchange as little as possible; circular dependences are forbidden because they couple everything involved.

Related Clean Code heuristics that show up as test pain:

- G13 Artificial coupling and G36 transitive navigation (`a.b().c().d()`): tests have to build the whole chain.
- G8 Too much information: a wide interface means more to stub.
- G22 Make logical dependencies physical: a module that silently assumes a fact about another should ask for it.

For the design side see `craft-module-design`.

## 8. A test window: observability in production

Pragmatic Programmer ch. 6: bugs survive into production. Give the software views into internal state without a debugger:

- log files with consistent, machine-parseable trace messages (inconsistent diagnostics are spew);
- a diagnostic window for the help desk;
- in server code, a status page on an embedded web server (the book's example: a non-standard port).

Surviving equivalents (adaptation): structured logging, metrics, health and debug endpoints, tracing. They also make tests easier, since a test can assert on emitted events.

## 9. Test location, harness and culture

- Keep tests easy to find: if it is not easy to find it will not be used. Accessible tests double as usage examples and as the basis for regression tests (Pragmatic Programmer ch. 6). The book's embedded-main idiom is dated; today tests live in separate files or directories next to the code.
- One harness per project, with standard setup and cleanup, selection of individual or all tests, analysis of expected versus unexpected results, standardised failure reporting, and composable tests. Discover tests by convention or reflection so no list is maintained by hand (DRY). Use the standard xUnit-style framework of the language rather than building one.
- One command runs everything, from a clean checkout (Clean Code E1, E2: the build in one step, the tests in one step; Pragmatic Programmer ch. 8: check out, build, test and ship with a single command).
- Run tests before every commit, and the full set in a scheduled or continuous build that runs all available tests, so a regression is attributed to the day's changes.
- Testing is more cultural than technical (Tip 49): all software gets tested, by you or by users.

## 10. Generated and copied code

Pragmatic Programmer ch. 6: do not use wizard code you do not understand (Tip 50). Generated code gets interwoven with your own and becomes yours. By the notes' inference the same holds for scaffolding, copied snippets and code produced by AI assistants. The testing consequence:

1. Write tests for the behaviour you depend on from generated or copied code, not for its text.
2. Remove a suspicious call and see whether anything fails; if you cannot explain why it was needed, it may be coincidence (programming by coincidence, Tip 44).
3. Run under different contexts (other locale, no GUI, different working directory, different timing) to expose accidental dependencies on the environment.
4. Keep regenerated artefacts behind a regeneration boundary; never hand-edit them and test around them.

Clean Code 2e (Future Bob, chapter 3) reports an assistant that produced a refactoring nearly identical to the first extract-method step but did not invert dependencies or separate policy from detail. Treat model-produced structure as a draft that needs a design check.

## 11. Testability as an architectural criterion

When judging a design, ask: can the core be exercised without the UI, the database and the network? Can each external dependency be replaced at one place? Can a module be built in a test harness without constructing the world? If the answers are no, the cost of every future test goes up and the safety net for refactoring thins. Clean Code 2e's chapter 3 example notes that test decoupling from the production code (tests constructing the derivatives) reduced test churn when types changed.

## 12. Symptoms and the move that fixes each

| Symptom | Cause | Move |
|---|---|---|
| Test setup is longer than the test | constructor does too much; many collaborators | pass collaborators in; pull a cohesive part out |
| Cannot test without a screen | logic in the view | extract functionality layer; test it directly |
| Tests fail at different times of day | real clock | inject time |
| Tests pass alone and fail together | shared mutable state, singletons | fresh state per test; pass instances |
| Need to stub five things to test one | high coupling; transitive navigation | give the unit what it needs, not the world |
| A bug appears only with the full app | integration or UI coupling | add a higher-level test; keep lower-level coverage |
| Logging utility fails on someone else's machine | assumes a writable working directory or a console (Pragmatic Programmer ch. 6, exercises) | make context an input; test in a clean environment |
| "Too hard to test" | tests written late; design ignored testing | find the seam; if none, redesign the dependency |

## 13. Verify

- Core logic can be imported and run in a test without starting a UI, a server, a database or a network.
- Each external dependency is reached through one named seam, and tests substitute it.
- No test reads the real clock or an unseeded random source.
- Delete the real UI implementation from the test build (or run without it): the core tests still run.
- A fresh clone passes one command to build and test.
- For generated or copied code you keep, there is at least one test of its behaviour and you can state which documented guarantee each risky call relies on.
