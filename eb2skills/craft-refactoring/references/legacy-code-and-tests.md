# Legacy code and building the safety net

Contents
1. The rule and the question to ask first
2. What a good safety net looks like
3. Procedure: adding tests to code that has none (characterisation)
4. Fresh fixtures, phases, one verify
5. What to test: risk, boundaries, unanticipated input
6. Is the suite good enough to refactor?
7. Seams and untestable code
8. Improving a legacy mess over time
9. Inheriting mature code with some tests (SerialDate workflow)
10. Adaptation for today's tooling
11. Verification checklist

## 1. The rule and the question to ask first

"If you want to refactor, you have to write tests" (Refactoring 2e ch. 4). Even with automated refactoring tools, many refactorings still need test checks. When code has no tests, first make the section self-testing, then restructure.

First question: how much of this do I really need to change or understand? Messy code you do not touch can stay (treat it as an API). Only build the net around the zone you are about to modify.

## 2. What a good safety net looks like

- Self-testing: fully automatic, compares actual with expected in code, prints a pass or the differing lines. Eyeballing console output is slow and unreliable.
- Fast enough to run every few minutes, and trivial to run (one command), with a simple summary (counts, green or red).
- Deterministic: fresh fixtures, no order dependence.
- Why it works: if a test that passed now fails, the fault is in the few lines changed since the last run, so finding it takes minutes instead of hours.
- Unit tests are the backbone. Business logic should be separable from UI, persistence and external services so it can be tested; start there.
- Treat tests as code: refactor them, remove duplication (through fixture set-up, not shared mutable state). Testability is a legitimate criterion for judging designs.
- Tests are constantly worked on; spending more time changing tests than the code under test is the sign of too many (or badly shaped) tests, but over-testing is "vanishingly rare compared to under-testing".

## 3. Procedure: adding tests to existing code (characterisation)

For each behaviour you are about to rely on:
1. Write the test with a placeholder expected value.
2. Run it. Replace the placeholder with the value the code actually produced (trusting the working code), or compute the expected value by hand if you doubt the code.
3. Inject a fault into the production code (for example change `demand - totalProduction` to `demand - totalProduction * 2`). Confirm the test fails with a useful message.
4. Revert the fault.
Every test should be seen failing at least once: a test written after the code passes by default and proves little.

Larger scale (Refactoring 2e ch. 1): for an output-producing function such as a report, build several inputs covering the variants, generate outputs, hand-check them once, and store them as reference strings (a golden master). Compare after every step, with a diff showing the differing lines.

Bug-driven: when a bug report arrives, first write a test that exposes the bug, then fix it. Ad hoc probes made while debugging should be formalised as tests before the session ends (Pragmatic Programmer sec. 34): code that broke once is likely to break again. Also test the neighbours of a bug: in Clean Code ch. 16 the history showed three neighbouring functions of a boundary-condition bug had been "fixed" before, and patterns in failures and in coverage gaps are revealing.

## 4. Fresh fixtures, phases, one verify

- Build the fixture in a per-test set-up hook (`beforeEach`), never once at suite scope. A shared object that one test mutates produces order-dependent, intermittent failures, "a collapse of confidence in the tests". If creation is truly slow, a shared fixture is acceptable only if immutable or provably unchanged.
- Phases: set-up, exercise, verify (given-when-then, arrange-act-assert), with implicit teardown.
- One verify per test as the general rule: a test stops at its first failed assertion, which can hide information. Two closely connected assertions are tolerable.
- Test descriptions need only enough text to identify which test failed.
- A failure is a verify step outside expected bounds; an error is an unexpected exception in an earlier phase. Some frameworks report both as failures.

## 5. What to test: risk, boundaries, unanticipated input

- Risk-driven, not coverage-driven: test what could plausibly break now or later. Skip trivial accessors and simple setters; test code with complicated behaviour (a setter that updates a derived total). It is better to write and run incomplete tests than not to run complete ones; writing too many tends to end in writing none.
- Play the enemy and probe boundaries:
  - empty collections (no producers: shortfall equals demand, profit 0);
  - zero (zero demand);
  - negatives (negative demand gives negative profit, which raises the domain question of reject or clamp);
  - blank strings from UI (parse gives NaN);
  - wrong types into constructors.
  Writing these tests raises design questions about how code ought to react; that is part of their value.
- Unanticipated-input errors: options are a better message, a default with a log, or leave it. Leave it if the input comes from a trusted source inside the same code base (duplicate validation between internal modules causes more trouble than it solves). Validate and test if the input comes from outside (for example a JSON request).
- Tests outside observable behaviour (the unanticipated exception) should be discarded when writing tests before a refactoring; refactoring preserves only observable behaviour. If bad data could propagate and be hard to debug, Introduce Assertion; do not write tests for assertion failures.
- Law of diminishing returns: do not let the fear that testing cannot catch all bugs stop you writing tests that catch most.
- Keep adding tests while refactoring; you understand the program better and find more.
- Pragmatic Programmer sec. 34 (test against contract): for each routine test a precondition violation, each boundary, a typical case, and a postcondition property; test dependencies before their dependents so a failure points at the right level.

## 6. Is the suite good enough to refactor?

- Best measure (subjective): "How confident are you that if someone introduces a defect into the code, some test will fail?" Caveat: false confidence.
- Coverage identifies only untested areas; it is no measure of suite quality. Clean Code ch. 16 measured about 50% statement coverage (91 of 185) on code that looked well tested, then raised it to 92% with an independent suite. Coverage figures also mislead when the denominator changes: after the refactoring the class had 84.9% because it shrank, not because it was less tested.
- Hand mutation check: inject a fault, confirm a test fails (section 3). The book does not call it mutation testing; the connection is inferred.
- Deterministic and fast.
- Adaptation, not from the book: for the exact area you will change, make a list of the behaviours the next ten steps depend on and confirm each has a test that fails when it breaks.

## 7. Seams and untestable code

- Legacy code usually has no tests and was not designed for them. The advice cited from Feathers (Working Effectively with Legacy Code): find seams where tests can be inserted. Creating seams needs refactoring without tests, a necessary risk, so prefer safe automated refactorings (rename, extract, move done by a tool) in that phase.
- Alternatives named in Refactoring 2e ch. 2: trust tool-performed refactorings only, or use a discipline of provably safe, language-specific recipes for large poorly tested code bases (not covered in the book).
- Wrap nondeterministic or environmental inputs such as the clock so tests are deterministic (Clock Wrapper in the Extract Function example).
- Make the production code testable by separating logic from I/O; Replace Query with Parameter pushes global reads to callers and makes a function referentially transparent (see `catalog-apis.md`).
- Make incompatible changes break the build (compiler as impact analysis) where you own all callers (Pragmatic Programmer).

## 8. Improving a legacy mess over time

- Even with tests, do not refactor a legacy mess all at once. Improve the piece you are passing through each time; areas visited more often get more attention, which is where the payoff is highest.
- Encapsulate global or widely used mutable data whenever you must change or add a reference to it (Encapsulate Variable); this stops coupling from growing.
- Order inside a zone (inferred from the ch. 1 sequence): Extract Function to name what you understand; Rename; Split Variable and Replace Temp with Query to simplify locals; then bigger moves.
- Inline-then-re-extract is legitimate when the existing decomposition is wrong.
- Stop adding features the moment you can see the next two additions will make the structure unmanageable, refactor first (Clean Code ch. 14; see `worked-sequences.md`).

## 9. Inheriting mature code with some tests (SerialDate workflow, Clean Code ch. 16)

1. Understand it by finding usages; list unused public things.
2. Measure coverage; write an independent suite for the missing behaviour. Tests that should pass but do not are left commented out as a to-do list of desired behaviour, to make pass during the work.
3. Fix bugs the tests expose cheaply. Boundary conditions first; check neighbouring functions.
4. Only then clean. Run all tests after every change.
5. Sweep top to bottom: noise (history headers, redundant comments, dead code); names and abstraction levels; enums for closed int codes; behaviour onto the owning type; base class never mentioning derivatives; polymorphism for switches; fix mutation and naming ambiguity.
6. Search the repository for usages before moving or deleting anything. Check whether anything but tests calls a function before polishing it (the author wasted a chain of steps on two functions only tests used).
7. Re-read the whole class for flow and reorder.
Caveat: those renames and type changes were safe because the author could update every caller.

## 10. Adaptation for today's tooling (not from the books)

- The book's JavaScript, Mocha and Chai are dated tool choices; any xUnit-style framework carries the same practices.
- Snapshot or approval tools can produce golden-master tests for large outputs; review the stored snapshot by hand once, as the book does with reference strings.
- A coverage report can show which lines a characterisation test touches; use it to find untested areas, not to certify quality.
- Mutation testing tools automate the hand fault-injection of section 3; use sparingly on the zone you will change.
- A type checker, linter and language-server rename are the modern "compile" step.
- When tests would take too long to build, a smaller change set with tool-automated steps is the fallback, not guesswork.

## 11. Verification checklist

- The tests for the zone were seen failing at least once (fault injection or a pre-fix run).
- Placeholder values were replaced by hand-checked or trusted actual values.
- Boundary cases (empty, zero, negative, blank) have tests, or a deliberate note says why not.
- Each fixture is created fresh per test; no order dependence (run the suite in a different order or alone to check).
- One command runs everything, including acceptance-level tests.
- Coverage was used only to find gaps.
- Tests for unanticipated-input behaviour were not treated as a refactoring contract.

Source: Refactoring 2e ch. 1, 2, 4; Clean Code ch. 14-16; Pragmatic Programmer ch. 6 (sec. 31, 33, 34).
