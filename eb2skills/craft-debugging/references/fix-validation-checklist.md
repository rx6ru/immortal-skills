# Fix validation checklist

Sources: WPF ch. 15.3-15.5, ch. 12.9, ch. 3 (regression), ch. 2 (tracking, commit linking); PP ch. 3 "Debugging" (post-mortem questions and checklist).

Use this before declaring a fix done, and show the evidence under each item to the user. Items marked (adaptation) are operationalisations by this skill, not claims of the books.

## Contents
1. Before editing
2. After editing
3. Same mistake elsewhere
4. Commit and report
5. Evidence to show
6. If the failure is still there

## 1. Before editing

1. Chain stated. Write it: defect at X, infection of state Y under condition Z, propagation, observed failure. The first statement where sane state becomes infected is named. If any link is a guess, you have a hypothesis; run the experiment first (set the value in a debugger or fixture and see whether the failure goes).
2. The chain explains the passing runs too: why the same code passes in other cases (the book asks this of its sort example, where the same out-of-bounds read also occurs in the passing run; our reading is that the stray value there sorted past the printed elements, so nothing propagated).
3. The candidate origin is infected (wrong against intended behaviour or specification) and causal (altering it removes the failure).
4. Prediction written. You can say how the change breaks each link and why similar failures disappear. If you cannot explain the fix to a reviewer in words, stop.
5. Correction or workaround classified. Not a special case, a swallowed error, a loosened assertion, or an edited expectation; if a workaround, the reason (cannot change, risk, design flaw) is recorded and the problem stays open (`locate-and-fix.md`).
6. Original saved: committed or stashed, so you can revert and earlier observations stay valid.
7. The reproduction test exists, is automated, and currently fails with the reported symptom (`reproduce.md`).

## 2. After editing

8. The original failing scenario now passes. Rerun the exact reproduction, not a nearby one. Being surprised that it worked means you were not systematic enough; the disappearance should be the last confirmation of a diagnosis you already believed.
9. The earlier infection point shows sane values (re-run the observation that showed the bad value), not just a changed final output.
10. A regression test exists that fails before the fix and passes after (adaptation, from "have a regression test ready"): run it against the old code once to see it fail for the right reason (`git stash` the fix, or check out the parent commit).
11. The full test suite passes. Many fixes introduce new problems; the book cites fixes as more likely to induce failures than other changes (Mockus and Weiss), so regression checking is not optional.
12. One defect per change. Fixing several defects at once lets them interfere and produce failures that look like the original. Check each correction individually.
13. The forward slice of the changed statement was inspected: other callers, other users of the changed value, changed contracts (`deduce-and-slice.md`).
14. Static checks and sanitizers relevant to the defect class are clean (warnings, linters, memory or thread sanitizers if the language has them) and the warning that pointed to the defect, if any, is gone.
15. Nondeterministic failures: the test was repeated N times with the failure rate before and after reported, not a single pass (adaptation). A single green run after an intermittent failure proves little.

## 3. Same mistake elsewhere

16. Search for the same pattern: other places with the idiom or the condition that caused this (the book's example: every allocation that sizes a copy with `strlen(t)` and forgets the terminator). Fix every instance, and replace the error-prone idiom with a helper that makes it impossible (a `strdup`-style function), where proportionate.
17. If bad data travelled several levels before failing, would a parameter check, assertion or earlier validation have isolated the defect sooner? Add it (`observe-and-trace.md`).
18. If someone's wrong assumption caused it, tell the team (here: say so in the report or commit message): if one person misunderstood, others may.

## 4. Commit and report

19. The commit message names the problem identifier and states the cause and why the change breaks the chain (not just "fix bug"); the tracker entry records the fixing change. Both directions of the link are recorded (WPF ch. 2).
20. The change is reviewed, or at least explained, before it is merged (peer review of corrections is the book's recommended defence).
21. Resolve the ticket only when fixed. A workaround leaves it open. A fix is not done when committed; it is done when verified and delivered (WPF ch. 2: fixed, verified, closed).
22. Ask the learning questions (`prevent-recurrence.md`): why was this not caught earlier, what would make the next fix easier.

## 5. Evidence to show the user

- The reproduction command and its output before and after.
- The chain in one paragraph, and the experiment that showed causality (the both-ways run).
- The names of the new regression test and the result of the full suite.
- The list of other places checked for the same mistake and what was done.
- What you did not verify (for example environments you cannot run), stated plainly.

## 6. If the failure is still there

Two possibilities (WPF ch. 15.4.1): there are multiple defects and fixing the first unmasked the second, or what you fixed was not the defect and your understanding of the chain was wrong. Being wrong should be rare and astonishing; reread the logbook, recheck observations and experiments, and reconsider. Revert the change before continuing, so earlier observations stay valid and edits do not stack. Do not pile a second speculative edit on top.
