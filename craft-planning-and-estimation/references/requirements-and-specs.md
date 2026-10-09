# Requirements and specifications

Contents: 1 What to establish before building; 2 Dig, do not gather; 3 Requirement, policy, implementation; 4 Use cases; 5 Seeing further: abstraction and glossary; 6 Requirements creep; 7 How much specification; 8 Test the spec before code; 9 Impossible problems and false constraints; 10 Reluctance to start; 11 Quality and expectations; 12 Documentation by reader need; 13 Procedure for a vague request; 14 Warning signs and verification

Sources: MMM ch. 13, 15, 16, 17, 19; PP ch. 1 (Tips 3, 7), ch. 2 (Tips 15 to 17), ch. 7 (Tips 51 to 58), ch. 8 section 45 (Tip 69). Sibling: `craft-testing` for test design; `craft-technical-communication` for document writing craft.

## 1. What to establish before building

Brooks (ch. 16): the hardest single part of building a software system is deciding precisely what to build. No other part cripples the system as much if done wrong or is harder to fix later. The most important function builders perform for clients is iterative extraction and refinement of requirements.

- Clients do not know what they want; they usually do not know which questions must be answered. "Make it work like the old manual system" is never exactly what they want. Software acts and moves, so its dynamics are hard to imagine in advance.
- Stronger claim: it is impossible for clients, even working with engineers, to specify completely, precisely and correctly a modern product before building and trying some versions.
- Planning rule: allow for extensive client-designer iteration as part of system definition. A specify, bid, build, install procurement rests on a false assumption.
- Vyssotsky (ch. 13): many, many failures concern exactly those aspects that were never quite specified.
- Passing tests only shows conformance to the spec; much of the essence of building a program is in fact debugging the specification (ch. 16, program verification). Separately confirm the spec with the user.

## 2. Dig, do not gather (PP Tips 51, 52)

Requirements are buried under assumptions, misconceptions and politics; they do not lie on the ground to be picked up.

- Find the reason behind what users do, not only how they do it now. Solve the business problem, not just the stated requirement. Document the reasons; the team uses them in daily decisions.
- Work with a user to think like a user: sit in for a day or a week while they do the job (help desk, warehouse). Do not get in the way. This is also the time to start building rapport and learning their expectations.
- Requirements are not architecture, design or user interface. Requirements are need.
- Show a user a prototype or walk through a scenario and listen for "except when ...".

## 3. Requirement, policy, implementation

- "Only an employee's supervisors and the personnel department may view that record" embeds a business policy in an absolute statement. Policies change regularly.
- Write the requirement generally ("only authorised users may access an employee record") and record the policy separately as an example of what must be supported, linked to it. Eventually policy becomes metadata.
- Design consequence: the specific wording tempts hard-coded checks at every access; the general wording leads to an access-control mechanism whose data changes when policy changes.
- A UI widget request ("we need a list box") may be an example of an ability the users need ("choose a loan term"). Ask what ability they need.
- PP exercise 42 (answers inferred): response time under 500 ms is a requirement (needs context: which operation, what load); gray dialog backgrounds is a UI detail (restate as consistent look and configurable styling); front-end processes plus back-end server is architecture (restate the underlying need, such as scalability); beep and reject non-numeric characters is a UI detail (restate as numeric fields accept only valid input and users are told when rejected); code and data must fit in 256 kB is a genuine constraint if the hardware demands it.

## 4. Use cases (PP ch. 7)

Describe a use of the system abstractly, not in UI terms. Cockburn's goal-driven template acts as an aide-memoire and as an agenda for user meetings.

| Block | Contents |
|---|---|
| A. Characteristic information | Goal in context, scope, level, preconditions, success end condition, failed end condition, primary actor, trigger |
| B. Main success scenario | Numbered steps |
| C. Extensions | Alternate branches by step number (for example "3a out of stock: renegotiate") |
| D. Variations | Phone, fax, web order; cash, cheque, card |
| E. Related information | Priority, performance target, frequency, superordinate and subordinate use cases, channels, secondary actors |
| F. Schedule | Release |
| G. Open issues | For example partial orders; stolen card |

Real use cases are textual, hierarchical and cross-linked. Reducing them to stick-figure diagrams loses the content. Do not be a slave to any notation; use what communicates best to the audience.

Sidebar (Brian Eno): a requirement may exist to leverage an existing skill set. Provide a transition through familiar metaphors; successful tools adapt to the hands that use them.

## 5. Seeing further: abstraction and glossary

- Tip 53: abstractions live longer than details. The Y2K example: not programmers saving bytes but analysts failing to see beyond current business practice, plus date logic scattered (a DRY violation). A requirement that says the system uses a DATE abstraction and implements date services (formatting, storage, math) consistently would have contained the problem. "Seeing further" does not mean predicting the future.
- Tip 54: keep one project glossary of every specific term ("client" and "customer" may differ). It is hard to succeed when users and developers use different names for one thing or one name for different things. Publish it somewhere linked and living (PP says hypertext; today a repo document or wiki).
- Tip 17: program close to the problem domain. A mini-language can capture domain rules; give users domain-level errors. Costs: a language others must learn, tools and debugging. Justify it when domain rules change often or non-programmers must configure. PP recommends adopting the more readable language up front because applications outlive their expected life.

## 6. Requirements creep

Scope creep is the boiled-frog syndrome (PP). Few projects track requirements actively, so they cannot report who requested a feature, who approved it, or how many were approved.

- Record, for each added requirement: requester, approver, date, schedule impact. Show sponsors each feature's schedule impact.
- When the project is a year late, an accurate record of how and when requirements grew helps. Tracking reveals that "just one more feature" is the fifteenth this month.
- A "chief water tester" (PP ch. 8, the team version of the boiled-frog tip) watches for scope increase, shrinking time scales, extra features and new environments. Changes need not be rejected, only noticed.
- Brooks (ch. 11): not all changes can be incorporated; set a change threshold that rises as development proceeds, or no product appears. Quantise change into numbered versions with a freeze date after which changes go to the next version.

More in `scope-and-second-system.md`.

## 7. How much specification

PP section 39, the specification trap, with Brooks's counterweight.

Why over-detailed specs fail (PP):
1. A spec cannot capture every nuance. Users rarely know exactly what they need; they may sign a 200-page document and then flood you with changes once they see the running system.
2. Natural language is limited. Tip 57: some things are better done than described (try writing how to tie a shoelace).
3. The straitjacket effect: a design that leaves no room for interpretation robs coding of skill, and opportunities (a cheaper way to the same result) appear only while coding. Do not just hack in changes, but raise them with the specifier.

Treat requirements gathering, design and implementation as facets of one process. Do not be against specs: very detailed ones are sometimes required (contract, environment, life-critical systems), and for interfaces and libraries used by others, make sure the calls are well specified. There is a point of diminishing or negative returns, and specs layered on specs without implementation or prototyping can specify something that cannot be built. The specification spiral is a security blanket for developers afraid of writing code; break out with a tracer bullet or prototype.

Brooks's counterweight (ch. 6, 13): the external spec must be precise, complete and written by few hands, and tested before code. The two are reconciled by what is specified: the external interface in precise detail, the internals left to implementers.

Rule of thumb for deciding (synthesis):
| Part | Spec depth |
|---|---|
| Interface used by other people, teams or agents; public library calls | Precise and complete, with examples and conformance tests |
| Safety-critical or contractual behaviour | Detailed, reviewed independently |
| Application-level behaviour that users will react to | Need-level statement plus a running slice they can try |
| Internals | Left to the implementer, constrained by budgets (size, time) |

## 8. Test the spec before code (ch. 13)

- Hand the spec to an outside group to scrutinise for completeness and clarity. Developers cannot do it: they will not say they do not understand it; they will invent their way through gaps and obscurities.
- Spec prose forces many small decisions; gaps in formal definitions show conspicuously.
- Agent version (adaptation): a separate reviewer reads only the spec and lists ambiguities and missing cases before implementation starts.
- Draft the user documentation before building: it embodies basic planning decisions (see section 12).

## 9. Impossible problems and false constraints (PP Tip 55)

"Think outside the box" is inaccurate: find the box, which may be larger than you think. When a problem seems impossible:
1. List all possible avenues; dismiss nothing.
2. For each, explain why it cannot be taken. Can you prove it?
3. Categorise and prioritise constraints, most restrictive first (cut the longest pieces first).

Ask: is there an easier way? Am I solving the right problem or a peripheral technicality? Why is this a problem? What makes it hard? Does it have to be done this way? Does it have to be done at all? Tag each constraint absolute, assumed or negotiable, with the person who can confirm it. Reinterpreting requirements can make a set of problems vanish (Gordian knot).

Related (ch. 17): much conceptual complexity comes from arbitrary complexity of the application, and most complexities in systems work can be symptoms of organisational malfunction (Sødahl). Before encoding a complicated business rule, ask whether it is a symptom of a process problem to fix at the source.

## 10. Reluctance to start (PP Tip 56)

Heed a nagging doubt, but test it. Prototype the part that feels difficult. If you become bored, the reluctance was probably procrastination: abandon the prototype and start real development. If you have a revelation that a premise was wrong, abandon the prototype and start the project properly with the fix. Remember why you are prototyping, so you are not weeks into "serious development" on what was meant to be a prototype.

## 11. Quality and expectations

- Tip 7: scope and quality are part of the requirements. Ask users how good it needs to be: pacemakers and widely distributed libraries differ from a new product with marketing promises. Both ignoring the user's constraints to polish "one more time", and promising impossible timescales while cutting basic engineering corners, are unprofessional. Great software today is often preferable to perfect software tomorrow. Know when to stop.
- Tip 69: success is how well the project meets its users' expectations, not only the specification. Communicate expectations throughout (tracer bullets and prototypes are the main means), aim for a common understanding including unverbalised expectations, then gently exceed them with cheap, superficial, low-risk extras found by listening (examples: tooltips, shortcuts, a quick-reference guide, automated install). Do not break the system adding them. The tension with "good enough" is resolved by size: small, user-chosen extras, never speculative gold plating.
- Tip 3 (communication of bad news): see `milestones-and-status.md`.

## 12. Documentation by reader need (MMM ch. 15)

Draft the user overview before the program is written; it embodies planning decisions. Concise, often 3 to 4 pages.

To use a program, nine items: purpose; environment; domain and range (valid inputs, legitimate outputs); functions realised and algorithms used; input-output formats, precise and complete; operating instructions including normal and abnormal ending; options and how specified; running time for a stated size and configuration; accuracy and checking.

To believe a program: ship test cases. Run thorough cases after modification in three parts of the input domain: mainline cases with common data; barely legitimate cases probing the edge of valid input (largest, smallest, valid exceptions); barely illegitimate cases probing from the other side so that invalid input produces proper diagnostics.

To modify a program: a well-commented listing plus an overview of internals: a structure graph (of phases or subprograms), algorithm descriptions or references, layout of all files, pass structure, and a discussion of contemplated modifications with hooks, exits, author's ideas, and hidden pitfalls. Say why, not only how (ch. 18, 15.14).

Keep documentation in the source where possible so that one change touches both (ch. 15; PP Tip 68): let names, declarations and structure carry meaning, use format to show nesting, and add paragraph comments for overview. PP Tip 67: treat English as a programming language (single source, generate views, version control, build with the product). Comments explain why (purpose, trade-offs, rejected alternatives), not how.

## 13. Procedure for a vague request (adaptation)

1. Restate the request as a need in one or two sentences. Separate policy and widget details into a side list.
2. Identify the three questions whose answers change the design (inputs and outputs, who else depends on this, what "good enough" means). Ask only those.
3. Check for an existing solution (`tools-and-build-vs-buy.md`).
4. Propose a mainline-only skeleton or prototype and ask what is wrong with it (ch. 16: a prototype simulates the important interfaces and performs the main functions, without handling exceptions or invalid input).
5. Write down the acceptance checks that will prove it, as executable tests where possible.
6. Record assumptions and the glossary terms used. Keep scope changes in a log.

## 14. Warning signs and verification

Warning signs:
- Requirements treated as fixed and complete before anything has been shown to a user.
- Requirements that name widgets, roles, numbers or technologies rather than needs.
- Spec pages growing faster than working code for weeks; sign-off meetings with no running software; implementers forbidden to suggest changes; spec text that dictates algorithms, field names and screen layouts.
- A project whose philosophy is that the diagram is the application and the rest is mechanical (PP Tip 59 warning).
- Different words for the same thing across documents.

Verification:
- For each requirement: need or solution? Does it embed policy that should be metadata? Can the reason be stated?
- Could a developer choose between two reasonable implementations without violating the spec?
- Is there an executable example (test, prototype, tracer slice) for each major requirement?
- Are interface and library specs detailed even if application-level specs are lean?
- Does every noun have a glossary entry?
- Is each requirement traced to requester, approver, date and schedule impact?
