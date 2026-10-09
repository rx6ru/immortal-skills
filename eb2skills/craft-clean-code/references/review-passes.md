# Review passes for cleaning working code

An ordered procedure for "clean this up", "tidy this", "make this readable", and for a quality
review of a diff. Built from the two case studies in Clean Code ch. 14 (an argument parser that
grew messy and was restructured) and ch. 15 (an already good string-comparison helper improved
further), the simple-design rules in ch. 12, the heuristics in ch. 17, and the obviousness and
consistency checks in A Philosophy of Software Design (PoSD) ch. 17 and ch. 18.

Mechanics of individual moves (extract, inline, move, replace conditional) and working without
tests are in `craft-refactoring`. This file is about what to look at, in what order, and when to
stop.

## Contents

1. Before starting
2. The passes
3. When the structure itself is the problem
4. Rules of conduct during cleaning
5. Review mode: reporting findings without changing code
6. Stopping
7. Verify

## 1. Before starting

1. **Fix the scope.** What did the user ask for: a file, a function, a diff? Is behaviour allowed
   to change at all (normally no)? Is a minimal diff expected? If the request is a feature or
   fix, cleaning is limited to what the change touches, and anything larger is proposed.
2. **Find the one-command build and test** (E1, E2). Run the whole suite and record the result.
3. **Read the tests first**, as the specification by example, and check what they cover (ch. 15
   starts this way; its subject had full coverage, which is what made the restructuring safe).
   Where coverage of the code you will touch is thin, add characterisation tests before changing
   structure (inferred in the notes), or restrict yourself to tool-driven renames.
4. **Pin public behaviour** you might disturb: error messages, defaults returned for missing or
   mismatched input.
5. **Learn the local conventions**: formatter, linter, a sibling file's order and naming (PoSD
   ch. 17).

## 2. The passes

Do them in this order. Earlier passes are cheap, low-risk, and make later ones easier to see.
After each individual change, run the tests. Each pass lists what to look for, the codes that
name the reason, and the usual remedy.

### Pass 1 — Remove what is dead
- Commented-out code (C5); uncalled functions (F4); unreachable branches and handlers (G9);
  unused variables, empty constructors, information-free comments (G12); history and bylines
  (C1).
- Remedy: delete. Deleting first means less to read in every later pass.
- A condition you suspect is always true or false: reason about its inputs, disable it, run the
  tests (ch. 15 found two dead conditions this way, after redefining a variable exposed that the
  conditions had always been true).

### Pass 2 — Names and encodings
- Vague, misleading, encoded, inconsistent or level-inappropriate names (N1–N7, G11, G16).
- Remedy: rename with tooling, one at a time. Watch for collisions exposed by removing a prefix
  (ch. 15: dropping a member prefix made a local shadow a field; the local was then renamed).
- Make conventions consistent within the unit: if some helpers set fields and others return
  values for the same kind of job, pick one (G11).
- Full rules: `naming.md`.

### Pass 3 — Literals and explanatory variables
- Unexplained numbers and strings (G25); long expressions (G19, G16).
- Remedy: named constants; named intermediate values.

### Pass 4 — Conditionals
- Compound conditions inline (G28); negatives (G29).
- Remedy: extract an intent-named predicate; state it positively where that reads better.

### Pass 5 — Mixed levels and mixed responsibilities
- A function mixing abstraction levels (G34) or doing several things (G30); mode flags (F3,
  G15); long parameter lists (F1); output arguments (F2); a name that understates what the
  function does (N7, G20).
- Remedy: extract along the level boundary; split by mode; rename to cover effects. Apply the
  keep test from `functions.md` to each extraction so you do not create shallow, conjoined
  helpers. A public function that, say, both computes and formats is separated so each part does
  one job (ch. 15, step 6).

### Pass 6 — Hidden order dependencies
- Steps that must run in order with nothing showing it (G31).
- Remedy: pass results forward, or merge the ordered steps into one function that calls them in
  sequence. A parameter added purely to force order looks arbitrary to the next reader (G32); the
  structure should explain itself.

### Pass 7 — Boundary arithmetic
- Scattered `+1`/`-1`, off-by-one adjustments (G33); corner cases trusted without tests (G3).
- Remedy: find the variable whose meaning is wrong (index versus length, zero- versus one-based)
  and redefine it so the adjustments move into one named place or disappear. Add boundary tests.

### Pass 8 — Duplication
- Identical or near-identical blocks; repeated type-switches; parallel implementations of one
  fact (G5, G23; ch. 12).
- Remedy: make near-copies textually identical, then extract; one creating switch or one
  exhaustive match; define one fact in terms of the other. Check that the copies really change
  together before merging them.

### Pass 9 — Comments
- With names and structure improved, re-examine every comment: redundant (C3), obsolete (C2),
  badly written (C4), nonlocal, banners.
- Add what is missing: interface comments on public declarations; units, bounds, null meaning
  and invariants on fields; why and warnings where the code cannot say them.
- Full procedure: `comments.md`.

### Pass 10 — Layout and placement
- Order top-down with helpers below first callers (G10); declarations near use; configuration
  at the high level (G35); things placed where a reader would look (G17, G13).
- Run the formatter last so its output is the final state.
- Full rules: `formatting-and-layout.md`.

### Pass 11 — Obviousness check
- Cold-read the result. Wherever the first guess about behaviour would be wrong, either simplify,
  conform to convention, or add the missing information (PoSD ch. 18). Look specifically for
  anonymous tuples and maps used as records, handlers without "when invoked" notes, and effects
  that outlive a constructor or entry point.

Then one more loop through passes 1 to 4 on anything that passes 5 to 8 created.

## 3. When the structure itself is the problem

The passes above polish a sound structure. Sometimes the finding is that the structure cannot
take the next change.

### The trigger (ch. 14)

In the case study, a parser handling one argument type was compact. Adding a second type added
fields and was tolerable; adding a third turned it into a mess. Each new type needed code in
three places (parsing its schema element, converting its command-line value, a typed accessor),
plus parallel maps and error state in several fields.

**Rule:** when you can see that the next two additions of a kind will make the structure
unmanageable, stop adding and restructure first. Signs:
- the same group of edits repeated for each variant;
- parallel collections indexed by variant;
- flags or type tests driving branches in several functions;
- error state spread across several fields and set from many places.

"Many different types, all with similar methods" is the description of a missing abstraction.

Tell the user you are stopping to restructure, and why, before doing it.

### The sequence (ch. 14, generalised)

Each step is small and keeps every test green. If a test goes red, fix it before anything else.

1. Make sure the safety net is complete. In the case study a defect slipped through because only
   the unit tests were being run, while a behaviour was pinned only by acceptance tests; the fix
   was to make one command run everything.
2. Name the missing abstraction.
3. Add it empty, beside the old code. This cannot break anything.
4. Migrate one variant at a time, using the abstraction as a thin shim over the old behaviour.
5. Move behaviour into the abstraction: first into the common part with everything under test,
   then down into each variant. Delete old code only when nothing uses it.
6. Merge parallel structures into one keyed collection: add the new one alongside, switch
   readers one by one, then writers, then delete the old ones. Inline helpers that no longer
   earn their keep.
7. Replace type tests with dispatch. Make the common signature uniform even if some variants
   ignore a parameter; the uniform signature is the point.
8. Prove the result by adding a new variant test-first. It should touch only a few, isolated
   places: the new variant, its accessor, one selection branch, its error cases.
9. Extract cross-cutting concerns such as error construction and message formatting into their
   own module. Note any compromise you accept.

### Lessons recorded in the case studies

- Intermediate states can look worse than hoped; the structure improved only slightly after
  several phases. Keep going.
- Putting something in so that it can be taken out again is normal. One refactoring often leads
  to another that undoes the first; ch. 15's final version reversed several earlier decisions.
- Large structural changes made "in the name of improvement" are one of the surest ways to ruin
  a program. Stay incremental.
- Much of good design is partitioning: creating the right places to put different kinds of code.
- A good abstraction yields an explicit recipe for extension.
- The notes flag that the case study's final design still has type-unsafe accessors and a large
  switch inside its exception class, which many would do differently today. The transferable
  part is the procedure, not that design.

## 4. Rules of conduct during cleaning

- **Priority order when goals conflict** (ch. 12): tests pass; no duplication; intent expressed;
  fewest elements. Never trade the first for any of the others.
- **One kind of change at a time.** Do not mix behaviour changes with structural ones.
- **Whole suite after each step**, not a subset.
- **Tie each change to a reason.** If you cannot say why (a code from the catalogue, or a
  sentence), do not make it.
- **Respect conventions.** Do not "improve" a consistent local style (PoSD ch. 17).
- **Do not chase a line count.** Stop extracting when the only available name restates the body.
- **Keep the diff reviewable.** Group changes into commits by pass or by move; keep cleanup
  separate from functional change.
- **Surface cost instead of hiding it.** If the user wants to skip tests or cleanup to save time,
  state the risk; do not silently comply and do not silently refuse (Clean Code ch. 1).

## 5. Review mode: reporting findings without changing code

When asked to review, not to edit:

1. Run passes 1 to 11 as reading passes.
2. For each finding give: location; what a reader would misread or have to work out; the code if
   one fits; the smallest remedy. Example: "`orders.py:88` `process(order, True)` — the boolean
   selects refund mode and is unreadable at the call site (G15). Split into `refund(order)` and
   `charge(order)`."
3. Order findings by cost to a future reader or risk of a defect, not by pass number. Wrong or
   misleading names and comments, hidden side effects and unchecked boundaries come first;
   layout last.
4. Separate "would cause a misreading or bug" from "preference". Do not raise formatter-owned
   matters.
5. Where a finding rests on a contested rule (function size, comment volume), say so and give
   the test you applied (`contested-rules.md`).
6. Note what is good where it explains a non-finding ("long, but single-level and reads block by
   block; left as is").

Review questions drawn from the definitions of clean code in ch. 1:
- Could another developer extend this without asking the author?
- Does each routine do what its name leads a reader to expect?
- Is there one way to do each thing?
- Are dependencies minimal and explicit?
- Is error handling complete and following one stated strategy?
- Are there tests?
- Is any idea expressed twice?

## 6. Stopping

Stop when:
- a cold read produces no wrong guesses;
- no further extraction yields a name that adds meaning;
- remaining findings are preferences or would require changing a convention;
- the next improvement needs a structural change outside the agreed scope (report it);
- further work would be motivated by a number, not by a reader.

The catalogue's own conclusion is that rules do not produce clean code and the list is never
complete; judgement about the reader does the work.

## 7. Verify

- Suite green before the first change and after every step; no test weakened or skipped; no
  warning suppressed (G4).
- Public behaviour pinned in section 1 is unchanged.
- Formatter diff empty; linter clean.
- Every change in the diff maps to a stated reason.
- No helper fails the keep test; no function was split or merged for length alone.
- Comments made false by the changes are updated or removed; the final diff scan found no
  leftover debug code or unresolved TODO.
- If a restructuring was done: adding a variant touches only the declared extension points
  (try it, or show the list of places).
- Cleanup commits are separate from functional ones, and anything out of scope is listed as a
  proposal.
- Evidence to show the user: test command and result before and after; the list of changes with
  reasons; the list of things deliberately left alone and why.
