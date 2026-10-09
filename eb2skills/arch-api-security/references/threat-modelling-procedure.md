# Threat-modelling procedure for an API

Contents: why and when; the six steps; drawing the data flow diagram; enumerating threats per element; scoring with DREAD; a written rubric you can adopt; worked example; outputs to hand the user; validation and re-runs; variants.

Source: Mastering API Architecture ch. 6 (threat modelling), with adaptation notes marked "Adaptation".

## Why and when

- Only identified threats can be mitigated. A threat model sets priorities, so effort goes to the likely and severe threats and not to "security theatre" (a steel door with the key under the mat).
- Run it at project start and again when the architecture changes (new consumer type, new third party, new endpoint family, a service split, a move to cloud). Treat it as part of the lifecycle, not a one-off audit.
- You do not need to be a security specialist. The people who know the structure best are the architects and developers; involve specialists to extend the list, not to start it. The stance to take is "what would an attacker do here?".
- Traffic inside a service mesh can be protected with mTLS, but once external parties (mobile apps, third-party systems) call the API, the model must cover threats that the mesh does not reach.
- Method used by the book: STRIDE (Microsoft, 1999) over data flow diagrams. Alternatives named: PASTA and Trike. Pick STRIDE unless the user's organisation already standardises on another.

## The six steps

| # | Step | What you produce | Guard against |
|---|---|---|---|
| 1 | Identify objectives | A few plain-language business and security objectives (the book gives three examples) | Objectives taken only from the team or InfoSec; source them across the organisation |
| 2 | Gather information | High-level design plus input from an expert on each component (client, gateway, database, each service) | Hidden assumptions ("surely the gateway validates that") |
| 3 | Decompose | One or more data flow diagrams with trust boundaries | One huge diagram nobody can read; use several |
| 4 | Identify threats | STRIDE applied to every process and every data flow | Tangents unrelated to the objectives |
| 5 | Evaluate risk | DREAD score per threat, ranked, each with an assigned mitigation | Subjective scores without a rubric |
| 6 | Validate | Evidence that mitigations work and objectives are met; decision on whether another pass is needed | Treating the model as finished; it is recursive and periodic |

Example objectives from the book: avoid unauthorised access; prevent PII leakage to conform to GDPR; provide 99.9% availability for contractual obligations (the last implies a focus on denial of service). The case study objective: prepare the Attendee API for third-party consumers by mitigating the OWASP API Security Top 10.

## Step 3: the data flow diagram

DFDs show dynamic movement of data (a C4 model shows static structure; use both if the repository has one). Five element types:

| Element | Meaning | Example |
|---|---|---|
| External entity | Outside your system and control | Mobile app, third-party CFP system |
| Process | Runs in your domain | API gateway, Attendee service |
| Data store | Where data rests | Attendee database |
| Data flow | A connection that carries data between the above | Mobile app to gateway over HTTPS |
| Trust boundary | A line where the level of trust changes | The internet boundary between mobile app and gateway |

Draw a trust boundary wherever the caller is not under your control, wherever the network is not yours, and wherever a component runs with different privilege. A data flow that crosses a boundary deserves the most scrutiny.

Tools named: Microsoft Threat Modeling Tool (it generated 27 STRIDE threats for the book's Attendee API) and OWASP Threat Dragon.

Adaptation for an agent working in a repository: when no diagram exists, derive a first draft from the code and configuration. Entry points come from route definitions, OpenAPI files, gateway or ingress config, queue consumers and scheduled jobs. Data stores come from connection strings, ORM models and cache clients. Outbound calls come from HTTP clients and SDK usage. Write the result as a Mermaid or ASCII diagram, mark each flow's protocol, and ask the user to confirm what you inferred, because the code does not show deployment-time controls such as a WAF in front.

## Step 4: STRIDE per element

Apply the six categories to each process and each data flow (data stores and external entities get the subset that makes sense: stores mainly T, I, D; external entities mainly S and R). The category-by-category API mitigations are in `stride-and-owasp-api.md`. Stay within the objectives; a threat that threatens none of them can be logged and parked.

Practical method: build a table with one row per element or flow and one column per STRIDE letter, and fill each cell with either a concrete threat sentence or "not applicable because ...". Empty cells are the thing to avoid; they hide unexamined assumptions.

## Step 5: DREAD

Score each threat 1 to 10 on five factors, then average:

| Factor | Question |
|---|---|
| Damage | How bad is the damage if exploited? |
| Reproducibility | How reliably can the attack be repeated? |
| Exploitability | How much effort and skill does it take? |
| Affected users | How many users are hit? |
| Discoverability | How easy is the weakness to find? |

Risk = (D + R + E + A + Disc) / 5.

Worked example from the book: denial of service against an API gateway with no rate limiting. Damage 8, Reproducibility 8, Exploitability 5 (the attacker has to pass authentication and authorisation, so needs a known client), Affected users 10, Discoverability 10. Risk = (8+8+5+10+10)/5 = 8.2, the highest in the case study. Mitigation: rate limiting and load shedding at the gateway (see `rate-limiting.md`).

DREAD scores are subjective. The book's remedy is to write down what each value means per factor so that scores are comparable between people and between runs. Its example for "affected users": all users = 10; all internal users or all external users = 7; half of a group = 3; none = 0. Do the same for the other four factors before scoring, and put the rubric next to the scores.

Variants: DREAD-D drops Discoverability, on the argument that security through obscurity is not protection. CVSS (used by NIST for published vulnerabilities such as Log4J) rates severity of a known flaw; use it when triaging a dependency vulnerability, not for design-time threats.

Note: the book says Microsoft no longer uses DREAD but it remains widely used. State the subjectivity when presenting scores; the ranking is the useful output, not the decimal.

## Rubric to adopt (adaptation)

Before scoring, agree with the user what each level means for each of the five factors, and keep the same rubric across runs. Only the "affected users" levels below come from the book: 10 = all users; 7 = all internal users or all external users; 3 = half of a group; 0 = none. For the other four factors, write the same kind of anchored levels at 10, 7, 3 and 0 (for example, Damage 10 = regulated data of all users exposed; Exploitability 3 = needs a privileged insider; these two examples are illustrative, not from the book) and record them beside the scores.

## Output format to give the user

1. Objectives (step 1), one line each.
2. The diagram, with trust boundaries.
3. Threat table: ID, element, STRIDE letter, threat sentence, OWASP API category, DREAD score with the five factor values, mitigation, owner, status (open, mitigated, accepted).
4. The rubric used.
5. Assumptions you could not verify and who can confirm them.
6. Re-run triggers.

## Step 6: validate

- For each mitigation, name the test or observation that shows it works (see Verify in `SKILL.md` and `security-review-checklist.md`). A mitigation without a check is a claim.
- Ask: are all objectives covered by at least one mitigation? Did the new mitigation create a new flow or element that needs its own pass (for example adding a token service adds a process and a boundary)?
- Re-run when functionality is added, when the architecture changes, and periodically because the outside threat landscape changes. The book notes it is time-consuming but gets easier with practice.

## Gateway versus distributed systems

A gateway gives high-level mitigation for many threats at once (TLS, validation, rate limiting, header allow-listing, logging). As the system becomes more distributed, extend the model to each service implementation and to inter-service communication; the gateway alone is not the whole defence. See `edge-and-zero-trust.md`.
