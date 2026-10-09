# The false assumptions of distributed systems and their defences

Source: DDIA 2e ch. 9 (The Trouble with Distributed Systems). Items marked (inferred) are
extrapolations in the study notes. Fencing and leases have their own file: `locks-leases-fencing.md`.

## Contents
1. The core idea: partial failure
2. Networks
3. Timeouts and fault detection
4. Clocks
5. Process pauses
6. Truth is decided by quorum
7. Byzantine faults
8. System models, safety and liveness
9. Verification techniques
10. Summary table: assumption, reality, defence

## 1. Partial failure
A distributed system differs from one computer because parts fail unpredictably while others work, and
you may not know whether an operation succeeded. A single computer is deliberately all-or-nothing. The
upside of tolerating partial failure: rolling upgrades and a reliable system built from unreliable
parts. In a big system one-in-a-million events happen daily. Test by creating faults on purpose.

## 2. Networks
Ethernet and the internet are asynchronous packet networks: no guarantee of delivery or timing.
A sender who gets no response cannot tell which happened: request lost; request queued; remote node
failed; remote node paused and recovers; remote processed it but the response was lost; remote
processed it but the response is delayed. After a timeout you still do not know whether the request
was processed, and it may still be delivered later.

What TCP does not give you: it cannot tell whether the packet or the ack was lost; it gives up after a
timeout; it does not deduplicate across reconnects (reconnect plus retransmit can duplicate); an ack
only means the remote kernel received data, not that the application handled it. Only an
application-level response proves a request succeeded (the end-to-end argument). The same applies to
QUIC, SCTP, uTP.

Observed faults: about 12 network faults a month in a medium datacentre (half single machine, half a
rack); redundancy helps less than expected because human misconfiguration is a major cause; undersea
and WAN cuts; round trips of minutes at high percentiles across regions; over a minute of delay
during a switch topology reconfiguration; partial partitions (A reaches B and B reaches C, A cannot
reach C); one-way failures (a NIC drops inbound but sends outbound); brief interruptions with
long-lasting effects. A network partition (netsplit) is unrelated to sharding partitions.

Defence: define and test error handling for every network failure. Undefined handling can deadlock a
cluster permanently or delete data. Handling need not mean tolerating (showing an error is valid if
rare), but recovery must work. Use fault injection. Make operations idempotent because a timeout
means "unknown outcome" (inferred).

## 3. Timeouts and fault detection
Fault detection is needed by load balancers and failover. Explicit signals sometimes exist (RST or FIN
from the OS when a process died but the host lives; a script notifying peers of a crashed process;
switch management interfaces; ICMP unreachable) but cannot be counted on. Assume silence and use
timeouts.
- Too long: slow detection, users wait. Too short: a slow node is wrongly suspected; if it was
  mid-action (sending an email) another node repeats it; load shifting onto others can cause cascading
  failure where every node declares the others dead.
- If delay bound d and processing bound r were guaranteed, timeout 2d + r would be exactly right. Real
  networks and servers provide neither.
- Sources of delay variance: queueing at switches when many senders target one port; OS queueing when
  cores are busy; VM pauses of tens of ms; TCP's own retransmission and sender-side queueing; noisy
  neighbours in multitenant clouds. Queues grow very fast near capacity.
- Choosing: measure the RTT distribution over long periods and many machines; better, use adaptive
  timeouts based on observed response times and jitter, such as the Phi Accrual failure detector (Akka,
  Cassandra); TCP's retransmission timeout is similar.
- TCP vs UDP: UDP avoids retransmission and flow-control variance; choose it when delayed data is
  worthless (voice, video calls).

Synchronous vs asynchronous networks: telephone circuits reserve bandwidth per call, so delay is
bounded and there is no queueing. Packet switching is chosen because it suits bursty traffic and high
utilisation. Variable delay is a cost/benefit trade (static partitioning gives guarantees at lower
utilisation and higher cost; dynamic sharing is cheaper), not a law of nature. Bounded-delay hybrids
(InfiniBand, QoS and admission control) are unavailable in public clouds and the internet. So there is
no correct timeout; determine it experimentally.

## 4. Clocks
Clocks serve durations (timeouts, latency percentiles) and points in time (expiry, log timestamps).
Each machine's quartz clock drifts; NTP synchronises against servers but network delay limits it.

| | Time-of-day | Monotonic |
|---|---|---|
| APIs | `CLOCK_REALTIME`, `System.currentTimeMillis` | `CLOCK_MONOTONIC`/`CLOCK_BOOTTIME`, `System.nanoTime` |
| Meaning | Calendar time since epoch, comparable across machines in theory | Arbitrary origin; only differences matter; never comparable across machines |
| Can jump | Yes (NTP reset, leap seconds, DST) | Never; NTP may slew its rate by up to 0.05% |
| Use for | Timestamps and dates | Elapsed time, timeouts, response times |

Multi-socket machines have per-CPU timers; take monotonicity with a pinch of salt.

Accuracy problems: Google assumes up to 200 ppm drift (6 ms per 30 s sync interval, 17 s per day);
NTP resets or refuses to sync when too far off; a node firewalled from NTP drifts unnoticed; NTP
accuracy is limited by RTT (about 35 ms best over the internet, spikes of about 1 s); wrong NTP
servers are mitigated by querying several and discarding outliers; leap seconds (59- or 61-second
minutes) crash systems (smear them; they end in 2035); VM pauses appear as clock jumps; user devices
may be deliberately wrong. High accuracy is possible but costly (finance regulation requiring clocks
within 100 microseconds via GPS or atomic clocks and PTP; GPS can be jammed).

Wrong clocks go unnoticed because the machine otherwise works, so the failure is silent, subtle data
loss. If you depend on synchronised clocks, monitor offsets between all machines and eject nodes that
drift too far.

Ordering with timestamps: see the last-write-wins failure in `conflicts-and-quorums.md`. Even tightly
synced clocks can show a message arriving before it was sent; ordering needs clock error much smaller
than network delay, which cannot be assured. Use logical clocks for ordering (`ids-and-clocks.md`).

A clock reading is a range, not a point: roughly drift since last sync plus NTP server uncertainty plus
RTT. Most APIs hide it; Google TrueTime and Amazon ClockBound return [earliest, latest]. Spanner uses
non-overlapping intervals as transaction timestamps and waits out the confidence interval before
committing (commit wait), so later transactions' intervals cannot overlap. GPS receivers or atomic
clocks in each datacentre keep uncertainty small (about 7 ms); the essential requirement is exposing an
interval.

## 5. Process pauses
Causes: lock or queue contention; stop-the-world garbage collection; VM suspend, resume and live
migration; laptop lid; context switches and hypervisor steal time; synchronous disk I/O (including lazy
class loading and network block devices); swapping and thrashing; SIGSTOP (Ctrl-Z, or by ops accident).

Principle: a node must assume it can be paused for a long time at any point, even mid-function, while
the world moves on and may declare it dead. Single-machine thread-safety tools (mutexes, atomics) do
not carry over.

The lease bug: a leader checks `lease.expiry - now < 10s -> renew`, then `if valid: process(request)`.
Two flaws: it compares an expiry set by another machine with the local wall clock (needs synchronised
clocks), and even with local monotonic time it assumes negligible time passes between check and act. A
15 s pause there means the lease has expired and another leader exists, and the thread cannot notice.
The remedy is fencing (`locks-leases-fencing.md`).

Limiting GC impact: modern collectors pause for milliseconds (G1, ZGC, Shenandoah, Go's concurrent
collector); GC-free or lifetime-checked languages (Swift ARC, Rust); object pools or off-heap
allocation; treat GC as a planned brief outage (drain the node from the load balancer first); rolling
restarts before long-lived garbage accumulates. These reduce pauses; none eliminates them. Hard
real-time guarantees exist (airbags, flight control) but cost throughput, tooling and money, and apply
to safety-critical embedded devices, not data systems.

## 6. Truth is decided by quorum
A node learns about others only through messages. A node that was declared dead may be unable to
object (its outputs are dropped) or may wake after a one-minute pause unaware. So a node cannot trust
its own judgement: decisions need a quorum, usually an absolute majority above n/2. If a quorum
declares a node dead, it is dead and must step down. A majority tolerates a minority of failures (3
nodes tolerate 1, 5 tolerate 2) and is safe because only one majority can exist at a time.

## 7. Byzantine faults
The book assumes nodes are unreliable but honest. Byzantine behaviour (lying, contradictory votes,
forged tokens) matters in aerospace and in multi-party untrusting systems such as blockchains. Usually
not worth it for server systems: nodes are under your control, byzantine protocols are expensive and
need more than 2/3 honest nodes (4 nodes tolerate 1), and identical software bugs defeat them. The
defence is authentication, ACLs, encryption and firewalls. Treat web clients as potentially malicious
with server-side validation. Cheap guards against weak lying: application-level checksums (corrupt
packets can pass TCP/UDP checksums) or TLS; input size and range limits even for internal services;
NTP clients with several servers and majority agreement.

## 8. System models, safety and liveness
Timing models:

| Model | Assumption | Realistic? |
|---|---|---|
| Synchronous | Bounded network delay, pauses and clock error | No |
| Partially synchronous | Synchronous most of the time, occasionally exceeds bounds arbitrarily, then recovers | Yes, models most systems |
| Asynchronous | No timing assumptions, no clocks, no timeouts | Very restrictive |

Node failure models: crash-stop (never returns); crash-recovery (stable storage survives, memory lost);
degraded or partial functionality (limping node, gray failure, fail-slow: answers health checks but is
too slow, such as a NIC falling to 1 Kb/s from a driver bug, GC thrash, a worn SSD, or a crashed
background thread); Byzantine. The most useful model for real systems is partially synchronous plus
crash-recovery. Gray failures are harder than clean ones.

Correctness is defined by properties. Safety ("nothing bad happens"): if violated you can point to the
moment, and it cannot be undone. Liveness ("something good eventually happens"; eventual consistency is
a liveness property). Demand that safety holds in all situations of the model, even if all nodes crash;
liveness may carry caveats (a majority up, the network eventually recovering). Fencing-token generator
example: uniqueness and monotonic sequence are safety properties; availability is liveness.

Model versus reality: crash-recovery assumes disk data survives, but real disks corrupt or vanish, and a
quorum algorithm breaks if a node suffers amnesia. Implementations should still handle "impossible"
cases, at minimum by halting for a human operator.

## 9. Verification techniques

| Technique | Does | Limit |
|---|---|---|
| Formal proof | Proves properties for all states of the model | Does not prove the implementation |
| Model checking (TLA+ and similar) | Explores states of a simplified spec for invariants; used by CockroachDB, TiDB, Kafka | Bounded; spec can drift from code |
| Property-based testing, fuzzing | Randomised inputs | No control of timing |
| Fault injection and chaos engineering (Jepsen, Chaos Monkey) | Injects crashes, pauses (kill, SIGSTOP), unmounted disks, firewalled links into real systems | Cumbersome, not replayable at fine grain |
| Deterministic simulation testing | Runs real code with network, I/O, clocks and scheduling under simulator control; replayable by seed; can run faster than wall time | Requires controlling all nondeterminism (application, runtime or machine level) |

Remaining nondeterminism traps: hash-table iteration order and resource-limit failures (out of memory,
stack overflow).

## 10. Summary: assumption, reality, defence

| Assumption | Reality | Defence |
|---|---|---|
| The network is reliable | Messages are lost, delayed, duplicated, one-way | Timeouts plus idempotent operations; application-level acks; fault injection |
| A timeout means failure | It means unknown outcome | Treat as unknown; retry safely; adaptive detectors; quorum for declaring death |
| Delay is bounded | It is not | Measure RTT distribution, adaptive timeouts, hysteresis against cascades |
| Clocks agree | Drift, jumps, unknown confidence | Monotonic clocks for durations; logical clocks for order; monitor offsets; interval APIs |
| My code runs continuously | Pauses of seconds | Fencing tokens; never trust a check made a moment ago |
| A node is up or down | Gray failures | Health checks that test real work; hedging; quorums |
| One node can decide | It can be wrong about itself | Majority decisions |
| Everyone tells the truth | Corruption and bugs | Checksums, validation; byzantine tolerance only when adversarial |
| Disks and memory are reliable | Corruption, amnesia | Halt for an operator on impossible states |

Closing advice: if it fits on a single machine, usually keep it there; distribute for fault tolerance
and geographic latency, not only scalability. A bad configuration pushed to every node still breaks
everything.
