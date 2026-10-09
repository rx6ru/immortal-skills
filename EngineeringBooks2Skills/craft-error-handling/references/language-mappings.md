# Language mappings

How the ideas in this skill appear in mainstream languages.

Status of this file: the source books are written around Java, C, C++, Eiffel and Scala. The study
notes give some cross-language mappings and mark most of them as inferred or as generalisation.
Items that come from the notes are tagged (notes). Everything else here is adaptation added so the
skill is usable today; treat it as a pointer to the idiom, and confirm details such as flags and
library names against the language's current documentation and the conventions of the repository
you are in. When the repository already has a convention, it wins.

## Contents

1. Concept to construct, at a glance
2. Per language: TypeScript, Python, Rust, Go, Java, Kotlin, Swift, C#, C and C++
3. Which assertion forms are stripped
4. What degrades when a language feature is missing
5. Service and API level equivalents

## 1. Concept to construct, at a glance

| Concept | TypeScript | Python | Rust | Go | Java | Kotlin | Swift | C# |
|---|---|---|---|---|---|---|---|---|
| Absent value, checked | `T \| undefined` under strict null checks (notes) | `Optional[T]` with a type checker (notes) | `Option<T>` (notes) | pointer or `(T, bool)` | `Optional<T>` for returns (notes) | `T?` (notes) | `T?` (notes) | `T?` with nullable reference types (notes) |
| Failure with reason, as a value | discriminated union (notes) | exceptions are idiomatic; result values at boundaries only (notes) | `Result<T, E>` (notes) | `(T, error)` (notes) | exceptions; library `Either`/`Try` (notes) | `Result`, library `Either` (notes) | `Result`, `throws` (notes) | exceptions |
| Propagate and keep the happy path flat | early return on `!r.ok` | let the exception rise | `?` (notes) | `if err != nil { return ... }` (notes) | let the exception rise | `?:`, `?.`, exception | `try`, `guard let` (notes) | let the exception rise |
| Add context when translating | `new Error(msg, { cause })` | `raise X(...) from e` (notes) | error enum variant with source; context helpers (notes name two crates) | `fmt.Errorf("...: %w", err)` (notes) | constructor with cause | constructor with cause | wrap in own error enum | constructor with inner exception |
| Bug: always-on check | explicit `throw`, assert function | explicit `raise` | `assert!`, `panic!`, `unreachable!` | `panic` | explicit throw, `Objects.requireNonNull` (notes) | `require`, `check` (notes) | `precondition`, `fatalError` | explicit throw, guard helpers |
| Bug: strippable check | none built in | `assert` (notes) | `debug_assert!` | none built in | `assert` (notes) | `assert` | `assert` | `Debug.Assert` |
| Exhaustive dispatch on a closed set | union + `never` check | `match` + checker's exhaustiveness helper | `match` | switch with failing `default` | sealed types + pattern switch (notes) | `when` on sealed | `switch` on enum | switch expression with failing default |
| Scoped release | `try/finally`; `using` where available | `with` (notes) | `Drop` (notes) | `defer` (notes) | try-with-resources (notes) | `use { }` | `defer` | `using` (notes) |
| Collect all validation errors | schema library collecting issues (notes) | model-validation library collecting errors (notes) | hand-written collector, or a validation crate (notes) | append to a slice; join errors | library `Validation` (notes) | library accumulate form (notes) | hand-written collector | hand-written collector or library |
| Combine independent async work | `Promise.all` (notes) | `asyncio.gather` (notes) | `join!` (notes) | wait group / error group | `CompletableFuture.allOf` (notes) | `awaitAll` | `async let`, task group | `Task.WhenAll` |

## 2. Per language

### TypeScript and JavaScript

- **Expected outcomes**: a discriminated union such as `{ ok: true, value } | { ok: false, error }`,
  or a library result type; narrowing on the tag takes the place of pattern matching (notes). The
  notes name two libraries as examples; check what the repository uses before adding one.
- **Absence**: `T | undefined` with strict null checking is the lightweight optional (notes).
  Without strict mode the compiler does not force handling and the benefit is lost (notes).
- **Unexpected failures**: throw `Error` subclasses; pass the original as `cause`.
- **Typing gap**: thrown values are untyped at the catch site, so a function's failure modes are
  not in its signature. This is the visibility problem the result-type school describes; prefer a
  result return for failures callers are expected to handle.
- **Async**: a promise that is created and neither awaited nor given a handler is the async form
  of an ignored return code; what happens to its rejection depends on the runtime (some only log
  it), so do not rely on it surfacing.
- **Independent work**: `Promise.all` for all-or-first-failure; a settle-all form when every
  outcome is wanted (the accumulate semantics).
- **Assertions**: there is no strippable built-in, so a small `invariant(cond, msg)` function that
  throws is always on. An assertion function typed to narrow gives the checker the fact as well.
- **Exhaustiveness**: assign the unreachable case to a `never`-typed variable in the default
  branch so adding a variant is a compile error.
- **Validation**: schema validators that return a list of issues from a safe-parse call are
  accumulating validation in practice (notes).

### Python

- **Convention**: exceptions are the idiom, including for some ordinary control flow, and
  attempt-then-handle is preferred to check-then-act; check-then-open is also a race in concurrent
  or security-sensitive code (notes). So: attempt, catch the specific exception next to the call,
  and convert to a value or a domain exception there.
- **Expected outcomes**: return `T | None` with type checking for simple absence; a small result
  dataclass or a `(value, errors)` pair at API boundaries; a library result type only if the
  codebase already uses one (notes).
- **Context**: `raise DomainError("...") from err` keeps the cause (notes). Build a small
  hierarchy under one base class per package (notes).
- **Do not**: bare `except:` or `except Exception: pass`. Catch-all is for the outermost boundary
  only.
- **Assertions**: `assert` is removed under `-O` (notes). For checks that must stay, raise
  explicitly or use a helper that does. Never validate input with `assert`.
- **Contracts**: contract libraries exist (the notes name two); property-based tests serve as
  executable postconditions (notes).
- **Resources**: `with` and context managers (notes); an exit stack when the number of resources
  is dynamic.
- **Validation**: model-validation libraries collect all errors in one exception (notes).

### Rust

- **Expected outcomes**: `Option<T>` and `Result<T, E>`; `?` is the chaining operation (notes);
  `ok_or` turns an option into a result (notes).
- **Traverse**: `iter().map(f).collect::<Result<Vec<_>, _>>()` collects or stops at the first
  error (notes). To accumulate instead, partition results or push into a `Vec` of errors, or use a
  validation crate (notes).
- **Error types**: an enum per module or crate, with variants chosen by what callers match on;
  the notes mention one crate for defining such enums and one for opaque application-level errors
  with context. The split matches "define errors by the caller's needs": typed for libraries whose
  callers branch, opaque for application code that only reports.
- **Bugs**: `panic!`, `unreachable!`, `assert!` are always on; `debug_assert!` is removed in
  release builds. `unwrap()` and `expect()` outside tests are assertions; each should correspond to
  a real invariant, with `expect` text saying why it cannot fail.
- **Must-use**: an unused `Result` produces a warning, which is the "cannot be ignored" property.
- **Resources**: `Drop` releases at scope end in reverse declaration order (notes).
- **Memory integrity**: in safe code the borrow checker enforces it (notes list it as a modern
  analogue of memory checkers); `unsafe` blocks still need a sanitizer or Miri.

### Go

- **Expected and unexpected failures alike** are `error` return values; `panic` is for bugs. This
  matches the expected-versus-impossible split (notes).
- **No map or flat-map**, so chains are written as `if err != nil` returns (notes). Keep each
  check to a one-line return with added context so the happy path stays in the left column.
- **Context**: wrap with `%w` (notes); test with the standard `Is`/`As` helpers. Keep errors typed:
  sentinel values or error types for the cases callers branch on (notes).
- **Ignored errors**: `_ = f()` or a call whose error result is dropped is the ignored return
  code. Linters catch this; without one, grep for it.
- **Absence**: the `value, ok` form for lookups; avoid returning a nil pointer with a nil error
  for "not found".
- **Assertions**: none built in; an `if !cond { panic(...) }` helper is always on.
- **Resources**: `defer` immediately after a successful acquire; deferred calls run in reverse
  order (notes for `defer`). Check the error from the acquire before deferring the release.
- **Accumulation**: collect into a slice of errors and join them.

### Java

- **Exceptions**: unchecked for the unexpected in application code; a checked exception only where
  the caller must handle a recoverable, expected failure right there (notes on the dated
  "debate is over" claim). Translate at layer boundaries.
- **Absence**: `Optional<T>` as a return type; discouraged for fields and parameters (notes).
  Empty collections instead of null (notes).
- **Null arguments**: forbid by convention; `Objects.requireNonNull` at entry is a fail-fast guard
  (notes).
- **Assertions**: the `assert` statement is off unless enabled with `-ea` (notes). Use explicit
  throws for checks meant to stay.
- **Exhaustiveness**: sealed types with pattern-matching switch (notes mention Java 21).
- **Resources**: try-with-resources (notes); `finally` otherwise. Finalisers are not a release
  mechanism (notes).
- **Values**: library `Either`, `Try` and `Validation` types exist (notes name one library).

### Kotlin

- **Absence**: nullable types enforced by the compiler; `?.` and `?:` (notes).
- **No checked exceptions** (notes). Use sealed result types or the standard `Result` for expected
  outcomes; a functional library offers `Either` and an accumulating form (notes).
- **Contracts**: `require` for arguments and `check` for state are always on (notes); `assert`
  follows the JVM flag.
- **Exhaustiveness**: `when` over a sealed type.
- **Resources**: `use { }` on closeable objects.

### Swift

- **Absence**: `Optional`; `guard let` for early exit (notes).
- **Failures**: `throws` (typed in recent versions, notes) and `Result`.
- **Checks**: `precondition` and `fatalError` remain in ordinary optimised builds, while `assert`
  does not; the unchecked optimisation level also drops `precondition`. Confirm for the build
  settings in use.
- **Resources**: `defer`; deterministic release through reference counting.

### C#

- **Absence**: nullable reference types with compile-time checking (notes).
- **Failures**: exceptions; no checked exceptions (notes via CC ch. 7). The try-pattern
  (`bool TryX(..., out T)`) is the conventional non-throwing form for an expected outcome, which
  is what the "offer a non-throwing form" advice asks for.
- **Checks**: explicit throws and guard helpers are always on; `Debug.Assert` is removed from
  release builds.
- **Resources**: `using` (notes).

### C and C++

- **C**: no exceptions; return codes are unavoidable. Reduce the damage: a checking macro for
  calls that must not fail, aborting with file, line, call text, expected and actual (PP ch. 4); an
  aborting wrapper around allocation (PoSD ch. 10); registered error handlers where a category of
  failure should have one policy (PP ch. 4). Avoid one global error-code header that everything
  includes (CC ch. 3).
- **Assertions**: `assert` becomes a no-op under `NDEBUG`, and its argument is then not evaluated
  (notes). Define your own always-on macro for the checks to keep.
- **C++ resources**: constructor acquires, destructor releases; keep the object on the stack or
  hold it through an owning pointer. The smart pointer named in the 1999 text (`auto_ptr`) is
  deprecated and removed from current standards; use the unique and shared owners (notes).
- **Exception safety**: the notes mention the basic, strong and no-throw guarantees as the
  formalisation of "the handler leaves state consistent".
- **Memory integrity**: run a memory checker or sanitizer first when behaviour is strange
  (WPF ch. 10; current tools named in the notes are compiler sanitizers and a binary-level
  checker). See `craft-debugging`.
- **Unchecked arithmetic**: an out-of-domain call such as a square root of a negative number
  yields a silent NaN that surfaces later in unrelated code (PP ch. 4); assert the domain.

## 3. Which assertion forms are stripped

The advice in this skill is: input, security and critical-result checks are never strippable;
cheap internal checks stay on; only measured-expensive ones are optional. To apply it you need to
know which construct is which.

| Language | Stripped or off by default | Always on |
|---|---|---|
| C, C++ | `assert` under `NDEBUG` (notes) | own macro, explicit `abort` |
| Java | `assert` unless `-ea` (notes) | explicit throw, `Objects.requireNonNull` |
| Python | `assert` under `-O` (notes) | explicit `raise` |
| Rust | `debug_assert!` in release | `assert!`, `panic!` |
| Swift | `assert` in optimised builds (`precondition` too under the unchecked level) | `precondition`, `fatalError` |
| C# | `Debug.Assert` in release | explicit throw |
| Kotlin | `assert` (JVM flag) | `require`, `check` (notes) |
| Go, TypeScript | no strippable built-in | helper that panics or throws |

Rows other than those tagged (notes) are adaptation; confirm for the toolchain in use, since build
profiles can change these defaults.

## 4. What degrades when a language feature is missing

From the notes (FPiS ch. 4 generalisation, marked inferred there):

- **No sum types or tagged unions**: use a result struct with an `ok` flag and an error field, and
  discipline. The compiler no longer prevents reading the value on the failure branch.
- **No generics**: you lose uniform map/flat-map helpers and write per-type code.
- **No enforced null checking**: an optional by convention loses the "compiler makes you handle
  it" benefit; rely on linters and tests.
- **No higher-kinded types**: not needed for any single result type. Write map, flat-map, combine,
  sequence and traverse per type, as mainstream libraries do; only abstracting over all such types
  at once needs them.
- **No exceptions** (C, and by choice Go and Rust): the ideas about reducing, masking and
  aggregating apply equally to error return values (PoSD ch. 10 notes).
- **No deterministic destruction** (garbage-collected languages): scope-bound release must use the
  block construct; object lifetime is not a release mechanism (PP ch. 4).
- **No contract support**: assertions emulate contracts with gaps: no inheritance of checks, no
  old values, unchecked library boundary (PP ch. 4).

## 5. Service and API level equivalents

The notes generalise the module-level techniques to APIs (PoSD ch. 10, marked as generalisation):

| Technique | Equivalent |
|---|---|
| Define away | Idempotent delete and put, upsert, "ensure" operations, an empty list for a filtered query with no matches where that suits consumers |
| Mask | Retries and timeouts inside a client SDK |
| Aggregate | Central error middleware or exception filter |
| Special case | Null object, empty collection |
| Promote / crash | Supervised restart of a worker or process |

For the design of error responses in an HTTP or RPC API see `arch-api-design`; for retries that
need idempotency see `arch-transactions`.
