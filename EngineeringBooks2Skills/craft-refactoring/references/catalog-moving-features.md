# Catalogue: moving features (Refactoring 2e ch. 8)

Refactorings that move elements between contexts (classes, modules), across a function boundary, or within a function; plus the loop and dead-code refactorings.

Contents
- Move Function
- Move Field
- Move Statements into Function / Move Statements to Callers
- Replace Inline Code with Function Call
- Slide Statements
- Split Loop
- Replace Loop with Pipeline
- Remove Dead Code
- Chooser and recurring tactics

Principle: modularity means you can change the program while understanding only a small part of it. That needs related elements together with easy-to-find links, and your understanding of the right grouping grows, so elements have to move (ch. 8 intro).

---

## Move Function (Move Method)

Use when
- The function references elements of another context more than its own.
- Its callers live elsewhere, or the next enhancement needs to call it from elsewhere.
- A nested helper has value on its own, or a method would be easier to use on another class.
- Often the right home is a new context: then Combine Functions into Class or Extract Class first.
- Heuristic: the harder the choice, the less it matters. Pick a home, learn, move again later.

Mechanics
1. Examine everything the function uses in its current context and decide whether it should move too. A called function that should also move is usually moved first (start a cluster with the one that depends least on the others). If a high-level function is the only caller of sub-functions, inline them into it, move, and re-extract at the destination.
2. Check whether it is polymorphic (account for super- and subclass declarations).
3. Copy the function to the target context and adjust it. Body references to the source context become parameters or a reference to the source. A new context often calls for a new name.
4. Static analysis.
5. Work out how to reference the target from the source context.
6. Turn the source function into a delegating function.
7. Test.
8. Consider Inline Function on the source. It can stay as a delegator; if callers reach the target just as easily, drop the middle man.

Example 1, nested function to top level: copy `calculateDistance` to top level under a distinct temporary name (`top_calculateDistance`) so both exist and the program still runs. Static analysis flags undefined symbols; pass `points` as a parameter. Helpers that depend on nothing in the enclosing scope move along: first nest them inside the original nested function and test (the linter and tests reveal complications), then copy them to the top-level copy. Replace the original body with a call to the new one, and run tests at that point. Give the highest-visibility function the best name; remove a shadowing local with Inline Variable. The author is wary of nested functions because they set up hidden data interrelationships; use the module system to restrict visibility.

Example 2, between classes (overdraft charge from `Account` to `AccountType`): the trigger is an upcoming change that makes the algorithm vary by type. Pass the simple value (`daysOverdrawn`) first; pass the whole source object only if more data is needed, especially data that varies by type. Replace the source body with a delegating call, then decide whether to inline it.

## Move Field

Use when
- You always pass a field from one record whenever you pass another record.
- A change to one record forces a change to a field in another.
- The same field must be updated in several structures.
- Good data structures keep behaviour code simple; poor ones create code whose only job is coping with the data. When you see the structure is wrong, change it.

Mechanics
1. Ensure the source field is encapsulated.
2. Test.
3. Create a field (and accessors) in the target.
4. Static checks.
5. Ensure there is a reference from the source object to the target (an existing field or method, a method you can create, or a new field in the source, permanent or temporary).
6. Adjust accessors to use the target field. If the target is shared between source objects, first make the setter update both fields and add an assertion to catch inconsistent updates; once confident, finish the switch.
7. Test.
8. Remove the source field.
9. Test.

Notes from the examples
- Failure mid-way: the setter ran before the target object existed in the constructor. The response was to revert to the last green state, reorder the constructor with Slide Statements, test, and retry, rather than debug forward.
- Bare record variant: create accessors first (ideally Encapsulate Record), route reads and writes through them; if the field is immutable, write both on set and migrate readers gradually.
- Moving to a shared object (an account's interest rate to its account type) is a refactoring only if all accounts of a type already share the value. Check the data (query it), add an assertion or log, run for a while, then switch the getter and drop the argument.

## Move Statements into Function (inverse: Move Statements to Callers)

Use when: the same statements run every time a function is called (they sit just before or after each call) and are best understood as part of that function. Folding them in means future changes happen once. If they later need to vary, move them out again.

If the statements do not belong conceptually inside the function but should still be called with it, Extract Function over (statements + call) instead; it is common to stop there.

Mechanics
1. If the repeated code is not adjacent to the call, Slide Statements to make it so.
2. If the target is called from one place only, cut from the source, paste into the target, test, done.
3. With more callers: Extract Function on one call site, extracting both the call and the statements, with a transient but greppable name.
4. Convert every other call to use the new function; test after each.
5. When all original calls use the new function, Inline Function the original into it and remove the original.
6. Rename the new function to the original's name (or better).

## Move Statements to Callers

Use when: an abstraction boundary shifted. A once-cohesive function now mixes things, because common behaviour must vary for some callers. Slide the varying behaviour to the start or end of the function and move it out to the callers. This is for small boundary shifts. If the boundary is wholly wrong, Inline Function, then Slide Statements and Extract Function to form better boundaries.

Mechanics
1. Simple case (one or two callers, simple function): cut the first or last line from the callee, paste (and fit) into the callers, test.
2. Otherwise Extract Function on all statements you do not want to move, with a temporary searchable name. If the function is overridden in subclasses, extract in all of them so the remaining method is identical everywhere, then remove the subclass methods.
3. Inline Function the original, one call site at a time with tests, then delete it.
4. Change Function Declaration to rename the extracted function to the original name (or better).

## Replace Inline Code with Function Call

Use when: inline code duplicates an existing function and the function's name makes sense in its place; also a library function now exists (`states.includes("MA")` replaces a flag-and-loop).

Do not use when: the similarity is coincidental, meaning that if the function changed you would not want this code to change. Test: does the function's name fit the inline code? If not, either the name is poor (rename) or the purpose differs (do not call it).

Mechanics: 1. Replace the inline code with a call. 2. Test.

## Slide Statements (Consolidate Duplicate Conditional Fragments)

Use when: related code should sit together (lines touching the same structure; declare a variable just before first use). Most often a preparatory step for Extract Function, which needs contiguous code.

Mechanics
1. Identify the target position. Examine the statements between source and target for interference and abandon if there is any. A fragment:
   - cannot slide earlier than the declaration of any element it references;
   - cannot slide later than any element that references it;
   - cannot slide over a statement that modifies an element it references;
   - if it modifies an element, cannot slide over any other statement that references that element.
2. Cut the fragment and paste it at the target.
3. Test.
If the test fails, slide over less code or move a smaller fragment.

Notes
- The simplest rule: fragments cannot swap if any data they both refer to is modified by either. It is not exhaustive (`a = a + 10; a = a + 5;` commute); real judgement needs understanding how the operations compose.
- Side-effect-free code rearranges freely, but you only know a call is side-effect-free by looking inside. Command-Query Separation lets the author trust his own code; in an unfamiliar code base be more cautious.
- Reduce mutable state first (for instance Split Variable on a reused variable).
- With complex data structures interference is hard to see, so tests carry the weight; if they are unreliable, improve them first.
- Conditionals: sliding identical statements out of every leg collapses them into one; sliding into a conditional duplicates the fragment in every leg.

## Split Loop

Use when: a loop does two things, so you must understand both to change either. A split loop computing one value can simply return it, which sets up Extract Function. Usual sequence: Split Loop, Slide Statements (bring each loop's set-up next to it), Extract Function, then Replace Loop with Pipeline or Substitute Algorithm.

Performance objection: iterating twice rarely matters. Keep refactoring separate from optimisation; if the traversal proves to be a bottleneck, merging is easy, and the split often enables bigger optimisations.

Mechanics
1. Copy the loop.
2. Identify and eliminate duplicate side effects, so each copy does only its own work (side-effect-free statements may stay for now).
3. Test.
4. Consider Extract Function on each loop.

## Replace Loop with Pipeline

Use when: a loop filters, maps and accumulates; a pipeline (`filter`, `map`, `reduce`, `slice`) reads top to bottom as a flow of elements. Where the language lacks closures, a loop may remain the idiomatic form (inferred).

Mechanics
1. Create a new variable for the loop's collection (a copy of an existing variable may do).
2. Starting at the top, replace each bit of loop behaviour with a pipeline operation in the derivation of that variable. Test after each.
3. When all behaviour is out of the loop, remove it. If it assigned to an accumulator, assign the pipeline result to it.

Example (CSV lines to offices in India): a skip-header flag becomes `slice(1)` and the flag disappears; a blank-line `continue` becomes `filter`; split becomes `map`; a conditional push becomes `filter` then `map` to the output shape; the loop now only pushes, so assign the pipeline result. Cleanups: inline the result variable, rename lambda parameters, lay the pipeline out like a table. Check laziness and short-circuit semantics when the target language differs (inferred).

## Remove Dead Code

Use when: code is unused. It costs nothing at runtime but a lot in understanding, because nothing marks it as ignorable. Delete it; version control remembers. Do not comment it out.

Mechanics
1. If the code could be referenced from outside (for example a whole function), search for callers.
2. Remove it.
3. Test.

Caveat (inferred): reflection, dispatch by name and published APIs can hide callers from a text search. Code whose only users are tests is dead too: delete the tests with it (ch. 3 Speculative Generality). Clean Code ch. 15 shows commenting out a suspect conditional and running tests as a way to find whether it is dead.

---

## Chooser

| Situation | Use |
|---|---|
| Function uses another module's data more than its own, or callers live elsewhere | Move Function |
| No good home for a group of functions | Combine Functions into Class or Extract Class, then Move Function |
| Field always travels with another record, updated in several places | Move Field |
| Same statements precede or follow every call and belong to the function | Move Statements into Function |
| Same, but they do not conceptually belong | Extract Function around statements and call |
| Part of a function must now vary per caller | Slide to the edge, Move Statements to Callers |
| Caller/callee boundary wholly wrong | Inline Function, Slide Statements, Extract Function |
| Inline code duplicates an existing function and the name fits | Replace Inline Code with Function Call |
| Lines need to be contiguous for an extraction | Slide Statements (after Split Variable if state is reused) |
| A loop computes several things | Split Loop, Extract Function, Replace Loop with Pipeline |

## Recurring safety tactics
- Copy first, then redirect: create the new thing beside the old, make the old delegate, test, then inline or delete the old.
- Use temporary greppable names (`top_`, `zz`); choose the real name last.
- Run static analysis deliberately as a probe after each copy; undefined symbols reveal hidden context dependencies.
- One call site at a time, test after each.
- On failure, revert to the last green state and take a smaller step, or do a preparatory refactoring first.
- If a move is behaviour-preserving only under a data assumption, check the data, add an assertion or log, and run for a while.

Source: Refactoring 2e ch. 8.
