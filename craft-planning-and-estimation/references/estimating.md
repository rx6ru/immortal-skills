# Estimating

Contents: 1 Why estimates fail; 2 Classify the deliverable; 3 The estimating procedure; 4 Data and rules of thumb; 5 Converting effort to calendar; 6 Estimate versus date; 7 Iterating the schedule; 8 Worked examples; 9 Warning signs and verification; 10 Dated material

Sources: Mythical Man-Month (MMM) ch. 1, 2, 8, 19 and notes; Pragmatic Programmer (PP) ch. 2 section 13 (Tips 18, 19), ch. 1 (Tip 3).

## 1. Why estimates fail

MMM ch. 2 gives five reasons projects run out of calendar time, each of which is a check on any estimate you produce or review:

1. The technique assumes all will go well. Programmers are optimists, and the medium (pure thought-stuff) is so tractable that people expect few implementation problems; the real trouble is faulty ideas, which only show up during implementation. A plan built from per-task "if nothing goes wrong" durations, with tasks chained end to end, is almost certainly wrong, because the chance that every link goes well is small.
2. It confuses effort with progress, treating people and months as interchangeable (see `staffing-and-partitioning.md`).
3. The estimator lacks "courteous stubbornness" and lets the wished-for date substitute for the estimate.
4. Progress is poorly monitored (see `milestones-and-status.md`).
5. When slippage appears, the reflex is to add people.

Also MMM ch. 1, woe 5: debugging converges slowly, and the last bugs take longer to find than the first. Do not extrapolate the testing tail from the early fix rate.

## 2. Classify the deliverable first

MMM ch. 1 (the 2x2). Decide which of these is being delivered before applying any rate.

| | Stand-alone | Part of a system (interfaces, integration) |
|---|---|---|
| Private use | Program: 1x | Programming system component: about 3x or more |
| Generalised, tested, documented, maintainable by others | Programming product: about 3x | Programming systems product: about 9x |

What each step adds:
- Program to product (about 3x): generalise range and form of inputs as far as the algorithm reasonably allows; a substantial recorded bank of test cases that probes input boundaries; documentation sufficient for anyone to use, fix and extend.
- Program to system component (about 3x, more with many components): every input and output conforms to precisely defined interfaces; stays within a resource budget (memory, devices, time); tested with other components in all expected combinations. This testing grows combinatorially and is slow because the bugs come from unexpected interactions of individually debugged pieces.
- Both: about 9x. Brooks (ch. 18, 1.1) says the two factors of 3 are essentially independent, hence multiplicative. The multipliers are his rules of thumb; in ch. 19 he said they still looked roughly right.

Why it matters: the "two programmers in a garage" figure compares a private program with a systems product. A demo's timing is not the basis for a production estimate.

Classification procedure (inferred from the text):
1. Script for me, on my machine, once: estimate as a program.
2. Others run or maintain it, or inputs are not controlled: multiply by about 3.
3. Must fit the interfaces and budgets of a larger system and be integration-tested: multiply by about 3.
4. Both: about 9.

Cost of making a component reusable: Brooks puts it at about 3x a one-shot (the productizing factor), where Yourdon said 2x (MMM ch. 17). Budget it only if several uses are expected.

## 3. The estimating procedure (PP ch. 2 section 13)

1. Decide how accurate it must be. The context sets the need: a grandmother asking arrival time wants lunch or dinner; a trapped diver wants seconds. Choose units to convey the accuracy:

| Duration | Quote in |
|---|---|
| 1 to 15 days | days |
| 3 to 8 weeks | weeks |
| 8 to 30 weeks | months |
| 30+ weeks | think hard before giving an estimate |

   125 working days is "about six months", which signals 5 to 7 months; "130 days" implies a precision you do not have.
2. Ask someone who has done it. An exact match is rare; a useful one is common.
3. Understand what is asked and the scope. State assumptions as part of the answer.
4. Build a rough model: for response time, a server and its arriving traffic; for a project, the steps the organisation follows plus a rough picture of the implementation. Model-building often reveals patterns and lets you reframe the question. Doubling the model effort gives only slight accuracy gain, so stop by experience.
5. Break the model into components, find how they combine (add, multiply, queue), and identify each component's parameters.
6. Give each parameter a value. Find which parameters matter most: multiplied or divided parameters outweigh added ones. Have a justifiable way to compute the critical ones (measure the existing arrival rate, time current requests, or use sub-estimates). Errors mostly creep in from sub-estimates.
7. Calculate the answer with varied critical parameters (a spreadsheet helps) and quote the answer in terms of them: "three quarters of a second with SCSI and 64 MB, one second with 48 MB". If an answer looks strange and the arithmetic is right, the model or your understanding is probably wrong; that is information.
8. Keep a record of estimates and actuals, including sub-estimates. When wrong, find out why. PP's challenge: log estimates and investigate any miss greater than 50%.

When asked on the spot, say "I'll get back to you". Estimates given at the coffee machine come back to haunt you (PP Tip 18).

## 4. Data and rules of thumb from Brooks

These are 1960s to 1990s figures. Compare ratios and shapes, not absolutes.

### 4.1 Effort grows faster than size
- Effort = constant x (instructions)^1.5 in the SDC studies (MMM ch. 8). In 1995 Brooks cites Boehm's data giving an exponent of 1.05 to 1.2 (ch. 18, 8.4). Use "superlinear, steeper with coupling", not the number.
- Small-program productivity does not extrapolate. A study of a roughly 3200-word program gave about 35,800 statements per year for one person coding and debugging; halving the program gave a much higher rate. Planning, documentation, testing, integration and training must be added. Brooks: linear extrapolation of sprint figures is meaningless.

### 4.2 Productivity falls with interactions
Aron (IBM, nine large systems, more than 25 programmers and 30,000 instructions): about 10,000 instructions per man-year with very few interactions among parts, about 5,000 with some, about 1,500 with many. These exclude system test; halving them covers it. Lasting point: roughly a seven-fold drop as coupling rises. Use it to argue for decoupling before staffing.

### 4.3 Complexity classes
Brooks's guideline: compilers are about three times as hard as normal batch applications, and operating systems about three times as hard as compilers (roughly 1 : 3 : 9). Hair's Bell Labs data gave about 600 words per man-year for control programs and about 2,200 for translators; OS/360 groups gave 600 to 800 and 2,000 to 3,000 debugged instructions per man-year respectively. Brooks flags that causality is unclear (complex jobs may be complex because more people were assigned).

### 4.4 Productivity per statement is roughly constant
Corbato (Multics): about 1,200 debugged lines per man-year in PL/I. Productivity is roughly constant in elementary statements, and a suitable high-level language can raise productivity as much as 5x (MMM ch. 8; Taliaffero in the notes: constant about 2,400 statements per year across assembler, Fortran and COBOL). Modern reading: expressing the same work in fewer statements helps; it does not help with the conceptual part (see `tools-and-build-vs-buy.md`).

### 4.5 Schedule fractions (Brooks's rule of thumb, ch. 2)
- 1/3 planning, 1/6 coding, 1/4 component test and early system test, 1/4 system test with all components in hand.
- Differences from usual practice: planning is larger (but only enough for a detailed, solid specification, not research or exploring new techniques); half the schedule goes to debugging finished code; coding, the easiest part to estimate, gets one sixth.
- Back-calculation (inferred): if coding is estimated at X, the whole job is about 6X; if someone says coding is 90% done, at most about half the schedule should be considered consumed.
- Do not estimate the whole task by estimating coding and applying ratios (ch. 8): an error in the coding estimate or the ratios gives ridiculous results.
- Caveat: Brooks in 1995 (ch. 19) says the waterfall model taints this rule. In modern work the same activities run interleaved. Use the fractions to test whether specification, verification and integration are visibly planned, not as a formula. If you use automated tests and continuous integration, the "late system test" share shrinks as a surprise but the work remains.

Why late system test is especially costly: the slip surfaces at the end with no warning, the team is fully staffed (cost per day at maximum), and other business depends on the delivery.

### 4.6 Time actually available
- Portman (ICL): teams missed estimates by about a factor of 2 despite careful PERT estimates, because only about 50% of the working week was real programming and debugging; the rest went to machine downtime, urgent short jobs, meetings, paperwork, sickness and personal time. Bardain (1964) measured 27%.
- Estimate in productive hours, and log where time really goes. For an agent session, the analogue is time waiting on builds, reviews, approvals and clarifications (adaptation).
- Portman's remark: when everything has been seen to work, all integrated, there are about four more months of work (MMM ch. 20 notes). Treat integration as a distinct, sizeable item.

### 4.7 Schedule law (Boehm, MMM ch. 19)
- Cost-optimal time to first shipment: T = 2.5 x (M)^(1/3), where M is effort in man-months and T is in months. Based on about 63 projects, mostly aerospace; Brooks says coefficients differ for commercial software but the shape is backed by data.
- Cost rises slowly if the planned schedule is longer than optimal and sharply if it is shorter.
- Hardly any projects succeed in less than 3/4 of the calculated optimum schedule, regardless of the number of people.
- Use: sanity check, and ammunition against an impossible schedule. If the requested time is under 0.75 T, cut scope rather than add people.

### 4.8 Staffing ramp and turnover (MMM ch. 20 notes)
Vyssotsky: a large project can absorb manpower buildup of about 30% per year before the informal structure strains. Corbato: expect about 20% a year turnover on a long project, and plan to train and integrate replacements.

## 5. Converting effort to calendar

1. Pick the matching productivity datum from comparable debugged, documented work; scale for complexity class.
2. Treat effort as nonlinear in size and in coupling.
3. Divide by productive hours (about half of the nominal week in Brooks's data), not by nominal hours.
4. Add the specification, test, integration and documentation lines explicitly.
5. Do not take effort in person-months and divide by head-count to get a date; that is the man-month myth (see `staffing-and-partitioning.md`).
6. Then compare the answer with the Boehm figure (4.7).

## 6. Estimate versus date

MMM ch. 2 "gutless estimating": the customer's urgency can govern the scheduled completion but not the actual completion. Omelette: promised in two minutes and not set, the customer can wait or eat it raw; turning up the heat gives an omelette burned in one part and raw in another. False scheduling to match the desired date is common in software because estimates have little data behind them and are hard to defend.

Rules:
- Present the estimate and the wished-for date as two things.
- Negotiate scope, not arithmetic: what can be delivered by the date at the stated quality.
- Until you have your own data, hold your estimate: a poor hunch is still better than a wish-derived number (Brooks's argument).
- Publish your productivity and defect figures over time so that estimates have a defence.

## 7. Iterate the schedule with the code (PP Tip 19)

For large projects normal estimating breaks down and the timetable usually comes from experience on that project. Practice incremental development repeating: check requirements, analyse risk, design, implement, integrate, validate with users. Do not fix the number of iterations up front unless it is the same team, same technology and a similar application. After each increment refine the guess about iterations and contents. Management wants one hard number up front; explain that team, productivity and environment determine the schedule, and that per-iteration refinement gives the most accurate estimate available.

Related behavioural data (MMM ch. 14, government contractor studies): estimates revised carefully every two weeks before an activity starts do not change significantly as the start approaches, however wrong; overestimates fall steadily during the activity; underestimates do not change until about three weeks before the scheduled completion. So late-surfacing underestimates need sharp interim milestones to be seen early.

## 8. Worked examples

These calculations are illustrative arithmetic on the formulas above, not book examples unless stated.

Example A (from MMM ch. 2). A task estimated at 12 man-months for 3 people over 4 months, with monthly milestones A to D. Milestone A arrives after two months. Options Brooks lists: (1) assume only the first part was misestimated, 9 man-months remain in 2 months, 4.5 people, add 2; (2) assume the whole estimate was low by 2x, 18 man-months remain, 9 people, add 6; (3) reschedule generously ("take no small slips"); (4) trim the task. Options 1 and 2 fail because the new people need training (if one month, 3 man-months go to work not in the estimate), the work must be repartitioned five ways (some finished work is lost) and system test grows. At the end of month 3 more than 7 man-months remain for 5 trained people and one month: as late as if nobody had been added.

Example B (my arithmetic with Boehm's formula). Effort 12 man-months: T = 2.5 x 12^(1/3) = 2.5 x 2.29, about 5.7 months. 0.75 T is about 4.3 months, so the 4-month plan in example A was already below the point where hardly any projects succeed, regardless of staffing. Effort 36 man-months: T about 8.3 months; 0.75 T about 6.2 months.

Example C (PP exercise, inferred arithmetic). Bandwidth of a 1 Mbps line versus a person carrying a 4 GB tape: 4 GB is 32 gigabit, about 32,000 seconds at 1 Mbps, about 9 hours; the walker wins if the trip is under about 9 hours, ignoring tape access time (state that scope assumption).

Example D (adaptation: agent task). Ask for a feature that adds an endpoint with validation, persistence and docs. A coding-only estimate says "small". Classification: it plugs into an existing service, so it is a component, not a program (about 3x). Add: contract tests against neighbours, boundary-case tests, docs, and a clean-build run. Give a range, name the two parameters that move it (how well the existing tests cover the area, whether the schema must change), and state the assumption that the interface is fixed.

## 9. Warning signs and verification

Warning signs:
- The estimate equals the requested date.
- A prototype or demo timing is quoted as the basis for a production estimate.
- Test and integration are under half the plan, or one block at the end.
- Schedule assembled from best-case task durations.
- Effort quoted in person-months and divided by head-count.
- Productivity figures quoted without saying what they include (planning, system test, support).
- A consistent miss of about 2x (the Portman signature: unmodelled overhead).
- One-point numbers given on the spot; units that imply false precision; no comparison to actuals.

Verification:
- Check against at least two independent data points (own history and a published or second-model figure).
- Check that the quoted rate includes test and documentation.
- Compare estimated productive hours with logged time.
- State the class of deliverable, the assumptions, the range, the dominant parameters.
- After the work, record the actual and compute the miss; investigate if over 50%.

## 10. Dated material

Absolute productivity numbers (hundreds to thousands of lines per man-year), PERT paper charts, the 1.5 exponent as a fixed constant, and the batch-era fractions are dated. What lasts: nonlinearity with size and coupling, the roughly 50% productive time finding, the range of about seven across levels of interaction, productivity per statement being nearly constant (so higher-level expression pays), and not generalising from small programs.
