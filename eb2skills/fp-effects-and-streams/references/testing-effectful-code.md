# Testing effectful code

Contents: 1 Principle; 2 Test pure cores directly; 3 Fake interpreters for effectful programs; 4 Stack-safety tests; 5 Law tests; 6 Resource-safety tests with a counting fake; 7 Concurrency tests; 8 Local mutation tests; 9 Evidence to show; 10 Pitfalls.

Sources: FP in Scala ch. 13 (verification: pure interpreters, stack, laws), ch. 15 (law and resource tests), ch. 7 (pool-of-one test), ch. 14 (local mutation checks). Many test designs below are the book's verification notes marked inferred, or adaptation. Property-based testing mechanics are in `fp-api-design-with-laws` and `craft-testing`.

## 1. Principle

The book's answer to "how do I test I/O code without mocks": make the program a referentially transparent expression that makes requests, and run it under an interpreter you control. For code that is only factored (not interpreter-based), the same effect comes from testing the pure core with plain values and running the shell against fakes.

Three layers of test, cheapest first:
1. Pure core: ordinary unit and property tests. No fakes.
2. Program against a port or algebra, run under a fake: assertions on output and recorded requests.
3. A few smoke tests with the real adapter, to check the real interpreter does what the fake claims.

## 2. Test pure cores directly

For the book's `winner` and `winnerMsg`: assertions on return values. If a core function needs a clock, random source or generator, it takes it as a parameter (see `fp-pure-core`), and the test passes a fixed one.

## 3. Fake interpreters

Console example in Python, with scripted input and captured output:

```python
class FakeConsole:
    def __init__(self, inputs): self.inputs, self.out = list(inputs), []
    def read_line(self): return self.inputs.pop(0) if self.inputs else None
    def print_line(self, s): self.out.append(s)

def test_converter():
    c = FakeConsole(["212"])
    converter(c)
    assert c.out == ["100.0"]
```

Free-structure form: the interpreter is a pure function from (program, input buffers) to (result, output buffers). The book's console state interpreter pops the input list on ReadLine and pushes onto the output list on PrintLine. Pair with property-based testing to generate random input scripts and assert invariants of the output.

Design the fake as a working implementation (in-memory file system, clock you advance, queue you drain), not a recorder of expected calls. Tests then check outcomes; refactors that change call order do not break them.

Record-and-replay variant (inferred): an interpreter that logs every instruction yields a trace you can assert on; the same program can be run again with the trace as input.

Check that fake and real agree on the contract with a shared contract test run against both (adaptation; see `craft-testing` contract-testing).

## 4. Stack-safety tests

- Build a looping program with 1e6 iterations (bounded by a condition) and run it with every interpreter (real, fake, async). The book's first Console interpreter passed on small inputs and failed here.
- Run in a thread or process with a small stack so failure is immediate (adaptation).
- Include left-nested bind shapes, since they trigger the reassociation path (`stack-safety.md`).

## 5. Law tests

Effect type
- Left identity: `run(unit(a).flatMap(f)) == run(f(a))` for several `f`.
- Right identity: `run(m.flatMap(unit)) == run(m)`.
- Associativity: both groupings of three steps produce the same output under a fake (reassociation in the trampoline depends on it).

Parallel description (`parallelism-as-description.md`)
- `map(y, id) == y`; `map(map(y, g), f) == map(y, f after g)`.
- `fork(x) == x` under pool size 1, 2, N, with a harness timeout to catch deadlock.
- `parMap(xs, f)` equals sequential map; order preserved.

Stream pipelines (`stream-pipelines.md`)
- `p(xs)` equals the equivalent list function for filter, take, count and similar.
- `(p |> q)(xs) == q(p(xs))`; `lift(f) |> lift(g) == lift(g after f)`.
- Monad-like laws for append and flatMap behave like lists.

Equality for effectful values is defined by running under the same interpreter and comparing results, not by comparing closures.

## 6. Resource-safety tests with a counting fake

```python
class FakeResource:
    def __init__(self, items, fail_at=None):
        self.items, self.i, self.fail_at = items, 0, fail_at
        self.opened = self.closed = 0
        self.is_closed = False
    def open(self): self.opened += 1; self.is_closed = False; return self
    def read(self):
        assert not self.is_closed, "read after close"
        if self.fail_at == self.i: raise IOError("boom")
        if self.i >= len(self.items): return None
        v = self.items[self.i]; self.i += 1; return v
    def close(self): self.closed += 1; self.is_closed = True
```

Scenarios (each asserts `opened == closed` and no read-after-close):
1. Consume all.
2. Take n then stop, with a source of much more than n items.
3. Source raises at read k.
4. Downstream transformer raises on item k.
5. External cancellation.
6. `close()` raises while another exception is in flight: the caller sees the original.
7. Zip of two sources where one ends first: both closed.
8. Dynamic: one resource per item of an index stream, each closed promptly.

Constant memory: source generating far more than memory, `take(n)`, check peak memory is flat (for example with a memory limit in the test process or a counter of items materialised at once).

## 7. Concurrency tests

- 100k forks on a 2-thread pool completes (book's check: `parMap` over a large range on a two-thread pool).
- Bounded thread count during the run (sample active threads).
- Throwing task: run fails with that error; no hang.
- Timeout: short budget on a chain fails near the budget.
- Repeat nondeterministic tests many times and with different pool sizes; a pass once proves little. Deeper techniques are in `craft-concurrency`.

## 8. Local mutation tests

Property: `f(xs)` leaves `xs` unchanged (compare to a deep copy), repeated calls give equal results, result equals a reference implementation; concurrent calls on shared input agree.

## 9. Evidence to show the user

- The command used and its result for each of: the I/O grep outside the shell, the million-step run, the pool-of-one test, the resource counters.
- For each test that must catch a bug, a note that it failed against a deliberately broken variant (remove the release, replace fork with a blocking wait) and passed on the real one. A test never seen failing has not been shown to test anything.

## 10. Pitfalls

- Fakes that diverge from the real adapter: add a shared contract test.
- Testing the interpreter's call sequence instead of outcomes.
- A law test that mirrors the implementation.
- Tests that pass because the pool is bigger than the number of nested waits; use pool size 1.
- Absence of a timeout in a test that can deadlock, which hangs CI instead of failing.
- Asserting only on the happy path of resource tests.

Related: `effect-descriptions-and-interpreters.md`, `resource-safety.md`, `stack-safety.md`, `craft-testing`.
