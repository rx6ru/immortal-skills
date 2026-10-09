# Simplify and isolate: ddmin and dd

Sources: WPF ch. 5 (simplifying), ch. 13 (isolating failure causes), Appendix A.1 (formal definitions). Script: `scripts/ddmin.py`.

## Contents
1. Simplify versus isolate: which one you need
2. Manual simplification
3. ddmin stated precisely
4. dd (isolating a minimal difference) stated precisely
5. Defining the test function
6. Choosing the unit of reduction
7. Making it faster
8. Applying it to inputs, changes, schedules and states
9. Costs, guarantees and traps
10. Verify

## 1. Simplify versus isolate

| | Simplify (ddmin) | Isolate (dd) |
|---|---|---|
| Starts with | One failing input | One failing and one passing input (or version, config, schedule) |
| Produces | A small failing case in which every part is relevant | An adjacent pair (passing, failing) whose difference is minimal |
| Use when | You need a short reproducer to read, attach to a report, add as a regression test, or search for duplicates | You need a fast pointer to the culprit circumstance in a huge input or history |
| Cost | Roughly proportional to the size of the result, quadratic worst case | Logarithmic when every outcome is PASS or FAIL; passing tests help too |
| Caveat | Shows relevant context, not the single cause | The difference sits in a large context you still have to understand, and it need not be a defect |

Doing both is common: isolate first for the pointer, then simplify for the reproducer (adaptation).

A circumstance is relevant if the failure needs it; irrelevant if the failure occurs with or without it. The value of simplifying lies as much in what you can remove as in what remains. Three further benefits beyond finding the cause: the report is easier to communicate, debugging is easier (less state, shorter run), and duplicates become visible because reports that differ only in irrelevant details collapse to the same case (WPF ch. 5).

## 2. Manual simplification

Binary search by hand: throw away half the input; if the output is still wrong keep that, otherwise restore it and discard the other half. Keep multi-level undo or version control handy, recheck that the bug still reproduces every few steps, and stop when removing anything more makes it disappear. In the book's example 896 lines of HTML reduced to one tag in 12 tests.

It fails when neither half alone reproduces, because the relevant part is spread across both halves (a tag split across the cut). Do not give up: cut smaller pieces (quarters, eighths, down to single units). That idea is ddmin.

## 3. ddmin stated precisely

Setting. A configuration is a set of circumstances C (lines, characters, tokens, tree nodes, events, changes). `test(c)` returns FAIL when the failure occurs, PASS when it does not, UNRESOLVED when the test cannot tell (invalid input, program did not start, a different failure).

Preconditions: `test(c_fail) = FAIL` and `test({}) = PASS`.

Goal: return `c' ⊆ c_fail` with `test(c') = FAIL` that is 1-minimal (also called relevant): removing any single circumstance from c' makes the failure disappear.

```
ddmin(c) = ddmin2(c, 2)

ddmin2(c, n):
  if |c| = 1:                                       return c
  split c into n near-equal disjoint chunks c_1..c_n
  if some i has test(c \ c_i) = FAIL:               return ddmin2(c \ c_i, max(n-1, 2))   # some removal fails
  if n < |c|:                                       return ddmin2(c, min(2n, |c|))        # increase granularity
  return c
```

Only FAIL accepts a reduction. PASS and UNRESOLVED both reject it. The invariant at each call is `test(c) = FAIL` and `n <= |c|`. The 2002 original also tried each chunk alone; later versions dropped that for little gain.

Properties from the book:
- The result is 1-minimal because the algorithm only stops after trying to remove every single element at single-element granularity and none was removable. It is a local minimum, not the global one; a smaller failing subset may exist (finding it would take exponentially many tests).
- Best case: with exactly one failure-inducing circumstance and every superset failing, about log2|c| tests (binary search).
- Worst case: quadratic in the size of the result (the book gives (|c'|^2 + 7|c'|)/2 in the body and (|c|^2 + 3|c|)/2 in the appendix for slightly different statements; treat "quadratic" as the safe claim).
- Observed in the book: NROFF/TROFF 100-200 runs; FLEX 11,000-17,960 runs on inputs up to about a million characters.

Python-shaped sketch (not the book's listing):

```python
def ddmin(c, test):                       # c: list of circumstances, test -> PASS/FAIL/UNRESOLVED
    n = 2
    while len(c) >= 2:
        chunks = split(c, n)
        for chunk in chunks:
            comp = [x for x in c if x not in chunk]       # use indices if items repeat
            if test(comp) == FAIL:
                c, n = comp, max(n - 1, 2); break
        else:
            if n >= len(c): break
            n = min(2 * n, len(c))
    return c
```

`scripts/ddmin.py` implements this with caching, index-based chunks (so duplicate lines stay distinct), a timeout that counts as UNRESOLVED, and budgets.

## 4. dd (isolating a minimal difference) stated precisely

Inputs: `c_pass ⊆ c_fail ⊆ C`, `test(c_pass) = PASS`, `test(c_fail) = FAIL` (usually c_pass is empty and c_fail is everything, or c_pass is the old version and c_fail the new one).

Output: a pair `(c_pass', c_fail')` with `c_pass ⊆ c_pass' ⊆ c_fail' ⊆ c_fail`, a passing c_pass', a failing c_fail', and a 1-minimal difference `delta = c_fail' \ c_pass'`: no single change in delta can be removed from c_fail' to make it pass, and none can be added to c_pass' to make it fail. The delta is an actual cause of the failure (see `anomalies-and-causes.md`). It may hold several changes that must all apply together.

Recursion `dd2(c_pass, c_fail, n)`, with `delta = c_fail \ c_pass` split into n chunks:

1. `|delta| = 1`: return the pair.
2. Some removal passes, `test(c_fail \ delta_i) = PASS`: that becomes the new c_pass (larger); recurse with n = 2.
3. Some addition fails, `test(c_pass ∪ delta_i) = FAIL`: that becomes the new c_fail (smaller); n = 2.
4. Some addition passes: new c_pass = c_pass ∪ delta_i; n = max(n-1, 2).
5. Some removal fails: new c_fail = c_fail \ delta_i; n = max(n-1, 2).
6. Otherwise, if n < |delta|: n = min(2n, |delta|). Else return the pair.

Cost: logarithmic in |delta| when no test is UNRESOLVED; quadratic worst case when most are. So the practical rule is to keep UNRESOLVED outcomes rare by grouping dependent changes and making candidates well-formed. The book's implementation checks the cheaper cases first (cases 1 and 2 need only the `c_fail \ delta_i` test, which makes dd a plain binary search when everything resolves), resumes from an offset after a removal so every chunk gets a fair chance, and assumes test results are cached.

Measured: on the book's Mozilla input, isolating took about 5-6 tests against 48 for ddmin. On FLEX, dd needed 23-51 runs against 11,000-17,960.

## 5. Defining the test function

This is where most of the effort and most mistakes live.

- Make FAIL mean the same failure: the same message or assertion, ideally the same crash site or stack trace as the original. A different failure is UNRESOLVED, not FAIL and not PASS. Otherwise the reducer drifts onto another bug. The tighter you define "same", the larger the cause required to reproduce all of it.
- Make invalid candidates UNRESOLVED without running the program when you can detect them (a tree node whose parent was removed, a patch that does not apply, a build that fails).
- Make it deterministic. Flaky tests break caching and the minimality claim. Make the run deterministic first (`reproduce.md`) or repeat each test and use a majority rule (adaptation).
- Check both endpoints before starting: `test(c_pass) = PASS` and `test(c_fail) = FAIL`.
- Run candidates in a scratch directory, so personal files and earlier runs do not interfere.
- Test run-time matters: thousands of runs at several seconds each is hours. Cache, stop early, or reduce the unit.

The script's contract: the command exits 0 when the failure still reproduces, 125 (configurable) for unresolved, anything else for pass. Write a small wrapper that greps the output for the original failure signature.

## 6. Choosing the unit of reduction

| Input kind | Unit | Why |
|---|---|---|
| Plain text, logs, line-oriented data | lines first, then characters on the result | Line-level took 12 tests in the book's example against 48 at character level |
| Structured text (HTML, XML, JSON, source code) | syntactic units: parse to a tree, make each node a circumstance | Character cuts are mostly invalid; removing an attribute without its value is infeasible, so return UNRESOLVED without running |
| Event or call sequences | single events or calls | The book reduced 95 recorded GUI events to 3 in 82 tests |
| Fuzz output | characters or bytes, after generating a large failing input | Combine fuzzing with reduction: random input finds the failure, ddmin shrinks it |
| Version history | commits, then hunks within the culprit commit | See section 8 |
| Configuration or feature flags | one setting per unit | Dependent settings travel together |

If the chunks are not independent (a closing brace without its opening), expect many UNRESOLVED results; either group them or change the unit.

## 7. Making it faster

| Technique | Idea | Notes |
|---|---|---|
| Caching | Memoise outcomes by configuration | Always; ddmin retests the same configuration (the book's example had repeats) |
| Stop early | Stop at a granularity, a time budget, or when progress stalls | FLEX shrank fast in about 50 tests and then crawled for 10,500 more; result is small but not 1-minimal |
| Syntactic units | Tree nodes instead of characters | 6 nodes versus 40 characters in the book's HTML case |
| Isolate a difference rather than minimise | Use passing runs as well as failing ones | 5 tests versus 48 in the example |
| Reduce lines before characters | Two passes | Practical combination (adaptation of the 12-versus-48 comparison) |

## 8. Applying it to inputs, changes, schedules and states

- Input (WPF ch. 13.5): minimise a failing input, or isolate against a passing input of similar shape.
- Code changes, the regression "blame-o-meter" (WPF ch. 13.7). One input, an old passing and a new failing version. Steps: apply a subset of changes to the old tree (a patch that fails to apply is UNRESOLVED), rebuild (build failure is UNRESOLVED), run the test in a scratch directory. The book's case had 8,721 individual changes and needed about 97 tests with scope grouping. Optimisations: group by time order and by file or function so builds are consistent; incremental builds and compile caches; on build failure add the changes that define the missing identifiers. The culprit was an innocent help-text change that the dependent program parsed by exact prefix: the cause of a regression need not be a mistake, and the test tells you why it fails, not who is wrong. Modern equivalent (adaptation): `git bisect` is dd over an ordered, always-consistent commit history, with `git bisect run <script>` using exit 0 good, 1-124 bad, 125 skip. Careful: `scripts/ddmin.py` shares only the 125 (unresolved) code; its exit 0 means the failure reproduces (bad), so a script written for one needs an inverted result for the other. Use ddmin-style subset testing when changes are unordered or finer than a commit (hunks in one commit, dependency sets, config keys).
- Schedules (WPF ch. 13.6): needs deterministic replay; dd over thread-switch positions. See `hard-cases.md`.
- Program states (WPF ch. 14): see `anomalies-and-causes.md`.
- Wrapping to simplify with dd, or to maximise the passing side ("ddmax"): possible in principle (exercises 13.2 and 13.3); not needed in practice.

## 9. Costs, guarantees and traps

- Treating "the program did something else" as PASS drives the reducer toward an invalid or different failure. Use UNRESOLVED and the signature check.
- Simplifying characters of structured input is slow and wasteful. Switch units.
- Stopping when the case "looks small" is not 1-minimality. Check by removing each remaining element once.
- Claiming "smallest possible": you have a 1-minimal case only.
- dd returns the first actual cause it finds; others may exist (removing any character of `<SELECT>` also removes the failure). Rerun on alternatives only if the first cause does not characterise the failure.
- The isolated cause suggests a fix of sorts (drop the character, revert the commit, forbid the switch). That is a workaround; the defect is a separate question (`locate-and-fix.md`).
- Interacting causes: if many circumstances must hold together the minimal set can still be large.

## 10. Verify

- The reduced input still fails with the original signature on a direct re-run.
- 1-minimality: removing each remaining unit (one at a time) makes the failure disappear. `scripts/ddmin.py` ends this way; confirm if you stopped by budget.
- `test(empty) = PASS` held (otherwise the failure does not depend on the input).
- Record the reduction ratio and number of runs in the logbook. Add the reduced case to the regression suite and attach it to the report; search for duplicates with it.
