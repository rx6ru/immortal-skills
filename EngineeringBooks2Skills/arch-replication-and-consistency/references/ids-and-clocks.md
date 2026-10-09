# ID generation and logical clocks

Sources: DDIA 2e ch. 10 "ID Generators and Logical Clocks", ch. 9 (physical clocks); System Design
Interview 2e ch. 7 (unique ID generator). Items marked (inferred) are extrapolations in the study
notes.

## Contents
1. Start from the requirements
2. Scheme comparison
3. Lamport timestamps
4. Hybrid logical clocks
5. Vector clocks
6. Snowflake layout
7. When you need a linearizable ID generator
8. What logical clocks cannot do
9. Choosing
10. Verification

## 1. Start from the requirements
Ask which of these the identifiers must satisfy:
- Unique.
- Compact (the interview book's example requirement: numeric, fits 64 bits, at least 10,000 IDs per
  second, ordered by date: later IDs larger, not necessarily +1).
- Order consistent with causality (A happened before B means id(A) < id(B)).
- Order consistent with real time across clients who never communicate (linearizable).
- Generated without coordination across regions.
Single-node autoincrement meets the first four and is linearizable (an atomic fetch-and-add), but it is
a single point of failure, slow across regions and a bottleneck at high write rates. A single
database's auto_increment cannot serve a large distributed system.

## 2. Scheme comparison

| Scheme | Unique | Compact | Order | Coordination | Notes |
|---|---|---|---|---|---|
| Single-node autoincrement (replicated; e.g. a timestamp oracle in TiDB/TiKV) | Yes | Yes | Linearizable | All requests to one node and region | Batching trick in section 7 |
| Multi-master autoincrement with step k (interview book option 1) | Yes | Yes | Not time-ordered across servers | Hard across datacentres; breaks when servers are added or removed | |
| Sharded (odd/even or shard bits) | Yes | Yes | No | None at runtime | |
| Preallocated blocks | Yes | Yes | No | Per block | |
| Random UUID v4 | Probably | 128 bit | No | None | Collision odds negligible (cited: 50 percent chance of one duplicate after about 1 billion per second for about 100 years); not numeric-friendly or 64-bit |
| Ticket server (Flickr): one database handing out IDs | Yes | Yes | Yes | One central DB | Fine for small to medium scale; single point of failure, multiple ticket servers bring sync problems |
| Wall-clock timestamp plus unique bits (UUIDv7, Snowflake, ULID, MongoDB ObjectID) | Yes | 64 to 128 | Approximate; skew and clock jumps can misorder | None, needs NTP | Atomic clock or GPS shrinks error |
| Lamport timestamp (counter, node ID) | Yes | Few bytes | Consistent with causality; total order; not linearizable | None | |
| Hybrid logical clock | Yes | Small | Causality-consistent, near wall time; not linearizable | Roughly synced clocks | Used by CockroachDB |
| Vector clock | Per-node counters | Grows with nodes | Detects concurrency | None | For conflict detection |
| TrueTime-style (clock returns an interval; wait out uncertainty) | Yes | Yes | Linearizable across regions without communication | Tight clock hardware and software | |

## 3. Lamport timestamps
Required of any logical clock: compact and unique, any two timestamps comparable (total order), and
consistent with causality.

Mechanics: a timestamp is (counter, nodeID). To generate one, increment the counter and use it. On
receiving a timestamp with a larger counter than the local one, set the local counter to it. Compare
counters first, then node IDs lexicographically. Example order: (1, Aaliyah) < (1, Caleb) < (2, Bryce).
Equal counters imply concurrent; unequal counters do not reveal whether the events were concurrent or
ordered. Limits: no relation to physical time (cannot query "messages on date X"), and nodes that never
communicate drift apart.

## 4. Hybrid logical clocks
Like a wall clock (microseconds) but moves forward to match any greater timestamp seen, and increments
on each generated stamp so it stays monotonic even if the physical clock jumps back. It may run
slightly ahead of physical time, kept small. Use when you want near-wall-clock timestamps consistent
with happens-before without special hardware.

## 5. Vector clocks
A counter per node stored with each write; if A is greater on one node and B on another, they are
concurrent. Cost: size grows with the number of nodes. Lamport and HLC are good for transaction IDs in
MVCC snapshot isolation (snapshots consistent with causality) but cannot tell concurrent from ordered;
use vectors for that. Details and comparison rules: `conflicts-and-quorums.md`.

## 6. Snowflake layout (System Design Interview ch. 7)
Divide and conquer on 64 bits instead of generating one number centrally:
- 1 bit sign (always 0, reserved)
- 41 bits timestamp: milliseconds since a custom epoch (Twitter's default was 1288834974657, 4 Nov
  2010). Maximum 2^41 - 1 ms is about 69 years; pick a custom epoch near now to delay overflow, then
  migrate to a new epoch.
- 5 bits datacentre ID (32 datacentres)
- 5 bits machine ID (32 machines per datacentre)
- 12 bits sequence: increments per ID within the same millisecond on a machine, reset every
  millisecond; 4096 IDs per millisecond per machine.
Datacentre and machine IDs are fixed at startup; changing them is risky (conflicts) and needs careful
review. Timestamp and sequence are computed at run time. Because the timestamp is most significant,
IDs are time-sortable.

Wrap-up points from the chapter: it assumes clocks are synchronised and monotonic across cores and
machines, which is not always true (use NTP; inferred: refuse or wait when the clock moves backward);
tune section lengths (fewer sequence bits and more timestamp bits for low-concurrency, long-lived
systems); the generator is mission-critical, so plan for high availability.

Selection rule from the chapter: sortable 64-bit numeric IDs at scale with no central coordination:
Snowflake-style. No ordering needed and 128 bits acceptable: UUID. Tiny scale: ticket server or database
auto_increment.

Sketch (Python, adaptation):

```python
def next_id(self):
    now = self.clock_ms()
    if now < self.last_ms:                       # clock moved backwards
        raise ClockWentBackwards(self.last_ms - now)   # or wait; never reuse a timestamp
    if now == self.last_ms:
        self.seq = (self.seq + 1) & 0xFFF
        if self.seq == 0:                         # sequence exhausted this ms
            now = self.wait_next_ms(now)
    else:
        self.seq = 0
    self.last_ms = now
    return ((now - EPOCH) << 22) | (self.dc << 17) | (self.machine << 12) | self.seq
```

Adaptation, not from the book: `last_ms` lives in memory, so a restart with a clock behind the last
issued timestamp can repeat IDs. Persist a high-water mark, or wait out the gap, before serving after
a restart. The sketch assumes `EPOCH`, `clock_ms`, `wait_next_ms` and a per-instance lock around
`next_id`; I ran it with a fake clock (10,000 IDs, forced sequence overflow, backward clock): all
unique and increasing, regression raised.

## 7. When you need a linearizable ID generator
Worked example (DDIA figure 10-10): account settings (public to private) live in one database, photo
uploads in another, each with its own Lamport or HLC counter. The photo database's counter is behind, so
the photo gets a lower timestamp than the privacy change. A stranger's MVCC read at a timestamp between
the two sees a public account and the photo, leaking it. Fixes: the photo database reads the account
state first (easy to forget); the client tracks the last timestamp (fails across devices); or use a
linearizable ID generator (simplest).

Building one:
1. A single node atomically increments, persists the counter and replicates it (single-leader) for
   fault tolerance.
2. Optimisation: persist and replicate a record describing a batch of IDs, hand out from the batch,
   persist the next batch before exhausting it. After a crash or failover some IDs are skipped but
   never duplicated or reordered.
3. You cannot easily shard it or run it multi-region; all requests go to one region. The job is trivial,
   so one node handles high throughput.
4. Or the Spanner approach: a physical clock with an uncertainty interval, waiting out the interval;
   needs hardware (GPS or atomic) and software for tight sync.

## 8. What logical clocks cannot do
To use timestamps to pick the winner of a lock or username, a node must hear from every other node that
might hold a lower timestamp; one dead or unreachable node halts the system. Fault-tolerant locks,
leases and uniqueness need consensus, not logical clocks or ID generators
(`linearizability-and-consensus.md`).

## 9. Choosing

| Need | Use |
|---|---|
| Unique key, no ordering, any size | UUID v4 |
| Sortable 64-bit key, no coordination, roughly time ordered | Snowflake-style; handle clock regressions |
| Time-ordered keys that are also valid with causality across services | HLC |
| Detect concurrent writes | Vector or version vector |
| Transaction IDs for MVCC consistent with causality | Lamport or HLC |
| Real-time order across clients who never talk | Linearizable generator (batched single node) or interval clock with commit wait |
| Lock or uniqueness | Consensus (not an ID scheme) |

Do not use wall-clock-derived IDs as evidence of order between machines; skew can invert them.

## 10. Verification
- Uniqueness test across simulated machines, including after a restart.
- Per-machine monotonic test; behaviour at millisecond rollover and on sequence overflow (waits for the
  next millisecond).
- Clock-skew and backward-clock test: the generator refuses or waits rather than duplicating.
- Audit that machine IDs are assigned uniquely (two machines with the same ID produce collisions).
- Causality test: when A sends a message to B and B generates an ID afterward, the ID is larger (for
  Lamport/HLC); for the linearizable requirement, two non-communicating clients acting in sequence get
  increasing IDs (inferred).
- Capacity check: epoch overflow date (about 69 years from the chosen epoch for 41 bits) written down.
