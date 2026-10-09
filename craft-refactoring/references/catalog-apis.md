# Catalogue: refactoring APIs (Refactoring 2e ch. 11)

Modules and functions are the building blocks; APIs are the joints. These refactorings change the joints: what a function takes, returns, and whether it changes anything.

Contents
- Separate Query from Modifier
- Parameterize Function
- Remove Flag Argument
- Preserve Whole Object
- Replace Parameter with Query / Replace Query with Parameter
- Remove Setting Method
- Replace Constructor with Factory Function
- Replace Function with Command / Replace Command with Function
- The parallel-change recipe (how nearly all of these are done safely)
- Published interfaces

Note: some code listings in the source notes lost their "after" lines in extraction; the mechanics below are reliable, and the intent of the examples was reconstructed.

---

## Separate Query from Modifier

Use when: a function returns a value and also has observable side effects. A function with no observable side effects can be called freely, moved around and tested easily. Rule (command-query separation): a function that returns a value should have no observable side effects. "Observable" matters: caching a result in a field is fine if any sequence of queries returns the same results.

Mechanics
1. Copy the function and name it as a query (what it returns; a receiving variable's name is a clue).
2. Remove side effects from the new query.
3. Static checks.
4. Find each call that uses the return value; replace it with a call to the query, and insert a call to the original directly below. Test after each.
5. Remove the return value from the original.
6. Test.
Afterwards tidy duplication by having the modifier call the query (Substitute Algorithm).

Example: `alertForMiscreant(people)` loops, sounds alarms and returns a name. Copy to `findMiscreant` without alarms; callers do `found = findMiscreant(people); alertForMiscreant(people);`; strip the return from the modifier; finally `if (findMiscreant(people) !== "") setOffAlarms();`.

Verify: the query returns identical results on repeated calls (inferred test); the modifier returns nothing; no caller consumes the modifier's return. This is the prerequisite of Consolidate Conditional Expression.

## Parameterize Function

Use when: two functions have very similar logic differing in literal values (`tenPercentRaise`, `fivePercentRaise`): one function with parameters removes the duplication.

Mechanics
1. Select one of the similar functions.
2. Change Function Declaration to add the literals as parameters.
3. For each caller, add the literal value.
4. Test.
5. Change the body to use the parameters, testing after each.
6. For each similar function, replace its call with a call to the parameterized one, testing after each.
7. If it does not work for a similar function, adjust it before moving on.

Start from the function in the middle of the variation (for range-oriented things, the middle band), since it has both literals; add parameters with an eye to the other cases. Use `Infinity` for open-ended bounds. A now-unneeded guard may stay as documentation.

## Remove Flag Argument (Replace Parameter with Explicit Methods)

Use when: callers pass a literal to pick which logic runs (`bookConcert(customer, true)`). Flags hide the available functions and, for booleans, say nothing at the call site.

Not every boolean is a flag argument. It is one only if (a) callers set it with a literal rather than data flowing through the program and (b) the implementation uses it to steer control flow rather than passing it on as data.

Mechanics
1. Create an explicit function for each value of the parameter.
2. If the main function has a clean dispatch conditional, use Decompose Conditional to create them; otherwise create wrapper functions.
3. For each caller using a literal, call the explicit function.

Notes
- If some callers pass computed data (`isRush = determineIfRush(order)`), keep those callers and the original function; support both. If all callers pass data, the signature is fine.
- Tangled variant (the flag is interleaved in the body): layer wrappers (`rushDeliveryDate = o => deliveryDate(o, true)`); if no one uses the parameter as data afterwards, restrict the original's visibility or rename it to say it is not for direct use.
- Several flags may legitimately stay (explicit functions for each combination would explode) but that signals a function doing too much.

## Preserve Whole Object

Use when: code derives several values from a record and passes them to a function. Pass the record and let the callee derive what it needs: handles change better (needing more data does not change the signature), shortens lists, and exposes duplicated logic that can move to the whole.

Do not use when: you do not want the callee to depend on the whole object (typically different modules).

Related smells: pulling several values from an object to compute is Feature Envy; common after Introduce Parameter Object; an object calling another with several of its own values should pass `this`.

Mechanics
1. Create an empty function with the desired parameters.
2. Give it a searchable temporary name (`xxNEW`).
3. Fill the body with a call to the old function, mapping new parameters to old.
4. Static checks.
5. Adjust each caller to use the new function, testing after each. Remove code that derived the old parameters if it becomes dead.
6. Once all callers have changed, Inline Function the original into the new one.
7. Rename the new function, and callers, to remove the prefix (a global replace works even without robust rename support).

Variation: build the new function from other refactorings (Extract Variable for the result and input, Extract Function with the prefix, Move Function), then continue as above.

## Replace Parameter with Query (inverse: Replace Query with Parameter)

Use when: callers pass a value the callee can determine "just as easily", most safely when it is derived from another parameter. A parameter list should summarise the points of variability. Bias: simplify callers, provided the responsibility fits the callee.

Do not use when: it adds a dependency the function should not have, or replaces a parameter with access to a mutable global (you lose referential transparency).

Mechanics
1. If necessary Extract Function on the calculation of the parameter.
2. Replace references to the parameter in the body with the expression that yields it; test after each.
3. Change Function Declaration to remove the parameter.

Typical trigger: another refactoring (such as Replace Temp with Query) leaves a parameter redundant.

## Replace Query with Parameter

Use when: a function reads something in its scope you do not like (a global; an element you plan to move). Push resolution to the caller. This changes dependency relationships and can purify a function: a common architecture is pure functions wrapped by logic that handles I/O and other variable things.

Cost: callers must supply the value and get more verbose. Neither direction is final, so know both.

Mechanics
1. Extract Variable on the query code to separate it from the rest of the body.
2. Extract Function on the body code that is not the query call.
3. Give the new function a searchable name.
4. Inline Variable on the variable you just created.
5. Inline Function the original.
6. Rename the new function to the original's name.

Example: a heating plan clamps a global thermostat's selected temperature; the new `targetTemperature(selectedTemperature)` is referentially transparent because the plan's fields are set only in the constructor.

Choosing: remove a parameter when the callee can derive it without unwanted coupling; add one to cut a dependency on a global or mutable thing, or to gain referential transparency.

## Remove Setting Method

Use when: a field should not change after construction. A setter signals that it may; removing it makes intent clear and makes the field immutable. Common cases: the only caller of the setter is the constructor, or a creation script calls the constructor then setters.

Mechanics
1. If the value is not passed to the constructor, Change Function Declaration to add it (all removed setters' values at once is simpler), and call the setter in the constructor.
2. Remove each call of the setter outside the constructor, using the new constructor value; test after each.
3. If you cannot replace a call by creating a new object (you are updating a shared reference object), abandon the refactoring.
4. Inline Function on the setter; make the field immutable if possible.
5. Test.

First step of Change Reference to Value.

## Replace Constructor with Factory Function (Factory Method)

Use when: constructors limit you: they must return an instance of exactly that class (no subclass or proxy), the name is fixed, and they usually need `new`. Also when callers pass a literal type code: create named factories (`createEngineer(name)`). Prerequisite for restructuring hierarchies (Replace Type Code with Subclasses, Replace Conditional with Polymorphism).

Mechanics
1. Create a factory function whose body calls the constructor.
2. Replace each constructor call with the factory.
3. Test after each change.
4. Limit the constructor's visibility as far as possible.

## Replace Function with Command (inverse: Replace Command with Function)

Use when: a complex function has many locals and cannot be broken up. A command object (the GoF Command, not "command" in the query/modifier sense) makes locals into fields so Extract Function becomes easy, and offers undo, parameters built over a lifecycle, hooks, and testable sub-methods. Cost is complexity: the author picks a first-class function 95% of the time.

Mechanics
1. Create an empty class named after the function.
2. Move Function the function into it; keep the original as a forwarding function until the end. Use the language's command naming convention, else `execute` or `call`.
3. Consider a field for each argument, moving arguments to the constructor (one at a time).
Then the point of the exercise: turn locals into fields one at a time, and Extract Function freely (`scoreSmoking()`), testing sub-functions directly. In JavaScript nested functions are an alternative; the author still prefers a command for testability.

## Replace Command with Function

Use when: the logic is simple enough that the command is more trouble than it is worth.

Mechanics
1. Extract Function on the creation of the command and the call to its execution method.
2. For each method the execution method calls, Inline Function (if it returns a value, Extract Variable on the call first).
3. Change Function Declaration to move all constructor parameters into the execution method.
4. For each field, change execution-method references to use the parameter, testing after each (delete the constructor's assignment so a missed reference breaks a test; if none does, add a test).
5. Inline the constructor call and execution call into the replacing function.
6. Test.
7. Remove Dead Code on the command class.

---

## The parallel-change recipe

Nearly every entry above uses one shape, also called expand-contract:
1. Add the new interface beside the old one (new function with a temporary searchable name that delegates to the old, or vice versa).
2. Redirect callers one at a time, testing after each.
3. Inline or delete the old interface.
4. Rename away the temporary name.
For a database column this is spread over releases: add the new column, write to both, move readers over, remove the old column after a bedding-in period (ch. 2).

## Published interfaces

A published interface has clients you cannot find or change. Keep the old declaration as a pass-through to the new one, mark it deprecated, retire it when (if ever) clients have moved. Do not publish interfaces prematurely. See `workflow-and-safety.md` for ownership and branch guidance.

Source: Refactoring 2e ch. 11 (with ch. 2 for published interfaces).
