# Contested rules and how to decide

Where the sources disagree with each other, with their own later editions, or with current
language practice. For each: the positions, the reasoning on each side, what they share, and a
rule for deciding in the code in front of you.

Sources: Clean Code (CC) ch. 1, 3, 4, 5, 12, 17 and the caveats recorded in the notes; Clean Code
2e excerpt; A Philosophy of Software Design (PoSD) ch. 9, 12, 13, 14, 15, 17, 18.

## Contents

1. How to arbitrate in general
2. Function size and splitting
3. Comments
4. Name length
5. Argument count, flags and output arguments
6. Switch versus polymorphism
7. Duplication versus fewer elements
8. Exceptions versus error values; try-first
9. Command/query separation
10. Encodings and prefixes
11. Formatting numbers and styles
12. Opportunistic cleanup versus minimal diff
13. Changing a convention
14. Room for growth versus YAGNI
15. Lesser disputes
16. What the two schools agree on

## 1. How to arbitrate in general

Clean Code itself says, in its first chapter, that its rules are one school's opinions stated as
absolutes, that many are controversial, and that other schools have equal claim. The 2nd
edition's chapter 3 calls its principles guidelines, not laws, to be applied in context. PoSD
states that readability is determined by readers, not writers. So:

1. **Codebase first.** If the repository shows a consistent practice (documented or evident in
   sibling files), follow it. Both books rank consistency above individual rules (CC G24; PoSD
   ch. 17).
2. **Language idiom second.** Where the language community has a settled answer (error values,
   doc comments, naming case, formatter output), use it.
3. **Then the shared tests.** Most disputes reduce to questions with observable answers: can the
   parent be read without opening the child; could a stranger have written this comment; does
   the name say more than the body. Use those, not counts.
4. **Reader evidence beats argument.** If a reviewer or a cold read stumbles, change the code.
5. **Say which reasoning you used** when the choice is visible in a review, in one line.

Never justify a change by the authority of a rule or a number alone.

## 2. Function size and splitting

**CC position (ch. 3, G30, G34; 2e ch. 3).** Functions should be very small: hardly ever 20
lines, mostly a handful; bodies of conditionals and loops a single call; one or two levels of
indentation. Extract until no further extraction yields a name that is more than a restatement.
Reasoning: small functions can be named precisely; the name documents the caller; mixed
abstraction levels hide the essential; extraction separates concerns so each change has one
obvious place.

**PoSD position (ch. 9, ch. 12).** Length alone is rarely a reason to split. Every split adds an
interface and separates code that is related. A long function is fine if it has a simple
signature and reads easily, even at hundreds of lines; several independent blocks in sequence can
be read block by block, and blocks that interact are better seen together. Over-splitting
produces shallow functions and "conjoined" pairs that cannot be understood apart. Expecting
readers to read implementations instead of comments drives exactly this over-splitting.

**Evidence.** CC's author states there is no research behind the size claim; it rests on
experience. PoSD's position is also argued from experience and examples. The notes record that
empirical studies show no clear optimal size.

**Shared ground.** One job per function; one level of abstraction; extract a cleanly separable
subtask that has a meaningful name; remove duplication; the reader decides.

**Where the 2nd edition stands.** Its table of contents shows a new chapter defending extraction
against five named objections (drowning in functions, obscured intent, performance, bouncing
around, entanglement) and an appendix recording a debate with PoSD's author on method length. The
text of both is not in the excerpt; do not attribute arguments to them. Chapter 3, which is
present, restates "small, a handful of lines" and concedes that added structure has a cognitive
cost that must be justified.

**Deciding rule.**

| Situation | Do |
|---|---|
| Mixed abstraction levels, labelled sections, duplicated block, unreadable condition, mode flag | Extract (both schools would) |
| The only possible name restates the body | Do not extract (CC's own stopping rule) |
| Helper would need many parameters or promoted fields to carry state | Do not extract; the pieces are conjoined |
| You must open the helper to follow the parent | Rejoin or re-cut |
| Long function, single level, reads block by block, simple signature | Leave it; add block-summary comments if helpful |
| Long function whose blocks interact through many locals | Keep together, or redesign the data so the interaction shrinks; a mechanical split makes it worse |
| Codebase or linter enforces a size limit | Follow it, but choose cut points by the tests above |
| Team style is many small functions and they read well | Follow it |

When in doubt, prefer the version in which a reader must hold less in mind at once, and check it
with a cold read.

## 3. Comments

**CC position (ch. 4).** A comment is at best a necessary evil, used to compensate for failing to
express intent in code. Comments rot because code moves and they do not follow; an inaccurate
comment is worse than none; truth is only in the code. So minimise comments by making code
self-explanatory. Permitted: legal, informative, intent, clarification, warning, TODO,
amplification, public API docs. Most other comments are bad.

**PoSD position (ch. 12, 13, 15).** "Good code is self-documenting" is a myth. Only the formal
part of an interface is in the code; what a method means at a high level, the meaning of
results, rationale, and the conditions for calling it can only be in comments. Without comments
the only abstraction is the declaration, so users must read implementations, which means there is
no abstraction. Every class, method and field should have a comment (rare exceptions for
truly obvious declarations). Staleness is handled by proximity, avoiding duplication, and review.
Writing comments first is a design tool.

**Shared ground.** Delete comments that restate code. Do not use comments to excuse unclear code.
Explain why. Document public interfaces. Keep comments next to what they describe. Remove
commented-out code, journals and bylines.

**The real difference** is the default for internal declarations and how much weight a name can
bear. CC: a long descriptive name beats a comment. PoSD: names help, but units, bounds, null
meaning, ownership, invariants, side effects and call-order rules do not fit in a name.

**2nd edition.** The comments chapter opens with a section titled "compensating for failure" and
keeps good and bad lists (with TODO now listed under bad comments), and the debate appendix has a
comments section. Index entries point to "long names vs. comments", "missing vs. incorrect comments" and
"interface comments". Headings and pointers only; the arguments are not available.

**Deciding rule.**

1. Public or exported API, or anything used without reading its body: write an interface comment
   with the PoSD contents. Both schools accept this.
2. Information that a signature cannot express (units, inclusive/exclusive, null, ownership,
   invariant, side effect, precondition, thread, rationale, warning): comment it, wherever it
   occurs. This is PoSD's point, and it falls inside CC's "informative", "intent" and "warning"
   categories.
3. Information a rename, extraction or constant can carry: put it in code. This is CC's point,
   and PoSD agrees that names reduce the need.
4. Internal declarations where a precise name and types leave nothing open: follow the
   repository. If it documents everything, do so with real content; if it is sparse, do not add
   comments that fail the stranger test.
5. (Adaptation, not from the books.) A user says "no comments": keep those under rule 2 that prevent misuse or record a
   non-obvious reason, and say that you kept them and why; or, if the instruction is absolute,
   comply and report what information is now carried nowhere.
6. A user says "document everything": write real content; where nothing can be added to a
   trivial accessor, say so instead of echoing the name.

Never: narration of the next line, change logs, disabled code, name-echo doc blocks.

## 4. Name length

**CC and PoSD** both favour descriptive names and both tie length to scope. **The Go style**
(reported in PoSD ch. 14) favours very short names, on the grounds that long names obscure what
the code does. PoSD's reply: the long version is no harder to read; reading the short one
required working out what a letter meant; short names reused for several meanings breed the kind
of bug in the `block` story; a short name that means the same thing everywhere is fine.

**Shared ground:** the farther the use from the declaration, the longer the name.

**Deciding rule:** follow the language community's habit for locals and receivers; lengthen any
name that crosses a function boundary, is reused with more than one meaning, or that a reader
queries. Trim words that add no distinction (CC ch. 2 "gratuitous context").

## 5. Argument count, flags and output arguments

**CC:** none, one, two; avoid three; more needs special justification. Booleans as arguments are
always a sign of two functions. Output arguments are to be avoided.

**Counter-positions (notes' caveats):** the ladder is a heuristic built on positional arguments.
Named and default arguments, builders and options objects remove the ordering problem.
Dependency-injected constructors legitimately take several collaborators. A boolean that is data
(`setEnabled(true)`) is fine; a mode can be an enum or a named argument. In C, C++, Go, C# and
Rust, output parameters or mutable borrows are idiomatic for buffer reuse and performance.

**Deciding rule:** minimise what the reader must track at the call site. Ask: can a reader of the
call tell what each argument is without opening the declaration? If not, name the arguments,
group them, or split the function. Avoid surprising writes to arguments; a conventional
out-buffer is not surprising.

## 6. Switch versus polymorphism

**CC (ch. 3, G23, G27):** every switch on type is suspect; allow one per kind of selection, to
create polymorphic objects. Structure that the compiler enforces is better than a convention that
every switch be kept in step.

**CC's own counter (ch. 6, cited in G23):** where new operations are added more often than new
types, data plus switch is appropriate; the book says this case is rare. **2e ch. 3:** switches
are not intrinsically bad; the problem is a case list that will grow in several places.

**Counter-position (notes' caveats):** with sealed or sum types and exhaustive matching, the
compiler flags every match when a case is added, which gives the completeness guarantee without
classes. For a stable set of types with changing operations, matching or a visitor fits better.

**Deciding rule:**
- Which changes more often here, the set of cases or the set of operations? Cases: dispatch
  (polymorphism, a table of functions). Operations: exhaustive matching over a closed type.
- In either design, the same selection must not be hand-repeated without the compiler checking
  completeness.
- One small switch used in one place is not a finding.

## 7. Duplication versus fewer elements

The four rules of simple design (CC ch. 12) rank: runs all tests; no duplication; expresses
intent; fewest classes and methods. The last is a deliberate counterweight: removing duplication
and adding expressiveness can be overdone into many tiny types and methods (an interface for
every class is given as pointless dogma). The book resolves the tension only by ranking. The
notes add (inferred, from general knowledge and not from the text) that later statements of
these rules order intent and duplication differently.

Separately, shape is not knowledge: two blocks that look alike but change for different reasons
can stay apart (inferred in the notes; the 2nd edition's contents list sections on accidental
duplication).

**Deciding rule:** remove duplication when the copies must change together. When resolving
conflicts go top-down: never break tests; prefer removing real duplication to having fewer
elements; prefer a clearer name or one more small function to fewer methods; remove a type or
interface only if it is pure ceremony.

## 8. Exceptions versus error values; try-first

**CC ch. 3:** prefer exceptions to returned error codes; error codes force nested checks and
violate command/query separation; a function that handles errors should do nothing else, with
`try` as its first statement.

**Counter-position (notes' caveats):** languages built around explicit error values (Go's error
returns, Rust's result type, functional languages) use values for expected failures by design,
and checked exceptions were later criticised. The "try first" form is specific to exception
languages. The 2e contents add a "caveat emptor" subsection under this heading (heading only).

**Portable core:** keep the normal path flat; make failure impossible to ignore; do not build one
central error enumeration that everything depends on (per-module error types instead); keep error
plumbing from interleaving deeply with logic.

**Deciding rule:** use the language's and the codebase's error mechanism. The policy question
belongs to `craft-error-handling`.

## 9. Command/query separation

**CC:** a function either changes state or answers, not both. **Accepted violations:** operations
whose point is atomicity (`pop`, `putIfAbsent`, compare-and-set, `iterator.next()`); splitting
them introduces races. **Deciding rule:** separate unless atomicity is required; never return an
ambiguous status from a setter-like command.

## 10. Encodings and prefixes

**CC (ch. 2, N6):** no Hungarian notation, member prefixes, or interface markers. **Limits
(notes' caveats):** the argument assumes static types and a highlighting editor. Unit and kind
suffixes in dynamic languages are useful; encoding semantic kind is defended; some languages
conventionally mark interfaces or private members. The ch. 15 case study records that the code
it cleaned used a member prefix by convention, and removing it immediately caused a local to
shadow a field. **Deciding rule:** follow the language and repository convention; do not encode
what the compiler enforces or what can silently go stale.

## 11. Formatting numbers and styles

CC's figures (files around 200 lines, 500 ceiling; lines to 120) are descriptive, from seven Java
projects. Its precedence-spacing and no-alignment advice can conflict with formatters; its own
listings omit braces on single statements, which many guides forbid. **Deciding rule:** the
formatter and linter decide. See `formatting-and-layout.md`.

## 12. Opportunistic cleanup versus minimal diff

**CC ch. 1 (Boy Scout Rule):** leave each file a little cleaner with every change. **PoSD ch.
16:** make the minimal clean change, not the minimal diff. **Counter-position (notes' caveats):**
both conflict with keeping diffs small and reviewable, and with "do not touch working code"
norms.

**Deciding rule:** small, behaviour-preserving cleanups that the task touches are fine, in a
separate commit where practical. Do not widen a bug fix into a refactor without agreement.
Larger cleanups: propose, with the specific findings. If the surrounding code makes the requested
change awkward, say so; that is a cost the user should see.

## 13. Changing a convention

PoSD ch. 17: do not, unless you have significant new information and the new approach is worth
migrating every old use. Some teams accept gradual migration with deprecation; PoSD's condition is
that every old use be updated. **Deciding rule for an agent:** do not introduce a second
convention on your own initiative. If the user asks for one, point out the migration cost and
offer to migrate the old uses or record the plan.

## 14. Room for growth versus YAGNI

2e ch. 3 restructures a small working example to make room for growth, and anticipates the
objection that this violates "you aren't going to need it". Its answer: the phrase is a question,
"what if you aren't going to need it?", meaning count the cost first; here there was stated
evidence of growth. The same chapter concedes that added structure costs cognitive effort and
probably a small amount of performance, and that for small projects some of its concerns may not
matter.

**Deciding rule:** add structure for change when you can point to evidence of that change (stated
plans, a pattern in the history, the next two additions visibly straining the current shape). No
evidence: keep the simpler form.

## 15. Lesser disputes

| Topic | Positions | Decide by |
|---|---|---|
| Wildcard imports (J1) | CC recommends; mainstream Java practice forbids | Project rules; do not apply by default |
| `Manager`, `Processor`, `Data`, `Info` in names | CC: avoid. Frameworks impose them | Treat as a prompt to look for an unnamed responsibility |
| `Impl` suffix | CC suggests marking the implementation; widely criticised | Name the implementation for what distinguishes it |
| Prefer non-static (G18) | Assumes object polymorphism | Language idiom; free functions are normal in many languages |
| Explanatory variables (G19) | "Hard to overdo" versus noise | Add where an expression's meaning is not evident |
| Single return | Structured-programming rule versus guard clauses | Both CC and current practice accept early returns in small functions |
| Positive conditionals (G29) | The author's own case study reversed its inversion | Preference, not rule |
| Mandated doc comments | CC: noise. Linters and doc tools require them on public symbols | Require on public API; reject name-restating text |
| Declared interface type versus allocated type | PoSD ch. 18: declare what you allocate so readers are not misled. CC G26: a concrete type where an interface will do over-constrains | Local, private state: concrete. Public signatures: the abstraction |
| TODO comments | CC 1e: good. CC 2e contents: listed under bad | Allow when actionable with a condition; follow the repository |
| Comments-first versus code-first | PoSD ch. 15: write interface comments before bodies. CC: write dirty code under test, then clean | Not exclusive: draft the interface and its comment, then iterate the body under test |
| Read/write ratio, 10% typing cost, indentation and bug density | All informal estimates | Do not cite as measurements |

## 16. What the two schools agree on

Useful when a user sets them against each other.

- Code is for readers; the reader's judgement decides what is clear.
- Precise, consistent names; one name per concept.
- No redundant comments; no commented-out code.
- Explain why; document public interfaces.
- Remove duplication.
- Each function does one job.
- Consistency with the codebase outranks personal preference.
- Refactor with tests, in small steps.
- Difficulty naming or describing something is a design signal.
