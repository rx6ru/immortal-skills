# ACID, BASE and the eventual-consistency patterns

Read this when a business request spans several services that each own a database and you must
decide how the pieces converge: "how do we keep Profile, Contract and Billing in step when a
customer unsubscribes", or "can we use a distributed transaction here".

Contents: what ACID gives inside one service; what is lost across services (BASE); the three
eventual-consistency patterns with trade-off tables; choosing; error handling; worked timeline;
verify. For heavy detail on two-phase commit and exactly-once see
`end-to-end-correctness.md`; for sagas see `saga-patterns.md`.

## ACID inside one service

(Hard Parts ch. 9; DDIA 2e ch. 8 for the sharper definitions.)

| Property | Meaning |
|---|---|
| Atomicity | All updates commit or all roll back as a unit. DDIA stresses this means abortability: after a fault the database discards every write so far and a retry is safe. It is not the multithreading sense of "nobody sees half-done state"; that is isolation. |
| Consistency | Application invariants hold before and after the transaction, possibly broken inside it. Mostly the application's job; the database enforces only declared constraints (foreign key, unique, check). |
| Isolation | Concurrent transactions do not step on each other; uncommitted data is invisible. Textbook form is serializability; most systems run weaker levels. |
| Durability | After the commit is acknowledged the data survives later failures. No perfect durability exists; combine disk, replication and backups. |

ACID can exist inside each service if its database supports it. A business request that spans
services is a distributed transaction and the request as a whole is not ACID. An architect cannot
analyse when a distributed transaction is acceptable without knowing precisely which of the four
properties they are giving up.

## Across services: BASE

Across the request all four properties are lost:

- Atomicity is bound to each service, not to the business request.
- Consistency: a failure in one service leaves tables out of step; foreign keys cannot span
  separately committed databases.
- Isolation: data committed by one service is visible to everyone before the overall request
  finishes.
- Durability exists only per service.

BASE: Basic availability (all participating services are expected to be up; asynchrony can decouple
but delays consistency), Soft state (the in-progress state of the business request is unknown or
hard to determine, especially with asynchronous or parallel work), Eventual consistency (given time
everything converges; how long depends on the pattern and the error handling). DDIA calls "BASE"
vaguer than ACID and effectively "not ACID"; treat it as a label for what you give up, not as a
design.

Running example: customer 123 unsubscribes. Customer Profile deletes its row and confirms, but
Support Contract and Billing Payment rows remain. The patterns below differ in when and how those
rows are fixed.

Eventual consistency is bought with performance, scalability, elasticity, fault tolerance and
availability. It is a trade, so name what the business gets for it.

## Pattern A: background synchronisation

- A separate process (nightly or hourly batch) detects changes, by event stream, database trigger
  or source-versus-target comparison, and aligns the data sources. Timeline: request 11:23:00,
  response 11:23:01, batch at 23:00 removes the leftover rows.
- Slowest convergence, fastest response.
- Serious problems: the sync process needs write access to every service's tables, which is shared
  ownership and breaks each bounded context; table changes must be coordinated with the external
  process; business rules get duplicated (for example "keep rows for three months after removal in
  case of resubscription" lives in the services and in the batch).
- Suitable for closed, heterogeneous systems that otherwise share no data (an order-entry system
  feeding an invoicing system on another platform). Avoid in microservices.

| Advantages | Disadvantages |
|---|---|
| Services decoupled | Data source coupling |
| Good responsiveness | Complex implementation |
| | Breaks bounded contexts |
| | Business logic may be duplicated |
| | Slow eventual consistency |

## Pattern B: orchestrated request-based

- The whole distributed transaction runs during the request while the user waits, driven by an
  orchestrator that knows the process, participants, multicasting, error handling and contract
  ownership. The orchestrator may be an existing primary service (overloads it and ties it tightly)
  or, preferred, a dedicated service (for example an Unsubscribe Orchestrator).
- Sequencing tip from the example: call Customer Profile first and synchronously, because it may
  refuse (an outstanding billing charge), and then nothing needs reversing. Then call Support
  Contract and Billing in parallel. Response at 11:23:02.
- Favours consistency over responsiveness.
- Error handling is the hard part. If Billing fails after Profile and Contract committed, options
  are retry, compensating transaction, tell the customer to retry later, or ignore. With no other
  repair mechanism, the last two are out, so you need compensation: re-insert the customer and reset
  the removal date, which requires the orchestrator to hold all data needed and the re-creation to
  have no side effects. If compensation itself fails the data is truly out of step and a human must
  repair it. This leads directly to sagas.

| Advantages | Disadvantages |
|---|---|
| Services decoupled | Slower responsiveness |
| Timeliness of data consistency | Complex error handling |
| Atomic business request | Usually requires compensating transactions |

## Pattern C: event-based

- Publish an event ("customer unsubscribed") or command to an asynchronous topic or event stream;
  interested services subscribe. Customer Profile deletes the row, publishes, responds in about a
  second; Contract and Billing react concurrently.
- Subscribers must be durable: on topic-based brokers a durable subscription lets a subscriber that
  was down at publish time still receive the message later. On event streaming platforms the broker
  must retain messages long enough.
- Error handling: if a subscriber fails mid-processing, the broker retries, then moves the message
  to a dead letter queue. An automated process tries repair; otherwise a person does.
- Handlers must be idempotent, because retry and redelivery are part of the mechanism (see
  `end-to-end-correctness.md`).

| Advantages | Disadvantages |
|---|---|
| Services decoupled | Complex error handling |
| Timeliness of data consistency | |
| Fast responsiveness | |

## Choosing

| Situation | Pattern |
|---|---|
| The request must be known complete before replying and latency is tolerable | Orchestrated request-based; accept compensation complexity |
| Fast response, decoupled services, modern microservices or event-driven style | Event-based; accept dead letter handling and soft state |
| Closed, legacy or heterogeneous systems, no bounded-context concern, lax timing | Background synchronisation |
| Microservices with real bounded contexts | Not background synchronisation |

Cross-check with the sagas: patterns B and C are the informal versions of the orchestrated and
choreographed eventual sagas. If the workflow has many error paths, go to `saga-patterns.md` and
`saga-state-and-compensation.md` rather than improvising.

## Verify

- State per business transaction: where ACID applies (inside which service), where BASE applies,
  how long convergence may take, and who repairs a stuck case.
- Event-based: test that a subscriber stopped during the publish receives the event on restart;
  that a poisoned message lands on the dead letter queue and is alerted on; that the handler is
  idempotent under redelivery (deliver it twice, assert one effect); measure real convergence time
  against the staleness the business accepts.
- Orchestrated: inject a failure at each participant in turn, and also a failure of the
  compensating action; confirm the end state is detectable and repairable.
- Background sync: list every table the batch writes to; each one is a violated ownership boundary
  that needs an explicit justification.
