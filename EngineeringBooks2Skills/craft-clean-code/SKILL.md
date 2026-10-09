---
name: craft-clean-code
description: Readability rules and review procedures for code at the level of names, functions, comments, formatting and file layout, with the Clean Code smells catalogue (C/E/F/G/J/N/T codes) as a checklist and explicit arbitration between the "tiny functions, almost no comments" school and the "deep modules, comments say what code cannot" school. Use when writing new functions or files, when asked to clean up, tidy or "make this readable", when reviewing a diff for quality, when choosing or fixing names, when deciding whether to add, keep or delete a comment or docstring, when a function is long, deeply nested, flag-driven or has many parameters, when a user says "no comments" or "document this", or when matching a repository's style. For module and interface structure use craft-module-design; for error policy craft-error-handling; for step-by-step restructuring mechanics craft-refactoring.
---

# craft-clean-code

## Purpose

Use this to make code that a first-time reader can follow quickly and guess correctly about: names
that say what a thing is, functions that sit at one level of abstraction, comments that carry only
what the code cannot, and layout that puts related things together. It changes two habits: you
judge readability from the reader's side instead of your own, and you treat the books' rules as
defaults with stated reasons, so that you can tell when a rule does not fit the code in front of
you. The two main sources disagree on function size and comments; this skill gives you a way to
decide in context instead of applying either school blindly.

## Choose what applies

| Situation | Use | Reference |
|---|---|---|
| Naming a new variable, function, type, field, flag, column or config key; a name feels vague or hard to pick | Naming rules below | `references/naming.md` |
| Writing a new function or deciding whether to split or merge one; long, nested, flag-driven, many parameters | Function rules and the split test below | `references/functions.md` |
| Deciding whether to write, keep, rewrite or delete a comment or docstring; user says "no comments" or "add docs" | Comment decision procedure below | `references/comments.md` |
| Writing a new class or module from scratch | Comments-first skeleton (in comments reference), then function rules | `references/comments.md` |
| Placing a new helper, field or constant; ordering a file; style disputes; repository has a formatter | Layout rules below; follow the repository's formatter and conventions first | `references/formatting-and-layout.md` |
| Asked to "clean up", "tidy" or "refactor for readability" code that already works | Ordered review passes | `references/review-passes.md` |
| Reviewing a diff or pull request for quality; need a named reason for each finding | Smell codes as checklist | `references/smells-and-heuristics.md` |
| A rule here conflicts with the codebase, the language idiom, or the other school | Arbitration rules | `references/contested-rules.md` |
| User cites Clean Code 2nd edition, or asks what changed | Summary of the excerpt | `references/second-edition-changes.md` |
| Small bug fix or feature in someone else's file | Match the file. Apply only the "leave it no worse" check from Verify; propose larger cleanup separately | — |

This skill does not apply, or applies only lightly, when:

- The question is how to shape a module, class, interface or layer (depth, information hiding,
  cohesion): use `craft-module-design`. This skill takes the module boundary as given.
- The question is what a piece of code should do when something fails: use `craft-error-handling`.
- You need the mechanics of a specific restructuring (extract, move, replace conditional with
  polymorphism) or a safety workflow for code without tests: use `craft-refactoring`.
- The code is generated, vendored, or owned by a formatter or code generator: do not hand-clean it.
- The code is a throwaway spike or one-off script the user has said will be discarded.
- The user asked for a minimal diff. Then report readability findings instead of applying them.

## How to apply

### Ground rules

1. Optimise for the reader. Code is read far more often than it is written (the 10:1 figure is an
   informal observation, not a measurement), and the reader does not have your context. "Obvious"
   means a reader's first quick guess about behaviour is right; you cannot judge that well for your
   own code, so use the cold-read check in Verify.
2. The repository's conventions outrank these rules. Before writing, find the nearest existing
   analogue (same layer, same kind of task) and copy its naming scheme, declaration order,
   error-handling idiom, comment style and test style. Consistency lets readers transfer what they
   learned elsewhere; a locally "better" style breaks that. Introduce a different convention only
   if you have information the original authors lacked and the change is worth migrating every
   old use; default to no.
3. When you make readers need information, prefer in this order: remove the need (simpler design,
   fewer special cases); rely on what readers already know (conventions, expected behaviour); state
   it in the code (names first, then comments).
4. Cite a rule by tying it to the specific line or shape that triggered it, not to the rule's
   authority. The heuristics are reasons for a change, not a linter.
5. Clean in small behaviour-preserving steps with tests green after each. Working code is the
   starting point of cleaning, not the end: write the clumsy version under test, then refine.

### Names

Apply in this order; stop when the name passes the isolation test (a stranger seeing only the name
could guess closely what it refers to).

1. Say what the thing is, with the distinguishing noun and the unit: `timeoutMs`, `fileBlock` vs
   `diskBlock`, `overdueInvoices`. If a name needs a comment to explain it, fix the name first.
2. Booleans are predicates whose true value is evident: `cursorVisible`, not `blinkStatus`.
3. Not too generic (`data`, `info`, `count`, `result`, `tmp`, `flag`, `value`) and not too specific
   (a parameter called `selection` on a function that works on any range).
4. One word per concept across the codebase, and that word used for nothing else. Two things of
   the same kind get a distinguishing prefix on the shared name (`srcFileBlock`, `dstFileBlock`).
   If two names differ, the things must differ; never disambiguate with digits or noise words.
5. Length follows the distance between declaration and use: `i` in a three-line loop, a full
   phrase for anything public or long-lived. Then cut words that add no distinction.
6. Functions say everything they do, including side effects and whether they mutate or return a
   new value (`addDaysTo` vs `daysLater`; `createOrReturnX`, not `getX`, for lazy creation).
7. Do not encode what the type system or tooling already shows, and do not encode anything that
   can go stale. Unit and kind suffixes in dynamically typed code are fine.
8. If no simple, precise name comes, treat that as a design signal: the thing probably does more
   than one job or has no clean definition. Reconsider the factoring before settling for a vague
   name.

### Functions

Write and review each function against these, in order of weight:

1. One level of abstraction: every statement is one step below what the function's name promises.
   A high-level call next to raw string or index manipulation is the commonest violation.
2. One job, done completely. Test: can you describe it as "to do X, we A, then B, then C" with all
   steps at one level, and name it without "and"/"or"?
3. Name matches all observable effects. A "check" that also resets a session is a hidden side
   effect; either remove the effect or put it in the name.
4. Few things for the caller to track: avoid boolean or enum parameters that select a mode (split
   into named functions, or use a named/enum argument where the language has them); group values
   that travel together into one object; avoid arguments that are silently written to.
5. A query answers, a command changes state; do not make a setter-like command return an ambiguous
   status. Atomic read-modify-write operations (`pop`, `putIfAbsent`, compare-and-set) are the
   accepted exception because splitting them creates races.
6. The same type-switch or if-chain must not appear in several functions. Keep one, and let it
   build polymorphic objects, or use exhaustive matching over a closed type so the compiler flags
   every site when a case is added.
7. Order-dependent steps are made visible: pass each step's result to the next, or merge the steps
   into one function that performs them in order.
8. Nesting stays shallow (the source's target is one or two levels); guard clauses and early
   returns are fine.

**Whether to split a function.** Length alone is not the criterion; the sources disagree on size
(see `references/contested-rules.md`) but agree on these tests.

Split when at least one holds, and the extracted piece passes the keep-test below:
- statements sit at mixed levels of abstraction;
- there are sections with banner or labelling comments (a comment that labels a block is a request
  for a function with that name);
- a block is duplicated, or differs from another only in literals;
- a conditional's intent is not readable (`if (shouldBeDeleted(timer))` reads better than the raw
  boolean expression);
- the function has a mode flag, or its name needs "and".

Keep-test for the extracted piece: its name says more than a restatement of its body; a reader of
the child needs to know nothing about the parent; a reader of the parent does not need to open the
child. If you must flip between the two to understand either, the split is wrong: rejoin them or
cut somewhere else.

Do not split when: the only available name restates the code; the pieces share so much state that
the helper needs many parameters or new fields just to carry it; the blocks interact so that
seeing them together is what makes them understandable; or the only argument is a line count.

### Comments

For each comment you are about to write, keep or delete:

1. Can a rename, an extracted function or variable, or a named constant carry the information?
   Do that instead.
2. Could someone who has never seen the code write this comment just from the adjacent code, or
   does it reuse the words of the name it documents? Delete it, or rewrite it with different words
   that add meaning.
3. Does it carry something the code cannot: the abstraction a caller relies on, units, inclusive
   or exclusive bounds, what null or absence means, who owns or closes a resource, an invariant, a
   side effect, a precondition or call order, when and on which thread a handler runs, why it is
   done this way, what goes wrong if changed, a link to the issue or spec? Write it, briefly, next
   to the code it describes.
4. Is it history, authorship, a change log, a banner, a closing-brace tag or disabled code? Remove
   it; version control and the tracker hold that.
5. Is it about something this code does not control (a default set elsewhere, another module's
   behaviour)? Move it to the owner, or point to it; do not duplicate.

Defaults by kind of declaration:

| Kind | Default |
|---|---|
| Public or exported API, anything callers use without reading the body | Interface comment: behaviour as callers see it, each parameter and return (units, ranges, nullability), side effects, errors, preconditions. No implementation detail. Both schools agree here. |
| Internal function with a precise name and typed signature | No comment unless item 3 above applies. If the repository documents every declaration, follow the repository. |
| Field, constant, configuration value | Comment when name and type leave units, bounds, null meaning, ownership or an invariant open. Describe what it represents (a noun), not how code updates it. |
| Inside a body | Only "what at a higher level" for a long block or loop, "why", "how we get here", and warnings. Never narration of the next line. |
| Cross-module rule ("adding a status means editing these other places") | One copy at the place a developer must visit, with short pointers elsewhere. |

When writing a new class or module, draft the interface comments and signatures before the bodies.
A comment you cannot make both short and complete, or one that has to describe the implementation,
means the abstraction is wrong; fix the design before coding (procedure in `references/comments.md`).

Never leave narration of generated code ("loop over the items"), changelog comments, or
commented-out code. Update or delete every comment your change makes false, in the same diff.

### Layout

1. Run the repository's formatter and accept its output; do not hand-format against it or argue
   style in review.
2. Order a file so it reads top-down: high-level entry points first, each helper below its first
   caller, lowest-level detail last. Follow the language's required or conventional order where it
   differs (definition-before-use languages, a standard type/constructor/method order).
3. Keep related things vertically close: declare a local at first use; keep sibling variants
   (overloads, functions sharing a naming scheme) together; do not separate tightly related lines
   with blank lines or filler comments.
4. Blank lines mark a change of thought; one between concepts, none inside a cohesive group.
5. Put configurable values and defaults at the high level and pass them down; replace unexplained
   literals with named constants unless the literal is universally recognised in self-explanatory
   code.
6. Return several values as a named record or struct, not an anonymous pair or map, when the
   element meanings are not evident at the use site.
7. A wish for column alignment, banners or a very long file is a size problem; question the list,
   function or module, not the formatting.

### Cleaning existing code

Use the ordered passes in `references/review-passes.md`. In brief: confirm the tests and what they
cover; names and encodings; conditionals; mixed levels and responsibilities; hidden order
dependencies; boundary arithmetic; dead code; comments; layout. Run the whole suite after each
step. Expect some steps to undo earlier ones; that is normal.

When the next two additions of a kind (another type, another flag, another parallel map) would
make a structure unmanageable, stop adding and restructure first; say so to the user.

## Verify

Run these on your own change before reporting. Show the user the command output and the list of
findings, not a claim that the code is "clean".

1. **Behaviour unchanged.** Run the full test suite (all levels that exist, not only unit tests)
   before and after; it must be green both times with no test edited to make it pass. If the code
   you are cleaning has no tests, write characterisation tests first or limit yourself to
   tool-driven renames; say which.
2. **Formatter and linter.** Run the project's formatter and linter; the formatter must produce an
   empty diff on your files and the linter no new findings. No newly disabled warnings or skipped
   tests.
3. **Cold read.** Re-read the diff as if new to it, or hand it to a fresh context, and for each
   function state what it does from the name and signature alone, then compare with the body. Any
   wrong guess is a finding. Read names aloud in a sentence; cover bodies and read only names and
   call sites.
4. **Split check.** For each function you extracted: is the name more than a restatement; can the
   parent be read without opening it; how many parameters or new fields exist only to carry state
   to it? For each function you left long: is every statement at one level, and can it be read
   block by block?
5. **Comment check.** For each comment added or kept: apply the stranger test; check it against
   actual behaviour by reading the code path; check that it sits next to what it describes. For
   each public declaration: can a caller use it correctly from the comment and signature alone
   (units, bounds, null, side effects, errors, preconditions)? Does any interface comment name
   private fields, internal helpers or algorithm steps?
6. **Mechanical searches on the diff** (adapt patterns to the language; the searches are derived
   from the catalogue entries, not prescribed by the books):
   - commented-out code, journal or byline comments, doc blocks that echo the signature;
   - boolean literals at call sites; functions with a mode parameter;
   - the same switch or if-chain on one discriminator in more than one function;
   - bare numeric or string literals in logic; `+ 1` / `- 1` repeated on the same expression;
   - `a.b().c().d()` chains across module boundaries;
   - anonymous pairs, tuples or string-keyed maps used as records;
   - one concept under two names, or one name for two concepts (list the verbs used for fetch,
     create, delete, convert in the module; each should map one-to-one);
   - names that still state a type or unit the code no longer has;
   - `TODO` without a condition for resolving it.
7. **No worse.** Touched files are no worse than before on names, nesting, duplication and
   conditional complexity, and unrelated cleanups are in a separate commit or listed as proposals.

Done means:

- Tests green before and after, formatter diff empty, no suppressed checks.
- Every new or changed name passes the isolation test; no concept has two names in the diff.
- Every function touched is at one level of abstraction and its name covers its effects.
- No comment restates code; every public declaration you added has an interface comment; no
  comment made false by the change remains.
- Each finding you report cites the line and the reason (smell code where useful).
- The diff contains only what the task and the agreed cleanup cover.

## Proportion and limits

- Scope. Opportunistic cleanup (rename one variable, extract one conditional) inside a task is
  fine when small and behaviour-preserving; a bug fix should not grow into a broad refactor without
  agreement. Keep cleanup commits separate so the functional change stays reviewable.
- Cost of structure. Each extraction adds a name and an indirection; many single-use helpers make
  a reader jump around, and the source itself ranks "fewest classes and methods" as a rule, below
  tests, no duplication and expressiveness. Structure that makes room for growth is justified by
  evidence that the growth is coming, not by habit.
- Evidence. The size limits (functions "hardly ever 20 lines", files around 200 lines with 500 as
  a ceiling, lines up to 120 characters) are one author's practice and a survey of seven Java
  projects; the author says there is no research behind small functions. Treat numbers as prompts
  to look, not thresholds to enforce, and prefer the repository's linter limits.
- Dated or language-bound material: Java import and constant rules (J1 to J3; J1 is contrary to
  current mainstream practice), Hungarian and member-prefix arguments that assume static types and
  an IDE, "prefer exceptions to error codes" in languages built on result values, "try as the
  first statement", HTML in doc comments, single-exit functions. See
  `references/contested-rules.md`.
- Contested: function size and comment volume. Do not pick a side silently; apply the arbitration
  rules and, when the choice is visible in a review, say which reasoning you used.
- The second edition is available here only as an excerpt (front matter, table of contents,
  chapter 3, index). Do not attribute specifics to its other chapters or its debate appendix.

## References

- `references/naming.md` — read when choosing or reviewing names: full rule set, the red flags,
  decision questions, language-convention adjustments.
- `references/functions.md` — read when writing, splitting, merging or reviewing a function:
  abstraction levels, arguments, flags, side effects, command/query, switches, duplication, the
  split and keep tests with examples.
- `references/comments.md` — read when deciding what to comment: the contents of interface, field,
  implementation and cross-module comments, the bad-comment table with fixes, the comments-first
  procedure, maintenance.
- `references/formatting-and-layout.md` — read when ordering a file, placing declarations, or
  settling style: vertical and horizontal rules, consistency and conventions, things that make
  code less obvious.
- `references/smells-and-heuristics.md` — read when reviewing: every coded entry (C1–C5, E1–E2,
  F1–F4, G1–G36, J1–J3, N1–N7, T1–T9) with recognition and remedy, plus where each is disputed.
- `references/contested-rules.md` — read when a rule conflicts with the other school, the language
  or the codebase: each dispute with both arguments and a deciding rule.
- `references/review-passes.md` — read when asked to clean working code: ordered passes, the
  stop-and-restructure trigger, the incremental migration sequence, lessons from the case studies.
- `references/second-edition-changes.md` — read when the 2nd edition of Clean Code is cited: what
  the excerpt shows changed, the chapter 3 principles and worked example, and what is not known.

## Sources

- Clean Code (1st ed.) foreword and introduction — structure of the book, the heuristic codes.
- Clean Code ch. 1 — definitions of clean code, read/write ratio, Boy Scout Rule, schools of thought.
- Clean Code ch. 2 — names. Ch. 3 — functions. Ch. 4 — comments. Ch. 5 — formatting.
- Clean Code ch. 12 — the four rules of simple design and their priority order.
- Clean Code ch. 14 and ch. 15 — the Args and ComparisonCompactor case studies (cleaning sequences).
- Clean Code ch. 17 and appendix C — the smells and heuristics catalogue and its cross-references.
- Clean Code 2nd ed. (excerpt) — introduction, detailed table of contents, ch. 3 "First Principles", index.
- A Philosophy of Software Design ch. 12, 13, 15 — why and what to comment, comments first.
- A Philosophy of Software Design ch. 14 — names. Ch. 17 — consistency. Ch. 18 — obvious code.
- A Philosophy of Software Design ch. 9 (method splitting) and ch. 16 (comment maintenance) are
  cited briefly where the disputes need them; their main treatment is in `craft-module-design` and
  `craft-refactoring`.
