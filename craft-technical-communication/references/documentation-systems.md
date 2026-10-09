# Documentation systems

Where documentation lives, in what format, who owns it, how it stays current, and how tools are chosen. Sources: Communication Patterns (Read 2023) ch. 10, 11, 15; Pragmatic Programmer ch. 8. Items marked (inferred) are readings added in the notes; "Agent" lines are adaptation.

## Contents

1. Principles at a glance
2. Products over projects
3. Perspective-driven documentation
4. Docs as code: single source, executable documents
5. Formats and shared load
6. Just-in-time and just-long-enough
7. Feedback built into the documentation workflow
8. Team conventions: one voice, librarian
9. Choosing and governing tools
10. Layout for a repository (adaptation)
11. Checks

## 1. Principles at a glance

| Principle | One line | Source |
|---|---|---|
| Products over projects | File knowledge by product; projects point at it | Comm. Patterns ch. 10 |
| Abstractions over text | Pick table, list or diagram to fit the content | ch. 10 |
| Perspectives | Collections of artefacts for one stakeholder's concerns, built from single sources | ch. 10 |
| DRY | One authoritative representation per fact | Pragmatic Programmer ch. 8, Comm. Patterns ch. 10 |
| English is a programming language | Apply DRY, orthogonality, model/view, automation, version control to prose | Pragmatic Programmer ch. 8 |
| Share the load | Open formats, owners with understudies, templates | Comm. Patterns ch. 11 |
| Just in time | Document what is needed now, retire what is not | Comm. Patterns ch. 11 |
| Feedback early | Share drafts, list assumptions with IDs | Comm. Patterns ch. 11 |

## 2. Products over projects (ch. 10)

- Problem: knowledge organised per project is transitory. After the project ends the docs are hard to find, forgotten or lost; later teams do not know prior docs exist and break things without knowing why decisions were made, what the original requirements were or how CI/CD works.
- Do: organise by product; projects reference the artefacts (one artefact can be referenced by several projects). Project-specific docs are still stored with the product.
- Benefits: discoverability, long-term focus, reuse across concurrent and sequential projects, consistency (templates and standards emerge), visibility of the impact of change, customer focus, continuous improvement.
- Methods: a central documentation portal organised by product that links to knowledge stored elsewhere (and links back); tags rather than folders (a folder forces one location, tags allow product, project and artefact type at once); if only folders exist, put product at the highest level, not under a department; key-value metadata (product, author, project, type, tags) rather than tag soup. Align with organisation-wide product IDs and terminology. For a cross-product project use tags or a project dashboard page linking into each product.
- Verify: from a product name all its docs are findable in one place; each artefact has product and type metadata; no document lives only inside a project folder.
- Agent: put design docs, ADRs and diagrams in a docs tree organised by component or product (for example `docs/architecture/`, `docs/adr/`), with front matter metadata, rather than in per-ticket or per-PR files.

## 3. Perspective-driven documentation (ch. 10)

- Definition: a perspective is a collection of one or more artefacts (pages, diagrams, tables) that addresses the concerns of one stakeholder (developer, architect, product owner, project manager, security, operations, customer). Documentation exists so stakeholders can find what they need when they need it; needs vary hugely. Long Word-style documents hinder finding and maintaining; wikis are better; perspectives better still.
- Defining one: the stakeholder and the author collaborate, since the stakeholder knows the concerns and not which artefacts address them. Refine into templates, checklists or forms (they act like an anticorruption layer between stakeholder and artefact author).
- DRY perspectives: every piece of knowledge has a single authoritative representation. Embed one artefact in many perspectives and updates appear everywhere; linking is the less accessible fallback. Links may be brittle (break on rename or move) or durable; check your tool. When you want a frozen or altered copy (a specific release, a version of a standard), make an explicit copy and name it to show why.
- Fractal perspectives: a perspective can embed other perspectives to any depth, and one artefact can sit in several parents as the same instance, not a copy.
- Layering diagrams: keep one master diagram with layers (security protocols on one, sync versus async on another) and show different layers in different artefacts. Serves DRY and single responsibility: a security change touches only security layers. In text-diagram terms (adaptation), split sources per concern and include shared definitions.
- Related frameworks named in the notes: TOGAF viewpoints, SABSA and Zachman (rigid matrices), Diataxis (tutorials, how-to guides, explanation, reference), 4+1 views, Rozanski and Woods perspectives. The author chose "perspective" over "view".
- Tool features to look for: tags and metadata, embedding or durable references, flat structure with tags, templates and checklists, layers, backlinks.
- Verify: no artefact is copy-pasted between docs; each perspective names its stakeholder and concern; intentional copies are named with the reason; one diagram source per concern or layered.
- Agent: write each fact once and link to it elsewhere (a README links to the architecture doc and the ADR); organise by audience; keep diagram source in one file and include it.

## 4. Docs as code (Pragmatic Programmer ch. 8, "It's All Writing")

- Treat English as just another programming language: apply DRY, orthogonality, model/view separation, automation, version control, and build the docs with the product.
- Build documentation in, do not bolt it on. Internal (comments, design and test documents) and external (user manuals). All documentation mirrors the code; if they disagree, the code is what matters.
- Executable documents. Problem shape: a specification lists table columns, separate SQL creates the table, a record type holds a row; the same knowledge exists three times. Technique: choose one authoritative source (the spec, a schema tool or a third source), export the other forms as generated views, then change only the model. Keep the source in plain text with markup so a script can extract from it. API docs generated from source are the same pattern, code being the model.
- Proprietary or binary documents: write macros to export tagged sections, or make the document subordinate to another authoritative source and import it every time it is produced, not once.
- Technical writers should work under the same principles, not receive material "over the wall".
- Print it or weave it: any documentation is a snapshot, so publish online with hyperlinks, put a date or version on every page so readers can judge currency, and keep presentation independent of content (one semantic source rendered to many outputs, a heading becoming a chapter in the report and a slide title in the deck). Use named styles or a markup language, keep the source under version control, and build it in the nightly build.
- Web sites generated from the repository and published automatically are views of one source. "Misleading information is worse than no information at all." Publish build and test results automatically.
- Do not hand-maintain what tools know: export lists, revision history, file lists, file names.
- Challenge questions: did you write an explanatory comment for the code you just wrote; if not, why? Reluctance to document a design because it is unclear in your head is a symptom of programming by coincidence.
- Verify: for each fact in a document, you can point to the single source it comes from or generates from; docs are in version control and built by the automated build; each published page carries a date or version; no hand-maintained headers that tools could produce (grep for version strings repeated in prose); names that behave differently from what they say (a `get*` that mutates) are fixed.
- Brooks ch. 15 agrees from the other side: merge the human-readable document into the source so one change touches both, and write the overview before the code.

## 5. Formats and shared load (ch. 11)

- Documentation must never depend on one person; creation and maintenance are shared.
- Nonproprietary formats: more people can create, edit and view; fewer licence worries; higher editor accessibility (free, browser-based); interoperability; less lock-in. Examples: Markdown, AsciiDoc, Git, ODF, draw.io, PNG, PDF, YAML, HTML. Trade-off: less vendor support for open source; weigh when selecting, mainly important for anything durable.
- The notation matters for authors too. UML or ArchiMate shrinks the pool who can maintain diagrams (training for every newcomer); C4, flow diagrams and simplified sequence diagrams widen it. Markdown or AsciiDoc beat formats requiring HTML and CSS.
- Email is not a knowledge repository (only sender and recipient can see it, poor search, deleted when people leave); move knowledge to a searchable, secure, accessible place.
- Collaboration: pair or ensemble-style work with a rotating driver; coaching; automatic notifications when documentation is created or updated; notifications of changes elsewhere (a requirement change should prompt an architecture check).
- Roles: assign documentation roles by documentation type or creator/reviewer pairs; avoid bottlenecks; have an understudy per role; never assume a handover period.
- Techniques: lunch-and-learn sessions that produce durable artefacts, templates (a flying start when moving between products), a documentation sprint or time block.
- Verify: docs in plain-text or open formats in version control; each doc type has an owner and an understudy; templates exist for repeated artefacts; a notification fires on change.
- Agent: write docs as Markdown, Mermaid or PlantUML text, not binary files; capture decisions in the repository, not only in chat or email threads.

## 6. Just-in-time and just-long-enough (ch. 11)

- Problem: architecture and docs produced ahead of need are predictions; when things change everything built on top must change too. Incorrect docs, or docs costing more to keep than they deliver, have negative net value.
- Do: decide and document only what you know you need now; order and prioritise the decisions and artefacts; interleave research or proofs of concept for fresher information; put architecture tasks on the board; break milestones into decisions and artefact-creation tasks so progress is still trackable.
- Why defer decisions: flexibility, learning, less risk from incomplete information, more diverse input, less complexity (refactoring to add is easier than rewriting to remove), and you may avoid the decision entirely. YAGNI is not an excuse to skip best practice.
- Just-long-enough: retire documents that served their purpose and make it obvious they are out of date.
- Mitigations: people who want information now are handed an artefact clearly marked draft or pending; people who want predictions can be given milestones framed as decisions and tasks (the notes cite one data source that teams estimating least produce most, a single-source claim); keep a parking-lot page for ideas relevant later and check it when producing later artefacts.
- Verify (inferred): each document or decision has a stated trigger (who needs it, for what, now); speculative sections are absent or marked draft; superseded documents are marked retired; a parking-lot exists.
- Agent: do not invent a future-state architecture for hypothetical needs. Record decisions needed now and list the rest as "not yet decided; revisit when X".

## 7. Feedback built into the workflow (ch. 11)

- Problem: heavy investment before any feedback wastes money; one wrong early assumption can steer everything (butterfly effect); the sunk cost fallacy makes you resist change as work accumulates.
- Do: small iterative increments; feedback on parts and on the whole; get sign-off on assumptions as soon as possible and, if you cannot, state that clearly in the docs; give every assumption an ID so you know what changes if it proves false; ask technical and business colleagues often, especially when new; never let rank block wisdom, since juniors know things you do not; play back your understanding of stakeholder needs.
- How: just show your work; ask juniors explicitly; fold into pull requests and checkpoints; ADRs with a consultation section and a deadline for input; existing meetings and reviews; an RFC process.
- Example workflow from the notes: docs tasks split into small chunks; review requested through a dedicated channel with quick turnaround; checkpoints at (1) the pull request for the artefact (peers, plus developers and architects if technical), (2) preview of the docs site (stakeholders such as the product owner), (3) after publishing (customers, support, colleagues).
- Verify: each assumption has an ID, status (signed off or unconfirmed) and owner; drafts are labelled draft with a feedback deadline; feedback is requested before the artefact is deemed done and before development begins on it.

## 8. Team conventions (Pragmatic Programmer ch. 8)

- Teams speak with one voice externally: documents that all look different and use different terminology are a warning sign; crisp, accurate, consistent documentation is a sign of a good team. Internally, lively debate is wanted.
- Brand the project: a memorable name and a quick logo on memos and reports gives identity (30 minutes of effort per the notes).
- DRY across people: a project librarian coordinating documentation and code repositories, or focal points per functional aspect (dates, database schema), so people know whom to ask and duplication is spotted early.
- Gently exceed expectations: the aim of communication with users is a common understanding of the process and deliverable, including expectations not yet spoken; tracer bullets and prototypes make this visible. Small, cheap, isolated extras (quick-reference guide, tooltips) can delight, but do not break the system adding them.

## 9. Choosing and governing tools (ch. 15)

### Selection (pattern)
- Start from requirements with MoSCoW (must, should, could, won't), plus initial and ongoing cost; use architecture characteristics to prioritise requirements; record the choice as an ADR (context, evaluation criteria, options scored, extra trade-offs); consider overlap with existing tools; apply YAGNI to features. Tool style signals meaning (a shared whiteboard feels transitory; a heavyweight modelling tool may put people off).
- Example in the notes: a custom in-house documentation system caused team conflict (maintainers favoured their own needs, builds broke). The problem was cultural, not technical. The team defined characteristics for the documentation system, used them as ADR criteria for off-the-shelf options and chose open source anyone may contribute to. "Cultural fit" joined the characteristics used for procurement.
- Attaching a file to email is an antipattern (a copy per recipient); share a link with access rights.

### Tool proliferation (antipattern)
- Data proliferation: each tool holds unique, shared and duplicated data; separate authentication per tool leads to weak passwords and accounts surviving role changes; copies drift; compliance questions (transfer, encryption, access control, location). Shadow IT: the notes cite a 2021 survey of organisations with 500 to 2,000 staff using about 800 cloud apps a month, 97 percent of them shadow IT (one source).
- Efficiency: duplicate tools, silos, cost creep per user per month, lost bulk discounts, learning curve per tool, unclear ownership.

### Tool governance (pattern), in order
1. Audit: what apps, for what, how many users, licences, initial and ongoing cost, ROI, and why each is used; record renewal and end-of-support dates.
2. Application portfolio: app, owner, users, licences, licence uptake with date; add dependencies and data flows for impact analysis and security.
3. Evaluate against policy (security, compliance, encryption), business objectives, pros and cons, requirements.
4. Consolidate: flag tools that duplicate features without reason, fail needs, violate policy or law, have negative ROI or excess licences.
5. Implement in phases, strangler-fig style, with early adopters.
6. Ongoing governance: lifecycle processes, training, a request process for new tools, periodic audits for shadow IT.
- Communicate with a technology radar (centre means use, edge means hold or retired; provide a searchable text version), an application catalogue, a wiki page for policies.
- Exceptions: allow documented exceptions; repeated exceptions signal that a policy or tool needs review. Too restrictive breeds shadow IT; automate checks, self-serve the rest. Give ownership to a role ("Owner of App X") so reassignment is trivial.
- Verify: portfolio has owner, purpose, licences, cost, renewal dates, dependencies; an ADR exists for each selection; exceptions are logged.
- Tool names in the notes are dated; the process (audit, evaluate, consolidate, record ownership and rationale) is the lasting part.

## 10. Layout for a repository (adaptation)

```text
README.md                 purpose, quick start, links to docs (links, not copies)
docs/
  architecture/           context and container diagrams (text sources), overview
  adr/                    decision records (template: arch-decisions-and-tradeoffs)
  how-to/                 task guides
  reference/              generated API and config references (do not edit by hand)
  glossary.md             terms and acronyms
```

Each page has front matter or a header naming product/component, type and last-reviewed date. This mirrors Diataxis-style audience separation and product-over-project filing; adapt names to the project's existing layout before inventing one.

## 11. Checks

1. Can every fact be traced to one source? Generated views are marked as generated.
2. Is each doc findable from the product page, with type and date?
3. Are formats plain text in version control, and does CI build or lint them?
4. Does each doc type have an owner and an understudy; is there a template?
5. Are stale or superseded docs marked retired?
6. Are open assumptions listed with IDs and owners?
