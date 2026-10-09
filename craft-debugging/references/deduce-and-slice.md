# Deduce from code: dependences, slices, smells

Sources: WPF ch. 7 (deducing errors), ch. 9.3 (dynamic slices), ch. 1 (preview), PP ch. 3 "Debugging".

## Contents
1. What deduction gives you
2. Procedure for an agent
3. Control flow and its caveats
4. Reads, writes, controls: data and control dependence
5. Slices and slice operations
6. Smells found from dependences and static checkers
7. Limits and the three risks
8. When to choose deduction
9. Verify

## 1. What deduction gives you

Zero runs needed. The main use of source code in debugging is to split statements into relevant (could have influenced the failing value) and irrelevant (could not, in any run). You ignore the irrelevant ones entirely. The reasoning direction is backward from the failure: something impossible happened, so think backward from the result.

Deduction abstracts over all runs, so its findings hold for every run, provided the abstraction (the source you read, the language semantics) is right.

## 2. Procedure for an agent

(Synthesised in the notes from WPF ch. 7.1-7.6; the ordering is the notes' own.)

1. Confirm the source you are reading is the code that ran: commit, build freshness, PATH, deployed version, generated or transformed code (transpilers, bundlers, macros, decorators, codegen mean the text you read is not what executes).
2. Run the compiler, linter and type checker with all warnings on. Clear or explain every warning in the failing area before deeper work.
3. Choose the slicing criterion: the statement and variable where the wrong value was observed.
4. Go backward: list every definition that can reach that use, including declarations or defaults and "impossible" paths, plus every condition that controls whether each definition or the use executes. Recurse on the ones that matter.
5. At each indirect construct (dynamic dispatch, callbacks, closures, async continuations, event handlers, exceptions, aliases, array or map indices, globals, reflection, monkey-patching, middleware) enumerate the possible targets rather than assuming one. Note where you approximated.
6. If other outputs are correct, dice: discard statements that also feed correct outputs. If several outputs are wrong, take the backbone: look at what they share.
7. If the remaining slice is still large or deduction says "could be anything", switch to observation (`observe-and-trace.md`) and use the dynamic slice of the failing run.

Example of the move (WPF ch. 7.3): `fib(1)` returned garbage. Listing every statement the returned `f` could depend on gave two: the assignment inside the loop and the bare declaration. The declaration is live exactly when the loop body does not run, which is when `n` is 1. Always include the statement that "obviously does nothing" and ask under which control condition it is the live definition.

## 3. Control flow and its caveats

Build the order in which statements can execute: a control flow graph (one node per statement or basic block, an edge when one can directly follow another). Earlier statements can influence later ones, not the reverse. Structured code gives patterned graphs; these break the pattern and make reading harder:

- Jumps and gotos, especially into loops or functions.
- Indirect jumps and function pointers: any statement could follow; in practice tables for dynamic dispatch.
- Dynamic dispatch: for every method call be aware of the possible destinations. A frequent source of misunderstanding.
- Exceptions: control may never reach the official end of a function. Be sure an exception does not go by unnoticed.

Modern instances of the same caveat (adaptation): callbacks, closures, promises and async/await continuations, event handlers, decorators, dependency injection, reflection.

## 4. Reads, writes, controls: data and control dependence

Per statement, tabulate what it reads, what it writes, and what it controls (conditional jumps have two or more successors). "Write" in the general sense includes printing and sending messages; bound it somewhere sensible.

- Data dependence: B depends on A if A writes a variable V that B reads and some path from A to B does not overwrite V in between.
- Control dependence: B depends on A if A's outcome decides whether B executes. Loop bodies depend on the loop head; other statements on function entry.
- The program-dependence graph holds both kinds of edge and reflects every influence within a program.

Two questions it answers: where does this value go to (impact analysis, follow edges forward), and where does this value come from (origin analysis, follow edges backward)? Impact analysis is also the right check on a proposed fix: the forward slice of the changed statement is what you may break.

Programmers already follow dependences implicitly; make it explicit. Tools: "find definitions reaching this use", "find uses of this definition", "what controls this statement", go-to-definition and find-references in an IDE, language server call hierarchies (adaptation).

## 5. Slices and slice operations

A slice is the subset of the program that may influence, or be influenced by, a statement (the slicing criterion). Static backward slices average about 30% of the program (Binkley and Harman, 43 C programs). What is not in a slice is the valuable information: it cannot affect the value.

| Operation | Definition | Use when |
|---|---|---|
| Forward slice | Statements that could be influenced by A | Impact of a suspect value or of a change |
| Backward slice | Statements that could have influenced B | Where could this state have come from |
| Chop | Forward slice of A intersected with backward slice of B | How exactly does suspect A reach symptom B: all paths of influence |
| Backbone | Intersection of two backward slices | Several infected values at different places; find a common origin |
| Dice | Difference of two backward slices | Program is largely correct: subtract the slices of the correct values from those of the infected ones; what remains feeds only infected values |

In the book's example (a loop computing both a sum and a product, with the product wrong), the dice of product minus sum is exactly the two statements that touch only the product. A slice difference is a hint, not proof: it does not always contain the faulty statement (exercise 9.4 asks for a counterexample).

An executable slice also keeps declarations so that it still runs; the book's slices are not required to be executable.

Dynamic slices (one run, about 5% of executed statements) are in `observe-and-trace.md`.

## 6. Smells found from dependences and static checkers

Whenever a failure occurs, run a static checker or the compiler with all warnings to rule out common defect patterns (WPF ch. 7.5). Get rid of smells reported by automated tools before debugging.

| Smell | Dependence signature | Notes |
|---|---|---|
| Read of uninitialised variable | A bare declaration with an outgoing data dependence | May be a false positive (switch over an enum without default) |
| Unused value | A write on which nothing depends | Tools usually restrict to locals |
| Unreachable code | A statement control-dependent on nothing | A deliberate defensive `default:` that prints and exits is a good sign; adding it also removes the uninitialised warning |
| Memory leak | A path from allocation to the last reference dying without deallocation | Early return without freeing |
| Resource misuse | A path from acquire to reference death without release | Streams, locks, sockets, DB handles |
| Null dereference | A path from a possible null assignment to a dereference without a check | Unchecked allocation result |

Typical linter findings (WPF table 7.2, FindBugs for Java): exception ignored, resource not closed, return value ignored, unread or unused field, `equals` misspelled, null dereference.

Redundant operations flag correctness errors (Xie and Engler, Linux kernel): idempotent self-assignment from a copy-paste slip, a value assigned and then immediately overwritten or ignored, dead code from a logging statement without braces that makes the following return unconditional, misleading indentation.

Expect false positives (the FindBugs authors report about half). Rewrite even the harmless smells so they do not hide real ones in the next report.

## 7. Limits and the three risks

Precise dependences are undecidable (does a write to `a[i]` influence a read of `a[j]`? depends on whether i equals j). Tools use conservative approximation: they never omit a real dependence but add spurious ones. With full paranoia (stray pointers, out of bounds indices, calls into code without source) they answer "I don't know" to everything. Constructs forcing approximation: indirect access, pointers and references, function calls (inlining is precise but does not scale and fails on recursion), objects, concurrency.

Three risks of pure deduction and their remedies:

1. Code mismatch: the source is not what runs. Remedy: version control, fresh builds, check which binary or package is executed.
2. Abstracting away: it assumes the compiler, OS, runtime and libraries behave as their semantics say; a defect in the environment cannot be deduced from source. Remedy: observation. Other source caveats: macros and preprocessors, undefined or compiler-chosen behaviour (bites when porting), aspects that weave in code.
3. Imprecision: slices are large. Remedies: add verified constraints (assertions that sharpen what states are possible) or combine with observation, which gives the dynamic slice.

## 8. When to choose deduction

Choose it when: there is no reproducible run yet; you want a cheap first pass; you want claims valid for all runs; you are checking a proposed fix's impact. Avoid relying on it when: the code is heavy on pointers, dynamic dispatch, metaprogramming or concurrency; the source is missing; you suspect the environment.

## 9. Verify

- Every statement you dismissed as irrelevant has no data or control path to the criterion, and you can say why.
- The claimed origin has an unbroken dependence chain to the symptom (a chop) with no overwrite in between.
- You enumerated, not assumed, the targets of every indirect call on the path.
- After a smell-type fix the corresponding static warning is gone.
- For any fix, the forward slice of the changed statement was inspected for unintended impact.
- You confirmed the code you read is the code that ran.
