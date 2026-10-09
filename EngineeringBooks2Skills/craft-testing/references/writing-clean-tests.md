# Writing clean tests

How to write a test so that it stays readable, fails usefully and survives change. Use when writing tests, reviewing them, or when tests have become the slow part of changing code.

## Contents

1. Why test code gets production standards
2. The shape of a test: build, operate, check
3. One concept per test (and the one-assert dispute)
4. Naming
5. Helpers and the test language that grows
6. DAMP versus DRY (a balance the notes add)
7. The dual standard
8. Fixtures: fresh per test
9. F.I.R.S.T., with checks
10. Fail first: see every test fail
11. Characterisation: adding tests to code that already works
12. Finding missing tests by restating cases
13. Error versus failure; assertion messages
14. Smells in test code
15. Two rewrites (Python and TypeScript)

---

## 1. Why test code gets production standards

Clean Code ch. 9 tells a story. A team decided tests need not meet production standards: quick and dirty, poor names, long functions. Tests became harder to change than the code. Every production change broke tests that were hard to repair; the cost rose each release until the suite was the developers' main complaint and estimates ballooned; they discarded the suite; defects rose; fear of change stopped cleaning of production code; the production code rotted. The decision to let tests be messy caused it, not testing itself.

The rule drawn: test code is as important as production code and gets the same thought and care. The downward spiral is dirty tests, then hampered change, then dirtier code, then lost tests, then rot.

Caveat in the notes: "dirty tests are worse than no tests" overstates it as a universal claim, since even a messy suite catches regressions. The cost dynamic is real, though. Use the claim as a reason to keep tests clean, not as a reason to delete a messy suite you inherited.

Measurable symptom (inferred in the notes): time to repair a broken test after a production change is large relative to the production change.

## 2. The shape of a test: build, operate, check

Every test should read as three visible parts (Clean Code ch. 9): build the data, operate on it, check the result. Same as arrange-act-assert and given-when-then; Refactoring 2e ch. 4 adds an implicit fourth phase, teardown (removing the fixture between tests).

Checks:

- Can you point at the line where each part starts? Separate with blank lines or comments if the language does not help.
- The test contains only the data and calls it truly needs. Object wiring, path parsing, casting, building a request URL by hand are detail that belongs in a helper.
- A reader should work out what the test does quickly without being misled or overwhelmed by detail.

## 3. One concept per test (and the one-assert dispute)

Clean Code ch. 9 considers, then rejects as a hard rule, "one assert per test".

- The idea (Dave Astels): each test reaches a single conclusion that is quick to understand. To apply it you split "response is XML" and "response contains these tags" into two tests with given/when/then helpers.
- The cost: the given and when parts are duplicated. Remedies are a template method in a base class, or a separate test class with the shared part in setup. Martin judges these "too much mechanism for such a minor issue" and prefers multiple asserts in that case.
- The better rule: test one concept per test function and minimise asserts per concept. It is not the number of asserts that causes trouble; it is testing more than one concept.

Refactoring 2e ch. 4 agrees on the general rule (a test stops at its first failed assertion, which can hide information while debugging) but tolerates two closely connected assertions and splits later.

Decision rule:

| Situation | Do |
|---|---|
| Several asserts all check one outcome of one operation | keep them; try to fold them into one expressive assertion via a helper or custom matcher |
| The test checks "one miscellaneous thing after another" (several scenarios in sequence, e.g. a `testAddMonths` with nine asserts) | split into one test per concept, each stated as given/when/then |
| Splitting duplicates a small setup | keep several asserts in one test |
| Splitting duplicates a large recurring setup | lift the setup into a fixture or helper |

Check: can you state the test as one given/when/then sentence? If you need "and also" for an unrelated behaviour, split.

## 4. Naming

- A test name states the expectation, not the method under test: `symbolic_links_are_not_in_xml_page_hierarchy` rather than `testPageHierarchy2` (Clean Code ch. 9 improved the names alongside the structure).
- Names must contain enough text to identify which test failed (Refactoring 2e ch. 4). Some people leave descriptions empty because they duplicate the code; if you do, the code must be readable on its own.
- If you cannot name the test without "and", it holds more than one concept.
- Names of the helpers follow the domain: `make_pages`, `submit_request`, `assert_response_contains`, not how the objects are wired.

## 5. Helpers and the test language that grows

Clean Code ch. 9: do not write tests directly against the production API the programmers use. Build a layer of helper functions on top of it (`make_page_with_content`, `submit_request`, `assert_response_contains`) that becomes a specialised API used only by tests. These map onto fixtures, factories, builders, custom matchers.

Key point: that testing API is not designed up front. It evolves by repeatedly refactoring test code that has become cluttered with obscuring detail. Trigger for extracting a helper: detail hides the intent.

Rules:

1. Extract at the level of the domain (what is set up, requested, asserted), not the mechanics of how objects are wired.
2. Duplicated setup and assert blocks across tests are a smell (Clean Code G5) and get extracted.
3. Compose assertions to cut eye-bouncing. In the book's controller example five separate on/off asserts were replaced by one comparison of an encoded state string (uppercase letter = on, lowercase = off, fixed device order). The book itself flags this as close to violating "avoid mental mapping". Prefer a named-set or custom-matcher comparison with a better failure message, for example `assert on(hw) == {"heater", "blower", "lo_alarm"}`. If you do use an encoding, document the legend in one place and use it where many tests check the same fixed set of flags.
4. Hide setup behind intention-named helpers: `way_too_cold()` rather than set-temperature-then-tick.

## 6. DAMP versus DRY (a balance the notes add)

Heavy helper abstraction can hide what a test actually does. Many practitioners prefer tests that are DAMP (descriptive and meaningful phrases) over strictly DRY, tolerating some duplication for local readability. This is the notes' counterweight to the book's helper advice (it is not Martin's claim). Decide with this rule:

- If, to understand why a test passes, the reader must open a helper and read its body, the helper hides too much. Inline it, or make its name state what it does.
- If the same ten lines of setup appear in twelve tests and none of the differences matter, extract.
- A test should show the values that matter to its expectation. A helper `cart_with(pens(3), coupon=ten_percent())` shows quantity and coupon; it hides cart wiring. A helper `standard_cart()` hides everything, including the inputs the assertion depends on.

Refactoring 2e ch. 4 removes duplication in tests through the per-test setup hook, never through shared mutable state.

## 7. The dual standard

Clean Code ch. 9: test code has a different standard from production code in exactly one dimension, efficiency of CPU and memory. It must still be simple, succinct and expressive. Things you would never do in production for performance reasons are fine in a test double (the book's example builds a state string by repeated concatenation inside a mock, unacceptable on the real embedded target). Cleanliness is never traded. The StringBuffer remark is dated Java; the principle is that doubles need not be optimised.

## 8. Fixtures: fresh per test

Refactoring 2e ch. 4:

- Do not build the shared object once at suite level. A constant reference only freezes the reference; a later test that mutates the object makes results order-dependent and intermittent, and confidence in the tests collapses.
- Build the fixture in the per-test setup hook (`beforeEach`, pytest fixture with function scope, `setUp`) so each test starts clean. It also tells the reader every test in the block starts from the same base data.
- "It's slow" is rarely true. If it is, share a fixture only when it is truly immutable or provably never changed.

## 9. F.I.R.S.T., with checks

Clean Code ch. 9. The right column is how the agent checks the property in a repository.

| Letter | Rule | Failure when violated | How to check |
|---|---|---|---|
| Fast | tests run quickly | slow tests are not run often, so problems are found late, you stop feeling free to clean the code, code rots | time the suite (`pytest --durations=10`, `jest --verbose`, `go test -v`); list the slowest tests; the book gives no threshold, so use "fast enough that you run it every few minutes" |
| Independent | no test sets up conditions for another; runnable alone, in any order | cascade of downstream failures, hidden defects, hard diagnosis | run one test alone; run the suite in random order (adaptation: `pytest-randomly`, `jest --randomize`, `go test -shuffle=on`); both must pass |
| Repeatable | same result in any environment | always an excuse for failure; cannot run when the environment is down | run with the network disabled or on a clean container; run twice in a row and confirm the second run starts from the same state |
| Self-validating | boolean outcome | failure becomes subjective, needs manual log reading or diffing | the exit status of one command says pass or fail; no test needs a person to read output |
| Timely | written just before the production code | tests written afterwards find the code hard to test; you may decide it is "too hard to test" | see `test-first-views.md`; the durable core is that testability shapes the design |

Reading note: "repeatable in production environment" means environment-independent, not "run unit tests against production".

## 10. Fail first: see every test fail

Refactoring 2e ch. 4: always make sure a test will fail when it should. A test written against code that already works passes immediately, and a pass proves little. Temporarily inject a fault into the production code, confirm the test fails with a useful message ("expected X to equal Y"), then revert. Every test should be seen failing at least once. In test-first work the red step is that proof.

Agent procedure:

1. Write the test; run it; if it passes against unchanged code that you believe is correct, that is expected.
2. Edit the production line it exercises so it is wrong (flip a comparison, change a constant, return early).
3. Run the test; it must fail, and the message must tell you what went wrong.
4. Revert the edit (`git diff` on the production file must be empty again).

## 11. Characterisation: adding tests to code that already works

Refactoring 2e ch. 4 pattern for tests on existing code:

1. Write the test with a placeholder expected value.
2. Run it; replace the placeholder with the value the code actually produced, after checking it is plausible (or compute it by hand).
3. Inject a fault; confirm it fails.
4. Revert the fault.

This records current behaviour, bugs included. Say so in the test name or a comment when you suspect the recorded value is wrong, so nobody reads it as a specification.

The chapter assumes tests can be added cheaply; for legacy code with poor coverage and no seams, Fowler points to Feathers' book on legacy code (the notes carry no detail from it), and `testability-design.md` section 5 covers the seams.

## 12. Finding missing tests by restating cases

Clean Code ch. 9: a long `testAddMonths` that checks three scenarios in sequence became independent given/when/then tests. Restating them exposed the general rule hiding in the cases (when incrementing a month, the day cannot exceed the last day of the target month), and that exposed a missing test (28 Feb plus one month should give 28 Mar). Technique: after splitting, write the rule above the tests in one sentence and ask which case the rule implies that no test covers.

## 13. Error versus failure; assertion messages

- A failure is a verify step whose actual value is outside expected bounds. An error is an unexpected exception raised earlier, such as in setup (Refactoring 2e ch. 4). Frameworks may report both as failures; know which you are looking at.
- Test the failure path with a precise assertion on the error type and message the contract promises (Pragmatic Programmer ch. 6 sqrt example: a thrown error is expected for a negative argument and a failure otherwise).
- Prefer assertions whose failure output shows the actual and expected values. A bare `assert ok` hides what you need.

## 14. Smells in test code

| Smell | Why it hurts | Fix |
|---|---|---|
| Body dominated by object construction, casts, string building | intent buried | helper at domain level |
| Copy-pasted tests with minor variations | duplication (G5) | parametrised test or a helper; keep what differs visible |
| Test named `testX` covering several scenarios | more than one concept | split by concept |
| Order dependence, or fails alone | not independent | fresh fixture per test |
| Needs network, a specific database, or a machine | not repeatable | isolate the dependency (`test-levels-and-doubles.md`) |
| Pass judged by reading a log or comparing files | not self-validating | assert in code |
| Fixed sleeps or absolute screen coordinates | fragile synchronisation (Why Programs Fail ch. 3) | wait on a condition; named controls |
| A test that works once but fails on the second run | state left behind | setup and teardown restore initial state |
| Tests left failing, skipped or commented out | overridden safety (G4) | fix, or record as an ignored test with the question |
| High coverage but unreadable tests | false confidence (inferred) | read the tests; fault-inject |
| Test restates the implementation | proves nothing new | assert an observable behaviour from a different angle |

## 15. Two rewrites

Python, noisy and multi-concept, then split with a small test language (fresh code, after Clean Code ch. 9):

```python
# before
def test_cart():
    c = Cart(); c.items.append(Item("pen", Decimal("2.00"), 3)); c.recalc()
    assert c.total == Decimal("6.00")
    c.coupon = Coupon("TEN", 10); c.recalc()
    assert c.total == Decimal("5.40")

# after: build / operate / check visible, one concept each
def test_total_is_sum_of_line_totals():
    cart = cart_with(pens(3))
    assert total_of(cart) == money("6.00")

def test_percentage_coupon_reduces_total():
    cart = cart_with(pens(3), coupon=ten_percent())
    assert total_of(cart) == money("5.40")
```

TypeScript, fresh fixture per test (after Refactoring 2e ch. 4):

```ts
describe("province shortfall", () => {
  let province: Province;
  beforeEach(() => { province = sampleProvince(); });   // new object every test

  it("equals demand minus total production", () => {
    expect(province.shortfall).toBe(5);
  });
  it("is the whole demand when there are no producers", () => {
    province = new Province({ ...sampleData(), producers: [] });
    expect(province.shortfall).toBe(30);
  });
});
```
