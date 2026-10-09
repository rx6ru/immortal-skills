# Formatting and layout

Where things go in a file, how code is spaced, and how to stay consistent with a codebase.
Sources: Clean Code ch. 5, the 1st-edition foreword, ch. 17 (G10, G11, G24, G35, G13, G17, G32);
A Philosophy of Software Design (PoSD) ch. 17 and ch. 18.

## 1. Order of authority

1. The language's hard constraints (definition before use, indentation as syntax).
2. The repository's formatter and linter configuration.
3. The repository's visible conventions (how sibling files are ordered and named).
4. The language community's standard style.
5. The rules in this file.

Reason: a formatting gesture is only information if it means the same thing in every file. The
team's style outranks personal preference (Clean Code ch. 5); consistency is almost always worth
more than a locally better idea (PoSD ch. 17).

Formatting is communication: functionality changes, but the readability habits set early affect
every later change. Keep the rules simple, apply them uniformly, and automate them (ch. 5).

## 2. Consistency

Consistency means similar things are done in similar ways and dissimilar things differently. It
gives leverage (learn once, apply everywhere) and safety (what looks familiar really is the same)
(PoSD ch. 17). It covers names, coding style, interfaces with several implementations, design
patterns, and invariants.

**Before writing in an existing codebase:**
1. Find the nearest analogue: same layer, same kind of task.
2. Note its structure: declaration order, public-before-private or not, naming case, error idiom,
   comment style, test layout.
3. If it looks like a convention, follow it. When making any decision, ask whether a similar
   decision has been made elsewhere and copy that approach.

**Do not change an existing convention** unless both hold (PoSD ch. 17):
1. you have significant new information that was not available when the convention was set, and
2. the new approach is so much better that it is worth updating every old use, leaving no trace
   of the old way.

A "better idea" alone is not enough. Introducing a second way of doing the same thing without
migrating the first leaves readers unable to trust appearances. Some teams accept gradual
migration with deprecation; PoSD allows change only under the two conditions.

**Establishing conventions:** write them down where people will see them; enforce the low-level
ones with tools that block violations (PoSD's example is a pre-commit script that rejects files
with the wrong line endings and also taught newcomers the rule); reinforce the rest in review.
Clean Code G24 adds that the code itself can serve as the example. Unwritten conventions will not
be followed by newcomers.

**Do not over-apply:** forcing dissimilar things into one name or one pattern destroys the
guarantee that "if it looks like an x, it is an x" (PoSD ch. 17).

For agents: a repository's stated conventions (contributor guide, agent instructions file, linter
config) outrank preferences from this skill (inferred in the notes).

## 3. Vertical layout

### 3.1 File as a newspaper article
The name tells you whether you are in the right place. The top gives the high-level concepts;
detail increases downward; the lowest-level functions are last. Many small articles are easier
than one long story (Clean Code ch. 5).

### 3.2 Openness and density
- A blank line separates distinct thoughts: imports, each function, each step within a function.
- Lines that are tightly related stay adjacent, with no blank lines or filler comments between
  them. Two field declarations separated by pointless doc comments lose their association.
- Check: unfocus your eyes; the code should fall into visible paragraphs.
- Inside a longer function, a blank line before each major block with a summary comment as the
  first line after it makes the structure scannable (PoSD ch. 18).

### 3.3 Distance (G10)
Concepts that are closely related are kept close, so the reader does not chase definitions up and
down the file.

| Item | Placement |
|---|---|
| Local variable | As close to first use as possible; in a short function, at the top |
| Loop control variable | In the loop statement |
| Instance fields | One well-known place; the Java convention is the top of the class. Follow the language idiom |
| Function called by another in the same file | Close to the caller, below it where the language allows |
| Sibling variants (overloads, functions sharing a naming scheme, variations of one operation) | Together, even if they do not call each other |
| Constant or default known at a high level | At the high level, passed down as an argument (G35), not buried in a low-level function |

The measure of acceptable distance is how much each item is needed to understand the other.

### 3.4 Ordering
Call dependencies point downward: the caller above the callee, the important concepts first with
the least detail, low-level detail last, so that skimming the first few functions gives the gist.
This is the stepdown order referred to in `functions.md`. The ch. 15 case study ends with analysis
functions first and synthesis functions last, each definition after its first use.

Where a new function goes: directly below its first caller; variants beside their siblings.

### 3.5 File size
A survey of seven Java projects in Clean Code ch. 5 found that substantial systems were built
from files typically around 200 lines with an upper bound near 500; the book calls this desirable,
not a hard rule. It is a descriptive observation from a small, dated sample. A file that is too
long is a module-size question (`craft-module-design`), not a formatting one.

## 4. Horizontal layout

- Keep lines short. The source's data shows programmers prefer short lines; it calls 80 somewhat
  arbitrary, accepts 100 to 120, and regards more as careless. Use the limit your formatter or
  community standard sets.
- Spacing shows association: spaces around assignment; none between a function name and its
  opening parenthesis; a space after each comma. Write `for (int pass = 1; pass >= 0 && !empty;
  pass--)`, not the same with all spaces removed (PoSD ch. 18).
- The source also uses spacing to show operator precedence (`b*b - 4*a*c`) and notes that most
  formatters remove it. Where a formatter is in force, accept its output.
- Do not align declarations or assignments in columns: alignment draws the eye to the wrong
  thing, and formatters remove it. A list long enough to want alignment is the problem. (Some
  style guides and formatters do align; follow the formatter.)
- Indentation mirrors scope. Do not collapse short blocks onto one line. Avoid empty loop bodies;
  if unavoidable, make the empty body visible on its own line with braces.
- Doc-comment parameters each start on their own line with wrapped text indented, so the number
  of parameters is visible at a glance (PoSD ch. 18).
- Single-statement bodies without braces appear in the source's own listings; many current
  guides require braces. Follow the repository; where free to choose, braces are the safer
  default for multi-line or consequential bodies (from the notes' caveats).

## 5. Placing code and data

These heuristics are about where a thing lives; they sit between layout and module design.

- **Least surprise** (G17): put code where a reader would look for it, judged by names. If a
  function named for totalling lives in the report module, readers expect the total to be
  computed there. If performance forces the work elsewhere, rename to say so.
- **No artificial coupling** (G13): do not park a general-purpose enumeration, constant or
  function inside a specific type because it was convenient; everything that needs it must then
  know that type.
- **Do not be arbitrary** (G32): have a reason for each structure and let the structure show it.
  Structure that looks arbitrary invites others to change it.
- **Configurable data high** (G35): defaults and configuration constants live at the top level
  and are passed down; a default buried in low-level code (`if port == 0: use 80`) is misplaced.
- **One language per file where possible** (G1): minimise the number and extent of extra
  languages embedded in a source file.
- **A place for everything** (foreword, "systematise"): code should be where you expect to find
  it; if it is not, move it.

## 6. Things that make code less obvious

From PoSD ch. 18. Each hides information the reader needs; either avoid it or compensate.

| Construct | Why it obscures | Compensate |
|---|---|---|
| Event-driven code, callbacks, handlers registered at run time | The call site does not show which function runs | Each handler's interface comment says when it is invoked and on which thread |
| Generic containers as records (pair, tuple, string-keyed map) | Elements have generic names (`getKey`, `first`) that hide meaning | Define a small named record or struct with meaningful field names |
| Declared type differs from allocated type | The real type affects performance and thread-safety, and the reader is misled | Declare the type that matches what is allocated, where callers do not need the generality |
| Code that violates reader expectations (an entry point that returns while threads it started keep running) | Readers assume the conventional behaviour | Follow the convention, or document the behaviour at the point of surprise and in the interface comment |

General rule from the same chapter: design for ease of reading, not ease of writing. A few extra
minutes for the writer are repaid across every later reader.

Adaptation noted in the source notes (inferred): named tuples, records and data classes make the
"define a small type" advice cheap in most current languages. Clear multiple named returns are a
partial exception. Dependency-injection containers, decorators, reflection-heavy frameworks and
implicit global state create the same kind of hidden control flow and need the same compensation.
Note the tension with Clean Code G26, which calls declaring a concrete list type where the
interface would do over-constraining; decide by whether readers of this code need to know the
concrete behaviour.

## 7. Warning signs

- Files of many hundreds of lines; fields scattered through a class; helpers far above their
  callers or in no visible order.
- Walls of code with no blank lines, or blank lines inside a tightly related group; filler
  comments between related fields.
- Very long lines; whole functions on one line; ragged indentation or mixed tabs and spaces.
- Different brace, naming or indent styles between files or authors.
- Long aligned declaration blocks.
- The same thing done two ways in one repository (two fetch idioms, two error shapes).
- A diff polluted by whitespace or line-ending changes.

## 8. Dated or contested points

From the notes' caveats.

- The file-length and line-length figures come from seven Java projects of the 2000s. Current
  defaults differ by ecosystem and are set by formatters; use the project's.
- Brace style, indent width, tabs versus spaces and alignment are arbitrary; what transfers is
  agreement and automation. Opinionated formatters have largely settled what the book's "team
  rules" section negotiates by hand.
- Caller-above-callee reverses the order some languages require or some communities standardise.
  Keep the principle (high level first where possible) inside the language's rules.
- "Fields at the top" is a Java convention.
- The foreword's report that consistent indentation correlated with low bug density is flagged by
  its own author as informal; do not cite it as evidence.

## 9. Verify

- Run the formatter and linter; after formatting, the diff on your files is empty (inferred in
  the notes, consistent with the book's call for an automated tool). They run in CI or
  pre-commit and block violations.
- Skim top to bottom: entry points first, each helper after its first caller, detail last.
- Compare the new or changed file with a sibling: same declaration order, naming scheme and
  error idiom?
- Search for the same concept implemented two ways; if you introduced a second way, is migration
  of all old uses planned?
- Search for pairs, tuples and string-keyed maps used as records, and for declarations whose
  type differs from what is allocated.
- Each handler or callback has a comment saying when and where it runs; side effects that outlive
  a constructor or entry point are documented.
- The diff contains no unrelated whitespace or reformatting changes.
