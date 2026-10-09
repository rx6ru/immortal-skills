# Non-abstract large system design (NALSD)

An iterative method that turns every whiteboard design into concrete resource numbers and a failure analysis before choosing the next
design. Source: The Site Reliability Workbook ch. 12 (worked example: an ad click-through-rate dashboard). Numbers below are the
book's illustrative assumptions, not universal facts.

## Contents
1. What it is and why
2. The questions and phases
3. The worked example, iteration by iteration (with the arithmetic)
4. Requirement-check table
5. Replayable checklist
6. Applying it to your problem
7. Caveats

## 1. What it is and why

State the problem, gather requirements, then iterate through increasingly sophisticated designs; each time convert the design into
concrete estimates (machines, disks, RAM, bandwidth) and examine failure. It combines capacity planning, component isolation and
graceful degradation. Systems eventually run on real computers, data centers and networks, so doing the arithmetic at every step avoids
late redesigns for physical constraints nobody counted. The reasoning and assumptions matter more than the final numbers; imperfect but reasonable assumptions
are fine, and the value comes from combining many rough results. Deferring reliability in design means accepting fewer features at higher cost.

Each iteration reuses the prior work (extend, do not restart) and separates components by expected growth so they scale independently and no single
hardware or software instance is a dependency. The final design is the end of a story of twists and turns, so keep the rejected designs and why.

## 2. The questions and phases

Basic design phase (does it work in principle?):
1. Is it possible? Could we build it, ignoring RAM, CPU and bandwidth limits, without "magic"?
2. Can we do better? Is it as simple as reasonably possible; faster, smaller, more efficient (for example O(N) to O(ln N))?

Scale-up phase (multiply a requirement dramatically):
3. Is it feasible? Can it scale within money, hardware and time? What distributed design is needed?
4. Is it resilient? Does it fail gracefully? What if this component fails? What if a whole data center fails?
5. Can we do better? (again)

In practice you bounce between questions and phases, and a design may pass early stages and fail later; then modify or replace components. Each iteration
ends in either "feeds the next iteration" or "good enough to recommend".

## 3. The worked example

Problem: report accurate click-through rate (clicks / impressions) per ad per search term to advertisers. Data: query log (time, query_id, search_term, ad_ids shown)
and click log (time, query_id, ad_id). The query log is separate from the click log because click logs derive from URLs with size limits and CTR is one of many insights.

Requirements as SLOs: 99.9% of dashboard queries answered in under 1 s; 99.9% of the time CTR data is under 5 minutes old. Load: 500,000 search queries/s and
10,000 clicks/s (average CTR 2%); millions of advertisers. The SLOs give an error budget to judge each design against.

### Iteration 1: one machine
Design: both logs on one machine, a data structure for fast CTR (a SQL DB indexed on query_id and search_term, join the logs on query_id, group by search term). It must compute CTR in constant time as load grows (no scanning logs).

Record size: time 8 B, query_id 8 B, ad_ids (three 64-bit ints) 8 B each, search_term up to 500 B, metadata 500-1000 B; aggressively round to 2 KB per query-log entry.

Arithmetic (scientific notation avoids unit errors):
- Storage: (5x10^5 queries/s) x (8.64x10^4 s/day) x (2x10^3 B) = 86.4 TB/day. The click log is only 2% of that. Add index overhead and round to about 100 TB/day.
- Disk IOPS: a 4 TB HDD gives about 200 IOPS. One disk write per log entry means 5x10^5 / 200 = 2,500 disks; even batching 10:1 needs hundreds.
- RAM-only: 100 TB / 64 GB per machine (standard machine 16 cores, 64 GB RAM, 1 Gbps) = 1,563 machines.
- SSD evaluation skipped for simplicity.

Evaluation: a single machine has SPOFs (CPU, memory, storage, power, network, cooling); a power cycle alone breaks the SLOs. Not wasted: it yielded constraints. Conclusion: multiple machines.

### Iteration 2: distributed batch (MapReduce)
Periodically batch-join the query and click logs to produce per-ad per-search-term click counts. Scales horizontally without running out of disk or RAM.
Rejected: batch cannot meet the 5-minute freshness SLO, and small batches of a few minutes are impractical because batches are arbitrary and non-overlapping: a click in batch 2 whose query is in batch 1 is never joined.

### Iteration 3: LogJoiner
Insight: clicks are far fewer than queries, so treat the larger side (query logs) as a lookup store rather than a batch. Components:
- QueryStore: full query logs keyed by query_id (like Bigtable); about 100 TB/day; expire old data.
- LogJoiner: streams the click log, looks up each click's query in QueryStore, writes results organised by ad_id.
- ClickMap: ad_id to clicks (output of LogJoiner). If a click's query is not found (query-log delay), set it aside and retry until a time limit, then discard.
- QueryMap: ad_id/search_term to queries shown (impressions), fed directly from the query log and indexed by ad_id.

Network arithmetic:
- Clicks into LogJoiner: 10^4/s x 2 KB = 20 MB/s = 160 Mbps.
- QueryStore lookup request: 10^4 x 8 B = 80 KB/s = 640 Kbps; response 20 MB/s = 160 Mbps.
- LogJoiner to ClickMap: 10^4 x 10^3 B (under 1 KB) = 10 MB/s = 80 Mbps.
- Aggregate about 400 Mbps (manageable).

Storage arithmetic:
- ClickMap per day = 10^4 x 8.64x10^4 x (8+8 B) = 14 GB/day, round to 20 GB/day. Ad/search-term tables are negligible (10M advertisers x 10 ads x 8 B about 800 MB).
- QueryMap: up to 3 ad_ids per query, so 3 x 5x10^5 x 8.64x10^4 x 16 B = about 2 TB/day. 2 TB fits on one machine's disks but the IOPS of small writes does not, so shard.

### Iteration 4: sharded LogJoiner
Concerns: data management (network and disk throughput are not limits), reliability (do not lose in-flight work when a LogJoiner dies), efficiency (minimum resources).
- Shard by query_id so LogJoiners run in parallel; scale horizontally, not vertically. The log sharder hashes query_id, takes it modulo N (+1) for the shard number and sends the record there.
- QueryMap (2 TB/day, too big for 64 GB RAM, needs many disks for IOPS) is sharded by ad_id, which is known before any read or write and matches dashboard access. Reuse the same sharder design for ClickMap (smaller).
- Reliability: if a LogJoiner fails after receiving but before joining, its work must be redone, delaying data and hurting the freshness SLO. Fix: the sharder sends duplicate log entries to two shards (a replica) so a failure does not slow results; replicas must never land on the same machine. If two machines holding both copies fail together, the error budget covers the residual risk and logs are reprocessed (the dashboard briefly shows data slightly older than 5 minutes). Build LogJoiner, ClickMap and QueryMap on both shard and replica. The dashboard must combine/query all ClickMaps.
- Evaluation: a single data center is a SPOF (an unlucky machine pair or a DC disconnect loses ClickMap work; dashboards fail).

### Iteration 5: multi-data-center
ClickMap must exist in every DC for failover without multiplying compute. This is a consensus problem. Recipe: 3 or 5 replicas of the shared service (ClickMap); use a consensus algorithm (Paxos) so state survives a DC-sized failure; at least one network round trip between participants for each write, which limits sequential throughput (different shards write in parallel).

Arithmetic:
- Paxos across fault-isolated DCs a few hundred km apart is about 25 ms per operation, so 40 sequential ops/s per process.
- 10^4 clicks/s sequential needs at least 250 processes per DC, sharded by ad_id (add more for backlog and spikes).
- Replication doubled the load: 20,000 clicks/s + 1,000,000 queries/s = 1.02x10^6 ops/s.
- Tasks = 1.02x10^6 / 40 = 25,500 tasks.
- Memory per task: two copies of the 2 TB QueryMap = 4x10^12 B, / 25,500 = 157 MB.
- Tasks per machine: 6.4x10^10 B (64 GB) / 1.57x10^8 B = 408.
- Network: 1.02x10^6 x 2 KB = 2.04 GB/s = 16 Gbps total; / 25,500 = 80 KB/s = 640 Kbps per task; x 408 tasks = about 260 Mbps per machine (the book prints 256; either way about 25% of 1 Gbps).
- Total about 4 TB RAM per data center, 4 TB / 64 GB = 64 machines.

## 4. Requirement-check table

After each iteration, map each requirement line to the component or property that satisfies it. The book's final check:

| Requirement | Satisfied by |
|---|---|
| 10k clicks/s | LogJoiner scales horizontally into ClickMap |
| 500k queries/s | QueryStore and QueryMap sized for a full day |
| 99.9% of dashboard queries under 1 s | lookup by ad_id in QueryMap and ClickMap: fast and simple |
| 99.9% of the time data under 5 min old | every component scales horizontally; adding machines cuts pipeline latency |

Also run the "what if this component fails, what if the whole DC fails" test and record the answer.

## 5. Replayable checklist

1. Restate the problem, the entities and the data flow. Convert requirements to SLOs (latency percentile, freshness) and load numbers (QPS, bytes per record). Note the error budget.
2. Draw the simplest design (single machine). Compute storage per day, IOPS, network and RAM in unit-explicit scientific notation, rounding up. Compare with a stated standard machine (example: 16 cores, 64 GB, 1 Gbps; 4 TB HDD about 200 IOPS).
3. List SPOFs (CPU, memory, storage, power, network, cooling). Decide whether the SLOs survive any one failure.
4. For each failed capacity check pick a scaling move:
   - batch vs streaming (check against the freshness SLO and cross-batch joins);
   - lookup store plus stream joiner (make the larger side the store);
   - shard by the key known at read/write time (hash(key) mod N);
   - replicate shards (never co-located);
   - multi-DC with consensus (ops/s = 1/RTT; tasks = load / ops per task; memory and bandwidth per task and per machine).
5. After each iteration run the requirement-check table and the "component dies / DC dies" test.
6. Record rejected designs with the reason (MapReduce: batch boundaries break joins and freshness).

## 6. Applying it to your problem

Adaptation (not from the book): in a repository task, the same loop works for sizing a log pipeline, a job queue, a search index or an analytics table.
Write the number sheet as a table (quantity, formula, value, unit, assumption) next to the design, update it when a design iteration changes a component,
and keep an "iterations" section listing each design, why it was rejected or kept. When numbers show the single-machine design fits with headroom and a replica for availability, stop at iteration 1 and say so; the method is a way to justify complexity, not to add it.

## 7. Caveats

- Numbers are illustrative (assumed 2 KB records, 64 GB machines); the 25 ms consensus latency is an assumption for DCs hundreds of km apart.
- SSD options and some workarounds were deliberately skipped in the source example.
- The doubled load for replication is counted in the multi-DC step.
- For SLO definition and alerting once the system exists, go to `arch-reliability-slos`; for the scaling model of the finished system, `arch-scalability-analysis`.
