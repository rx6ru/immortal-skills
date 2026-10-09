# Complexity and red flags

How to recognise unnecessary complexity, decide where it matters, and respond to it. Use this file
for reviews, for explaining a design judgement to a user, and when changing existing code.

Contents
1. What complexity is
2. Symptoms and causes
3. Where to spend effort
4. Strategic and tactical work
5. Modifying existing code
6. Red-flag catalogue
7. The fifteen design principles
8. Judging trends and techniques
9. Verification

## 1. What complexity is

Complexity is anything about the structure of a system that makes it hard to understand and modify
(APOSD ch. 2). Consequences of taking that definition seriously:

- It is not size or feature count. A large system that is easy to work in is not complex; a small
  one can be.
- Line count does not measure it. A shorter version is not automatically simpler; more lines can be
  simpler if they lower what the reader has to hold in mind.
- It is judged by readers. If someone else finds the code hard, it is hard; find out what they were
  missing, because that gap is the information you need.
- It is weighted by activity. The notes reconstruct the book's formula as: total complexity is the
  sum, over the parts of the system, of each part's complexity times the fraction of developer time
  spent there. The author calls it crude; use it as a way of thinking, not a number to compute. The
  corollary is useful: complexity sealed in a place almost nobody works in is nearly as good as
  complexity removed. That is the justification for deep modules and for making the common case
  simple.

There are two ways to fight it (APOSD ch. 1): eliminate it (remove special cases, be consistent) or
encapsulate it (modular design, so a person can work in one module without the details of others).

Design is continuous. The first design of anything is rarely the best, problems show up during
implementation, and incremental development therefore means continual redesign. The principles here
are for comparing alternatives, not for deriving an answer.

## 2. Symptoms and causes

Three symptoms (APOSD ch. 2):

| Symptom | Meaning | Severity |
|---|---|---|
| Change amplification | A simple-looking change needs edits in many places | Annoying; survivable when it is clear where to edit |
| Cognitive load | How much a developer must know to complete a task | Raises cost and bug risk; workable when it is clear what to read |
| Unknown unknowns | It is not evident what must change or what must be known | Worst: you learn of the problem from a bug |

Illustration from the notes: a banner colour written literally on every page is change
amplification. Moving it to one shared variable fixes that. But if a few pages hard-code a darker
shade derived from the banner colour, changing the variable silently leaves them wrong: an unknown
unknown. The cure is a single source for the decision and derived values computed from it.

Two causes:

- Dependencies: code that cannot be understood or modified in isolation. A method signature is one
  (adding a parameter touches every call site); so are the two ends of a protocol. They cannot be
  eliminated, since every new unit creates dependencies around its interface. Aim for fewer, and for
  the remainder to be simple and obvious. The shared-variable fix did not remove the dependency; it
  swapped an invisible agreement for a visible reference that can be searched for and checked by
  the compiler. That trade, non-obvious for obvious, is the general move.
- Obscurity: important information is not obvious. Generic names, undocumented units, a required
  co-change that nothing at the starting point mentions (add an error status here, and a message
  table entry somewhere else), the same name used for two purposes. Needing extensive documentation
  to explain a design is itself a sign that the design is off; simplifying the design is the better
  cure.

Dependencies lead to change amplification and cognitive load. Obscurity leads to unknown unknowns
and cognitive load.

Complexity is incremental: no single mistake causes it, it accumulates from many small dependencies
and obscurities, each of which looked harmless. Removing one makes no visible difference, which is
why it is hard to reverse and why small additions deserve attention when they are made.

## 3. Where to spend effort

- Weight by how often people work in the code. A modest mess on a path touched weekly outranks ugly
  code in a corner nobody opens.
- Prefer removing unknown unknowns over reducing change amplification.
- When a dependency must exist, make it explicit and checkable by a tool.
- Aim for an obvious system: a developer can make a quick guess about what to do and be right.

## 4. Strategic and tactical work

Tactical work (APOSD ch. 3) is focused on getting the current thing working as fast as possible and
accepts a kludge to finish sooner. It fails because of the incremental property: every task adds a
little, and the sum makes later work slow. The dynamics are a trap: earlier shortcuts cause trouble,
fixing them would slow the current task, so another patch goes in.

Strategic work treats working code as insufficient: most code is written by extending existing code,
so the main job is to make that extension easy.

- Proactive investment: take a little longer to find a simple design for each new unit; try an
  alternative; imagine a few likely changes and check they would be easy; write the documentation.
- Reactive investment: when you find a design problem, fix it instead of working around it.
- Scale: roughly 10 to 20 percent of total effort, as many small investments. The author states
  that the supporting progress-over-time picture is a qualitative illustration and that he knows of
  no measurement; treat the figure as judgement.
- Not a big up-front design. The ideal design emerges in pieces with experience.
- Do it now. "After this crunch" becomes permanent, and the longer a problem waits the larger and
  more intimidating its fix.

The book concedes that an organisation can succeed either way; the argument is about cost over the
life of the code, not inevitability.

Signs that work has drifted tactical:

- "I'll clean it up after the deadline."
- A workaround placed beside a problem instead of a fix to the problem.
- A new flag, special case or parameter added so that one caller works.
- One person lands features fast and everyone else is slow in that area (the book's "tactical
  tornado": a prolific developer whose speed is paid for by the people who clean up after).
- No comments or tests because there was no time.

For an agent, this translates to a bounded rule: before implementing, spend a small effort on
design and sketch at least one alternative; while implementing, fix a design problem in code you
are touching if the fix is small relative to the task, and if it is large, record it and raise it
instead of silently patching around it or silently expanding the task.

## 5. Modifying existing code

A mature system's design is determined more by the changes made to it than by its original
conception (APOSD ch. 16).

The usual instinct is the smallest change that works, often justified by fear of breaking things.
Each minimal change adds a special case or a dependency. The standard to aim for instead: after the
change, the system has the structure it would have had if it had been designed with that change in
mind. If you are not making the design better, you are probably making it worse.

Procedure:

1. Read the interface documentation and design of the module before editing.
2. Decide whether, knowing the new requirement, you would still structure it this way. If not,
   restructure so the feature fits naturally.
3. When the ideal restructuring is out of reach (it would take far longer than the task, or would
   disrupt other people's code), ask what the cleanest design is under the constraints you really
   have. Look for a nearly-as-clean alternative of smaller size, and make the deferred clean-up
   visible.
4. Make the minimal clean change, which may differ from the minimal diff.
5. Update the comments that the change makes false. Keep each comment close to the code it
   describes, because distance is what lets comments go stale; the further a comment sits from its
   code, the more abstract it should be.
6. Put rationale that future readers will need in the code, not only in the commit log; nobody
   thinks to search the log. A copy in the commit message is fine.
7. Document each decision once, in the most obvious place, and point to it from elsewhere. A stale
   pointer reveals itself; a stale duplicate does not.
8. Before committing, read the whole diff: stale documentation, leftover debug code, unresolved
   TODOs.

This is in tension with "do not touch working code" and minimal-diff norms. The notes observe that
the chapter mentions the risk of restructuring but does not pair it with test advice; the practical
mitigation (inferred there) is to rely on tests and review, which is where `craft-refactoring` and
`craft-testing` take over. Comment-writing detail belongs to `craft-clean-code`.

## 6. Red-flag catalogue

A red flag is a sign that code is probably more complicated than it needs to be. The response is
always the same: stop, look for an alternative that removes it, try several because each attempt
teaches something, and if it stays, be able to state why it is acceptable in this case. Flags are
symptoms, not verdicts.

The book lists fourteen (APOSD summary of red flags). Entries use: recognition; tests; remedy;
where detailed.

### Shallow module
- Recognition: the interface is not much simpler than the implementation. Small units tend this way.
- Tests: is the documentation longer than the body? Must a caller know what the body does anyway?
  Is calling it no simpler than writing the body inline?
- Remedy: give it more functionality behind the same interface, merge it into its caller or a
  neighbour, or delete and inline.
- Detail: `deep-modules-and-information-hiding.md`.

### Information leakage
- Recognition: one design decision is reflected in several modules, either through an interface or
  by the back door (two classes that both understand a file format, neither exposing it).
- Tests: pick a decision and ask how many modules change if it changes. Look for duplicated parsing
  or formatting code and for interface elements that expose representation.
- Remedy: reorganise so one class is affected; merge small, tightly tied classes; or extract a class
  that owns only that knowledge, provided its interface abstracts the details away (otherwise you
  have converted back-door leakage into interface leakage).
- Detail: `deep-modules-and-information-hiding.md`.

### Temporal decomposition
- Recognition: structure mirrors execution order; phases are separate units and share knowledge.
  Names like `Reader`/`Parser`/`Writer`, `Step1`/`Step2`, `PreProcessor`/`PostProcessor`.
- Tests: do two phase units need the same format or rules?
- Remedy: group by knowledge; one module owns the decision and offers a higher-level interface.
  Order still appears somewhere in the code; it should shape module structure only when the stages
  really use different information.

### Overexposure
- Recognition: using a common feature forces the caller to learn or pass something only rare callers
  need (a mandatory argument for an unusual option; a wrapper chain to get default behaviour).
- Tests: can the common caller finish without reading about or supplying anything rare?
- Remedy: defaults; rare features in separate methods, overloads or options.

### Pass-through method
- Recognition: a method that does little except call another with a similar signature; a class where
  most public methods do so.
- Tests: delete it and let callers call the target; did any logic vanish?
- Remedy: expose the lower class directly, redistribute functionality so the classes need not call
  each other for it, or merge them.
- Detail: `layers-and-abstraction.md`.

### Repetition
- Recognition: the same non-trivial code appears over and over.
- Remedy: the right abstraction has not been found. Extract when the snippet is long and the
  signature simple; otherwise restructure so the code runs in one place. Do not extract one-liners
  that reach into many locals.
- Detail: `together-or-apart.md`; knowledge-level duplication in `coupling-orthogonality-dry.md`.

### Special-general mixture
- Recognition: a general-purpose mechanism contains code specialised for one use of it.
- Effect: the mechanism is more complicated and coupled to that use; changes to the use force
  changes to the mechanism.
- Remedy: move the specialised code into the user of the mechanism or a layer on top.

### Conjoined methods
- Recognition: you cannot understand one method's implementation without the other's; more broadly,
  two separated pieces of code each need the other to be understood. Typical cause: a function cut
  in half at an arbitrary point, the halves sharing state or assumptions.
- Remedy: rejoin, or cut again at a line where the child stands alone.

### Comment repeats code; implementation documentation contaminates interface
- Recognition: a comment says only what the adjacent code already shows; an interface comment
  describes implementation details users do not need.
- Relevance here: the second is evidence about the interface. If you cannot document the interface
  without describing internals, the abstraction is leaking.
- Detail and remedies: `craft-clean-code`.

### Vague name; hard to pick a name
- Recognition: a name so imprecise it carries little information; or real difficulty finding a
  precise, intuitive name.
- Relevance here: difficulty naming a unit usually means it has no single clear responsibility.
  Treat it as a prompt to reconsider the decomposition, not only the wording.

### Hard to describe
- Recognition: complete documentation for a variable or method has to be long.
- Relevance here: a long description of a small thing is another form of shallowness.

### Non-obvious code
- Recognition: behaviour or meaning cannot be understood quickly.
- Remedy: supply the missing information through design, convention, naming or comments.

Not boxed in the book but named as anti-patterns in the notes: classitis (the belief that more,
smaller classes are always better, producing many interfaces that each hide little) and false
abstraction (an interface that looks simple because it omits something callers need).

First-move triage (derived in the notes):

| Flags | First move |
|---|---|
| Shallow module, pass-through, classitis | Merge, delete or deepen |
| Leakage, temporal decomposition, special-general mixture | Re-cut around knowledge; push specifics up; extract the general core |
| Overexposure | Defaults; separate rare-path methods |
| Repetition, conjoined | Find the missing abstraction, or rejoin |
| Naming and description flags | The design is unclear; reconsider the decomposition |
| Non-obvious code | Add information |

Coupling warning signs from the other sources that belong in the same review (Pragmatic Programmer
ch. 2 and 5; Clean Code ch. 6, 8, 10, 11):

- Every change seems to cause several other things to go wrong; fixes break distant code.
- Developers are afraid to change code because they cannot tell what it affects.
- A unit test has to pull in a large part of the system to build or run.
- Widely shared globals or singletons; many near-identical functions.
- Identifiers based on real-world properties you do not control (a phone number as customer id).
- Library calls that force special handling at every call site; remoteness leaking into callers.
- Call chains through several objects; a getter and setter for every field; public fields beside
  substantial behaviour; business rules inside persistence entities.
- Vendor types in signatures across many modules; the same cast or unwrapping repeated everywhere.
- Class names with `Manager`, `Processor`, `Super` (by extension `Helper`, `Util`, `Data`, `Info`);
  a description that needs "and"; fields used by only one or two methods.
- Business code that constructs its collaborators or lazily initialises them; domain classes that
  extend framework base classes.

## 7. The fifteen design principles

From the book's summary (APOSD back matter), with where each is developed:

1. Complexity is incremental: sweat the small stuff. (this file)
2. Working code is not enough. (this file)
3. Make continual small investments in the design. (this file)
4. Modules should be deep. (`deep-modules-and-information-hiding.md`)
5. Design interfaces so the most common usage is as simple as possible. (same)
6. A simple interface matters more than a simple implementation. (same; `layers-and-abstraction.md`)
7. General-purpose modules are deeper. (same)
8. Separate general-purpose and special-purpose code. (`together-or-apart.md`)
9. Different layers should have different abstractions. (`layers-and-abstraction.md`)
10. Pull complexity downward. (`deep-modules-and-information-hiding.md`)
11. Define errors and special cases out of existence. (`craft-error-handling`)
12. Design it twice. (`design-it-twice.md`)
13. Comments should describe what is not obvious from the code. (`craft-clean-code`)
14. Design for ease of reading, not ease of writing. (`craft-clean-code`)
15. The increments of development should be abstractions, not features. (section 8)

## 8. Judging trends and techniques

Evaluate any practice by one question: does it give leverage against complexity (APOSD ch. 19)?

- Incremental development: right, because the best design cannot be seen up front. The risk is
  drifting tactical by treating features as the unit of work and postponing design. Make the
  increment an abstraction: it is fine to delay thinking about an abstraction until a feature needs
  it, but once it is needed, design it cleanly, as a reasonably complete core, and somewhat general.
- Unit tests: valued because they make structural change safe. Without a suite, people minimise
  diffs and complexity accumulates.
- Test-driven development: the book's position is that it steers attention to getting individual
  features working instead of finding the best design, with no natural moment to design. It keeps
  test-first for bug fixes: write the failing test that reproduces the bug, then fix. This is one
  side of a contested question; `craft-testing` gives the others. A workable middle for an agent:
  sketch the abstraction's interface first, then write tests alongside the implementation, and
  always test-first for a reported bug.
- Design patterns: usually good when one fits, since it is hard to beat. The risk is forcing a
  problem into a pattern. More patterns is not better. See `craft-design-patterns`.
- Inheritance and accessors: see `objects-data-and-classes.md`.

Clean Code ch. 11 adds two system-level cautions with the same flavour: adopt a standard or a heavy
framework only when you can state the concrete value it adds to this system, and prefer the simplest
thing that can work, grown incrementally, which is possible only while concerns stay separated.

## 9. Verification

- Three questions per plausible change: places to edit, knowledge required, anything nothing would
  lead you to. Write the answers down for the top two or three changes.
- Reader test: would another developer find this simple? For an agent: can the design be explained
  to the user in a few sentences without caveats about hidden co-changes?
- Search test (inferred in the notes): every site depending on a decision can be found by searching
  for one name.
- After a change: the design is at least slightly better, not slightly worse. Count special cases,
  flags and parameters added; each needs a reason.
- Review question: was the first idea taken, or was an alternative considered and rejected for a
  stated reason?
- No design rationale lives only in the commit message or PR text.
- Each red flag found is either removed or has a one-line justification.
