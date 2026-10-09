# Data ownership: single, common, joint

Read this when a table is written by more than one service, when someone proposes a shared
database or "let service B connect to A's schema", or when you are splitting a monolith's data and
must decide who owns what.

Contents: the ownership rule; procedure; single; common; joint (four techniques, each with its
trade-off table); choosing among the joint techniques; the one-schema rule; worked example;
anti-patterns; verify.

## The rule

The service that writes to a table owns it (Hard Parts ch. 9). Reads from other services do not
confer ownership; they raise an access problem (see `distributed-data-access.md`).

Companion rule from the data architect in the notes: it is acceptable for several services to
connect to one schema (a data domain), but not for one service to connect to several databases or
schemas. This is the "one-schema rule" and it removes options later (see below).

Diagramming trick: draw a table inside a service box to say it belongs to that bounded context. A
table drawn outside every service is a shared data domain.

## Procedure

1. List every table and, for each, which services write to it (not read). Read-only users are
   handled later.
2. Resolve single ownership first. It clears the field and shrinks the problem.
3. Resolve common ownership (most or all services write, for example an audit table).
4. Resolve joint ownership (a couple of services in the same domain write).
5. For each remaining reader in another bounded context, pick an access pattern.
6. Validate the assignment against each business workflow's transaction needs (which operations
   used to be one ACID transaction and now cross services). Then write an ADR.

## Single ownership

One writer, so that service owns the table. Other services that read it need an access technique.
Example: the Wishlist table is owned by the Wishlist service.

## Common ownership

Symptom: nearly every service writes the table (audit log, notification log).

- A shared database or schema brings back the problems of a shared database: change control,
  connection starvation, scalability, fault tolerance.
- Technique: create a dedicated service that is the sole owner (reads and writes); the others send
  it data.
  - Callers that need no response: asynchronous fire-and-forget over a persistent queue (the
    broker writes to disk, so delivery survives broker or service failure).
  - Callers that need a return value (a confirmation number or generated key): synchronous
    REST or gRPC, or request-reply messaging (pseudo-synchronous).
- Example: a new Audit service owns the Audit table; Wishlist, Catalog and Inventory send it
  asynchronous messages.

## Joint ownership: four techniques

Running example: a Product table where Catalog inserts and removes products and edits static data,
while Inventory updates inventory counts.

### 1. Table split

- What: split the table so each service owns its part. Mechanics: create `Inventory(product_id,
  inv_cnt)`, populate from `Product`, drop `inv_cnt` from `Product`.
- Result: single ownership each, but the services must synchronise on create and remove (Catalog
  generates the id and tells Inventory; on removal it informs Inventory).
- The hard questions are the availability-versus-consistency choice. If Inventory is down while
  Catalog adds a product, either the product operation succeeds without the inventory row (choose
  availability) or it fails (choose consistency). Synchronous with confirmation improves
  consistency and hurts performance; fire-and-forget does the reverse.
- Use when: columns separate cleanly by owner and consistency may lag.

| Advantages | Disadvantages |
|---|---|
| Preserves bounded context | Tables must be altered and restructured |
| Single data ownership | Possible data consistency issues |
| | No ACID transaction between the two table updates |
| | Data synchronisation is difficult |
| | Data replication between tables may occur |

### 2. Data domain

- What: both services share ownership; their tables live in the same schema or database, forming a
  broader bounded context. Performance, availability and consistency problems disappear; the
  services do not depend on each other at runtime.
- Re-check the premise: if the data is common, why are these separate services? Valid reasons are
  different scalability, fault tolerance or throughput needs, or isolating code volatility.
- Costs: schema changes must be coordinated across all sharing services (wider testing, more
  deployment risk); if only one service should write certain columns you need explicit write
  governance.

| Advantages | Disadvantages |
|---|---|
| Good data access performance | Schema changes involve more services |
| No scalability or throughput issues | Increased testing scope for schema changes |
| Data remains consistent | Data ownership governance (who writes what) |
| No service dependency | Increased deployment risk for schema changes |

### 3. Delegate

- What: one service is the sole owner (the delegate); the other asks it to perform updates on its
  behalf.
- Choosing the delegate:
  - Primary-domain priority (the authors' recommendation): the owner is the service that does most
    CRUD on the primary entity (Catalog for Product). Inventory calls Catalog for count changes.
    Fix the resulting performance and fault-tolerance cost with a replicated in-memory cache or
    distributed cache for reads.
  - Operational-characteristics priority: the owner is the service needing the highest performance,
    availability or throughput (Inventory, since counts change in real time and product edits are
    rare), so hot updates go straight to the database. Cost: Inventory now handles database work
    and error handling for static product data it does not conceptually own.
- Communication: synchronous waits, stays consistent, slower; asynchronous is faster and eventually
  consistent, but if the delegate errors there is no guarantee the update happened.
- Best for writes that do not need atomic transactions and tolerate eventual consistency.

| Advantages | Disadvantages |
|---|---|
| Forms single table ownership | High level of service coupling |
| Good schema change control | Low performance for non-owner writes |
| Abstracts data structures from other services | No atomic transaction for non-owner writes |
| | Low fault tolerance for non-owner services |

### 4. Service consolidation

- What: merge the co-owning services into one, giving single ownership. Atomic transactions return
  and performance is good.
- Costs: coarser scalability (catalogue maintenance must scale with inventory load), less fault
  tolerance (they fail together), larger testing scope, more deployment risk.

| Advantages | Disadvantages |
|---|---|
| Preserves atomic transactions | More coarse-grained scalability |
| Good overall performance | Less fault tolerance |
| | Increased deployment risk |
| | Increased testing scope |

## Choosing among the joint techniques

| Situation | Technique |
|---|---|
| The two writers need one atomic transaction and are inseparable | Service consolidation |
| Same, but they must stay separate for scale, fault tolerance, throughput or volatility reasons | Data domain |
| Columns split cleanly by owner and consistency can lag | Table split |
| One entity clearly dominates; the other service's writes can be asynchronous or eventual | Delegate, primary-domain priority, with a cache for reads |
| Services must be independent and a shared schema is tolerable | Data domain, after re-justifying the split |
| A service already belongs to another data domain's schema | Data domain is ruled out for it (one-schema rule) |

## Worked example (Sysops Squad and the retail illustration)

- Retail illustration: Wishlist table to the Wishlist service (single); Audit table to a new Audit
  service fed by an asynchronous persistent queue (common); Product table by delegate with Catalog
  as owner and Inventory sending update requests (joint).
- Expert profile table: only User Maintenance writes it, so User Maintenance owns it. Ticket
  Assignment reads it constantly and may not touch the schema (access solved in
  `distributed-data-access.md`).
- Survey table: Ticket Completion writes completion timestamp and expert; the Survey service
  writes sent timestamp and results, so ownership is joint. Table split was impossible because of
  the table structure. Data domain was rejected because Ticket Completion already uses the ticketing
  data domain schema and merging survey tables into it would regrow a monolithic database. Chosen:
  delegate to the Survey service. Ticket Completion already sent a message to start the survey, so
  that message now carries all the data the Survey service needs, and survey record creation became
  the Survey service's own activity.
- Process lesson from the notes: the data team and the development team argued because they were
  separate; ownership decisions go faster with both in the room.
- ADR pair recorded: "single table ownership for bounded contexts" (read-only consumers cannot
  access another context's schema directly; consequence is possible read performance and
  fault-tolerance cost) and "Survey service owns the survey table" (consequence: the trigger
  message must carry all data Ticket Completion used to insert).

## Anti-patterns

- Granting a second service write access to a table "just for this one case". It creates joint
  ownership without anyone deciding the technique.
- Letting a consumer connect to the owner's schema because it is quicker than an access pattern.
- Choosing data domain by default and not asking why the services are separate.
- Using delegate with asynchronous writes where the business needs the write confirmed.

## Verify

- Ownership audit (inferred): every table has exactly one service with write grants, or is
  explicitly documented as part of a named data domain. Implement as a fitness function that scans
  database grants and the SQL or ORM mappings in each repository for writes to tables the service
  does not own.
- For every business transaction that used to be one database transaction, the design document
  states its new consistency model, its failure compensation and its maximum staleness window.
- For table split: a test where the partner service is down during create and remove, showing the
  chosen behaviour (succeed without the row, or fail) and that the repair path exists.
- For delegate: a test for the delegate being unavailable, and for the duplicate-request case if
  the call is asynchronous (the delegate must be idempotent).
