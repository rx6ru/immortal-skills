---
name: fp-data-and-errors
description: Functional handling of data and failure, language-independent (TypeScript, Python, Rust, Kotlin, Java, Go). Covers immutable data with sharing, sum and product types with exhaustive matching, folds and higher-order functions instead of hand-written loops and recursion, stack safety, Option/Result values instead of exceptions or sentinels, fail-fast versus accumulate-all validation, and lazy sequences. Use when modelling a closed set of variants, replacing null, -1 or thrown errors with typed results, reviewing collection loops, fixing recursion stack overflows, validating a form or config and reporting every problem, turning a list of fallible calls into one fallible list (sequence, traverse, Promise.all), building early-exit pipelines, or generating sequences from state. Purity and effect separation belong to `fp-pure-core`, laws and monad design to `fp-api-design-with-laws`.
---

# Functional data and errors

## Purpose

This skill changes how you shape data and failure in code you write or review. Data becomes immutable values drawn from a closed set of cases that the compiler or a test can check. Loops become folds or small state-passing functions. Failure becomes a value in the return type that callers must acknowledge, and independent validations report every problem together. Laziness is used on purpose: for early exit, for unbounded or large sequences, and for sequences generated from a state step.

The source is a Scala book, but nothing here needs Scala. Where the host language lacks a feature (sum types, tail calls, laziness, higher-kinded types), each reference file says how the idea degrades and what to do instead.

## Choose what applies

| Situation in front of you | Do this | Read |
|---|---|---|
| A concept has a fixed set of variants (states, message kinds, AST nodes, results), currently flags, nullable fields, or class hierarchies with type checks | Model as a sum of products; match exhaustively | `references/algebraic-data-types.md` |
| Callers copy collections defensively, or a "modifying" function mutates its input; many readers share one value; need undo or snapshots | Immutable data with sharing; pick the structure to match the operations | `references/immutable-data-and-sharing.md` |
| Loop with mutated accumulators, or recursive function over a list/tree; two functions that differ only in a constant and an operator | Generalise to a fold; state-passing loop; check stack safety | `references/folds-and-recursion.md` |
| Two functions identical except for one inner operation or one concrete type; adapting a function to a callback signature; stuck on how to implement a generic function | Extract a function or type parameter; follow the types | `references/higher-order-and-types.md` |
| Function returns null, -1, NaN, empty string, or throws for an ordinary "no answer" or "bad input" | Option or Result in the return type; wrap throwing APIs once at the boundary | `references/typed-errors.md` |
| Several fallible steps chained; a list of fallible calls to combine; catching exceptions to continue a pipeline | map / flatMap chaining, `map2`, sequence, traverse | `references/typed-errors.md` |
| Validating a form, request body, config file or CSV row with several independent fields and users should see all problems | Accumulating validation, not a fail-fast chain | `references/validation-accumulation.md` |
| Independent async calls awaited one after another | Combine as independent (`Promise.all` family) rather than as a dependent chain | `references/validation-accumulation.md` |
| Multi-stage map/filter pipeline on large or unbounded data; need first match only; sequence generated from a counter, cursor or backoff schedule; argument expensive and rarely needed | Lazy pipeline, thunk, memoisation, unfold | `references/laziness-and-streams.md` |
| Unsure how an idiom is spelled in the language at hand, or the language lacks the feature | Look up the mapping and the fallback | `references/language-mappings.md` |

This does not apply when:

- The task is about separating I/O and state from logic, injecting time or randomness, or describing effects as values: use `fp-pure-core` or `fp-effects-and-streams`.
- You are asked to design a composable library from laws (monoid, functor, monad, property-based checking of laws): use `fp-api-design-with-laws`.
- The code is a small script, a one-off, or a codebase whose conventions are deliberately imperative and exception-based, and the user asked for a narrow change. Apply only the parts that remove a real defect (for example, a null return that has already caused a crash), and match local style for the rest.
- The failure is a programmer bug or an unrecoverable condition. Crashing is right; see "Typed errors or exceptions" below.

## How to apply

### 1. Model data as a closed set of cases

1. List the distinct variants of the concept. For each, list the fields that exist only in that variant. A field that is meaningful only in some states is a sign the variants are not separated yet.
2. Write each variant as a product (a record with its fields) and the concept as a sum (a tagged union, sealed hierarchy, or enum with payloads).
3. Write one function per operation with one branch per variant. Make the compiler check coverage (exhaustive `match`, `when` over a sealed type, a `never` check in TypeScript, `match` with no catch-all in Rust). Where the language cannot check, the default branch must fail loudly, and a test must reach each variant.
4. Do not add a catch-all branch to a match over your own type: it silently swallows the next variant someone adds.
5. If values must satisfy an invariant (non-empty, validated, sorted), immutability alone does not give you that. Hide the raw constructor behind a smart constructor that returns a Result or Option (see `typed-errors.md`). Open constructors are fine when any combination of fields is valid.

Details, fold-per-type recipe and the encoding per language: `algebraic-data-types.md`.

### 2. Replace a loop or hand recursion with a fold

1. Write the loop's mutated variables down. Those are the accumulator.
2. If a built-in with a name exists (`map`, `filter`, `sum`, `any`, `all`, `find`, `groupBy`), use it. The fold is how you derive the function; the named function is what readers should see.
3. Otherwise write `fold(items, initial, combine)`. The initial value is the answer for empty input. `combine` takes the accumulator and one element and returns the new accumulator. The accumulator type may differ from the element type.
4. If you need to stop early, a plain fold cannot (the strict version always visits everything). Use `any`/`all`/`find`, an early-exit loop, or a lazy pipeline.
5. If the language has no guaranteed tail-call elimination, write the same state-passing function as a local `while` loop whose variables never escape the function. The book accepts mutation that no caller can observe.
6. Prove stack safety with a large input (100k to 1M elements), not by inspection.

Details, tail position, the two folds compared: `folds-and-recursion.md`.

### 3. Return failures as values

1. Decide what the caller needs.

| Caller needs | Return |
|---|---|
| Only whether there is an answer (lookup miss, empty collection) | Option / nullable under strict null checks |
| Why it failed (message, category, original exception) | Result / Either with an error type |
| Every problem from several independent checks | Accumulating validation (section 4) |
| Nothing: no reasonable caller could recover (broken invariant, programmer bug) | Throw / panic |

2. Make the function total: every input maps to exactly one output of the declared type.
3. Chain with map (next step cannot fail), flatMap (next step can fail), filter (turn success into failure on a rule), and a default or fallback at the edge. Handle the failure once, near the top, not at every step.
4. Wrap each throwing third-party call once at the boundary, in a thin adapter that converts the exception to a value. Keep the original error if the cause matters; a catch-all that returns "nothing" loses the reason.
5. Do not change a working function to make it Option-aware. Lift it (`map`, `map2`) at the call site.
6. For a list of fallible calls, use traverse: apply the function to each element and get either all successes or the first failure. In Rust this is collecting an iterator of Results into a Result of a Vec.

Details, API, worked insurance-quote example: `typed-errors.md`.

### 4. Validate independent fields with accumulation

1. Ask whether any check needs the output of another. Parse-then-use is dependent: fail fast is correct and cheap. Independent field checks are not: users should see all errors from one submission.
2. For the independent ones, run every check, then combine the results with an N-ary combine (`map2`, `map3`, ...). If more than one failed, concatenate the error lists in input order. If all succeeded, build the value.
3. Never express independent checks as nested flatMap, `?` chains, or sequential `await` followed by early return: those stop at the first error by construction.
4. Mixed forms: accumulate within a stage, fail fast between stages that depend on each other.

Details, the Validation type, library equivalents: `validation-accumulation.md`.

### 5. Use laziness deliberately

1. Pass an argument as a thunk (zero-argument function) when it is expensive or effectful and only sometimes needed: defaults, fallbacks, log messages.
2. A thunk re-evaluates at every use. If it is referenced more than once, cache it (memoise).
3. For multi-stage transforms on large data, or when only a prefix or first match is needed, use the language's lazy iterator or generator machinery rather than building an intermediate list per stage. Small data: strict pipelines are simpler and fine.
4. To produce a sequence from a state transition, write `unfold(state, step)` where step returns the next element and next state, or nothing to stop.
5. Bound every unbounded sequence with `take`, `takeWhile` or `find`. Remember the work happens at the terminal operation, not where the pipeline was built.

Details: `laziness-and-streams.md`.

## Typed errors or exceptions: where the sources and host languages disagree

The book's position: exceptions break the substitution rule (the same expression means different things inside and outside a `try`) and are invisible in types; use them only when no reasonable program would catch the error. Checked exceptions force a decision but cannot be handled by generic higher-order code, which cannot know what its function argument throws.

Host-language reality (adaptation): Python, Java and C# codebases are built on exceptions, and Go uses `(value, error)` returns that are already a manual Either. Decide by layer:

- Expected failures that a caller can recover from (parse errors, not found, validation): value in the return type, in new code and at module boundaries.
- Bugs and broken invariants: exception or panic, loudly.
- Existing code that throws throughout a module: do not mix styles inside one layer; callers cannot tell which functions throw. Convert at the boundary and say so in the module's documentation.

## Verify

Run these checks against your own change; adapt names to the language.

Data and matching:
- Add a variant to the sum type in a scratch edit (or reason through it) and confirm the compiler or a test flags every operation that needs a new branch. If nothing flags it, the match has a catch-all or the language cannot check; add the test that reaches each variant.
- Persistence: after calling any function that "modifies" a value, assert the original is unchanged.
- Fold on the constructors is the identity: folding a list with "cons" and "empty" gives back an equal list. Tree fold reproduces size, depth, maximum and map written by hand.

Loops and recursion:
- Stack safety: run the function on 100k to 1M elements. A tail-call guarantee is checked by the compiler only where the language has an annotation (Scala `@tailrec`, Kotlin `tailrec`); elsewhere only the large-input test proves it.
- Equivalence: new fold or loop equals a naive reference on random inputs. For associative combine with an identity element, left and right folds agree.
- Polymorphic higher-order functions: `uncurry(curry(f))(a, b) == f(a, b)`, `compose(f, identity) == f`.

Errors:
- Every Option/Result-returning function has a test for the failing branch and the success branch; random inputs never make pure code throw.
- No unwrap right after creation (`.get`, `unwrap()`, `!`, `.value`) outside program edges and tests. Search for them: `rg '\.unwrap\(\)|\.get\(\)|!!|as any'` as a starting set, then read each hit.
- Review question with an observable answer: "from the signature alone, can a caller tell everything that can go wrong?" and "does any path discard the error reason?" (search for `catch` blocks that return a default).
- Chaining laws: `map(identity)` is identity; `None`/failure anywhere gives failure; `sequence` of all successes equals success of the list. For fail-fast traverse, a call counter shows the function stops being called after the first failure.

Validation:
- Submit input with two independent problems; both errors appear, in input order. Add an independent check later and confirm earlier errors are not suppressed.
- One valid input produces the built value; one invalid field produces exactly that field's errors.

Laziness:
- Counter test: a source that counts how many elements were pulled (or throws after the needed prefix). `find` on an unbounded source terminates; `take(2)` pulls two, not three.
- Each stage function is called at most once per element in a fused pipeline.
- A memoised thunk with a counter runs once when forced twice.
- Lazy pipeline equals the strict reference on random lists.

Evidence to show the user: the test names and results above that apply, the large-input run for stack safety, and the before/after signature of each function whose failure mode changed.

Done means:
- every closed set of cases has exhaustive handling with no silent default;
- every recoverable failure is visible in a return type, with the reason preserved where the caller needs it;
- independent validations report all errors, and dependent steps fail fast;
- no loop or recursion you added can overflow the stack on realistic input, shown by a test;
- laziness is used only where an early-exit, size or unbounded-source reason exists, with a test that demonstrates it;
- nothing outside the requested scope was rewritten.

## Proportion and limits

- Cost of the functional forms: allocation per update on immutable collections (accidental O(n^2) when you copy in a loop), extra wrapper types and unwrapping noise in languages without sum types or a short propagation operator, and readers unfamiliar with fold. Weigh these against the defect class you remove.
- Eager `map`/`filter` chains on small data are fine. Reach for laziness only for large data, early exit, or unbounded sources.
- Laziness has its own costs: evaluation moves to the terminal operation, so errors and cost show up away from where the pipeline was written; memoised nodes keep memory alive while a reference to the head is held (the notes mark this as inferred); side effects inside thunks make order unpredictable.
- Higher-kinded abstractions (one interface over Option, Result, Future) are not needed for any of this. Writing `map`, `flatMap`, `map2`, `sequence` and `traverse` per type is normal in Rust, Java, TypeScript and Go.
- Several claims in the sources are the authors' assertions without measurements (for example that sharing beats defensive copying "in the large"). Treat them as reasons to prefer immutability, not as performance guarantees; measure when performance matters.
- Dated points: the book's Scala-specific workarounds (variance annotations, grouping of parameter lists for inference, a non-right-biased Either, no Option/Either `traverse` in the standard library) do not carry over. Go before generics needed `interface{}` or code generation for this style.
- Do not rewrite working imperative code into folds for style. Rewrite when it has a defect or a duplication, or when the user asked.

## References

- `references/algebraic-data-types.md`: modelling with sums and products, exhaustive matching, fold per type, constructor exposure versus smart constructors, open versus closed sets.
- `references/immutable-data-and-sharing.md`: persistence, structural sharing, operation costs, choosing a structure, copy fallbacks, tests.
- `references/folds-and-recursion.md`: loop to state-passing function, tail position, deriving folds, foldLeft versus foldRight, stack safety, cost of composing passes.
- `references/higher-order-and-types.md`: extracting functions and type parameters, following types to implementations, curry, compose, partial application, argument order.
- `references/typed-errors.md`: why not exceptions, alternatives for partial functions, Option and Either APIs, lifting, wrapping, sequence and traverse, decision table.
- `references/validation-accumulation.md`: fail-fast versus accumulate, the independence rule, the Validation type, traverse in general, concurrency analogy, laws to test.
- `references/laziness-and-streams.md`: strictness, thunks and memoisation, lazy sequences, fusion, early exit, unfold, corecursion, pitfalls, tests.
- `references/language-mappings.md`: the idioms and fallbacks in TypeScript, Python, Rust, Kotlin, Java, Go, Swift and C#.

## Sources

- Functional Programming in Scala (1st ed.) ch. 2: loops as recursion, tail position, higher-order and polymorphic functions, following types.
- Functional Programming in Scala ch. 3: algebraic data types, pattern matching, data sharing, folds, list and tree combinators.
- Functional Programming in Scala ch. 4: Option, Either, lifting, map2, sequence, traverse, the case against exceptions.
- Functional Programming in Scala ch. 5: strictness, thunks, lazy lists, fusion, unfold, corecursion.
- Functional Programming in Scala ch. 12: applicative versus monad rule, error-accumulating validation, traverse (validation and traversal parts only).
