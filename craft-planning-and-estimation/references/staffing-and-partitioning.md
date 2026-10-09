# Staffing and partitioning

Contents: 1 Effort is not progress; 2 Four task types; 3 Communication arithmetic; 4 Brooks's Law and its mechanisms; 5 What later studies changed; 6 Late-project decision list; 7 Small sharp teams and the surgical team; 8 Organisation: producer, technical director, the tree; 9 Organising around function (Pragmatic); 10 Other people-and-project findings; 11 Warning signs and verification

Sources: MMM ch. 2, 3, 7, 10, 11, 19, 20 notes; PP ch. 2 (orthogonality, team parts), ch. 8 section 41 (Tip 60).

For the agent version of this material see `orchestrating-subagents.md`.

## 1. Effort is not progress

Cost varies as people times months; progress does not. Using the man-month as a unit of job size is, in Brooks's phrase, a dangerous and deceptive myth (ch. 2). Anything you write that divides a person-month figure by a head-count to produce a date is applying the myth.

## 2. Four task types (ch. 2)

| Task type | Time against number of workers | Example | Effect of adding people |
|---|---|---|---|
| Perfectly partitionable, no communication | time = effort / n | reaping wheat | Even trade of people for months |
| Unpartitionable, sequential constraint | flat | nine months to bear a child whatever the number of women; debugging is largely sequential | No effect on the schedule |
| Partitionable but needs communication | falls, slower than an even trade | most real work | Helps less than proportionally |
| Complex interrelationships | falls then rises | system programming | Past a point, more people lengthen the schedule |

Software construction is inherently a systems effort (the last row); the communication burden quickly dominates the gain from partitioning.

## 3. Communication arithmetic

Two components:
- Training in the technology, the goals, the strategy and the work plan. It cannot be partitioned, so the added effort grows linearly with the number of workers.
- Intercommunication. If every part must be coordinated with every other, effort grows as n(n-1)/2 (Babel chapter writes it as (n^2 - n)/2). Multi-way conferences are worse. Babel adds that with n workers coordination is potentially needed within almost 2^n teams.

| n | pairs n(n-1)/2 |
|---|---|
| 2 | 1 |
| 3 | 3 |
| 4 | 6 |
| 5 | 10 |
| 7 | 21 |
| 10 | 45 |
| 20 | 190 |
| 50 | 1225 |

Use: this is a reason to limit concurrent actors and to use a star topology around an owner instead of a mesh. The purpose of organisation is to reduce the communication and coordination needed, by division of labour and specialisation of function (ch. 7).

## 4. Brooks's Law and its mechanisms

"Adding manpower to a late software project makes it later." Brooks calls it an outrageous oversimplification.

Three mechanisms (ch. 2):
1. Training time taken from the experienced people (ramp-up).
2. Repartitioning of the work, which discards some finished work.
3. More communication paths and a longer system test.

Demythologised rule (ch. 2):
- The number of months depends on the project's sequential constraints.
- The maximum useful number of people depends on the number of independent subtasks.
- From these you can derive schedules with fewer people and more months (the risk is obsolescence). You cannot get workable schedules with more people and fewer months.

## 5. What later studies changed (ch. 19)

- Boehm (about 63 projects): cost-optimal schedule T = 2.5 x M^(1/3); cost rises slowly if the schedule is longer than optimal and sharply if shorter; hardly any projects succeed in less than 3/4 of the optimum regardless of staffing.
- Abdel-Hamid and Madnick (simulation): adding people to a late project always makes it more costly but does not always make it later. Adding early is far safer than late, since newcomers have an immediate negative effect that takes weeks to offset.
- Stutzke (simple model including mentor diversion, tested on a real project): manpower was successfully doubled mid-project after a slip and the original schedule was met. Late additions must be team players who work within the process rather than try to change it. He treats communication growth as second-order.
- Neither model captures repartitioning of the work, which Brooks finds non-trivial.
- Verdict: keep the law as "the best zeroth-order approximation", a warning against the instinctive fix to a late project.

Boehm also found team quality to be the largest factor in cost, about four times the next largest. DeMarco and Lister (quoted by Brooks): the major problems of the work are more sociological than technological; the manager's function is to make it possible for people to work (ch. 19).

## 6. Late-project decision list

From ch. 2, refined by ch. 19. Follow it in order.
1. Establish how late with a measurable milestone, not a feeling.
2. Decide which assumption fits: only the part already done was misestimated, or the whole estimate is uniformly low. Default to the conservative (uniform) assumption unless there is a specific reason the miss was local.
3. Prefer, in order: trim scope formally (especially when the cost of delay is high), or reschedule once with margin ("take no small slips", P. Fagg).
4. Add people only if all of these hold: the remaining work has genuinely independent subtasks; training cost is small; the remaining time is long compared with ramp-up; ideally the addition is early. If forced: add team players, assign mentors, repartition deliberately, and expect a dip of some weeks.
5. Do not repeat the add-people cycle. Brooks: "therein lies madness".
6. Never keep date, scope and staffing all fixed. The scope is then trimmed silently through hasty design and skipped tests.
7. Check quality controls first: late, costly projects spend most of the extra time finding and repairing errors in specification, design and implementation (Jones, ch. 17). Productivity follows quality, though extreme quality assurance (space-shuttle level) lowers productivity again (Boehm).

## 7. Small sharp teams and the surgical team (ch. 3)

The tension: for efficiency and conceptual integrity you want few minds designing and building; for timeliness on big systems you need many hands.

Evidence cited: experienced programmers varied about 10:1 in productivity and about 5:1 in program speed and space in the Sackman, Erikson and Grant data, with no correlation to years of experience (Brooks doubts that is universal). Consensus limit for a small sharp team: about 10. Brute-force big projects (OS/360 had over 1,000 people at peak, about 5,000 man-years) are costly and lack integrity. A bound calculation: a team of 10 each 7x as productive, with another 7x from reduced communication, would still take about 10 years for 5,000 man-years.

Mills's proposal: organise each segment as a surgical team. One person does the cutting; others support and amplify.

| Role | Does | Modern analogue (adaptation) |
|---|---|---|
| Surgeon (chief programmer) | Defines specs, designs, codes, tests, writes the documentation personally | The design owner (human or lead agent) |
| Copilot | Alter ego who knows all the code, discusses and evaluates design, researches alternatives, may represent the team to others; writes code but is not responsible for it; surgeon is not bound by the advice | Reviewer or critic with no authority; second pair of eyes |
| Administrator | Money, people, space, machines; the surgeon has the last word but spends almost no time | Project or team admin |
| Editor | Criticises and reworks the surgeon's draft documents; the surgeon still writes them | Technical writer |
| Program clerk | Keeps all technical records in a library; makes all runs visible and all programs team property | Version control, CI logs, artefact store |
| Toolsmith | Keeps basic services adequate and builds the special tools the surgeon wants | Developer experience or platform role |
| Tester | Adversary who devises system tests from the functional specs, and assistant who devises debugging data and scaffolding | Test author working from the spec |
| Language lawyer | Expert in language intricacies; short studies of technique; one can serve two or three surgeons | Framework or language expert, reference docs |

Why it works: (1) conventional partners divide the work and each designs a part; surgeon and copilot both know all the design and code, which removes shared-resource negotiation and preserves integrity; (2) conventional partners are equals, so judgement differences must be compromised and are compounded by differences of interest; in the surgical team there are none, and judgement differences are settled by the surgeon. Result: no division of the problem and a superior-subordinate relationship, so the team acts with one mind and the communication pattern is radically simpler.

Dated: secretaries, keypunching, batch-run logging. Softened by later practice: strict single-author hierarchy gives way to review and collective ownership, but the parts that last are to separate the mind that designs from the hands that support, make all work visible and team-owned, and keep the communication graph a star.

Gap in the source notes: the end of ch. 3 (scaling up to very large systems) is missing from the notes. Ch. 4 to 7 develop it (architecture separated from implementation, see `conceptual-integrity.md`).

## 8. Organisation: producer, technical director, the tree (ch. 7)

Six essentials of any effective subtree: a mission, a producer, a technical director or architect, a schedule, a division of labour, interface definitions among the parts.

| Role | Does |
|---|---|
| Producer | Assembles the team, divides the work, sets the schedule; acquires resources (communication outside the team); ensures the schedule is met |
| Technical director | Conceives the design, identifies subparts, specifies the external appearance, sketches the internal structure; supplies unity and conceptual integrity; works mostly inside the team |

Three workable relationships:
1. Same person: only for very small teams (about 3 to 6 programmers). Rare because thinkers are rare, doers rarer, thinker-doers rarest, and each role is full-time.
2. Producer is boss, director is right-hand man: the difficulty is giving the director real authority without putting him in the management chain. Conditions: the producer proclaims and backs the director's technical authority in an extremely high proportion of cases; they share fundamental technical philosophy; they talk out main issues privately in advance; the producer respects the director's technical prowess; status symbols signal the director's decision power.
3. Director is boss, producer his right hand: best for small teams (linked to the surgical team); producer-as-boss is better for the larger subtrees of a big project.

The tree is really a structure of authority and responsibility; the real communication structure is a network, so the tree is only a passable approximation and the gaps produce staff groups, task forces, committees and matrix organisations. Design the organisation around the people available.

## 9. Organising around function (PP Tip 60)

- Traditional job-function splits (analysts, architects, designers, coders, testers, documenters) follow the waterfall. They fail because analysis, design, coding and testing are views of the same problem, and programmers two or three levels from the users lack the context to make informed decisions.
- Prescription: small teams, each responsible for a functional aspect of the final system (including technical ones such as the database access layer). Aim for cohesive, mostly self-contained groups, the criteria used to modularise code. Let each team organise itself. Teams relate by agreed commitments, which change per project.
- Reasoning: apply contracts, decoupling and orthogonality to people; a change of database vendor then affects the database team only.
- Warning sign of a wrong organisation: two subteams working on the same module or class.
- Condition: only with responsible developers and strong project management. The project needs a technical head (philosophy and style, assigns responsibilities, arbitrates, hunts for unnecessary commonality between teams) and an administrative head (resources, progress reporting, priorities in business terms, ambassador). Larger projects add a librarian and a tool builder.
- Informal orthogonality metric (PP ch. 2): how many people must be involved in discussing each requested change; larger means less orthogonal.
- Challenge posed: if 4 programmers take 6 months, how long do 8 take? In how many scenarios is the time reduced? (Few; the book only poses it.)
- One voice: externally the team speaks with one voice; internally lively debate is wanted. A project librarian or functional focal points avoid interdeveloper duplication; keep a searchable Q&A record.

## 10. Other people-and-project findings

- Conway's Law (quoted in ch. 10): organisations that design systems are constrained to produce systems that copy their communication structures. The org chart and the interface specification are intertwined, and the chart initially reflects the first system design, which is almost surely wrong. If the design is to be free to change, the organisation must be prepared to change. Planning consequence: how you split work among people or agents will shape the module boundaries.
- Organising for change (ch. 11): assign people to jobs that broaden them; keep two or three top programmers as a flexible "cavalry" to send where the battle is thickest; keep managers and technical people interchangeable as talent allows; dual ladder (technical and managerial) with prestige parity. Reluctance to document tentative designs is often reluctance to defend decisions that are tentative; an unthreatening environment is needed.
- Moving projects (ch. 19): of about six observed moves, none was successful, because team fusion was broken. Missions can be moved; projects cannot.
- Subsidiary function (ch. 19): do not assign to a higher body what a lower one can do. Microsoft feature teams (30 to 40 people with 4 to 5 specialties) owned their feature set, schedule and process; IBM reported delegation to teams as improving quality, productivity and morale. Individuals report somewhat less control actually relinquished than managers claim.
- Great designers (ch. 16): the best designers produce structures faster, smaller, simpler and cleaner; products with passionate fans come from one or a few designing minds. Brooks recommends rewarding great designers as much as great managers.

## 11. Warning signs and verification

Warning signs:
- Several peers each own a slice of one design and nobody knows all of it.
- Private working copies and runs the team cannot see.
- The lead designer spends significant time on administration or tool plumbing.
- Disputes over shared resources between sub-owners.
- A full mesh of communication paths; the same person as producer and director on a large project; a technical genius with no authority or protection from management.
- "We will add people to catch up"; a second round of adding people.

Verification:
- The plan states its sequential chain and the count of independent subtasks, and the staffing does not exceed that count.
- After a slip there is one re-plan with an explicit choice among trim, reschedule and add; any increase carries an explicit ramp-up and repartitioning cost.
- Map teams or agents to modules: does any module have two owners?
- For a plausible change (swap a vendor, replace a component), count the teams that must change. More than one signals poor orthogonality.
- Is there a named technical lead and a named administrative lead?
