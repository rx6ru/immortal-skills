# Compound patterns, combining patterns, and MVC

Sources: HF ch. 12 (Compound Patterns: the duck simulator and MVC), ch. 13 Q&A; GoF ch. 1 (1.2 MVC in Smalltalk), ch. 2 (Lexi), ch. 3 discussion (relationships), ch. 6 (parting thought). Items marked "(adaptation)" or "(inferred)" are not claims of the books.

Contents
1. Definitions: compound pattern versus patterns used together
2. Combining patterns one requirement at a time (the duck simulator)
3. Interplay rules when patterns touch
4. MVC as a compound pattern
5. Worked MVC example: the DJ beat controller
6. Adapting a model to an existing view and controller
7. MVC questions the book answers
8. MVC on the web and in modern UI architectures
9. Procedure: designing a UI feature with MVC
10. Smells and verification
11. Combinations the GoF book shows
12. Density, not accumulation

## 1. Definitions: compound pattern versus patterns used together

- "Patterns are often used together and combined within the same design solution." (HF ch. 12)
- A compound pattern combines two or more patterns into a solution that solves a recurring or general problem.
- Key distinction (HF Q&A): a set of patterns that merely works together in one design (the duck simulator) is not a compound pattern. A compound pattern is a general-purpose, reusable combination applied to many problems. MVC is the example. Do not call a one-off combination a compound pattern.

Warning from the same Q&A: it is "wrong" to treat design as taking a problem and applying patterns until you have a solution. The duck design is forced and artificial, parts are overkill, and sometimes plain OO principles are enough. Apply patterns where they make sense, never to use patterns.

## 2. Combining patterns one requirement at a time (the duck simulator)

Start: a `Quackable` interface with `quack()`, implemented by `MallardDuck`, `RedheadDuck`, `DuckCall`, `RubberDuck`; the simulator calls `simulate(Quackable)` polymorphically. Each new requirement then picks one pattern.

| # | Requirement | Pattern | Move |
|---|---|---|---|
| 1 | Geese (which `honk()`) must be usable wherever a `Quackable` is expected | Adapter | `GooseAdapter implements Quackable`, holds a goose; `quack()` calls `goose.honk()` |
| 2 | Count total quacks without changing duck classes | Decorator | `QuackCounter implements Quackable`, wraps one, delegates `quack()`, then increments a counter. Geese deliberately left undecorated (the ranger did not want honks counted) |
| 3 | Decoration is lost if someone forgets to wrap | Abstract Factory | `AbstractDuckFactory` with creation methods per duck kind; one concrete factory makes plain ducks, another returns each wrapped in `QuackCounter`. Rationale: "you have to make sure they get wrapped", so localise creation and decoration in one place |
| 4 | Manage many ducks and sub-families as a group | Composite (with Iterator) | `Flock implements Quackable`, holds a list of `Quackable`, `add()`, and `quack()` iterates the children. Flocks can contain flocks |
| 5 | Be notified in real time when any individual duck quacks | Observer | `QuackObservable` (register, notify); `Quackable` extends it; a helper `Observable` holds the observer list and is composed into each duck, which delegates to it so registration code is not repeated in every class |

The method to copy: for each new requirement, ask which single variation it adds. A foreign interface is Adapter; an added behaviour layer is Decorator; "someone forgot to wrap" is a factory; grouping is Composite; change notification is Observer. Check that each addition is justified, not decorative. The final design uses six patterns (Adapter, Decorator, Abstract Factory, Composite, Iterator, Observer).

## 3. Interplay rules when patterns touch

| Interplay | Rule | Source |
|---|---|---|
| Decorator and Observer | A decorated object must remain observable: the wrapper delegates `registerObserver` and `notifyObservers` to the wrapped duck (exercise) | HF ch. 12 |
| Observer on a Composite | Observing a composite means observing all its members: `Flock.registerObserver` registers the observer on each child, recursively for sub-flocks; `Flock.notifyObservers` is empty because each child notifies for itself | HF ch. 12 |
| Composite safety versus transparency | Here only `Flock` has `add()`, so you cannot add to a duck (safe), but clients must know a `Quackable` is a flock to add (less transparent). The Composite chapter chose transparency (the same methods on leaf and composite). A real trade-off to choose consciously | HF ch. 12 and 9 |
| Wrapping needs a factory | Wrapped objects only work when something guarantees they are wrapped; put the wrapping in a factory or builder | HF ch. 3, 12 |
| Adapter in a hierarchy | Adapters implement the target interface and delegate; the client treats an adapted object like any other | HF ch. 12 |
| Abstract Factory with new products | Adding a product kind (`createGooseDuck()`) either extends the existing factories or creates a separate factory; choose by whether the new kind belongs to the same family | HF ch. 12 exercise |
| Factory and Singleton | A concrete factory is often a singleton; prefer injecting a single instance (creational.md) | GoF ch. 3 |
| Builder builds Composite | Builder often builds a composite tree | GoF ch. 3 |
| Prototype with Composite and Decorator | Cloning pre-built structures helps heavy users of those two | GoF ch. 3 |
| Factory Method inside Template Method | The creator's workflow is a template; the factory method is its hook | GoF ch. 3 |

## 4. MVC as a compound pattern

HF thesis: learning MVC from the top down is hard; it is "just a few patterns put together". GoF 1.2 makes the same point from Smalltalk: Model (the application object), View (presentation), Controller (reaction to input). The model-view subscribe-and-notify protocol generalises to Observer; nested views are Composite; the view's controller is a Strategy that can be swapped at run time (for instance, a controller that ignores input disables a view). GoF also notes Factory Method (the default controller class a view creates) and Decorator (scrolling added to a view).

### Roles (HF ch. 12)

- Model: holds all data, state and application logic. Oblivious to view and controller, but exposes an interface to read and change its state, and notifies observers of changes.
- View: the presentation of the model; usually pulls the state it shows from the model.
- Controller: takes user input and works out what it means to the model; translates user actions into model operations; may also tell the view to change (for instance, enabling or disabling controls).

### Interaction sequence

1. The user acts on the view; the view tells the controller.
2. The controller asks the model to change state.
3. The controller may also ask the view to change.
4. The model notifies the view that its state changed, whether because of the user's action or an internal change.
5. The view asks the model for state and updates itself.

### The patterns inside MVC

| Pattern | Where | Effect |
|---|---|---|
| Observer | the model is the subject; views (sometimes controllers) register as observers | keeps the model independent of views and controllers; several views on one model; add views without editing the model |
| Strategy | the view is configured with a controller; the controller is the view's strategy for handling user actions | swap the controller to change behaviour without touching the view; the view stays decoupled from the model's mutators because the controller interacts with it |
| Composite | the view is a tree of nested windows, panels, buttons and labels | telling the top component to repaint propagates downward |

Dependency summary: the model depends on nobody; the view depends on the model (reads state) and on the controller (strategy); the controller depends on the model and the view. The invariant that carries across every variant: the model does not know the view.

## 5. Worked MVC example: the DJ beat controller

- Model interface: `initialize`, `on`, `off`, `setBPM`, `getBPM` (0 if off), plus registration for two observer kinds: beat observers (every beat) and BPM observers (BPM change). The model runs a thread that plays a clip, notifies beat observers and sleeps `60000 / bpm` milliseconds.
- View: implements both observer interfaces, registers in its constructor, holds the model and the controller. Handlers for buttons and menus only call controller methods. `updateBPM()` calls `model.getBPM()` (pull); `updateBeat()` pulses the bar.
- Controller: constructed with the model, creates the view, calls model methods, and makes the "intelligent decisions" for the view: after start, disable the Start item and enable Stop. The view knows how to enable or disable items, not when. `increaseBPM` is `model.setBPM(model.getBPM() + 1)`. The controller interface is richer than the model's.
- Wiring: `new BeatController(new BeatModel())`; the controller creates the view.
- Observation: after pressing increase, the display updates although the view has no direct link from control to display. The change round-trips through the model and the notification.

Sketch (TypeScript), showing the dependency directions:

```ts
class BeatModel {                       // knows nothing about views
  private bpm = 0; private observers = new Set<() => void>();
  subscribe(fn: () => void) { this.observers.add(fn); return () => this.observers.delete(fn); }
  getBpm() { return this.bpm; }
  setBpm(v: number) { this.bpm = v; this.observers.forEach(fn => fn()); }
}
class BeatController {                  // translates intent into model calls
  constructor(private model: BeatModel) {}
  increase() { this.model.setBpm(this.model.getBpm() + 1); }
}
class BeatView {                        // pulls state from the model on notification
  constructor(private model: BeatModel, private controller: BeatController, private render: (bpm: number) => void) {
    model.subscribe(() => this.render(model.getBpm()));
  }
  onIncreaseClicked() { this.controller.increase(); }
}
```

## 6. Adapting a model to an existing view and controller

`HeartModel` offers `getHeartRate` and observer registration, with a different interface from the beat model's. `HeartAdapter implements` the beat model interface: `getBPM` returns `heart.getHeartRate()`, observer registration delegates, and `on`, `off`, `setBPM` and `initialize` are no-ops ("we don't know what these would do to a heart"). A `HeartController` creates the same view with the adapter and disables start and stop items. The view is reused unchanged. Rule of thumb from the book: use an adapter to adapt a model to work with existing controllers and views. Remaining wart: other buttons still render but do nothing; the view could be changed to support disabling them.

To expose only a subset of the model's API to the view, use Adapter to adapt the model to a narrower interface (the book's hint).

## 7. MVC questions the book answers

| Question | Answer |
|---|---|
| Can the controller observe the model? | Yes in some designs, for example when model state decides which controls are enabled; the controller then asks the view to update |
| Why a controller, not that code in the view? | The view would get two responsibilities (UI plus control logic) and become tightly coupled to the model, killing reuse of the view with another model |
| Does the controller hold application logic? | No. It translates view actions into model calls, possibly choosing which; the logic that manages data lives in the model |
| Is "state" the State pattern? | No, only the general idea; a model might use State internally |
| Is the controller a Mediator? | To a degree: the view never sets model state directly. But the view also holds the model to read, so not a true mediator |
| Push or pull? | The model could send state in the notification (push); HF ch. 2 calls pull the more "correct" choice, and better when the subject's data set may grow. Many web adaptations deviate |
| How many controllers? | Typically one per view at run time, but one controller class can manage many views |

## 8. MVC on the web and in modern UI architectures

HF ch. 12: MVC is adapted in many web frameworks (Spring Web MVC, Django, ASP.NET MVC, AngularJS, Ember, Backbone). Thin client: model, most of view and controller on the server, the browser displays and relays input. Single-page app: nearly everything on the client. Hybrids share parts. Each framework maps M, V and C differently across client and server; knowing the underlying patterns lets you adapt.

Adaptation (the notes mark the mapping as general rather than from the book): MVP and MVVM keep the Observer-based data binding with a presenter or view-model in place of the controller; a Redux-style store is the model and a subscription is the observer. Frameworks vary in who observes whom and in push versus pull. Modern GUI toolkits and browsers hide the Composite structure of the view, so it is harder to see than when MVC was invented.

## 9. Procedure: designing a UI feature with MVC (derived from the chapter)

1. Put state and rules in a model with no UI imports and give it a subscription mechanism.
2. Have views subscribe and re-read the state they need (pull) when notified.
3. Route user events to a controller object behind an interface; the controller calls model methods and decides which controls should be enabled.
4. Keep domain rules in the model. If the controller grows rules, move them.
5. When a new model must feed an existing view, adapt the model interface rather than editing the view.
6. Wire the pieces at one place (the composition root or the controller's constructor, as in the DJ example).

## 10. Smells and verification

Smells (inferred in the notes, from the roles):
- The model references view classes.
- The view contains business rules or calls persistence.
- A fat controller holds domain rules.
- Notification loops: an observer that mutates the model on every update.
- A view wired to a concrete model class instead of an interface (blocks the HeartAdapter-style reuse).

Verification tests:
- The model can be unit tested headless (no UI import in its module). Check imports.
- Two different views can be attached to one model, and both update.
- Swapping the controller needs no edits to the view.
- Removing a view's subscription stops its updates (no leak); order of notifications is not relied on.
- After a user action, the view's display is produced by the notification path, not by the controller writing to the view directly (unless it is a control-enable decision).
- A fake model implementing the model interface drives the view in a test.

When combining patterns in other settings: for each pattern in the combination, state the single requirement that introduced it; delete any whose requirement cannot be named.

## 11. Combinations the GoF book shows

- Lexi: Composite for structure, Strategy for formatting, Decorator for embellishment, Abstract Factory for look and feel, Bridge for window systems (with Abstract Factory choosing the implementor), Command for operations and undo, Iterator for traversal, Visitor for analyses. The summary claim is that none is editor-specific: a portfolio tree is Composite, register-allocation schemes in a compiler are Strategy, and any GUI application likely uses Decorator and Command.
- Creational relationships: Abstract Factory by Factory Methods or Prototypes; concrete factories as Singletons; Builder building a Composite.
- Composite with Iterator and Visitor: the iterator walks the tree, the visitor does the work at each node (the iterator separated from the action so many analyses reuse one traversal).

## 12. Density, not accumulation

GoF ends with Alexander's thought: stringing patterns together loosely gives an "assembly of patterns", not something dense or profound; overlapping many patterns in the same space gives density. The best designs use many patterns that dovetail and intertwine. For an agent this means: a pattern should serve more than one need in the design (Observer in MVC serves both view updates and independent reuse of the model), and a pattern that serves nothing but itself should be removed (using-patterns-well.md).
