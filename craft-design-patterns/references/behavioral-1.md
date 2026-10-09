# Behavioural patterns, part 1: Chain of Responsibility, Command, Interpreter, Iterator, Mediator, Memento

Six patterns about who handles a request, how a request or a piece of state becomes a thing you can
pass around, how a small language is evaluated, how a collection is walked, how a group of peers
coordinates, and how state is saved without breaking encapsulation. The other five (Observer, State,
Strategy, Template Method, Visitor) and the full comparison discussion are in `behavioral-2.md`.

Citations: "GoF" is Design Patterns (1994), chapter 5 and the per-pattern pages; "HF" is Head First
Design Patterns 2e with chapter numbers. Statements marked (adaptation) are not claims of the books:
they translate an idea to current languages or are checks drawn up from the notes. Function-based and
sum-type forms of each pattern are collected in `modern-idioms.md`. In every pattern entry the "Verify" bullets, misuse signs and smell lists come from the notes' own inferred sections, so treat them as the note-takers' checks, not the books' text, even where a bullet carries no label.

## Contents

1. What the behavioural family is about
2. Chooser for this file
3. Chain of Responsibility
4. Command
5. Interpreter
6. Iterator
7. Mediator
8. Memento
9. How the six combine

---

## 1. What the behavioural family is about

GoF ch. 5 opening: behavioural patterns concern algorithms, the assignment of responsibilities between
objects, and the patterns of communication between them. They characterise control flow that is hard
to follow at run time and move the focus from flow of control to how objects are interconnected.

- Class patterns (inheritance distributes behaviour): Template Method and Interpreter.
- Object patterns (composition): peer cooperation (Mediator, Chain of Responsibility, Observer) and
  encapsulating behaviour in an object that is delegated to (Strategy, Command, State, Visitor,
  Iterator).

A recurring theme (GoF ch. 5 discussion): when some aspect changes often, define an object that
encapsulates it and let the rest collaborate with that object. The pattern is usually named after the
encapsulating object: Strategy an algorithm, State state-dependent behaviour, Mediator the protocol
between objects, Iterator how an aggregate is traversed. This is the same move as "identify what
varies and separate it" (HF ch. 1).

## 2. Chooser for this file

| Situation | Pattern |
|---|---|
| Several candidates might handle a request and which one is decided at run time | Chain of Responsibility |
| Need to queue, log, undo, redo, schedule or script operations, or pass "do this" as a value | Command (plus Memento when undo needs hidden state) |
| A recurring problem can be stated as sentences in a small language | Interpreter (for non-trivial grammars use a parser generator) |
| Walk a collection without exposing how it is stored, or support several traversals | Iterator |
| A known cluster of peers has tangled mutual dependencies | Mediator |
| Capture and later restore an object's internal state without exposing it | Memento |

---

## 3. Chain of Responsibility

**Intent.** Avoid coupling the sender of a request to its receiver by giving more than one object a
chance to handle it; chain the receivers and pass the request along until one handles it (GoF
Chain of Responsibility; HF appendix).

**Problem that signals it.** The right handler is not known in advance. GoF: context-sensitive help;
the user asks for help on a button, and the most specific help (button, then dialog, then application)
should answer, without the button knowing who supplies it. HF: an email flood sorted into fan mail,
complaints, new-location requests and spam, each routed to a different owner.

**Use when.**
- More than one object may handle a request and the handler is not known a priori.
- You want to issue a request to one of several objects without naming the receiver.
- The set of handlers should be specified dynamically.

**Do not use when.**
- You know the receiver: call it. A map lookup beats a walk down a chain for every request
  (adaptation).
- Receipt must be guaranteed and there is no sensible terminal handler.
- Every link must run on every request. That is a pipeline or decorator stack, not this pattern (see
  the note below).

**Structure.** Handler interface with an optional successor link and a default that forwards;
ConcreteHandlers handle what they are responsible for and otherwise forward; the client sends the
request to the head of the chain. A handler holds one reference (the successor), not references to all
candidates.

**Consequences and costs.**
1. Reduced coupling: sender and receiver do not know each other; a handler does not know the chain's
   structure.
2. More flexibility in assigning responsibilities: change the chain at run time, combine with
   subclassing to specialise handlers.
3. Receipt is not guaranteed: a request can fall off the end or the chain can be misconfigured. HF
   adds that it is hard to observe and debug at run time. Mitigation (adaptation): put an explicit
   terminal handler that logs or raises, and test that every request kind is handled by someone.

**Implementation choices.**
- Successor links: define new links in Handler, or reuse existing ones such as the parent reference
  in a Composite hierarchy. Reuse saves effort only if the structure matches the responsibility
  structure.
- Connecting successors: Handler keeps the successor and supplies a default `handle` that forwards, so
  uninterested subclasses do not override it.
- Representing requests, a trade-off between type safety and open-endedness: (a) one hard-coded
  operation per request kind (safe, fixed set); (b) one handler method taking a request code
  (open-ended, needs conditional dispatch, no type-safe parameters); (c) request objects, one subclass
  per kind with parameters; handlers inspect the kind, handle what they know and forward the rest to
  the parent implementation.

**Sketch.**
```
class Handler:
    def __init__(self, successor=None): self.next = successor
    def handle(self, req):
        if self.can(req): return self.do(req)
        if self.next:     return self.next.handle(req)
        raise Unhandled(req)          # make "falls off the end" explicit
```

**Neighbours and how to choose.**
- Command, Observer, Mediator and Chain are four ways to decouple sender from receiver (full table in
  `behavioral-2.md`). Chain is the one where the receiver is chosen dynamically from candidates, at the
  price of no guarantee of receipt.
- Composite: a component's parent is often the successor. Command: requests can be Command objects
  passed down the chain.
- Variant to distinguish when reviewing (adaptation): the book stresses "one handler handles it".
  Middleware stacks often let every link act and pass on; that is closer to Decorator. If the first
  capable link stops the request it is Chain of Responsibility; if every link runs it is a pipeline.
- Today's forms: middleware pipelines (Express/Koa, ASP.NET Core, servlet filters, Go handler
  chains, gRPC interceptors), DOM event bubbling, exception propagation up the call stack, logging
  handler hierarchies, approval workflows. Functional form: a list of functions returning an optional
  result and a `find_map`-style search over it (adaptation).

**Verify.**
- Each handler tested alone: it handles what it owns and forwards the rest.
- The assembled chain gets one request of each kind and one of an unknown kind; the unknown kind ends
  in an explicit failure or default, not silence.
- Order-sensitive cases are tested; handlers that silently swallow requests, order-dependent chains
  with hidden coupling and missing terminal handlers are the review smells (adaptation).

---

## 4. Command

**Intent.** Encapsulate a request as an object, so you can parameterise clients with different
requests, queue or log requests, and support undoable operations (GoF Command, also known as Action,
Transaction; HF ch. 6).

**Problem that signals it.** The thing that triggers an action cannot know what the action is. GoF: a
toolkit's menu items and buttons must trigger operations only the application knows. HF: a remote
control with seven programmable slots must drive household devices with unrelated interfaces (light,
stereo, ceiling fan, hot tub), with new vendor classes coming; the rejected design is an if/else chain
over device types in the remote, which must be edited for every vendor class (violates open-closed).
Framing principle (HF): the remote should interpret button presses and make requests, not know how to
turn on a hot tub.

**Use when.**
- You want to parameterise objects by an action (commands are an object-oriented replacement for
  callbacks).
- Requests should be specified, queued and executed at different times, possibly by another thread or
  process.
- You need undo and redo.
- You need logging for crash recovery: persist each command as executed, reload from a checkpoint and
  re-execute in order.
- You structure a system around high-level operations built from primitives (transactions), invoked
  uniformly.

**Do not use when.**
- A direct call would do and nothing needs to be queued, logged, undone or swapped.
- In a language with closures, you only need "call this later": a closure is enough (see below).
- Undo would be a fake: an "inverse operation" that does not truly invert (a lossy delete) gives
  wrong results. Use a state snapshot (Memento) or do not offer undo.

**Structure.** Command declares `execute` (and `undo` if supported). ConcreteCommand binds a Receiver
to an action. Client creates the command and sets its receiver; Invoker stores the command and calls
`execute` at some point; Receiver does the work and can be any class. HF's diner mapping: customer is
client, order slip is command, waitress is invoker, short-order cook is receiver.

**Consequences and costs.**
1. Decouples the invoker from the object that knows how to perform the operation.
2. Commands are first-class objects: manipulated and extended like any object.
3. Commands can be assembled into composite commands (a macro is a Composite).
4. Easy to add new commands without changing existing classes.
- Costs: many small classes (a subclass per sender-receiver binding, avoidable with closures or
  generics); undo needs disciplined state capture; unbounded history lists (adaptation).

**Implementation choices.**
- How smart should a command be? From a pure binding of receiver and action to a command that does
  everything itself with no receiver. "Dumb" commands keep the invoker/receiver decoupling and let one
  command class be bound to different receivers; "smart" commands lose that (HF Q&A) but are
  sometimes right, for example when no suitable receiver exists.
- Undo and redo: a command may need to store the receiver, the arguments, and the original receiver
  values that change; the receiver must expose operations to restore state. One level of undo is
  "remember the last command"; unlimited undo is a history list walked backwards (HF: a stack).
- Capture prior state before acting. HF's ceiling-fan command reads the previous speed in `execute`
  before changing it, because the inverse depends on prior state. A single `prevSpeed` field on a
  reused command instance only undoes the latest execution; store per-execution state or fresh
  instances in the history (adaptation).
- Copy a command before putting it on the history list if its state varies per invocation (GoF).
- Avoid error accumulation (hysteresis) over repeated execute and unexecute: store enough to restore
  exactly, using a Memento if internals must stay hidden.
- A macro's undo runs its subcommands in reverse order (GoF and HF).
- Null Object (HF ch. 6): pre-load empty slots and the undo slot with a command that does nothing, so
  the invoker never null-checks.
- Queuing (HF): producers enqueue commands, worker threads take one, execute it and discard it; the
  queue knows nothing of what commands compute.
- Persistence (HF): add store and load so commands can be saved; replay must be safe (see Verify).

**Sketch.**
```
interface Command { execute(); undo?() }
class Paste(doc): execute(){ prev = doc.snapshot(); doc.paste() }  undo(){ doc.restore(prev) }
history = []
run(cmd):  cmd.execute(); history.append(cmd)
undo():    history.pop().undo()
Macro(cmds): execute -> each in order; undo -> each in reverse
```

**Neighbours and how to choose.**
- Strategy: both are one-method interfaces swapped into a holder. Command binds a receiver and a
  specific request; Strategy swaps an algorithm the context uses (adaptation, from the HF notes'
  inference).
- Observer: the same Swing listener interface plays both roles (HF ch. 6); Observer notifies many of
  a change, Command packages one request for deferred or undoable invocation.
- Memento supplies state for undo; Composite builds macros; Prototype copies commands for the
  history; Chain of Responsibility passes commands until one handles them.
- Coplien's functors differ: Command binds a receiver and an action, not just a function (GoF).
- In languages with first-class functions, a plain command is a closure. Keep a command object only
  for the extras: undo, serialisation or logging (a data-only command such as `{type, docId}` with a
  handler registry), queuing across processes, inspection, macros. Redux actions, event-sourcing
  events, job-queue messages, database migrations (up and down) and editor undo stacks are all
  Command. A closed set of commands can be a sum type with an exhaustive `apply` and `invert`
  (adaptation).
- HF's lambda note: with a single-method interface a lambda replaces a class (the book's remote
  drops from 22 classes to 9), but a second abstract method (`undo`) ends that; then use a pair of
  closures or a small record.

**Verify.**
- Round trip: `execute` then `undo` yields state equal to the original, including stateful receivers
  and macros (reverse order). Property form: any random sequence of executes followed by the same
  number of undos equals the initial state; redo after undo equals the state after execute.
- The invoker imports no concrete receiver types and has no type switches on device kind; adding a
  receiver needs zero edits to the invoker.
- Pressing an empty slot does nothing and does not throw.
- Log replay on fresh state reproduces the final state; replayed commands are idempotent and do not
  depend on current time or randomness (adaptation).
- Queued commands are safe on the worker thread (receiver thread-safety); history is bounded.

---

## 5. Interpreter

**Intent.** Given a language, define a representation of its grammar together with an interpreter that
uses it to interpret sentences (GoF Interpreter, a class pattern; HF appendix).

**Problem that signals it.** A problem recurs often enough that its instances can be expressed as
sentences in a simple language. GoF: regular-expression matching, one class per grammar rule
(literal, alternation, sequence, repetition), where a regex is a tree of those objects and each node
has an `interpret(context)` operation. HF: a duck simulator teaching tool where children program a
duck with a tiny language and the grammar maps directly to classes.

**Use when.** There is a language to interpret and statements can be represented as syntax trees, and
(works best when):
- the grammar is simple: complex grammars make the class hierarchy unmanageable, and parser
  generators are better and can avoid building trees;
- efficiency is not critical: the fastest interpreters translate trees into another form first
  (regex to state machine).

**Do not use when.**
- The grammar is large: at least one class per rule does not scale. HF: use a parser or compiler
  generator.
- Performance matters and you can compile instead.
- You are looking at an ordinary Composite with operations on it. GoF notes almost every composite
  with operations contains Interpreter in a general sense; reserve the name for when the hierarchy
  defines a language.

**Structure.** AbstractExpression declares `interpret`; TerminalExpression (one class per terminal
kind); NonterminalExpression (one class per rule, holds child expressions and interprets recursively);
Context holds global interpreter information; the client builds or receives the syntax tree and calls
interpret.

**Consequences and costs.**
- Easy to change and extend the grammar (inheritance, incrementally); easy to implement (node classes
  are similar, generation can be automated); easy to add new ways to interpret an expression (pretty
  printing, type checking), and if that keeps happening use Visitor so grammar classes do not change.
- Complex grammars are hard to maintain.

**Implementation choices.**
- Building the tree is not part of the pattern: table-driven parser, hand-written recursive descent,
  or the client builds it.
- Interpretation need not live in the node classes; when new interpreters are common (type-check,
  optimise, generate code) use Visitor.
- Share terminals with Flyweight; parents pass context as extrinsic state.
- GoF samples: a regex matcher where state is a set of input streams, built so that host-language
  expressions are themselves the parser (an embedded DSL); a Boolean-expression language where even
  `replace` and `copy` are interpretations. The Boolean sample ignores precedence, leaving it to
  whoever builds the tree.

**Sketch (adaptation).**
```ts
type Expr = {k:"lit",v:boolean} | {k:"var",n:string} | {k:"and",l:Expr,r:Expr} | {k:"not",e:Expr}
const ev = (e: Expr, env: Record<string,boolean>): boolean => {
  switch (e.k) { case "lit": return e.v; case "var": return env[e.n];
    case "and": return ev(e.l,env) && ev(e.r,env); case "not": return !ev(e.e,env) } }
```
A new operation is a new function; a new node kind touches every match (the same trade-off as Visitor).

**Neighbours and how to choose.**
- Composite: the syntax tree is a Composite. Flyweight shares terminals. Iterator traverses.
  Visitor holds per-node behaviour and lets you add interpretation passes without changing grammar
  classes. GoF ch. 5 summary also pairs Interpreter with State for parsing contexts.
- Today's forms: embedded DSLs, parser combinators, query builders, rule engines, template engines,
  feature-flag and targeting rules, spreadsheet formulas, policy languages. Prefer an existing
  grammar tool (PEG or ANTLR-style generators, tree-sitter, parser-combinator libraries) once the
  grammar is non-trivial. Interpreters of untrusted expressions need limits on depth, steps and time,
  and must not delegate to the host language's `eval` (adaptation).

**Verify.**
- Property tests: `parse(print(ast)) == ast`; `eval` agrees with a reference implementation (regex
  against the library) on random inputs.
- A golden test per grammar rule.
- Fuzz for depth and non-termination (the book's repetition loop terminates only when the match state
  becomes empty).
- Smells: grammar past a dozen hand-written rule classes; interpretation logic duplicated for every
  new pass; ad hoc string handling instead of a real parser; implicit precedence (adaptation).

---

## 6. Iterator

**Intent.** Provide a way to access the elements of an aggregate sequentially without exposing its
underlying representation (GoF Iterator, also known as Cursor; HF ch. 9).

**Problem that signals it.** Callers need to walk collections stored differently. HF: two restaurant
menus, one in a list and one in a fixed array padded with nulls; the client needs two different loops
for every operation, is coupled to both representations, and a hash-table menu would force edits. What
varies is the iteration (HF ch. 9). GoF's motivation: a list should allow several traversals without
bloating its interface with each one.

**Use when.**
- You must access an aggregate's contents without exposing its representation.
- You need several concurrent traversals.
- You want one uniform way to traverse different structures (polymorphic iteration).

**Do not use when.**
- The language already provides the protocol (nearly every language does): use it rather than
  writing an Iterator class. Write your own only for structures without one (HF: arrays padded with
  nulls, custom trees).
- A getter that returns the raw internal collection is the smell this pattern removes; do not "fix"
  it by exposing a different raw collection.

**Structure.** Iterator interface; ConcreteIterator tracks the position; Aggregate declares how to
create an iterator (a Factory Method); ConcreteAggregate returns the right ConcreteIterator.

**Consequences and costs.**
1. Supports variations in traversal (swap the iterator; subclass for new orders).
2. Simplifies the Aggregate interface; HF ties this to the Single Responsibility Principle: an
   aggregate that also iterates has two reasons to change.
3. More than one traversal can be pending because each iterator holds its own state.

**Implementation choices (GoF).**
1. Who controls the iteration. External: the client advances and asks for the next element; more
   flexible (comparing two collections is easy, almost impossible with an internal iterator).
   Internal: the client hands over an operation and the iterator applies it to every element; easier
   to use, weak only in languages without closures.
2. Who defines the traversal algorithm: the iterator (easy to swap, but may need aggregate internals)
   or the aggregate, with the iterator holding only a cursor (a simple Memento).
3. How robust: modifying an aggregate during traversal can double-visit or skip. A robust iterator
   survives insertions and removals without copying, usually by registering with the aggregate.
4. Extra operations: previous for ordered aggregates, skip-to for sorted ones; minimum is first,
   next, is-done, current (or one `next` returning a sentinel).
5. Polymorphic iterators in C++ cost heap allocation and cleanup, fixed with a stack-allocated proxy
   (modern equivalents: RAII, `using`, `defer`, `with`).
6. Iterators may need privileged access; the alternative is protected accessors for subclasses only.
7. Iterators for composites: external iterators over recursive structures must store a path; internal
   iterators keep the path in the call stack. Offer separate iterators for pre-order, post-order,
   in-order and breadth-first.
8. Null iterators: always done; leaves return one for "iterate children" so recursion needs no special
   case.

HF additions: iterators imply no order unless the collection documents it; `remove` is optional and
may throw an unsupported-operation error; the behaviour of removal during concurrent modification is
unspecified and must be designed for in multithreaded use.

**Sketch.**
```
it = coll.iterator()                     # external
while it.hasNext(): use(it.next())
coll.forEach(use)                        # internal; early exit needs a return value or exception
```

**Neighbours and how to choose.**
- Composite (iterators traverse it; HF: not an evolution of Iterator, but they pair well); Factory
  Method (polymorphic iterators); Memento (cursor, or Dylan's iteration state); Template Method (an
  internal traverser); Visitor (Iterator abstracts how to traverse, Visitor decides what to do at each
  node; they pair).
- Built-in forms (adaptation): Python `__iter__` and generators, Java `Iterable` and streams, C#
  `IEnumerable` with `yield`, JS iterator protocol and generators, Rust `Iterator` with adapters, Go
  range-over-function. Generators let you write a tree walk as an external iterator without a
  manual path stack, which answers GoF issue 7. Lazy `map/filter/take` chains are composed iterators.
- Fail-fast versus robust: some collections throw on modification during iteration; concurrent
  collections give weakly consistent snapshots; Rust's borrow checker forbids the mutation at compile
  time; immutable collections make iterators trivially robust (adaptation).

**Verify.**
- Iterating twice gives the same sequence; two live iterators on one aggregate do not interfere; an
  empty collection yields nothing; `next` after exhaustion fails in the documented way; `hasNext` is
  idempotent (HF contract checks, partly adaptation).
- Mutation during iteration has a defined, tested behaviour (fail fast or robust).
- Resource-holding iterators (database cursors, file handles) release resources on early exit.
- Client code compiles without naming any concrete aggregate; no getter exposes the internal
  collection; no traversal state lives in the aggregate.

---

## 7. Mediator

**Intent.** Define an object that encapsulates how a set of objects interact; promote loose coupling by
keeping the objects from referring to each other explicitly, and let their interaction vary
independently (GoF Mediator; HF appendix).

**Problem that signals it.** Behaviour distributed across objects ends with every object knowing every
other, which kills reuse and makes system-wide changes need many subclasses. GoF: a dialog where a
button is disabled when an entry field is empty, picking from a list fills the field, typing selects
list entries; each dialog has different dependencies, so stock widgets would need subclassing per
dialog. HF: a smart home whose alarm, coffee pot, calendar and sprinkler each hold rules that mention
the others ("no coffee on weekends", "sprinkler off before showers").

**Use when.**
- A set of objects communicate in well-defined but complex ways and the interdependencies are
  unstructured and hard to understand.
- Reusing an object is difficult because it refers to many others.
- Behaviour distributed among several classes should be customisable without many subclasses.

**Do not use when.**
- The sources of change should not know their dependents and the dependents vary: that is Observer.
- The mediator would simply mirror each colleague's methods: it has become a Facade.
- The coordination logic is growing into the whole application; the mediator has become a god object
  (see consequences).

**Structure.** Mediator interface; ConcreteMediator knows and maintains colleagues and implements the
cooperative behaviour; each Colleague knows only its mediator and communicates through it.

**Consequences and costs.**
1. Limits subclassing: change interaction by subclassing the mediator; reuse colleagues as is.
2. Decouples colleagues.
3. Simplifies object protocols: many-to-many becomes one-to-many.
4. Abstracts how objects cooperate: interaction becomes its own concept.
5. Centralises control, the liability: complexity moves from the interactions into the mediator, which
   can become a monolith more complex than any colleague. In the book's sample, `widgetChanged` grows
   with the dialog into an if/else chain on which widget changed. HF names the same risk.

**Implementation choices.**
- Omit the abstract Mediator when colleagues work with exactly one mediator.
- Colleague-to-mediator communication: the mediator observes colleagues (they are subjects), or a
  specialised notification where the colleague passes itself (`widgetChanged(this)`) so the mediator
  can tell who sent it.

**Sketch.**
```
class FontDialog:                      # mediator
    def __init__(s): s.list=ListBox(s.on_change); s.name=Entry(s.on_change); s.ok=Button(s.on_change)
    def on_change(s, who):
        if who is s.list: s.name.text = s.list.selection
        s.ok.enabled = bool(s.name.text)
```

**Neighbours and how to choose.**
- Observer versus Mediator is the main decision (full discussion in `behavioral-2.md`): Observer
  distributes communication and Mediator centralises it. Pick Mediator when the coordination is one
  cohesive rule set among a known group; pick Observer for an open-ended set of dependents.
- Facade: one-way simplification that adds no behaviour and is unknown to the subsystem; Mediator is
  multi-directional, adds cooperative behaviour and is known to its colleagues.
- Observer's ChangeManager is a Mediator between subjects and observers (see `behavioral-2.md`).
- HF ch. 12 notes the MVC controller resembles a mediator only partly, because the view also reads
  the model directly.
- Today's forms: UI controllers, presenters and view models, state stores and reducers, game-engine
  systems, request mediators, form-validation controllers, saga orchestrators and workflow engines.
  Orchestration versus choreography in service design maps to Mediator versus Observer
  (adaptation).

**Verify.**
- Colleague unit tests use a fake mediator.
- Mediator tests send each colleague event and assert the resulting colleague states, as a decision
  table of interactions (adaptation).
- No colleague imports another colleague.
- Smells: a mediator accumulating domain logic ("god mediator"); colleagues still referencing each
  other directly (partial mediation); event ordering that is hidden or cyclic update loops (A changes
  B changes A): add guards or make the derived state declarative (adaptation).

---

## 8. Memento

**Intent.** Without violating encapsulation, capture and externalise an object's internal state so the
object can be restored to it later (GoF Memento, also known as Token; HF appendix).

**Problem that signals it.** You need checkpoints or undo, but the state is private and exposing it
would break encapsulation. GoF: a constraint solver keeps equations so connected shapes stay linked;
undoing a "move" by moving back the same distance does not restore appearance and the solver's public
interface cannot reverse its effects exactly. The solver hands out an opaque state object that only
it can read. HF: a game that loses days of progress when the character dies; save progress at a level
boundary and restore it, without letting other code read or break the state.

**Use when.**
- A snapshot of some part of an object's state must be saved so it can be restored, and
- a direct interface to get the state would expose implementation details.

**Do not use when.**
- Capture or restore is expensive (copying large state, doing it often) and cannot be made
  incremental.
- A plain value copy would do, because the state is already public data.
- Immutable or persistent data structures are in use: keeping the old version is the memento
  (adaptation).

**Structure.** Memento stores as much or as little of the originator's state as the originator
decides, with a narrow interface for the caretaker (pass it around) and a wide one for the originator.
Originator creates a memento of its state and restores from one. Caretaker keeps mementos safe and
never inspects them.

**Consequences and costs.**
1. Preserves encapsulation boundaries.
2. Simplifies the Originator: clients, not the originator, store the versions they asked for.
3. Mementos might be expensive.
4. Defining narrow and wide interfaces may be hard in some languages.
5. Hidden cost of caring for mementos: a lightweight caretaker (an undo history) cannot know how much
   state each memento holds and may incur large storage costs; it must delete what it keeps.
HF adds: saving and restoring can take time; serialisation is one way to save state.

**Implementation choices.**
1. Two protection levels: C++ friend access. Modern equivalents (adaptation): a nested private class,
   package- or module-private constructors and fields, opaque types or handles, a closure that
   captures state, or an immutable snapshot value (encapsulation then by convention).
2. Incremental changes: if mementos are created and restored in predictable order (undo history),
   store only the delta. Restoring arbitrary mementos out of order then breaks.
3. Restoring must re-establish invariants: the book re-solves the constraints after restoring.

**Sketch.**
```
class MoveCmd:
    def execute(s): s.snap = solver.create_memento(); s.target.move(s.d); solver.solve()
    def undo(s):    s.target.move(-s.d); solver.restore(s.snap); solver.solve()
# create_memento returns an opaque object only restore can read
```

**Neighbours and how to choose.**
- Command stores a memento for undo and avoids hysteresis. Iterator can use a memento as its cursor
  or iteration state. Prototype can sometimes clone state (adaptation).
- GoF ch. 5: Command and Memento are "magic tokens" passed around and used later. Command's token is a
  request and polymorphism is central to it; a Memento's interface is so narrow that it can only be
  passed by value, with no polymorphic operations for clients.
- Today's forms (adaptation): persistent collections and structural sharing (state-store time travel,
  version control commits, filesystem snapshots, copy-on-write); serialisation for save games and
  training checkpoints; database transactions and savepoints; event sourcing replaces a snapshot per
  change by replay from a snapshot.

**Verify.**
- Property: capture, mutate, restore yields a value-equal state for random mutations.
- Mementos remain valid after the originator keeps changing: no aliasing (a shallow copy of mutable
  state silently changes after capture).
- History size and length are bounded; secrets and huge blobs are not captured by accident; persisted
  mementos carry a version for schema evolution.
- Originator invariants hold after restore.

---

## 9. How the six combine

GoF ch. 5 summary: with few exceptions the behavioural patterns complement each other.

- A class in a chain of responsibility likely uses Template Method (primitive operations decide
  "should I handle it?" and "who is next?"); the chain can carry Command objects as requests.
- Interpreter can use State to define parsing contexts; Iterator traverses an aggregate while Visitor
  applies an operation to each element.
- A Composite system might use Visitor for operations on components, Chain of Responsibility so
  components reach global properties through their parent, Decorator to override those properties on
  parts, Observer to tie one structure to another, and State to let a component change behaviour with
  its state; Builder may create it and Prototype may copy it.
- The book's point: well-designed systems have several patterns embedded in them, not necessarily
  because the designers thought in those terms; composing at the pattern level gives the synergy with
  less effort.
