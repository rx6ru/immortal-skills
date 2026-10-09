---
name: fp-api-design-with-laws
description: Provides a method for designing composable libraries and internal APIs (combinator libraries, DSLs, builders, validators, parsers, aggregators) by writing the ideal API before any representation, separating primitive from derived operations, stating algebraic laws and checking them with property-based tests, plus a chooser for monoid, functor, applicative, traversable and monad. Use when designing or reviewing a library or fluent API, when identical map/flatMap/combine code repeats across types, when choosing between dependent chaining and independent combination (sequential await vs all-at-once, fail-fast vs collect-all), when an aggregation must be mergeable or parallel, when writing law tests, or when the user says "make this composable", "what laws should this satisfy", "is this a monad". Running effects and streams is fp-effects-and-streams; general test strategy is craft-testing.
---

# Designing composable APIs with laws

## Purpose

Use this when the task is to shape an API that other code will combine: a small library, an internal
DSL, a set of combinators over some domain type. It changes the order of work. You write the calls you
wish existed first, state what must always be true of them (laws), reduce the operations to a small
primitive set, and only then choose a representation, which you are free to replace whenever a law or
a use case breaks. It also gives names and laws for the shapes that keep reappearing (monoid, functor,
applicative, traversable, monad) so you can recognise one in duplicated code and pick the weakest one
that does the job.

Scala is where the material comes from, not where it has to be used. Everything here is stated for
TypeScript, Python, Rust, Kotlin, Java, Go, Swift or C#; `references/language-mappings.md` says how
each idea looks and how it degrades where a language feature is missing.

## Choose what applies

| Situation | Use |
|---|---|
| Asked to design a new library, DSL, builder, validator, parser, scheduler, query or rule API | The design loop below; detail in `references/design-method.md` |
| An API exists and you are reviewing it for composability | `references/combinator-library-checklist.md` |
| A "run"/"execute"/"check" function prints, throws or returns nothing, so results cannot be combined | Design loop steps 3 and 4 (return a description or a rich result) |
| One function both combines things and decides when, where or how they run | "Split conflated concerns" rule below |
| The same `map`, `flatMap`, `sequence`, `zip` or merge body is written on several types | "Recognise a structure in duplicated code" below; `references/choosing-an-abstraction.md` |
| Deciding between a chain of dependent steps and combining independent ones (sequential awaits vs gather, first error vs all errors) | Applicative-vs-monad rule below |
| A reduction, merge or aggregation that should run in chunks, in parallel, incrementally or across shards | Monoid procedure in `references/choosing-an-abstraction.md` |
| Asked "what should always be true of this API?" or to write law tests | `references/laws-catalogue.md`, then `references/property-based-testing.md` |
| A law test or use case fails against the current implementation | "When a law fails" rule below; `references/worked-evolutions.md` for precedents |
| You want to see how a design moves from first guess to final form | `references/worked-evolutions.md` |
| Working in a language without higher-kinded types, laziness, pattern matching or tail calls | `references/language-mappings.md` |

This does not apply, or applies only lightly, when:

- The code is a one-off script or a single function with one caller. Nothing is being composed, so
  there is no algebra to design.
- The task is to make existing logic pure or to push effects to the edges: see `fp-pure-core`.
- The task is modelling data, typed errors, folds, laziness or the fail-fast versus accumulate choice
  for one validation: see `fp-data-and-errors`. This skill covers why that choice is the
  applicative/monad choice and how to design a library around it.
- The task is building or running an IO type, an interpreter, a stream pipeline or non-blocking
  parallelism: see `fp-effects-and-streams`. This skill uses the parallelism library only as a worked
  example of the design method.
- The task is general test strategy, test doubles or suite structure: see `craft-testing`. This skill
  covers property tests as the means of checking laws.
- The team's language and codebase make the abstraction cost more than the duplication it removes; see
  "Proportion and limits".

## How to apply

### The design loop

Work through these in order, but expect to loop. Each step names the moment in the source's worked
libraries where it happens; `references/design-method.md` expands every step.

1. **Pick the smallest use case that shows the domain.** Summing a list in parallel, parsing a
   repeated-letter string, one property of `reverse`. A realistic example brings incidental structure
   that hides the core operations. Realistic clients come later, at step 8.
2. **Write the call site you wish existed and read the types off it.** Invent type names and
   signatures; give each an informal one-line meaning. Do not choose a representation. Do not start
   from the substrate's API (threads, sockets, regex engine); work backward from the ideal.
3. **Make results values.** If the natural operation returns nothing, prints, or blocks, it cannot be
   combined. Return a description that a single interpreter (`run`) executes, or a structured result
   that carries everything a combiner needs.
4. **Settle each ambiguous meaning by asking what information the operation would need.** If one
   reading requires a global resource (a pool, a connection, a clock, a random source), choose the
   other reading: the operation describes, the interpreter receives the resource as a parameter. If
   you cannot decide yet, carry on; later steps usually force the answer.
5. **Split operations that mix two concerns.** Each primitive should say one thing. Offer the
   convenient mixtures as derived functions.
6. **Reduce to primitives.** Before adding an operation, try to build it from what exists by following
   the types. Keep the primitive set small; put everything else in terms of it.
7. **State laws and try to break them.** Start from a concrete equation, generalise it, simplify it,
   make it an executable property, then attack it with hostile inputs and hostile interpreters.
8. **Write one realistic client against the interface only.** Before any implementation exists if the
   language lets it type-check. It tests expressiveness and keeps the client independent of the
   representation.
9. **Derive the representation from what each primitive needs to know.** Start with the simplest
   thing (often a function from the interpreter's resource to a result) and extend it one primitive
   at a time. Treat it as provisional.
10. **When a law or use case breaks, choose deliberately** between fixing the implementation,
    changing the representation, and narrowing the law with a documented precondition.
11. **Probe the edge of expressiveness.** Find a use case where a later step depends on an earlier
    result. If the algebra cannot say it, add the most general primitive that closes the gap, and
    record what that extra power costs.
12. **Use it for real work and smooth it.** Add helpers and syntax where intent is buried in noise.
    This step adds convenience, not expressive power.

Two habits run through all twelve steps. Alternate between the abstract interface and a concrete
representation so each corrects the other: an interface with no representation drifts away from the
goal, and a representation with no interface overfits to the first examples. And when the code feels
tedious to write (state threaded by hand through many lines, the same three calls in every function),
treat the tedium as a sign that a combinator is missing and look for the repeated shape.

### Primitive or derived

Make an operation primitive only if at least one of these holds:

- Its meaning requires access to the representation, usually for efficiency (returning the matched
  slice of input without building the intermediate structure).
- It carries information to the implementation that no combination of other operations carries (an
  error label, a context scope, a commit point, a "run this elsewhere" marker).
- It enlarges what can be expressed (dependent sequencing cannot be built from independent
  combination).
- Measured cost justifies it, after the design has settled.

Otherwise derive it. The reason is that tricky logic (timeouts, races, error bookkeeping) then lives
in the primitives once and every derived operation inherits it. When A can be built from B but B
cannot be built from A, B is the stronger operation; note the direction, because it tells you which
abstraction you are in (see the chooser below). Some pairs are interchangeable (`map2` and `product`;
`flatMap` and `map` + `join`), and then the choice of primitive is yours.

### Split conflated concerns

Signs that one operation is doing two jobs: an argument you would sometimes want strict and sometimes
lazy; a policy (where it runs, how failures are reported, how large inputs are) that every caller
gets whether or not it wants it; an obviously wasteful result for a trivial input.

Fix by adding a primitive for the second concern and leaving the first operation plain. Combining two
results and marking something to run on another thread become `map2` and `fork`; replacing an error
message and adding context to one become `label` and `scope`; generating a value and knowing the size
to generate at become a generator and a sized layer over it. Prefer a layer over the existing type
when that type already has many operations and the new concern does not apply everywhere.

For an operation that means "this, then that" or "this, otherwise that", make the later argument lazy
(a thunk in strict languages). The second part may never run, and recursive definitions do not
terminate without it.

### Finding and using laws

1. Define what "equal" means for your type first. For descriptions and functions it is observational:
   run both under the same interpreter and inputs and compare results.
2. Get candidate laws from three places, in decreasing order of value: your mental model of the
   domain; plausible equations you invent and then test for consistency; the implementation you
   already have. The last is weakest because it will happily certify a bug.
3. Write a concrete instance (`map(unit(1))(x => x + 1)` equals `unit(2)`), generalise it over all
   arguments, then substitute trivial arguments such as the identity function to get the smallest
   form (`map(y)(id)` equals `y`). A law mentioning fewer operations tells you more about each.
4. Ask what the law forbids. Mapping with the identity changing nothing means `map` may not inspect
   values, drop elements, raise before applying the function, or flip success to failure.
5. Switch roles and attack it: empty input, a function that throws, the smallest resource (a pool
   with one thread), deep nesting, large size. Counterexamples found this way are design defects
   found before any user hits them.
6. Encode each surviving law as a property test and keep it. It guards every later change of
   representation.

Laws are what allow a caller to treat your values as black boxes and what allow generic code to be
written over them. An operation whose behaviour depends on unstated assumptions cannot be composed
safely.

### When a law fails

| Finding | Do |
|---|---|
| The law is one that composition or refactoring depends on | Fix the implementation, changing the representation if the current one cannot satisfy it |
| The law holds only under a condition the caller controls | Narrow the law, document the condition next to the operation, and test the conditional form |
| The "fix" satisfies the law by no longer doing the job | Keep the result as a separately named operation if it is useful, and continue looking |
| The law was derived from the implementation and conflicts with the model | Trust the model; the law was describing a bug |

Documenting a precondition is a legitimate outcome: an assumption that was implicit is now written
down. It is a poor outcome when the law is the one that lets users add or remove an annotation freely.

### Choosing an abstraction: the short form

Use the least powerful structure that expresses the use case. Each step up the list admits fewer
types, gives the implementation less freedom, and composes worse.

| Structure | You have | It is for | Laws |
|---|---|---|---|
| Monoid | an identity value and an associative combine | folds, merges, aggregation in any grouping, parallel or incremental | associativity; left and right identity |
| Functor | `map` | changing contents without changing shape | identity (composition follows when `map` is parametric) |
| Applicative | `unit` + `map2` | combining independent computations whose structure is fixed up front | functor laws; left/right identity; associativity; naturality |
| Traversable | `traverse` or `sequence` | applying an effectful function across a structure and keeping its shape | reduces to `map` under the identity effect and to `foldMap` under a monoid |
| Monad | `unit` + `flatMap` | steps where an earlier result decides which step comes next | associativity; left and right identity |

The decision that matters most in practice:

- If the pieces do not depend on each other's results, combine them applicatively (`map2`, `mapN`,
  `zip`, `all`, `gather`, `traverse`). You get the freedom to run in parallel or batch, a structure
  that can be inspected before running, and, with an accumulating result type, all errors instead of
  the first (`Promise.all` and Rust's `collect` into `Result` are independent but still report only
  one).
- If a later piece needs an earlier result to decide what to do or what to ask for, you need
  `flatMap`. Accept what it costs: steps become sequential, later steps never run after a failure,
  and the program can no longer be analysed ahead of time.
- Independent work written as a dependent chain (a sequence of awaits over unrelated calls, nested
  `flatMap` over unrelated validations) is the common defect. It loses concurrency or hides all
  errors after the first.

For reductions: if there is an identity and the combine is associative, abstract it as a monoid and
write the traversal once. If the natural result is not associative (a mean, a word count across a
split, "is sorted"), enlarge it to a summary that is (count and sum; edge fragments plus an interior
count; minimum, maximum and a flag) and project at the end. Associativity does not give you
commutativity, so partial results must be combined in their original order.

Full chooser, costs and instance-by-instance meanings: `references/choosing-an-abstraction.md`.

### Recognise a structure in duplicated code

1. Look for bodies that are textually the same on different types (`map2` written as a `flatMap`
   containing a `map` on three unrelated types).
2. Copy the shared body into one generic place. List exactly the operations it calls that the generic
   place does not know; those are the abstract members.
3. Shrink that list to a minimal set by deriving what you can (`map` from `flatMap` and `unit`).
4. Check which primitives each generic function really uses. If a function only needs `unit` and
   `map2`, it belongs to the weaker interface, and more types get it.
5. If the laws you need match a known structure, use its standard name and its standard laws. If your
   laws differ, pick another name.
6. In a language that cannot abstract over the container type, stop at step 3 per type: keep the same
   names, the same laws and the same law tests on each type, and copy the few small generic functions.
   The shared laws and vocabulary are the value; the generic interface is optional.

## Verify

Check the design with evidence that can be run or pointed at.

**Laws as executable properties.** For every law you claim, there is a property test that generates
inputs and compares both sides under the type's notion of equality. Minimum sets:

- Any type with `map`: identity law.
- Any monoid instance, including composed ones: associativity over generated triples, identity on
  both sides, fold of empty input returns the identity, left fold equals right fold equals a balanced
  fold, and chunked equals whole for random split points.
- Any type with `unit` and `flatMap`: both identity laws, associativity, and `map(x)(f)` equal to
  `flatMap(x)(a => unit(f(a)))`.
- Any type with `map2`: left and right identity with `unit`, associativity through `product`,
  naturality.
- Any function between two monoids that is meant to preserve structure: the homomorphism law.
- Domain laws you stated in the design (for example "adding this annotation never changes the
  result", "a labelled failure reports the label").

**Hostile interpreters.** Run the properties under the worst environments the interpreter allows,
generated as inputs alongside the data: the smallest resource pool (size one), a bounded pool, a
function that throws, empty and single-element input, deep nesting, large input (ten thousand
elements or more for anything recursive).

**Primitive/derived audit.** List the primitives. For each, write down which of the four
justifications applies. For each derived operation, confirm by reading the code that it calls only
primitives and other derived operations and does not touch the representation.

**Representation independence.** At least one realistic client compiles and passes using only the
public interface. If you changed the representation during the work, the law tests passed before and
after without edits to the tests.

**Abstraction choice.** For each use of dependent sequencing, name the earlier result the later step
depends on. If you cannot, change it to independent combination and show the observable difference
(all errors reported; calls overlapping in time).

**Reproducibility.** A failing property prints the failing input and the seed, and rerunning with that
seed fails the same way.

**Evidence to show the user.** The interface with one-line meanings; the list of laws with the test
that checks each; the primitive list with justifications; the property-test run output including
case counts and the environments exercised; any law you narrowed, with its documented precondition.

Done means:

- [ ] The smallest use case and one realistic client both read cleanly against the interface.
- [ ] Every operation is classified primitive or derived, and each primitive has a stated reason.
- [ ] Equality for the main type is defined, and every claimed law has a passing property test.
- [ ] The laws were attacked with hostile inputs and interpreters, and the results are recorded.
- [ ] The interpreter is the only place that touches resources; no combinator blocks or performs
      effects when merely constructed.
- [ ] Each structure used (monoid, applicative, monad, ...) is the weakest that expresses the use
      case, or the reason for the stronger one is written down.
- [ ] Any narrowed law has its precondition documented at the operation.

## Proportion and limits

- **Size of the task.** The full loop suits an API with several operations and more than one client.
  For a helper with one caller, take only the habit of writing the call site first. For adding one
  operation to an existing library, do steps 6 and 7 for that operation.
- **Law tests cost time to write and run.** Passing a hundred random cases is evidence and not proof,
  except on a domain small enough to enumerate. Decide how complete the property set should be by
  the usual cost and benefit; a partial specification is still worth having.
- **Generic interfaces need language support.** A `Monad` or `Applicative` interface over any
  container needs higher-kinded types. Emulating them in a language without them usually costs more
  readability than it saves duplication. Use the per-type form from step 6 of the recognition
  procedure and keep the laws.
- **Host idiom wins ties.** Where the language has a native form of the pattern (async/await, `?`,
  comprehensions, iterator adapters), build on it and state your laws against it; do not wrap it in
  a parallel vocabulary the team has to learn. Do not force every type through the generic interface
  either: the generic operations are a small part of any real type's API.
- **Eager substrates bend the laws.** A future that starts when created cannot satisfy "constructing
  a description runs nothing". Either wrap it in a thunk or document what starts when; see
  `references/language-mappings.md`.
- **The worked libraries are teaching designs.** The source says its non-blocking parallel
  implementation is not necessarily the best, its testing library has no real shrinking and a naive
  size schedule, and its parser ignores memoisation and left recursion. Take the method from them and
  take production implementations from maintained libraries.
- **Sized generation versus shrinking** is a real disagreement: the source builds the first and notes
  that the established libraries do the second. Rule: when using an existing library, use what it
  provides (current ones do both); when hand-rolling a small generator, sized generation is the one
  that needs no per-type code.
- **Laws you choose are yours to enforce.** No compiler checks them. An untested law is a comment.

## References

- `references/design-method.md`: read when designing from scratch or stuck at a step; each step with
  its decision rule and the moment in the worked libraries that illustrates it.
- `references/laws-catalogue.md`: read when deciding which laws apply or writing law tests; every law
  with its statement, what it guarantees and how to test it.
- `references/choosing-an-abstraction.md`: read when choosing among monoid, functor, applicative,
  traversable and monad, when recognising one in code, or when making an aggregation mergeable.
- `references/property-based-testing.md`: read when turning laws into tests, choosing properties,
  building generators, or designing a result type for a test runner.
- `references/worked-evolutions.md`: read for precedents; how the state, parallelism, testing and
  parser libraries each moved from first guess to final representation, and what forced each change.
- `references/combinator-library-checklist.md`: read when reviewing an existing or just-finished API.
- `references/language-mappings.md`: read before writing code in a specific language; names, idioms
  and degradations for TypeScript, Python, Rust, Kotlin, Java, Go, Swift and C#.

## Sources

- Functional Programming in Scala, 1st ed. (Chiusano and Bjarnason), ch. 6: purely functional state
  (state actions, deriving combinators from repetition, generalising a signature).
- Same, Part 2 introduction and ch. 7: purely functional parallelism (the design method, primitive
  versus derived, the mapping and forking laws, changing representation).
- Same, ch. 8: property-based testing (generators, properties, sized generation, laws as tests).
- Same, ch. 9: parser combinators (algebra first, error reporting in the algebra, deriving the
  representation).
- Same, Part 3 introduction and ch. 10: monoids (laws, folds, parallel folds, composition,
  homomorphisms).
- Same, ch. 11: monads (functor, monad, minimal primitive sets, laws, what a monad is).
- Same, ch. 12: applicative and traversable functors (weaker abstractions, laws, composition).
