# Comments

What to comment, what not to, how to write each kind, and how to keep comments true. Sources:
Clean Code ch. 4 and ch. 17 (C1–C5); A Philosophy of Software Design (PoSD) ch. 12, 13, 15, 18,
and ch. 16 for maintenance.

The two books start from opposite premises. Clean Code treats a comment as compensation for a
failure to express intent in code; PoSD treats comments as the only way to state an abstraction.
The dispute and how to decide are in `contested-rules.md`. This file gives the working rules that
survive both, marking which book each comes from.

## Contents

1. What both books agree on
2. Decision procedure for one comment
3. Kinds of comment and what each contains
4. Writing better comments: precision and intuition
5. Bad comments and their fixes
6. Comments-first procedure for new code
7. Keeping comments true
8. Language and tooling notes
9. Verify

## 1. What both books agree on

- A comment that restates the code is worthless and should be deleted (Clean Code C3; PoSD ch. 13
  "comment repeats code").
- A comment does not make up for unclear code. If a rename, an extraction or a named constant can
  carry the information, do that (Clean Code ch. 4). PoSD agrees that good names reduce the need.
- "Why" is worth writing: intent, rationale, constraints, warnings of consequences.
- Public interfaces get real documentation (Clean Code ch. 4 lists doc comments on public APIs
  among the good comments; for PoSD it is the main case).
- An inaccurate comment is worse than none; distance from the code is what makes comments rot.
- Commented-out code, change journals and bylines are removed; version control holds them.

Where they differ is the default for everything in between: internal functions, fields, and how
much a name can be trusted to carry.

## 2. Decision procedure for one comment

1. **Can code carry it?** Rename, extract a predicate or variable, introduce a named constant.

   ```python
   # before
   # eligible for full benefits if hourly and over 65
   if emp.flags & HOURLY and emp.age > 65: ...
   # after
   if emp.is_eligible_for_full_benefits(): ...
   ```

2. **Stranger test** (PoSD ch. 13): could someone who has never seen this code write the comment
   just by looking at the code next to it? If yes, it adds nothing.
3. **Different-words test** (PoSD ch. 13): does it reuse the words of the name it documents
   ("the horizontal padding" on `horizontalPadding`)? Rewrite with different words that add
   meaning, or delete.
4. **Does it carry what code cannot?** See the content lists in section 3. Write it, short, next
   to the code it describes.
5. **Is it about another place?** A default set elsewhere, a caller's behaviour, another module's
   decision: move it to the owner or point to it.
6. **Is it history, authorship, a banner, a closing-brace tag, disabled code?** Do not write it.
7. **Is it a TODO?** Acceptable when it names a job that cannot be done now and is actionable;
   not as cover for leaving bad code. (The 1st edition lists TODO among good comments; the 2nd
   edition's table of contents lists it under bad comments. The reasoning is not in the excerpt.)

"Obvious" is judged from the position of someone reading the code for the first time, not yours.
If a reviewer says something is not obvious, it is not; fix the code or the comment instead of
arguing (PoSD ch. 13, ch. 18).

## 3. Kinds of comment and what each contains

PoSD ch. 13 defines four categories. The contents lists below are from PoSD ch. 13 unless marked.

### 3.1 Interface comment (before a type, function or method)

Purpose: a developer can use the thing without reading its body. If users must read the code,
there is no abstraction (PoSD ch. 12).

**Type or class:** the abstraction it provides; what one instance represents; limitations (for
example, single-threaded use). Optionally a short usage sketch for a type whose usage pattern is
not evident. No implementation detail, no per-method specifics.

**Function or method:**
- one or two sentences on behaviour as callers perceive it;
- each argument and the return value, precisely: units, valid ranges, inclusive or exclusive
  bounds, nullability and what null means, dependencies between arguments;
- side effects: anything that affects the system's future behaviour and is not part of the result;
- errors or exceptions that can come out;
- preconditions, including required call order (keep them few, document the rest);
- thread-safety where relevant (in the notes' checklist).

What to leave out: how it works. Internal data structures, names of internal helpers or remote
calls, private configuration, recovery mechanics the caller cannot observe.

Example of the line between the two, from PoSD ch. 13's range-query class: the comparison rule
used for keys belongs in the interface comment (callers depend on it); the wire format to servers
and the server-side index structure do not; whether requests are issued concurrently may be worth
a high-level mention because callers care about performance; crash handling is omitted if crashes
are invisible to callers (if they surface, say how they appear, not how recovery works).

**Red flag: implementation documentation contaminates the interface.** The interface comment
describes details not needed to use the thing. Move them into the body as implementation comments
and rewrite the interface comment in terms of observable behaviour.

**Red flag: the interface comment has to describe the implementation to be complete.** Then the
function is shallow; this is a design finding (see section 6 and `craft-module-design`).

```ts
/**
 * Copies bytes from this buffer into `dest`.
 *
 * @param offset index in this buffer of the first byte to copy
 * @param length number of bytes requested
 * @param dest   must have room for `length` bytes
 * @returns the number of bytes actually copied; fewer than `length` if the
 *          range runs past the end of the buffer, 0 if there is no overlap
 */
copy(offset: number, length: number, dest: Uint8Array): number
```

Nothing here says how the buffer is scanned.

### 3.2 Data-member comment (beside a field, constant or static)

Name and type are imprecise; the comment adds precision:
- units;
- whether boundaries are inclusive or exclusive;
- what null or absence means;
- who frees or closes a resource;
- invariants ("always contains at least one entry").

Write nouns, not verbs: say what the variable represents, not when code sets or clears it.
"True means a heartbeat has been received since the election timer was last reset" replaces a
list of the places it is toggled; readers can infer those.

Be specific. "Current offset in the response buffer" (current in what sense?) became "position in
this buffer of the first object that has not been returned to the client". For a map of line
lengths to counts, the improved comment states what the key is, in which unit, what the value is,
and that a missing key means no line of that length, and the variable was renamed to match.

"The code" in "not obvious from the code" means the adjacent declaration, not every use across
the application.

### 3.3 Implementation comment (inside a body)

Most short functions need none. Where needed, the purpose is what and why, not how.

- **Block summary** in a long function: one comment before each major block, abstract:
  "Phase 1: scan active requests to see whether any have completed."
- **Loop summary** for a long or intricate loop: what each iteration does.
- **Higher-level intent** in place of narrating conditions: "Try to append the current key to an
  existing request to the same server that has not been sent yet." From this a reader can infer
  most of the conditions and judge whether the code is right.
- **How we get here**: the circumstances under which this code runs, especially an unusual path.
- **Why** for tricky code: a workaround, a bug fix with non-obvious code. Refer to the tracker
  entry instead of copying its details.
- **Warning of consequences** (Clean Code ch. 4): "not thread safe, create one per use" stops a
  later "optimisation" into shared state.
- **Amplification** (Clean Code ch. 4): stress that something innocuous-looking matters ("the trim
  matters: leading spaces would make this parse as a list").
- **Clarification** of an obscure value from a library you cannot change (Clean Code ch. 4); the
  clarification can itself be wrong and is hard to check, so look for another way first.
- **Local variables**: comment only important ones used over a long span.

Clean Code would first try to turn each block summary into a function name. Use the split and
keep tests in `functions.md`: if the block passes them, extract it and the comment becomes the
name; if not, the block summary is the right tool.

### 3.4 Cross-module comment

Design decisions that span modules (a protocol affecting sender and receiver; a rule that adding
an enumeration value requires edits in several other files) cause many bugs. The difficulty is
finding a place developers will see.

- Put it at the obvious central place: for "adding a value requires these other edits", at the
  end of the enumeration where new values are added.
- If there is no central place: one notes file with labelled sections, and a one-line pointer at
  each relevant code site ("See 'Zombies' in designNotes"). PoSD describes this as an experiment
  and notes the cost: far from the code, so it may go stale. In today's repositories the same role
  is often played by an architecture decision record (adaptation, inferred in the notes).
- Do not duplicate the explanation at each site.

### 3.5 Clean Code's permitted list, mapped

| Clean Code ch. 4 "good comment" | Where it fits above |
|---|---|
| Legal (short; point to a standard licence) | file header; follow the repository |
| Informative (e.g. the format a regex matches) | implementation; prefer a rename or a dedicated type if possible |
| Explanation of intent | implementation "why" — the strongest category |
| Clarification | implementation, with care |
| Warning of consequences | implementation or interface |
| TODO | see section 2, item 7 |
| Amplification | implementation |
| Doc comments on public APIs | interface |

## 4. Writing better comments: precision and intuition

A useful comment is at a different level of detail from the code beside it (PoSD ch. 13):

- **Lower, more precise**: mostly on declarations (units, bounds, null, ownership, invariants).
- **Higher, more abstract**: what this code is trying to do, the simplest statement that explains
  everything in it, the most important thing about it. Harder to write; it is the same skill as
  designing an abstraction.

A comment at the same level as the code repeats it.

If you write a comment, write it well: careful wording, correct grammar, brief (Clean Code C4). A
comment that sends the reader to another module to work out what it means has failed (ch. 4
"mumbling").

## 5. Bad comments and their fixes

From Clean Code ch. 4 unless marked.

| Kind | Recognition | Fix |
|---|---|---|
| Redundant (C3) | Says what the adjacent code says; takes longer to read than the code; a doc block that echoes the signature | Delete; make the code clear |
| Name-echo (PoSD) | Uses the same words as the name | Rewrite with added meaning or delete |
| Misleading | Not precise enough to be true (a "returns when X" that omits the timeout path) | Make exact or delete |
| Obsolete (C2) | Drifted from the code it described | Update or delete now |
| Mumbling | Written because it felt required; meaning needs a hunt elsewhere | Write it properly or not at all |
| Mandated noise | A rule that every declaration has a doc block, producing `@param title The title` | Keep requirements for public APIs; reject name-restating text |
| Noise | `Default constructor.`, `The day of the month.`; venting | Delete; if venting, fix the structure |
| Copy-paste doc errors | Doc text that describes a different member | Delete; nobody was reading it |
| Journal / change log (C1) | History at the top of a file | Delete; version control |
| Attribution / byline (C1) | "Added by ..." | Delete; version control |
| Commented-out code (C5) | Disabled code nobody dares remove; it rots as names and conventions change | Delete; version control keeps it |
| Position marker / banner | `// ----- Actions -----` | Rarely; usually delete or split the file |
| Closing-brace comment | `} // while` | Shorten the function |
| Comment where a name would do | A comment above a long expression explaining it | Named variable or function |
| Nonlocal information | A comment on a setter stating a system default it does not control | Put it beside the thing it describes |
| Too much information | A pasted specification excerpt | Keep the pointer only |
| Unobvious connection | Comment and code do not visibly correspond (which number is the "200 bytes for header"?) | Named constants; make the link visible |
| Function header on a small one-job function | A header block above a function whose name already says it | A good name is better |
| Formal docs on non-public code | Full doc blocks on internal classes | Keep them plain and minimal (public API docs are the case that earns full detail) |
| Markup in comments | HTML making the source hard to read | Let the doc tool add markup (dated; Markdown doc comments are now common) |
| Interface contamination (PoSD) | Interface comment names internals | Move detail into the body |
| Vague data comment (PoSD) | "current offset", "contains all widths" | State what it represents, units, bounds, null meaning |
| Verb comment on a variable (PoSD) | Lists when the variable is set | Describe what it represents |

Also never leave narration of generated code ("loop over the items"), which the Clean Code notes
single out for coding agents.

An empty `catch` with a reassuring comment is a red flag for both comment quality and error
handling; see `craft-error-handling`.

## 6. Comments-first procedure for new code

From PoSD ch. 15. Purpose: better comments, and a design check before effort is spent on bodies.

1. For a new type, write its interface comment first.
2. Write signatures and interface comments for the most important public functions, bodies empty.
3. Read the comments critically and iterate until the structure feels right.
4. Write declarations and comments for the most important fields.
5. Fill in bodies, adding implementation comments as needed.
6. For each helper or field discovered while coding, write its comment before its body or with
   its declaration.

When the code is done, the documentation is done; there is no backlog.

**Design signals to act on at step 3:**

| Signal | Meaning | Action |
|---|---|---|
| Hard to describe: no comment is both simple and complete | The abstraction is probably wrong, or a variable has mixed purposes | Simplify the abstraction, split the variable, move responsibilities; then describe again |
| The interface comment must cover all the major features of the implementation | The function is shallow | Merge it into its caller or deepen it |
| Long comment needed for a variable | Wrong decomposition | Reconsider the data |
| Comment lists many special cases, hedges | Interface complexity | Reduce special cases |

The signal is reliable only if the comment itself is complete and clear; a cryptic comment says
nothing about depth.

Cost: PoSD estimates that typing code and comments together is a small fraction of development
time (it uses about 10% as a rough upper bound, an argument and not a measurement), so writing
comments early costs little and may save rewrites by stabilising interfaces before coding. With an
exploratory spike the comments may need rewriting (inferred in the notes).

Why delayed comments are worse: they tend never to be written; when written later, the design
reasoning has faded and the author is looking at the code, so the comments repeat it.

## 7. Keeping comments true

Clean Code's central objection is that comments rot because code moves and comments do not
follow. PoSD's answer is locality and review, not omission (ch. 12, ch. 16):

- Keep each comment next to the code it describes; push implementation comments down to the
  narrowest scope that contains what they refer to.
- The farther a comment is from its code, the more abstract it should be, so that small code
  changes do not falsify it. Higher-level comments change only when behaviour changes.
- Say a thing once. Do not re-document a callee at the call site; do not copy a cross-module rule
  to every site. A stale pointer is self-evident; a stale duplicate is not.
- Put rationale in the code, not only in the commit message; the next reader of the code will not
  read the log.
- Before committing, scan the whole diff and check that every change is reflected in the comments.
  The same scan catches leftover debug code and unresolved TODOs.
- Reviewers check comments along with code.

## 8. Language and tooling notes

Adaptation, from the notes' caveats and generalisation sections.

- Doc comments are part of the product where tools consume them: Python docstrings, Go doc
  comments, Rust `///`, TSDoc, generated API references, editor hover. Use the documentation
  tool's conventions; if the project has none, borrow from a similar project.
- Many linters require docs on public symbols. Meet the requirement with content from section
  3.1, not with name-restating filler.
- For HTTP APIs the specification's descriptions carry the informal part of the contract:
  idempotency, ordering, units, error semantics (inferred in the notes).
- In C and C++ the principle for where an interface comment lives is proximity to the code the
  developer edits; PoSD ch. 16 argues for the implementation file on those grounds. Follow the
  project's convention.
- Comments in tests: descriptive test names and assertion messages do the job better than a
  clarifying comment beside an assertion.
- Region or folding markers are tool-supported in some editors; in a long file they are still a
  size signal.
- For event handlers and callbacks, the interface comment says when the handler is invoked and
  on which thread, because the call site cannot show it (PoSD ch. 18). For a constructor or
  entry point whose effects outlive the call (threads started, listeners registered), say so.

## 9. Verify

- **Deletion test** (Clean Code): remove each comment mentally. Does the reader lose information
  not derivable from names, types and tests? If not, delete.
- **Stranger test** (PoSD): cover the comment and read only the adjacent code; if you could have
  guessed the comment, it is redundant.
- **Truth test**: check each surviving comment against behaviour by reading the code path,
  especially "returns when ..." and stated defaults.
- **Interface audit**: for each public declaration, can it be called correctly from comment and
  signature alone: units, bounds, null, side effects, errors, preconditions? Does any phrase name
  private fields, internal types or algorithm steps?
- **Depth check**: is any interface comment as long and involved as the implementation?
- **Higher-level comments**: can a reader use the comment to judge whether the code is correct?
- **Cross-module**: when X changes, does a comment at X say what else must change? Does every
  pointer resolve (search for the referenced tag)?
- **Diff scan**: new comment lines that paraphrase the next line; commented-out code; doc
  parameters whose text is only the parameter name; TODO with no condition (inferred in the
  notes); comments falsified by the change.
- **History check** (inferred in the notes): comments arrive in the same commit as the code, not
  in a later "add docs" commit.
