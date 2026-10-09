# Language mappings

How the ideas in this skill look in mainstream languages and how they degrade where a feature is
missing. The source is written in Scala; almost everything in this file is adaptation, and where the
study notes supply a mapping it is marked there as inferred. Treat library names as pointers to check
against the project's dependencies, not as claims about current APIs. "FPiS" is Functional
Programming in Scala, 1st ed.

## Contents

- What the method needs from a language
- Abstract interface before representation
- Descriptions and interpreters; eager and lazy substrates
- Laziness of later arguments
- Stack safety
- Sum types and pattern matching
- Operator syntax
- The abstractions without higher-kinded types
- Names by language: functor, applicative, traversable, monad
- Monoid and folds by language
- Accumulating validation
- Sequencing syntax
- Property-testing libraries
- Parser-combinator libraries
- Per-language notes
- Where the functional form costs more than it gives

## What the method needs from a language

| Need | Used for | If missing |
|---|---|---|
| First-class functions and closures | Every combinator | No mainstream target lacks them |
| Generics | Typed `map2`, typed results | Untyped trees or run-time checks |
| A way to defer evaluation | Descriptions, lazy later arguments, recursive definitions | Explicit thunks `() => X` |
| Sum types with exhaustive matching | Result types such as passed/falsified/proved, success/failure | Tagged unions, sealed hierarchies, or a struct with a tag and a switch |
| Tuples or records | State actions returning value and next state | Small structs |
| Higher-kinded types | One generic `Monad`/`Applicative`/`Traverse` interface | Per-type operations with shared names and laws |
| Chaining syntax | Readable dependent sequences | Method chains, early return, or plain step functions |
| Tail-call elimination or trampolines | Deep recursion in repetition | Loops |

Higher-kinded types are not needed to define the combinators for one concrete type; they are needed
only to abstract over all such types (FPiS ch. 6 notes).

## Abstract interface before representation

The parser chapter declares its interface generic over the parser type so that client code compiles
before any implementation exists (FPiS ch. 9).

| Language | Closest form |
|---|---|
| TypeScript | An `interface Parsers<P>`-style record of functions is not expressible over a type constructor; use an opaque branded type `Parser<A>` exported from a module with the constructor hidden, and write clients against the exported functions |
| Rust | A trait with associated types, or an opaque `struct Parser<A>` with private fields; `impl Trait` in return position hides representations |
| Kotlin, Java, C# | A generic interface or abstract class `Parser<A>` with package-private or internal implementation |
| Swift | A protocol with associated types, or a struct with a private stored closure |
| Python | A class with a private callable and a `Protocol` for typing; convention does the hiding |
| Go | An interface type or a struct with unexported fields; generic functions over `Parser[A]` |

The goal is the same in each: clients cannot see or depend on the representation, so you can replace
it. Compiling a client before the implementation exists is possible wherever stubs type-check
(`declare function` in TypeScript, `todo!()` in Rust, `TODO()` in Kotlin, `raise NotImplementedError`
with type hints in Python).

## Descriptions and interpreters; eager and lazy substrates

The method wants "constructing a computation runs nothing" (FPiS ch. 7). Whether the platform's async
value satisfies that differs.

| Language | Native async value | Starts when | To get a description |
|---|---|---|---|
| TypeScript/JavaScript | `Promise` | Created | Use a thunk `() => Promise<A>`, or a task/effect type from a library |
| Java | `CompletableFuture` | Created/supplied | `Supplier<CompletableFuture<A>>` |
| Kotlin | `Deferred` from `async` | Created (unless lazy start) | A `suspend` lambda; run within a scope |
| C# | `Task` | Usually when created | `Func<Task<A>>` |
| Python | Coroutine object | Awaited or scheduled | Already lazy; do not wrap it in a task until the edge |
| Rust | `Future` | Polled | Already lazy |
| Swift | `async` function call | Awaited; `Task {}` starts at once | Pass the `async` closure, not a `Task` |
| Go | No future type | A goroutine starts at `go` | A `func(ctx) (A, error)` value run by a group at the edge |

Combination forms: `Promise.all`, `asyncio.gather`, `join!`, `CompletableFuture.allOf`, `async let`,
`awaitAll`, `Task.WhenAll`, `errgroup` are the independent (`map2`/`sequence`) form; a run of `await`
statements or `then` chains is the dependent form.

**Degradation.** On an eager substrate you cannot state "`unit` is not yet running" or "`map2` does
not start anything". Either wrap in a thunk and keep the algebra, or keep the eager type and replace a
law like `fork(x) == x` with documentation of what starts when. Whichever you pick, errors must reach
the caller of the interpreter and continuations must always fire; the source leaves that as an
unfinished part of its own implementation.

The deadlock the source's forking law exposed (a pooled task blocking on another pooled task) is
reproducible on any bounded pool: blocking `get`/`join`/`.Result`/`block_on` inside pool work. Test
with a pool of size one.

## Laziness of later arguments

Scala's by-name parameters make the second argument of "then" and "or else" lazy. Elsewhere:

- Pass a thunk: `or(p1, () => p2)`; `lazy(() => expr)` for recursive grammar rules.
- Rust: closures or function pointers; recursive parsers usually need boxing or a function item.
- Python: a `lambda`, or a forward-declaration object filled in later.
- Kotlin: a lambda parameter, or a `lazy` value for a recursive rule. Swift: `@autoclosure` gives a
  by-name-like call site.
- C#: `Func<T>` or `Lazy<T>`.

Recursive definitions (an expression containing a parenthesised expression) need this in every strict
language regardless of other design choices.

## Stack safety

The source's parser overflows on large inputs because repetition recurses, and suggests a specialised
stack-safe repetition since every repetition form can be defined through `many` (FPiS ch. 9
footnote).

- No mainstream target here guarantees tail-call elimination in general (Scala and Kotlin optimise
  marked self-recursion; Swift and Rust may but do not promise it; JavaScript engines mostly do not;
  Python, Java, Go and C# do not).
- Write repetition and folds as loops inside the primitive. Local mutation there is fine: it is not
  observable through the interface.
- For deeply nested `flatMap` chains built by recursion, use the platform's async machinery (which is
  already heap-allocated) or a trampoline; see `fp-effects-and-streams`.
- Test with ten thousand or more elements and with deep nesting.

## Sum types and pattern matching

| Language | Result-like types |
|---|---|
| Rust | `enum` with `match`; exhaustive |
| Swift | `enum` with associated values; exhaustive `switch` |
| Kotlin | `sealed interface`/`sealed class` with `when`; exhaustive when used as an expression |
| TypeScript | Discriminated unions with a `kind` tag; exhaustiveness via a `never` check |
| Python | `@dataclass` variants with `match` (3.10+); a type checker enforces exhaustiveness |
| Java | `sealed` interfaces and `record`s with pattern `switch` (recent versions) |
| C# | Records with pattern matching; no closed unions in older versions, so add a default that throws |
| Go | A struct with a tag field, or an interface with a type switch; no exhaustiveness check |

Without exhaustiveness checking, keep result types small and add a test that each case is handled.

## Operator syntax

The source uses infix operators for choice, product and repetition. Where operator overloading exists
(Python, Kotlin, Swift, Rust, C#) use it sparingly and only with conventional meanings. Elsewhere use
named functions and method chaining. Keep one primary definition of each operation and have any sugar
delegate to it (FPiS ch. 9).

## The abstractions without higher-kinded types

Haskell and Scala can write one `Monad` interface for all container types. Encodings exist for
TypeScript and Kotlin in functional libraries. Java, Go, Rust, Python, Swift, C# and plain TypeScript
cannot express it directly.

What to do instead:

1. Give each of your types the operations it supports, with the conventional names for the language.
2. Hold each to the same laws and reuse one parameterised law-test helper across types.
3. Write the small derived functions (`sequence`, `traverse`, `map2` from `flatMap`) per type. They
   are a few lines each.
4. Do not build an emulated higher-kinded encoding in application code unless the team already uses
   a library built on one. The readability cost is high and the duplication saved is small.

What is lost: writing a function once for every monad or applicative. What is kept: the laws, the
vocabulary, the decision between independent and dependent combination, and safe refactoring.

Partial application of a two-parameter type (fixing the state type of a state action) is ordinary in
these languages: define the type with the state fixed, or close over it.

## Names by language: functor, applicative, traversable, monad

| Idea | TypeScript/JS | Python | Rust | Kotlin | Java | Go | Swift | C# |
|---|---|---|---|---|---|---|---|---|
| `map` | `map`, `then` (on promises, with a value-returning callback) | `map`, comprehensions | `map` | `map`, `let` | `map`, `thenApply` | hand-written generic `Map` | `map` | `Select` |
| `unit` | `Promise.resolve`, `of`, literal | constructor | `Some`, `Ok`, `ready` | constructor, `just` | `Optional.of`, `completedFuture` | constructor | `.some`, `.success` | `Task.FromResult` |
| `flatMap` | `flatMap`, `then` (with a promise-returning callback), `await` | nested comprehension, `await` | `and_then`, `flat_map`, `?` | `flatMap`, `?.let`, suspend calls | `flatMap`, `thenCompose` | explicit `if err != nil` sequencing | `flatMap`, `try`, `await` | `SelectMany`, `await` |
| `map2`/product | `Promise.all`, tuple of results | `zip`, `asyncio.gather` | `zip`, `join!` | `zip`, `awaitAll` | `thenCombine`, `allOf` | `errgroup` plus collection | `zip`, `async let` | `Zip`, `Task.WhenAll` |
| `sequence`/`traverse` | `Promise.all(xs.map(f))` | `gather(*map(f, xs))`, list comprehension with early return | `iter().map(f).collect::<Result<Vec<_>, _>>()`, likewise into `Option<Vec<_>>` | `map { }` in a coroutine scope; library `traverse` | stream `map` then collect; `allOf` then join | loop with error return | `map` with `try`; task group | `Select` then `WhenAll` |
| traverse with state | `reduce`, index argument of `map` | `enumerate`, `itertools.accumulate` | `scan`, `enumerate`, `fold` | `runningFold`, `withIndex` | stream reduce (awkward), loop | loop | `enumerated`, `reduce(into:)` | `Aggregate`, `Select` with index |

Caveats worth knowing when testing laws on native types:

- JavaScript promises flatten automatically: resolving a promise with a promise yields one layer, and
  `then` acts as both `map` and `flatMap`. The functor and monad laws therefore fail for values that
  are themselves promise-like. Avoid nesting; do not expect the laws to hold there (inferred in the
  notes).
- Rust's `collect` into `Result<Vec<_>, _>` is a traverse that short-circuits on the first error. It
  does not accumulate.
- `Promise.all` rejects with the first rejection and reports no others, so it is the independent
  form but not the accumulating one; `Promise.allSettled` and Python's
  `asyncio.gather(..., return_exceptions=True)` return every outcome, and you collect the errors
  from those (adaptation).
- Optional chaining with nested scope functions is the dependent form; a flat `zip` is the
  independent form.

## Monoid and folds by language

Where there is no typeclass mechanism, pass the monoid explicitly as a pair or record of `zero` and
`op`. The source does the same (`foldMap(xs, m)(f)`) (FPiS ch. 10).

| Language | Fold | Carrying a monoid |
|---|---|---|
| TypeScript | `reduce(op, zero)` | `{ empty: A, concat: (x: A, y: A) => A }` |
| Python | `functools.reduce(op, xs, zero)`; `sum`, `any`, `all`, `min`, `max` | A small dataclass or two arguments; `collections.Counter` merges with `+` but drops zero and negative counts, so it is a lawful monoid only when every count is positive (with `Counter(a=1) + Counter(a=-3) + Counter(a=3)` the two groupings give 3 and 1); `Counter.update` or a `dict` merge does not drop them |
| Rust | `Iterator::fold`; `sum` and `product` through traits | A trait with `empty` and `combine`, or `Default` plus `Add`/`Extend` |
| Kotlin | `fold(zero, op)` | An interface, or a pair |
| Java | `Stream.reduce(identity, op)` | `identity` plus `BinaryOperator`; `Collector` for richer summaries |
| Go | A loop or a generic `Fold` helper | A struct with `Empty` and `Combine` |
| Swift | `reduce(zero, op)` | A protocol with a static `empty` and a `combine` |
| C# | `Aggregate(zero, op)` | An interface or two delegates |

Notes:

- Parallel reducers in standard libraries (Java parallel streams' `reduce`, data-parallel iterator
  libraries, map-reduce and stream-processing frameworks) require exactly an identity and an
  associative operation. A wrong identity or a non-associative combine yields results that vary with
  the split.
- Summary-type aggregation (count and sum for a mean) maps onto "accumulator plus finisher" APIs such
  as Java's `Collector` or a fold followed by a projection.
- Building strings by repeated concatenation in a fold is quadratic for immutable strings; use a
  builder or join. The source's point about balanced folds is the same observation.
- Floating-point sums differ in low bits between groupings; test with a tolerance or on integers.

## Accumulating validation

The source's validation type collects errors with `map2`, where a fail-fast result type built on
`flatMap` stops at the first (FPiS ch. 12). Mechanics of the type belong to `fp-data-and-errors`.
Pointers from the notes:

- Schema validators that return all issues at once behave as the accumulating applicative (schema
  libraries in TypeScript and Python are named in the notes as examples).
- Kotlin and Java functional libraries offer a validated type or an accumulate-on-zip operation.
- Rust's `Result` short-circuits; to accumulate, collect errors into a vector by hand or use a
  validation crate.
- With none available, write `map2` for `Result<A, List<E>>` yourself: two failures concatenate, one
  failure passes through, two successes apply the function. Then N-ary versions follow.

## Sequencing syntax

A chain of `flatMap` is what these express: Scala `for`, Haskell `do`, `async`/`await`, Rust's `?`,
Kotlin suspend functions, C# query syntax, Python generators used as coroutines. Prefer the native
form to nested callbacks. Remember that each is the dependent form: steps written one after another
with `await` or `?` run in sequence and stop at the first failure, even when they are independent.

Where there is no such syntax for your type (a custom state action in Go, Java or Python), a
combinator chain becomes verbose. Use an immutable state record and plain step functions
`(state, input) -> (state, output)` folded over the inputs; it is the same idea with less machinery
(FPiS ch. 6 notes, inferred).

## Property-testing libraries

Named in the notes (inferred): Hypothesis (Python); fast-check (TypeScript/JavaScript); proptest and
quickcheck (Rust); jqwik and junit-quickcheck (Java); kotest-property (Kotlin); rapid and gopter (Go);
ScalaCheck; QuickCheck. Check the project's existing test dependencies before adding one.

What a language needs: generators as first-class values or classes, generics for typed generators
(dynamic languages use untyped ones), a seedable random source, and closures for generated functions.
If no library is available, hand-roll `gen(rng, size) -> value` functions and a loop that increases
`size`, printing the seed on failure.

## Parser-combinator libraries

Named in the notes (inferred): parsimmon and combinator-style use of chevrotain (TypeScript); parsy,
pyparsing, funcparserlib (Python); nom, chumsky, combine (Rust); jparsec (Java); parsec and megaparsec
(Haskell). Correspondences given there: nom's `alt` is choice and its `cut` is commit; parsec's `try`
is `attempt` and its `<?>` is `label`.

The same design applies beyond parsing: schema decoders, validators, routers, query builders,
command-line argument parsers, configuration loaders and test generators all use
map/flatMap/or/many/label/scope, with scope giving path-aware errors (inferred).

## Per-language notes

**TypeScript.** Discriminated unions and closures cover everything except higher-kinded types. Hide
representations behind module boundaries. Wrap promises in thunks when you need descriptions. Do not
test monad laws on raw promises with promise values.

**Python.** Dynamic typing means laws are your only contract; property tests matter more. Coroutines
are lazy descriptions until scheduled. Recursion depth is limited: write loops in primitives.

**Rust.** Ownership prevents reusing a consumed state value, which removes the reuse-old-state bug at
compile time when state is moved and not copied (inferred). Futures are lazy. Closures have distinct
types, so combinator libraries lean on generics or boxing; expect longer signatures. No
higher-kinded types: per-type `map`/`and_then`.

**Kotlin.** Sealed types, extension functions and suspend lambdas fit the method well. Functional
libraries provide validated types and traverse if the project already depends on one.

**Java.** Records and sealed interfaces (recent versions) give sum types. `Optional` and
`CompletableFuture` have `map`/`flatMap`-style methods; `CompletableFuture` is eager. Generic
combinators are verbose; keep the primitive set small.

**Go.** Generics allow `Map`/`Fold` helpers but method chaining over generic types is limited and
there are no sum types. Combinator style is costly here. Keep the parts that travel: values describing
work run by one function that takes a context; explicit `(zero, combine)` for aggregations; step
functions for state; table-driven and property tests for laws.

**Swift.** Enums with associated values, protocols with associated types, `@autoclosure`, and
`async let` for independent combination. No higher-kinded types.

**C#.** LINQ query syntax is the dependent-sequencing sugar for any type with `Select`/`SelectMany`.
`Task` is usually hot; use `Func<Task<T>>` for descriptions. Records and pattern matching cover result
types.

## Where the functional form costs more than it gives

- **Generic effect interfaces in languages without higher-kinded types.** Use per-type operations.
- **A combinator DSL where a native construct exists.** Do not rebuild `async`/`await`, iterator
  adapters or the standard optional chaining under new names.
- **Heavy closure composition in hot paths** in languages where closures allocate or defeat inlining.
  Measure; make the hot operation a primitive with a loop inside, which the method allows.
- **Custom state or reader types** where the team's idiom is to pass a parameter. Pass the parameter;
  keep the function pure.
- **Operator-heavy syntax** in codebases whose readers do not know it. Named functions cost a few
  characters and save explanations.
- **Lazy descriptions over an eager ecosystem.** If every library the code touches returns running
  futures, a thunk layer at your boundary may be all that is practical; document the semantics
  instead of pretending the law holds.
- **Go and similar languages.** Apply the design ideas (description plus interpreter, explicit
  resources, laws as tests, mergeable aggregates) in the language's plain style.

In each case keep the parts that are free in any language: the call site designed first, one job per
operation, explicit resources, stated laws, and property tests that check them.
