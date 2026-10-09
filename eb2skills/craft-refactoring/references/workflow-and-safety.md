# Workflow and safety

Contents
1. What counts as refactoring
2. The two hats
3. When to refactor, and when not to
4. The step loop (rhythm, step size, revert to green)
5. Commits and review (a contested area)
6. Published interfaces and ownership
7. Branches and integration
8. Databases
9. Performance
10. Speculative flexibility (yagni) and refactoring
11. Tools: automated refactoring versus text edits
12. Refactoring versus rewrite
13. Modifying code strategically (A Philosophy of Software Design ch. 16)
14. Pragmatic Programmer rules (ch. 6 sec. 33)
15. Verification checklist

## 1. What counts as refactoring

Noun: a change to the internal structure of software that makes it easier to understand and cheaper to modify without changing observable behaviour. Verb: restructure by a series of such changes. The point is small steps, so the code is almost never broken and you can stop at any moment. Diagnostic: if someone says their code was broken for a couple of days while they were refactoring, they were not refactoring (Refactoring 2e ch. 2).

- "Observable behaviour" is deliberately loose: what a user cares about must not change. Call stacks, performance characteristics and module interfaces may change.
- Bugs noticed while refactoring stay there. Fixing one is a separate behaviour-changing step with its own test. Exception: latent bugs nobody has yet observed may be fixed.
- Refactoring versus optimisation: both keep functionality; refactoring aims at understandability and cheap modification (and may speed up or slow down), optimisation aims only at speed and may accept harder code.
- Restructuring is the general word for any reorganisation; refactoring is the disciplined kind.
- Tiny steps are faster overall because they compose and no time goes on debugging.

## 2. The two hats (Kent Beck)

| | Adding-functionality hat | Refactoring hat |
|---|---|---|
| Existing code | Not restructured, only added to | Restructured |
| Tests | Add tests, make them pass; that is the progress measure | Add none (unless you find a gap); change tests only to follow an interface change |
| Behaviour | Changes | Must not change |

Swap hats often, even several times in ten minutes; the discipline is knowing which hat is on. Agent check (inferred): before each edit say which hat it is. A diff that both restructures and changes behaviour means the hats were mixed; split it.

## 3. When to refactor, and when not to

Why refactor at all (Refactoring 2e ch. 2): it keeps the design from decaying under short-term changes (duplication is the central target: say everything once and only once); it makes code easier for the next reader, often you; it helps find bugs, because clarifying structure exposes assumptions; and it speeds up work, because good modularity means a change needs only a small part of the code understood.

Rule of Three (Don Roberts): the first time, just do it; the second time, wince at the duplication but do it anyway; the third time, refactor.

| Kind | Trigger | Action |
|---|---|---|
| Preparatory | About to add a feature or fix a bug and the structure makes it awkward | Refactor first, then make the change. Best time to refactor. "Make the change easy (this may be hard), then make the easy change" (Beck). For bugs: unify copies or separate update from query, then fix |
| Comprehension | You had to think to understand code | Move the understanding into the code: rename, split. Deeper design issues then show ("wiping the dirt off a window") |
| Litter-pickup | You understand it and see it does the job badly | Easy: fix now. More effort: note it and fix after the task. Hours: still make it a little better each visit (camp-site rule) |
| Planned | Refactoring was neglected, or a problem area grew despite regular refactoring | Dedicated time; should be rare |
| Long-term | Replacing a library, extracting a shared component; takes weeks | Agree a direction and nudge code that way whenever it is touched. For library swaps use Branch By Abstraction: an abstraction that fronts either library, move callers, then switch |
| In code review | Reviewing someone's code | Try the suggestion by refactoring; works best with the author present and poorly in asynchronous pull requests |

Preparatory, comprehension and litter-pickup are all opportunistic: refactoring is not separately scheduled, "any more than you set aside time to write if statements". Excellent code also needs refactoring, because yesterday's correct trade-offs become wrong as features change.

Do not refactor when
- The messy code does not need to be modified or understood: leave it and treat it as an API.
- Rewriting is easier than refactoring (a judgement call; often you cannot tell without trying refactoring for a while).
- A big refactoring is warranted but the present feature is tiny: add the feature and leave the big one.
- The code is rarely touched, so the inconvenience is rarely felt.
- You are unsure what the improvement should be (or treat it as an experiment).
Incline towards refactoring when it makes the present feature easier, you have met the same ugliness before, or the area is visited often.

Justification is economic, never moral. Too little refactoring is far more common than too much. The argument is faster features and bug fixes, not "clean code is good practice". Design Stamina Hypothesis (an explicit hypothesis, not proven): effort on internal design lets a team go faster for longer. Fowler's advice on telling a manager is contested: for a technically savvy manager explain design stamina; otherwise "don't tell", since refactoring is part of how a professional builds fast. Treat that as one author's position.

## 4. The step loop

1. Confirm a self-checking test suite covers the area (see `legacy-code-and-tests.md` if it does not).
2. Pick one named refactoring from the catalogue. Know its mechanics.
3. Make the smallest step of the mechanics.
4. Compile or type-check, then run the tests. Commit locally on green (squash into meaningful commits before sharing).
5. If a test fails and the cause is not immediately visible, revert to the last good state and redo with smaller steps. Do not debug forward.
6. After an extraction, look immediately for cheap clarifications (renames) in the new function.

Rules of thumb
- The trickier the situation, the smaller the steps. Fowler's written mechanics are baby steps; in daily work he takes bigger ones and backs out to smaller ones on a failure.
- Never refactor on a red bar.
- Test after every step, however trivial: a failure then points to a tiny change.
- Run the whole safety net, not a subset. In Clean Code ch. 14 only unit tests were run during a refactoring; an acceptance test required behaviour the unit tests did not check, and a bug slipped through. The fix was one command that runs everything.
- Intermediate states may look worse than where you started (Clean Code ch. 14 calls one stage "a bit disappointing"); keep going. Sometimes one refactoring leads to another that undoes the first (Clean Code ch. 15 reversed several earlier decisions).
- Do not mix a rename with an add-parameter in one step.

## 5. Commits and review

- Each commit is a single named refactoring or a small group; no commit mixes structure change with behaviour change. This is the safe default for an agent.
- Fowler himself is "not convinced" that refactoring and feature commits must be separate: the benefit is independent review, the cost is that the refactoring loses its context of justification. He says teams should experiment. The Pragmatic Programmer lists "don't refactor and add functionality at the same time" as a rule. Decision rule: separate them when a reviewer will read the diff or when you may need to revert one without the other; interleave them when the refactoring only makes sense next to the feature, and say so in the description.
- Pull-request critique in the book concerns doing refactoring during review, not PRs as such.

## 6. Published interfaces and ownership

- A published interface has clients independent of the declaring code (other teams, external customers). You cannot find or change all callers.
- When renaming: keep the old declaration as a pass-through to the new one, mark it deprecated, retire it eventually or perhaps never. This complicates the interface; it is the price of not breaking clients.
- Avoid fine-grained strong code ownership. Team ownership (anyone on the team may change team code) or an open-source-like model across teams lets a team update its callers and delete old declarations.
- Inference: do not publish interfaces prematurely.
- Clean Code ch. 16's renames, int-to-enum changes and static-to-instance changes were safe only because the author could update every caller; for a published library they would be breaking changes (inferred).
- The Pragmatic Programmer's contrasting tactic for internal code: make an incompatible change break the build so old clients fail to compile and are found quickly. Use it where you own all clients.

## 7. Branches and integration

- Version control merges text, not meaning: rename a function on one branch, add a call to the old name on another, and the merge is clean and the code broken.
- Merge difficulty grows worse than linearly with branch age.
- Refactorings are many small scattered edits, exactly what produces semantic conflicts, so feature-branching teams often stop refactoring. Recommended: continuous integration (everyone integrates at least daily), small chunks, feature toggles for unfinished work.
- Feature branches are acceptable when short, and for open-source projects with infrequent outside contributors.
- Practical rule for an agent: keep refactoring branches short; merge the mainline in often; avoid sweeping renames while others have long-lived branches open.

## 8. Databases

Evolutionary database design: bundle schema change, access-code change and a data migration script as one small versioned unit; migrations compose in sequence. Unlike code refactorings, spread a database change over several production releases so each can be reversed. Renaming a column: add the new column unused; write to both; move readers over gradually; after a bedding-in period remove the old column (parallel change, expand-contract). Keep migration scripts in version control.

## 9. Performance

Refactoring can make code slower and more tunable. "Write tunable software first, then tune it for sufficient speed" (except hard real-time).
- Time budgeting suits hard real-time only.
- Constant attention to speed works badly: optimisations make code harder, are scattered, and rest on wrong assumptions; most time is spent in a small fraction of code.
- Recommended: well-factored first, then a tuning phase. 1. Profile. 2. Focus on hot spots. 3. Change in small steps; compile, test, re-profile after each. 4. Back out changes that did not help. 5. Repeat until users are satisfied.
- Sidebar: experts' guesses about a slow spot were all wrong; the profiler showed half the time creating identical date objects. An earlier clarity refactoring allowed a five-minute fix that doubled speed. Measure, do not speculate.
- While refactoring, mostly ignore performance. Split Loop and Replace Temp with Query add repeated work that rarely matters; if a refactoring causes a real slowdown, finish refactoring, then tune. Never justify a performance-motivated change without a before and after measurement.
- The Pragmatic Programmer (ch. 6 sec. 32) adds: estimate the order of an algorithm, measure at several input sizes, and confirm a bottleneck before optimising.

## 10. Speculative flexibility (yagni)

Flexibility mechanisms (extra parameters, hooks) are not free: they complicate the present case, are frequently wrong, and make the flexibility you actually need harder to add. Decision procedure for a speculative mechanism:
1. Does it add complexity? If not (small well-named functions), include it.
2. If it does, estimate how hard it would be to add later by refactoring.
3. Add it now only if refactoring later would be substantially harder.
4. Concretely: add no parameter unless callers pass different values; Parameterize Function is cheap later.
Yagni "isn't credible without the foundation of refactoring": self-testing code, continuous integration and refactoring reinforce each other. Some up-front architectural thinking still pays where later change would be hard.

## 11. Tools

- Prefer syntax-tree tools with type information (IDE refactorings, language-server rename) to text search and replace. Static typing makes a rename on one class safe where a same-named method exists on another; without types it is a judgement per call site.
- Even good tools slip on reflective calls; run the tests periodically anyway.
- In dynamically typed code after a rename, also search for string and reflective uses and run the tests (inferred).
- Text replace is a useful crude first step, never trusted without tests.
- The temporary searchable prefix (`xxNEW`, `zz_`) turns a rename into a safe global replace even without a rename tool.
- Without tests, restrict yourself to tool-performed refactorings (Fowler's first alternative) and see `legacy-code-and-tests.md`.

## 12. Refactoring versus rewrite

Fowler gives no rule, only a judgement: rewriting is sometimes easier, and you often cannot tell without refactoring for a while. Signals gathered from the books:
- Refactor when you can get tests around the code or even a seam, the code is on your path, and each step keeps the system shippable.
- Leave alone when you do not need to change or understand it.
- Rewriting a small piece, or replacing an algorithm behind a function, is ordinary: Substitute Algorithm with the old version kept as a test oracle.
- Do not be a slave to history: existing code does not dictate future code, and all code can be replaced (Pragmatic Programmer), but the cost of change must be weighed against the cost of not changing.
- A whole-system rewrite is not covered by these sources; treat it as a separate planning decision (see `craft-planning-and-estimation`).

## 13. Modifying code strategically (PoSD ch. 16)

- Tactical habit: "what is the smallest change that does what I need?" Each such change adds special cases or dependencies and the design degrades step by step.
- Goal: after each change the system has the structure it would have had if designed from the start with that change in mind. Make the minimal clean change, not the minimal diff.
- "If you are not making the design better, you are probably making it worse." Even without needing refactoring, fix design imperfections you see while there.
- Constraints are real (three-month refactor versus two-hour hack). Ask whether this is the best you can do given constraints; look for an almost-as-clean variant doable in days; if refactoring cannot happen now, record follow-up cleanup.
- Agent translation (the notes' generalisation): bias against narrow band-aids that add flags, parameters or special-case branches; check whether a local refactoring makes the feature natural.
- Comment hygiene while editing: update interface comments and nearby comments in the same change; keep each comment near its code; document a decision once, in the most obvious place, with short pointers elsewhere; put rationale in the code, not only in the commit message; before commit scan the whole diff for stale docs, debug code and unresolved TODOs; higher-level comments survive code changes better.

## 14. Pragmatic Programmer rules (sec. 33, 1999, partly dated)

- Triggers: duplication, non-orthogonal design, outdated knowledge, performance (moving functionality between areas). Tip 47: refactor early, refactor often; if it cannot be done now, schedule it and tell users of the affected code.
- Rules: do not refactor and add functionality at the same time; have good tests first and run them often; take short deliberate steps.
- Software is a garden rather than a building: constant tending, moving and pruning.
- Delay costs more: more dependencies later and the time will not exist then. Time pressure is not an excuse. A tumour is easier to remove when small.
- Related discipline from sec. 31 (Don't Program by Coincidence): if code works and you do not know why, find the documented guarantee or write an assertion or test that proves the assumption before changing around it. Remove lucky calls; rely only on documented behaviour.
- Tip 50: do not use generated or wizard code you cannot explain; it becomes maintained code. Modern equivalent (inferred): scaffolds and AI-generated snippets that you cannot explain line by line.
- The "automatic refactoring browser" passage is dated; the surviving principle is to use tool-automated, behaviour-preserving refactorings.

## 15. Verification checklist

- After each step the code builds and the entire suite passes; you could stop and ship.
- No test was edited except to follow an interface change.
- Any noticed bug was left alone or fixed in its own step with its own test.
- Published interfaces keep the old entry point delegating to the new one.
- Performance-motivated changes have before and after measurements; unhelpful ones were reverted.
- Speculative parameters or hooks have at least two distinct callers' needs behind them, or were omitted.
- Database changes are expand-contract across releases with migration scripts under version control.
- Each commit has one purpose.

Source: Refactoring 2e ch. 1-2 and 4 (practices); Clean Code ch. 14-15; Pragmatic Programmer ch. 6; PoSD ch. 16.
