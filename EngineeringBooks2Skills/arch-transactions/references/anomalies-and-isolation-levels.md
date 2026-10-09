# Anomalies and isolation levels

Source: DDIA 2e ch. 8 (sections on weak isolation, lost updates, write skew, summary table). SQL sketches are adaptation (PostgreSQL-flavoured) and show the shape of the problem, not a tested migration.

## Contents
1. The precise table
2. Naming traps across vendors
3. Anomaly entries (dirty write, dirty read, read skew, lost update, write skew, phantom)
4. Remedy ladder when you cannot raise the isolation level
5. Materializing conflicts
6. Single-object helpers are not transactions
7. How snapshot isolation works (MVCC)

## 1. The precise table

| Isolation level | Dirty reads | Read skew | Phantom reads | Lost updates | Write skew |
|---|---|---|---|---|---|
| Read uncommitted | possible | possible | possible | possible | possible |
| Read committed | prevented | possible | possible | possible | possible |
| Snapshot isolation | prevented | prevented | prevented | depends (see below) | possible |
| Serializable | prevented | prevented | prevented | prevented | prevented |

- Dirty writes are prevented by almost every implementation, even read uncommitted, so they are left out of the table.
- Snapshot isolation and lost updates: the database may detect the lost update automatically and abort one transaction. PostgreSQL repeatable read, Oracle "serializable" and SQL Server snapshot isolation do. MySQL/InnoDB repeatable read does not (which is why the book says it is arguably not true snapshot isolation).
- "Phantom" in the snapshot column means a read-only query never sees a phantom. A read-write transaction that checks for absence and then inserts is the dangerous phantom, and snapshot isolation does not stop that one (see write skew).

## 2. Naming traps across vendors

The SQL standard was written before snapshot isolation existed and is ambiguous. The names do not port.

| Name in vendor docs | What it actually is (per the notes) |
|---|---|
| PostgreSQL "repeatable read" | snapshot isolation, with automatic lost-update detection |
| Oracle "serializable" | snapshot isolation (so write skew is possible) |
| MySQL InnoDB "repeatable read" | MVCC read view, weaker than snapshot isolation: no lost-update detection |
| IBM Db2 "repeatable read" | serializability |
| SQL Server snapshot isolation | snapshot isolation with lost-update detection |
| PostgreSQL "serializable" | SSI (serializable snapshot isolation) |
| MySQL InnoDB and SQL Server "serializable" | two-phase locking |

Rule for the agent: never reason from the level's name. Find the engine and version in use, read its documentation for that level, and if the code's correctness depends on the answer, write the interleaving test (see `code-review-checklist.md`). Vendor behaviour in the notes is dated; treat the table as a starting hypothesis.

## 3. Anomaly entries

Entry format: what happens; how it looks in code; minimum level that stops it; remedies below that level; test.

### Dirty write
- What: transaction B overwrites a value transaction A has written but not committed. Book example: two buyers of one car; the listing goes to one buyer and the invoice to the other because the two updates interleave.
- In code: you will almost never see it, because every real transaction implementation takes row locks held to commit/abort. If you see a store without them (a multi-put on a NoSQL API, see section 6), a multi-key update can interleave.
- Stops it: any real transaction implementation. Remedy otherwise: none inside the store; move to one that has it.

### Dirty read
- What: seeing another transaction's uncommitted writes. Harms: sees half of a multi-row update (inbox shows the new email while the unread counter still says 0); sees data that is later rolled back.
- In code: a reader and a writer on related rows with no committed-only guarantee; read uncommitted level, or a store without transactions.
- Stops it: read committed. Most databases implement this by keeping the old committed value and serving it to readers until the writer commits; some (Db2, SQL Server with read_committed_snapshot off) use read locks, so readers can stall behind writers.
- Test: with two connections, start a write, do not commit, read from the other connection, assert you see the old value.

### Read skew (nonrepeatable read)
- What: within one transaction, different parts of the database are seen at different points in time. Book example: two accounts of $500 each, read during a $100 transfer, show $500 and $400, total $900. Each value was committed when read, so read committed allows it.
- Matters most for: backups (the inconsistency becomes permanent on restore), analytical queries, integrity checks, any report that adds up several rows.
- In code: several SELECTs in one request that must agree with each other, running at read committed; long scans.
- Stops it: snapshot isolation (every statement in the transaction reads from the snapshot taken at transaction start).
- Remedies below that: run long read-only, backup and analytics work as a transaction on a snapshot; or take explicit locks (costly).
- Test: transaction 1 reads account A; transaction 2 transfers A to B and commits; transaction 1 reads B; assert the sum is unchanged.

### Lost update
- What: two read-modify-write cycles overlap; the later write does not include the earlier change and clobbers it. Counter 42 read by both, both write 43. Also: appending to a list inside a JSON document (parse, change, write back), two users saving a whole wiki page.
- In code: SELECT then UPDATE with a value computed in the application; ORM load-entity, mutate, save; read a document, edit it, replace it.
- Stops it: snapshot isolation only if the engine auto-detects (see table), or serializable.
- Remedies (table rows follow the book's order of presentation; the preference order is the ladder in section 4, which is the notes' synthesis, inferred):

| Technique | Sketch | Works when | Weakness |
|---|---|---|---|
| Atomic write operation | `UPDATE counters SET value = value + 1 WHERE key = 'foo'` | the change is expressible as one DB operation (most counters, increments, in-document modifications, Redis structure ops) | ORMs readily generate the unsafe read-modify-write instead; hard to find by testing; free-text edits cannot be expressed this way |
| Explicit lock | `SELECT ... FROM game WHERE id = 7 FOR UPDATE;` check rules in app; `UPDATE ...` | the logic cannot be one DB op | easy to forget one code path; multiple locks risk deadlock (DB detects, aborts one, app retries) |
| Automatic detection | run at an engine/level that detects it, retry on abort | PostgreSQL repeatable read, Oracle serializable, SQL Server snapshot | not available in MySQL/InnoDB repeatable read; app must retry |
| Conditional write (compare-and-set / version column) | `UPDATE wiki SET content = :new, version = version + 1 WHERE id = 1234 AND version = :seen`; check rows-affected, retry on 0 | any store; the only option in stores without transactions | under MVCC the WHERE may evaluate against the old snapshot in some engines; verify per database |
| Merge in replicated stores | siblings merged afterwards | operations are commutative (counter increments, set adds; CRDTs) | conditional writes cannot be made commutative; last-write-wins silently loses updates |

- Locks and compare-and-set assume a single up-to-date copy, so they do not apply to multi-leader or leaderless replication; see `arch-replication-and-consistency`.
- Test: run N concurrent increments (threads or connections), assert the final value equals N. Repeat with the real isolation level and with retries on.

### Write skew
- What: two transactions read the same set of rows, each then updates different rows based on what it read, and the combined result violates an invariant that neither would violate alone. Book example: hospital needs at least one doctor on call; both doctors see count 2 under snapshot isolation, each sets own on_call = false, count becomes 0. If the two wrote the same row it would degenerate into a dirty write or lost update.
- Other book examples: two meeting-room bookings that overlap (check no overlap, then insert); two game figures moved to one square (a lock on the moved figure does not help); claiming a username; double-spending (insert tentative spend row, sum rows, check balance not negative).
- In code, the three-step pattern: (1) a SELECT checks a precondition, often by counting or searching rows; (2) the application decides; (3) a write changes what step 1 would now return. ORM-generated code is as exposed as hand-written SQL.
- Not stopped by: atomic single-object operations (the rows differ), automatic lost-update detection, ordinary FK/unique/check constraints (single-object; multi-object constraints need triggers or materialized views).
- Stops it: serializable isolation only.
- Remedies below serializable, in the order the notes give them:
  1. Real serializable isolation (the actual fix).
  2. Lock the rows the decision depends on: `SELECT ... FROM doctors WHERE on_call = true AND shift_id = 1234 FOR UPDATE;` before updating. Works only when those rows exist. Select the rows themselves: PostgreSQL rejects `FOR UPDATE` combined with `count(*)` or other aggregates (adaptation), so lock first, then count in the application or in a second query.
  3. A uniqueness constraint when the invariant is uniqueness (username, one booking per slot if the slot is a row).
  4. Materialize conflicts (section 5).
- Test: open two transactions at the configured level, have both run step 1, then both step 3, commit both; assert the invariant. At serializable, expect one commit to fail with a serialization error and the retry to see the new state.

### Phantom
- What: a write in one transaction changes the result of a search query in another. Read-only phantoms are prevented by snapshot isolation. The harmful kind is the same three-step pattern as write skew where step 1 checks for absence (no booking, username free, square empty): `SELECT ... FOR UPDATE` has nothing to lock because no row matches yet.
- Stops it: serializable (index-range locks under 2PL, or conflict detection under SSI). Otherwise a unique constraint or materialized conflicts.
- Test: two transactions both check "no booking overlaps 12:00-13:00 in room 123", both insert; assert only one booking exists after the retry cycle.

## 4. Remedy ladder when you cannot raise the isolation level

Use the first that fits the invariant (the ordering is the notes' synthesis, inferred):
1. Atomic operation or constraint inside one statement (increment, unique, check, FK).
2. Conditional write with a version column.
3. `FOR UPDATE` on rows that exist and that the decision depends on.
4. Materialized conflicts for absence checks.

If serializable isolation is available and the invariant spans rows and the workload tolerates retries, use it instead of steps 3 and 4 (`choosing-an-isolation-level.md` section 4 weighs the cost). The book calls materializing conflicts a last resort.

## 5. Materializing conflicts

Turn a phantom into a lock conflict on real rows. Booking example: pre-create a table of (room, 15-minute slot) rows for the next months; a booking transaction runs `SELECT ... FOR UPDATE` on the slot rows for its room and time, then checks overlap and inserts the booking. The slot table holds no booking data; it exists only to be locked.
- Costs: hard to design correctly, easy to get wrong, and it leaks concurrency control into the data model. Do it only when serializable is unavailable or too costly.

## 6. Single-object helpers are not transactions

- Storage engines almost universally make single-object writes atomic and isolated (no half-written 20 kB document, no spliced old/new).
- Atomic increment and compare-and-set are useful and prevent lost updates on that one object. They are not multi-object transactions.
- A "multi-put" in many NoSQL APIs can succeed for some keys and fail for others; it is not atomic.
- Cassandra/ScyllaDB lightweight transactions and Aerospike strong-consistency mode give a linearizable read plus conditional write on one object, with no cross-object guarantee.
- Why multi-object transactions are still needed: foreign keys and graph edges across mutually referencing records; denormalized copies that must change together (the unread counter); secondary indexes are separate objects that can otherwise disagree with the record.

## 7. How snapshot isolation works (MVCC)

Read this to predict what a snapshot transaction sees and what it costs. PostgreSQL-style; other engines differ in detail.
- Principle: readers never block writers and writers never block readers. Writes still take row write locks, so two writers on one row wait for each other. Reads take no locks.
- Several committed versions of a row are kept because in-flight transactions need different points in time.
- Each transaction gets a unique, increasing transaction ID. Each row version records `inserted_by` and `deleted_by` (initially empty). A delete sets `deleted_by`; an update is a delete plus an insert of a new version. A background cleanup (vacuum) removes versions no transaction can still see.
- Visibility, fixed when the transaction starts: ignore writes of transactions that were in progress at that moment (even if they commit later), of transactions with a later ID, and of aborted transactions; everything else is visible. Equivalent: a version is visible if its inserter had committed before the reader started and it is either not deleted or its deleter had not committed before the reader started.
- Consequences: a long-running transaction keeps old versions alive, so cleanup cannot reclaim them and storage bloats (inferred). PostgreSQL's transaction ID is 32 bits and wraps after about 4 billion transactions; vacuum handles wraparound.
- Indexes point at one version in a chain; a lookup walks the chain for a visible match, and cleanup removes index entries with dead versions.
- Alternative design: immutable copy-on-write B-trees (CouchDB, Datomic, LMDB). Each write creates a new root, copying modified pages and sharing the rest, so every root is a snapshot and no ID filtering is needed; a background process compacts old pages.
- Naming: see section 2; the same mechanism is sold as "repeatable read" or "serializable" depending on vendor.
