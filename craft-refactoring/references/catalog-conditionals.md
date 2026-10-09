# Catalogue: simplifying conditional logic (Refactoring 2e ch. 10)

Contents
- Decide which tool (decision list)
- Decompose Conditional
- Consolidate Conditional Expression
- Replace Nested Conditional with Guard Clauses
- Replace Conditional with Polymorphism
- Introduce Special Case (Null Object)
- Introduce Assertion
- Safety tactics

Much of a program's power and complexity lives in conditionals. The chapter's toolkit: clarify (Decompose), combine (Consolidate), pre-check (guard clauses), separate by case (polymorphism), absorb repeated null/sentinel checks (Special Case), and communicate assumptions (Assertion, the one that adds a condition).

## Decide which tool

| What you see | Use |
|---|---|
| A condition or branch whose body tells what happens but not why | Decompose Conditional |
| Several checks, each different, with the same result | Consolidate Conditional Expression, then maybe Extract Function |
| An unusual case buried in nested if/else around the main path | Guard clauses |
| The same condition (type, state) switched on in several functions; or a base case with a variant that alters a few methods | Replace Conditional with Polymorphism |
| Many clients test for the same null or sentinel and react the same way | Introduce Special Case |
| Code only works if something holds, and that is only implied | Introduce Assertion |
| A single, isolated switch | Leave it. Most conditionals should stay plain if/else and switch (the author disagrees with "replace all conditionals") |

---

## Decompose Conditional

Use when: a long function with conditionals; both the checks and the actions say what happens but hide why. Extract the condition and each leg to functions named for intent. It is Extract Function applied to a conditional; the payoff is consistently large.

Mechanics
1. Apply Extract Function to the condition and to each leg.

Follow the one-extraction-then-test rhythm. Example: `summer()`, `summerCharge()`, `regularCharge()`, then the result reads as a ternary.

## Consolidate Conditional Expression

Use when: a series of checks gives the same result. Combining them shows it is really one check and sets up Extract Function, which replaces a statement of what with why.

Do not use when: the checks are truly independent and should not be thought of as one.

Mechanics
1. Ensure none of the conditions has side effects; if one does, Separate Query from Modifier first.
2. Combine two conditions with a logical operator: sequences combine with `or`, nested ifs with `and`.
3. Test.
4. Repeat until all are in one condition.
5. Consider Extract Function on the result.

Examples: three early `return 0` checks in a disability calculation fold into `isNotEligibleForDisability()`; `if (onVacation) if (seniority > 10) return 1;` becomes `onVacation && seniority > 10`. Mixed and/or gets messy: extract liberally.

## Replace Nested Conditional with Guard Clauses

Use when: one leg of a conditional is the normal path and the other an unusual condition. If/else gives both legs equal weight; a guard clause says "this is not the core of the function; handle it and leave". Single entry is enforced by modern languages and single exit is "not a useful rule": clarity decides.

Mechanics
1. Select the outermost condition that needs replacing and make it a guard clause.
2. Test.
3. Repeat.
4. If all guards return the same result, Consolidate Conditional Expression.

Example (`payAmount`): guard for separated, then for retired; the `result` temp becomes pointless, so return the final computation directly (removing a mutable variable is always a gain).

Reversing conditions (credit Kerievsky): with `if (capital > 0) { if (interestRate > 0 && duration > 0) {...} }`, replace one at a time, reversing each condition as you introduce the guard (`if (capital <= 0) return result;`). For a compound condition, first wrap it in `!( ... )`, then simplify with De Morgan, because leftover nots twist the mind. Two guards with the same return consolidate to one `||`; the double-duty `result` goes.

Verify: tests after each guard; no `else` follows a return; the main path is unindented; no leftover mutable `result` (inferred).

## Replace Conditional with Polymorphism

Use when
- Several functions switch on the same type code (create a class per case), or
- there is a base case with variants (put the common logic in a superclass and write each variant to emphasise its difference).
- Polymorphism is prone to overuse; apply it when the same condition is tested in several places.

Mechanics
1. If the classes do not exist, create them with a factory function that returns the right instance.
2. Use the factory in calling code.
3. Move the conditional function to the superclass.
4. If the conditional logic is not a self-contained function, Extract Function first.
5. Pick a subclass. Create an overriding method; copy that leg's body in and adjust.
6. Repeat for each leg.
7. Leave a default in the superclass method, or make it abstract or throwing to mark subclass responsibility.

Example 1, generalisation (birds): `plumage` and `airSpeedVelocity` both switch on type. Combine Functions into Class (`Bird`), add empty subclasses plus a `createBird` factory, change callers, move one leg at a time. After moving each leg, replace the same leg in the superclass with `throw` to prove the new path is reached ("because I'm paranoid"). The book's own factory has a misspelled case name (`'NorweigianBlueParrot'`) that would silently fall to the default: test every type value through the factory.

Example 2, variation (voyage rating): scattered "China voyage with a captain who has been to China" logic. Combine into a `Rating` class, add an empty `ExperiencedChinaRating` and a `createRating` factory. Move behaviours one at a time: simple ones become a subclass override (`Math.max(super.captainHistoryRisk - 2, 0)`) and the condition leaves the base. A tangled one (an if/else with logic in both branches) needs Extract Function on the whole block first (the name `voyageAndHistoryLengthFactor` contains an "And", tolerated temporarily), then split into single-purpose hooks (`historyLengthFactor` differs by class; the "+3" moves to the subclass `voyageProfitFactor`). Introducing a method just to be overridden is normal in base-and-variant inheritance, but a crude one obscures; split it into well-named hooks.

Verify: every leg moved; the superclass switch is gone or only throws or defaults; the factory covers every type name exactly as spelled in the data; tests per type.

## Introduce Special Case (Introduce Null Object)

Use when: many clients check for the same special value (null, `"unknown"`) and most then do the same thing. Capture that reaction in a special-case object so most checks become plain calls. Null Object is a special case of Special Case.

Forms: a class (when the object has behaviour or may be updated); a frozen literal object (read-only use); a transform that inserts the special case into a plain record (data from outside, such as JSON).

Mechanics (container with a subject property; clients compare the subject to a special value)
1. Add a special-case check property (`isUnknown`) to the subject, returning false.
2. Create a special-case object with only that property, returning true.
3. Extract Function on the special-case comparison code. Ensure all clients use the new function.
4. Introduce the special-case subject into the code (returned by a function, or via a transform).
5. Change the comparison function's body to use the special-case property.
6. Test.
7. Combine Functions into Class or into Transform to move common special-case behaviour into the new element (fixed responses can be a literal record).
8. Inline Function on the comparison for places where it is still needed.

Key difficulty: flipping the subject to return the new object forces every `=== "unknown"` client to change at once. Escape: Extract Function around the thing you would otherwise change in many places (a global `isUnknown(arg)` that first does the old comparison and throws for any value that is neither the real class nor the sentinel), migrate clients one at a time, then change the function body and the producer.

Further points
- Move common behaviour in one response at a time (name returns "occupant"; a setter becomes a no-op so writer clients drop their guards; related objects returned are usually special cases too, such as a null payment history with zero weeks delinquent).
- Special-case objects are value objects and immutable even if the object they replace is mutable.
- Expect exceptions: of 23 clients one may want different behaviour; keep an explicit `isUnknown` check there. When done, Remove Dead Code on the global check.
- In the transform variant, make the check tolerant of both raw and enriched forms during migration.

Verify: no remaining comparisons to the sentinel (grep); the migration trap never fired; tests cover the special-case behaviour; special-case objects are immutable.

## Introduce Assertion

Use when: code works only if a condition holds (a square root of a positive number; at least one of several fields set) and the assumption is implicit or in a comment. An assertion is a condition assumed always true; failure means programmer error, and the program must run equally correctly with all assertions removed.

Mechanics
1. When you see a condition assumed true, add an assertion for it. This is always behaviour-preserving, since assertions must not affect running of the system.

Placement: prefer the setter over the point of use (`assert(aNumber === null || aNumber >= 0)`), because a failure in use leaves you puzzling how the bad value got in.

Warnings
- Assert only what must be true, not everything you believe.
- Duplicated assertion conditions get tweaked inconsistently: Extract Function.
- Assertions are for programmer errors only. Validation of external data (files, user input) is a first-class part of the program, not an assertion.
- Their communication value outlasts their debugging value once the code is self-testing.

Also used as the hypothesis test in Replace Derived Variable with Query and Move Field.

## Safety tactics
- Extract a function around what you would have to change in many places, migrate callers one at a time, then change the body (with a throwing trap for unexpected values).
- Make the old check tolerant of both old and new representations during migration.
- After moving a branch, replace the original with a throw to prove the new code is reached.
- Move one leg or guard at a time and test after each.
- Combine conditions only after confirming none has side effects.
- Remove mutable temporaries that become redundant.

Source: Refactoring 2e ch. 10.
