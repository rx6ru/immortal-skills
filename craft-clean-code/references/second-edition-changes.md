# Clean Code, 2nd edition: what the excerpt shows

Use this when a user cites the 2nd edition, asks what changed, or relies on a 1st-edition rule
the author has since restated.

**Limits of this file.** Only an excerpt was available: front matter, the detailed table of
contents, the foreword and introductions, chapter 3 "First Principles" in full, and the index.
Chapters 1, 2 and 4 onward, the afterword and the appendix are known from headings and index
entries only. Statements below about those parts describe what the headings show; where the notes
mark something as inferred it is marked here. Do not attribute arguments or details to the absent
chapters.

## 1. What the author says changed (introduction)

- Written more than fifteen years after the first edition. The essence of the message is stated
  to be unchanged, but the text was "significantly restated and expanded" instead of lightly
  revised.
- Added: newer languages and paradigms; revamped older chapters; new material on design,
  architecture and ethics, which the author says the first edition lacked. The architecture and
  craftsmanship parts are abridged from his later books.
- Tone: in the first edition he presented his ideas as one programmer's view; he now says he is
  more confident because the ideas have lasted.
- Critics: contrary views from other experienced programmers are included. From the contents and
  index this is an appendix recording a debate with the author of A Philosophy of Software
  Design, covering method length, comments, a rewrite of a prime-number generator by each side,
  and test-driven development.
- "Future Bob" notes: where he now disagrees with one of his own examples he left a marked
  comment showing his reaction instead of silently fixing it.
- Structure: four parts — Code, Design, Architecture, Craftsmanship. Part I leans on Part II
  through forward references.

## 2. Changes visible in the contents that affect this skill

Headings only unless stated.

| Area | 1st edition | 2nd edition contents show |
|---|---|---|
| Functions | One chapter | Split into "Clean Functions" (properties: contextual, nameable, descriptive, convenient, insulated, homogenous, pure, partial purity) and "Function Heuristics" |
| Function arguments | Ladder of 0/1/2/3 | Adds sections on variadic arguments, "more than three?", keyword arguments |
| Extraction | Asserted | A new chapter "One Thing" defending extract-method against five named objections: drowning, obscured intent, performance, bouncing around, entanglement; and a long section on what large functions are |
| Reading order | Stepdown rule | A new chapter "Be Polite": newspaper metaphor, stepdown again, "the abstraction roller coaster", "this is how we write, but not how we want to read" |
| Process | Scattered | A new chapter "The Clean Method" (make it right, with an example) and "Clean That Code!" on the cleaning process, with a postscript on using an AI assistant |
| Duplication | DRY | Sections on simple repeated code, similar code, loop duplication, and accidental versus essential duplication |
| Side effects | One section | Subsections for functional and object-oriented languages |
| Exceptions | Prefer to error codes | Same heading plus a "caveat emptor" subsection |
| Names | Sixteen-odd rules | Adds "build a system of names", "use names of appropriate length", "use appropriate parts of speech", "consider keyword parameters" |
| Comments | Good and bad lists | A "compensating for failure" section with subsections on hidden or obscured comments, lying comments, comments that are too intimate, and explaining intent in code; TODO appears in the bad list; "redundancy and imprecision" added |
| Formatting | Vertical, horizontal, team rules | Same topics visible in the headings |
| Simple design | "Emergence" chapter | "Simple Design" in the new design part: YAGNI, covered by tests, maximise expression, minimise duplication, minimise size |
| Smells and heuristics | Coded catalogue, ch. 17 | No separate chapter visible; the notes infer its content was folded into other chapters |
| AI | Absent | A chapter on programming by prompt; index entries on AI help in editing and cleaning and on its limits |

Index entries relevant to the disputes in `contested-rules.md` (pointers, not content): "long
names vs. comments", "missing vs. incorrect comments", "interface comments", "comments:
necessary evil", "verification of comments", "method splitting and complexity", "chopped-up
functions", "speculative cleanup".

## 3. Chapter 3 "First Principles" (the one chapter present)

### Framing
The chapter claims that grasping its principles gets a reader most of the way to cleaning code,
and qualifies them as old, established guidelines, not strict laws, to be applied in context.

### Core rule
Everything small, well named, organised and ordered:
- keep everything small;
- choose names that communicate to others;
- define a structure that lets others find their way;
- order elements so one concept follows another sensibly.

Warning attached: your own understanding biases your naming and structure. Deliberately take the
position of someone who does not understand the code.

### Functions
- Small; most a handful of lines. Reason: this allows descriptive names, separation of concerns
  and doing one thing.
- If a snippet does something that can reasonably be named, move it into a function named for
  what it does. Names are verb phrases; the calling sequence should read like prose.
- Example shape: a date function whose body had comment-labelled blocks ("check arguments",
  "find the date") became two calls to named helpers. The author's later note dislikes a leading
  minus sign in the result and would add a `subtractDays` helper.
- Working heuristic (inferred in the notes): a comment that labels a block of statements is a
  request to extract a function with that name.

### The larger example and the principle invoked at each step
A rental-statement class with a pricing catalogue, a discount, a tax and a bonus rule, starting
as one class with three switch statements. Premise: it grew to this form and is expected to keep
growing, so make room for growth first.

1. Extract functions so each does one thing; the orchestrating function only orchestrates. "Not
   more executable code; just more names and more structure." Single responsibility is put in
   stakeholder terms: the people who care about tax change only the tax function. Violating it
   makes code fragile: changing one concern breaks another.
2. Switches are not intrinsically bad, but a case list that will grow means one feature is added
   in several places. Turning the catalogue item into a data-carrying enumeration reduced the
   places touched.
3. Keep new changes out of old modules: move the enumeration to its own file.
4. High-level policy should not depend on low-level detail: adding an item should not force the
   policy code to be rebuilt. The author concedes this may not matter for small projects.
5. Separate the class's two jobs (collecting items; totalling and bonuses).
6. Turn the item enumeration into an interface with one implementation per item. Recorded
   trade-off: a field changed from an enumeration to a string, giving up some static type safety
   to isolate detail from policy.
7. Extract the bonus rule behind its own interface; rename types as understanding improved.
8. Result: a high-level component and a low-level one, with every dependency pointing toward the
   high-level side.

Tests were written before the restructuring and kept green at each step.

### On YAGNI
The objection that this is unneeded structure is answered by reading the phrase as a question:
what if you are not going to need it? Count the cost first. Here the stated business plans were
the evidence that growth was coming.

### Costs the chapter admits
- More modules and indirection are harder to read; added structure adds complexity that is not
  free. It is justified where cognitive load would grow anyway and the structure contains that
  growth.
- Probably slightly slower, by an amount the author considers not easily measurable for most
  applications.

### On AI assistance
The author reports that an AI assistant produced a result close to his first extract-function
cleanup but did not invert the dependencies or separate policy from detail, and concludes that
such models are not good at higher architectural goals. For an agent using this skill, the
practical reading is that function-level tidying is not the whole job when the request is about
making room for change; structural questions go to `craft-module-design`.

## 4. How to use this in practice

- A user quoting the first edition's absolutes ("functions must be under N lines", "comments are
  failures") can be told that the author's own later framing is "guidelines applied in context",
  and that the second edition includes the opposing view in an appendix. Do not claim to know
  what either side concluded there.
- The chapter 3 sequence is a compact model of "tidy first, then make room for growth": extract
  for one-thing-ness; then check whether adding the next expected item touches one place or
  many; restructure only on evidence of growth.
- Verification, as inferred in the notes: all tests pass after each step; adding a new item or
  bonus changes only the low-level side; dependencies point only from low-level to high-level.
- The Java-specific details (enumerations as classes, rebuild and redeploy costs) do not carry
  over literally; the string-for-type trade-off matters only in statically typed languages.
