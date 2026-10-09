# Decomposing a shared database

Contents: 1. Why this is harder than splitting code; 2. Drivers to break the data apart (six); 3. Drivers to keep it together (two); 4. Checklist; 5. The five-step process; 6. Connection quotas worked example; 7. Selecting a database type per service; 8. Worked case (survey); 9. Verify; 10. Limits.

Source: Architecture: The Hard Parts ch. 6. Ratings of database types were charts in the book that the notes could not recover; the table in section 7 is rebuilt from prose and the notes mark parts as inferred. For ownership of data, data access across services, sagas and analytical data, go to `arch-distributed-workflows`. For general database selection and models, `arch-data-storage`.

## 1. Why this is harder than splitting code

- Data is the company's most important asset and is tightly coupled to application behaviour, so the seams are hard to find and the disruption risk is high.
- Mapping from code: components correspond to data domains; class files to tables; coupling points between classes to foreign keys, views, triggers and stored procedures.
- Architecture style matters. Microservices need each service to own its data (a bounded context). Service-based architecture allows a shared database, so you can stop short of this chapter's work.
- Include the DBA or data architect from the start. In the case, the data architect first refused ("convince me with a solid justification") because she had been left out.

## 2. Data disintegrators: reasons to break the database apart

1. Change control. Question: how many services are affected by a change to one table? Breaking changes: drop or rename a table or column, change a column type. Non-breaking: add a column or table. With a shared database all affected services must be updated, tested and deployed together with the database. Worse, a forgotten service reading the changed table fails in production (picture 42 or 400 services on one clustered database). Remedy through bounded context: a service owns the data it writes (read-only access is not ownership). Other services ask the owner through a contract (JSON, XML, object), which shields callers from the schema. Example: table `Wishlist(CUSTOMER_ID, ITEM_ID, QUANTITY, EXPIRATION_DT)` exposed as JSON `{cust_id, item_id, qty, exp_dt}` with the date as epoch milliseconds. Dropping the column changes only the owner, who can keep the contract by returning a far-future date or 0 until the contract is deliberately changed.
2. Connection management. Each service instance has its own connection pool, and a shared database saturates. Symptom: frequent connection waits (also seen as timeouts or tripped circuit breakers). Arithmetic from the notes: a monolith with 200 connections becomes 50 services x 10 connections x at least 2 instances = 1,000, and the notes give about 1,700 if half scale to 5 instances (my own arithmetic gives 1,750, so treat it as order of magnitude). Remedy: connection quotas per service (section 6).
3. Scalability. As services scale out, the database must too (connections, throughput, capacity). Separate data domains need fewer connections each and carry less load.
4. Fault tolerance. A shared database is a single point of failure: a crash or maintenance takes down every service. Splitting limits the blast radius to services using the failed database.
5. Architectural quanta. The database is part of static coupling, so five services sharing one database are one quantum even if two of them need different characteristics. Splitting lets each service group with its data become its own quantum.
6. Database type optimisation. One database means one type for everything. Splitting lets key-value reference data go to a key-value store, survey data to a document store, and so on.

## 3. Data integrators: reasons to keep data together

1. Data relationships. Foreign keys, triggers, views, stored procedures and logical relationships (ticket and ticket status) tie tables together. Database-per-service means removing every cross-boundary foreign key, view and so on. Foreign keys can stay inside one bounded context or schema, not across. Questions to ask: is change control worth more than this foreign key? Is fault tolerance worth more than this materialised view?
2. Database transactions. A service writing several tables in one database gets a single ACID unit of work. Once the tables live in different schemas or databases behind remote calls, a write can commit in one and fail in the other. That is handled by sagas (`arch-distributed-workflows`) and the granularity rule that an ACID need is a reason to merge (`service-granularity.md`).

## 4. Checklist to run for each candidate data domain

1. How many services are hit by a schema change to these tables?
2. Connection waits now, and projected connections for planned services and instances versus the limit.
3. Throughput and capacity versus the scaling plan.
4. Blast radius of database downtime.
5. Does the data need to be in its own quantum because characteristics differ by service?
6. Does the data fit a different database type better?
7. List every foreign key, view, trigger and transaction that would be severed.
8. Decide: decompose where disintegrator evidence outweighs integrator cost. Combine data domains when tables are too tightly related (a broader bounded context where several services own related data).

Evidence to gather in a repository (adaptation): grep services' configuration and code for connection strings and table names to build a table-to-service access map; read slow-query and connection-wait metrics; list foreign keys, views, triggers and stored procedures from the schema (`information_schema` or the engine's catalogue).

## 5. The five-step process (iterative, evolutionary)

A data domain is a collection of coupled database artifacts (tables, views, foreign keys, triggers) tied to one domain and used together in a limited functional scope. Picture the database as a soccer ball: each hexagon is a data domain; relationships inside a hexagon stay; dotted lines across hexagons must go. Remove cross-domain foreign keys, views, triggers, functions and stored procedures with the refactoring patterns from the database-refactoring literature (Ambler/Sadalage's *Refactoring Databases* is the book's reference). A data domain is an architectural concept, a schema is the database construct; usually 1:1, sometimes one schema for several combined domains.

Step 1. Analyse the database and create data domains. Start state: shared-database integration, every service can reach every table. Group related tables. Case result: Customer (customer, customer_notification); Survey (survey, question, survey_administered, survey_question, survey_response); Payment (billing, contract, payment_method, payment); Profile (sysops_user, profile, expert_profile, expertise, location); Knowledge Base (article, tag, keyword, article_tag, article_keyword); Ticketing (ticket, ticket_type, ticket_history).

Step 2. Assign tables to data domains (schemas). Create a schema per domain and move tables, for example `ALTER SCHEMA payment TRANSFER sysops.billing;` (the notes' syntax is SQL Server style; adapt per engine). Fix cross-domain objects. Case: the view `payment.v_customer_contract` joined `customer.customer` for `customer_name`; rewrite it to drop the join and the column (keep `customer_id`), and the Payment service calls the Customer service for the name. If two domains are too tightly coupled, combine them.
- Interim aid: synonyms (like symlinks), for example `CREATE SYNONYM ticketing.sysops_user FOR profile.sysops_user;` so queries join a local alias. They do not remove cross-schema coupling (read/write privileges still cross, coupling points remain) but make dependency checking and later splitting easier. Treat them as scaffolding with a removal date.

Step 3. Separate database connections per data domain. Refactor each service to connect only to its own schema, with read/write only on its domain's tables. All cross-schema access becomes a call to the owning service, and synonyms go. This is the hardest step. Rule: do not reach into another database; use the service that owns the data domain. The result is data sovereignty per service.
- Benefits: schema changes do not affect other domains; each service can pick the best database type.
- Shortcomings: performance problems when a service needs large volumes of other domains' data; the database can no longer enforce referential integrity across domains (bad-data risk); all database code (procedures, functions) touching other domains' tables has to move into the service layer.

Step 4. Move schemas to separate database servers. Many schemas on one server are still one quantum with shared fate for scalability, fault tolerance and performance. Two options: backup and restore (back up each schema, create servers, restore, repoint services, drop from the old server; usually needs downtime) or replication (set up servers, replicate schemas, switch connections, drop from old; no downtime but more setup and coordination).

Step 5. Switch to independent database servers. Cut connections to the old server and remove the schemas from it. Final state: each data domain on its own server; teams tune each for availability and scalability and may choose a more suitable database type.

Order matters. Steps 1 to 3 give logical separation (one server, separate schemas); steps 4 and 5 give physical separation. Adaptation, not the book's claim: logical separation is usually cheaper to reverse, and stopping after step 3 is defensible when the drivers that remain (connection limits, blast radius, type fit) are not pressing. If you stop, say so in the ADR, because shared-server fate (one quantum) remains.

## 6. Connection quotas worked example

Rule: start with an even split, measure concurrent connection use per service as a fitness function, store quotas in an external configuration server, and adjust (manually or programmatically) by moving headroom from services that have spare to services that wait.

Database limit 100, five services:

| Round | Quotas A/B/C/D/E | Observation |
|---|---|---|
| 1: even | 20/20/20/20/20 | Max used: A 5, B 20 (waits), C 15, D 20 (waits), E 14 |
| 2 | 10/25/20/25/20 | B still waits |
| 3 | 8/29/20/25/18 | No waits; B max 27 |

Scaling caution from the same example: with instances A2, B3, C3, D2, E4 the notes give 242 connections needed against 100 available (142 short), even though the quotas sum to 100 (I could not reproduce 242 from the quota tables in the notes, so take it as the book's illustration of the effect, not a checkable figure). So per-service quotas control fairness, not total capacity: when instance counts grow, the total must be re-derived and the database or the split must change.

## 7. Selecting a database type per service

Choosing a new type needs a business justification: each type adds operational and skills cost. Evaluation characteristics: learning curve; ease of data modelling; scalability and throughput; availability and partition tolerance; consistency (ACID versus BASE or tunable); language support, maturity, SQL support and community; read versus write priority (a scale, not binary).

Summary (qualitative, reconstructed from prose; ratings that were charts are not reproduced):

| Type | Examples | Fits | Watch for |
|---|---|---|---|
| Relational | PostgreSQL, Oracle, MS SQL, MySQL | General purpose, strongest consistency (ACID), easiest to learn, flexible modelling, very mature | Mostly vertical scaling; replication and failover are complex; hard for arbitrary-depth graphs; weaker for reactive streams |
| Key-value | Riak KV, DynamoDB, Redis, MemcacheDB | Query by known key (session id, user id, order id), very high scale, read-priority such as sessions and preference caches | Can only query by key; changing an aggregate means rewriting everything; consistency tunable per query and costs latency |
| Document | MongoDB, Couchbase, AWS DocumentDB | Aggregates such as orders and tickets, easy to learn, forgiving because inner parts can be indexed and queried | Complex indexes reduce scale; sharding needs a key; ACID only within a collection with edge cases |
| Column family | Cassandra, Scylla, SimpleDB | Write-heavy, sparse data, horizontal scale for reads and writes; node loss is transparent | Hard to learn; needs iterations on row-key design; higher consistency levels lower availability |
| Graph | Neo4j, Infinite Graph, TigerGraph | Relationship-heavy, read-heavy, traversal very fast, built-in algorithms | Steep learning; hard to model (relations are explicit edges); writes hard to shard; changing relationship types is expensive |
| NewSQL | VoltDB, ClustrixDB, SingleStore, CockroachDB | Relational semantics with horizontal scale and strong ACID, geo placement | Some are DBaaS-only; sharding and geo design needed |
| Cloud native | Snowflake, Datomic, Redshift, Azure CosmosDB | Automatic scaling, lower DBA operations load, warehouses for read-priority analytics | Cost is the trade-off; newer, harder to hire for; needs a cloud account; learning varies by product |
| Time series | InfluxDB, kdb+, TimescaleDB, Amazon Timestream | Append-only timestamped, tagged points, read-heavy | Not general purpose; model one fact per tag (`ticket_status=Open` and `ticket_id=374737` separately, not one combined value) |

Concepts to use when choosing:

- Aggregate orientation (from domain-driven design): operate on related data as one unit (a ticket or a customer with dependents). Benefits: easy distribution, fewer joins, better read/write performance, less impedance mismatch. Costs: hard to get aggregates right and to change their boundaries; analysis across aggregates is hard. All NoSQL families here are aggregate-oriented.
- Sharding is horizontal partitioning across different nodes by a key; partitioning on one server is different.
- "Schema-less" is a myth: data has a schema, implicit or elsewhere, and the application must handle several versions of it.

Selection procedure (derived by the notes): identify the access pattern (by key, by relationships, by time window, analytical); the consistency need (ACID versus tunable); scale, throughput and availability needs; team skills and hiring; operational model (managed service or not); and the ability to change the schema. Choose the type whose strengths match, and require a business reason.

## 8. Worked case: moving survey data to a document store

- Developers wanted a document database for survey data; the data architect refused ("relational has always worked") and objected to adding database types. Agreement: developers and the database team work together.
- The business case came from the product owner: survey changes are frequent (marketing wants flexibility) but take days even to add one question because of querying and aggregating relational data for the UI, so marketing stopped filing change requests. The driver was flexibility and time to change, a business reason rather than engineering taste.
- Model both options before deciding. (a) Single aggregate: the survey document embeds its questions (one read renders the survey; questions are duplicated across survey documents). (b) Multiple aggregates: the survey references question documents (reuse, no duplication, harder to render). Facts: only five survey types (one per product category), changes mostly add or remove questions, the complexity is in the UI. So accept duplication, choose (a).
- ADR: use a document database for the customer survey. Consequences: with a single aggregate several documents must change when a common question changes; survey functionality must be shut down during migration from relational to document.

## 9. Verify

After step 3 (logical separation):
- No service holds credentials or a connection string for another domain's schema.
- No cross-schema view, foreign key or synonym remains (query the catalogue to prove it).
- Every cross-domain read in the code goes through the owner's API; grep for the other domain's table names outside the owning service finds nothing.
- Reports or aggregations that previously joined across domains were rewired through services or a separate analytical store.

After steps 4 and 5:
- Each database can be restored and each service deployed independently.
- Connection waits per service are near zero under a load test at projected instance counts; quotas are in configuration and a fitness function reads actual usage.
- A failure drill: stop one database and confirm only its services fail.

Before starting: the ADR lists the disintegrators with evidence, the integrators with what will be severed, and the DBA has agreed.

## 10. Limits

- If the architecture is service-based and the drivers are weak, a shared database is a valid end state.
- Do not split data for a database type you cannot justify to the business; polyglot persistence multiplies operations.
- Cross-domain consistency and cross-service reads create new problems (latency, integrity, sagas). Plan for them with `arch-distributed-workflows` before step 3, not after.
