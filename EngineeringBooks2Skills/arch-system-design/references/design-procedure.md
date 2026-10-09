# Design procedure

The end-to-end procedure for turning a problem statement into a design you can defend. Source:
System Design Interview ch. 3 (a four-step framework written for interviews, but its notes say to treat it as a general design
procedure), combined with the iteration style of SRE Workbook ch. 12 (see `nalsd-method.md`).

## Contents
1. The four steps and how to size them
2. Step 1: clarify scope (question checklist)
3. Step 2: high-level design and buy-in
4. Step 3: deep dive
5. Step 4: wrap-up checklist
6. Adapting the procedure when no one is there to answer questions
7. Design document skeleton
8. Common failures of the process

## 1. The four steps and how to size them

| Step | Interview budget (45 min) | What it produces |
|---|---|---|
| 1. Understand the problem, establish scope | 3-10 min | Written scope, assumptions, numbers to design for |
| 2. High-level design, get agreement | 10-15 min | Box diagram, the main flows, a first fit check by estimation |
| 3. Deep dive | 10-25 min | The few components that decide success, designed in detail |
| 4. Wrap up | 3-5 min | Bottlenecks, failure cases, operations, next scale step |

The minutes are the book's interview budget. For real work keep the proportions: scoping is a real
fraction of the effort, the high-level design is the largest block of shared understanding, and the
deep dive goes only where the risk is. The point of the sequence is that detail comes after agreement on the
blueprint and after the numbers say the blueprint can work.

## 2. Step 1: clarify scope

Do not answer instantly. Ask, or (if nobody can answer) write down your assumption for each line.

Checklist (from ch. 3, extended with the DDIA/NALSD items):
- What exact features are in scope? What is explicitly out of scope? (Chat: 1:1 only, or groups? Text only, or media?)
- How many users? DAU vs total? Growth at 3, 6, 12 months?
- Which clients and platforms: mobile, web, both, smart TV, other services?
- Existing stack and services that can be reused (the book's YouTube design leans on existing CDN and blob storage rather than building them).
- Limits on the data: maximum friends per user, maximum file or message size, maximum group size.
- Ordering and ranking: is sorting required (reverse-chronological only? ranked?).
- Media types and sizes.
- Traffic shape: average vs peak, read:write ratio, skew (celebrity accounts, hot items).
- Latency, freshness and availability targets stated as numbers (see `requirements-and-nfrs.md`).
- Consistency needs per data type: what must never be stale, what may be?
- Data retention and deletion obligations (privacy law is an architectural input; DDIA ch. 1).
- Regions: single or international users; any data-residency constraint.

Output of this step: a short list of functional requirements, a table of non-functional requirements with numbers,
and the assumptions you made where you could not ask. The ch. 3 red flags to avoid here: jumping to a solution, and
over-engineering (design purity that ignores trade-offs and compounding costs).

## 3. Step 2: high-level design and buy-in

1. Propose a blueprint as a box diagram: clients, API/web tier, data stores, cache, CDN, queue, external providers.
   Treat the reviewer or requester as a teammate and ask for feedback before going deeper.
2. Split the system into its flows. The book's news-feed design separates a publishing flow (write path) from a feed-building
   flow (read path); the chat design separates sending, receiving, presence and sync. Designing each flow separately keeps each simple.
3. Run the estimation (`estimation.md`) now, before detail, to check the blueprint fits. (The book says to ask whether
   estimation is wanted; in real work do it unless the problem is trivially small.)
4. Walk two or three concrete use cases through the diagram, including one unhappy path, to expose gaps.
5. Define APIs and schema only if the scope is small enough for that to be meaningful. The book's example: yes for a
   multiplayer poker backend, too low-level for "design web search".
6. Start from the simplest design that meets today's numbers (a single server if the numbers allow) and climb
   `scaling-ladder.md` only as far as the numbers demand.

## 4. Step 3: deep dive

- Agree with the requester which components deserve depth. Choose by criticality: the component whose failure or
  limit decides whether the requirements are met.
- The type of problem shapes the focus: URL shortener, the key-generation scheme; chat, latency and presence; an
  analytics pipeline, freshness and correctness; a senior-level question, bottlenecks and resource estimates.
- Avoid rabbit holes (the book's example: the internals of a ranking algorithm in a feed design that excluded ranking).
- For each deep-dived component state: the options considered, the one chosen, what it costs, and what would make you switch.
  Offering more than one approach and saying why one wins is the behaviour the book rewards.

## 5. Step 4: wrap-up checklist

Do not declare the design perfect. Cover, in this order:
1. Bottlenecks and improvements: what breaks first as load grows, and what you would change.
2. Failure cases: server failure, network loss, a third-party provider outage, a whole data center. (Per-component playbooks
   appear in the YouTube and Drive designs in `worked-designs.md`.)
3. Operations: metrics (QPS at peak, latency percentiles, queue depth, error rates), error logs, rollout.
4. The next scale step: what changes when users go 10x (the book uses 1M to 10M users).
5. Further refinements you deliberately left out, and why.
6. If you offered several options, a recap of which one you recommend.

## 6. Adapting when no one can answer questions

An agent working from a one-shot request often cannot ask. Adaptation (not from the book): put an "Assumptions"
table at the top of the answer with one row per open question, your chosen value, and the effect if it is wrong
("if DAU is 10x higher, the cache tier becomes mandatory rather than optional"). Ask the user only for the two or three
assumptions that would change the architecture, and proceed with defaults on the rest. State which parts of the
design are sensitive to which assumption.

## 7. Design document skeleton

1. Problem and scope (in / out).
2. Requirements: functional list; non-functional table with numbers and measurement points.
3. Assumptions and estimates (the number sheet).
4. High-level design: diagram, flows (write path, read path), APIs, data model.
5. Deep dives: one subsection per critical component with alternatives and the reason for the choice.
6. Failure handling: component-by-component table (what fails, what the user sees, how it recovers).
7. Operations: metrics, alerts, rollout, capacity triggers.
8. Rejected designs and why (the SRE Workbook records these explicitly).
9. Open risks and next scale step.
10. Decisions worth recording: hand the significant ones to `arch-decisions-and-tradeoffs` (ADR format).

## 8. Common failures of the process

From ch. 3 "don'ts" plus the other chapters:
- Unprepared for the typical building blocks (see `building-blocks.md`).
- Jumping to a solution before scope and numbers.
- Excessive detail on one component early, before the blueprint is agreed.
- Silence: not saying why. (Architecture's Second Law in Fundamentals ch. 1: why matters more than how. Record rationale.)
- Stuck without asking for a hint or an input.
- Declaring done before the reviewer does; not asking for feedback early and often.
- Treating a trade-off-free design as finished: if you cannot name what the design gives up, you have not found the
  trade-off yet (Fundamentals ch. 1, First Law and its corollary).
