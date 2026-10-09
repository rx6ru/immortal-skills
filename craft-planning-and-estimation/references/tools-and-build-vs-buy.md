# Tools, essence and accident, build versus buy

Contents: 1 Essence and accident; 2 The four essential difficulties; 3 Evaluating a claimed breakthrough; 4 Candidates and verdicts; 5 Attacks on the essence; 6 Build versus buy and reuse; 7 Object-oriented methods and abstraction level; 8 Methodologies and tools: Pragmatic view; 9 Shared tools and automation; 10 AI coding assistants (adaptation); 11 Dated material; 12 Warning signs and verification

Sources: MMM ch. 12, 16, 17, 18, 19; PP ch. 7 (section 40, Tips 58, 59), ch. 8 section 42 (Tip 61), appX (Tip 50). Sibling: `arch-decisions-and-tradeoffs` for recording a buy or build decision as an ADR.

## 1. Essence and accident (MMM ch. 16)

- Essential tasks: fashioning the complex conceptual structures that compose the abstract software entity (data sets, relationships among data items, algorithms, invocations of functions). Accidental tasks: representing that abstraction in programming languages and mapping it onto machine languages within space and speed constraints.
- "The hard part of building software is the specification, design, and testing of this conceptual construct, not the labor of representing it." Syntax errors are fuzz next to conceptual errors.
- Arithmetic argument: unless accidental work is more than 9/10 of all effort, shrinking it to zero cannot give a tenfold improvement. If a is the accidental fraction, the best speedup from eliminating it is 1/(1 - a): a of 0.5 gives at most 2x; a of 0.9 gives 10x.
- Brooks's opinion in 1995 (ch. 17): the accidental part is now about half or less. It could be measured; no respondent claimed 9/10. Glass and Conger measured requirements specification at about 80% intellectual and 20% clerical (ch. 20 notes); Brooks knows of no end-to-end measure.
- Bug finding splits between the two: conceptual flaws (failing to recognise an exception case) against representational flaws (a pointer or allocation mistake).
- Headline: no single development in technology or management technique promises by itself even one order-of-magnitude improvement within a decade in productivity, reliability or simplicity. Skepticism is not pessimism: there is "no royal road, but there is a road". An order of magnitude combined over time is plausible (though in 1995 he judged his 1986 expectation of the combined effect too optimistic; DeMarco had not seen 10x in ten years).
- Herzberg: environmental factors cannot raise productivity however good, but can lower it when bad. Much past progress removed negative factors (awkward machine languages, slow batch turnaround, poor tools, memory limits). Distinguish removing a drag (bounded gain) from adding a motivator or attacking essence.
- Hardware is the anomaly: six orders of magnitude of price-performance in about 30 years, because manufacture became a process industry. Design remains labour-intensive in both hardware and software (ch. 19).

## 2. The four essential difficulties

| Difficulty | Meaning | Planning consequence |
|---|---|---|
| Complexity | No two parts alike above the statement level; scaling adds different elements that interact nonlinearly. Abstracting the complexity away abstracts away the essence | Team communication cost, unreliability from unenumerable states, hard-to-use functions, side effects on extension, hard overview, turnover is a disaster |
| Conformity | Software must conform to the arbitrary complexity of human institutions and systems it interfaces, which were designed by different people | Interface conformity work cannot be designed away inside the software alone |
| Changeability | All successful software gets changed: users stretch it, and it outlives its machine | Plan for change as normal (`delivery-strategy.md` section 10) |
| Invisibility | Software is unvisualisable; diagrams are several overlaid graphs (control flow, data flow, dependency, time sequence, name space) | One diagram does not capture a system; enforce link cutting until at least one graph is hierarchical; choose the view for the question |

These are not hopeless (ch. 17): each can be ameliorated. Much conceptual complexity comes from the arbitrary complexity of the application; much from the implementation itself (data structures, algorithms, connectivity), which can be avoided by growing software in higher-level chunks.

## 3. Evaluating a claimed breakthrough

Apply in order (ch. 16, 17 synthesis):
1. Does it reduce work on the conceptual construct (what to build, the spec, the design, verifying the design) or on expressing it?
2. If it attacks expression only, bound the gain by the share of total effort that expression occupies. If conceptual work dominates, expect marginal gain.
3. Is there an independent happy user who paid for it and reports the claimed gain? Not the inventor or vendor. Brooks buys after talking to bona fide pleased paying customers.
4. Is the cost front-loaded, and over how many projects does it pay back? (Retraining, generalising.) Do not expect a methodology change to speed up the first project.
5. Can you buy or reuse instead of building?
6. Does a new tool pay off by the design discipline it forces (Ada's training in modularity, abstract data types, hierarchy), not by its features?

## 4. Candidates and verdicts (1986 judgments, with what survives)

| Candidate | 1986 verdict | Reason | What survives |
|---|---|---|---|
| High-level languages | Most powerful stroke; at least 5x | Freed programs of accidental complexity (bits, registers, channels) | Limit: they supply constructs the programmer imagines; later elaboration becomes burden |
| Time-sharing | Improves productivity (less than languages) by preserving immediacy | Slow turnaround is accidental | Gain stops when response passes the human noticeability threshold, about 100 ms |
| Unified programming environments | Integral-factor gains | Integrated libraries, uniform file formats, pipes and filters | A new tool applies to any program in standard formats |
| Ada and newer languages | Useful, not a breakthrough | Payoff from forced modern design training | A language often pays through the discipline it forces |
| Object-oriented programming | Most hopeful of the fads, still only removes accident | Abstract data types and hierarchy (two orthogonal ideas); a 10x gain needs type-specification underbrush to be 9/10 of design work | Ch. 17, 19 revise: real promise is higher-level reusable tested chunks |
| Artificial intelligence | No | Parnas's split; speech and image recognition do not change programming practice. "The hard thing about building software is deciding what to say, not saying it" | See section 10 |
| Expert systems | Modest, real value as disseminators of good practice | Separate application complexity from the program; power from richer knowledge bases; need an articulate expert | Changeable domain knowledge separate from the engine; tools that spread best practice are valuable because the gap between best and average is wide; a diagnostic knowledge base should mirror the product's module structure |
| Automatic programming | No, except in narrow domains | A euphemism for programming in a higher-level language than currently available | Three-property test (below) |
| Graphical programming | No | Flowcharts are poor abstractions; software is unvisualisable; each diagram shows one dimension | Pick the view for the question |
| Program verification | No labour saving; valuable for specific cases | Proofs are so much work; a perfect proof shows conformance to spec; much of the essence is debugging the specification | Passing tests or proofs shows conformance to the spec, not that the spec is right |
| Environments and tools | Marginal from here | Big-payoff problems already solved | A shared current source of project detail persists |
| More powerful workstations | No magic | Once think-time dominates, faster machinery does not help | General rule |

Three-property test for when generation from a problem statement works reliably (Parnas on "automatic programming"): the problem is characterised by few parameters; there are many known solution methods forming a library; and extensive analysis yields explicit rules for choosing a method from the parameters. Examples: sort generators, differential-equation integrators.

## 5. Attacks on the essence (ch. 16)

1. Buy versus build (section 6).
2. Requirements refinement and rapid prototyping (`requirements-and-specs.md`, `delivery-strategy.md`).
3. Incremental development: grow, do not build (`delivery-strategy.md` section 5). The building metaphor of specifications, components and scaffolding has outlived its usefulness.
4. Great designers. Good practice can be taught and moves practice from poor to good; it does not move good to great. Great designs come from great designers. The gap between great and average approaches an order of magnitude. Products with passionate fans come from one or a few minds (Unix, APL, Pascal, Smalltalk, Fortran); committee products contrast (Cobol, PL/I, Algol, MVS/370, MS-DOS). Brooks recommends identifying top designers early (often not the most experienced), mentoring, a career development plan with apprenticeship and solo design assignments, and opportunities to interact. Put design authority with the strongest designer available rather than a committee.

## 6. Build versus buy and reuse

### Ch. 16 (1986)
- "The most radical possible solution for constructing software is not to construct it at all."
- Any product that really exists is cheaper to buy than to build afresh. Benchmark: even at $100,000, a purchased product costs about one programmer-year (1986 dollars), and delivery is immediate. Purchased products tend to be better documented and maintained.
- Qualifier: "immediate" only for products that actually exist and whose developer can point the prospect to a happy user. Ask for a satisfied reference before counting on delivery.
- Software cost is development cost, not replication cost; n copies multiply the developers' productivity by n.
- What changed acceptance of packages in the 1980s was the hardware-to-software cost ratio: the buyer of a $2M machine could afford $250K of custom payroll, the buyer of a $50K machine cannot, so adapts procedures to the package. Rule: when custom software would cost a large fraction of the value of the platform or problem, change the process to fit the package rather than the package to fit the process.
- Giving non-programmer knowledge workers general tools (spreadsheet, writing, database, statistics) and turning them loose is one of the most powerful productivity moves.

### Ch. 17 (1995) revisions
- Mass-market software is nearly a different industry: when packages sell in thousands or millions, quality, timeliness, product performance and support cost dominate rather than development cost.
- For information systems work the most dramatic gain is to buy off the shelf what would have been built. Brooks: "I underestimated both the degree of package customizability and its importance" (correcting ch. 16).
- Reuse: the best way to attack the essence is not to build it at all. Experienced programmers' private libraries gave about 30% reused code by volume; corporate reuse aims for 75% and needs library support and credit for reuse. Reusable modules on the market were 1 to 20% of normal development cost.
- The cost of making a component reusable is about 3x a one-shot (Brooks, the productising cost; Yourdon said 2x).
- Consumer-side barriers (Snyder): if the engineer perceives that finding and verifying a component costs more than writing one, a duplicate is written; perception matters, not true cost. Reuse works where reconstruction cost is high (arcane, enormous intellectual input per line) and discovery cost is low (a rich standard nomenclature, as in mathematical software). To increase reuse, lower the cost of discovery and verification (naming, documentation, examples).
- Parnas: reuse needs good design and very good documentation. Ken Brooks: it is hard to anticipate which generalisation will be needed; he was still bending his UI library on the fifth use. Do not generalise beyond the uses actually in view.
- Large vocabularies (ch. 17): the higher the level, the more primitive elements to learn. People learn in sentence contexts, so publish many examples of composed products and not only libraries of parts; organise by kind of thing; expect incremental learning in context.
- Open-source package ecosystems have since made reuse far more common (dated-note in ch. 17 notes: the consumer-side argument explains why).

### Ch. 19: buy and build
- Radical gains in robustness and productivity come only from moving up a level and composing modules. Mass-market packages as platforms (for example a tracking system built on a shrink-wrapped database and communications package) attack the essence: the package is a big, tested module with a proper interface whose internal conceptual structure need not be designed.
- Metaprogramming: building a new layer that customises a package for a subset of users. Four levels of user: as-is; metaprogrammer on a single application; external function writer; metaprogrammer using several applications as components (poorly served, highest potential). A metaprogramming interface wanted for the last: the ensemble controls the user interface, can invoke any application function as if typed by the user, receives output parsed into logical units of suitable data types, and has a scripting language to coordinate (Unix pipes, AppleScript). Modern analogue (inferred): an API, CLI or scripting surface that returns structured output.
- Obstacles: packages are stand-alone and unchangeable by the metaprogrammer, and package builders have little incentive to serve as components.

### Decision procedure (synthesis)
1. State the need in one sentence and the fraction of platform value that custom work would cost.
2. Search for an existing library, package or service. Require evidence that it exists, works, and has a referenceable happy user.
3. Estimate honestly the cost to find, understand and verify it against the cost to rebuild. Do not trust the instinct that rewriting is cheaper (ch. 17).
4. Check for scripting hooks, structured output and control of the interface; without them the package cannot be a component.
5. Weigh adapting your process to it against building. If adapting, record the decision (ADR).
6. If building for reuse, budget about 3x, add composed examples, and deliver at product quality or label it non-reusable.

## 7. Object-oriented methods and abstraction level (ch. 17)

OO bundles four separable disciplines: modularity with clean interfaces, encapsulation, inheritance with hierarchy and virtual functions, and strong abstract data typing. Any can be had without the OO languages. Adoption was slow because programmers aim low in abstraction (small encapsulations yield small benefits; prefer large-grained classes matching client concepts), because OO was taught as a language not as a design approach (Parnas), and because cost is front-loaded and benefit back-loaded and managerial courage is scarce. Lesson: the abstraction level of the building blocks determines the payoff; choose domain-level abstractions the client recognises.

## 8. Methodologies and tools: Pragmatic view (PP section 40)

- Methods that aim to make programming like engineering (structured programming, chief programmer teams, CASE, waterfall, spiral, ER diagrams, OMT, UML) each gather disciples and are replaced; only structured programming has had a long life. Adrift developers cling to the latest fad like shipwreck victims to driftwood.
- Tip 58, shortcomings: diagrams are meaningless to end users so no real formal checking by the real user (prefer showing a prototype); methods encourage specialisation and us-versus-them; most combine a static model with event charts and cannot show runtime dynamism, which pushes toward static relationships that should be knitted together dynamically.
- Glass (1999): research on seven technologies (4GLs, structured techniques, CASE, formal methods, cleanroom, process models, OO) found initial hype overblown; benefits appear only after a significant productivity and quality drop while adopting. Never underestimate adoption cost; treat the first projects as learning.
- Tip 59: treat methodologies as a toolbox, take the parts that work, and refine monthly. Do not grant authority to an artefact because of its volume or the price of the tool that made it. A stack of diagrams and 150 use cases is still someone's fallible interpretation. Red flag: "the class diagram is the application, the rest is mechanical coding".
- Review questions: are these notations an effective way of communicating with these users? How would you tell the method is bringing benefit, and can you separate the benefit of the tool from the team gaining experience? Where is the break-even between future benefit and productivity lost while adopting? For any process artefact: name the decision it informs and the person who reads it; if neither exists it is ceremony.
- Tip 50 (from the card): do not use wizard code you do not understand; wizards generate reams of code, so understand all of it before adopting.

## 9. Shared tools and automation (MMM ch. 12; PP ch. 8 section 42)

- Tools are a project asset. Private toolsets fail because the essential problem is communication, tool lifetime is short, and common development of general tools is more efficient. Keep a toolmaker per team for specialised needs. Plan: computer facility, operating system, language policy, utilities, debugging aids, test-case generators, text processing.
- High-level language and interactive programming were Brooks's two most important tools. Objections to a high-level language (cannot do what I want, object code too big, too slow) were answered: fix speed by replacing 1 to 5% of the generated program with hand code after full debugging. Prototype algorithms in a high-productivity notation.
- PP: Tip 61, do not use manual procedures. People are not repeatable; a script runs the same instructions every time and can be put under source control. Build from a scripted tool even when using an IDE; goal: check out, build, test and ship with a single command. A build takes an empty directory and a known environment and produces the final deliverable (see `done-and-verification.md`).
- Estimate the value of automation: time wasted on repeated procedures against time to build it (PP uses a loaded annual cost per developer; the figure is dated, the method survives).
- Keep generated artefacts regenerated by the build, not hand-edited.

## 10. AI coding assistants (adaptation, not a claim of the books)

The books predate current AI assistants; their argument can be applied the way Brooks applied it to the candidates of his time.
- Fast code generation attacks accident (typing, syntax, boilerplate, tool glue). Expect large gains on those parts, bounded by 1/(1 - a). The essential parts remain: deciding what to build, the spec, conformity to external interfaces, and verifying the concept.
- Therefore an agent should spend scarce effort on specification, requirements validation, interface contracts and test design, not on code volume, and should treat requirement change and interface conformity as normal.
- Treat a user's first statement as a hypothesis and propose a mainline-only prototype.
- Before writing code, search for an existing package; estimate discovery and verification cost explicitly.
- Do not promise speed-ups from a new framework or method on the first project.
- Cheap iteration changes how one works (ch. 19: an order of magnitude in change-time makes a qualitative difference, enabling exploration of many alternatives early). The conceptual choice among alternatives still needs one coherent owner.
- Agent-generated small snippets are "sprint" data (`estimating.md` section 4): they do not extrapolate to integrated, tested, documented systems.

## 11. Dated material

Dollar figures; named products (Ada, PL/I, Works); the screen-size argument; 1986 AI forecasts; the 1995 state of reuse; microfiche; target-machine scheduling in blocks (the principle, exclusive blocks for shared environments, survives).

## 12. Warning signs and verification

Warning signs:
- A vendor claim of 10x from a language, tool or process; a claim supported only by its inventor.
- Belief that a diagram or model captures the full system.
- Treating requirements as fixed.
- Building custom what a general tool or package already does; a product "available immediately" with no existing satisfied user.
- Reusable components with no examples or documentation; abstractions at data-structure level when the problem is domain-level.
- Expecting a methodology change to pay on the first project.
- Private toolkits; no shared build; expensive tooling treated as proof of design quality.

Verification:
- State what fraction of total effort the proposed improvement can touch; check measured gains against the 1/(1 - a) bound.
- Classify recent defects as conceptual or representational to see where effort goes (inferred).
- The vendor can name a happy user; delivery is shown on a trial, not promised.
- A newcomer can find and use a reusable component correctly from its examples alone.
- Every increment leaves a working system.
- Tests passing means conformance; separately confirm the spec with the user.
