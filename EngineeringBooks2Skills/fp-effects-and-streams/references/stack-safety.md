# Stack safety and trampolining

Contents: 1 Why monadic loops overflow; 2 Choosing a fix; 3 The trampoline in language-neutral form; 4 Reassociation; 5 General use beyond I/O; 6 Costs; 7 Procedure to trampoline a function; 8 Verify; 9 Pitfalls.

Sources: FP in Scala ch. 13.2-13.4 (stack overflow, trampolining, TailRec, interpreter pitfalls). Items marked (adaptation) are not the book's claims.

## 1. Why monadic loops overflow

In the simple effect type, `flatMap` builds a value whose `run` calls `f(self.run()).run()`. Each bind nests another `run` call on the stack. A `forever(printLine(...))` or a recursive REPL overflows after a few thousand iterations. The same happens when you compose a hundred thousand functions with ordinary composition, which is why the technique is not about I/O.

Hosts without guaranteed tail calls (JVM, JS, Python, C#, Rust, Go with caveats) are exposed. Languages with tail-call elimination need less of this (Scheme, Haskell; Scala for self-recursive functions with the annotation). Go has growable stacks, so deep recursion is rarely fatal but still bounded by memory (book cross-language note, inferred).

## 2. Choosing a fix

| Situation | Fix | Why |
|---|---|---|
| Self-recursive function whose recursive call is in tail position | Accumulator loop (or the language's tail-call mechanism if guaranteed) | Cheapest, no allocation |
| Structural recursion over data you control (tree, list) with bounded depth | Leave it; bound the depth in a test | A trampoline would cost more than the risk |
| Recursion where depth follows input size and can be millions | Explicit stack/queue loop (work list) | Same effect, clearer in languages without sum types (inferred) |
| Mutual recursion, recursion via composed functions, state machines expressed as chained binds | Trampoline | The call is not a self tail call, so no loop rewrite applies |
| Monadic/effect loops (`forever`, repeat-until, long `flatMap` chains) | Trampolined effect type (Free over a thunk, or a library type that is stack-safe) | The loop is built from binds; the interpreter must run them iteratively |
| Interpreting a free structure | Reassociating interpreter loop | See section 4 |

If your ecosystem's effect library already documents stack-safe binds, use it and verify with the test in section 8 instead of writing your own.

## 3. The trampoline in language-neutral form

Reify control flow as data, then run it in a loop. Three constructors:
- `Return(a)`: finished with value a.
- `Suspend(resume)`: a pending step that produces a value when called (a thunk).
- `FlatMap(sub, k)`: run `sub`, then continue with `k`.

`flatMap(f)` is just `FlatMap(this, f)`; `map(f)` is `flatMap(a => Return(f(a)))`.

Interpreter (a loop in tail position):
- `Return(a)`: result is a.
- `Suspend(r)`: result is `r()`.
- `FlatMap(x, f)` where x is `Return(a)`: continue with `f(a)`.
- ... where x is `Suspend(r)`: continue with `f(r())`.
- ... where x is `FlatMap(y, g)`: continue with `y.flatMap(a => g(a).flatMap(f))` (reassociate, section 4).

The program yields requests and the runner drives them, like cooperating coroutines. The book calls the runner a trampoline.

```ts
type Tramp<A> =
  | { t: "ret"; a: A }
  | { t: "sus"; r: () => A }
  | { t: "bind"; sub: Tramp<any>; k: (x: any) => Tramp<A> };

function run<A>(p: Tramp<A>): A {
  for (;;) {
    if (p.t === "ret") return p.a;
    if (p.t === "sus") return p.r();
    const { sub, k } = p;
    if (sub.t === "ret") p = k(sub.a);
    else if (sub.t === "sus") p = k(sub.r());
    else p = { t: "bind", sub: sub.sub, k: (x) => ({ t: "bind", sub: sub.k(x), k }) };
  }
}
```

Constructors and a check (run under Deno and Node 22; with `node --stack-size=100`, a stack far smaller than the default, all four cases still complete, while the naive `IO` class of `effect-descriptions-and-interpreters.md` section 2 overflows):

```ts
const ret = <A>(a: A): Tramp<A> => ({ t: "ret", a });
const sus = <A>(r: () => A): Tramp<A> => ({ t: "sus", r });
const bind = <A, B>(m: Tramp<A>, k: (a: A) => Tramp<B>): Tramp<B> => ({ t: "bind", sub: m, k });

// 1. right-nested loop: each step binds the next iteration
const loop = (n: number, acc: number): Tramp<number> =>
  n === 0 ? ret(acc) : bind(sus(() => acc + 1), (x) => loop(n - 1, x));
console.assert(run(loop(1_000_000, 0)) === 1_000_000);

// 2. left-nested chain ((m >>= f) >>= f) ... : exercises the reassociation branch
let m: Tramp<number> = ret(0);
for (let i = 0; i < 1_000_000; i++) m = bind(m, (x) => ret(x + 1));
console.assert(run(m) === 1_000_000);

// 3. mutual recursion through binds
const isEven = (n: number): Tramp<boolean> => n === 0 ? ret(true) : bind(ret(null), () => isOdd(n - 1));
const isOdd = (n: number): Tramp<boolean> => n === 0 ? ret(false) : bind(ret(null), () => isEven(n - 1));
console.assert(run(isEven(1_000_000)) === true);
```

Note that a `Suspend` thunk in this sketch returns a plain value (`() => A`), not another `Tramp`; the loop in `run` is what continues the computation. If you want a thunk that returns the next step (the "More(thunk)" form some libraries use), add a fourth case that sets `p = p.r()`.

A Python version uses the same three tags with a `while True` loop; a Rust version uses an enum and a `loop` (adaptation).

## 4. Reassociation

Left-nested binds `((a >>= f) >>= g) >>= h` are what a naive left fold of continuations builds. The interpreter rewrites `FlatMap(FlatMap(y, g), f)` into `FlatMap(y, a => FlatMap(g(a), f))`. Repeating this turns the tree into a right-nested chain `FlatMap(a1, a1 => FlatMap(a2, ...))` whose evaluation needs constant stack. The rewrite is valid because of the monad associativity law. If your own bind violates associativity (for example by doing work eagerly), the reassociating loop changes results; test the law (section 8).

## 5. General use beyond I/O

Book example: compose 100,000 `Int -> Int` functions with ordinary composition and it overflows. Make each function return `Return(x)` (or `Suspend` before the call), compose with Kleisli composition through `flatMap`, then run. The resulting type is a monad for tail-call elimination; the book renamed it `TailRec[A]` (= Free over a thunk).

## 6. Costs

- Slower than direct calls for ordinary code (allocation of nodes and closures per step). The book's footnote adds that for calls that would otherwise build deep stacks it can win, and describes an alternative that uses exceptions to return to the loop only periodically.
- Gives predictable stack use, which is the reason to pay.
- Stack traces show the interpreter, not your logical call chain; debugging is harder (inferred).
- Do not put a trampoline in a hot inner loop whose depth is small. Measure before and after.

## 7. Procedure to trampoline a function

1. Change the return type `B` to `Tramp<B>`.
2. Replace each recursive call in tail position by `Suspend(() => f(x))`, or `f(x)` wrapped so it returns a node rather than recursing.
3. Replace `g(f(x))` with `f(x).flatMap(g)`.
4. Run the result with `run` at the single place that needs the value.
5. If only a self tail call exists, prefer an accumulator loop instead (inferred; cheaper).

Per-language equivalents of the idea (book note, inferred): Kotlin `DeepRecursiveFunction`; JavaScript hand-written thunk trampolines; Rust loops over an enum, or crates that grow the stack on demand; Python generators or an explicit work stack.

## 8. Verify

- Million-step test: build the looping program with N = 1e6 (bounded by a condition, not `forever`) and run it on the real interpreter. Also on every other interpreter; the book's own Function0 interpreter was not stack-safe even though the program type was.
- Make failure fast: run the test with a deliberately small stack so a regression fails in milliseconds (adaptation). Concrete forms: `node --stack-size=100 script.js` (kilobytes; lowering it is safe, raising it past the OS limit can crash), `deno run --v8-flags=--stack-size=100 script.ts`, Python `sys.setrecursionlimit(200)` before the run, a Rust or Java thread created with a small stack size.
- Law checks on the bind: `run(unit(a).flatMap(f)) == run(f(a))`; `run(m.flatMap(unit)) == run(m)`; associativity by running both groupings on sample programs (including the left-nested shape that exercises reassociation).
- Property: for random small programs, the trampolined result equals the naive recursive result.

## 9. Pitfalls

- Trampolining the program but running it with a naive interpreter (see `effect-descriptions-and-interpreters.md` section 5.3).
- Forgetting that a thunk executes arbitrary code: exceptions inside `Suspend` must be caught and routed to the error channel if your type has one.
- A trampoline stops the stack but not memory growth: a loop that holds a reference to every previous result (memoised stream, accumulating list) still exhausts the heap. For large data use a stream pipeline (`stream-pipelines.md`).
- Mixing in non-bound recursion: one direct recursive call inside a `Suspend` body reintroduces stack growth.

Related: `effect-descriptions-and-interpreters.md`, `language-mappings.md`.
