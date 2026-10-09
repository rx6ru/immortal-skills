# Messaging systems and log-based brokers

Read this when choosing a transport between producers and consumers (queue, log, direct call), sizing partitions and retention, handling slow consumers or poison messages, or reviewing consumer code for ordering and duplicate problems.

Contents: 1 The two questions every messaging design must answer; 2 Delivery mechanisms; 3 Brokers vs databases; 4 Multiple consumers; 5 Acknowledgement, redelivery, reordering; 6 Poison messages and dead letter queues; 7 Log-based brokers; 8 Offsets, retention, lag, replay; 9 Choosing; 10 Sizing and operating checklist; 11 Warning signs; 12 Verify.

Source: DDIA 2e ch. 12 unless marked.

## 1. The two questions every messaging design must answer

1. Producers faster than consumers: drop messages, buffer them in a queue, or apply backpressure (block the producer)? Unix pipes and TCP use backpressure. If queueing, decide what happens when the queue outgrows memory: crash, spill to disk (and how disk affects performance), what when disk is full?
2. A node crashes or goes offline: are messages lost? Durability costs disk writes and replication; tolerating loss buys throughput and latency.

Loss tolerance depends on the application. Periodic sensor samples can tolerate loss (though a large silent drop can go unnoticed). Counting events cannot: every loss is a wrong counter. Write the loss policy down per stream before choosing technology.

Batch gets a strong guarantee for free (retry failed tasks, discard partial output, as if nothing failed). Streaming must recreate it; see `exactly-once-and-idempotency.md`.

## 2. Delivery mechanisms

| Mechanism | Examples | Strengths | Weaknesses |
|---|---|---|---|
| Direct, no broker | UDP multicast, ZeroMQ, StatsD over UDP, webhooks, direct HTTP or RPC | lowest latency; no intermediary | the application must handle loss; assumes both sides are always online; an offline consumer misses messages; a crashed producer loses its retry buffer |
| AMQP or JMS style broker | RabbitMQ, ActiveMQ, IBM MQ, Azure Service Bus, Qpid | centralised durability; clients come and go; per-message ack and load balancing; can join XA transactions | messages are deleted after ack (no replay; new consumers see only future messages); assumes short queues, so slow consumers hurt; redelivery reorders; subscription by pattern only, no queries |
| Log-based broker | Kafka, Kinesis Streams, Pulsar, Redpanda | durable, replayable, ordered per partition, trivial fan-out, very high throughput through partitioning, consumer progress is just an offset | parallelism capped at partition count; one slow message blocks its partition; ordering only per partition |

## 3. Brokers vs databases

Databases keep data until it is deleted; many brokers delete on delivery. Brokers assume a small working set. Databases have indexes and queries; brokers match topic patterns only. A database query is a point-in-time snapshot and does not tell you about later changes; a broker pushes new messages but cannot query or update old ones. A database used as a queue is possible but hard to tune. A log-based broker sits in between: it keeps messages durably like a database and notifies like a broker.

## 4. Multiple consumers

- Load balancing: each message goes to one consumer (JMS shared subscription, several AMQP clients on one queue). Use when messages are expensive to process.
- Fan-out: each message goes to all consumers (JMS topic subscription, AMQP exchange bindings).
- Both at once: Kafka consumer groups. Within a group, partitions are divided among members; across groups, every group sees every message.

## 5. Acknowledgement, redelivery, reordering

The consumer acks when finished. No ack (closed connection, timeout) means redelivery to another consumer. A lost ack means a duplicate, so consumers need idempotence or an atomic commit.

Load balancing plus redelivery reorders. Example: consumer 2 crashes while handling m3; m3 is redelivered to consumer 1 after m4, so consumer 1 sees m4, m3, m5. Brokers that promise order (JMS, AMQP) cannot prevent this. Remedies: one queue per consumer (no load balancing), or make sure messages are independent. This matters whenever messages have causal dependencies.

## 6. Poison messages and dead letter queues

A malformed message (a JSON document missing a required key) crashes every consumer that receives it, is never acked and is redelivered forever. With strict ordering it blocks the stream; without ordering it wastes resources.

Handling:
1. After N failed deliveries, move the message to a dead letter queue (DLQ).
2. Monitor the DLQ: any message in it is an error.
3. An operator decides: drop, repair and republish, or fix the consumer.

Supported by queue systems, Pulsar and Kafka Streams. Adaptation: record the failure reason and original coordinates (topic, partition, offset) with each dead-lettered message so repair and republish is possible.

## 7. Log-based brokers

A producer appends to the end of a log; a consumer reads sequentially and waits for new appends, like `tail -f`. To scale, shard the log into partitions across machines; a topic is a group of partitions. Each message has a monotonically increasing offset within its partition. Order is total within a partition and undefined across partitions. Replicate partitions for fault tolerance.

Ordering requirement: route all events that must stay ordered to the same partition with a partition key (for example user ID or account ID).

Downsides:
- Maximum consumers in a group equals the partition count. More parallelism needs more partitions. Single-threaded processing per partition is preferred; a thread pool inside a partition complicates offset tracking.
- One slow message blocks the partition (head-of-line blocking).
- Kafka now also supports JMS-style groups sharing a partition, blurring the line.

## 8. Offsets, retention, lag, replay

- Progress is one number per partition per consumer group, like a replication log sequence number with the broker as leader and the consumer as follower. Less bookkeeping than per-message acks, hence higher throughput.
- On consumer failure another node takes the partitions and resumes from the last recorded offset. Messages processed after that offset are processed again: at-least-once.
- Retention: the log is split into segments; old segments are deleted or archived, so the log is a ring buffer on disk. Back-of-envelope from the book: a 20 TB disk written at 250 MB/s sequentially fills in about 22 hours at full speed, so real deployments retain days to weeks. A consumer whose offset falls off retention misses messages. Tiered storage and brokers built on object stores (Redpanda tiered storage, WarpStream, Confluent Freight, Bufstream) extend retention; data in Iceberg format lets batch or warehouse queries read the log directly.
- Slow consumers: the log is a large fixed-size buffer. Monitor consumer lag (distance behind the head) and alert before it nears retention. Only the lagging consumer is affected; others continue. A dead consumer costs nothing but its offset, unlike an abandoned queue in a traditional broker, which accumulates messages.
- Replay: reading does not change the log, and the consumer controls its offset. Start a copy of a job at yesterday's offset, write to a different output, change the code, compare. This gives batch-like reprocessing and easier recovery from bugs, and lets you attach experimental consumers to a production log safely.

## 9. Choosing

| Situation | Choose |
|---|---|
| Expensive per-message processing, want per-message parallelism and freely added consumers, order unimportant | AMQP or JMS style broker (work queue) |
| High throughput, fast messages, order matters, need replay, several independent consumers or derived-data pipelines | log-based broker |
| Strict ordering for an entity | log-based, partition key = entity ID |
| Loss acceptable, latency paramount, consumers always online | direct messaging (UDP multicast and similar) |
| Actors or in-process concurrency | an actor framework is a concurrency mechanism (ephemeral one-to-one messages, arbitrary or cyclic communication, usually no delivery guarantee on crash), not data management; stream processing is durable, multi-subscriber and acyclic |

## 10. Sizing and operating checklist

- Partition count sets maximum consumer parallelism. Choose with future growth in mind (inferred in the notes). Adaptation: changing the count later changes the key-to-partition mapping, which breaks per-key ordering across the change, so leave headroom.
- Retention longer than the longest plausible consumer outage plus time to detect it (adaptation of the book's lag-versus-retention point); compute the fill time from write rate as in the book's example.
- Alerts: consumer lag and DLQ depth (from the book); broker disk use is an adaptation.
- Poison-message policy: retry count, DLQ, owner.
- Producer side: partition key chosen so ordering-sensitive events share a partition and load is spread (adaptation: a hot key defeats partitioning).
- Compacted topics only where every message carries a key and the full new value (see `derived-data-sync.md`).

## 11. Warning signs

- Ack-based load balancing where order matters.
- A poison message looping; no DLQ, or a DLQ nobody watches.
- Consumers whose lag is approaching the retention window, and no lag alert.
- A queue used as a database (querying, long retention, updates).
- Parallelism needs exceeding partition count discovered in production.
- An abandoned queue accumulating messages in a traditional broker.

## 12. Verify

- Kill a consumer mid-batch and restart: show the sink ends with no duplicates and no gaps.
- Publish a deliberately malformed message in a test environment: show it lands in the DLQ after N tries and the stream continues.
- Two events for the same entity published in sequence: show a consumer sees them in order (same partition) even with several consumer instances.
- Stop a consumer for longer than retention in a test: show lag alert fires before data is lost (or document that it does not).
- Replay from an old offset into a scratch output: show the result matches the live output for the same range.
