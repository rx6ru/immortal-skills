# The 23 patterns in function, closure, generic and sum-type form

Read this file when the language you are writing in has first-class functions, closures, generics or
traits, or sum types with pattern matching (TypeScript, Python, Rust, Kotlin, Swift, Go, C#, modern
Java and the ML family), and you are about to write a pattern as an interface plus a class per variant.
For most of the 23 a smaller form exists. The decision criteria that choose the pattern are unchanged;
only the scaffolding changes.

Provenance: the books (GoF 1994, Head First 2e) describe the class forms, with some notes on lambdas
and language features (HF ch. 2, 6, 7, 8, 9, 11; GoF's own remarks on templates, closures and
multimethods). The function and sum-type forms below are mostly adaptation by the note-takers and this
skill, not claims of the books; they are labelled "(adaptation)" where they go beyond the notes. Every
other pattern's full entry is in `structural.md`, `behavioral-1.md`, `behavioral-2.md` and the
creational reference files of this skill.

## Contents

1. The general rule: when the smaller form is enough and when the class form stays
2. Summary table of all 23
3. Creational: Abstract Factory, Builder, Factory Method, Prototype, Singleton
4. Structural: Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy
5. Behavioural: Chain of Responsibility, Command, Interpreter, Iterator, Mediator, Memento, Observer,
   State, Strategy, Template Method, Visitor
6. Four substitutions that recur
7. Checks before replacing a class form with a smaller one, or the other way round

---

## 1. The general rule

Keep the pattern's vocabulary and its decision criteria; drop the class scaffolding when a function,
closure, generic parameter or enum states the same thing more directly (the note-takers' modern lens
on GoF ch. 5; applied here to all 23).

A function-shaped form is enough when all of the following hold:
- the variation is one operation (one method's worth of behaviour);
- it needs no per-variant state beyond what a closure can capture;
- nobody needs to name, register, list, serialise, compare or inspect the variants individually;
- there is no second operation that must stay consistent with the first (undo with do, close with
  open, reverse with forward).

The class (or interface plus classes) form is still right when any of these hold:
- the variant has several operations or its own configuration and lifecycle;
- variants must be discoverable, named, registered or chosen from configuration (the open set: plugins);
- you need identity or inspection (history lists, debuggers, logs that print "which handler");
- the base class must enforce an invariant around the variable step (Template Method with a final
  template);
- other developers will extend it by subclassing in a framework you ship;
- the type system's checks (a closed set of variants, exhaustive matching) are what you want, in
  which case a sum type is the smaller form, not a function.

Two guardrails from the notes. First, a pattern name is shared vocabulary (HF ch. 1): a wrapper
function that retries is still "a Decorator" in a design discussion, and naming it so costs nothing.
Second, the book's warning against pattern fever and against applying open-closed everywhere (HF
ch. 1, ch. 3) applies in both directions: do not build a class hierarchy for a one-line callback, and
do not replace a ten-method strategy with a bag of loose lambdas.

---

## 2. Summary table of all 23

| Pattern | Smaller form (adaptation) | Class form stays right when |
|---|---|---|
| Abstract Factory | record or struct of constructor functions; DI binding | many product kinds that must stay in one family, with the factory as a unit that is swapped, tested and named |
| Builder | named/default parameters, copy-with, options struct; or a handler/callback object in a parser | a genuine director plus builders (one construction algorithm, several representations) |
| Factory Method | pass a constructor function or class reference; static factory function | a framework template method calls the hook and users already subclass the creator |
| Prototype | spread/copy-with of an immutable value; registry of presets | cloning mutable object graphs with identity, cycles or resources |
| Singleton | module-level value, language `object`, DI container singleton scope | a true correctness invariant of one instance (rare), behind an abstraction |
| Adapter | lambda, extension method, trait impl for a foreign type; or nothing under structural typing | several operations to translate, or state kept in the adapter |
| Bridge | interface or function-typed field injected through the constructor; generic parameter | two real hierarchies that both grow |
| Composite | recursive sum type plus a fold | open set of node types added by plugins; node types with substantial behaviour of their own |
| Decorator | higher-order function from function to function; middleware | wrapping a multi-method interface with state per wrapper |
| Facade | module with a narrow export list | n/a: already usually a module or function; a class when it holds the subsystem instances |
| Flyweight | interning, immutable shared values, ids into arrays | a pool with lifecycle management and a typed key |
| Proxy | lazy value (memoised thunk), generated client stub, dynamic proxy | access control with state or policy; remote proxies with a contract |
| Chain of Responsibility | list of functions plus a first-match search; middleware list | handlers with configuration and their own tests that must be assembled dynamically |
| Command | closure; data-only record plus handler table; sum type of commands | undo, serialisation, queuing across processes, inspection |
| Interpreter | sum type plus recursive evaluation function; parser combinators | no: the sum type is the modern class form; use a grammar tool for large grammars |
| Iterator | built-in iterator protocol, generator, lazy stream | custom resource-owning iteration with explicit close |
| Mediator | controller function or state store with a reducer | many colleagues with real behaviour; a workflow engine |
| Memento | immutable value kept by the caller; persistent data structure | opaque, versioned snapshots of encapsulated mutable state |
| Observer | subscribe(fn) returning an unsubscribe handle; event stream; signals | need for aspects, ordering, batching or a change manager |
| State | sum type plus transition function; type-state; table or machine library | many states with substantial per-state behaviour |
| Strategy | function parameter; generic or trait bound | several operations, own config or state, or a named registry |
| Template Method | higher-order function taking the steps; trait with default methods | framework base class that enforces a lifecycle |
| Visitor | exhaustive match over a sum type; multimethod | stable object-oriented hierarchy that you cannot turn into a sum type, and many passes |

---

## 3. Creational

### Abstract Factory (GoF Abstract Factory)
**Intent kept.** Create families of related objects without naming concrete classes, and keep a family
consistent (GoF).
**Smaller form (adaptation).** A factory is an interface or a plain record of constructor functions:
pass `{ makeButton, makeScrollBar }` or a dependency-injection binding. A registry map from string to
factory replaces the if-else chain. Class references (Python classes, JS constructors, Kotlin and Swift
types) are the "class-based factory" GoF describes for Smalltalk, where a new factory is a
configuration of classes rather than a subclass.
```ts
type UiKit = { button(label: string): Button; scrollBar(): ScrollBar };
const kits: Record<string, UiKit> = { motif: motifKit, pm: pmKit };
function buildDialog(kit: UiKit) { const b = kit.button("OK"); /* never names a concrete class */ }
```
**Class form stays right when** several product kinds must be swapped together as a unit, the factory
needs its own tests or name in configuration, or product kinds are added rarely and you want the
compiler to force every family to supply them (the book's liability: a new product kind edits the
interface and every factory).
**One-product case.** If there is only one product kind, a plain factory function is enough (inferred
from the GoF applicability list, which is about families of related products; the book does not
state this as a rule).
**Check.** Concrete product class names appear only inside the factory definitions; swapping the
factory changes every product at once.

### Builder (GoF Builder)
**Two things share the name (note-takers' observation).** GoF's Director plus Builder gives double reuse:
one construction algorithm, many representations. The popular fluent "builder" for assembling an
immutable object with many optional fields is a different and much smaller idea.
**Smaller form for the second (adaptation).** Named and default parameters, struct literals with
spread, copy-with (`data class copy`), or an options struct replace it in most modern languages.
**Form that survives for the first.** SAX-style parsers calling a handler object with
`startElement/endElement`, tree builders, query builders, DOM builders; a callback object or a set of
closures can stand in for the builder interface.
```ts
interface HtmlBuilder { heading(t: string): void; para(t: string): void }
function parse(src: string, b: HtmlBuilder) { for (const tok of lex(src)) tok.kind === "h" ? b.heading(tok.text) : b.para(tok.text) }
```
**Class form stays right when** one parse or construction algorithm must drive several output
representations (including a builder that builds nothing but counts).
**Check.** A new output representation requires no edit to the director; incomplete construction
sequences are detected at the final retrieval step.

### Factory Method (GoF Factory Method)
**Smaller form (adaptation).** Pass a factory function or class reference into the constructor
(dependency-injection style), removing the need to subclass: `create: () => Product`. First-class
constructors (Python, JS, Kotlin class references, Swift metatypes) and constrained generics
(`T: Product + Default`) replace the `StandardCreator<T>` template GoF uses in C++.
**A different idiom with the same name.** "Static factory methods" and named constructors
(`Foo.fromJson(...)`) are much more common and involve no subclass choice; do not confuse them.
**Class form stays right when** an inheritance-based framework calls the hook from its own template
(document creation inside open, `get_queryset`-style hooks, test-fixture setup). Do not call the
factory method from the base constructor: the subclass override is not ready yet (GoF); use lazy
creation through an accessor.
**Check.** A test subclass, or a test function passed in, injects a fake product without editing base
code.

### Prototype (GoF Prototype)
**Smaller form (adaptation).** With immutable values the pattern largely vanishes: a "prototype" is a
value you derive new values from (`{...preset, name}`, Kotlin `copy()`). Registries of presets (map from
name to config object) cover the palette and catalogue use cases. JavaScript is prototype-based
(`Object.create`, `structuredClone`); Python has `copy.deepcopy`; Rust `Clone` is explicit. Java
`clone()` is widely considered flawed, so prefer copy constructors or factories.
```ts
class Note { constructor(readonly o: { duration: number }) {} clone() { return new Note({ ...this.o }); } }
const presets = new Map<string, Note>([["whole", new Note({ duration: 4 })]]);
const make = (k: string) => presets.get(k)!.clone();      // same dynamic type, independent copy
```
`structuredClone` copies plain data only: applied to a class instance it returns a plain object without
the class's methods or prototype, so use it for config records and a `clone()` method for typed objects
(checked by running both).
**Class form stays right when** you copy mutable object graphs and must decide what is shared, or when
a type hierarchy needs clone-returns-same-dynamic-type behaviour. GoF's own warning stands: deep versus
shallow, cycles and resource-holding objects.
**Check.** Mutate the clone and assert the original is unchanged; the clone has the same dynamic type;
cycles and internal sharing in the graph are preserved as intended.

### Singleton (GoF Singleton)
**Smaller form (adaptation).** A module-level value gives "one instance with a well-known access
point" in JS, Python and Go package variables; Kotlin and Scala `object`; dependency-injection
containers register services with singleton lifetime without the class knowing. Language-level lazy
statics solve thread-safe lazy initialisation (a function-local static in C++11, `OnceLock`/`LazyLock`
in Rust, `static let` in Swift).
**Bias to keep.** The book lists only advantages; the notes add, as adaptation, that the pattern is
widely regarded as hidden global state: hidden dependencies, hard to test, initialisation-order and
thread-safety hazards, and it ties a uniqueness policy to a class's behaviour. Most cases are "one is
enough", a composition decision: create one object at startup and pass it in. A true "only one may
ever exist" invariant is rare.
```ts
const config = load(); const app = new App(config, new Db(config));   // one object, injected
```
**Class form stays right when** the resource is truly process-wide with one correct instance (a logger
sink, a hardware handle), and then keep it behind an interface so tests can substitute.
**Check.** Tests can build isolated instances or reset it; initialisation is thread-safe; nothing
depends on initialisation order.

---

## 4. Structural

### Adapter (GoF Adapter; HF ch. 7)
**Smaller forms (adaptation).** With structural typing (TypeScript, Go interfaces) a type with the right
shape needs no adapter; adapt only where shapes differ. Extension methods and traits (Kotlin
extensions, Rust `impl Trait for ForeignType` within orphan rules, Swift extensions) add the missing
interface without a wrapper. A lambda is the "parameterised adapter" of GoF (`getChildren: n =>
n.subdirs()`). At service boundaries the idea is an anti-corruption layer or port and adapter.
```ts
const tree = new TreeDisplay<Dir>({ children: d => d.subdirs(), label: d => d.name });  // parameterised adapter
```
**Class form stays right when** there are several operations to translate, semantic compensation to
perform (HF's repeat-five-times flight), or state to keep.
**Check.** No adaptee type leaks beyond the adapter; Target contract tests pass; gaps fail loudly.

### Bridge (GoF Bridge)
**Smaller forms (adaptation).** "Accept an interface in the constructor": ordinary injection of a
driver or backend (database drivers, renderers, loggers, storage backends). A function-typed field
suffices when the implementor has one primitive. Generics or traits give a compile-time bridge (Rust
`struct Shape<R: Renderer>`); interface-typed fields give a run-time one. The Cheshire-cat idiom is
opaque types or module-private structs.
**Class form stays right when** both hierarchies really have several members and keep growing (N+M
rather than N x M).
**Check.** Add an implementor without touching the abstraction, and the reverse.

### Composite (GoF Composite; HF ch. 9)
**Sum-type form (adaptation).** `enum Node { Leaf(..), Group(Vec<Node>) }` with recursive functions and
exhaustive match; no Component interface needed. "A leaf cannot have children" is enforced by the type,
which resolves the safety-versus-transparency dilemma in favour of safety. Aggregation is a fold over
the children (`reduce`) rather than an explicit iterator. In class-based languages, generics can
restrict child types (`Composite<T extends Component>`).
```rust
enum Item { Disk, Group(Vec<Item>) }
fn price(i: &Item) -> u32 { match i { Item::Disk => 40, Item::Group(c) => c.iter().map(price).sum() } }
```
**Class form stays right when** the set of node kinds is open (plugins) or each node kind carries
substantial behaviour of its own. File systems, the DOM, ASTs, widget trees, org charts and permission
sets are everyday composites in either form.
**Check.** Operation on the root equals the aggregate over leaves; an empty group has the identity
value; nesting depth three.

### Decorator (GoF Decorator; HF ch. 3)
**Function form (adaptation).** A decorator is a higher-order function from a function to a function of
the same signature: Python `@decorator` (with `functools.wraps` to keep metadata), JS/TS higher-order
functions, Express/Koa/ASGI/tower middleware, Go `http.Handler` wrappers, `compose(logging, retry,
timeout)(handler)`. Language "decorator" and annotation syntax is sugar for this wrapping.
```ts
const withRetry = <A, R>(n: number, f: (a: A) => R) => (a: A): R => { for (let i = 0;; i++) try { return f(a) } catch (e) { if (i >= n - 1) throw e } };
```
Delegation features (Kotlin `by`, Go and TypeScript embedding) cut the forwarding boilerplate when
wrapping a multi-method interface.
**Same traps as the class form.** Wrapping order matters; identity and type tests on the wrapped
object break; long wrapper chains make stack traces hard to read.
**Class form stays right when** the wrapped interface has many methods and each wrapper has state.
**Check.** Contract tests pass for wrapped and bare; one test pins the order that matters.

### Facade (GoF Facade; HF ch. 7)
**Form (adaptation).** Usually a module or package whose exports are the narrow API
(`compiler.compile()`), with the rest internal via package or module visibility. Service-layer classes,
SDK client wrappers, API gateways and backend-for-frontend services are facades at larger scale.
**Class form** when the facade must hold the subsystem instances and be configured with different ones.
**Check.** Import rules show clients only import the facade; no cycle back.

### Flyweight (GoF Flyweight; HF appendix)
**Forms (adaptation).** Interning: string interning, small-integer caches, symbols and atoms,
enum-like constants, the Go `unique` package, colour and font tables, texture atlases, shared immutable
configuration objects. Structure-of-arrays or columnar layouts achieve the same goal by storing
extrinsic data in arrays indexed by an id.
**Requirements that matter more today.** Flyweights must be immutable or thread-safe because they are
shared; the pool must be thread-safe and may need weak references to avoid leaks; small value types
often beat objects, so measure first.
**Class form stays right when** the pool has a lifecycle and a typed key that clients must go through.
**Check.** Heap profile before and after; same key gives the same instance.

### Proxy (GoF Proxy; HF ch. 11)
**Forms (adaptation).** Dynamic proxies (Java reflective proxies, JS `Proxy`, Python `__getattr__`
delegation, C# `DispatchProxy`), generated RPC stubs (gRPC and OpenAPI clients are remote proxies), ORM
lazy loading (virtual proxy), lazy values and memoised thunks (`Lazy<T>`, `once_cell`) as the
first-class-function form of a virtual proxy, `Rc`/`Arc` plus copy-on-write types and persistent data
structures for copy-on-write, sidecars and gateways as protection and remote proxies at system scale.
```python
class Lazy:
    def __init__(s, make): s._make, s._v = make, None
    def get(s):
        if s._v is None: s._v = s._make()   # a factory that may return None would need a separate flag
        return s._v
```
**Cautions the notes carry over.** Identity and equality surprises, hidden latency and failure (make
remote failure part of the interface), errors deferred to first use, and thread-safety of lazy
initialisation (`sync.Once`, double-checked locking done right).
**Class form stays right when** the proxy implements an access policy with state, or a remote contract
that you want explicit.
**Check.** Same contract tests as the real subject; lazy subject created once and not before use.

---

## 5. Behavioural

### Chain of Responsibility (GoF Chain; HF appendix)
**Form (adaptation).** A list of functions of the form request to optional result with a
`find_map`-style first-match search; in Rust or Haskell a fold over `Option` or `Either`. Middleware
pipelines (Express/Koa, ASP.NET Core, servlet filters, Go handler chains, gRPC interceptors), DOM event
bubbling, exception handler chains and approval workflows are all this.
**Distinguish two variants.** If the first capable handler stops the request, it is Chain of
Responsibility. If every link acts and passes on, it is closer to Decorator or a pipeline.
**Class form stays right when** handlers have their own configuration and tests and chains are
assembled dynamically.
**Check.** An explicit terminal handler; one request per kind and one unknown kind.

### Command (GoF Command; HF ch. 6)
**Forms.** A plain command is a closure (`() => doc.paste()`). With a single abstract method a lambda
replaces the class (HF ch. 6: the remote drops from 22 classes to 9), but once the interface has a
second method (`undo`) that stops working; use a pair of closures, a small record or classes. Keep an
object when you need undo, serialisation or logging (a data-only command like `{type:"paste",
docId}` with a registry of handlers), queuing across processes, inspection or macro composition.
Redux actions, event-sourcing events, job-queue messages, database migrations (up and down), editor
undo stacks, Java `Runnable`/`Callable` and Go `func()` are all Command.
**Sum-type form.** A closed set of commands as `enum Cmd { Insert{..}, Delete{..} }` with an exhaustive
`apply` and `invert` gives the type-safe parameters the book's class form lacked. Open sets keep the
interface and registry.
```ts
type Cmd = { k: "insert"; at: number; text: string } | { k: "delete"; at: number; len: number; removed: string };
const invert = (c: Cmd): Cmd => c.k === "insert" ? { k: "delete", at: c.at, len: c.text.length, removed: c.text }
                                                  : { k: "insert", at: c.at, text: c.removed };
```
**Check.** Round trip `execute; undo`; log replay on fresh state; replayed commands are idempotent.

### Interpreter (GoF Interpreter; HF appendix)
**Form (adaptation).** Sum type plus a recursive evaluation function:
`enum Expr { Lit(bool), Var(String), And(..), Not(..) }` with `fn eval(e, env)`. Adding an operation is a
new function (what Visitor tried to give); adding a node kind touches every match, the same
expression-problem trade-off as Visitor. Embedded DSLs, parser combinators, query builders, rule
engines, template engines, feature-flag rules, spreadsheet formulas and policy languages are
Interpreter.
**Use a grammar tool** (PEG or ANTLR-style generators, tree-sitter, parser-combinator libraries) once
the grammar is non-trivial. Interpreters of untrusted expressions need limits on depth, steps and
time, and no host-language `eval`.
**Check.** Round-trip and reference-implementation properties; fuzz for depth and non-termination.

### Iterator (GoF Iterator; HF ch. 9)
**Form.** Built into the language: Python `__iter__` and generators, Java `Iterable`, `Iterator` and
`Stream`, C# `IEnumerable` and `yield`, the JS iterator protocol and generators, the Rust `Iterator`
trait with adapters, Go range-over-func. Lazy `map/filter/take` pipelines are composed iterators.
Generators write complex traversals (tree walks) as external iterators without a manual path stack.
**Robustness by language.** Java collections fail fast on concurrent modification; concurrent
collections give weakly consistent snapshots; Rust's borrow checker forbids mutation during iteration;
immutable collections make iterators trivially robust.
**Class form stays right when** the iterator owns a resource (database cursor, file handle) and must be
closed on early exit; use the language's scoped-cleanup construct.
**Check.** Iterate twice gives the same sequence; early exit releases resources.

### Mediator (GoF Mediator; HF appendix)
**Forms (adaptation).** UI controllers, presenters and view models; state stores with reducers; game-engine
systems; request mediators; form-validation controllers; saga orchestrators and workflow engines. A
callback-injection version is a single function the colleagues call with "who changed". An event bus
is not this; it is Observer (publish-subscribe) and decentralised.
```python
def on_change(who, ui):
    if who is ui.list: ui.name.text = ui.list.selection
    ui.ok.enabled = bool(ui.name.text)
```
**Class form stays right when** colleagues are numerous and the mediator has real behaviour that needs
its own tests.
**Check.** Decision-table tests; no colleague imports another; beware the god mediator.

### Memento (GoF Memento; HF appendix)
**Forms (adaptation).** Immutable and persistent data structures make mementos nearly free via
structural sharing: keep the old version (state-store time travel, immutable-update libraries, version
control commits, filesystem snapshots, copy-on-write). Serialisation as memento for save games and
checkpoints; database transactions and savepoints are mementos managed by the engine; event sourcing
replaces snapshot-per-change by replay from a snapshot.
**Pitfalls.** Snapshots that alias mutable state (a shallow copy), secrets or huge blobs in the
snapshot, schema evolution of persisted snapshots (version them), unbounded history, restoring partial
state that leaves invariants broken.
**Class form stays right when** the state is encapsulated mutable state that must stay opaque (narrow
interface to the caretaker, wide to the originator).
**Check.** Capture, mutate, restore equals original by value.

### Observer (GoF Observer; HF ch. 2)
**Form.** A closure replaces the Observer interface: `subject.subscribe(fn)` returning an unsubscribe
handle. HF ch. 2 shows the lambda for a single-method listener. Events and listeners, signals and
slots, `EventEmitter`, DOM `addEventListener`, C# events, observables and reactive streams, signals in
UI frameworks, spreadsheet-like reactive graphs and database triggers are Observer in function form.
Distinguish in-process Observer from distributed publish-subscribe, where delivery guarantees, ordering
and persistence appear.
```ts
function emitter<T>() { const fs = new Set<(v: T) => void>();
  return { subscribe: (f: (v: T) => void) => (fs.add(f), () => fs.delete(f)), emit: (v: T) => [...fs].forEach(f => f(v)) } }
```
**Failure modes to design out** (adaptation of the book's liabilities): leaks from observers never
detached, re-entrancy, one observer's exception stopping the rest, callback thread, ordering
assumptions, update storms and diamond glitches (batching or topological propagation).
**Class form stays right when** you need interest by aspect, a change manager, or batching semantics
that deserve a named type.
**Check.** Detach during notification; state consistent at notification time; unsubscribed observers
are collectable.

### State (GoF State; HF ch. 10)
**Sum-type form.** A tagged union `enum Conn { Closed, Listening, Established{..} }` with a function from
(state, event) to the next state; the compiler checks exhaustiveness of states times events. Type-state
makes illegal transitions unrepresentable (`Conn<Closed>.open() -> Conn<Established>`; Rust,
TypeScript branded types, phantom types). Libraries and engines: XState, Spring StateMachine, Erlang
`gen_statem`; async/await compiles to state machines; order lifecycles, editor tool modes and UI
loading/error/ready states are State.
```ts
type S = { t: "closed" } | { t: "open"; sent: number };
const step = (s: S, e: "open" | "send" | "close"): S => {
  switch (s.t) { case "closed": return e === "open" ? { t: "open", sent: 0 } : s;
                 case "open":   return e === "send" ? { t: "open", sent: s.sent + 1 } : e === "close" ? { t: "closed" } : s } };
```
**Heuristic from the notes.** Few states and transitions: enum plus match. Many states with rich
per-state behaviour: State objects. Declarative, serialisable, timers and guards: a machine library.
**Warning sign.** Boolean flags that encode state implicitly with impossible combinations.
**Check.** (state, event) transition table test; only reachable states occur.

### Strategy (GoF Strategy; HF ch. 1)
**Function form.** The strategy is a function, lambda or closure parameter: `sorted(xs, key=...)`,
comparators, predicates passed to `map` and `filter`, retry and timeout policies on an HTTP client, Go
`func(a, b T) int`. Use a strategy object only when it has several operations, its own configuration or
state, or needs to be named, registered and tested as a unit.
**Generic form.** Trait or generic bounds give a compile-time strategy with no run-time cost (Rust
`S: Hasher`, C++ policy-based design, Java `Comparator<T>`), the book's template-parameter variant.
**Sum-type alternative.** When the set is closed and small, an enum plus match keeps the logic visible;
Strategy wins when the set is open (plugins) or configured externally (a config file naming an
algorithm).
```python
def render(rows, width, layout=simple_layout): return layout(rows, width)
render(rows, 80, layout=tex_layout)
```
**Check.** One contract suite parameterised by strategy; new strategy, zero edits elsewhere.

### Template Method (GoF Template Method; HF ch. 8)
**Function form.** Pass the varying steps as function arguments to a higher-order function that owns
the skeleton: `with_retry(op, on_error=...)`; setup-and-teardown wrappers (context managers,
`try-with-resources`, `defer`); `sort(cmp)`; test-framework `setUp/tearDown`; build-tool lifecycle
phases; middleware lifecycles. Traits with default methods (Rust, Scala, Java 8+) give Template Method
without class hierarchies; Go uses embedding plus function fields.
```python
def run_job(setup, step, teardown):
    ctx = setup()
    try: return step(ctx)
    finally: teardown(ctx)
```
**Caution for the inheritance form.** Fragile base class (a subclass breaks when the base reorders
calls; hooks called from constructors see a half-built subclass); prefer composition when more than
one axis varies.
**Class form stays right when** a framework must enforce a lifecycle with a final template and users
extend by subclassing.
**Check.** Cleanup runs when the step throws; the call order is pinned by one test.

### Visitor (GoF Visitor; HF appendix)
**Sum-type form.** Sum types with pattern matching replace Visitor in ML-family languages, Rust, Kotlin
sealed classes, Swift enums, Scala case classes, TypeScript discriminated unions, and Java sealed
interfaces with `switch` patterns: a new operation is a new function with a `match`; a new variant
makes the compiler flag every non-exhaustive match. Multimethods (Julia, Clojure `defmulti`, Common Lisp)
and Python `singledispatch` give double dispatch directly.
**Where a visitor object remains normal.** Compiler and AST libraries (ANTLR visitors and listeners,
Roslyn `SyntaxWalker`, Java annotation-processor visitors), file-system walkers, document exporters,
linters with per-node rule visitors, serialisation and AST transforms.
```ts
type E = { k: "num"; v: number } | { k: "add"; l: E; r: E };
const show = (e: E): string => e.k === "num" ? String(e.v) : `(${show(e.l)}+${show(e.r)})`;
```
**Check.** Exhaustiveness; a composite visit touches each child once.

---

## 6. Four substitutions that recur

Most of the table collapses to four moves; once you see which one applies, the rest is routine.

1. **Interface with one method becomes a function type.** Strategy, Command (no undo), Observer,
   the parameterised Adapter, Template Method's varying step, Factory Method and the factory in
   Abstract Factory, and an internal Iterator. Gain: no class per variant, closures capture the
   receiver. Cost: variants are anonymous, so listing, naming, logging and serialising them needs a
   registry or a data-only form.
2. **Class per variant of a closed set becomes a sum type plus match.** State, Interpreter, Visitor,
   Composite, the closed Command set. Gain: exhaustiveness checking, illegal combinations
   unrepresentable. Cost: adding a variant touches every match; open sets by plugins are awkward.
3. **Wrapper class becomes function composition.** Decorator, Proxy for cross-cutting concerns,
   Chain of Responsibility, middleware. Gain: tiny and composable. Cost: order sensitivity, identity
   loss and debugging depth are unchanged.
4. **Hand-written plumbing becomes a language or library feature.** Iterator (generators and iterator
   traits), Singleton (module value, lazy statics, DI scope), Prototype (copy-with, deep copy),
   Memento (persistent data), Flyweight (interning), Builder (named and default arguments), Adapter
   (structural typing and extension traits).

## 7. Checks before replacing a class form with a smaller one, or the other way round

Going down to a function or sum type, ask:
1. Is there exactly one operation, or do paired operations (do and undo, open and close) have to stay
   consistent? If paired, use a small record or class.
2. Does anything need to print, list, persist or compare the variants? If so, give them names and a
   registry, or keep them as data.
3. Is the set closed? Then a sum type; is it open to plugins? Then an interface or registry.
4. Will a reader of this code in a stack trace be able to tell which variant was running? Anonymous
   closures cost that.
5. Is shared state captured by the closures? Captured mutable state is the function-form version of
   the book's warning about strategies sharing mutable state.

Going up to the class form, ask:
1. Which of the "class form stays right" conditions in section 1 holds? If none, the class is
   scaffolding.
2. Would the pattern be absent from the design discussion if the code were a function? If naming
   the pattern in the comment or the type name is what a reader needs, keep the name and use the small
   form.
3. Does the language already provide the pattern (iterator, singleton by module, clone by copy)?
   Then writing it again is the smell.

Tests that survive either choice: write the pattern's behavioural test against the contract (round
trip, substitutability, exhaustiveness, one-update-per-change, same-instance-for-same-key) so that the
form can change without the tests changing.
