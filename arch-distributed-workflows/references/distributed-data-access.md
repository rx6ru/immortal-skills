# Reading data a service does not own

Read this when a service needs read access to a table owned by another service ("assignment needs
the expert profile", "the wishlist page must show item descriptions") and in a monolith this was a
join.

Contents: the problem; the four patterns with costs and trade-off tables; decision procedure;
sizing a replicated cache; worked example; verify.

## The problem

After ownership is assigned (`data-ownership.md`), a service often still needs data owned
elsewhere. The join is gone. Four patterns, each with a price (Hard Parts ch. 10). Running example:
Wishlist (customer id, item id, date added) must display `item_desc`, owned by Catalog.

## 1. Inter-service communication

Ask the owner over REST, gRPC or messaging. Wishlist sends item ids to Catalog and receives
descriptions. The most common choice and the simplest.

- Latency adds three parts: network (typically 30 to 300 ms), security (endpoint authorisation, 20
  to 400 ms), data (the owner's extra database call instead of a join, 10 to 50 ms). Together up to
  about a second for descriptions alone.
- Coupling is semantic and static. If Catalog is down Wishlist is down, and scaling Wishlist forces
  scaling Catalog.
- Using messaging instead of REST does not remove the wait if the caller needs the answer.

| Advantages | Disadvantages |
|---|---|
| Simplicity | Network, data and security latency |
| No data volume issues | Scalability and throughput issues |
| | No fault tolerance (availability issues) |
| | Requires contracts between services |

## 2. Column schema replication

Copy the needed column (`item_desc`) into the consumer's own table so it can use local queries and
joins. The owner publishes changes (create, remove, description change) over queues, topics or an
event stream; asynchronous is preferred unless immediate transactional sync is required.

- Problems: consistency lag, synchronisation machinery, and governance (a replica sits in a table
  another service could modify even though it does not own the data).
- Benefits: immediate local access, good performance, fault tolerance and scalability.
- The authors caution against it for the Wishlist/Catalog case. Consider it for aggregation or
  reporting, or when other patterns fail for large volumes, high responsiveness needs or high fault
  tolerance needs.

| Advantages | Disadvantages |
|---|---|
| Good data access performance | Data consistency issues |
| No scalability or throughput issues | Data ownership issues |
| No fault tolerance issues | Data synchronisation is required |
| No service dependencies | |

## 3. Replicated caching

Cache models:

- Single in-memory cache: each service has its own unsynchronised cache. Helps one service, no
  sharing.
- Distributed cache: data in an external cache server. Not suitable here: it moves the dependency
  from the service to the cache server (no fault tolerance gain), other services can update the
  shared data (ownership and bounded context broken), and every read is a remote call.
- Replicated cache: each service holds in-memory data, synchronised behind the scenes among
  instances, with no external dependency. Products named in the notes: Hazelcast, Apache Ignite,
  Oracle Coherence (check the vendor supports replicated mode).

Setup: Catalog is the only writer to the cache; Wishlist holds a read-only replica. No inter-service
calls; Wishlist keeps working when Catalog is down; scaling is independent.

Limits to check, because every pattern has a trade-off and if you cannot see it you have not found it:

1. Startup dependency: the owner must be running when the first consumer instance starts. Later
   instances can load from a sibling; once loaded, the owner may come and go.
2. Data volume: feasibility drops quickly above roughly 500 MB, and memory is cache size times the
   number of instances (500 MB across 5 instances is 2.5 GB).
3. Update rate: too-volatile data (inventory counts) cannot be kept in sync; descriptions can.
4. Configuration: instances discover each other by TCP/IP broadcast and lookup; wide ranges slow
   the handshake and dynamic IPs in cloud or container setups make it hard.

| Advantages | Disadvantages |
|---|---|
| Good data access performance | Cloud and containerised configuration can be hard |
| No scalability or throughput issues | Not good for high data volumes |
| Good level of fault tolerance | Not good for high update rates |
| Data remains consistent | Initial service startup dependency |
| Data ownership is preserved | |
| No service dependencies | |

## 4. Data domain (shared schema)

Place the consumer's and owner's tables in one shared schema; the consumer reads with a SQL join.
Choose when inter-service calls fail on reliability or latency, column replication fails on
consistency needs, and a replicated cache fails on volume.

- Benefits: services fully decoupled at runtime, very responsive, high consistency and integrity
  (foreign keys enforceable; views, stored procedures and triggers usable). No contract is needed
  because the table schema is the contract.
- Costs: that same absence of a contract means no abstraction layer, so a schema change can force
  several services to change (a broader bounded context); write-ownership governance; data access
  security, since the consumer can see everything in the domain whereas a contract can restrict
  fields.

| Advantages | Disadvantages |
|---|---|
| Good data access performance | Broader bounded context to manage data changes |
| No scalability or throughput issues | Data ownership governance |
| No fault tolerance issues | Data access security |
| No service dependency | |
| Data remains consistent | |

## Decision procedure

1. Rule out options that cannot apply structurally: the one-schema rule (a service already in one
   data domain cannot join a second), and consolidation across unrelated domains.
2. Profile the access: reads per request, latency budget, availability need, data volume (compare
   against about 500 MB times instances), update rate (static or volatile), required consistency.
3. Pick:
   - Small, mostly static, read-heavy data: replicated cache (preferred when it fits).
   - Strict consistency and integrity, large volumes, and a shared schema is acceptable: data
     domain.
   - Occasional or low-volume reads where the latency is tolerable: inter-service communication.
   - Reporting or aggregation, or large volume with weak consistency needs: column schema
     replication.
4. Record unknowns as risks (new technology, licensing, deployment constraints such as availability
   zone crossings and firewalls), run a proof of concept, confirm with stakeholders, then write the
   ADR.

Method note from the notes: hypothesis-based selection. Hypothesise the likely winner, then hunt for
its negatives; do not stop at the advantages.

## Sizing a replicated cache (worked)

Expert profile data: 900 experts, mostly static (skills, service zones, standard schedule; live
location arrives elsewhere), about 1.3 KB each, so about 1,200 KB total. Maximum instances: 2 for
User Management and 4 for Ticket Assignment at peak. Always size with the maximum expected
instance counts. Total memory is tiny, so volume does not rule it out.

Negatives found: the startup dependency (User Management must be up before the first Assignment
instance; after population, Assignment no longer depends on it, so it is more fault tolerant than
remote calls) and team inexperience (product choice, licensing cost, deployment constraints). The
decision recorded: use an in-memory replicated cache between User Management (sole writer) and
Ticket Assignment, with consequences of the startup ordering and licensing cost.

Eliminations that led there: service consolidation out (different domains); data domain out
(Assignment already connects to the ticketing schema, cannot connect to two, and merging would
regrow a monolithic database); that left inter-service communication versus replicated cache.

## Verify

- Latency: load-test the read path against the stated budget. For pattern 1, add the three latency
  parts and compare.
- Memory: compute cache size times maximum instances and compare with the per-instance memory limit.
- Staleness: measure replication lag against the staleness the business accepts.
- Resilience: stop the owner after warm-up and confirm the consumer keeps working; cold-start a
  consumer without the owner and confirm the documented behaviour (it waits).
- Ownership: confirm the consumer's replica or cache is read-only by configuration and that no
  consumer credentials can write the owner's tables.
- Security: for a data domain, list the columns each consuming service can see and confirm that is
  acceptable.
