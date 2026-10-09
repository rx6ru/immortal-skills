# Temporal coupling, workflow and coordination

Sources: Pragmatic Programmer ch. 5 ("Temporal Coupling", "Blackboards", tips 39, 40, 41, 43); Clean Code ch. 13 (dependencies between calls). Inferred items are marked.

## Contents
1. What temporal coupling is
2. Finding real parallelism: workflow analysis (tip 39)
3. Services and the hungry-consumer model (tip 40)
4. Making state valid at every point (tip 41)
5. Hidden global state and call-again protocols
6. Blackboards (tip 43)
7. Warning signs and checks

## 1. What temporal coupling is

Time has two aspects in design: concurrency (things at the same time) and ordering (relative position in time). Linear thinking ("do this, then always that") creates temporal coupling: method A must be called before B; only one report at a time; wait for the redraw before handling the click. It is not flexible and not realistic (Pragmatic Programmer ch. 5).

Two kinds to look for:
- **Ordering coupling**: correctness depends on call order that the type system does not enforce (`init()` after constructor, `open()` before `read()`).
- **Needless serialisation**: steps run one after another purely by habit, though no data or resource dependency forces the order.

## 2. Finding real parallelism: workflow analysis (tip 39)

Procedure:
1. List the activities of the workflow (a user flow, a build, a data pipeline, an agent plan).
2. Draw each as a node; draw an arrow from A to B only if B needs A's output or a resource A holds. Use a synchronisation bar where several actions must finish before the next starts.
3. Every action with no incoming arrow can start at once. Everything between the same pair of bars can run in parallel.
4. Justify every serial edge with a real dependency; delete the rest.

Worked example from the notes: making a blended drink has 12 serial steps as people describe it, but the actual dependencies let five top-level tasks (open blender, open mix, measure rum, get glasses, get umbrellas) start up front; three more run in parallel after that; only closing, liquefying, opening and serving are inherently serial. People describe and perform things serially even when no dependency exists.

Adaptation for an agent: the same graph applies to independent tool calls, file edits and test runs; batch independent reads together. Edits to the same file are a shared resource and are serial.

Verify: the graph exists (even as a list); each serial edge names its dependency; only then add parallelism, with the measurements from `design-principles.md` section 1.

## 3. Services and the hungry-consumer model (tip 40)

The notes' example: an on-line transaction system with input tasks (one per communication line), an application-logic queue, application servers, a database queue and a database handler. Processes communicate through work queues; requests are asynchronous (an input task returns to monitoring its line at once; the application server is notified when the database transaction completes). Constraints that drove it: database operations are slow and must not block the communication lines; the database degrades with too many concurrent sessions; many transactions are in flight per line.

**Hungry consumer**: instead of a central scheduler assigning work, N independent consumers pull from one shared work queue. If one bogs down, the others take up slack; each proceeds at its own pace. It is quick and rough load balancing, and the components are decoupled in time. The notes report that this temporal decoupling made the system easier to write, not harder.

A service here is an independent, concurrent object behind a well-defined, consistent interface.

When to use: uneven task cost, many consumers, a shared slow resource that needs a concurrency cap (the cap is the number of consumers).
When not: work needing strict global ordering; request-reply flows where the sender needs the specific answer from a known service (the cost of asynchrony outweighs the gain).
Checks: the queue is concurrency-safe and bounded; end-of-stream or shutdown is defined; a stress test with uneven task durations shows no consumer idle while work waits (inferred).

## 4. Making state valid at every point (tip 41)

Threads impose useful constraints that also fight programming by coincidence:
- Global and static variables must be protected from concurrent access: ask why the global exists.
- State must be consistent whatever the call order. Ask "when is it valid to query this object?" If it is invalid between certain calls, you depend on the coincidence that nobody can call then.
- The widget example: create and then show in two steps, state not settable until shown. In a concurrent system another thread can touch the widget in between. Symptom: a class with a constructor and a separate `init()` where the constructor does not leave the object initialised.

Remedy: establish class invariants (design by contract; see `craft-error-handling`) so that the object is valid at every point it can be called; prefer constructors, factories or builders that fully initialise. When a fixed order is genuinely needed between steps, do not leave it implicit: chain each step's output into the next step's argument (`g = step_a(); s = step_b(g); step_c(s)`), so out-of-order calls cannot be written (Clean Code ch. 17, G31). The notes accept the extra syntax because it exposes the true ordering. Where ordering cannot be avoided, encode it in types (a `Connected` value that only exists after connect) or in a builder (adaptation).

## 5. Hidden global state and call-again protocols

The notes' example is the C tokenizer whose first call takes the string and later calls take NULL: hidden static state, not thread safe, mutates its input, and cannot tokenise two strings at once even in one thread (interleaved calls clobber each other). The Java tokenizer object holds its own state, so two instances work independently.

Principle: a "call it again with NULL" or "call reset first" protocol is temporal coupling. Return an iterator or handle that holds the state, so each use has its own. Examples today (adaptation): module-level parsers with `current_position`, global "current user" or "current transaction" variables, singletons with mutable data.

## 6. Blackboards (tip 43)

A blackboard lets producers and consumers of knowledge be completely decoupled, anonymous and asynchronous, and reduces code. Detectives around a board: none needs to know others exist; they watch and add findings; people come and go.

Operations in the tuple-space lineage the notes describe: read (search/retrieve), write (put an item), take (read and remove), notify (callback when a matching item is written); retrieval by partial-field match or subtype. Large blackboards get cluttered; partition them into zones or a hierarchy.

Example: a loan application. Data arrives in unpredictable order and from different offices and systems; some data depends on other data; new data raises new policies. A fixed workflow engine must be rewired when regulations change. Blackboard plus a rules engine: posting a fact triggers applicable rules, and rule outputs post back and trigger more rules. Order of arrival is irrelevant.

Modern equivalents (inferred): message topics and queues, shared stores with change feeds, event-sourced systems, a shared scratchpad in a multi-agent system.

Good fit: parallel workers taking chunks and writing results; asynchronous participants with differing availability; agents watching a stream and posting conclusions.
Poor fit (inferred): tightly ordered low-latency request-reply; designs where tracing a chain of anonymous reactions costs more than the coupling it removes.

Checks (inferred): every participant can be tested by posting facts to a test board; conclusions are traceable back to the facts and rules that produced them (log them); no circular rule chains without a termination condition.

## 7. Warning signs and checks

Warning signs (inferred from the text):
- Comments or docs saying "must call X before Y".
- Objects with `init()` or `open()` required before other calls.
- Module-level mutable state; singletons holding mutable data.
- Serial scripts whose independent steps run in sequence by habit.
- A central scheduler that is a bottleneck.

Checks (inferred):
- Run tests with calls reordered, repeated and interleaved: two instances in one thread, then two threads.
- Review: can every public method be called in any order without corrupting state, or do types or invariants prevent invalid orderings?
- Draw the activity graph; each serial edge must be justified by a real data or resource dependency.
