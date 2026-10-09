# Locate the defect and correct it

Sources: WPF ch. 15 (fixing the defect), ch. 9.5, ch. 1; PP ch. 3 "Debugging".

## Contents
1. The TRAFFIC sequence and where time goes
2. Locating: the backward infection loop
3. Where to look first: priority order
4. The two tests every candidate must pass
5. Correction versus symptom patch
6. Think before you code: theory, not hypothesis
7. Workarounds
8. Procedure
9. Warning signs of a bad fix

## 1. The TRAFFIC sequence and where time goes

| Step | What | Reference |
|---|---|---|
| Track | Record the problem so it is not lost | `reproduce.md` |
| Reproduce | Make it happen on demand | `reproduce.md` |
| Automate | Turn it into an automated test; simplify to a minimal case | `reproduce.md`, `simplify-and-isolate.md` |
| Find origins | Follow dependences back from the failure to possible infection origins | `deduce-and-slice.md`, `observe-and-trace.md` |
| Focus | Examine the most likely origins first | section 3 |
| Isolate | Use the scientific method to isolate each origin; repeat until a chain from defect to failure | `scientific-method-and-logbook.md` |
| Correct | Remove the defect, break the chain, verify | this file |

Tracking is bookkeeping, reproduction and automation are usually straightforward, correction is usually simple once the chain is understood (unless the problem is a design flaw). The find-focus-isolate loop, locating the defect, takes most of the time.

## 2. Locating: the backward infection loop

1. Start from the infected value that defines the failure.
2. Determine its possible origins by following data and control dependences in the source.
3. Observe each origin and decide infected or sane. If one is infected, make it the new starting point and go to step 2.

Stop at an infection whose origins are all sane. The code that produces that infection from sane inputs is the defect. This is guaranteed to find the chain but is tedious; induction and experiments (`anomalies-and-causes.md`) help choose which origin to check, yet they have no notion of correctness. Only an assertion, a specification or your judgement of intended behaviour says sane versus infected.

Practicalities:
- Take larger gaps at function and package boundaries, where only arguments and return values cross; sanity is easier to judge there.
- If a state is sane, do not look at earlier states; search forward from there for the moment it becomes infected. The code between a sane point and an infected point holds the defect.
- When stuck among N origins, bisect in time with an assertion or print at a boundary on the chain; search the half that contains the sane-to-infected transition (inferred in the notes, consistent with PP's binary search).
- A failing assertion is an infection by definition; a passing one rules out whatever it covers.

## 3. Where to look first: priority order

When several origins or hypotheses are candidates, rank in this order (WPF ch. 15.2):

1. Known infections: an origin already shown faulty by a failing assertion or observation. Check whether it causes the failure.
2. Causes: state, input or code that experiments (dd, isolation) showed to be causes. Check whether they are infected. Causes beat anomalies because causality is experimentally shown; a cause transition from a sane to an infected variable gives the defect and its chain.
3. Anomalies: origins tied to coverage differences or violated learned invariants. They correlate with failure.
4. Code smells: static checker findings, uninitialised variables, unused values, ignored return values.
5. Dependences: anything outside the backward slice of the infected state cannot (in a safe language) have caused it. Check the slice, closest statements first.

Add two history-based tie-breakers (WPF ch. 16): files with many earlier fixes and files changed very recently or together with recently defective files are likelier (see `prevent-recurrence.md`). Use them to order candidates, never to skip the tests in section 4.

## 4. The two tests every candidate must pass

At each step of tracing back, show both (WPF ch. 15.3):

1. The origin is infected: its value is incorrect or unexpected compared to the intended behaviour or specification.
2. The origin causes the chain: changing it makes the failure, and the remaining infections, no longer occur (the counterfactual experiment, `anomalies-and-causes.md`).

Why the second test: the example of `a = compute_value(); print a` showing 0. Setting `a = 1` before the print still printed 0, because the format was wrong. Skipping the test would have meant a long search into why `a` became zero. Be especially careful with suspicious origins, values you cannot tell are right or wrong: replace the value with a non-suspicious one and confirm that the failure goes away before following the scent.

"Infected and causing" is two separate findings. A value can be wrong and harmless to this failure (the wrong size that only matters when the extra element is zero), and a cause can be correct (a legitimate input that exposes a defect elsewhere). A found cause is not automatically an error.

## 5. Correction versus symptom patch

A fix is a change after which the failure no longer occurs. A correction removes the defect. A workaround leaves the defect in place. Aim for a correction: break the chain so as to prevent as many failures as possible, not only the reported one.

Bad fixes in the book:
- Special-casing data (`if account == 123 then add 45.67`, `if y == 17 then x = 25.15`). The origin of the wrong amounts is untouched.
- Ignorant surgery: changing a loop bound from `i < size` to `i < size - 1` made the failing case work "and so proved the loop header was to blame", without knowing why. The real defect (the caller passing a count one too large) remained, and the function now failed for other callers. This is debugging into existence.
- McConnell's devil's guide, as things not to do: find the defect by guessing, scatter print statements, change code until something works, keep no backups, do not bother understanding what the program should do, take the most obvious fix.

Exercise 15.6 ranks four fixes of a summing bug (the caller computes with `n-1` elements): special-casing the failing input is worst; fixing the helper to match its specification, or replacing the call with a correct loop, treats the cause; changing the helper's specification to match its behaviour is right only if the specification was wrong and every other caller is checked.

Agent additions (inferred in the notes): loosening an assertion, catching and swallowing an exception, weakening or editing a test's expected value, hard-coding a literal from the failing test, are symptom patches unless you can show the assertion, handler or test was wrong.

## 6. Think before you code: theory, not hypothesis

You may skip the causality experiment at a given step only if you have a theory: you can predict exactly (a) how your change breaks the infection chain and (b) how that makes the failure and similar failures disappear. Test of a theory: explain the fix to a reviewer, in words, before applying it. If the prediction then comes true, the fix retrospectively validates causality. If it does not, your understanding of the chain was wrong; revert (below).

Before changing anything, save the original code (commit or stash) so earlier observations remain valid and you can revert.

## 7. Workarounds

Use a workaround when locating is easy but correcting is hard: you cannot change the code (third party, no source), the change is risky (large, system-wide), or the problem is a flaw (the design itself needs rework). A workaround detects and handles the situations that would trigger the defect, or repairs behaviour afterwards. Examples in the book: spam filters, virus scanners, date windowing for two-digit years. Rules:
- It is not permanent; it is specific to the situation and the failure tends to return after changes.
- Keep the problem open in the tracker to implement a proper solution later; say in the code and the commit that it is a workaround, and why.
- Removing the isolated cause (drop the character, revert the commit, forbid the thread switch) is a workaround, not a correction.

## 8. Procedure

1. Reproduce with an automated test (`reproduce.md`). Simplify if inputs are large.
2. Run static checks and warnings; fix or explain smells in the area.
3. Form hypotheses in the logbook; rank candidates by section 3; apply the two tests of section 4 to each.
4. Reach an infected value whose origins are all sane; name the defect and write the full chain: defect, infection under which condition, propagation, failure. Check that the chain also explains why other runs pass (the same defect was executed in passing runs, but the infection did not reach the output).
5. Choose correction or workaround (section 7). Predict the effect of the change on each link (section 6).
6. Save the original; make the change; run `fix-validation-checklist.md`.

## 9. Warning signs of a bad fix

- You cannot explain why it works.
- You tried several edits until the symptom vanished.
- It contains a literal from the failing test, or special-cases an identifier or input value.
- The edited function has other callers you did not check.
- The failure vanished but you never saw the infected value.
- The change is a catch-all or a loosened check at the symptom site rather than at the origin.
- More than one defect fixed in the same change.
