---
name: fp-pure-core
description: Procedures for structuring code so that decisions and calculations are pure functions and effects (I/O, mutation, time, randomness, ID generation) sit in a thin outer layer, in any mainstream language. Use when logic is hard to test without mocks or a live service, when a test is flaky because of clocks, random numbers or generated IDs, when a function both computes and sends/writes/prints, when effects need batching, deduplicating, dry-running or reordering, when hidden mutable state (fields, globals, counters, cursors) should become an explicit state value, reducer or state machine, when asked for "functional core, imperative shell", "make this pure" or "make this deterministic", or when judging in-place mutation inside a function. Effect types, interpreters and streaming belong to `fp-effects-and-streams`; folds, algebraic data types and typed errors belong to `fp-data-and-errors`.
---

# fp-pure-core

## Purpose

Use this skill to move decisions out of code that performs effects, so that the logic takes plain
values in and returns plain values out, and a thin outer layer does the reading, writing and
calling. The agent's work changes in three ways: it judges purity with a concrete test instead of
by feel, it refactors with a fixed procedure instead of reaching for a mock or an interface first,
and it proves the result with tests that compare returned values.

The material comes from a Scala book but nothing here needs Scala. Every technique is "return a
value instead of doing a thing", which works in TypeScript, Python, Rust, Kotlin, Java, Go, Swift
and C#.

## Choose what applies

| Situation in front of you | Use | Read |
|---|---|---|
| "Is this function pure?" or a review asks whether code has side effects | Substitution test (section 1 below) | `references/purity-and-substitution.md` |
| A function computes a result and also prints, sends, charges, writes or publishes | Split into input, pure function, output (section 2) | `references/separating-effects-procedure.md` |
| A test needs a mock only to observe that a call happened | Return a description of the effect (section 3) | `references/separating-effects-procedure.md` |
| The same effect must be batched, merged, deduplicated, counted, dry-run or reordered | Return a description and give it a combining operation (section 3) | `references/separating-effects-procedure.md` |
| A class or module has private mutable fields, a global, a counter, a cursor, or a state machine written as flags | State as a value: `step(state, input) -> (state', output)` (section 4) | `references/state-as-value.md` |
| A test fails only sometimes; logic calls the clock, a global random function, or a UUID/ID generator | Inject the source of nondeterminism (section 5) | `references/injecting-nondeterminism.md` |
| A pure function needs an in-place algorithm for speed (sort, table, buffer, builder) | Local mutation behind a pure interface (section 6) | `references/local-mutation.md` |
| Deciding whether logging, metrics, caching or allocation "count" as effects | Track the effects correctness depends on (section 7) | `references/purity-and-substitution.md` |
| Reviewing a diff or module for effect placement | Checklist | `references/review-checklist.md` |
| Need the idiom's name or shape in a specific language, or the language lacks a feature | Mappings | `references/language-mappings.md` |

This skill does not apply, or applies only lightly, when:

| Situation | What to do instead |
|---|---|
| The code is pure plumbing with no decisions (read a row, write a row) | Leave it. There is no logic to extract, and an integration test is the right test. |
| A one-off script or a throwaway prototype | Do at most the section 2 split if it makes the script easier to check by hand. |
| You need an IO type, swappable interpreters, a free structure, trampolining, or stream pipelines | `fp-effects-and-streams`. This skill stops at "return a description, run it at the edge". |
| You need to design the combinator set for a state or effect type, or check its laws | `fp-api-design-with-laws`. |
| The problem is how to represent failure in the returned value (optional, result, validation) | `fp-data-and-errors`, or `craft-error-handling` for the policy question. |
| The request is a small bug fix in imperative code that already has adequate tests | Fix the bug. Mention the purity issue only if it caused the bug. |

## How to apply

### 1. The substitution test (is it pure?)

An expression is referentially transparent if every occurrence of it in the program can be replaced
by the value it evaluates to without changing what the program means. A function is pure if calling
it with such arguments is always such an expression. In practice:

1. Pick the call you doubt. Name its result (`v = f(x)`).
2. Take a program that uses `v` twice. Rewrite it so each use is `f(x)` instead. Then go the other
   way: where `f(x)` appears twice, replace both with one `v`.
3. If either rewrite can change any result or any observable behaviour, `f` is not pure.

Worked cases: reversing an immutable string passes. Appending to a mutable string builder fails,
because binding the appended builder once and reading it twice gives equal strings, while inlining
the append at both sites appends twice. A `buyCoffee(card)` that charges the card and returns a
coffee fails, because replacing the call by "a coffee" loses the charge.

Fast signals, each a prompt to run the test and not a verdict:

- A return type of `void`/`Unit`/`None` usually means the function exists for its effect.
- The same expression gives different answers at different times or in a different order
  (clock, random, global, reused mutable builder).
- The function reads or writes anything not reachable from its parameters and return value.

What counts as an effect: reassigning a variable or mutating a structure visible outside the
function, setting a field, throwing or halting, console/file/network/database I/O, drawing to the
screen. Reading hidden changing state (clock, RNG, global) is as much a violation as writing it.

The rule that makes the rest of this skill work: everything a function does should be represented
in the value it returns. Input arrives by one route (arguments) and output leaves by one route
(the return value), so the logic can be reused where the attached effect would not be wanted.

### 2. Split into input, pure function, output

Any impure procedure can be factored into a step that obtains inputs, a pure function, and a step
that consumes the output, without changing behaviour.

1. Find the lines that perform I/O or mutate outside state.
2. Move every decision and calculation into functions that take plain values and return plain
   values. When "what should happen" is more than a primitive, return an optional, a result, an
   enum/sum type or a small record that says so.
3. Leave the effectful caller as plumbing: read inputs, call the core, write outputs.
4. Look at the plumbing again. If it still contains a decision (which destination, what text,
   whether to send), that decision is another pure function. Repeat until only primitive
   read/write calls remain.

Example of the shape: `contest(a, b)` that prints the winner becomes `winner(a, b)` returning an
optional player, `winnerMessage(optionalPlayer)` returning text, and a one-line caller that prints.

### 3. Return a description of the effect

Use this when the effect is the output of the logic (a charge, an email, a row to write, an event
to publish) and step 2 alone leaves the logic unable to say what should happen.

1. Identify the collaborator call inside the logic.
2. Define a small immutable record carrying exactly the data that call would take. Name it as a
   noun or command: `Charge`, `SendEmail`, `WriteRow`.
3. Return it alongside the normal result: a tuple, a result record, or a record with a list of
   commands. The function now knows nothing about the collaborator.
4. If merging is meaningful, add a combining function (two charges on the same card sum). Where
   combining can fail (different cards), return a typed error or optional; do not throw.
5. Build larger behaviour with ordinary collection operations on the descriptions: buy N by
   repeating the single purchase and reducing the charges; coalesce by grouping per card and
   reducing each group.
6. Write one `execute` function at the edge (main, controller, queue consumer) that turns
   descriptions into real calls.
7. Test the logic by equality on returned values. Test `execute` separately with a fake or an
   integration test.

Choosing how far to go, cheapest first:

| Need | Enough |
|---|---|
| Testable, readable logic | Section 2 split, passing values in and out |
| Logic must say what effect should happen; batching, dedup, dry-run | Section 3 description records plus one `execute` |
| Logic must read from the world between decisions | Split into stages, each pure, with the shell reading between them (adaptation); or pass a narrow interface with a fake in tests |
| Effects composed as values (stored, retried, scheduled, run in parallel), interpreters swapped, a component restricted to a declared set of operations, very long effectful loops | An effect type with an interpreter: `fp-effects-and-streams` |

Injecting an interface only so that a mock can observe a call is the half-measure to avoid as a
first step: it forces an abstraction where a concrete class would do, and the test ends up
inspecting the mock's recorded state. Separate first; introduce an interface when there really
are several implementations.

### 4. Hidden state becomes a value passed and returned

1. List the hidden state: private mutable fields, globals, counters, RNG, cursor or parser
   position, flags that together encode a mode.
2. Put it in one immutable record.
3. Rewrite each operation from "mutate and return A" to "take the state, return A and the next
   state". For event-driven code this is `step(state, input) -> state'` (a reducer); a run over
   many inputs is a fold of `step` from an initial state.
4. Hold the single mutable reference to the current state, if one is needed at all, in the shell.
5. Do not thread state by hand through long sequences. Reusing an old state value silently repeats
   a result (two "random" numbers that are equal). Use a fold, a small set of combinators
   (`map`, `flatMap`, `sequence`, `get`, `set`, `modify`), or an ownership system that forbids
   reuse.
6. Test by fixing the initial state and asserting on the pair of output and final state.

A loop is the same idea in small: its mutated variables are the state. Either write it as a
recursive helper whose parameters are the loop state (only where the language guarantees
tail-call elimination), or keep a local loop with local variables, which is invisible outside
(section 6), or use a fold.

### 5. Time, randomness and identifiers come in as arguments

Logic that calls the clock, a global random function or an ID generator is not a function of its
arguments, so a failure cannot be reproduced on demand.

- Prefer passing the value: `now` as a timestamp parameter, an already generated ID as a parameter.
- When the logic needs many values, pass a generator that is itself a value: each call returns
  the result and the next generator state, so the same seed always replays the same run.
- Passing a mutable seeded generator object is a partial fix: reproduction then needs the same
  seed and the same number of prior calls. Accept it where the host language makes it idiomatic,
  and create the generator in the test, not in a shared fixture (adaptation).
- Put the seed in every failure message so the failing run can be replayed (inferred).
- Reducing a random integer to a range with `% n` is biased; use rejection sampling or the
  library's range function. Taking the absolute value of the most negative integer overflows.

### 6. Local mutation behind a pure interface

A mutation inside a function is not a side effect if nothing outside the function can refer to
the mutated object. Use it freely for sorting in place, dynamic-programming tables, buffers and
builders.

1. Allocate the mutable structure inside the function, or copy the input into it. Do not mutate
   arguments.
2. Mutate only that structure.
3. Do not store it in a field, return it, capture it in a closure, iterator, generator or lazy
   sequence that outlives the call, or pass it to a callback you do not control.
4. Convert to an immutable value, or hand over sole ownership, on return.

Compiler enforcement exists (a scoped state type that relies on rank-2 polymorphism; ownership and
borrowing in Rust) but has notation and efficiency cost. Treat it as an available technique, not a
requirement for every helper.

### 7. Which effects to track

Purity is relative to what the program can observe. Allocating an object is observable through
reference identity, yet almost no program cares. So tracking an effect is a choice:

- Track (keep out of the core, or return as data) the effects that correctness depends on for the
  callers' notion of meaning: file and database writes, network calls, payment, the clock when
  logic depends on time, standard output when the program's output is its product.
- Do not track debug logging, metrics, memory allocation, or an internal cache that returns the
  same results and is safe under concurrency (the cache point is inferred).
- When in doubt, ask whether a caller's correct behaviour would change if the effect happened
  twice, never, or in a different order. If yes, track it.

Write the decision down where it is not obvious (for example, "logging inside the core is allowed
and is not asserted on").

## Verify

Checks to run, in the order that gives evidence fastest:

1. **Core tests use no doubles.** Tests of the extracted functions construct inputs, call, and
   compare returned values. No mock framework, spy, patch of a clock or random module, network or
   filesystem. Search the test files for the mocking library and report the count before and
   after.
2. **Core imports nothing effectful.** Search the core modules for I/O clients, clock, random,
   UUID, environment and logging-with-meaning calls. Example (adapt the patterns to the stack):
   `grep -rnE "Date\.now|new Date\(\)|Math\.random|randomUUID|datetime\.now|time\.time|random\.|uuid\.uuid|System\.currentTimeMillis|Instant\.now" src/core`.
   Each hit is either removed or listed with the reason it is allowed.
3. **Substitution holds.** For each function claimed pure, write a test that calls it twice with
   equal arguments and asserts equal results, and a test that the arguments are unchanged
   afterwards (deep-compare against a copy taken before the call).
4. **Behaviour unchanged.** Before refactoring, pin current behaviour with a characterisation
   test at the outer boundary (inputs in, effects recorded by a fake at the edge). It passes
   unchanged after the refactoring.
5. **Description records carry everything.** The `execute` function contains no conditionals on
   business data. If it does, a decision leaked out of the core.
6. **Combining operations.** Where descriptions are merged, test that the merge is associative and
   that coalescing preserves totals per key and yields at most one description per key
   (inferred properties).
7. **State as value.** Same initial state and inputs give the same output and final state on two
   runs; a run that draws two values gets two different draws and a final state different from
   the initial one; state-machine rules have one test each plus invariants (for example, a count
   that never goes negative).
8. **Nondeterminism.** Run the suite twice, and in a different order, with fixed seeds and a fixed
   `now`; results are identical. A failing property prints its seed.
9. **Local mutation.** Property test: the input is unchanged after the call, repeated calls give
   equal results, and the result equals a simple reference implementation on random inputs.
10. **One edge.** Each entry point (main, handler, consumer) is the only place that calls
    `execute` or holds the current-state reference. Show the call sites.

Evidence to show the user: the before and after signatures of the changed functions, the list of
effects that remain and where each lives, the mock count before and after, and the test run.

Done means:

- Every decision that was inside effectful code is now in a function whose result depends only on
  its arguments, or is listed as deliberately left with a reason.
- Effects are performed in named edge functions, and the logic states what they should be as data.
- Clock, randomness and ID sources enter through parameters wherever logic depends on them.
- Any in-place mutation is confined to structures created inside the function that mutates them.
- The checks above that apply have been run and their output shown, with skipped checks named.

## Proportion and limits

- Match the size of the change to the request. Extracting one pure function from the function
  being edited is usually welcome; restructuring a module into core and shell is a separate piece
  of work to propose, not to slip into a bug fix.
- Returning descriptions adds types and an `execute` step. It pays when the logic is worth
  testing in isolation or when effects need combining. For code that only forwards data it is
  ceremony.
- State passing copies state. That is cheap for small records and can be costly for large
  structures without persistent data structures; local mutation (section 6) is the sanctioned
  answer for hot paths.
- In languages without tuples, sum types or a binding syntax, the combinator style of state
  threading is verbose. Use the plain reducer form there; it is the same idea.
- Recursion as a loop depends on tail-call elimination, which most mainstream runtimes do not
  guarantee. Use a local loop or a fold in those languages.
- When the functional version feels tedious, the source's advice is that an abstraction is usually
  missing and worth finding. In a codebase whose conventions are imperative, weigh that against
  consistency with the surrounding code and the team's ability to maintain the result.
- An imperative implementation behind a functional interface is legitimate, but the foreword of
  the source notes it is often overused. Prefer pure components where they are not slower or
  harder to write, because they are easier to get right and compose better.
- The source's opening example is deliberately small and is not offered as proof that the
  functional form is better in general. Present the change as a refactoring with specific
  benefits (tests without doubles, batching), not as a matter of principle.
- No mainstream language outside the Haskell family checks purity. The boundary is kept by
  convention, module layout, review and the searches in the Verify section.
- The strict definition of purity has acknowledged subtleties (identity, timing, allocation).
  Section 7 is how to settle them: decide what counts as observable for this program.

## References

- `references/purity-and-substitution.md`: read when judging whether something is pure, explaining
  why, or deciding which effects are worth tracking.
- `references/separating-effects-procedure.md`: read before refactoring a function that mixes
  logic and effects; contains the step-by-step procedure with before and after in TypeScript and
  Python, and the ladder of how far to go.
- `references/state-as-value.md`: read when converting a stateful class, global, loop or flag-based
  state machine into explicit state; covers the reducer form, the combinator form and the
  state-reuse bug.
- `references/injecting-nondeterminism.md`: read when a test is flaky or logic depends on time,
  randomness or generated identifiers.
- `references/local-mutation.md`: read when a pure function wants in-place mutation, or when
  reviewing whether mutable data escapes.
- `references/review-checklist.md`: read when reviewing code or a design for effect placement; the
  questions have observable answers.
- `references/language-mappings.md`: read to find each idiom's name and shape in TypeScript,
  Python, Rust, Kotlin, Java, Go, Swift and C#, and what to do where a feature is missing.

## Sources

- Functional Programming in Scala, 1st ed. (Chiusano and Bjarnason), front matter and ch. 1:
  definitions of side effect, pure function and referential transparency; the effect-as-value
  refactoring.
- ch. 2: pure core with an impure shell as program shape; loops as state-passing recursion and
  tail calls.
- ch. 6: purely functional state, state actions, the general state type, state machines.
- ch. 13 (sections 13.1, 13.2, 13.6 and the decision rules): factoring effects outward, when a
  description type is warranted, a single impure entry point.
- ch. 14: local mutation behind a pure interface, scoped mutation enforced by types, purity as
  relative to what is observed.
