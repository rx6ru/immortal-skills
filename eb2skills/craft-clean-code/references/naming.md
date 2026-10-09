# Naming

Rules, tests and decision questions for names of variables, functions, parameters, types, modules,
files, and by extension database columns, API fields, CLI flags, config keys and test names.
Sources: Clean Code ch. 2 and ch. 17 (N1–N7, G11, G16, G19, G20, G25); A Philosophy of Software
Design (PoSD) ch. 14, ch. 17, ch. 18.

## Why names get this much attention

- A name is documentation that travels to every use site, including completion lists where no
  comment is visible. A precise name removes the need for other documentation and makes errors
  stand out (PoSD ch. 14).
- A vague name can cause real defects. PoSD ch. 14 describes a file-system bug that took months to
  find: `block` meant a physical disk block in some places and a logical block within a file in
  others, and one was used where the other was needed. Reviewers assumed the wrong meaning by
  reflex. `fileBlock` and `diskBlock` would have made the mistake unlikely.
- Complexity from names is incremental: one mediocre name is harmless, thousands are not.
- Choosing a good name takes time and saves more than it takes; rename when a better name appears
  (Clean Code ch. 2). Expect to rename several times as understanding improves (ch. 1, N1).

## The two tests

1. **Isolation test** (PoSD ch. 14): if someone saw only the name, with no declaration, comment or
   surrounding code, how closely could they guess what it refers to? Is there a name that paints a
   clearer picture of what the thing is and is not?
2. **Comment test** (Clean Code ch. 2): if the name needs a comment to explain it, the name fails.
   Fix the name before writing the comment. (This does not mean names replace comments; see
   `comments.md` for what a name cannot carry.)

## Rules

Each rule: statement, reason, and example or check.

### 1. Reveal intent
A name answers why the thing exists, what it does and how it is used. Include what is measured and
its unit where relevant. Code can be structurally simple and still opaque because the reader has to
know what the collection holds, what index 2 means and what the literal 3 stands for (Clean Code
ch. 2 calls this missing context "implicity").

Three escalating fixes: rename the variables and the function; replace literals and indexes with
named constants; replace the primitive structure with a small type that exposes an
intention-revealing predicate.

```python
# before: what is r[2]? what is 3?
def get(lst):
    return [r for r in lst if r[2] == 3]

# after
def overdue_invoices(invoices):
    return [inv for inv in invoices if inv.is_overdue()]
```

### 2. Be precise: not too generic, not too specific
- Too generic is the most common fault: `count` (of what?), `x`/`y` for a text position (pixels?
  characters?), `status`, `data`, `info`, `value`, `flag`, `temp`. Name the specific thing:
  `numIndexlets`, `charIndex`/`lineIndex` (PoSD ch. 14).
- Booleans are predicates. `blinkStatus` says neither what blinks nor what true means;
  `cursorVisible` does.
- Sentinels say what they mean, not that they are special: `NOT_YET_VOTED`, not
  `VOTED_FOR_SENTINEL_VALUE`.
- `result` is acceptable in a function that returns it; it is misleading in a function that
  returns nothing.
- Too specific also misleads: a `delete(Range selection)` parameter suggests the text is always
  the UI selection; `range` is correct.

### 3. Do not disinform
- No word with an entrenched other meaning.
- No container type in a name unless it is that type; `accountList` that is a set or map misleads.
  Prefer `accounts`. Even when it is a list, leaving the type out is usually better.
- No pairs of long names that differ in one mid-word token.
- Spell similar concepts similarly; inconsistent spelling is disinformation because people pick
  from completion lists by name alone.
- No lowercase `l` or uppercase `O` as names.

### 4. Make distinctions meaningful
If two names must differ, the things must differ in a way the names state. Not a misspelling, not a
number series (`a1`, `a2`; write `source`, `destination`), not a noise word (`Info`, `Data`,
`Object`, `the`, a type suffix). `Product`, `ProductInfo` and `ProductData` tell the caller
nothing; neither do sibling functions `getActiveAccount`, `getActiveAccounts`,
`getActiveAccountInfo`. Ask what actually differs and name that. If nothing differs, there should
be one thing.

### 5. Pronounceable and searchable
- Programming is social; a name has to be sayable in discussion. `genymdhms` becomes
  `generationTimestamp`.
- Single letters and bare literals cannot be searched for. Anything used in more than one place
  needs a name a single search will find with few false hits. A named constant beats a literal.

### 6. Length follows scope (N5)
The greater the distance between a name's declaration and its uses, the longer the name should be
(both books; PoSD ch. 14 quotes this as the point of agreement with the Go style). `i`, `j`, `k`
are fine for a short loop whose whole range is visible; replacing `i` with `rollCount` in a
five-line loop obscures. Anything long-lived, exported or far from its use gets a full phrase.
Then remove words that add no distinction: shorter is better as long as it stays clear.
Consistent loop indices: `i` outer, `j` nested.

### 7. One word per concept, one concept per word
- One word for one abstract operation across the codebase: not `fetch` here, `retrieve` there and
  `get` elsewhere for the same thing; not `Controller`, `Manager` and `Driver` for the same role
  (Clean Code ch. 2; G11).
- The converse: do not reuse a word for a different idea to look consistent. If `add` means
  "combine two values into a new one", a method that puts an element into a collection is `insert`
  or `append` (Clean Code ch. 2 "don't pun").
- PoSD ch. 14 states three requirements for a shared name: always use it for that purpose; never
  use it for anything else; keep the purpose narrow enough that everything with that name behaves
  the same. The `block` bug broke the third.
- Two of the same kind in one scope: keep the common name and add a distinguishing prefix
  (`srcFileBlock`, `dstFileBlock`).
- Related function names share phrases so that a missing sibling is noticeable
  (`includeSetupPage`, `includeSuiteSetupPage`, ...; Clean Code ch. 3).

### 8. No encodings (N6)
Do not encode type or scope into names (Hungarian notation, `m_`, `f` prefixes) or prefix
everything with a project or subsystem acronym. Reasons: a decoding burden, worse pronounceability,
and the encoding goes stale when the type changes (`PhoneNumber phoneString`). Tooling shows type
and scope. If an interface and its implementation must be distinguished, leave the interface
unadorned and mark the implementation, because callers should not have to know they hold an
interface.

Limits of this rule are in "Adjustments" below.

### 9. No mental mapping, no cuteness
The reader should not have to translate your name into the concept. Single letters outside tiny
scopes are placeholders the reader must map. No jokes, slang or culture-dependent references.

### 10. Parts of speech
- Types: noun or noun phrase (`Customer`, `AddressParser`). Words such as `Manager`, `Processor`,
  `Data`, `Info`, `Helper` usually hide an unnamed responsibility; treat them as a prompt to look,
  not a ban, since frameworks impose such names.
- Functions: verb or verb phrase (`postPayment`, `deletePage`). A one-argument function should
  form a verb/noun pair with its argument (`writeField(name)`).
- Accessors, mutators and predicates follow the language's convention (see Adjustments).
- Where constructors would be overloaded, prefer named factory functions that describe the
  arguments (`Complex.fromRealNumber(23.0)`).

### 11. Solution-domain, then problem-domain vocabulary
Readers are programmers: use the standard technical term where one exists (queue, visitor, cache,
factory), including pattern names in type names (N3). Where none exists, use the domain expert's
term so a maintainer can ask about it. Use the project's shared domain language consistently.

### 12. Context: enough, not gratuitous
Most names are not meaningful alone. Supply context by placing them in a well-named type, function
or namespace; prefix (`addrState`) only when that is impossible. Do not add context that every name
already shares (an application acronym on every class); it defeats completion and makes names
non-reusable. The type is `Address`; instances may carry the role (`customerAddress`). When real
distinctions exist, name them precisely (`PostalAddress`, `MAC`, `URI`).

A group of loose variables whose meaning depends on the algorithm around them is a sign that a
type is missing; making them fields of a type named for the concept gives each a context and
makes extraction of small functions possible without passing them around (Clean Code ch. 2).

### 13. Names at the right level of abstraction (N2)
Name for the abstraction, not the current implementation: `Modem.dial(phoneNumber)` breaks for
connections that have no phone number; `connect(connectionLocator)` does not.

### 14. Names describe everything the thing does (N7, G20, N4)
- Side effects belong in the name: a `getX()` that lazily creates X is `createOrReturnX`.
- State mutation versus new value: `date.add(5)` leaves both the unit and the semantics open.
  `addDaysTo` / `increaseByDays` for mutation; `daysLater` / `daysSince` for a new value.
- A pair like `doRename` calling `renamePage` tells the reader nothing about the difference;
  prefer a long precise name (`renamePageAndOptionallyAllReferences`), acceptable because it is
  called from one place.
- If you have to read the implementation or documentation to know what a call does, rename, or
  restructure so the pieces can be named well.

### 15. Explanatory variables and named constants (G19, G25, G16)
- Break a calculation into named intermediate values. The source says this is hard to overdo;
  others find long runs of temporaries noisy, so apply it where the expression's meaning is not
  evident.
- Replace unexplained literals with named constants. Exceptions: values universally recognised in
  self-explanatory code (`hourlyRate * 8`, `radius * PI * 2`; a constant named `TWO` is absurd).
  Counter-exception: long well-known literals such as pi still get a name, because readers do not
  check their digits and precision should not vary between uses. Strings and numbers in tests
  count too (`HOURLY_EMPLOYEE_ID`).

## Red flags

| Flag | Recognition | Response |
|---|---|---|
| Vague name (PoSD ch. 14) | Broad enough to refer to many things: `count`, `data`, `info`, `status`, `result`, `x`, `block`, `temp`, `value`, `flag` | Name the specific abstraction: units, which entity, what true means. Split a variable that serves several purposes. |
| Hard to pick a name (PoSD ch. 14) | You cannot find a simple, precise, intuitive name | The entity may lack a clean definition or do several things. Reconsider the factoring, then name the result. |
| Name needs a comment (Clean Code ch. 2) | A declaration followed by a comment explaining the name | Rename. |
| Ambiguous pair (N4) | Two identifiers differing by pluralisation, a noise suffix or one mid-word token | Name the real difference or merge. |
| Stale encoding (N6) | A type or container word in a name that no longer matches the type | Rename without the encoding. |
| Split vocabulary (G11) | Same concept under several verbs; one verb with two meanings | Pick one word per concept and migrate. |
| Hidden effect (N7) | Simple verb on a function that does more | Put the effect in the name or remove the effect. |

## Decision questions

- **How long?** Proportional to scope, then trim words that add no distinction.
- **Technical or domain word?** A standard technical term if one exists; otherwise the domain
  expert's word.
- **Need to tell two things apart?** Ask what differs and name it. If nothing differs, merge.
  Never append `2`, `Info`, `Data`, `New`, `Tmp`.
- **Feels like it needs a prefix?** Prefer enclosing it in a type, namespace or module.
- **Adding an operation similar to existing ones?** Same semantics: reuse the established verb.
  Different semantics: a different verb.
- **Literal in an expression?** If it could be searched for, misread or reused, name it.
- **Readers say a name is cryptic?** Lengthen it. Readability is decided by readers, not writers
  (PoSD ch. 14).
- **Cannot name it?** Design problem first, naming problem second.

## Adjustments for language and codebase

These are adaptation notes in the source notes' caveats, not the books' own text.

- Language conventions outrank the specifics (G24, N3). `get`/`set`/`is` is the JavaBean
  convention; Python uses properties and `is_`/`has_`; Go discourages `Get` and favours short
  receiver and local names; C# prefixes interfaces with `I`. Follow the idiom and apply the
  reasoning within it.
- The case against Hungarian notation and member prefixes assumes static types and a highlighting
  editor. In dynamically typed code a unit or kind suffix (`timeout_ms`, `user_ids`,
  `html_escaped`) is useful and consistent with "state the unit". The surviving principle: do not
  encode what the compiler already enforces, and do not encode something that can silently go
  stale. Encoding semantic kind (safe versus unsafe string) is widely defended and is not what the
  rule attacks. A leading underscore for private members is a light convention many teams keep.
- An `Impl`-style suffix is itself widely criticised; name the implementation for what
  distinguishes it (`InMemoryShapeFactory`). The core is: do not burden the abstraction's name.
- Short names in small scopes or with mathematical convention (`x`, `y`, `n`, `dx`) are fine under
  the scope-length rule. PoSD ch. 14 records the Go view that long names obscure what code does,
  and answers that a short name is fine when it means the same thing everywhere; what breeds bugs
  is one short name reused for several meanings.
- Where two values of the same primitive type must not be mixed (two kinds of block number),
  distinct names help, and distinct types help more where the language makes them cheap
  (inferred in the notes; PoSD discusses only names).

## Verify

- Read the code aloud; every identifier should be sayable and the sentence should make sense.
- Cover the bodies and read only names and call sites; predict what each does, then check.
- Search test: each important constant or concept is found by one search with few false hits.
- Lexicon check (inferred in the notes): list the verbs used for retrieval, creation, deletion
  and conversion in the module; each concept maps to one verb and each verb to one concept.
- Search a recurring concept's names across the codebase: one name per concept, no name serving
  two concepts.
- After a type change, no name still states the old type or unit.
- For each boolean: is it a predicate, and is the meaning of true evident at the use site?
