# Choosing an error strategy

A decision guide for one question: given a way this code can fail, what should the code do about it?
Use it when designing a function or module, or when a review argument is about throw versus return.

Short citations: PoSD = A Philosophy of Software Design; CC = Clean Code; PP = The Pragmatic
Programmer; WPF = Why Programs Fail; FPiS = Functional Programming in Scala.

## Contents

1. Why the choice matters
2. Step 0: enumerate the failure conditions
3. The classification procedure
4. Class by class: signals, treatment, verification
5. Where the handler goes
6. Contested rules and how to decide
7. Worked classifications
8. Review checklist

## 1. Why the choice matters

- Any uncommon condition that changes normal control flow counts: thrown exceptions, and also
  special return values such as null, -1 and error codes (PoSD ch. 10).
- Handling is harder than the normal case. You either push forward despite the problem or abort and
  report upward, and aborting may mean undoing a partial update. Handling can itself fail, producing
  secondary errors that are subtler than the first (PoSD ch. 10).
- Handlers rarely run, so their bugs survive. Code that has not been executed should be assumed not
  to work. The notes cite a study (Yuan et al., OSDI 2014) attributing over 90% of catastrophic
  failures in the distributed data-intensive systems it examined to incorrect error handling
  (PoSD ch. 10).
- Every error a module can raise is part of its interface and can travel several stack levels, so
  more error cases means a shallower module and more work for callers and their callers (PoSD ch. 10).
- Error handling that hides what the code does is wrong even if it is complete; it has to be a
  separate concern that can be read independently of the main logic (CC ch. 7).
- Throwing in order to avoid a hard decision passes the problem to someone with less information.
  If you cannot decide what to do, the caller probably cannot either (PoSD ch. 10).

The practical consequence: the goal is fewer places where errors have to be handled, not more
detection for its own sake.

## 2. Step 0: enumerate the failure conditions

For the routine in front of you, write a short list. The usual sources (PoSD ch. 10):

- arguments or configuration from the caller are bad;
- something the routine calls cannot complete (I/O failure, missing resource);
- a distributed-system problem (lost or delayed message, unresponsive server, peer misbehaving);
- a detected bug or internal inconsistency.

Add two that are easy to forget: the routine has no answer for a valid input (empty list, key not
present; FPiS ch. 4 calls such a function partial), and the routine acquires something it must give
back (see `resources-and-cleanup.md`).

## 3. The classification procedure

Ask in this order; stop at the first yes. The first four leave the least handling code behind
(order of preference from PoSD ch. 10, with the expected/unexpected split from PP ch. 4 and FPiS
ch. 4).

| # | Question | If yes | Class |
|---|---|---|---|
| 1 | Can the operation's meaning be restated so this case is a normal result, without hiding anything callers need? | Redefine the contract | Defined away |
| 2 | Is the alternative outcome a genuine domain rule with a sensible stand-in value? | Return a special-case object or empty value | Special case |
| 3 | Can this module recover by itself (retry, resend, replica, fallback) and do callers not need to know? | Handle it inside | Masked |
| 4 | Is it an outcome that can legitimately occur and that at least one caller will want to act on? | Put it in the return type, or a documented specific error | Expected outcome |
| 5 | Is it a failure of the environment in something that should have worked? | Raise or propagate with context; handle once at a boundary | Unexpected failure |
| 6 | Is it impossible if all the code is correct? | Assert; stop the unit of work | Bug / contract violation |
| 7 | Is it rare, with no sane recovery in this application? | Fail with diagnostics through one wrapper | Fatal |

Closing checks:

- Have you hidden something important? Things that do not matter should be hidden, the more the
  better; things that matter must be exposed (PoSD ch. 10).
- Does the signature or documented contract tell a caller how each remaining failure is signalled,
  and can it be silently ignored? (CC ch. 7; FPiS ch. 4.)
- Is one convention used across the layer? (FPiS ch. 4 warning sign.)

## 4. Class by class

### Defined away

- Signals: callers wrap the call in catch-and-ignore; callers clamp, test for existence, or
  otherwise pre-check before calling; the "error" is the state the caller wanted anyway.
- Treatment: restate the operation as an outcome to ensure. Details and examples in
  `define-errors-away.md`.
- Wrong when: the caller would act differently if told; the silent result could conceal a logic bug
  that matters (inferred caution in the notes: financial index arithmetic, security checks).
- Verify: a test that the formerly failing call returns normally; a search showing the callers'
  guard code is gone.

### Special case

- Signals: a caller catches a "not found" only to substitute a default; `if x is None` followed by
  the same fallback in several places; a boolean such as `hasSelection` consulted throughout.
- Treatment: the callee always returns an object of the expected type; the stand-in implements the
  default behaviour (CC ch. 7); or represent "none" as an empty value that flows through the normal
  path (PoSD ch. 10).
- Wrong when: the default is not a real rule and merely papers over missing required data.
- Verify: callers contain no branch for the case; a test of the stand-in's behaviour.

### Masked

- Signals: retry or reconnect loops repeated in callers; an error that every caller treats by
  trying again.
- Treatment: do the recovery in the lowest module that can, typically a widely used library layer.
- Wrong when: callers need to learn of the failure to stay correct; recovery can loop forever with
  no way for a person or supervisor to interrupt.
- Verify: fault-injection test with a dependency that fails a few times; a test of the permanent
  failure case.

### Expected outcome

- Signals: user-supplied input, lookups, parsing, optional files, anything where "no" is a normal
  answer. Rule of thumb (FPiS ch. 4): if some caller might reasonably recover, give them a value.
- Treatment: optional when only presence matters; a result with an error type when the reason
  matters; an accumulating form when several independent problems should be reported together.
- Wrong when: used for bugs. A result type for "index out of range in my own loop" just moves the
  noise.
- Verify: tests for both branches; no unwrap right after creation; review question "can the caller
  see from the signature everything that can go wrong?"

### Unexpected failure

- Signals: something that ought to exist or work does not (PP ch. 4: a system file that must be
  present; a read on an already open handle).
- Treatment: exception, or error value with wrapped cause in languages that use values. One handler
  at the unit-of-work boundary. Message says what was being attempted and on what.
- Wrong when: the handler is used as an if-statement for an anticipated case.
- Verify: a test that forces it and checks type, message content, and state consistency afterwards.

### Bug / contract violation

- Signals: "this can't happen"; a default branch; a violated precondition or invariant.
- Treatment: assertion or contract check that stays on; on failure, stop without relying on the
  state that triggered it (PP ch. 4).
- Wrong when: the condition can be caused from outside the program.
- Verify: violate it once on purpose and read the report.

### Fatal

- Signals: out of memory; internal inconsistency; in many applications a hard I/O error on an open
  file or failure to open a required socket (PoSD ch. 10).
- Treatment: one wrapper that checks and aborts with a clear message, so call sites do not each
  check and so a forgotten check does not turn into a confusing later fault.
- Wrong when: recovery from that very condition is the product's job (a replicated store and I/O
  errors).
- Verify: the wrapper is the only place that calls the underlying primitive.

## 5. Where the handler goes

- Low, for masking: one implementation inside the library that everyone calls.
- High, for aggregation: one catch near the top of the request or command loop. Works best when
  errors pass up through several levels untouched (PoSD ch. 10).
- At the boundary, for translation: wrap third-party and I/O calls so foreign error types are
  converted once (CC ch. 7; FPiS ch. 4).
- Division of knowledge: the raising code composes the message because it knows what went wrong;
  the top handler knows how to present an error and does only that (PoSD ch. 10).
- Keep "abort this request" errors and "the process cannot continue" errors as visibly different
  types (PoSD ch. 10).
- Write the handler skeleton first, with the body as a transaction whose handler leaves things
  consistent (CC ch. 7). The notes add that this analogy is idealised: resource release needs its
  own construct, and external effects may need real transactions or compensation.

## 6. Contested rules and how to decide

### Exceptions or values

- For exceptions (CC ch. 3, ch. 7): return codes force a check after every call, nest the
  algorithm inside success branches, and are forgotten; a shared error-code enumeration becomes
  something every file depends on, so people reuse old codes instead of adding accurate ones.
- For values (FPiS ch. 4): a throw is invisible in the type, the compiler does not prompt the
  caller, and the meaning of the expression depends on the surrounding `try`. Checked exceptions
  try to fix visibility but do not work with higher-order functions, which cannot declare what
  their function arguments might throw.
- For restraint (PP ch. 4): exceptions are a non-local jump; used for ordinary flow they couple
  callers to callees and read like spaghetti.
- Decide: follow the layer's convention; values for expected outcomes where the language checks
  them; exceptions (or panics) for the unexpected and the impossible; never untyped sentinels. In
  a value-based language, the "flat happy path" that exceptions were meant to buy is obtained with
  early return or a propagation operator.

### Detect more, or define fewer

- Defensive view (PP ch. 4; WPF ch. 10): check everything, fail fast, be strict in what you accept;
  the closer a failure is to the defect, the cheaper the diagnosis.
- Reductive view (PoSD ch. 10): each rejected input is another case callers must handle; extra
  checks add code that carries its own bugs; simpler software has fewer bugs.
- These address different classes. Strictness and fail-fast are right for contract violations
  between modules (class 6). Reduction is right for conditions that are legitimate and that callers
  uniformly do not care about (classes 1 to 3). When unsure which you have, ask whether a caller
  doing this is necessarily wrong. If yes, reject loudly. If no, and nothing useful is lost, absorb
  it.

### Strict or liberal inputs

- PP ch. 4 deliberately prefers narrow, explicit input domains at internal module boundaries, the
  opposite of "be liberal in what you accept". PoSD's substring example prefers an API that is
  well-defined for any indices.
- Decide: widen the domain when a natural, unsurprising meaning exists for the extra inputs and
  callers currently write guard code. Keep it narrow when no natural meaning exists and an
  out-of-range argument indicates a caller mistake.

### One error type or many

- CC ch. 7: classify by how callers catch; one type per area usually suffices; distinct types only
  if some caller catches one and not another.
- PoSD ch. 10: fewer exception types make a deeper interface.
- Counterpoint recorded in the notes: API consumers may want a small hierarchy with machine-readable
  codes. Both follow from designing for the caller's needs; list the distinct caller reactions and
  create that many types.

### Special-case objects or loud failure

- For: removes branches from every caller (CC ch. 7; PoSD ch. 10).
- Against (notes' caveat): a placeholder can stand in for something that was required and hide a
  data error.
- Decide: is the default written down as a rule of the domain? If someone would be surprised to
  find the stand-in in a report, fail instead.

### Check first or attempt and handle

- PP ch. 4: when a file may or may not exist, test for it and return an indicator rather than rely
  on an exception.
- Notes' caveat: check-then-open is a race in concurrent or security-sensitive settings, and some
  language cultures (Python) attempt first by convention. There, attempt the operation and treat
  not-found as a normal caught result, converted to a value at once.
- The principle that survives either way: classify the failure as expected or not, and make the
  expected ones visible in the interface.

### Who checks the precondition

- Contract view (PP ch. 4): the caller is responsible for meeting the precondition; the routine is
  written assuming it holds; with language support the check is neither party's code.
- Practical view (notes on CC ch. 7): guard clauses at entry are common and fine, and public
  boundaries that receive user input or deserialised data must validate regardless.
- Decide: at a trust boundary, validate with real error handling. Inside the boundary, assert the
  precondition in the callee (cheap, catches the caller's bug at its source) and do not write
  recovery code for it.

## 7. Worked classifications

**A container with `add` and `fetch`** (PP ch. 4 exercise; the answers are marked inferred in the
notes). No memory for the new element: fatal or unexpected failure, so an exception. Requested entry
not found: an expected outcome, so a return value. Null passed to `add`: a caller bug, so a
precondition or assertion.

**Opening a file** (PP ch. 4). A file the system requires: absence is an unexpected failure, let it
propagate. A name the user typed: absence is an expected outcome, return an indicator; real I/O
faults can still raise.

**Mean of a list** (FPiS ch. 4). The empty list has no mean. Throwing hides it from the type.
Returning NaN or another sentinel lets it travel silently. Taking a default argument forces the
immediate caller to decide and fixes the return type. Returning an optional makes the function
total and lets whichever level is appropriate decide.

**Removing a variable or a record** (PoSD ch. 10). If the usual use is clean-up, "absent already"
is the goal state. Define the operation as "ensure absent" and the error disappears. Signal that
the original was wrong: callers wrapped it in catch-and-ignore.

**Substring with out-of-range indices** (PoSD ch. 10). Defining the result as "the characters, if
any, whose index is in range" removes the caller's clamping code. Contested where an out-of-range
index would indicate a bug worth knowing about.

**A missing request parameter in a web handler** (PoSD ch. 10). Every service method would handle
it the same way, by producing an error response. Let it propagate to the dispatcher; the parameter
extractor writes the message; the dispatcher builds the response. Other request errors (malformed
number, permission denied) join the same base type with no change to the dispatcher.

**Expenses with nothing filed** (CC ch. 7). The caller wants a total either way. The data-access
call always returns an expenses object; when none were filed it returns one whose total is the
per-diem amount. Legitimate because the per-diem is a stated rule.

**Corrupted object in a storage server** (PoSD ch. 10). Rather than a dedicated repair mechanism,
treat it as a server crash and reuse crash recovery. Acceptable because corruption is rare; the
shared recovery path also gets exercised more often.

**Square root of a number the user typed** (PP ch. 4). Non-negativity is the routine's
precondition. The caller, which read the input, decides the policy for a negative number (stop,
ask again, or something else). The routine is written knowing its argument is in range.

## 8. Review checklist

- Each failure condition is listed and has a class.
- No class-1 to class-3 treatment hides information a caller needs.
- Expected outcomes are in the return type or a documented error; unexpected ones carry context.
- No catch implements a business branch; no handler is empty without a stated reason.
- Handlers with identical bodies have been merged upward or into a wrapper.
- One convention per layer.
- Each handler that remains has a test that makes it run.
