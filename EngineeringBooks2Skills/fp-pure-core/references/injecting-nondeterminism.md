# Injecting time, randomness and identifiers

How to make logic that depends on the clock, random numbers or generated identifiers reproducible.
Citations are to Functional Programming in Scala, 1st ed. ("FPiS"). The book works the random
number case in detail; clock and identifier generation are treated in the notes as the same
problem (inferred). (adaptation) marks material added for other languages.

## The underlying problem

A global random function, a clock read and an ID generator share one property: the result depends
on hidden state that changes between calls, so the call is not referentially transparent
(FPiS ch. 6). Logic that contains such a call has a result not determined by its arguments.

Observable symptoms:

- A test passes most of the time. The book's die roll with an off-by-one passes five runs in six
  (FPiS ch. 6).
- A failure seen once cannot be reproduced on demand.
- Tests assert loosely ("is some string", "within a second of now") because exact values are
  unknowable.
- Tests patch a global (`mock.patch("time.time")`, fake timers) to gain control.

## Three levels of fix

| Level | What changes | Reproducibility | Use when |
|---|---|---|---|
| 0. Call the global inside the logic | Nothing | None | Never in logic you want to test |
| 1. Pass a mutable source object in (a seeded generator, a clock object, an ID factory) | The source is a parameter | Partial: needs the same seed and the same number and order of prior calls | The host language makes this the idiom and each test builds its own source (adaptation) |
| 2a. Pass the value in | `now`, the random draw, or the new ID is a plain argument | Full | The logic needs one or a few values. The simplest and usually the best option |
| 2b. Pass a source that is itself a value | Each call returns the result and the next source state | Full: a run is determined by the initial state | The logic needs many draws or an unknown number of them |

The book considers level 1 and rejects it as a complete answer (FPiS ch. 6): to reproduce a
failure you need a generator created with the same seed and also in the same state, meaning the
same number of prior calls, because each call destroys the previous state. Its conclusion is to
avoid the side effect on principle and move to level 2b.

Reconciling that with common practice (adaptation): level 1 is a real improvement over level 0
and is often what a codebase's conventions support. Its weakness appears when the source is
shared between tests or between components, since then the count of prior calls depends on
everything that ran before. If you use level 1, create the source inside each test, and do not
share one source across independent pieces of logic.

## Level 2a: pass the value

Procedure:

1. Find each clock, random and ID call inside logic. A search such as
   `grep -rnE "Date\.now|new Date\(\)|Math\.random|randomUUID|datetime\.now|time\.time|uuid\.uuid|Instant\.now|System\.currentTimeMillis"`
   is a start (adaptation; extend for the stack).
2. For each, ask what the logic needs: usually one timestamp for the whole operation, or one new
   identifier.
3. Add a parameter of the plain type (`now: Instant`, `id: OrderId`).
4. Move the call up to the shell, which obtains the value once and passes it down.
5. In tests, pass literals.

One reading of the clock per operation is also more correct: logic that reads the clock several
times can see time advance between its own decisions (adaptation).

```python
# before
def is_expired(token):
    return token.expires_at < datetime.now(timezone.utc)

# after
def is_expired(token, now):
    return token.expires_at < now
```

## Level 2b: a source that is a value

The book's construction (FPiS ch. 6): a generator whose "next integer" operation returns the
integer together with a new generator, leaving the original unchanged. The implementation shown
is a linear congruential generator holding a single seed; the book says the details are
unimportant. What matters is that the same generator value always returns the same pair, so a
whole computation is a deterministic function of the initial seed.

With the general state machinery (see `state-as-value.md`), generating functions never mention
the generator: you compose small generating actions with `map`, `map2`, `flatMap` and `sequence`
and run the result once with a seed.

Where the idiom is unavailable or foreign (adaptation):

- Pass a seed, and derive a fresh local generator from it inside the function. The function's
  output is then a function of the seed.
- For parallel or independent components, give each its own seed derived from a parent seed, so
  that one component's number of draws does not shift another's values. The notes mention
  splitting a generator for parallel work (inferred).
- Identifier generation as a value: pass a counter state and return the next one, or pass the
  list of pre-generated identifiers the operation may consume.

TypeScript sketch of a value-style generator interface and its use:

```ts
type Rng = Readonly<{ seed: number }>;
declare function nextInt(r: Rng): readonly [number, Rng];   // pure: same r, same result

function twoDraws(r0: Rng): readonly [[number, number], Rng] {
  const [a, r1] = nextInt(r0);
  const [b, r2] = nextInt(r1);        // r1, not r0: reusing r0 would repeat `a`
  return [[a, b], r2];                // return the final state so the caller can continue
}
```

## Pitfalls specific to random numbers

These are worked in the book (FPiS ch. 6) and recur in real code.

| Pitfall | What goes wrong | Remedy |
|---|---|---|
| Reusing a generator state | Two draws from the same state are identical | Thread the returned state; prefer combinators or a fold; test that consecutive draws differ |
| Reducing to a range with remainder | Biased: the integer range is not a multiple of `n`, so small residues are more frequent | Rejection sampling: draw again when the value lies above the largest multiple of `n`; or use the library's bounded draw |
| Rejection needs a retry | A plain `map` cannot retry, because it has no state to draw from again | Use the operation that lets the next step depend on the value (`flatMap`), or thread explicitly |
| Absolute value of a random integer | The most negative integer has no non-negative counterpart | Map negatives another way, for example to `-(i + 1)` |
| A float in a half-open unit interval | Dividing by the maximum integer can give exactly one | Divide by the maximum plus one |
| Off-by-one in a bounded draw | "Below six" is zero to five, not one to six | Shift after bounding; a property test over many seeds finds it |

## Reproducing a failure

With pure state, a failing run is completely described by the function and the seed. The book
finds a seed for which the faulty die roll returns zero and notes that this can be re-created
reliably, turning an intermittent failure into a fixed test case (FPiS ch. 6).

Practice (inferred, consistent with the book's later property-testing chapter):

1. Every randomised test takes its seed from one place and prints it on failure.
2. When a failure occurs, copy the seed into a regression test with a literal seed.
3. For time, the equivalent is a literal `now` in the test.
4. For identifiers, the equivalent is a literal ID or a deterministic sequence.

## Where the real sources live

The shell obtains real values and passes them down (FPiS ch. 2, ch. 13 for the shape):

- entry point or request handler: read the clock once, generate request-scoped IDs, create or
  seed the generator
- core: receives them as arguments
- tests: pass literals or a fixed seed

If many layers lie between shell and the logic that needs the value, threading a parameter
through all of them is the honest cost. Options to reduce it (adaptation): bundle `now`, `rng`
and an ID supply in one small context record passed down; or restructure so the logic that needs
the value is called closer to the shell. Avoid a global "current clock" that tests replace, which
is level 0 again with extra steps.

## Proportion

- Not every clock read needs injecting. Timestamps on log lines and metrics are effects that
  correctness does not depend on (see `purity-and-substitution.md`).
- An ID that is opaque to the logic and never asserted on can be generated in the shell and
  passed down without further ceremony; do not build a value-style ID generator for it.
- Cryptographic randomness is a security matter; do not replace it with a seeded generator in
  production code. Inject the source so tests can substitute a deterministic one, and keep the
  real source in the shell (adaptation).

## Verify

- Search the core for clock, random and ID calls; the result is empty or each hit is justified.
- Run the test suite twice and in shuffled order; results are identical.
- For each function that takes `now`: a test just before, at, and just after each time boundary
  in the logic, using literals.
- For each function that takes a generator or seed: same seed gives the same output; two draws in
  one run differ; a bounded draw stays in range across many seeds (this is how the book's
  off-by-one is found); a rough uniformity check over a large sample for range reductions
  (inferred).
- Failure messages of randomised tests include the seed. Demonstrate by forcing one failure.
- No test patches a global clock, random module or timer.
