# Algebraic data types and exhaustive matching

Source: Functional Programming in Scala (FPiS) ch. 3 (sections 3.1, 3.2, 3.5 and the sidebar on ADTs and encapsulation), ch. 4 (Option, Either as ADTs). Items marked (adaptation) are not the book's claims.

## Contents

1. What an ADT is
2. Procedure: from a requirement to an ADT
3. Matching: rules and failure modes
4. Fold per type (the recipe for any ADT)
5. Exposed constructors versus smart constructors
6. Closed versus open sets
7. Smells that call for an ADT
8. Verify

## 1. What an ADT is

An algebraic data type is a type defined by a fixed list of data constructors. The type is the sum (a choice) of its constructors; each constructor is the product (a bundle) of its fields. FPiS ch. 3: `List[A]` has `Nil` (no fields) and `Cons(head, tail)` (two fields, one of them recursive). `Tree[A]` has `Leaf(value)` and `Branch(left, right)`. `Option[A]` is `Some(value) | None`. `Either[E, A]` is `Left(E) | Right(A)`. A tuple is a product ADT with syntax sugar. This "ADT" is not "abstract data type".

Two properties make it useful:

- The set of cases is closed. A tool can check that every case is handled.
- Each case carries exactly the fields that make sense for it. There is no field that is "only valid when state is X".

Polymorphic types take a type parameter (`List<A>`). An empty variant (`Nil`) belongs to every instantiation because it holds no elements. Variance annotations (`+A`) are a Scala detail from encoding constructors via subtyping; skip them in other languages.

## 2. Procedure: from a requirement to an ADT

1. Name the concept and list its variants as the domain describes them (for example a payment is pending, settled with a receipt id, or failed with a reason).
2. For each variant list only its own fields. If you find yourself writing nullable fields or booleans that qualify other fields, split the variant.
3. Mark recursive fields (the tail of a list, the children of a node). Recursive types are legitimate; they need a case with no recursion as the base.
4. Encode with the language's sum type (table in `language-mappings.md`). Put the functions that operate on the type together, in the module or companion that owns it. Convention from the book: lowercase function names mirroring constructors are smart constructors (`cons`, `empty`).
5. For each operation, write one branch per variant. Recursive variants call the operation on their recursive fields.
6. Order branches from specific to general if patterns overlap: the first match wins (FPiS 3.2 puts a special case for `0.0` before the general `Cons`).
7. Decide how partial operations behave on empty or invalid cases (tail of an empty list). The book flags this as the set-up for chapter 4: return Option/Result, not a bogus value (see `typed-errors.md`).

Sketch (TypeScript):

```ts
type Tree<A> =
  | { tag: "leaf"; value: A }
  | { tag: "branch"; left: Tree<A>; right: Tree<A> };

function size<A>(t: Tree<A>): number {
  switch (t.tag) {
    case "leaf": return 1;
    case "branch": return 1 + size(t.left) + size(t.right);
    default: { const _never: never = t; return _never; } // compile error if a case is missing
  }
}
```

## 3. Matching: rules and failure modes

- A match destructures: literals, variables (bind anything), wildcard, nested constructor patterns. A pattern matches when some assignment of variables makes it structurally equal to the value (FPiS 3.2).
- First matching case wins. Overlapping patterns are order-sensitive; verify with a case that hits each branch.
- No matching case is a runtime error in Scala (`MatchError`). That is the failure to design out.
- Typical recursion shape: one case per constructor, base case for the non-recursive one.

Rules for the agent:

1. Match over your own sum type without a catch-all. A wildcard branch turns "I forgot a variant" from a compile error into silent wrong behaviour.
2. A wildcard is acceptable when you really mean "all other cases behave the same and will for any future case". Say so in a comment.
3. Without pattern matching (Go, older Java, C), keep one branch per variant, make the default branch fail loudly (panic, throw, assert unreachable), and add a test per variant. FPiS (inferred) lists the alternatives: `is_empty/head/tail` accessors, `instanceof` chains, tagged switch, visitor, or a polymorphic method on each variant.
4. Do not branch on a type tag outside the module that owns the type if you can avoid it; adding an operation is easy for ADTs, adding a variant touches every operation (section 6).

## 4. Fold per type (the recipe for any ADT)

FPiS 3.4 and exercise 3.29 give the idea: a function over an ADT is a choice of replacement for each constructor. Folding a list with the constructors themselves rebuilds the list (identity). For a tree:

```
fold(tree, onLeaf, onBranch):
  leaf(v)      -> onLeaf(v)
  branch(l, r) -> onBranch(fold(l, ...), fold(r, ...))
```

Recipe (the book states it for tree and list; applying it to every ADT is its generalisation):

1. One function parameter per constructor.
2. That function receives one argument per field of the constructor.
3. A recursive field is replaced by the result of folding it.

Then size, depth, maximum and map become one-liners:

| Operation | onLeaf | onBranch |
|---|---|---|
| size | `_ => 1` | `(l, r) => 1 + l + r` |
| maximum (numbers) | `v => v` | `max` |
| depth | `_ => 0` | `(l, r) => 1 + max(l, r)` |
| map f | `v => Leaf(f(v))` | `Branch` |

(Size counts leaves plus branches, depth is the longest root-to-leaf path, as in exercises 3.25 to 3.28.)

Use the fold when you are about to write the third recursive traversal of the same type. Write explicit recursion when the traversal needs to stop early or carry unusual state; a fold cannot short-circuit when strict (see `folds-and-recursion.md`, `laziness-and-streams.md`).

## 5. Exposed constructors versus smart constructors

The book's position (sidebar, FPiS 3.5): exposing data constructors is normal in FP, because immutable data has no delicate mutable state that outside code could corrupt. Use an ADT when the set of cases is closed, and layer a more abstract API on top if you want information hiding.

The caveat the notes add from outside the book: immutable does not mean valid. If a value must satisfy an invariant (sorted, non-empty, a validated email, an age that is not negative), a raw public constructor lets callers build invalid values. Use a smart constructor that checks and returns Option/Result (the book's `mkName` and `mkAge` do this), and make the raw constructor private or the type opaque.

Decision rule:

| Situation | Choice |
|---|---|
| Any combination of fields is a valid value (list, tree, plain coordinates) | Expose the constructors |
| Values carry a rule beyond their field types | Smart constructor returning a Result/Option; hide the raw constructor |
| Memoisation or caching is part of the invariant (lazy cons cell) | Smart constructor only; building the raw case bypasses the invariant (FPiS 5.2) |

## 6. Closed versus open sets

Inferred in the notes (the expression problem): an ADT makes adding operations easy (write another function with a branch per case) and adding variants hard (touch every operation). If third parties must add variants, use an interface, trait or type class with one implementation per variant instead of a closed sum. If you control all variants and operations change often, use the ADT. In the sealed-hierarchy languages the compiler's exhaustiveness check is the benefit of closing the set; do not close a set that plugins must extend.

## 7. Smells that call for an ADT

(Adaptation, derived from the sections above.)

- A class with a `kind` or `type` string and several fields that are null depending on it.
- Several booleans that cannot all be true together.
- An `Optional`/null field whose presence depends on another field's value.
- A result object with both `value` and `error` fields (use a sum: success or failure, never both).
- `instanceof` or tag checks scattered across modules, each with an `else` that does nothing.
- A function returning a sentinel for "none of the above" because the types have no way to say it.

## 8. Verify

- Exhaustiveness: compile with warnings as errors for non-exhaustive matches where the language has the check (Scala, Rust, Kotlin sealed `when` used as an expression, TypeScript `never` guard). Otherwise a test that feeds one value of each variant to each operation.
- Order-sensitive patterns: a test input for each specific branch plus one for the general branch.
- Smart constructors: invalid input yields the failure value, valid input yields the value, and no code path builds the type directly (search for the raw constructor outside its module).
- Fold checks: folding with the constructors reproduces the input; fold-based size/depth/maximum/map agree with hand-written versions on random trees.
- Deep structures: the default string conversion of a recursive structure can overflow the stack on long lists (FPiS notes this for case-class `toString`); give deep structures an iterative display.
