# Separating effects from logic: the procedure

A step-by-step refactoring from a function that decides and acts, to a pure function that decides
and a thin layer that acts. Citations are to Functional Programming in Scala, 1st ed. ("FPiS").
(inferred) marks generalisations made in the study notes; (adaptation) marks material added for
other languages. The code is fresh illustration, not taken from the book.

## Contents

1. The two moves and when each applies
2. Before you start
3. Move A: input, pure function, output
4. Move B: return a description of the effect
5. Worked example in TypeScript
6. Worked example in Python
7. When logic and effects interleave
8. How far to go: the ladder
9. Common mistakes
10. Verify

## 1. The two moves and when each applies

The principle behind both (FPiS ch. 13): inside every function with side effects there is a pure
function that can be extracted. An impure function from A to B can be split into a pure function
from A to D, where D describes the result or what to do, and an impure function from D to B that
acts on the description. Applying the split repeatedly pushes effects outward until the program
is a pure core inside a thin shell (FPiS ch. 1, ch. 2, ch. 13).

| Move | Use when | Result |
|---|---|---|
| A. Input, pure function, output | The effect is at the start (obtaining input) or the end (reporting a result) and the logic's output is an ordinary value | Pure functions plus a one-line caller |
| B. Return a description | The effect is itself what the logic decides (charge this card this amount, send this message), or effects must be combined, counted, filtered or dry-run | Pure function returning result plus command records; one `execute` at the edge |

Move A is always possible (FPiS ch. 13): any impure procedure factors into a procedure that
supplies inputs, a pure function, and a procedure that consumes the output, with behaviour
unchanged. Start there. Move B is move A where the output type D is a command.

## 2. Before you start

1. Confirm the change is wanted at this size. Extracting a function from the code being edited is
   small. Reshaping a module is a proposal to make first.
2. Pin current behaviour (adaptation): write a characterisation test at the outer boundary, with a
   fake at the true edge recording the effects, so the refactoring can be shown to preserve
   behaviour. See `craft-refactoring` for the safety workflow.
3. List the effects in the function: each read and each write that is not an argument or the
   return value. Include clock, random and ID calls.
4. Decide which effects matter (see `purity-and-substitution.md`, "Deciding which effects to
   track"). Leave debug logging where it is unless it is asserted on.

## 3. Move A: input, pure function, output

Procedure (FPiS ch. 13, language independent):

1. Find the lines that do I/O.
2. Move every decision and computation into a function that takes plain values and returns plain
   values. When the answer is more than a primitive, represent "what should happen" with an
   optional, a result type, an enum or sum type, or a command record.
3. Keep the I/O call as a one-liner that reads inputs, calls the core, and writes outputs.
4. Repeat on the shell until only primitive I/O calls remain.

The book's example (FPiS ch. 13): a `contest` procedure that works out which of two players has
the higher score and prints the outcome. Three steps:

1. Extract a function returning an optional player (absent means a draw).
2. Extract a function from that optional player to the message text.
3. The procedure becomes: print the message for the winner of the two players. The effect is at
   the outermost layer and its argument is a pure expression.

Further decisions, such as whether to display in a user interface or write to a file, become pure
choices of the description type, not new branches in the shell (FPiS ch. 13).

## 4. Move B: return a description of the effect

The book's example (FPiS ch. 1): `buyCoffee(card)` creates a coffee and charges the card through
a payment service.

The problems listed for the original:

1. It cannot be tested without contacting the payment processor.
2. Injecting a payments interface regains some testability, but forces an interface where a
   concrete class might have been fine, makes for awkward mocks whose internal state the test has
   to inspect, and is heavy machinery for asserting that the charge equals the price.
3. It cannot be reused. Buying twelve coffees by calling it twelve times contacts the processor
   twelve times, with twelve fees. A special batching function duplicates logic. Batching inside
   the payments implementation raises questions with no good owner: how many to batch, how long
   to wait, who closes the batch.

The move, step by step (FPiS ch. 1, generalised in the notes):

1. Identify the effectful call.
2. Introduce a plain immutable type describing the effect, carrying exactly the data the call
   would have taken: a charge with a card and an amount. Name it as a noun or command.
3. Return the description with the original result: a pair of coffee and charge. The function no
   longer knows anything about payment processing.
4. Give the description a combining operation where merging makes sense: two charges on the same
   card combine into one with the summed amount. Different cards cannot combine. The book throws
   at this point and defers the better approach; return a typed error or optional instead.
5. Build larger behaviours by ordinary value manipulation. Buying N is: repeat the single
   purchase N times, separate the coffees from the charges, reduce the charges with the combining
   operation. Coalescing a list of charges is: group by card, reduce each group.
6. A separate thin outer layer executes charges against the processor.
7. Test the function by equality on returned values. Test the executor separately with a fake or
   an integration test (inferred).

Why it works: a description that is an ordinary value can be batched, combined, filtered, stored,
reordered, counted or tested before anything touches the outside world, and the composition is
done with ordinary collection operations (FPiS ch. 1).

What the language must provide (inferred): immutable records or tuples, and first-class functions
with collection operations such as map, group-by and reduce. Where sum types are missing, the
description is a plain struct or class with a tag; where tuples are missing, return a small
result struct. See `language-mappings.md`.

Related names for the same idea (inferred; the book says only "pure core, thin outer layer"):
command pattern, an event-sourcing decide function that returns events, functional core and
imperative shell, an update function that returns commands.

## 5. Worked example in TypeScript

A handler that renews a subscription. Before:

```ts
async function renew(subId: string, db: Db, pay: Payments, mail: Mailer): Promise<void> {
  const sub = await db.getSubscription(subId);
  if (sub.status !== "active") return;
  if (sub.expiresAt.getTime() - Date.now() > 3 * DAY) return;
  const price = sub.plan === "pro" ? 2000 : 800;
  await pay.charge(sub.cardId, price);
  sub.expiresAt = new Date(sub.expiresAt.getTime() + 30 * DAY);
  await db.save(sub);
  await mail.send(sub.email, `Renewed for ${price / 100}`);
}
```

Effects listed: one database read, the clock, a charge, a mutation of the loaded record, a
database write, an email. Returns nothing, which is the hint (FPiS ch. 2). A test needs three
doubles and a patched clock.

After move A (the read and the clock become inputs) and move B (the charge, save and email become
descriptions):

```ts
type Sub = Readonly<{ id: string; status: "active" | "cancelled"; plan: "pro" | "basic";
                      cardId: string; email: string; expiresAt: number }>;

type Command =
  | { kind: "charge"; cardId: string; amount: number }
  | { kind: "saveSub"; sub: Sub }
  | { kind: "email"; to: string; body: string };

// Pure: result depends only on (sub, now).
function decideRenewal(sub: Sub, now: number): readonly Command[] {
  if (sub.status !== "active") return [];
  if (sub.expiresAt - now > 3 * DAY) return [];
  const amount = sub.plan === "pro" ? 2000 : 800;
  const renewed: Sub = { ...sub, expiresAt: sub.expiresAt + 30 * DAY };
  return [
    { kind: "charge", cardId: sub.cardId, amount },
    { kind: "saveSub", sub: renewed },
    { kind: "email", to: sub.email, body: `Renewed for ${amount / 100}` },
  ];
}

// Shell: reads inputs, calls the core, executes. No business decisions.
async function renew(subId: string, deps: Deps): Promise<void> {
  const sub = await deps.db.getSubscription(subId);
  for (const c of decideRenewal(sub, deps.clock())) await execute(c, deps);
}

async function execute(c: Command, d: Deps): Promise<void> {
  switch (c.kind) {
    case "charge":  return d.pay.charge(c.cardId, c.amount);
    case "saveSub": return d.db.save(c.sub);
    case "email":   return d.mail.send(c.to, c.body);
  }
}
```

Note on the types (adaptation): the "before" read `expiresAt` as a `Date`; the "after" stores
epoch milliseconds so the core never touches `Date.now()` or a mutable `Date`. The shell (or the
database adapter) converts at the boundary. The two versions were run against fakes on six
subscriptions (active pro and basic, cancelled, far from expiry, exactly three days out, already
expired) and recorded the same charge, save and email calls in the same order.

The test of the logic is equality with no doubles:

```ts
expect(decideRenewal({ ...activePro, expiresAt: T + DAY }, T)).toEqual([
  { kind: "charge", cardId: "c1", amount: 2000 },
  { kind: "saveSub", sub: { ...activePro, expiresAt: T + 31 * DAY } },
  { kind: "email", to: "a@example.com", body: "Renewed for 20" },
]);
```

Combining, in the manner of the book's coalesce: a nightly job that renews many subscriptions can
collect all commands, group the charges by card, sum each group, and execute one charge per card.
That is a few lines over the command list and needs no change to `decideRenewal`.

Note on ordering and failure (adaptation): the shell above executes commands in order and stops
at the first failure, as the original did. If the save must not happen when the charge fails,
that policy lives in the shell or in a transaction around `execute`; see `arch-transactions` and
`craft-error-handling`. The core states what should happen, not how failures are recovered.

## 6. Worked example in Python

A function that scores a quiz and reports. Before:

```python
def grade(path):
    rows = list(csv.DictReader(open(path)))
    total = 0
    for r in rows:
        if r["answer"].strip().lower() == r["key"].strip().lower():
            total += int(r["points"])
    pct = 100 * total / sum(int(r["points"]) for r in rows)
    if pct >= 60:
        print(f"PASS {pct:.0f}%")
    else:
        print(f"FAIL {pct:.0f}%")
        requests.post(ALERT_URL, json={"file": path, "pct": pct})
```

After. The description is a frozen dataclass; the decision about alerting is data.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Outcome:
    passed: bool
    pct: float

@dataclass(frozen=True)
class Alert:
    file: str
    pct: float

def score(rows) -> Outcome:                       # pure
    earned = sum(int(r["points"]) for r in rows
                 if r["answer"].strip().lower() == r["key"].strip().lower())
    possible = sum(int(r["points"]) for r in rows)
    pct = 100 * earned / possible
    return Outcome(passed=pct >= 60, pct=pct)

def message(o: Outcome) -> str:                   # pure
    return f"{'PASS' if o.passed else 'FAIL'} {o.pct:.0f}%"

def alerts(path: str, o: Outcome) -> list[Alert]: # pure
    return [] if o.passed else [Alert(path, o.pct)]

def grade(path):                                  # shell
    with open(path) as f:
        rows = list(csv.DictReader(f))
    outcome = score(rows)
    print(message(outcome))
    for a in alerts(path, outcome):
        requests.post(ALERT_URL, json={"file": a.file, "pct": a.pct})
```

This is the book's `contest` shape with one extra description. Tests call `score`, `message` and
`alerts` with literal rows and compare results. The pure version also exposes a case the original
hid: `possible == 0`. Decide it in `score` (for example by returning an optional outcome) instead
of letting a division error escape. Both versions raise `ZeroDivisionError` on an empty or
all-zero-points file, before printing anything; the refactoring preserves that, and changing it is a
separate decision.

## 7. When logic and effects interleave

The moves above assume inputs can be gathered first and effects performed last. When a later
read depends on an earlier decision, the notes give the general direction (repeat the split on
the shell, FPiS ch. 13) but not a recipe. Options, cheapest first (adaptation):

1. **Read more up front.** If the extra read is cheap and safe, fetch it unconditionally and pass
   it in. The logic stays one pure function.
2. **Stage the logic.** Split into pure stages with the shell between them:
   `plan = decide1(input)`, shell performs the read the plan asks for, `commands = decide2(plan,
   fetched)`. Each stage is tested by equality.
3. **Return a request and a continuation.** The pure function returns "I need X" plus a function
   from X to the next step. This is the beginning of an effect type with an interpreter; if you
   need more than one or two such steps, stop and use `fp-effects-and-streams`.
4. **Pass a narrow interface.** Accept a small port with only the operations needed and supply an
   in-memory fake in tests. The logic is then not pure, but it is deterministic under the fake.
   The book treats the injected interface as the lesser first step (FPiS ch. 1); it is reasonable
   when options 1 to 3 would distort the code.

## 8. How far to go: the ladder

The four rungs are this skill's arrangement of the decision rules distilled in the notes on FPiS
ch. 13:

| Rung | What you build | Sufficient when |
|---|---|---|
| 1 | Pure functions extracted; shell passes values in and writes results out | The goal is testability and clarity. Always try this first. |
| 2 | Descriptions of effects returned as data; one `execute` | The logic must say which effects should happen; effects need batching, dedup, dry-run, audit |
| 3 | An effect-description type with composition (an IO-like value) | Effects must be composed as values: stored, retried, run in parallel, scheduled; or a long effectful loop must be stack-safe |
| 4 | A declared algebra of operations with several interpreters | The set of operations is small and stable and you want real, in-memory, recording, dry-run or asynchronous interpreters, or want to restrict a component to those operations |

Rungs 3 and 4 are the territory of `fp-effects-and-streams`. The book's own advice bounds them
(FPiS ch. 13): use an IO type directly as little as possible, because programs written inside it
tend to be monolithic with limited reuse and bring back many difficulties of ordinary imperative
code. Not worth it for one-off scripts, performance-critical inner loops, or teams and languages
where the boilerplate is high (the last three are inferred costs).

At every rung, the interpreter or `execute` is called in one place, at the program's entry
(FPiS ch. 13: the entry point is the only impure function).

## 9. Common mistakes

| Mistake | Why it is one | Fix |
|---|---|---|
| Introducing an interface and a mock as the first step | Leaves the decision welded to the call; tests inspect mock state (FPiS ch. 1) | Separate first; add an interface only for real multiple implementations |
| The description holds a live object (a client, a callback, an open handle) | It can no longer be compared, stored or combined | Carry only the data the call needs |
| `execute` branches on business data | A decision has leaked into the shell | Move the branch into the core and make its outcome part of the description |
| The pure function still reads the clock, a global or config from the environment | Its result is not determined by its arguments | Pass the value in; see `injecting-nondeterminism.md` |
| The pure function mutates its argument (the loaded record) | Observable by the caller (FPiS ch. 14) | Return a new value |
| Throwing from the combining operation | Throwing is an effect (FPiS ch. 1); the book's example does this and corrects it later | Return an optional or result |
| A description value that has already started running (an eager promise or future) | It is not a description any more; it cannot be dropped or reordered (inferred) | Use plain data, or a deferred thunk |
| Converting plumbing that has no decisions | Adds types and indirection for nothing | Leave it and cover it with an integration test |
| Enlarging a small request into a restructuring | Out of proportion to what was asked | Extract what the task touches; propose the rest |

## 10. Verify

1. The characterisation test written in step 2 of "Before you start" passes unchanged.
2. Tests of the extracted functions contain no mocks, spies, patches or I/O. Report the count of
   test doubles before and after.
3. The core module imports no I/O client, clock, random or ID module. Show the search command and
   its output.
4. `execute` has one branch per description kind and no other conditionals.
5. Each description type is immutable and comparable by value; a test constructs one by hand and
   compares it with the function's output.
6. If a combining operation exists (inferred properties): it is associative; coalescing gives at
   most one description per key; totals per key are preserved. Property tests are the natural
   form; see `craft-testing` or `fp-api-design-with-laws`.
7. The entry point is the only caller of `execute`. Show the call sites.
8. For the user: before and after signatures, the list of effects and where each now lives.
