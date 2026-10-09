# Dataflow modes: database, service call, workflow, message

Use this file when deciding how data moves between processes and what each path demands of encoding and compatibility: sharing data through a database, calling a service (REST or RPC), running a multi-step workflow with durable execution, or exchanging messages through a broker or actors. The format-level rules are in `encoding-and-schema-evolution.md`; API design and gateways are in `arch-api-design`; broker and log internals are in `arch-data-pipelines`.

Contents
1. Summary table
2. Through databases
3. Through services (REST and RPC)
4. Load balancing and service discovery
5. Durable execution and workflows
6. Message brokers and actors
7. Choosing a mode
8. Verification

Sources: DDIA 2e ch. 5 (modes of dataflow); ch. 1 for microservice context.

---

## 1. Summary table

| Mode | Who encodes / decodes | Compatibility demand | Main hazard |
|---|---|---|---|
| Database | Writer encodes, later reader decodes (possibly years later, possibly the same app) | Backward always (message to your future self); forward too during rolling upgrades | Data outlives code; unknown fields dropped on read-modify-write |
| Service call (REST/RPC) | Request encoded by client, response by server | Request backward + response forward when servers upgrade first | Network is not a function call; timeouts and duplicates; clients you cannot upgrade |
| Workflow / durable execution | Engine logs calls and results; code replays | Workflow code versions; external APIs idempotent | Replay requires deterministic code and stable call order |
| Message / event | Sender encodes, recipient decodes later | Both directions; brokers are encoding-agnostic | Consumers that republish drop unknown fields; retained logs hold old formats forever |

## 2. Through databases

- Single process: storing is a message to your future self, so backward compatibility is needed. Multiple processes or instances during a rolling upgrade: forward compatibility too, since old code may read what new code wrote.
- Data outlives code. Old rows stay in their original encoding unless rewritten. LSM engines rewrite into the latest format during compaction; relational databases allow cheap changes such as adding a nullable column with default null (readers fill nulls for missing columns), which gives the appearance of a single schema.
- Complex changes (single-valued to multi-valued, moving data to a separate table) need an application-level rewrite; cross-version compatibility there is an open research problem.
- Warning: preserve unknown fields when read-modify-write goes through an ORM or model object.
- Archival storage and snapshots: write the dump in the latest schema, using Avro container files or Parquet (columnar, analytics-friendly), immutable once written.

## 3. Through services (REST and RPC)

- A service exposes an application-specific API limited by business logic, unlike a database that accepts arbitrary queries; this gives encapsulation and fine-grained restriction. The microservice goal is independent deployment and evolution, one owning team, frequent releases without cross-team coordination, so old and new clients and servers coexist and encodings must be compatible.
- Web services use HTTP. Three contexts: client apps over the public internet, service-to-service in one organisation, cross-organisation (payments, OAuth).
- REST: simple formats, URLs identify resources, uses HTTP features (cache control, auth, content negotiation). IDLs: OpenAPI/Swagger (JSON or YAML) and Protocol Buffers (gRPC). Two workflows: code-first with a generated IDL (FastAPI) or IDL-first with generated server scaffolding and client SDKs (gRPC). IDL tooling gives docs, compatibility verification and test UIs.

**Why "location transparency" RPC is flawed** (a network call is not a function call):
1. Unpredictable: request or response can be lost, the remote side can be slow or down, so failures must be anticipated (retries).
2. A timeout adds an outcome: you do not know whether the request was processed.
3. Retries may duplicate the action unless the protocol is idempotent or deduplicates (idempotency keys).
4. Latency varies wildly, from sub-millisecond to seconds.
5. Parameters must be encoded to bytes; no pointers; hard for large or mutable objects.
6. Cross-language type mismatches (JavaScript numbers above 2^53).
Legacy technologies that suffered from pretending otherwise: EJB, RMI (Java only), DCOM (Microsoft only), CORBA, SOAP/WS-*. Do not make remote services look like local objects; REST's appeal is treating state transfer as distinct from function calls.

**Evolution.** Simplifying assumption: servers upgrade first, clients second, so requests need backward compatibility and responses forward compatibility. gRPC and Avro RPC inherit their format's rules. REST over JSON treats adding optional request parameters and adding new response fields as compatible, so clients must ignore unknown response fields.

**Cross-organisation APIs.** The provider cannot force clients to upgrade, so compatibility must last a very long time, and breaking changes mean maintaining multiple API versions side by side. There is no consensus on versioning: version in the URL, version in the Accept header, or a server-side version stored per API key and changed through an admin interface (Stripe style). Details on versioning policy are in `arch-api-design`.

## 4. Load balancing and service discovery

| Option | How | Pros | Cons and when |
|---|---|---|---|
| Hardware load balancer | Appliance in the datacentre; one host:port; routes and detects failures | Simple for clients | Special hardware |
| Software LB (NGINX, HAProxy) | Same on a commodity machine | Simple deployments are best served here | Extra hop |
| DNS | Multiple IPs per name | Simple, ubiquitous | Caching and slow propagation give stale IPs when servers churn |
| Service discovery (etcd, ZooKeeper) | Instances register host, port and metadata (shard ownership, datacentre) and heartbeat; clients query the registry then connect directly | Dynamic environments; metadata enables smarter client-side balancing | One more system to run |
| Service mesh (Istio, Linkerd) | Sidecar or in-process LB on both client and server; local connections | mTLS handled by the mesh; observability of who calls whom | Complex; for highly dynamic Kubernetes-style environments |

Specialised infrastructure (databases, brokers) may need its own balancing.

## 5. Durable execution and workflows

A workflow is a graph of tasks (activities or durable functions), for example fraud check, debit card, deposit to bank, defined in code, a DSL or markup (BPEL). The engine is an orchestrator (schedules tasks; triggers by time, external service or human) plus an executor (runs tasks), and decides placement, failure handling and parallelism limits.

Families: ETL and data orchestrators (Airflow, Dagster, Prefect); graphical BPMN for non-engineers (Camunda, Orkes); durable execution (Temporal, Restate).

**Durable execution** gives exactly-once-like semantics for multi-service workflows where a database transaction cannot span services and third-party gateways. On failure the framework re-executes the task but skips RPCs and state changes that already succeeded, returning the logged results of earlier calls, by replaying from a durable record like a write-ahead log.

Constraints:
- External services still need idempotent APIs; pass unique IDs to prevent duplicate execution.
- Replay expects the same calls in the same order, so editing workflow code is brittle (reordering calls gives undefined behaviour). Safer: deploy changed workflow code as a new version; in-flight executions keep the old version and new ones use the new code.
- Code must be deterministic: no raw random numbers or system clock; use the framework's replacements. Static analysis exists for this (Temporal Workflow Check).

Choose it when a business process spans several services and must complete or compensate despite crashes. Plain RPC with retries plus idempotency keys is enough when steps are few and idempotent. Broker-based choreography suits cases where decoupling matters more than central control (this comparison is inferred; the saga and orchestration-vs-choreography trade-offs are in `arch-distributed-workflows`).

## 6. Message brokers and actors

An event or message is sent without waiting and goes via a broker (message queue, event broker, message-oriented middleware). Advantages over direct RPC: buffering when the recipient is down or overloaded; redelivery after a consumer crash; no service discovery; one message to many recipients; decoupling of sender and recipient. Communication is asynchronous; a synchronous feel is possible with a reply on a separate channel.

Brokers named: TIBCO, IBM WebSphere, webMethods (legacy commercial); RabbitMQ, ActiveMQ, HornetQ, NATS, Redpanda, Kafka (open source); Kinesis, Azure Service Bus, Google Pub/Sub (cloud). Two patterns: a queue (one of many consumers gets each message) and a topic (all subscribers get it).

Brokers are encoding-agnostic (bytes plus metadata). Use protobuf, Avro or JSON with a schema registry that stores all valid schema versions and checks compatibility; AsyncAPI is the messaging counterpart to OpenAPI. Many brokers delete after consumption; some retain indefinitely (needed for event sourcing), which means old formats must stay readable for as long as the log is kept. Consumers that republish messages must preserve unknown fields.

**Distributed actors** (Akka, Orleans, Erlang/OTP): an actor encapsulates state and handles one asynchronous message at a time, with no threads or locks, and delivery is not guaranteed. The same message passing works locally or remotely, with transparent encoding. Location transparency works better here than in RPC because the model already assumes message loss. It is effectively broker plus actor model in one. Rolling upgrades still need forward and backward compatible message encodings.

## 7. Choosing a mode

| Need | Mode |
|---|---|
| Share durable state among components | Database (single owner per table; see `arch-decomposition` for shared-database problems) |
| Ask another service to do or return something now | Service call with idempotency keys and timeouts |
| Multi-service business process that must finish or compensate | Durable execution, or sagas (`arch-distributed-workflows`) |
| Notify many parties, absorb bursts, decouple availability | Broker with topics |
| Spread work among consumers | Broker with a queue |
| Event history is the source of truth | Retaining log plus event-sourcing model (`data-models.md`) |

## 8. Verification

- For each arrow in an architecture diagram, label the mode and the compatibility direction required; any arrow without a direction is unreviewed.
- For each RPC call site: timeout set, retry policy defined, operation idempotent or carrying an idempotency key. Test by injecting a timeout after the server has processed the request and confirm no duplicate effect (inferred test).
- For each consumer that republishes: the unknown-field round-trip test from `encoding-and-schema-evolution.md`.
- For each workflow: no clock, random or network calls outside the framework's deterministic APIs; in-flight execution of the old version still completes after deploying the new one (rehearse it).
- For each topic or log with long retention: a schema registry entry and a compatibility mode, and a replay test from the oldest retained message.
