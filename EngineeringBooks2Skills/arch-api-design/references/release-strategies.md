# Deploying and releasing APIs: separating deploy from release

Contents: 1. Deployment versus release; 2. Feature flags; 3. Where traffic is shaped; 4. Strategies (canary, mirroring, blue-green, A/B); 5. Choosing; 6. Automating rollouts with metric gates; 7. Observability for rollouts; 8. Application-level gotchas; 9. Opinionated platforms; 10. Verify

Source: Mastering API Architecture (MAA) ch. 5, with ch. 4 (mesh traffic splitting) and ch. 3. Tools named (Argo Rollouts, LaunchDarkly, Prometheus, Istio) are 2022 examples; equivalents include Flagger, Spinnaker and cloud deployment services. Operating practice for canary analysis (population size, duration, metric selection) is in `arch-production-operations`.

## 1. Deployment versus release

- Deployment: new code runs in production but real interactions have not exercised it.
- Release: the feature is activated for users in a controlled way, with business impact. More frequent deployments lower risk while the business controls release timing.

API architectures decouple teams, but if deployment and release are inseparable, releases must be choreographed across teams, causing downtime and pressure on many services. Separation plus versioning and lifecycle prevents that. Warning sign: a legacy system where a UI plus server upgrade means downtime and slow rollback.

## 2. Feature flags

- State lives in a configuration store outside the application; the code ships with the feature off; a toggle (per user or global) selects the branch. In the case study a controller decides per user whether to call the modern Attendee API or the legacy store (a default of false in the flag call). Migrate a small batch of users, toggle back if wrong, continue to 100 percent.
- The flag service is a cross-cutting single point of failure: degrade gracefully with a last-known-value cache or safe defaults.
- Give every flag a unique name and remove the flag code when the migration is done. The cautionary tale in the notes: a reused flag plus a failed deployment cost about 460 million dollars at Knight Capital.
- Use flags first for an existing monolith with no routing layer; in-process flags are not realistic when many consumers already call out of process (use a gateway facade instead, `evolving-with-apis.md`).
- Verify (inferred in the notes): flag defaults tested with the flag service down; a stale-flag inventory with cleanup tickets; both branches tested.

## 3. Where traffic is shaped

At the API gateway ingress and in service mesh constructs. Kubernetes alone replaces the running deployment with a rolling update, and release configuration is a separate step that sets the strategy. Plain Kubernetes can split only by pod ratio (1 percent means 99 old pods plus 1 new), which is impractical; use gateway or mesh traffic shifting for precise weights.

## 4. Strategies

### Canary release
- Deploy v1.1 beside v1.0, route a small share (for example 1 percent), watch technical signals (latency, error rate) and business KPIs (conversion, checkout value), then shift progressively to 100 percent.
- The mesh lets you canary any internal service (for example the Session service gaining caching: watch the schedule-view KPI plus SLIs such as CPU).
- The same split supports A/B or multivariate tests (50/50, compare).
- Pros: tight exposure control, one extra instance set only (cheaper than blue-green), automatable rollback. Cost: needs good monitoring to detect trouble quickly.

### Traffic mirroring (dark launch)
- Duplicate live requests to the new version; discard its responses; evaluate out of band: compare refactored with existing results for correctness, or observe latency and CPU.
- Assesses operational performance, not business impact, because users never see the results.
- Caution (inferred in the notes): mirrored writes and side effects duplicate. Mirror only idempotent or read traffic, or stub the downstream.

### Blue-green
- A router, gateway or load balancer fronts two complete environments: blue (live) and green (next). Verify green, flip traffic at go-live; blue remains for quick rollback; the next release flips back.
- Best for coupled services (deploy legacy v1.1 and attendees v1.1 together as green). Simple and easier with persistent services, but take care with rollback when data or schema changed. Needs double the resources.

### Parallel versions (major breaking change)
Not a rollout but a lifecycle matter: run live and deprecated versions side by side (`specification-and-versioning.md`).

## 5. Choosing

| Situation | Strategy |
|---|---|
| Loosely coupled minor or patch change, good monitoring, limited blast radius wanted, business KPI validation wanted | Canary with gateway or mesh weights |
| Validate behaviour, performance or correctness of a refactor without user impact | Mirroring / dark launch |
| Consumer and producer coupled, released together | Blue-green |
| Existing monolith with no routing layer | Feature flags first |
| Compare two designs on user metrics | A/B split |
| Breaking major change | Parallel versions plus lifecycle |

Guideline (MAA Table 5-2): start by separating deploy and release of existing software (enables evolutionary architecture and simplifies the system); feature flags are a good way but can become a single point of failure; review the coupling between APIs and pick the strategy for the situation. Ask whether it is possible in the live systems, how coupled consumer and producer are, and whether the pipeline can enforce the loose-coupling requirements of traffic-managed APIs (compatibility tested).

## 6. Automating rollouts with metric gates

Rollouts should not be run by hand. In the Argo Rollouts example a Rollout resource (a Deployment plus a strategy) has 5 replicas and canary steps: set weight 20, pause until manual promotion, 40, pause 10, 60, pause 10, 80, pause 10. A command updates the image; a dashboard shows steps; an operator can promote or abort. Pod-ratio granularity applies unless integrated with a mesh or ingress gateway (NGINX, Ambassador) for finer weights.

Metric-driven promotion: an analysis template queries Prometheus; example success condition `result[0] >= 0.95` on the success rate; the Rollout progresses only when the criteria hold. The authors caution that raw success rate is simplistic because some failures are client errors rather than infrastructure faults.

Pipeline control for breaking changes: run the OpenAPI diff and fail the build on a non-backward-compatible spec unless the override is deliberate (`specification-and-versioning.md`).

## 7. Observability for rollouts

Single service means one log file; many hops mean many more failure points, and manual log hunting does not scale.
- Three pillars: metrics (periodic measurements; the platform chooses), logs (granular, prefer structured; insufficient alone), traces (follow one request across components; add a unique header as close to the origin as possible and propagate everywhere; across queues put it in the message envelope). Use OpenTelemetry to avoid vendor lock-in (metrics and tracing stable, logging newer at the time).
- Choose metrics with RED (rate, errors, duration) or the four golden signals (latency, traffic, errors, saturation). Applied mechanically they lose context. API context: 5xx means infrastructure or service failure; 4xx is the client's problem but a run of 403s may be an attacker probing and many 401s from a partner may mean a compromise or stolen token.
- Tie important metrics to alerts and avoid false positives (a low-traffic alert firing on weekends: restrict to business hours or tie to login counts).
- Case-study metric list: requests per minute for attendees; an SLO on average latency (deviation is an early warning); count of 401s from the partner system; availability of the Attendee service; memory and CPU; total attendees in the system as a business sanity metric.
- Read signals against a baseline or expected range. Early indicators (rising GC pause time, "strange engine noise") precede client-visible symptoms (API latency, "check-engine light"). In an outage start with traces. Practise incident response before the first real total outage.
- Signals to watch during a rollout (synthesised in the notes): error rate by status class, latency percentiles against baseline, saturation, business KPIs, 401/403 spikes, canary compared with stable; automate halt and rollback on breach.

Alert design with SLO arithmetic is in `arch-reliability-slos`.

## 8. Application-level gotchas

- Response caching hides failures: a canary looked fine, the rollout proceeded, then the caller's proxy cache expired and 500s appeared everywhere. During validation, send `Cache-Control: no-cache, no-store` on GETs; otherwise a cached result masks a broken new version. Gateways, proxies and CDNs in front may serve stale data and make rollout metrics lie.
- Header propagation: any service that terminates a request and calls another must copy tracing headers downstream. For auth headers decide deliberately what is safe to forward: forwarding the wrong credential lets a service impersonate another service or user. An OAuth2 bearer token is safe to send downstream over secure transport, but audience and token-exchange concerns exist (`arch-api-security`).
- Logging for debugging: keep two log types, a journal (sparse, important transactions and events) and diagnostics (failures, unexpected errors), with a log-type field in structured logs.
- Eventual consistency affects change at the application level (the notes give little detail; see `arch-replication-and-consistency`).

## 9. Opinionated platforms

Without a conscious decision each team re-solves tracing, headers, caching and logging, producing inconsistency. A platform team can build a paved path to production so these are solved once. Opinions are constraints: a trade-off between developer freedom and consistent behaviour, and adoption depends on making teams' lives easier.

Guideline (Table 5-3): treat developers as customers with a feedback channel; make key features transparent (auto-configure a library for OpenTelemetry); new apps get the latest stack, so plan how existing users receive new features. Discussion: which languages (can you centre on a few), can you run the platform as an internal product, which constraints add value (observability out of the box), how recommendations get pushed to teams already on it.

## 10. Verify

- Show that a deployment can be made with the feature off and released later without a redeploy.
- Flag tests: default value with the flag service unreachable; both branches; every flag has an owner and a removal ticket.
- For a canary: weights are configured at the gateway or mesh (not by pod count), a metric gate is wired, and an induced failure (return 500 from the canary build in staging) halts and rolls back automatically. Show the run.
- For mirroring: demonstrate that mirrored responses are dropped and that writes are not duplicated.
- For blue-green: rehearse the flip back, including any data or schema change.
- Rollout validation GETs bypass caches.
- One trace id appears across every hop of a sample request.
