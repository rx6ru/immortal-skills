# The design method, step by step

How to design a composable library or internal API, with the moment in the source's worked libraries
that shows each step. "FPiS" is Functional Programming in Scala, 1st ed. The four worked libraries
are: state actions (ch. 6), parallel computations `Par` (ch. 7), property testing `Gen`/`Prop`
(ch. 8) and parsers `Parser` (ch. 9). Their full timelines are in `worked-evolutions.md`.

## Contents

- Framing
- Step 1: smallest use case
- Step 2: ideal call site, types read off it
- Step 3: results as values; description and interpreter
- Step 4: decide meanings by the information they need
- Step 5: split conflated concerns
- Step 6: primitive and derived
- Step 7: laws
- Step 8: a realistic client against the interface
- Step 9: derive the representation
- Step 10: when a law or use case breaks
- Step 11: probe expressiveness and generalise
- Step 12: usability pass
- Step 13: look across libraries
- Techniques used throughout
- A short modern illustration
- Verify the method was followed

## Framing

The source presents design as iterative and without single right answers, only trade-offs, and takes
some wrong turns on purpose so their consequences can be seen (FPiS Part 2 intro). Practical reading:
you are allowed to proceed with an undecided question, run small experiments, and revise. The steps
below are an order of attack, not a waterfall. The source also insists that no existing library is
beyond re-examination: spending an hour or two writing signatures for a domain is a cheap way to learn
its trade-offs even when you will end up using a library someone else wrote (FPiS ch. 7, ch. 8).

Two orders of work appear. In ch. 7 and ch. 8 laws arrive after a first API sketch. In ch. 9 the
interface and its laws come first and the representation last ("algebraic design"). Prefer the ch. 9
order when you can state meanings up front; fall back to the ch. 7 order when you need a sketch to
find out what the meanings are.

## Step 1: smallest use case

**Do.** Choose the most trivial example that still exhibits the domain. Write it in plain code.

**Why.** A complicated example carries incidental structure. A trivial one isolates the essence; you
add complexity gradually. Expressiveness should come from a small set of composable core types and
functions, not from special cases (FPiS ch. 7).

**Moments.**
- Parallelism: summing a list by splitting it in half. It does not matter that parallelising a sum is
  probably slower in practice; it is a probe (ch. 7).
- Parsers: strings like "abracadabra" and "abba", explicitly not JSON or HTML yet (ch. 9).
- Testing: two properties of list reversal read from a short snippet (ch. 8).
- State: rolling a die with a random generator (ch. 6).

**Rule.** If your first example needs more than a few lines of setup, it is not the first example.

## Step 2: ideal call site, types read off it

**Do.** Pretend the perfect API exists. Write the example against it. Name each type and function the
example needs and give each a signature and a one-line informal meaning. No implementation and no
representation.

**Why.** Starting from the substrate's API imports its limitations. The source critiques raw thread
primitives with three questions that work as a checklist for any low-level API (ch. 7):

- Does the operation return a meaningful value, or can results only be obtained by side effect? If
  the latter, it cannot be manipulated generically.
- Does it tie a logical unit to a scarce physical one (a logical task to an OS thread)? Users should
  be able to create as many logical units as is natural and have them mapped to physical ones later.
- Does getting the result block, and are there combinators for composing results without waiting?

A type that fails these is acceptable as an implementation substrate and unsuitable as the
user-facing API.

**Moments.**
- From `sum(left) + sum(right)` the source reads off a container type for a result, a way to put a
  value in, and a way to get one out: `Par[A]`, `unit`, `get` (ch. 7).
- From a generator-and-property snippet: `Gen[A]`, a polymorphic `listOf`, and `forAll` returning a
  new type `Prop` that supports `&&` (ch. 8). It also notes what the signature leaves out: the list
  size is not a parameter, so either the generator assumes one or someone tells it. Leaving it out
  of the generator's API gives the runner freedom to choose sizes, which later makes minimising
  failing cases possible.
- From "recognise the character c": a `Parser[A]` parameterised by its result, because running a
  parser should yield more than yes or no, and a `run` returning either an error value or the result
  (ch. 9).

**Rule.** Make operations as polymorphic as their meaning allows the moment you write them:
`or` over parsers of any result type, not only strings; `listOfN` over any element.

**Keeping the representation abstract in code.** The parser chapter declares the interface generic
over the parser type and the error type, so everything written against it compiles with no
implementation at all (ch. 9). In languages without that facility, use an interface, protocol, trait
or module signature with an opaque type; see `language-mappings.md`.

## Step 3: results as values; description and interpreter

**Do.** Make the API return values that describe work. Provide one interpreter function that takes a
description and whatever resource is needed and carries it out.

**Why.** An operation that returns nothing, or prints, throws information away. The source's wording
for the test runner is that the trouble is less the side effect than the discarded information: a
`check` that prints cannot support `&&`, because combining two of them needs their outcomes (ch. 8).

**Moments.**
- `Par` begins as "a container you get a value out of" and becomes "a first-class program that `run`
  interprets"; `get` is renamed `run` to mark the shift (ch. 7).
- A parallel `get` in the middle of an expression breaks substitution: replacing two names by their
  definitions yields a program with the same value and no parallelism. Conclusion: combine without
  waiting, and delay the one blocking call to the very end (ch. 7).
- `Prop` moves from printing, to a boolean, to a result value carrying the failing case and the count
  of successes (ch. 8).

**Rule.** The interpreter is the only operation that may block, perform I/O, or consume a resource.
Combinators must do nothing observable when called.

Building IO types and interpreters in general is `fp-effects-and-streams`; here it is one design move.

## Step 4: decide meanings by the information they need

**Do.** When an operation could mean two things, do not implement both to find out. For each meaning,
list what the operation would have to have access to.

**Moments.**
- Does `fork` start work immediately or only mark it? If it starts work, it needs a thread pool at
  the point of the call, so the pool must be globally reachable and callers lose control of the
  parallelism strategy per subsystem. If it only marks, it needs nothing and the interpreter supplies
  the pool. The second meaning is chosen (ch. 7).
- What must a property receive in order to run? First a number of cases, then a random source because
  it has to generate values, later a maximum size. Each is added as an explicit parameter of the run
  function as it is discovered (ch. 8).
- "Combinators specify information": parser combinators at first say only what the grammar is. If
  implemented at that point, error reporting would be decided arbitrarily by the implementation. So
  the algebra gets operations whose whole job is to tell the implementation what to report (ch. 9).

**Rules.**
- If a meaning requires a global, choose the meaning that does not, and pass the resource to the
  interpreter.
- A newly discovered dependency becomes a parameter of the representation, not ambient state.
- For every cross-cutting concern (errors, positions, cancellation, timeouts, resources) ask what the
  API must carry so that any implementation can handle it well, and add an operation that carries it.
- When still unsure, keep going. The source's advice is that the trade-offs often become clear later
  in the process (ch. 7).

## Step 5: split conflated concerns

**Do.** When one operation both combines and decides policy, separate the two.

**Moments.**
- `map2` first had to be lazy in its arguments and start both sides in parallel. Then the trivial
  case `map2(unit(1), unit(1))` showed that forking is not always wanted and the API had no way to
  say where it happens. Two concerns were mixed: combining two results, and deciding whether a task
  runs asynchronously. Adding `fork` lets `map2` and `unit` be strict, removes a global policy from
  every combinator, and makes the lazy constructor derived: `lazyUnit(a) = fork(unit(a))` (ch. 7).
- Error messages: `label` replaces the message of a failing parser; `scope` adds context and keeps
  the inner detail. One operation could not serve both (ch. 9).
- Size: the generator type already had many operations, so size-awareness was added as a layer over
  it (a function from size to generator) and not by changing the generator (ch. 8).

**Rule.** Prefer a layered extension when the base type is already rich and the new concern does not
apply to all of its uses.

**Laziness of later arguments.** For "one thing then another" and "one thing or else another", make
the second argument non-strict. If the first fails the second is never consulted, and recursive
definitions such as "many p = p followed by many p, or nothing" expand forever otherwise. The
alternative is an explicit delaying combinator; the source invites comparing the two (ch. 9).

## Step 6: primitive and derived

**Do.** For every operation, try to write it using only existing ones. Keep it derived if you can.

**Moments.**
- `map` built from `map2` and `unit`, showing `map2` is strictly more powerful (ch. 7).
- `parMap` built from `sequence`, itself a fold with `map2`; no new primitive. The source's reason for
  not making it primitive: it is hard to do correctly, especially with timeouts, and primitives are
  where such logic should live once (ch. 7).
- `char` from `string` and `map`; `succeed` from `string("")` and `map`; `many1` from `map2` and
  `many`; `many` from `map2`, `or` and `succeed`; `listOfN` from `map2` and `succeed` (ch. 9).
- `slice` is the counterexample: its meaning is "return the matched input and do not build the
  intermediate structure", which constrains the implementation and so needs the representation.
  That is the hint it is primitive (ch. 9).
- Parser primitive set at the midpoint: string, regex, slice, succeed, or, flatMap. `regex` is a
  pragmatic primitive (alternation over single characters would be inefficient). After error
  reporting is designed: string, regex, slice, label, scope, flatMap, attempt, or, plus succeed
  (ch. 9).
- For a monad, three interchangeable minimal sets: `unit` + `flatMap`; `unit` + `compose`;
  `unit` + `map` + `join` (ch. 11). For an applicative: `unit` + `map2`; `unit` + `apply`;
  `unit` + `map` + `product` (ch. 12).

**Rules.**
- Primitive if it needs the representation, carries information nothing else carries, or adds
  expressive power. Otherwise derived.
- Promote a derived operation to primitive for efficiency only once the design is stable and the
  cost is measured. During exploration, learning which operations are truly primitive is the point.
- Writing the signature and following the types often produces the implementation; you can almost
  ignore the domain while doing it (ch. 7).

## Step 7: laws

**Do.** State what must hold for all inputs, then try to falsify it.

**Sequence.**
1. Define equality for the type. For `Par`: two computations are equal if, for any valid executor,
   they produce the same value. For parsers: same result on every input (ch. 7, ch. 9).
2. Concrete equation, then generalise, then simplify by substituting identity. The mapping law goes
   from `map(unit(1))(_ + 1) == unit(2)` to `map(unit(x))(f) == unit(f(x))` to `map(y)(id) == y`
   (ch. 7).
3. Read off what it forbids (see `laws-catalogue.md`).
4. Put on the "debugger hat": try corner cases and counterexamples; aim for an argument that would
   convince a sceptical colleague (ch. 7).
5. Make it executable. The parser chapter writes each law as a property using the testing library
   from the chapter before (ch. 9).

**Where laws come from** (ch. 7): the conceptual model; invented plausible equations tested for
consistency; the implementation. The last is the weakest, since laws read off buggy code describe the
bug.

**Why bother** (ch. 7 sidebar): hidden assumptions prevent treating components as black boxes, and
that makes composition impossible. Laws also make later factoring of common patterns possible.

**Moment.** `fork(x) == x` was written from the model. Attacking it with a pool of one thread
predicted a deadlock, with no failing use case reported by anyone. See step 10.

In the parser chapter each combinator gets a law as it is introduced, starting as a concrete example
(`run(char(c))(c.toString)` succeeds with `c`). The source says the set of laws need not be complete
to be useful (ch. 9).

## Step 8: a realistic client against the interface

**Do.** Write one real client using only the abstract interface.

**Moment.** A JSON parser is written as a function that takes any implementation of the parser
interface and returns a JSON parser, before any implementation exists. Reason given: a concrete
implementation ties you down and makes changing the API harder; an algebra is easier to refine when
nothing depends on a commitment (ch. 9).

**Rule.** If the client needs something the interface does not offer, add a general combinator to the
interface (not a JSON-specific one). Helpers for tokens, whitespace and literals are derived.

## Step 9: derive the representation

**Do.** Start with the simplest candidate and extend it one primitive at a time, asking of each
primitive what the value must know to support it.

**Moments.**
- `Par`: the simplest model is a function from the executor to a value. Returning a future instead
  keeps the caller's control over timeout and cancellation. The source adopts it provisionally:
  assume it is that simple and revise if some needed functionality turns out to be impossible
  (ch. 7).
- `Parser`: begin with "a function from input to error-or-value" (the parser is its own run
  function). Sequencing needs to know how much input was consumed, so the function takes a location
  and success carries a consumed count. Context needs an error stack. Commit needs a flag on failure.
  The source's observation: a parser is a state action that can fail, the state being the position
  (ch. 9).
- `Prop`: representation follows what must come out (failing case, count) and what must go in
  (cases, random source, size) (ch. 8).
- `Gen`: a state action over a pure random generator, reusing the state combinators from ch. 6, so
  generation is deterministic for a seed (ch. 8).

**Rules.**
- Give a component the least power that does the job. A parser returns how many characters it
  consumed, not a new location, because the latter would let it rewrite the input (ch. 9).
- A pure interface may sit on an effectful implementation. Mutable cells, latches and callbacks are
  acceptable inside as long as nothing observable leaks; keep the unsafe entry points non-public
  (ch. 7).
- Use a named result type when an encoding hides intent. "No failure" as an empty optional was
  replaced by explicit `Passed` and `Falsified` cases (ch. 8).
- Values only shown to people can be strings; values you compute with get a type (ch. 8).

## Step 10: when a law or use case breaks

**Options** (ch. 7): make the law hold by changing the implementation; or refine the law to state the
condition under which it holds. The second still has value because it forces an implicit assumption
into the documentation.

**Moment.** With a fixed pool of size one, forking a forked computation deadlocks: the outer task
holds the only thread while waiting for an inner task that can never start. Any fixed-size pool can
be made to deadlock the same way. A naive fix that simply runs the argument without forking satisfies
the law and no longer forks; it is kept under another name (`delay`). The real fix is a new
representation in which nothing blocks: a future that accepts a callback, with `map2` coordinating
two arrivals through a small actor. After the change the forking law holds for fixed-size pools, and
a parallel map over a hundred thousand elements runs on two threads (ch. 7).

**Lessons the source draws.** The law exposed a resource problem that might otherwise have been found
much later. Writing the tricky implementation correctly is hard, but the laws test it and it only has
to be right once. And one gap remained: the non-blocking version swallows exceptions, left as an
exercise, so do not copy that part.

**Decision table.** See "When a law fails" in SKILL.md.

## Step 11: probe expressiveness and generalise

**Do.** Look for something the algebra cannot say. Then generalise the operation that fills the gap
until nothing about it is arbitrary.

**Moments.**
- Parsers built from sequencing and choice cover context-free grammars. They cannot parse "a digit n
  followed by n letters", because the second parser depends on the first one's result. Adding
  `flatMap` closes the gap; `map` and `product` then stop being primitive (ch. 9).
- Generators need `flatMap` to choose a length and then generate a list of that length (ch. 8).
- State actions need `flatMap` to retry when a generated number falls in a biased range; `map` cannot
  express the retry (ch. 6).
- The generalisation chain in ch. 7: `choice` between two computations by a boolean; ask what is
  arbitrary (boolean, exactly two); `choiceN` over a list by index; the list is arbitrary too, so
  `choiceMap` over a map by key; the container is only ever used as a function from the first result
  to a computation, so `chooser`; that is `flatMap`, so rename it; and `flatMap` decomposes into `map`
  followed by `join`, either of which can be the primitive.

**Rules.**
- For each parameter ask "what is arbitrary here?" Replace fixed data containers by functions.
- When the generalised form matches a well-known shape, give it the well-known name.
- Record the cost of the stronger primitive. With dependent sequencing the structure is no longer
  known before running, so it cannot be analysed or optimised ahead of time (ch. 12 states this for
  parsers; see `choosing-an-abstraction.md`).
- Being able to say what an algebra can and cannot express, and to reduce it to minimal primitives,
  is the skill being trained (ch. 7).

## Step 12: usability pass

**Do.** Write real code with the library. Where intent is buried, add helpers and syntax.

**Moment.** Testing the parallelism laws with the testing library was first verbose. Refinements, in
order: a `check` for a single hard-coded case; a `Proved` result because a single case that passes is
proved and not merely unfalsified; lifting equality into the tested type so comparison runs once at
the end; a `forAllPar` that draws the executor from a weighted generator of pool configurations; a
product operator for pairing generators (ch. 8).

**Rule.** This step aims at pleasant use, not more expressive power. Choose defaults deliberately
(the source defaults to 100 cases and a maximum size of 100 to balance coverage against time).

## Step 13: look across libraries

**Do.** After two or three libraries, compare them. Operations with the same signature and the same
laws on different types are one abstraction.

**Moments.** `map` on generators looks like `map` on parallel computations, options, lists, streams
and state actions, and all satisfy the identity law (ch. 8). The body of `map2` written with `flatMap`
and `map` is identical for generators, parsers and options (ch. 11). `traverse` turns out to use only
`unit` and `map2`, revealing a weaker interface inside the monad (ch. 12).

**Mechanical extraction** (ch. 11): copy the shared body to a generic place; add as abstract exactly
the operations it calls; reduce to a minimal set. Then revisit earlier code and make generic every
function that had been written per type.

**Heuristics for discovering more.**
- When you have an operation over a pair, look for the opposite over an either/sum (ch. 11:
  `distribute` and `codistribute`).
- When a concrete container such as a list appears in an abstract interface, ask what happens if you
  abstract over it (ch. 12: how traversable is found).
- Try the effectful version of every ordinary function (map, filter, fold, zip) and see what it means
  for each instance (ch. 11).

## Techniques used throughout

**Program trace by substitution.** Expand a small expression by hand, replacing calls by their
definitions, to see what an evaluation choice does. It showed that a strict `map2` builds the whole
left half of a computation tree before touching the right (ch. 7), and that a strict recursive `many`
never terminates (ch. 9).

**Follow the types.** Write the signature, then let it dictate the body.

**Play.** Do not wait for obviously useful examples. If you only follow concrete needs you overfit the
design to them and end up with ad hoc features. Vary representations and primitives and ask: these
two functions look alike, is there a more general one? Could this be polymorphic? What if this single
value were a list? (ch. 8 sidebar)

**Oscillate.** Move between the abstract algebra and a concrete representation so each informs the
other (ch. 8).

**Awkwardness as a signal.** When the functional form feels tedious, a combinator is almost always
missing. The source's example: every random-number function has the shape "take a generator, return a
value and the next generator", and threading it by hand both bores and produces the bug of reusing an
old state. Naming the shape and writing `unit`, `map`, `map2`, `flatMap` and `sequence` once removes
both (ch. 6).

**Generality that was already there.** After writing `map` for random actions, the source notes the
implementation never used anything specific to random generators; widening the signature to any state
type required no change to the body (ch. 6). A footnote in ch. 7 makes the same point: when an
operation is indifferent to the representation, it is probably more general than its current home.

## A short modern illustration

This is an adaptation to show steps 1 to 7 on a different domain; it is not from the source. Domain:
retry policies.

```ts
// Steps 1-2: the call site we wish existed.
const policy = both(upTo(5), spaced(100));          // at most 5 tries, 100 ms apart
const result = await run(policy, fetchUser, clock); // interpreter gets the clock

// Types read off it.
type Policy = { /* opaque */ };
declare function upTo(n: number): Policy;           // stop after n attempts
declare function spaced(ms: number): Policy;        // wait ms between attempts
declare function both(a: Policy, b: Policy): Policy;    // continue only if both would; longer delay
declare function either(a: Policy, b: Policy): Policy;  // continue if either would; shorter delay
declare const forever: Policy;                      // always continue, no delay
```

- Step 3: a `Policy` is a value; nothing sleeps until `run`.
- Step 4: who owns the clock? If `spaced` slept by itself it would need a global timer. It describes;
  `run` receives the clock, so tests pass a fake one.
- Step 5: "how many times" and "how long to wait" are separate primitives, combined by `both`.
- Step 6: `upTo`, `spaced`, `both`, `either` primitive; `exponential`, `jittered(p)` derived or
  justified separately.
- Step 7: candidate laws. `both(p, forever)` behaves as `p` (identity). `both` is associative. Both
  are checked by running policies against a fake clock and comparing the sequence of decisions.
  Attack: zero attempts, zero delay, a clock that jumps.
- Step 9: simplest representation is a function from attempt number to "stop" or "wait this long";
  revise when a policy needs the last error or elapsed time.

`both` with identity `forever` is a monoid, which is step 13 arriving early.

## Verify the method was followed

- There is a written smallest use case, and it predates the implementation in the change history or
  design note.
- The interface can be read without reading the implementation: each operation has a one-line meaning.
- Each operation is marked primitive or derived, with a reason for each primitive.
- Each law has a property test; the tests refer only to the public interface.
- Constructing any value of the main type causes no observable effect (assert with a fake resource
  that records calls: zero calls before `run`).
- A realistic client exists that imports only the interface.
- Any change of representation left the law tests untouched and passing.
