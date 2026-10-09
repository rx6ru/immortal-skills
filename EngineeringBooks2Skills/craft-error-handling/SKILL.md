---
name: craft-error-handling
description: Decision procedures for how code should treat failure - design the error out of the interface, mask it low down, handle it once at the top, surface it as an exception or typed result, assert it as a contract, or crash - plus rules for null and absent values, resource release, and validation that reports every problem. Use when writing or reviewing code that throws, catches, returns null or error codes, wraps a third-party or I/O call, validates input, or acquires files, locks, connections or transactions; when a user says "add error handling", "should this throw or return null", "make this robust", "why is this error swallowed", "show all form errors at once", "add assertions" or "we leak connections"; and when designing a module's error contract. Finding the cause of an existing failure belongs to craft-debugging; the Option/Either combinator toolkit belongs to fp-data-and-errors.
---

# craft-error-handling

## Purpose

Error handling is where much of a program's complexity and many of its worst failures come from, and
handlers are the code that runs least and is tested least. With this skill you stop adding a
try/catch or a null check by reflex. For each way an operation can fail you classify the failure,
choose the cheapest treatment that is still honest to the caller, put the handling in the one place
that knows what to do, and prove the failure path by forcing it.

## Choose what applies

| Situation in front of you | Do this | Read |
|---|---|---|
| Writing a new function or API and wondering what it should do when something is wrong | Run the classification procedure below for each failure condition | `references/choosing-a-strategy.md` |
| Callers wrap a call in catch-and-ignore, or clamp/pre-check arguments before every call | Redefine the operation so the case is a normal result | `references/define-errors-away.md` |
| The same catch body is repeated at many call sites | Let it propagate to one handler near the top of the request/command loop | `references/define-errors-away.md` (aggregation) |
| Retry/reconnect/fallback logic is copied into callers | Mask it inside the lowest module that can recover, provided callers do not need to know | `references/define-errors-away.md` (masking) |
| "Should this throw, return null, return a status, or return a Result?" | Apply the expected-outcome vs should-never-happen split and the layer's existing convention | `references/exceptions-results-and-null.md` |
| Code returns or passes null, -1, NaN, empty string as "nothing" | Empty collection, special-case object, optional type, or typed result, depending on what the caller needs | `references/exceptions-results-and-null.md` |
| A vendor or I/O API throws many types or returns nulls | Wrap it once; translate to your own error type at the boundary | `references/exceptions-results-and-null.md` |
| "This can never happen", a `default:` that does nothing, an invariant on a data structure, a subclass overriding a method | State the contract; add assertions that stay on; crash early on violation | `references/contracts-and-assertions.md` |
| Deciding which checks survive into production builds | Input and critical-result checks are hard-coded; cheap assertions stay; prune only measured hot ones | `references/contracts-and-assertions.md` |
| Opens, locks, transactions, temp files, subscriptions; a leak that appeared after a small change | Pair acquire and release in one routine or one object's lifetime, released by a language construct | `references/resources-and-cleanup.md` |
| A form, config file, request body or batch where the user should see every problem | Accumulate independent checks; short-circuit only dependent steps | `references/validation-and-accumulation.md` |
| Need the idiom in a specific language (TypeScript, Python, Rust, Go, Java, Kotlin, Swift, C#, C/C++) | Look up the mapping, including which assert forms are stripped | `references/language-mappings.md` |

This skill does not apply, or applies only lightly, when:

- You are diagnosing an existing failure. Use `craft-debugging`; come back here when choosing the
  fix and the assertion that would have caught it earlier.
- The question is about failure between services (retries with idempotency keys, sagas, timeouts
  across a network of services). Use `arch-transactions` and `arch-distributed-workflows`. The
  masking and aggregation ideas here still describe where in a client library the handling goes.
- The task is the shape of functions or modules in general. Use `craft-clean-code` and
  `craft-module-design`. This skill covers only the error part of an interface.
- The user asked for a small change in a codebase with a settled error convention. Follow the
  convention; do not convert a module from exceptions to results (or back) as a side effect.

## How to apply

### 1. Classify every failure condition before writing a handler

List the ways the operation can fail to do what its name says. For each one, ask the questions in
order and stop at the first that fits. The order is a preference order: the earlier treatments leave
less handling code behind, and handling code is the expensive part (throwing is easy; handling is
hard).

1. **Can the operation be redefined so this is a normal result?** "Ensure it no longer exists"
   instead of "delete it"; clamp a range; return an empty collection; represent "nothing selected"
   as an empty selection. If callers lose no information they need, do this and there is nothing to
   handle.
2. **Is absence or the alternative outcome a real rule of the domain?** Return a special-case
   object or a default that embodies the rule (a per-diem object when no expenses were filed). Only
   when the default is a genuine business rule; a placeholder standing in for missing required data
   hides a bug.
3. **Can this module recover on its own without the caller caring?** Retry, resend, read the
   replica, inside the module. This is masking. Do not mask when the caller needs to know (lost
   messages, failed peers, data loss).
4. **Is it an expected outcome that some caller will want to act on?** Not found, invalid input,
   parse failure, a file the user named that may not exist. Put it in the return type: an optional
   when only presence matters, a result carrying a reason when the caller needs the reason. In a
   codebase whose convention is exceptions, a specific documented exception is the equivalent, but
   offer a non-throwing form if callers treat it as a normal branch.
5. **Is it an unexpected failure of the environment in something that should have worked?** A file
   that must exist, a dropped connection mid-read. Raise an exception or propagate an error value
   with context, and catch it in one place that can abort the unit of work (the request, the
   command, the job) and continue.
6. **Is it impossible if the code is correct?** A violated precondition, a broken invariant, an
   enum value outside the known set. That is a bug, not an event. Assert it and stop the unit of
   work without trusting the bad state.
7. **Is it rare, unrecoverable, and without a sane response?** Out of memory, internal
   inconsistency. Fail with a clear diagnostic through one wrapper rather than checks at every
   call site. Whether a condition is in this class depends on the application: a replicated store
   must recover from an I/O error because that recovery is its job.

Then check the result against two questions. Is anything important now hidden from a caller who
needs it? Can a caller tell from the signature or documented contract how each remaining failure is
signalled, and is it impossible to ignore by accident?

### 2. The split that settles most arguments

| The condition is | Mechanism | Who is at fault |
|---|---|---|
| A legitimate thing that happens (bad user input, optional file missing, lookup miss, network refusal you planned for) | Ordinary handling: validation, optional/result value, documented error | Nobody |
| Something that should have worked and did not | Exception or propagated error, handled once at a boundary | The environment |
| Logically impossible if the code is right | Assertion or contract check, left on | A programmer: caller for a precondition, callee for a postcondition |
| The impossible having happened | Stop early, clean up without relying on the bad state | Unknown; preserve the evidence |

A quick test for misuse of exceptions: imagine every handler removed, so an uncaught exception ends
the program. If the program could no longer do its normal work, exceptions are carrying ordinary
control flow and those cases belong in return values. A quick test for misuse of assertions: could
this fire because of something a user typed or the network did? Then it is validation and must be
hard-coded handling, since assertions can be compiled out.

### 3. Exceptions, results, or status codes

The sources disagree on the default, and the disagreement dissolves once you see what each is
protecting.

- Clean Code prefers exceptions to return codes: status checks after every call bury the algorithm
  and are easy to forget.
- Functional Programming in Scala prefers typed results: an exception does not appear in the
  signature, the compiler does not make the caller decide, and its meaning depends on which `try`
  encloses it. It keeps exceptions only for conditions no reasonable caller would catch.
- A Philosophy of Software Design says both count as exceptions for complexity purposes; reduce how
  many exist before arguing over their form.
- The Pragmatic Programmer reserves exceptions for the unexpected and uses return values for
  outcomes that can normally occur.

The shared requirements are: the happy path reads straight through; a failure cannot be silently
ignored; error handling is consolidated rather than scattered. Decide like this:

1. Use what the layer already uses. A module where some functions throw and others return results
   leaves callers unable to know which to expect.
2. In a language built around error values (Go, Rust), use values for everything a caller can
   handle and panic only for bugs.
3. In a language built around exceptions (Java, C#, Python, Ruby), use exceptions for unexpected
   failures; use optional/result returns for expected outcomes where the language gives you a
   checked form (optionals, nullable types under strict checking, sealed types); otherwise a
   specific documented exception.
4. Never a bare status code or sentinel (`-1`, `NaN`, `null`, `""`) that shares the type of valid
   answers. It propagates silently and cannot work in generic code.
5. Whatever the form, the reason must travel with the error: the operation attempted, the entity,
   and the cause.

Checked exceptions: Clean Code calls the debate over in favour of unchecked, because a new checked
type at a low level forces signature changes all the way up. The notes mark that claim as dated and
overstated. Decide by this rule: do not let low-level failure types leak through layers; translate
at each boundary. A checked or typed error is reasonable where failure is an expected, recoverable
part of a contract and the caller sits right next to it.

### 4. Place the handler where it catches the most cases

1. Write the try/catch/finally (or the result-returning skeleton) first when a routine can fail;
   it fixes what the caller may expect. Treat the try body as a transaction: whatever happened
   inside, the handler leaves state consistent or rethrows with context.
2. Keep the body of the try as the happy path. A function that handles errors does that and
   nothing else; extract the body.
3. Masking belongs low, in a widely used module. Aggregation belongs high, at the dispatcher. Both
   put one handler where it covers many call sites.
4. For a request-processing system, define one error base type meaning "abort this request", caught
   in one place in the loop. Build the message where the error is raised (that code knows what
   went wrong); let the top handler only turn it into a response. Keep it distinct from errors
   fatal to the whole process.
5. Define error types by how callers react, not by which component raised them. One type per area
   with data inside is usually enough; add a second type only when some caller catches one and lets
   the other pass.
6. Log where the error is handled, not at each level it passes through. Log-and-rethrow duplicates
   entries; log-and-continue is swallowing.

### 5. Null and absence

- Return an empty collection, not null, for "none".
- Return an optional type when a single value may be absent and that is all the caller needs.
- Return a result with a reason when the caller needs to know why.
- Do not pass null as an argument. Under that convention a null argument is always a bug, so you do
  not defend against it throughout the interior. Public boundaries (user input, deserialised data)
  still validate.
- Do not unwrap an optional or result immediately after creating it (`.get`, `unwrap()`, `!`); carry
  it through with map/flat-map style operations and unwrap at the edge.

### 6. Contracts and assertions

1. For a non-trivial routine, write down the precondition (what the caller must ensure), the
   postcondition (what the routine guarantees) and, for a class, the invariant (true whenever
   control is outside the class). Doing this at design time is the main benefit even if nothing is
   checked at run time.
2. A precondition must be something the caller can check and control. If it depends on user input
   or the environment, it is error handling, not a precondition.
3. Be strict in what the routine accepts and promise as little as it can get away with; a routine
   that accepts anything and promises everything is a lot of code.
4. For a stateful type, write one `is_sane()` check built from one helper per property and assert
   it at entry and exit of each public mutating method. Failing at entry means the corruption
   happened earlier; failing at exit means it happened here.
5. Assertion conditions have no side effects, and nothing that must run lives inside one.
6. Give every switch on a closed set a default that fails, or use exhaustive matching.
7. Keep cheap assertions on in production. If one is measurably expensive, make that one optional.
   In languages that strip the built-in assert by default, use an always-on helper for the checks
   you intend to keep.
8. A subclass may accept more and guarantee more than its parent, never less.

### 7. Resources

1. The routine or object that acquires a resource releases it. If you cannot point to the release
   in the same routine or the same object's lifetime, restructure before adding features.
2. Release through a construct that runs on every exit path (scope-bound object, `finally`,
   `with`/`using`/try-with-resources, `defer`), not through calls duplicated on each path.
3. Release in reverse order of acquisition; acquire the same set in the same order everywhere.
4. Acquire before entering the protected block, so a failed acquisition does not run cleanup for
   something that was never obtained.
5. When a structure outlives the routine that allocates into it, decide and document who owns it.

### 8. Validation

1. Independent checks (each field of a form, each entry of a config) are combined so that all
   failures are collected and reported together.
2. Dependent steps (parse, then use the parsed value) short-circuit at the first failure.
3. A chain in which each step is nested inside the previous one's success can only ever report one
   error. If the user needs all of them, the checks must be run side by side and their error lists
   concatenated.
4. Turn raw input into validated types at the boundary, so the interior takes the validated type
   and has nothing left to check.
5. Tell the user what is wrong in the domain's words ("a PIN has four digits"), not as a failed
   assertion.

## Verify

Run these checks on the code you wrote or reviewed, and show the user the results that matter. The
search patterns are starting points to adapt to the language; they are an adaptation, not something
the books prescribe.

**Search the diff and its neighbourhood**

- Empty or swallowing handlers: `rg -nU "catch\s*(\([^)]*\))?\s*\{\s*\}"`, `rg -n "except.*:\s*$" -A1 | rg "pass"`,
  `rg -n ", _ :?= |^\s*_ = "` (Go), `rg -n "\.unwrap\(\)|\.expect\("` (Rust, outside tests),
  `rg -nU "catch \(e\) \{\s*(console\.log|logger)"`. Each hit needs either a reason in a comment or
  a fix.
- Null and sentinels: `rg -n "return (null|None|nil|undefined|-1|NaN)"`, `rg -n "[!=]==? ?null"`.
  The counts should fall or stay flat, not rise.
- Catch-and-ignore around one particular callee, or clamping before every call to it: the callee's
  contract should change.
- Identical catch bodies: group handlers by body; duplicates collapse into one higher handler or one
  wrapper.
- Vendor error types outside the wrapper: grep for the vendor's exception or error names; they
  should appear only in the adapter.
- Acquire without a paired release in the same scope: `rg -n "open\(|\.lock\(|begin|acquire|connect\("`
  and confirm each sits in a scope-bound construct.
- Strippable asserts guarding input, security or money: `rg -n "^\s*assert "` (Python),
  `rg -n "\bassert\b"` (Java, C), `debug_assert` (Rust). Each must be something that cannot be
  caused from outside.

**Tests to write or run**

1. One test per failure path you kept: force the condition (bad input, missing file, a fake
   dependency that fails) and assert the error type and that the message names the operation and
   entity.
2. After the forced failure, assert that state is still consistent and that the same object can be
   used again (the transaction property of the handler).
3. For a define-away change: a test that the formerly erroneous call now returns the normal result
   (deleting twice succeeds; an out-of-range slice returns empty).
4. For a masked failure: a fake that fails N times then succeeds; assert the caller sees success,
   and a second test that a permanent failure is still surfaced or bounded.
5. For a top-level handler: a test that one failing request produces an error response and that the
   next request is served.
6. For a wrapper: a test with a failing vendor fake asserting that callers only ever see your error
   type.
7. For each assertion added: violate it deliberately once and read the message; it should give
   location and the failed condition. Run the suite with assertions disabled (where the language
   allows) and confirm passing runs produce the same output.
8. For accumulating validation: an input with k independent faults yields k errors, in a stable
   order; adding another check does not suppress earlier errors. For short-circuit chains: a
   counter proving later steps did not run after the first failure.
9. For resources: a test that runs the unit of work many times, including the early-return and
   failure paths, and asserts that the count of open handles, connections or locks returns to its
   starting value.

**Review questions with observable answers**

- Can a caller tell from each public signature or its contract comment everything that can go
  wrong? Point to where.
- Does any path drop the reason for an error? Point to each conversion and show the cause is kept.
- Does each remaining `catch` either restore consistency, translate with context, or end the unit
  of work? Name which.
- Is any `catch` implementing a business branch? If so, that case should be a return value.
- Where is each error logged? There should be one place per error.

**Evidence to show the user**: the list of failure conditions with the class you assigned each; the
before and after counts from the searches; the names of the failure-path tests and their output;
any condition you chose to expose instead of hide, with the caller that needs it.

**Done means**

- Every failure condition of the changed code has a named class and a treatment that follows from it.
- No new empty handler, no new null or sentinel return, no new strippable assert on external input.
- Each kept failure path has a test that forces it and checks state afterwards.
- Errors carry operation, entity and cause, and are logged once.
- Every acquired resource is released by a construct that runs on all exit paths.
- The module uses one error convention, and it matches the surrounding layer.
- Nothing a caller needs has been masked or defined away.

## Proportion and limits

- Match the size of the request. If asked to fix one handler, fix that handler and mention the
  neighbouring problems you saw. Do not introduce a result type, a contract library or an error
  hierarchy into a codebase that has none in order to fix a bug.
- Defining an error away changes the contract. Silent clamping or silent defaults are wrong where
  the error would have revealed a logic bug that matters, such as index arithmetic in financial
  code or a security check (the notes mark this caution as inferred). In those places expose the
  error.
- "Reduce the number of errors" and "crash early" pull in different directions only on the surface.
  The first is about conditions that are legitimate and uninteresting to callers; the second is
  about states that mean the program is wrong. Classify first and the conflict goes away.
- Crashing means different things by context: a command-line tool exits; a server fails the request
  or the worker and a supervisor restarts it; a library raises and never terminates its host. The
  last two are noted in the source notes as widely held practice, not as the books' text.
- Promoting small errors to a crash that reuses one recovery path is only sensible when the error
  is rare and recovery cost is acceptable.
- Assertions cost run time and writing effort. The books' claim that the benefit outweighs the cost
  rests mostly on experience; the notes record a single controlled study. Leaving them on is
  contested by ecosystem defaults (C, Java and Python strip or disable them), so say which checks
  you made permanent and why.
- A specification or assertion can itself be wrong. When code and assertion disagree, review both.
- Typed results in a language without sum types, generics or enforced null checking lose most of
  the "compiler makes you handle it" benefit and add ceremony; in such code prefer the native
  convention and apply results only at boundaries for expected failures.
- Dated material: the notes flag the checked-exception verdict, C `malloc` and NFS examples,
  1990s contract preprocessors and leak tools, and `auto_ptr`. The principles survive; the tools
  are replaced in `references/language-mappings.md`.

## References

- `references/choosing-a-strategy.md` - read when designing the error contract of a new function or
  module, or when a review turns into "throw or return?"; holds the full classification procedure,
  the contested rules with a deciding rule each, and worked classifications.
- `references/define-errors-away.md` - read when callers are burdened by an error (catch-and-ignore,
  pre-checks, duplicated handlers); catalogue of define-away, special-case, mask, aggregate,
  promote, crash, with when each is wrong.
- `references/exceptions-results-and-null.md` - read when writing throw sites, catch blocks, result
  types, wrappers around third-party code, or removing null returns.
- `references/contracts-and-assertions.md` - read when stating preconditions, postconditions and
  invariants, adding assertions, deciding what stays on in production, or overriding a method.
- `references/resources-and-cleanup.md` - read when code opens, locks, begins or allocates, or when
  chasing a leak.
- `references/validation-and-accumulation.md` - read when validating input with several fields or
  items and deciding between first-error and all-errors.
- `references/language-mappings.md` - read to translate any of the above into a specific language
  and to learn which assert forms are stripped there.

## Sources

- A Philosophy of Software Design (1st ed.), ch. 10: defining errors out of existence, masking,
  aggregation, crashing, special cases, and taking it too far.
- Clean Code (1st ed.), ch. 7: exceptions over return codes, try-first, context, caller-oriented
  exception classes, special case, null.
- Clean Code (1st ed.), ch. 3, error parts: exceptions vs error codes, extracting try/catch bodies,
  the shared error-code dependency magnet.
- The Pragmatic Programmer (1st ed.), ch. 4: design by contract, crash early, assertions, when to
  use exceptions, balancing resources.
- Why Programs Fail (2nd ed.), ch. 10: assertions as automated observation, invariants, pre- and
  postconditions, what to keep on in production.
- Functional Programming in Scala (1st ed.), ch. 4: failures as values, optional and either types,
  wrapping throwing code, sequence and traverse.
- Functional Programming in Scala (1st ed.), ch. 12, validation part: independent vs dependent
  effects and error accumulation.
