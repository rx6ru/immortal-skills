# Functions

How to write, size, split, merge and review a function. Sources: Clean Code ch. 3, ch. 12, ch. 17
(F1–F4, G5, G15, G19, G23, G27–G31, G33, G34); Clean Code 2e ch. 3 (excerpt); A Philosophy of
Software Design (PoSD) ch. 9 for the opposing view on splitting (main treatment in
`craft-module-design`), ch. 18.

Error-handling policy (exceptions, results, null) is in `craft-error-handling`; this file only
covers its effect on function shape.

## Contents

1. What a good function is
2. Abstraction level and "one thing"
3. Size, and the dispute about it
4. Split test, keep test, join test
5. Arguments
6. Side effects, output arguments, command/query
7. Conditionals and switches
8. Duplication
9. Order dependence and boundaries
10. Structured-programming rules
11. How such functions get written
12. Warning signs
13. Verify

## 1. What a good function is

Points the sources share:

- A reader can tell what it does from its name and signature and is not surprised by the body
  ("each routine turns out to be pretty much what you expected", Clean Code ch. 1).
- It does one job and does it completely (Clean Code ch. 3; PoSD ch. 9 uses the same words with
  a different meaning of "one": one clean abstraction, not a small line count).
- Its statements sit at one level of abstraction.
- It has no undeclared effects.
- It asks the caller to track little: few parameters, no mode switches, no hidden ordering.

Clean Code ch. 3 frames a program as a story told in a layered vocabulary the programmer builds:
functions are the verbs, types the nouns. The aim is the layered readable language; short functions
are a means.

## 2. Abstraction level and "one thing"

**Operational definition** (Clean Code ch. 3, G34): a function does one thing if all its steps are
one level of abstraction below the operation its name states. Describe it as a "to" paragraph:

> To render the page with setups and teardowns, we check whether it is a test page and, if so,
> include setups and teardowns; in either case we render the HTML.

If the paragraph needs steps at different levels ("...then we append a newline to the buffer"),
the levels are mixed.

**Why mixed levels hurt:** the reader cannot tell essential concept from detail, and once detail
is mixed in, more accretes.

**Recognising levels:** in one function, a domain operation (`page.getHtml()`), an intermediate
helper (`PathParser.render(path)`) and a raw primitive operation (`.append("\n")`) are three
levels.

**Iterate:** splitting along one line of abstraction often reveals another that was hidden
(G34's worked example: a renderer that mixed "a rule has a size" with HTML tag syntax; after
moving tag construction out, the size formatting turned out to be a further level, and a field
was renamed to say what it really held).

**Sections are a symptom** (G30): a function with labelled phases ("declarations",
"initialisation", "sieve") or blank-line-separated phases is doing several things. 2e ch. 3 puts
it as a working heuristic (inferred in the notes): a comment that labels a block of statements is
a request to extract a function with that name.

```ts
// before: three levels in one function
function previousWeekday(target: Weekday, from: Date): Date {
  // check arguments
  if (target < 0 || target > 6) throw new RangeError("weekday");
  // find the date
  let back = from.getDay() - target;
  if (back <= 0) back += 7;
  const result = new Date(from);
  result.setDate(from.getDate() - back); // calendar days; subtracting 86_400_000 ms is wrong across DST
  return result;
}

// after: labels became names; the body is one level
function previousWeekday(target: Weekday, from: Date): Date {
  checkWeekday(target);
  return subtractDays(daysBefore(target, from), from);
}
```

**Stepdown order:** arrange the file so each function is followed by those one level down, in
call order, so the file reads as a cascade of "to" paragraphs (see `formatting-and-layout.md`).

## 3. Size, and the dispute about it

**Clean Code position (ch. 3; 2e ch. 3):** small, then smaller; hardly ever 20 lines; "most
should be just a handful of lines"; blocks inside `if`/`else`/`while` are one line, usually a
call; indent level one or two. Reasons given: a small function can have a descriptive name, keeps
concerns apart, and documents its callers through its name. The author states there is no
research behind the size claim; it rests on long personal practice. The 2e chapter says its
principles are guidelines applied in context, and that added structure has a cognitive price.

**PoSD position (ch. 9, ch. 12):** length alone is rarely a reason to split. Each split adds an
interface and separates related code. A long function with a simple signature that reads block by
block is fine, even at hundreds of lines; such a function is deep. Designing for "read the code
instead of comments" pushes toward many shallow functions whose behaviour the reader then needs
anyway.

**Where they agree:** extract a subtask that is cleanly separable and has a meaningful name;
remove duplication; one job per function; one level of abstraction; the reader's ease decides.

**Deciding rule:** use the split, keep and join tests below. Do not cite a line count as the
reason in either direction. The fuller argument is in `contested-rules.md`.

## 4. Split test, keep test, join test

### Split when one of these holds

| Signal | Source |
|---|---|
| Statements at mixed levels of abstraction | Clean Code ch. 3, G34 |
| Sections, banners or labelling comments inside the body | ch. 3, G30, 2e ch. 3 |
| A block duplicated, or repeated with only literals changed | ch. 3, ch. 12, G5 |
| A compound condition whose intent is unreadable | G28 |
| A mode flag or selector argument; a name needing "and"/"or" | F3, G15 |
| The function does unrelated things and most callers want only one | PoSD ch. 9 |
| A cleanly separable, fairly general subtask exists | PoSD ch. 9 |
| Nesting deeper than about two levels | Clean Code ch. 3 |

### Keep the extracted piece only if

1. Its name is more than a restatement of its implementation (G34 test: if the only available
   name is something like `includeIfTestPage`, you are done splitting).
2. A reader of the child needs to know nothing about the parent.
3. A reader of the parent does not need the child's implementation (PoSD ch. 9).
4. It does not need many parameters, or newly promoted fields, purely to carry the parent's local
   state (inferred in the PoSD notes as a suspect sign for single-use helpers).

If you must flip between parent and child to understand either, PoSD calls them conjoined: rejoin,
or cut along a boundary where the child stands alone.

### Join two functions when it

- replaces two shallow functions with one deeper one;
- removes duplication;
- removes a dependency or an intermediate data structure between them;
- puts knowledge in one place;
- makes the interface simpler (PoSD ch. 9).

### Worked contrast

PoSD ch. 9 gives a second case against over-splitting: a logging class whose methods
(`logRpcOpenError`, `logRpcSendError`, ...) were one-line wrappers, each called from exactly one
catch block. Readers flipped between the call site and the wrapper to check that the right data
was logged. The fix was to log at the point where the error is detected. A single-use wrapper with
a long doc comment and no reuse fails the keep test.

The source's own G30 example splits a short `pay()` loop into `pay()` (loops),
`payIfNecessary(e)` (checks payday) and `calculateAndDeliverPay(e)`. Under the Clean Code view
each has one job. Under the PoSD view the three are understandable only together and each adds an
interface, so the original loop was fine. Apply the keep test: does `payIfNecessary` say more than
its two lines do? Is anything reused? If not, leave the loop and at most extract the condition
into a named predicate. If payday rules or delivery are expected to grow, the split gives each a
home; 2e ch. 3 justifies such room for growth by evidence that growth is coming.

## 5. Arguments

**Ladder** (Clean Code ch. 3, F1): none is easiest, then one, then two; three is to be avoided;
more needs special justification.

Reasons: each argument is something the reader must interpret, often at a lower level than the
function's name; test combinations multiply; ordering mistakes happen.

**Forms of a one-argument function:** a question about the argument (`fileExists(name)`), a
transformation that returns the result (`open(name)`), or an event that changes state and returns
nothing (make the event nature evident in the name). Avoid one-argument functions that fit none.
A transformation returns its result instead of writing into its argument.

**Two arguments:** fine when they are ordered parts of one value (`Point(x, y)`). Otherwise the
reader must learn which is which (`assertEquals(expected, actual)` is regularly swapped).

**Reducing arguments. Ask in order:**
1. Do some travel together? Group them in an argument object (`makeCircle(center, radius)` instead
   of `(x, y, radius)`). A group that travels together deserves a name.
2. Is one the subject? Make the function a method on it.
3. Is one a long-lived collaborator? Make it a field of an enclosing type.
4. Are some of them modes? Split the function.

Variadic arguments treated identically count as one list argument.

**Flag and selector arguments** (F3, G15): a boolean, enum or code used only to choose behaviour
says the function does several things, and the call site (`render(true)`,
`calculateWeeklyPay(false)`) is unreadable. Split into named functions, with a shared private
helper for the common part.

**Adjustments (from the notes' caveats, as adaptation):**
- Named or keyword arguments, defaults, builders and options objects remove the ordering problem
  the ladder relies on; use them where the language has them. The 2e table of contents adds
  "keyword arguments" and "more than three?" sections under function arguments (headings only).
- A boolean that is genuinely data (`setEnabled(true)`) is fine; a mode can also be an enum or a
  named argument (`render(mode=SUITE)`) where splitting would duplicate.
- Constructors that receive collaborators by dependency injection may legitimately take several.

## 6. Side effects, output arguments, command/query

- **No undeclared side effects** (Clean Code ch. 3, N7). A function that promises one thing and
  does another creates order dependencies. Example shape: a password check that also initialises
  the session, so a caller who only wants to validate destroys an existing session. Remove the
  effect or put it in the name (accepting that the name then admits two jobs). "No side effects"
  cannot be literal for commands; read it as "none that the name and documentation do not state".
- **Output arguments** (F2): readers expect arguments to be inputs. `appendFooter(report)` leaves
  open whether it appends the report or appends to it. Prefer returning a value or changing the
  state of the object the method belongs to (`report.appendFooter()`). In languages where output
  parameters or mutable borrows are idiomatic for buffer reuse or multiple results, the rule
  narrows to: no surprising ones.
- **Command/query separation**: a function changes state or answers a question, not both.
  `if (set("username", "bob"))` is ambiguous between "was set" and "set succeeded". Query first,
  then command. Accepted exceptions where atomicity matters: `pop`, `putIfAbsent`,
  compare-and-set, `iterator.next()`; splitting those introduces races.
- **Error returns and shape**: status codes returned from commands push callers into nested
  checks; keep the normal path flat and make failure hard to ignore. A function that handles
  errors should do only that: put the real work in its own function and keep the handler thin.
  A central error-code enumeration that everything imports becomes a dependency magnet, so people
  reuse old codes instead of adding new ones. Which mechanism to use is `craft-error-handling`.

## 7. Conditionals and switches

- **Encapsulate conditionals** (G28): `if (shouldBeDeleted(timer))` over
  `if (timer.hasExpired() && !timer.isRecurrent())`.
- **Prefer positive conditionals** (G29): `if (buffer.shouldCompact())` over a doubled negative.
  The ch. 15 case study ended up defining the positive predicate in terms of the negative one
  after all; treat this as a preference.
- **Type switches** (Clean Code ch. 3, G23, G27): a switch on a type code is large, grows with
  each type, and tends to be repeated in every operation that varies by type. The source's rule:
  at most one switch per kind of selection, used to create polymorphic objects, hidden from the
  rest of the system. Abstract methods are preferred to a naming convention plus switches because
  the compiler forces every variant to implement every operation.
- **Limits** (stated in the source and its caveats): the book's own ch. 6 says a switch is the
  right tool where new operations are added more often than new types; G23 calls that case rare.
  2e ch. 3 says switches are not intrinsically bad; the concern is a case list that will grow in
  several places. In languages with closed sum types and exhaustive matching, the compiler gives
  the same completeness guarantee without classes. The portable core: do not repeat the same
  type-switch in several places, and make additions to the set of cases compiler-checked.

```python
# one creating switch; the rest dispatches
def make_employee(rec):
    return {"hourly": Hourly, "salaried": Salaried}[rec.kind](rec)

make_employee(rec).pay()
```

## 8. Duplication

Ranked by the sources as among the most important rules (G5; second of the four simple-design
rules, Clean Code ch. 12). Every duplication is a missed abstraction, and each copy is another
place to change and another chance to miss one.

Forms and remedies:

| Form | Remedy |
|---|---|
| Identical lines | Extract a function |
| Similar lines | Make them textually identical first, then extract |
| Same switch or if-chain on the same condition in several places | Polymorphism or one exhaustive match |
| Same algorithm skeleton with one varying step | Template method, strategy, or pass a function |
| Duplicated implementation (two members tracking the same fact, e.g. an `isEmpty` flag beside a count) | Define one in terms of the other |

Even three duplicated lines are worth removing; extracting small commonality often shows that the
new function belongs in another type, where others can reuse it (ch. 12).

PoSD ch. 9 sets a limit on extraction as the remedy: it pays when the repeated snippet is long and
the new function's signature is simple. For one or two lines, or a snippet that reads and writes
many locals (so the helper needs a long parameter list), extraction gains little. The alternative
is to restructure control flow so the snippet runs in one place (for example one log or cleanup
statement at the end, reached from every branch; `finally`, `defer` or a context manager give the
same single copy; the book's own example uses `goto`).

Limit: remove duplication of knowledge or of a reason to change, not of shape. Two blocks that
look alike but change for different reasons can stay separate (inferred in the ch. 12 notes; the
2e table of contents has sections titled "accidental versus essential duplication" and
"accidental duplication", headings only).

## 9. Order dependence and boundaries

- **Hidden temporal coupling** (G31): calls that must happen in order but whose signatures do not
  show it. Make each step return what the next needs, so out-of-order calls are not reasonably
  possible. The added syntax is accepted because it shows real complexity.
- The ch. 15 case study refines this: adding a parameter only to force order looked arbitrary
  (G32), since nothing told the next programmer why it was there. Merging the ordered steps into
  one function that calls them in sequence made the dependency self-explaining.
- **Boundary conditions** (G33): keep boundary arithmetic in one named place (`nextLevel = level
  + 1`). Scattered `+1`/`-1` usually mean a variable's meaning was chosen badly (length versus
  index, zero- versus one-based); finding the right unit removes them (ch. 15).
- **Understand the algorithm** (G21): before calling a function done, know why it is correct, not
  only that tests pass. Refactoring until it is evident how it works is the usual route.

## 10. Structured-programming rules

Single entry and single exit matter only in large functions. In small ones, an extra `return`,
`break` or `continue` is harmless and often clearer; `goto` is avoided (Clean Code ch. 3). Guard
clauses and early returns are fine.

## 11. How such functions get written

Not in one pass. Write the clumsy version (long, nested, arbitrary names, duplicated), with tests
covering it, then refine in small steps: split, rename, remove duplication, reorder, keeping the
tests green (Clean Code ch. 3, ch. 14). The sequence for cleaning existing code is in
`review-passes.md`; mechanics of individual moves are in `craft-refactoring`.

## 12. Warning signs

- Section headers, banner comments or blank-line-separated phases in a body.
- Long parameter lists; boolean or selector parameters; parameters that are written to.
- A command that returns a status boolean.
- The same type-switch in several functions.
- Nested success checks forming a pyramid; a shared error-code enumeration imported everywhere.
- A name with "and"/"or", or a body that does something the name does not mention.
- Copies of an algorithm differing only in a string or constant.
- A high-level call beside raw string, byte or index manipulation.
- After a split: helpers with many parameters, single-use helpers you must open to follow the
  parent, a call chain many levels deep for a simple flow.
- Anonymous pair, tuple or string-keyed map as a return value where element meaning is unclear
  (PoSD ch. 18).

## 13. Verify

- Read top to bottom: every statement at one level; the body reads as a "to" paragraph.
- Try a non-restating extraction; if none exists, the function is as small as is useful.
- Nameable without "and"/"or"; the name covers every write to fields, globals and parameters.
- Count, as prompts and not thresholds: nesting depth, parameters, flag and output parameters.
- For each helper created: keep test passes (name adds meaning; parent reads without it; child
  reads without the parent; no state-carrying parameter list).
- Search for duplicates: no two blocks differing only in literals; no type-switch repeated.
- Tests unchanged and green after each extraction; if there are none, characterisation tests
  first (inferred in the notes, consistent with ch. 3 and ch. 14).
