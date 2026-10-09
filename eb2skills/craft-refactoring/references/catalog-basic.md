# Catalogue: the basic refactorings (Refactoring 2e ch. 6)

Eleven refactorings that make up most day-to-day work: extract and inline (function, variable), change a declaration, encapsulate and rename a variable, group data and functions (parameter object, class, transform), and split a function into phases.

Contents
- Extract Function / Inline Function
- Extract Variable / Inline Variable
- Change Function Declaration
- Encapsulate Variable
- Rename Variable
- Introduce Parameter Object
- Combine Functions into Class
- Combine Functions into Transform
- Split Phase
- Quick chooser

Entry format: use when, do not use when, mechanics (numbered, as the book gives them), verify, related. "Test" means run the fast suite. "Static checks" means compile, type-check or lint. Examples in the book are JavaScript; the steps are language-neutral. Wherever a step says "temporary searchable name", pick a prefix that will not occur elsewhere (the book uses `zz_`, `xxNEW`), so a grep finds every leftover.

---

## Extract Function (Extract Method)

Use when
- A fragment needs effort to understand, or has a comment above it saying what it does. The measure is the distance between what a fragment does and how it does it, not its length. A one-line function whose name says more than its body is fine (Refactoring 2e ch. 6, ch. 3 Long Function).
- Before moving or reusing a piece of logic, or before replacing a conditional leg or loop body.

Do not use when
- You cannot find a name better than the code itself. If you extract and find it unhelpful, inline it again; that costs little.
- Too many locals are assigned inside the fragment. Simplify those first (Split Variable, Replace Temp with Query), then retry.

Mechanics
1. Create a new function named for what it does, not how. A good name may only appear while you work; refine it later.
2. If the language has nested functions, nest the new one inside the source function; this avoids passing out-of-scope variables. Move it later if needed.
3. Copy the fragment into the new function.
4. Scan the fragment for local variables of the source function that are not in scope in the new one; pass them as parameters.
   - Read-only variables: pass as parameters.
   - A variable declared outside but used only inside the fragment: move its declaration into the fragment.
   - Assigned variables: if only one, treat the fragment as a query and return it (declare it inside the new function and assign the result at the call site). An assigned parameter must first be split into a temp (Split Variable). A structure that is only mutated (array, object) can be passed in.
   - If many locals are assigned, abandon and simplify variables first.
   - Needing several values back: prefer extracting different code so each function returns one value; a returned record is a last resort and usually a sign the temps need reworking.
5. Static checks once all variables are dealt with.
6. Replace the fragment in the source with a call to the new function.
7. Test.
8. Look for other code that duplicates the fragment and consider replacing it with a call (Replace Inline Code with Function Call).

Tips from the worked example: if the fragment will end up at top level, extract to a sibling function first rather than nested, because scope problems only show when you move it. A reassigned accumulator is handled by Slide Statements (put its declaration next to the loop), copy the loop into a new function that declares and returns the variable, call it, then rename the returned variable. Wrap clock calls (Clock Wrapper) so tests stay deterministic.

Verify: tests pass; the name states intent; no parameter remains that the new function does not use.

Related: Inline Function, Replace Temp with Query, Split Variable, Decompose Conditional.

## Inline Function (Inline Method)

Use when
- The body is as clear as the name; a group of functions is badly decomposed (inline them all into one, then re-extract the way you prefer); or everything just delegates to something else and you want to flush out the useful indirection.

Do not use when
- It is a polymorphic method (subclasses override it), recursive, has multiple return points, or is being inlined into an object without accessors. If those complications appear, stop.

Mechanics
1. Check it is not a polymorphic method (a class method with overriding subclasses cannot be inlined).
2. Find all callers.
3. Replace each call with the body.
4. Test after each replacement; tricky parts can be done gradually.
5. Remove the definition.

Hard case: a function that pushes lines into an output array: go one statement at a time with Move Statements to Callers, then delete the empty function. If a fast attempt breaks tests, revert to the last green state and use smaller steps.

## Extract Variable (Introduce Explaining Variable)

Use when: part of a complex expression deserves a name, or you want a hook for a debugger or print. Choose the scope of the name: meaningful only inside this function means a variable; meaningful to the whole object or class means a getter or function (Extract Function, later Replace Temp with Query), so other code can use it without repeating the expression. If promotion is much more effort, leave it for later; if easy (inside a class), do it now.

Mechanics
1. Ensure the expression has no side effects.
2. Declare an immutable variable and set it to a copy of the expression (or the part to name).
3. Replace the original expression with the variable.
4. Test.
5. If the expression occurs more than once, replace each occurrence, testing after each.

Example outcome: a price function gets `basePrice`, `quantityDiscount`, `shipping` and its comment disappears; inside an `Order` class the same names become getters.

## Inline Variable (Inline Temp)

Use when: the name says no more than the expression, or the variable blocks refactoring of nearby code.

Mechanics
1. Check the right-hand side has no side effects.
2. Make the variable immutable if it is not already, and test (this proves it is assigned once).
3. Replace the first reference with the right-hand side.
4. Test.
5. Repeat for every reference.
6. Remove the declaration and assignment.
7. Test.

---

## Change Function Declaration (Rename Function, Add Parameter, Remove Parameter, Change Signature)

Use when
- A name no longer says what the function does (fix it as soon as you know a better one; trick: write a comment saying what it does, then turn the comment into the name).
- The parameter list is wrong: taking a narrower value (a phone number, not a person) widens where the function can be used and removes coupling; taking the whole object lets the logic evolve without caller changes. There is no permanent right answer, so become fluent at moving this joint (ch. 6).

Choose the mechanics
- Simple: you can change the declaration and every caller in one go.
- Migration: many callers, callers hard to reach, a polymorphic method, a published API, a non-unique name (two classes have `changeAddress`, only one should change), or a simple attempt failed (revert to last good state and retry).
- Rename and add-parameter are separate changes; test between them.

Simple mechanics
1. If removing a parameter, check the body does not reference it.
2. Change the declaration.
3. Find all references to the old declaration and update them.
4. Test.

Migration mechanics
1. If needed, refactor the body so the extraction in step 2 is easy.
2. Extract Function on the body to create the new function. If it will have the same name, use a temporary searchable name.
3. If it needs extra parameters, add them with the simple mechanics.
4. Test.
5. Inline Function on the old function (callers switch one by one, test between).
6. If a temporary name was used, apply Change Function Declaration again to restore the final name.
7. Test.
- Polymorphic methods: add the indirection for each binding; with one hierarchy a forwarding method on the superclass is enough.
- Published API: stop after creating the new function, deprecate the old one, delete only when (if ever) all clients have moved.

Examples in the book
- Add a parameter `isPriority` to a booking method: extract the body to `zz_addReservation(customer, isPriority)`, old method calls it with `false`, add an assertion that the new parameter is a boolean (JavaScript does not check arity), inline the old method into callers, rename back.
- Change a parameter to one of its properties (`inNewEngland(aCustomer)` to `inNewEngland(stateCode)`): Extract Variable for `stateCode` inside the body; Extract Function for the rest under a temporary name; Inline Variable on the input in the old function; Inline Function of the old function into callers (they now pass `c.address.state`); rename the new function.
- With static typing and an IDE the rename is automatic and low risk; without static typing, text search gives false positives, so lean on tests.

## Encapsulate Variable (Encapsulate Field, Self-Encapsulate Field)

Use when
- Mutable data is reachable from more than one function and you want to rename it, move it, validate it, or find out who changes it. Functions can be moved while a forwarder remains; data cannot, so route access through functions first and turn a hard data reorganisation into an easier function reorganisation.
- Rule of habit: encapsulate any mutable data whose scope exceeds one function, more strictly the larger the scope. In legacy code, encapsulate a variable whenever you must add or change a reference to it.

Do not use when: the data is immutable (copy it instead; no validation hook needed). Self-encapsulating inside a class is excessive unless you are about to split the class; if the class is so big you need it, break the class up.

Mechanics
1. Create functions to read and update the variable.
2. Static checks.
3. Replace each reference with a call to the right function; test after each.
4. Restrict the variable's visibility (JS: move variable and accessors into their own module, export only the accessors). If that is impossible, rename the variable (for example `__privateOnly_x`) and test to find stragglers.
5. Test.
6. If the value is a record, consider Encapsulate Record.

This encapsulates the reference, not the contents. To control contents: have the getter return a copy (works on one level only), or a read-only wrapper (Encapsulate Record), preferably as a temporary measure to find mutators; consider copying in the setter too. Deeper structures need deeper copies.

## Rename Variable

Use when: the name is wrong because of insufficient thought, learning, or changed purpose. A name's importance grows with the breadth of its use: a lambda parameter may be one letter, a persistent field needs the most care.

Mechanics
1. If widely used, consider Encapsulate Variable.
2. Find all references and change each. If any reference lives in another code base, it is a published variable and you cannot do this refactoring.
3. If the variable does not change, copy it under the new name and migrate gradually, testing after each.
4. Test.

Constants and exported read-only values need no encapsulation: declare the new name with the value, make the old name a copy of the new one, migrate references gradually, remove the old name.

## Introduce Parameter Object

Use when: the same group of values travels together (a data clump), for example `(station, min, max)`. The refactoring makes the relation explicit and, more importantly, gives you a place to move behaviour (`range.contains(x)`), which can reveal a new domain abstraction. Stopping before moving behaviour in leaves half the benefit.

Mechanics
1. If no suitable structure exists, create one. Prefer a class (easier to add behaviour later); make it a value object without update methods.
2. Test.
3. Change Function Declaration to add a parameter for the new structure.
4. Test.
5. Adjust each caller to pass an instance; test after each.
6. For each element of the structure, replace the use of the original parameter with the structure's element and remove the parameter; test.

Follow-up: search for other min/max pairs (for example the operating plan's floor and ceiling become one range), move more behaviour in, add value equality.

## Combine Functions into Class

Use when: several functions work on the same data record, usually passed as an argument. A class makes the shared environment explicit, shortens calls, gives a handle to pass around and invites more behaviour. Its decisive advantage over a transform: if the underlying data can change, derived values computed on demand stay consistent.

Mechanics
1. Encapsulate Record on the common data.
2. If the common data is not a record yet, Introduce Parameter Object.
3. Move Function each function that uses the record into the new class.
4. Remove arguments that are now members from the calls.
5. Extract Function on remaining logic that manipulates the data and move the result into the class.

Example: three clients each compute `baseRate(month, year) * quantity`, and a helper already exists but was missed. Wrap the record in a `Reading` class, move the helper in as a property `baseCharge` (uniform access: callers cannot tell stored from derived), replace the duplicates, then extract and move the taxable-charge calculation. Nested functions are another grouping option but are hard to test and awkward to expose.

## Combine Functions into Transform

Use when: derived values are needed in several places and the source data is read-only or immutable (display data, pipeline stages). Gather derivations in one function that returns the record enriched with the derived fields.

Do not use when: clients may change the source data afterwards. The derived fields stored in the output go stale. Use Combine Functions into Class instead.

Mechanics
1. Create a transform function that takes the record and returns a deep copy; write a test that the transform does not alter its input.
2. Pick logic, move its body into the transform as a new field of the result, change the client to read the field. If the logic is complex, Extract Function first.
3. Test.
4. Repeat for other functions.

Naming: "enrich" when the output is the input plus information; "transform" when the output is a different thing. Mutating the result inside the transform is acceptable; keep immutability at the boundaries. Add the "input unchanged" test by cloning the input as an oracle.

## Split Phase

Use when: a fragment does two sequential things that use different sets of data and functions (parse then compute; price then ship; the compiler archetype). Separating phases lets you change one without holding the other in mind, and lets a second consumer (an HTML renderer next to a text one) reuse phase one.

Mechanics
1. Extract the second-phase code into its own function.
2. Test.
3. Introduce an intermediate data structure as an extra argument to that function.
4. Test.
5. Examine each parameter of the second phase. If the first phase uses it, move it into the intermediate structure, testing after each. If the second phase should not use it, extract the results of its use into a field of the structure and Move Statements to Callers on the line that populates it.
6. Extract Function on the first-phase code, returning the intermediate structure (a transformer object is also reasonable).

Example (`priceOrder`): extract `applyShipping(...)`; add `priceData = {}`; move `basePrice`, then `quantity`, then `discount` into it; leave `shippingMethod` as a parameter because phase one does not use it; extract `calculatePricingData(product, quantity)`; inline the final temporaries.

Verify: the second phase reads only the intermediate structure plus its own inputs; the intermediate structure is treated as immutable result data.

---

## Quick chooser

| Situation | Refactoring |
|---|---|
| Fragment needs a comment or takes effort to read | Extract Function |
| Body says no more than the name; too much delegation; wrong decomposition | Inline Function, then re-extract |
| Complex expression, part deserves a name | Extract Variable (variable for local scope, function or getter for wider scope) |
| Variable name adds nothing or blocks another refactoring | Inline Variable |
| Bad name, or wrong parameters | Change Function Declaration (migration mechanics for many callers, polymorphism, published API) |
| Widely used mutable data to rename, move or guard | Encapsulate Variable first |
| Bad variable name | Rename Variable |
| Same values travel together | Introduce Parameter Object, then move behaviour in |
| Functions share a record and the data may change | Combine Functions into Class |
| Derived values scattered, data read-only | Combine Functions into Transform |
| Two sequential concerns with different data | Split Phase |

Source: Refactoring 2e ch. 6 (with ch. 2 and 3 for motivation).
