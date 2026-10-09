# Smells and heuristics catalogue

The 66 coded entries of Clean Code ch. 17, as a review checklist. Each entry is a reason to change
code: the author compiled the list by asking "why did I make this change?" while refactoring.
Appendix C of the book maps each code to the case-study chapters where it was applied.

## Contents

1. How to use the codes
2. Quick index by review question
3. C — Comments (C1–C5)
4. E — Environment (E1–E2)
5. F — Functions (F1–F4)
6. G — General (G1–G36)
7. J — Java (J1–J3)
8. N — Names (N1–N7)
9. T — Tests (T1–T9)
10. Decision rules distilled from the entries
11. Disputed and dated entries
12. Mechanical checks
13. Where each code is demonstrated

## 1. How to use the codes

- Use a code to name the reason for a finding, attached to a specific line: "`render(true)` at
  line 40 — selector argument (G15); split into `renderForSuite` and `renderForSingleTest`". The
  book's introduction says a heuristic has little value alone; its value is the link to the
  concrete decision it justified.
- The chapter's conclusion says the list is not complete and that clean code does not come from
  following rules; the entries express a value system. Treat a match as a prompt to look, then
  judge.
- Entry format below: **recognise**, **why**, **remedy**, and **note** where the entry carries
  its own exception or is disputed (details in section 11 and `contested-rules.md`).
- Related files: `naming.md` (N), `functions.md` (F and the function-shaped G entries),
  `comments.md` (C), `formatting-and-layout.md` (G10, G11, G24, G35). T entries are summarised
  here; their full treatment is in `craft-testing`. Entries about class and module structure
  (G6–G8, G13, G14, G17, G18, G22, G36) are developed in `craft-module-design`.

## 2. Quick index by review question

| Question | Codes |
|---|---|
| Is anything here dead, disabled or leftover? | C5, F4, G9, G12, C2 |
| Do the comments earn their place? | C1, C2, C3, C4, C5 |
| Can I tell what this call does from its name? | N1, N4, N7, G20, G16 |
| Are the names consistent and at the right level? | N2, N3, N5, N6, G11 |
| Does this function do one thing at one level? | G30, G34, F3, G15 |
| Are the parameters reasonable? | F1, F2, F3, G15 |
| Is anything repeated? | G5, G23 |
| Are conditions readable? | G28, G29, G33, G19 |
| Are there unexplained literals? | G25, G35 |
| Does order matter without saying so? | G31 |
| Is this code in the right place? | G6, G7, G10, G13, G14, G17, G18, G22, G32, G35, G36 |
| Does it expose too much? | G8 |
| Is it correct at the edges, and does the author know why it works? | G2, G3, G21, G26 |
| Have safeties been switched off? | G4 |
| Does structure enforce the rule, or only convention? | G24, G27 |
| Can I build and test in one step? | E1, E2 |
| Are the tests adequate? | T1–T9 |
| Language-specific hygiene | G1, J1, J2, J3 |

## 3. C — Comments

**C1 Inappropriate Information**
- Recognise: change history, author, last-modified date, ticket numbers held in comments.
- Why: clutters the source with material another system keeps better.
- Remedy: move to version control or the tracker. Comments are for technical notes about code
  and design.

**C2 Obsolete Comment**
- Recognise: old, irrelevant or wrong; drifted away from the code it described.
- Remedy: update or delete at once; better, avoid comments that will go stale.

**C3 Redundant Comment**
- Recognise: restates the code (`i++; // increment i`); a doc block that says no more than the
  signature.
- Remedy: delete. A comment should say what the code cannot say for itself.

**C4 Poorly Written Comment**
- Recognise: rambling, ungrammatical, states the obvious.
- Remedy: if it is worth writing, write it well: careful words, correct grammar, brief.

**C5 Commented-Out Code**
- Recognise: stretches of disabled code.
- Why: nobody knows how old it is or whether it matters; everyone assumes someone else needs it;
  it rots as names and conventions change.
- Remedy: delete; version control remembers.

## 4. E — Environment

**E1 Build Requires More Than One Step**
- Recognise: checking out many pieces, arcane command sequences, hunting for extra artifacts.
- Remedy: one command to check out, one command to build.

**E2 Tests Require More Than One Step**
- Remedy: all unit tests run with one command; running them is quick, easy and obvious.

For an agent: find the single build and test commands before starting work; if none exist, say so
and propose adding them (adaptation).

## 5. F — Functions

**F1 Too Many Arguments**
- Recognise: more than three; preference order is none, one, two, three.
- Remedy: argument object, make it a method, move a collaborator to a field, split the function
  (see `functions.md` section 5).
- Note: disputed in languages with named arguments and for dependency-injected constructors.

**F2 Output Arguments**
- Recognise: an argument the function writes to.
- Why: readers expect arguments to be inputs.
- Remedy: return a value, or change the state of the object the function belongs to.

**F3 Flag Arguments**
- Recognise: a boolean parameter.
- Why: it declares that the function does more than one thing.
- Remedy: split the function. See G15.
- Note: a boolean that is data, not a mode, is not this smell.

**F4 Dead Function**
- Recognise: never called.
- Remedy: delete; version control remembers.

## 6. G — General

**G1 Multiple Languages in One Source File**
- Recognise: one file mixing a programming language with markup, templates, queries, scripts,
  doc-comment markup and prose.
- Remedy: ideally one language per file; realistically, minimise the number and extent of extras.

**G2 Obvious Behavior Is Unimplemented**
- Recognise: a function or type that does not do what another programmer would reasonably expect
  (a day-name parser that rejects common abbreviations or is case-sensitive).
- Why: once the obvious is missing, readers stop trusting names and read every implementation.
- Remedy: implement the expected behaviour (principle of least surprise).

**G3 Incorrect Behavior at the Boundaries**
- Recognise: corner cases trusted on intuition.
- Remedy: find every boundary condition and write a test for it. Pairs with T5 and G33.

**G4 Overridden Safeties**
- Recognise: compiler warnings disabled, failing tests turned off "for now", manual control of
  things the toolchain manages.
- Why: each safety was overridden because it was inconvenient; the deferred cost accumulates.
- Remedy: do not override; if truly necessary, record it as a known risk.

**G5 Duplication**
- Recognise: (1) identical clumps of code; (2) the same switch or if-chain testing the same
  conditions in several places; (3) modules with similar algorithms but different lines.
- Why: every duplication is a missed abstraction, and each copy must be changed together.
- Remedy: (1) extract a function; (2) polymorphism; (3) template method or strategy.
- Note: ranked among the most important rules in the book.

**G6 Code at Wrong Level of Abstraction**
- Recognise: a base type or interface holding constants, variables or functions that only make
  sense for some implementations (`percentFull()` on a general stack interface).
- Why: general concepts and details must be in different containers, completely; returning a fake
  value for the cases where the member is meaningless is a lie.
- Remedy: move the detail to the derived or more specific abstraction.
- Note: the book says there is no quick fix; isolating abstractions is hard.

**G7 Base Classes Depending on Their Derivatives**
- Recognise: a base type mentions the names of its derivatives.
- Why: the general concept should be independent of the specific ones so they can be deployed
  separately.
- Remedy: remove the dependency.
- Note: stated exception: a strictly fixed set of derivatives that the base selects among (as in
  some state machines), which always deploy together.

**G8 Too Much Information**
- Recognise: wide interfaces; types with many methods, many fields, many protected members.
- Why: more exposed surface means more to depend on.
- Remedy: hide data, helpers, constants and temporaries; keep interfaces small.

**G9 Dead Code**
- Recognise: a branch for an impossible condition, a handler for an error that is never raised,
  uncalled helpers, cases that never occur.
- Why: it is not maintained when designs change.
- Remedy: delete. A way to test a suspect condition (ch. 15): disable it, run the tests, and
  reason about whether it could ever be true.

**G10 Vertical Separation**
- Recognise: a variable declared far from its use; a private function far from its first caller.
- Remedy: locals just above first use; private functions just below their first use.

**G11 Inconsistency**
- Recognise: similar things done in different ways; different names for the same kind of object.
- Remedy: choose conventions carefully and keep to them (the same variable name for the same
  kind of thing everywhere; parallel names for parallel operations).

**G12 Clutter**
- Recognise: empty default constructors, unused variables, uncalled functions, comments with no
  information.
- Remedy: remove.

**G13 Artificial Coupling**
- Recognise: a general enumeration, constant or function declared inside a specific type because
  it was convenient.
- Why: everything using it must now know that type.
- Remedy: take the time to decide where it belongs.

**G14 Feature Envy**
- Recognise: a method that mostly uses another object's accessors to manipulate that object's
  data.
- Remedy: move the behaviour to the type that owns the data.
- Note: stated exception: do not move it if that would drag an unrelated reason to change (such
  as an output format) into the data-owning type.

**G15 Selector Arguments**
- Recognise: a boolean, enum or integer argument used only to choose behaviour
  (`calculateWeeklyPay(false)`).
- Why: unreadable at the call site; combines several functions into one.
- Remedy: split into separately named functions with a shared private helper.

**G16 Obscured Intent**
- Recognise: run-on expressions, encoded names, magic numbers; small dense code that is hard to
  penetrate.
- Remedy: spend the time to make intent visible: names, explanatory variables, constants.

**G17 Misplaced Responsibility**
- Recognise: code placed where it was convenient instead of where a reader would look.
- Remedy: place by least surprise; use function names as the guide to where work is expected to
  happen. If performance forces another place, rename to reveal it.

**G18 Inappropriate Static**
- Recognise: a static function for which alternative implementations are plausible.
- Remedy: make it a non-static member. A static is right when all data comes from arguments and
  polymorphism is implausible (`max`).
- Note: assumes object polymorphism is the extension mechanism; see section 11.

**G19 Use Explanatory Variables**
- Recognise: a calculation whose intermediate meanings are not named.
- Remedy: break it into named intermediate values.
- Note: the book says this is hard to overdo; others find heavy use noisy.

**G20 Function Names Should Say What They Do**
- Recognise: `date.add(5)` — which unit, and does it mutate or return a new value?
- Remedy: rename to state it (`addDaysTo`, `daysLater`); if you must read the implementation to
  know what a call does, rename or restructure.

**G21 Understand the Algorithm**
- Recognise: code made to "work" by adding conditions and flags until tests pass.
- Remedy: before calling it done, know that the solution is correct; refactor until it is
  evident how it works.
- Note: exploration is a legitimate route; not knowing what your own code does is the fault.

**G22 Make Logical Dependencies Physical**
- Recognise: module A assumes something about module B (a page size, a format) without asking B.
- Remedy: B exposes it and A asks. The dependent module explicitly requests everything it
  depends on.

**G23 Prefer Polymorphism to If/Else or Switch/Case**
- Recognise: a switch on a type; the same selection made in more than one place.
- Remedy: "one switch" rule: at most one switch per kind of selection, creating polymorphic
  objects that replace the others.
- Note: the book flags its own tension with ch. 6 (switch is appropriate where operations change
  more often than types); see section 11.

**G24 Follow Standard Conventions**
- Recognise: code that departs from the team's standard.
- Remedy: follow the team standard, based on industry norms; the code itself is the example.

**G25 Replace Magic Numbers with Named Constants**
- Recognise: raw numbers or strings whose meaning is not self-describing, including in tests.
- Remedy: named constants.
- Note: exceptions for values universally recognised in self-explanatory code; counter-exception
  for long well-known literals, which still get a name because nobody checks their digits.

**G26 Be Precise**
- Recognise: decisions made loosely: assuming the first match is the only one; floating point for
  money; skipping locking because concurrent update "seems unlikely"; over- or under-constraining
  a declaration.
- Remedy: decide deliberately and handle the exceptions: check for null where it can occur,
  verify uniqueness where one result is expected, use integers or a money type, lock where
  concurrent update is possible.

**G27 Structure over Convention**
- Recognise: a design rule upheld only by naming or by everyone remembering to write the same
  switch.
- Remedy: use structure that forces compliance, such as abstract methods every variant must
  implement.

**G28 Encapsulate Conditionals**
- Recognise: a compound boolean expression inline in an `if` or loop.
- Remedy: extract a function or variable named for the intent.

**G29 Avoid Negative Conditionals**
- Recognise: `if (!buffer.shouldNotCompact())`.
- Remedy: express the positive.

**G30 Functions Should Do One Thing**
- Recognise: a function with several sections performing a series of operations.
- Remedy: split into functions that each do one.
- Note: disputed where the pieces are trivial; see `contested-rules.md`.

**G31 Hidden Temporal Couplings**
- Recognise: calls on shared state that must occur in order, with nothing enforcing it.
- Remedy: each step returns what the next needs. The extra syntax exposes real complexity.
- Note: ch. 15 found that a parameter added only to force order looked arbitrary; merging the
  ordered steps into one function was clearer.

**G32 Don't Be Arbitrary**
- Recognise: structure with no evident reason (a public type nested in an unrelated one).
- Why: arbitrary-looking structure invites others to change it.
- Remedy: have a reason and let the structure communicate it.

**G33 Encapsulate Boundary Conditions**
- Recognise: `+1` / `-1` adjustments scattered through the code.
- Remedy: one named place (`nextLevel = level + 1`).

**G34 Functions Should Descend Only One Level of Abstraction**
- Recognise: statements at different levels in one function.
- Remedy: extract so that all statements are one level below the function's name; expect to
  iterate, since one separation often reveals another.
- Note: the book calls this possibly the hardest heuristic to interpret.

**G35 Keep Configurable Data at High Levels**
- Recognise: a default or configuration constant buried in low-level code.
- Remedy: define it at the high level and pass it down.

**G36 Avoid Transitive Navigation**
- Recognise: `a.getB().getC().doSomething()`.
- Why: if many modules encode the path, inserting something between B and C means editing every
  chain.
- Remedy: immediate collaborators offer the service needed.

## 7. J — Java

**J1 Avoid Long Import Lists by Using Wildcards**
- Book's remedy: import the whole package when using two or more of its classes.
- Note: contrary to mainstream Java practice today; do not apply by default. See section 11.

**J2 Don't Inherit Constants**
- Recognise: constants obtained by implementing an interface that declares them.
- Remedy: import the constants explicitly. Portable form: do not use inheritance to obtain scope.

**J3 Constants versus Enums**
- Recognise: integer codes as named constants.
- Remedy: an enumeration, which keeps its meaning and can carry fields and methods. Portable
  form: prefer named closed types over integer codes.

## 8. N — Names

**N1 Choose Descriptive Names** — Do not name quickly; re-evaluate as meaning drifts. Good names
set expectations so that each helper is what the reader expected.

**N2 Choose Names at the Appropriate Level of Abstraction** — Name for the abstraction, not the
implementation (`connect(locator)`, not `dial(phoneNumber)`).

**N3 Use Standard Nomenclature Where Possible** — Pattern names, language idioms, and the
project's shared domain language.

**N4 Unambiguous Names** — Recognise: `doRename` calling `renamePage`. Remedy: precise even if
long.

**N5 Use Long Names for Long Scopes** — Length proportional to scope; short names are right in
short scopes.

**N6 Avoid Encodings** — No type, scope or subsystem prefixes; tools supply that.

**N7 Names Should Describe Side-Effects** — Recognise: `getX()` that creates X. Remedy: a name
that says everything the function does.

Detail and adjustments: `naming.md`.

## 9. T — Tests

Summaries; see `craft-testing` for the full treatment.

- **T1 Insufficient Tests** — Test everything that could possibly break; "seems enough" is not a
  measure. Sets an ideal; no percentage is given.
- **T2 Use a Coverage Tool** — Coverage reports show untested branches quickly.
- **T3 Don't Skip Trivial Tests** — Cheap to write; their documentary value exceeds their cost.
- **T4 An Ignored Test Is a Question about an Ambiguity** — When a requirement is unclear, record
  the question as a disabled test.
- **T5 Test Boundary Conditions** — The middle is usually right; the edges are misjudged.
- **T6 Exhaustively Test Near Bugs** — Bugs cluster; after finding one, test that function
  thoroughly.
- **T7 Patterns of Failure Are Revealing** — Ordered, complete cases expose patterns in which
  inputs fail.
- **T8 Test Coverage Patterns Can Be Revealing** — Which code passing tests do and do not execute
  hints at why failing tests fail.
- **T9 Tests Should Be Fast** — A slow test does not get run.

## 10. Decision rules distilled from the entries

- **A conditional on type appears.** One switch per kind of selection, creating polymorphic
  objects (G23); the same chain elsewhere is duplication (G5); structure beats convention (G27).
  Counter-case: where operations are added more often than types, a switch over data may be
  right.
- **Where does this code or constant go?** Where a reader expects, judged by names (G17); not
  where it creates a pointless dependency (G13, G32); configuration at the top, passed down
  (G35); detail out of base types (G6); the base never names derivatives (G7); if A needs a fact
  owned by B, A asks B (G22).
- **Static or instance?** Static only if all data comes from arguments and polymorphism is
  implausible (G18).
- **Name the constant or keep the literal?** Name it unless universally recognised in
  self-explanatory code; always name long literals (G25).
- **Move an envious method?** Yes, unless it brings an unrelated axis of change (G14).
- **Boolean or enum parameter?** Split into named functions (F3, G15).
- **Order-dependent calls?** Chain outputs to inputs, or merge into one function (G31).

## 11. Disputed and dated entries

From the notes' caveats.

| Entry | Issue | Handling |
|---|---|---|
| J1 | Most current Java style guides and default tool settings forbid wildcard imports: they hide where names come from and can break compilation when a package gains a clashing name | Author's view only; follow the project's import rules |
| J2, J3 | Java-specific and of their era | Keep the portable forms given above |
| F1, F3, G15, G30, G34 | Among the most disputed parts of the book; critics argue extreme decomposition yields shallow functions and scatters logic. The book's own G30 example splits a short loop into three functions | Apply the split and keep tests in `functions.md` |
| G23 | The book flags tension with its ch. 6. With closed sum types and exhaustive matching, the compiler gives the completeness guarantee without classes | Core: no repeated type-switch; additions compiler-checked |
| G18 | Assumes object polymorphism. In functional or module-oriented languages free functions are normal and substitution is by passing functions | Follow the language idiom |
| G19, N4 | "Hard to overdo" and very long names: some find them noisy | Limit by scope (N5) and by how many call sites exist |
| G25, G14, G7, G21 | Carry their own stated exceptions | Read the note on each |
| T1, T3 | State an ideal, not a threshold | See `craft-testing` |
| C series | The stance that comments are mostly failures is contested; the catalogue itself only condemns specific bad kinds and endorses well-written technical notes | See `comments.md`, `contested-rules.md` |
| N6 | Light conventions such as a leading underscore for private members persist in dynamically typed languages | Do not encode what tooling shows |

## 12. Mechanical checks

Checks an agent can run on a diff or module. Those marked (inferred) are derived in the notes,
not given by the book. Adapt patterns to the language.

- One-command build and one-command test exist and work from a clean checkout (E1, E2).
- No commented-out code, change logs or signature-echo doc blocks in the diff (C1, C3, C5).
- No newly disabled warnings; no skipped tests without a stated open question (G4, T4).
- Repeated switch or if-chain on the same discriminator: more than one is a finding (G23, G5)
  (inferred).
- Method chains across module boundaries (G36); boolean literals at call sites (G15, F3); bare
  numeric and string literals (G25); `+ 1` / `- 1` repeated on the same expression (G33)
  (inferred).
- For each function: does the name alone tell the caller what it does, including side effects
  and mutation versus new value (G20, N7)? All statements one level below the name (G34)? One
  thing (G30)?
- For each interface or base type: does any member only make sense for some implementations
  (G6)? Does the base mention a derivative (G7)?
- Each boundary condition has a test (G3, T5); coverage tool run and uncovered branches inspected
  (T2); after a bug fix the surrounding function is tested thoroughly (T6).
- Unused functions, variables and parameters reported by the compiler or linter (F4, G9, G12)
  (adaptation).
- Suite runtime short enough to run on every change (T9); the book gives no threshold.

## 13. Where each code is demonstrated

From appendix C (chapter numbers only; the printed table has page-number slips, so use it as a
pointer, not an authority).

- Ch. 14 (Args refactoring): F1, F4, G23, N5.
- Ch. 15 (ComparisonCompactor): G10, G11, G28, G29, G30, G31, G32, G33, N1, N4, N5, N6, N7.
- Ch. 16 (SerialDate; covered by `craft-refactoring`): C1–C3, F4, most of G1–G21, G23–G25,
  J1–J3, N1–N4, T1–T3, T5–T8.
- Ch. 9: G4, G5. Ch. 6: G6, G23, G34, G36. Ch. 5: G10, G35. Ch. 2: N5. Ch. 1: G34.
- Defined only in ch. 17 with no demonstration elsewhere: C4, C5, E1, E2, F2, F3, G26, G27, T4,
  T9.

The sequences from ch. 14 and ch. 15 are in `review-passes.md`.
