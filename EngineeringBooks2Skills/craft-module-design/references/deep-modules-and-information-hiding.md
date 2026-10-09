# Deep modules and information hiding

How to design and judge an interface: what counts as the interface, what depth means, how to hide
decisions, how general to make it, and who should carry a piece of unavoidable complexity.

Contents
1. Vocabulary
2. Depth
3. Designing for the common case
4. Information hiding
5. Leakage and how to remove it
6. Temporal decomposition
7. Returning data, defaults, and hiding within a class
8. General-purpose interfaces
9. Pulling complexity down
10. Configuration parameters
11. Limits of each principle
12. Worked example: an HTTP request class
13. Verification

## 1. Vocabulary (APOSD ch. 4)

- Module: any unit with an interface and an implementation. A function, a class, a package, a
  subsystem, a network service.
- Interface: everything a developer working in a different module must know to use this one.
  - Formal part: what the language expresses and partly checks (signatures, types, public members,
    declared exceptions).
  - Informal part: behaviour, side effects, ordering constraints ("call A before B"), performance
    expectations, error cases. Usually larger than the formal part and describable only in
    documentation.
  - Rule: if a user must know it to use the module, it is part of the interface whether or not the
    signature shows it.
- Implementation: the code that keeps the interface's promises.
- Abstraction: a simplified view that omits unimportant details. Two ways to get it wrong:
  including details that do not matter (extra load on every user) and omitting details that do
  (a false abstraction: it looks simple, and users lack what they need to use it correctly).

A developer working in a module should need its own interface and implementation plus the
interfaces of what it calls, never other modules' implementations. The goal of modular design is to
minimise dependencies between modules.

## 2. Depth

A deep module provides a lot of functionality behind a simple interface. Think of cost and benefit:
the benefit is functionality, the cost is the interface, because the interface is the complexity the
module imposes on everyone else. Maximise functionality per unit of interface.

Examples from the notes:

- Unix file I/O: five calls with small signatures (`open`, `read`, `write`, `lseek`, `close`) hide
  on-disk layout, directories and path lookup, permissions, caching, concurrent access, device
  differences. Implementations changed completely over decades; the calls did not.
- A garbage collector: no interface at all. Adding it shrinks the system's interface, since the
  "free" operation disappears.
- A balanced tree behind insert/remove/fetch.

A shallow module has an interface that is complex relative to what it provides. A linked list class
hides little. The extreme case is a method whose whole body is one statement on a field: it offers
no abstraction (the caller still has to know about the field), is no easier to think about than its
body, needs documentation longer than the code, and adds one more interface to learn.

Classitis is the belief that more, smaller classes are always better. Each class may be simple, but
their interfaces accumulate into system-level complexity, along with boilerplate. The book states
this as a direct disagreement with small-classes-small-functions advice; the reasoning is that the
unit of cost is the interface. See `together-or-apart.md` for how to decide in a given case.

Judging depth, as a procedure:

1. List what a caller must know: signatures, behaviour, ordering constraints, side effects, error
   cases, configuration.
2. Set that against what the module does for them.
3. If the list is nearly as long as the implementation, the module is shallow.

Should detail X be in the interface? Yes if some user's correctness depends on it; no if users only
need the result to be adequate. A file system hides block allocation but must expose the rules for
when data is flushed to stable storage, because a database needs them for crash safety.

## 3. Designing for the common case

Interfaces should make the most common use as simple as possible.

- Identify the common case. Make it one call with few or no options.
- Put rare needs behind separate methods, constructors or options so they do not appear on the
  common path.
- Choose good defaults.

The notes' negative example is dated but clear: reading objects from a file in classic Java needed a
file stream, wrapped in a buffered stream, wrapped in an object stream; buffering, which nearly
everyone wants, had to be requested, and forgetting it silently gave slow I/O. The defence "some
people do not want buffering" is answered by providing buffering by default and a cleanly separate
way to turn it off.

Effective complexity: when an interface has many features but most developers need only a few, its
effective complexity is that of the commonly used features. A wide interface is acceptable if the
rare parts are invisible to the common user.

## 4. Information hiding (APOSD ch. 5)

Each module should encapsulate a few pieces of knowledge, each a design decision, so that the
knowledge lives in the implementation and does not appear in the interface. Candidates: data
structures and algorithms, file and wire formats, protocols, how a logical thing maps to a physical
one, low-level details such as sizes, higher-level assumptions such as "most files are small".

Two benefits: a simpler interface (less to know), and easier evolution (a hidden decision has no
dependants outside, so changing it touches one module).

When designing a module, ask what can be hidden in it. More hidden means a simpler interface and a
deeper module.

- Private is not hiding. A private field with a getter and setter that reveal its nature and use is
  as exposed as a public one.
- Partial hiding has value. A feature needed by few users, reached through separate methods and
  invisible in the common case, creates fewer dependencies than something every user sees.

## 5. Leakage and how to remove it

Information leakage is one design decision reflected in several modules, so that changing the
decision means changing all of them. Anything in a module's interface is leaked by definition, which
is why simpler interfaces go with better hiding.

Back-door leakage involves no interface: one class writes a file format and another reads it;
neither exposes the format, both depend on it. It is worse than interface leakage because nothing
shows it.

Remedies when two classes share knowledge:

1. Reorganise so the knowledge affects only one class.
2. If the classes are small and closely tied to the shared knowledge, merge them.
3. Extract a new class that encapsulates only that knowledge. This works only when the new class
   can offer a simple interface that abstracts the details. If it exposes most of the knowledge,
   you have replaced back-door leakage with interface leakage.

Information hiding can often be improved by making a class slightly larger: it brings together all
the code for a capability, and it lets the interface rise in level (one method that does the whole
computation instead of three step methods). This runs against small-class advice; the limits are in
`together-or-apart.md`.

The notes generalise (marked inferred): two services that both parse the same message schema, or
both know a table layout, are back-door leakage at system level; the remedies map to a shared
library or a single owning service.

## 6. Temporal decomposition

Structure that mirrors the order of operations. An application that reads a file, modifies it and
writes it gets a reader, a modifier and a writer; reader and writer both know the format.

It is tempting because execution order is on your mind while coding. But most design decisions show
up at several moments in a program's life. Guideline: focus on the knowledge needed for each task,
not on when tasks happen. Order should be reflected in module structure only when that is consistent
with information hiding, for example when stages use entirely different information.

Pipelines split as extract/transform/load by time can leak format knowledge the same way (inferred
in the notes).

## 7. Returning data, defaults, and hiding within a class

- Do not expose internal data structures. Returning the internal map makes the method shallow,
  fixes the representation into the interface, makes the caller do two steps, and makes the caller
  responsible for not mutating it. Return what the caller needs: a value, through accessors that
  also do the conversions callers always do.
- A caller-supplied value the module could compute is a leak. If a response's protocol version must
  match the request's and the request is already an argument, the library should supply it.
- Defaults are partial information hiding: normal callers need not know the item exists. A module
  should do the right thing without being asked.
- Inside a class: design private methods so each encapsulates some information or capability, and
  minimise the number of places each instance variable is used. Fewer usage sites, fewer
  dependencies within the class.

```ts
// leaks representation and makes every caller convert
getParams(): Map<string, string>

// hides storage, source (URL or body), decoding and conversion
getParameter(name: string): string
getIntParameter(name: string): number
```

## 8. General-purpose interfaces (APOSD ch. 6)

The dilemma: build a general mechanism (risk: guessing wrong, unused facilities, awkward for today)
or a special one (risk: tied to today's use).

Recommendation: somewhat general-purpose. The module's functionality reflects current needs; its
interface does not. The interface should be general enough to serve several uses and easy for the
present one. The main benefit is not reuse but a simpler, deeper interface; that holds even if the
module is only ever used once.

The notes' example is the text class of a GUI editor.

- Special-purpose version: methods that mirror UI features (`backspace(cursor)`, `delete(cursor)`,
  `deleteSelection(selection)`) using UI types. Many shallow methods, most called from one place.
  UI concepts leak into the text class, so every new UI operation needs a new text-class method.
- General version: insert text at a position; delete a range between two positions; compute a
  position a given number of characters away. Backspace becomes "delete from one position before
  the cursor to the cursor", written in the UI code.
- The UI code is slightly longer and more obvious: the reader sees exactly which characters are
  removed. The special `backspace` was a false abstraction, because UI developers needed to know
  what it deleted and had to read it anyway. Deciding who needs to know what, and when, is a core
  design question; when details matter to the caller, make them explicit at the call site.

Three questions to ask:

1. What is the simplest interface that covers all my current needs? Fewer methods with the same
   capability suggests more general methods. Stop when merging would require piling on parameters
   or flags.
2. In how many situations will this method be used? A method built for one particular use is a sign
   of over-specialisation.
3. Is this interface easy to use for my current needs? If callers must write a lot of extra code
   (loops, glue), it is too low-level. A single-character insert/delete interface is simple and
   general but forces range loops and is inefficient; build in range operations.

Smell test on a proposed name or parameter type: does it contain the name of a UI feature, a
screen, a caller or a workflow? Then the caller is leaking into the callee. Special-purpose code
belongs in the layer that owns the special purpose; general mechanisms belong below.

This is not an instruction to build future features. Functionality stays minimal; only the shape of
the interface is freed from today's caller. The notes extend the idea (inferred) to endpoints that
mirror screens versus resource-oriented operations.

## 9. Pulling complexity down (APOSD ch. 8)

When a module meets unavoidable complexity related to its own job, it should handle it inside. A
module has more users than developers, so the developer should bear the cost. A simple interface
matters more than a simple implementation.

The tempting opposite is to solve the easy part and export the hard part: throw when unsure and let
callers cope, or define a parameter and let administrators decide. That is easy for the author and
multiplies the cost by the number of callers or installations.

Example: a line-oriented text interface has a simple implementation but forces the UI to split and
join lines for mid-line inserts and multi-line deletes. A range-oriented interface makes the text
class do the splitting and merging. Its implementation is harder; the system is simpler.

Pull complexity down only when all three hold:

- (a) it is closely related to the module's existing functionality;
- (b) doing so simplifies many other places;
- (c) it simplifies the module's interface.

The `backspace` method above looks like pulling UI complexity down, but fails (a) and barely helps
(b): it is leakage, not depth.

Before throwing, returning an error code, adding a flag or adding an option, ask whether the module
can decide for itself with a sensible policy or by measuring. For the error side, see
`craft-error-handling`.

The notes generalise to client libraries that handle retries, backoff, pagination and timeouts so
each caller does not.

## 10. Configuration parameters

Configuration parameters move complexity up, to users and administrators. The case for them: users
know their domain or workload better than low-level code (which requests are urgent, for instance).
The case against: they are an easy way to dodge a decision; users often cannot determine the right
value either; values go stale as conditions change; and the system could often compute the value
with some extra work.

Example: instead of a configurable retry interval for a network protocol, measure the response time
of successful requests and use a multiple of it. That pulls the complexity down and adapts as
conditions change.

Rules:

- Before exporting a parameter ask: will users or higher-level modules be able to determine a
  better value than this module can?
- If it must exist, compute a reasonable default so users supply a value only in exceptional
  conditions.
- Ideally a module solves its problem completely; a parameter is an incomplete solution.

The Pragmatic Programmer's "configure, don't integrate" (ch. 5) points the other way for a
different class of value. The reconciliation is in `coupling-orthogonality-dry.md`: values a module
could work out are computed; details owned by the deployment, the business or the user go to
configuration with defaults and validation.

## 11. Limits of each principle

- Hide only what is not needed outside. Performance-affecting settings that different uses must
  tune belong in the interface. Best of all is a module that tunes itself; next best is exposing
  what has to be exposed.
- An interface that hides something callers need is a false abstraction and causes obscurity.
- Do not merge to the extreme of one class for the application.
- Do not generalise until the interface is hard to use for the present need.
- Do not pull unrelated complexity down.
- Linked lists and similar small utilities are sometimes unavoidably shallow; that is tolerable.

## 12. Worked example: an HTTP request class

From the notes (APOSD ch. 5), a course project to receive HTTP requests and send responses.

| Design choice | Verdict | Why |
|---|---|---|
| One class reads the request from the socket into a string, another parses the string | Leak (temporal decomposition) | Reading needs parsing: the length header must be parsed to find the end of the body, so both classes know the format, parsing code is duplicated, and callers must call two classes in order. Merge into one class that reads and parses. |
| Parameters from the URL and from the body merged behind one lookup | Good | Callers do not care where a parameter came from. |
| Values returned already URL-decoded | Good | Decoding is hidden. |
| `getParams()` returning the internal map | Shallow, leaks representation | See section 7. Use `getParameter(name)` and typed variants. |
| Caller must pass the HTTP version when creating a response | Overexposure | It must match the request's, which the library already has. Default it, and default the date header too. |

## 13. Verification

Several of these are marked inferred in the notes; they are practical probes consistent with the
chapters.

- Interface-only test: can a new user write correct calling code from the interface description
  alone? If not, the interface is under-documented or the abstraction is false.
- Counts: public methods, parameters, required call orders and caller-handled special cases, versus
  functionality. A redesign should reduce the first group without reducing the second.
- Common case: one obvious call with defaults.
- Replaceability: could the data structure, algorithm or storage be replaced with no change to
  callers? Where cheap, do it in a branch or a test double and run the tests.
- Change-impact search: for each design decision, search for who knows it. One module is the goal.
- Getter audit: accessors or returned mutable internals that reveal representation.
- Default audit: any parameter nearly every caller sets to the same value, or that the module could
  compute from its other arguments.
- Duplicate-knowledge scan: the same format constants or parsing code in more than one class.
- Generality: count callers per method; a method with one caller and a feature-specific name is a
  suspect. Imagine a second client (a batch tool, a test harness): how much of the interface would
  it use unchanged? Does adding a feature above require editing the module below?
- Pull-down: after the change, callers contain fewer lines and branches for cases the module could
  handle; the interface is no larger than before.
- Knobs: a typical deployment needs close to zero required settings; each remaining knob has a
  stated reason and a default.
