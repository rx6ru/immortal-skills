# Review checklist: effect placement

Questions for reviewing a diff, a module or a design for the separation of logic from effects.
Each question has an answer that can be observed in the code or a test run. Citations are to
Functional Programming in Scala, 1st ed. ("FPiS"). (inferred) marks generalisations made in the
study notes; (adaptation) marks checks added for use in a repository.

## How to use

1. Decide the scope first. For a diff, apply the checklist to the code the diff touches, not to
   the whole repository.
2. Establish which effects matter for this program (section A). Without that, later answers are
   arguments about taste.
3. Go through the sections that apply. Record each finding as: location, which question it fails,
   what a caller could observe, and the smallest change that fixes it.
4. Rank findings. A hidden effect that can corrupt results or make failures unreproducible
   outranks a pure function that merely could be extracted.
5. Do not report code that is only plumbing as a finding.

## A. Which effects count here

- [ ] Is there a stated or evident list of the effects correctness depends on (writes, external
      calls, clock where logic depends on time, output where output is the product)?
      (FPiS ch. 14)
- [ ] Are effects that are deliberately ignored (debug logging, metrics, allocation) named as
      such, and is nothing asserting on them?
- [ ] For each effect in doubt: would a caller behave incorrectly if it happened twice, never,
      or in another order? If yes, it belongs in the tracked list.

## B. Locating effects

- [ ] Search the modules claimed to be logic for I/O clients, clock, random, ID generation,
      environment reads and global mutable variables (adaptation). Every hit is either a finding
      or on the ignored list.
- [ ] Which functions return nothing (`void`, `Unit`, `None`)? Each is presumed to exist for an
      effect (FPiS ch. 2). Are any of them in the logic layer?
- [ ] Does any function described or named as a calculation, validation, decision or formatting
      also perform a write or an external call?
- [ ] Does any function read something that is neither a parameter nor a constant?

## C. The core

- [ ] Can each core function be called in a test with literal arguments and no setup of
      collaborators? Try one (FPiS ch. 1).
- [ ] Do core tests compare returned values by equality? Count mocks, spies and patches in those
      test files; the target is zero.
- [ ] Does any core function mutate an argument, a field or a global? (FPiS ch. 14)
- [ ] Does any core function throw for an expected outcome instead of returning it? Throwing is
      on the book's list of effects (FPiS ch. 1). See `fp-data-and-errors`.
- [ ] Does the substitution test hold for the functions claimed pure: equal arguments, equal
      results, any order? (FPiS ch. 1)
- [ ] Are decisions about what to do expressed in the return type (optional, result, enum,
      command record) and not as calls made along the way? (FPiS ch. 13)

## D. Descriptions of effects

- [ ] Is each description an immutable record containing only data, comparable by value?
      (FPiS ch. 1)
- [ ] Does a description hold a client, handle, callback or already-started task? That is a
      finding: it cannot be compared, stored or dropped (inferred).
- [ ] Does it carry exactly the data the eventual call needs, so the executor makes no further
      decisions?
- [ ] Where descriptions are merged or batched: is the merge a function on descriptions, and are
      associativity and preservation of totals tested (inferred)? Does a failed merge return a
      typed error and not throw (FPiS ch. 1 caveat)?
- [ ] Is the introduction of an interface justified by more than one real implementation, or
      does it exist only so a mock can watch a call? (FPiS ch. 1)

## E. The shell

- [ ] Is the shell only: obtain inputs, call the core, execute outputs? Point to any conditional
      on business data in the shell; each is a decision that leaked (FPiS ch. 13).
- [ ] Is there one place per entry point that executes descriptions or runs the effectful
      program? List the call sites (FPiS ch. 13: a single impure entry point).
- [ ] Does the shell obtain clock, random seed and identifiers and pass them down?
- [ ] Is the shell covered by a small number of integration or fake-backed tests, with the
      combinatorial cases tested in the core?
- [ ] Is the policy for a failing effect (stop, continue, compensate) located in the shell or a
      transaction, and stated?

## F. State

- [ ] Is each piece of mutable state (field, global, counter, cursor) either turned into a value
      passed and returned, or held in exactly one known place in the shell? (FPiS ch. 6)
- [ ] Is state threaded by hand across more than a few steps? Look for numbered variables
      (`s1`, `s2`, `rng2`). Check each use for reuse of an older value (FPiS ch. 6).
- [ ] For a state machine: is there one pure transition function, a written rule table, a test
      per rule including the "ignored" cases, and invariant tests (inferred)?
- [ ] Do the same initial state and inputs produce the same outputs and final state on two runs?
- [ ] Do flags that are never true together appear as separate booleans where one enum would do
      (adaptation)?

## G. Time, randomness, identifiers

- [ ] Does any logic call the clock, a global random function or an ID generator directly?
      (FPiS ch. 6)
- [ ] Is the clock read once per operation and passed as a value (adaptation)?
- [ ] If a mutable generator object is passed in, is it created per test and not shared, given
      that reproduction then depends on the number of prior calls? (FPiS ch. 6)
- [ ] Do randomised tests print their seed on failure (inferred)?
- [ ] Is a random integer reduced to a range by remainder? That is biased (FPiS ch. 6).
- [ ] Do any tests patch global time or randomness? Each is a sign the dependency was not
      injected.
- [ ] Are tests free of loose assertions ("is a string", "within a second") that exist only
      because the value could not be controlled?

## H. Local mutation

- [ ] For each mutable structure inside a function claimed pure: is it created or copied inside
      that function? (FPiS ch. 14)
- [ ] Trace every reference to it. Is any stored, returned while retained, captured by an
      escaping closure, iterator, generator or lazy sequence, or passed to an unknown callback?
- [ ] Is anything returned a view over an internal buffer (read-only wrapper, slice, sub-list)?
      A read-only view is not a copy.
- [ ] Is the structure reachable from more than one thread or task (inferred)?
- [ ] Is there a test that the input is unchanged and that results match a simple reference
      implementation (inferred)?
- [ ] Does an internal cache change results, or only speed (inferred)?

## I. Loops and recursion

- [ ] Is recursion used as a loop in a language without guaranteed tail-call elimination? Is the
      depth bounded by something small, or is there a test with a large input? (FPiS ch. 2)
- [ ] Where the language has a tail-call annotation, is it present on recursive loops?
- [ ] Is the recursive call really in tail position (nothing done with its result but returning
      it)?

## J. Proportion

- [ ] Is the separation applied where there is logic worth testing, and not to pass-through
      code?
- [ ] Has an effect type, interpreter or command framework been introduced where a returned
      value would do? The ladder in `separating-effects-procedure.md` (from the notes' decision rules on FPiS ch. 13): factor first; use a description type only when effects
      must be composed, swapped, restricted or made stack-safe (FPiS ch. 13).
- [ ] Is the change the size the task called for? Larger restructuring should be a separate
      proposal.
- [ ] Does the result fit the conventions of the codebase and language well enough that the
      next maintainer will keep it working?

## Reporting format

For each finding:

```
<file>:<line>  <question id, e.g. C3>
Observed: what the code does, and what a caller or test can observe as a result
Risk:     wrong result / unreproducible failure / untestable without doubles / none (style)
Change:   the smallest refactoring that fixes it, with the reference file that describes it
```

Close the review with: the list of tracked effects and where each lives after the proposed
changes; counts of test doubles in core tests; any check that could not be run and why.
