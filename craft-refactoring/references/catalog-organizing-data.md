# Catalogue: organizing data (Refactoring 2e ch. 9)

Five refactorings about variables, fields and the reference-or-value question. Related entries elsewhere: Encapsulate Variable, Encapsulate Record, Rename Variable (see `catalog-basic.md`, `catalog-encapsulation.md`), Replace Primitive with Object, Remove Setting Method (`catalog-apis.md`).

Contents
- Split Variable
- Rename Field
- Replace Derived Variable with Query
- Change Reference to Value
- Change Value to Reference
- Choosing between siblings; safety tactics

---

## Split Variable (Split Temp, Remove Assignments to Parameters)

Use when
- A variable is assigned more than once and is not a loop variable or a collecting variable (sum, string concatenation, stream write, collection append). A variable that holds the result of a bit of code for later reference should be set once; assigned twice, it has two responsibilities, which confuses readers.
- Also for an input parameter that is also used as the result holder.
- Typical trigger: Extract Function or Replace Derived Variable with Query is blocked by a reused variable.

Mechanics
1. Rename the variable at its declaration and first assignment, naming it for its first use only.
2. If a later assignment has the form `i = i + something`, it is a collecting variable: do not split.
3. If possible declare the new variable immutable, which proves it is assigned once.
4. Change all references up to the second assignment.
5. Test.
6. Repeat in stages: at each stage rename at the next assignment (which becomes a new declaration) and change references until the following assignment, until the last. The original name disappears.

Examples: an `acc` that was first acceleration from the primary force, later from primary plus secondary, becomes `primaryAcceleration` and `secondaryAcceleration`. A function that mutated `inputValue` becomes `let result = inputValue` with the later lines deliberately reading the original input where the line is conceptually about the input.

Verify: each new variable can be immutable; no use of the old name remains; tests unchanged. A splittable variable shows up as a `let` assigned in two non-accumulating places.

## Rename Field

Use when: a name in a widely used record (or a class getter/setter pair, which is effectively a field to clients) is misleading. Domain understanding should be embedded in names.

Mechanics
1. If the record has limited scope, rename all accesses and test; done.
2. If not encapsulated, Encapsulate Record.
3. Rename the private field inside the object and adjust internal methods.
4. Test.
5. If the constructor uses the name, Change Function Declaration to rename its parameter or key.
6. Rename Function on the accessors.

Gradual path for widely used data: encapsulate; separate input data from internal data (the internal field becomes `_title` while accessors still say `name`); make the constructor accept either `title` or `name`; migrate constructor callers one by one; remove `name` support; rename the accessors. Scope decides: used locally, rename in one go; if tests break, switch to the gradual procedure. For immutable data, skip encapsulation: copy the value to the new name, move users gradually, delete the old name. Duplicating mutable data is a recipe for disaster.

## Replace Derived Variable with Query

Use when: a mutable variable could just as easily be computed from other data (a running total kept beside the list it totals). Mutable data couples code with hard-to-spot knock-on effects; computing instead cannot go stale. Exception: if the source is immutable and the result can be made immutable, a transform that creates a new structure is fine.

Mechanics
1. Identify all points of update of the variable; use Split Variable to separate them if needed.
2. Create a function that calculates the value.
3. Introduce Assertion that the variable and the calculation agree whenever the variable is used (Encapsulate Variable first if you need a home for the assertion).
4. Test.
5. Replace each reader with a call to the new function.
6. Test.
7. Remove Dead Code on the declaration and updates.

Example: an adjustments list and a `_production` accumulator are both updated. Add `calculatedProduction` (a reduce over adjustments), assert equality in the getter, run the suite, then return the calculation and delete the field. If a constructor supplies an initial value the assertion fails: Split Variable first into `_initialProduction` and an accumulator, and replace only the accumulator.

Verify: the assertion runs over the whole suite (optionally logged in production) without firing before you switch readers.

## Change Reference to Value (inverse: Change Value to Reference)

Use when: an inner object is updated in place (`person.telephone.areaCode = x`) and you would rather replace it whole with an immutable value object. Value objects are easier to reason about, can be passed or copied without worry, hold no memory links, and help in distributed and concurrent systems.

Do not use when: several owners must share one object so that a change is visible to all; it must stay a reference.

Mechanics
1. Check that the class is immutable or can become so.
2. For each setter, apply Remove Setting Method.
3. Provide a value-based equality method using the fields (in Java also override `hashCode`; in Ruby `==`; JavaScript has no support, so write `equals`).

Example: `TelephoneNumber` extracted from `Person`. Add area code and number to its constructor, change each owner setter to build a new instance (`this._telephoneNumber = new TelephoneNumber(arg, this.officeNumber)`), test, then add `equals`.

Test equality with two independently constructed objects built from identical arguments; also unequal numbers, comparison with a different type and with null. Verify no setters remain and mutation attempts fail (freeze or removed setters, inferred).

## Change Value to Reference

Use when: several records describe the same logical entity (many orders for one customer) as separate copies, and the entity must be updated: miss one copy and you have inconsistency. Switch to a single shared object per entity, found through a repository.

Mechanics
1. Create a repository for instances of the related object (if none exists).
2. Ensure the constructor can look up the correct instance (an ID).
3. Change the host's constructors to use the repository. Test after each change.

Example: `Order` did `new Customer(data.customer)`, so five orders for customer 123 had five customers. A module-level repository (`registerCustomer(id)` creates if missing and returns the one instance; `findCustomer`) fixes that. Variants: create on first reference, or pre-populate the repository and treat an unknown ID as an error.

Caveat: the constructor is now coupled to a global repository; the book says to treat globals "like a powerful drug". If that bothers you, pass the repository as a constructor parameter.

---

## Choosing between siblings
- Reference versus value is a two-way door. Value when the data is (or can be) immutable and not meant to be shared and mutated; reference when one entity is duplicated and must be updated consistently.
- If a derived accumulator has a second role (an initial value), Split Variable first, then replace only the derived part.
- Rename Field: scope decides between one-shot and gradual; failing tests mean go gradual.

## Safety tactics seen here
- Make the new variable immutable as a probe that it is assigned once.
- Use an assertion to test a hypothesis (stored equals computed) before switching.
- Migrate through an intermediate form that accepts both old and new names, then remove the old (parallel change).
- Smaller steps with a test after each; "not making mistakes is a fantasy".

Source: Refactoring 2e ch. 9.
