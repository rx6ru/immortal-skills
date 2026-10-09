# Decision pitfalls

Ways architecture decisions go wrong, how to recognise each, and what to do instead. Sources: Hard
Parts ch. 1, ch. 2, ch. 3, ch. 15; Fundamentals preface and ch. 1; Communication Patterns ch. 8,
ch. 9, ch. 12; Mastering API Architecture intro.

Entry format: signal; why it fails; do instead; check.

## Contents

1. Analysis pitfalls
2. Advocacy pitfalls (including cognitive bias, 2.5 and 2.6)
3. Process pitfalls
4. Scope pitfalls
5. Governance pitfalls
6. Agent-specific pitfalls
7. Quick screen

## 1. Analysis pitfalls

### 1.1 Looking for the best practice

- **Signal:** "what is the best practice for...", "the industry standard is...", a recommendation
  with no mention of this system.
- **Why it fails:** each problem is a particular mix of organisation, technology and constraints;
  the best design would maximise every competing factor, which is not available (Hard Parts ch. 1).
- **Do instead:** look for the least-worst set of trade-offs for this context.
- **Check:** the recommendation names at least one fact about this system that it depends on.

### 1.2 The option with no downside

- **Signal:** a consequences section with only benefits; "there is no real cost".
- **Why it fails:** every architecture choice is a trade-off; if none is visible, it has not been
  found yet (Fundamentals ch. 1).
- **Do instead:** keep looking; ask what gets harder, slower, more expensive or more coupled.
- **Check:** each option has at least one stated disadvantage.

### 1.3 Comparing unlike things

- **Signal:** a product compared with a category, or a component compared with a platform that
  contains it; a team arguing "X versus Y" where X and Y solve different problems.
- **Why it fails:** overlapping capabilities make the comparison unfair (Hard Parts ch. 15). The
  case study opens with exactly this, an integration bus argued against a streaming platform.
- **Do instead:** name the capability being chosen and compare only that.
- **Check:** every option could be substituted for every other in the same slot of the design.

### 1.4 Missing option

- **Signal:** two options, both of which the proposer already knew; no "do nothing"; no recently
  available alternative.
- **Why it fails:** the list is not exhaustive (Hard Parts ch. 15). A reviewer finding an
  unconsidered alternative is grounds to reject an ADR (Mastering API Architecture intro).
- **Do instead:** scan by category before scoring.
- **Check:** the ADR lists eliminated candidates with a reason each.

### 1.5 Deciding out of context

- **Signal:** a generic pros-and-cons table reused from an article; all criteria treated as equal.
- **Why it fails:** context changes which criteria carry weight and can reverse the result (Hard
  Parts ch. 15).
- **Do instead:** take criteria from this system's drivers and characteristics; drop criteria that do
  not apply.
- **Check:** each criterion has a source in this project.

### 1.6 Deciding without scenarios

- **Signal:** only abstract ratings; no concrete workflow traced through the options.
- **Why it fails:** generic drivers miss the cost that only shows when a real workflow crosses the
  proposed boundary (Hard Parts ch. 15).
- **Do instead:** model a change, an extension and a cross-boundary or failure case.
- **Check:** scenarios are named after real requirements or expected changes.

### 1.7 Overwhelming evidence

- **Signal:** a large matrix handed to a decision maker with no conclusion.
- **Why it fails:** non-technical owners cannot decide from it (Hard Parts ch. 15).
- **Do instead:** one either/or question in outcome terms, table in support.
- **Check:** the summary fits in three sentences.

### 1.8 False precision

- **Signal:** totals compared to a decimal place; unweighted scores deciding the outcome.
- **Why it fails:** architecture comparisons are qualitative; numbers on a five-point scale encode
  judgement, not measurement (Hard Parts ch. 15; scoring format from Communication Patterns app. A).
- **Do instead:** keep rationale per score; test whether the conclusion survives a one-point change
  in the most uncertain cells; measure where a measurement is cheap.
- **Check:** each score has a rationale; sensitivity is stated when totals are close.

### 1.9 Vague or composite criteria

- **Signal:** "must be scalable", "improves agility" with no measure.
- **Why it fails:** unmeasurable criteria cannot discriminate between options or be governed (Hard
  Parts ch. 1).
- **Do instead:** decompose and attach a measure (`architecture-characteristics.md`).
- **Check:** each criterion has an observable.

### 1.10 Advice past its constraints

- **Signal:** "we always do it this way"; a pattern justified by a cost or limitation that no longer
  exists.
- **Why it fails:** architectures are products of their context; styles became dominant under
  constraints of their time, and the axioms keep changing (Fundamentals preface, ch. 1; Hard Parts
  ch. 1).
- **Do instead:** ask what constraint made the advice sensible and whether it still holds here.
- **Check:** the ADR's Context states the assumptions the decision rests on.

### 1.11 "Decouple everything"

- **Signal:** loose coupling treated as a goal in itself.
- **Why it fails:** fully decoupled parts cannot communicate; coupling is a dosage question (Hard
  Parts ch. 2).
- **Do instead:** decide where coupling should be and what kind.
- **Check:** the design names its intended coupling points.

## 2. Advocacy pitfalls

### 2.1 Evangelism and snake oil

- **Signal:** a technology presented through its strengths only; a tool promising a surprising new
  capability; "it worked brilliantly at my last company".
- **Why it fails:** evangelism magnifies the good and hides the bad, and the trade-offs come back
  later. One success with a characteristic does not generalise (Hard Parts ch. 15).
- **Do instead:** ask the advocate for an honest good-and-bad assessment; run scenario analysis on
  likely domain scenarios.
- **Check:** the proposal's author has written its disadvantages.

### 2.2 Being pushed into the opposing camp

- **Signal:** a debate has become two sides, and you are expected to argue the other one.
- **Why it fails:** you stop being able to arbitrate trade-offs.
- **Do instead:** bring it back to trade-offs. In the source's example, instead of arguing against a
  proposed single repository, the architect agreed to try it with metrics and fitness functions to
  catch the specific risk, accidental coupling between projects (Hard Parts ch. 15).
- **Check:** the response to a contested proposal is a trial with stated measures, or a trade-off
  table, not a counter-position.

### 2.3 Undisclosed interest or bias

- **Signal:** recommending a vendor one has worked for, a tool one built, a framework one prefers,
  without saying so.
- **Why it fails:** undisclosed interests cost credibility when discovered and leave the reader
  unable to weigh the advice (Communication Patterns ch. 9).
- **Do instead:** declare motivations, biases and conflicts up front or just before the relevant
  part; cite sources that disagree; consider whether someone else should make the case. Categories
  to check: employment, financial interest, personal relationships, ideological preference,
  professional association.
- **Check:** the ADR or proposal has an assumptions-and-interests line where one applies.

### 2.4 Persuasion out of balance

- **Signal:** all data and no context; or vivid language and no evidence; or authority and no
  reasoning.
- **Why it fails:** credibility, emotional relevance and logic work together (Communication Patterns
  ch. 9).
- **Do instead:** give context first (why are we deciding, who is affected), then data from credible
  sources with their limits, then the reasoning that connects them. Explain data; do not leave it to
  speak for itself. Use plain terms correctly; jargon used to impress backfires. Use marketing
  adjectives and hyperbole sparingly in technical documents (that caution is marked inferred in the
  notes).
- **Check:** the recommendation contains a why-now, at least one sourced fact, and an explicit
  link from facts to conclusion.

### 2.5 Believing the decision owner is unbiased

- **Signal:** "we looked at it objectively"; a decision made quickly in a meeting or chat; the same
  people who proposed the option are the only reviewers.
- **Why it fails:** cognitive biases are unconscious simplification errors, comparable to premature
  optimisation, and they remain in any owner (Communication Patterns ch. 12, myth 7; ch. 8). They
  cannot be eliminated, so the working strategy is awareness plus process. Fast, instinctive
  judgement (the book's "system 1", after Kahneman, which it presents as an abstraction) dominates
  real-time conversation; asynchronous work leaves room for slower reasoning. Leaning too far on the
  fast mode produces bias and error; leaning too far on the slow mode produces analysis paralysis.
- **Do instead:** use the countermeasures in 2.6. Expect and invite dissent; ask consulted people to
  say what is unsafe and why; write down the strongest case for the rejected option.
- **Check:** the Consultation section records at least one dissenting or cautionary input, or states
  that none was received.

### 2.6 Specific biases and their countermeasures

Source: Communication Patterns ch. 8 ("Battling Bias") and ch. 12. The book names three biases to
watch in technical decisions. The "Do instead" lines combine its countermeasures with agent
adaptations, marked as such.

| Bias | What it looks like in a technical decision | Do instead |
|---|---|---|
| Confirmation bias: reading information as support for what you already believe | Researching a technology and finding only articles that praise it; an ADR whose evidence all points one way; coming back from a conference convinced; a user's stated preference treated as the answer | Deliberately look for perspectives that disagree and note them in the ADR, including the strongest argument against the chosen option. Adaptation: search for "problems with X" and "alternatives to X" as well as "X tutorial", and record what the disagreeing sources say |
| Hindsight bias: believing after the outcome that it was predictable ("I knew the upgrade would make it worse"), inevitable ("it had to happen"), or misremembering your own position ("I said so" when nobody did). Occurs when things go very right or very wrong, or when a client changes their mind | Post-incident reviews and retrospective ADRs that rewrite the decision as obvious; blame assigned for a call that was reasonable with the information at the time | Record the reasoning at decision time (the ADR is that record). Adaptation: when writing a retrospective ADR, label it as written later and state what was and was not known when the decision was made |
| Groupthink: wanting harmony produces flawed decisions: dissent goes unspoken, alternatives are not analysed, outside views are ignored | Everyone agrees quickly; no alternative has a score or a rationale; reviewers are all from one team | Ask for commitment, not agreement, so that dissent is expected (myth 6 and 7 in ch. 12). Consult people outside the team. State in the ADR who was invited, including those who stayed silent |

Countermeasures for bias in general (ch. 8):

1. **Learn the biases.** Awareness is the first step because they are unconscious.
2. **Slow the decision down by writing it up.** Documenting the decision in an ADR forces careful
   thought because the template asks for context, options and consequences.
3. **Put bias prompts in the template or feedback form.** The book recommends adding them but does
   not list them. Adaptation, prompts an agent can answer in the ADR: What evidence would contradict
   this choice, and did I look for it? What would change this decision? Which sources disagree with
   me, and what do they say? Which option did I compare against only briefly? What do I or the
   author gain from this outcome?
4. **Reduce distractions** while analysing and deciding.
5. **Ask others for feedback, knowing the limit.** Reviewers share your biases; if they share the same
   one, their agreement is itself confirmation. Prefer reviewers who differ in role and background.
6. **Make the ADR's Consultation section do the work.** The book's example has a Consultation
   heading in every ADR and asks a diverse group (roles, age, gender, experience, tenure) to look
   for biases; its stated aim is that the worst outcome is everyone agreeing. A related finding the
   notes cite (Taras et al., HBR 2021): exposure to different institutions, politics and economics
   improves problem solving and decisions, while differences in age, culture and language can
   harm team climate unless handled deliberately.

Check an ADR for bias handling (from ch. 8; item 3 partly inferred in the notes): it has a
Consultation section naming diverse reviewers; it lists alternatives and counter-evidence; it
carries bias prompts or states which were answered.

Agent translation (ch. 8): when producing an ADR or recommendation, include the alternatives
considered, the evidence against the chosen option, and the question "what would change this
decision?"; state uncertainty; do not simply confirm the user's prior. Language models inherit
biases from their training data, so the agent is also subject to the first row: a fluent,
familiar-sounding recommendation is not evidence. Cite the repository facts that support it.

Persuasion note (inferred in the notes): repetition makes people believe a claim more, which is
the same mechanism as confirmation bias. Do not use repetition as a substitute for evidence in an
ADR; state the point once with its support.

## 3. Process pitfalls

Each corresponds to a decision-making myth in Communication Patterns ch. 12.

| Pitfall | Signal | Do instead |
|---|---|---|
| Treating decisions as linear | The draft is never revised; earlier decisions are never revisited | Iterate on the draft; supersede when new information arrives |
| Too many options | Six-way comparisons, shallow on each | At most three in depth |
| Rank decides | The most senior person chooses regardless of expertise | Owner is the most expert or most affected person |
| Everyone weighs in | Review by the whole organisation | Input from those important to implementation; others informed |
| Undirected feedback | "Any thoughts?" | Ask each stakeholder a specific question |
| Waiting for agreement | Decision stalls until unanimous | Seek commitment, not agreement; work through safety objections |
| Whack-a-mole | The same decision reopened repeatedly | Point to the ADR; reopen only on new information, by superseding |

Other process failures:

- **Decisions made out of sight.** Reasoning lives in chat threads or in one person's head. Record
  it; if needed tie a gate to the record, lightly (Communication Patterns ch. 12).
- **Lost reasons.** A later team reverses a decision without knowing what requirement it met.
  Retrospective ADRs for significant past decisions fix this.
- **Expecting no challenge.** Most architecture decisions will be challenged, by product and project
  owners on cost and time and by developers on approach. Prepare the justification in business terms
  (Fundamentals ch. 1). The case study credits its turnaround to looking at business drivers,
  cross-team collaboration, and justifying decisions through trade-offs in business terms (Hard
  Parts ch. 15).

## 4. Scope pitfalls

### 4.1 Technical justification only

- **Signal:** "nothing else works", "the code is a mess, we need microservices".
- **Why it fails:** it is not a business justification, and it skips matching benefits to actual
  problems (Hard Parts ch. 3).
- **Do instead:** symptom, evidence, driver; then options; then a business case.

### 4.2 Assuming modularity means distribution

- **Signal:** jumping from "hard to maintain" to separate services.
- **Why it fails:** maintainability, testability and deployability can be partly achieved in a
  modular monolith or microkernel without the costs of distribution (Hard Parts ch. 3).
- **Do instead:** put the single-deployable modular option on the list.

### 4.3 Distributed in name only

- **Signal:** several services, one database; services that must be deployed together in order;
  dense synchronous calls.
- **Why it fails:** it is one quantum, so the promised independent characteristics are not
  delivered, and the result is a distributed big ball of mud (Hard Parts ch. 2, ch. 3). A related
  story from Communication Patterns ch. 9: a move to many small functions and several data stores
  produced a web of function dependencies that had to be recomposed into services owned by teams.
- **Do instead:** count quanta before claiming benefits.

### 4.4 Doing everything up front

- **Signal:** a gateway, a mesh and a dozen services designed before the first need appears.
- **Why it fails:** unknown unknowns make large up-front designs wrong in ways no one can foresee;
  architectures become iterative regardless (Fundamentals ch. 1). Extract services and add
  infrastructure when the need is found (Mastering API Architecture intro).
- **Do instead:** take the next evolutionary step and record it.

### 4.5 Style without the practices it assumes

- **Signal:** a fine-grained service style with manual provisioning, little automated testing and
  infrequent releases.
- **Why it fails:** style and engineering practice have to fit each other; the mismatch creates
  heavy friction (Fundamentals ch. 1).
- **Do instead:** rate options as this team would actually run them, or include the practice changes
  in the consequences.

### 4.6 Making the technology choice for the team

- **Signal:** a decision that names a product where a constraint would do.
- **Why it fails:** an architecture decision should help teams make the right technical choice, not
  make it for them, unless a characteristic depends on the specific technology (Fundamentals ch. 1).
- **Do instead:** state the constraint ("a reactive UI framework").

### 4.7 Rule where a guideline was needed, or the reverse

- **Signal:** a rule with constant exceptions; or a "preference" whose violation breaks a
  characteristic.
- **Why it fails:** a rule cannot enumerate every condition; a guideline cannot protect a
  characteristic (Fundamentals ch. 1).
- **Do instead:** rules get a variance path and a check; guidelines leave judgement.

### 4.8 Describing only the structure

- **Signal:** "the architecture is microservices."
- **Why it fails:** structure is one of four dimensions; characteristics, decisions and principles
  are missing (Fundamentals ch. 1).

## 5. Governance pitfalls

- **Documented but not governed.** The rule is in an ADR and nowhere else. Add a fitness function
  (Hard Parts ch. 1).
- **Checks that do not run.** On-demand validation validates nothing. Wire it in.
- **Governance as obstruction.** Interlocking checks designed away from the teams, blocking ordinary
  work (Hard Parts ch. 1); or red tape heavy enough to be circumvented (Communication Patterns
  ch. 12). Keep the set small and explain each with its ADR.
- **Structural decay unnoticed.** No periodic look at whether the architecture still delivers its
  characteristics; re-evaluate architectures older than about three years (Fundamentals ch. 1).
- **Records filed with the project.** Gone when the project closes (Communication Patterns ch. 10).

## 6. Agent-specific pitfalls

These are adaptations: how the pitfalls above tend to appear when an AI coding agent is the one
recommending.

- **Reaching for the familiar pattern.** Recommending the commonly written-about option without
  reading this repository. Counter: cite the files and constraints the recommendation rests on.
- **Presenting one option.** Counter: at least two real options and "keep as is" where viable.
- **Agreeing with the user's stated preference without stating its cost.** This is forced evangelism
  from the other direction. Counter: state the trade-off once, clearly, then follow the user's
  decision.
- **Arguing a side when challenged.** Counter: return to the trade-off table; offer a measured trial.
- **Inventing numbers.** Counter: measure in the repository, or label the figure an estimate and
  show its inputs.
- **Writing a Decided or Accepted status.** The agent has not consulted anyone. Counter: Draft or
  Proposed, with the open questions listed.
- **Enlarging the task.** Turning a small change into an architecture review. Counter: apply the
  "is this an architecture decision" test first; if it fails, do the task.
- **Generated documentation as the record.** Generated reference material never explains why, and
  machine-written text can be fluent and wrong (Communication Patterns ch. 12). Counter: the ADR is
  hand-reasoned and checked against the code.

## 7. Quick screen

Run these on any proposal, including your own, before recommending it:

1. What is given up? If the answer is "nothing", stop and look again.
2. Are the options the same kind of thing, and is any category missing?
3. Where does each criterion come from in this project?
4. Which real scenario makes the chosen option look worst, and is that acceptable?
5. What one question would the business owner answer to settle it?
6. What assumption, if it changed, would reverse the decision? Is it written down?
7. Does anyone, including the author, have an interest or strong preference that should be stated?
   Did I look for evidence against my preferred option, and is it written down (2.6)?
8. What will stop this decision eroding once written: which check, running where?
9. Is the amount of analysis in proportion to how hard the decision is to reverse?
