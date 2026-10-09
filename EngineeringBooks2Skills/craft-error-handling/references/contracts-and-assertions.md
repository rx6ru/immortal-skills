# Contracts and assertions

How to state what a routine requires and guarantees, check it while the program runs, and decide
which checks remain in production.

Short citations: PP = The Pragmatic Programmer ch. 4; WPF = Why Programs Fail ch. 10;
CC = Clean Code ch. 7.

## Contents

1. Definitions
2. Writing a contract: procedure
3. Whose job is the precondition
4. Contracts and subclasses
5. Data invariants and the `sane()` pattern
6. Postconditions and "old" values
7. Loop invariants and semantic invariants
8. Rules for assertions
9. Crash early: what to do when a check fails
10. What stays on in production
11. Ladder of adoption
12. Contracts as specification, and its limits
13. Reference runs as an oracle
14. Warning signs
15. Verification
16. Worked examples

## 1. Definitions

- **Precondition**: what must hold for the routine to be called. Meeting it is the caller's
  responsibility. A routine should never be called with its precondition violated (PP; WPF).
- **Postcondition**: what the routine guarantees on completion. Having one implies the routine
  terminates (PP).
- **Class or data invariant**: a condition that is true whenever control is outside the type's
  methods. It may be broken temporarily inside a method and must hold again on return. In practice
  it holds at the start and end of every public method (PP; WPF). Consequence: no field that takes
  part in the invariant can be freely writable from outside (PP).
- **The contract as one sentence**: if the caller meets every precondition, the routine guarantees
  that the postconditions and invariants hold when it finishes (PP).
- **Breach**: a violated contract is a bug, never an anticipated event. A violated precondition is
  the caller's bug; a violated postcondition is the callee's (PP; WPF). Because of this,
  preconditions are not a mechanism for validating user input or anything else that legitimately
  happens (PP).
- **Assertion**: an executable check of a condition that should always be true, which reports the
  location and the failed expression and, classically, can be switched off (WPF). Each one acts as
  a detector that fires before bad state spreads and hides where it began, and unlike a manual
  inspection it checks every run (WPF).

## 2. Writing a contract: procedure

1. List the input domain and its boundary conditions. Write what the routine promises and, more
   usefully, what it does not promise. This design-time step is described as the largest benefit of
   the technique even when nothing is checked at run time (PP).
2. Keep the precondition narrow and the promise small: strict about what is accepted, modest about
   what is returned. Accepting anything and promising everything means a great deal of code (PP).
   Compare the opposite choice in `define-errors-away.md`; the deciding rule is in
   `choosing-a-strategy.md` under "strict or liberal inputs".
3. Check that every precondition is something the caller can test and control. A condition that
   depends on user input or the environment is error handling.
4. Express each condition in the programming language where possible, using only side-effect-free
   queries (PP).
5. If a postcondition mentions an input, make sure the routine cannot alter that input, or capture
   its value at entry (PP).
6. Check that the postcondition constrains the result and covers the whole promised effect,
   including what must not change (marked inferred in the notes).
7. For a type, write the invariant and confirm every public mutator re-establishes it.
8. Decide the enforcement level from the ladder in section 11.

## 3. Whose job is the precondition

- With language support, the check runs after the call is made and before the body, so it is in
  neither party's code. Any explicit test of the arguments is therefore the caller's (PP).
- Without support, bracket the routine with a preamble and postamble that check (PP).
- Putting the domain in the precondition lets the routine be written knowing its inputs are in
  range, and puts the policy decision with the party that has the context. Example: a program reads
  a number and takes its square root. If the user types a negative number, the reading code chooses
  to stop, re-prompt or do something else. The square-root routine does not have that choice to
  make (PP).
- Practical rule combining this with the notes' caveats: at a trust boundary (user input,
  deserialised data, another system), validate with real error handling. Inside it, assert the
  precondition at the callee's entry and write no recovery for it.

## 4. Contracts and subclasses

- Substitutability: code written against the base type must work with any subtype without knowing
  the difference (PP).
- Rule: an override may accept a wider range of inputs and may guarantee more, but must accept at
  least what the parent accepts and guarantee at least what the parent guarantees (PP).
- A compiler checks only signatures. Nothing prevents an override with the right name that does not
  do the job. A contract stated once on the base type binds every future subtype (PP).
- With plain assertions, overriding methods do not inherit the checks; they have to be repeated or
  routed through a non-overridable wrapper method (PP lists this as a gap of assertions).

## 5. Data invariants and the `sane()` pattern

Procedure (WPF):

1. Write a single predicate, conventionally `sane()` or `is_valid()`, that returns true when the
   object is valid.
2. For a complex structure, compose it from one helper per property. For a red-black tree the notes
   list: the root has no parent; the root is black; a red node has only black children; every path
   has the same number of black nodes; there are no cycles; parent links are consistent.
3. Assert it at entry and at exit of every public method that changes state.
4. Prefer using the public interface inside the predicate so subclasses and alternative accessors
   are covered, but make sure those accessors do not themselves call the predicate, or it recurses.
5. Do not assert it in the middle of a method, where the object may legitimately be inconsistent.

What the result tells you (WPF):

| Entry check | Exit check | Conclusion |
|---|---|---|
| fails | - | The corruption happened before this method was called |
| passes | fails | The corruption happened inside this method |
| passes | passes | This method is not where it happened |

If every wrapped method passes, the type is ruled out as the place where state went bad.

Reducing clutter (WPF): apply the entry and exit check from one place to all methods matching a
pattern, so future methods are covered and the checks can be toggled together. The book uses
aspects; the notes list decorators, proxies, base-class template methods and test-only subclass
hooks as equivalents.

```python
def checked(method):
    def wrapper(self, *args, **kwargs):
        assert self.is_sane(), f"{type(self).__name__} corrupt before {method.__name__}"
        result = method(self, *args, **kwargs)
        assert self.is_sane(), f"{type(self).__name__} corrupt after {method.__name__}"
        return result
    return wrapper
```

(In Python this uses the strippable `assert`; see section 10 before relying on it in production.)

Without changing code: a conditional breakpoint on a method that stops when the predicate is false
works like an assertion even in a build where assertions are disabled. It is slower, not
persistent and not shared with the team (WPF).

Limit: per-object invariants do not establish that the whole program state is sane; relations
between objects and global properties are not covered (WPF).

## 6. Postconditions and "old" values

- Check preconditions at the start and postconditions at the end; in a routine with several exits,
  make sure the postcondition runs on each (the multi-exit point is marked inferred in the notes).
- A postcondition that compares against the entry state needs a saved copy made at entry. When the
  checks are disabled the saved variables are unused, which compilers may flag (WPF).
- Cheap oracles for a postcondition (WPF decision guide): the inverse operation reproduces the
  input; a round trip returns the original; the output is sorted; a quantity is conserved.
- The helper predicates written for postconditions, such as "is sorted" or "contains", often
  deserve to be public methods (WPF).
- An assertion that restates the implementation gives no independent check (marked inferred in the
  notes); prefer a property that could be verified by different means.

```python
def divide(dividend: int, divisor: int) -> tuple[int, int]:
    ensure(divisor != 0, "divisor must be non-zero")            # precondition
    quotient, remainder = dividend // divisor, dividend % divisor
    ensure(quotient * divisor + remainder == dividend, "bad division")   # postcondition
    return quotient, remainder
```

(`ensure` here stands for an always-on check helper; see `language-mappings.md`.)

## 7. Loop invariants and semantic invariants

**Loop invariant** (PP). A statement of the loop's goal, generalised so that it is true before the
loop starts and after every iteration. It guards against not knowing when to stop and against
off-by-one mistakes. Example: finding the largest element with an index `i` starting at 1 and a
running value `m` starting at the first element. The invariant is "`m` is the largest of the
elements before position `i`". It holds at the start, each iteration preserves it, and when `i`
reaches the length `m` is the answer. The example assumes a non-empty array, which is its
precondition. Usable as an assertion or only as a reasoning tool.

**Semantic invariant** (PP). A requirement that is part of the very meaning of the thing and must
never be violated, as opposed to a business policy that could change. The notes' example is a
payment switch: a transaction must never be applied to an account twice; in any failure prefer not
processing to double processing. Having this stated resolved many error-recovery design questions.
Practice: state it unambiguously and publish it where everyone sees it. Use it when recovery
choices are contested: ask which choice preserves the invariant.

## 8. Rules for assertions

1. **No side effects in the condition.** The run must behave the same with checks off. The notes'
   example: asserting on "next element is not null" consumes an element, and the loop then
   processes only half the collection. Fetch into a variable, then assert on the variable (PP; WPF).
2. **Nothing that must execute goes inside an assertion**, because it may be compiled out (PP).
3. **Assertions are not error handling.** They are for what should never happen. Checking that a
   user typed one of the allowed letters is validation (PP; WPF).
4. **Use them systematically** on invariants and on pre- and postconditions, not sprinkled at
   random (WPF).
5. **A useful failure report** gives file and line and the text of the failed expression (WPF);
   named conditions make the message self-explanatory (PP).
6. **Trigger for adding one**: any time you think "that could never happen" (PP).
7. **Every switch over a closed set has a default that fails** so that an unexpected value is
   reported instead of skipped (PP). With exhaustive matching on closed types the compiler supplies
   this (notes' generalisation).
8. Typical uses: argument sanity; checking an algorithm's own output, for example sortedness after
   a sort (PP).

The claim "this cannot happen" deserves suspicion. The notes list things that sound impossible and
are not: a month with fewer than 28 days, a failure to stat the current directory, a sum of two
known integers not being what arithmetic says, a minute without 60 seconds, `a + 1 <= a` for an
integer (explanations marked inferred there: a calendar reform, a removed directory, interference
or redefinition, leap seconds, overflow).

## 9. Crash early: what to do when a check fails

- Bugs are often first noticed by something unrelated, long after they occurred. The closer the
  stop is to the defect, the less there is to investigate (PP; WPF).
- Once the impossible has happened the program's state cannot be trusted. Continuing risks writing
  corrupted data somewhere permanent. A stopped program usually does far less harm than a damaged
  one that keeps going (PP).
- An unnoticed wrong result is more dangerous than a noticed abort. Do not blame the assertion for
  the failure it revealed (WPF).
- A failed assertion does not have to mean process exit. It may raise, jump to an exit point, or
  call a handler that releases resources. Whatever it does must not rely on the data that was just
  found to be bad (PP).
- A plain exit is sometimes inappropriate: there may be resources to release, a log to write,
  transactions to close, other processes to coordinate with. Do that, and do no more normal work
  (PP).
- Install one top-level handler that reports a fatal error in a form the user can act on and
  offers whatever recovery is safe (WPF).
- In a language without exceptions, wrap calls that must not fail in a checking macro or function
  that compares the return code with the expected one and aborts with file, line, the call text,
  expected and actual (PP).
- Context (noted in the sources as widely held practice beyond the book): in a server or supervised
  system, "crash" normally means failing the request or worker and letting a supervisor restart it;
  in a library, raise and never terminate the host process.

Signals that code is not crashing early (PP): swallowed exceptions, ignored return codes, a default
branch that does nothing, returning null, NaN or -1 and carrying on, logging an impossible state
and continuing.

## 10. What stays on in production

**Never implemented as a strippable assertion** (WPF):

- **External conditions and input.** Check syntax and meaning with ordinary code and answer in the
  user's terms. A disabled input assertion is a security hole.
- **Critical results** (life, health, money). Validate with additional computation that is always
  present. Running a second independent implementation and comparing is weaker, and the book
  itself records serious doubt that it works.
- Security-relevant checks generally (notes' caveat on PP).

**The remaining assertions: reasons to keep them on** (PP; WPF):

- Testing covers a tiny fraction of the states the code will meet, and production is hostile in
  ways tests are not.
- More active checks catch more bad states, including ones that would not otherwise surface.
- Failures in the field are the hardest to reproduce, and a failed assertion says how the bad state
  arose.
- Layering: ordinary error checks are the first line; assertions are the net for what was missed.

**Performance** (PP; WPF): measure before removing anything. If a specific assertion is the
problem, typically a full traversal on a hot path or an invariant checked on every call, make that
one optional and leave the rest. Keep the cheap ones, especially those protecting result integrity.

**Ecosystem defaults** (notes' caveat): several languages disable or strip the built-in assert in
release or by default. To follow the advice there, use an always-on helper (a `require`/`check`
function or an explicit raise) for checks you intend to keep, and reserve the built-in for the
expensive, optional ones. `language-mappings.md` lists which is which.

Evidence note: the books argue from experience; the notes record a single controlled study,
finding better reliability and understandability at the price of more programming effort, and
nothing measured for debugging specifically.

## 11. Ladder of adoption

From weakest to strongest enforcement (PP):

1. **Design time only.** Think the contract through. Still the main benefit.
2. **Comments.** Write the contract next to the routine; gives a starting point when something
   breaks.
3. **Assertions.** Partial emulation. Gaps: no inheritance of checks; no built-in old values; the
   run time and libraries are not contract-aware, so the library boundary, where many problems
   show up, is unchecked.
4. **Preprocessors or libraries** that expand annotations into checks. More integration effort;
   third-party code still has no contracts.
5. **Native language support.** All code including libraries honours contracts.

Choose the lowest rung that the code's risk justifies; rung 1 costs nothing and applies always.
Current forms of the higher rungs (listed in the notes as surviving or analogous): built-in
asserts, non-null and richer type systems, require/check functions, contract libraries, languages
with built-in contract clauses, and property-based tests acting as executable postconditions.
Where a property can be put in a type, the check moves to compile time (notes' analogues: non-null
types, static type checks).

## 12. Contracts as specification, and its limits

- Natural-language specifications are readable but ambiguous and uncheckable; separate formal
  specifications are precise but costly to keep aligned with code. Executable contracts live in the
  code: any run that passes them is correct for that run (WPF).
- That suffices for mainstream software. Where a failing assertion at run time is unacceptable,
  proof for all runs is needed (WPF).
- The same annotations can feed documentation, generated tests, static checking and, with enough
  made explicit, verification; the notes describe this as a smooth path from run-time assertion to
  proof (WPF).
- A specification can be wrong. The notes' case: aircraft software that correctly implemented a
  requirement about when reverse thrust may engage, where the requirement itself was mistaken.
  When code and assertion disagree, examine both; do not bend code to a faulty assertion.

## 13. Reference runs as an oracle

When there is no stated contract but there is another run known to be right, compare against it
(WPF). Sources of a reference: the previous version; the same program in a different environment;
a port; a reimplementation. Use the same input for both and treat unexpected differences as errors
or at least anomalies. Where internal data structures differ, compare through a common abstraction
(for instance, both as sets). Current equivalents named in the notes: golden-file, snapshot and
differential tests, comparing logs of passing and failing versions. For applying this while
hunting a defect, see `craft-debugging`.

## 14. Warning signs

- A condition with side effects; behaviour that changes when checks are off (PP; WPF).
- A `sane()` that calls instrumented public methods and recurses (WPF).
- An invariant asserted mid-method (WPF).
- User input or critical output guarded by something that disappears in release builds (WPF).
- A postcondition that refers to a local implementation variable, checks only part of the promise,
  or imposes an unstated requirement (from the notes' inferred analysis of a contract exercise).
- A postcondition that mutates what it verifies, such as checking a push by popping (same source).
- Assertions that restate the code (inferred in the notes).
- All assertions deleted for speed instead of the measured expensive ones (WPF).
- An override that rejects inputs the parent accepted (PP).
- A specification trusted over evidence (WPF).

## 15. Verification

- After adding an assertion, violate it deliberately and confirm it fires with location and
  expression (WPF, partly inferred).
- On passing runs, the build with checks disabled produces the same output as the build with them
  enabled (WPF, partly inferred).
- For a bug fix, add the assertion or postcondition that would have caught the bad state earliest;
  confirm it fails on the old code and passes on the fixed code (WPF, partly inferred).
- Checklist for a contract (PP, with inferred items marked in the notes): each precondition is
  checkable and controllable by the caller; each expression is free of side effects; the
  postcondition is not a tautology and covers the whole effect; overrides only weaken preconditions
  and only strengthen postconditions; every public mutator restores the invariant and no
  invariant-bearing field is publicly writable; old values are captured where needed.
- Search for strippable asserts on anything reachable from outside the program and convert them.
- Search for switches and matches on closed sets with no failing default.

## 16. Worked examples

**Insert into an ordered list with unique entries** (PP). Invariant: every node that has a
predecessor is greater than it. Precondition: the list does not already contain the item.
Postcondition: the list contains the item. (`require` is an always-on check helper, like `ensure`
above.)

```python
def insert(self, item):
    require(item not in self, "item already present")     # pre
    self._link_in_order(item)
    require(item in self, "item missing after insert")    # post
    require(self._strictly_sorted(), "order broken")      # invariant
```

**A time-of-day type** (WPF). `sane()` is: hour between 0 and 23, minute between 0 and 59, second
between 0 and 60 to admit a leap second. `set_hour(h)` has precondition `0 <= h <= 23` and
postcondition `hour() == h`, with the minutes equal to the value saved at entry.

**A blender controller** (PP exercise; the contract below is marked inferred in the notes). Ten
speeds with zero meaning off; it may not run empty; speed changes one step at a time. Invariant:
speed is between 0 and 9, and a non-zero speed implies the jar is full. `set_speed(x)` requires
that `x` differs from the current speed by exactly one, is in range, and the jar is full; it
ensures the speed equals `x`. `fill` requires not full and ensures full. `empty` requires speed
zero and ensures not full. Note how the "one step at a time" rule became a precondition, which
puts the burden on the caller; whether that is right depends on whether the caller can check it,
which here it can.
