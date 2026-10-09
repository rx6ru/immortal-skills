# Interpreting coefficients and improving scalability

Source: USL booklet, "Using the USL to Improve Scalability", conclusions, the queueing-relationship section; DDIA 2e ch. 2 (architectures, principles); SRE Workbook ch. 11 (dependencies and autoscaling interplay). Items marked (adaptation) are mine.

Contents
1. Read the coefficients
2. Contention (sigma): causes and fixes
3. Crosstalk (kappa): causes and fixes
4. Partitioning when crosstalk cannot be removed
5. The pessimistic-baseline rule for diagnosis
6. Case: PayPal Java versus NodeJS
7. Architecture families and the two penalties
8. Finding the causes in a repository (adaptation)
9. Verify an improvement
10. Scaling people and organisations

## 1. Read the coefficients

| What the fit shows | Reading | Look first at |
|---|---|---|
| sigma large, kappa near zero | Amdahl-like: queueing and serialization cap throughput at lambda/sigma, no decline | the serial sections: locks, single-threaded stages, final gather |
| kappa large, sigma small | coherency cost dominates; throughput peaks at sqrt((1-sigma)/kappa) and then falls | what workers share or tell each other |
| both sizeable | both penalties; fixing one moves the peak but not the cause of the other | which term is larger at your operating N and at Nmax |
| sigma < 0 | usually a measurement or setup problem | the measurement design (measuring-and-fitting.md section 8) |

Effect sizes to remember: 5 percent serialization caps speedup at 20x; even a tiny kappa produces retrograde behaviour. In the source's Cisco fit kappa was under 0.001 yet scaling ended around N = 35.

## 2. Contention (sigma): causes and fixes

Cause (queueing sense): work that cannot be parallelised queues for a shared resource. Throughput can only flatten.

Typical sources named in the notes: mutex hold times, single-threaded stages, global locks, the final gather step of scatter-gather, a single event loop, queueing in front of a shared resource, single points of coordination.

Fixes, in the order the notes give them:
1. Shrink or remove the serial section.
2. Shorten lock hold times.
3. Parallelise the gather stage.
4. Remove single points of coordination.
5. Avoid queueing in front of shared resources.

Tenet: avoid serialization and queueing; make things as parallel as possible.

## 3. Crosstalk (kappa): causes and fixes

Cause: workers (threads, CPUs, servers) must communicate to share or synchronise mutable state, and the cost is pairwise, so it grows with the square of N. It inflates service time, which is why it is the only thing that makes throughput fall.

Typical sources: cache coherence traffic, replication and consensus traffic, shared mutable state, all-to-all messaging, chatty coherence protocols, pairwise data interchange.

Fixes:
1. Reduce shared mutable state.
2. Avoid pairwise or all-to-all synchronisation; prefer hierarchical or one-to-few communication (adaptation).
3. Avoid chatty coherence protocols (fewer, larger messages; weaker consistency where the requirement allows, see `arch-replication-and-consistency`).
4. If it cannot be avoided, partition (next section).

Tenet: avoid crosstalk and synchronisation.

## 4. Partitioning when crosstalk cannot be removed

Split into smaller independent systems, each run at a size where the quadratic term has not exploded, and replicate partitions rather than building one giant coherent cluster. Each partition has its own Nmax; the aggregate scales roughly with the number of partitions provided the partitions really do not talk to each other and the routing layer is not itself a contention point (the last clause is adaptation). For choosing keys and rebalancing see `arch-replication-and-consistency`.

## 5. The pessimistic-baseline rule for diagnosis

The synchronous repairman model is a worst case for queueing delay, so a well-built system should scale at least as well as its USL predicts. Use the fitted curve as a baseline the system ought to beat. If measurements are worse than the curve, ask whether the cause is queueing or serialization (contention) or synchronisation and communication (crosstalk), and suspect something like mutex contention. If measurements are much better than a fit from small N, check for superlinear artefacts. This is the opposite stance to planning, where you treat the same forecast as best case (see capacity-planning.md); the difference is the question being asked: "is something wrong?" versus "how much can I count on?".

## 6. Case: PayPal Java versus NodeJS

| System | sigma | kappa |
|---|---|---|
| Java, multi-threaded, five cores | 0.000011 | 0.006323 |
| NodeJS, single-threaded event loop, one core | 0.080319 | 0.000222 |

Reading: many threads sharing state shows up as crosstalk; a single event loop shows up as serialization. Both scaled poorly in absolute terms. Lesson: the architecture's concurrency model predicts which coefficient will dominate, and the fit should confirm it. If it does not, you have misunderstood the system.

## 7. Architecture families and the two penalties

DDIA 2e ch. 2 compares three architectures. The mapping to the USL penalties is my adaptation; the pros and cons are the book's.

| Architecture | Book's description | Book's cons | Likely USL reading (adaptation) |
|---|---|---|---|
| Shared-memory (scale up) | bigger machine, threads share RAM | cost grows faster than linear; bottlenecks mean 2x hardware does not give 2x load | lock and cache-coherence costs: both sigma and kappa |
| Shared-disk | several machines, shared disk array via NAS or SAN | contention and locking overhead limit scalability | the shared array is a serialization point; lock traffic is crosstalk |
| Shared-nothing (scale out) | own CPU, RAM, disk per node; coordination in software | needs explicit sharding; all distributed-systems complexity | crosstalk appears only where nodes must coordinate; sharding keeps it local |

"Shared-nothing, therefore linear" is a bogus claim: it means only that there is no single hard cap. Measure it (limits-and-pitfalls.md).

## 8. Finding the causes in a repository (adaptation)

When the fit says contention, look for:
- global or process-wide locks, synchronized/Mutex around I/O, connection pools with a small fixed size
- single-threaded consumers on a hot path, one writer thread, a lone leader or coordinator for every request
- scatter-gather where the merge step is sequential and large
- single-row or single-key hot spots in a database (a counter row, a sequence)

When the fit says crosstalk, look for:
- broadcast or all-to-all messaging, gossip frequency tied to cluster size, cache invalidation sent to every node
- synchronous replication or consensus on the request path with growing membership
- shared mutable caches or counters touched by every worker, false sharing
- distributed locks taken per request

Confirm with a profile or trace under load before editing; the USL tells you which family to search, not the exact line (see `craft-debugging` for locating a cause, `craft-concurrency` for in-process locking).

## 9. Verify an improvement

1. State the prediction: "removing lock X should lower sigma" or "batching invalidations should lower kappa".
2. Re-run the same measurement design (same N values, same per-unit load and data).
3. Refit. The targeted coefficient should move, and Nmax and peak throughput should rise in the direction implied.
4. If neither coefficient moved, the bottleneck is elsewhere (notes: inferred). Go back to the profile.
5. Check the other coefficient did not worsen (trading contention for crosstalk is common: splitting a lock into many can add coordination).

## 10. Scaling people and organisations

The source notes that communication overhead behaves like crosstalk in teams and companies, and queueing for a shared person like contention. DDIA lists breaking the system into smaller independent components as the common thread (microservices, sharding, stream processing, shared-nothing) with the hard part being where to draw the boundaries; see `arch-decomposition`. Do not make things more complicated than needed: a single-machine database beats a complicated distributed setup if it suffices.
