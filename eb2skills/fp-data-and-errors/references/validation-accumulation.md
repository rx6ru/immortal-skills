# Fail-fast versus accumulate-all validation, and traverse

Source: FPiS ch. 4 (4.4, exercise 4.8) and ch. 12 (12.1 to 12.7: the validation and traversal parts only; the full laws and abstraction chooser live in `fp-api-design-with-laws`). Items marked (adaptation) or (inferred in notes) are not the book's own claims.

## Contents

1. Two semantics
2. The independence rule
3. The Validation type
4. Using it: before and after
5. Mixed forms
6. Concurrency is the same distinction
7. traverse and sequence in general
8. Why prefer the weaker form
9. Without higher-kinded types
10. Verify

## 1. Two semantics

| | Fail-fast (monadic chaining: flatMap, `?`, sequential await, nested `let`) | Accumulate-all (applicative combination: map2/mapN, collect-all) |
|---|---|---|
| Behaviour on failure | stops at the first error | runs every check and collects every error |
| Reason | each stage may use the previous stage's result, so later stages cannot run without it | the checks are independent, so all can run |
| Typical type | Either / Result | Validation (success, or a non-empty list of errors) |
| Output on two bad fields | one error | both errors |

FPiS ch. 4, exercise 4.8: `mkPerson` built from `map2` over Either reports only the first of two invalid fields. The book poses the question (change `map2`, change `mkPerson`'s signature, or add a data type with more structure) and ch. 12 answers it with Validation.

## 2. The independence rule

Ask of each pair of checks: does one need the other's output?

- Yes (parse the string, then range-check the number; look up the id, then fetch the record by it): dependent. Fail fast is correct and usually what you want.
- No (name, birthdate and phone on a form): independent. Accumulate, so the user gets all errors in one round trip.

Why Either cannot do it: a chain like `validName flatMap (n => validBirthdate flatMap (b => validPhone map ...))` is a linear dependency chain, so if the first fails the others never run. `map3` built on flatMap halts at the first error. With independent checks, use applicative `map3` on Validation: `map3(validName(n), validBirthdate(b), validPhone(p), WebForm)` returns all errors at once.

## 3. The Validation type

```
Validation<E, A> = Failure(head: E, tail: List<E>)  |  Success(A)
```

`map2(va, vb, f)`:

- both Failure: Failure with the errors of `va` followed by the errors of `vb` (concatenation preserves input order)
- one Failure: that Failure
- both Success: `Success(f(a, b))`

`Failure` holds a head plus a tail so the error list cannot be empty. (If you use a plain list-of-errors, make sure a Failure with zero errors is unrepresentable or at least never constructed.)

Sketch (TypeScript):

```ts
type V<E, A> = { ok: true; value: A } | { ok: false; errors: [E, ...E[]] };

const map2 = <E, A, B, C>(a: V<E, A>, b: V<E, B>, f: (a: A, b: B) => C): V<E, C> =>
  a.ok && b.ok ? { ok: true, value: f(a.value, b.value) }
  : !a.ok && !b.ok ? { ok: false, errors: [...a.errors, ...b.errors] }
  : (a.ok ? b : a) as V<E, C>;
```

The other piece: the book also writes the Either monad (exercise 12.5), where `flatMap` on Left short-circuits. Validation deliberately has no `flatMap` consistent with accumulation, which is the trade (section 8).

## 4. Using it: before and after

Before (fail-fast, loses information):

```
const name = mkName(input.name);      // Result, early return on error
if (!name.ok) return name;
const age = mkAge(input.age);
if (!age.ok) return age;
return ok({ name: name.value, age: age.value });
```

After:

```
return map2(validName(input.name), validAge(input.age), (name, age) => ({ name, age }));
```

Both calls run; if both fail the caller receives two errors. When the number of fields is larger, use `mapN` of that arity, or collect into a record and check that every entry is Success.

Practical rule (ch. 12): independent field checks use Validation (collect all errors, show them in one go); dependent steps use Either (fail fast).

## 5. Mixed forms

(Adaptation, a direct reading of the independence rule.) A realistic request has stages: parse the JSON (fails fast; nothing else makes sense without it), then validate the fields (accumulate), then check a business rule that needs the whole validated value (fails fast). Build it as: fail-fast parse, then flatMap into an accumulating step, then flatMap into the rule check. Do not accumulate across a dependency, and do not fail fast across independence.

Dependent later checks within the accumulating stage (end date must be after start date) need both values: validate each field first, then check the relation once both are Success.

## 6. Concurrency is the same distinction

Notes (inferred): `Promise.all`, `asyncio.gather`, `Future.zip` and `join!` are the applicative form: independent, concurrent. Sequential `await` or `.then` chains are the monadic form. Awaiting independent calls one after another is the smell of "used a monad where an applicative was enough" and gives up concurrency. A dependent call (needs the previous result as input) must be sequential.

Caution (adaptation): `Promise.all` rejects on the first rejection (fail-fast across the group); if you want all outcomes, use the all-settled variant (`Promise.allSettled` in JS) and collect failures yourself.

## 7. traverse and sequence in general

The ch. 12 observation: `traverse` was written many times, once per monad, but only uses `unit` and `map2`, never `flatMap` directly. So it works for any type that supports those two operations, including Validation, which is not a monad.

- `traverse(items, f)` with `f: A -> G<B>` returns `G<List<B>>`; `sequence(listOfG)` returns `G<List>`. It "swaps the order of the two containers".
- Meaning by signature: list of options becomes option of list (None if any None); tree of options becomes option of tree; map of async values becomes async map (evaluate in parallel); with Validation all errors are collected; with State actions run in order threading state.
- Heuristic from the book: whenever a concrete container like List appears in an abstract interface, ask what happens if you abstract over it. Instances: List, Option, Map, Tree.
- Traverse keeps the shape of the structure (length of list, shape of tree). Fold discards it and replaces it with monoid operations.
- State-threading traversal: `mapAccum(fa, s0, f)` where `f: (a, s) => (b, s')` returns a structure of the same shape plus the final state. Examples: `zipWithIndex` (state is a counter, works for lists, trees, any traversable); `toList` (accumulate in state and reverse); `reverse` for any traversable (take the list reversed and refill). Zipping two structures needs matching shapes or a dominant side.

Use a traverse when you have a loop "for each item do an effectful thing and collect the results into a container of the same shape". Use `sequence` when you already hold a container of effects and want an effect of the container.

Equivalents in practice (inferred in notes): Rust `iter().map(f).collect::<Result<Vec<_>, E>>()` and `Option<Vec<_>>`; TypeScript `Promise.all(xs.map(f))`; Python `asyncio.gather(*map(f, xs))`; Swift `try xs.map(f)` with a throwing closure (the notes also list `compactMap`, but that drops failures instead of failing, so it is not a traverse); Java `CompletableFuture.allOf` followed by join; Kotlin Arrow `traverse` (the Arrow API has changed between versions). Rust's `collect` is a fail-fast traverse; to accumulate, write a Validation or error-collector.

## 8. Why prefer the weaker form

Rule of chapter 12: prefer the weakest abstraction that does the job. For validation that means: do not reach for flatMap when `mapN` suffices. Reasons the notes give:

1. Generic combinators written against the weaker interface (traverse) work for more types.
2. A weaker interface gives the interpreter more freedom. If a parser or form description is built without flatMap, the structure is known before running, so the runner can analyse it, optimise it, batch it or generate documentation or help text from it. Adding flatMap generates parts dynamically and limits the interpreter. The cost of power is paid in analysability. (Build systems, query planners and form schemas are the notes' inferred extension.)
3. Applicatives compose; monads in general do not. Layered effects (an Option inside a Future) compose for free with applicatives; monads need a transformer or a hand-built combined type, each written per monad.

Is it applicative or monadic? Fixed structure whose results fill holes: applicative. An earlier result chooses what to run next: monadic. Example: a CSV with known column order is applicative; a CSV whose first line names the column order requires a monadic parser. Applicative parsers handle context-free structure only; monadic parsers handle context-sensitive structure.

Practical consequence for CLI argument parsers, config loaders, form descriptions and query batchers: declare the independent pieces applicatively so the program can inspect the description before running it.

## 9. Without higher-kinded types

You do not need them. Write `map2`/`mapN`, `traverse` and `sequence` for each type you use and test the laws per type (below). Libraries that already provide accumulation (inferred in notes): Zod `safeParse` and Pydantic collect all issues, Kotlin Arrow `zipOrAccumulate` (older Arrow: `Validated`, deprecated in recent versions), Java Vavr `Validation`, Cats `Validated`, Rust crates such as `validator`. Using one is better than hand-rolling when it is already a dependency.

## 10. Verify

Validation behaviour:

- Two independent invalid fields: both errors present, in input order.
- Adding another independent check does not suppress the errors of earlier ones.
- All valid: the value is built from the validated pieces.
- A dependent check that needs a failed field's value does not run (and does not crash).

Laws for any `map2` you write (from ch. 12, state equality on the observable result):

- functor: `map(v, identity) == v` and `map(map(v, g), f) == map(v, f after g)`;
- identity: combining with a unit value (`Success(())`) on either side leaves the structure unchanged;
- associativity: grouping of three effects does not matter, up to re-pairing the results;
- naturality: you may transform the values before or after combining.

The notes call these sanity checks, not deep results; check them first on Option, then on your Validation, List and State-like types. If `map2` secretly depends on the order of side effects inside it, associativity and naturality break (inferred in notes).

Traverse checks (inferred in notes): the result has the same length or shape as the input; sequence of Option results is None iff any is None; traversing with the identity container equals `map`; traversing with a constant monoid container equals a fold; `zipWithIndex` yields 0..n-1 in traversal order; the reverse law `toList(reverse(x)) ++ toList(reverse(y)) == reverse(toList(y) ++ toList(x))`.

Concurrency check: with two independent calls each sleeping T, total time near T (applicative) not 2T (sequential).
