# Effect descriptions and interpreters

Contents: 1 Factoring effects outward; 2 A simple effect type; 3 Ports and adapters (interfaces as the interpreter); 4 Choosing between factoring, ports, effect values and free structure; 5 Free structure and interpreters (runnable example, limits of inspection); 6 Natural transformations and many interpreters; 7 Non-blocking interpreters; 8 One entry point; 9 Review checklist.

Sources: FP in Scala ch. 13 (all), ch. 7 (description vs interpretation). Statements marked (adaptation) are not the book's claim.

## 1. Factoring effects outward

Claim (FP in Scala ch. 13.1): inside every function with side effects is a pure function waiting to get out. An impure `A -> B` splits into a pure `A -> D` and an impure `D -> B`, where D is a description of what to do. Apply repeatedly and the effects move to the outermost layer.

Procedure
1. Find the lines that do I/O.
2. Move each decision and computation into a function taking and returning plain values. When the answer is richer than a primitive, return a data value: enum, Option/result, command object.
3. Keep the I/O as a one-liner shell: read inputs, call the core, write outputs.
4. Repeat for the shell until only primitive I/O calls remain.

Book example in three steps: `contest(p1, p2)` computed the winner and printed. Extract `winner(p1, p2) -> Option<Player>` (None means draw), extract `winnerMsg(Option<Player>) -> string`, leave `print(winnerMsg(winner(p1, p2)))`. Extra decisions (display to UI vs file) become pure choices of the description.

Before/after, TypeScript

```ts
// before: decision and effect tangled
function contest(p1: Player, p2: Player): void {
  if (p1.score > p2.score) console.log(`${p1.name} wins`);
  else if (p2.score > p1.score) console.log(`${p2.name} wins`);
  else console.log("draw");
}
// after
const winner = (a: Player, b: Player): Player | null =>
  a.score === b.score ? null : a.score > b.score ? a : b;
const winnerMsg = (w: Player | null) => (w ? `${w.name} wins` : "draw");
const contest = (a: Player, b: Player) => console.log(winnerMsg(winner(a, b))); // shell
```

Smell: a function that returns `void`/`Unit`/`None` purely to perform an effect, located in logic code. It is the sign that a description is missing.

Stop here when the need is only clarity and tests: the core can be tested with plain values and no mocks. See `fp-pure-core` for the full procedure.

## 2. A simple effect type

Version 1 in the book: an IO value with a single `run`. `PrintLine(msg)` is a value; running it prints. The program that returns IO is a pure expression; only `run` has the effect. This alone buys little (it is a delay of the effect, and a monoid under "run one then the other"). The point is that you may invent whatever small language you like for describing interaction with the world.

Add results: `IO<A>` with `run(): A`, `map`, `flatMap` (`f(self.run()).run()`), `unit`. Now input is expressible and the type is a monad, so generic monad combinators apply.

```ts
class IO<A> {
  readonly run: () => A;
  constructor(run: () => A) { this.run = run; }      // lazy: nothing happens at construction
  map<B>(f: (a: A) => B) { return new IO(() => f(this.run())); }
  flatMap<B>(f: (a: A) => IO<B>) { return new IO(() => f(this.run()).run()); }
  static of<A>(a: A) { return new IO(() => a); }
}
const readLine = new IO(() => prompt() ?? "");
const printLine = (s: string) => new IO(() => console.log(s));
const echo = readLine.flatMap(printLine);            // a value; nothing has run
```

Generic combinators that come with the monad (book sidebar): `replicateM(n)(io)`, `forever`, `doWhile`, `foldM`, `foreachM`, `when`, `sequence_`, `skip`. Not every combinator is meaningful for every monad (`forever` on an optional type makes no sense), so check the semantics.

What the simple version gives
- IO values are ordinary values: put them in lists, build them dynamically, wrap a pattern in a function.
- The representation is hidden, so the interpreter can change under unchanged client code.
- The type forces honesty about where the outside world is touched.

What it costs (the book's list)
1. Stack overflow in long or looping programs, because `flatMap` nests `run` calls. See `stack-safety.md`.
2. Opaque: an `IO<A>` is a thunk. You can only compose or run it; you cannot inspect which operations it will perform.
3. Says nothing about concurrency, async or non-blocking I/O.
4. Programming inside it has the same difficulties as ordinary imperative programming; efficient code tends to be monolithic loops. See `stream-pipelines.md` for the answer.

The book does not recommend writing whole programs this way. Wrapping a monolithic impure block in IO is acceptable when it is cheaper than redesigning (the book notes this for efficiency and syntax).

Eager vs lazy warning (adaptation, and the book's cross-language note): an already-started computation is not a description. JavaScript promises and Java `CompletableFuture` start on creation; wrap them in a thunk or a lazy task type. Rust futures and Python coroutines do nothing until polled or awaited. Kotlin `suspend` functions are lazy; `async {}` in a live scope is eager.

## 3. Ports and adapters (interfaces as the interpreter)

(adaptation, following the book's cross-language note) You can get the main benefit of an interpreter, swapping the real world for a test world, without any monad: define an interface of the operations a component needs, pass it in, and choose the implementation at the entry point.

```python
class Console(Protocol):
    def read_line(self) -> str | None: ...
    def print_line(self, s: str) -> None: ...

def converter(c: Console) -> None:
    line = c.read_line()
    if line is not None:
        c.print_line(f"{(float(line) - 32) * 5 / 9:.1f}")

class FakeConsole:                      # scripted input, captured output, no mocking framework
    def __init__(self, inputs): self.inputs, self.out = list(inputs), []
    def read_line(self): return self.inputs.pop(0) if self.inputs else None
    def print_line(self, s): self.out.append(s)
```

Choose ports when: the set of effects is small and stable, testability is the reason, and the language has interfaces. Fakes replace mocks: they have behaviour, so tests assert on outcomes rather than call sequences. This is the lightweight form of the book's "restrict the instruction set, vary the interpreter".

Limits: the program is executed directly, so you cannot inspect, serialise, optimise or run it twice differently from one description; effects happen as the code runs; stack depth is the host's. If you need those, see sections 2 and 5.

## 4. Choosing between factoring, ports, effect values and free structure

Rules from the book's summary of this chapter, plus adaptation.

| Need | Smallest tool |
|---|---|
| Clarity and unit-testable logic | Factoring (section 1) |
| Test without the real world, small stable set of effects | Ports and adapters with a fake (section 3) |
| Compose effects as values: store, retry, run in parallel, schedule | Effect value (section 2) |
| Swap interpreters of the same program (test, production, async, dry-run, recording) | Ports (interface) or free structure (section 5) |
| Restrict a component to a declared set of operations | Port interface exposing only those operations, or free structure over that instruction type |
| Inspect, optimise, serialise or log the program before it runs | Free structure (data) |
| Long monadic loops without stack overflow | Trampolined effect type (`stack-safety.md`) |

Free structure is worth it when: the effect domain is small and stable (a handful of operations); you want several interpreters (real, in-memory test, recording, dry-run, async); you want to inspect, optimise or serialise the program; you want to forbid other effects statically.
It is not worth it for: one-off scripts; performance-critical inner loops (interpretation overhead and continuation allocation); teams or languages lacking sum types or conventions to keep the boilerplate bearable.

Stated cost (the book's concern, with the inferred extras): indirection, learning curve, harder stack traces.

## 5. Free structure and interpreters

Idea: make the operations data, make the program a tree of those operations, and give the meaning in a separate interpreter. Programs become referentially transparent expressions that make requests of an interpreter; the program neither knows nor cares whether the requests perform side effects.

Shape (language-neutral): a program is one of
- `Return(value)`: finished.
- `Suspend(instruction)`: one instruction from the effect family F, whose answer is the program's next value.
- `FlatMap(sub, k)`: run `sub`, then continue with `k(result)`.

`Free[F, A]` is a monad for any F, even one without monad structure; "free" means generated without requiring more. Equivalent readings (book): a recursive structure with an A wrapped in zero or more layers of F; a tree with A at the leaves; an abstract syntax tree of a program in a language whose instructions are F, with free variables in A. The program and its interpreter behave as coroutines; F defines the protocol between them. Choose F to control exactly which interactions are allowed.

Instances in the book: `TailRec[A] = Free[Function0, A]` (trampolined sequential computation); `Async[A] = Free[Par, A]` (trampolined plus non-blocking).

### 5.1 An instruction set (the algebra)

```ts
type Console<A> =
  | { tag: "ReadLine"; _?: A }          // answers string | null
  | { tag: "PrintLine"; line: string };  // answers void
```

(TypeScript cannot index the answer type by tag without GADT tricks; the common workaround is a discriminated union plus a cast in the interpreter, or an interface with one method per instruction. This is the HKT/GADT degradation described in `language-mappings.md`.)

Rule of thumb for the instruction set (adaptation from the book's file system/network/DB mentions): one algebra per family of external operations (console, files, DB, network, clock). Programs declare which family they use. A read-only file algebra is a different type from a read-write one, which gives you the static restriction.

Caveat (book footnote 12): most host languages cannot enforce that a program of type `Free[Console, A]` does nothing else. The restriction is discipline plus review.

### 5.2 Interpreter targets (book 13.4)

All of these run the same program:
- Real blocking effects (Console to a thunk).
- Async (Console to a parallel/async value).
- Reader: fixed input, pure.
- State over a pair of buffers (`in`, `out`): ReadLine pops the input list, PrintLine pushes onto output. A pure simulation. Use this in tests with scripted input and captured output; combine with property tests for random scripts.

This is the book's answer to testing I/O code without mocks.

A runnable TypeScript version of the whole shape (adaptation: the book's code is Scala with `Free[F, A]` and `F ~> G`; here the instruction set is a union and an interpreter is a `step` function plus one shared driver). It was run under Deno and Node 22 (`echo 212 | node --experimental-strip-types file.ts`): the fake run asserts the output, a million-step program completes, and the real run prints `100.0`.

```ts
type Op = { tag: "ReadLine" } | { tag: "PrintLine"; line: string };
type Prog<A> =
  | { t: "ret"; a: A }
  | { t: "sus"; op: Op }                                  // one instruction; its answer is the value
  | { t: "bind"; sub: Prog<any>; k: (x: any) => Prog<A> };

const ret = <A>(a: A): Prog<A> => ({ t: "ret", a });
const bind = <A, B>(m: Prog<A>, k: (a: A) => Prog<B>): Prog<B> => ({ t: "bind", sub: m, k });
const readLine: Prog<string | null> = { t: "sus", op: { tag: "ReadLine" } };
const printLine = (line: string): Prog<void> => ({ t: "sus", op: { tag: "PrintLine", line } });

// One generic driver (reassociates left-nested binds, constant stack) + one `step` per target.
function interpret<A>(p: Prog<A>, step: (op: Op) => unknown): A {
  for (;;) {
    if (p.t === "ret") return p.a;
    if (p.t === "sus") return step(p.op) as A;
    const { sub, k } = p;
    if (sub.t === "ret") p = k(sub.a);
    else if (sub.t === "sus") p = k(step(sub.op));
    else p = bind(sub.sub, (x) => bind(sub.k(x), k));
  }
}

// A program is a value; nothing has run.
const converter: Prog<void> = bind(readLine, (l) =>
  l === null ? ret(undefined) : printLine(((Number(l) - 32) * 5 / 9).toFixed(1)));
const echo = (n: number): Prog<void> =>
  n === 0 ? ret(undefined)
          : bind(readLine, (l: string | null) => bind(printLine(l ?? ""), () => echo(n - 1)));

// Real interpreter (Node or Deno): stdin and stdout.
import { readFileSync } from "node:fs";
function realStep(): (op: Op) => unknown {
  const lines = readFileSync(0, "utf8").split("\n");
  let i = 0;
  return (op) => op.tag === "ReadLine" ? (i < lines.length ? lines[i++] : null) : void console.log(op.line);
}
// Fake interpreter: scripted input, captured output, no I/O.
function fake(inputs: string[]) {
  let i = 0;
  const out: string[] = [];
  const step = (op: Op): unknown => op.tag === "ReadLine" ? (inputs[i++] ?? null) : void out.push(op.line);
  return { step, out };
}

const f = fake(["212"]);
interpret(converter, f.step);
console.assert(f.out.join() === "100.0");               // same program, test world
const g = fake(Array.from({ length: 1_000_000 }, (_, i) => String(i)));
interpret(echo(1_000_000), g.step);                      // a million steps, constant stack
console.assert(g.out.length === 1_000_000);
interpret(converter, realStep());                        // same program, real world: echo 212 | node ...
```

Two things the sketch shows. The program `converter` is built once and run under two interpreters without change. The driver reassociates left-nested binds exactly like the trampoline in `stack-safety.md`, which is why `echo(1_000_000)` does not overflow; replace `interpret` with a plainly recursive one (`const x = interpret(p.sub, step); return interpret(p.k(x), step);`) and the million-step run fails with a stack overflow (checked).

### 5.2a What "inspect" can and cannot mean (adaptation)

Each `bind` holds a continuation `k`, which is an opaque function. You cannot walk the program tree and list the instructions it will issue, because later instructions depend on answers not yet known. What you can do is run it under a recording or dry-run interpreter (log each instruction, answer from a script, or answer with a default) and read the trace. To get a program whose instructions can be listed up front, give up dependence on earlier answers: independent steps expressed as a list or tree of instructions are statically visible (the applicative form; see `fp-data-and-errors`). State which kind of inspection the design needs before choosing free structure for it.

### 5.3 The stack-safety trap in interpreters (book Exercise 13.4)

A naive interpreter that targets a monad whose `flatMap` is not stack-safe is itself not stack-safe, even if the program is trampolined. Fix: translate the program into another `Free` over a stack-safe target and run that, or represent the target as `Input -> TailRec[...]`. Test with a million-step program on every interpreter, not just the real one.

## 6. Natural transformations and many interpreters

An interpreter from instruction family F into target monad G is a function that works for every answer type A: `F[A] -> G[A]` (a natural transformation, written `F ~> G`). The generic runner takes a program `Free[F, A]` and a `F ~> G` and produces `G[A]`; `Return` becomes G's unit, `Suspend(i)` becomes `translate(i)`, and `FlatMap(Suspend(i), k)` becomes `G.flatMap(translate(i))(a => run(k(a)))` after a reassociation step.

Practical reading (adaptation): in a language without higher-kinded types, an interpreter is a switch over the instruction tag that returns the answer, plus a driver loop that feeds answers back into the continuation. The natural-transformation typing is lost, but the structure is the same: one `interpret(instruction) -> answer` function per target, one generic driver.

## 7. Non-blocking interpreters

Same program, different interpreter: compile Console instructions to async actions instead of blocking calls (book: "a kind of compilation"). Callback-based real APIs (`readBytes(n, cb)` returning immediately) fit the same shape as the async value's internal continuation. Add one primitive that wraps a callback-registering function into the async type; the book says it may be the most primitive operation of the async type, with others derived.

```ts
const asyncOf = <A>(register: (k: (a: A) => void) => void): Task<A> =>
  () => new Promise<A>(res => register(res));   // thunk: nothing registered until run
```

Include an error channel: the callback should take a result (value or error) so a failing read reaches the consumer. The book's version lacked this; the latch was never released on exception.

Pattern: wrap each callback API once into the async type, then program against the monadic interface; this avoids callback nesting. See `parallelism-as-description.md` for the full non-blocking discussion and its pitfalls.

## 8. One entry point

Methodology (book 13.6): for each family of external operations write an algebra; write programs against the algebra; test with pure interpreters; finally compile each algebra into one lowest-level effect type (sequential plus async). `main` is the only impure function: it calls the interpreter once on `pureMain(args)`. Name the runner so impurity is visible (the book uses `unsafePerformIO`). The program has effects but not side effects, because nothing inside it can observe their performance.

Practical rule (inferred): exactly one call site runs the top-level description; all other code builds descriptions or takes a port.

## 9. Review checklist

- Does any print, DB call, clock, random, fetch or file call appear outside the shell, the adapters, or the single run site?
- Does any "pure" function return Unit/void/None (an effect in disguise)?
- Is the interpreter or adapter chosen only at the entry point?
- Is every description lazy: does constructing it start nothing?
- Is every `run`/`await`/`block_on` at the edge, never in the middle of a combinator?
- If free structure is used: is the instruction set small and stable, and is there more than one interpreter in use (including a test one)? If there is only one interpreter, justify the data layer or remove it.
- Are all interpreters stack-safe (million-step test)?
- If the program is a stream (large data, early exit), is it a pipeline rather than a monolithic loop inside the effect type? See `stream-pipelines.md`.

Related: `stack-safety.md` (trampolines), `parallelism-as-description.md` (async), `testing-effectful-code.md` (fakes and pure interpreters), `language-mappings.md`.
