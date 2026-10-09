# Analytical storage: warehouses, lakes, columnar formats

Use this file when designing or reviewing storage for analytics: choosing a warehouse or lake layout, picking file and table formats, deciding row vs column storage, sort keys, compression, materialised views and cubes, and understanding why analytic queries are fast or slow.

Contents
1. OLTP engines vs analytic engines
2. Cloud warehouses and the decomposed lake stack
3. Column-oriented storage
4. Compression, bitmaps and sort order
5. Writing to column stores
6. Query execution: compilation vs vectorisation
7. Materialised views and data cubes
8. Choosing and verifying

Sources: DDIA 2e ch. 4 (analytics half), ch. 1 (warehouse, lake), ch. 3 (star schemas).

---

## 1. OLTP engines vs analytic engines

Warehouses are usually relational and SQL fits analytics, so they look like OLTP databases from outside while the internals differ; vendors increasingly specialise. HTAP products (SQL Server, SAP HANA, SingleStore) are increasingly two separate storage and query engines behind one SQL interface. For the workload definitions and when HTAP is warranted, see `data-system-tradeoffs.md`. For the logical schema (fact and dimension tables, star, snowflake, one big table), see `data-models.md`.

## 2. Cloud warehouses and the decomposed lake stack

Cloud warehouses (BigQuery, Redshift, Snowflake) differ from on-premise ones (Teradata, Vertica, SAP HANA) by decoupling compute from storage: data lives on object storage, storage and query compute scale independently, the service is elastic and serverless, and ingestion integrates better (Dataflow, Kinesis are named).

Open-source warehouses (Hive, Trino, Spark) have been broken into components over a data lake on object storage:

| Component | Role | Examples |
|---|---|---|
| Query engine | Parse SQL, optimise, execute a distributed plan | Trino, DataFusion, Presto (execution maybe via Spark or Flink) |
| Storage format | How rows are encoded as bytes in a file, usable by any app on the lake | Parquet, ORC, Lance, Nimble |
| Table format | Which files make up a table, plus schema; adds inserts and deletes over immutable files, time travel, garbage collection, even transactions | Apache Iceberg, Delta |
| Data catalog | Which tables make up a database; create, rename, drop; standalone service with REST API; discovery and governance | Polaris, Unity Catalog, Iceberg catalog |

Why it matters: Parquet-style files are immutable, so mutation and transactions come from the table-format layer. When someone says "we have a lakehouse", ask which of these four layers they run and who owns each.

Choose a managed cloud warehouse when load is bursty and the team lacks operations skill; choose lake components when multiple engines or ML tools must read the same files, or lock-in is a concern (adaptation of the cloud-vs-self-host factors in `data-system-tradeoffs.md`).

## 3. Column-oriented storage

Fact tables are often 100+ columns wide, while a typical query touches only 4 or 5 (the book's example reads three of them). Row storage must load whole rows, parse and filter. Column storage keeps each column's values together so the query reads only the columns it needs.

- Row identity is implicit: the k-th entry of every column belongs to row k, so all columns must keep the same row order.
- Real engines split a table into blocks of thousands to millions of rows (often by timestamp range) and store columns separately within each block, so time-range queries skip blocks.
- Used by Snowflake, DuckDB, Pinot, Druid, Parquet, ORC, Lance, Nimble, Arrow, Pandas/NumPy, InfluxDB IOx, TimescaleDB. Parquet handles nested documents by shredding/striping (Dremel).
- Do not confuse with the wide-column data model (Bigtable, HBase, Accumulo, Cassandra): that is row-oriented, with all values of a row stored together.

Do not use columnar storage as the primary store for point reads and frequent single-row updates; that is OLTP work.

## 4. Compression, bitmaps and sort order

- Repetition in a column compresses well, cutting disk and network I/O.
- **Bitmap encoding**: when a column has few distinct values relative to row count (100,000 products against billions of rows), keep one bitmap per distinct value, one bit per row. Sparse bitmaps are run-length encoded. Roaring bitmaps choose per chunk between plain and run-length form, whichever is smaller.
- Bitmap query algebra: `product_sk IN (31, 68, 69)` is an OR of three bitmaps; `product_sk = 30 AND store_sk = 3` is an AND of two. Valid because row order is identical across columns. Also usable for graph questions (followed by X AND following Y).
- **Sort order**: sort whole rows (never each column independently, which would break row reconstruction) by chosen sort keys picked from common queries, for instance date first for time-range queries and product second. Benefits: range queries scan only relevant rows; the first sort key produces long runs, so run-length encoding compresses it to kilobytes even for billions of rows; the benefit decays for the second and third keys.

Apply: choose sort keys from the top few real queries, put the most commonly range-filtered column first, and measure bytes scanned before and after.

## 5. Writing to column stores

Inserting a row into the middle of sorted, compressed columns means rewriting every column after the insertion point. Bulk loads amortise this. Solution: be log-structured. Writes go first to a row-oriented, sorted in-memory store; when enough accumulate they are merged with the column files and written as new immutable files in bulk (which suits object storage). Queries read both the disk columns and recent in-memory writes and combine them, so inserts, updates and deletes are visible immediately. Snowflake, Vertica, Pinot and Druid do this.

Implication for design: trickle inserts of single rows into a plain Parquet table are a smell. Batch them, or use an engine or table format that buffers (adaptation).

## 6. Query execution: compilation vs vectorisation

A naive row-at-a-time interpreter, checking the query structure per row, is too slow for scans over millions of rows; CPU time matters as well as I/O.

| Approach | How | Notes |
|---|---|---|
| Query compilation | Generate code for the specific query, compile to machine code (for example with LLVM), run over in-memory columns | Per-query code, tight loops |
| Vectorised processing | Interpreted, but with a fixed set of predefined operators that each process a batch of column values (an equality operator takes a column and a constant and returns a bitmap; AND combines bitmaps) | SIMD-friendly, no compile step |

Both appear in practice and both exploit sequential memory access (fewer cache misses), tight inner loops without function calls, parallelism (threads, SIMD) and operating directly on compressed data. Terminology trap: "vector" in vectorised processing means a batch of values; in embeddings it means a float array.

## 7. Materialised views and data cubes

- A virtual view is a stored query expanded at read time. A **materialised view** is an actual copy of the result on disk and must be updated when underlying data changes (some databases automate this; Materialize specialises). Cost: more work on writes; benefit: faster repeated reads. Maintenance is revisited in the stream-processing material (`arch-data-pipelines`).
- A **data cube** (OLAP cube) is a grid of aggregates (SUM, COUNT) grouped by dimension combinations (date by product; collapse along an axis to roll up). With five dimensions it is a hypercube. Certain queries become nearly free.
- The catch: it is inflexible. You cannot answer questions about attributes not in the cube's dimensions (share of sales from items priced over $100 if price is not a dimension). Rule: keep as much raw data as possible and use cubes only as a performance boost for known hot queries.

## 8. Choosing and verifying

Decision list:
1. Is the workload scans and aggregates over history? Use a column-oriented engine or format; do not run it on the OLTP primary.
2. Is data volume small (single-node scale)? An embedded analytic engine such as DuckDB on Parquet files can suffice (the chapter lists single-node databases as covering many workloads; the specific pairing is adaptation).
3. Must several engines or ML tools read the same data? Use open storage and table formats on object storage plus a catalog.
4. Are queries fixed and hot? Add materialised views or cubes, keep raw data too.
5. Is the product itself an analytics screen needing low-latency answers on fresh data? Look at real-time analytics engines (Pinot, Druid, ClickHouse are named).

Verify:
- Check the bytes scanned and columns read of the top queries; they should match the columns the query names (columnar working) and skip blocks outside time filters (block pruning working).
- Confirm sort keys match the common filter columns, by comparing scan size with and without the filter on the first sort key.
- For every materialised view or cube, name its refresh trigger, lag, and the raw table it can be rebuilt from.
- Confirm no dashboard or analyst tool connects to the OLTP primary.
- Confirm the table format, not ad hoc file edits, is the only path that mutates files.
