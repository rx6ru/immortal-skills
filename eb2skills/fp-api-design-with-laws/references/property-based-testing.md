# Property-based testing as the way to check laws

How to state properties, build generators and run them, with the design lessons the source draws from
building a testing library. The emphasis here is checking the laws of an API you designed. For where
property tests sit in an overall test strategy, see `craft-testing`. "FPiS" is Functional Programming
in Scala, 1st ed., ch. 8 unless another chapter is given. "(inferred)" marks items the notes flag as
not stated in that form by the source.

## Contents

- What it is
- When to use it and when not
- Procedure
- Property catalogue
- Generators
- Minimising failing cases
- Running: result type, counts, seeds, labels
- Testing laws of an API
- Environment as a generated input
- Properties over functions
- Exhaustive checking and "proved"
- Pitfalls
- Design lessons from building the library
- Verify

## What it is

Specifying behaviour is separated from producing test cases. You state a property (a predicate that
should hold for every input of a described kind) and describe the inputs with a generator. The
framework produces many cases, runs them, and on failure reports a falsifying input.

Vocabulary: a generator knows how to produce values of a type and is an ordinary composable value;
its domain is the set of values it can produce; a property binds a generator to a predicate and can
be combined with other properties; running a property reports that it passed some number of cases or
that it was falsified after some number, with the offending argument.

Several properties together are a partial specification. The aim is greater confidence, not a
complete specification; decide how far to go by cost and benefit.

## When to use it and when not

Use when:
- You have stated a law for an API (`laws-catalogue.md`).
- A function has an inverse, an invariant, an obvious slow equivalent, or a relation to a sibling
  function.
- You are about to change a representation and want a guard that does not depend on it.
- Example tests keep missing edge cases.

Prefer plain example tests when:
- The only property you can state restates the implementation.
- The behaviour is a table of specific cases (a tax table, a routing table).
- Valid inputs are so constrained that the generator would be harder to get right than the code.

Keep concrete regression examples beside properties as single-case checks (inferred).

## Procedure

1. Pick the function or law. List candidate properties using the catalogue below.
2. Build a generator for the inputs from small combinators. Prefer constructing valid values directly
   over generating broadly and filtering (inferred).
3. Make the random source explicit and seeded; make failures print the input and the seed (inferred;
   the source's default seeds from the clock, which is why printing matters).
4. Run a bounded number of cases with sizes going from small to large.
5. Read the first failure as information about an assumption you had not stated: empty input,
   overflow, duplicates, a value outside the intended range. Then either fix the code or narrow the
   generator and document the precondition (inferred as a procedure; the source's example is below).
6. Add any failing case as a fixed example.

The source's example of step 5: a property that the maximum of a list is at least every element
failed because the library's own maximum function fails on an empty list. The property had to be
restricted to a non-empty-list generator. Its comment: property testing has a way of revealing hidden
assumptions.

## Property catalogue

Properties the source gives or hints at:

| Function | Properties |
|---|---|
| reverse | Reversing twice gives the original; the first element equals the last of the reversed list |
| sum | Reversing the list does not change the sum; a list of n copies of x sums to n times x |
| max | No element exceeds it; (inferred) it is an element of the list; undefined on empty input |
| takeWhile | Every element of the result satisfies the predicate; `takeWhile` followed by `dropWhile` with the same predicate rebuilds the input |
| API laws | `map(y)(id) == y`; `fork(x) == x`; `map(unit(x))(f) == unit(f(x))` |

Further ones marked inferred in the notes: sum of an empty list is zero; sum of a concatenation is the
sum of the sums; sum is invariant under permutation; sorted output is ordered, is a permutation of
the input, has the same length, and sorting is idempotent; the result of `takeWhile` is a prefix.

General categories to scan (inferred):

| Category | Shape | Example |
|---|---|---|
| Round trip / inverse | `decode(encode(x)) == x` | Serialise then parse |
| Idempotence | `f(f(x)) == f(x)` | Sorting, normalising |
| Invariant preserved | Some measure is unchanged | Length, sum, set of elements |
| Oracle / model | Agrees with a slow obvious implementation | Optimised versus naive |
| Algebraic law | Associativity, identity, commutativity, functor identity | Monoid instances |
| Relation between functions | Two functions reconstruct or bound each other | take/drop |
| No crash | Any input yields a defined result | Parsers, decoders |
| Metamorphic | A known change to input causes a predictable change to output | Appending an element raises the count by one |

A property written in the wrong form is worth trying on purpose: the source shows a false one
(reverse equals the original) failing immediately with a small counterexample, which confirms the
harness can fail.

## Generators

**Primitives in the source's library:** a constant; an integer in a half-open range; a boolean; a list
of fixed length from an element generator.

**Combinators:**

| Combinator | Purpose |
|---|---|
| `map` | Transform generated values |
| `flatMap` | Dependent generation: draw a length, then a list of that length; draw a string, then a second using only its characters |
| product (pair) | Two independent generators into a generator of pairs |
| `union` | Either of two generators with equal likelihood |
| `weighted` | Either of two with probability proportional to given weights |
| list of N / list / non-empty list | Collections; the unsized `list` takes its length from the runner's size |
| `unsized` | Lift a plain generator into a sized one |

**Representation.** A generator is a state action over a pure random source (FPiS ch. 6, ch. 8).
Consequences: generation is deterministic for a given seed, failures are reproducible, and the
generator's combinators are the state combinators.

**Questions to ask while designing generators** (the source's "play" list): is a new primitive needed
for a pair in a range, or does it follow from existing ones? Can a generator of optionals be made
from a generator and the reverse? Can strings be built from existing primitives?

**Polymorphism.** A list combinator should work for any element generator; needing one per element
type would be odd.

**Size is not the generator's decision.** The list combinator's signature does not mention size. Left
out, the runner is free to choose sizes, which is what makes minimisation possible. Provide a
fixed-length variant for when the test needs one.

## Minimising failing cases

Two approaches, presented in the source as alternatives:

| | Shrinking | Sized generation |
|---|---|---|
| Idea | After a failure, repeatedly reduce the failing input while it still fails | Generate in order of increasing size, so the first failure is already small |
| Per-type code | Typically needs reduction code for each data type | None; a generator only needs to produce a value of a given size |
| Who decides the search | The shrinker | The runner owns the schedule over sizes |
| Result | Small relative to the original failing value | Smallest by size, not necessarily structurally minimal (inferred) |
| Constraint | Works on any failing value (inferred) | Size must flow from runner to generator from the start (inferred) |

The source builds sized generation, calling it somewhat simpler and in some ways more modular, and
says the established libraries of its time shrink. The notes add that current libraries commonly do
both. Decision rule: with a library, use what it offers and do not disable it; when hand-rolling a
small harness, sized generation costs the least.

**How the source implements it.** A sized generator is a function from a size to a generator, layered
over the plain generator type. The property's run function receives a maximum size and a case count.
For each size from zero up to the smaller of the two it runs an equal share of the cases, computed as
(cases + max - 1) / max, and combines the per-size properties with "and". The source calls this
schedule simplistic and suggests a runner could instead try sizes 0, 1, 2, 4, 8, ... and then narrow
in like a binary search.

## Running: result type, counts, seeds, labels

**Return a value.** A runner that only prints cannot be combined: "and" of two such checks has
nothing to work with. The source's result type ends as three cases: passed; falsified with the
failing case and the number of successes before it; proved. Map that value to output and an exit
status at the edge (inferred application).

**Failing case as text.** The failing value is kept as a string because it is only ever shown to
people. Data you compute with gets a type.

**Exceptions.** If the predicate throws, catch it and report a falsification that includes the
generated input, the message and the stack trace. Otherwise the throw loses the input that caused it.

**Counts and sizes.** Defaults in the source are 100 cases and a maximum size of 100, chosen to
balance coverage and running time.

**Labels.** When properties are combined with "and"/"or", a failure does not say which part failed.
Attach a label to each property and prefix failure messages with it.

**Single cases.** Use a dedicated single-case check for a hard-coded example; running it a hundred
times through the general mechanism is waste.

## Testing laws of an API

Translate each law to "for all generated x, the left side equals the right side" using the type's
equality (`laws-catalogue.md` section 1).

- **Lift equality into the tested type** where possible so the test does not reach into internals and
  runs the interpreter once. For parallel computations the source defines equality as a combined
  computation yielding a boolean.
- **Vary structure, not content, for parametric operations.** `map` cannot depend on the values it
  maps over, so testing its identity law with one value type is sufficient. What can matter is the
  structure of the computation: generate deeply nested or heavily forked computations.
- **Laws quantify over all values and types; a test covers the ones generated.** Say so in the test
  name or comment rather than implying a proof.
- **Parser laws** are expressed by running both sides on generated input strings and comparing
  outcomes; conditional laws (about failure messages) check only the cases where the parser fails
  (FPiS ch. 9).
- **Monoid laws** are a reusable function from an instance and a generator to a property
  (FPiS ch. 10).

Sketch (Python with a property-testing library; adaptation):

```python
from hypothesis import given

def monoid_laws(zero, op, gen):
    @given(gen, gen, gen)
    def associativity(x, y, z):
        assert op(op(x, y), z) == op(x, op(y, z))

    @given(gen)
    def identity(x):
        assert op(x, zero) == x and op(zero, x) == x

    associativity()
    identity()
```

Call it for every instance, including composed ones.

## Environment as a generated input

The source's parallelism properties do not fix one thread pool. They draw the executor from a
weighted generator: with weight 0.75 a small fixed pool whose size comes from a range
generator starting at one, and with weight 0.25 an unbounded pool. Each property is thereby exercised across the variation that exposed
the forking deadlock.

Generalise: anything the interpreter takes as a resource or configuration (pool size, buffer size,
batch size, clock behaviour, the seed) is a candidate for generation alongside the data. Include the
smallest legal value.

## Properties over functions

To test `takeWhile` for any predicate you need generated functions. Options, in order of effort:

1. A handful of fixed functions (is-even, always-true, always-false). The source calls this the cheap
   workaround.
2. A generator of constant functions. Easy and nearly useless: every generated predicate is always
   true or always false.
3. A generator of functions that use their argument. The source leaves this as an open exercise. One
   approach (inferred, not in the source text): draw a seed, and let the function compute its output
   by seeding a generator from a hash of the input combined with that seed. Equal inputs then give
   equal outputs and different inputs give varied ones.

Established libraries provide function generation; use it when present (adaptation).

## Exhaustive checking and "proved"

When a generator's domain is small enough to enumerate, testing every value is a proof and not just
the absence of a counterexample. A single hard-coded case that passes is likewise proved. The source
adds a distinct "proved" outcome so the report does not claim "passed 100 tests" for a single check.
Extending this to enumerate small domains (booleans, bytes) and sized generators up to the maximum
size is left as an open exercise.

## Pitfalls

- Random passes are evidence, not proof.
- A property that mirrors the implementation proves nothing. Come at the behaviour from another
  direction: inverse, relation, oracle.
- Generators that never produce the edge cases (empty, one element, duplicates), or are too narrow,
  give false confidence (inferred).
- Constant-function generators.
- Seeding from the clock without reporting the seed makes failures unreproducible (inferred).
- Comparing effectful or function-valued results structurally. Define equality through running.
- Unlabelled composite properties.
- Filtering heavily in generators, which wastes cases and biases what remains (adaptation).

## Design lessons from building the library

These are uses of the method in `design-method.md`; the full timeline is in `worked-evolutions.md`.

- Read needed types off a usage snippet, including what the signatures leave out.
- Reject an operation that discards information.
- Grow a representation by asking what must come out, then what must go in; add each new dependency
  as a parameter.
- Replace a clever encoding with a named type when intent is unclear.
- Add a layer over a rich type for a concern that does not apply everywhere.
- Test usability by writing real tests; add helpers and syntax where intent is obscured.
- The operations and laws of generators match those of other types; note it.

## Verify

- Every property has a label, and a deliberate break in the code under test makes the corresponding
  property fail (mutate one line, run, restore).
- A failure report contains the input and the seed; rerunning with that seed reproduces it.
- Generators demonstrably reach the edge cases: log or assert that empty, single-element and maximal
  sizes occur within a run.
- The runner returns a value and the build fails on falsification.
- Law tests import only the public interface of the type under test.
- For concurrency-related laws, the smallest resource configuration is among those generated and the
  run has a timeout.
- Case count and maximum size are stated; running time is acceptable for the suite it lives in.
