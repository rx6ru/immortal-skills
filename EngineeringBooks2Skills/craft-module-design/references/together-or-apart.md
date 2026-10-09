# Together or apart

Decision guide for whether two pieces of functionality belong in one unit or two, at every level:
functions, classes, modules, services.

Contents
1. What splitting costs
2. Signs of relatedness
3. Decision list
4. Reasons to bring together
5. Separating general-purpose from special-purpose code
6. Splitting and joining functions
7. The size disagreement and how to decide
8. Worked cases
9. Verification

## 1. What splitting costs (APOSD ch. 9)

The naive view is that smaller components are individually simpler, so more of them is better.
Subdivision adds complexity of its own:

1. More components to track and find, and usually more interfaces, each of which costs something.
2. Extra code to manage the components: what used one object now coordinates several.
3. Separation: the pieces are farther apart, in different classes or files. Good when they are
   truly independent, because a reader can focus on one. Bad when they are dependent, because the
   reader flips back and forth and may not know the dependency exists.
4. Duplication: code that existed once may be needed in each piece.

So the goal is not small or large units. It is the structure with the best information hiding, the
fewest dependencies and the deepest interfaces.

## 2. Signs of relatedness

Bringing pieces together helps most when they are related. Indicators:

- They share information, for example both depend on the syntax of one document type.
- They are used together, in both directions. A block cache nearly always uses a hash table, but
  hash tables are used everywhere without caches, so the relation is one-way and they stay apart.
- They overlap conceptually: a simple higher-level category contains both (substring search and
  case conversion are both string manipulation).
- It is hard to understand one without looking at the other.

## 3. Decision list

1. List what each piece knows (formats, protocols, data structures). Shared knowledge: together, or
   extract a single owner.
2. Would merging simplify the interface, by removing an intermediate hand-off or letting something
   happen automatically? Together.
3. Is the same code repeated? Factor it out if it is long with a simple signature; otherwise
   restructure the flow.
4. Is one piece general-purpose and the other specific to one user? Apart, the specific part in the
   higher layer.
5. Does reading one require reading the other? Together.
6. Are they independent, with no shared knowledge and each understandable alone? Apart is fine.
7. For a function: split only if a cleanly separable, fairly general subtask exists, or the
   function does unrelated things and callers will mostly want one of them. Never because of line
   count.
8. For a class: apply the responsibility tests in `objects-data-and-classes.md` (name, 25-word
   description, reasons to change, field usage). Different reasons to change: apart.

## 4. Reasons to bring together

Shared information. In the HTTP example, the method that read a request could not find the end
without parsing the headers, so reading and parsing both needed the format. Combining them made the
code shorter and simpler.

A simpler interface. Combining can remove the intermediate interface between two pieces, and can
let something happen automatically so most users never learn of it. Merging a raw stream with its
buffering, with buffering on by default and a way to turn it off, is the standard example.

Eliminating duplication. Two techniques:

- Factor the repeated code into one function. Works best when the snippet is long and the new
  function has a simple signature. It pays little for one or two lines, or when the snippet touches
  many local variables and would need a complicated signature.
- Restructure so the snippet runs in only one place. The notes' example is a packet-processing
  function that logged the same error in several branches, reworked to a single logging point at
  the end that every error branch jumps to. The book used `goto` for this and says so; the general
  form in other languages is a single shared exit through `finally`, `defer`, scope-based cleanup or a
  context manager (that mapping is marked inferred in the notes).

Repetition is a red flag: when the same non-trivial code keeps appearing, the right abstraction has
not been found. Knowledge-level duplication (the same fact in two forms) is treated in
`coupling-orthogonality-dry.md`.

## 5. Separating general-purpose from special-purpose code

A module that provides a general-purpose mechanism should provide only that mechanism: nothing
specialised for one use, and no second unrelated mechanism. Code specific to one use goes in the
module associated with that use, which is normally a higher layer. If a class mixes general and
special features of the same abstraction, split it into a general class and a special one built on
top.

The red flag is the special-general mixture: the mechanism becomes more complicated and is tied to
one use, so changes to that use force changes to the mechanism.

A nuance from the undo example below: the rule applies per mechanism. Special-purpose undo code for
text is separated from the general undo engine, yet it sits comfortably inside the text class,
because it is closely related to other text functions. General code for one mechanism can live
beside special code for another.

## 6. Splitting and joining functions

Length alone is rarely a good reason to split a function. Developers tend to split too much;
splitting adds interfaces and separates related code. A function with five fairly independent
blocks in sequence can be read block by block; when the blocks interact in complicated ways it
matters even more to keep them in view together. The book goes as far as saying that functions of
hundreds of lines are fine when the signature is simple and they are easy to read, because such
functions are deep.

The design goal for a function: a clean, simple abstraction that does one thing and does it
completely.

Two valid ways to split:

- Factor out a subtask into a child; the parent keeps its interface and calls the child. This is
  the best kind. It is valid only when the subtask is cleanly separable: a reader of the child needs
  to know nothing about the parent, and a reader of the parent does not need the child's
  implementation. The child is typically fairly general-purpose and could plausibly be used by
  other functions. If you have to flip between parent and child to follow either, the split is bad.
- Split into two functions that are both visible to callers. Sensible when the original had an
  overly complicated interface because it did several unrelated things. Each new interface should
  be simpler than the original and most callers should need only one. Callers needing both is a
  bad sign. These splits are uncommon because they push more onto callers.

The failure mode is a split that leaves callers invoking each piece in turn and passing state back
and forth: shallow functions that are conjoined.

Joining functions helps when it replaces two shallow functions with one deep one, removes
duplication, removes dependencies or intermediate data structures between the originals, puts
knowledge in one place, or simplifies the interface.

The conjoined-methods red flag: you cannot understand the implementation of one without the other.
Remedy: rejoin, or cut again at a boundary where the child is independently understandable.

## 7. The size disagreement and how to decide

Two positions, both from the source notes.

Small is the goal (Clean Code ch. 10):
- Classes should be small, and then smaller, with size measured in responsibilities, not lines.
- A class should have one reason to change. Tests: a concise name; a description of about 25 words
  with no "if", "and", "or", "but"; one kind of change that would force an edit.
- Answer to "many small classes hide the big picture": the system has the same number of moving
  parts either way; the choice is between many small, well-labelled drawers and a few drawers with
  everything thrown in. With small classes a developer knows where to look and reads only what is
  affected.
- Extracting small functions tends to reveal classes: locals promoted to fields so the extracted
  pieces need no parameters lower cohesion, and the fields plus the functions that share them are a
  class of their own.
- The chapter's worked example grew from about one page to nearly three, and accepts that as the
  price of names and structure.

Depth is the goal (APOSD ch. 4, 5, 9):
- Each unit costs an interface. Small units tend to be shallow, and many of them means many
  interfaces and many dependencies while each hides little.
- Rules such as "split any method longer than N lines" are rejected.
- Information hiding is often improved by a slightly larger class.
- "Do one thing" means one clean abstraction done completely, not a small line count.

Where they agree: extract genuinely separable, general-purpose subtasks; remove duplication; a
class that mixes unrelated responsibilities should be divided. Neither wants an arbitrary cut, and
Clean Code's own tests are about responsibility, not length.

Points from the notes that should temper each side:
- The Clean Code example is often criticised as harder to follow than a short, well-commented
  function, and its refactored generator shares state through static mutable fields. Promoting
  locals to fields trades explicit data flow for hidden shared state; do it only if you follow
  through to a cohesive class.
- The APOSD position is one author's judgement, stated without empirical backing, and it does not
  discuss splitting for the sake of testing or reuse.

Rule for deciding:

1. Do not use size as the criterion in either direction.
2. Ask the responsibility question: do the pieces change for different reasons, or use different
   knowledge? If yes, a split is likely to give units that each hide something.
3. Ask the independence question of the result: can each unit be understood from its interface
   alone? If a proposed split fails this, it is along the wrong line; look for a different line or
   do not split.
4. Ask the interface question: does the split reduce what callers must know, or add to it?
5. Weigh the reader's path: if the code is read top to bottom as one algorithm, keep it together
   and structure it with blocks and comments; if readers arrive wanting only one of several
   independent things, separate them.
6. Follow the local convention when the two options are close. A codebase written in one style
   reads worse with islands of the other.

## 8. Worked cases (APOSD ch. 9)

Cursor and selection: apart. An editor had an insertion cursor (always present) and a selection
(may be absent; the cursor is at one end). One team combined them in a single object holding two
positions and flags for which end was the cursor and whether a selection existed. Higher-level code
still treated them as two things, and the implementation needed flag checks everywhere. Revised
design: no special classes; a general `Position` type; the selection is two positions and the cursor
is one. Simpler to use and to implement, and positions were reusable. They were not related closely
enough to combine.

A separate logging class: together. A class called a dedicated logger from each catch block; the
logger had one shallow method per error site, each with long documentation and exactly one caller.
The separation added interfaces and made readers flip between call site and logging method. Better:
put the log statement where the error is detected.

Undo: separate general from special. Requirement: multi-level undo and redo covering text,
selection, cursor and view. The poor design put all of undo in the text class: a history list,
automatic entries for text changes, extra methods for the UI to add selection and cursor entries,
callbacks to the UI on undo. A general undo core ended up mixed with special handlers for things
unrelated to text, with information leaking both ways. The better design:

- A `History` class that manages a list of actions. An action is an object with `undo` and `redo`.
  `History` offers add-action, add-fence, undo and redo, and knows nothing about what actions do.
- Action types live in the modules that understand them: insert and delete actions in the text
  class, selection and cursor actions in the UI.
- Fences mark group boundaries, so one user-level undo walks back to the previous fence. Where to
  put fences is a policy decided by high-level UI code.

Three kinds of functionality end up in three places, each independent: the general mechanism, the
specifics of each action, and the grouping policy. The one decision that produced the design was
separating the general-purpose part of undo from the special-purpose parts. The same shape (general
engine, special adapters, policy at the top) recurs in plug-in systems and middleware; it is the
Command pattern with a general engine, see `craft-design-patterns`.

## 9. Verification

- For every extracted function: a reader understands it from signature and description alone, and
  the parent reads naturally with only the child's interface. If not, it is conjoined.
- Single-use helper with an awkward signature and many parameters carrying state: suspect (marked
  inferred in the notes).
- After combining: did the number of interfaces and the lines of glue code go down?
- After splitting: is each new interface simpler than the original, and do most callers use only
  one of the pieces?
- Shared-knowledge scan: the same format or structure handled in two classes argues for a merge or
  a single owner.
- Repetition scan: search for the same snippet; remaining repeats mean a missing abstraction.
- Special-general check: does the lower module mention any name from the layer above it? Does
  adding a feature in the upper layer require editing the lower one?
- Class split: each resulting class passes the description test and you can name the single kind of
  change that would touch it.
- Service-level reading (inferred in the notes): services that share a schema or must be released
  together are conjoined; splitting them added interfaces, network distance and duplication without
  independence. For that level use `arch-decomposition`.
