# Laws catalogue

Every law in the source notes, in one format: statement, what it guarantees, how to test it. "FPiS" is
Functional Programming in Scala, 1st ed. Items the notes mark as inferred or reconstructed carry
"(inferred)".

Notation: `unit(a)` wraps a plain value; `map(x)(f)` transforms the contents of `x`;
`map2(x, y)(f)` combines two; `flatMap(x)(f)` feeds the result of `x` to `f`, which returns the next
computation; `id` is the identity function; `==` is the type's equality (see section 1).

## Contents

1. Before any law: equality
2. Functor
3. Monoid
4. Monad
5. Applicative
6. Traversable
7. State actions
8. Parallel computations
9. Parsers
10. Consistency between primitive and derived forms
11. Turning a law into a test
12. Which laws to test for which type

## 1. Before any law: equality

A law is an equation, so decide what equality means first (FPiS ch. 7).

| Kind of value | Equality to use |
|---|---|
| Plain data | Structural equality |
| A description run by an interpreter (parallel computation, effect, policy) | Run both under the same resource; compare results. For all valid resources. |
| A parser, decoder, validator | Same result on every input, including the same failure where failure content is part of the contract |
| A state action or reader | Run both from the same initial state or environment; compare value and final state |
| A random generator | Run both from the same seed; compare outputs |
| Floating-point results | Tolerance, or test on integers (inferred) |

Comparing closures structurally is meaningless; put the "run both and compare" logic into a helper
and build law tests on it. The source lifts equality into the tested type
(`equal(p, p2) = map2(p, p2)(_ == _)`) so the test runs once at the end and knows nothing about
internals (ch. 8).

## 2. Functor

### 2.1 Identity

- **Statement.** `map(x)(id) == x`.
- **Guarantees.** `map` preserves structure: only the contents change, never the shape. It may not
  raise before applying the function, drop or duplicate elements, turn a present value into an absent
  one, flip success and failure, consume extra input, or behave differently depending on the type or
  value of the contents. Consequently derived functions inherit shape facts for free: splitting a
  container of pairs into a pair of containers yields two of the same length in matching order, with
  no separate test needed (ch. 11).
- **Test.** Generate `x`; compare `map(x)(id)` with `x`. Since `map` cannot depend on the contents,
  one content type is enough; vary the structure of `x` instead (nesting depth, size, the failing and
  empty cases) (ch. 8).
- **Source.** ch. 7 (as the mapping law for `Par`), ch. 8, ch. 9 (parsers), ch. 11.

### 2.2 Composition (fusion)

- **Statement.** `map(map(x)(g))(f) == map(x)(a => f(g(a)))`.
- **Guarantees.** Two passes can be fused into one. For a parallel computation this avoids spawning a
  second task. It follows from the identity law by parametricity (a "free theorem"), so it does not
  need to be assumed separately where the language enforces parametric polymorphism (ch. 7). In
  languages where a generic function can inspect its argument at run time, test it too (adaptation).
- **Test.** Generate `x` and two functions; compare. Fixed functions such as "add one" and "double"
  are an acceptable start when function generation is unavailable.
- **Source.** ch. 7 (exercise), ch. 12 (listed among the functor laws).

### 2.3 The fuller mapping law

- **Statement.** `map(unit(x))(f) == unit(f(x))`.
- **Guarantees.** `unit` and `map` cannot inspect the value. The source derives 2.1 from this law by
  substituting `id` and reading `unit(x)` as an arbitrary `y`, and says each follows from the other.
  That holds in a setting where the only values are ones built from `unit` and parametric operations.
  As a general statement it is too strong (checked by running both ways on lists and options): a
  `map` that reverses its list satisfies 2.3, because a one-element list is its own reverse, and
  fails 2.1; a non-parametric `unit` that returns "absent" for the argument 0 satisfies 2.1 and fails
  2.3. Test both laws, not one as a stand-in for the other (reviewer correction, not in the notes).
- **Test.** Generate `x` and a function; compare under the interpreter.
- **Source.** ch. 7.

## 3. Monoid

A monoid is a type, a binary operation `op` and a value `zero` (ch. 10).

### 3.1 Associativity

- **Statement.** `op(op(x, y), z) == op(x, op(y, z))`.
- **Guarantees.** The grouping of a reduction is free: left fold, right fold and balanced fold give
  the same answer. Hence partial results from chunks, threads, shards or time windows can be combined
  in any grouping, cached and merged later. It does not license reordering; see 3.6.
- **Test.** Generate triples; compare both groupings. Run for every instance you define, including
  ones built by composition (pair, map-merge, function-valued, optional).

### 3.2 Identity

- **Statement.** `op(x, zero) == x` and `op(zero, x) == x`.
- **Guarantees.** Empty input has a well-defined answer; empty chunks do not disturb a merge; a fold
  can be seeded without changing the result.
- **Test.** Generate `x`; check both sides. Also check that folding an empty collection returns
  `zero` and that `zero` never leaks into a non-empty result (using 0 as the identity for `max` is
  the classic failure).

### 3.3 Fold equivalences (consequences worth testing directly)

- **Statement.** `foldLeft(zero)(op)`, `foldRight(zero)(op)` and a balanced split-and-combine fold
  agree; `foldMap` over the whole equals `op` of `foldMap` over any two-way split at any position.
- **Guarantees.** That the parallel or chunked implementation is equivalent to the sequential one.
- **Test.** Generate a sequence and a split index; compare whole against split. Include empty and
  single-element inputs. Compare the parallel fold against the plain fold on the same data.

### 3.4 Homomorphism

- **Statement.** For a function `f` from monoid M to monoid N:
  `N.op(f(x), f(y)) == f(M.op(x, y))`, and `f(M.zero) == N.zero`.
- **Guarantees.** You may map then combine, or combine then map. Example: the length of a
  concatenation equals the sum of the lengths.
- **When to check.** Whenever two types in your library are monoids and a function goes between them,
  ask whether it is meant to preserve the structure, and if so test it (ch. 10).
- **Test.** Generate `x`, `y`; compare both sides.

### 3.5 Isomorphism

- **Statement.** Homomorphisms `f` and `g` in opposite directions whose compositions both ways are the
  identity. Examples in the source: strings and lists of characters under concatenation; booleans
  under "or" with false, and under "and" with true, related by negation.
- **Guarantees.** The two representations are interchangeable for anything stated in monoid terms.
- **Test.** Round-trip both ways plus 3.4 for each direction.

### 3.6 What a monoid does not promise (inferred)

- Commutativity. String and list concatenation and function composition are associative and not
  commutative. Combine chunk results in the original order.
- Exact associativity for floating-point addition; parallel sums can differ in the low bits.
- An identity may be missing altogether; then you have only the associative operation. Fold non-empty
  inputs, or wrap in an optional to supply one.

## 4. Monad

A monad is one of the minimal sets of operations (`unit` + `flatMap`; `unit` + `compose`;
`unit` + `map` + `join`) satisfying associativity and identity (ch. 11). The contract says nothing
about what happens between steps beyond these laws.

### 4.1 Associativity

- **Statement (flatMap form).** `flatMap(flatMap(x)(f))(g) == flatMap(x)(a => flatMap(f(a))(g))`.
- **Statement (Kleisli form).** With `compose(f, g) = a => flatMap(f(a))(g)` for functions returning
  computations: `compose(compose(f, g), h) == compose(f, compose(g, h))`. This form shows it is the
  same shape as monoid associativity.
- **Guarantees.** The grouping of sequential steps does not matter, only their order. You can extract
  part of a chain into a named sub-computation, or inline one, without changing behaviour. The
  source's motivating case: generating an order by drawing name, price and quantity in one chain, or
  by first defining an item generator and then using it, must behave the same.
- **Test.** Generate `x` and two functions into the type; compare both sides under the type's
  equality. As a practical variant, take a real chain from the codebase, extract a middle section
  into a helper, and assert results are unchanged.
- **Proof pattern.** For a data type with constructors, split by case and simplify each side by
  substitution (for an optional type: the absent case reduces to absent on both sides; the present
  case reduces both sides to `flatMap(f(v))(g)`).

### 4.2 Left identity

- **Statement.** `flatMap(unit(y))(f) == f(y)`; in Kleisli form `compose(unit, f) == f`.
- **Guarantees.** Wrapping a plain value and feeding it onward is the same as calling the function.
  `unit` adds no effect.
- **Test.** Generate `y` and a function; compare.

### 4.3 Right identity

- **Statement.** `flatMap(x)(unit) == x`; in Kleisli form `compose(f, unit) == f`.
- **Guarantees.** Ending a chain with a trivial wrap changes nothing. Together with 4.2, trivial
  steps can be inserted or removed freely.
- **Test.** Generate `x`; compare.

### 4.4 Laws in terms of `join`, `map` and `unit`

The source leaves restating the laws in this form as an exercise, and the notes do not record the
statements. If you use `join` as a primitive, define `flatMap(x)(f) = join(map(x)(f))` and test
4.1 to 4.3 through that definition. The standard direct forms (adaptation, not from the notes; they
held on list and option in a property run) are `join(join(mmm)) == join(map(mmm)(join))`,
`join(unit(m)) == m` and `join(map(m)(unit)) == m`, where `mmm` has three layers.

### 4.5 Extra primitives carry extra laws

Each monad adds its own operations, and those have their own laws relating them to `unit` and
`flatMap`. For state (ch. 11 exercise; statements inferred): reading the state and writing it straight
back is a no-op; reading after writing `s` yields `s`.

## 5. Applicative

Primitives `unit` and `map2` (or `unit` + `apply`, or `unit` + `map` + `product`). Let
`product(a, b) = map2(a, b)((x, y) => (x, y))` (ch. 12). The source calls these sanity checks that
`unit`, `map` and `map2` behave consistently, and suggests checking them on an optional type first.

### 5.1 Functor laws

- **Statement.** 2.1 and 2.2 hold for the derived `map`.

### 5.2 Left and right identity

- **Statement.** `map2(unit(()), x)((_, a) => a) == x` and `map2(x, unit(()))((a, _) => a) == x`.
- **Guarantees.** Combining with a trivial value leaves the structure of `x` untouched. So `map`
  defined through `map2` and `unit` is structure-preserving whichever side `unit` is placed on.
- **Test.** Generate `x`; check both.

### 5.3 Associativity

- **Statement.** `product(product(a, b), c) == map(product(a, product(b, c)))(assoc)` where `assoc`
  re-nests `(a, (b, c))` as `((a, b), c)`.
- **Guarantees.** Grouping three effects either way gives the same result up to tuple shape. Without
  it you would need left- and right-leaning variants of every N-ary combiner.
- **Test.** Generate three values; compare.

### 5.4 Naturality of product

- **Statement.** `map2(a, b)((x, y) => (f(x), g(y))) == product(map(a)(f), map(b)(g))`.
- **Guarantees.** Transforming before combining equals transforming after. Refactoring that moves a
  `map` across a combine is safe.
- **Test.** Generate two values and two functions; compare.

### 5.5 Structural facts (stated as exercises in the source)

- Every lawful monad yields a lawful applicative when `map2` is defined through `flatMap`.
- The product of two applicatives is an applicative (run both in lockstep).
- The composition of two applicatives, one nested in the other, is an applicative.
- Monads do not compose generically.

### 5.6 Accumulating validation (inferred checks)

For an error-accumulating applicative: all failures are present in the result; their order matches
the order of the checks; adding an independent check never removes an earlier error.

### 5.7 A way applicative laws get broken (inferred)

If `map2` performs hidden side effects whose order matters, associativity and naturality fail.

## 6. Traversable

`traverse(xs)(f)` applies an effectful `f` to each element and returns the effect of a structure of
the same shape; `sequence` swaps a structure of effects into an effect of a structure (ch. 12).

| Law or check | Statement | Guarantees | Test |
|---|---|---|---|
| Reduces to map | Traversing with the identity effect equals `map` | Traverse generalises map; a traversable is a functor | Compare on generated structures |
| Reduces to foldMap | Traversing with the constant effect built from a monoid (`unit = zero`, `map2 = op`) equals `foldMap` | A traversable is foldable | Compare with `foldMap` for a sum or concat monoid |
| Shape preservation | The output structure has the input's shape | Traverse differs from fold exactly here: fold discards shape | Length or tree shape before and after |
| Short-circuit meaning | `sequence` over optionals is absent iff any element is absent | The effect's semantics decide the behaviour | Generate lists with and without an absent element |
| Reverse | `toList(reverse(x)) ++ toList(reverse(y)) == reverse(toList(y) ++ toList(x))` | A generic `reverse` written through state traversal is correct | Generate two structures |
| Index order (inferred) | `zipWithIndex` yields indices 0..n-1 in traversal order | The state threading visits elements once, in order | Compare indices with a range |

## 7. State actions

These are the functor and monad laws at the state-action type (ch. 6 notes list them as inferred,
ch. 11 states them generally). Equality: run from the same initial state; compare value and final
state.

- `map(unit(a))(f) == unit(f(a))`; `map(s)(id) == s`.
- `flatMap(unit(a))(f) == f(a)`; `flatMap(s)(unit) == s`; associativity of `flatMap`.
- Determinism: the same action from the same seed gives the same value and final state. This is a
  property of the pure design itself and is the reason failures are reproducible.
- Threading: two draws in one run differ, and the final state differs from the initial one. Guards
  against the reuse-old-state bug.
- Get/set (inferred): get then set is a no-op; set `s` then get yields `s`.

## 8. Parallel computations

### 8.1 Mapping

Sections 2.1 to 2.3 with equality "same value under any valid executor" (ch. 7).

### 8.2 Forking

- **Statement.** `fork(x) == x` for all `x` and all executors.
- **Guarantees.** Forking is purely a scheduling annotation: it can be added or removed without
  changing meaning. The type system cannot say where forking is safe, so general combinators such as
  a parallel map are sound only if this holds.
- **Test.** Generate `x`, preferably nested; run under generated executors including a pool of size
  one, small fixed pools and an unbounded pool; compare. The size-one pool is the test that found the
  deadlock in the first implementation. Add a stress case: very many forks on a two-thread pool,
  with a timeout so a deadlock fails the test instead of hanging it.
- **History.** Failed for fixed-size pools under the blocking representation; holds after the switch
  to a non-blocking one. The alternative was to restrict the law to unbounded pools and document it.

### 8.3 Further checks (some inferred)

A parallel map gives the same results as the plain map; `sequence` preserves order; behaviour with a
throwing function is defined and reaches the caller of `run`; thread use stays bounded. The source
leaves laws relating `join` to the other primitives as an open question.

## 9. Parsers

Equality: same outcome of `run` on every input (ch. 9).

| Law | Statement | Guarantees | Test |
|---|---|---|---|
| char | `run(char(c))(c as string)` succeeds with `c` | Base case | Generated characters |
| string | `run(string(s))(s)` succeeds with `s` | Base case | Generated strings |
| succeed | `run(succeed(a))(s)` succeeds with `a` for any `s` | `succeed` consumes nothing and never fails | Generated `a`, `s` |
| map identity | `map(p)(id) == p` | `map` examines no extra input and cannot change failure into success or back | Generated inputs; compare `run` of both |
| label | If `label(msg)(p)` fails, its error message is `msg` | Callers control the reported message | Generated inputs and messages; check only the failing cases |
| scope | If `p` fails with error stack `e`, `scope(msg)(p)` fails with `msg` on top of `e` | Context is added, inner detail kept | Same pattern |
| attempt | `or(attempt(flatMap(p)(_ => fail)), p2) == p2`, approximately | `attempt` undoes commitment, so the alternative is tried | Generated inputs. Approximate because `p2` may fold in errors from both branches |
| slice (inferred) | `run(slice(p))(s)` returns the portion of `s` that `p` matched | `slice` reports input, not structure | Compare with the matched prefix |
| repetition (inferred) | `many` agrees with `listOfN` for the count actually present | Derived repetition forms are consistent | Generated repeated inputs |
| round trip (inferred) | Parsing a printed value gives the value back | Parser and printer agree | Generate values, print, parse |

**Open questions the source leaves to the designer.** Is `or` commutative? Is it associative? Is
`product` associative (up to tuple nesting), and how do `map` and `product` interact? The answers are
choices with consequences: a commutative `or` gives up left bias, ordering-based disambiguation and
commit semantics; a non-commutative one must document its order.

## 10. Consistency between primitive and derived forms

When an operation can be defined two ways, the definitions must agree. These are cheap to test and
catch hand-optimised overrides that drift.

- `map(x)(f) == flatMap(x)(a => unit(f(a)))` (ch. 11).
- `map(x)(f) == map2(x, unit(()))((a, _) => f(a))` (ch. 7, ch. 12).
- `map2(x, y)(f) == flatMap(x)(a => map(y)(b => f(a, b)))` for a monad (ch. 11). Note the meaning
  differs where the type has a separate parallel or accumulating `map2`: then this equation is a
  design decision, not a given (ch. 7 leaves it as an open question for `Par`).
- `apply(fab)(x) == map2(fab, x)((f, a) => f(a))` and `map2(x, y)(f) == apply(map(x)(curried f))(y)`
  (ch. 12).
- `join(xx) == flatMap(xx)(id)` and `flatMap(x)(f) == join(map(x)(f))` (ch. 11).
- `sequence(xs) == traverse(xs)(id)`.

## 11. Turning a law into a test

1. Write a helper `equal(lhs, rhs, env)` that implements the type's equality.
2. Write generators for the type's values. Cover the structural cases: empty, failing, single,
   nested, large.
3. For laws that quantify over functions, either generate functions (see
   `property-based-testing.md`) or use a small fixed family that includes identity, a constant
   function, and one that depends on its argument.
4. One property per law, each labelled, so a failure names the law.
5. Generate the environment too (pool size, seed, input size).
6. Keep the law tests independent of the representation so they survive rewrites.

Sketch (TypeScript with a property-testing library; adaptation):

```ts
const monadLaws = <A>(name: string, genM: Gen<M<A>>, genA: Gen<A>, genF: Gen<(a: A) => M<A>>) => [
  prop(`${name}: left identity`,  genA, genF, (a, f) => equal(flatMap(unit(a), f), f(a))),
  prop(`${name}: right identity`, genM,       (m)    => equal(flatMap(m, unit), m)),
  prop(`${name}: associativity`,  genM, genF, genF, (m, f, g) =>
    equal(flatMap(flatMap(m, f), g), flatMap(m, a => flatMap(f(a), g)))),
];
```

## 12. Which laws to test for which type

| Your type offers | Test |
|---|---|
| `map` | 2.1 (and 2.2 if generic code can inspect values) |
| `zero`/`empty` and a combine | 3.1, 3.2, 3.3; 3.4 for each structure-preserving function |
| `unit` and `map2`/`zip`/`all` | 5.1 to 5.4; 5.6 if it accumulates errors |
| `unit` and `flatMap`/`then`/`andThen` | 4.1 to 4.3 and the first three rows of section 10 |
| `traverse`/`sequence` | Section 6 |
| A scheduling or annotation operation meant to be meaning-free | A law of the form `annotate(x) == x`, under hostile environments (8.2) |
| Operations that set messages, context or options | A law saying the setting is observable in the result (section 9, label and scope) |
| Get/set style accessors | The pair of laws in 4.5 |
