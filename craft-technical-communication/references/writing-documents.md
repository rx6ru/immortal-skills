# Writing documents

How to structure and word technical documents, how to argue a recommendation, and what documentation a program needs. Sources: Communication Patterns (Read 2023) ch. 7, 8, 9, 10, 11; Pragmatic Programmer ch. 1 and 8; Mythical Man-Month ch. 10 and 15. Items marked (inferred) are readings or thresholds added in the notes; "Agent" lines are adaptation.

## Contents

1. Before writing: decide the message and the reader
2. Structure: answer first (pyramid)
3. Technical-writing syntax
4. Plain language and acronyms
5. Audience empathy and the document header
6. Choosing the form: lists, tables, visuals
7. Arguing a recommendation (ethos, pathos, logos)
8. Bias and consultation
9. Documents a program needs (Brooks ch. 15)
10. The managerial document set (Brooks ch. 10)
11. Checks

## 1. Before writing

- Know what you want to say. Outline first and ask "does this get across what I mean?" until it does. Typing a heading and writing whatever follows is the failure case. (Pragmatic Programmer ch. 1)
- Know your audience with WISDOM (Pragmatic Programmer ch. 1, Fig. 1.1): what do you want them to learn; what is their interest in it; how sophisticated are they; how much detail do they want; whom do you want to own the information; how can you motivate them to listen. The notes' example: one bug-report-system proposal, four pitches (end users, marketing, support managers, developers).
- Choose your moment (what is the reader's current priority) and your style (formal brief or short note). If asked for a paragraph on something that needs pages, say so.
- Involve the audience: circulate early drafts. The process of producing a document is often worth more than the document.
- Agent: write the audience, the ask and the single message as a three-line plan in your reasoning, then write.

## 2. Structure: answer first (Structured Writing, ch. 7)

- Build the text as a pyramid: key idea at the top, supporting arguments below, each broken down further. Each element summarises its children (vertical link) and sits in a logical order with its siblings (horizontal link). State a major idea, then answer the questions the reader will have about it. Major ideas come before minor ones.
- Newspaper analogy: the headline carries the story; the reader may stop at any point and still have the key points.
- Example from the notes: an email that narrated the reasoning chronologically (supplier cannot attend, people on leave, school runs, Tuesday 10 a.m. looks best) was rewritten to open "We need to reschedule the kick-off meeting. Can you let me know ASAP if Tuesday 10am works?" and then give reasons. (Replace "ASAP" with a dated deadline, see `messages-and-status.md`.)
- Apply to technical documents, reports, slide decks, PR descriptions and ADRs.
- Test: truncate after any paragraph; what remains is a coherent shorter message. Siblings are grouped logically (roughly non-overlapping, inferred).

## 3. Technical-writing syntax (ch. 7)

Clarity is the most fundamental rule.

- Strong verbs. Prefer precise active verbs and limit be/was/happen. "The error notification happens when ..." becomes "The service generates the notification when ...". Avoid "there is/there are" openings. Match the audience: a weak verb the reader knows beats a strong one they may not. Prefer active voice naming the actor (inferred).
- Short sentences. They read faster and, like code, shorter text has fewer bugs and is easier to maintain; one reason for each sentence to exist. A working ceiling of about 20 to 25 words is a heuristic (inferred).
- Precise paragraphs. First sentence is the most important (readers scan). One topic per paragraph (a sentence is like a method, a paragraph like a class). Cover what, why it matters, how the reader can use it or know it is true. Three to five sentences is the sweet spot; over seven is a wall of text, split it; many tiny paragraphs, merge or make a list.
- Consistent vocabulary. One word for one thing throughout (like not renaming a variable mid-method): choose among application/program/software, engineer/developer, user/client/customer. Call out a similar word that means something different. If you introduce a short name, use it consistently; if the long form appears only a few times, skip the short form.
- Checks: count "there is" and weak verbs; look at maximum sentence length; paragraph sentence counts; grep for synonyms of the key terms.

## 4. Plain language and acronyms (ch. 7)

### Simple Language
- Problem: complex vocabulary, long sentences, idioms and sarcasm reduce understanding, and reaching for clever words makes readers think less of you.
- Why it matters: readers with dyslexia or ADHD struggle with complex words and dense blocks; autistic readers often struggle with sarcasm and idioms; non-native readers have smaller vocabularies and may run machine translation, which copes better with simple, idiom-free text. The notes cite a 2022 study that about 4,000 word families cover about 95 percent of English news stories.
- Do: short common words; define necessary technical terms; keep a glossary (ties to domain-driven design's ubiquitous language); no idioms or sarcasm.
- Substitutions from the notes: acquire to buy; adopt to use; dispatch to send; locate to find; patron to customer; a majority of to most; as a result of to because of; is able to to can; determine the location of to find; for the purpose of to for; have a tendency to to tend to; on two occasions to twice; make decisions about to decide on; is of the opinion to thinks; in order to to to.
- Agent: avoid words such as "leverage", "utilize", "robust" and idioms such as "low-hanging fruit" in docs, commit messages and PRs.

### Acronym Hell (antipattern)
- Problem: undefined acronyms. The same acronym means different things to different people (SPA could be single-page application or single point of access); the cause is the curse of knowledge.
- Do: expand at first use (full term then acronym in brackets), and again at first use per section in long documents; say both when speaking; define in a legend or footnote for diagrams; keep a findable glossary. Acronyms that became words (radar, laser) need no definition.
- Verify: every acronym has a definition in the artefact or a visible link to a glossary.

## 5. Audience empathy and the document header (ch. 7)

- Knowledge questions: how much do they know (do not state basics); do they know something similar (use comparison); have they not used the knowledge for long (overview plus optional detail); is their knowledge out of date (compare old and new, with advantages and disadvantages).
- Needs questions: what are they trying to accomplish ("after reading, the audience will be able to ..."); what must they learn first ("... will have learned ..."); must it be done in order (numbered list).
- Header content: key points; scope; non-scope with links to where uncovered topics live; intended audience; prerequisites with links.
- Agent: README or design-doc template: TL;DR, Scope, Out of scope, Audience, Prerequisites, "After reading you will be able to ...", body.
- Verify: the first screen holds all six items.

## 6. Choosing the form (ch. 10, "Abstractions over Text")

Visuals with abstraction usually communicate better than paragraphs, but they do not replace all text; make detailed content optional for different objectives (learning versus refreshing).

Lists
- Most important item first; items start with the same part of speech; numbers only when order matters (readers ascribe meaning to numbers); similar lengths; emphasise the first sentence of multi-sentence items; at most a few sentences per item; extra space between items when more than two; consistent capitalisation and punctuation; sublists follow the same rules with a different marker and visible indent.

Tables
- Use for data that would need long prose, repeated or relational information, exact values, side-by-side comparison, and as the accessible alternative to a chart. Not for irregular content, content quickly summarised or needing heavy explanation.
- Introduce with a sentence ending in a colon; concise, visually distinct column and row headers; one data type per column; cells at most two sentences (otherwise a list); check rendering on small screens.
- Architecture uses: requirements traceability matrix, component interface specification, performance metrics report, testing matrix, stakeholder analysis matrix.

Visual abstractions
- Star ratings (0 to 5, partial stars for decimals, never more than five, give the number too, for example 3.5/5); Harvey balls (a single glyph for a five-point score, filled clockwise, consistent across the organisation, good in ADR option-evaluation tables); traffic lights (red on top, green at the bottom, or add + and - for colour-blind readers); word clouds (size equals frequency after removing stop words, used in workshops); charts for patterns and trends with a headline stating the takeaway, tables for precise values; infographics with an accessible text version.
- Accessibility: provide alternative text or formats for readers with vision impairment, those using translation, or blocked audio.
- Agent: in Markdown, a comparison of options is a table with an intro sentence and a recommendation line below it; sequential steps are a numbered list; everything else is parallel bullets or prose.

## 7. Arguing a recommendation (ch. 8 and 9)

Persuasion starts with the reader's goals. Align the proposal with them (then little persuasion is needed), do discovery in advance, and say explicitly how you will solve their problem and what they gain. People resist when they think you have not understood their problem. Persuasion is a process over many conversations.

Rhetoric triangle (ch. 9): ethos (credibility), pathos (story and emotion), logos (logic). For written technical work:

Ethos
- Use trustworthy sources: reputable publishers, professional bodies, academic databases, government agencies, conference papers, your own and credible others' experience. Several independent sources add confidence. Link directly and archive online sources (Wayback Machine "Save Page Now" or Archive.is), citing the archived address. A list titled "Further Reading" sounds less patronising than "References".
- Be transparent: disclose motivations, biases and conflicts of interest (employer, financial interest, personal relationship, ideology, professional association), up front or just before the relevant section. Cite sources that disagree with you; it shows confidence. Sometimes avoiding the conflict is better than declaring it.
- Demonstrate knowledge: real examples and case studies, terms used correctly, complex things explained simply, up-to-date knowledge; if your knowledge is superficial, ask questions and compare rather than pretend.

Pathos
- Tell a story: why we are communicating, how the problem appeared, whom it affects, before technical detail. Types: success stories; failure stories with why it failed and the lessons; use-case scenarios; clarity stories on why a decision was made (what happened in the past, the turning point, what will be done now, what will happen in the future).
- Vivid language and imagery (metaphors, similes, analogies that compare and explain) sparingly in technical documents; hyperbole and marketing adjectives conflict with plain language and honesty (inferred).
- Be authentic; never fabricate a personal story.

Logos
- Data and facts from credible sources, or state their limits and biases. Make logical connections with transitions (therefore, consequently) and structure; connections must make sense to the audience or credibility is lost.
- Reasoning and argumentation: show trade-offs (what each option costs and why the others lost). Anticipate counterarguments: an alternatives-considered section and an FAQ of predicted objections save repeated questions. Some objections are subjective ("too slow to implement" may mean revisit the criteria, or may just be a difference of opinion).
- The Architecture Decision Record is the standard container for this argument. The full template, statuses and writing guidance are in `arch-decisions-and-tradeoffs`; the book's ADR in ch. 9 has identifier and title, status, context, evaluation criteria, options scored against the criteria, decision, implications (positive and negative) and consultation (placed last because it can be long and obscure the decision). Do not copy the template here; use that skill.

Persuasion techniques worth using in writing (ch. 8)
- Headline statement: the most important message first, headline length (email subject, top of a report). A striking real figure helps if true.
- Bold words: say "The plan is ..." rather than "We will hopefully ..." when you are confident; when you are not confident, say what is uncertain. Do not use confident phrasing to hide real uncertainty (adaptation).
- Give options: a small number of options that all work for you rather than yes/no. More options reduce satisfaction with the choice. Offer two or three with a recommendation.
- Anticipate questions and pushback and plan answers; if you do not know, say you will find out, then follow through.
- Cognitive reframing and redefining: move from a bad situation to what was learned, or from the reader's concern to your focus ("Yes, this option costs more, but only it meets the compliance requirement").
- Caveat: repetition and option framing are manipulation-adjacent (inferred); the book bases them on value and listening. Persuasion can still fail for reasons outside your control.

## 8. Bias and consultation (ch. 8)

- Cognitive biases are unconscious simplification errors; they cannot be eliminated, so build in brakes. Slow decisions down by writing them (the template forces careful thought); add bias prompts to templates; reduce distractions; ask others, knowing they share biases.
- Confirmation bias: looking for what supports the existing belief; deliberately seek and record disagreeing perspectives. Hindsight bias: "I knew it" after the event; written decisions with dates protect you. Groupthink: harmony produces flawed decisions; dissent unspoken, alternatives not analysed.
- Practice from the notes: every ADR has a Consultation heading with a diverse group of reviewers (role and demographics); the aim is to find biases, and "the worst thing that can happen is everyone agreeing".
- Note: LLMs inherit biases from training data.
- Agent: when producing a recommendation include alternatives considered, evidence against the chosen option, the question "what would change this decision?", and honest uncertainty; do not simply confirm the user's prior.

## 9. Documents a program needs (Brooks ch. 15, "The Other Face")

A program tells its story to people as well as machines; for a shipped program the human-facing side is fully as important.

To use a program, a prose description with an overview first ("the map of the forest"). The nine items:
1. Purpose.
2. Environment (machines, configurations, operating system).
3. Domain and range (valid inputs, legitimate outputs).
4. Functions realised and algorithms used.
5. Input and output formats, precise and complete.
6. Operating instructions, including normal and abnormal endings as seen by the user.
7. Options and how they are specified.
8. Running time for a stated size and configuration.
9. Accuracy and checking (expected precision, built-in checks).
Often three to four pages when concise. Most must be drafted before the program is written, since it embodies basic planning decisions.

To believe a program, test cases. Ship small test cases that reassure users a copy is faithful and correctly installed, and thorough cases to run after modification, covering: mainline cases with common data; barely legitimate cases at the edge of valid input; barely illegitimate cases at the boundary on the invalid side, so bad inputs produce proper diagnostics.

To modify a program: a well-commented listing plus a sharp overview of internals: a one-page subprogram structure graph; algorithm descriptions or literature references; layout of all files; pass structure; contemplated modifications, location of hooks and exits, the author's ideas about desirable changes, and hidden pitfalls.

Self-documenting source: keep human-readable documentation merged with the source so a change touches both. Use the parts that must exist anyway (labels, declarations, names) to carry meaning; use space and format to show nesting; add prose as paragraph-level comments that give overview (most programs have enough line comments but lack these). Documentation built into structure and names gets written when the program is first written, which is when it should be. Brooks's twelve techniques include mnemonic names with version identifiers, a prose description at the top of each procedure, citing the standard literature for basic algorithms and showing how this version differs, declarations commented as a legend, and a run log. The flow-chart advice (detailed blow-by-blow charts are an obsolete nuisance; keep a one-page structure graph) is dated tooling; the lasting rule is to write the overview first and keep docs with the code.

Agent: for code you write or change, provide the overview-level comment or README section (purpose, inputs and outputs, options, constraints, how to verify), tests for mainline, barely valid and barely invalid inputs, hooks and pitfalls where they exist, and update the documentation in the same change. Comment density conventions belong to `craft-clean-code`.

Comments in code (Pragmatic Programmer ch. 8): comments explain why (purpose, trade-offs, discarded alternatives), not how. Do not hand-maintain what tools know: lists of exported functions, revision history (source control), file lists, file names. Do record ownership. Names must not mislead; a `get` routine that writes to disk is worse than a meaningless name. Per-method headers at the "JavaDoc level" (one-sentence purpose, each parameter, the return value including the not-found case) are the book's recommendation; later clean-code schools want fewer comments, so follow the project's convention and keep the why.

## 10. The managerial document set (Brooks ch. 10)

A small number of documents are the manager's pivots: they focus thought, crystallise discussions, serve as checklist, status control and database for reporting. For a software project the set answers: what (objectives and product specification), when (schedule), how much (budget), where (space allocation, read for software as environments and compute), who (organisation). Start these as mini-documents immediately, whatever the project size, instead of meeting to debate structure.

Why write them: writing decisions down exposes gaps and inconsistencies and forces hundreds of mini-decisions; it communicates decisions (policy the manager thought common knowledge is unknown to some team member); and it gives a database and checklist for review. The organisation chart and the interface specification are intertwined (Conway's Law as quoted: organisations that design systems copy their communication structures); if the design is to be free to change, the organisation must be prepared to change.

Agent: before a large task write the minimal five (objective and constraints, spec and acceptance, milestones, limits, who or which agent owns what), keep them in the repo so subagents share them, and check that they agree with each other. Conway's Law applies when splitting work across agents (inferred application). Planning detail lives in `craft-planning-and-estimation`.

## 11. Checks

- Opening states the point, ask or decision; truncation test passes.
- Header has key points, scope, non-scope, audience, prerequisites, reader goal.
- Consistent vocabulary (grep), acronyms defined, no idioms.
- Paragraphs 3 to 5 sentences; lists parallel; numbers only for order; tables introduced.
- Each claim that matters has a source or is marked as the writer's judgement; conflicts of interest disclosed.
- Alternatives and counter-evidence present in any recommendation.
- Every fact appears once (see `documentation-systems.md`).
- Documentation of code answers the nine questions that apply, and tests include boundary cases on both sides.
