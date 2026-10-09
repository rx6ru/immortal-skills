# Validation: stop at the first error or collect them all

How to structure validation so that the user sees the right number of errors, and so that the
interior of the program receives data it does not have to re-check. Sources: Functional Programming
in Scala (FPiS) ch. 4 and the validation part of ch. 12; The Pragmatic Programmer (PP) ch. 4 and
Why Programs Fail (WPF) ch. 10 for where validation sits relative to assertions.

## Validation is not assertion

- Input and other external conditions can legitimately be wrong. Checking them is ordinary error
  handling that is always present, never a precondition and never a strippable assert (PP ch. 4;
  WPF ch. 10).
- Verify both syntax and meaning, and report in the user's vocabulary: "a PIN has exactly four
  digits", not the text of a failed expression (WPF ch. 10).
- Once input has been validated at the boundary, the interior may state the same facts as
  preconditions, because a violation there would now be a bug.

## The central distinction

Two semantics exist and they are not interchangeable (FPiS ch. 4, ch. 12):

| | Short-circuit | Accumulate |
|---|---|---|
| Behaviour | Stops at the first failure; later steps do not run | Runs every check; returns all failures together |
| Fits | Dependent steps: a later step needs the value an earlier one produced | Independent checks: none needs another's result |
| Shape of the code | A chain, each step nested in the previous step's success (flat-map, propagation operator, early return) | Side-by-side combination of the checks' results (map-N, zip, collect) |
| Error carried | One | A non-empty list |
| Typical use | Parse then interpret; look up an id then use it | Fields of a form; entries of a config; items of a batch |

Why a chain cannot accumulate: in a chain the second step is a function of the first step's
successful value. If the first fails there is no value to give it, so it cannot run. This is
structural, not an implementation shortcut. A three-argument combine built on top of the chaining
operation inherits the same behaviour and halts at the first error (FPiS ch. 12).

Why side-by-side can: when the checks are independent, each one has already produced its result
before they are combined. Combining looks at all the results: if every one succeeded it applies
the constructing function; if any failed it concatenates the failures (FPiS ch. 12).

Rule: independent checks are combined, never nested. Dependent steps are chained. If users see one
error per submission on a form with independent fields, the validation was written as a chain
(FPiS ch. 4 warning sign).

## Choosing

1. List the checks.
2. Draw the dependencies: which check needs the output of another? (A date-range check needs both
   dates parsed. A "password confirmation matches" check needs both fields present.)
3. Checks with no arrows between them form a group to accumulate.
4. Each arrow is a short-circuit: if the source failed, skip the dependent check; do not report a
   second, derived error for the same root cause.
5. Decide what the consumer wants. A person filling in a form wants everything at once. A machine
   caller retrying may be satisfied with the first. A pipeline stage after an expensive or
   side-effecting step should usually stop at once.
6. If there is no user-facing reason to accumulate, short-circuit: it is simpler and every
   language supports it directly.

There is a second, more general reason to prefer the side-by-side form when it suffices: because
the structure of the computation is fixed before any of it runs, whatever executes it has more
freedom, for example to run parts concurrently or to inspect the set of checks (FPiS ch. 12 on why
to prefer the weaker abstraction). Running independent calls strictly one after another when they
could be combined is the same mistake in another setting (marked inferred in the notes).

## The accumulating result type

Shape (FPiS ch. 12): either a success holding the value, or a failure holding one error plus a
sequence of further errors, so that a failure always has at least one. Combining two:

| Left | Right | Combined |
|---|---|---|
| success a | success b | success f(a, b) |
| failure e1 | success | failure e1 |
| success | failure e2 | failure e2 |
| failure e1 | failure e2 | failure e1 followed by e2 |

Notes:

- Keep the order of errors stable (left to right) so output is deterministic and testable.
- Such a type supports combination but deliberately offers no chaining operation consistent with
  it; if you need a dependent step, convert to the short-circuit form for that step (FPiS ch. 12
  presents it as a type that can be combined but is not chainable).
- Applying a check to every element of a list and gathering either all the values or all the
  errors is the list form of the same combination; for the accumulating type, the "traverse" and
  "sequence" operations collect every error instead of stopping at the first (FPiS ch. 4 exercise
  discussion; ch. 12).

A fresh sketch in TypeScript, with no library:

```ts
type Validated<T> = { ok: true; value: T } | { ok: false; errors: [string, ...string[]] };

const ok = <T>(value: T): Validated<T> => ({ ok: true, value });
const fail = <T>(msg: string): Validated<T> => ({ ok: false, errors: [msg] });

function combine<A, B, C>(a: Validated<A>, b: Validated<B>, f: (a: A, b: B) => C): Validated<C> {
  if (a.ok && b.ok) return ok(f(a.value, b.value));
  const errors = [...(a.ok ? [] : a.errors), ...(b.ok ? [] : b.errors)];
  return { ok: false, errors: errors as [string, ...string[]] };
}

function all<T>(items: Validated<T>[]): Validated<T[]> {
  return items.reduce<Validated<T[]>>(
    (acc, item) => combine(acc, item, (xs, x) => [...xs, x]),
    ok([]),
  );
}
```

And the same idea in Python where the idiom is simply a list of problems:

```python
def validate_signup(form) -> tuple[Signup | None, list[str]]:
    errors: list[str] = []
    name = form.get("name", "").strip()
    if not name:
        errors.append("name: must not be empty")
    age = parse_int(form.get("age"))            # returns None on failure
    if age is None:
        errors.append("age: must be a whole number")
    elif age < 0:                               # dependent on the parse: only checked if it parsed
        errors.append("age: must not be negative")
    if errors:
        return None, errors
    return Signup(name=Name(name), age=Age(age)), []
```

The second sketch shows both semantics in one function: the name and age checks are independent
and both run; the range check on age depends on the parse and is skipped when the parse failed.

## Validated types at the boundary

- Write a small constructor function per field that takes the raw value and returns either a
  failure or a value of a dedicated type (a `Name`, an `Age`), then build the aggregate by combining
  the results (FPiS ch. 4). The interior of the program takes the dedicated types and has nothing
  to re-check. The notes label the link to "make illegal states unrepresentable" as inferred.
- Do not alter an existing computation's signature to accept raw strings. Parse each raw input
  into a result separately and combine the results to call the unchanged function (FPiS ch. 4,
  insurance-quote example).
- The reasons collected should identify the field or item, so the consumer can attach each message
  to its source.

## Converting between the forms

- Optional to result: attach a reason at the point where you know it.
- Short-circuit result to accumulating: wrap its single error in a one-element list.
- Accumulating to short-circuit: keep the whole list as the error, or take the first, for the
  dependent step that follows.
- Either form to an exception at the outer edge, if the caller decides failure is fatal (FPiS
  ch. 4 gives the unwrap-or-throw idiom).

## Design question to settle up front

When a combine of two fields reports only the first error, there are three possible places to
change (posed, not answered, in FPiS ch. 4): the combining operation; the signature of the
aggregate constructor; or a new data type with more structure. The later chapter's answer is the
third. In practice that means: do not try to make the short-circuit type accumulate by patching
call sites; use a type or collector whose combine concatenates.

## Warning signs

- A form that reports one problem per submission.
- A second error that is merely a consequence of the first ("age must not be negative" when the
  age did not parse).
- Validation mixed into business logic, so interior functions re-check what the boundary checked.
- A catch-all around parsing that returns "nothing", discarding which field failed and why (FPiS
  ch. 4).
- Validation implemented with assertions (WPF ch. 10).
- Error order that varies between runs.
- A combine operation whose result depends on hidden side effects or evaluation order; the
  regrouping and reordering guarantees below then fail (inferred in the notes).

## Verification

- An input with k independent faults produces exactly k errors, in a defined order (FPiS ch. 12
  verification, marked inferred there: all failures present and order preserved).
- Adding a new independent check does not remove any error previously reported for the same input
  (same source).
- A dependent check does not run when its prerequisite failed; prove it with a counter or a fake
  that records calls (FPiS ch. 4 verification, inferred).
- A fully valid input yields the constructed value and no errors.
- Grouping does not matter: combining (a with b) with c gives the same value or the same error
  list as a with (b with c). This is the associativity guarantee of the combine operation (FPiS
  ch. 12), worth one property test if you wrote the combinator yourself.
- Transforming before or after combining gives the same result (the naturality guarantee, FPiS
  ch. 12); in practice, extracting a sub-value before calling the combine must not change which
  errors appear.
- Messages are in domain language and name the field.
- No strippable assert in the validation path.

## Related

- The full functional vocabulary (applicative versus monadic composition, laws, traversals) is in
  `fp-data-and-errors` and `fp-api-design-with-laws`. This file keeps only what is needed to
  choose and implement validation behaviour.
- Library support per language: `language-mappings.md`.
