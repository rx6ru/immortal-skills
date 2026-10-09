# Reducing the places where errors are handled

A catalogue of techniques for removing error handling from callers, in order of preference. All of
it comes from A Philosophy of Software Design (PoSD) ch. 10 unless another source is named; the
special-case object is from Clean Code (CC) ch. 7. Each entry has the same fields: what it is, use
when, do not use when, how, cost, verify, related.

The order matters. Try each technique before the next: redefine, special-case, mask, aggregate,
promote, crash, and only then expose.

## Contents

1. Define the error out of existence
2. Design special cases out of existence
3. Mask the error
4. Aggregate handlers
5. Promote small errors into a larger, already handled one
6. Just crash
7. Otherwise: expose it
- Taking it too far
- Quick diagnosis table
- Verification for the whole area

---

## 1. Define the error out of existence

**What.** Change what the operation means so that the situation is covered by its normal behaviour.
There is then nothing to throw, return or check.

**Use when.**
- Callers surround the call with catch-and-ignore. That is the clearest signal the contract is
  wrong.
- Callers write pre-check code (existence tests, clamping) before calling.
- The "failure" leaves the world in the state the caller asked for.
- Anyone who does need to know can find out another way.

**Do not use when.**
- Callers would behave differently if told (a missing record that should prompt creation; a write
  that did not happen).
- The silent result could conceal a mistake that matters. The notes add, as an inferred caution,
  financial index calculations and security checks as places to expose rather than absorb.

**How.**
1. Restate the operation as an end state to ensure, not an action to perform. "Make sure this
   variable does not exist" is satisfied when it was already gone.
2. For range-like arguments, define the result for every value: "the elements, if any, whose
   position lies in the range" is well-defined for negative, reversed or oversized bounds.
3. For queries, return an empty collection when nothing matches.
4. Update the documentation of the contract; this is a semantic change, not an implementation
   detail.
5. Delete the callers' guard code.

**Examples from the notes.**
- A scripting language's "unset variable" command that raised when the variable was absent, though
  its main use was clearing temporary state whose contents are unknown; every caller wrapped it.
  The author calls it one of his biggest mistakes.
- File deletion: one operating system family refuses to delete a file that is open, leaving users
  hunting for the process; another removes the name at once and keeps the data until the last
  opener closes it. The second defines away both the delete error and any error for processes
  still using the file.
- A substring operation that throws on out-of-range indices forces callers to write several lines
  of clamping; defining the result for all indices removes that code and makes the operation more
  functional for the same interface.

**Cost.** The contract becomes more permissive; a caller's bug that used to be reported may now
pass silently.

**The objection that errors catch bugs.** The reply in PoSD: the erroring design may catch some,
but it adds code (to avoid or ignore the error) that causes others, and forgotten checks become
run-time surprises. The best way to reduce bugs is simpler software. Treat this as an experience
claim, not a proof.

**Adaptation to current APIs** (the notes mark these as generalisation): idempotent delete and put,
upsert, "ensure" operations; an empty list instead of a not-found status for a filtered query
where that suits the consumers.

**Verify.** A test that the previously erroneous call returns normally and that a repeat call has
the same effect; a search showing no caller still guards or ignores around the call.

**Related.** Special case (next); `contracts-and-assertions.md` for the opposite choice, a narrow
precondition.

---

## 2. Design special cases out of existence

**What.** Arrange the normal-case code so that the special case is handled by it with no extra
branch. In its object form: return a stand-in object that behaves correctly for the special case
(Special Case pattern, a relative of Null Object; CC ch. 7).

**Use when.**
- A state flag such as "exists", "is empty", "has selection" is tested in many places.
- A caller catches a not-found error only to supply a default.
- An absent value has a natural neutral form: empty selection, empty list, zero-length range.

**Do not use when.**
- The neutral value is not a real rule of the domain. A placeholder for something required hides a
  data error (notes' caveat on CC ch. 7).
- Downstream code needs to distinguish "none" from "empty" and now cannot.

**How.**
1. Find the notion of absence that is only the user's or caller's concept and need not exist in the
   implementation. A text editor's "no selection" can be a selection whose start equals its end.
2. Make the value always exist. Copying an empty selection inserts nothing; deleting it joins the
   text before and after, which reproduces the original line. No checks.
3. For a lookup with a business default, have the provider return an object of the normal type
   whose behaviour is the default: an expenses object whose total is the per-diem when nothing was
   filed.
4. Remove the flag and its tests.

**Cost.** One more small type or one constant; a risk of over-quiet behaviour.

**Verify.** Grep for the removed flag; tests of the operations on the neutral value (copy, delete,
total) showing ordinary results.

**Related.** `exceptions-results-and-null.md` for the null alternatives.

---

## 3. Mask the error

**What.** Detect and handle the condition at a low level so that higher levels never learn of it.

**Use when.**
- The module can fully recover by itself: resend, retry, read another copy.
- Every caller would otherwise write the same recovery.
- The handling sits in a module used from many places, so doing it once there covers them all.

**Do not use when.**
- Callers need the information to be correct. The counter-example in the notes: a networking module
  that caught and discarded every network error, so applications could not learn of lost messages
  or dead peers and could not be made robust. It had to expose them.
- The recovery can create further problems the peer or caller must then handle (a resend of a
  packet that was only delayed produces a duplicate). Make sure the cascade ends somewhere.

**How.**
1. Put the recovery inside the module that owns the failing operation.
2. Remove the error from the module's interface.
3. Decide what happens when recovery does not succeed: keep trying with a visible signal, or give
   up into one of the later techniques.

**Examples from the notes.**
- A reliable transport protocol hides packet loss by resending inside its implementation.
- A network file system whose clients retry indefinitely when the server is down, printing a
  notice. Applications hang, and users complain, but the alternative is worse: applications can do
  little with the error, per-call retry is more work than one retry in the file-system layer, and
  aborts would cascade through the user's whole environment. With masking, work resumes when the
  server returns, and a person can abort by hand. The notes label this example controversial.

**Cost.** The module is harder to write; a problem may be invisible to operators unless the module
reports it another way. Masking is an instance of pulling complexity downward and makes the module
deeper: less in the interface, more behind it.

**Adaptation** (notes' generalisation): retries and timeouts inside a client SDK are masking.

**Verify.** A fake dependency that fails a few times and then succeeds, with the caller observing
only success; a second test for failure that never clears, checking that the behaviour is the one
you decided on and that a signal is emitted.

**Related.** For retries against other services, idempotency matters; see `arch-transactions`.

---

## 4. Aggregate handlers

**What.** Handle many errors with one piece of code instead of a handler at each site.

**Use when.**
- Several call sites catch and do the same thing.
- The system processes units of work (requests, commands, jobs, messages) and the right response
  to most errors is "abandon this unit, report, continue with the next".
- Errors can pass up through several levels without intermediate code needing to act.

**Do not use when.**
- An intermediate level holds something it must undo or release; it still needs its own cleanup
  construct (see `resources-and-cleanup.md`), though not its own reporting.
- Different sites truly need different reactions.

**How.**
1. Define one error base type meaning "abort the current unit of work". Subtypes for distinct
   conditions only where a caller distinguishes them.
2. Raise at the point of detection with a message composed there, because that code knows what went
   wrong. Store the message in the error.
3. Catch in one place near the top of the processing loop. That handler knows how to present an
   error (build the response, write the log line) and uses the message as given.
4. Keep errors that are fatal to the whole process as a clearly separate type that this handler
   does not absorb.
5. Remove the per-site handlers.

**Example from the notes.** Web service methods each read parameters through an extractor that
raises when one is missing. Students wrapped every extraction in its own handler, all building the
same error response. Letting the error reach the dispatcher needs one handler, and the same handler
then covers malformed values and permission failures, which differ only in their message. New
service methods need no error code at all.

**Sketch** (fresh, Python):

```python
class RequestError(Exception):
    """Abort this request; message is safe to show the client."""

def int_param(req, name):
    raw = req.params.get(name)
    if raw is None:
        raise RequestError(f"missing parameter {name!r}")
    try:
        return int(raw)
    except ValueError:
        raise RequestError(f"parameter {name!r} must be an integer, got {raw!r}") from None

def dispatch(req):
    try:
        return route(req)(req)          # handlers contain no error code
    except RequestError as e:
        return error_response(400, str(e))
```

**Cost.** Control flow becomes non-local; a reader of a service method must know the dispatcher
exists. Mitigate by documenting the base type as part of the framework.

**Adaptation** (notes' generalisation): a central error middleware or exception filter is
aggregation.

**Verify.** One failing request yields an error response and the next request succeeds; grep shows
a single catch of the base type; a new handler that raises a new subtype works without changing the
dispatcher.

**Related.** Aggregation and masking are the same move at opposite ends: put one handler where it
covers the most cases, high for one, low for the other.

---

## 5. Promote small errors into a larger, already handled one

**What.** Instead of building a recovery mechanism for each kind of failure, convert a minor
failure into a major one for which recovery already exists.

**Use when.** The minor failure is rare; a robust recovery path for the major failure exists and
must exist anyway; the cost of the heavier recovery is tolerable at that frequency.

**Do not use when.** The failure is frequent. You would not restart a server for each lost packet.

**How.** On detecting the minor condition, trigger the major one deliberately (in the notes'
example, a storage server that finds a corrupted object crashes itself and the cluster's ordinary
crash recovery restores the data).

**Benefit beyond less code.** The single recovery path runs more often, so its defects surface.

**Cost.** Recovery is more expensive per incident.

**Adaptation** (notes' generalisation): supervised "let it crash" designs follow the same reasoning.

**Verify.** A test that injects the minor fault and checks that the general recovery restores
service and data.

---

## 6. Just crash

**What.** For an error that is hard or impossible to handle and is rare, print diagnostics and
stop.

**Use when.**
- There is nothing useful to do. Out of memory is the standard case: had there been memory to
  spare it would already have been released, and the handler would probably need memory too.
- Internal inconsistencies that indicate a bug.
- In many applications: an I/O error on an already open file, or failure to open a required socket.

**Do not use when.** Surviving that condition is part of what the system is for. A replicated
storage system has to recover from I/O errors using its replicas.

**How.** Wrap the primitive once. The wrapper calls it, and on failure reports and aborts. All code
calls the wrapper. This replaces a check at every call site, and prevents the worse outcome of a
forgotten check turning into a null dereference somewhere else that disguises the real cause.

**Sketch** (fresh, C):

```c
void *xalloc(size_t n) {
    void *p = malloc(n);
    if (p == NULL) { fprintf(stderr, "out of memory allocating %zu bytes\n", n); abort(); }
    return p;
}
```

**Cost.** Loss of the work in progress. See `contracts-and-assertions.md` for what "crash" should
mean in a server or a library.

**Verify.** Grep shows the raw primitive is called only inside the wrapper.

---

## 7. Otherwise: expose it

When none of the above fits, the condition is real and important to callers. Put it in the
interface and document it. `exceptions-results-and-null.md` covers the form.

---

## Taking it too far

- Defining away and masking are legitimate only when callers do not need the information.
- Test before hiding: name a caller that would do something different if it knew. If you can, the
  condition must be visible.
- Hiding is for the unimportant; exposure is for the important. Getting this wrong in either
  direction produces a worse module: too many errors make it shallow, too few make robust
  applications impossible to build on it.

## Quick diagnosis table

| You see | Likely remedy |
|---|---|
| Catch-and-ignore around one callee, in many places | Define away (1) |
| Clamping or existence checks before a call | Define away (1) |
| `if has_x:` scattered through a class | Special case (2) |
| Catch "not found" then substitute a default | Special case (2) |
| Retry loops in callers | Mask (3) |
| Identical catch bodies in sibling functions | Aggregate (4) |
| Several bespoke recovery mechanisms, each rarely run | Promote (5) |
| A check after every allocation or similar primitive | Crash wrapper (6) |
| A module that never reports anything, and callers that cannot tell if work was done | Too far; expose |

## Verification for the whole area

- Count raise sites and catch sites per module before and after (the notes mark counting as
  inferred); the number of catch sites should go down.
- Search for flags like "exists", "empty", "none" used in conditionals and ask whether a neutral
  value could flow through the normal path.
- Because handlers seldom run, force failures in tests. The fewer distinct recovery paths there
  are, the more each is exercised.
