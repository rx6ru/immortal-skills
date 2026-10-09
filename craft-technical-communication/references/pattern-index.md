# Pattern and antipattern index

One line per named item. "CP" is Communication Patterns (Read 2023); "PP" is Pragmatic Programmer; "MMM" is Mythical Man-Month. A pattern is a reusable solution known to be effective; an antipattern looks like a solution but costs more than it gives (it is not merely the opposite of a pattern). Detail is in the file named in the last column.

## Contents

1. Visual patterns (CP Part I)
2. Written and verbal patterns (CP Part II)
3. Knowledge-management patterns (CP Part III)
4. Remote and async patterns (CP Part IV)
5. Pragmatic Programmer and Brooks items

## 1. Visual patterns (CP Part I)

| Name | Kind | One line | File |
|---|---|---|---|
| Know Your Audience (ch. 1) | pattern | Name the readers, the thing you want from them, their technical level, detail needed and language; pick diagram type and notation to fit | diagrams-checklist |
| Mixing Levels of Abstraction (ch. 1) | antipattern | Parent and child elements in one view; draw one level per diagram | diagrams-checklist |
| Representational Consistency (ch. 1) | pattern | Same names and IDs across levels; dashed boundary labelled like the parent; figure captions | diagrams-checklist |
| Color Overload (ch. 2) | antipattern | Too many or meaningless colours; few colours, one per category, with a key | diagrams-checklist |
| Boxes in Boxes in Boxes (ch. 2) | antipattern | One box form for many meanings, deeply nested; use labels, merge, differentiate, split | diagrams-checklist |
| Relationship Spiderweb (ch. 2) | antipattern | Crossing lines and labels; orthogonal routing, fewer crossings, line jumps, move noisy components out | diagrams-checklist, text-diagrams |
| Balance Text (ch. 2) | pattern | Short labels, no repeated words, numbered notes, prose and tables beside the diagram | diagrams-checklist |
| Relying on Color to Communicate (ch. 3) | antipattern | Add pattern, symbol, shape or text; test in greyscale and colour-blindness simulation; check contrast | diagrams-checklist |
| Include a Legend (ch. 3) | pattern | Explain symbols, colours and acronyms; partial or linked legends save space | diagrams-checklist |
| Appropriate Labels (ch. 3) | pattern | Name plus type on nodes, verb phrase on edges, 12 pt minimum | diagrams-checklist |
| The Big Picture Comes First (ch. 4) | pattern | Context before detail; why before how | diagrams-checklist |
| Match Diagram Flow to Expectations (ch. 4) | pattern | Start top-left, requests left to right, numbered steps | diagrams-checklist |
| Clear Relationships (ch. 4) | pattern | One-way labelled arrows; five relationship types and matching forms | diagrams-checklist |
| Using Icons to Convey Meaning (ch. 5) | antipattern | Icons only in addition to labels; icon-removal test | diagrams-checklist |
| Using UML for UML's Sake (ch. 5) | antipattern | Choose notation by audience: standard with legend, simplified, or simple boxes | diagrams-checklist |
| Mixing Behavior and Structure (ch. 5) | antipattern | One message per diagram; split structural and behavioural | diagrams-checklist |
| Going Against Expectations (ch. 5) | antipattern | Follow colour, shape, notation and technology conventions or state the deviation | diagrams-checklist |
| Illegible Diagrams (ch. 6) | antipattern | Pick landscape canvas first; legible at display size; crop-and-enlarge rescue | diagrams-checklist |
| Style Communicates (ch. 6) | pattern | Sketch look signals draft, polished look signals decided; match house style | diagrams-checklist |
| Misleading Composition (ch. 6) | antipattern | Zero baselines, shared scales, honest counts, equal sizes unless meaningful | diagrams-checklist |
| Create a Visual Balance (ch. 6) | pattern | Approximate symmetry or counterweights; consistency | diagrams-checklist |

## 2. Written and verbal patterns (CP Part II)

| Name | Kind | One line | File |
|---|---|---|---|
| Simple Language (ch. 7) | pattern | Short common words, defined terms, no idioms or sarcasm | writing-documents |
| Acronym Hell (ch. 7) | antipattern | Define acronyms at first use; keep a glossary | writing-documents |
| Structured Writing (ch. 7) | pattern | Pyramid: conclusion first, supporting points grouped and ordered | writing-documents |
| Syntax of Technical Writing (ch. 7) | technique group | Strong verbs, short sentences, precise paragraphs, consistent vocabulary | writing-documents |
| Audience Empathy (ch. 7) | pattern | Knowledge and needs questions; header with key points, scope, non-scope, audience, prerequisites | writing-documents |
| Using the Acceptance Prophecy (ch. 8) | pattern | Expect approval; relevant for live presentation, not written work | messages-and-status |
| Giving Your Full Attention (ch. 8) | pattern | Listen fully; restate and ask; transfers as careful reading of requests | messages-and-status |
| Using Body Language and Gestures (ch. 8) | pattern | Human-presenter skill; no agent transfer | (none) |
| Battling Bias (ch. 8) | pattern | Name biases, slow decisions by writing, consult a diverse group, record counter-evidence | writing-documents |
| Being Present (ch. 8) | pattern | Active listening and summarising back | messages-and-status |
| Awareness of Cultural Differences (ch. 8) | pattern | Research and ask; encoding and decoding differ by background | messages-and-status |
| Influence and Persuasion techniques (ch. 8) | technique group | Headline statement, bold words, credibility statement, anticipate pushback, reciprocity, pauses, give options, repetition, reframing, redefining | writing-documents |
| Establish Your Credentials (ch. 9) | pattern (ethos) | Credentials by action and outcome, not bragging | writing-documents |
| Use Trustworthy Sources (ch. 9) | pattern (ethos) | Cite reputable and independent sources; archive links | writing-documents |
| Be Transparent (ch. 9) | pattern (ethos) | Disclose conflicts and biases; cite disagreeing sources | writing-documents |
| Demonstrate Your Knowledge (ch. 9) | pattern (ethos) | Real examples, correct terms, simple explanations | writing-documents |
| Tell a Story (ch. 9) | pattern (pathos) | Success, failure, use-case and clarity stories | writing-documents |
| Speak from the Heart (ch. 9) | pattern (pathos) | Authentic, true stories; listen | writing-documents |
| Vivid Language and Strong Imagery (ch. 9) | pattern (pathos) | Metaphor and analogy that explain; sparingly in technical text | writing-documents |
| Use Data and Facts (ch. 9) | pattern (logos) | Credible data with limits stated | writing-documents |
| Make Logical Connections (ch. 9) | pattern (logos) | Transitions and structure; connections must make sense to the audience | writing-documents |
| Use Reasoning and Argumentation (ch. 9) | pattern (logos) | Trade-off analysis, ADRs, preempt counterarguments with alternatives and FAQ | writing-documents |

## 3. Knowledge-management patterns (CP Part III)

| Name | Kind | One line | File |
|---|---|---|---|
| Products over Projects (ch. 10) | principle | File knowledge by product with tags and metadata | documentation-systems |
| Abstractions over Text (ch. 10) | principle | Lists, tables, ratings and charts chosen to fit content; alt text | writing-documents |
| Perspective-Driven Documentation (ch. 10) | pattern | Stakeholder concerns served by DRY, embedded, layered artefacts | documentation-systems |
| Get Feedback Early and Often (ch. 11) | pattern | Share small drafts, numbered assumptions, checkpoints in the workflow | documentation-systems, messages-and-status |
| Share the Load (ch. 11) | pattern | Open formats, owners with understudies, templates, notifications | documentation-systems |
| Just-in-Time Architecture and Documentation (ch. 11) | pattern | YAGNI for docs; defer decisions; retire stale docs; parking lot | documentation-systems |

## 4. Remote and async patterns (CP Part IV)

| Name | Kind | One line | File |
|---|---|---|---|
| Synchronize Time (ch. 13) | pattern | Always give zone; ISO dates; recipient's zone or UTC | messages-and-status |
| Empathy and Compromise (ch. 13) | pattern | Rotate and compensate inconvenient meetings; record; async before and after | messages-and-status |
| Split Shifts (ch. 13) | pattern | Shifted hours to create overlap with far zones | messages-and-status |
| Respect Working Patterns (ch. 13) | pattern group | Communicate availability, defend part-time hours, plan holidays, allow for culture, real capacity, efficient booking | messages-and-status |
| Improve Energy and Productivity (ch. 13) | pattern group | Control notifications, automate, work with rhythms, schedule for energy, protect focus time | messages-and-status |
| Synchronous versus Asynchronous (ch. 14) | decision principle | Table of when to use each; asynchronous sandwich | messages-and-status |
| Enhance Meetings (ch. 14) | pattern | Goal, agenda, parking lot, right invitees, async before and after, documented outcome | messages-and-status |
| Reducing synchronous meetings (ch. 14) | pattern | Give async access to status, trial no-meeting blocks, redesign necessary meetings | messages-and-status |
| Direction Matters (ch. 14) | pattern | Unidirectional works async; bidirectional varies; switch after about four exchanges | messages-and-status |
| Enhance Async (ch. 14) | pattern | Automate access, pre-fill status, connect tools | messages-and-status |
| Setting and Handling Expectations for Async (ch. 14) | pattern | Who, What, When, Wah-wah, Why | messages-and-status |
| Remote-First Working (ch. 14) | principle | Process and decisions designed for remote; outcomes over hours | messages-and-status |
| Symmetrical Email (ch. 15) | pattern | Urgency and response in the subject, per-person asks, links not attachments | messages-and-status |
| Online Presentations (ch. 15) | pattern group | Engagement, attention, content, screen shares | messages-and-status |
| Slideument (ch. 15) | antipattern | Deck that holds everything the presenter says | messages-and-status |
| Infodeck (ch. 15) | pattern | Stand-alone reading deck for diagrams and layout | messages-and-status |
| Attach instead of link (ch. 15) | antipattern | A copy per recipient; share a link with access rights | messages-and-status, documentation-systems |
| Tool and data proliferation, shadow IT (ch. 15) | antipattern | Sprawl, drifting copies, security gaps | documentation-systems |
| Tool Selection (ch. 15) | pattern | MoSCoW requirements, ADR with criteria, cultural fit | documentation-systems |
| Tool Governance (ch. 15) | pattern | Audit, portfolio, evaluate, consolidate, phase in, keep governing | documentation-systems |

## 5. Pragmatic Programmer and Brooks items

| Name | One line | File |
|---|---|---|
| Communicate: both what you say and the way you say it (PP ch. 1, tip 10) | Eight practices: know what to say, know the audience (WISDOM), choose the moment, choose a style, make it look good, involve the audience, listen, get back to people | writing-documents, messages-and-status |
| English is another programming language (PP ch. 8, tip 67) | Apply DRY, orthogonality, automation and version control to prose | documentation-systems |
| Build documentation in, do not bolt it on (PP ch. 8, tip 68) | Comments say why; generate views from a model; date every page | documentation-systems |
| Gently exceed users' expectations (PP ch. 8, tip 69) | Common understanding of the deliverable; small cheap extras | documentation-systems |
| Sign your work (PP ch. 8, tip 70) | Report done only when tested and documented | messages-and-status |
| Documentary hypothesis (MMM ch. 10) | A few documents (what, when, how much, where, who) are the manager's pivots | writing-documents |
| The other face (MMM ch. 15) | Docs for use, belief and modification; self-documenting source; tests at the edges | writing-documents |
| Flow-chart curse (MMM ch. 15) | Detailed flow charts are an obsolete nuisance; keep a one-page structure graph | writing-documents |
