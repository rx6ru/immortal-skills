# Higher-order functions, polymorphism and following the types

Source: FPiS ch. 2 (2.4.2, 2.5, 2.6), ch. 3 (3.3.2 on argument grouping). Items marked (adaptation) or (inferred in notes) are not the book's own claims.

## Contents

1. Extract a function parameter
2. Extract a type parameter
3. Following types to implementations
4. The combinators curry, uncurry, compose, partial
5. Argument order and inference
6. Dynamic languages and bounded generics
7. Verify

## 1. Extract a function parameter

Functions are values: they can be assigned, stored, passed and returned. A higher-order function (HOF) takes or returns functions.

Move: two near-identical functions differ only in which sub-computation they call (`formatAbs` and `formatFactorial` differ only in `Int => Int`). Add a parameter `f` for that sub-computation and make both callers one-liners.

General recipe: when two pieces of code differ only by a sub-computation, make the sub-computation a function parameter.

Naming: HOF parameters are conventionally `f`, `g`, `h`. A short name is fine because the HOF has no opinion on what the function does, only on its type.

## 2. Extract a type parameter

A monomorphic function fixed to one type that shows the same structure elsewhere should be parametrised over the type and over whatever operation was type-specific. The book's example: `findFirst(strings, key)` returning the index or -1 becomes `findFirst<A>(items, predicate)`. Two changes happened: equality against a key became a predicate argument, and `String` became a type variable. Using the same type variable in two places forces those two arguments to agree.

This is parametric polymorphism (generics), distinct from subtype polymorphism. Another instance: `isSorted<A>(items, ordered: (A, A) => bool)` injects the comparison, so the function works for any element type and ordering, and it short-circuits at the first out-of-order pair.

Lambdas (anonymous functions) are the way to write the arguments inline; all mainstream languages now have them (closures in Go and Rust, lambdas and functional interfaces in Java).

## 3. Following types to implementations

If a function is polymorphic in `A`, the only things it can do to an `A` are the operations passed in as arguments. So the signature often determines the implementation, sometimes uniquely.

Procedure (derived from the `partial1` walkthrough):

1. Start from the return type. If it is a function type `B => C`, write the lambda header `b => ???`.
2. Ask which values of the needed result type you can produce. The only sources are values in scope (arguments and lambda parameters) and applications of the given functions. A `C` can only come from calling `f: (A, B) => C`, so `f(a, b)`.
3. Leave placeholders (`???` in Scala) and let the compiler's typed holes guide the next step.
4. Check parametricity: if your code ignores an argument, or could be written without using every input, you probably missed a requirement.

The point the book makes: day-to-day FP is fitting building blocks together in the only way that makes sense; and composition over one-liners has the same character as composition over functions backed by millions of lines.

How it degrades (inferred in notes): works best in languages with expressive static types and generics (TypeScript, Rust, Kotlin, Swift, Java generics, C#). With trait or interface bounds (Rust, C++, Go) more operations are available so uniqueness weakens, but the principle holds: operations available = arguments + bounds. In dynamic languages carry the signature in type hints or JSDoc and treat it as the design document; the compiler will not catch mistakes, so lean on tests.

## 4. The combinators curry, uncurry, compose, partial

Each has exactly one total implementation given its type:

| Name | Type | Implementation |
|---|---|---|
| curry | `(A, B) => C` to `A => B => C` | `a => b => f(a, b)` |
| uncurry | `A => B => C` to `(A, B) => C` | `(a, b) => f(a)(b)` |
| compose | `f: B => C`, `g: A => B` to `A => C` | `a => f(g(a))` |
| andThen | `f andThen g` | `g compose f` |
| partial1 | `a: A`, `f: (A, B) => C` to `B => C` | `b => f(a, b)` (closure captures `a`) |

A closure sees variables of its enclosing scope, which is how state and configuration travel without objects.

What they are for (notes, inferred):

- Adapting a function to a callback signature (map a list with a two-argument function by partially applying one argument).
- Pipelines: `pipe(f, g)`.
- Dependency injection by partial application of configuration arguments.

Currying is idiomatic in ML-family languages and Haskell; in TypeScript and Python closures or `functools.partial` do the job. Partial application is the generally useful part; automatic currying is optional.

## 5. Argument order and inference

Put the data first and the callback last (the book curries its HOFs as `dropWhile(xs)(f)` so type information flows left to right and the lambda needs no annotation). That is a Scala inference limitation; the cross-language lesson (inferred in notes): in TypeScript, Kotlin trailing lambdas, and Rust closures the same ordering helps inference; method syntax `xs.map(f)` achieves it with the receiver first. If inference is poor in your language, a method on the collection is an alternative.

## 6. Dynamic languages and bounded generics

- Python and JavaScript: write the type as a hint or doc comment first, then the body. The derivation works the same; tests replace the compiler.
- Go before 1.18 had no generics, so generic HOFs needed `interface{}` or code generation. This is dated; check the module's Go version.
- Unconstrained generics (TypeScript `<A>`, Kotlin `<A>`) let you rely on parametricity. Adding a constraint (`A extends Comparable`) is a deliberate step; prefer passing the operation in (the `ordered` parameter above) unless the constraint is natural.

## 7. Verify

Property-style checks (inferred in notes; use the language's property-testing library, or a loop over random inputs):

- `uncurry(curry(f))(a, b) == f(a, b)`
- `compose(f, identity) == f` and `compose(identity, f) == f`
- `isSorted` agrees with a naive reference for random arrays and random comparators
- A polymorphic HOF you wrote uses all its arguments; if one is ignored, find out why.
- Tail recursion inside such helpers: use the large-input test in `folds-and-recursion.md`.

Review questions with observable answers:

- Do two functions in this diff differ only by a constant, an operator, or one inner call? If so, extract it.
- Does a function mention a concrete type only to call something the caller could pass in?
