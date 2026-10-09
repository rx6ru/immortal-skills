# Catalogue: dealing with inheritance (Refactoring 2e ch. 12)

Inheritance is very useful and easy to misuse, and the misuse is often visible only in the rear-view mirror. These refactorings move features up and down a hierarchy, add and remove classes, and swap inheritance for delegation when it rubs badly.

Contents
- Decide which tool
- Pull Up Method / Pull Up Field / Pull Up Constructor Body
- Push Down Method / Push Down Field
- Replace Type Code with Subclasses
- Remove Subclass
- Extract Superclass
- Collapse Hierarchy
- Replace Subclass with Delegate
- Replace Superclass with Delegate
- Safety tactics

## Decide which tool

| Situation | Refactoring |
|---|---|
| Same method in sibling subclasses | Make bodies identical (Parameterize Function, Change Function Declaration), then Pull Up Method. Different flow, similar steps: Form Template Method |
| Same field in sibling subclasses | Pull Up Field (Rename Field first if names differ) |
| Constructors repeat assignments | Pull Up Constructor Body |
| Method or field used by only one or few subclasses | Push Down. If callers do not know the subclass, use polymorphism with placebo behaviour on the superclass instead |
| A type-code field drives behaviour or subclass-only data | Replace Type Code with Subclasses |
| A subclass does too little | Remove Subclass |
| Two classes do similar things | Extract Superclass (simpler) before Extract Class (delegation); switch later with Replace Superclass with Delegate if needed |
| A class and its parent no longer differ enough | Collapse Hierarchy |
| Inheritance rubs: second axis of variation, variant must change at runtime, coupling | Replace Subclass with Delegate |
| Inheritance is the wrong IS-A: inherited operations that make no sense, type-instance homonym | Replace Superclass with Delegate |

---

## Pull Up Method (inverse: Push Down Method)

Use when: duplicate methods in subclasses. Copies breed bugs (a change reaches one copy, not the other) and are hard to find. Easiest when bodies are identical. If they are not, look at the differences: they often reveal behaviour you forgot to test. Relying on tests croaking is "a lot of reliance on tests".

Complication: the body uses features that exist on the subclass but not the superclass; pull those up first (Pull Up Field, Pull Up Method).

Mechanics
1. Inspect the methods to ensure they are identical; if they do the same thing but are not identical, refactor until their bodies are.
2. Check that all calls and field references in the body are callable from the superclass.
3. If signatures differ, Change Function Declaration to the one you want on the superclass.
4. Create the method in the superclass and copy one body into it.
5. Static checks.
6. Delete one subclass method.
7. Test.
8. Keep deleting subclass methods until none remain.

Example: `Employee.annualCost` and `Department.totalAnnualCost` both `monthlyCost * 12`. Rename one, copy to `Party`, remove from each subclass. Dynamic languages need a trap on the superclass (`get monthlyCost() { throw new SubclassResponsibilityError(); }`); static languages declare it abstract.

## Pull Up Field (inverse: Push Down Field)

Use when: independently developed subclasses duplicate a field, perhaps under different names; only usage tells you. Pulling it up removes the duplicate declaration and lets behaviour that uses it move up.

Mechanics
1. Inspect all users to ensure they use it the same way.
2. If names differ, Rename Field to unify.
3. Create the field in the superclass, accessible to subclasses.
4. Delete the subclass fields.
5. Test.

## Pull Up Constructor Body

Use when: subclass constructors repeat assignments. Constructors have ordering rules, so Extract Function then Pull Up Method does not work directly. If it gets messy, consider Replace Constructor with Factory Function.

Mechanics
1. Define a superclass constructor if none exists, and make subclass constructors call it.
2. Slide Statements to move common statements to just after the super call.
3. Remove the common code from each subclass and put it in the superclass; pass to the super call any parameters the common code references.
4. Test.
5. If common code cannot move to the start, Extract Function then Pull Up Method.

Example: common code later in the constructor (`if (this.isPrivileged) this.assignCar()`, where `isPrivileged` depends on a subclass-assigned grade): extract `finishConstruction()`, pull it up, and have subclass constructors call it after setting their fields.

## Push Down Method / Push Down Field

Use when: a member is relevant to only one subclass or a small proportion. It must be possible for callers to know they hold that subclass.

Mechanics (method; field is the same shape)
1. Copy it into every subclass that needs it (field: declare it in those subclasses).
2. Remove it from the superclass.
3. Test.
4. Remove it from each subclass that does not need it.
5. Test.

## Replace Type Code with Subclasses

Subsumes Replace Type Code with State/Strategy and Extract Subclass; inverse of Remove Subclass.

Use when
- Kinds of a thing are coded as enum, string or number, and either (1) several functions behave differently by code (then follow with Replace Conditional with Polymorphism), or (2) some fields or methods are valid only for some values (create the subclass and Push Down Field; more explicit than validation logic).
- Most of the time a code alone is enough.

Direct versus indirect: subclassing the class itself is simpler. It is impossible if inheritance is already used for another axis (part-time and full-time) or if the type is mutable (the object must change type). Then go indirect: Replace Primitive with Object on the code, and subclass the new type class.

Mechanics
1. Self-encapsulate the type code field.
2. Pick a value; create a subclass for it; override the getter to return the literal.
3. Create selector logic mapping the code to the subclass. Direct: Replace Constructor with Factory Function and put the selector in the factory. Indirect: the selector may stay in the constructor.
4. Test.
5. Repeat for each value, testing after each.
6. Remove the type code field.
7. Test.
8. Push Down Method and Replace Conditional with Polymorphism on methods that use the type accessors. Once all are replaced, remove the accessors.

Example notes: do not put selector logic in a JS constructor; use a factory. Paranoid check: temporarily break a subclass's return value and see a test fail, proving the subclass is used. The factory's `default: throw` replaces separate type validation. Drop the now-useless `type` constructor parameter. In the indirect form a mutable `type` setter creates the right `EmployeeType` subclass; leave the empty base class, since it states the relationship and hosts shared behaviour.

## Remove Subclass (Replace Subclass with Fields)

Use when: subclasses support variation, but the variation moved elsewhere or vanished, or subclasses were added for features never built. A subclass that does too little costs more to understand than it is worth.

Mechanics
1. Replace Constructor with Factory Function on the subclass constructor.
2. If constructor callers use a data field to choose the subclass, put that logic in a superclass factory.
3. If code tests against the subclass's type, Extract Function on the test and Move Function to the superclass; test after each.
4. Create a field representing the subclass type.
5. Change methods that refer to the subclass to use the field.
6. Delete the subclass.
7. Test.
For a group, encapsulate all of them first, then fold in one by one.

Example: `Male` and `Female` subclasses of `Person` become a `genderCode` field. First check clients for subclass-dependent behaviour (none), encapsulate construction in `createPerson`, extract `isMale(p)` for the `instanceof` check (an `instanceof` test never smells good) and move it to `Person`, add the field, fold in one subclass at a time, and tidy the default so readers do not wonder.

## Extract Superclass

Use when: two classes do similar things. Pull the similarities up with Pull Up Field and Pull Up Method. Inheritance is often discovered during evolution, not planned from a real-world classification. Extract Class (delegation) is the alternative; start with the superclass knowing you can switch later.

Mechanics
1. Create an empty superclass; make the originals its subclasses.
2. If needed, Change Function Declaration on the constructors.
3. Test.
4. One by one, Pull Up Constructor Body, Pull Up Method, Pull Up Field.
5. Examine remaining subclass methods for common parts; Extract Function then Pull Up Method.
6. Check clients; consider switching them to the superclass interface.

Example: `Employee` and `Department` share `name` and costs, so `Party`. For `annualCost` against `totalAnnualCost`, ask whether they represent the same intent; if yes, unify names with Change Function Declaration, then pull up.

## Collapse Hierarchy

Use when: after pulling and pushing, a class and its parent no longer differ enough.

Mechanics
1. Choose which to remove, by which name makes more sense going forward.
2. Pull Up / Push Down fields and methods to get everything into one class.
3. Adjust references to the removed class.
4. Remove the empty class.
5. Test.

## Replace Subclass with Delegate

Use when: inheritance rubs badly.
- Only one axis of variation per hierarchy ("a card that can only be played once").
- Subclass and parent are tightly coupled; parent changes break children, worse across modules or teams.
- The object must change variant during its life (`aBooking.bePremium()`), rather than being rebuilt.
Delegation allows many delegates for many reasons through a regular object relationship with a clear interface. The result is the State or Strategy pattern.

Honest caveat from the book: this is a refactoring where the code is not improved by the move alone; delegation adds dispatch logic, back-references and complexity. The author reaches for inheritance first and switches to delegation when it rubs, and phrases the folk rule as "favor a judicious mixture of composition and inheritance".

Mechanics
1. If there are many constructor callers, Replace Constructor with Factory Function.
2. Create an empty delegate class; its constructor takes subclass-specific data and usually a back-reference to the host.
3. Add a field to the superclass for the delegate.
4. Modify subclass creation to initialise the delegate field (in the factory, or in the constructor if it can reliably tell).
5. Choose a subclass method to move.
6. Move Function it to the delegate; do not remove the source's delegating code (the subclass keeps a forwarder).
7. If the method needs elements that should move, move them; if they should stay, give the delegate the host reference.
8. If the source method has callers outside the class, move the subclass's delegating code up to the superclass, guarded by a check for the delegate's presence. If not, Remove Dead Code.
9. If there is more than one subclass and code is duplicating, Extract Superclass on the delegates. Then host methods need no guard if default behaviour moves to the delegate superclass.
10. Test.
11. Repeat until all methods of the subclass are moved.
12. Change all callers of the subclass constructor to the superclass constructor.
13. Test.
14. Remove Dead Code on the subclass.

Example 1 (`PremiumBooking`): encapsulate creation in factories, attach the delegate in the premium factory, move a simple override (`hasTalkback`) with a guarded dispatch in the host. An override that calls `super` (`basePrice`) cannot call the host's public getter from the delegate (infinite recursion): either extract a private base calculation the delegate calls, or recast the delegate method as an extension that receives the base result (slightly preferred, smaller). A subclass-only method (`hasDinner`) moves to the delegate and the host returns undefined when absent.

Example 2 (bird species hierarchy replaced so that wild/captive subclasses become possible): one subclass at a time, simplest first. A guarded `if (delegate) return delegate.plumage` fails because other delegates lack `plumage`. Rejected: an `instanceof` check on delegates ("almost never a good idea"). Solution: Extract Superclass on the delegates holding the defaults, and have the default case return a base delegate so the field is never null; host methods become unguarded one-line delegations.

Verify: every public method of the old subclass works through the delegate; each variant is exercised by a test; no `instanceof` on delegates; the subclass constructor has no callers (grep); the object can switch variant if that was the goal (inferred). The book again misspells `'NorweigianBlueParrot'` in a factory switch, a reminder that string-keyed dispatch needs a test per value.

## Replace Superclass with Delegate (Replace Inheritance with Delegation)

Use when
- Superclass operations do not make sense on the subclass (a `Stack` extending `List` exposes every list operation).
- Not every instance of the subclass is valid wherever the superclass is used. Example: a car-model class reused as a physical car adds VIN and manufacture date (the type-instance homonym modelling mistake).
- Coupling is high and superclass changes break the subclass.
Not "never inherit": if every superclass method applies and every subclass instance is a superclass instance, inheritance is simple and effective. Use it first; apply this refactoring when it becomes a problem. The cost is writing boring forwarding functions.

Mechanics
1. Create a field in the subclass referring to a superclass instance; initialise it to a new instance.
2. For each superclass element, create a forwarding function in the subclass; test after each consistent group (a getter/setter pair can only be tested once both are moved).
3. When all superclass elements have forwarders, remove the inheritance link.

Example (library scroll extends catalogue item): add `_catalogItem`, write forwarders (`id`, `title`, `hasTag`), drop `extends`. Often that is enough. Here the model is wrong in a further way (several physical scrolls, one catalogue entry), so also Change Value to Reference: give the scroll its own `_id`, look the item up in the catalogue by catalogue ID, then remove the now-unused title and tags constructor parameters.

Verify: the class no longer extends; its public interface exposes only intended forwarders; two scrolls for one catalogue ID share one item (identity check); tests for forwarders (inferred).

---

## Safety tactics
- Always encapsulate creation first (Replace Constructor with Factory Function); selector logic lives in the factory.
- Migrate through a delegating shell: move one method at a time, leave a forwarder, test, delete the old class last.
- Prove a new subclass is reached: temporarily break its override and watch a test fail; use a throw for unreachable legs.
- Use trap methods for subclass responsibility in dynamic languages.
- Check differences between "identical" methods; they expose untested behaviour.
- Avoid `instanceof`: extract the check, move it to the base class, then replace by a field or polymorphism.
- In static languages, compiling catches missing superclass members when pulling up; in dynamic ones add traps and tests.

Source: Refactoring 2e ch. 12.
