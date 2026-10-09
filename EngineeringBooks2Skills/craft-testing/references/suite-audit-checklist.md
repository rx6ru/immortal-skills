# Suite audit checklist

Ordered passes for reviewing a test suite or the tests in a pull request, with the check the agent can run for each. Use when asked "are these tests good", "is this enough to refactor safely", "why is the suite slow or flaky", or before reporting work as done.

## Contents

1. How to run an audit
2. Pass 0: can the suite be run at all (E1, E2)
3. Pass 1: the T1-T9 heuristics
4. Pass 2: F.I.R.S.T.
5. Pass 3: structure and readability
6. Pass 4: do the tests detect faults
7. Pass 5: coverage of risk and states
8. Pass 6: levels, doubles and stubs
9. Pass 7: overridden safeties and clutter
10. Sufficient to refactor? the decision
11. Evidence to show the user
12. Warning signs index

---

## 1. How to run an audit

Work in order; stop and fix or report at the first pass that fails badly, because later passes assume earlier ones hold (a suite that cannot run says nothing about coverage). Time-box each pass to what the change or request needs. For a pull request audit only the tests touched or required by the change plus the suite's overall state; for "is this suite good enough to refactor" run all passes on the area to be changed.

Treat the codes as prompts for judgment, not a linter: Clean Code ch. 17 states that clean code is not written by following a set of rules, and the list is an expression of values.

## 2. Pass 0: can the suite be run at all (E1, E2)

| Check | Command or evidence |
|---|---|
| One command builds from a clean checkout (E1) | run it in a fresh clone or container |
| One command runs all tests (E2); quick, easy, obvious | `make test`, `npm test`, `pytest`, `go test ./...`, `cargo test` |
| The exit status says pass or fail | `echo $?` after the run |
| Baseline recorded | note failing or skipped tests that exist before your change |

## 3. Pass 1: the T1-T9 heuristics

Clean Code ch. 17, Tests entries. The book gives no numeric thresholds for any of them.

| Code | Heuristic | How to check |
|---|---|---|
| T1 Insufficient tests | A suite should test everything that could possibly break. "That seems like enough" is not a metric. Insufficient while any condition is unexplored or any calculation is unvalidated. | list the behaviours and conditions in the changed code; point to a test for each; unexplored ones are findings |
| T2 Use a coverage tool | Reports expose gaps; red/green line marking finds untested `if` and `catch` bodies quickly. | run the coverage report on the changed files; read the unexecuted branches; decide for each whether it can fail |
| T3 Don't skip trivial tests | Cheap to write; documentary value exceeds cost. | spot where default values, simple mappings or formatting are unpinned; add a one-line test if it documents behaviour |
| T4 An ignored test is a question about an ambiguity | Record doubts about requirements as ignored (or commented-out) tests. | list skipped tests; each should state a question; delete the ones that are only dead |
| T5 Test boundary conditions | The middle of an algorithm is usually right; boundaries are where it is misjudged. | for each comparison and loop bound in the code, a test at n-1, n, n+1 |
| T6 Exhaustively test near bugs | Bugs congregate. | after any bug, test the whole function and its siblings |
| T7 Patterns of failure are revealing | Complete, sensibly ordered cases expose patterns (all inputs longer than five characters fail). | arrange cases by size and class; read red/green as a pattern |
| T8 Test coverage patterns are revealing | Compare which code passing tests execute and which they do not, for clues about why failing tests fail. | diff coverage of passing and failing runs |
| T9 Tests should be fast | A slow test is a test that will not get run; under pressure slow tests are dropped first. | time the suite; show the slowest ten |

Related Clean Code codes that bear on tests: G3 incorrect behaviour at boundaries (do not trust intuition; test every boundary), G4 overridden safeties (skipped failing tests, disabled warnings), G5 duplication (duplicated setup and asserts in tests), G9 dead code.

## 4. Pass 2: F.I.R.S.T.

Commands in `writing-clean-tests.md` section 9. Summary of what to run:

- Fast: durations report; slowest tests listed.
- Independent: run one test alone; run in random order.
- Repeatable: run offline; run twice in a row.
- Self-validating: exit status only.
- Timely: were tests written close to the code? Check git history or ask; if the code is "too hard to test", see `testability-design.md`.

Refactoring 2e adds: never refactor on a red bar; if the suite goes red, revert to the last green checkpoint.

## 5. Pass 3: structure and readability

For each test touched:

1. State in one sentence what behaviour it specifies. If you cannot, or if details obscure it, the test needs helpers or a rename.
2. Build, operate and check are visible.
3. One concept per test; no "and also" for an unrelated behaviour.
4. The name states the expectation.
5. Duplicated setup and assert blocks across tests are extracted; helpers are named for the domain, and do not hide the values the assertion depends on (DAMP caution in `writing-clean-tests.md` section 6).
6. Tests are given the same production-quality review as code: naming, size, duplication.
7. No logic in tests (loops, conditionals computing expected values by re-implementing the code under test) unless that is the oracle you chose on purpose (adaptation).

## 6. Pass 4: do the tests detect faults

The most informative pass; the one most often skipped.

1. For each new or changed test, apply fault injection once: break the production line, expect a clear red, revert (`writing-clean-tests.md` section 10). Show the red output.
2. For a larger area, run a mutation tool if the stack has one (adaptation: Stryker, mutmut, PIT, cargo-mutants) and report surviving mutants in the area of the change. Surviving mutants are the unprotected behaviours.
3. The project-scale form is a saboteur working in a separate copy of the tree (Pragmatic Programmer ch. 8, Tip 64).
4. Check for tests that have never been seen to fail (listed as a warning sign in that chapter).

The confidence question (Refactoring 2e ch. 4): how sure are you that if someone introduces a defect here, some test will fail?

## 7. Pass 5: coverage of risk and states

1. List the risky behaviours (section 2 of `what-to-test.md`); map each to a test.
2. Boundary checklist (`what-to-test.md` section 3) applied to the changed code.
3. States, not lines (Tip 65): for each input, name the classes and the edges; check at least one test per class and edge. Coverage percentage is not the criterion; there is no percentage in the books.
4. Every fixed bug has a regression test that failed before the fix (Tip 66; APOSD ch. 19). Check `git log` for fixes without test changes.
5. Rules the code implies but the tests do not state (the 28 February plus one month gap).

## 8. Pass 6: levels, doubles and stubs

1. The suite is pyramid-shaped: most unit, fewer component, integration and contract, few end-to-end. End-to-end only for core journeys, with security on and realistic payloads.
2. Doubles replace what is slow, external or nondeterministic, not the unit's own logic.
3. Stubs have a known origin (generated from a contract, recorded with a date, or hand-written and flagged); hand-typed JSON that nobody validates is a finding.
4. Integration tests check the interaction at the boundary, not the dependency's own behaviour.
5. Contracts exist for service interactions with known consumers (`contract-testing.md`).
6. Performance tests, if any, run in a like-for-like environment against stated objectives.

## 9. Pass 7: overridden safeties and clutter

- Skipped, ignored or commented-out tests without a stated question or ticket (G4, T4).
- Disabled warnings or linters in test files.
- Commented-out code, change logs and echo comments in tests (C1, C3, C5).
- Dead helpers and unused fixtures (G9, G12).
- Fixed sleeps, absolute screen coordinates.
- Test code with different conventions across files (G11, G24).

## 10. Sufficient to refactor? the decision

Refactoring 2e ch. 4 criteria, plus the checks above:

| Question | Yes means |
|---|---|
| Is the suite green and quick to run on demand? | you can run it after each small step |
| Does a deliberately injected defect in the area make a test fail? | the net catches what you could break |
| Are the boundaries and the states of the area tested? | coverage of risk |
| Are the tests behavioural (assert observable outcomes) rather than implementation-coupled? | refactoring will not turn them red for the wrong reasons |
| Is each fixed bug pinned? | old defects will not return |

If any answer is no, add characterisation tests around the area first (`writing-clean-tests.md` section 11) and then hand off to `craft-refactoring`. Fear reduction depends on test quality as much as coverage (the notes' caveat).

## 11. Evidence to show the user

Present facts, not adjectives:

- the command run and its summary line (counts of passed, failed, skipped);
- skipped tests listed with reasons;
- for each new test, the red output from fault injection (or the test-first red run) and the line of production code you broke;
- the coverage or mutation result for the changed region, with surviving mutants or unexecuted branches named;
- timing of the slowest tests if speed was in question;
- what you did not test and why (a boundary left as an ignored test with its question).

## 12. Warning signs index

From the notes, one place to scan:

- Tests copy-pasted with small variations; bodies full of construction and casting.
- Test names that do not say what is checked; `testX` covering several scenarios.
- Attitude that tests "just need to pass or cover".
- Failing, skipped or commented-out tests accepted as normal.
- Rising time to change code, blamed on "the tests".
- Tests that must run in order, or fail alone.
- Tests needing a network, a particular database or a machine.
- Pass judged by reading a log or diffing files.
- Production code declared too hard to test.
- A slow suite that people avoid running.
- A written test plan nobody runs; testing scheduled at the end; coverage percentage as the definition of sufficient.
- A test that has never been seen to fail; the same bug reported twice.
- Application logic reachable only through the UI.
- Only invented data, or only production samples without boundary data.
- Stress or performance tests run "when someone remembers".
- Results that need a human to read output and decide.
- Scripts with absolute screen coordinates or fixed waits.
