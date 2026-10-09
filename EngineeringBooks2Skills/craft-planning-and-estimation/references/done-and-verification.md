# Definition of done and proof of completion

Contents: 1 What done means; 2 Done by deliverable class; 3 Tests that back "done"; 4 Test data; 5 Testing the tests; 6 When to test; 7 Bug-fix workflow; 8 A build that proves it; 9 Documentation done; 10 Verification before reporting; 11 Warning signs

Sources: PP ch. 8 sections 42 to 44 (Tips 61 to 68), ch. 2 (Tip 15), ch. 1 (Tip 7); MMM ch. 1, 13, 14, 15, 16. Sibling: `craft-testing` has test design in depth (levels, doubles, property-based testing, suite audits); this file covers what to demand before declaring a plan item finished.

## 1. What done means

PP Tip 63: coding is not done until all the tests run. Finishing typing is not done. Code is never really done, and cannot be claimed usable until it passes all available tests. Do not report completion to a boss or client before the full suite passes.

Brooks (ch. 14): milestones are binary, observable events: for example "debugged version passes all test cases". Done for an agent is the same: a statement that can be checked by running something.

Quality is a requirement (Tip 7): what "done" means includes the quality bar agreed with the user. Stop when it is met; do not exceed it on your own initiative at the expense of the schedule.

## 2. Done by deliverable class

Derived from the 2x2 in `estimating.md` (MMM ch. 1; verification items are inferred from the text).

| Class | Done also requires |
|---|---|
| Program (private use) | It runs on the author's machine with the intended input; the author knows its limits |
| Programming product | A recorded bank of test cases that probes input boundaries; documentation sufficient for a stranger to use, fix and extend it; evidence of running in more than the author's environment |
| System component | A written interface definition; a stated resource budget with measured usage; integration tests against its neighbours in the expected combinations |
| Systems product | All of the above |

## 3. Tests that back "done" (PP Tip 62 to 66)

Test early, test often, test automatically. Tests that run with every build beat elaborate plans that sit on a shelf. Write test code at the same time as, or before, production code. A good project may have more test code than production code. "Automatically" includes automatic interpretation of results, not just automatic execution.

| Kind | Question | Notes |
|---|---|---|
| Unit | Does each module work alone? | Foundation. All modules pass their own tests before proceeding |
| Integration | Do subsystems honour their contracts with each other? | With good tested contracts integration issues are easy to detect; without them integration is often the single largest source of bugs |
| Validation and verification | Is it what users need, not just what they said? | Start as soon as there is an executable UI or prototype. Watch how end-user access patterns differ from developer test data |
| Resource exhaustion, errors, recovery | What happens at the real limits? | Memory, disk, CPU, wall-clock time, disk and network bandwidth, display limits. Ask when, not if, it fails: gracefully (save state, no lost work) or crashing in the user's face |
| Performance | Meets requirements under real load? Scales? | May need specialised load simulation |
| Usability | Does it fit the hand? | With real users under real conditions, as early as possible; failing usability criteria is as big a bug as dividing by zero |
| Testing the tests | Does the suite catch what it should? | Section 5 |

Three-part test domain (MMM ch. 15): mainline cases with common data; barely legitimate cases probing the edge of valid input (largest, smallest, valid exceptions); barely illegitimate cases probing the boundary from the other side so invalid input produces proper diagnostics. Ship a few small cases that let a user check a faithful installation.

Tip 65: test state coverage, not code coverage. Coverage tools give a general feel; do not expect 100%, and 100% line coverage is still not the whole picture. Example: f(a, b) = a / (a + b) with each argument from 0 to 999 has three lines but 1,000,000 logical states, of which one fails (a + b = 0). Data and the order of traversal matter more than lines executed. Practical consequence (inferred): choose inputs by partitioning the input and state space, probing boundaries, zero and empty, combinations and call sequences.

Design metrics (sidebar): lines of code, cyclomatic complexity, inheritance fan-in and fan-out, response set, coupling ratios. Some give a pass grade; others are useful by comparison. Compute per module, take mean and standard deviation, and look for outliers; ask whether an outlier is justified.

## 4. Test data

Both kinds are needed because they expose different bugs.
- Real-world data (from an existing system, a competitor's, or a prototype): most likely to reveal defects and misunderstandings in requirements analysis; the big surprises come as you discover what typical means.
- Synthetic data: for volume beyond any sample (seed from real data, vary unique fields); boundary conditions (an invalid date such as 29 February 1999, huge records, foreign postal codes); statistical properties (every third transaction fails; presorted against random input to expose an algorithm that degrades on sorted data).

GUI systems: tools that couple scripts tightly to layout break when a dialog moves. Design remedy: decouple so application logic can be tested without a GUI; then a bug that appears with the UI present was probably created by UI code. If the logic is too hard to test independent of the GUI, that says something about coupling.

Fixtures and scaffolding (MMM ch. 13): dummy components with faked data, miniature files with a few typical records (file-format misunderstanding is a very common system bug), test data generators, analysis printouts.

## 5. Testing the tests (Tip 64)

We cannot write perfect software, so we cannot write perfect tests. After writing a test to detect a particular bug, cause the bug deliberately and confirm the test complains. At project level, a saboteur takes a separate copy of the source tree, introduces bugs on purpose, and verifies the tests catch them. The modern automated form is mutation testing (not named in the book). A test that has never been seen to fail is not evidence.

## 6. When to test

- Not at the last minute, where testing gets cut against the deadline. As soon as production code exists, it needs testing.
- Always before checking code into the repository (modern form: pre-commit or pre-merge gates).
- Tests that cannot run often (stress tests needing special setup) run weekly or monthly, but on a regular schedule with resources allocated.
- Run a full nightly or continuous build with all tests, so a regression is found while its cause is recent (MMM ch. 19, PP ch. 8).

## 7. Bug-fix workflow (Tip 66, find bugs once)

If a bug slips through the existing tests, add a test that traps it next time. Once a human tester finds a bug, that should be the last time a human finds it: the automated tests check for it from then on, every time, no exceptions, however trivial.

1. A bug is reported: write an automated test that reproduces it and fails.
2. Confirm it fails for the right reason (the alarm sounds).
3. Fix; the test passes; the full suite passes before declaring done or committing.
4. Ask what class of states the bug belongs to and add data for neighbouring states.
5. Regression discipline (MMM ch. 11): a fix has a 20 to 50% chance of introducing another defect, so rerun the whole prior bank, not just the new test.

For the investigation method, see `craft-debugging`.

## 8. A build that proves it (PP ch. 8 section 42)

A build is a procedure that takes an empty directory and a known compilation environment and builds the project from scratch, producing the final deliverable.
1. Check out the source from the repository.
2. Build from scratch (top-level script), marking the build with a version or date.
3. Create the distributable image in the exact format required at ship time (do not wait until the night before shipping to find that it does not work).
4. Run the specified tests.

Rules:
- Goal: check out, build, test and ship with a single command. Recursive build tools that cannot see cross-invocation dependencies cause unnecessary rebuilds or stale artefacts; keep build dependencies and test dependencies in mind.
- If the product is compiled or configured differently from earlier versions (final build flags, locked repository, tagging), test that version all over again. Capture the final configuration in a single target.
- Scheduled builds run all available tests and publish results automatically (build summary, test results, performance statistics, metrics). A published status page must not require hand maintenance: misleading information is worse than none.
- Approval procedures can be automated (a status marker in each file scanned by a script that lists items needing review); the content of the review still needs a person.
- Automate any recurring, consistency-critical task, and put the script under version control (Tip 61). Check cost by comparing time wasted on the procedure to time to build the automation.

## 9. Documentation done

- Documentation is a mirror of the code. If there is a discrepancy, the code is what matters (PP Tip 68). Build documentation in, do not bolt it on.
- Comments record why: purpose, trade-offs, rejected alternatives. Too many comments can be as bad as too few. Do not hand-maintain what tools can produce: export lists, revision history, dependency lists, file names.
- Single-source facts: choose one authoritative source (a schema, a spec), generate the other forms as views, and from then on change only the model.
- Names must match behaviour: a misleading name is worse than a meaningless one. Check, for example, `get*` functions that mutate state and `is*` with side effects.
- Date stamp or version each published page.
- Overview before detail; user documentation drafted before the program (see `requirements-and-specs.md` section 12).
- Reluctance to document a design because it is unclear in your head is a symptom of programming by coincidence (Tip 44; see `craft-debugging`/`craft-clean-code` for related practice).

## 10. Verification before reporting

Run in the repository and show the output.

1. Clean build from an empty directory or fresh checkout; one command if one exists.
2. Full suite, with counts of passed, failed and skipped tests. Do not substitute a subset.
3. For each fixed bug: the test that failed first and passes now.
4. Integration order and regression runs, if components came from several sources.
5. A diff review for silent shortcuts (stubs, commented-out code, TODOs): each is deliberate, has a reason, and is in the report.
6. A comparison of the original request with the result; unrequested additions removed or flagged.
7. Boundary checks: at least one case on each side of each stated input limit.
8. A statement of what was not verified and why (no environment, no data, not asked).

Signing the work (Tip 70): report only what is tested and documented, state what was and was not verified, and leave an auditable trail.

## 11. Warning signs

- A written test plan nobody runs; "done" declared before tests pass; testing scheduled at the end.
- Coverage percentage used as the definition of sufficient testing; a test never seen failing; the same bug reported twice.
- Logic reachable only through the UI.
- Only developer-invented data, or only production samples without boundary data.
- Stress tests run when someone remembers; pass or fail judged by a human reading output.
- A release built differently from the tested build; setup steps living in prose rather than scripts.
- Docs that describe every tree but no forest; documentation in a separate file that lags the code; comments that restate lines while paragraph-level intent is missing.
