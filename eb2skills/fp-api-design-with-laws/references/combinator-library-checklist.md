# Combinator library checklist

Review questions for a composable API, each answerable by looking at code or running something. Use
it on a design you just produced or on an existing library under review. Sources are chapters of
Functional Programming in Scala, 1st ed. ("FPiS"). Items the notes mark as inferred carry
"(inferred)".

How to report: for each failed item give the operation, the observation, and the smallest change that
fixes it. Do not report items that do not apply to the library's size; see the last section.

## A. Starting point

- [ ] There is a written smallest use case, a few lines long, that the API was designed from.
      (FPiS ch. 7, ch. 9)
- [ ] The call site was designed before the representation; the public signatures do not mention
      substrate types that the user has no reason to see (thread handles, raw sockets, engine
      objects). (ch. 7)
- [ ] Every public operation has a one-line statement of meaning that does not refer to the
      implementation. (ch. 7, ch. 9)

## B. Values and interpretation

- [ ] Operations return values that can be passed to other operations. None returns nothing, prints,
      or reports only by side effect. (ch. 7, ch. 8)
- [ ] Constructing or combining values performs no observable effect. Check: build a large expression
      with a recording fake resource and assert zero calls before the interpreter runs. (ch. 7)
- [ ] Exactly one kind of operation (the interpreter) touches resources, blocks or performs I/O, and
      it receives its resources as parameters. No global pool, clock, connection or random source.
      (ch. 7, ch. 8)
- [ ] No combinator calls the interpreter or a blocking wait internally. Search the implementation
      for the blocking call; it should appear only at the outer edge. (ch. 7)
- [ ] Results carry what a combiner needs: on failure, the cause and enough context; on success, the
      value. Values shown only to people may be strings; anything computed with has a type. (ch. 8)
- [ ] Result types name their cases. No "empty means success" or boolean flags whose meaning must be
      remembered. (ch. 8)
- [ ] Errors raised by user-supplied functions are caught at the interpreter and reported with the
      input or position that caused them; continuations always complete. (ch. 8; ch. 7 leaves this
      as a gap in its own implementation)

## C. Operations

- [ ] Each operation does one job. No operation both combines and sets a policy (where it runs, how
      it reports, how big). Signs of failure: a trivial input does unnecessary work; callers wish for
      both a strict and a lazy version. (ch. 7)
- [ ] The primitive set is listed, and each primitive has one of these reasons: needs the
      representation; carries information nothing else carries; adds expressive power; measured
      efficiency. (ch. 7, ch. 9)
- [ ] Derived operations are implemented only through primitives and other derived operations. Check
      by reading: no access to private fields or constructors of the main type. (ch. 7)
- [ ] There is no primitive that could be derived without loss. Try deriving each from the others.
      (ch. 7, ch. 9)
- [ ] Operations are as polymorphic as their meaning allows; no type-specific duplicates of a general
      operation. (ch. 8, ch. 9)
- [ ] There is a constructor for a plain value (`unit`/`pure`/`of`/`succeed`) and a transform
      (`map`). (ch. 7, ch. 9)
- [ ] There is a way to combine independent values (`map2`/`zip`/`product`), and it does not go
      through dependent sequencing unless the type has no independent meaning. (ch. 7, ch. 12)
- [ ] Dependent sequencing (`flatMap`) is present only if a use case needs a later step chosen by an
      earlier result, and that use case is recorded. (ch. 9, ch. 12)
- [ ] For "then" and "or else" operations the later argument is lazy or thunked, and a recursive
      definition terminates. Check with a recursive example on empty and non-empty input. (ch. 9)
- [ ] Choice operations document their bias and backtracking rule. (ch. 9)
- [ ] Cross-cutting concerns the user cares about (error messages, context, positions, timeouts,
      cancellation) are expressed through operations in the API and not left to the implementation's
      discretion. (ch. 9)
- [ ] Generalised operations carry the general name. A `flatMap` is not called `chooser`. (ch. 7)
- [ ] Convenience syntax delegates to the primary definitions; there is one implementation of each
      operation. (ch. 9)

## D. Laws

- [ ] Equality for the main type is defined, and a test helper implements it. (ch. 7)
- [ ] Laws are written down next to the interface, each with what it guarantees.
- [ ] At least some laws came from the model of the domain and not from reading the implementation.
      (ch. 7)
- [ ] The `map` identity law is tested. (ch. 7, ch. 9, ch. 11)
- [ ] If the type has `unit` and `flatMap`: left identity, right identity and associativity are
      tested. (ch. 11)
- [ ] If the type has `unit` and `map2`: identity, associativity and naturality are tested. (ch. 12)
- [ ] If there is a combine operation with an empty value: associativity and identity are tested for
      every instance, composed ones included; functions between such types are tested for structure
      preservation where intended. (ch. 10)
- [ ] Any annotation meant to be meaning-free (scheduling, labelling, grouping) has a law saying so,
      tested under the least favourable environment. (ch. 7)
- [ ] Derived operations that also have a hand-written fast path are tested for agreement with the
      derived definition.
- [ ] Laws that hold only conditionally state the condition in the documentation and in the test.
      (ch. 7)
- [ ] The laws were attacked: there is evidence of tests with empty input, throwing functions,
      minimal resources, deep nesting and large size. (ch. 7)

## E. Representation

- [ ] The representation is not exposed. A realistic client compiles using the public interface only.
      (ch. 9)
- [ ] The representation contains what each primitive needs and no more; a component is not given
      power it should not have (for example the ability to replace its input). (ch. 9)
- [ ] Internal mutation, callbacks or locks are unobservable from outside, and the unsafe entry
      points are not public. (ch. 7)
- [ ] Repetition and recursion are stack-safe on large input. Test with ten thousand or more
      elements. (ch. 9 footnote)
- [ ] Repetition of a component that can succeed without making progress terminates (inferred).
- [ ] On a bounded resource pool, deeply nested compositions complete. Test with a pool of one.
      (ch. 7)
- [ ] Building a large description does not use more memory than the input warrants. (ch. 7)
- [ ] Combined operations respect budgets such as timeouts (a combined wait subtracts time already
      spent). (ch. 7)

## F. Abstraction fit

- [ ] Each generic function is written against the weakest interface that suffices. (ch. 12)
- [ ] Where independent combination would do, dependent chaining is not used. Look for chains whose
      later steps ignore earlier results. (ch. 12)
- [ ] Where the requirement is "report all problems", the combining operation accumulates. Test with
      two independent failures. (ch. 12)
- [ ] Reductions use an identity and an associative combine, and the identity is correct for the
      operation. (ch. 10)
- [ ] Aggregates that are not associative are computed through a summary type and a final projection.
      (ch. 10)
- [ ] Chunked or parallel reduction preserves chunk order when the combine is not commutative
      (inferred).
- [ ] Standard names are used only where the standard laws hold. (ch. 11)
- [ ] The library does not force its whole API through a generic interface; type-specific operations
      exist beside the generic ones. (ch. 11)

## G. Usability

- [ ] Real client code reads close to the problem statement; where it does not, a helper is missing.
      (ch. 8)
- [ ] Common patterns have derived helpers. (ch. 8, ch. 9)
- [ ] Defaults (counts, sizes, limits) are chosen and documented. (ch. 8)
- [ ] Failures say which component failed (labels on composed items). (ch. 8)
- [ ] Error output is structured data formatted at the edge, with location where applicable; inner
      context is kept or deliberately trimmed. (ch. 9)

## H. Red flags

Stop and reconsider the design if you see any of these.

| Red flag | Likely cause | Reference |
|---|---|---|
| A `run`/`get`/`await` inside a combinator | Description and interpretation mixed | `design-method.md` step 3 |
| Tests pass on a large pool and hang on a small one | Blocking inside pooled tasks | `worked-evolutions.md` section 2 |
| The same state value used twice in succession | State threaded by hand | `worked-evolutions.md` section 1 |
| Many lines of unwrap, compute, rewrap | Missing combinator | `design-method.md`, "Awkwardness as a signal" |
| A new primitive for every new use case | Primitives not general enough; missing dependent sequencing or missing generalisation | `design-method.md` step 11 |
| Laws that read like the implementation line by line | Laws derived from code, not model | `design-method.md` step 7 |
| Recursive definition overflows or never returns | Strict later arguments; non-stack-safe repetition | `worked-evolutions.md` section 4 |
| Only the first error ever reported | Dependent chaining over independent checks | `choosing-an-abstraction.md` |
| A parallel or chunked result differs from the sequential one | Non-associative combine, wrong identity, or lost order | `choosing-an-abstraction.md`, monoid |
| "Expected X" messages from the wrong alternative | Missing backtracking control around a shared prefix | `worked-evolutions.md` section 4 |
| Global configuration needed before the library can be used | An operation is acting where it should describe | `design-method.md` step 4 |

## I. Scaling the checklist to the task

| Size of API | Apply |
|---|---|
| One or two functions, one caller | A (first item), B (first two items) |
| A small internal module with a few combinators | A, B, C, the `map` and identity items of D, G |
| A library with several clients or a public package | Everything |
| Adding one operation to an existing library | C (primitive or derived, one job), D for the new operation, F |
| Reviewing an aggregation or reduction only | F (reduction items), D (combine item) |

## Evidence to attach to a review

- The primitive list with reasons.
- The law list with a test name for each, and the run output.
- The environments and sizes the tests covered.
- For each failed item: the operation, what was observed, the proposed change.
