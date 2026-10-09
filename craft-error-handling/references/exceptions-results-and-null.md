# Exceptions, typed results, and null

How to signal and receive a failure once you have decided it must be visible to the caller. For the
decision whether it should be visible at all, see `choosing-a-strategy.md` and
`define-errors-away.md`.

Short citations: CC = Clean Code; FPiS = Functional Programming in Scala; PP = The Pragmatic
Programmer; PoSD = A Philosophy of Software Design.

## Contents

1. What every mechanism has to achieve
2. Status codes and sentinels: why not
3. Exceptions: rules for raising and catching
4. Typed results: optional and either
5. Working with result values without unwrapping
6. Boundaries: wrapping code that throws or returns null
7. Null and absence
8. Checked exceptions
9. Error handlers as callbacks
10. Warning signs
11. Verification

## 1. What every mechanism has to achieve

Whichever form you choose, check it against these four requirements, which are what the sources
agree on beneath their disagreement:

1. The normal path reads straight through, without error plumbing nested around each step
   (CC ch. 3, ch. 7; PP ch. 4).
2. A failure cannot be ignored by accident (CC ch. 7; FPiS ch. 4).
3. Handling is consolidated, not repeated at every call (PoSD ch. 10; FPiS ch. 4 names this as the
   one benefit of exceptions worth keeping).
4. The error says what happened: the operation, the thing it was applied to, the cause (CC ch. 7).

## 2. Status codes and sentinels: why not

**Status codes returned from commands** (CC ch. 3, ch. 7; PP ch. 4):

- The caller must check immediately after each call, and the checks nest, so that the real logic is
  buried in the innermost success branch.
- A check is easily omitted and nothing complains.
- A status returned from a command mixes doing with answering.
- A single shared enumeration of codes becomes a file everything imports. Adding a code forces
  rebuilds everywhere, so people reuse an old inaccurate code instead. Independent error types do
  not have this effect. In the notes' words on modern languages: avoid a central god error-enum and
  give each module its own error type.

**Sentinel values in the result's own type** (NaN, -1, null, empty string) (FPiS ch. 4):

- The error propagates silently; the compiler gives no reminder; it is discovered far from where
  it arose.
- Each call site needs an explicit test, multiplied when calls are chained.
- It cannot work in generic code: a function over an arbitrary element type has no value of that
  type to use as "nothing".
- It imposes a special calling convention, which makes the function awkward to pass to
  higher-order functions that treat results uniformly.

**A default supplied by the caller** (FPiS ch. 4) makes the function total but forces the immediate
caller to know the answer and restricts the outcome to the same type; the caller cannot abort a
larger computation or branch. Useful as a convenience on top of an optional, not as the only form.

## 3. Exceptions: rules for raising and catching

### Raising

- Raise when the routine cannot do its job and the condition is not an anticipated outcome (PP
  ch. 4; CC ch. 7 decision procedure).
- Give context: a stack trace shows where, not what was intended. State the operation that failed
  and the kind of failure, with enough data to log it (CC ch. 7).
- Keep the cause when translating one error into another.

```python
# weak
raise RuntimeError("failed")
# useful
raise StorageError(f"reading section {name!r} from {path}: file not found") from err
```

### Types

- Classify by how callers will catch, not by which component or library produced the failure
  (CC ch. 7).
- One type per area with discriminating data inside is often sufficient. Introduce distinct types
  only when some caller wants to catch one and let another pass (CC ch. 7).
- A hierarchy that mirrors the implementation's components is a warning sign (CC ch. 7).
- Each error type is interface surface; fewer is deeper (PoSD ch. 10).

### Catching

- Start with the try/catch/finally when writing a routine that can fail. The try block announces
  that execution may stop at any point inside it, so think of it as a transaction: the handler must
  leave the program consistent whatever happened (CC ch. 7).
- Test-first mechanics for this (CC ch. 7): write a test that expects your error type for an
  invalid input; make it pass with a body that attempts the operation inside the try and rethrows
  as your type; narrow the catch to the specific underlying exception; then add the remaining logic
  inside the try as if nothing could go wrong.
- The body of a try is the happy path and nothing else. A function that handles an error does only
  that: the try opens the function and nothing follows the handler; the real work is an extracted
  function (CC ch. 3). In languages with propagation operators or early returns the same goal is a
  flat happy path with errors returned early (notes' caveat).
- Catch the narrowest type that the handler can deal with.
- A handler has three legitimate things to do: restore consistency and continue; translate with
  context and rethrow; end the unit of work and report. Anything else, including log-and-continue,
  is swallowing (notes on CC ch. 7).
- Log once, at the boundary that handles the error. Log-and-rethrow produces duplicates.

### The removal test

Suppose an uncaught exception terminates the program. Would the program still do its normal work
with every handler deleted? If not, exceptions are being used for circumstances that are not
exceptional (PP ch. 4). Review question derived from it (marked inferred in the notes): is any
catch block implementing a business branch?

### Why restraint

An exception is an immediate non-local transfer of control. In normal flow it couples routines to
their callers through the handling code and breaks encapsulation (PP ch. 4). It also makes the
meaning of an expression depend on the enclosing try, so it cannot be reasoned about locally
(FPiS ch. 4).

## 4. Typed results: optional and either

Put the possibility of failure in the return type so that the function is total: every input maps
to an output, and the caller must decide what to do with the failing branch (FPiS ch. 4).

| Type | Meaning | Use when |
|---|---|---|
| Optional (`Option`, `Maybe`, checked nullable) | A value, or nothing | The reason for absence is obvious or uninteresting: lookup miss, first element of an empty list |
| Either / Result with an error type | A value, or a description of the failure | The caller needs to know why: parse failure, validation message, error category. May hold a message, a structured error, or a captured exception to keep its stack trace |
| Accumulating result | A value, or a non-empty list of failures | Several independent checks and every failure is wanted. See `validation-and-accumulation.md` |

Rule of thumb for the boundary with exceptions (FPiS ch. 4): throw only if no reasonable program
would ever catch it; if for some callers it might be a recoverable error, return a value and let
them choose. A caller who decides the failure is fatal can convert back at the edge by unwrapping
with a throw.

A different type for "maybe a value" than for "a value" is what gives the safety: the compiler will
not let the caller forget to handle or defer the missing case.

## 5. Working with result values without unwrapping

The common fear is that a result type spreads through the whole codebase. It need not, because
ordinary functions can be applied to wrapped values from outside (FPiS ch. 4). The operations, in
language-neutral terms:

| Operation | Does | Use for |
|---|---|---|
| map | Apply a function to the value if present | Continue as though nothing failed; the function is skipped on failure |
| flat-map (and-then) | Apply a function that can itself fail | A sequence of stages, each of which may fail; stops at the first failure |
| filter | Turn a success that fails a predicate into a failure | A rule the value must satisfy |
| get-or-else | Leave with a default | The end of the pipeline |
| or-else | Try an alternative that may also fail | Fallback chains |
| lift | Turn a plain function into one over wrapped values | Reusing existing code unchanged |
| map2 / zip | Combine two wrapped values with a two-argument function | Calling an existing function whose arguments each came from a fallible step |
| sequence | A list of results becomes a result of a list | "All succeeded, or the first failure" |
| traverse | Apply a fallible function to each item and collect | Parsing every element; one pass, stops at the first failure |

Guidance:

- The shape to aim for: transform with map, flat-map and filter; handle once at the end. No test
  for failure at each stage.
- Recognise one of these patterns before reaching for an explicit match or branch.
- You should not have to modify an existing function to make it aware of optional inputs; lift it
  or combine with map2.
- Keep helpers such as sequence in a module of the result type, not on the list type and not on
  the element type.
- Many languages offer syntax for the flat-map chain: comprehension or do-notation, a propagation
  operator, optional chaining (the notes mark the cross-language analogies as inferred).

```ts
type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };

function parseAge(s: string): Result<number, string> {
  const n = Number(s);
  // Number("") and Number("  ") are 0, so reject blank input explicitly
  return s.trim() !== "" && Number.isInteger(n) && n >= 0
    ? { ok: true, value: n }
    : { ok: false, error: `age must be a non-negative integer, got "${s}"` };
}
// the caller cannot read .value without first checking .ok
```

Short-circuit versus accumulate is a real semantic difference, not a style: a flat-map chain can
only stop at the first failure because each stage needs the previous value (FPiS ch. 4, ch. 12).

## 6. Boundaries: wrapping code that throws or returns null

Both schools prescribe the same move for third-party and I/O code: wrap it once.

**In an exception-based codebase** (CC ch. 7). When several catch clauses around a vendor call all
do the same thing, wrap the vendor API in a thin class of your own that catches the vendor's
exceptions and rethrows one type of yours. Gains: minimal dependence on the vendor; freedom to
replace it; easy to fake in tests; an interface you designed. Also wrap vendor methods that return
null.

**In a value-based codebase** (FPiS ch. 4). Write one adapter that runs the throwing call and
converts a thrown exception into a failure value. The argument must be evaluated inside the
adapter's try, so pass it lazily (a thunk). Keep the wrapper thin. An adapter that converts to a
bare optional discards the reason; convert to a result that holds the exception when the cause
matters.

```python
def attempt(thunk):
    """Run thunk(); return (value, None) or (None, exc)."""
    try:
        return thunk(), None
    except Exception as exc:      # boundary adapter only; never in interior code
        return None, exc
```

Rule shared by both: foreign error types do not appear outside the adapter (the defensible core the
notes extract from the checked-exception debate is exactly this: translate at boundaries so
low-level failure types do not leak through layers).

Do not change an existing pure function's signature to accept raw unvalidated input; parse the
inputs separately into results and combine them, so parsing and computing stay separate concerns
(FPiS ch. 4).

## 7. Null and absence

**Do not return null** (CC ch. 7). It creates work for every caller and one missed check causes a
failure far away. The fix is not more null checks; a codebase with null checks on every other line
has too many nulls. Alternatives:

| The caller needs | Return |
|---|---|
| To iterate over zero or more things | An empty collection |
| A usable object with default behaviour that is a real rule | A special-case object |
| To know whether there is a value | An optional type |
| To know why there is no value | A result with a reason |
| Nothing, because absence means the routine failed | Raise |

```python
# before
def employees():
    return None if not rows else rows
# after
def employees():
    return rows            # [] when there are none; callers just iterate
```

**Do not pass null** (CC ch. 7). Each response to a null argument is unsatisfying: a null
dereference; a custom invalid-argument error that nobody knows how to handle; an assertion that
documents well but is still a run-time failure. Forbidding null arguments by convention means a
null in an argument list is always a bug, so interior code does not defend against it. The notes
add: fail-fast guards at entry remain reasonable, and public boundaries that take user input or
deserialised data must validate regardless.

**Modern type systems** (notes' caveat): languages with compile-time nullability checks enforce
both rules for you; prefer them over convention. One Java-specific caution in the notes: its
optional type is discouraged as a field or parameter type.

**Unwrapping.** Forcing a value out of an optional immediately after obtaining it throws away what
the type was for. Carry it through and unwrap at the program's edge (FPiS ch. 4 warning sign).

## 8. Checked exceptions

- Against (CC ch. 7): declaring a new checked type at a low level forces every signature between
  it and the catch to change, with rebuilds, and makes middle layers know about low-level details.
  Languages without them produce robust software.
- Against (FPiS ch. 4): they cannot be combined with higher-order functions, which do not know
  what their function arguments throw, so generic code falls back to an unchecked catch-all.
- For: they force a decision, which is the same property typed results provide. CC allows them for
  a critical library where callers must catch.
- Status of the claim: the notes call "the debate is over" dated and overstated; the design space
  now includes typed results and typed throws, and the debate continues.
- Rule: use an unchecked exception for the unexpected in application code. Use a checked or typed
  error where the failure is an expected, recoverable part of a contract and is handled close by.
  In either case translate at each layer boundary so that the types a caller sees belong to the
  layer it called.

## 9. Error handlers as callbacks

An alternative to both: a routine registered to be called when a category of error is detected
(PP ch. 4). It is the necessary form in languages without exceptions and occasionally useful
alongside them, when a pervasive failure would otherwise have to be handled at every call. The
notes' example is a remote-invocation framework that made every remote call declare a failure;
wrapping the remote object in a local class with a registered failure callback let client code
treat local and remote objects alike. The specific framework is dated; the surviving pattern is an
adapter that turns a pervasive failure into a registered policy (retry and circuit-breaker
wrappers, on-error hooks). It is a form of masking, so the same limit applies: only when callers do
not need to see each failure.

## 10. Warning signs

- Caller logic interleaved with status checks; comments narrating error states; deep nesting from
  status tests (CC ch. 3, ch. 7).
- The same handler body in several catch blocks; a catch of the broadest type that swallows; an
  empty catch (CC ch. 7).
- Declared-exception lists growing as a change ripples upward (CC ch. 7).
- Null checks throughout; methods returning null for "none"; null passed for an optional argument
  (CC ch. 7).
- Errors with no message, or a message that does not name the operation or entity (CC ch. 7).
- Sentinel returns: null, -1, NaN, empty string (FPiS ch. 4).
- Callers catching a generic library's exceptions in order to carry on a pipeline (FPiS ch. 4).
- A catch-all that returns "nothing" and so loses the reason (FPiS ch. 4).
- A result unwrapped at once (FPiS ch. 4).
- A flat-map chain validating many independent fields, so users see one error per attempt
  (FPiS ch. 4).
- Throwing and result-returning functions mixed within one module (FPiS ch. 4).
- A default branch that silently does nothing; code that records an impossible state and continues
  (PP ch. 4).

## 11. Verification

- For each public function: can a caller tell from the signature or contract how failure is
  signalled, and can the failure be silently ignored? (CC ch. 7.)
- Tests that force each failure path and assert the type and the content of the message; after the
  failure, assert the state is consistent (CC ch. 7).
- Counts of null returns and null comparisons fall; no empty handler without a justification;
  handlers grouped by body show no duplicates (CC ch. 7).
- With the wrapper faked to fail, callers never observe a vendor type (CC ch. 7).
- Each error log has operation, entity identifier and cause (marked inferred in the notes).
- Every function returning an optional or result has a test for each branch; a property test with
  random inputs showing no exception escapes code that claims to be total (inferred in the notes).
- Law-style checks for home-made combinators (inferred in the notes): mapping the identity changes
  nothing; combining two successes applies the function; a failure anywhere gives a failure;
  sequencing a list of successes gives a success of the list; traversing equals mapping then
  sequencing, and for the short-circuit form the function is not called after the first failure
  (use a counter).
- Review questions: can the caller tell from this signature everything that can go wrong; does any
  path swallow the reason?
