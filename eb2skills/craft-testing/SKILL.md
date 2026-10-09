---
name: craft-testing
description: Guidance for deciding what to test and writing tests that stay useful - purposes of tests, risk- and boundary-driven case selection, readable test structure (build-operate-check, one concept per test, FIRST), a regression test for every bug, test levels (unit, component, integration, contract, end-to-end), test doubles, designing for testability, property-based and law tests, the T1-T9 test heuristics, and views on test-first. Use when asked to write, add, review, speed up or repair tests; to judge whether a suite is enough to refactor safely; to pin a bug fix or legacy code with tests; to choose between mocks, fakes, stubs, real containers or end-to-end; when tests are flaky, slow, brittle or unreadable or code is "hard to test". Reproducing a failure is craft-debugging; refactoring mechanics are craft-refactoring.
---

# Craft: testing

## Purpose

Tests are what let you change code without fear, state what code promises, and point at a defect within minutes of introducing it. This skill changes how you pick cases (by risk, boundary and state, not by line count), how you write them (readable, one concept each, seen failing once), where you put them (the cheapest level that can show the failure), and what you show the user as evidence that the tests do their job.

## Choose what applies

| Situation | Do this | Read |
|---|---|---|
| New or changed behaviour needs tests | Procedure A below | `references/what-to-test.md`, `references/writing-clean-tests.md` |
| A bug was reported or found | Procedure B: failing test first, then fix | `references/what-to-test.md` section 7 |
| About to refactor or change code with weak or no tests | Procedure C: characterisation tests, then hand off | `references/writing-clean-tests.md` section 11, `craft-refactoring` |
| Choosing unit versus component versus integration versus end-to-end; mock or real | Level and doubles rules below | `references/test-levels-and-doubles.md` |
| Two services or a client and an API must stay compatible | Contract testing | `references/contract-testing.md` (design and versioning of the API: `arch-api-design`) |
| Function with an inverse, an invariant, an oracle, algebraic laws, or many input shapes | Property tests next to examples | `references/property-based-testing.md` |
| Code is hard to test: logic in UI, clock, randomness, network, globals, singletons | Introduce seams | `references/testability-design.md` |
| Tests are flaky, slow, order-dependent, unreadable, or break on every change | Audit passes | `references/suite-audit-checklist.md`, `references/writing-clean-tests.md` |
| Reviewing tests in a pull request or asked "is this enough?" | Audit, then Verify below | `references/suite-audit-checklist.md` |
| "Should I do TDD?" or the user states an order | Decision rule | `references/test-first-views.md` |

This does not apply, or applies lightly, when:

- You are diagnosing a failure you cannot yet reproduce or locate. Use `craft-debugging` (this skill supplies the regression test at the end).
- The task is the mechanics of restructuring. Use `craft-refactoring`; come here only for the safety net.
- Code is a throwaway spike or script that will be deleted. Say so and skip, or test only what you will keep.
- You are asked to raise a coverage number. Coverage finds untested code; it does not show quality. Write tests for risk and report the number as a by-product.
- The question is load modelling or capacity (`arch-scalability-analysis`), security threat testing (`arch-api-security`), or fault behaviour of distributed systems (`arch-*`). This skill covers performance and resilience tests only as a category (`test-levels-and-doubles.md` section 2).
- The subject is a trivial accessor with no behaviour. Skip it (Refactoring 2e ch. 4), unless one line documents a default.

## How to apply

### Procedure A: tests for new or changed behaviour

1. Find the one command that runs the tests and run it before changing anything; note failures and skips that already exist (Clean Code E2). If there is no such command, say so; fixing that is part of the job.
2. State each behaviour in one given/when/then sentence, including what the code requires and promises (preconditions, postconditions). If the expected result is unclear, record the question as an ignored test with a reason and ask (Clean Code T4); do not guess silently.
3. Pick the level (rules below). Default to the lowest level where the behaviour can fail alone.
4. Derive cases, riskiest first: typical case, then boundaries (empty, one, zero, negative, limits, n-1/n/n+1), invalid input per the contract, sequences and state (`what-to-test.md` sections 3 to 5). Think how to break it. Stop when more tests would only restate cases you have.
5. Write each test as build, operate, check; one concept; named for the expectation; fresh fixture per test (`writing-clean-tests.md`). Extract a helper only when detail hides the intent.
6. See each test fail for the right reason: write it first and run it red, or temporarily break the production line and run it red, then revert (Refactoring 2e ch. 4).
7. Run the whole suite. Do not report done until all available tests pass (Pragmatic Programmer, Tip 63).
8. Run the quick audit in Verify.

### Procedure B: bug fix

1. Write an automated test that reproduces the bug through the lowest level that shows it. Run it; it must fail, and for the reason in the report (otherwise it may not trigger the bug and will not prove the fix).
2. Fix the code. The new test passes; run the full suite.
3. Test the neighbourhood: bugs congregate, so test the surrounding function and similar inputs more exhaustively (Clean Code T6).
4. Ask what gap in the suite let it through, and say so in the summary.
5. Keep any ad hoc check you used while diagnosing as a permanent test (Pragmatic Programmer ch. 6). Finding bugs once is the rule: a human should find a given bug only once (Tip 66).

### Procedure C: safety net before changing code that has none

1. Do not touch the code yet. Make a small test first: placeholder expected value, run, replace with the observed value after sanity-checking it, then inject a fault and confirm red, revert (Refactoring 2e ch. 4).
2. Cover the area by risk and boundary, not by every method. Tests of behaviour that nobody designed (crash on wrongly typed internal input) are not worth preserving; refactoring keeps observable behaviour only.
3. Name any recorded value you suspect is wrong, so nobody treats it as specification.
4. Hand off to `craft-refactoring`: small steps, test after each, never refactor on red, revert to green on failure.

### Choosing the level

Pick the lowest level that can fail for the reason you care about (Why Programs Fail ch. 3; Mastering API Architecture ch. 2):

| The behaviour you must pin | Level |
|---|---|
| Logic, computation, a state machine, parsing | unit |
| A service's handling of a request end to end in-process: status codes, auth, empty results | component |
| The shape of one interaction between two services | contract |
| The code talks correctly to a database, queue or HTTP dependency | integration with a real container or a contract-generated or recorded stub |
| A core user journey through several of your own services | end-to-end (few, realistic payloads, security on) |
| The failure only exists in the presentation layer | presentation-layer test with named controls, never coordinates |

Keep the totals pyramid-shaped; an inverted shape gives false confidence. Push edge cases down; keep journeys up.

### Doubles in one paragraph

Replace only what is slow, nondeterministic, external or outside the unit's purpose; keep the unit's own logic real. Prefer asserting outcomes over asserting calls; verify calls only when the call is the behaviour. Prefer stubs generated from a contract or real containers to hand-typed JSON, because stubs go stale while production moves (tests pass, production fails). Pass in time, randomness, identifiers and I/O so tests control them (`testability-design.md`).

### Rules that get used most

| Rule | Reason | Source |
|---|---|---|
| Test code gets production-quality care | messy tests become harder to change than the code, then get dropped | Clean Code ch. 9 |
| One concept per test; minimise asserts per concept; do not enforce "one assert" mechanically | single conclusion, readable failures; mechanical splitting adds duplication | Clean Code ch. 9 |
| Build, operate, check are visible | reader grasps intent without being overwhelmed | Clean Code ch. 9 |
| Fresh fixture per test | shared mutable fixtures cause order-dependent, intermittent failures | Refactoring 2e ch. 4 |
| F.I.R.S.T.: fast, independent, repeatable, self-validating, timely | slow or dependent tests stop being run | Clean Code ch. 9 |
| Every test is seen failing once | a pass proves little for code that already works | Refactoring 2e ch. 4; Pragmatic Programmer Tip 64 |
| Risk first, boundaries always | the middle is usually right; edges are where bugs are | Refactoring 2e ch. 4; Clean Code T5 |
| State coverage, not line coverage | one line can hide a million states | Pragmatic Programmer Tip 65 |
| A regression test for every bug, failing first | the same bug must not need finding twice | Pragmatic Programmer Tip 66 |
| Never refactor on a red bar; revert to green | keeps the suspect set small | Refactoring 2e ch. 4 |
| Do not skip or disable failing tests to proceed | overridden safeties accumulate | Clean Code G4 |
| Ambiguous requirement becomes an ignored test with the question | the question stays visible | Clean Code T4 |
| Tests run often and fast; a slow test will not be run | feedback delay turns into rot | Clean Code T9, F.I.R.S.T. |

## Verify

Run this before saying the tests are done. Each item has an observable answer.

1. **Run and report.** Run the project's one test command. Show the summary line (passed, failed, skipped). Skips and ignored tests each have a stated reason. No test that was green before is now red without explanation.
2. **Fail-first evidence.** For each new test, show the red result: either the test-first run or the output after you broke the production line, plus a clean diff on that production file afterwards (`git diff -- <file>` empty or showing only your intended change). For a bug fix show failing-before and passing-after.
3. **Independence.** Run the new tests alone, and the suite in random order if the stack supports it (adaptation: `pytest-randomly`, `jest --randomize`, `go test -shuffle=on`). Run them twice in a row.
4. **Repeatability.** Unit tests pass offline and with no real clock, random seed or environment dependence. Grep the new tests for `sleep`, `now()`, unseeded random, absolute paths and network URLs.
5. **Readability.** For each test write its given/when/then sentence. If you need "and also" for an unrelated behaviour, split. Names state expectations. No setup block copied into more than two tests.
6. **Boundary and state review.** For each comparison or loop bound in the changed code, name the tests at n-1, n, n+1; for each input, the classes and edges covered. Gaps are either added or listed as ignored tests with the question.
7. **Coverage gaps, not percentages.** If a coverage tool exists, run it on the changed files and read the unexecuted branches; for each, say it cannot fail or add a test. Do not quote a percentage as proof.
8. **Mutation spot-check** for risky logic: a mutation tool (adaptation: Stryker, mutmut, PIT, cargo-mutants) or three manual faults (flip a comparison, off-by-one, drop a branch). Report any that survive.
9. **Level check.** For each test, state the level and the real things it touches. A test labelled unit that touches a socket, a database or the clock is mislabelled or needs a seam. Stubs have a known origin.
10. **Speed.** Show the slowest tests if the suite grew noticeably. There is no threshold in the sources: "fast enough that you run it every few minutes".

Done means:

- the full suite passes with one command, and the output was shown;
- every new or changed behaviour has a test that was seen failing for the right reason;
- boundaries and invalid inputs of the changed code are tested or recorded as ignored questions;
- a bug fix includes a regression test that failed before the fix;
- no test was disabled, skipped or loosened to make the run pass, or each such case is listed with a reason;
- tests read as build, operate, check with names stating expectations;
- you stated what is not tested and why.

For a larger audit, work through `references/suite-audit-checklist.md`.

## Proportion and limits

- **Cost and benefit.** Writing too many tests tends to end in writing none; over-testing is far rarer than under-testing, but if you spend more time changing tests than the code under test, the tests are too coupled or too many (Refactoring 2e ch. 4). A small request gets a small set of well-chosen tests, not a suite rewrite.
- **Coverage.** No book gives a percentage. T1's ideal ("everything that could break") is a direction, not a threshold.
- **One assert per test.** Contested inside Clean Code itself; use one concept per test.
- **DRY versus DAMP.** The book's helper extraction can hide what a test does; keep the values that matter in view (`writing-clean-tests.md` section 6). This balance is added by the notes, not Martin's.
- **Test-first.** Sources disagree: Martin's thirty-second cycle against Ousterhout's "tactical programming" objection, with agreement on bug fixes. Use the rule in `test-first-views.md`; follow the user if they state an order.
- **"Dirty tests are worse than none"** overstates; the cost dynamic is real. Do not delete an inherited messy suite; improve it where you work.
- **Pyramid.** Authors of the API book hold firm to the pyramid; others use different shapes. Use the pyramid as the default and argue deviations from risk.
- **Mocks.** The books describe stubs and mocks but not a policy on mock-heavy styles; the rules here (state over interaction, real logic) are adaptation consistent with the sources, not their direct claims.
- **Dated material.** JUnit 3 idioms, embedded `main` test methods, GUI recorders and specific tool names in the sources are dated; the principles survive. The "HBchL" encoded-state assertion is better replaced by a named-set or custom matcher.
- **Property tests** give evidence, not proof (except exhaustive small domains). Use them where a crisp property exists; use examples where the behaviour is a table of business rules.
- **Contract tests** add a layer to learn and maintain. The source still recommends them for API work (producer contracts to start, consumer-driven later for internal APIs); where they are infeasible, careful component tests are the fallback, which the source calls error-prone and tedious.

## References

- `references/what-to-test.md` - read when choosing cases: purposes of tests, risk-first selection, boundary checklist, state coverage, testing against a contract, test data, regression tests per bug, patterns of failure, when the suite is enough, worked derivation.
- `references/writing-clean-tests.md` - read when writing or reviewing a test: build-operate-check, one concept, naming, helpers, DAMP versus DRY, dual standard, fresh fixtures, F.I.R.S.T. with checks, fail-first, characterisation, smells.
- `references/test-levels-and-doubles.md` - read when choosing the level or a double: quadrants, pyramid, level table, layer decision procedure, dependence inversion, component, integration, end-to-end, presentation tests, guideline tables.
- `references/contract-testing.md` - read when two services or a client and an API must agree: producer versus consumer-driven contracts, frameworks, storage, adoption steps, pitfalls.
- `references/property-based-testing.md` - read when a property or law exists: property categories, generators, procedure, shrinking versus sizes, laws as properties, library mapping.
- `references/testability-design.md` - read when code is hard to test or being designed: contracts first, bottom-up testing, separating logic from presentation, seams, explicit nondeterminism, test window, generated code.
- `references/suite-audit-checklist.md` - read when auditing a suite or PR: ordered passes with commands, T1-T9 with checks, sufficiency for refactoring, evidence to show, warning-sign index.
- `references/test-first-views.md` - read when choosing test order or answering a TDD question: the positions, the real disagreement, the decision rule.

## Sources

- Clean Code 1st ed. ch. 9 (unit tests, three laws, clean tests, F.I.R.S.T.) and ch. 17 (T1-T9, E1-E2, G3, G4, G5, G13, G22, G31, G33, G36).
- Clean Code 2nd ed. excerpt: outline and front matter (testing chapters named by heading only), ch. 3 first principles (tests kept green while restructuring; assistants and architecture).
- Refactoring 2nd ed. ch. 4 (self-testing code, fixtures, fail-first, what to test, when the suite is sufficient).
- The Pragmatic Programmer ch. 6 (easy-to-test code, contracts, programming by coincidence, wizards) and ch. 8 (ruthless testing, state coverage, saboteurs, find bugs once, automation).
- Why Programs Fail ch. 3 (testing for debugging, test layers, isolating units, designing for testability).
- Functional Programming in Scala ch. 8 (property-based testing).
- Mastering API Architecture ch. 2 (quadrants, pyramid, contract, component, integration and end-to-end testing).
- A Philosophy of Software Design ch. 19 (unit tests enable refactoring; TDD critique; bug-fix exception).
