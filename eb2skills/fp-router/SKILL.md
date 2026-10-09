---
name: fp-router
description: "Index of the fp-* skills (the functional style of writing code, generalised from Functional Programming in Scala to TypeScript, Python, Rust, Kotlin, Java, Go, Swift and C#) that maps a coding situation to the skill worth loading and says how far to take the style in a given language and codebase. Use when a request mentions functional programming, purity, immutability, side effects, monads, Option/Result, folds, laws or property tests without making clear which aspect is meant, when code is hard to test because logic and effects are tangled, or when deciding whether a functional approach fits the codebase at all. Skip it when one fp-* skill obviously fits; load that skill directly. For general code practice use craft-router."
---

# Functional-style skills: which one, and how far to go

## Purpose

The four fp skills teach one way of writing code at four levels. This index picks the level that
matches the problem and guards against the common failure of the style: importing heavy machinery
into a language or team that gains little from it.

## Pick by the problem

| What you see or were asked | Load |
|---|---|
| A function computes and also writes, sends, prints or reads the clock; tests need mocks or a live service; hidden mutable state; "make this deterministic" | `fp-pure-core` |
| A closed set of variants; null, -1 or thrown errors as results; hand-written loops and recursion; "report every validation error"; lazy sequences | `fp-data-and-errors` |
| Designing a library, DSL or fluent API; the same map/flatMap/combine code repeated across types; "what laws should this satisfy"; mergeable aggregations | `fp-api-design-with-laws` |
| Proposals for an IO or effect type; async code that blocks or deadlocks; stack overflow in long loops; a stream over a file or cursor that leaks or is read after close | `fp-effects-and-streams` |

## The levels, in the order to try them

Each level costs more than the one before. Stop at the first one that solves the problem.

1. **Separate decisions from effects** (`fp-pure-core`). Plain functions that take values and
   return values, with I/O in a thin caller. Works in every language and needs no library. This is
   the level most codebases benefit from.
2. **Make data and failure explicit** (`fp-data-and-errors`). Sum types, exhaustive matching, typed
   results, folds. Cheap where the language has pattern matching and result types; a judgement call
   where it does not.
3. **Design interfaces around laws** (`fp-api-design-with-laws`). Worth it when you are building
   something others compose with: a library, a validation or parsing toolkit, an aggregation.
4. **Represent effects as values with interpreters** (`fp-effects-and-streams`). Pays off when you
   need to swap, test, retry or sequence effects systematically, or need guaranteed resource
   release in streaming code. Highest cost in languages without supporting libraries.

## How far to take it, by language and codebase

| Situation | Guidance |
|---|---|
| Any language, tangled logic and I/O | Level 1 always applies |
| Rust, Kotlin, Swift, modern TypeScript, Scala, F# | Levels 1 and 2 are idiomatic; level 3 where you design a library; level 4 only with an established effect library the team already uses |
| Python, Java, C#, Go | Level 1 fully; level 2 selectively (use the language's own sum-type and optional features, follow local convention on exceptions); levels 3 and 4 as ideas for design and testing more than as types |
| A codebase with an existing style | Match it. Introduce a functional form where it removes a concrete problem, and keep the change local |
| Performance-critical inner loops | Keep a pure interface, allow local mutation inside (see `fp-pure-core`) |

Each fp skill has a `language-mappings.md` with the idiom for each language and how it degrades
where a feature is missing.

## Boundaries with other sets

- Error policy in any style (throw, return, assert, crash) is `craft-error-handling`; the typed
  result toolkit is `fp-data-and-errors`.
- Property-based testing as a technique appears in `craft-testing`; using it to check the laws of
  an API you are designing is `fp-api-design-with-laws`.
- Threads, locks and races are `craft-concurrency`; describing parallel work as a value is
  `fp-effects-and-streams`.
- Module depth and information hiding are `craft-module-design`.

## Verify you routed well

- You can name the concrete problem the functional form removes (a test that needed a mock, a
  missed variant, a leaked handle), not only that the result is "more functional".
- You stopped at the lowest level that solves it.
- The result reads as idiomatic code in the host language to someone who has not read the book.

## Proportion

The book builds everything from first principles to teach; production code should use the
language's and the team's existing tools. Rewriting working imperative code into combinators with
no concrete gain is a cost, not an improvement.

## Sources

Functional Programming in Scala (Chiusano and Bjarnason, 1st ed.), chapters 1 to 15. Cross-language
guidance is adaptation, labelled as such inside each skill.
