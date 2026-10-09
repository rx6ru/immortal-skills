# Typed errors without exceptions

Source: FPiS ch. 4 (all sections), with the Option/Either API, `map2`, `sequence` and `traverse`. Items marked (adaptation) or (inferred in notes) are not the book's own claims.

## Contents

1. The claim
2. Why exceptions are a problem
3. Alternatives for a partial function
4. Option: API and when to use each operation
5. Lifting and wrapping
6. Combining: map2 and friends
7. sequence and traverse
8. Either (Result)
9. Decision table
10. Mapping the idea to your language
11. Warning signs
12. Verify

## 1. The claim

Represent failure as an ordinary value returned from a function, and write higher-order functions that capture the common propagation patterns. The result is safer than exceptions, keeps the substitution rule, and keeps the one thing exceptions did well: consolidating error handling in one place instead of scattering it. Exceptions are reserved for truly unrecoverable conditions.

## 2. Why exceptions are a problem

Two named problems (FPiS 4.1):

1. They break referential transparency and introduce context dependence. Example from the book: `y = throw ...` then `try { x + y } catch { ... => 43 }` throws out of the function, but substituting the throw expression for `y` inside the `try` returns 43. The same expression means something different depending on the enclosing `try`. That is the origin of the folk rule "exceptions are for errors, not control flow".
2. They are not type safe. The signature `Int => Int` says nothing about failure and the compiler does not force the caller to decide. A forgotten handler appears at runtime.

Checked exceptions force a decision but cost boilerplate, and, more importantly, do not work for higher-order functions: `map(list, f)` cannot know what `f` throws, so generic code falls back to catch-all runtime exceptions.

## 3. Alternatives for a partial function

`mean(xs)` is partial: undefined for an empty list. Options and the book's verdict:

1. Throw: rejected above.
2. Return a bogus value (NaN, -1, null, a magic number). Rejected because errors propagate silently and are found late; every call site needs an `if`; it is not applicable to polymorphic code (`max<A>` of an empty sequence cannot invent an `A`, and null does not exist for primitives); and it needs a special calling convention that makes the function awkward to pass to higher-order functions.
3. Pass a default or a handler (`mean(xs, onEmpty)`). Total, but it forces the immediate caller to know what to do and fixes the return type; callers cannot abort the larger computation. The decision should be deferrable to the most appropriate level.
4. Return Option or Either. Chosen. The function is total (each input maps to exactly one output) and the caller decides.

Non-termination is another kind of partiality; it is not a recoverable error and is out of scope.

## 4. Option: API and when to use each operation

`Option<A> = Some(value) | None`. Think of it as a list with at most one element. Standard-library uses: map lookup, first-element-or-none, last-element-or-none.

| Operation | Meaning | Use when |
|---|---|---|
| `map(f)` | transform the inside; `f` is never called on None | proceed as if success; the next step cannot fail |
| `flatMap(f)` with `f: A -> Option<B>` | next step can itself fail; stops at first None | a chain where each stage may fail |
| `filter(p)` | Some becomes None when the predicate fails | success that violates a rule becomes failure |
| `getOrElse(default)` | leave the Option world with a default; default passed lazily | at the edge, one place |
| `orElse(alternative)` | first if defined else the second; second passed lazily | fallback chains |

Pipeline shape: `lookup("Joe").map(dept).filter(not accounting).getOrElse("Default")`. Transform with map, flatMap and filter, handle once at the end. You do not check for None at each stage. The authors' advice: try to recognise the pattern before resorting to pattern matching.

Multi-stage example: `variance(xs)` is `mean(xs).flatMap(m => mean(xs.map(x => (x - m)^2)))`; any failing stage aborts the rest.

Because `Option<A>` is a different type from `A`, the compiler will not let you forget to defer or handle the missing case.

## 5. Lifting and wrapping

Does Option infect the codebase? The book's answer is no, because of lifting.

- `lift(f) = optionA => optionA.map(f)`. An existing plain function can be made Option-aware after the fact; it stays unaware of Option. (For example `lift(abs)`.)
- Wrapping throwing APIs: `Try(thunk)` evaluates the argument lazily inside a `try` and returns Some on success or None on exception. The argument must be passed unevaluated, otherwise the exception is raised before the `try`. The caveat: None discards the reason; use the Either version when the cause matters.

Worked example, the insurance quote: form fields arrive as strings; `insuranceRateQuote(age: Int, tickets: Int)` must not change (changing it would entangle concerns, and you may not own it). Parse each field with `Try(parseInt)`, then combine with `map2`. In pseudo-notation (a for-comprehension in Scala, a do-block in Haskell, `?` or `map2` elsewhere; runnable versions are in section 7):

```
for age in Try(parseInt(ageStr)), n in Try(parseInt(ticketsStr)): yield rateQuote(age, n)
```

Message: you never need to change an existing function to make it work with optional values; use map, lift, map2, sequence, traverse.

## 6. Combining: map2 and friends

`map2(a, b, f)` returns None if either is None, else `Some(f(x, y))`. Shape: `a.flatMap(x => b.map(y => f(x, y)))`, which is exactly what a for-comprehension or do-notation desugars to. `map3`, `map4`, `map5` follow the same pattern. Sugar in other languages (inferred in notes): `?` in Rust (roughly), async/await in C#/JS, LINQ `from ... select`, Kotlin and Swift optional chaining and `guard let`.

Independence matters here: `map2` on Option is fine because both inputs are independent and the result is only "present or absent". For Either, the same shape short-circuits on the first error; see `validation-accumulation.md` for when that is wrong.

## 7. sequence and traverse

- `sequence(listOfOptions)` returns `Some(list)` if every element is Some, otherwise None.
- `traverse(items, f)` with `f: A -> Option<B>` returns `Option<List<B>>`. `sequence(items.map(f))` works but traverses twice; implement `traverse` in one pass (fold from the right with `map2(f(head), tail)(cons)`), then `sequence = traverse(identity)`.
- Use case: `parseInts(strings) : Option<List<Int>>`.
- Placement (footnote): not a method on List (List should not know about Option) and not on Option; put them in the Option module.

Takeaway from the book: between `map`, `lift`, `sequence`, `traverse`, `map2` and its siblings you never need to modify an existing function to work with optional values.

For Either, `sequence` and `traverse` return the first error encountered (exercise 4.7). A fail-fast traverse stops calling `f` after the first failure; a counter in a test shows that.

Runnable sketch (TypeScript, checked with `deno check`; the checks at the end passed). It is the whole toolkit for one concrete type: constructors, a boundary wrapper, `flatMap`, `map2` and a fail-fast `traverse`.

```ts
type Result<A, E> = { ok: true; value: A } | { ok: false; error: E };
const ok = <A>(value: A): Result<A, never> => ({ ok: true, value });
const err = <E>(error: E): Result<never, E> => ({ ok: false, error });

// Wrap a throwing call once, at the boundary; keep the exception as the reason.
function attempt<A>(thunk: () => A): Result<A, Error> {
  try { return ok(thunk()); } catch (e) { return err(e instanceof Error ? e : new Error(String(e))); }
}
const flatMap = <A, B, E>(r: Result<A, E>, f: (a: A) => Result<B, E>): Result<B, E> =>
  r.ok ? f(r.value) : r;
const map2 = <A, B, C, E>(ra: Result<A, E>, rb: Result<B, E>, f: (a: A, b: B) => C): Result<C, E> =>
  flatMap(ra, (a) => flatMap(rb, (b) => ok(f(a, b))));
// Fail-fast traverse: stops calling f after the first failure.
function traverse<A, B, E>(xs: readonly A[], f: (a: A) => Result<B, E>): Result<B[], E> {
  const out: B[] = [];
  for (const x of xs) {
    const r = f(x);
    if (!r.ok) return r;
    out.push(r.value);
  }
  return ok(out);
}

const parseIntStrict = (s: string) => attempt(() => {
  if (!/^-?\d+$/.test(s)) throw new Error(`not an integer: ${s}`);
  return Number(s);
});
const insuranceRateQuote = (age: number, tickets: number) => 100 + 5 * tickets + (age < 25 ? 50 : 0); // unchanged
const quote = (age: string, tickets: string) =>
  map2(parseIntStrict(age), parseIntStrict(tickets), insuranceRateQuote);
// quote("30", "2") is { ok: true, value: 110 }; quote("abc", "2") is { ok: false, error: Error("not an integer: abc") }
// traverse(["1", "x", "3"], f) calls f for "1" and "x" only.
```

The same in Python (run with `python3 -I`; checks passed): `Ok` and `Err` are frozen dataclasses, `flat_map(r, f)` is `r if isinstance(r, Err) else f(r.value)`, `map2` nests two `flat_map` calls, `try_(thunk)` returns `Ok(thunk())` or `Err(e)` from `except Exception as e`, and `traverse` is a loop that returns the first `Err` and otherwise `Ok(list)`. `int("abc")` already raises `ValueError`, so `try_(lambda: int(s))` is the whole parser. In Python, keep this style at API boundaries and for expected failures (section 10).

## 8. Either (Result)

Option does not say what went wrong. `Either<E, A> = Left(E) | Right(A)`; by convention Right is success, Left is failure, `E` is the error type. Variants of `E`: a message string, an exception (keeps the stack trace), or your own error ADT (adaptation: prefer a small enum or ADT of failure causes for callers that branch on the cause).

The API is right-biased: `map`, `flatMap`, `orElse` and `map2` act on Right and pass Left through. (Scala 2.12+ made Either right-biased; the book defines its own. The `EE >: E` type parameters on `flatMap` and `map2` are a Scala variance detail.)

`Try` for Either converts a thrown exception into `Left(exception)`:

```
for age in Try(parseInt(ageStr)), n in Try(parseInt(ticketsStr)): yield rateQuote(age, n)   // Either<Exception, Double>
```

Smart constructors that return Either (the book's validation example):

```
mkName(name) : Either<string, Name>    // Left if empty or null
mkAge(age)   : Either<string, Age>     // Left if negative
mkPerson(name, age) = map2(mkName(name), mkAge(age), Person)
```

The limitation (exercise 4.8, left as a design question): `mkPerson` reports only the first error, even when both name and age are invalid. If you need both, use an error-accumulating type; see `validation-accumulation.md`.

## 9. Decision table

| Situation | Use | Reason |
|---|---|---|
| Legitimately no answer, reason uninteresting (lookup miss, head of empty) | Option / strict nullable / Maybe | caller needs only presence |
| Caller needs to know why (validation message, parse failure, category) | Either / Result with an error type | carries the reason |
| Several independent validations on one input, report every problem | error-accumulating type (list of errors) | flatMap/map2 on Either short-circuit |
| Unrecoverable condition or programmer bug no reasonable caller would catch | exception | the book's rule of thumb: exceptions only if no reasonable program would catch them; if some callers may recover, use Option or Either |
| You must call a throwing third-party API | wrap once at the boundary with `Try`, then continue with values | converts to a value; keep the wrapper thin |
| Generic higher-order code must handle errors from its function argument | have the function return Option/Either; use traverse and sequence | checked exceptions cannot do this |

To turn a value back into an exception at the program edge: `o.getOrElse(throw ...)`.

## 10. Mapping the idea to your language

Details are in `language-mappings.md`. In short (notes, inferred): TypeScript discriminated union `{ok:true,value} | {ok:false,error}` or `T | undefined` under strict null checks; Rust `Option`/`Result` and `?`, with `collect::<Result<Vec<_>,_>>()` as traverse; Kotlin nullable types and `Result`; Swift `Optional` and `Result`; Java `Optional` and library `Either`/`Try`; Python `Optional[T]` hints with exceptions kept for the unexpected; Go `(T, error)` as a manual Either.

What the language must offer: sum types or tagged unions, generics, closures. Higher-kinded types are not needed to write `map`, `flatMap`, `map2`, `sequence` and `traverse` for one concrete type; they are only needed to abstract over all such types at once. Without them write the combinators per type.

Rule from the notes for exception-based languages (Python is called out): exceptions are idiomatic there, so apply the technique at API boundaries and for expected failures only. Do not mix both styles within one layer; callers cannot tell which functions throw. Pick a convention per layer and document it.

## 11. Warning signs

- `null`, -1, NaN or empty string used as "no result": convert to Option or Result.
- Callers catch exceptions from a generic library to continue a pipeline: wrap the call at the boundary with a Try-style adapter.
- A catch-all handler that returns None: the reason is lost; use Either when the cause matters.
- Option or Either unwrapped right after creation (`.get`, `unwrap()`, `!`): defeats the point. Unwrap only at the program edge, or use map/flatMap/getOrElse.
- A flatMap chain over a form with many independent fields: only one error at a time. Use accumulation.
- Some functions in a module throw and others return Either.

## 12. Verify

- Totality: tests for the failing branch and the success branch of every function returning Option or Result; a property test with random inputs that asserts pure code never throws (inferred in notes).
- Law-like tests (inferred in notes): `map(identity)` is identity; `map2(Some(a), Some(b), f) == Some(f(a, b))`; None anywhere gives None; `sequence(xs.map(Some)) == Some(xs)`; `traverse(xs, f) == sequence(xs.map(f))` as results, though for Either the traverse calls `f` only until the first failure (check with a counter).
- Review questions: "Can a caller tell from this signature everything that can go wrong?" "Does any path swallow the error reason?"
- Search the diff for `catch` blocks returning a default and for unwrap calls; each hit needs a stated reason.
