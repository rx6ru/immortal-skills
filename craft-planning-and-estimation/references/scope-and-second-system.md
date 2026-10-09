# Scope, the second-system effect and budgets

Contents: 1 The second-system effect; 2 Featuritis; 3 Countermeasures; 4 Check the premises; 5 Budgets; 6 Good enough, and when to stop; 7 Rewrite or v2 checklist; 8 Contested and dated points; 9 Warning signs and verification

Sources: MMM ch. 4, 5, 9, 11, 17, 19, 20 notes; PP ch. 1 (Tips 4, 6, 7), ch. 7 (requirements creep, section 36), ch. 8 (Tip 69). Siblings: `craft-refactoring` (changing structure safely, refactor against rewrite at code level), `craft-module-design` (performance design, interfaces).

## 1. The second-system effect (MMM ch. 5)

- An architect's first system is spare and clean: he knows he does not know what he is doing, so he is restrained. During it, frills occur to him and are stored for next time. The second system is "the most dangerous system a man ever designs". The tendency is to over-design with all the shelved ideas, producing a big pile. By the third and later systems, experiences confirm each other (generalisable) and differences mark the particular.
- Examples: the 709/7090 as second system after the clean 704, with an operation set so rich that only about half was regularly used; Stretch, "immensely ingenious, immensely complicated, extremely effective, but somehow crude, wasteful, and inelegant"; OS/360 for most of its designers; a trivial frill of 26 bytes of permanently resident date routine to handle day 366 of leap years, which an operator could have handled.
- Note (ch. 20): the effect applied to OS/360 control programs; compiler teams on their third or fourth systems produced excellent work. Repetition after a proper first system improves quality.
- Second manifestation: refining techniques made obsolete by changed system assumptions. Examples: the linkage editor (the best static overlay facility ever, in a system built on multiprogramming and dynamic allocation); TESTRAN (the culmination of batch debugging when interactive systems and fast compilers were arriving); the scheduler (excellent for fixed batch job streams, nearly uninfluenced by OS/360's needs for remote entry, multiprogramming and interactive subsystems). Effort would have been better spent on the new assumptions.
- Which "second"? (ch. 19) The ch. 5 second system is the second fielded system, the follow-on that invites frills. The ch. 11 "second" is the second try at the first system to be fielded, built under new-project schedule and ignorance constraints that impose a slimness discipline. (The ch. 11 recommendation is separately retracted; see `delivery-strategy.md`.)

## 2. Featuritis (ch. 19)

- With mass-market products the architect designs for a large, amorphous user set. The temptation is to overload with marginal features at the expense of performance and ease of use. The appeal of a feature is visible at the outset; the performance penalty appears only during system test; ease-of-use loss sneaks up as manuals grow fatter. Strongest for long-lived products where the original architect has left, and each request is "evidence the market demands it". The example given was a review calling a word processor big and slow.
- Defend with an explicit user set and frequency guesses (see `conceptual-integrity.md` section 7): write down who the users are, what they need and what they think they need.
- Ease of use improves only if time saved specifying functions exceeds time lost learning and searching (ch. 4). Each added feature must pass the function-to-conceptual-complexity test.

## 3. Countermeasures (ch. 5)

1. The architect cannot skip the second system, but can be conscious of its hazards and use extra self-discipline against functional ornamentation and against extrapolating functions obviated by changed assumptions and purposes.
2. Assign each small function a value: capability x is worth no more than m bytes of memory and n microseconds per invocation. These budgets guide initial decisions and warn implementers during the build. Generalisation (inferred): per-feature budgets for latency, memory, complexity, lines, or dependency weight.
3. The project manager should insist on a senior architect with at least two systems under his belt, stay aware of the temptations, and ask questions that check the original philosophy and objectives are reflected in the detailed design.
4. Interactive cost discipline: early and continuous communication gives the architect cost readings, so features are cut or implementations cheapened before they are built (`conceptual-integrity.md` section 5).

## 4. Check the premises

Before porting or polishing a subsystem in a rewrite or new version, list the system's basic assumptions (batch or interactive, static or dynamic, single user or many, local or networked, human-operated or automated). For each refined subsystem ask whether it still follows from them. If the platform is moving away from the premise, effort is better spent on the new assumptions. Brooks's phrase for building the elaborate tool for the old assumption: "stomach ahead of feet".

## 5. Budgets (ch. 9)

Program size is a cost, aside from running time. "Size itself is not bad, but unnecessary size is." Compare a size cost with what the feature gives users and with alternative uses of the same money.

Size control is the project manager's job, part technical and part managerial: study users and applications to set sizes; subdivide and give each component a target; know the size-speed trade-offs, which come in big quantum jumps; keep a reserve to allocate as work proceeds. OS/360 lessons:
1. Budget all aspects of size, not only core. Disk residence made accesses feel cheap; each component had a core target but no access budget. Programmers over their core target split code into overlays, growing total size and slowing execution, and the control system, which collected only core used, did not notice. Set total size, resident-space budgets, and budgets on backing-store accesses. Modern analogues: latency, token, memory, bundle size, request and query counts (the N+1 query is the new disk access), dependency and cognitive-complexity budgets.
2. Define exactly what a module must do when you specify how big it must be. Size budgets set before functional allocations were final led programmers in trouble to throw functions over the fence into a neighbour's space, compromising security and protection.
3. Local optimisation: on a large project with poor communication, people saw themselves as contestants meeting their own targets rather than builders of a product, and each suboptimised his piece. Architects must watch system integrity; fostering a total-system, user-oriented attitude may be the most important function of the programming manager.

Space techniques: no amount of budgeting makes a program small; that takes invention and craftsmanship.
- Trade function for size. Decide the granularity of options. Many optional features each cost a little; for a given set a monolithic program is smaller. Every option multiplies the test surface (inferred).
- Trade space against time: more space gives more speed over an amazingly large range, which is what makes budgets feasible. Train people in technique and share peculiarities; keep a notebook of good routines. The two-version idea (quick and squeezed) is flagged as obsolete in ch. 18.
- Representation is the essence of programming. Lean, fast programs come from strategic breakthrough rather than tactical cleverness: a new algorithm sometimes, a redone representation of data much more often. When out of space, step back from the code and contemplate the data. For a request to cut size or latency (adaptation): look first at data representation and algorithmic strategy, not micro-tweaks; budget the whole path; measure it; define each part's responsibility.
- Check by measurement: the OS/360 performance simulator caught the problem early. Do not rely on self-reported numbers.

## 6. Good enough, and when to stop (PP)

- Perfect, bug-free software is not attainable. Discipline yourself to write software that is good enough for users, future maintainers and your own peace of mind (credited to Yourdon). "Good enough" is not sloppy: systems must still meet requirements, and users get a say in when it is good enough.
- Tip 7: make quality a requirements issue. Procedure: identify stakeholders and the quality their context demands; make the trade-off (features, polish, date) explicit and let them choose; meet the agreed level; stop when it is met.
- Know when to stop: like over-layering paint, over-embellishment and over-refinement ruin a good program. Gold plating, speculative generality and repeated unasked polishing are the warning signs; so is skipping tests or error handling to meet a date nobody was told was unrealistic.
- Tip 4, broken windows: do not leave bad design or code unmarked. If there is no time to fix it, board it up (comment out the offending code, show a "Not Implemented" message, or substitute dummy data) so that damage does not spread and someone is visibly on top of it. In a pristine codebase people take care not to be first to make a mess.
- Tension to hold: Tip 69 (gently exceed expectations) against know-when-to-stop. Resolution in the text: extras are small and superficial, found by listening, never speculative. See `requirements-and-specs.md` section 11.
- Scope creep: track every addition with requester, approver, date and schedule impact (`requirements-and-specs.md` section 6).

## 7. Rewrite or v2 checklist (adaptation, built from the notes)

1. Why rewrite? Lehman and Belady: when fixes mostly repair earlier fixes and modules touched per release outgrow modules added, the system may have worn out as a base for progress, and a ground-up redesign may be needed (ch. 11). Measure this; do not assume it. Mostly-structural problems may respond to refactoring with tests first (`craft-refactoring`).
2. Who is designing it, and is it their second system? Require a senior designer who has shipped at least two systems of this class, or an explicit reviewer playing that role.
3. List the wish list from the first system. For each item: named user, stated frequency guess, cost budget, and what existing concept it extends. Cut what lacks all four.
4. Check premises (section 4): which parts of the old design rest on assumptions that no longer hold?
5. Plan as incremental: a running skeleton first, with old behaviour characterised by tests (note ch. 6 warning: an old implementation carries accidental behaviour; decide deliberately which of it matters).
6. Budget the new system the same way (size, speed, dependency, complexity).
7. Fix an explicit freeze date and a change threshold that rises over time.
8. Moving the team is dangerous: of about six observed project moves, none succeeded (ch. 19).
9. Report cost and schedule with the estimating method, including the productising factor (about 3x) if the result is meant to be reused.

## 8. Contested and dated points

- Retraction: "plan to throw one away" (ch. 11) was retracted in 1995 as too simplistic (see `delivery-strategy.md`).
- Data about the Lehman-Belady growth law is from a large OS of that era; refactoring and automated tests partly supersede the pessimism, but unmanaged change still degrades structure.
- OO and methodology investment (ch. 17): front-loaded cost, back-loaded benefit. Retraining and generalising functions into classes cost up front; benefit arrives in successor building, extension and maintenance. Coggins: the first project is not faster, nor the second; the fifth in a family will go blazingly fast. Brooks notes no result was reported for a fifth use; do not promise first-project speedups from a new method.
- The 10 versus 150 anecdote (ch. 4) is a single case.

## 9. Warning signs and verification

Warning signs:
- A version 2 or rewrite of a clean, successful product led by people for whom it is the second system.
- A backlog of "could not do it last time" features added all together.
- A feature that only half the users touch; sophisticated machinery whose premise has changed.
- Effort polishing an approach that the platform is moving away from.
- Manuals thickening, performance regressions found late, requests justified only as "the market demands it".
- Only one resource budgeted; components reporting within target while the whole degrades; complexity moving across module boundaries.

Verification:
- Each feature has a stated cost budget and a stated user who needs it.
- Usage data or instrumentation exists to see which features are used.
- The list of the system's basic assumptions is written and each refined subsystem is checked against it.
- Someone on the design team has shipped two systems of this class.
- Resource budgets cover every scarce resource and are measured end to end, not self-reported; no resource usage has migrated across ownership boundaries.
- The delivered change contains nothing beyond what was requested unless flagged.
