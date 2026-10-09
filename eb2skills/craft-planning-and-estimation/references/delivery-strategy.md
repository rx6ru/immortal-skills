# Delivery strategy: tracer bullets, prototypes, skeletons, throwaways, integration and change

Contents: 1 The options in one table; 2 Tracer bullets; 3 Prototypes; 4 Tracer versus prototype; 5 Incremental build (end-to-end skeleton); 6 Plan to throw one away, and its retraction; 7 Why the waterfall fails; 8 Parnas families, build-to-budget, nightly build; 9 Integration discipline; 10 Planning for change; 11 Maintenance and entropy; 12 Environments and promotion; 13 Choosing; 14 Warning signs and verification

Sources: PP ch. 2 sections 10, 11 (Tips 15, 16), ch. 7 section 38; MMM ch. 11, 12, 13, 16 (growing software), 18, 19 (retractions and the replacement). Sibling: `craft-testing` for test practice, `craft-refactoring` for safe change of structure.

## 1. The options in one table

| Option | Answers | Code fate | Needs |
|---|---|---|---|
| Tracer bullet | "Where is the target?" Unknown requirements, unfamiliar techniques, changing environment | Kept; it is the skeleton of the final system | Production-quality structure, error checking, tests, real build |
| Prototype | One specific risky question | Discarded; the lesson is kept | Everyone knows it is disposable |
| Mock or Wizard-of-Oz | How will users react to the interface | Discarded | Users who will try it |
| Vertical slice | Performance risk | Kept or discarded by choice | Limited function built fully |
| Incremental build from an end-to-end skeleton | Everything else on a big job | Kept | Stubs, regression suite, a build that runs |
| Throwaway pilot delivered to customers | (Do not do this) | | Brooks: costs user agony, builder distraction, bad reputation |

## 2. Tracer bullets (PP Tip 15)

Metaphor: firing a machine gun in the dark. Dead reckoning calculates range, wind and ammunition once, then shoots and hopes. Tracer rounds show where the bullets go, in the same environment as the real ammunition, with immediate feedback at low cost. "Ready, fire, aim."

Goal: from a requirement to some aspect of the final system quickly, visibly and repeatably.

- Worked example (PP): a client-server database marketing application with temporal queries. First build could only list all rows of a table, but proved the path from the user interface through the query-representation library, serialisation, and conversion to SQL on the server. Then every component grew in parallel with each new query type.
- Tracer code is not disposable. It has error checking, structure, documentation and self-checks, and is simply not fully functional. Once it is end to end, measure the distance to the target and adjust.
- Advantages: (1) users see something working early, set expectations, contribute and buy in; (2) developers get a structure to work in, with more consistency; (3) an integration platform, so you integrate every day rather than big bang and debugging is faster; (4) there is always something to demo; (5) a better feel for progress, use case by use case, avoiding "95% complete" week after week.
- Tracers may miss, and that is the point: the user says "not what I meant", data is unavailable, performance doubts appear. A small body of code has low inertia.

Agent form (adaptation): the first deliverable of a large task is a runnable path through every layer that will matter (entry point, core logic stub, persistence stub, output), with a test that exercises it and the real build running it. Each increment adds function inside that path.

## 3. Prototypes (PP Tip 16)

Prototypes analyse and expose risk and give chances for correction at greatly reduced cost. They need not be code: Post-its for workflow, whiteboard drawings or non-functional mock-ups for UI.

- Value is lessons learned, not code produced. State the question first.
- Prototype anything risky, never tried, critical, unproven, experimental, doubtful or uncomfortable: architecture; new functionality in an existing system; structure or content of external data; third-party tools; performance; UI design.
- You may ignore correctness (dummy data), completeness (one input, one menu item), robustness (error checking may be absent) and style (comments), but write down what you learn.
- Use the most productive language or tool available for the experiment (a REPL, scripting language or mock tool today). If investigating absolute performance you need something close to the target's speed; relative comparisons tolerate a different language.
- Prototyping architecture, ask: are responsibilities of major components well defined and appropriate? Are collaborations well defined? Is coupling minimised? Can you identify sources of duplication? Are interface definitions and constraints acceptable? Does every module have an access path to the data it needs, when it needs it? (The last is the biggest source of surprises.)
- How not to use them: make sure everyone understands the code is disposable, incomplete and cannot be completed. Sponsors may insist on deploying a prototype because it looks complete (balsa and duct tape, not for rush-hour traffic). If your culture may misread it, use a tracer instead.

Brooks's definition (ch. 16): a prototype simulates the important interfaces and performs the main functions of the intended system, not bound by the same speed, size or cost constraints; it does the mainline tasks and makes no attempt to handle exceptions, invalid input or clean aborts. Its purpose is to make the conceptual structure real so the client can test it for consistency and usability. Variants (ch. 19): a finite-state-machine interface mock with no real function; Wizard of Oz, where a hidden human simulates responses.

## 4. Tracer versus prototype

| | Tracer | Prototype |
|---|---|---|
| Purpose | Find the target; build the skeleton | Learn about one aspect |
| Quality | Lean but complete, production structure | Cut corners freely |
| After | Kept and grown | Thrown away, rewritten properly with the lessons |
| Example (PP box-packing app) | Trivial first-come packing plus a simple working UI, everything plumbed together | A UI sketch in a builder tool; packing algorithms tested in a forgiving language |

Prototyping is reconnaissance before firing a tracer. If the details cannot be given up, you are not prototyping.

## 5. Incremental build from an end-to-end skeleton (MMM ch. 16, 19)

Technique (Harlan Mills): first make the system run, even if it does nothing useful except call the proper dummy subprograms. Then flesh it out bit by bit; each subprogram becomes real actions or calls to empty stubs at the level below. Properties: it needs top-down design; allows easy backtracking; lends itself to early prototypes; each added function grows organically out of what exists. There is a working system at every stage. Morale jumps when something runs. Brooks's claim from his teaching lab: teams can grow far more complex entities in four months than they can build.

Ch. 19 mechanics:
- Build the top-level driver with calls to stubs for every function. Compile and test; it runs doing nothing correctly. Add a primitive input and output module. Then refine function by function, always keeping a running, tested system. Occasionally the driver loop or module interfaces must change.
- Costs: the regression burden grows with each module (every new module is run against all earlier cases).
- Benefits: (1) user testing can begin very early; (2) build-to-budget: a strategy that protects absolutely against schedule and budget overruns, at the cost of possible functional shortfall; (3) morale.
- Distinguish a first milestone build from a rapid prototype: function. A shippable product is defined by useful completeness of function plus robustness; the first milestone may do nothing anyone cares about.

Sketch of a first increment (fresh illustration):

```python
def load_config(): return {}                  # stub: defaults
def read_input(cfg): return "sample"          # stub: canned sample
def process(data): return data                # stub: identity
def report(result): return f"result: {result}"  # stub: one line

def main():
    cfg = load_config()
    data = read_input(cfg)
    result = process(data)
    return report(result)

# test: run main() end to end and assert the one-line output; CI runs it
assert main() == "result: sample"
```

## 6. Plan to throw one away, and its retraction

1975 (ch. 11): chemical engineers need a pilot plant between bench and factory; in software the first system built is barely usable, and redesign is unavoidable, in one lump or piecewise. The management question is whether to plan the throwaway or promise to deliver it. Delivering it buys time at the cost of agony for users, distraction for builders redesigning while supporting it, and a bad reputation. "Plan to throw one away; you will, anyhow."

1995 (ch. 19, ch. 18 item 11.6): wrong, "not because it is too radical, but because it is too simplistic". It presumes the sequential waterfall model, in which a project passes through each stage once. Replace it with incremental build and progressive refinement. One of the ch. 20 notes to ch. 11 records him still advocating a planned-for-discard pilot while conceding he oversimplified design change (it cites Saltzer on evolutionary design); the notes do not date that remark, and ch. 19 retracts the slogan, so follow ch. 19. A beta is now common practice but is not an alpha, a limited-function prototype, which he also advocates.

What to keep: prototype early, learn, discard, and do not ship the prototype. The "second system" in ch. 5 is the second system fielded; the "second" in ch. 11 is the second try at the first system (a student pointed out the contradiction; Brooks said it is more linguistic than real). See `scope-and-second-system.md`.

## 7. Why the waterfall fails (ch. 19)

- Fallacy 1: assumes a project passes through the process once, with excellent architecture and sound implementation design, so that all mistakes are in realisation. Real failures are in the architecture (awkward for users, unacceptable performance, susceptibility to user error or malice), found only at the end because system and user testing come last. A spec review (alpha test) helps but there is no substitute for hands-on users.
- Fallacy 2: assumes you build the whole system at once and integrate end to end only after most coding and component test.
- There must be upstream movement: knowledge from downstream stages must leap upstream, sometimes more than one stage (like salmon). Implementation design shows that an architectural feature cripples performance; coding shows a function balloons space. Expect two or more architecture-implementation cycles before realising anything as code.
- Royce's 1970 improvement (feedback to the preceding stage only) is not enough. Parnas and Clements: produce documentation as if an ideal process had been followed (a rational design process, faked), but do not pretend the process was linear (ch. 20 notes).
- Consequence for the Ch. 2 fractions: they inherit this taint (see `estimating.md`).

## 8. Parnas families, build-to-budget, nightly build

- Parnas families (ch. 19): design a product as a family tree of related products. Put the design decisions least likely to change near the root. Extend the strategy to the intermediate versions of an incremental build so the product grows with minimum backtracking.
- Build-to-budget: with a running skeleton, cut function not quality when the budget ends. Pair with the Boehm schedule law (`estimating.md`).
- Nightly build (Microsoft, McCarthy; ch. 19): rebuild the developing system every night and run the test cases, from the first milestone. The build cycle becomes the heartbeat of the project. Programmer-tester teams check in daily; if the build breaks, stop everything until it is fixed. Everyone always knows status. It costs resources but builds credibility and morale. PP ch. 8 agrees (a full nightly build running all tests, so a regression is found while its cause is recent). Modern analogue: continuous integration.

## 9. Integration discipline (MMM ch. 13)

Design the bugs out:
- Bug-proof the definition: the most pernicious bugs are system bugs from mismatched assumptions between component authors. Careful function definition and disciplined exorcism of frills reduces them.
- Test the specification with an outside group (see `requirements-and-specs.md`).
- Top-down design (Wirth) as refinement steps: sketch a rough task definition and solution; examine the difference from what is wanted; break big steps into smaller. Use as high-level a notation as possible at each step. It identifies modules whose refinement proceeds independently; the degree of modularity determines adaptability. You will sometimes scrap the top level; it becomes clear when and why. Many poor systems come from salvaging a bad basic design with cosmetic patches.
- Structured control flow: think about control structures as control structures, not individual branches. Doctrinaire elimination of every goto is excessive.

Component debugging (adapted): prepare each session. Gold's results: three times as much progress on the first interaction of a session as on later ones. Brooks's rule: two hours at the desk for each two-hour terminal session, half sweeping up after the last (update the log, explain strange phenomena), half preparing the next (plan changes, design detailed tests). For an agent (adaptation): state the hypothesis and expected result before each run; write the findings down after.

System debugging (unexpectedly hard):
1. Use debugged components. Reject "bolt it together and try" (clean components save far more system test time than the scaffolding costs) and the "documented bug" approach (entering system test with known unfixed flaws; you do not know all their effects, and fixing them injects unknown bugs mid system test).
2. Build plenty of scaffolding: dummy components with faked data, miniature files with a few typical records (file-format misunderstanding is a very common system bug), test data generators, analysis printouts. Half as much scaffolding as product code is not unreasonable.
3. Control changes. One person authorises component changes or version substitutions. Keep a locked-up latest version for component testing, one under test where fixes are installed, and playpen copies per developer. Purple-wire technique: a quick fix goes in visibly and is logged, while the official change goes through the process, after which the paper and the model agree again. Software needs a change journal, a conspicuous distinction between quick patches and tested, documented fixes, and respect for the documentation as the product.
4. Add one component at a time. Assume lots of bugs. Rerun old cases on each new partial sum to detect regression.
5. Quantise updates. Other teams use the latest tested integrated system as a test bed; give each user periods of stability interrupted by bursts of change. Lehman and Belady: quanta should be very large and widely spaced, or very small and frequent; Brooks would never risk the latter. Contested: in 1995 he reports Microsoft's nightly builds making small frequent quanta work (ch. 18, 13.17). Rule for deciding: small frequent change is safe when backed by an automated suite that runs on every change and a policy of stopping to fix a broken build; otherwise batch changes into scheduled releases.

## 10. Planning for change (ch. 11)

- Accept change as a way of life. The programmer delivers satisfaction of a user need, not a tangible product (Cosgrove); the need and its perception change as the program is built, tested and used.
- Set a change threshold that rises as development proceeds. Quantise change: numbered versions each with its own schedule and a freeze date after which changes go to the next version (now standard).
- Plan the system for change: careful modularisation, extensive subroutining, precise and complete interface definitions with documentation, standard calling sequences, table-driven techniques wherever possible, a high-level language and self-documenting techniques, compile-time includes for standard declarations. Brooks says these are more discussed than practised.
- Cosgrove would treat all plans and schedules as tentative; Brooks thought that going too far: the common failing is too little management control.
- Reversibility (PP Tip 14, section 9): critical decisions (vendor database, architectural pattern, deployment model) are often irreversible except at great expense. Write decisions in the sand. Hide third-party products behind your own interface; keep deployment choices configurable (a switch from client-server to stand-alone should take days). If you cannot isolate cleanly, put the requirement in metadata and insert it with an automatic mechanism, so that what is added automatically can be removed automatically. Verification (inferred): write a second trivial implementation of the abstraction (in-memory store) and run the same tests against both. Cost: indirection; apply where the decision is uncertain and costly to change.
- Configure, do not integrate; put abstractions in code and details in metadata (PP Tips 37, 38; detail in `craft-module-design`).

## 11. Maintenance and entropy (ch. 11)

- Fixing a defect has a substantial chance (20 to 50%) of introducing another: two steps forward, one step back. Reasons: a subtle defect shows as a local failure but has non-obvious system-wide effects, and the repairer is usually not the author.
- Consequence: maintenance needs far more system testing per statement written than any other programming; rerun the entire prior test bank after each fix, or approximate it.
- Lifetime maintenance of a widely used program typically costs 40% or more of development (ch. 18, 11.21); cost rises with the number of users.
- Lehman and Belady: across releases the number of modules grows linearly but the number of modules affected grows exponentially. Repairs tend to destroy structure; eventually fixing ceases to gain ground and the system has worn out as a base for progress. Building is entropy-decreasing and metastable; maintenance is entropy-increasing and only delays subsidence. In 1995 Brooks adds: real upgrade needs often attack internal structural boundaries, and the original boundaries often caused the later deficiencies.
- Partly superseded by refactoring plus automated tests, but unmanaged change still degrades structure. Tracking measure: modules touched per release, defects introduced per fix. PP: tag bug fixes in source control and report the number of files touched per fix monthly.
- Rewrite decision: see `scope-and-second-system.md`.

## 12. Environments and promotion (ch. 12)

Tools are a project-level asset, not a personal possession. Points that apply to delivery:
- Playpen to integration to release: each programmer's own copies with no restrictions; a copy passed to the integration manager when ready, who runs system tests and may not be bypassed; a released current version that is sacrosanct, touched only for crippling bugs, and the base for all new integration. Two key ideas: control (managers authorise changes) and formal separation and progression. Modern analogues (adaptation): feature branches or worktrees, a merge gate with CI, a protected release branch, code owners.
- Dependable is not the same as accurate: a simulator or stable fake gives the same behaviour day to day, whereas new hardware (or a flaky test environment) changes, which robs you of incentive to hunt your own bug. Make the environment stable before blaming code.
- Build a performance simulator or measurement outside-in, top-down, start very early, and listen when it speaks (OS/360 found early that the compiler would run at five statements per minute).
- Allocate scarce shared environments in exclusive blocks: ten shots in a six-hour block beat ten shots spaced three hours apart, because sustained concentration reduces thinking time. Principle survives for shared test environments.
- Fast feedback is the sharpest tool: interactive debugging at least doubled system-programming productivity (Bell Labs data cited in ch. 12).

## 13. Choosing

| Situation | Choose |
|---|---|
| New kind of system, vague or shifting requirements | Tracer bullet, then incremental growth |
| A specific technical or UX question blocks the design | Prototype that question; write the lesson; delete the code |
| Users must judge the interface but the back end is not ready | Mock or Wizard-of-Oz |
| Performance is the main risk | Vertical slice with measurement |
| Hard budget or date | Build-to-budget from a skeleton; cut function not quality |
| Culture will ship any demo that looks finished | Tracer instead of prototype |
| Clear, small, well-understood change | Just do it; run the tests |
| Many components from many workers | Interface frozen first; skeleton; one component integrated at a time |

## 14. Warning signs and verification

Warning signs:
- The first prototype is in the customer's hands while the team redesigns.
- A schedule that assumes the first design is the final one; nothing runs until late.
- User-visible flaws discovered only at system test.
- No freeze or version policy; requirements accepted without a rising threshold.
- Fixes patched locally with no regression bank; modules touched per release rising faster than modules added.
- Components entering integration with known bugs; several added at once; no scaffolding "to save time".
- A broken build left for days; status unknown.
- Maintenance by juniors on undocumented code.

Verification:
- At every increment the full system builds and all earlier tests pass (a regression suite that only grows).
- An end-to-end path exists in the first iteration, touches every layer or external system, and runs in CI. Each increment adds function inside that path rather than a new silo. A demo is possible at any time.
- Each prototype has a written question before it starts and a written lesson after; stakeholders have been told it is throwaway.
- Versions are numbered with freeze dates; changes after the freeze are logged to the next version.
- Every quick patch is marked and has a follow-up documented fix.
- Scaffolding ratio sanity check (about half of product code is a rule of thumb, not a law).
