# Availability with dependencies, redundancy claims and downtime arithmetic

Sources: SRE Workbook ch. 2 (modelling dependencies), ch. 6 (dependency arithmetic), ch. 3 (provider SLOs), ch. 5 (grouping services, canary exposure), ch. 8 (budget anchors), ch. 19 (platform and customer composition, reality of "five nines"); DDIA 2e ch. 2 (correlated faults, tail amplification, fault versus failure).

Use when a design states an availability number, depends on other services, claims redundancy across zones, or must pick an SLO that its dependencies can support.

## 1. Downtime budget table (arithmetic, 30-day window)

Allowed full-outage time = (1 - SLO) x window. The notes' own anchors: 99.99% is about 15 minutes per quarter (13 minutes by arithmetic over 90 days), 99.999% about 80 seconds per quarter, 99.98% about 26 minutes per quarter.

| SLO | Budget | Full outage allowed in 30 days |
|---|---|---|
| 99% | 1% | 7.2 hours |
| 99.5% | 0.5% | 3.6 hours |
| 99.9% | 0.1% | 43.2 minutes |
| 99.95% | 0.05% | 21.6 minutes |
| 99.99% | 0.01% | 4.3 minutes |
| 99.999% | 0.001% | 26 seconds |

The Home Depot's menu of uptime tiers (each step up costs significant investment): 99.5% for apps not used by store associates or an MVP of a new service; 99.9% for most non-selling systems; 99.95% for selling systems and services supporting them; 99.99% for shared infrastructure.

## 2. Composing availability

Rule from the notes: each critical dependency of availability P reduces your availability by a factor of P. A 99.99% service with nine critical 99.99% dependencies is 0.9999^10, about 99.9%, three nines.

Adaptation (standard probability, not a quotation):

- Serial (all must work): multiply availabilities, A = A1 x A2 x ... x An. Only critical dependencies count; a dependency you can survive without (cached, optional, degraded path) multiplies only the fraction of requests that need it.
- Redundant (any one suffices), only if failures are independent: 1 - (1 - A1)(1 - A2). The independence assumption is usually false, see section 3.
- A platform at 99.999% and a customer system that never exceeds 99% gives a best-case experience of 98.99901% (0.99 x 0.99999): the weakest link dominates, and the platform owner is held accountable regardless (Workbook ch. 19).

Planning procedure for a user-facing interaction:

1. List the critical dependencies on the request path for that interaction (from the architecture sketch).
2. Take each dependency's measured availability for that call, not its marketing number. Teams that believed they were at "five nines" typically measured 99.5% to 99.9% against honest SLOs (Workbook ch. 19; the notes call this anecdotal, from Google CRE experience, not a study).
3. Multiply. If the product is below the target for the journey, change the design instead of the arithmetic.
4. Record the result in the SLO document rationale.

## 3. Do not math your way out

Workbook ch. 2: two zones each at 99.9% do not give 99.9999%, because of shared dependencies, shared failure domains, shared fate and global control planes. DDIA 2e ch. 2 explains why: redundancy works best when faults are independent, but faults correlate (same rack, datacentre, same software). Software faults are highly correlated across nodes because every node runs the same code, so they cause more failures than hardware does; a leap-second bug or a firmware bug hits all replicas at once. Cascading failures spread overload between components.

Practical consequences for review:

- Reject an availability claim that multiplies replica failure rates without listing the shared components (DNS, load balancer, config push, identity provider, deployment pipeline, the same binary version).
- Ask which changes roll out to all replicas at once. Staged rollouts are the defence against correlated software faults (`arch-production-operations`).
- Prefer software-level fault tolerance across machines and availability zones to counting on one machine's hardware reliability; but treat the zones as one failure domain for anything global.

## 4. Dependency SLOs and what to do when one is too weak

- A critical dependency (its unavailability makes you unavailable) of a high-value interaction needs a guarantee at least as high as the dependent action. Its owning team owns its SLO the way you own your product SLO.
- If a component's inherent limit is below what the journey needs, engineer around it: a different component, caching, offline store-and-forward, graceful degradation (the quality SLI measures the share of undegraded responses).
- Do not derive your SLO from a provider's published SLO. The provider's global rollup can be green while your region or footprint suffers ("lost in the rollup"). Share your SLO and real-time performance against it with the provider, agree in advance that high SLO impact is treated as a priority incident with a shared bridge, and use the same dashboards (Evernote and Google CRE, `case-studies.md`).
- Alignment matters for paging too: misaligned SLOs between a service and its dependencies produce pages the team cannot fix (the on-call chapter lists it as an input to pager load; `pager-load-targets.md`).
- Each dependency should publish availability and latency SLOs for the APIs others call (Home Depot practice), so consumers can check fit before depending.

## 5. When a dependency causes the budget miss

Two schools: do not freeze, since it is not your fault; or freeze regardless. The second makes users happier. Decide per service and write the choice in the error budget policy (`error-budget-policy-template.md` lists the example's exceptions: company-wide networking problems, and another team's service that has itself frozen releases).

## 6. Latency composition and fan-out

When one user request fans out to many backend calls it waits for the slowest. The probability that at least one call is slow grows with the number of calls, so a bigger fraction of user requests is slow than the fraction of slow backend calls (tail latency amplification, DDIA 2e ch. 2). Consequences:

- Set tighter tail targets on backends called many times per user request. Amazon's internal targets use p99.9 because the slowest requests come from the customers with most data; p99.99 was judged too expensive, dominated by random events.
- Error amplification from retries: an error or timeout retried at several levels multiplies the total calls (Workbook ch. 7 on amplification). Prefer retrying at one layer, with backoff and jitter (the single-layer preference is an adaptation). Retry storms can sustain overload after the trigger is gone (metastable failure, `percentiles-and-nfr-targets.md`).

## 7. Grouping low-traffic services

For alerting you can combine microservices of the same product or request types of the same binary into one group, ideally those sharing a failure domain such as a common backend. Add longer-period alerts so a total failure of one member is not lost in the group (`alerting-on-slos.md`).

## 8. Checklist for a design review

- Is every availability claim backed by a product of measured critical-dependency availabilities, with the list of dependencies?
- For any "N replicas gives X nines" claim, are shared fate components named?
- Does the SLO of each critical dependency meet or exceed the journey's target? Where not, which workaround (cache, degrade, queue) is chosen?
- Are provider SLOs treated as input, not as your SLO?
- Is the retry policy single-layer with backoff, jitter and a cap?
- Is the policy for dependency-caused misses written down?
