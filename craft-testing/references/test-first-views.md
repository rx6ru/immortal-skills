# Views on test-first

The sources disagree about when tests should come before code. This file lays out each position, what the disagreement is really about, and a rule the agent can apply in context. Use when deciding whether to write the test first, when a user asks for TDD or says not to use it, or when you need to justify the order you worked in.

## Contents

1. The positions
2. Where they actually disagree
3. What every position keeps
4. Decision rule for the agent
5. How to work test-first in short cycles
6. Test && commit || revert and small bundles (headings only)
7. Verify
8. Limits of the notes

---

## 1. The positions

| Source | Position | Reasoning |
|---|---|---|
| Clean Code ch. 9 (Martin) | Three laws: no production code before a failing unit test; no more test than enough to fail (not compiling counts as failing); no more production code than enough to pass the failing test. Cycle roughly thirty seconds; tests are only seconds ahead of the code; dozens of tests a day, thousands a year, covering virtually all production code. "Timely" in F.I.R.S.T.: tests are written just before the code that makes them pass. | Tests written afterwards find the code hard to test, and you may declare parts too hard to test. The sheer bulk of tests becomes a management problem unless kept clean. |
| Refactoring 2e ch. 4 (Fowler) | Uses and recommends test-driven development (short cycles of failing test, code to pass, refactor, many times an hour) but does not cover it. Writing the test first asks what is needed to add the function, focuses on the interface, and gives a clear definition of done. | Also: when refactoring code with no tests, first make it self-testing. |
| Pragmatic Programmer ch. 6 and 8 (Hunt, Thomas) | Design to test (Tip 48); build tests before the code to try out the interface before committing. "Code a little, test a little": write test code at the same time as, or even before, production code (Tip 62). Not called TDD in this edition. Coding is not done until all the tests run (Tip 63). | The earlier a bug is found, the cheaper it is to fix. A good project may have more test code than production code. |
| Why Programs Fail ch. 3 (Zeller) | Test first: write tests before implementing; tests act as example specifications. Also: authors are psychologically unsuited to test their own code, have others test. Continuous testing (tests at each save) helps developers write better code faster. | You cannot test early and often enough. |
| APOSD ch. 19 (Ousterhout) | Strong advocate of unit tests; not a fan of TDD as a design method. It focuses on getting specific features working rather than finding the best design: "tactical programming pure and simple". Too incremental; at each point it is tempting to hack in the next feature; no obvious time to design. Increments of development should be abstractions, not features. Exception: bug fixes, where a failing test is written first, then the fix. | Unit tests exist to enable refactoring. A new class's interface should be designed as a whole, with a reasonably comprehensive core set of functions, not built one test at a time. |
| Clean Code 2e outline (headings only) | Chapter 14 "Testing Disciplines": TDD with the three laws; "Test && Commit || Revert" (TCR); "Small Bundles"; a section on why the discipline matters (tedious and slow; debugging; documentation; reliability; design). The Appendix "The Clean Code Debate" includes a TDD discussion with Ousterhout. | The text is not in the notes; only headings. Do not infer the arguments. |

## 2. Where they actually disagree

- Granularity: Martin's thirty-second cycle versus Ousterhout's design-the-abstraction-first. They disagree about what the unit of work is: a test case or an abstraction.
- Design effect: Does test-first improve design (Martin, Fowler: interface focus, definition of done) or push toward tactical, feature-by-feature code (Ousterhout)?
- Not in dispute: automated tests are essential; tests enable refactoring; a bug fix begins with a failing test.

Empirical results on TDD benefits are mixed (the notes' caveat). The thirty-second cycle suits fine-grained logic and suits exploratory work, user interfaces and spikes less well.

## 3. What every position keeps

1. The test must be seen to fail before it is trusted (fail first). Test-first gives this for free; test-after needs fault injection.
2. Production code never runs far ahead of tests.
3. Tests are run frequently and the full suite passes before work is called done.
4. Tests are written close enough in time to the code that testability shapes the design.
5. Every bug gets a regression test that fails first.

## 4. Decision rule for the agent

Choose by the kind of work:

| Work | Order | Why |
|---|---|---|
| Bug fix | reproduce with a failing test first, then fix | all sources agree; otherwise the test may not trigger the bug |
| Fine-grained logic with a clear contract (parsing, calculation, state machine, algorithm) | test-first in short cycles | cheap, the interface is small, boundaries get considered up front |
| Adding behaviour to well-covered code | test-first or test-with, both acceptable; run the suite after each step | the net already exists |
| A new abstraction or module whose interface is not yet clear | sketch the interface and contract first (design it as a whole, per APOSD), then write tests from the contract, then implement | avoids building the abstraction one test at a time |
| Exploratory work, UI layout, spike | explore freely, then write tests before calling it done; discard the spike or cover it | tests written during exploration are often thrown away |
| Refactoring code without tests | characterisation tests first (`writing-clean-tests.md` section 11) | the safety net must exist before the change |
| User explicitly asks for TDD or for tests last | follow the request, and still apply sections 3.1 to 3.5 | the request governs order; the safeguards stay |

Tie-breaker when unsure: write the test before the production line when you can state the expected result in one sentence; otherwise sketch first.

## 5. How to work test-first in short cycles

1. Write the smallest test that fails (not compiling counts as failing, per the book's second law). Run it; confirm it fails for the intended reason and read the message.
2. Write the least production code that passes it. Run the test.
3. Run the whole suite. Never refactor on a red bar.
4. Refactor with the suite green (`craft-refactoring`); revert to green if anything breaks.
5. Repeat. If you cannot name the one failing test that justifies the line you are typing, you are running ahead of the tests (the notes' check, inferred).
6. Keep a design pass between cycles when a new concept appears: put the abstraction in one place and give it a comprehensive interface rather than growing it one case at a time (APOSD correction).

## 6. Test && commit || revert and small bundles (headings only)

Clean Code 2e's outline names two further disciplines next to TDD: "Test && Commit || Revert" and "Small Bundles". The excerpt in the notes contains only the headings, so the mechanics are not described there. The name suggests committing when the tests pass and reverting when they do not; the same shape as Refactoring 2e's "revert to green" (undo recent changes back to the last passing state, usually the last version-control checkpoint). Use the latter, which the notes do describe, as the working rule.

## 7. Verify

- For a bug fix: show the test failing before the change and passing after, in the same session. Name the commit or diff that contains both.
- For test-first work: show the red run output for each new behaviour.
- For test-after work: show fault-injection results, because no red run exists.
- Show that you did not leave production code with no test that would fail if you deleted it (spot check: delete or break a line you added; a test goes red).
- State which order you used and why, in one line.

## 8. Limits of the notes

- The notes for Clean Code 2e contain only Chapter 3 text, headings and an index; the Clean Code Debate appendix's arguments are not available. Do not attribute positions to either debater beyond what the first-edition and APOSD notes say.
- "Dirty tests are worse than none" and "tests must be written first" are the author's ideals, not universal practice. The surviving core is in section 3.
