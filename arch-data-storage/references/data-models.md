# Data models and query languages

Use this file to choose a data model for a feature or service (relational, document, graph, event-sourced, DataFrame), to decide how far to normalise, to design analytical schemas, and to review models for known failure signs.

Contents
1. Model chooser
2. Relational vs document
3. Normalisation and denormalisation
4. Schema-on-read vs schema-on-write and migrations
5. Analytical schemas: star, snowflake, one big table
6. Graph models and their query languages
7. GraphQL
8. Event sourcing and CQRS
9. DataFrames, matrices, arrays
10. Warning signs and checks

Sources: DDIA 2e ch. 3; ch. 1 for the derived-data framing.

---

## 1. Model chooser

| Situation | Model | Why |
|---|---|---|
| Self-contained, tree-shaped records loaded whole; rare links between records | Document | Locality, one lookup, structure close to app objects |
| Many-to-one and many-to-many links, need to reference rows directly, enforced schema | Relational | Joins, referencing by ID |
| Everything may relate to everything; multi-hop or variable-depth traversal | Graph (Cypher, SPARQL, Datalog or recursive SQL) | Variable-length traversal is natural there |
| Warehouse/BI, regular structure, many joins and aggregates | Relational with star or snowflake schema, or one big table | Convention analysts and tools expect |
| Complex domain, many different read shapes, audit, replay | Event sourcing plus CQRS | Log of facts, many derived views |
| Feature prep for ML, statistics, scientific arrays | DataFrames, matrices, array databases | Bulk transformations, linear algebra |
| Untrusted client needs exact fields for a UI | GraphQL in front of any of the above | Restricted query surface |

Models can be emulated in each other, awkwardly (a graph in SQL), and products are converging: relational systems now take JSON types and indexes, document systems added joins, secondary indexes and declarative queries, and SQL has graph support. Best results often combine models in one database. So the choice is rarely "one model forever"; decide on the dominant access pattern and let the secondary pattern use the engine's convergence features.

Declarative query languages (SQL, Cypher, SPARQL, Datalog) state the pattern wanted, not the algorithm. The optimiser can pick indexes, join order and parallelism and improve over time without query changes; imperative code must hand-implement all that.

## 2. Relational vs document

**Object-relational mismatch.** A translation layer sits between objects and tables. ORMs cut boilerplate, cache query results and manage migrations, but: they cannot fully hide the difference; they serve only OLTP app development while data engineers still need the underlying schema; they are mostly relational-only; generated schemas can be awkward and customising them negates the benefit; and they make inefficient queries easy. The standard one is the **N+1 problem**: one query returns N rows, then N separate lookups run instead of a join. Fix by telling the ORM to eager-fetch or join.

**Document strengths.** Whole tree in one place (a CV with positions, education, contact info) means one read instead of several queries or a messy multiway join ("shredding" trees into tables). Better locality. Natural ordered lists (a JSON array for reorderable items). Schema flexibility.

**Document weaknesses.** Cannot refer directly to a nested item ("the second position of user 251"). Weak or absent joins, so many-to-one and many-to-many need ID references and application-side joins. Whole-document load and usually whole-document rewrite on update.

**Relational strengths.** Joins, many-to-one and many-to-many via an associative table with secondary indexes on both columns, referencing any row by ID, enforced schema. **Weaknesses.** Trees need shredding; there is no standard way to model reorderable lists (integer position column with renumbering, linked list of IDs, fractional indexing).

Rules:
- "One-to-many" is really one-to-few. If a parent can have thousands of children (comments on a celebrity post), do not embed; use separate records.
- Keep documents small and avoid frequent small updates, since the database loads and rewrites the whole thing.
- Locality is not exclusive to documents: Spanner interleaved tables, Oracle multi-table clusters, and Bigtable/HBase column families offer it for other models.
- For documents with many-to-many links, either store IDs on both sides (denormalised, can drift) or store the relationship once and put a secondary index on a value inside an array (for example `positions[].org_id`).
- Document query languages range from key-value only, through secondary indexes, to rich ones (MongoDB aggregation pipeline is roughly a subset of SQL in JSON syntax; XQuery/XPath for XML).

## 3. Normalisation and denormalisation

- **Normalised**: a human-meaningful value is stored once and referenced by a meaningless ID that never needs to change. Benefits listed: consistent spelling, disambiguation, one place to update, localisation, better search. Cost: every display needs a lookup, a join.
- **Denormalised**: the value is duplicated into each record. Costs: more code, more writes, more space, inconsistency if some copies update and others do not.
- Trade-off statement: normalised writes fast (one copy) and reads slower (joins); denormalised reads fast and writes costlier.
- Treat denormalisation as derived data. You need a process that refreshes the copies and must handle a crash halfway through. Atomic multi-record transactions help, but not every document database offers cross-document atomicity; the alternative is stream processing (`arch-data-pipelines`).
- Guidance: OLTP is better normalised (reads and updates both need to be fast). Analytics is often better denormalised (read-dominated, bulk updates, history rarely changes). At small or moderate scale normalised is usually best: no consistency worry and joins are affordable. At very large scale join cost can become a problem.

**Worked case: home timeline.** A materialised timeline is a denormalised cache of the posts-follows join, kept up to date by fan-out on write. But the timeline stores only post ID, sender ID and small metadata, not post text. On read the service hydrates the IDs: application-side joins fetch post content (like and reply counts) and sender profile. Reason: counts, names and photos change quickly, so copying them into every timeline would be wasteful and stale. Hydration parallelises well and its cost does not depend on follower count. Lessons: joins on read are not inherently an obstacle to scale; the most scalable design may denormalise some fields and not others; decide per field by how often it changes and by the read/write cost for outliers such as celebrity accounts. Normalisation is not inherently good or bad.

Decision procedure per field that you consider copying:
1. How often does the source change? (Fast-changing fields stay referenced.)
2. How many copies would one change touch, including the worst-case entity?
3. Who refreshes copies, and is that atomic or at least restartable?
4. What staleness is acceptable to the reader?
If you cannot answer 3, keep the field normalised.

## 4. Schema-on-read vs schema-on-write

"Schemaless" is misleading: there is always an implicit schema assumed by the reading code. Schema-on-read resembles dynamic typing, schema-on-write resembles static typing, and the book says there is no clear winner.

Changing a field's shape (full name into first and last name):
- Document database: start writing new-shape documents and have every reader handle old shapes, forever, unless you backfill.
- Relational: migrate. Adding a nullable column with a default of null is fast on most databases; the backfill `UPDATE` rewrites every row and is slow on large tables; changing a column type often copies the whole table. Online schema-change tools named: pt-online-schema-change, gh-ost, pg-osc, pgroll. A cheap trick is to add the nullable column and fill it at read time, as a document database would.

Schema-on-read wins when items are heterogeneous (many object types, not practical as one table each) or when structure is dictated by external systems that may change. If all records share a structure, a schema documents and enforces it.

For how stored data of different shapes coexists with rolling code deploys, see `encoding-and-schema-evolution.md`.

## 5. Analytical schemas

Warehouses are usually relational with conventions: star schema, snowflake schema, dimensional modelling (Kimball) and one big table.

- **Fact table**: one row per event (a purchase of a product by a customer, a page view, a click). Kept as individual events for flexibility, so it is huge (petabytes). Columns are attributes (sale price, cost) plus foreign keys to dimension tables.
- **Dimension tables**: the who, what, where, when, how and why (dim_product, dim_store, dim_customer, dim_date; a date dimension lets holidays and the like be encoded). Queries do many joins to dimensions.
- **Star**: fact table in the centre, dimensions as rays. **Snowflake**: dimensions normalised further into sub-dimensions (brand and category tables behind dim_product). Snowflake is more normalised but stars are often preferred for being simpler for analysts.
- Tables are wide: fact tables often over 100 columns, sometimes several hundred.
- Multi-item purchases are modelled as one fact row per product sharing customer, store and timestamp, not as a basket entity.
- **One big table (OBT)**: dimensions folded into fact columns, a precomputed join. More storage, sometimes faster queries. Denormalisation is fine here because the data is a historical log that rarely changes.

Choose star by default for BI over regular data; snowflake only if dimension duplication is itself a maintenance problem; OBT when join cost dominates and storage is cheap. Physical layout of such tables (columnar, sort order) is in `analytical-storage.md`.

## 6. Graph models

Choose a graph when many-to-many relationships are pervasive and complex; documents suit tree-like data and relational handles simple many-to-many. A graph is vertices (entities) plus edges (relationships). Uses: social graphs, web graph, road networks, knowledge graphs, heterogeneous graphs (people, places, events in one graph).

**Property graph** (Neo4j, Memgraph, KùzuDB; Neptune supports both models). Vertex: ID, label, properties, incoming and outgoing edges. Edge: ID, tail vertex, head vertex, label, properties. It can be stored relationally as `vertices(id, label, properties jsonb)` and `edges(id, tail, head, label, properties jsonb)` with indexes on tail and head to traverse both ways. Properties: no schema restricting which vertices connect; efficient traversal in both directions; labels let one graph hold many kinds of data; flexible hierarchies of varying granularity; good evolvability. Limitation: an edge links exactly two vertices, so a three-way relationship needs an extra vertex (or a hypergraph).

**Cypher** uses arrow patterns. People who emigrated from the US to Europe:

```
MATCH (p)-[:BORN_IN]->()-[:WITHIN*0..]->(:Location {name:'United States'}),
      (p)-[:LIVES_IN]->()-[:WITHIN*0..]->(:Location {name:'Europe'})
RETURN p.name
```
`*0..` follows the edge zero or more times. Because the query is declarative, the engine may start from people or from the two named locations.

**SQL for the same query** needs `WITH RECURSIVE` common table expressions because the number of joins is not known in advance; the book's example grows from 4 lines of Cypher to about 31 lines of SQL, plus extra concerns (cycles, breadth vs depth first). Use this as a signal: a query with variable-depth traversal written as a fixed number of joins is the wrong tool or the wrong model.

**Triple stores and SPARQL** (Datomic, AllegroGraph, Blazegraph): data is (subject, predicate, object). An object that is a primitive means a property; an object that is a vertex means an edge. Real systems add metadata (Neptune quads add a graph ID; Datomic uses 5-tuples with transaction ID and deleted flag). RDF is the data model, with URIs for predicates to avoid clashes when merging data across organisations. The Semantic Web did not succeed as envisioned but left JSON-LD, Schema.org, Wikidata and Open Graph. SPARQL's pattern syntax was borrowed by Cypher.

**Datalog** (Datomic, LogicBlox, CozoDB): facts as rows, queries as rules that derive virtual tables, applied repeatedly until no new facts appear. A recursive rule such as `within_recursive(Loc, Name) :- within(Loc, Via), within_recursive(Via, Name)` expresses the traversal. Build queries rule by rule like functions. Very expressive for recursive queries; less known.

**Query language options**: Cypher, SPARQL, Datalog, GraphQL, SQL recursive CTEs, plus Gremlin, GSQL, PGQL; ISO GQL (2024, Cypher-based) is not yet widely adopted.

## 7. GraphQL

Restrictive by design: for OLTP queries from untrusted client code (mobile, web) that want a JSON document with exactly the fields needed to render a UI. Frontend developers can change queries without changing server APIs. It intentionally forbids recursive queries and arbitrary search conditions (denial-of-service protection); only joins declared in the schema can be requested. The response is deliberately denormalised (sender name repeated per message) to make rendering simple while storage stays normalised. It works over relational, document or graph back ends.

Costs: tooling to translate to internal REST/gRPC calls; authorisation, rate limiting and performance concerns. Apply: set depth and cost limits, authorise per field, and measure the resolver query count (the N+1 trap reappears in resolvers; adaptation). API-style choice among REST, gRPC and GraphQL is in `arch-api-design`.

## 8. Event sourcing and CQRS

Idea: write in one representation, derive read-optimised ones. The simplest, fastest write form is an append-only log of immutable, self-contained, timestamped events; never modify or delete, only append superseding events.

- **Event sourcing**: events are the source of truth; every state change is an event. **CQRS**: separate read-optimised representations (materialised views, projections, read models) derived from the write-optimised log. Both come from the domain-driven design community and relate to state machine replication.
- **Command vs event**: a user request is a command and is validated first (enough seats?). If valid it becomes a fact and the event is appended. The log holds only valid events, and a view consumer must not reject an event. Name events in the past tense ("seats were booked"). Cancellation is a new later event.
- Contrast with a star-schema fact table: both are histories of past events, but fact rows share one column set and are unordered; event logs have many event types and order matters.

Advantages:
1. Events convey intent ("booking was cancelled") rather than raw row mutations.
2. Views are reproducible: delete and recompute by replaying the same events in order with the same code; a bug in view code is fixed and rebuilt; debugging by re-running.
3. Multiple views, each optimised per query pattern, in any model, even in-memory only.
4. New features add new views or event types without touching old events.
5. Mistakes are fixed by appending compensating events; downstream views self-correct.
6. Built-in audit log.
7. High write throughput from sequential appends; bursts absorbed while views catch up.

Disadvantages and how to handle them:
1. External information (an exchange rate) must not be fetched at processing time or replays differ. Embed the value in the event, or look up a historical value deterministically by event timestamp.
2. Immutability conflicts with erasure. Per-user logs can be deleted; shared logs cannot. Options: keep personal data outside the event, or crypto-shredding (encrypt with a deletable key). Both complicate recomputation.
3. Replays must not repeat externally visible side effects (do not resend emails when rebuilding a view).
4. Hard requirement: every view must process events in exactly the log order, which is non-trivial in distributed systems (`arch-replication-and-consistency`).

Implementations: any database; purpose-built (EventStoreDB, MartenDB on PostgreSQL, Axon Framework); or a Kafka log with stream processors maintaining views. Pipeline mechanics are in `arch-data-pipelines`.

Use when: the domain has many read shapes over the same facts, audit or replay is valuable, or the history itself is the product. Do not use when: the system is simple CRUD with one read shape, nobody will replay, or erasure and side-effect constraints cannot be met.

## 9. DataFrames, matrices, arrays

DataFrames (R, Pandas, Spark, Dask) look like tables with relational-style bulk operators (filter, group and aggregate, join called "merge") but are manipulated imperatively as a sequence of commands on a private copy, not by declarative query. Typical use is turning relational-like data into a matrix or multidimensional array for ML: a user-by-movie ratings pivot becomes a sparse matrix with thousands of columns, a poor fit for a relational database. Non-numeric data becomes numeric by scaling dates to floats and one-hot encoding small fixed value sets (one 1/0 column per genre). Array databases (TileDB) serve scientific data such as rasters and imaging; finance uses DataFrames for time series. Not covered by the chapter: genome similarity, double-entry ledgers (TigerBeetle), full-text and vector search (see `storage-engines-and-indexes.md`).

## 10. Warning signs and checks

| Sign | Likely problem | Check or fix |
|---|---|---|
| Query count per request grows with result size | N+1 from lazy loading | Log or count queries in a test; eager-fetch or join |
| Embedded array with no upper bound | Document grows without limit | Move children to a separate collection or table |
| Denormalised field with no named refresh path | Stale or inconsistent copies | List every denormalised field and its refresh mechanism (inferred check) |
| Reader code full of branches on old document shapes | Schema-on-read debt | Add a version field and backfill (inferred) |
| Fixed number of joins for variable-depth data | Wrong tool for traversal | Recursive CTE or a graph language |
| View cannot be rebuilt identically from the log | Events depend on external lookups or wall clock | Embed the external value in the event; replay test |
| GraphQL exposed to untrusted clients without limits | Expensive or unauthorised queries | Depth/cost limits, authorisation, rate limiting |
| Join table needed for 3+-way relation in a property graph | Edge links only two vertices | Reify the relationship as a vertex |
