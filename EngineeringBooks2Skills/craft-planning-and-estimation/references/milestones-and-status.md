# Milestones, the critical path and honest status

Contents: 1 Termites, not tornadoes; 2 Milestones; 3 The critical path; 4 How status gets hidden; 5 Two ways to lift the rug; 6 Scheduled and estimated dates; 7 Plans and Controls; 8 The documents that carry the plan; 9 Bad news: options, not excuses; 10 Boiled frogs and the big picture; 11 Status report format for an agent; 12 Warning signs and verification

Sources: MMM ch. 2, 10, 14, 18; PP ch. 1 (Tips 3, 6), ch. 2 (Tip 19), ch. 8 (Tips 69, 70). Sibling: `craft-technical-communication` for message and status-update writing craft; this file covers what the plan and report must contain.

## 1. Termites, not tornadoes (MMM ch. 14)

How does a project get to be a year late? One day at a time. Major calamities trigger radical reorganisation and the team rises; day-by-day slippage (a sick key person, a cancelled meeting, a late disk) is harder to recognise, prevent and make up. PP says the same: most project overruns happen a day at a time (Tip 6).

## 2. Milestones

The only rule for choosing milestones: they must be concrete, specific, measurable events, defined with knife-edge sharpness.

- Anti-examples: coding "90 percent finished" for half of the coding time; debugging "99 percent complete" for most of the debugging time; "planning complete" (can be declared at will).
- Good examples (100-percent events): specifications signed by architects and implementers; source code 100 percent complete and entered into the library; a debugged version passes all test cases.
- It is more important that a milestone be sharp and unambiguous than easy for the boss to verify. People rarely lie about a milestone sharp enough that they cannot deceive themselves. With a fuzzy one the boss hears a different report than was given, and bad news is softened without intent to deceive.
- Fuzzy milestones are millstones: they grind morale down, and chronic slippage kills morale (McCarthy, quoted in ch. 18: if you miss one deadline, make sure you make the next).
- Estimation behaviour (government contractor studies): estimates revised carefully every two weeks before an activity starts do not change significantly, however wrong; overestimates come down steadily during the activity; underestimates do not change until about three weeks before the scheduled completion. So only sharp interim milestones give early warning of underestimates.

Writing a milestone (adaptation):
1. A one-line name that states an observable outcome.
2. The check: a command, test, artefact or sign-off that returns pass or fail.
3. Who or what verifies it, and when.
4. The dependencies it unblocks.
Test: could two honest people disagree about whether it happened? If so, tighten it.

## 3. The critical path (ch. 14)

"The other piece is late anyway" is the excuse used to dismiss a one-day slip.

- Counter 1: hustle. Running faster than necessary gives the cushion to cope with routine mishaps; a calculated response dampens hustle. (Contestable: pressure culture can burn people out. Use the mechanism, not the pressure.)
- Counter 2: not all slips matter equally. A PERT or critical-path chart shows who waits for whom, who is on the critical path (a slip moves the end date), and how much an activity can slip before it joins the critical path. Strict PERT uses three time estimates per event; Brooks said it is not worth the extra effort and used the term for any critical-path network.
- Preparing the chart is the most valuable part: laying out the network, identifying dependencies and estimating the legs forces very specific early planning. The first chart is always terrible; one invents and invents in making the second.
- In operation it answers the excuse, shows where hustle keeps your part off the critical path, and suggests ways to make up lost time elsewhere.

Practical form: a list of tasks with dependencies, a longest chain highlighted, and a slack number per task. Update it when a milestone moves.

## 4. How status gets hidden ("under the rug")

A first-line manager with a slipping team rarely runs to the boss: he thinks he can fix it, and the boss has other worries. The boss needs two kinds of information: exceptions to plan requiring action, and a status picture for education. Role conflict: the manager fears reporting a problem will lead the boss to act on it and pre-empt his authority, so he waits until he thinks he can solve it alone.

## 5. Two ways to lift the rug (use both)

1. Reduce the role conflict, inspire sharing. The boss must distinguish action information from status information, discipline himself not to act on problems managers can solve, and never act while explicitly reviewing status (a boss who phoned in orders before the first paragraph of a status report ended guaranteed that disclosure stopped). Label meetings as status review or problem action; a status meeting can become an action meeting if a problem is out of hand, but everyone knows the score and the boss thinks twice before grabbing the ball.
2. Yank the rug off. Use review techniques that reveal true status regardless of cooperation: a critical-path chart with frequent sharp milestones as the basis; review some part of the project every week, cycling through all of it in about a month. The key document is a milestone report of scheduled against actual completions; it is the meeting agenda, and the component owner prepares to say why late, when finished, what has been done, and what help is needed.

For agents (adaptation): report status by milestone with proof, separate "FYI" from "I need a decision", and do not wait to report until the problem is solved.

## 6. Scheduled and estimated dates (Vyssotsky; ch. 14)

Carry both in the milestone report.
- Scheduled dates belong to the project manager: a consistent, a-priori-reasonable work plan for the whole project.
- Estimated dates belong to the lowest-level manager responsible for the piece: the best judgement of when it will actually happen given resources and arrival of prerequisite inputs.
- The project manager keeps his fingers off the estimated dates and stresses accurate, unbiased estimates rather than palatable optimistic or self-protective conservative ones. Then he can see far ahead where trouble will come.

For a single agent (adaptation): keep the original plan dates and the current forecast side by side. The gap is the early warning.

## 7. Plans and Controls (ch. 14)

A small staff group (1 to 3 people) extends the boss: it maintains the milestone report, the update and revision of the network. It has no authority except to ask line managers when milestones are set or changed and whether they were met; it takes the paperwork away so line managers' burden is decisions. It needs skill and diplomacy. A modest investment here made more difference than the same people building product code: it is the early warning system against losing a year, one day at a time. Modern analogue (adaptation): a tracker or board maintained by one owner, with an automated view of slipping items.

## 8. The documents that carry the plan (ch. 10)

A small number of documents become the pivots of management. Preparing each focuses thought; maintaining each is surveillance and warning; each serves as checklist, status control and database.

| Question | Document |
|---|---|
| What | Objectives (need, goals, desiderata, constraints, priorities); product specifications (speed and space specs are critical) |
| When | Schedule |
| How much | Budget. It forces technical decisions otherwise avoided and, more importantly, forces policy decisions |
| Where | Space allocation; for software read it as resource allocation (environments, machines, compute) |
| Who | Organisation chart (who or which agent owns what) |

- Start formalising mini-documents immediately regardless of project size, rather than meeting to debate structure and then coding.
- Writing decisions down is essential: gaps and inconsistencies appear only when written, and writing forces hundreds of mini-decisions. Documents communicate decisions (policy thought common knowledge is often unknown to some team member). The manager's chief daily task is communication, not decision-making; only about 20% of an executive's time needs information from outside his head (the other 80% is communication).
- Conway's Law and the org chart: see `staffing-and-partitioning.md`.
- The estimate-forecast-price cycle (hardware business): prices below those postulated give a success spiral, prices above a disastrous one. Stress can bring out the best work or ridiculous vacillation; an engineering manager acting as a flywheel damps fluctuations. The logic applies to any product with fixed costs and unit economics.
- Check consistency: spec, schedule and budget agree; missing document means an unmade decision.

## 9. Bad news: options, not excuses (PP Tip 3)

Take responsibility: a commitment that something will be done right, including analysing risks outside your control. When you misjudge, admit it and offer options. Do not blame a vendor, language, management or coworkers. If a vendor might not deliver, you should have had a contingency plan.

Procedure before reporting that something cannot be done, is late or is broken:
1. Say the explanation out loud first. Does it sound reasonable or stupid?
2. Rehearse the conversation: what will they ask ("have you tried ...", "didn't you consider ...")? Prepare the answers; if you can predict the question, act on it first.
3. Ask whether there is anything else you can try before reporting.
4. Replace "it can't be done" with what can be done: rework with the value of refactoring explained; time to prototype if the best path is unknown; better testing or automation to prevent recurrence; additional resources.
5. Do not be afraid to ask for help.

Report check (inferred): what happened, stated plainly; your contribution acknowledged; at least one concrete option with its cost; what would prevent recurrence. For an agent: when a task cannot be completed as asked, say so directly, say what was tried, and offer workable alternatives rather than blaming tooling or silently delivering less.

Honest slippage options come from `staffing-and-partitioning.md`: trim scope formally, reschedule once generously, or add capacity under stated conditions. The manager's real choice, Brooks says, is to trim formally and carefully, reschedule, or watch the task be silently trimmed by hasty design and incomplete testing.

## 10. Boiled frogs and the big picture (PP Tip 6, section 3)

Dropped in hot water a frog jumps out; heated slowly it does not notice. Systems drift from the specification feature by feature; patch upon patch until nothing of the original is left. Teams are more prone than individuals because everyone assumes someone else is handling it. Practice: review what is around you constantly, appoint someone to watch for scope increase, shrinking time scales, extra features and new environments, and keep metrics on new requirements. Distinction: broken windows are people losing the will because they think no one cares; the boiled frog is people not noticing at all. Different failure, different remedy.

Check (inferred): compare current state against the original request and plan: what has been added since, whether the sum still matches the goal, and how many consecutive patches an area has received. At the end of a long agent task, re-read the original request before finishing.

Iterate the schedule with the code (Tip 19) is in `estimating.md`.

## 11. Status report format for an agent (adaptation)

1. Result in one line: done, in progress with forecast, or blocked.
2. Milestones: each with name, pass or fail, and evidence (command and result).
3. Plan against forecast: scheduled and current estimate for the next milestone.
4. Changes since the last report: scope added or cut, assumptions changed, interface changes.
5. Risks and decisions needed from the user, with options and costs.
6. What was not verified.

Sign your work (Tip 70): stand behind output, report only what is tested and documented, state what was and was not verified, and leave an auditable trail (commit authorship, clear change descriptions). Code must be owned, though not necessarily by an individual. Collective ownership needs extra practices (pairing, review) so accountability does not evaporate. Risk on the other side: territoriality.

## 12. Warning signs and verification

Warning signs:
- Percent-complete reporting with vague phases; milestones complete by assertion.
- Surprises in the final weeks.
- Managers reporting only after the problem is fixed; bosses reacting to status with orders.
- Excuses of the form "the other piece is late".
- No dependency network; scheduled and estimated dates collapsed into one number.
- Meetings substituting for writing; policies everyone knows that someone does not.
- Estimates that never change until three weeks before the deadline.

Verification:
- Every milestone has a binary, observable completion test written in advance.
- A dependency network exists and identifies the critical path and slack per task.
- Reports show scheduled against estimated dates, with owners.
- Meetings and messages are labelled status or action.
- Someone independent maintains the plan.
- Bad-news reports contain options.
