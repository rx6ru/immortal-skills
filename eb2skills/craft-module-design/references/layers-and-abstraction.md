# Layers and abstraction

How to decide whether a layer, wrapper or forwarded parameter earns its place, and where
cross-cutting behaviour should live.

Contents
1. The rule
2. Pass-through methods
3. When the same signature is fine
4. Decorators and wrappers
5. Interface versus implementation
6. Pass-through variables and context objects
7. Layering for orthogonality
8. Cross-cutting concerns
9. Reconciling the sources on wrappers
10. Verification

## 1. The rule (APOSD ch. 7)

In a well-designed system each layer offers a different abstraction from the layers above and below
it. Follow one operation down through the calls and the abstraction should change at each step. A
file system shows it: files as variable-length byte sequences on top, a cache of fixed-size blocks
in the middle, device drivers moving blocks at the bottom. So does a transport protocol: a reliable
byte stream above, best-effort packets below.

Adjacent layers with similar abstractions are a red flag about the decomposition. The symptoms are
pass-through methods, shallow decorators, pass-through variables and an interface that mirrors the
implementation.

Underlying economics: every piece of design infrastructure (an interface, an argument, a function,
a class) adds complexity. It should remove more than it adds, or go.

## 2. Pass-through methods

A pass-through method does little except invoke another method with the same or a similar
signature. The notes' example: a document class with fifteen public methods, thirteen of which only
forwarded to a text-area class.

Harm:

- It widens the class's interface without adding functionality, making it shallower.
- It creates a dependency: change the callee's signature and the wrapper changes too.
- It signals a confused division of responsibility. The interface to a piece of functionality
  should be in the class that implements it.

Remedies, pick one:

- Expose the lower-level class directly to the callers; the higher class gives up responsibility
  for that feature.
- Redistribute functionality between the classes so they no longer call each other for it.
- Merge the classes if they cannot be disentangled.

The question to work from: exactly which features and abstractions is each of these classes
responsible for? Overlap will show.

A forwarding method is doing real work if it adds validation, translation, dispatch, caching,
locking, or presents a different level of abstraction.

At application scale the same shape appears as controller, service and repository layers with
identical signatures that each only call the next (the notes mark this generalisation as inferred).
Apply the same test before adding or keeping such a layer.

## 3. When the same signature is fine

A repeated signature is acceptable when each method contributes significant, distinct functionality.

- Dispatcher: chooses one of several methods based on its arguments and calls it. It has the
  targets' signature and does real work, the selection.
- Several implementations of one interface (device drivers, polymorphic subclasses). The shared
  signature lowers cognitive load, because learning one teaches the rest. These methods usually sit
  in the same layer and do not call each other.

## 4. Decorators and wrappers

A decorator wraps an object, presents a similar or identical interface, and forwards calls while
adding behaviour. The motive is to keep special-purpose extensions apart from a generic core. The
problem is that decorators tend to be shallow: much forwarding boilerplate for a little new
functionality, and easy to multiply into a pile of thin classes.

Before writing one, consider in order:

1. Add the functionality directly to the underlying class. Right when it is fairly general,
   logically related to the class, or used by most of its users.
2. If it is specific to one use case, merge it into that use case instead of creating a class.
3. Merge it into an existing decorator, giving one deeper decorator instead of several shallow ones.
4. Ask whether it must wrap at all. It may work as an independent class (scroll bars separate from
   the window they scroll).

The book's summary is that decorators sometimes make sense but there is usually a better
alternative. The notes observe that this contrasts with pattern-catalogue enthusiasm; for the
pattern itself see `craft-design-patterns`.

## 5. Interface versus implementation

A class's interface should normally differ from its internal representation. If they look alike the
class is probably shallow.

Example: a text class stored as lines. Exposing a line interface (get a line, put a line) forces
the UI to split and join lines for mid-line inserts and multi-line deletes, and that code gets
duplicated across the UI. A position-and-range interface keeps lines internal. The distance between
the interface and the storage is the functionality the class provides.

Design question: what is the internal representation, and is the interface deliberately at a higher
level than it? If they match, check whether the class is a veneer.

## 6. Pass-through variables and context objects

A pass-through variable is handed down a chain of functions that do not use it, to reach one that
does. The notes' example is a certificate setting read in `main` and needed only by a low-level
function that opens a socket, which therefore appears in every signature in between.

Harm: every intermediate function has to know about it, and adding another such variable means
editing every path again.

Options:

| Option | Assessment |
|---|---|
| Store it in an object the top and bottom already share | Good when such an object exists; it may itself be a pass-through |
| Global variable | Avoids passing but almost always causes other problems; in particular it prevents two independent instances in one process, which tests need |
| Context object | The book's preferred choice, with admitted downsides |

Context object: one object per system instance holding application-wide state (configuration
options, shared subsystems, counters, timeouts). Major objects keep a reference to it; an object
creating another passes its context to the constructor, so the context appears explicitly only in
constructors. Adding a new piece of global state changes only the context class. Tests can build a
context with altered fields.

Its downsides, stated by the author: it has most of the disadvantages of globals (not clear why a
field is there or who uses it); without discipline it becomes a grab-bag with hidden dependencies;
and it raises thread-safety issues, best handled by making its contents immutable. He reports not
having found a better solution.

Practical rule: when data is needed deep in a call stack but not in the middle, first look for an
existing shared object; otherwise a context that is initialised once, immutable, and limited to
truly system-wide items. Not a global, and not a new parameter on every intermediate function.

Adaptation (inferred in the notes): request-scoped values such as user, tenant, trace id or
deadline are the same problem. Go's `context.Context`, request-scoped objects and
dependency-injection containers are forms of the context object and carry the same grab-bag risk.
Pragmatic Programmer ch. 2 gives compatible advice from the other side: avoid global data, pass
context explicitly through constructor parameters or context structures, and be wary of singletons
used as disguised globals.

```python
# threaded through functions that do not use it
def handle(req, tls_cert): return route(req, tls_cert)
def route(req, tls_cert):  return fetch_upstream(req.path, tls_cert)

# held by the object that needs it; wired once at construction
class Upstream:
    def __init__(self, settings: Settings): self._cert = settings.tls_cert
    def fetch(self, path): ...
```

## 7. Layering for orthogonality (Pragmatic Programmer ch. 2)

Layers are one way to get orthogonality: each layer uses only the abstractions of the layer below,
so a change behind an abstraction does not reach upward. The check: if the requirements behind one
function change dramatically, how many modules are affected? The ideal answer is one. Swapping a
graphical interface for a voice interface should touch only the interface modules, with both
sharing one core.

APOSD ch. 9 adds the direction of specialisation: lower layers tend to be general-purpose and upper
layers special-purpose, so special-purpose code should be pulled upward, towards the module
associated with that purpose.

Physical structure matters as well as logical structure (Pragmatic Programmer ch. 5, sidebar):
file, directory and library relationships determine build times and what a unit test drags in, and
cyclic dependencies are very hard to undo later. Depend on declarations or interfaces instead of
full definitions where the language allows. The appendix exercise makes the point with a header
that includes another to hold a value, versus one that forward-declares the type and holds a
pointer; the second is less coupled. The C++ detail is dated; import and package hygiene is the
general form.

## 8. Cross-cutting concerns (Clean Code ch. 11; Pragmatic Programmer ch. 2)

Some concerns cut across natural module boundaries: persistence, transactions, security, caching,
failover, logging. Each can be modular on its own; the trouble is the fine-grained intersection,
which tends to become the same code pasted into many methods.

The approach both books recommend is to keep business code free of the concern and attach it from
outside:

- Declare where the behaviour applies in one place, and have a mechanism apply it without editing
  the target code. In Java terms this was aspect-oriented programming, done through proxies,
  container configuration or annotations; the notes list the options in rising power (dynamic
  proxies, pure-Java AOP frameworks, annotation-based persistence, a full aspect language) and the
  rule to start with plain objects plus the lighter mechanism and reach for the heavy one only when
  the lighter cannot express the concern.
- The value is the concise, modular statement of system-wide behaviour, not the proxy machinery.
- Whatever mechanism adds the behaviour, make it reversible: what is added automatically can be
  removed automatically (Pragmatic Programmer ch. 2).

Adaptation: in current ecosystems the equivalents are middleware and interceptors, function
decorators, annotation-driven frameworks and wrappers composed at the wiring point. The durable
rule is to keep domain objects free of infrastructure imports and add cross-cutting behaviour by
wrapping, not by editing.

The framework side of the same idea: if domain logic must inherit from or implement framework
types, a framework change is a domain change and tests need the framework. That was the failure of
the early container the chapter criticises. Annotations on domain entities still couple the domain
to the persistence library; the chapter accepts that as much less harmful and notes the mapping can
be moved to external configuration.

## 9. Reconciling the sources on wrappers

Three positions sit close together and can look contradictory.

- APOSD: forwarding methods and decorators are usually shallow; avoid them.
- Clean Code ch. 11: nest decorators around a plain business object to add persistence,
  transactions and the like.
- Pragmatic Programmer ch. 5 and Clean Code ch. 6: to avoid reaching through an object, add a
  method on the near object that delegates.

They agree once you ask what the wrapper adds:

| Wrapper | Keep it when | Remove it when |
|---|---|---|
| Delegating method for Demeter | It states the caller's intent at the near object's level and hides where the answer comes from | It mirrors the far object's method one for one and the far object is really what the caller works with |
| Decorator | The behaviour is cross-cutting, applies uniformly to many operations, and would otherwise be duplicated in business code; ideally generated or generic so there is no hand-written forwarding | It adds one feature most users want (put it in the class) or one use case needs (put it there) |
| Layer (service, facade, repository) | It offers a different abstraction, enforces a rule, or is the single point of contact with a vendor | Each method forwards with the same signature |
| Adapter at a boundary | It translates your interface to a vendor's and is the only place vendor types appear | It only renames the vendor's methods and exposes the vendor's types anyway |

## 10. Verification

- Forwarding ratio: list a class's public methods whose body is a single call with the same
  arguments. The notes offer "more than a few is a flag" as an inferred threshold; the bad example
  was thirteen of fifteen.
- Deletion test: remove the method and let callers call the target directly. If no logic
  disappeared, it was a pass-through.
- Lockstep test: change a callee's signature. If wrappers must change with it and contain no logic,
  they are pass-throughs.
- Layer sentence (inferred): state in one sentence how this layer's abstraction differs from the
  one below. If you cannot, the layers are redundant.
- Parameter trace: for each parameter, confirm the function uses it other than to forward it.
- Context audit: the context object is constructed once, is immutable, and holds only system-wide
  items; a test can run two instances in one process.
- Interface versus storage: the public interface does not mirror the internal data layout.
- Cross-cutting scan: search business methods for repeated transaction, auth, logging or cache
  boilerplate; search domain modules for framework or infrastructure imports.
- Dependency graph: no cycles between packages; arrows point from upper layers to lower ones.
