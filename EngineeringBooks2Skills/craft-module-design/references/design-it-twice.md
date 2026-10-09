# Design it twice

A short, bounded procedure for comparing alternatives before committing to a significant design
decision. Source: APOSD ch. 11, with supporting material from ch. 3 and ch. 6 and the
architecture-prototype checklist from Pragmatic Programmer ch. 2.

## When to use it

Use for decisions that are costly to change once code depends on them:

- the interface of a module, class or internal API that several callers will use;
- the decomposition of a feature or system into major modules;
- a data model or representation that the rest of the code will be shaped around;
- the implementation strategy of a module where simplicity or performance is at stake.

Do not use for every function. The cost argument assumes the unit is small enough that sketching
alternatives takes an hour or two against days or weeks of implementation; larger modules deserve
more exploration and repay it more. For a small request, one sentence naming the alternative you
considered and why you did not take it is enough.

## Why

The first idea is unlikely to be the best structure. Comparing designs is also how design judgement
is built: seeing why one option is better teaches you to rule out bad options faster next time.
Capable people resist this because first ideas have usually been good enough; eventually problems
get hard enough that they are not. This is about the problems being hard, not about ability.

## Procedure

1. Name the decision in one sentence ("the interface of the class that manages the text of a file
   for the editor").
2. Sketch at least two alternatives that are radically different from each other. Variations on one
   theme teach little. Sketch only the most important operations, not every feature.
3. If you are sure there is only one reasonable approach, design a second anyway, however poor you
   expect it to be. Its weaknesses show what the first is getting right.
4. Write the calling code for the main use cases against each alternative. A few lines each.
5. List pros and cons. For an interface the most important criterion is ease of use for the
   higher-level code. Then:
   - Is one interface simpler?
   - Is one more general-purpose?
   - Does one allow a more efficient implementation?
   - Which hides more (fewer decisions visible to callers)?
6. Choose one, or combine features of several.
7. If none is attractive, generate more, driven by the problems of the ones you have. When every
   candidate forces callers to do the same extra work, that shared work is the signal that the
   abstraction is at the wrong level.
8. Repeat at the next level down. After the interface, do it again for the implementation, where
   the criteria shift to simplicity and performance.
9. Record the alternatives and the reason for the choice where a future reader will find it: a
   design note, the PR description, or a short comment near the interface. Rationale that lives
   only in a commit message is easily lost (APOSD ch. 16).

## Worked example (APOSD ch. 11)

Decision: the interface of an editor's text class.

| Alternative | Operations | Caller experience | Efficiency |
|---|---|---|---|
| Line-oriented | insert, modify, delete whole lines | Callers must split and join lines for partial-line edits and for multi-line operations such as cutting a selection | Fine |
| Character-oriented | insert or delete one character | Callers must loop for any multi-character edit | Likely much slower: one call per character |
| Range-oriented | insert a string at a position; delete the range between two positions, across lines | Matches what the higher-level code does; no extra text manipulation in callers | Allows efficient bulk operations |

The first two both push text manipulation up into the callers. That is a red flag: if there is a
text class, it should do the text manipulation. Noticing what the first two had in common is what
led to the third. The operations the higher-level code performs are neither single characters nor
single lines, so the interface should not be either.

Then the second round, for the implementation: a list of lines, fixed-size blocks, or a gap buffer,
compared on simplicity and performance.

## Comparison criteria in full

Use these as column headings when the decision is larger.

| Criterion | Question | Source |
|---|---|---|
| Caller ease | How much code do the main use cases need? Any loops, glue or conversions that belong in the module? | APOSD ch. 11, ch. 6 |
| Interface size | How many methods, parameters, ordering rules and special cases must callers know? | ch. 4 |
| Common case | Is the main use one obvious call with defaults? | ch. 4 |
| Generality | Could a second, different client use it unchanged? Is any method named after one caller's feature? | ch. 6 |
| Hiding | Which decisions does each alternative keep inside? What changes outside if the representation changes? | ch. 5 |
| Layer fit | Does it offer a different abstraction from what it sits on? | ch. 7 |
| Who carries the hard part | Does the module or its callers handle the unavoidable complexity? | ch. 8 |
| Error surface | How many error cases and exceptions does each expose? | ch. 10; see `craft-error-handling` |
| Efficiency | Does it permit an efficient implementation of the common operations? | ch. 11, ch. 20 |
| Likely changes | For two or three plausible changes, how many places change under each? | ch. 2, ch. 3 |

## Checklist for a decomposition sketch

When the decision is how to divide a feature or system into parts, sketch the parts on paper before
writing code and ask (Pragmatic Programmer ch. 2, on prototyping architecture):

- Are the responsibilities of the major components well defined and appropriate?
- Are the collaborations between them well defined?
- Is coupling minimised?
- Can you identify potential sources of duplication?
- Are the interface definitions and constraints acceptable?
- Does every module have an access path to the data it needs, when it needs it? This last question
  is the one that most often turns up surprises.

Such a sketch is a prototype in the book's sense: it answers a few questions and is thrown away.
Choosing between prototypes and incremental end-to-end builds as a delivery approach is covered in
`craft-planning-and-estimation`.

## Note template

Keep it short. Adapt freely; the template itself is an adaptation, not from the books.

```
Decision: <what is being decided>
Main uses: <two or three calling scenarios>

Option A: <name>
  Sketch: <key signatures>
  Caller code: <a few lines for the main use>
  For: ...   Against: ...

Option B: <name, radically different>
  Sketch: ...
  Caller code: ...
  For: ...   Against: ...

Chosen: <A | B | combination>, because <the consideration that decided it>
Not chosen because: <one line each>
Revisit if: <the change in circumstances that would reopen this>
```

For architecture-level decisions with long-lived consequences, use the decision record format in
`arch-decisions-and-tradeoffs` instead.

## Verification

Marked inferred in the notes, consistent with the chapter:

- Evidence exists that alternatives were considered: a note listing the options and trade-offs.
- Caller code for the top use cases was sketched against the chosen interface, and no rejected
  candidate had materially simpler caller code.
- The final interface does not require callers to perform manipulations that conceptually belong in
  the module.
- The alternatives were really different (different abstraction level or different division of
  responsibility), not two spellings of one design.
- The time spent was proportionate: small next to the implementation effort it informed.

## Limits

- The aim is comparison, not exhaustiveness. Two or three alternatives are usually enough; the book
  makes no claim that more are needed.
- It does not replace learning from implementation. Problems surface while building; when they do,
  revisit the design instead of patching around it (APOSD ch. 1, ch. 3).
- It is not a whole-system design phase. The same book rejects designing everything up front.
