# Pipeline reliability (SRE practices and maturity matrix)

Read this when a pipeline is going into production as a service, is missing its freshness target, delivers stale or wrong data, or needs SLOs, a rollout plan, a failure playbook or a maturity assessment.

Contents: 1 Pipeline types and triage; 2 SLOs for pipelines; 3 Dependencies and disaster recovery; 4 Documentation; 5 Development lifecycle; 6 Hotspotting; 7 Autoscaling and resources; 8 Access control; 9 Escalation; 10 Technology feature table; 11 Idempotent and two-phase mutations, checkpoints; 12 Maturity matrix; 13 Failures: delay and corruption; 14 Case study: event delivery; 15 Design checklist; 16 Verify.

Source: SRE Workbook ch. 13 unless marked. For SLO and alerting arithmetic see `arch-reliability-slos`; for canary mechanics see `arch-production-operations`.

## 1. Pipeline types and triage

A pipeline is a multi-stage process: each stage is a separate process whose output feeds the next.

- ETL or event processing: extract from sources, transform (add or remove fields, aggregate across sources, index for serving), load into a target. Examples: ML and BI preprocessing, event counts per interval, billing reports, search indexing.
- Analytics and BI: example is a game whose tables are updated three times a day by an analytics product; a job triggers on new data and writes a daily aggregate table.
- Machine learning: (1) extract features and labels, (2) train, (3) evaluate on a test set, (4) serve the model, (5) other systems use the responses. In the worked example, new products must enter recommendations within 12 hours; the model must pass accuracy checks on a test set before promotion. Symptom: a new model sometimes unpublished for more than 24 hours and intermittent recommendation errors.

Triage questions when recommendations or decisions are missing, stale or wrong:
1. Is data stuck before preprocessing?
2. Is the model bad (software bug, spam, poor features)?
3. Was a new model version generated, or is a stale one serving?

## 2. SLOs for pipelines

Alert before the error budget is exhausted.

Freshness forms:
- X percent of data processed in Y time.
- The oldest data is no older than Y.
- The pipeline job completed successfully within Y.
Example: 99 percent of user actions affecting score appear on the scoreboard within 30 minutes.

Correctness: hard when no predefined correct output exists. Create golden data (for example test accounts with expected output you compute), run it through production, compare expected with actual and alert on discrepancy thresholds. A backward-looking form: no more than 0.1 percent of invoices incorrect per quarter; or the number of hours or days bad data was served.

Isolation: if you promise a tighter SLO for high-priority data, process it first when resources are tight. Use separate queues or jobs, workers that take the highest-priority tasks, and differently provisioned worker pools (memory, CPU, network tiers), retrying failed work on higher-provisioned workers.

End-to-end measurement: customers see the sum of stages. Per-stage SLOs force tight alerts that do not model user experience, and per-stage correctness can miss end-to-end corruption. Example: an upstream stage adds a field and expects a downstream stage to use it; the downstream stage does not expect it and drops it; both report healthy and users never see the data. Measure the SLO end to end, preferably from an independent system.

## 3. Dependencies and disaster recovery

Design for the largest failure allowed by your dependencies' advertised SLAs. If single-region storage availability is below what your SLO needs, replicate across regions. Depending on stronger guarantees than the provider advertises means you can fail while they remain in SLA; sometimes accept a looser SLA for customers instead.

Planned outage drills (the authors simulate regional outages): planned pipelines fail over automatically, others are delayed until an operator fails over by hand (which needs enough resources to bring up the stack elsewhere). Worst case: jobs keep processing stale data and pollute downstream; recovery may need restoring from backup and reprocessing. Practise disaster recovery, assess dependencies, automate responses.

## 4. Documentation

Three kinds:
- System diagrams: each component (applications and data stores) and each transformation, since each can introduce configuration bugs. Include live status links (waiting, processing, complete) and historical run times that foreshadow degradation. Use them to analyse data dependencies before launches.
- Process documentation: release a version, change a data format, rare manual tasks such as turn-up and turn-down in a region. Automate, then generate documentation from the source.
- Playbook entries for every alert, linked from the alert message.

## 5. Development lifecycle

Stages: prototype, 1 percent dry run, staging, canary, partial deployment, production.

| Stage | Purpose and rules |
|---|---|
| Prototype | verify semantics; choose language and model (batch vs streaming); unit tests for added features |
| 1% dry run | run the full stack on a subset of production data in a non-production environment; scale gradually and track bottlenecks; keep performance testing after launch |
| Staging | data as close to production as possible (full copy or representative subset); data must flow end to end, since unit tests miss integration issues; A/B compare new output with previous known-good output |
| Canary | pipeline tests take longer than for stateless jobs because data persists; tie the canary to the whole pipeline; it may process real data but skip production writes (two-phase mutation); wait a full processing cycle to see customer-impacting problems; compare with live. Region-by-region progression is often impossible for replicated pipelines, so roll out to a small percent of data or in dry-run mode first. Verify with SLO metrics, automate verification |
| Partial deployment | a flag or config admitting a subset of data: one or two accounts, then about 1, 10, 50, 100 percent. Failure routes: bad or delayed input, processing bug, storage error. Do not promote corrupt data to low-latency frontends |
| Production | restore a known good state quickly (roll back binaries); mark potentially broken data as bad (replace from backup, block jobs from reading it, reprocess) |

## 6. Hotspotting

Examples: many workers hitting one serving task; one machine holding a hot piece of data (an overloaded tablet); row-lock contention; disk head contention (use SSD); one huge work unit. Mitigations: block fine-grained bad records so the rest progresses; framework dynamic rebalancing by splitting work; an emergency flag to skip input matching a pattern or a problematic user; restructure data and access patterns; reduce load with static allocation; finer lock granularity.

## 7. Autoscaling and resources

Do not provision for peak all the time; this matters most for streaming and variable loads (batch jobs expand to consume everything available). Plan growth; weigh resource cost against engineering effort; include storage and cross-region replication and network costs; prune unused data. Measure the SLO end to end but resource efficiency per stage, to find which job caused a usage jump.

## 8. Access control

No PII in temporary storage (or encrypt it); least privilege per stage; TTL on logs and PII; separate projects or instances per function for finer scoping; a master project with cross-project views for controlled client access.

## 9. Escalation

Design so a machine or zone failure never pages on SLO violation; by the time you page, automation is exhausted. With good SLO alerting you hear before customers do; communicate proactively.

## 10. Technology feature table (what to look for)

| Concern | Look for |
|---|---|
| Latency | streaming, batch or both APIs; an interchangeable API lowers migration cost |
| Data correctness | exactly-once semantics (unneeded if work units are idempotent); two-phase mutations; windowing functions; black-box monitoring; flow control gating a job until its inputs complete |
| High availability | multihoming; autoscaling |
| MTTR | code changes tied to a release for fast rollback; tested backup and restore; easy region drain; alerts, dashboards and logs that explain why data is delayed or corrupt; data checkpointing |
| MTTD | SLO monitoring; alert on symptoms not causes |
| Development lifecycle | a canary environment before production |
| Resource inspection | accounting dashboard including storage and network; a metric that correlates with growth |
| Ease of development | fitting language; simple API (simplicity against flexibility); reuse of libraries, metrics and reporting |
| Ease of operation | reuse existing automation; automate infrequent big tasks (moving the stack from region A to B) with health checks on the new stack before production |

## 11. Idempotent and two-phase mutations, checkpoints

- Idempotent mutation: applying it several times gives the same result; rerunning a pipeline on the same input always yields the same output, so reprocessing does not duplicate or corrupt stored data.
- Two-phase mutation: write the mutations to a temporary location; a verification step or separate pipeline validates them; a follow-up step applies only verified mutations. Used for canaries and testing so an owner approves outputs before they touch production.
- Checkpointing: periodically save partial state so long-running work resumes after failure, preemption or rescheduling (for example changed CPU or memory limits). The job shuts down cleanly and on restart detects which work units are done; it also skips expensive reads and computation. Especially valuable for model training where each iteration depends on the previous.
- Code patterns: shared libraries (add a metric once and get it in all pipelines; a generic freshness alert); microservice-style pipelines (smaller single-purpose pipelines released and monitored separately instead of a monolith).

## 12. Maturity matrix

Score each row 1 (chaotic) to 5 (continuous improvement); if two milestones apply use 2 or 4. Spend effort on the weak rows; prefer existing products or open source over building.

| Category and row | 1 | 3 | 5 |
|---|---|---|---|
| Failure tolerance: failover | none | some work-unit retries, even manual | multihomed with automatic failover |
| Failure tolerance: global work scheduling | none | hot/hot/hot (same work in all three regions so one survives) | effective warm/warm/warm (spread work across three regions, store centrally to survive loss of a region) |
| Failure tolerance: failed task management | none | (not stated) | automatic retry of failed work units and automatic quarantine of bad work units |
| Scalability: autoscaling worker pool | manual | works with extra manual tools | built in, no third-party configuration |
| Scalability: dynamic resharding | fixed work units | manual resharding, or automatic with extra code | built-in dynamic subsharding to balance |
| Scalability: load shedding and prioritisation | none | some prioritisation | easy prioritisation, built-in shedding, workers handle preemption notices and clean up |
| Monitoring: debug tools | no logs, no tracking of failed units | can identify failed unit and extract logs | logs from the failure time retrieved directly from the failed unit; automatic quarantine and replay |
| Monitoring: dashboards | none | easy to configure; work units per stage, latency and aging per stage | fine-grained execution map, delay up to each stage, throttling rationale, limiting factors, worker internal state, failing/stuck/slow counts, historical stats |
| Implementation: discoverability | none | partial or manual | automatic global registry of configured pipelines |
| Implementation: code | large setup cost | some reusable components | base frameworks, minimal code, machine-readable config, zero-config, familiar library semantics |
| Implementation: documentation | sparse or outdated | minimal setup docs | comprehensive, current, with training examples |
| Testing: unit framework | none | slow tests, timeouts, heavy resources, no coverage, easy data-source switch | sanitizers, minimal build dependencies, coverage, debugging info, no external dependencies, built-in test data generation |
| Testing: ease of configuration | none, or heavy learning with a different language or API | first integration test costly, later ones copy and extend | decoupled from production config yet reusable |
| Testing: integration framework | needs in-house tools | minimal docs, long runs even for small inputs, hard on-demand triggering, hard to separate prod from non-prod (for example event logs going to prod logging) | scaled-down input, output diffing, configurable monitoring for test runs, ample docs and examples |

## 13. Failures: delay and corruption

Most common: data delay and data corruption. Track MTTD and MTTR per outage; postmortems look for patterns and toil.

Delayed data (input or output): downstream stages must not start without their data. Stale data is almost always better than incorrect data: stall and resume rather than process incomplete or corrupt data, because reprocessing prolongs outages. Create data dependencies that all stages respect. Batch stages wait for predecessors; streaming with event-time processing can start portions as upstream portions finish. Notify dependent services and customers. For debugging, want progress of current and past runs, log links, a data-flow diagram, and the ability to trace a unit of work with counters.

Corrupt data: causes are software bugs, data incompatibility, unavailable regions, configuration bugs. Prevent with corruption tests and alerts, blocking policies, abuse and spam detection. Response in two steps: (1) mitigate: stop more corrupt data entering; (2) restore from a known good version or reprocess. Drain a bad region; roll back a bad binary. Reduce reprocessing cost with selective reprocessing (only affected users or accounts) or persisted intermediates as checkpoints. Corrupt output can propagate downstream; recovery is labour-intensive and hard to automate.

Causes to consider:
- Pipeline dependencies (storage, network or other services throttling or refusing writes; hotspots; storage bugs): file a ticket, allow time to add resources; load balance and drop low-priority data.
- Application or configuration (bottleneck, bug, performance regression, out-of-memory, abusive data prone to hotspots, wrong input or output location configs): roll back binary or config, cherry-pick a fix, repair permissions, restructure problem data. The most common cause; vet binaries and configs in non-production first.
- Unexpected resource growth: autoscale but expect strain on downstream dependencies; know how to request emergency resources and the lead time; interim measures such as prioritising data classes.
- Region-level outage: singly-homed pipelines stall; multihomed with automatic failover may just drain; stranded or delayed data can make dependents' output incorrect.

## 14. Case study: event delivery at scale

System: hundreds of billions of events a day, used for A/B analysis, play counts, personalised playlists and royalty payment. Delivered events go into hourly buckets partitioned by event type; buckets are the only interface for data jobs, and SLOs are defined on bucket delivery per event type.

Architecture lessons:
- A managed log service decouples collection from delivery (independent failure domains).
- Full event-type isolation: each type has its own topic and dedicated ETL instance. ETL is three single-responsibility pieces: a service consuming the stream, a service assigning events to hourly partitions, and a batch job that deduplicates and writes the final location.
- Event types are enabled or disabled by configuration; resources are right-sized by an autoscaler because the needs of a new event type are unknown.

Three SLO types, measured by independent external systems:
- Timeliness: maximum delay to deliver an hourly bucket, measured from the earliest theoretical close time (a bucket for hour 13 closed at 14:53 is 53 minutes late). Three priority tiers per event type. Downstream jobs poll dependency bucket status before processing.
- Skewness: maximum percentage of data misplaced per day. Heuristics decide when a bucket is complete; late events can land in a wrong future bucket, so jobs under-report then over-report.
- Completeness: percentage of events delivered after being successfully published, from a daily audit comparing published and delivered counts.
Skewness and completeness SLOs are offered only for finance-bearing events, flagged by the customer; others are best effort. Events are assigned to buckets by server receive time, not client time (clients buffer offline up to 30 days and can change clocks). No SLO on data quality: the postal-service analogy, delivered on time, intact and unopened; quality belongs to producing teams.

Customer integration: a fully managed service with limited functionality (one publish format, hourly buckets, one serialisation). Delivery must be explicitly enabled with a finance flag, a timeliness tier and a named event owner (accountability and an incident contact). Documentation treated like software: every support request is a documentation bug or a product bug.

Operating lessons:
- SLO alerts fire after customers are hit, so also monitor components (CPU as a basic health signal, building up to richer metrics). Keep logs deliberately limited; reading logs is a last resort.
- Capacity: components share one cloud project quota; provision for about 50 percent CPU at peak. Autoscaler pitfall: it relies on CPU correlating with work, so daemons or instances burning CPU without work make it scale out until resources run out. Cap maximum instances, restrict daemon CPU, throttle a component's CPU when no useful work is detected, and still capacity-plan.
- Development: testing pyramid (many unit tests, fewer integration tests on the public API, a black-box end-to-end test); peer review and green tests before merge; because failure stalls all data processing, deploy in stages with manual approval between staging (mirrored representative production traffic), a production canary subset, and full rollout.
- Incidents: mitigate first; make no major changes during incidents except rollback of recent deploys. Freshness breach: customers wait. Completeness or skew breach involves customers: redeliver from the last known-good checkpoint (incompleteness) or reshuffle events into the right buckets (skew), both manual; advise customers to reprocess.
- History: earlier versions paged engineers every few nights; the redesign was modular, single-purpose, offered as a product with SLOs, developed and operated by one team across its lifecycle, on proven external services.

## 15. Design checklist

- [ ] Freshness, correctness (golden data) and isolation SLOs defined end to end, measured externally.
- [ ] Dependency SLAs checked; multi-region plan; disaster recovery drill.
- [ ] Idempotent writes; two-phase mutation for canary; checkpoints; data-dependency gating (stale beats wrong).
- [ ] Quarantine of bad records; emergency skip flag; per-stage resource metrics; autoscaler maximum cap and quota.
- [ ] Lifecycle: unit, 1 percent dry run, staging with A/B diff against known-good output, canary on a data subset, ramp 1/10/50/100 percent.
- [ ] Playbook per alert; diagrams with live links; backup and restore and region drain tested; maturity matrix scored.

## 16. Verify

- Show the SLO definitions (freshness, correctness, isolation if tiered) with the number, the window and where each is measured.
- Show a golden-data test flowing through the real pipeline and the alert that fires when its output is wrong. Inject a wrong value to prove the alert fires.
- Show a delayed-input drill: hold back an upstream input and confirm downstream stages wait instead of producing incomplete output.
- Show a corruption drill: inject a bad record or bad binary in staging; show quarantine, blocking of downstream reads, and the restore or selective reprocess path with timing.
- Show a rerun with the same input produces the same stored output (idempotent mutation).
- Show the maturity matrix scored with the lowest rows chosen for work.
