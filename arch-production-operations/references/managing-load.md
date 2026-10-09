# Managing load: load balancing, load shedding, autoscaling and their interactions

Sources: SRE Workbook ch. 11 (Managing Load); ch. 6 (dependency arithmetic); ch. 8 (identification and mitigation delay). Google Cloud Load Balancing (GCLB) is the book's running example; the lessons apply to other clouds and to in-house load balancers. For the capacity-modelling side see `arch-scalability-analysis`; for rate-limit algorithm design see `arch-api-security`.

## Contents

1. The central point
2. Layers of a global load balancer (what to borrow)
3. Case study: Pokemon GO on GCLB
4. Autoscaling: rules and failure modes
5. Interactions between tools (case study: Dressy)
6. Precautions by combination
7. Deadlines, retries and synchronised clients
8. Design checklist
9. Verification: how to test a load design
10. Warning signs

## 1. The central point

No single solution equalises and stabilises load. You combine load balancing, load shedding and autoscaling, and these tools are installed separately but are not independent. Each one reacts to signals the others change, so isolated tools can create catastrophic feedback loops. No amount of shedding, autoscaling or throttling saves you when everything fails in sync (synchronised retries plus a load balancer waiting on unresponsive backends). Plan mitigations in advance: flags, changed defaults, expensive logging that can be enabled, and exposing the live values of the parameters the traffic manager uses.

Combinations seen in practice: autoscaled instance groups cloned across regions need load balancing plus load-based autoscaling; three colos with weeks of lead time to add machines and a 5x social-media spike need load balancing plus shedding; a Kubernetes data pipeline that adds pods when slow but runs out of memory when data arrives too fast needs autoscaling plus shedding.

## 2. Layers of a global load balancer (what to borrow)

Request path in GCLB: client, anycast virtual IP, Maglev (packet or connection level), GFE (HTTP reverse proxy and TLS termination), backend, with a global software load balancer (GSLB) as control glue.

- DNS-based balancing is the simplest and most effective pre-connection balancing, but depends on clients expiring and refetching records, so GCLB does not use it.
- Anycast: the same IP announced from many points via BGP; packets reach the topologically nearest frontend. Benefits: no unicast IP proliferation, no DNS geolocation, a single VIP allows a long DNS TTL and so lower latency. Two residual problems: too many nearby users can overwhelm a site, and BGP route recalculation can reset in-progress TCP connections. Stabilised anycast fixes the second: a machine receiving a packet for a client closer to another site forwards it to that site, so TCP streams hold together when routes flap.
- Maglev: distributed packet-level balancer on commodity hardware. ECMP spreads packets across a pool, so you add machines to add capacity, and redundancy is N+1 rather than active/passive 1+1. It hashes the 5-tuple, looks in a connection-tracking table, and uses consistent hashing when there is no entry. No connection-state sharing between Maglevs is needed.
- GSLB: balances live traffic between clusters to match demand to capacity, knows backend health and drains failed clusters automatically.
- GFE: terminates TCP and TLS, picks a backend from the HTTP header or path, re-encrypts, health-checks backends, supports lame-duck mode (fail health checks but finish in-flight requests) for graceful removal, and keeps persistent sessions to recently used backends to cut latency.
- Latency design: an HTTPS handshake costs two round trips, so terminate TLS at the edge near users and use long-lived encrypted connections deeper in.
- Gradual rollout inside the balancer: deploy to very few servers, raise traffic gradually, and if a nonfatal regression appears, administratively remove that instance group from the balancer without touching the main version.

Adaptation: for most applications this reduces to concrete requirements on your own balancer: health checks that distinguish "failing" from "draining" (lame duck), consistent hashing for stateful routing, a way to remove one pool from rotation without a deploy, TLS termination close to clients, and per-location minimums (section 6).

## 3. Case study: Pokemon GO on GCLB

- Niantic had load-tested to 5x its most optimistic estimate; real launch traffic was about 50x the estimate. World state was shared in near real time among players in an area.
- Before GCLB: a regional network load balancer, then Kubernetes with Nginx pods as L7 proxies. Consequences: TLS needed two client round trips to Niantic's proxies, buffering slow clients exhausted proxy resources, and a packet-level proxy cannot absorb SYN floods.
- A large SYN flood prompted a migration to GCLB. At peak, true client demand was 200% higher than previously observed. Refused connections did not show up in inbound-request monitoring, because the backends never had a chance to see them.
- Cascade: Cloud Datastore, game backends and the balancer exceeded Niantic's project quota; backends became extremely slow rather than refusing, so requests timed out at the balancer; the balancer retried GETs, adding load; GFE SSL client code reconnecting to unresponsive backends hit unprecedented stress and a performance regression cut GCLB capacity worldwide by about 50%. The client retry strategy was one immediate retry then constant backoff, so quick error bursts synchronised client retries into a thundering herd up to 20x the previous global peak.
- Resolution by Traffic SREs: isolate the GFEs able to serve the game from the main pool; enlarge the isolated pool to handle peak despite the regression, shifting the bottleneck to Niantic's stack; with Niantic's consent apply administrative overrides limiting accepted traffic so Niantic could recover and scale.
- Lessons stated: add jitter plus truncated exponential backoff to clients; treat backends as a significant source of load and qualify or load test for degradation caused by slow backends; measure load as close to the client as possible or you under-provision. Inferred: isolate noisy tenants, keep admin rate-limit overrides ready, cap retries.

## 4. Autoscaling: rules and failure modes

Vertical (more resources per machine) or horizontal (more machines). Powerful when right, harmful when misconfigured.

| Concern | Rule |
|---|---|
| Unhealthy machines | Autoscalers average utilisation over all instances and assume homogeneity. Non-serving instances (slow to start or warm, zombies) still count in the average, so scale-up may never trigger. Combine: autoscale on a capacity metric observed by the load balancer (which discounts unhealthy instances); wait for new instances to stabilise before collecting metrics (a cool-down period); autoscale plus autoheal, leaving enough time after restart for health. Creating instances is never instant |
| Stateful systems | Sessions pinned to a backend mean adding instances does not help a hot path. Use task-level routing that spreads load (consistent hashing). Vertical autoscaling absorbs short hotspots but is uniform, so quiet instances may grow needlessly: use with caution |
| Conservative configuration | Scaling up matters more and is less risky than scaling down. Be more sensitive to rises than drops (add quickly, remove slowly). Keep the service far from key bottlenecks and give the autoscaler reaction time. User-facing services reserve spare capacity for overload protection and redundancy |
| Constraints | Set min and max bounds and enough quota to reach the max. Failure scenarios: CPU-based scaling plus a release that burns CPU without doing work scales until quota is exhausted; a failing dependency leaves requests stuck on your servers, so the autoscaler adds jobs, more stuck traffic and more load on the failing dependency, blocking its recovery |
| Kill switch | On-call must know how to disable autoscaling and scale manually. The switch must be easy, obvious, fast and well documented |
| Backends | Do a dependency analysis before enabling autoscaling (some services scale less linearly). Ensure backends have headroom and degrade gracefully, and use the result to set limits. With shared-quota microservices one scaling up can starve others: limit scaling pre-emptively or give each its own quota |
| Imbalance | Regional managed instance groups run a separate job to even out zone sizes, so quota use and failure domains stay diverse |

## 5. Interactions between tools (case study: Dressy, "When Load Shedding Attacks")

- Three equal regions A, B, C, each steady at 90 RPS. Traffic rises everywhere; A hits 120 RPS first; ten minutes later A is at 400 RPS while B and C dip to 40; most of A's requests return 503.
- The balancer was utilisation-aware and estimated fullness from container CPU. Load shedding (enabled earlier that week) rejects new requests when CPU passes a threshold. A passed the threshold first and began rejecting 10%, 20%, 50% of requests while CPU stayed at the cap (80%). The balancer saw falling per-request CPU cost (rejected requests are cheap), so A looked about 10x more efficient (240 RPS at 80% CPU versus 120 for B and C), and sent it more traffic: a positive feedback loop.
- Root cause: the balancer did not know the "efficient" requests were errors, and shedding and balancing were added by different people and never examined as one system.
- Fix: add error handling to the balancer logic, counting each error as more than 100% CPU (for example 120%) so A looks overloaded and traffic spreads.
- General rules: examine how each new load tool interacts with the existing ones; instrument their intersection; add monitoring to detect feedback loops; coordinate emergency shutdown triggers across the systems; consider automatic shutdown triggers if they behave wildly.

## 6. Precautions by combination

| Combination | Hazard | Precaution |
|---|---|---|
| Load balancing + autoscaling | Balancer routes to the nearest location, autoscaler grows it, more traffic goes there: positive feedback until all capacity sits in one place. If it fails, others are overloaded and scale-up is not instant | Set a minimum number of instances per location to keep failover spare capacity |
| Load shedding + autoscaling | Shedding starts before scale-up, so you drop traffic you could have served | Set thresholds so the system autoscales before shedding begins |
| Load balancing + load shedding | Shed responses look cheap and the balancer favours the shedding location | Make shed responses visible to the balancer as full or overloaded |
| Any of them + RPC | Without a deadline, resources are held for in-flight requests up to a huge default, causing latency, memory exhaustion and crashes | Set deadlines on RPCs; servers terminate requests that run too long; clients cancel requests no longer useful (do not start an expensive search if the client already errored); put a suggested default deadline in the API definition comment; set client deadlines deliberately |

## 7. Deadlines, retries and synchronised clients

- Client retries: jittered, truncated exponential backoff; a cap on attempts (inferred: a retry budget).
- Retries at several layers multiply load (amplification). A single error retried at each of three levels with three attempts each can produce up to 27 calls (inferred arithmetic from the amplification warning in the simplicity chapter; see `simplicity.md`). Retry at one layer and keep the rest fail-fast.
- Monitor refused-at-edge connections, which Pokemon GO's monitoring missed.
- Traffic-reduction levers to prepare ahead: feature flags to disable expensive features, tunable defaults, switchable verbose logging, and a visible, editable set of the traffic manager's parameters.

## 8. Design checklist (synthesised in the notes)

1. Retries: jittered, truncated exponential backoff; retry budgets; deadlines everywhere.
2. Autoscaler: min and max with quota to reach max; scale on balancer-observed capacity or a healthy-only metric; cool-down; kill switch; headroom away from the bottleneck; dependency capacity analysis; separate quotas.
3. Shedding: threshold above the autoscale trigger; shed responses visible to the balancer (counted as full) and to monitoring; check feedback loops.
4. Balancer: per-location minimum for failover; measure demand at the client edge; ability to rate-limit a tenant administratively; lame-duck draining.
5. Monitoring: refused-at-edge connections; per-region utilisation versus request cost.

## 9. Verification: how to test a load design

- Review the configuration for each tool together and write down what signal each reads and what each changes. Any loop (A reads a signal B changes, B reads one A changes) needs a test or a damper.
- In a staging or load test, push a single location past the shedding threshold and confirm that traffic moves away from it, not toward it (the Dressy symptom is a region taking more traffic while returning more errors).
- Kill a dependency or make it slow and confirm the autoscaler does not scale the stuck tier up unboundedly; confirm the max bound and quota stop it.
- Confirm the autoscaling trigger fires at a lower load than the shedding threshold.
- Run the kill-switch drill: disable autoscaling and scale manually from the documented steps.
- Inject a synchronised error burst and check client backoff has jitter (retry timestamps spread out rather than aligned).
- Confirm every RPC path has a deadline and that servers drop work whose client has gone.
- Show the user the dashboards or test output for: per-location RPS and error rate, healthy instance counts, shed rate, and edge-refused counts.

## 10. Warning signs

Autoscaling on average CPU with unhealthy instances included; no max bound or quota check; shedding and balancing owned by different people with no joint test; shed errors that look like cheap successes to the balancer; fixed or immediate client retries; RPCs with no deadline; no kill switch; monitoring that counts only requests that reached a backend; a single location holding all spare capacity.
