# Choosing an abstraction: monoid, functor, applicative, traversable, monad

What each structure is for, how to recognise it in code, what extra power costs, and how to pick the
weakest that works. "FPiS" is Functional Programming in Scala, 1st ed. "(inferred)" marks items the
notes flag as not stated in that form by the source. Law statements are in `laws-catalogue.md`.

## Contents

- Why these structures are worth naming
- The ladder at a glance
- Decision procedure
- Monoid
- Functor
- Applicative
- Traversable
- Monad
- Applicative or monad: the central choice
- What extra power costs
- Composition
- Recognising a structure in existing code
- Verify the choice

## Why these structures are worth naming

Three benefits are claimed (FPiS Part 3 intro): duplicated code disappears into one definition;
separate instances are understood as one concept, so seeing the shape in a new problem takes you a
long way toward the solution; and a shared name lets a design be communicated in a word.

Each is an algebra and nothing more: operations plus laws. Instances may have nothing else in common,
and intuition drawn from one instance is not guaranteed to transfer (ch. 10). The generic operations
are also only a fragment of any real type's API; do not expect the abstraction to describe the whole
type (ch. 11).

A structure is useful to the extent that useful generic code can be written knowing only what it
provides (ch. 10). That is the test for introducing one into a codebase: name the generic function you
will write against it.

## The ladder at a glance

| Structure | Minimal operations | Purpose | Every ... is also |
|---|---|---|---|
| Monoid | `zero`, `op` | Combine values of one type in any grouping | |
| Functor | `map` | Transform contents, keep shape | |
| Applicative | `unit`, `map2` | Combine independent computations of fixed structure | a functor |
| Traversable | `traverse` (or `sequence` + `map`) | Run an effectful function across a structure, keeping its shape | a functor and foldable |
| Monad | `unit`, `flatMap` | Let an earlier result choose the next computation | an applicative |

Not every functor is a monad; not every applicative is a monad. Moving down the table the interface
gets stronger, fewer types can implement it, and whoever interprets the values knows less in advance.

## Decision procedure

1. **Is the task to combine many values of one type into one** (sum, merge, concatenate, count,
   collect, combine partial results)? Look for a monoid.
2. **Is the task to transform what is inside a container or computation without changing its shape
   or outcome?** `map` is enough.
3. **Are several computations combined whose results do not influence each other?** Applicative:
   `map2`, an N-ary version, or `traverse` over a collection.
4. **Is one effectful function applied to every element of a structure, wanting the same structure
   back inside the effect?** `traverse`. A structure of effects to be turned into an effect of a
   structure? `sequence`. A counter or accumulator carried through? Traverse with state.
5. **Does a later step need an earlier step's result to decide what to run or what to ask for?**
   Monad. Name the dependency; if you cannot, go back to 3.
6. **Does the caller need all errors and not only the first?** Accumulating applicative, with the
   independent checks combined flat and never nested.
7. **Can the runner profit from knowing the whole structure before running** (analysis, batching,
   parallel fan-out, optimisation, generated help or schema)? Stay applicative.
8. **Are two effects layered** (absence inside async, errors inside state)? Applicatives compose
   without extra work; monads need a purpose-built combined type. See "Composition".

## Monoid

**What it is.** A type with an associative binary operation and an identity value. Examples from the
source: strings under concatenation with the empty string; integers under addition with 0 and under
multiplication with 1; booleans under "and" with true and under "or" with false; lists under append
with the empty list (ch. 10).

**For.** Folding a collection where the fold's grouping should not matter. With a monoid you write
the traversal once as `foldMap(xs, monoid)(f)`: map each element to the monoid's type and combine.
Sum, count, any, all, min, max, concatenate, group and frequency count each become a choice of
monoid.

**What associativity buys.**
- Left, right and balanced folds agree, so you may pick the shape.
- A balanced fold can run its halves in parallel, and is cheaper when the cost of combining grows
  with size (repeated concatenation of immutable strings copies ever larger intermediates; combining
  halves cuts the work).
- Partial results can be computed per chunk, shard, worker or time window and merged later, or cached
  and merged incrementally.

**Recognise it.** An accumulation loop with a starting value and a combine step; "merge the results
from the workers"; configuration layers overlaid; error lists concatenated; metrics aggregated; maps
unioned with a rule for colliding keys.

**Composition, where most of the leverage is.**
- Pair: if A and B are monoids, so is the pair, componentwise. Lets one pass compute two folds
  (length and sum together, then divide for the mean).
- Map merge: for any key type and any value monoid, maps form a monoid (empty map; union of keys,
  colliding values combined with the value monoid). It nests: a map of maps of counts merges with no
  additional code.
- Function: functions into a monoid form a monoid, pointwise.
- Functions from a type to itself form a monoid under composition with the identity function.
- Optional: an optional of a type can be made a monoid (for example first-present-wins, or its
  mirror).
- A frequency count ("bag") is a fold with the map-merge monoid over counts, mapping each element to
  a single-entry map.

**When the natural result is not associative.** Enlarge the result to a summary type that carries the
boundary information needed to combine parts, show that the summary is a monoid, and project to the
answer at the end.

| Wanted | Why the plain result fails | Summary type | Final projection |
|---|---|---|---|
| Word count over a text split anywhere | A word cut by the split is counted twice or not at all | Either "only a fragment so far", or "left fragment, whole words inside, right fragment" | Interior count plus one for each non-empty fragment |
| Mean | A mean of means is wrong | Count and sum | Sum divided by count |
| "Is this sequence ordered?" | A boolean per half says nothing about the boundary | Minimum, maximum and an ordered flag, with an empty case (inferred shape) | The flag |

Median has no such small summary (inferred).

**Choosing among several monoids for one type.** A type can have more than one (integers: addition or
multiplication). Pass the instance explicitly or name it; do not attach "the" monoid to the type and
hope readers know which.

**Do not use when.**
- The combine is not associative even after enlarging the result (subtraction; order-sensitive
  stateful operations). Then do not regroup or parallelise.
- Order matters and your execution model cannot keep chunk order. Associativity is not
  commutativity.
- The work per element is small. Parallelising small tasks costs more than it returns, and a balanced
  fold only helps when combine cost scales with size.

**Pitfalls.** Wrong identity (0 for max, min or product). A mean of means. A separator-joining
operation applied inconsistently. Monoid and mapping function defined separately and drifting out of
step: define them together as one aggregator value (inferred).

**Verify.** `laws-catalogue.md` section 3: associativity, identity, fold equivalences, chunked equals
whole, homomorphism for functions between monoids.

**Without an identity (inferred).** You have a semigroup. Fold only non-empty inputs, or wrap in an
optional to gain an identity.

## Functor

**What it is.** A type constructor with `map` obeying the identity law.

**For.** Transforming the result of a computation or the elements of a container without running it
early and without changing shape. The source's example: sorting the list inside a parallel
computation with `map`, never calling `run` (ch. 7).

**Generic code it supports.** Little: splitting a container of pairs into a pair of containers
(`distribute`), and its dual for either-values (`codistribute`). The source says plainly that a
functor alone is not compelling (ch. 11). Its value is the law, which every stronger structure
inherits.

**Recognise it.** Any type with a `map`-like method. If you write a new one, test the identity law.

**Do not** build a generic functor interface for its own sake in a language where that is awkward.
Just give each type a lawful `map`.

## Applicative

**What it is.** `unit` plus `map2`. Equivalent primitive sets: `unit` + `apply`; `unit` + `map` +
`product`. `map`, `product`, N-ary combiners, `sequence`, `traverse` and `replicateM` are all derived
(ch. 12). With `apply`, an N-ary function is curried, lifted with `unit`, and applied one argument at
a time.

**For.** Combining independent computations. The structure of the whole is fixed before anything
runs; results only fill in the holes.

**Types that are applicative and not monads.**
- Streams combined pointwise: `unit` is an infinite constant stream, `map2` zips. `sequence` over a
  list of such streams transposes them.
- Accumulating validation: a failure carries one or more errors; `map2` of two failures concatenates
  their errors; of one failure, keeps it; of two successes, applies the function.

**Why a fail-fast result type cannot accumulate.** Combining through `flatMap` creates a linear chain
in which a later check only exists once the earlier one succeeded. An N-ary combiner built on
`flatMap` therefore stops at the first failure. If the checks are independent, combine them with the
accumulating applicative's N-ary combiner and all errors come back together.

**Recognise it.**
- Several lookups keyed by the same input, then a constructor applied to all results.
- A form or record validated field by field.
- Several remote calls whose arguments do not depend on each other.
- A parser for fields in a fixed, known order.
- A declarative description (command-line options, a configuration schema) that should be inspectable
  before running (inferred as general application).

**Do not use when** a later step needs an earlier result to choose the next computation.

**Verify.** `laws-catalogue.md` section 5.

## Traversable

**What it is.** A structure F with `traverse(fa)(f)`, for any applicative G, turning a structure of
A into a G of a structure of B. `sequence` swaps F-of-G into G-of-F. Implement `traverse`, or
`sequence` plus `map`. Instances in the source: list, optional, map, tree (ch. 12).

**How it was found.** By the heuristic "when a concrete container appears in an abstract interface,
ask what happens if you abstract over it": `traverse` over lists generalises to any such structure.

**For.** "For each element do an effectful thing and collect the results in the same shape." What
`sequence` means is fixed by the two types involved:

| From | To | Meaning |
|---|---|---|
| List of optional | Optional of list | Absent if any element is absent |
| Tree of optional | Optional of tree | Same, keeping tree shape |
| Map of parallel computations | Parallel computation of a map | Evaluate all values in parallel |
| Structure of validations | Validation of structure | All errors collected |
| Structure of state actions | State action of structure | Run in order, threading state |

**Traverse and fold.** Traverse preserves the structure's shape. `foldMap` discards it and leaves only
the monoid's combination.

**Relations.** With the identity effect, traverse is `map`. With the constant effect built from a
monoid, traverse is `foldMap`. So a traversable is a functor and is foldable. A foldable is not in
general a functor.

**Traversal with state.** Carrying an accumulator through a traversal gives a general
`mapAccum(fa, s)(f)` where `f` takes an element and the state and returns a result and the next
state. From it:
- `zipWithIndex`: state is a counter.
- `toList`: state is the list so far (prepend, then reverse at the end).
- `reverse` for any traversable: flatten to a list, reverse, refill the same shape.
- `foldLeft`.
- `zip` of two structures: traverse one while consuming the flattened other. Shapes must agree or one
  side must dominate (keep the left's shape and pad the right, or the reverse). Because traversal
  preserves shape it cannot merge different shapes, which is both its strength and its limit.

**Fusion and nesting.** Using the product of two applicatives, one traversal performs two effects.
Traversable instances compose, so a map of optional lists is traversed in one go.

**Recognise it.** A loop that builds a new collection while calling something that may fail, is
asynchronous, or needs state. A list of futures awaited as a group. A manual index counter beside a
map.

**Verify.** `laws-catalogue.md` section 6.

## Monad

**What it is.** One of three equivalent minimal sets, satisfying associativity and identity:
`unit` + `flatMap`; `unit` + `compose` (composition of functions that return computations);
`unit` + `map` + `join` (flatten one layer). Everything else (`map`, `map2`, `sequence`, `traverse`,
`replicateM`, `filterM`, `product`) is derived once (ch. 11).

**For.** Sequences of steps in which each step may use the results of earlier ones to decide what to
do. A chain of `flatMap` reads like a block of statements binding variables, and the monad defines
what happens at each statement boundary:

| Type | What happens between steps |
|---|---|
| Identity | Nothing; plain variable binding |
| Optional | A step may yield absence, which ends the rest |
| List | A step may yield many results; the following steps run once per result |
| State | The latest state is passed to the next step |
| Reader (inferred) | The same read-only environment is passed to every step |
| Parallel/async (inferred) | The next step continues when the previous one completes |
| Parser (inferred) | The next step continues from the remaining input; failure may backtrack |
| Generator (inferred) | The random source is threaded to the next step |

The contract itself says nothing about those behaviours beyond the laws. A working test for whether a
type is a monad (inferred): can you state its between-steps behaviour in one sentence?

**Extra primitives.** Each monad is the shared operations plus its own: state has get and set; a
reader has "ask for the environment"; a parser has its own. Those are specified separately with their
own laws.

**What the derived operations mean per instance.**
- `replicateM(n, x)`: repeat the effect n times and collect. For lists, all length-n combinations of
  choices; for optionals, present only if `x` is present; for generators, a list generator; for
  parsers, n repetitions; for state, n runs threading state.
- `sequence`: run a list of computations in order under the type's between-steps rule.
- `filterM`: filter with an effectful predicate; for optionals it short-circuits; for lists with a
  predicate that answers both true and false it enumerates every sub-list (inferred).

**The identity instance** is useful as the "no effect" case: generic code can be run through it to
get plain behaviour (inferred).

**Recognise it.** A constructor from a plain value, a `map`, and a `flatMap`/`then`/`andThen`/`bind`
on the same type. Chains of dependent steps with absence, failure, asynchrony or threaded state.

**Do not use when** the steps are independent; see the next section.

**Verify.** `laws-catalogue.md` section 4.

## Applicative or monad: the central choice

Three phrasings of the same distinction (ch. 12):

1. Applicative computations have fixed structure and only sequence effects; monadic computations
   choose structure dynamically from earlier results.
2. Applicative is context-free; monadic is context-sensitive.
3. With a monad, effects are first-class: they can be generated while the program is being
   interpreted, not only chosen ahead of time by the program.

Worked contrasts from the source:

| Case | Independent form | Dependent form |
|---|---|---|
| Lookups | Two lookups by the same name, combined | First lookup yields an id used as the key for the next ones |
| Tabular parsing | Columns in a known order: combine a date parser and a temperature parser | Column order given by a header line: parse the header into a row parser, then run that |
| Form validation | Name, date and phone checked independently; all errors reported | Parse a value, then validate something that needs the parsed value; stop at the first error |

Rule of thumb: independent checks get the accumulating applicative so the user sees every problem at
once; dependent steps get the fail-fast monadic chain. A single validation often has both: dependent
steps within one field (parse, then range-check), independent combination across fields. The
mechanics of the validation type are in `fp-data-and-errors`.

Adaptation to everyday code: a run of sequential awaits over calls that do not use each other's
results is a monadic chain where an applicative combine was enough, and it gives up concurrency. The
same goes for nested optional or result chaining over unrelated values, which is better as a flat
zip.

## What extra power costs

1. **Fewer instances.** Generic code written against the stronger interface excludes types that only
   offer the weaker one. Write each combinator with as few assumptions as it needs: `traverse` needs
   only `unit` and `map2`, so placing it on the applicative interface gives it to validation and
   zip-streams too (ch. 12).
2. **Less freedom for the interpreter.** If a parser is built without `flatMap`, the whole grammar is
   known before parsing and the runner may analyse it and pick a faster strategy. With `flatMap`,
   parsers are generated during parsing and that knowledge is gone. The source's summary is that
   power comes at a cost (ch. 12). The same reasoning applies to build graphs, query plans, form and
   schema descriptions and batched execution (inferred).
3. **Worse composition.** Applicatives compose generically; monads do not (next section).
4. **Opacity.** A representation that is an opaque function is easy to implement and cannot be
   rewritten by an optimiser; one that is data can be inspected and transformed, for instance to
   fuse two maps (ch. 7 footnote).

The same ordering appears one level down: `map2` is stronger than `map` (`map` can be built from `map2`
and `unit`, but `map2` cannot be built from `map`), and `flatMap` is stronger than `map2`. `join` cannot be built from `unit`
and `map2`: `unit` only adds a layer and `map2` applies a function inside without flattening (ch. 12).

## Composition

- **Monoids** compose by pairing, map merge, functions and optional wrapping.
- **Applicatives** compose: the product of two (run both side by side) is an applicative, and one
  nested inside another is an applicative, with `unit` and `map2` defined by nesting the two.
- **Traversables** compose.
- **Monads** do not compose in general. Flattening the alternating nest F-G-F-G cannot be written
  generically. It can be done when the inner type is traversable (swap the middle two with
  `sequence`, then flatten each). Otherwise you write a combined type by hand for each specific inner
  monad (a "transformer": for example, an optional inside any monad M, whose `flatMap` handles
  absence by returning M's `unit` of absent). There is no generic strategy. The source's conclusion:
  expressivity sometimes costs compositionality and modularity (ch. 12).

Practical consequence: when layering two effects, first ask whether applicative combination is
enough. If dependent sequencing is required across both layers, prefer a combined type the ecosystem
already supplies (a result-returning async function, for example) over building a general transformer
stack; see `language-mappings.md`.

## Recognising a structure in existing code

| You see | Likely structure | Next action |
|---|---|---|
| Loop with accumulator, a start value and a combine step | Monoid | Check identity and associativity; rewrite as `foldMap`; consider composed monoids for multi-statistic passes |
| Several passes over the same data for different statistics | Product monoid | One pass with a pair (or record) of monoids |
| "Combine results from workers/shards/windows" | Monoid, possibly needing a summary type | Find the summary; test chunked equals whole |
| The same `map` body on several types | Functor | Keep per type; test identity law on each |
| Nested chaining of unrelated values; sequential awaits of unrelated calls | Applicative used monadically | Switch to `map2`/N-ary/`all`; expect all errors or concurrency |
| A loop pushing onto a result list while calling something that can fail or is async | Traverse | Replace with `traverse`/`sequence` for that effect |
| A manual index or running total alongside a map | Traverse with state | `mapAccum` or the language's scan/enumerate |
| Identical `map2`-via-`flatMap` bodies on several types; chains of dependent steps | Monad | Extract mechanically (see SKILL.md); test the three laws |
| A function that takes a selector and a collection of alternatives, then runs one | `flatMap` in disguise | Generalise the collection to a function; rename |
| Two effect types wrapped one in the other with repeated unwrap-rewrap code | Composition problem | Applicative composition if independent; otherwise a combined type |

## Verify the choice

- For each monoid: the law tests pass, and the generic fold is actually used in more than one place or
  with more than one grouping. If neither, the abstraction is not earning its keep.
- For each `flatMap`: the dependency on an earlier result is named in the code review.
- For each applicative combine over a fail-fast type where the user-facing requirement says "report
  all problems": a test with two independent failures asserts both are reported.
- For each change from sequential to combined asynchronous calls: a test or measurement shows the
  calls overlap, and failure behaviour is as specified.
- For each traverse: output shape equals input shape, and the short-circuit or accumulate behaviour
  matches the effect chosen.
- The interface each generic function is written against is the weakest that type-checks.
