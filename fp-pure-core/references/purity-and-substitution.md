# Purity and the substitution test

Use this file to decide whether a piece of code is pure, to explain the verdict, and to decide
which effects are worth keeping out of the core. Citations are to Functional Programming in Scala,
1st ed. ("FPiS"). Items marked (inferred) are generalisations made in the study notes, not
statements of the book. Items marked (adaptation) are added here for use in other languages.

## Definitions

**Side effect** (FPiS ch. 1). A function has a side effect if it does anything other than return
a result. The book's list:

- reassigning a variable
- modifying a data structure in place
- setting a field on an object
- throwing an exception or halting with an error
- printing to or reading from the console
- reading from or writing to a file
- drawing on the screen

By extension the same holds for any network, database, queue or device call.

**Pure function** (FPiS ch. 1). A function from A to B relates every value of A to exactly one
value of B, determined only by the argument. No changing state, inside or outside the process,
plays a part in the result, and the call has no observable effect other than producing the
result.

**Referential transparency** (FPiS ch. 1, restated ch. 14). A property of expressions: an
expression is referentially transparent if, in every program, each occurrence can be replaced by
the result of evaluating it without changing the program's meaning. A function is pure if applying
it to referentially transparent arguments always gives a referentially transparent expression.

**Substitution model** (FPiS ch. 1). When all expressions have this property, evaluation is
replacing equals by equals, as in algebra. Reasoning becomes local: understanding a call needs
only its arguments, not a mental replay of the state changes that happened before it.

**Procedure versus function** (FPiS ch. 2). The book calls impure methods procedures and pure
ones functions. A program's shape is an outer shell of procedures calling a core of functions.

## Why it matters for the agent's work

A pure function separates three things that impure code welds together: how the input is obtained,
the logic of the computation, and what is done with the result (FPiS ch. 1). Input arrives only as
arguments and output leaves only as the return value. Consequences the book claims: such code is
easier to test, reuse, run in parallel, generalise and reason about. The practical test of each
claim is in the Verify section of `SKILL.md`.

The property that carries the weight: referential transparency forces everything a function does
to be represented by the value it returns, according to its result type (FPiS ch. 1). When that
holds, a signature is an honest summary.

## The test procedure

The book notes that nobody applies substitution mechanically in daily work because the answer is
usually obvious (FPiS ch. 1, footnote). Run it explicitly when the answer is not obvious or when
the verdict must be justified to someone.

1. Choose the expression in doubt, for example the call `f(x)`.
2. Write, or find, a small program that uses its result in two places through a name:
   `v = f(x); use(v); use(v)`.
3. Rewrite by inlining the definition at each use: `use(f(x)); use(f(x))`.
4. Compare the two programs' results and observable behaviour.
5. Also go the other way: where the code already has `f(x)` in two places, hoist it into one
   name and compare.
6. If any comparison can differ, the expression is not referentially transparent, and `f` is not
   pure.

A cheaper executable approximation (inferred): call the function twice with equal arguments and
compare; call it in a different order relative to other calls and compare; compare the arguments
before and after the call. This can show impurity but cannot prove purity.

### Worked cases from the book (FPiS ch. 1)

| Expression | Result of the test | Why |
|---|---|---|
| Reversing an immutable string bound to a name | Passes | Replacing the name by its definition, or the call by its value, changes nothing. |
| Appending to a mutable string builder, with the appended builder bound once and converted to a string twice | The two conversions agree | The append happened once. |
| The same, but with the append expression inlined at both uses | Fails | The builder is appended to twice, so the second string is longer. The rewrite changed the meaning, therefore append is not pure. |
| `buyCoffee(card)` that calls the payment service and returns a coffee | Fails | A program containing the call differs observably from the same program containing just "a coffee": the charge is gone. |

A fresh sketch of the builder case in Python, where a list plays the builder:

```python
def add_world(parts):          # mutates its argument
    parts.append("World")
    return parts

x = ["Hello"]
y = add_world(x)
r1, r2 = " ".join(y), " ".join(y)                       # equal

x = ["Hello"]
r1, r2 = " ".join(add_world(x)), " ".join(add_world(x)) # differ
```

## Signals that an effect is present

Each is a reason to look, not a conclusion.

| Signal | Source | What it usually means |
|---|---|---|
| Return type is `void`, `Unit`, `None`, `()` | FPiS ch. 2: such a return type is usually a hint of a side effect | The function exists for what it does, not what it returns. |
| A test needs a mock or stub of a collaborator only to observe that a call was made | FPiS ch. 1 | An effect is embedded in logic. |
| You want to call the function N times and merge the effects (batch, dedupe, one transaction) and cannot | FPiS ch. 1 | Same. |
| The same-looking expression gives different results at different times or in different order | FPiS ch. 1 (inferred phrasing) | Hidden clock, random source, global, or a reused mutable object. |
| A test fails only sometimes and cannot be reproduced on demand | FPiS ch. 6 | Hidden state in a random source or clock. |
| A "pure" function mutates its argument, a field or a global | FPiS ch. 14 | The mutation is observable by callers, so it is not local. |
| A returned view, iterator or slice aliases an internal mutable buffer | FPiS ch. 14 | The caller can watch the data change later. |

Reading counts as much as writing. A function that reads the clock, a global or a mutable field
does not have a result determined solely by its arguments, even if it writes nothing.

Throwing counts too (FPiS ch. 1). The book's own first example throws when asked to combine
charges on different cards, which it acknowledges and repairs later with typed errors. When
applying the technique, return an optional or result value instead; see `fp-data-and-errors`.

## Purity is judged at the boundary of observation

Two refinements keep the definition usable (FPiS ch. 1 preview, ch. 14).

**Local effects.** Nothing in the definitions forbids mutating state that is created inside a
function and never visible outside it. An in-place sort over a private copy is a pure function as
a whole, even though each inner helper would be impure on its own. See `local-mutation.md`.

**Contextual purity** (FPiS ch. 14). Constructing an object allocates, and the new object is
distinguishable from an equal one by reference identity. By the strict definition every
constructor call has an effect; almost no program observes it. So the definition is restated
relative to a program: an expression is referentially transparent with regard to a program if
replacing it by its value does not affect that program's meaning. What "meaning" includes
(standard output, object identity, timing, memory use) depends on the context, and is a choice
made by the programmer or the language designer.

**Effects versus side effects** (FPiS ch. 13). A program whose only impure function is the entry
point that runs a description has effects but not side effects, in the book's terms, because
nothing inside the program can observe the effects being performed.

## Deciding which effects to track

The book's policy (FPiS ch. 14): track the effects that program correctness depends on. Tracking
is a value judgement with costs and benefits.

| Effect | Track it (keep out of the core, or return it as data)? | Reasoning |
|---|---|---|
| File, database, network writes | Yes | Correctness depends on whether and how often they happen. |
| Reads from files, databases, network, environment | Yes | The result is not determined by the arguments. |
| Payment, email, message publication | Yes | Duplication or omission is a defect. |
| Clock | Yes when logic depends on time (expiry, scheduling, ordering) | The book's rule: clocks if the logic depends on time. |
| Randomness, generated identifiers | Yes when the values affect results or are asserted on | See `injecting-nondeterminism.md`. |
| Standard output | Depends | If output is the program's product (a command-line filter), track it. If it is a debug message, tracking it is wasted effort. This is the book's `timesTwo` example. |
| Debug logging, metrics | Usually no | Callers' correctness does not depend on them. (Metrics is inferred, by the same argument as logging.) |
| Memory allocation | No | With automatic memory management, the cost of tracking exceeds the benefit. |
| Reference identity | Only if the program relies on it | Then it must be known statically where it is relied upon. |
| Internal cache or memoisation | No, provided results are identical and it is safe under concurrency | (inferred, follows from contextual purity) |

A decision question that covers cases not in the table: would any caller's correct behaviour
change if this effect happened twice, not at all, or in a different order? If yes, track it.

Record non-obvious choices near the code (adaptation), for example a module comment stating that
logging inside the core is permitted and never asserted on.

## Hedges to keep when explaining this to a user

- The book states that the definition has subtleties it refines later (FPiS ch. 1 footnote,
  ch. 14).
- Its opening example is deliberately simple, and the full benefit is claimed only across the
  whole book. Present the technique as a refactoring with concrete gains, not as proof of a
  paradigm.
- The authors hold that several accepted practices (single responsibility, immutable data) are
  consequences of the same premise taken further. That is their framing; it is useful for
  explaining why an early refactoring looks like common sense.
- The host language of the book does not distinguish pure from impure functions in its types
  (FPiS foreword), and the same is true of most mainstream languages. Purity is a discipline
  supported by review and tests.

## Verify

- For a function claimed pure: a test calling it twice with equal arguments and asserting equal
  results; a test that arguments are unchanged; no test double in its tests.
- For a function claimed impure in a review: point at the specific read or write that is not an
  argument or the return value, or show the two programs from the test procedure that differ.
- For an effect deliberately left in the core: a written statement of why it is not observed by
  callers, and no test that asserts on it.
