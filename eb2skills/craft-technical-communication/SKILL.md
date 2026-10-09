---
name: craft-technical-communication
description: Procedures and checklists for producing diagrams, documents, PR descriptions, status updates and other messages that technical readers can actually use. Covers audience and level of abstraction, diagram clutter, colour and accessibility, narrative order, notation choice, Mermaid/PlantUML/ASCII practice, plain-language and structured writing, documentation organisation and docs-as-code, early feedback and assumptions, and asynchronous messages with explicit asks and deadlines. Use when asked to draw or fix an architecture/sequence/flow diagram, write a README, design doc, PR description, commit message, final report or status update, organise docs, write to people across time zones, or when a reader says "I don't get it", "too cluttered", "what do you need from me". The ADR template itself lives in `arch-decisions-and-tradeoffs`.
---

# Craft: technical communication

## Purpose

Success is measured at the reader, not the writer: a message works when the reader ends up with the understanding you meant and can act on it. This skill makes the agent decide audience and ask first, give each diagram or document one purpose, lead with the conclusion, keep one source for each fact, and check the result with observable tests (greyscale test, icon-removal test, truncate-after-any-paragraph test) before handing it over.

## Choose what applies

| Situation | Do this | Read |
|---|---|---|
| Asked to draw or revise any diagram | Steps A below (audience, one level, one message), then the checklist | `references/diagrams-checklist.md` |
| Output is Mermaid, PlantUML or ASCII | Steps A, then the text-diagram rules (edge budgets, classDef, autonumber, legends) | `references/text-diagrams.md` |
| README, design doc, spec, ADR prose, report, long answer | Steps B below | `references/writing-documents.md` |
| PR description, commit message, final report, status update, email/chat message, async request | Steps C below | `references/messages-and-status.md` |
| Deciding where docs live, how to keep them current, who owns them | Docs-as-code rules, single source, perspectives | `references/documentation-systems.md` |
| Writing a recommendation or choosing between options | Lead with the headline, list options and counter-evidence; ADR format from `arch-decisions-and-tradeoffs` | `references/writing-documents.md` (argument section) |
| Looking up a named pattern or antipattern | One-line index with chapter | `references/pattern-index.md` |
| One-line answer to a quick factual question | Answer first, no ceremony | none |
| The reader is the agent's own next step (scratch notes, intermediate files) | This skill does not apply; do not decorate | none |
| Code comments, naming, function layout | Not here; see `craft-clean-code` | none |
| Choosing an architecture or recording the decision template | Not here; see `arch-decisions-and-tradeoffs` | none |

## How to apply

### A. Diagrams

1. Name the audience and the ask in one line before drawing: "Audience: product owner and support lead; they must approve the scope by Friday." Role mix decides notation. Developers can read class and sequence diagrams; a mixed or non-technical audience needs a context-style diagram (system as one box, people and external systems around it) in plain labels. (Comm. Patterns ch. 1)
2. Pick one level of abstraction per diagram: system context, containers (deployable building blocks), components inside one container, code. Never draw a thing and its own parts as peers in the same view; that is the diagram form of mixing abstraction levels in one function. When you need both, draw two diagrams and show the focus system as a labelled dashed boundary in the zoomed view. (ch. 1)
3. Pick one message per diagram: structure (what exists and where) or behaviour (what happens in order), not both. A deployment topology with request numbering and error paths is two diagrams. (ch. 5)
4. Link levels explicitly: identical names or IDs across diagrams (process 2 splits into 2.1, 2.2; data stores keep their letter), captions "Figure N: ...", and text that refers to the figure by label. (ch. 1)
5. Reduce clutter before adding anything. Colours carry meaning by category (four or five at most) with a key; boxes are replaced by labels where a box adds nothing; nesting depth stays small; edges do not cross components. Details: the checklist. (ch. 2)
6. Make it readable without colour: every colour-coded category also differs by shape, line style, symbol or text. Never refer to elements by colour alone in text. (ch. 3)
7. Label for the reader: each node says what it is and does; each edge is a verb phrase that reads correctly as "source label target"; no bare arrows; no unexplained icons or acronyms. Add a legend for anything not obvious, or label directly when the diagram is tiny. (ch. 3, 5)
8. Order for reading: entry point top-left or middle-left, requests left to right, responses back right to left, steps numbered. In a document, the widest-scope diagram comes first and each later one zooms into an element of the previous. (ch. 4)
9. Choose notation by audience: standard UML only if the readers are fluent and a legend is present; otherwise simplified sequence diagrams with descriptive messages, or labelled boxes and lines. State any deviation from a notation's rules. (ch. 5)
10. Keep honest scale: bar charts start at zero, charts compared side by side share a scale or say they do not, equal sizes unless size means something, "x3" says whether fixed, minimum or maximum. (ch. 6)

### B. Documents

1. Write the point first (a sentence stating the conclusion, decision or ask), then support. Test: truncate after any paragraph and what remains is still a coherent shorter message. (ch. 7, pyramid structure)
2. Open a technical document with: key points, scope, explicit non-scope, intended audience, prerequisites, and what the reader will be able to do afterwards. (ch. 7)
3. Use short common words, defined terms, one name per concept, acronyms expanded at first use or in a glossary, no idioms or sarcasm. Paragraphs of three to five sentences with the key sentence first. (ch. 7)
4. Choose the form to fit the content: table for comparisons and exact values (introduce with a sentence ending in a colon), numbered list only for ordered steps, parallel bullets otherwise, diagram for structure or flow, prose for reasoning. (ch. 10)
5. Write each fact once. Link to the authoritative place instead of restating; generate secondary views (API docs, schema listings, version numbers) from the source. (Pragmatic Programmer ch. 8; Comm. Patterns ch. 10)
6. Keep documentation next to the code and in plain text under version control, in the same change as the code it describes. (Pragmatic Programmer ch. 8; Comm. Patterns ch. 11)
7. Write only what a named reader needs now. State deferred decisions as "not yet decided; revisit when X". Retire superseded documents visibly. (ch. 11, just-in-time)

### C. Messages and status

1. First line carries the tag and the ask: `FYI`, `Action needed by <date, time, zone>`, or `Decision needed`. Do not overuse urgency; it stops meaning anything. (ch. 15, Symmetrical Email)
2. One topic per message. Address each person's expected action separately, including "FYI only". State the cost ("15 minutes to review"). (ch. 15)
3. Give absolute deadlines with a time zone and an ISO date. Say what happens on silence ("if I hear nothing by then I will proceed with option A"). (ch. 13, 14)
4. Link to documents instead of attaching or pasting copies. (ch. 15)
5. Report status without being asked: answer first, evidence next, open items and assumptions last; say what was and was not verified. (Pragmatic Programmer ch. 1, 8)
6. Surface assumptions with IDs (A1, A2) at the top, mark each confirmed or unconfirmed, and ask for confirmation before building on them. Share a small draft early and say what feedback you want and by when. (ch. 11)
7. Switch channel when a thread bounces back and forth about four times. Use a live call for decisions and rapport; use writing for updates, drafts needing review, and anything that must be found later. (ch. 14)

### D. Decision rules used most often

| Question | Rule | Why |
|---|---|---|
| Which diagram first for a newcomer? | Context (system as one box, people and external systems around it) | Readable by almost every role; gives the big why before detail (ch. 4) |
| Which notation for a mixed audience? | Labelled boxes and lines, C4-style; UML only with a fluent audience and a legend | A non-fluent reader cannot decode UML, and UML is costly to maintain (ch. 5) |
| Colour or no colour? | Colour only as an extra; shape, line style or text carries the meaning | About 1 in 12 men have colour vision deficiency; greyscale print loses hue (ch. 3) |
| Icons? | Only beside a text label | Readers cannot be assumed to know the icon (ch. 5) |
| Table, list or prose? | Table for comparison and exact values; numbered list for order; bullets for parallel items; prose for reasoning | Each form suits one kind of content (ch. 10) |
| Diagram too busy? | Split by level or by concern before shrinking text | Diagrams are free; clutter costs the reader (ch. 2) |
| Fact appears in two docs? | Keep one, link or generate the other | Copies drift; misleading docs are worse than none (Pragmatic Programmer ch. 8) |
| Thread still unresolved after about four exchanges? | Move to a call, then write up the outcome | Back-and-forth text is expensive and loses tone (ch. 14) |
| Need input from several people? | Per-person asks, one deadline with zone, default on silence | Removes ambiguity and stalls (ch. 14, 15) |
| Writing about something not needed yet? | Do not; record as deferred with a revisit trigger | Predictive docs decay and cost upkeep (ch. 11) |
| Must a draft be shown before it is finished? | Yes, labelled draft with a feedback deadline | Early feedback is cheap; late is costly (ch. 11) |

### E. Worked example (adaptation)

Request: "Document how checkout works." Applying the steps:
1. Audience and ask: new backend developers; after reading they can find where an order is validated. No decision is requested. Record this in the header (Step B2).
2. Document layout: TL;DR, scope, non-scope (payments internals, linked), audience, prerequisites, then body. Terms: "order" used throughout (not "basket"), "payment service provider (PSP)" expanded once.
3. Diagrams: Figure 1 context (Customer, Shop system, PSP); Figure 2 containers (Web app, Orders API, Orders DB, Receipt worker) with the boundary labelled "Shop system"; Figure 3 sequence diagram for order submission, participants in call order, `autonumber`. Each has a caption and is cited in text.
4. Facts: endpoint names and status codes are generated from the OpenAPI file or linked to it, not retyped.
5. Checks: render all diagrams, run the greyscale and icon-removal tests, truncate-after-each-paragraph, link check. In the reply, give the one-line summary first, list what was verified and what was not (for example "diagrams rendered; link check not run because no tool is configured"), and list assumptions with IDs for the user to confirm.

### F. Warning signs that something needs rework

- A reader asks "what do you want from me?" or "which box is the system?"
- A diagram where a parent and its children are siblings, or where one colour is the only difference between two categories.
- Arrows without labels, icons without names, acronyms without expansions.
- A document that starts with background and history and reaches its conclusion in the last paragraph.
- The same number, command or endpoint typed in three places.
- A deadline of "soon", "ASAP" or "end of day" with no time zone.
- A status report that says "done" without saying what was checked.

## Verify

Run the checks that apply and show the results to the user in a line or two.

Diagrams (see the checklist for the full list):
- Greyscale test: convert the image or reason through the encoding; every category must still be distinguishable. For text diagrams, list the shape/line-style/label that differs per category.
- Icon-removal test: delete icons and logos; the message must survive on labels alone.
- Level test: label the diagram with one level; confirm no node is the parent of another node in the same view.
- Count: distinct fill colours (target at most five, each in the legend); nesting depth; edges per diagram (adaptation: split when a text-laid-out diagram passes about 10 to 15 edges, a heuristic, not from the book); every edge labelled; nothing overflows its shape.
- Render it. For Mermaid use `mmdc -i in.mmd -o out.svg` (mermaid-cli) or the repository's docs build; for PlantUML run `plantuml -checkonly` or render a PNG; a diagram that does not parse is a failed deliverable. Look at the rendered result, not only the source.
- Reading-order test: narrate the diagram aloud in order; if the narration jumps around, reorder nodes or number the steps.

Documents and messages:
- Truncation test: cut after each paragraph; each cut must still read as a complete, shorter message.
- Ask test: find the sentence that says what you want from the reader and by when; if missing, add it.
- Term grep: `grep -n -i` for synonyms of the main terms (user/client/customer) and for undefined acronyms; fix inconsistencies.
- Duplicate-fact check: every number, version, schema or command appears once and elsewhere is linked or generated.
- Link check: every relative link and figure reference resolves (a markdown link checker or a quick script).
- Audience test: can a reader from the named audience act on it without asking you a question? If you can, ask the user for a one-minute read-through and note what they asked.

Done means:
- Audience and ask are stated (in the artefact or the reply).
- One level and one message per diagram, labelled, legend present or unnecessary, rendered without errors.
- Information does not depend on colour or icons alone.
- The conclusion or ask comes first; deadlines carry a zone; assumptions have IDs.
- Each fact has one home; docs are in plain text in the repository next to what they describe.
- You reported what you checked and what you did not.

## Proportion and limits

- A two-line change needs a two-line message. Apply the full template (scope, non-scope, prerequisites) to documents others will rely on later, not to every reply.
- Diagrams are cheap, so splitting beats cramming, but each extra diagram must have a reader and a purpose. Do not add a diagram when three sentences or a table say it better.
- The notes on layout (symmetry and visual balance, style signalling, cultural colour meaning, body language, persuasion techniques such as repetition and framing options) are low priority for an agent. Visual balance mostly cannot be controlled in auto-laid-out Mermaid or PlantUML. Persuasion is built on understanding the reader's goals; do not use it to push a conclusion the evidence does not support.
- Thresholds marked "inferred" in the references (labels of about five words, nesting depth of two, 10 to 15 edges, sentences of 20 to 25 words) are working heuristics from the notes' reading, not figures from the books. Break them for a reason.
- Sources disagree on comment density: Pragmatic Programmer asks for a header on each class and method and comments that explain why; later clean-code schools want almost none. Code comments belong to `craft-clean-code`; here, rely on "document why, not how" and keep per-project convention first.
- Tool names (Teams, Slack, Confluence, draw.io, Thoughtworks Radar) date quickly. The surviving rule: pick the channel by purpose, direction, urgency and need to find it later.
- Single-source reports of fatigue and estimation (Zoom fatigue research, "teams that estimate least produce most") are supporting evidence only.
- Brooks's dismissal of detailed flow charts is about the 1970s; the lasting rule is to keep documentation merged with the source and to write the overview before the code.

## References

- `references/diagrams-checklist.md`: read when creating, reviewing or fixing any diagram; every visual pattern and antipattern with problem, fix, check.
- `references/text-diagrams.md`: read when the diagram is Mermaid, PlantUML or ASCII, or must be diffable in a repository.
- `references/writing-documents.md`: read for README, design doc, report, argument or recommendation, and code-adjacent documentation (Brooks's document set and "other face").
- `references/documentation-systems.md`: read when deciding where docs live, formats, ownership, perspectives, tool selection and just-in-time documentation.
- `references/messages-and-status.md`: read for PR descriptions, commit messages, status updates, email/chat, async requests across time zones, meetings versus writing.
- `references/pattern-index.md`: read to find a named pattern or antipattern quickly; one line each with chapter.

## Sources

- Communication Patterns (Read, 2023) ch. 1-7: essentials, clutter, accessibility, narrative, notation, composition, written communication.
- Communication Patterns ch. 8-9: verbal skills, bias, persuasion, rhetoric (ethos, pathos, logos) as they transfer to written work.
- Communication Patterns ch. 10-11: knowledge management principles, perspectives, feedback, shared load, just-in-time documentation.
- Communication Patterns ch. 13-15: time zones, sync versus async, remote-first, symmetrical email, presentations, tool governance.
- Mythical Man-Month ch. 10 (documentary hypothesis) and ch. 15 (the other face of a program).
- Pragmatic Programmer ch. 1 (Communicate!) and ch. 8 (team communication, It's All Writing, expectations).
