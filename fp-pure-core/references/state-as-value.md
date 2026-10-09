# State as a value

How to turn hidden mutable state into explicit state that is passed in and returned. Citations
are to Functional Programming in Scala, 1st ed. ("FPiS"). (inferred) marks generalisations made
in the study notes; (adaptation) marks material added for other languages. Code is fresh
illustration.

## Contents

1. The problem with hidden state
2. The mechanical translation
3. The state-reuse bug
4. Three forms and which to use
5. Reducer form
6. Combinator form (state actions)
7. State machines
8. Loops as state passing
9. Imperative-looking code is still fine
10. Costs
11. Warning signs
12. Verify

## 1. The problem with hidden state

The book's example is a random number generator object whose internal state changes on each call
(FPiS ch. 6). Asking it for the next integer is not referentially transparent: the same call
gives a different result each time. The stated consequences: code using it is hard to test,
compose, modularise and parallelise.

The testability illustration: a die roll written as "random integer below six" has an off-by-one
(it yields zero to five, not one to six). A test asserting the result is between one and six
passes five times in six, and a failure cannot be reliably reproduced. The harder the bug and the
larger the program, the more this matters.

The same structure appears wherever an operation's result depends on what was called before
(inferred list): a private mutable field, a global, a counter, an ID generator, a clock, a cursor
or iterator position, a parser's input position.

## 2. The mechanical translation

The key move (FPiS ch. 6): make state updates explicit. Do not update the state as a side effect;
return the new state along with the value. This separates computing the next state from
communicating it to the rest of the program. The caller decides what to do with the new state.

The recipe as stated in the book: a class with a private mutable state field and methods that
return a result while mutating that field becomes an interface whose methods each return the
result paired with the next version of the object. The book's claim is that this can always be
done.

In neutral form:

```
before:  op(args) -> A              (reads and mutates hidden s)
after:   op(args, s) -> (A, s')     or, curried:  op(args) -> (s -> (A, s'))
```

The one-line summary from the chapter (FPiS ch. 6, summary): use a pure function that takes a
state argument and returns the new state alongside its result. The advice attached: when you meet
an imperative API that relies on side effects, see whether you can give it a purely functional
version. The pattern was motivated by random numbers but comes up in many domains; in the same
book it is reused for test-data generators and for the position in a parser's input.

## 3. The state-reuse bug

The cost of the translation is that the caller must thread each new state into the next call.
Reusing an old state value yields the same result again. The book's example: a function meant to
produce a pair of random integers that asks the same generator value twice returns two identical
numbers. The correct version uses the generator returned by the first call for the second, and
returns the final generator so the caller can continue.

Nothing in most type systems catches this. Defences:

- Do not thread by hand; use a fold or combinators (sections 5 and 6).
- An ownership system that consumes the old state on use prevents reuse (Rust move semantics;
  inferred).
- A test that asserts two consecutive draws differ and that the final state differs from the
  initial one (section 12).

## 4. Three forms and which to use

| Form | Shape | Use when | Avoid when |
|---|---|---|---|
| Explicit pair | `op(s) -> (a, s')`, threaded by hand | One or two steps | More than a few steps; the reuse bug appears and the code is all bookkeeping |
| Reducer | `step(s, input) -> s'` (or `-> (s', output)`), driven by a fold | State evolves in response to a sequence of inputs or events; languages without a binding syntax | Each step's choice of next operation depends on a value just produced and there is no input sequence |
| State actions with combinators | A value of type `s -> (a, s')` composed with `map`, `flatMap`, `sequence`, `get`, `set`, `modify` | Many small stateful steps composed in varying ways (generators, parsers); the language has a binding syntax | The host language makes the chain unreadable; the team does not use the style |

The notes' judgement (inferred): where chaining syntax is poor, the combinator style is verbose
and the reducer over an immutable record is the same idea with less machinery. The combinator
form adds sequencing convenience, not capability.

## 5. Reducer form

Procedure:

1. Collect the hidden state into one immutable record.
2. Define the inputs as a closed set (an enum or sum type).
3. Write `step(state, input) -> state'` as a pure function. If a step also produces output or
   requests an effect, return a pair of new state and outputs (the output list is where effect
   descriptions go; see `separating-effects-procedure.md`).
4. Run a sequence of inputs with a fold from the initial state.
5. In a long-running program, the shell holds the only mutable reference to the current state
   and does `current = step(current, input)` (adaptation).

Python sketch of a rate limiter whose counter and window were instance fields:

```python
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class Window:
    start: float
    count: int

def allow(w: Window, now: float, limit: int, span: float) -> tuple[bool, Window]:
    if now - w.start >= span:
        return True, Window(start=now, count=1)
    if w.count < limit:
        return True, replace(w, count=w.count + 1)
    return False, w
```

Note that `now` is a parameter. Hidden state and hidden time usually come out together.

## 6. Combinator form (state actions)

The derivation in the book (FPiS ch. 6) is worth knowing because it shows what each piece is for.

- Every function in the random-number API has the shape "generator in, value and generator out".
  Call such a function a state action or state transition, and give the shape a name. The book is
  careful about the reading: it is a program that depends on some state, uses it to produce a
  value, and transitions the state.
- Combinators let the state stay unmentioned in application code:

| Combinator | What it does | Needed when |
|---|---|---|
| `unit(a)` | Produces `a`, passes the state through untouched | Lifting a constant into a chain |
| `map(action, f)` | Transforms the produced value; state flows through unchanged | Post-processing a result (a non-negative even number from a non-negative one) |
| `map2(a, b, f)` | Runs `a`, threads its state into `b`, combines the two values | Two independent steps (a pair of an integer and a float) |
| `sequence(actions)` | Runs a list of actions in order, collecting values | N steps (a list of N integers) |
| `flatMap(action, g)` | Runs `action`, passes its value to `g`, which chooses the next action | The next step depends on a produced value (retry when a draw falls in the rejected range) |
| `get` | Returns the current state as the value | Reading state |
| `set(s)` | Replaces the state, produces nothing | Writing state |
| `modify(f)` | `get`, then `set(f(state))` | Updating state |

- `map` and `map2` can be written with `flatMap`; this is what "more powerful" means there.
  Choosing the least powerful combinator that does the job is covered in
  `fp-api-design-with-laws`.
- None of the combinators mention the generator. Changing the signature of `map` to work for any
  state type required no change to its body; the general type had been there all along. One
  general state-action type with general combinators then serves any state.
- `get` and `set`, with the others, are stated to be all the tools needed to implement any state
  machine or stateful program purely.
- Run the composed action once at the edge with an initial state (inferred phrasing of the
  book's pattern).

What the language needs (inferred): pairs or records, closures, generics, and ideally a binding
syntax. Higher-kinded types are not needed to define these combinators for a state type; they
are needed only to abstract over all types of this family at once.

The book's sidebar on awkwardness (FPiS ch. 6): when the functional version feels like tedious
bookkeeping, that is almost always a sign of an abstraction waiting to be found. Its advice is to
continue and look for the repeated pattern to factor out. Hand-threaded state over many lines is
the standard instance.

For the laws these combinators should satisfy and how to test them, see
`fp-api-design-with-laws`.

## 7. State machines

The book's exercise (FPiS ch. 6): a candy dispenser with two inputs, coin and turn, and a machine
state of locked flag, candies remaining and coins held. Rules:

- A coin into a locked machine unlocks it if any candy is left.
- A turn on an unlocked machine dispenses one candy and locks it.
- A turn on a locked machine, or a coin into an unlocked machine, does nothing.
- A machine with no candy ignores all inputs.

The function to write runs a list of inputs and returns the coins and candies at the end. The
example given: starting with 10 coins and 5 candies, after 4 successful purchases the result is
14 coins and 1 candy.

Technique from the notes: write a pure transition from input and machine to machine, apply it
across the input list, then read the final machine. In combinator form that is `modify` per
input, `sequence`, then `get`. In reducer form it is a fold (inferred equivalence).

TypeScript sketch in reducer form:

```ts
type Input = "coin" | "turn";
type Machine = Readonly<{ locked: boolean; candies: number; coins: number }>;

function step(m: Machine, i: Input): Machine {
  if (m.candies === 0) return m;
  if (i === "coin" && m.locked)  return { ...m, locked: false, coins: m.coins + 1 };
  if (i === "turn" && !m.locked) return { ...m, locked: true, candies: m.candies - 1 };
  return m;
}

const simulate = (start: Machine, inputs: readonly Input[]) => {
  const end = inputs.reduce(step, start);
  return [end.coins, end.candies] as const;
};
```

Procedure for converting a flag-based state machine in existing code (adaptation):

1. Write down the states and inputs actually present. Booleans that are never both true are one
   enum.
2. Write the rule table in prose, as above, including "ignored" cases.
3. Implement `step` with one branch per rule and a final "unchanged" branch.
4. Move effects out: `step` returns the new state and, if needed, descriptions of effects
   (dispense, refund).
5. Write one test per rule and the invariants in section 12.

## 8. Loops as state passing

A loop's mutated variables are its state (FPiS ch. 2). The functional loop is a local recursive
helper whose parameters are the loop state: to iterate, it calls itself with new values; to
finish, it returns without recursing. The outer function calls the helper with the initial
values.

Conversion procedure (inferred from the chapter):

1. Every variable mutated in the loop becomes a parameter of the helper.
2. The loop's exit condition becomes the base case, returning the result.
3. The body's updates become the arguments of the recursive call.
4. The initial values go in the outer call.

Tail position: the recursive call is in tail position when the caller does nothing with its value
except return it. `go(n - 1, n * acc)` is; `1 + go(...)` is not. The book's host language
compiles self-recursion in tail position to a jump and offers an annotation that fails the build
when it cannot. The authors' point is that this is something the program relies on, not an
optimisation, because without it large inputs overflow the stack. Only self-recursion is covered;
mutual recursion is not.

Outside languages that guarantee this, write the same state-passing loop as a local loop with
local variables (the mutation is invisible outside the function, which the book endorses; see
`local-mutation.md`), or use a fold. The book calls hand-written loops rarely necessary and poor
form in its own language because they hinder composition; that judgement does not transfer to
languages without tail-call elimination (the language matrix in `language-mappings.md` is
inferred).

## 9. Imperative-looking code is still fine

The book's sidebar (FPiS ch. 6): imperative and functional are not opposites. Functional
programming is programming without side effects, and maintaining state without side effects is
reasonable. A sequence of state actions bound one after another reads like statements; a binding
syntax makes nested `flatMap` chains read as a list of steps. Such programs can still be reasoned
about by substitution.

Practical consequence: do not contort code to avoid looking sequential. The requirement is that
state changes are values returned, not that the code avoids the word "then".

## 10. Costs

- No in-place update means copying state (FPiS ch. 6, footnote). Cheap for a small record.
  Mitigate for large state with persistent data structures, or mutate in place without breaking
  referential transparency where the mutation is local.
- Callers take on the duty of threading; see the reuse bug.
- In languages without a binding syntax the combinator form is verbose (inferred).
- Where existing code and collaborators expect a mutable object, the shell needs an adapter that
  owns the current state.

## 11. Warning signs

| Sign | Meaning | Action |
|---|---|---|
| Two consecutive "fresh" values are equal | An old state was reused | Thread the returned state; add the test in section 12 |
| `(a, s1) = ...; (b, s2) = ...; (c, s3) = ...` over many lines | Missing abstraction (the book's sidebar) | Fold or combinators |
| A mutable variable inside the recursive helper | Defeats the point of the state-passing loop | Make it a parameter, or use an honest local loop |
| Non-tail recursion over large input | Stack overflow | Accumulator style, loop or fold |
| `step` performs I/O | The transition is not pure | Return a description from `step` |
| The state record has a field nothing reads | It is not state | Remove it |
| A failing test involving randomness or time cannot be re-run to the same failure | Hidden nondeterminism remains | `injecting-nondeterminism.md` |

## 12. Verify

- **Determinism**: the same action or `step` sequence with the same initial state gives the same
  output and final state on two runs.
- **Threading**: a run that draws twice returns two different values; the final state differs
  from the initial state.
- **Reproducible failure**: a failing run is fully described by the function and the initial
  state or seed. The book finds a seed for which the die roll yields zero and notes it can be
  re-created reliably; the fix is to add one to the bounded draw. Keep the seed in the failure
  message (inferred).
- **State machine**: one test per rule, including each "does nothing" rule. Invariants as
  property tests (inferred): candies never negative; coins never decrease; candies remaining plus
  candies dispensed is constant.
- **Loop conversions**: the compiler annotation where one exists; otherwise a test with an input
  large enough to overflow an unoptimised stack (the notes suggest 100k to 1M iterations,
  inferred), and an equivalence test against the original loop.
- **Combinators** (inferred, stated as monad laws later in the book): mapping the identity
  function changes nothing; `flatMap` with `unit` on either side changes nothing; `flatMap` is
  associative. See `fp-api-design-with-laws`.
- **Shell**: exactly one place holds the mutable reference to the current state. Show it.
