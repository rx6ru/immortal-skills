# Behavioural patterns, part 2: Observer, State, Strategy, Template Method, Visitor, and the behavioural comparison

Five patterns about notifying dependents, changing behaviour with state, swapping algorithms, fixing an
algorithm's skeleton, and adding operations to a stable structure; then the discussion that tells them
apart from each other and from Command, Mediator, Chain of Responsibility and Iterator in
`behavioral-1.md`.

Citations: "GoF" is Design Patterns (1994), chapter 5 and the per-pattern pages; "HF" is Head First
Design Patterns 2e with chapter numbers. Statements marked (adaptation) are not claims of the books:
they translate an idea to current languages or are checks drawn up from the notes. Function-based and
sum-type forms are collected in `modern-idioms.md`. In every pattern entry the "Verify" bullets, misuse signs and smell lists come from the notes' own inferred sections, so treat them as the note-takers' checks, not the books' text, even where a bullet carries no label.

## Contents

1. Chooser for this file
2. Observer
3. State
4. Strategy
5. Template Method
6. Visitor
7. The behavioural comparison discussion
   - 7.1 Encapsulating variation
   - 7.2 Objects as arguments
   - 7.3 Mediator vs Observer: encapsulate or distribute communication
   - 7.4 Decoupling senders and receivers: Command, Observer, Mediator, Chain
   - 7.5 State vs Strategy vs Template Method vs Factory Method
   - 7.6 Visitor vs sum types vs methods on classes: choose by the axis of change
   - 7.7 Quick chooser for all eleven behavioural patterns
   - 7.8 Review questions

---

## 1. Chooser for this file

| Situation | Pattern |
|---|---|
| Unknown or varying set of dependents must hear about a state change | Observer |
| An object's behaviour depends on a lifecycle mode; the same state test is repeated in several methods | State |
| The client (or configuration) picks one of several interchangeable algorithms | Strategy |
| Several classes share a fixed sequence of steps and differ in a few of them; the base must enforce the sequence | Template Method |
| Many unrelated operations over a stable, heterogeneous structure | Visitor |

---

## 2. Observer

**Intent.** Define a one-to-many dependency so that when one object changes state, all its dependents are
notified and updated automatically (GoF Observer, also known as Dependents, Publish-Subscribe; HF
ch. 2).

**Problem that signals it.** Related objects must stay consistent without tight coupling. HF: a weather
data object must update three displays (current conditions, statistics, forecast) and new displays
should be addable by other developers and by users at run time. The naive design calls each concrete
display from the data object's change hook. The quiz diagnosis (HF ch. 2): it codes to concrete
implementations, every new display edits this code, displays cannot be added or removed at run time,
and the varying part is not encapsulated. GoF: a data object plus a spreadsheet view and a bar chart
view that all update when the data changes.

**Use when.**
- An abstraction has two aspects, one dependent on the other, and you want to vary and reuse them
  independently.
- A change to one object requires changing others, and you do not know how many.
- An object should notify others without assuming who they are.

**Do not use when.**
- There is one fixed dependent: call it. The subscription machinery costs more than it saves
  (adaptation).
- The coordination is one cohesive rule set among a known group: Mediator (see section 7.3).
- Delivery guarantees, ordering, filtering by message type or persistence are needed across
  processes: that is publish-subscribe through a broker, which HF says is related but more complex
  and different (message-type interest, further separation). In-process Observer has none of these.
- Display or domain logic is being put inside `update` in a real application; HF says that is fine
  for a toy and that real separation comes with MVC.

**Structure.** Subject: attach, detach, notify. Observer: `update`. ConcreteSubject stores state and
notifies when a change could make observers inconsistent; ConcreteObserver holds a reference to its
subject and keeps its state consistent. The subject depends only on the Observer interface.

**Consequences and costs.**
1. Abstract coupling between subject and observer; they can sit in different layers.
2. Broadcast communication: no explicit receiver; observers can be added and removed at any time and
   decide to handle or ignore.
3. Unexpected updates (the liability): observers are blind to each other and to the cost of changing
   the subject; an innocuous operation can cascade; a plain update protocol does not say what changed.
HF's loose-coupling principle ("strive for loosely coupled designs between objects that interact")
lists what Observer gives: the subject knows only the interface; observers can be added, replaced or
removed at run time; new observer kinds never change the subject; each side can be reused alone;
changes to either side do not affect the other so long as the contract holds. Loose coupling does not
mean no dependency, it means one object knows little about the other's details.

**Implementation choices (GoF unless noted).**
1. Mapping subjects to observers: references in the subject (simple) or a central associative table
   (no per-subject cost when few subjects have observers, slower lookup).
2. Observing more than one subject: pass the subject to `update` so the observer knows which fired.
3. Who triggers the update: state-setting operations call notify automatically (clients cannot
   forget, but several consecutive changes give several updates) or clients call notify after a batch
   (fewer updates, easy to forget).
4. Dangling references to deleted subjects: the subject notifies observers on deletion.
5. The subject must be self-consistent before it notifies. Easy to violate when a subclass calls an
   inherited operation that notifies before the subclass state is updated. Fix: make notify the last
   step of a Template Method in the base subject and document which operations notify.
6. Push versus pull. Push sends detailed change data whether wanted or not (observers become less
   reusable; the subject must anticipate needs). Pull sends a minimal notification and observers ask
   for what they need. HF ch. 2 uses pull because adding a datum then means adding a getter, not
   changing every `update` signature and every observer, and calls pull the more correct choice; the
   costs it names are more calls and a subject that must expose getters, and (note-taker inference) a
   risk of an observer reading inconsistent state between notification and reads. A middle path in
   today's code is to send a small event object (adaptation).
7. Specify events of interest: register for an aspect so only interested observers hear about
   specific events.
8. A ChangeManager (a Mediator, usually a singleton) can own the subject-to-observer map and the
   update strategy. A DAG-aware manager gives an observer watching several subjects one update after all
   have changed, avoiding redundant or glitchy updates.
9. Do not rely on notification order (HF ch. 2, quoting the JDK's advice).

**Sketch.**
```
class Subject:
    def __init__(s): s._obs = []
    def attach(s, o): s._obs.append(o)
    def detach(s, o): s._obs.remove(o)
    def _notify(s):
        for o in list(s._obs): o.update(s)       # iterate a copy: observers may detach in the callback
class Timer(Subject):
    def tick(s): s.t += 1; s._notify()           # notify last, with consistent state
```

**Neighbours and how to choose.**
- Mediator: see section 7.3. Command: both appear as the same listener interface in GUI toolkits (HF
  ch. 6); Observer broadcasts a change, Command packages one request.
- Strategy swaps one algorithm owned by the client; Observer fans a change out to many dependents (HF
  ch. 2).
- Observer is the notification channel between model and view in MVC (HF ch. 12; see the compound
  patterns file of this skill).
- Java's built-in `Observable` class and `Observer` interface were deprecated in Java 9 (HF ch. 2);
  people found it easier to write their own or wanted something more robust. The class form also
  forced subjects to extend it, an inheritance cost (the book hints at this; it is not argued in
  detail).
- Today's forms (adaptation): events and listeners, signals and slots, `EventEmitter`, DOM
  `addEventListener`, C# events, reactive streams, signals in UI frameworks, spreadsheet-style
  reactive graphs (the DAG manager is a precursor of glitch-free propagation), database triggers,
  webhooks. A closure replaces the Observer interface: `subject.subscribe(fn)` returns an
  unsubscribe handle.

**Verify.**
- The subject imports no concrete observer types; adding an observer class changes zero lines in the
  subject.
- Detach works: after `removeObserver(o)`, `o` gets nothing, including when detaching during a
  notification.
- A fake observer shows each change delivered exactly once per notification, and that the subject's
  state is already consistent when the observer reads it.
- Count updates for a batch operation; a diamond dependency (one observer on two subjects that share
  a source) yields one update.
- Failure modes the book's liabilities predict (adaptation): observers never detached (leaks; the
  lapsed-listener problem; use weak references or lifecycle-scoped unsubscribe handles); an observer
  mutating the subject inside its callback (loops, inconsistent order; iterate a copy or queue
  notifications); one observer's exception stopping the others; callbacks on an unexpected thread.
- The reproducible demo from HF ch. 2: three measurement updates produce three lines from each
  display, with statistics running average, max and min.

---

## 3. State

**Intent.** Allow an object to alter its behaviour when its internal state changes; the object appears
to change its class (GoF State, also known as Objects for States; HF ch. 10).

**Problem that signals it.** The same state test is repeated in many methods. GoF: a TCP connection
responds differently to open, close, send and acknowledge depending on whether it is established,
listening or closed. HF: a gumball machine coded with integer state constants and an if/else chain
over all states in each of four action methods; it works until a "one in ten wins two gumballs"
feature needs a new state, which means a new branch in every method. HF's checklist of what is wrong
with the conditional version: it violates open-closed, is not really object-oriented, hides
transitions inside conditionals, encapsulates nothing that varies, and further additions are likely to
break working code.

**Use when.**
- An object's behaviour depends on its state and must change at run time accordingly.
- Operations contain large multipart conditionals on that state (usually enum constants), often the
  same conditional in several operations.

**Do not use when.**
- Few states and no growth expected: an enum with a switch, or a sum type with a match, is simpler (HF
  warns only briefly about the one-off case; the heuristic is the notes').
- You need a declarative, serialisable or visual machine with guards and timers: use a state-machine
  library or a transition table (see implementation choices).
- The "states" are chosen by the caller and stay fixed: that is Strategy.

**Structure.** Context (the client-facing object) holds a current State object and delegates
state-specific requests to it, often passing itself. State interface declares an operation per
action. ConcreteStates implement behaviour for one state each and either they or the Context decide
the successor state.

**Consequences and costs.**
1. Localises state-specific behaviour and partitions it per state; new states and transitions are new
   classes. The alternative scatters look-alike switches and touches many operations for each new
   state. Cost: more classes and less compactness, worthwhile with many states.
2. Makes transitions explicit and atomic from the Context's view: rebinding one variable rather than
   several, which protects against inconsistent internal states.
3. State objects can be shared when they hold no instance variables (state is in the type): they are
   flyweights with no intrinsic state. HF: share them across contexts if they keep no per-context
   data, passing the context into each call.

**Implementation choices.**
1. Who defines transitions. Context: good when transitions are fixed. State classes: more flexible and
   extendable by new subclasses, but states then know their successors, which couples subclasses; HF
   suggests context getters instead of naming concrete state classes. The choice decides which
   classes stay closed for modification.
2. Table-driven alternative (Cargill): a table maps (state, input) to next state. Pros: regular and
   changeable as data. Cons: slower than a virtual call, transition logic less explicit, hard to
   attach actions. State pattern models state-specific behaviour; the table models transitions.
3. Create state objects on demand and destroy them (states unknown up front, rare changes, big states)
   or create all up front and keep them (rapid changes).
4. Dynamic inheritance is impossible in most OO languages (delegation languages do it directly).
5. HF design aids: before coding, write a state-by-action table giving each cell's behaviour and
   target state. A base class with default "you cannot do that" responses removes duplicated code
   in the error states (GoF's own sample default is a no-op base; decide explicitly whether an invalid
   event is ignored or rejected), at the price of states no longer being forced to say anything about every
   action; interface versus abstract class lets you add methods later without breaking states. A new
   event is a new method on the State interface plus one implementation per state (HF refill
   exercise: no-op everywhere except the sold-out state).
6. Whether to give a variant its own state class: HF discusses putting "winner dispenses two" into the
   existing sold state to save duplication versus a distinct winner state. It frames this as a
   trade-off; the default lean is one class per distinct state, because merging gives a class two
   responsibilities and the rule may change.

**Sketch.**
```
class InvalidOperation(Exception): pass
class State:                          # defaults: an event the state does not handle is rejected
    def open(self, c):  raise InvalidOperation("cannot open")
    def close(self, c): raise InvalidOperation("cannot close")
    def send(self, c):  raise InvalidOperation("cannot send")
class Closed(State):
    def open(self, c): c.state = Established()
class Established(State):
    def close(self, c): c.state = Closed()
    def send(self, c):  c.transmit()
class Conn:
    def __init__(self):   self.state = Closed()
    def open(self):       self.state.open(self)
    def close(self):      self.state.close(self)
    def send(self):       self.state.send(self)
    def transmit(self):   print("sent")
```

**Neighbours and how to choose.**
- Strategy: same class diagram, different intent. See section 7.5.
- Flyweight (sharing state objects); Singleton (states are often singletons); Proxy (HF's design
  puzzle: an image proxy with two hidden states is a State candidate).
- Sum types: `enum Conn { Closed, Listening, Established{..} }` with a function from (state, event) to
  the next state gets exhaustiveness checking over states times events from the compiler. The
  type-state technique (Rust, TypeScript branded types) makes illegal transitions unrepresentable:
  `open` exists only on a closed connection and returns an established one (adaptation). Compilers
  turn async functions into state machines too (adaptation).
- Rule of thumb from the notes: few states and transitions, use enum and match; many states with
  substantial per-state behaviour, use State objects; need a declarative machine, use a library or
  table.
- Warning signs: boolean flags (`isLoading && !isError && hasData`) that encode states implicitly with
  impossible combinations; the same `switch(state)` in many methods; transitions scattered over the
  code; clients setting the context's state directly.

**Verify.**
- Transition table test: for every (state, event) pair assert the expected next state and side effects
  or an explicit rejection. When the pattern is introduced as a refactoring, the old test-drive output
  must be reproduced exactly (HF ch. 10).
- Illegal events in a state are harmless (message or no-op), never data corruption.
- The Context contains no `if` or `switch` on state; adding a state touches the new class, the context
  field or getter, and only the transitions into it.
- Shared state objects hold no mutable per-context fields.
- Property: only reachable states occur; per-state invariants hold (adaptation).

---

## 4. Strategy

**Intent.** Define a family of algorithms, encapsulate each, and make them interchangeable, so the
algorithm varies independently from the clients that use it (GoF Strategy, also known as Policy; HF
ch. 1).

**Problem that signals it.** Inheritance or conditionals are being used to vary behaviour. HF's
SimUDuck: adding `fly` to the `Duck` base class made rubber ducks fly ("a localised update caused a
nonlocal side effect"); overriding to do nothing means inspecting every new subclass forever;
splitting into `Flyable`/`Quackable` interfaces removes the wrong behaviour but destroys code reuse
and duplicates the flying code across dozens of classes. Quiz-level disadvantages of subclassing for
behaviour: duplicated code, hard run-time change, hard to know every duck's behaviour, unintended
changes to other ducks. GoF: line-breaking algorithms hard-wired into the class that needs them, which
makes clients large, loads unused algorithms and makes adding algorithms hard.

**Use when.**
- Many related classes differ only in behaviour: configure a class with one of many behaviours.
- You need different variants of an algorithm (space and time trade-offs).
- An algorithm uses data clients should not know about.
- A class has many behaviours that appear as multiple conditionals; move the branches into strategy
  classes. Code with many conditionals often indicates a need for Strategy.

**Do not use when.**
- The variation is not relevant to clients; they would have to know the strategies just to choose
  one, which leaks implementation. Hide it, or give a sensible default.
- The set is closed and small: an enum or sum type with a match keeps the logic visible (adaptation).
- The strategy interface would carry many parameters that most strategies ignore (communication
  overhead; GoF says if it hurts, couple more tightly).
- Applying open-closed everywhere: HF ch. 3 says concentrate on areas most likely to change.

**Structure.** Strategy interface; ConcreteStrategies implement the algorithm; Context holds a
Strategy and delegates, either passing all needed data in the call or passing itself so the strategy
calls back. The client normally creates a ConcreteStrategy, hands it to the context and thereafter
talks only to the context. HF assembles the same thing from three principles: encapsulate what
varies, program to an interface, favour composition (has-a) over inheritance (is-a).

**Consequences and costs.**
1. Families of related algorithms; inheritance can factor common parts.
2. An alternative to subclassing the Context: subclassing hard-wires behaviour, mixes algorithm with
   context code and prevents run-time switching.
3. Eliminates conditional statements.
4. A choice of implementations with different time and space trade-offs.
5. Clients must be aware of the strategies to choose one.
6. Communication overhead between strategy and context: the shared interface forces parameters some
   strategies ignore.
7. More objects; reduce by making strategies stateless and shareable (Flyweight).
HF gains: a behaviour class can be reused by non-ducks (a duck call reuses the quack behaviour);
adding a new behaviour is one new class and no edit to the host; behaviour can change at run time by
a setter. Behaviour objects can still have state and methods.

**Implementation choices.**
1. Defining the interfaces: take the data to the strategy (parameters; decoupled but may pass
   unneeded data) or pass the context itself (the strategy pulls exactly what it needs; the context
   needs an elaborate data interface; tighter coupling). The interface must support all present and
   plausible algorithms; changing it forces changing every strategy.
2. Strategies as template (generic) parameters when chosen at compile time and never changed at run
   time: no abstract base, static binding, efficiency.
3. Optional strategy: the context uses default behaviour when none is set, so only clients that dislike
   the default deal with strategies.
4. Where the strategy is assigned: HF's constructors hard-code `new Quack()`, which it admits is a
   flaw, deferred to the factory chapter; because the field is interface-typed it can be replaced by
   a setter.

**Sketch.**
```
class Report:
    def __init__(self, rows, layout=SimpleLayout()):      # default strategy
        self.rows, self.layout = rows, layout
    def render(self, width): return self.layout.compose(self.rows, width)
Report(rows, layout=TeXLayout())
```

**Neighbours and how to choose.**
- State vs Strategy, Template Method vs Strategy: section 7.5.
- Decorator vs Strategy: Decorator changes the skin (wraps; the component is unaware; the wrapper
  conforms to the component's interface); Strategy changes the guts (the component knows its
  extension points; the strategy may have its own narrow interface). Prefer Strategy when the
  component is heavy (GoF).
- Flyweight: strategy objects make good flyweights.
- In languages with first-class functions the strategy is often just a function or closure parameter
  (`sort` key, comparator, predicate, retry policy, timeout). Use an object only when the strategy has
  several operations, its own configuration or state, or must be named, registered and tested as a
  unit. Generics or traits give a compile-time strategy with no run-time cost (the book's
  template-parameter variant). Plugins and externally chosen algorithms ("algorithm: tex" in a config
  file) favour the object or registry form (adaptation).
- Warning signs: `if type == "x"` ladders; an interface with eight parameters most strategies ignore;
  strategies sharing mutable state; client code that must know every concrete strategy to pick one
  (use a registry or factory, or a default).

**Verify.**
- One behavioural contract test suite, parameterised by strategy, runs against every strategy.
- A context test with a stub strategy confirms delegation; a default-strategy test; a setter test
  that changing the strategy changes the next call's result (HF runtime demo).
- Adding a new strategy needs zero edits to the context or existing strategies.
- Stateless shared strategies are tested for thread safety.

---

## 5. Template Method

**Intent.** Define the skeleton of an algorithm in an operation, deferring some steps to subclasses,
which can redefine certain steps without changing the algorithm's structure (GoF Template Method, a
class pattern; HF ch. 8).

**Problem that signals it.** Two or more classes repeat the same sequence of steps with different step
implementations. HF: coffee and tea recipes (boil water, brew or steep, pour into cup, add condiments);
the first cut only moved two shared methods up, leaving the four-step sequence duplicated in each
subclass. Step: notice the analogous steps are named differently, generalise the names (`brew`,
`addCondiments`), write the sequence once in the base, and the base now "runs the show". GoF: a
framework `openDocument` fixes the order (check, create, add, hook, open, read) and subclasses fill in
steps.

**Use when.**
- Implement the invariant parts of an algorithm once and leave the varying parts to subclasses.
- Factor common behaviour out of subclasses to avoid duplication (identify the differences, extract
  them into operations, replace the differing code with a template method).
- Control subclass extensions: the template calls hooks at specific points, so extension is possible
  only there.
- Enforce an invariant around a variable step (GoF AppKit `display`: set focus, call the overridable
  draw step, always reset focus).

**Do not use when.**
- The variation must change at run time, or you would need a subclass per combination, or you do not
  own the base class: use Strategy or closures (GoF and HF).
- More than one axis varies: inheritance forces a combinatorial hierarchy; prefer composition.
- The skeleton has a dozen abstract steps: subclassing becomes tedious.

**Structure.** AbstractClass defines the template method (final where the language allows) and the
steps; ConcreteClass implements the primitive steps. Control is inverted: the Hollywood principle,
"don't call us, we'll call you".

**Kinds of operation inside the template (GoF; HF ch. 8).**
- the template method itself (not overridable);
- primitive (abstract) operations the subclass must implement;
- concrete operations in the base (generally useful helpers);
- factory methods (Factory Method is a specialisation of Template Method);
- hooks: concrete operations with an empty or default body that subclasses may override.
Decision rule (HF Q&A): abstract method when the subclass must provide the step; hook when the step is
optional. Uses of hooks: make a step optional (`customerWantsCondiments()` guarding the condiments
step), let the subclass react to something about to happen or just happened, let the subclass make a
decision for the base class. Replace "override and remember to call super" by a template that calls
an empty hook, so subclasses cannot forget to call the inherited operation.

**Consequences and costs.**
- A fundamental technique for code reuse, especially in frameworks.
- Subclasses depend on the base class's implementation of its steps; the notes (HF fireside chat)
  list this as the cost against Strategy. Fragile base class risk (adaptation): a subclass breaks when
  the base changes the order of calls; hooks called from a base constructor see a half-initialised
  subclass.
- Document which operations are hooks (may override) and which are abstract (must override), or subclass
  writers cannot reuse the class. Keep the number of required primitives small; do not make steps too
  granular, because fewer steps mean less flexibility and more steps mean more burden (HF).

**Implementation choices.**
1. Access control: primitives protected, required ones abstract, the template method final or sealed
   (C++ non-virtual; Java/Kotlin `final`; Python by convention, ABC or `__init_subclass__`).
2. Minimise primitives.
3. Naming conventions flag overridable steps (`Do-` prefix in one framework).
4. Where there is no subclass (HF `Arrays.sort`): the algorithm cannot subclass arrays, so the missing
   step, comparing, is deferred to an interface the elements implement. HF argues this is Template
   Method in spirit (the skeleton is fixed and incomplete), not Strategy, where the composed object
   supplies the entire algorithm.

**Sketch.**
```
class Beverage:
    def prepare(self):                    # final in spirit: do not override
        self.boil_water(); self.brew(); self.pour_in_cup()
        if self.wants_condiments(): self.add_condiments()
    def brew(self): raise NotImplementedError          # required step
    def add_condiments(self): raise NotImplementedError
    def wants_condiments(self): return True            # hook with a default
```

**Neighbours and how to choose.**
- Strategy: section 7.5.
- Factory Method: factory methods are called by template methods; Factory Method is a specialisation.
- Observer: notify as the last step of a template. Iterator: an internal traverser is a template.
- Dependency rot (HF): the Hollywood principle keeps high-level components deciding when and how
  low-level ones are called; it is a technique for building frameworks, and a narrower idea than
  dependency inversion, which says depend on abstractions.
- Functional equivalents (adaptation): a higher-order function taking the varying steps, retry and
  setup-teardown wrappers (context managers, `try-with-resources`, `defer`), `sort(cmp)`, test-framework
  setup and teardown, build lifecycle phases, framework lifecycle methods, and traits with default
  methods. Go uses embedding plus function fields.

**Verify.**
- Test the template once with a minimal subclass that records call order; assert step order and that
  default hooks leave default behaviour.
- Teardown or cleanup still runs when a step throws (adaptation).
- Each concrete subclass is tested for its own steps only.
- The template method is final or sealed; no subclass duplicates the sequence; a new variant needs
  only the primitive operations and zero edits to the base.
- Smells: subclasses that must call super in a particular order; a dozen abstract primitives; hooks
  invoked from the base constructor; undocumented required versus optional overrides; abstract methods
  almost everyone stubs out (should be hooks) or hooks that must be overridden to be correct (should
  be abstract) (adaptation).

---

## 6. Visitor

**Intent.** Represent an operation to be performed on the elements of an object structure; define a new
operation without changing the classes of the elements it operates on (GoF Visitor; HF appendix).

**Problem that signals it.** Many unrelated operations must run over a structure of many classes, and
each one added as a method makes the node classes hard to maintain. GoF: a compiler syntax tree with
type checking, optimisation, flow analysis, pretty-printing and metrics; each new operation means
editing and recompiling every node class. HF: nutrition facts across a composite menu; adding
`getCalories`, `getProtein`... to every menu class is Pandora's box, and a new class such as a recipe
repeats the work.

**Use when.**
- An object structure contains many classes with differing interfaces, and operations depend on the
  concrete class.
- Many distinct and unrelated operations must be performed and you want to avoid polluting the
  classes; related operations are kept together in one visitor, and only applications that need an
  operation include its visitor.
- The classes defining the structure rarely change but you often add operations. If element classes
  change often, define the operations in the classes instead.

**Do not use when.**
- The element hierarchy changes often: every new element adds a method to Visitor and to every
  concrete visitor.
- The language has sum types and pattern matching, which give the same trade-off with less machinery
  (section 7.6).
- Visitors would need to mutate the structure while traversing, or the elements would have to expose
  every field just to serve visitors (encapsulation cost).

**Structure.** Visitor declares a `visit` operation per ConcreteElement class; ConcreteVisitors
implement them, hold local state and accumulate results; Element declares `accept(visitor)`;
ConcreteElement's accept calls the matching visit passing itself (double dispatch); ObjectStructure can
enumerate its elements.

**Consequences and costs.**
1. Adding new operations is easy (add a visitor).
2. A visitor gathers related operations and separates unrelated ones; algorithm-specific data stays
   inside it.
3. Adding new ConcreteElement classes is hard. This is the key trade-off: are you more likely to
   change the algorithms or the element classes? Stable hierarchy and changing operations: Visitor.
   Frequently changing hierarchy: operations in the classes.
4. Visits across class hierarchies: unlike Iterator, no common supertype is needed.
5. Accumulates state while visiting, instead of extra arguments or globals.
6. Breaks encapsulation: elements must expose enough interface for visitors. HF lists this and
   the harder structural changes as drawbacks.

**Implementation choices.**
- Double dispatch: the operation depends on two types, the element's and the visitor's. Languages
  with single dispatch simulate it; languages with multiple dispatch lessen the need. Overloading
  `visit(Foo)` versus distinct names `visitFoo` is a style choice; overloading hides which case runs
  at the call site.
- Who traverses: the object structure (most common; a composite's accept recurses and then calls the
  composite visit); a separate iterator (an internal iterator does not double-dispatch, but works if
  the visitor method just calls the element's operation without recursing); or the visitor itself
  (duplicates traversal code in every visitor, justified when traversal is irregular or depends on
  results, as in the regex matcher whose repeat re-traverses its body).
- A base visitor with no-op defaults lets concrete visitors override only some.

**Sketch.**
```
class Num:  accept(v)= v.num(self);   class Add: accept(v)= v.add(self)
class Eval: num(n)=n.value ; add(a)= a.l.accept(self)+a.r.accept(self)
class Show: num(n)=str(n.value) ; add(a)= "("+a.l.accept(self)+"+"+a.r.accept(self)+")"
# a new pass = a new class; a new Mul node = a new method in EVERY visitor
```

**Neighbours and how to choose.**
- Composite (visitors apply operations over composites); Interpreter (a visitor can do the
  interpretation, and lets you add passes without changing grammar classes); Iterator (traversal
  versus per-node operation; they pair).
- Where visitors still earn their keep (adaptation): compiler and AST libraries with visitor or walker
  APIs, lint-rule engines, annotation processors, file-system walkers, document exporters,
  serialisation, AST transforms. A visitor with dozens of methods most of which are empty is a smell.
- Return types: use a generic `Visitor<R>` rather than state fields for results (adaptation).

**Verify.**
- Exhaustiveness: every concrete element has a visit method in the base visitor (compile-time in
  sealed-type languages; in dynamic languages a test that enumerates the element classes).
- Each visitor is tested on small trees; a composite's accept visits each child exactly once in the
  documented order (pre or post).
- Adding an operation touches no element class.

---

## 7. The behavioural comparison discussion

Source: GoF ch. 5 closing discussion (the opening is summarised in `behavioral-1.md`) plus the Head
First chapters named above.

### 7.1 Encapsulating variation

Many behavioural patterns share a theme: define an object that encapsulates an aspect that changes
frequently and let other parts collaborate with it. Usually there are two kinds of object, the new
encapsulating object and the existing objects that use it; without the pattern the new functionality
would be wired into the existing objects (strategy code inside its context, state code inside its
context). Not all partition the system that way: Chain of Responsibility works with an arbitrary
number of objects, possibly already in the system, and its communication relationships are not static.

Design heuristic: identify what is likely to change and give it its own object behind an abstract
interface. This is HF's first principle (identify the aspects that vary and separate them from what
stays the same) and applies from the start, not only after pain (HF ch. 1 Q&A).

### 7.2 Objects as arguments

- Visitor is an argument to a polymorphic `accept`; it is not part of the visited objects, even though
  the conventional alternative distributes the code across the structure's classes.
- Command and Memento are tokens passed around and used later. A Command is a request; a Memento is an
  object's internal state at some time. Clients never see the complex internals. Polymorphism is
  central to Command; a Memento's interface is so narrow that it can only be passed by value.

### 7.3 Mediator vs Observer: encapsulate or distribute communication

| | Observer | Mediator |
|---|---|---|
| Where the interaction logic lives | distributed: emerges from how subjects and observers are wired | centralised: squarely in the mediator |
| Reuse | easier to make reusable subjects and observers (finer-grained classes) | harder to make a mediator reusable |
| Comprehension | wiring is made shortly after creation and hard to find later; the indirection makes the system harder to follow | easier to follow the communication flow in one place |
| Main risk | unexpected cascades; hard-to-trace wiring | monolithic "god" mediator |
| Typical shape | open-ended set of dependents, data-dependency propagation, subject must not know receivers | one cohesive rule set among a known group (dialog widgets) |

GoF adds that a Smalltalk programmer often uses Observer where a C++ programmer would use Mediator,
because observers can be parameterised with messages to read subject state: language features shift
the balance (the adaptation today is that closures make subscription cheap).

Decision rule: one cohesive set of interaction rules among a known group, Mediator, accepting the risk
of a monolith. Open-ended dependents, subject should not know receivers, Observer, accepting the risk
of cascades. In distributed systems the same split appears as orchestration (Mediator) versus
choreography (Observer) (adaptation).

### 7.4 Decoupling senders and receivers: Command, Observer, Mediator, Chain

Direct references between collaborating objects create dependencies that hurt layering and reuse. Four
patterns decouple them differently (GoF ch. 5):

| Pattern | How decoupled | Trade-offs and when |
|---|---|---|
| Command | A command object binds sender to receiver; the sender calls only `execute` | Sender reusable with different receivers; a command can parameterise a receiver with different senders. Nominally a subclass per binding (avoidable with templates or closures). Single receiver, explicit binding. |
| Observer | The subject signals changes through a fixed Subject/Observer interface | Looser than Command: several observers, number varies at run time. Interface designed for communicating changes, so best for data dependencies. |
| Mediator | Objects refer to each other only through the mediator, which routes requests and centralises communication | Fixed interface may need its own dispatch scheme (encoded requests, packed arguments) for an open-ended set of operations; reduces subclassing by centralising behaviour; ad hoc dispatch decreases type safety. |
| Chain of Responsibility | The request is passed along a chain of potential receivers | Also a fixed interface and maybe custom dispatch, with the same type-safety drawback. Good when the chain is already part of the structure and one of several objects may be positioned to handle the request; the chain is easy to change. Receipt not guaranteed. |

### 7.5 State vs Strategy vs Template Method vs Factory Method

State and Strategy have essentially the same class diagram. The difference is intent and who drives the
change (HF ch. 10 calls them "twins separated at birth" and runs the fireside chat; GoF State and
Strategy pages).

| | Strategy | State |
|---|---|---|
| Who picks the object | the client, usually at construction, and it normally stays | the context moves itself through states over time |
| Transitions | none among strategies | well-defined transitions; each state may name its successor |
| Do the objects know each other | no: algorithms are independent | states often know their successors |
| What the client sees | a configured algorithm | one object that seems to change class |
| Heuristic | client picks, it stays: Strategy | object moves itself through a defined set: State (a State is a Strategy that swaps itself) |

"Can change at run time" does not distinguish them, since both use composition and delegation.

Template Method versus Strategy: Template Method uses inheritance to vary part of an algorithm; the
skeleton is fixed, binding is at compile time and per class; shared code lives in the superclass (no
duplication), it needs fewer objects, it is ideal for frameworks, and subclasses depend on the
superclass's step implementations. Strategy uses composition to vary the entire algorithm at run time
per object; it is more flexible and independent of other classes, but may duplicate code among
strategies (HF ch. 8 fireside chat). Prefer Strategy or closures when the variation must change at run
time, when you would otherwise need a subclass per combination, or when the base class is not yours;
prefer Template Method when the skeleton and its invariants must be enforced and subclassing is
natural, as in frameworks.

Matching (HF ch. 8, ch. 10): Template Method, subclasses decide how to implement steps; Strategy,
encapsulate interchangeable behaviours and use delegation to choose; State, encapsulate state-based
behaviour and delegate to the current state; Factory Method, subclasses decide which concrete classes
to create.

Related, Decorator vs Strategy (skin versus guts) in section 4 and in `structural.md`.

### 7.6 Visitor vs sum types vs methods on classes: choose by the axis of change

Two axes: the set of variants (node kinds) and the set of operations. Ask which one grows.

| Your code grows mostly by | Prefer |
|---|---|
| new operations over a stable set of variants | Visitor, or functions with an exhaustive match over a sum type |
| new variants over a stable set of operations | methods on the classes (ordinary polymorphism) |
| both | an accepted cost either way; consider dispatch tables or multimethods; do not pick Visitor to avoid thinking about it |

In languages with sealed types and pattern matching (ML family, Rust, Kotlin, Swift, Scala, TypeScript
discriminated unions, Java sealed interfaces with switch patterns) a visitor is usually an exhaustive
match: a new operation is a new function; a new variant makes the compiler flag every non-exhaustive
match. That is the same trade-off as Visitor (the "expression problem"). Languages with multimethods
or single-dispatch libraries give double dispatch directly. (Adaptation of the notes' modern-language
remarks.)

### 7.7 Quick chooser for all eleven behavioural patterns

- Many conditionals on a mode flag that changes over the object's life: State. The same conditionals
  choosing an algorithm the client picks: Strategy. A fixed skeleton with a few overridable steps in
  a class hierarchy: Template Method.
- Need to queue, log, undo or schedule operations: Command (plus Memento for state).
- Need to walk a collection without exposing it: Iterator. Many operations over a stable heterogeneous
  structure: Visitor.
- Need to notify unknown dependents: Observer. Coordinate a known cluster: Mediator. Route a request to
  whoever can handle it: Chain of Responsibility.
- Need to evaluate sentences of a small language: Interpreter.
- Modern lens (adaptation): many of these collapse to first-class functions (Strategy, Command,
  Template Method, Observer callbacks, internal Iterator), sum types (State, Interpreter, Visitor),
  generators (Iterator) and middleware (Chain). Keep the vocabulary and the decision criteria and drop
  the class scaffolding when a function or enum says it more directly. Details in `modern-idioms.md`.

### 7.8 Review questions

1. Is the thing that varies named and isolated behind an interface, and who chooses the variant: the
   client, the object itself over time, or a subclass?
2. If a state variable is tested in more than one method, is State (or a transition table or sum type)
   missing? If a type code selects an algorithm, is Strategy missing?
3. If notifications exist, can the subject's state be read consistently at notification time, and can
   observers be removed, including from inside a callback?
4. Does the base class of a template enforce its sequence, and are the hooks documented?
5. Which axis grows, operations or variants? Does the chosen mechanism make that axis cheap?
6. Does any mechanism here (chain, mediator, observer list) have a defined behaviour when nobody
   handles the request, an observer throws, or the colleagues form a cycle?
