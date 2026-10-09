# Worked evolutions: how four libraries reached their final form

Each library is given as a sequence of stages: what the design was, what forced a change, what
changed, and the transferable lesson. Use these as precedents when your own design hits a similar
moment. "FPiS" is Functional Programming in Scala, 1st ed. "(inferred)" marks items the notes flag as
reconstructed. Signatures are written in a neutral notation: `A -> B` is a function, `F<A>` a generic
type, `(A, B)` a pair.

## Contents

1. State actions (ch. 6)
2. Parallel computations (ch. 7)
3. Property testing (ch. 8)
4. Parser combinators (ch. 9)
5. From three libraries to shared abstractions (ch. 10 to 12)
6. Triggers and responses across all four
7. Using a precedent

## 1. State actions (FPiS ch. 6)

The shortest of the four, and the one the later libraries build on.

| Stage | Design | What forced the next step |
|---|---|---|
| 1 | A random generator with hidden internal state; each call mutates it | A die-roll function with an off-by-one passes most of the time and its failure cannot be reproduced |
| 2 | Pass the generator in as an argument | Still unreproducible: you need the same seed and the same number of prior calls, since each call destroys the previous state |
| 3 | Make the update explicit: `next: Rng -> (Int, Rng)`. Return the new state with the value | The caller must thread the state by hand. Reusing an old state silently yields the same number twice |
| 4 | Notice that every function has the shape `Rng -> (A, Rng)`. Name it (a state action) and write `unit`, `map`, `map2`, `sequence` so application code never mentions the state | A range function built with `map` and a modulus is biased, and the fix (retry on a bad draw) cannot be written with `map` because the next action depends on the drawn value |
| 5 | Add `flatMap`; rebuild `map` and `map2` from it | None of the combinators use anything about random generators |
| 6 | Generalise to `State<S, A> = S -> (A, S)`. The implementations do not change. Add two primitives, `get` and `set`, and derive `modify` | |

**Payoffs shown.** A failing run is fully described by the function and the seed, so the off-by-one is
found by searching seeds and then reproduced at will, with no mock. A vending-machine exercise becomes
a pure transition function from input and machine to machine, lifted and sequenced over a list of
inputs.

**Lessons.**
- The mechanical translation works for any stateful API: each mutating method returns its result
  paired with the next state.
- Tedium signals a missing abstraction. Hand-threading over many lines is both the boredom and the
  bug source.
- A more general signature may already fit your implementation unchanged.
- With `get`, `set` and the sequencing combinators, any state machine can be written purely. In
  languages without a convenient chaining syntax the same idea is a plain step function
  `(state, input) -> (state, output)` folded over inputs (inferred); see `fp-pure-core`.

## 2. Parallel computations (FPiS ch. 7)

| Stage | Design | What forced the next step |
|---|---|---|
| 1 | Use case: sum a list by splitting it. Read off `Par<A>`, `unit(a)`, `get(par)` | If `unit` starts work at once, `get(l) + get(r)` is parallel only until someone inlines `l` and `r`; then it is sequential. `get` exposes a side effect and breaks substitution |
| 2 | Do not `get` in the middle. Return `Par<Int>` from the sum and combine with `map2(pa, pb)(f)` | Is `map2` strict? A hand trace shows a strict `map2` builds the entire left half of the tree before the right half exists |
| 3 | Make `map2` lazy and start both sides in parallel | `map2(unit(1), unit(1))` should obviously not spawn anything, and the API cannot say so. Combining and scheduling are mixed |
| 4 | Add `fork(par)`: run this on a separate logical thread. `map2` and `unit` become strict. `lazyUnit(a) = fork(unit(a))` is derived | Does `fork` start work when called, or later? |
| 5 | Reason by information needed: starting at once requires a global pool. So `fork` only marks; an interpreter does the work. Rename `get` to `run`. `Par` is now a description | Need a representation |
| 6 | `Par<A> = Executor -> Future<A>`; `run(executor)(par)` applies it. A future is returned, not a bare value, so the caller keeps timeout and cancellation. Adopted provisionally | First implementation: `map2` waits on both futures and does not itself fork; `fork` submits a task that waits for the inner computation. Known weaknesses recorded: timeouts ignored by `map2`, and `fork` occupies a thread just to wait |
| 7 | Explore what is expressible: `map` from `map2`; `asyncF` to lift a function; `sequence` by folding with `map2`; `parMap = fork(sequence(xs.map(asyncF(f))))`; parallel filter | Reasoning has been informal |
| 8 | State laws: `map(y)(id) == y`; `fork(x) == x`. Define equality as "same value under any executor" | Attacking `fork(x) == x` with a one-thread pool: the outer task holds the thread and waits for an inner task that cannot start. Deadlock, on any fixed-size pool |
| 9 | Options: restrict the law to unbounded pools, or fix the implementation. A non-forking `fork` satisfies the law vacuously and is kept as `delay` | The root cause is that a value cannot be taken from the substrate's future without blocking |
| 10 | New representation: a future is something that accepts a callback. `unit` calls the callback at once; `fork` submits the evaluation to the executor; `map2` uses a small actor to collect the two results and fire once both are in. Only `run` blocks, through a latch | Exceptions are swallowed (the latch is never released); left as an exercise |
| 11 | Generalise: `choice` to `choiceN` to `choiceMap` to `chooser`, which is `flatMap`; then `join` | Open: laws for `join`; what cannot be expressed |

**Lessons.**
- Blocking calls belong only at the outermost point.
- A semantic question can be answered without code by asking what each answer needs.
- A deadlock was predicted from a law. Without the law it would have surfaced later as a production
  resource problem.
- Tricky code is acceptable inside if the interface stays pure and the laws test it. It only needs to
  be right once.
- The first implementation's recorded weaknesses were all real; write them down when you see them.
- The final implementation is described by its authors as law-respecting, not as the best possible.

The general topic of describing parallel work and running it without blocking is covered by
`fp-effects-and-streams`.

## 3. Property testing (FPiS ch. 8)

| Stage | Design | What forced the next step |
|---|---|---|
| 1 | From a usage snippet read off `Gen<A>`, a polymorphic `listOf`, `forAll(gen)(predicate): Prop`, and `&&` on `Prop`. Note that size is absent from `listOf` | What is a `Prop`? |
| 2 | `Prop` has `check(): Unit` that prints | `&&` cannot be implemented: nothing to combine. The operation throws information away |
| 3 | `check(): Boolean` | Need the failing case and the number of successes |
| 4 | Either a failure (case, count) or a success count. The failing case is a string since it is only displayed; aliases name the parts | How many cases? Where do random values come from? |
| 5 | `Prop = (TestCases, Rng) -> Result`. Each discovered dependency becomes a parameter | The success count on the success side is redundant, and "empty means success" as an optional is unclear |
| 6 | `Result = Passed | Falsified(failure, successes)` | Need generators |
| 7 | `Gen<A>` wraps a state action over the pure random source. Primitives: range, constant, boolean, list of N. Add `flatMap` for dependent generation; `union`; `weighted` | `forAll`: generate a lazy sequence of samples, pair with indices, take N, find the first failure. A throwing predicate loses its input |
| 8 | Catch exceptions and report them as falsifications carrying the input | Combined properties do not say which part failed |
| 9 | Labels on properties | Failing cases are large |
| 10 | Minimisation by sized generation: `SGen<A> = Int -> Gen<A>` layered over `Gen`. `Prop = (MaxSize, TestCases, Rng) -> Result` | Using the library to test the parallelism laws is verbose |
| 11 | Usability: single-case `check`; `Proved` result; equality lifted into the tested type; `forAllPar` drawing the executor from a weighted generator; product operator for generators | Higher-order functions need generated functions |
| 12 | Constant-function generator (insufficient). Real function generation left open | Observation: `map` and `flatMap` on `Gen` match those on the other types, laws included |

**Lessons.**
- The runner's result type is designed from the consumer backwards.
- A layer (the sized generator) was preferred to modifying a type with many existing operations.
- A dependency found while implementing one function (size, in `forAll`) was propagated into the
  signature of the type it belongs to and not worked around.
- Real use drives the helpers, not speculation.

## 4. Parser combinators (FPiS ch. 9)

Here the algebra and its laws come first; the representation is derived last.

| Stage | Design | What forced the next step |
|---|---|---|
| 1 | Toy inputs. `char(c): Parser<Char>`, `run(p)(input): Either<ParseError, A>`. Interface generic over the parser and error types, so it compiles with no implementation. Law: running `char(c)` on `c` yields `c` | More inputs |
| 2 | `string(s)`; `or(p1, p2)` generalised at once to any result type; `listOfN(n, p)`. Each with an example law. Infix syntax delegating to the interface | Tasks: count zero or more of a character; one or more with a custom message; zero or more of one then one or more of another |
| 3 | `many(p): Parser<List<A>>`. To count, add `map` instead of specialising `many`. Law: `map(p)(id) == p`, written as a property over generated strings | Building a list only to take its length is wasteful |
| 4 | `slice(p): Parser<String>` returns the matched input. Because its meaning forbids building the intermediate list, it must be primitive | `many1` should not be primitive |
| 5 | `product(p1, p2)`, `map2` from it; `many1(p) = map2(p, many(p))(cons)`; `many(p) = or(map2(p, many(p))(cons), succeed(empty))` | A hand trace: `many` recurses forever because `map2` evaluates its second argument eagerly |
| 6 | Make the second argument of `product`/`map2`/`or` lazy. `or` is left-biased | Is this enough? It is, for context-free grammars. It is not for "a digit n then n letters" |
| 7 | Add `flatMap`. `product`, `map2`, `map` become derived. Add `regex`. Primitives: string, regex, slice, succeed, or, flatMap | Check expressiveness on something real |
| 8 | Write a JSON parser against the interface alone | Nothing in the algebra says anything about error messages |
| 9 | `label(msg)(p)` replaces the message; errors carry a location (input and offset; line and column computed lazily). Law: a failing labelled parser reports the label | One level of message is not enough; want "while parsing X, unexpected Y" |
| 10 | `scope(msg)(p)` pushes context; `ParseError` becomes a stack of (location, message). Law: new stack is the message on top of the old stack. The abstract error type parameter is dropped in favour of this concrete type | With `or`, which branch's error is reported? After matching the first token of a branch the user wants that branch's error |
| 11 | Commit: a parser that has consumed at least one character is committed, and `or` tries its second branch only on an uncommitted failure. `attempt(p)` cancels commitment for cases needing lookahead across several tokens. Final primitives: string, regex, slice, label, scope, flatMap, attempt, or (plus succeed) | Need a representation |
| 12 | `Parser<A> = String -> Either<ParseError, A>` | Sequencing needs to know how much was consumed |
| 13 | `Parser<A> = Location -> Result<A>`; `Result = Success(value, consumed) | Failure(error)`. A parser is a state action that can fail. It reports a count and not a new location, so it cannot rewrite the input | `scope` and `label` |
| 14 | `scope` maps the error by pushing; `label` maps it by replacing | `or` and `attempt` need to know about commitment |
| 15 | `Failure(error, isCommitted)`; `attempt` clears the flag; `or` runs its second parser only on an uncommitted failure; `flatMap` advances the location, marks later failures committed if the first parser consumed input, and adds the consumed counts | `slice` still builds the value; large inputs overflow the stack |
| 16 | Left as exercises: an efficient `slice` by changing the representation; a stack-safe `many` (all repetition forms can be defined through it); formatting errors by grouping labels at the same location; keeping errors from both branches of `or` or the one that got furthest | |

**Commit example from the source.** Two alternatives, each scoped: a "magic spell" of two words and a
"gibberish" of two other words. On input whose first word matches the spell and whose second word has
a wrong capital letter, the wanted report is the spell's error, because the first word committed the
parse to that branch. Committing also saves work by not exploring other branches.

**Where `attempt` is needed.** When two alternatives share a prefix and several tokens must be read
before the right one is known, wrap the shared-prefix part of the first alternative in `attempt`.
Forgetting it yields a misleading "expected" message from the wrong branch.

**Lessons.**
- With the algebra and laws fixed, the representation matters less and need not be public. A type's
  meaning comes from its operations and laws, not its internals.
- The representation was dictated primitive by primitive: three versions, each forced by one
  operation's need for information.
- `label` trims inner detail by design; `scope` keeps it. Use labels for user vocabulary ("expected a
  number") and scopes for context ("while parsing an array").
- Error values are structured and only formatted at the edge.
- Optimisations (slice, stack-safe repetition) change the representation and leave the algebra and
  its law tests alone.
- Combinators as ordinary values versus a generator tool: with values you can write new helpers to
  abstract common patterns and debug them as normal code; generated parsers tend to be monolithic.
  The reverse advantage of generators (peak speed, analysis) is marked inferred in the notes.

**Pitfalls recorded in the notes.** Strict recursion never terminates. Repetition of a parser that
can succeed without consuming input loops forever (inferred; guard by stopping when nothing was
consumed). Non-tail recursion in repetition overflows on large inputs (the source's footnote cites a
ten-thousand-element array). When both branches of `or` fail, the first branch's errors are dropped
unless you design otherwise.

## 5. From three libraries to shared abstractions (FPiS ch. 10 to 12)

| Stage | Observation | Result |
|---|---|---|
| 1 | Concatenation, addition, boolean "and"/"or" obey the same two laws | Monoid: an algebra defined only by operations and laws. Generic fold written once |
| 2 | A word count over split text is not combinable as a plain number | Enlarge the result type to carry boundary fragments; that type is a monoid; project at the end |
| 3 | Monoids of pairs, maps and functions follow from component monoids | Assemble aggregations declaratively; several statistics in one pass |
| 4 | `map` has the same signature and law on every library type | Functor |
| 5 | `map2` written with `flatMap` and `map` is textually identical for generators, parsers and options | Mechanical extraction: copy the body to a generic place, add the called operations as abstract, minimise. Monad = `unit` + `flatMap` |
| 6 | Expecting that extracting part of a chain into a helper does not change behaviour | That expectation is the associativity law; `unit` being neutral is the identity law |
| 7 | `sequence`, `traverse`, `replicateM` were written per type | Written once for all monads; then each is reinterpreted per instance |
| 8 | `traverse` uses only `unit` and `map2` | A weaker interface, applicative, sits inside monad. Some types are applicative and not monadic |
| 9 | A list appears concretely in `traverse`'s signature | Abstract over it: traversable |

The procedures drawn from these are in `choosing-an-abstraction.md`.

## 6. Triggers and responses across all four

| Trigger | Response | Seen in |
|---|---|---|
| The natural operation returns nothing or prints | Return a description or a rich result | Par (`get`), Prop (`check`) |
| An operation would need a global resource | Make it a description; pass the resource to the interpreter | Par (`fork`), Prop (random source) |
| A trivial input makes the operation do something silly | Two concerns are mixed; split them | Par (`map2`/`fork`) |
| A hand trace shows runaway evaluation | Make later arguments lazy | Par, Parser (`many`) |
| A needed operation depends on an earlier result | Add `flatMap` | State (retry), Gen (dependent length), Parser (context-sensitive), Par (`chooser`) |
| A new dependency appears during implementation | Add a parameter to the representation | Prop (cases, source, size), Parser (location, committed flag) |
| A law fails under a hostile environment | Fix or narrow; change representation if needed | Par (non-blocking) |
| An operation's meaning constrains implementation cost | It is primitive | Parser (`slice`) |
| Implementation would have to decide a user-visible policy arbitrarily | Add operations that carry the information | Parser (`label`, `scope`, `attempt`) |
| A base type is rich and a new concern is partial | Layer over it | Gen/SGen |
| An encoding obscures intent | Named result type | Prop (`Passed`/`Falsified`/`Proved`), Parser (`Result`) |
| Real use is noisy | Helpers and syntax, no new power | Prop (`check`, `forAllPar`), Parser (infix forms) |
| Same body on several types | Extract and minimise | Monad |
| A generic function uses fewer primitives than its interface offers | Extract the weaker interface | Applicative |

## 7. Using a precedent

1. Find the trigger in section 6 that matches your situation.
2. Read the stage in the library where it occurred.
3. Apply the response to your API, then re-run your law tests.
4. If no trigger matches, do a hand trace of your smallest example and ask at each operation what it
   must know to do its job; the missing information usually names the change.
