# What to test

Deciding which cases deserve a test, and when a suite is enough. Read this before writing tests for new code, before adding a safety net around code you are about to change, and when someone asks "is this tested enough?".

## Contents

1. What tests are for
2. Choosing cases: risk first
3. Boundary and "play the enemy" checklist
4. State coverage, not line coverage
5. Testing against a contract
6. Test data: real and synthetic
7. The regression test for every bug
8. Reading patterns of failure
9. Unanticipated input: test it or not
10. Questions the tests cannot answer (ignored tests as questions)
11. How much is enough
12. Worked derivation (adaptation)
13. Kinds of testing to remember exist

---

## 1. What tests are for

Name the purpose before writing the test, because it changes what you write.

| Purpose | What it demands of the test | Source |
|---|---|---|
| Safety net for change | Fails when behaviour breaks, passes when only structure changes. Behavioural, not tied to implementation. | Refactoring 2e ch. 4; Clean Code ch. 9; APOSD ch. 19 |
| Specification / example of use | Readable as a statement of what the unit promises; names say the expectation. | Pragmatic Programmer ch. 6 (tests give usage examples); Clean Code ch. 9 |
| Defect localisation | Small scope and fast, so a red result points at code written minutes ago. | Refactoring 2e ch. 4; Why Programs Fail ch. 3 |
| Debugging aid | Automatic pass/fail on a known failure, rerunnable many times. | Why Programs Fail ch. 3 |
| Design feedback | Hard-to-write tests reveal coupling (see `testability-design.md`). | Pragmatic Programmer ch. 6 (Tip 48), Clean Code ch. 9 |

Reasoning for the first two rows: tests are what remove the fear of changing code. With a good suite developers restructure confidently; without one they minimise every diff and complexity accumulates (APOSD ch. 19, which cites a large interpreter replacement where the unit suite exposed so many bugs that only one surfaced after alpha). Clean Code puts it as: unit tests, not architecture, keep code flexible.

Why localisation works: if a test passed before and fails now, the cause is in the small amount of code written since the last run, so finding it takes minutes. This only holds if you run the tests often (Refactoring 2e ch. 4).

Testing for validation (find unknown problems) and testing for debugging (aim at a known problem) are different jobs. A test written to reproduce a known failure is reused to simplify, observe and verify the fix, then kept as a regression test (Why Programs Fail ch. 3). For the reproduction work itself use `craft-debugging`.

## 2. Choosing cases: risk first

Test what could plausibly break, now or later, not every public method (Refactoring 2e ch. 4).

1. Rank the behaviour by risk: complicated logic, derived values updated by setters, parsing, arithmetic, state transitions, anything you are nervous about. Start there; this gives the most benefit per effort.
2. Skip what cannot meaningfully fail: trivial accessors that read or write a field, simple setters. Clean Code T3 pushes the other way ("don't skip trivial tests", they are cheap and document behaviour). Resolve this by cost: a trivial test that costs two lines and documents a default value is fine; a test file full of getter echoes is noise. Do not let the decision block you.
3. Prefer incomplete tests that run over complete tests that never get written. Writing too many tests tends to end in writing none; over-testing is far rarer than under-testing (Refactoring 2e ch. 4).
4. Keep adding while you work. You understand the program better as you go and find more bugs.
5. Do not let the fear that testing cannot catch every bug stop you from catching most (Refactoring 2e ch. 4).

Clean Code T1 sets the ideal: a suite should test everything that could possibly break, and "that seems like enough" is not a measure. No threshold is given; use the coverage and fault-injection checks in section 11 instead.

## 3. Boundary and "play the enemy" checklist

"The middle of an algorithm is usually right; boundaries are where it is misjudged" (Clean Code T5, G3: do not trust intuition, look for every boundary condition and write a test). Think how to break the code.

| Kind of input | Cases to try |
|---|---|
| Collections | empty; one element; two; duplicates; very large; unsorted vs sorted vs reversed (Pragmatic Programmer ch. 8 on presorted input exposing a degrading algorithm) |
| Numbers | zero; one; negative; maximum and minimum representable; just inside and just outside every limit (n-1, n, n+1); non-integers if floats arrive |
| Strings from outside | empty; blank; whitespace only; unparseable (an empty string parsing to NaN in Refactoring's example); very long; non-ASCII (inferred) |
| Dates | invalid calendar dates such as February 29 in a non-leap year (Pragmatic Programmer ch. 8); month ends: adding one month to the 31st of a month (Clean Code ch. 9); the case the rule implies but nobody wrote (28 Feb plus one month) |
| Types | wrong type in a constructor argument, null/undefined/None |
| Records | huge record sizes; foreign formats such as non-local postal codes (Pragmatic Programmer ch. 8) |
| Sequences of calls | wrong order; repeated call; call after failure; call twice (a second run that fails because the first left state behind) |
| Environment | resource exhaustion: memory, disk, CPU, wall-clock time, bandwidth; a missing optional dependency |

Writing these tests raises design questions (should a negative demand be rejected or clamped?). Answering them is part of the value. When the answer is "undefined, ask the owner", record it as an ignored test (section 10) rather than silently picking.

Scatter of `+1`/`-1` in production code is the production-side sign that boundaries are not encapsulated (Clean Code G33); fix it in one place and test that one place.

## 4. State coverage, not line coverage

Tip 65 (Pragmatic Programmer ch. 8): test state coverage, not code coverage.

Example from the book: `f(a, b) = a / (a + b)` with each argument 0..999. Three lines, one million logical states; 999,999 work and one fails (`a + b == 0`). A test that executes the line says nothing about that state.

What to do with it:

- Treat line coverage as a map of what is untested, never as proof of what is tested. Run it, look at the unexecuted `if` and `catch` bodies (Clean Code T2: coverage tools show gaps with red/green marking), and decide for each whether it can fail.
- Partition the input space into classes that behave alike and test one from each class plus every edge between classes. Data used and the order in which code is traversed matter more than which lines ran, so vary both: input classes, call sequences.
- The notes mark "partition and probe" as a practical consequence the agent should draw (inferred); the book itself says only that you can never be sure you have tested enough.

## 5. Testing against a contract

Unit testing is checking that a unit honours its contract, and it also checks that the contract means what you think (Pragmatic Programmer ch. 6). Derive tests from the contract:

| Contract element | Test |
|---|---|
| Precondition | invalid input is rejected in the way the contract says |
| Boundary of the precondition | the exact edge is accepted (zero for a square root) |
| Postcondition | for values across the legal range, the stated relation holds (squared result close to the argument within tolerance) |
| Invariant | holds after each operation in a sequence |

Test combinations bottom-up: if module A uses LinkedList and Sort, test LinkedList's contract fully, then Sort's, then A's. If the first two pass and A fails, the defect is in A or in A's use of its parts, so debugging is focused (Pragmatic Programmer ch. 6). The same reasoning argues for passing the unit tests before the integration tests (Pragmatic Programmer ch. 8: if parts do not work alone they will not work together).

Write assertions for assumptions too: when you are about to rely on behaviour you cannot point to documentation for, "don't guess; actually try it" with an assertion or test. If right, you improved the documentation; if wrong you found out early (Pragmatic Programmer ch. 6, Tip 44). This matters most for generated or copied code you did not write: test the behaviour you depend on.

See `craft-error-handling` for assertions and contracts as design tools. This file only covers using the contract to choose cases.

## 6. Test data: real and synthetic

You need both because they expose different bugs (Pragmatic Programmer ch. 8).

- Real-world data (from an existing system, a competitor, a prototype): shows what "typical" means, and is the most likely to reveal misunderstood requirements.
- Synthetic data, when you need: (1) volume beyond any real sample (seed from real data, vary unique fields); (2) boundary conditions; (3) specific statistical properties (every third transaction fails; presorted versus random input).

Agent note (adaptation): real data from production needs personal data removed before it goes into a repository. Where no real sample exists, say so and ask, rather than inventing "typical" values.

## 7. The regression test for every bug

Find bugs once (Pragmatic Programmer ch. 8, Tip 66): when a bug slips past the tests, add a test that traps it, every time, however trivial and however sure the developer is it will not recur. Once a human found it, a human should never find it again.

Workflow:

1. Write an automated test that reproduces the bug. Run it and confirm it fails, and fails for the reason in the report (APOSD ch. 19 gives the reason: otherwise the test may not trigger the bug at all and will prove nothing about the fix).
2. Fix the code.
3. Confirm the new test passes and run the full suite before declaring done (Tip 63: coding is not done until all available tests pass).
4. Ask which class of states the bug belongs to and add neighbouring cases. Bugs congregate: when you find one in a function, test that function exhaustively (Clean Code T6).
5. Ask whether the bug reveals a gap in the suite itself (Refactoring 2e ch. 4).
6. Ad hoc checks made while debugging (a print statement, a snippet in a debugger) are formalised before the session ends and added to the suite (Pragmatic Programmer ch. 6).

APOSD ch. 19 accepts test-first for exactly this case even though it rejects it as a general design method (see `test-first-views.md`).

## 8. Reading patterns of failure

When many tests fail, look at the pattern before reading any single failure (Clean Code T7, T8; used in the SerialDate case study).

- Complete, sensibly ordered cases expose patterns: every input longer than five characters fails; every case with a negative second argument fails. The red/green pattern alone can suggest the cause.
- Compare which code ran in passing tests with which code ran in failing ones (T8).
- Order your cases so such patterns are visible: sorted by size, grouped by input class.

For hypothesis-driven diagnosis beyond this, hand off to `craft-debugging`.

## 9. Unanticipated input: test it or not

When a test reveals a crash on input nobody planned for (Refactoring 2e ch. 4, e.g. producer data given as the wrong type):

- Input from a trusted source in the same code base: leave it. Duplicating validation between internal modules causes more trouble than it is worth.
- Input from an external source (a JSON request, a file, a user): validate and test the rejection.
- When bad data could propagate and be hard to debug later, fail fast with an assertion and do not write a test for the assertion; the assertion is itself a form of test.
- When writing tests as a safety net before a refactoring, discard tests that cover unanticipated-input behaviour: refactoring preserves observable behaviour only, so you need not preserve how it fails on inputs nobody designed for.

## 10. Questions the tests cannot answer

When a requirement is ambiguous, record the question as a test that is marked ignored (an annotation, or commented out if the ambiguous thing would not compile) so the question stays visible and executable later (Clean Code T4).

Rules that keep this from becoming clutter (adaptation):

- Every ignored/skipped test carries a one-line reason that states the question or the ticket.
- Never ignore a test because it is failing and inconvenient. Disabling a failing test "for now" is an overridden safety (Clean Code G4): each override was convenient, and Chernobyl-style failures are chains of them.
- Report skipped tests in the summary you show the user.

## 11. How much is enough

The book offers no objective measure. Use these in combination:

1. Confidence question (Refactoring 2e ch. 4): "How confident are you that if someone introduces a defect into the code, some test will fail?" If you can refactor, see green, and be pretty sure you broke nothing, the suite is good enough. Caveat: false confidence is not accounted for.
2. Fault injection: temporarily break the production code in the way the test is meant to catch (change an operator, remove a line), confirm the test goes red with a useful message, then revert. Every test should be seen failing at least once. The project-scale form is a saboteur who works on a separate copy of the tree and plants bugs to see if the tests notice (Pragmatic Programmer ch. 8, Tip 64). Automated, this is mutation testing (the books do not name it; Clean Code 2e's table of contents lists "Mutation Testing" under relentless improvement, headings only). Tools (adaptation): Stryker for JS/TS, mutmut for Python, PIT for Java, cargo-mutants for Rust.
3. Coverage to find untested areas only (T2; Refactoring 2e ch. 4: coverage identifies untested code, it does not judge quality).
4. Signals of too many tests: you spend more time changing tests than the code under test, and the tests slow you down (Refactoring 2e ch. 4).
5. Tests run fast and deterministically, so you actually run them every few minutes (T9, Refactoring 2e ch. 4). Refactoring 2e ch. 4 suggests running the tests for the code you are working on every few minutes and all tests at least daily; Pragmatic Programmer ch. 8 adds running them before every check-in and running all available tests in a scheduled build, so a regression is attributed to that day's changes.
6. A second pair of eyes on the tests. Why Programs Fail ch. 3 lists "have others test" among its essential rules: testing is destructive work, and authors are psychologically poorly placed to test their own code. For an agent that wrote both code and tests, adapt this by deriving cases from the contract or requirement rather than from the implementation just written, and by fault-injecting (item 2) so the tests are checked by something other than your own reading. The same list says to measure statement and branch coverage and add random inputs for extremes (property tests, `property-based-testing.md`).

## 12. Worked derivation (adaptation, fresh example)

Function: `page_count(item_count, page_size)` returns how many pages are needed. Contract: `item_count >= 0`, `page_size >= 1`; result is the smallest number of pages that hold all items; zero items needs zero pages.

| Class | Cases | Expected |
|---|---|---|
| Empty | `(0, 10)` | 0 |
| Below one page | `(1, 10)`, `(9, 10)` | 1 |
| Exactly one page | `(10, 10)` | 1 |
| Just over | `(11, 10)` | 2 |
| Exact multiple | `(20, 10)`; `(21, 10)` | 2; 3 |
| Smallest page size | `(5, 1)` | 5 |
| Precondition violations | `(-1, 10)`; `(5, 0)`; `(5, -3)` | rejected as the contract says |
| Large | `(10**9, 7)` | postcondition holds: `pages*size >= items > (pages-1)*size` |

The off-by-one boundaries (9/10/11, 20/21) are where the real bugs live; the large case checks the postcondition rather than a hand-computed number. If the contract were silent on `page_size = 0`, the right move is an ignored test with the question, not a guess.

## 13. Kinds of testing to remember exist

Pragmatic Programmer ch. 8 lists what a project may need beyond unit tests. Use as a prompt for "what have we not considered".

| Kind | Question it answers |
|---|---|
| Unit | does the module meet its contract? The foundation: parts that fail alone will not work together |
| Integration | do subsystems honour each other's contracts? Without tested contracts this is often the largest source of bugs |
| Validation and verification | is what we built what users need? Start as soon as there is a prototype; watch how real access patterns differ from developer data |
| Resource exhaustion, errors, recovery | when memory, disk, CPU, time, bandwidth run out, does it fail gracefully, saving state, or crash in the user's face? |
| Performance | does it meet requirements under real load? Needs a realistic environment |
| Usability | with real users in real conditions; failing usability criteria is as big a bug as dividing by zero |
| Design metrics | compute per-module metrics (lines, cyclomatic complexity, inheritance fan-in/out, coupling), look for outliers, ask whether each outlier is justified |

Regression testing compares current output with previous or known values; any kind above can be run as a regression test. Place stress tests that cannot run on every commit on a regular schedule with resources allocated, not "when someone remembers" (Pragmatic Programmer ch. 8).
