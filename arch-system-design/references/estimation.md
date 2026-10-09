# Back-of-the-envelope estimation

Source: System Design Interview ch. 2 (procedure, tips, Twitter example) plus the estimates inside chapters 8, 9, 13, 14, 15; SRE
Workbook ch. 12 (unit-explicit arithmetic and machine reference points); DDIA 2e ch. 2 (hardware failure rates). The point of
estimating is to judge which designs can meet the requirements; reasoning and assumptions matter more than the final number.

## Contents
1. Number tables (and which are reconstructed)
2. The procedure
3. Formula templates
4. Rules of thumb
5. Worked estimates collected from the books
6. Sanity checks
7. Common mistakes
8. Machine reference points

## 1. Number tables

Reconstructed marker: in System Design Interview ch. 2 the printed tables were images that did not survive extraction. The values below are
the standard ones the book is known to print, rebuilt from well-known sources by the note-taker. The latency figures are the 2010
numbers attributed to Jeff Dean; the book itself says some are outdated but they show relative magnitude. Use them for ratios, not for precision.

### Powers of two (reconstructed)
| Power | Approximate value | Name |
|---|---|---|
| 2^10 | 1 thousand | 1 KB |
| 2^20 | 1 million | 1 MB |
| 2^30 | 1 billion | 1 GB |
| 2^40 | 1 trillion | 1 TB |
| 2^50 | 1 quadrillion | 1 PB |

A byte is 8 bits; an ASCII character is 1 byte.

### Latency (reconstructed, 2010 figures)
| Operation | Time |
|---|---|
| L1 cache reference | 0.5 ns |
| Branch mispredict | 5 ns |
| L2 cache reference | 7 ns |
| Mutex lock/unlock | 100 ns |
| Main memory reference | 100 ns |
| Compress 1 KB with Zippy | 10 us |
| Send 2 KB over 1 Gbps network | 20 us |
| Read 1 MB sequentially from memory | 250 us |
| Round trip within the same data center | 500 us |
| Disk seek | 10 ms |
| Read 1 MB sequentially from network | 10 ms |
| Read 1 MB sequentially from disk | 30 ms |
| Packet round trip California to Netherlands and back | 150 ms |

Units: 1 ns = 10^-9 s; 1 us = 1,000 ns; 1 ms = 1,000 us. Conclusions the book draws: memory is fast and disk is slow; avoid disk
seeks; simple compression is fast, so compress before sending over the internet; cross-region round trips cost real time.

### Availability (reconstructed)
HA = continuously operational for a long time, expressed as a percentage. An SLA is a formal uptime agreement with customers; the major cloud providers' SLAs are 99.9% or above (per the book).

| Availability | Downtime per day | Downtime per year |
|---|---|---|
| 99% | 14.40 min | 3.65 days |
| 99.9% | 1.44 min | 8.77 h |
| 99.99% | 8.64 s | 52.60 min |
| 99.999% | 864 ms | 5.26 min |
| 99.9999% | 86.4 ms | 31.56 s |

Quick derivation (adaptation): downtime fraction = 1 - availability; times 86,400 s per day, or times about 31.56 million s per year (365.25 days, which is what the table uses; with 365 days 99.99% is 52.56 min). Use it to check any claimed nines.
For chains of dependencies and error-budget arithmetic go to `arch-reliability-slos`.

## 2. The procedure

1. Write the assumptions (users, behaviour, sizes, retention). If given by the requester, copy them; otherwise state your own.
2. DAU = monthly users x fraction active daily.
3. Actions per user per day x DAU = events per day.
4. QPS = events per day / 86,400 (round 86,400 to about 10^5 for mental arithmetic).
5. Peak QPS = 2 x average QPS (the book's rule; replace it if you know the traffic shape).
6. Bytes per record x records per day = storage per day; x retention days = total storage; x replication factor for raw capacity (replication factor is an adaptation, not in ch. 2).
7. Derive cache size, server count and bandwidth from QPS and sizes as the design needs.
8. Round aggressively and keep units on every line (5 KB is not 5 MB). Precision is not expected; the process is.
9. Compare to capacity: one machine, one disk's IOPS, one NIC (section 8), and to the latency table.

Commonly asked outputs: QPS, peak QPS, storage, cache size, number of servers.

## 3. Formula templates

| Quantity | Formula |
|---|---|
| Average QPS | DAU x actions per user per day / 86,400 |
| Peak QPS | 2 x average (default rule) |
| Read QPS | write QPS x read:write ratio |
| Storage per day | records per day x bytes per record |
| Total storage | storage per day x 365 x years |
| Bandwidth | QPS x bytes per request |
| Keys needed | records per year x years; pick length n with alphabet^n >= keys (URL shortener: 62^7 about 3.5 trillion) |
| Concurrent connections memory | connections x per-connection memory (chat: 1M x 10 KB about 10 GB) |
| Sequential ops per process (consensus) | 1 / round-trip time (25 ms gives 40 ops/s) |
| Tasks needed | total ops per second / ops per task |
| Cost | transfer volume x price per GB (video CDN: 5M x 5 x 0.3 GB x $0.02 = $150,000/day) |

## 4. Rules of thumb used across the book

- Peak = 2 x average.
- 86,400 s/day is about 10^5; 1M requests/day is about 12 QPS (from the notes' digest of later chapters).
- Media dominates the size of a record that includes media: estimate only the media (Twitter example: 140 B text vs 1 MB media).
- A request per keystroke multiplies QPS by characters typed (autocomplete: 20 requests per 20-character query).
- Read:write ratio is an input, not a constant: URL shortener 10:1, 1:1 for chat and file sync.
- Use scientific notation in long chains (SRE Workbook): (5x10^5 queries/s) x (8.64x10^4 s/day) x (2x10^3 B) = 86.4 TB/day. Round up when sizing capacity.
- Replication doubles write load (NALSD multi-DC step counts this explicitly).

## 5. Worked estimates collected from the books

| Problem | Assumptions | Result |
|---|---|---|
| Twitter-like (SDI ch. 2) | 300M MAU, 50% daily, 2 tweets/user/day, 10% with 1 MB media, 5-year retention | DAU 150M; about 3,500 QPS; peak 7,000; 30 TB/day media; about 55 PB over 5 years |
| URL shortener (ch. 8) | 100M new URLs/day, 10:1 read:write, 10 years, 100 B per URL | 1,160 writes/s; 11,600 reads/s; 365 billion records; 36.5 TB (365 billion x 100 B; the book itself prints 365 TB, an arithmetic slip in the source); key length 7 |
| Web crawler (ch. 9) | 1 billion pages/month, 500 KB per page, 5 years | about 400 pages/s; peak 800/s; 500 TB/month; 30 PB over 5 years |
| Autocomplete (ch. 13) | 10M DAU, 10 searches/day, 20 characters/query, request per keystroke, 20% of queries new | about 24,000 QPS (the book's rounding; exact division gives about 23,000); peak about 48,000; about 0.4 GB new data/day |
| Video platform (ch. 14) | 5M DAU, 5 videos watched/day, 10% upload 1 video/day, 300 MB average | 150 TB/day stored; CDN egress about $150,000/day (CDN cost dominates) |
| File sync (ch. 15) | 50M users, 10M DAU, 10 GB quota, 2 uploads/day of 500 KB | 500 PB allocated; upload QPS about 240; peak 480 |
| Chat (ch. 12) | 1M concurrent connections, about 10 KB each | about 10 GB memory; fits one box, but a single server is a SPOF |
| Ad click-through dashboard (SRE Workbook ch. 12) | 500,000 queries/s, 10,000 clicks/s, 2 KB per query-log entry | 86.4 TB/day (round to 100 TB with indexes); full arithmetic in `nalsd-method.md` |
| Home timelines (DDIA ch. 2) | 500M posts/day, 200 followers | about 5,800 posts/s; 1.16M timeline writes/s vs 400M lookups/s for read-time queries |

## 6. Sanity checks

- Data path vs latency table: does any per-request step need a disk seek, a cross-region round trip, or many sequential network
  hops? Add the numbers: 10 sequential in-data-center round trips cost about 5 ms, one disk seek about 10 ms.
- Compare the result to one machine's capacity (section 8) before adding machines. DDIA ch. 1: a single node often suffices, and
  a simple single-threaded program can beat a 100-core cluster.
- Storage x replication must fit the chosen store and budget.
- Cross-check two derivations (for example per-second vs per-day totals).
- Tail check (NALSD): after sizing, add the failure case: capacity left after losing one machine, rack or data center.
- Hardware failure at scale (DDIA ch. 2): a 10,000-disk cluster expects about one disk failure a day, so replication and repair
  capacity are part of the estimate, not an afterthought.

## 7. Common mistakes

- Unlabelled units; mixing bits and bytes (network in Mbps, storage in bytes: 20 MB/s is 160 Mbps).
- Using the average where the peak or a skewed tail sets capacity.
- Forgetting indexes, replicas, retained versions or derived copies when sizing storage.
- Forgetting that fan-out multiplies work (one post times followers; one query times shards).
- Estimating to false precision; the book wants the order of magnitude and the stated assumptions.
- Treating illustrative book numbers as facts about your system. Replace every assumption you can with a measurement.

## 8. Machine reference points

From the SRE Workbook worked example, flagged there as illustrative assumptions (not universal): a standard machine of 16 cores,
64 GB RAM and a 1 Gbps network; a 4 TB hard disk at about 200 IOPS; consensus across fault-isolated data centers a few hundred km apart at about 25 ms per operation. The
note-taker marks these as assumed values. State your own reference machine in every estimate and replace these with the hardware you
actually run (for example, a cloud instance type) before relying on the result. SSD options were deliberately skipped in the source example.
