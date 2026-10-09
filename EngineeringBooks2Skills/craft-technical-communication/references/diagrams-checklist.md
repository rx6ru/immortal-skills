# Diagrams checklist

Every visual pattern and antipattern from Communication Patterns (Read 2023) Part I, in one uniform entry format. Items marked (inferred) are readings or thresholds added in the notes, not the book's wording. "Agent" lines are adaptation for diagrams an agent emits as text or images.

## Contents

1. Order of work
2. Foundation (ch. 1)
3. Clutter (ch. 2)
4. Accessibility (ch. 3)
5. Narrative (ch. 4)
6. Notation (ch. 5)
7. Composition (ch. 6)
8. Pre-delivery checklist
9. Worked review example

## 1. Order of work

Apply chapter 1 first (audience, level, links between diagrams), then reduce information (ch. 2), then make it accessible (ch. 3), then order it as a story (ch. 4), then fix notation (ch. 5) and composition (ch. 6). Diagrams are free: use as many as needed, each with one purpose. Scope creep turns a diagram multipurpose and lets clutter back in.

## 2. Foundation

### Know Your Audience (pattern, ch. 1)
- Problem: the diagram is pitched wrong for the people who must use it.
- Do: list the reader roles (developers, architects, analysts, product owner, project manager, customers, support). Group roles by diagram type and pick type and notation to fit. A class diagram suits developers, architects and database people only; a context diagram (the system and the people and systems around it) is readable by nearly everyone; a domain story suits business roles plus translators.
- Ask five questions: What do they want from you? What do you want from them (sign-off, a decision, by when)? What is their technical understanding? What level of detail do they need? What language and cultural background do they have (see plain language in `writing-documents.md`)?
- Do not: assume the company's written or unwritten template fits; ask the teams, and escalate rules that do not fit.
- Verify: you can name the audience roles and the one thing you want from them; every listed role can read the notation without help.
- Agent: write "Audience: X; they need to decide/do Y" in the reply or a caption before the diagram. State the ask explicitly in the PR, README or ADR where the diagram appears.

### Mixing Levels of Abstraction (antipattern, ch. 1)
- Problem: all information crammed into one diagram; elements from different levels sit side by side (a system box partly divided into containers, with the system-level box still related to them). Same flaw as mixing abstraction levels inside one method.
- Levels (C4 as the model): 1 system context (system, people, external systems); 2 container (the building blocks inside the system in scope); 3 component (inside one container); 4 code (usually more detail than needed). Think zoomable map. Also applies to sequence diagrams, data flow and informal sketches.
- Fix: two diagrams. Context diagram shows the system as one box with its surroundings. Container diagram shows the system as a dashed boundary with its containers inside.
- Verify: you can label the diagram with exactly one level; no element is parent or child of another in the same view; all boxes are at the same granularity.
- Agent: never place a node and its own sub-parts as sibling peers; use a subgraph or boundary only for the system in focus; in sequence diagrams do not mix service-to-service calls with method calls inside one service.

### Representational Consistency (pattern, ch. 1)
- Problem: separate diagrams at different levels that the reader must link mentally.
- Do: make the link explicit whichever diagram they see first. C4: the zoomed diagram draws a dashed boundary labelled with the same name as the central box of the parent. Data flow diagrams: number processes 1 to 3, children 2.1 to 2.3 on the level-2 diagram, data stores keep identical IDs (A, B) across levels in order of access. Notations with no formal link: show the parent process as an enclosing labelled box around its sub-processes. In documents, caption figures ("Figure 1: System X context diagram"), refer to them by label, hyperlink where possible.
- Verify: for every diagram you can point to the identical name or ID in the adjacent level; names are identical across diagrams; text cites each figure by label.

## 3. Clutter

### Color Overload (antipattern, ch. 2)
- Problem: too many colours, or colours with no meaning (tool defaults, random, "always been our colours"). Readers decode irrelevant detail even with a legend.
- Fix: minimum palette; non-clashing hues, mindful of luminosity; one colour per category (for example UI, data store, API, service) with a key. Greyscale is acceptable; do not "fix" by going all black-and-white unless intended.
- Verify: count distinct fills; each maps to a named category in a legend; no two categories share a colour; no component-per-colour rainbow.
- Agent: Mermaid `classDef` per category rather than per-node styles; in ASCII or PlantUML prefer shapes and stereotypes plus a legend; small default palette (inferred: at most four or five).

### Boxes in Boxes in Boxes (antipattern, ch. 2)
- Problem: one form of delineation (a box) used for many meanings (network, account, policy, logical location, grouping) and nested deeply. Needs whitespace, which leaves less room for the message. Common in cloud and location diagrams.
- Fix, in order: replace some boxes with labels or notes on the component; merge boxes whose separation does not serve the message; differentiate remaining boxes by colour and outline pattern together (solid line plus shaded fill versus dashed with no fill); remove unnecessary detail; split into several diagrams. Keep dashed lines for boundaries and solid for relationships. Whitespace is content; keep the background subtle with high-contrast borders and text.
- Verify: nesting depth at most two (inferred); each box style has exactly one meaning, listed in the legend; no box could be replaced by a label.
- Agent: avoid subgraph inside subgraph inside subgraph; write region, account or network as a label such as "(eu-west-1)"; split cloud diagrams per concern (network, identity, storage).

### Relationship Spiderweb (antipattern, ch. 2)
- Problem: lines cross each other and components; labels cannot be matched to lines. Tool defaults (straight arrows) are the usual cause; change the defaults.
- Fix: right-angle connectors for control of routing; place components to minimise crossings; standardise label position (near the line start or middle) with exceptions that clarify, away from corners and other labels; distinguish relationship types by colour and pattern; where crossing is unavoidable use a line jump (arc); move noisy cross-cutting components (a logging service) to a separate diagram.
- Verify: zero line-through-component crossings; few line-line crossings, any remaining with jumps; every label unambiguously next to one line; consistent label position.
- Agent: auto-layout cannot route lines, so reduce edges: split diagrams, drop cross-cutting nodes (logging, metrics, auth), order nodes for one dominant direction, use line style for relationship kinds, label every edge briefly. Split when edges exceed about 10 to 15 (inferred threshold).

### Balance Text (pattern, ch. 2)
- Problem: extra information drowns the diagram (the same word repeated in every box; text overflowing shapes).
- Do: short phrases not sentences; delete words implied by the title, context or structure; use the notation's own annotation mechanism before ad hoc side notes; numbered notes with references for the rest; move prose to text beside the diagram and relational data to a table; remove what is truly unneeded or give it its own diagram. Moving everything to footnotes only relocates the problem.
- Warning: notes fully separated from the diagram may be lost; the diagram must not mislead without them.
- Verify: no text overflows its shape; no label repeats a word in the title or neighbours; labels at most about five words (inferred); every note referenced by number; the main flow reads correctly without the notes.

## 4. Accessibility

Accessibility is not only screen readers: audiences differ in knowledge, function, product familiarity, screen size and available time. Aim to put everyone on equal footing.

### Relying on Color to Communicate (antipattern, ch. 3)
- Problem: meaning carried by colour alone (new items in colour, red/green with no other cue, "the red boxes"). Facts in the notes: about 4.5 percent of people have colour vision deficiency (1 in 12 men, 1 in 200 women); monitors and projectors differ; greyscale print keeps only lightness, so distinct hues can become one grey and a legend then means nothing. Contrast ratio is the luminance difference between foreground and background; smaller elements need more of it; it applies to arrows, icons and patterns too. The notes give pure red on white as about 4:1; the usual WCAG thresholds (4.5:1 normal text, 3:1 large text and graphics) are inferred from WCAG, not stated in the notes.
- Fixes: (1) add a second cue: pattern (dashed border, hatching), symbol (+ and -), shape, text label; (2) in text, say "the dashed-border boxes", never "the red boxes"; (3) use an accessible palette and check with a simulator (Color Oracle, Coblis, Sim Daltonism, Chromatic Vision Simulator, Viz Palette); (4) vary saturation and lightness so colours differ in luminance; (5) different palettes per medium (white wiki versus black slide); (6) do not trust tool defaults or corporate palettes: the notes' example was a pastel set of equal luminosity that became identical in greyscale and merged under deuteranopia simulation; (7) check cultural meanings; (8) give alt text for public diagrams and ask colour-blind users for feedback.
- Verify: greyscale or deuteranopia view still separates every category; each colour-coded category also has a pattern, shape, symbol or label; contrast passes for text and arrows; prose never names elements by colour alone.
- Agent: in Mermaid or PlantUML also vary shape (cylinder for stores, rounded for services), line style and a stereotype such as `<<queue>>`; give a legend; dark fill with light text or the reverse; add alt text or a description beside any embedded image.

### Include a Legend (pattern, ch. 3)
- Problem: without a key you assume the audience knows the notation, all terms and acronyms and all icons.
- Do: include a legend on most diagrams ("be explicit, not implicit"). To save room: a visible link to a show/hide legend, one legend at the top of a page covering several diagrams, or a partial legend listing only symbols used here. Valuable for UML (people forget its eccentricities) and ArchiMate relationship types.
- Not needed: very simple diagrams, and charts where direct labels on lines or columns beat a legend.
- Verify: every colour, line style, shape, icon and notation symbol appears in a legend or is labelled directly; the legend lists only what is used; a hidden legend has a visible link.
- Agent: a small "Legend" subgraph or a markdown table under the diagram; PlantUML `legend ... end legend`; a "Key:" line for ASCII.

### Appropriate Labels (pattern, ch. 3)
- Problem: too few, too many, wrong or badly placed text.
- Do: label next to what it describes; every component says what it is or does; every relationship has a verb phrase in the direction drawn; detail depth fits the audience and goal. Unlike code, diagrams often need explanation because communicating is their whole job. Fonts no smaller than 12 pt; Atkinson Hyperlegible is a free low-vision-friendly font.
- Verify: every node has a name plus type or description ("[Software System] does X"); every edge reads as "source label target"; nothing overflows; text is legible at display size.
- Agent: `A -->|"submits order (HTTPS)"| B`; technology on nodes; no bare arrows.

## 5. Narrative

Other chapters decide what to show; this one decides how to tell it: a beginning, middle and end.

### The Big Picture Comes First (pattern, ch. 4)
- Problem: opening with the detailed diagram; the audience lacks context and "the big why". The assembled model on the LEGO box, not the loose bricks.
- Do: order from high to low abstraction: business context, benefits, requirements (or a summary linking to an appendix); then context diagram (C4 context, or data flow level 0); container diagram; data flow level 1; level 2 with one diagram per parent process; then detail. Data flow levels: 0 whole system with flows to and from externals; 1 significant processes; 2 and 3 more detail, one diagram per parent. Time spent on context depends on what the audience already knows.
- Verify: the first diagram is the widest in scope; each next one zooms into an element of the previous; no gaps in the story; the why precedes the design.
- Agent: README, design doc and PR structure: purpose in two or three sentences, then overview diagram, then details.

### Match Diagram Flow to Expectations (pattern, ch. 4)
- Problem: reading order never considered; the start sits bottom-right and flows against habit.
- Do (for left-to-right languages; mirror for right-to-left): start at top-left or middle-left, flow top-to-bottom and left-to-right. Requests go left to right, responses back the other way, visually distinguished. Number steps (letters for data stores) or add a "Start here" mark when layout cannot change. Sequence diagrams: participant order across the top so requests run left to right. Structural diagrams: actors at top, systems in the middle, infrastructure such as databases at the bottom (a guideline; do not break other rules for it). Layered architecture: user-facing layer on top. Hexagonal: lay out clockwise from top-left, directing the eye with colour or weight.
- Verify: explain it aloud; the narration sweeps across rather than jumping; entry is top or middle-left; each response runs opposite its request; step numbers rise in reading order.
- Agent: `flowchart LR` for request/response pipelines, `TB` for layers; declare nodes in reading order with the actor first; declare sequence participants in call order; use `autonumber`.

### Clear Relationships (pattern, ch. 4)
- Problem: unclear relationships lose the message: developers build something other than designed, or stakeholders never see the value and withhold budget.
- Do: prefer one-way arrows with a label that describes the relationship in the direction drawn; use a double-headed arrow only when the same thing truly happens both ways (rare). Do not merge request and response of a sequence diagram into one bidirectional arrow. Distinguish relationship types by line pattern and colour in a legend. ArchiMate's many relationship types are valid but need a key; consider C4 for audiences who do not know it.
- Match the form to the relationship type: hierarchical (org charts, taxonomies), sequential (flowcharts, timelines), causal (decision trees, system diagrams), proportional (bar, pie, treemap), spatial (maps, network diagrams).
- Verify: no bidirectional arrow whose directions would carry different labels; each arrow reads "source label target"; arrow styles are in the legend.
- Agent: `A -->|"requests price"| B` and `B -.->|"returns price"| A`; avoid `<-->`.

## 6. Notation

Notation is the system of symbols in a diagram (UML, BPMN, C4, ArchiMate, or your own boxes and lines). Do not over-think it, do not under-think it.

### Using Icons to Convey Meaning (antipattern, ch. 5)
- Problem: cloud-provider icon sets act as a pseudo-notation; icon-heavy diagrams with few labels test the reader's icon knowledge, and icons change with versions. Example from the notes: traffic flowing Internet to a CDN to an unlabelled icon that was actually a different service; without labels the reader cannot tell why or what.
- Do: icons only in addition to information, never instead. Label icons (service name, version or type) and relationships. If you cannot edit an icon-only diagram, add a legend defining each icon. Add text for iconic information ("3.5/5" beside 3.5 stars). Do not lift diagrams straight from vendor documentation. Ask whether icons add clutter.
- Verify (icon-removal test): delete all icons; the message is fully understood from labels. Every icon has a label. Icon version is stated where the provider may change it.
- Agent: with sprites, icon packs or draw.io shapes, always include the text name; prefer plain labelled shapes in text-based diagrams.

### Using UML for UML's Sake (antipattern, ch. 5)
- Problem: assuming UML (or BPMN, or any standard) must always be used. UML has 14 diagram types, half structural and half behavioural; only a few are used regularly and many professionals do not read it. It changes slowly, goes stale quickly, and the author must master it too, which makes maintenance a bottleneck.
- Decide: define goal, audience and their knowledge first. Then (a) standard notation if the audience is fluent and a legend is included; (b) simplified UML (a sequence diagram with descriptive messages instead of method names, which age fast and need codebase knowledge); (c) simpler notation: C4 or labelled boxes and lines, still with a legend. Example: a UML component diagram with lollipop and socket symbols needs a legend and is hard to make; a C4 container diagram with labelled relationships shows nearly the same and is readable by technical and business audiences.
- Be consistent in symbols, colours and fonts within and across diagrams.
- Verify: you can say who reads it and why this notation fits them; a non-developer stakeholder could read it unaided (when that matters); labels avoid volatile details; a legend is present.
- Agent: default to C4-style labelled boxes and plain-language sequence diagrams unless the user asks for UML or the audience clearly speaks it.

### Mixing Behavior and Structure (antipattern, ch. 5)
- Problem: one diagram shows structure (what and where) and behaviour (how, to whom: data flow, state change); no clear message. Single responsibility applied to diagrams: one reason to change, one message.
- Fix: a conceptual structural diagram plus a behavioural diagram (such as data flow). Two diagrams are normal.
- Verify: each diagram is structural or behavioural, not both; the title states the single message ("how X is organised" or "how data moves when Y").

### Going Against Expectations (antipattern, ch. 5)
- Problem: breaking the audience's mental models. Colour: red means danger or stop (luck in parts of Asia); English shade names may not translate. Shapes: triangles suggest action and direction, squares and rectangles suggest stop, order, formality. Technology conventions: deviate only with a ready answer to "why does everyone else follow the convention?". Notation: follow a standard's rules and flag variations; if you change a notation your audience knows, introduce the change, show its benefits and the old one's problems.
- Verify: any deviation from convention (colour meaning, arrow direction, notation semantics, unusual layout) is stated in the legend or intro and justified.

## 7. Composition

### Illegible Diagrams (antipattern, ch. 6)
- Problem: the default portrait page is rarely how a diagram is consumed; on a landscape screen a portrait diagram uses about a third of the display and its text becomes unreadable. Fonts also fail when projected, printed or on small laptops.
- Do: choose canvas size and ratio first; default to landscape (16:9 or 16:10) unless a portrait format is required (landscape can be rotated into print). Rescue for a diagram you cannot edit: an overview, then crop-and-enlarge slides per region, each keeping legend, title and caption, repeating a neighbouring element for context, optionally greying duplicated labels.
- Verify: fits a 16:9 screen without scrolling; smallest text at least 12 pt at display size; no zooming needed.
- Agent (inferred): keep text diagrams narrow (avoid very long LR chains; wrap or split), export images landscape at about 16:9, ASCII under about 80 to 100 columns, split rather than shrink text.

### Style Communicates (pattern, ch. 6)
- Idea: visual style carries a message independent of content. A hand-sketched look says early and open to change; a polished solid-line look says decided and formal. The notes' example: the same proposal was rejected, then approved a week later once redrawn in the decision maker's own diagram style.
- Do: decide what you want to signal (draft or final, formal or collaborative) and style accordingly; question what tool defaults signal; matching the audience's house style can raise acceptance.
- Agent (inferred): label proposals as such (title "Proposed", ADR status), follow the repository's existing diagram tooling and conventions, and never present a rough sketch as the settled design.

### Misleading Composition (antipattern, ch. 6)
- Problem: visuals mislead by accident or intent. Four forms: (1) truncated baseline exaggerates differences (the same data can support opposite messages; use zero, or switch to a table); (2) adjacent charts with different scales imply comparability (share a scale or make the difference explicit); (3) quantity notation such as "x3" suggests exactly that many instances always exist (state minimum, maximum or per-element scaling); (4) size implies capacity (a hugely drawn bus suggests more resources than other elements; keep sizes equal unless size means something, and split the diagram by concern if small boxes make lines hard to read).
- Principle: all models are wrong, some are useful; balance abstraction against accuracy where it matters.
- Verify: bar charts start at 0; neighbouring charts share a scale or state otherwise; size, position, proximity and boldness encode only intended meaning; counts say fixed, minimum or maximum.
- Agent: set y-axes from 0 in matplotlib or other chart code; put comparisons on the same axes; do not enlarge a node (long label, big subgraph) unless it means something; write "1-3 instances (autoscaled)".

### Create a Visual Balance (pattern, ch. 6)
- Problem: a valid diagram feels unsatisfying because elements are unevenly placed. It will not rescue a bad diagram but improves a good one.
- Do: symmetry where possible (approximate is fine, for example at fan-out and fan-in points); otherwise asymmetric balance through position, weight and direction; be consistent within and across diagrams.
- Agent (inferred): low priority with auto layout; when hand-placing (SVG, draw.io XML, ASCII) centre the focus element and mirror fan-outs.

## 8. Pre-delivery checklist

1. Audience and ask stated; notation fits them.
2. One level, one message (structure XOR behaviour); title says which.
3. Names and IDs match the neighbouring diagrams; figure captions and references exist.
4. Colours at most five, each meaning listed; greyscale test passes; no colour-only references in prose.
5. Icon-removal test passes; no undefined acronyms; legend present where needed.
6. Every edge labelled and directional; no bidirectional arrow hiding two different messages.
7. Nesting shallow; edges few; no crossings through components.
8. Reading order: entry top or left; responses opposite requests; numbered steps.
9. Scale honest: zero baselines, shared scales, equal sizes, counts qualified.
10. Landscape, legible at display size, 12 pt minimum; rendered without errors.

## 9. Worked review example (adaptation)

A single Mermaid graph shows a "Platform" box containing "API", "Worker" and "DB", the same graph also shows a "Platform" node linked to "Customer", every node a different colour, retry arrows in red, and unlabelled arrows.

Findings and fixes, using this file:
- Platform and its parts appear as peers: mixing levels. Make a context diagram (Customer, Platform, external payment system) and a container diagram (API, Worker, DB inside a boundary named Platform).
- Colour per node: colour overload. Four categories (person, API, worker, store) in `classDef`, with a legend.
- Red retry arrows: colour-only cue. Make retries dashed and label them "retries (max 3)".
- Unlabelled arrows: label each with a verb phrase.
- Retry paths on a structure diagram: mixing behaviour and structure. Move request/retry behaviour to a sequence diagram.
