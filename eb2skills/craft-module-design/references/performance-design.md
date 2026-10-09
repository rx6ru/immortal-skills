# Designing for performance

How to take performance into account while designing, and how to make something faster without
wrecking its structure. Main source: APOSD ch. 20; supporting points from Pragmatic Programmer
ch. 2, ch. 5 and appendix B.

Contents
1. Stance
2. Know what is expensive
3. Design-time choices
4. When to accept complexity for speed
5. Measure before modifying
6. Fundamental fixes first
7. Redesign around the critical path
8. Worked example: a chunked buffer
9. Deliberate, contained violations of other rules
10. Procedure
11. Verification
12. Limits

## 1. Stance

Two extremes fail. Optimising every statement slows development, adds complexity, and many of the
optimisations do not help. Ignoring performance leads to many small inefficiencies spread through
the code; the book puts the possible result at a system 5 to 10 times slower than it need be, with
no single fix that makes much difference.

The middle path: use basic knowledge of what is fundamentally expensive to choose designs that are
naturally efficient and also clean and simple. The chapter's conclusion is that clean design and
high performance are compatible: complicated code tends to be slow because it does redundant work.

## 2. Know what is expensive

Cost classes named in the chapter. The figures are from 2018 and approximate; use the ordering, not
the numbers.

| Operation | Rough cost given in the notes |
|---|---|
| Network round trip within a datacentre | 10 to 50 microseconds, tens of thousands of instruction times |
| Wide-area network round trip | 10 to 100 milliseconds |
| Disk I/O | 5 to 10 milliseconds, millions of instruction times |
| Flash storage I/O | 10 to 100 microseconds |
| Dynamic memory allocation | The allocation plus freeing or garbage-collection overhead |
| Cache miss | A few hundred instruction times; often as significant as computation |

Learn real costs with micro-benchmarks: small programs that measure one operation in isolation. The
notes report that the author's project built a micro-benchmark framework in a few days, after which
a new benchmark took minutes.

Measuring has its own hygiene (Pragmatic Programmer app. B): uneven results usually mean other load
or swapping; avoid noisy shared machines; compiler settings can change results significantly;
measure in the target environment.

## 3. Design-time choices

When two options are equally simple, take the cheap one.

- Keyed lookup: a hash table instead of an ordered map, unless ordering is needed. The chapter
  gives 5 to 10 times as a possible difference.
- An array of structures stored inline instead of an array of pointers to separately allocated
  objects: one allocation instead of many.
- Avoid needless allocation, needless layer crossings, and network or storage calls inside tight
  loops.

Simplicity helps directly:

- Special cases that have been designed away need no checks.
- Deep modules are more efficient than shallow ones: more work per call and fewer layer crossings,
  each of which has overhead.

A per-call cost multiplies by depth or count. The appendix exercise: a recursive tree walk with a
large local buffer in each frame uses stack in proportion to depth; allocating one buffer outside
and passing it down makes the cost constant. Hoist large per-call costs out of recursion and loops.

## 4. When to accept complexity for speed

- The efficient design costs a little extra complexity that stays hidden inside the module and out
  of interfaces: acceptable, bearing in mind that complexity accumulates.
- The efficient design adds a lot of implementation complexity or complicates interfaces: start
  with the simple version and optimise later if needed.
- Exception: clear evidence that performance will matter in this place, such as prior measurement.
  Then do it up front. The notes' example is a storage system that bypassed the operating system's
  networking from the start, because earlier measurements had shown it too slow; getting that one
  large issue right allowed the rest to be designed for simplicity.

"Clear evidence" is a judgement call; the chapter gives no threshold.

## 5. Measure before modifying

Intuition about performance is unreliable, including that of experienced developers.

1. Measure to find where tuning matters. Go deeper than top-level numbers until you have a few
   specific places that consume significant time and for which you have ideas.
2. Establish a baseline so you can measure again after the change.
3. If a change makes no measurable difference, back it out, unless it also made the code simpler.
   There is no reason to keep complexity that bought nothing.

## 6. Fundamental fixes first

Look first for a change in approach: a cache, a different algorithm or data structure, bypassing an
expensive layer. Implement it with the normal design techniques.

Adaptation (marked inferred in the notes): for services the equivalents are fixing repeated
per-item queries, batching and adding a cache, after profiling.

## 7. Redesign around the critical path

A last resort when no fundamental fix exists.

1. Ask what is the smallest amount of code that must run to perform the task in the common case.
   Ignore the existing structure.
2. Imagine writing that as one function: no special cases, all the relevant code together, only the
   data that is needed, in whatever shape is most convenient. This is the ideal, the simplest and
   fastest the code could be.
3. Look for a clean design that comes as close to the ideal as possible. Keep the ideal code mostly
   intact; a little extra, such as a call to a general-purpose class, is fine. It is almost always
   possible to get close.
4. Move special cases off the critical path. Each one adds conditionals or calls. Ideally one test
   at the start detects every special case; if it fails, control goes to separate code off the
   path. That code can be written for simplicity, since special cases are not performance-critical.

This is the fast-path and slow-path shape (the notes mark that naming as their own generalisation).

```python
def append(self, data: bytes) -> None:
    # single guard: zero when there is no chunk, the last chunk is not ours, or it is full
    if len(data) <= self._spare_in_last_chunk:
        self._append_in_place(data)          # critical path, no further checks
    else:
        self._append_slow(data)              # all special cases live here
```

## 8. Worked example: a chunked buffer (APOSD ch. 20)

A buffer class presents what looks like a linear byte array and stores it as chunks. Chunks are
either external (the caller owns the storage and the buffer refers to it, to avoid copying large
data) or internal (the buffer owns the storage and copies small data in). The class itself was a
fundamental fix: it avoids copying large objects when assembling a response.

Measurement showed heavy use, several buffers per request. The critical path chosen was appending a
small amount of new data to internal storage. The ideal: one check that the last chunk is internal
and has room, then extend it.

The original code went through three layers of methods with near-identical signatures, effectively
pass-through methods, and checked six distinct conditions along the way, some of them twice, with
each call's result checked again by its caller.

The redesign, built around this path and around another common operation (getting the total
length):

- shallow layers removed, deeper internal abstractions introduced;
- one method for the append path, with a single test that rules out all special cases, using a new
  field holding the unused space directly after the last chunk (zero when there is none, when the
  last chunk is not internal, or when there are no chunks);
- total length maintained incrementally on each append, a small added cost, because recomputing it
  over many chunks was expensive and the operation is common.

Reported results: the class shrank by about 20 percent (1886 lines to 1476), and the measured
operations became about twice as fast (appending one byte to internal storage 8.8 ns to 4.75 ns;
construct, append a small chunk, destroy 24 ns to 12 ns).

Lessons: the speed-up came from simplification; the pass-through layers that were a design red flag
were also the performance problem; and a derived value was cached deliberately, inside the class.

## 9. Deliberate, contained violations of other rules

Performance is the usual reason to break a design rule on purpose. Both books allow it under the
same conditions: it comes later, it is measured, and it is confined.

- Duplicated knowledge (Pragmatic Programmer ch. 2): caching a derived value violates single
  representation. Allowed as an optimisation if hidden inside one unit that keeps the copies
  consistent, for example a cached length with a changed flag set by the mutators and recomputed
  lazily. The outside sees no duplication. Reading values through accessors is what makes this
  possible without touching callers.
- Tight coupling (Pragmatic Programmer ch. 5): modules may be coupled closely for a measured gain,
  as a database is denormalised, provided the coupling is known and accepted. Accidental,
  undocumented coupling is the failure.
- Forwarding overhead: Demeter-style delegation adds calls; in rare cases the overhead matters and
  the rule gives way, with the same documentation requirement.
- Lazy instantiation (Clean Code ch. 11): described as an optimisation and perhaps a premature one;
  if needed, have the wiring layer provide it instead of scattering null checks through business
  code.

## 10. Procedure

1. At design time, pick naturally efficient options that cost no extra complexity. Know the cost
   classes.
2. Is there hard evidence that this area is performance-critical? If yes and the fix adds
   complexity, do it now and keep the complexity inside the module. Otherwise write the simple
   version.
3. If it turns out too slow: measure at depth, with a baseline, and locate specific hot spots.
4. Look for a fundamental fix.
5. Failing that, define the critical path, write the ideal, redesign to approach it cleanly, and
   push special cases behind one test.
6. Measure again. Revert changes that did not help unless they simplified the code.
7. Document any deliberate rule-breaking at the place it happens, with the measurement that
   justified it.

## 11. Verification

- Before and after numbers on the same workload and environment, reported to the user with the
  method used. Keep only changes with a significant measurable gain.
- Micro-benchmarks for hot primitives where a design choice depends on their cost.
- Static review of the critical path: count conditionals, calls and allocations; the target is a
  single guard check.
- Size and layering (marked inferred in the notes): a performance change should not increase code
  size or layer count; a speed-up that comes with simplification is the sign of success.
- Interfaces unchanged, or simpler; the optimisation is not visible to callers.
- Any cached or duplicated value has one owner that keeps it consistent, and a test that exercises
  the invalidation.
- Functional tests still pass; the optimisation changed no behaviour.

## 12. Limits

- The latency numbers are dated and the example is low-level systems code. Nanosecond-level tuning
  matters only in latency-critical code.
- Do not optimise without measurement, and do not keep an optimisation that measurement does not
  support.
- Micro-benchmarks measure an operation in isolation and can mislead about a whole system; confirm
  on a realistic workload before claiming an end-to-end gain (an adaptation, not from the books).
- Modelling how throughput behaves under load is a different subject: see
  `arch-scalability-analysis`.
