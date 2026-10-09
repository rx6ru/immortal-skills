# Resources and cleanup

How to make sure everything acquired is released on every path, including the failure paths that
error handling introduces. The material is from The Pragmatic Programmer (PP) ch. 4, section
"How to Balance Resources", with one point from Clean Code (CC) ch. 7. Mappings to current
language constructs are adaptation and are collected in `language-mappings.md`.

## What counts as a resource

Anything of limited availability that is obtained and must be given back: memory, transactions,
threads, files, timers, windows, locks, connections (PP). By the same reasoning, subscriptions,
temporary files and directories, spawned processes and leases belong on the list (adaptation).

## The rule

The routine or object that allocates a resource is responsible for deallocating it. The normal
shape is allocate, use, deallocate, visibly together (PP).

## Why it goes wrong: the worked case

The notes' example (PP), retold:

- One routine opens a customer file into a shared, global handle and reads a record. Another
  rewinds, writes the record and closes that handle. A third calls the first, changes the balance,
  and calls the second. The open and the close are in different routines, tied together by a
  global that the third routine never mentions.
- A change request arrives: write only when the new balance is not negative. The maintainer puts
  the write call inside an `if`. Tests pass.
- In production, some hours later: too many open files. When the write is skipped, nothing closes
  the file.
- A poor fix adds a close in the `else` branch of the third routine. Now three routines are coupled
  through the global.
- The sound fix: the third routine opens the file, passes the handle as a parameter to the read and
  write routines, which no longer open or close anything, and closes it before returning. Open and
  close sit together; the global is gone.

Pattern to recognise: a leak that appears only after someone adds an innocent conditional or early
return means acquisition and release live in different places.

## Procedure for code that acquires something

1. **Locate the pair.** For each acquire (open, lock, begin, allocate, start, subscribe), point to
   the release in the same routine or in the lifetime of the same object. If you cannot, fix that
   first: lift both to a common caller and pass the resource down as a parameter.
2. **Bind the release to scope.** Use the language's construct that runs on every exit path. With
   exceptions a routine has at least two ways out; writing the release once in the handler and
   again at the normal end duplicates it and will be missed on the next change (PP).
3. **Place the acquisition correctly relative to the protected block.** Acquire first, then enter
   the block whose cleanup releases it. If the acquisition is inside the block, a failed
   acquisition runs cleanup for something that was never obtained; if other statements sit between
   acquisition and the block, a failure there leaks (PP notes this on its own sample).
4. **Order.** Release in the reverse order of acquisition, so that a resource that refers to
   another is not left dangling. Acquire the same set of resources in the same order everywhere,
   which removes one cause of deadlock: two parties each holding what the other wants (PP).
5. **Do not let helpers own what they did not acquire.** A routine that receives a handle uses it;
   it does not close it unless ownership transfer is its documented purpose.
6. **Handlers leave state consistent** as well as resources released: a handler's job after a
   failure inside its block is to put the program back into a state callers can continue from
   (CC ch. 7). Releasing the file is not enough if a half-written record remains; that needs a
   transaction, a write-then-rename, or compensation (the notes on CC ch. 7 flag the try-as-
   transaction picture as idealised for exactly this reason).

## Mechanisms

| Mechanism | How it balances | Notes |
|---|---|---|
| Scope-bound object (constructor acquires, destructor releases) | Released automatically when the object goes out of scope, on any exit | PP's preferred form in languages with deterministic destruction. Make the object a local, or hold a heap object through a small owning wrapper or the standard owning pointer. The specific smart pointer the 1999 text names is deprecated; use the current owning pointers |
| `finally` block | Runs if any statement of the `try` runs, whether it leaves by exception or return | The fallback in garbage-collected languages, where collection is lazy and finalisers may never run, so destructors cannot be trusted for non-memory resources (PP) |
| Block-scoped resource statements | Compiler-generated `finally` | Current form of the above in most managed languages (adaptation) |
| Deferred call | Registered at acquisition, runs at function exit in reverse order | Adaptation; note the reverse order matches rule 4 |
| Finalisers | Not a mechanism | Unreliable; never the only release path (PP) |
| Emulated non-local jumps in C | No automatic release | Think hard about orphaned resources (PP challenge) |

Sketches (fresh):

```python
def update_customer(path, name, new_balance):
    with open(path, "r+b") as f:            # acquired, then protected
        rec = read_customer(f, name)        # helper uses the handle, does not close it
        if new_balance >= 0:
            rec.balance = new_balance
            write_customer(f, rec)
    # closed here on every path
```

```go
func transfer(a, b *Account, n int) error {
    first, second := lockOrder(a, b)        // one global order everywhere
    first.mu.Lock()
    defer first.mu.Unlock()
    second.mu.Lock()
    defer second.mu.Unlock()                // runs first: reverse of acquisition
    return move(a, b, n)
}
```

## When acquisition and release cannot be in one routine

Dynamic structures: a routine allocates a node and links it into something that lives longer. Set
an ownership rule, a semantic invariant for the structure, and decide what happens when the
top-level structure is released (PP). Three options:

1. The top level releases its substructures recursively.
2. The top level alone is released; what it pointed to, if not referenced elsewhere, is orphaned.
3. The top level refuses to be released while it still contains substructures.

Choose per structure, make the choice explicit, and implement it consistently. In a procedural
language, write one module per major structure that provides its standard allocate and release
operations (and, usefully, debug printing, serialisation and traversal). If tracking becomes
difficult, use reference counting (PP).

The same decision applies to anything handed across a boundary: a connection returned from a
factory, a buffer passed to a callback. State in the interface who releases it (adaptation of the
ownership rule).

## Checking the balance

Do not assume release happens; build something that checks (PP):

- Wrap each resource type and count acquisitions and releases in the wrapper.
- At points where the program's logic dictates a known resource state, assert it.
- In a long-running request server, the top of the main loop, waiting for the next request, is the
  place to check that usage has not grown since the previous iteration.
- Use leak-detection tools. The ones the book names are dated; the notes give memory checkers,
  sanitizers, heap profilers, handle and descriptor counters and connection-pool metrics as the
  current equivalents.
- A contract can state the balance directly: a postcondition "resource count unchanged" (PP
  challenge).

```python
def test_update_releases_handle_on_all_paths(tmp_path):
    path = tmp_path / "customers.dat"
    path.write_bytes(b"ann,0\n")
    before = open_fd_count()                  # e.g. len(os.listdir("/proc/self/fd")) on Linux
    for balance in (10, -10):                 # write path and skip path
        update_customer(path, "ann", balance)
    with pytest.raises(FileNotFoundError):
        update_customer(tmp_path / "missing.dat", "ann", 10)   # failure path
    assert open_fd_count() == before
```

## Small habits with a reason

- Clearing a pointer after freeing it makes a later use fail at once and makes a second free
  harmless (the explanation is marked inferred in the notes).
- Dropping a reference when finished in a long-lived scope lets a collector reclaim the object
  sooner and makes accidental reuse fail fast (also marked inferred).

## Warning signs

- A handle, connection or lock stored in a global or long-lived field and released by a different
  routine from the one that acquired it.
- Release calls written more than once in a routine (one per exit).
- A routine with an early return or a new conditional added after an acquire and before its
  release.
- A resource created before a `try` with other fallible statements in between.
- Resources released in acquisition order, or locks taken in different orders in different places.
- Reliance on finalisers or garbage collection to close files, sockets or transactions.
- A structure whose documentation does not say who frees its contents.
- "Too many open files", pool exhaustion or lock timeouts that appear only under sustained load.

## Review checklist

Marked in the notes as inferred from the section:

- For every acquire, can you point to the release in the same routine or the same object's
  lifecycle?
- Does release happen on every exit path, including early returns and failures, through a language
  construct and not through duplicated calls?
- Are multiple resources released in reverse order and acquired in one global order?
- For structures that outlive the allocating routine, is the owner documented?
- Is there a test or run-time check that resource counts return to baseline after a unit of work?

## Related

- Lock ordering and deadlock in depth: `craft-concurrency`.
- Scoped release in streaming and effect systems: `fp-effects-and-streams`.
- Undoing external effects when a multi-step operation fails part-way: `arch-transactions`,
  `arch-distributed-workflows`.
