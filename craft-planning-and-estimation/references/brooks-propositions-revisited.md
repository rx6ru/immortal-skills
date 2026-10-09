# Brooks's propositions revisited: what he kept, revised or retracted

Contents: 1 How to use this file; 2 Retractions and revisions; 3 Propositions by chapter with status; 4 Dated material; 5 Source caveats

Sources: MMM ch. 18 (Brooks's own propositions, numbered chapter.item, with 1995 bracketed comments), ch. 19 (what he retracts and why), ch. 17, ch. 20 notes. Status labels here (stands, revised, retracted, obsolete, contested) are my reading of the notes; "Brooks says" marks his own verdict.

## 1. How to use this file

Before applying a Brooks rule, find it here. Use "stands" items directly. For "revised" or "retracted" items, use the 1995 position. For "contested" items, see the decision rule in the row. Item numbers follow the book's chapter.item scheme so a claim can be traced.

## 2. Retractions and revisions

| Item | 1975 claim | 1995 status | What to do now |
|---|---|---|---|
| 11.6 (ch. 11) | Plan to throw one away; you will anyhow | Retracted in ch. 19: "too simplistic", tied to the waterfall model | Land a thin end-to-end skeleton, grow it, show it early. Throwaway mocks only for interface feedback; never ship a prototype. See `delivery-strategy.md` |
| 2.8 (ch. 2) | 1/3 planning, 1/6 coding, 1/4 component test, 1/4 system test | Not struck, but ch. 19 says waterfall taints the whole book, starting with this rule | Use as a test that specification, verification and integration are planned; do not apply as a formula. See `estimating.md` |
| 7.14, 7.15 (ch. 7) | Information hiding is "a recipe for disaster"; everyone sees everything | Reversed: "Parnas was right, and I was wrong" | Show the interfaces fully, keep interiors changeable. See `conceptual-integrity.md` section 9 |
| 8.4 (ch. 8) | Effort grows as size^1.5 | Boehm's data: 1.05 to 1.2 | Use "superlinear". See `estimating.md` |
| 2.11 (Brooks's Law) | Adding manpower to a late project makes it later | Stands as the best zeroth-order approximation, refined: always costlier, not always later; add early not late | See `staffing-and-partitioning.md` |
| 16: packages not more general | Packages had not become much more general or customisable | Revised in ch. 17: "I underestimated both the degree of package customizability and its importance" | Check for a package first. See `tools-and-build-vs-buy.md` |
| 9.10, 9.13 | Transient-area sizing; quick and squeezed versions of components | Obsolete (virtual memory, cheap RAM) | Budget thinking survives; these specifics do not |
| 12.16 | The only reasonable systems language is PL/I | No longer true | Ignore |
| 11.2 | A pilot plant is equally necessary yet not routine | Now common as the beta; the alpha (a limited-function prototype) is also advocated | Use both |
| 6.8 | Telephone interpretations | Email now | Use a searchable record |
| 7.8 | Each member should see all workbook material | Should be able to see all; the Web would suffice | Link, do not print |
| 13.17 | Change quanta should be very large or very small; small frequent ones are unstable | A Microsoft team makes small frequent quanta work by rebuilding nightly | Contested; see the rule in `delivery-strategy.md` section 9 |
| 5.4 | OS/360 as the second-system example | Adds Windows NT as a 1990s example | Fine |
| 12.7, 12.17, 13.9 | Block scheduling; batch persists for some work; plan debugging sessions | Still true in 1995 | Keep |
| 11.13 | Numbered versions with freeze dates | Now standard | Keep |

Other 1995 positions (ch. 19): architect and conceptual integrity "more convinced than ever"; men-months nonlinear confirmed by Boehm; people matter most confirmed (COCOMO team quality is the largest factor, four times the next); the shrink-wrapped industry was the biggest surprise; software engineering is "not hopeless but merely immature" (chemical engineering analogy: about 50 years from rules of thumb to mathematical models).

## 3. Propositions by chapter with status

### Ch. 1 The Tar Pit
- 1.1 A programming systems product costs about 9x the component programs written for private use; two independent factors of about 3 (productising; integrating). Stands (rule of thumb).
- 1.3 Woes: perfection demanded; objectives and dependencies set by others; painstaking labour; the project converges more slowly the nearer the end; threatened with obsolescence before completion (the paper tiger beats the real one unless real use is wanted). Stands.

### Ch. 2 The Mythical Man-Month
- 2.1 More projects have gone awry for lack of calendar time than for all other causes combined. 2.2 Some tasks cannot be hurried without spoiling the result. 2.3 All programmers are optimists. 2.4 and 2.5 Pure thought-stuff leads us to expect few implementation difficulties, but ideas are faulty, so there are bugs. 2.6 Cost-accounting confuses effort with progress. 2.7 Partitioning costs training and intercommunication. Stand.
- 2.8 Schedule split: revised (see above). 2.9 and 2.10 Lack of data and lack of courage to defend estimates. Stand.
- 2.11, 2.12 Brooks's Law and its three added-effort mechanisms (repartitioning, training, intercommunication). Stand with refinements.

### Ch. 3 The Surgical Team
- 3.1 Very good professionals are about 10x as productive as poor ones. 3.2 No correlation with experience in the data (Brooks doubts the universality). 3.3 to 3.5 A small sharp team is best but too slow for big systems; 3.6 brute-force scaling is costly and yields unintegrated systems; 3.7 the chief-programmer team combines integrity with many helpers. Stand; strict hierarchy softened by later practice.

### Ch. 4 Aristocracy, Democracy and System Design
- 4.1 Conceptual integrity is the most important consideration. 4.2 Function-to-conceptual-complexity ratio is the test [1995: a measure of ease of use, valid across simple and difficult uses]. 4.3 One mind or a few agreeing minds. 4.4 Separate architecture from implementation [1995: for small projects too]. 4.5 Someone must control the concepts. 4.6 Discipline is good for art. 4.7 An integrated system is faster to build and test. 4.8 Architecture, implementation and realisation can proceed in parallel [1995: hardware and software design too]. Stand.

### Ch. 5 The Second-System Effect
- 5.1 Early, continuous communication gives the architect cost readings. 5.2 How the architect influences implementation (suggest, do not dictate; be ready to show a way; quietly and privately; forego credit; listen). 5.3 The second system is the most dangerous. 5.5 Assign a priori byte and microsecond budgets to functions. Stand.

### Ch. 6 Passing the Word
- 6.1 Results must be written by one or two people. 6.2 Define what the architecture does not prescribe. 6.3 and 6.4 Formal and prose definitions; one is the standard, the other derivative. 6.5 An implementation can serve as the definition, with formidable disadvantages. 6.6 Direct incorporation. 6.7 At least two implementations initially. 6.8 Telephone log (email now). 6.9 The independent product-testing organisation is the project manager's best friend and daily adversary. Stand.

### Ch. 7 Why Did the Tower of Babel Fail?
- 7.1 to 7.3 Failure of communication and, as a consequence, organisation; communicate in as many ways as possible. 7.4 to 7.13 Project workbook (structure imposed on documents the project produces anyway; design it early; timely updating critical; show what changed and its significance). Mostly stand (medium updated). 7.14 and 7.15 reversed. 7.16 to 7.21 Organisation reduces communication; the tree reflects authority; actual communication is a network; each subproject needs a producer and a technical director; any of three relationships works. Stand.

### Ch. 8 Calling the Shot
- 8.1 Do not estimate total effort by estimating coding and multiplying. 8.2 Data from small isolated systems does not apply. 8.3 Effort grows as a power of size. 8.5 Only about 50% of time is programming and debugging (Portman). 8.6 Productivity ranges with interaction (Aron: 1.5 to 10 KLOC per man-year). 8.10 Productivity is constant in elementary statements. 8.11 A high-level language can raise productivity up to about 5x. Stand (absolute numbers dated; 8.4 revised).

### Ch. 9 Ten Pounds in a Five-Pound Sack
- 9.1 to 9.9 Size is a cost; set targets; budget resident size and accesses; tie budgets to function assignments; suboptimisation; the manager's most important function is a total-system user-oriented attitude; decide option granularity early. Stand in principle. 9.10 and 9.13 obsolete. 9.14 to 9.16 Strategic breakthrough over tactical cleverness; representation is the essence of programming. Stand.

### Ch. 10 The Documentary Hypothesis
- 10.1 to 10.12 A few documents are the manager's pivots (objectives, spec, schedule, budget, organisation, resources); writing focuses thought; the chief daily task is communication; the management total-information system rests on an invalid model. Stand (tooling dated).

### Ch. 11 Plan to Throw One Away
- 11.3 to 11.5 The first system is barely usable; shipping the throwaway costs. 11.6 retracted. 11.7 to 11.13 Accept change; plan systems and organisations for it; numbered versions. 11.20 to 11.27 Maintenance: 40% or more of development cost for a widely used program; cost rises with users; a fix has a 20 to 50% chance of a new defect; rerun the whole test bank; design to eliminate or illuminate side effects. 11.28, 11.29 Lehman-Belady entropy. Stand with the caveat that refactoring plus tests helps.

### Ch. 12 Sharp Tools
- 12.1 to 12.12 Common tools plus personal ones; own target machine; instrument it; block scheduling; logical simulator; playpen, integration, release libraries; performance simulator built early. 12.13 to 12.19 High-level language and interactive programming. Principles stand; 12.16 obsolete.

### Ch. 13 The Whole and the Parts
- 13.1 to 13.8 Define the product well; have an outside group scrutinise the spec; top-down design; structured programming. 13.9 to 13.17 Plan debugging; two hours at the desk per two-hour session; debugged components first; scaffolding up to about half of product size; control changes; add one component at a time; quantise updates (13.17 contested). Stand.

### Ch. 14 Hatching a Catastrophe
- 14.1 to 14.18 A year late one day at a time; sharp milestones; estimate behaviour; hustle; critical-path charts and their value in making them; status versus action information; scheduled versus estimated dates; Plans and Controls. Stand (hustle culture contestable).

### Ch. 15 The Other Face
- 15.1 to 15.15 Documentation is as important as the face to the machine; draft user docs before building; nine items; ship mainline, barely legitimate and illegitimate test cases; internals overview with five kinds of content; flow charts oversold; keep docs in the source; say why. Stand (flow chart advice dated).

### Original epilogue
- E.1 Software systems are among the most intricate things humanity makes. E.2 The tar pit will stay sticky a long time. Stand.

## 4. Dated material

Absolute productivity numbers (KLOC per year), PL/I and flow-chart advice, microfiche and workbook mechanics, batch and target-machine scheduling, OS/360 and S/360 specifics, WIMP interface details and its predicted decline, 1995 reuse landscape, DOD-STD-2167. What lasts is in the sections above.

## 5. Source caveats

- Ch. 3: the notes lack the last pages (scaling the surgical team to very large projects and the communication-pattern figure); ch. 4 to 7 supply the idea.
- Ch. 11: the notes lack the pages on maintenance introduction; the 40% figure comes from the ch. 18 summary of the proposition, not from ch. 11 text.
- Brooks warned that his 1995 opinions are less grounded in large-project experience than the 1975 ones.
- Figures in several chapters (graphs, tables such as the Bell Labs data) were lost in extraction and were reconstructed from prose in the notes; treat any number from those tables as approximate. The rules of thumb used in this skill come from the running text.
- Brooks does not grade each proposition true or false himself; he flags only the revisions listed in section 2.
