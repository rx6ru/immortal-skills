# Conceptual integrity, the architect and passing the word

Contents: 1 The claim; 2 The test: function against conceptual complexity; 3 Architecture, implementation, realisation; 4 Aristocracy and democracy; 5 Architect and builder: rules of engagement; 6 Passing the word: the toolset; 7 Designing for a broad user set; 8 Case: the desktop interface; 9 Information hiding: Brooks reversed himself; 10 Applying it to agents and teams; 11 Warning signs and verification

Sources: MMM ch. 4, 5, 6, 7, 16, 17, 18, 19. Sibling skills: `craft-module-design` (information hiding, interface depth), `arch-decisions-and-tradeoffs` (ADR template and trade-off method).

## 1. The claim

Conceptual integrity is the most important consideration in system design (MMM ch. 4, 18 item 4.1). It is better to omit anomalous features and improvements and reflect one set of design ideas than to include many good but uncoordinated ones. Large projects tend toward disunity not because master designers follow one another but because design is split into many tasks done by many people at once. In 1995 Brooks wrote that he was more convinced than ever.

What integrity means for the user (ch. 19): the product presents a coherent mental model of the application, of the strategies for doing it, and of the user-interface tactics. A coherent interface can still be awkward, and uniformity across applications matters too.

The conflict: integrity wants one mind (or a few agreeing, resonant minds); the schedule wants many hands. Two techniques resolve it: separate architecture from implementation, and use the surgical-team structure (see `staffing-and-partitioning.md`).

## 2. The test: function against conceptual complexity

- A system exists to make the machine easy to use. It buys that with facilities, but the external description of a programming system was 10 to 20 times the size of the bare machine's, so there is more to learn. Ease of use improves only if the time saved specifying functions exceeds the time lost learning, remembering and searching manuals.
- The ultimate design test is the ratio of function to conceptual complexity (ch. 4; ch. 18 item 4.2). Neither function alone nor simplicity alone is the goal.
- For a given level of function, the best design specifies things with the most simplicity and straightforwardness. Few elementary concepts is not enough: if expressing intent needs involuted idiomatic combinations, the burden of lore returns. Both properties come from integrity: the same philosophy, the same balance of desiderata, the same syntax techniques and analogous semantic notions in every part.

Use it as a feature-admission test (adaptation of the book's reasoning): for each proposed feature ask whether it fits the existing concepts or needs its own idioms. If it does not fit, leave it out. Can one person state the guiding concept in a few sentences, and does every feature follow from it?

## 3. Architecture, implementation, realisation

- Architecture is the complete, detailed specification of the user interface. For a CPU, the programming manual; for a compiler, the language manual; for the whole system, the union of manuals the user must consult. Modern equivalents (inferred): public API, CLI, UI, file formats, protocol contract.
- The architect is the user's agent, bringing professional knowledge in the user's interest against salesman and fabricator interests.
- Blaauw: architecture tells what happens; implementation tells how it is made to happen. Clock example: the face, hands and winding knob are architecture; the mechanism is implementation. One architecture with nine implementations (S/360); one implementation serving four architectures; a language standard as the architecture of many compilers.
- A third layer, realisation: the physical or technology embodiment (in software, subroutine conventions, supervisory techniques, search and sort algorithms).
- Check (inferred from the clock example): are implementation choices invisible through the interface? Can the implementation be swapped without a change to the manual?
- Recursion for large products (ch. 19): a master architect partitions the system into subsystems at points where interfaces are minimal and easiest to define rigorously; each subsystem has its own architect reporting to the master on architecture. Architect is a full-time job except on the smallest teams. Brooks insisted even four-person student teams elect a manager and a separate architect, and noted this may be a little extreme but worked.

## 4. Aristocracy and democracy

- Objection: architects are an elite and implementers become cogs. Reply: good ideas can come from implementers and users, but ideas that do not fit the system's basic concepts are left out; if many important incompatible ideas pile up, scrap and start on a new integrated basis.
- Specification is not more creative than implementation, only different. Ease of use depends most on the architect; cost-performance depends most on the implementer.
- Form is liberating: externally supplied architecture focuses implementers on the part nobody has addressed. Unconstrained groups spend effort on architectural debate and shortchange implementation. Evidence: a PL/C team decided to implement PL/I unchanged and unimproved because language debate would consume all effort.
- The OS/360 mistake (ch. 4): the architecture manager had 10 good people and said they could write the external specs in 10 months, 3 more than scheduled. The control program manager had 150 people and said he could do it on time. Brooks gave the specs to the 150. Result: specs 3 months late, much lower quality, a system costlier to build and change; Brooks estimated it added a year to debugging. Cause: the siren song of putting 150 people to work. It is a single case; the principle is that spec authorship by many dilutes integrity and the calendar time saved is lost later.
- Three objections to architect-written specs: they will be too rich in function and ignore cost (a real danger; see section 5 and `scope-and-second-system.md`); architects get all the fun (an illusion); implementers sit idle (an illusion of timing).
- Parallel phasing: implementers need not wait. They can start with vague assumptions about the manual but clearer ideas about technology, and well-defined cost and performance objectives: module boundaries, table structures, pass breakdowns, algorithms, tools; they keep communicating with the architect. Integral systems go together faster and test faster. A wide horizontal division of labour is replaced by a vertical one (architect, implementer, realiser), which simplifies communication and improves integrity.

## 5. Architect and builder: rules of engagement (ch. 5)

What bounds the architect's inventive enthusiasm is thorough, careful, sympathetic communication with the builder.

- Interactive discipline: a building architect works to a budget confirmed by contractor bids. A software architect can get cost readings from the builder almost any time, but usually from one contractor, who may inflate estimates if displeased. Early and continuous communication gives the architect cost readings and the builder confidence, without blurring responsibilities.
- Given a too-high estimate the architect has two moves: cut the design, or challenge the estimate by suggesting cheaper implementations. The second is emotionally charged. Rules:
  - the builder owns implementation creativity, so suggest, do not dictate;
  - always be ready to show a way to implement anything specified, and accept any other way that meets the objectives as well;
  - make such suggestions quietly and privately;
  - be ready to forego credit.
- The builder often counters with architecture changes, and is often right: a minor feature can have unexpectedly large cost once implemented. Listen to those suggestions.

## 6. Passing the word: the toolset (ch. 6)

How can ten architects keep the conceptual integrity of a system that a thousand people build?

1. Written specification (the manual). Necessary, not sufficient.
   - Describe everything the user sees and refrain from describing what the user does not see; that is the implementer's freedom. The architect must be able to show an implementation of any feature but must not dictate it.
   - Changes are quantised: dated versions appearing on a schedule, so implementers do not chase continuous change.
   - Style: precise, full, accurate. Each definition repeats its essentials, since users read single entries. Precision beats liveliness.
   - Few pens: the System/360 Principles of Operation was written by two people, though ideas came from about ten. Writing prose forces many small decisions (for example how the condition code is set after each operation) that must be made consistently.
   - Define what is not prescribed (where models, copies or revisions may differ) as carefully as what is.
2. Formal definitions. English is not a precision instrument; formal notation is precise and tends to be complete (gaps show conspicuously) but lacks comprehensibility. Expect both forms. "Never go to sea with two chronometers; take one or three": one form is the standard and the other a clearly labelled derivative. Almost all formal definitions embody an implementation, so they over-prescribe; state that the definition covers only externals and say what those are. Today's analogues (adaptation): schema or OpenAPI as the formal form, prose guide and examples as the explanatory form, a conformance suite as the check.
3. Implementation as definition ("ask the machine"). Pros: experiment settles every question unambiguously and quickly. Cons: it over-prescribes even externals (invalid input yields side effects users depend on; emulating a 1401 on S/360 exposed 30 widely used "curios"); unplanned, inelegant answers to sharp questions; confusion over which is the standard; the implementation must be frozen while it serves as the standard.
4. Direct incorporation. Define interface declarations once and require implementations to include them at compile time, referencing fields by symbolic name so that additions need recompilation, not edits. Modern equivalents (inferred): shared schema or IDL, generated types, one package imported by all users. Ch. 19: Apple built the interface into ROM, making it easier for third-party developers to use than to bypass; this achieved cross-application integrity without coercion. General rule: make the standard thing the easiest thing to use.
5. Conferences and courts. A weekly half-day conference of architects and implementers' representatives, chief architect presiding. Proposals distributed in writing beforehand; creativity first (invent many solutions), then a few are detailed as precisely-worded manual change proposals, circulated and decided. Consensus if it emerges, otherwise the chief architect decides. Minutes kept; decisions disseminated formally, promptly and widely. It works because the same group meets weekly, everyone can make binding commitments, written proposals force focus, and decision power is clear. An annual (Brooks would run it every six months) "supreme court" resolves the backlog of minor appeals just before major freezes, with the project manager presiding.
6. Multiple implementations. With several implementations built at once and strict compatibility, when machine and manual disagree the manual wins because fixing the errant implementation costs less than revising everything that followed the manual. Build at least two implementations of a language definition initially.
7. The telephone log. Implementers ask the architect rather than guess; each architect logs every question and answer; weekly the logs are combined and distributed to all. Modern equivalent (inferred): decision log, ADRs, a searchable issue tracker.
8. Product test. An independent product-testing organisation is the project manager's best friend and daily adversary: it checks products against the spec, acts as the surrogate customer, and finds where the word was not passed. It must operate early and simultaneously with design.

## 7. Designing for a broad user set (ch. 19)

- Featuritis and the paradox: a general-purpose tool is harder to design than a special-purpose one because the differing needs of diverse users must be weighted. Define the user set explicitly: each designer carries a different implicit image of the user. Write down who they are, what they need, what they think they need, what they want.
- Frequency guessing (named technique): for each attribute of the user set, postulate values and their frequencies, write them down, debate them, note which decisions hinge on which guesses, and spend money to firm up only the guesses that important decisions depend on (informal sensitivity analysis). Rule: it is far better to be explicit and wrong than to be vague. Brooks knew of no published a priori frequency estimates compared with a posteriori data. A tool for tracking design decisions and rationale (gIBIS) is mentioned, unused by him.
- Power against ease of use: one of the hardest architect issues. Dual encoding (menu items with shortcut keys shown beside them) gave a smooth novice-to-power-user path with an undo safety net.

## 8. Case: the desktop interface (ch. 19)

Integrity through a single extended metaphor (the desktop): overlapping windows, drag and drop, icons, folders, trash, cut and paste all follow. Consistency is so strong that the one inconsistency (dragging a diskette to the trash to eject it) jars. Transferable points: pick a metaphor and extend it consistently; look for the single inconsistency; give novices visible choices (menus show the valid verbs at each state) and experts shortcuts. Brooks's predictions about the interface's replacement are dated; the noun-and-verb analysis (a command needs a verb and a noun at once) applies to any command interface.

## 9. Information hiding: Brooks reversed himself

In 1975 (ch. 7) Brooks called Parnas's information hiding a recipe for disaster and said every worker should see all material (a project workbook, in OS/360 more than 10,000 pages). In 1995 (ch. 19; ch. 18 items 7.14 and 7.15): "Parnas was right, and I was wrong." Information hiding, today often embodied in object-oriented programming, is the only way of raising the level of software design. He still notes both extremes can fail: openness lets people know the detailed semantics of the interfaces they build to; hiding is robust under change. Most of the benefit comes from encapsulation plus prebuilt libraries built to product standard. Planning consequence: let workers see the interface fully and the interiors only as needed; keep the shared record about interfaces and decisions, not every internal. Depth and design of interfaces: `craft-module-design`.

## 10. Applying it to agents and teams

(Adaptation from the notes' suggestions.)
- One owner (human or lead agent) for the interface or contract; sub-workers implement against a frozen or explicitly versioned spec. Do not let parallel workers each invent API shapes.
- Start scaffolding (data structures, module boundaries, tests, tooling) while the spec is still firming up; do not let implementers redefine the interface silently.
- Test every "just add this good idea" request against the system's concept first.
- Treat the spec as a contract: versioned, with a "not specified" list, with every clarification logged where all workers see it, with an independent tester working from the spec rather than the implementation.
- Prefer direct incorporation to policing: a shared generated type or template that is easier to use than to bypass.

## 11. Warning signs and verification

Warning signs:
- Committee-designed interfaces with many good ideas that do not compose; features that need lore to combine.
- Implementers debating interface questions instead of building.
- The largest group given spec authority because it is idle; spec authority diffused so that nobody controls the concepts.
- Two inconsistent mental models of the user in one product.
- Teams changing local assumptions without broadcast.
- Using an existing implementation as the standard without saying so.

Verification:
- A single named owner of the user-facing interface, backed visibly by the manager.
- A dated, versioned spec exists and all implementers work from the latest version.
- Exactly one declared source of truth (prose or formal); the others are derived and labelled.
- Unspecified behaviours are listed as unspecified.
- Two independent implementations (or one implementation and an independent test suite) pass the same conformance tests (inferred).
- Every clarification answer is recorded and broadcast.
- Each new feature has been tested against the guiding concept, and a user-set document with frequency guesses exists where the user base is broad.
