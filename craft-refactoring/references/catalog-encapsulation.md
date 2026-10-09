# Catalogue: encapsulation (Refactoring 2e ch. 7)

Refactorings that hide a secret (a data structure, a representation, a connection between classes) so that fewer places need to change when it does.

Contents
- Encapsulate Record
- Encapsulate Collection
- Replace Primitive with Object
- Replace Temp with Query
- Extract Class / Inline Class
- Hide Delegate / Remove Middle Man
- Substitute Algorithm
- Cross-cutting tactics

Underlying idea: decompose by the secrets modules should hide; data structures are the commonest secret (ch. 7 intro). Encapsulate first, then change what is inside.

---

## Encapsulate Record (Replace Record with Data Class)

Use when
- A mutable record (an object literal, hash, map, nested list-and-hash structure possibly loaded from JSON) is read and written all over the code. An object can hide which values are stored and which are derived, and lets you rename fields by providing both names during migration.
- Hash-style records with arbitrary keys hide their fields; the wider the use, the worse. When making an implicit record explicit, prefer a class.

Do not use when: the record is immutable (copy the field instead), or a narrow-scope hash needs no wrapper.

Mechanics
1. Encapsulate Variable on the variable holding the record.
2. Give the encapsulating functions deliberately ugly, searchable names (for example `getRawDataOfOrganization`); they are short-lived.
3. Replace the variable's content with a simple class wrapping the record. Add an accessor in the class that returns the raw record, and make the encapsulating functions use it.
4. Test.
5. Add functions that return the object instead of the raw record.
6. For each user of the record, switch from the raw-record function to the object function, using accessors on the object (create them as needed). Test after each.
7. For a nested record, deal with clients that update first. Consider returning a copy or read-only proxy to clients that only read.
8. Remove the class's raw-data accessor and the ugly functions.
9. Test.
10. If the fields are structures themselves, apply Encapsulate Record and Encapsulate Collection recursively.

Nested-record example (customer usage by year and month): extract each digging write (`setUsage(id, year, month, amount)`) and move it into the wrapper class; getting all updates visible in one place is the most important part.

Prove you found every writer, by one of:
- make the raw getter return a deep copy, so a missed writer mutates the copy and (with good coverage) breaks a test;
- return a read-only proxy that throws on write;
- return a recursively frozen copy.

Readers, three options:

| Option | Strength | Cost |
|---|---|---|
| Explicit read methods moved into the class | The class shows every use of the data | Much code if many special cases; loses native navigation |
| Hand out a deep copy | Simplest | Copy cost on big structures (measure first); clients may expect writes to stick, so freeze the copy |
| Recursive Encapsulate Record | Most control | Most effort; not worth it if little of the structure is touched |

Verify: nothing references the raw accessor any more (rename the field or search to confirm); updates go through setters that can host validation; tests green after each client migration.

## Encapsulate Collection

Use when: a getter returns the collection itself, so clients can add and remove without the owner knowing (`person.courses.push(x)`).

Policy for the getter (pick one and apply it everywhere in the code base, because consistency matters most)
1. Never return a collection: rejected by the book, it adds code and cripples collection pipelines.
2. Return a read-only view or proxy.
3. Return a copy: the most common. Costs: callers may expect write-through; large collections cost time (measure first).
- A proxy shows later changes to the source, a copy does not; this rarely matters since such lists are held briefly. Also copy before calling something that mutates (in JavaScript `sort` mutates in place).

Mechanics
1. Encapsulate Variable if the reference is not already encapsulated.
2. Add functions to add and remove elements. If there is a setter for the collection, use Remove Setting Method if possible, otherwise make it store a copy.
3. Static checks.
4. Find every caller that modifies the collection and switch it to the new functions; test after each.
5. Change the getter to return a protected view (read-only proxy or copy).
6. Test.

Design detail: decide what `remove` does for an absent element (the book raises by default, with an optional handler).

Verify: after step 5 a missed direct mutation silently does nothing on a copy, so make sure tests assert membership after add and remove (inferred); a throwing proxy gives louder feedback.

## Replace Primitive with Object (Replace Data Value with Object, Replace Type Code with Class)

Use when: a string or number acquires behaviour (formatting, comparison, validation, extracting a part) and that logic is being duplicated. Make a class as soon as you want to do more than print it. It starts as a thin wrapper and becomes the home for behaviour; the book rates it among the most valuable refactorings.

Mechanics
1. Encapsulate Variable if not already.
2. Create a simple value class: constructor takes the existing value, a getter returns it.
3. Static checks.
4. Change the setter to create an instance and store it.
5. Change the getter to return the result of the new class's getter.
6. Test.
7. Consider renaming the accessors to say what they now do.
8. Decide whether the object is a value or a reference (Change Reference to Value or Change Value to Reference).

Example: order priority string becomes a `Priority`. Self-encapsulate the field first; prefer a conversion (`toString()`) to a `value` getter; rename the old getter `priorityString`, add one that returns the object; let the constructor accept an instance of itself; then add validation against legal values, `equals`, `higherThan`, and make it immutable. `order.priority.higherThan(new Priority("normal"))` replaces string comparisons.

## Replace Temp with Query

Use when
- A temp blocks extraction (it would have to be passed in), the same value is computed in several functions, or you want a stronger boundary that exposes hidden dependencies.
- Works best inside a class, where methods share context.

Do not use when: the temp is a snapshot (`oldAddress`) rather than a value that must come out the same whenever read, or it is assigned several times in ways that cannot all go into the query.

Mechanics
1. Check the variable is fully determined before use and the calculation yields the same value every time.
2. If the variable is not read-only and can be, make it so.
3. Test (catches a missed reassignment).
4. Extract the assignment into a function. If the names clash use a temporary function name. Ensure the function has no side effects; if it does, Separate Query from Modifier.
5. Test.
6. Inline Variable to remove the temp.

## Extract Class (inverse: Inline Class)

Use when: a class grew by accretion; a subset of data and methods go together, change together or depend on each other. Test: if you removed this field or method, which others would become nonsense? Another sign: subtyping affects only some features, or some features need subtyping one way and others another.

Mechanics
1. Decide how to split the responsibilities.
2. Create a child class for the split-off responsibility. If the parent's remaining job no longer matches its name, rename the parent.
3. Create an instance of the child when constructing the parent and link parent to child.
4. Move Field for each field to move; test after each.
5. Move Function for the methods, lower-level ones first (those being called rather than calling); test after each.
6. Review both interfaces: remove unneeded methods, rename for the new context (`officeAreaCode` becomes `areaCode`).
7. Decide whether to expose the child; if so, consider Change Reference to Value.

## Inline Class

Use when: a class no longer pulls its weight, often after other refactorings moved responsibility out; or as the first half of re-partitioning (merge two classes with Inline Class, then Extract Class along the new seam). General rule: sometimes move elements one at a time; sometimes collapse the contexts and re-separate.

Mechanics
1. In the target class create delegating functions for all public functions of the source class.
2. Change all references to the source's methods to the target's delegators; test after each.
3. Move all functions and data from the source to the target, testing after each, until the source is empty.
4. Delete the source class.

## Hide Delegate (inverse: Remove Middle Man)

Use when: clients call a method on an object held in the server's field (`person.department.manager`), so they depend on the delegate. A forwarding method on the server confines delegate interface changes to the server.

Mechanics
1. For each delegate method, create a simple delegating method on the server.
2. Adjust the client to call the server; test after each.
3. If no client needs the delegate any more, remove the server's accessor for it.
4. Test.

## Remove Middle Man

Use when: the server is mostly forwarding, and every new delegate feature needs another forwarder; often the result of zealous Law of Demeter. There is no fixed right amount of hiding; it changes as the system changes. A mix is fine: keep common delegations for convenience and expose the delegate for the rest.

Mechanics
1. Create a getter for the delegate.
2. For each client use of a delegating method, replace the call with a chain through the accessor; test after each. Delete delegating methods once all callers are gone. (With tooling: Encapsulate Variable on the delegate field, then Inline Function on the methods.)

Decision between the pair: look at actual usage. Hide Delegate when clients are being coupled to a delegate's interface; Remove Middle Man when forwarding methods dominate the server.

## Substitute Algorithm

Use when: a clearer way exists, a library now provides the behaviour, or you need the behaviour to be easier to change. First decompose the method as far as possible; replacing a large complex algorithm is very hard, replacing a small one is tractable.

Mechanics
1. Arrange the code to replace so it fills a complete function.
2. Prepare tests that use only this function, to capture its behaviour.
3. Prepare the alternative algorithm.
4. Static checks.
5. Run tests comparing old and new output. If equal, done. If not, keep the old algorithm as an oracle for debugging.

Verify with a differential test: run old and new on the same inputs (including edge cases) until outputs agree.

---

## Cross-cutting tactics seen in this chapter
- Encapsulate before changing a representation, so call sites are insulated.
- Introduce a delegating shell at the old location, migrate callers one at a time with a test after each, then delete the shell.
- Make a variable `const` and run tests as a cheap probe for hidden reassignments.
- Probe for hidden writers with a deep copy, frozen copy or throwing proxy.
- Value-object wrappers should be immutable and define equality.

Source: Refactoring 2e ch. 7. Note: the opening of the Encapsulate Record motivation was lost in the book's text extraction; the motivation above is reconstructed from the surviving part.
