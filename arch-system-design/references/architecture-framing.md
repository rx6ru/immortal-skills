# Describing and framing an architecture

How to describe, justify and govern the architecture of a system without reducing it to a style name. Source: Fundamentals of
Software Architecture ch. 1 and preface. Only chapter 1 of that book is in the notes; chapters 2-24 are known from the table
of contents only, so no specifics (ratings, metrics, style tables) are attributed to the book here. For decision records,
characteristic analysis and fitness-function catalogues go to `arch-decisions-and-tradeoffs`.

## Contents
1. The four dimensions
2. Decision, principle, technology choice
3. The two laws and what they demand of you
4. Expectations that apply to an agent doing architecture work
5. Architecture and engineering practice must match
6. Vitality and decay
7. Using this in a review or description task
8. Caveats

## 1. The four dimensions

Saying "it is microservices" describes structure only. A description is complete when it covers:

| Dimension | What to write down | Example question to answer |
|---|---|---|
| Structure | The architecture style(s) in use | Layered? Services? Pipeline? |
| Architecture characteristics ("-ilities") | The success criteria that are not functionality: performance, availability, scalability, and so on | Which two or three matter most here, and with what numbers? |
| Architecture decisions | Rules for how the system is built; constraints teams must follow | Which layers may call the database? |
| Design principles | Guidelines that leave room for judgement | Prefer async messaging between services; REST or gRPC allowed where better |

Choosing between a decision and a principle: if you must constrain absolutely, write a decision (a rule) and provide a
variance process (a formal exception request reviewed by an architecture review board or the chief architect, approved or
denied on justification and trade-offs). If you want to steer while leaving flexibility, write a principle.

## 2. Decision, principle, technology choice

A good architecture decision guides the technology choice; it does not make it. "Use a reactive-based framework" is an
architecture decision (Angular, Elm, React and Vue all satisfy it). "Use React.js" is a technology decision. Test: does the
statement help teams choose the right technology, or choose it for them? The exception: when a characteristic (scalability,
performance, availability) requires a specific technology, naming it is still an architecture decision.

## 3. The two laws

- First Law: everything in software architecture is a trade-off. Corollary: if you think you found something that is not a
  trade-off, you have probably not identified it yet. In practice: every recommendation you write should survive the
  question "what did we give up?" and the answer should be on the page.
- Second Law: why is more important than how. A diagram shows how; only a written rationale shows why this and not the
  alternatives. Capture rationale in an ADR (template in `arch-decisions-and-tradeoffs`).

## 4. Expectations that apply to an agent doing architecture work

The book lists eight expectations of an architect. The ones that change what an agent does in a repository:
1. Make decisions that guide (section 2).
2. Continually analyse the architecture (section 6).
3. Ensure compliance with decisions: check that teams, and your own changes, follow the documented rules. Automated fitness
   functions and tooling are the preferred way (a fitness function is an objective integrity check of one characteristic:
   a metric, a test, a monitor or a chaos experiment; example: a page-load-time test per page run in CI; the more often it runs, the faster the feedback).
4. Diverse exposure: know the options with their pros and cons; breadth over depth when choosing.
5. Domain knowledge: you cannot judge requirements without the business domain; read the domain model before proposing structure.
6. Expect decisions to be challenged (product owners, project managers, developers). Prepare the cost/time justification
   with the decision.

Interpersonal and political expectations (7 and 8) matter for humans; for an agent they translate to: write the rationale so a
reviewer can disagree with a specific point rather than with the whole.

## 5. Architecture and engineering practice must match

Style and engineering practices form a "symbiotic mesh". Microservices assumes automated provisioning, automated testing and
automated deployment; building them with manual operations and thin testing creates large friction. Waterfall plus
microservices is another mismatch; iterative process fits evolutionary architecture. When recommending a style, check
the repository for the practices it presumes (CI, automated deploys, tests) and say so if they are missing.

Responsibility placement: operational concerns such as elasticity are often better delegated to operations/platform than built
defensively into the application architecture; misallocated responsibility is accidental complexity. (The book's contrast: 1990s-2000s
architectures were defensive about operations they could not control; microservices-era architects hand more to operations.) Check
before designing a custom mechanism whether the platform already provides the capability.

Unknown unknowns: you cannot design for what you cannot foresee, so big up-front design fails; expect to iterate and
keep the design cheap to change. Migrations from a monolith are supported by the strangler pattern and feature toggles
(see `arch-decomposition`).

## 6. Vitality and decay

- Architectures decay structurally when code and design changes erode required characteristics (performance, availability,
  scalability). Re-evaluate an architecture that is three or more years old against current business and technology.
- All architectures are products of their context. Example from the book: a service-per-machine-and-database design was
  unaffordable in 2002 because of licence costs; open source plus DevOps changed that. Re-check inherited assumptions
  ("we can't afford X", "Y is expensive") before reusing an old design.
- Look at the delivery environment too: if tests take weeks and releases take months, the overall system is not agile whatever the diagram says.

## 7. Using this in a review or description task

Description task ("document the architecture"):
1. Structure: name styles and show the main boxes.
2. Characteristics: list the top few, with numbers if known; mark which are explicit in requirements and which you inferred.
3. Decisions: list the rules you can see enforced in the code (for example, "only the service layer touches the database") and how
   they are enforced or not.
4. Principles: list the guidelines teams follow.
5. Rationale: for each significant choice, one line of why, and flag where the repository does not say (do not invent).

Review task: check each of the four dimensions, then ask the First-Law question about each proposal, then check whether a
fitness function exists for each stated characteristic.

## 8. Caveats

- Much of chapter 1 is framing and opinion rather than procedure. Claims about microservices cost/benefit and DevOps are as of about 2020.
- The excerpt does not include the book's chapters on modularity, characteristic identification, styles or risk analysis. If a task
  needs those, use `arch-decisions-and-tradeoffs` and `arch-decomposition`, not this file.
