# Batch processing

Read this when designing, reviewing or debugging a batch job or a multi-job workflow: choosing engine and storage, scheduling, retries, joins and grouping, getting results to a serving system.

Contents: 1 The baseline: Unix pipelines and the working set; 2 Storage: file system vs object store; 3 Orchestration and scheduling; 4 Workflows; 5 Fault handling; 6 Processing models and the shuffle; 7 Joins and grouping; 8 Query languages, warehouses and frameworks; 9 DataFrames; 10 Use cases; 11 Serving derived data; 12 Decision procedures; 13 Warning signs; 14 Verify; 15 Dated material.

All claims are from DDIA 2e ch. 11 unless marked "adaptation" (my addition for current practice) or "(inferred)" (marked inferred in the source notes).

## 1. The baseline: Unix pipelines and the working set

A pipeline such as extract-a-field, sort, count-duplicates, sort-by-count, take-top-5 answers "most popular pages" for a log file in seconds. Compare with a small custom program that keeps a hash table in memory. The choice depends on the working set: the memory needed for random access, which is the number of distinct keys, not the number of records.

| Approach | Works when | Behaviour as data grows |
|---|---|---|
| In-memory hash table | distinct keys plus counters fit in memory | fastest and simplest |
| Sort-based (GNU sort) | working set larger than RAM | sorts in-memory chunks, spills sorted segments to disk, merges them (the same idea as LSM storage, sequential I/O); uses several cores; limit becomes disk read rate |

Lessons: a few standard tools handle gigabyte-scale analysis in seconds; reach for a cluster only when data does not fit a machine (inferred from the cited "command-line tools can be faster than your Hadoop cluster" point). Sorting is the foundational batch primitive: it makes equal keys adjacent, so aggregation needs constant state per key.

## 2. Storage: file system vs object store

| Aspect | Distributed file system (HDFS, GlusterFS, CephFS, JuiceFS) | Object store (S3, GCS, Azure Blob, MinIO, R2) |
|---|---|---|
| Model | files split into large blocks | key to immutable blob in a bucket; get and put; no file handles or seek |
| Metadata | name node or metadata service | flat key space; "directories" are a key-prefix convention; no empty directories (use a marker object) |
| Mutation | in place or append | immutable objects; update means full rewrite (append only on a few products) |
| Rename | atomic | not atomic: copy then delete; renaming a "directory" renames every object |
| Locks, links | yes (hard links, symlinks, locking) | generally none |
| Compute locality | tasks can run on the node holding a block | storage and compute decoupled: more network traffic, but each scales independently |

Notes:
- Object stores and open table formats offer time travel, so a bad run can be undone by switching back to the earlier output; a read/write database cannot do this, because rolling back code does not repair data the buggy code wrote.
- Replication: copies on several machines or erasure coding for lower overhead. Shared-nothing commodity hardware, unlike shared-disk appliances.
- The S3 API is a de facto interface that other products imitate. File-system lookalikes over object stores (FUSE) exist, but performance and consistency semantics differ: verify behaviour before adopting.
- Default today: object store for decoupled compute and cheap scale. Choose a distributed file system when you must run on premises with data-local compute or need POSIX semantics such as atomic rename and locks (inferred from the table).
- Never assume rename is atomic on an object store. Publishing a finished output needs a commit protocol or a table format that has atomic commits (inferred from the non-atomic rename). Adaptation: write all output under a unique run prefix, then publish by writing a single small manifest or "current version" pointer last; readers consult only the pointer.

## 3. Orchestration and scheduling

A job request carries: task count, CPU, memory and disk per task, job ID, credentials, input/output parameters, hardware needs such as GPUs, and the executable location. The parts:

- Task executor on each node (YARN NodeManager, Kubernetes kubelet): starts tasks, heartbeats, reports status, isolates with cgroups.
- Resource manager: global cluster state. It is centralised, so it is a scalability and availability concern; its state lives in a coordination store (ZooKeeper for YARN, etcd for Kubernetes).
- Scheduler: decides which task runs on which node. Application-specific sub-schedulers exist (YARN ApplicationMasters, Kubernetes operators).

Allocation trade-offs, from the example of two jobs each wanting 100 of 160 cores:

| Strategy | Problem |
|---|---|
| Split evenly | both finish later; partial progress |
| Gang scheduling (all 100 at once) | idle cores while reserving; deadlock when several jobs reserve; starvation if cores never free |
| Wait for resources | others grab them; starvation |
| Preempt running tasks | wasted work |
| Hold back for a hypothetical future job | idle capacity |

Optimal scheduling is NP-hard, so schedulers use heuristics: FIFO, dominant resource fairness, priority queues, quotas, bin packing. Practical rule: give each job realistic resource requests and a priority; do not gang-schedule many jobs against each other.

## 4. Workflows

Use a workflow when one job's output feeds several teams' jobs, when you move between tools (Spark to object store to a SQL engine), or when a later stage needs a different sharding key. Batch workflows pass big datasets and normally make no RPCs (this differs from durable-execution workflows).

- Jobs usually write to the file system or object store and the next job reads it; they run at different times. The scheduler starts a job with several inputs only when all upstream jobs have succeeded.
- Workflow schedulers (Airflow, Dagster, Prefect) manage dependencies, retries, failed-job marking and have operators for databases and engines. Per-job schedulers (YARN, Spark's own) do not manage whole workflows. Workflows of 50 to 100 jobs are common.

## 5. Fault handling

- In long jobs with many tasks, a task failure is almost certain, and preemption is deliberate on spot instances. Batch suits spot or preemptible capacity because output can be regenerated and nothing is time critical: cheaper and higher utilisation.
- Recovery: delete the failed task's partial output and rerun it elsewhere. Keep tasks independent so the unit of retry is a task, not the job.

| Engine | Intermediate data strategy | Trade-off |
|---|---|---|
| MapReduce | write all intermediates to the replicated file system, readers wait for the writer to finish | robust under preemption; heavy writes, slow |
| Spark | keep intermediates in memory (spill to local disk), write only the final result; remember how data was computed (lineage) and recompute lost pieces | fast; recomputation cost on failure |
| Flink | periodic checkpoints of task state | checkpoint overhead; restart from snapshot |

## 6. Processing models and the shuffle

MapReduce (obsolete, but its structure explains the rest): input format parses files into records (Parquet is columnar, Avro row-based); a mapper runs per record and emits zero or more key-value pairs; the framework sorts by key; a reducer runs once per key with an iterator over all values. A second sort (for example ranking by count) is a second job. Weaknesses: joins written by hand, file I/O between jobs prevents pipelining, a new process per task, sort always performed.

Dataflow engines (Spark, Flink) treat a whole workflow as one job with flexible operators. Advantages: sort only where needed; fuse non-reshuffling operators such as map and filter into one task; the scheduler sees dependencies and can co-locate producer and consumer; intermediates stay in memory or local disk; operators start as soon as input is ready; processes are reused. Usually much faster for the same computation.

The shuffle is a distributed sort-and-partition (it has nothing to do with randomising). Mechanics in Hadoop MapReduce:
1. One map task per input shard; the author sets the number of reduce tasks.
2. Each mapper writes one local output file per reducer, chosen by hash of key modulo reducer count, so equal keys reach the same reducer.
3. While writing, the mapper sorts each file (in-memory structure, spilled sorted segments, merge).
4. When a mapper finishes, reducers fetch their files and merge-sort them so equal keys are adjacent regardless of source.
5. The reducer runs once per key; its output is one file per reducer, a shard of the output dataset.

Modern warehouses keep the shuffle in memory or in external sorting services that also replicate shuffled data. The same shuffle underlies joins and aggregations in Spark, Flink, Daft, Dataflow and BigQuery.

## 7. Joins and grouping

Sort-merge join of a fact table (events with a user ID) with a dimension table (users):
1. One mapper emits (userId, pageURL) from events; another emits (userId, dateOfBirth) from users.
2. Shuffle on userId. Use a secondary sort so the user record arrives first and that user's events follow in timestamp order.
3. The reducer keeps the date of birth in a local variable and emits (URL, dateOfBirth) per event. It holds one user record and makes no network calls.
4. A second job shuffles by URL and counts per age group.

Principle: the shuffle collocates all records with the same key, turning joins and aggregations into local computation. Cost (inferred; not discussed in the source): data crosses the network and is sorted, and a very popular key makes one reducer a straggler. When a job is slow, look at partition skew before adding machines.

## 8. Query languages, warehouses and frameworks

SQL is the common language: less code, usable interactively by analysts, optimisable. The engine turns SQL into a syntax tree and physical operators; cost-based optimisers (Hive, Trino, Spark, Flink) choose join algorithms and join order. Cloud warehouses and batch frameworks are converging: frameworks gained SQL, columnar formats and vectorised execution; warehouses gained shuffle, scheduling, fault tolerance and DataFrame APIs.

| Choose | When |
|---|---|
| Warehouse or SQL engine | the work is relational and SQL-expressible; convenience; existing integration |
| Spark, Flink or Ray | iterative graph algorithms (PageRank), complex ML, nonrelational or multimodal data (images, video, audio), row-by-row computation that columnar engines handle poorly, or cost at large scale (warehouses cost more) |

The decision is usually cost, convenience, ease of implementation and availability. Large organisations run several; small ones should run one.

## 9. DataFrames

A DataFrame is a table with typed columns manipulated through relational-operator functions (R, Pandas; distributed versions in Spark, Flink, Daft). Pitfalls when moving local code to a distributed engine: local DataFrames are indexed and ordered, distributed ones generally are not; Pandas executes eagerly while Spark builds and optimises a plan lazily; Apache Arrow is the shared in-memory columnar model. Do not port Pandas code assuming index or order semantics survive.

## 10. Use cases

Batch fits when there is a lot of data and freshness does not matter: reconciliation and inventory, demand forecasting, recommendation training, bank clearing networks that are mostly batch.

| Use case | Notes |
|---|---|
| ETL or ELT | embarrassingly parallel filter and project; schedulers retry then mark failure; easy to debug and rerun; pipelines and analytical queries increasingly share engines (SparkSQL, Trino, DuckDB) |
| Analytics | lakehouse: query engine over files in an object store, a table format (Iceberg) and a catalog. Pre-aggregation (rollups, cubes, marts, scheduled; may feed Druid or Pinot) vs ad hoc queries where latency matters because analysts iterate |
| Machine learning | feature engineering, training (data in, weights out), batch inference; graph processing with the bulk-synchronous-parallel (Pregel) model, which repeats vertex-to-neighbour propagation until convergence; LLM data preparation (extract text, dedupe, filter, tokenise or embed) with Ray, Kubeflow, Flyte |

## 11. Serving derived data back to production systems

Anti-pattern: each task writes records to the production database through its client. Three reasons it fails:
1. A network request per record is orders of magnitude slower than batch throughput, even with client batching.
2. Many parallel tasks at batch speed overwhelm the database and hurt live queries.
3. External writes break all-or-nothing: a half-finished job's output is visible, and retried tasks duplicate writes.

| Option | How | Pros | Remaining issues |
|---|---|---|---|
| Push through a log (Kafka) | search and OLAP stores (Elasticsearch, Pinot, Druid, ClickHouse) ingest from the log | sequential writes suit bulk loads; buffer and throttle protect production; multiple consumers; clean security boundary | still needs a "job done" signal; consumers must keep the data invisible until it arrives (like uncommitted data under read committed) |
| Build a new database in the job and bulk-load it | for example RocksDB SST ingestion, TiDB Lightning, Pinot import | very fast; atomic switch between dataset versions | hard to update incrementally; hybrid (bulk bootstrap plus incremental updates) is common |

## 12. Decision procedures

- Single machine or cluster: if the working set fits one machine, use Unix tools or a local engine (inferred).
- Aggregation: hash table if distinct keys fit memory; sort-based otherwise.
- Engine: replace MapReduce with a dataflow engine unless there is a legacy reason; relational work with a SQL engine; non-relational, iterative or ML work with Spark, Flink or Ray.
- Storage: object store by default; distributed file system for data-local compute or POSIX semantics.
- Intermediates: replicated file system (robust, slow) vs memory with lineage (fast, recompute) vs checkpoints.
- Cost: run on spot capacity since tasks are restartable.
- Delivery: never record by record into the serving database; use a log buffer plus completion signal, or build-and-swap bulk load.
- Multi-job pipelines: a workflow scheduler with each job depending on the success of all its inputs.

## 13. Warning signs

- A batch job calling an OLTP database per record, or running highly parallel against production.
- Output visible before the job finishes, or duplicates after task retries.
- Assuming object-store directories or atomic rename.
- Pandas code moved to Spark assuming index or order.
- A sort stage and a replicated file-system write between every stage (MapReduce legacy) causing slowness.
- Gang scheduling many jobs against each other.

## 14. Verify

- Rerun the job on the same input: output is identical (inferred).
- Compare this run's output with the previous run's: row counts, null rates, distribution drift. The book suggests monitoring jobs that do this because inputs are immutable and can feed several jobs.
- Inject a failure (kill a task, simulate a spot preemption): the output has no duplicates and no missing shards.
- Downstream consumers read only published (completed) versions: try reading mid-run and show it returns the old version or nothing, never partial data.
- Partition balance: the hash partitioning yields shards of comparable size; report the largest-to-median ratio (inferred).

## 15. Dated material

Hadoop and MapReduce specifics, HDFS names and Oozie-era scheduling are dated. What survives: immutable input and derived output, sort and shuffle as the grouping primitive, sort-merge join via key collocation, task-granular retry, lineage versus materialisation versus checkpoint, decoupled storage and compute, and the batch-to-serving handoff patterns.
