# Property-based testing and law tests

Stating what must hold for all inputs of a kind and letting a tool generate the cases. Use when a function has an inverse or invariant, when there are too many input shapes to enumerate, when you are checking algebraic laws of an API (identity, associativity, `map` identity), or when example tests keep missing edge cases such as empty input.

Source: Functional Programming in Scala ch. 8. The book builds its own small library mainly to teach library design (see `fp-api-design-with-laws` for the design method). This file extracts what an agent needs to use property testing in any language; mappings to current libraries are adaptation.

## Contents

1. What it is
2. When it pays and when it does not
3. Kinds of properties to look for
4. Procedure to add property tests to a codebase
5. Generators
6. Running, sizes, failure reports and reproducibility
7. Shrinking versus sized generation
8. Laws as properties
9. Generating functions
10. Environment as a generated input
11. Pitfalls
12. Library mapping (adaptation)
13. Verify

---

## 1. What it is

Separate the specification of behaviour from the creation of test cases (ch. 8). You write a property, a predicate that should hold for every input of a described kind, plus constraints on the inputs. The framework generates many cases, runs them, and reports a falsifying case.

Vocabulary: a generator knows how to produce values of a type; a property binds a generator to a predicate; running reports either "OK, passed 100 tests" or "falsified after 6 passed tests" with the argument. Several properties together form a partial specification. The goal is greater confidence, not total specification; do a cost-benefit analysis on how complete the properties should be.

Example properties of list reversal: reversing twice gives back the list; the first element of a list equals the last element of its reverse. A deliberately false property (a list equals its reverse) fails quickly and prints the argument.

Passing is evidence, not proof, with one exception: when the domain is small enough (for example all booleans or bytes) and every value is tested, the result is a proof, and a good runner says so.

## 2. When it pays and when it does not

Use when:

- the function is pure or nearly so, with a crisp relation between input and output (parsers, serialisers, sorting, arithmetic, data-structure operations, normalisers);
- there are round-trips, inverses or invariants;
- you have a slow, obviously correct implementation to compare against;
- you want to check a law claimed by an API;
- examples keep missing empty, duplicate or extreme inputs. The book's first run of a `max` property crashed on the empty list, revealing a hidden assumption.

Do not use when:

- the behaviour is a specific business rule with no general relation (a tax table). Write examples.
- the property you can think of just restates the implementation. That proves nothing; look for a different angle (relationship, inverse, model).
- tests would need a database or network per case and run too slowly for 100 cases. Use a handful of examples or a model-based approach with in-memory fakes.
- you cannot make randomness reproducible (section 6).

## 3. Kinds of properties to look for

The book hints at several (sum, max, sorted, takeWhile); the full categories below are the notes' generalisation and are marked inferred where they go beyond the hints.

| Kind | Form | Example |
|---|---|---|
| Round trip / inverse (inferred) | `decode(encode(x)) == x` | serialise then parse |
| Idempotence (inferred) | `f(f(x)) == f(x)` | sorting twice, normalising twice |
| Invariants preserved (inferred) | length, sum, ordering unchanged | reversing preserves the sum of a list; a list's sum is unchanged under permutation |
| Output bounds | result relates to every input element | max is at least every element and is itself an element |
| Oracle / model comparison (inferred) | fast version equals slow obvious version | optimised algorithm versus naive loop |
| Algebraic law | associativity, identity, commutativity, `map(id) == id` | `map(unit(x))(f) == unit(f(x))` |
| Relationship between two functions | combination reconstructs input | `takeWhile(f) ++ dropWhile(f) == s`; `s.takeWhile(f).forall(f)` |
| No crash for arbitrary input (inferred) | the call does not throw | parsing garbage returns an error value, not an exception |
| Metamorphic (inferred) | change input in a known way, output changes predictably | adding a constant c to every element raises the sum by c times the length |
| Special cases | all elements equal x implies sum is n times x | fast sanity check |

Sorting (the book leaves it as an exercise; the properties are standard, inferred): output is ordered; output is a permutation of the input; same length; idempotent.

## 4. Procedure to add property tests to a codebase

Language-independent procedure from the notes (inferred application of ch. 8):

1. Pick one function with a crisp specification.
2. List properties by category (section 3). Write them in a sentence each before coding.
3. Write a generator for the domain from small parts: constants, ranges, booleans, bounded lists, weighted unions, dependent generation, tuples. Prefer generators that build valid values by construction over generate-then-filter (filtering wastes cases and can starve the test).
4. Make randomness an explicit seeded value. Print the seed, or at least the failing case, so any failure is reproducible.
5. Run N cases with sizes increasing from small to large. The defaults in the book: 100 tests and a maximum size of 100, a balance between coverage and time.
6. On the first failure, read it as information about an assumption you had not stated (empty input, overflow, NaN, duplicates, Unicode). Either fix the code or tighten the generator and document the precondition.
7. Add the concrete failing case as an ordinary example test beside the property, so the regression stays even if the generator changes.
8. Check the property itself can fail: break the code (fault injection, `writing-clean-tests.md` section 10) and see that the property finds it.

## 5. Generators

Design notes from the book's derivation:

- A generator should be a first-class, composable value. Read its type signature off the usage: it is polymorphic, a generic list-of generator takes a generator of elements.
- Keep the size of generated collections out of the generator's own signature. If the generator owns the size, the runner cannot choose sizes, and minimisation becomes impossible (section 7). Offer an explicit-size variant too.
- Building blocks to have: constant, integer in a range, boolean, list of n, union with equal likelihood, weighted choice, product of two generators, and dependent generation (generate a length, then a list of that length; or a string, then another string using only characters of the first).
- Deterministic given a seed: build generators on an explicitly threaded random state.
- Play with the design (sidebar "The importance of play"): ask whether two functions are special cases of a more general one, whether something should be polymorphic. This avoids overfitting the generator set to the few examples you have.
- Generators that never produce edge cases give false confidence. Check the distribution: do you ever get the empty list, one element, duplicates, extremes? Weight them in explicitly.

Sketch (Python with Hypothesis, adaptation):

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers(), min_size=1))      # non-empty: precondition made explicit
def test_max_bounds(xs):
    m = max_of(xs)
    assert m in xs and all(x <= m for x in xs)
```

Sketch (TypeScript with fast-check, adaptation):

```ts
import fc from "fast-check";
test("encode/decode round trip", () => {
  fc.assert(fc.property(fc.string(), s => decode(encode(s)) === s));
});
```

## 6. Running, sizes, failure reports and reproducibility

- The runner returns a structured result (passed with the count; falsified with the case and the number of passes before it; proved for exhaustive cases), not just a printed line. A runner that only prints cannot be composed and cannot drive an exit status in CI.
- Exceptions thrown by the predicate are caught and reported as a failing case with the exception message, otherwise a throw loses the input that triggered it.
- Compose properties and tag them, so a failure of a conjunction says which part failed.
- The book's default seeds from the system clock; so print the seed. Without it, a failing run cannot be repeated (inferred).
- A hardcoded single-case check should be reported as proved, not "passed 100 tests".

## 7. Shrinking versus sized generation

Two ways to give the smallest failing example (ch. 8):

| | Shrinking | Sized generation |
|---|---|---|
| How | after a failure, a separate procedure reduces the failing value until it stops failing | generate cases in order of increasing size; the first failure is the smallest at that size |
| Code needed | per-data-type shrink code | generators only need to produce a value of a given size; the runner owns the size schedule |
| Notes | works on any failing value | must be designed in from the start; smallest by size, not by structure |

Modern libraries (Hypothesis, fast-check) do both shrinking and size bias (the book's own library does only sized generation). Use what your library provides, and keep generators simple.

## 8. Laws as properties

Translate a law to `forAll(gen)(x => lhs(x) == rhs(x))`. The chapter's examples: `map(y)(id) == y`; `map(unit(x))(f) == unit(f(x))`; `fork(x) == x`. The identity law for `map` recurs across every container (a parallel computation, an option, a list, a stream, a state transition, a generator); if you write a new `map` or `flatMap`, expect the same laws and test them.

Parametricity note from the book: `map` cannot care about the values, so one value type is enough for the identity law; what should vary is the structure of the computation, so generate richer structures (deeply nested computations).

Equality of effectful or function-valued results must be defined through running them; build that into a helper (`equal`, `forAllPar`). The full catalogue of laws and the monoid, functor and monad laws are in `fp-api-design-with-laws`.

## 9. Generating functions

Testing a higher-order function with an arbitrary predicate (`takeWhile(f)`) needs generated functions. Constant functions are uninteresting (always true or always false). The book leaves proper function generation as an open exercise; the notes' inferred approach: derive the output from a hash of the input combined with a generated seed, so the same input always gives the same output and different inputs vary, and record the seed so the function can be reproduced. Cheaper workaround: test with a few specific predicates (even, positive, always-false).

## 10. Environment as a generated input

Make the strategy or environment part of the generated input instead of hard-coding one. The book generates the thread pool (mostly small fixed pools, sometimes a cached pool) so each property of a parallel computation is exercised across pool sizes, the variation that exposed a deadlock. Adaptation: generate configuration flags, locale, time zone or batch size the same way.

## 11. Pitfalls

- Treating 100 passing random cases as proof.
- Properties that restate the implementation.
- Generators too narrow, constant, or lacking edge cases.
- Filtering generated values until few survive.
- Nondeterministic failures with no printed seed.
- Slow predicates times 100 cases.
- Tests that depend on generated order of side effects.
- Forgetting to restrict the generator when the function has a documented precondition, and then "fixing" the library instead. Decide: is the empty list valid input? Either handle it or document and exclude it.

## 12. Library mapping (adaptation)

| Language | Library |
|---|---|
| Python | Hypothesis |
| TypeScript/JavaScript | fast-check |
| Rust | proptest, quickcheck |
| Java | jqwik, junit-quickcheck |
| Kotlin | kotest-property |
| Go | rapid, gopter |
| Scala/Haskell | ScalaCheck, QuickCheck |

What a language needs: generators as values (functions or classes), generics for typed generators (degrades to untyped generators or reflection in dynamic languages), a seedable random source, closures for function generators. Where nothing is available, a hand-rolled `gen(rng, size)` function and a loop run the same idea.

## 13. Verify

- Each property has a one-sentence statement and a category (section 3).
- The property fails when you break the code on purpose.
- The seed or failing case is printed; rerunning with it reproduces the failure.
- The generator can produce empty, minimal, duplicate and large values (print a sample or add a coverage label).
- Example tests for known regressions sit beside the properties.
- Run time is acceptable for the pipeline (default 100 cases).
