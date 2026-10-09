# Language mappings for the pure-core techniques

What each idiom in this skill is called and looks like in mainstream languages, and what to do
where a feature is missing.

Status of this file: the source book uses Scala only. The study notes contain cross-language
remarks marked as inferred; those are repeated here with that label. Everything else in this file
is adaptation written for this skill. Treat specific library and feature names as pointers to
verify against the version of the language and libraries in the repository, not as claims of the
book.

## Contents

1. What the techniques need from a language
2. Feature matrix
3. Per-language notes: TypeScript and JavaScript, Python, Rust, Kotlin, Java, Go, Swift, C#
4. Degradation guide: what to do when a feature is missing
5. Verify

## 1. What the techniques need from a language

| Technique | Needs | Source of the requirement |
|---|---|---|
| Split into input, pure function, output | Nothing special; functions and return values | Notes on FPiS ch. 13 (inferred): works in any language |
| Return a description of the effect | Immutable records or tuples; collection operations (map, group, reduce) for combining | Notes on FPiS ch. 1 (inferred) |
| Closed set of descriptions or inputs | Sum types with exhaustive matching, or a struct with a tag | Notes on FPiS ch. 1 (inferred) |
| State as a value, reducer form | Immutable record with a copy-with-change operation; fold | Notes on FPiS ch. 6 (inferred) |
| State as a value, combinator form | Pairs, closures, generics; ideally a binding syntax. Higher-kinded types are not needed for one state type | Notes on FPiS ch. 6 (inferred) |
| Loops as recursion | Guaranteed tail-call elimination for self calls | FPiS ch. 2; cross-language matrix inferred |
| Local mutation behind a pure interface | Nothing; enforcement needs ownership or rank-2 polymorphism | FPiS ch. 14; cross-language notes inferred |
| Injected time, randomness, IDs | Parameters; a seedable generator | FPiS ch. 6 for randomness; rest inferred |

## 2. Feature matrix

"Conv." means by convention only, with no compiler support.

| | Immutable record | Copy with change | Sum type with exhaustive match | Tuple or multiple return | Self tail-call elimination | Purity checked | Local-mutation enforcement |
|---|---|---|---|---|---|---|---|
| TypeScript | `Readonly<T>`, `readonly` fields (compile-time only) | object spread | discriminated union plus `never` check | array tuple types | not guaranteed | no | `readonly` types only |
| Python | `@dataclass(frozen=True)`, `NamedTuple` | `dataclasses.replace` | union of dataclasses with `match`; exhaustiveness via a type checker | tuples | no | no | conv. |
| Rust | structs are immutable unless bound `mut` | struct update syntax | `enum` with `match` | tuples | not guaranteed | no (no effect system) | ownership and borrowing |
| Kotlin | `data class` with `val` | `copy(...)` | `sealed` hierarchy with `when` | `Pair`, `Triple`, data classes | `tailrec` keyword | no | conv. |
| Java | `record` | hand-written "with" methods | `sealed` interface with pattern `switch` in recent versions | small record | no | no | conv. |
| Go | struct passed by value | assign to a copy | none; interface or struct with a kind field | multiple return values | no | no | conv. |
| Swift | `struct` with `let` | copy and assign to a `var` copy | `enum` with associated values and `switch` | tuples | not guaranteed | no | value semantics help |
| C# | `record` | `with` expression | none built in; record hierarchy with `switch` patterns | tuples | not guaranteed | no | conv. |

The tail-call column follows the notes' inferred matrix: guaranteed for self calls in Scala (with
an annotation that fails the build otherwise), Kotlin (`tailrec`), Haskell, OCaml, Scheme,
Erlang and Elixir, and Clojure through explicit `recur`; not guaranteed in Java, Python,
JavaScript (the language specification's tail calls are in effect implemented by one engine
family only), Go, Rust and C#. Swift's entry is adaptation.

## 3. Per-language notes

Each entry uses the same headings: effect description, state as value, nondeterminism, local
mutation, shell, watch for.

### TypeScript and JavaScript

- **Effect description**: discriminated union of plain objects with a `kind` field; return a
  `readonly Command[]` or a `{ result, commands }` object. Add an exhaustiveness check in the
  executor's `switch` (assign the unmatched value to `never`).
- **State as value**: reducer `(state, input) => state` with object spread, driven by
  `Array.prototype.reduce`. This is the same shape as the update functions of reducer-style
  state libraries (inferred equivalence in the notes).
- **Nondeterminism**: pass `now: number` or a `Date` created by the shell; pass a `() => number`
  only where a single value will not do. `Math.random` cannot be seeded, so randomness has to be
  a parameter (a seeded generator function or library).
- **Local mutation**: `const out = []; ...; return out` (inferred as idiomatic in the notes).
  `ReadonlyArray` and `readonly` are erased at run time, so a retained mutable reference still
  aliases.
- **Shell**: the request handler, CLI `main`, queue consumer or UI event handler.
- **Watch for**: a `Promise` is eager, so it is not a description of an effect; it has already
  started. A deferred description is a thunk `() => Promise<T>` (inferred in the notes on
  FPiS ch. 13). Object spread is shallow, so nested mutable objects remain shared.

### Python

- **Effect description**: frozen dataclasses or `NamedTuple`s; return a tuple
  `(result, [commands])`. Dispatch in the executor with `match` or `isinstance`.
- **State as value**: frozen dataclass plus `dataclasses.replace`; drive with
  `functools.reduce` or an explicit loop in the shell.
- **Nondeterminism**: pass `now` as a `datetime`; pass a `random.Random(seed)` instance created
  by the caller (this is the partial fix of FPiS ch. 6: reproducible only with the same seed and
  the same sequence of prior calls), or pass a seed and build the instance inside the function.
- **Local mutation**: `list.append` in a local list, then return it or `tuple(...)` (inferred as
  idiomatic in the notes). Do not use a mutable default argument as scratch space; it persists
  across calls and is observable.
- **Shell**: `main()`, the web framework's view function, a task function.
- **Watch for**: no tail-call elimination and a modest default recursion limit, so recursion as a
  loop is unsuitable; use loops or `reduce`. `frozen=True` is shallow. Generators are lazy and
  capture local variables, which is an escape route for local mutable state (FPiS ch. 14 warning
  on closures and lazy sequences).

### Rust

- **Effect description**: an `enum` of commands with data; return `(T, Vec<Command>)`. `match`
  is exhaustive by default.
- **State as value**: `fn step(state: State, input: Input) -> State`, taking the state by value.
  Because the old state is moved, reusing it is a compile error, which removes the state-reuse
  bug of FPiS ch. 6 (inferred in the notes). This holds only while the state type is not `Copy`
  and not `Clone`d at the call site; a `Copy` state can be reused silently. `Iterator::fold` and `scan` drive it.
- **Nondeterminism**: pass a timestamp value; pass `&mut impl Rng` created from a seed by the
  caller, or take and return the generator by value for the fully pure form.
- **Local mutation**: a `let mut v = Vec::new()` filled and then returned by move is the normal
  style. Exclusive `&mut` borrows give both invariants of FPiS ch. 14 natively (inferred in the
  notes).
- **Shell**: `main`, handler functions, the task that owns the I/O resources.
- **Watch for**: a function taking `&mut` on its argument is an in-place mutation visible to the
  caller. That is explicit in the signature, which makes it honest, but it is not the pure
  interface; choose deliberately. Interior mutability (`RefCell`, `Mutex`, atomics) reintroduces
  hidden state behind a shared reference. Futures are lazy until polled, so an unspawned future
  is a description (inferred in the notes). Tail calls are not guaranteed; use loops or iterator
  adaptors.

### Kotlin

- **Effect description**: `sealed interface Command` with `data class` cases; return a
  `Pair<Result, List<Command>>` or a small data class. `when` over a sealed type is exhaustive
  (the compiler checks the cases of a `when` over a sealed type; verify the rule for `when`
  statements against the Kotlin version in use).
- **State as value**: `data class` with `copy`, driven by `fold`.
- **Nondeterminism**: pass an `Instant`; pass a `kotlin.random.Random(seed)` created by the
  caller.
- **Local mutation**: `buildList { ... }` and `buildString { ... }` are the idiom (inferred in
  the notes): mutable inside the block, read-only type outside.
- **Shell**: `main`, controller, coroutine entry point.
- **Watch for**: `List` is a read-only interface, not an immutable collection; a `MutableList`
  behind it can still change. `tailrec` marks a self call that must be eliminated and the compiler
  reports when it cannot be (a warning rather than the build failure of the Scala annotation in
  FPiS ch. 2; check the diagnostics level of the project's build).

### Java

- **Effect description**: `sealed interface` with `record` implementations; pattern-matching
  `switch` in recent versions. On older versions use a class per command and a visitor or an
  `instanceof` chain (the degraded form in the notes: plain class plus a tag).
- **State as value**: records with hand-written "with" methods; drive with a loop in the shell or
  `Stream.reduce` for simple cases.
- **Nondeterminism**: pass an `Instant`, or a `java.time.Clock` (a fixed clock in tests); pass a
  `Random` constructed from a seed by the caller.
- **Local mutation**: `StringBuilder` then `toString`; `ArrayList` then `List.copyOf` (inferred
  in the notes).
- **Shell**: `main`, controller method, message listener.
- **Watch for**: `Collections.unmodifiableList` is a view, not a copy, which is exactly the
  aliasing hazard described in FPiS ch. 14 (inferred in the notes). No tail-call elimination.
  Records are shallowly immutable. Without tuples, return a small record (notes on FPiS ch. 1).

### Go

- **Effect description**: no sum types. Use a struct with a kind field, or an interface with one
  struct per command and a type switch in the executor (the degraded form in the notes). Multiple
  return values serve as the tuple: `func decide(...) (Result, []Command)`.
- **State as value**: structs passed and returned by value; `func step(s State, in Input) State`.
  Drive with a `for` loop in the shell.
- **Nondeterminism**: pass a `time.Time`; pass a `*rand.Rand` created from a seed by the caller.
- **Local mutation**: build a slice locally and return it, keeping no reference. The notes
  mention copying slices before return (inferred); copy when the slice shares a backing array
  with something the function keeps or was given.
- **Shell**: `main`, HTTP handlers, goroutines that own connections.
- **Watch for**: slices and maps inside a struct are references, so passing the struct by value
  still shares them; `append` may or may not reallocate, so two slices can alias the same backing
  array unpredictably. A type switch is not checked for exhaustiveness; add a default branch that
  fails loudly and a test that covers every command kind. The combinator form of state threading
  is verbose here; use the reducer form (notes on FPiS ch. 6, inferred). Growable stacks make
  deep recursion less immediately fatal, but it is still bounded by memory (inferred in the
  notes).

### Swift

- **Effect description**: `enum Command` with associated values; return a tuple
  `(result: T, commands: [Command])`. `switch` is exhaustive.
- **State as value**: `struct` state; `func step(_ s: State, _ i: Input) -> State`, driven by
  `reduce`. Value semantics mean a copy is independent.
- **Nondeterminism**: pass a `Date`; make functions generic over a `RandomNumberGenerator` and
  supply a seeded implementation in tests.
- **Local mutation**: a local `var` array or a `mutating` helper on a local value, returned by
  value.
- **Shell**: the app entry point, view-model actions, request handlers.
- **Watch for**: `inout` parameters and `mutating` methods on a caller's value are visible
  mutations of the argument. Classes have reference semantics; a struct holding a class
  instance shares it.

### C#

- **Effect description**: `abstract record Command` with derived records; `switch` expression
  with type patterns in the executor. There is no closed hierarchy check, so include a default
  arm that throws and a test that covers every case.
- **State as value**: `record` with `with` expressions, driven by LINQ `Aggregate`.
- **Nondeterminism**: pass a `DateTimeOffset`, or the platform's time abstraction where the
  codebase uses one; pass a `Random` constructed from a seed by the caller.
- **Local mutation**: `StringBuilder`, or `List<T>` filled locally and returned as an immutable
  collection or by sole ownership.
- **Shell**: `Main`, controller action, hosted service.
- **Watch for**: `IReadOnlyList<T>` is a read-only view over a possibly mutable list. `Task<T>`
  is usually already running, so it is not a description; use `Func<Task<T>>` for a deferred one
  (the eager-versus-lazy point in the notes on FPiS ch. 13, applied here as adaptation).

## 4. Degradation guide

| Missing feature | Effect on the techniques | What to do |
|---|---|---|
| No sum types (Go, older Java, C#) | The set of commands or inputs is not closed, so a new kind can be forgotten in the executor | Struct with a kind tag or interface plus type switch; default branch that fails; a test enumerating every kind (notes on FPiS ch. 1 for the first part) |
| No tuples (Java) | Cannot return result and description as a pair | Small named result record (notes on FPiS ch. 1). Often clearer than a tuple anyway |
| No pattern matching | Executor and transition functions are `if` chains | Keep one branch per case, in the same order as the rule table |
| No guaranteed tail calls (most mainstream runtimes) | Recursion as a loop can overflow the stack on large input | A local loop with local variables, which is invisible outside the function, or a fold (notes on FPiS ch. 2, inferred). For recursion that cannot be turned into a loop, see `fp-effects-and-streams` on trampolining |
| No binding syntax for chained state actions (Go, Java, Python) | The combinator form of state threading is verbose | Reducer form: immutable record and `step(state, input)` (notes on FPiS ch. 6, inferred) |
| No higher-kinded types (none of the eight languages here has them as such) | Cannot write one set of combinators for every state-like or effect-like type | Not needed for this skill: define the combinators for the one concrete type in use (notes on FPiS ch. 6) |
| No deep immutability (TypeScript, Python, Java, Kotlin, C#) | A "frozen" record can hold a mutable collection | Use immutable collection types inside records, copy at boundaries, and test that inputs are unchanged |
| No purity checking (every language in this list) | The core can silently acquire an effect | Module layout (core imports no I/O modules), a lint or search in CI for forbidden imports in core paths, review with `review-checklist.md` |
| No laziness by default | A description must be data or an explicit thunk; an eagerly started task is not a description | Plain records for descriptions; thunks where deferral is required (notes on FPiS ch. 13, inferred) |
| No rank-2 polymorphism | The scoped-state enforcement of local mutation is unavailable | Ownership (Rust), privacy, defensive copies, and the tests in `local-mutation.md` (notes on FPiS ch. 14) |
| Expression-poor syntax (statement `if`, no block values) | Tempting to assign a variable in each branch | Conditional expression or a small helper function returning the value; avoid mutating one variable across branches (notes on FPiS ch. 2) |

## 5. Verify

- The mapping chosen for the repository's language is the one its existing code already uses,
  where there is one. Find an existing immutable record, sum type or reducer in the codebase and
  follow its form.
- Each "watch for" item for the language has been checked against the changed code: for example,
  in TypeScript no description holds a `Promise`; in Java no unmodifiable view is returned over
  an internal list; in Go no returned slice shares a backing array that is retained.
- The executor fails loudly on an unknown command kind in languages without exhaustive matching,
  and a test covers every kind.
- Any library or language feature named in this file has been confirmed to exist in the version
  the repository uses before relying on it.
