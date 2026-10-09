# Language mappings and degradation

The book is Scala; this file maps its ideas for data and failure to eight mainstream languages. All of it is adaptation, not the book's text. Cells marked (notes) were suggested in the study notes (themselves inferred, not the book's); unmarked cells and version numbers were added by the skill's author from general knowledge of each language and are not from the notes. Language features move between versions: confirm the feature exists in the version the repository targets before using it, and prefer what the repository already uses.

## Contents

1. What each idea needs from a language
2. Sum types and exhaustive matching
3. Immutability and persistent collections
4. Loops, recursion and tail calls
5. Folds
6. Option and Result
7. Propagation, traverse and accumulation
8. Laziness, thunks and generators
9. Language notes
10. Degradation summary

## 1. What each idea needs

| Idea | Needs | If missing |
|---|---|---|
| ADT and exhaustive matching | sum types, product types, a coverage check | tag plus switch, default branch that fails, a test per variant |
| Immutable data | immutable bindings and records, persistent collections | copy-on-write, builders, freeze at the boundary |
| Loops as state-passing | closures; ideally self tail calls | local `while` with local variables |
| Folds, higher-order functions | first-class functions, generics | codegen or loops |
| Option / Result | sum types or tagged unions, generics, closures (notes) | struct with `ok`/`error` fields and discipline (notes) |
| map / flatMap chains | closures; a short propagation syntax helps | explicit `if err != nil` |
| Generic over all containers (Applicative, Traverse) | higher-kinded types | write per type (notes) |
| Laziness | closures, a memo cell, lazy iterators | thunks as lambdas, explicit cache |

## 2. Sum types and exhaustive matching

| Language | Encoding | Coverage check |
|---|---|---|
| TypeScript | discriminated union (`{tag: "leaf"} \| {tag: "branch"}`) (notes) | `switch` on the tag with a `never` assignment in `default` |
| Python | frozen dataclasses plus `Union`; `match` statements from 3.10 (notes) | type checker (mypy, pyright) with `typing.assert_never` in the final branch (3.11+; `typing_extensions` earlier); otherwise a test per variant |
| Rust | `enum` with payloads; recursive variants need `Box` | `match` without wildcard; compiler enforces |
| Kotlin | `sealed interface` plus data classes (notes) | `when` used as an expression over the sealed type |
| Java 17+ | sealed interfaces plus records (notes); older: abstract class plus subclasses plus visitor | a `switch` with type patterns over a sealed type is checked for exhaustiveness without `default` from Java 21 (preview in 17 to 20, so on 17 expect `instanceof` chains or a visitor); check the project's version |
| Go | interface plus one struct per variant plus type switch (notes) | none from the compiler; add a lint, or a visitor, and a test per variant |
| Swift | `enum` with associated values; recursive cases need `indirect` | `switch` must be exhaustive |
| C# | records and an abstract base class; `switch` expressions (check version) | the compiler warns on a non-exhaustive `switch` expression over enums, bools and similar, but cannot treat an ordinary class hierarchy as closed (to my knowledge; newer versions may add closed or union types, so check): end the switch with an arm that throws, and add a test per variant |

## 3. Immutability and persistent collections

| Language | Immutable bindings and records | Persistent collections or fallback |
|---|---|---|
| TypeScript | `const`, `readonly`, `as const`; `Object.freeze` for runtime | Immutable.js (notes); otherwise spread/copy accepting O(n) |
| Python | `@dataclass(frozen=True)`, tuples, `frozenset` | the third-party `pyrsistent` library offers persistent vector, map and set (only if the project already depends on it); otherwise copy |
| Rust | bindings immutable by default; ownership prevents aliasing mutation | `im` crate (notes); `Arc` for sharing (notes); `Vec` clone otherwise |
| Kotlin | `val`, data classes with `copy` (notes), read-only collection interfaces | persistent collections library (notes); copy otherwise |
| Java | `final`, records, `List.of`, unmodifiable wrappers (views do not freeze the underlying list) | vavr persistent collections (check); copy otherwise |
| Go | no immutability in the type system; pass by value for small structs; copy slices | copy; keep mutation inside one function |
| Swift | `let`, structs with value semantics | value-type copy-on-write is built in for standard collections |
| C# | `readonly`, records, `init` setters (C# 9) | `System.Collections.Immutable`: `ImmutableList` and `ImmutableDictionary` are tree-based and share structure; `ImmutableArray` copies on every change, so use it for build-once, read-many data (with its builder). Check the package is referenced on older targets |

Rule across all: copying inside a loop is a hidden O(n^2); use a local builder and freeze at the end.

## 4. Loops, recursion and tail calls

Self tail-call elimination (notes, inferred): guaranteed in Scala (`@tailrec`), Kotlin (`tailrec`), Haskell, OCaml, Scheme, Erlang/Elixir; Clojure via `recur`. Not guaranteed in Java, Python, JavaScript, Go, Rust, C#. Swift is not covered by the notes; do not assume it.

In the languages without a guarantee write the loop form:

```python
def fib(n):                 # the state-passing helper, written as a local loop
    prev, cur = 0, 1
    for _ in range(n):
        prev, cur = cur, prev + cur
    return prev
```

The variables are local and invisible to callers, as the book accepts. Verify with a large input (100k to 1M) rather than trusting inspection.

## 5. Folds

| Language | Left fold | Notes |
|---|---|---|
| TypeScript/JS | `Array.prototype.reduce` (always pass an initial value) | `reduceRight` is a native loop and did not overflow on 5 million elements in Node 22 (the notes' claim that it is not stack-safe did not reproduce); a hand-written recursive right fold, or `Math.max(...bigArray)` spreading, does overflow |
| Python | `functools.reduce`; often `sum`, `any`, `all`, `min`, `max`, `itertools.accumulate` | early exit via `any`/`all`/`next(gen, default)` |
| Rust | `Iterator::fold`; `try_fold` for early exit with Result/Option | iterators are lazy |
| Kotlin | `fold`, `reduce`, `runningFold` | `Sequence` for laziness |
| Java | `Stream.reduce`, collectors | `Stream` is lazy |
| Go | a `for` loop; generics-based helpers after 1.18 | a loop is idiomatic; do not force a fold library in |
| Swift | `reduce`, `reduce(into:)` | `lazy` collections |
| C# | `Aggregate`; LINQ | LINQ queries are deferred |

Use the named function (`map`, `filter`, `sum`, `any`, `groupBy`) when it exists; the fold is the derivation.

## 6. Option and Result

| Language | Option | Result / Either |
|---|---|---|
| TypeScript | `T \| undefined` with `strictNullChecks` (notes); fp-ts `Option` | discriminated union `{ok:true,value} \| {ok:false,error}` or neverthrow, fp-ts `Either` (notes) |
| Python | `Optional[T]` hint with a type checker (notes); the `returns` library (notes) | exceptions are idiomatic; use result values at API boundaries and for expected failures only (notes) |
| Rust | `Option<T>` | `Result<T,E>`; `ok_or` converts Option to Result (notes) |
| Kotlin | nullable types | stdlib `Result`; Arrow `Either` (notes) |
| Java | `Optional` (commonly kept to return values; a convention, not from the notes) | vavr `Either` / `Try` (notes) |
| Go | pointer or `(T, bool)` | `(T, error)` as a manual Either; no map/flatMap, so chains use `if err != nil`; keep error values typed via sentinel or wrapped errors (notes) |
| Swift | `Optional` | `Result`; `throws` (typed throws appear in Swift 6, per the notes) |
| C# | nullable reference types | no standard Result; a library or a hand-rolled type |

The cheap Option is the compiler-enforced nullable: TS strict, Kotlin, Swift, Rust. Unchecked null in Java, Python and JS without strict tooling loses the benefit of being forced to handle the missing case (notes).

## 7. Propagation, traverse and accumulation

| Idea | Idiom |
|---|---|
| flatMap chain | Rust `?`; Kotlin/Swift optional chaining and `guard let`; Haskell `do`; Scala for-comprehension; C#/JS async/await is the same shape for futures (notes) |
| map2 (independent pair) | Rust `Option::zip`; Promise `Promise.all` for two; flat `zip` rather than nested `let` (notes) |
| traverse, fail-fast | Rust `iter().map(f).collect::<Result<Vec<_>,E>>()` and `Option<Vec<_>>`; Swift `try xs.map(f)` with a throwing closure (not `compactMap`, which drops the failures instead of failing); Kotlin Arrow `traverse` (notes; the Arrow API has changed between versions, check) |
| traverse, concurrent | `Promise.all(xs.map(f))`; Python `asyncio.gather(*map(f, xs))`; Java `CompletableFuture.allOf` plus join (notes) |
| Accumulating validation | Zod `safeParse` and Pydantic collect all issues; Kotlin Arrow `zipOrAccumulate` (older Arrow: `Validated`, deprecated in recent versions); Java Vavr `Validation`; Cats `Validated` (notes). In Rust write a small collector or use a validation crate |

To accumulate by hand in any language: run all checks, partition into successes and failures, return the failures concatenated if any exist, otherwise build the value from the successes.

## 8. Laziness, thunks and generators

| Language | Thunk | Memo | Lazy sequence |
|---|---|---|---|
| TypeScript/JS | `() => expr` | closure with cached value (notes) | generator functions, iterators |
| Python | `lambda: expr` | `functools.cache` on a zero-argument function (3.9+; it caches by arguments, so it is a memo for a thunk only when there are none); `functools.cached_property` (3.8+) for a method | generators, `itertools` |
| Rust | closure `impl FnOnce() -> T` (notes) | `OnceCell` (std since 1.70), `LazyLock` (std since 1.80) (notes name both) | `Iterator` adapters are lazy; `successors`, `from_fn` for unfold |
| Kotlin | lambda | `lazy {}` (notes) | `Sequence`, `generateSequence` |
| Java | `Supplier<T>` | hand-written holder | `Stream`, `Stream.iterate`/`generate` |
| Go | `func() T` (notes) | `sync.Once` | range-over-func iterators (`iter.Seq`, Go 1.23+); a channel-based generator leaks its goroutine if the consumer stops early, so give it a cancel path |
| Swift | closure, `@autoclosure` for by-name-like parameters | `lazy var` (notes) | `lazy` sequences |
| C# | `Func<T>` | `Lazy<T>` (notes) | `IEnumerable<T>` with `yield return`; LINQ is deferred (notes) |

Unfold is a generator with explicit state in every language above.

## 9. Language notes

- TypeScript: `T | undefined` needs `strictNullChecks`. Narrowing replaces pattern matching. For tagged unions put the tag first and keep it a string literal.
- Python: exceptions are idiomatic; follow the project's convention. Use result types at boundaries and expected failures; keep `raise` for bugs. `match` is available from 3.10.
- Rust: `Result` and `?` already give the idiom; do not wrap them in another layer. Recursive enums need `Box`.
- Kotlin: nullable types and sealed classes cover most of this without libraries.
- Java: `Optional` for return values; sealed types and records for ADTs where the version allows. Checked exceptions do not compose with lambdas (the notes' reason for not using them in generic code).
- Go: do not import a functional style wholesale. `(T, error)`, typed errors and small loops are the local idiom; apply sum-type discipline with an interface and a type switch plus a test.
- Swift: `Optional`, `Result` and enums with associated values are the idiom; recursive enums need `indirect`.
- C#: records, pattern-matching `switch` expressions, nullable reference types, the immutable collections package. Check the language version before suggesting a feature.

## 10. Degradation summary

- No sum types: tagged struct, discipline, a test per variant.
- No exhaustiveness check: a default that throws, plus tests.
- No tail calls: local loops.
- No laziness: thunks as lambdas and an explicit memo cell, or use the language's iterator machinery.
- No higher-kinded types: per-type combinators; test laws per type.
- No generics (Go before 1.18): `interface{}` or code generation (dated).
- No persistent collections: copy-on-write or builder-then-freeze; watch for loops.
- No pattern matching: accessors and branch per variant.
