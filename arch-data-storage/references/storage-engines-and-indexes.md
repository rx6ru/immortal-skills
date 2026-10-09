# Storage engines and indexes

Use this file to choose between log-structured (LSM) and update-in-place (B-tree) engines, to design and review secondary, multicolumn, covering, spatial, full-text and vector indexes, to decide on in-memory storage, and to recognise engine-specific warning signs in production.

Contents
1. Why an index costs something
2. Hash index over a log
3. SSTables and LSM-trees
4. B-trees
5. LSM vs B-tree comparison and chooser
6. Secondary, clustered, covering and multicolumn indexes
7. In-memory databases
8. Multidimensional indexes
9. Full-text search
10. Vector indexes
11. Embedded engines
12. Verification checklist

Sources: DDIA 2e ch. 4. Column-oriented storage and warehouses are in `analytical-storage.md`.

---

## 1. Why an index costs something

An index is a structure derived from the primary data to speed lookups; adding or removing one changes only query performance, never contents. The fundamental trade-off: a well-chosen index speeds reads, but each index uses disk and must be updated on every write, sometimes noticeably slowing them. That is why databases do not index everything by default. Add an index only when you can point to a query pattern whose read benefit outweighs the write cost; each added index (partial, covering or multicolumn especially) is paid on every write.

You will not write a storage engine, but you must choose and configure one, which needs a rough model of what it does. The two OLTP families are log-structured (write immutable files) and update-in-place (B-trees). Analytics uses a different layout (see `analytical-storage.md`).

## 2. Hash index over a log (Bitcask-style)

Mechanism: append-only log file plus an in-memory hash map from each key to the byte offset of its latest value. Write = append and update the map. Read = lookup, seek, read.

Problems: old entries are never freed (needs compaction); the map is not persisted, so restart rebuilds it by scanning the log; the map must fit in memory (on-disk hash maps perform badly); range queries are inefficient (must look up each key). In practice hash tables are rarely used for database indexes.

Use only when: all keys fit in RAM, access is point lookup, no range scans. Otherwise use a sorted structure.

## 3. SSTables and LSM-trees

**SSTable**: key-value pairs sorted by key, each key once per file. Pairs are grouped into blocks of a few KB; a sparse index holds the first key of each block. To find a key not in the index, seek to the greatest indexed key at or below the target and scan that block. Blocks can be compressed to save space and I/O at some CPU cost. Not all keys need to fit in memory, and sorted order gives efficient range scans.

**Building them (the LSM approach)**:
1. Writes go to an in-memory ordered map, the **memtable** (red-black tree, skip list or trie).
2. When it passes a threshold (typically a few MB), write it out as a new SSTable segment; a fresh memtable takes new writes meanwhile.
3. Reads check the memtable, then the newest segment, then older ones; absent from all means the key does not exist.
4. Background **merging and compaction** combines segments like a merge sort, keeping the newest value per key and dropping overwritten and deleted values, using minimal memory.
5. Crash safety: every write is also appended to a separate unsorted **write-ahead log** used only to rebuild the memtable; the log part is discarded after the flush. The log's last record may be torn, so use checksums and discard corrupted entries.

**Deletes** append a **tombstone**; the merge uses it to discard older values, and the tombstone itself is dropped only when merged into the oldest segment. Segment files are immutable once written, so crash recovery of a half-written SSTable is simply delete and redo. Merges run in the background; reads keep using the input segments until the merged output replaces them.

Lineage and users: Bigtable paper (SSTable, memtable), LSM-tree paper (1996); RocksDB, Cassandra, ScyllaDB, HBase; Lucene term dictionaries. Segments can live on object storage (SlateDB, Delta Lake).

**Bloom filters.** Reading a key last updated long ago, or a missing key, would check many segments. A Bloom filter per SSTable is a bit array; each key sets k bit positions via k hashes. Any 0 bit for the query key means definitely absent (skip the segment); all 1s means maybe present (a false positive costs wasted work, never a wrong answer). Rule of thumb from the book: about 10 bits per key gives roughly 1% false positives, and each extra 5 bits per key cuts the rate about tenfold. They do not help range queries.

**Compaction strategies**

| Strategy | How | Strengths | Costs |
|---|---|---|---|
| Size-tiered | Newer, smaller SSTables merged into older, larger ones | Very high write throughput; data rewritten only a few times, in big sequential merges | Old SSTables grow huge; merges need lots of temporary disk; more SSTables to check per read; more stale-version space |
| Leveled | Fixed-size SSTables in levels L0, L1, ...; L0 newest; deeper levels are key-range-partitioned and each larger than the last; when a level exceeds its limit, SSTables merge into the next | Incremental compaction, less disk space, fewer SSTables per read | More rewriting (higher write amplification than size-tiered; implied by the notes) |

Choose size-tiered for mostly writes and few reads. Choose leveled when read-dominated, or when a small set of keys is written often and a large set rarely. Most engines make the strategy configurable.

## 4. B-trees

Introduced 1970; the standard index in almost all relational databases and many others. Keeps keys sorted (point lookups and range scans) but uses fixed-size pages overwritten in place, not variable-size immutable segments.

- Page size: traditionally 4 KiB; PostgreSQL 8 KiB; InnoDB 16 KiB (as of the book; may change). Pages are addressed by page number.
- Structure: a root page; interior pages hold keys and child references (each child covers a contiguous key range); leaves hold values inline or references to them. Branching factor is typically several hundred. Strictly this is a B+ tree.
- Update: find the leaf, overwrite the page. Insert: find the covering page; if full, split into two half-full pages and update the parent (splits can cascade; splitting the root makes a new root). Delete is more complex (node merging).
- Depth is O(log n); most databases fit in 3 to 4 levels. A 4-level tree of 4 KiB pages with branching factor 500 holds up to about 250 TB. Read cost is one page per level.

**Crash safety.** A split overwrites several pages; a crash midway can leave an orphan page and a corrupt tree, and hardware that cannot write a page atomically gives torn pages. The fix is a **write-ahead log** (redo log): every modification is appended and fsynced before it is applied to the tree pages; recovery replays it. Pages are buffered and flushed lazily, so durability comes from the fsynced WAL (check that fsync really happens before acknowledging a write; inferred).

**Variants**: copy-on-write (LMDB) writes modified pages to new locations with new parent versions, needing no WAL for crash safety and helping snapshot isolation; key abbreviation in interior pages for higher branching factor; sequential leaf layout for faster range scans; sibling pointers between leaves.

## 5. LSM vs B-tree comparison and chooser

Rule of thumb: LSM is better for write-heavy loads, B-trees are faster for reads. The book stresses this is a rule of thumb; benchmarks are workload-sensitive, so test with your workload. Hybrids exist.

| Axis | B-tree | LSM-tree |
|---|---|---|
| Point read | One page per level, few levels: predictable latency | May check several SSTables at different compaction stages; Bloom filters help; latency less predictable |
| Range query | Simple and fast | Scan all segments in parallel and merge; Bloom filters do not help |
| Write pattern | Random small page overwrites | Sequential writes of whole segment files |
| Write throughput | Lower on same hardware | Generally higher; large gap on HDD, smaller but real on SSD |
| Write amplification | At least 2x (WAL plus page); may rewrite a whole page for a few bytes (InnoDB doublewrite, PostgreSQL full-page writes) | WAL, memtable flush, every compaction rewrite; typically lower for common workloads; key-value separation (WiscKey) helps when values are much larger than keys |
| Space | Fragmentation: freed mid-file pages cannot return to the OS; background vacuum (PostgreSQL) | No unused page space; compresses better; stale data lingers until compaction (low with leveled, higher with size-tiered, plus temporary space) |
| Latency spikes | Few | If the memtable fills because compaction lags, backpressure (RocksDB suspends reads and writes until a flush) |
| Deletion guarantees | Overwritten in place (still needs care) | A deleted record can persist across levels until the tombstone propagates: a problem for regulatory deletion |
| Snapshots/backups | Hard to snapshot cheaply when pages are overwritten | Immutable files: record which segment files exist and do not delete them |

SSD note: flash writes by page (about 4 KiB) but erases by block (about 512 KiB). Sequential writes fill whole blocks from one file, so deletion frees a block without garbage collection; random writes interleave valid and invalid pages, so the controller does more GC, consuming bandwidth and wearing the drive faster. NVMe drives allow many parallel reads and engines should exploit that.

Benchmark warning: run write benchmarks long enough. An empty LSM-tree has no compaction going on, so early numbers overstate throughput; as data grows, compaction competes for disk bandwidth.

**Chooser**
- LSM engine (RocksDB, Cassandra, ScyllaDB, HBase) when: write-heavy ingestion, large datasets where compression and space matter, cheap snapshots wanted, sequential-friendly writes. Watch for write stalls from compaction debt, expensive range scans, slow physical deletion.
- B-tree engine (PostgreSQL, InnoDB, SQL Server, LMDB) when: read-heavy, predictable latency, common range queries, transactional features built on page-level locking or versioning. Accept random-write cost.

Warning signs: LSM shows throughput dropping as the database grows, periodic write stalls, disk usage doubling during size-tiered compaction. B-tree shows bloat and fragmentation needing vacuum, write throughput capped by IOPS, SSD wear.

## 6. Secondary, clustered, covering, multicolumn indexes

A secondary index is a key-value index whose indexed values are not unique. Make entries unique by storing a list of matching row IDs (postings list) as the value, or by appending the row ID to the key. Works on B-trees and log-structured storage. Many secondary indexes per table are normal.

| Placement | What the index stores | Examples | Trade-off |
|---|---|---|---|
| Clustered | The full row inside the index structure | InnoDB primary key; one clustered index per table in SQL Server | Fewest hops for primary-key lookups; secondary entries carry the primary key (InnoDB), so a secondary lookup is two traversals |
| Non-clustered with heap file | A reference into an unordered heap file | PostgreSQL | Indexes share one heap copy; in-place overwrite if the new value is not larger; otherwise the row moves and indexes are updated, or a forwarding pointer is left |
| Covering / included columns | Some columns stored in the index too | SQL Server INCLUDE, PostgreSQL INCLUDE | Query answered from the index alone; extra disk and slower writes because data is duplicated |

**Multicolumn (concatenated) index** joins columns into one key in declared order, like a phone book sorted by (last name, first name). It serves queries on a left prefix (last name alone, or last name plus first name) and is useless for first name alone. Column order matters. Verification: confirm query predicates form a left prefix of the index columns and that EXPLAIN shows the index being used (inferred).

Sketch (adaptation):

```sql
CREATE INDEX idx_user_name ON users (last_name, first_name);
EXPLAIN SELECT * FROM users WHERE first_name = 'Ana';   -- expect no index use
EXPLAIN SELECT * FROM users WHERE last_name = 'Silva';  -- expect index use
```

## 7. In-memory databases

Disks were tolerated for durability and low cost per GB; as RAM gets cheaper and datasets stay modest, memory-resident storage is feasible, possibly across machines. Durability options: battery-backed RAM, an append-only change log on disk, periodic snapshots, replication. If the disk is only an append-only log and reads come from RAM, it is still an in-memory database.

Examples in the book: Memcached (cache only; loss on restart acceptable), VoltDB, SingleStore and Oracle TimesTen (relational in memory), RAMCloud (durable key-value with log-structured memory), Redis and Couchbase (weak durability via asynchronous disk writes).

Counterintuitive point: the speed advantage does not come from avoiding disk reads (the OS page cache already serves hot blocks from RAM). It comes from avoiding the overhead of encoding in-memory structures into a disk-friendly form. A second benefit: structures that are hard on disk (Redis priority queues and sets) are simple in memory.

Choose when the dataset fits in RAM (perhaps sharded), latency matters, and either losing recent writes is acceptable or you pay for a durable log or replication.

## 8. Multidimensional indexes

A concatenated index gives a range on latitude or longitude, not both at once, which is poor for a bounding-box query. Options: map 2-D to one number with a space-filling curve and use an ordinary B-tree; use a spatial index (R-trees, Bkd-trees; PostGIS uses an R-tree via PostgreSQL GiST); or use a regular grid of triangles, squares or hexagons. Not only geographic: RGB colour range search is 3-D, (date, temperature) is 2-D.

## 9. Full-text search

Core idea: each term is a dimension; a document has a 1 in that dimension if it contains the term. A search for "red apples" needs 1 in both. Language processing (tokenising languages without spaces, stemming, synonyms, typos) is out of the chapter's scope.

- **Inverted index**: term maps to a postings list of document IDs. With sequential IDs the list can be a sparse (run-length-encoded) bitmap, and a multi-term AND is a bitwise AND, the same trick as vectorised warehouse queries.
- Lucene (Elasticsearch, Solr) keeps term-to-postings in SSTable-like sorted files merged in the background, so it is log-structured. PostgreSQL GIN uses postings lists for full-text and JSON indexing.
- **n-gram (trigram) index**: indexes all substrings of length n; supports arbitrary substring and regex search (minimum length n) at the cost of a large index.
- **Fuzzy matching**: Lucene stores terms as a finite-state automaton (trie-like) and builds a Levenshtein automaton to match within edit distance k.

A full-text index is a secondary (derived) index; if it lives in a separate search system, treat it as derived data with a refresh path (`data-system-tradeoffs.md`).

## 10. Vector indexes

Semantic search matches meaning rather than words; used in RAG for LLMs. An embedding model turns a document or query (possibly with context such as location) into a vector of floats, often over 1,000 dimensions; similar inputs map to nearby points. Individual numbers are not interpretable. Distance: cosine similarity (angle) or Euclidean. R-trees do not work well in high dimensions.

| Index | Mechanism | Accuracy | Cost |
|---|---|---|---|
| Flat | Store raw vectors; compare query to every one | Exact | Full scan, slow |
| IVF (inverted file) | Cluster the space into partitions with centroids; check the `probes` nearest partitions | Approximate (a near neighbour can sit in another partition) | Faster than flat; more probes = more accurate and slower |
| HNSW | Multi-layer proximity graphs; start at the nearest node in the sparse top layer and descend following edges to closer nodes | Approximate | Fast greedy search; memory-heavy (inferred) |

Implementations named: Faiss (IVF and HNSW variants), pgvector (both). Choose flat for small corpora or when exactness is required; IVF or HNSW for large corpora where approximate recall is acceptable; tune probes (IVF) as the recall/latency knob. Verify by measuring recall@k against a flat-index baseline whenever you change ANN parameters (inferred). Terminology trap: "vector" in vectorised query execution means a batch of values, not an embedding.

## 11. Embedded engines

Embedded databases run in-process as libraries (RocksDB, SQLite, LMDB, DuckDB, KùzuDB): function calls and local files, no network API. Typical on mobile. On a backend they suit data that fits on one machine with few concurrent transactions, for example one small isolated database per tenant with no cross-tenant queries (the book cites Bluesky's use of single-tenant SQLite). The same techniques apply to embedded and client/server engines.

## 12. Verification checklist

1. Every index maps to a named query; every frequent query maps to an index or an accepted scan. Query plans (EXPLAIN) confirm it.
2. Multicolumn index column order matches predicate prefixes.
3. For an LSM store: compaction strategy matches the read/write mix; monitor compaction backlog, write stalls and peak disk usage; delete semantics (tombstone propagation) checked against any retention or erasure requirement.
4. For a B-tree store: bloat and vacuum health monitored; write IOPS headroom measured.
5. Benchmarks ran long enough to include steady-state compaction or checkpointing, with production-like data size and key distribution.
6. Durability: fsync before acknowledging; WAL replay tested by killing the process mid-write (inferred test).
7. For ANN indexes: recall@k measured against exact search; probes or graph parameters recorded.
8. For in-memory stores: stated tolerance for lost writes, or a durable log and tested restart time.
