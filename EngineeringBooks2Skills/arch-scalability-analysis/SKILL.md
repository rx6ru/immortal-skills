---
name: arch-scalability-analysis
description: Measure, model and judge how a system scales with the Universal Scalability Law (contention, crosstalk, retrograde scaling, throughput peak). Fits benchmark or production data with a bundled script, finds usable capacity at a latency target, sets forecast limits, diagnoses sublinear scaling, and audits scaling claims, charts and percentile reporting. Use when asked "will more nodes/threads/cores help", "how many servers or pool connections do we need", how much headroom is left, why throughput plateaus or drops as concurrency grows, to interpret a load-test or benchmark table, or to review a "scales linearly" claim. For designing a system from requirements use arch-system-design; for SLO and alert definitions use arch-reliability-slos; for running autoscalers and load shedding use arch-production-operations.
---

# Scalability analysis

## Purpose

Turn "does it scale?" into a measured function: throughput against a stated scale variable, fitted to a model with two physical penalties, checked, and then used for a decision (how many units, how much headroom, what to change). It replaces eyeballing a chart or trusting a vendor's "linear" claim, and it stops the usual mistake of reading maximum throughput as capacity.

## Choose what applies

| Situation | Do this | Read |
|---|---|---|
| Benchmark or load-test table (throughput against threads, connections, cores or nodes) to interpret | Fit the USL, read both coefficients, report peak and usable capacity | `references/measuring-and-fitting.md`, run `scripts/usl_fit.py` |
| "How many servers/threads/pool size do we need?" with measurements available | Fit, solve for the load at the latency target, apply the 2x forecast rule | `references/capacity-planning.md` |
| "How many servers do we need?" with nothing built yet | Back-of-envelope arithmetic with explicit units; hand the design method to `arch-system-design` | `references/capacity-planning.md` section 6 |
| Throughput flat or falling as load rises; "we added cores and got slower" | Decide contention versus crosstalk, then search for the cause | `references/interpreting-and-improving.md` |
| Design doc, vendor page or PR says "scales linearly", "97 percent scaling", "shared-nothing so linear" | Per-node and efficiency arithmetic; chart audit | `references/limits-and-pitfalls.md` |
| Latency reported as an average, or p99 averaged across hosts, or SLO of "fast" | Percentile rules, tail amplification, client-side measurement | `references/percentiles-and-load.md` |
| Choosing the degree of parallelism of a scatter-gather or parallel query | Speedup form of the model; minimum of R(N) | `references/usl-model.md` section 8 |
| Want a full replay with real numbers to copy the method | Cisco MySQL data end to end | `references/worked-example.md` |
| Fewer than about six measurements, or a single known hard cap (for example exactly the core count) | Do not fit; measure more, or reason from the cap (see Proportion and limits) | this file |
| Question is about correctness of replicas, transactions or shard keys, not throughput | Not this skill | `arch-replication-and-consistency`, `arch-transactions` |
| Question is about in-process locks and thread safety | Not this skill | `craft-concurrency` |

## How to apply

Work through these in order; skip steps the situation does not need.

1. **Name the question.** Diagnose (is it scaling worse than it should), forecast (how much can I count on), or audit (is this claim honest). The same fit is read differently: as a pessimistic baseline for diagnosis, as a best case for forecasting.
2. **Define the scale variable N.** Size (cores, nodes, partitions) with per-unit work held constant, or load (threads, connections, concurrency) on fixed hardware. Three things interact: drivers, servers, data. Change one, scale the others in proportion. A fixed dataset with more nodes manufactures fake superlinear scaling. Write the definition down.
3. **Get data.** Pairs (N, steady-state mean throughput), plus mean latency per N. At least six points, a dozen or more preferred, spread from low N to near the knee. If you only have throughput and latency, concurrency is N = X * R (Little's Law). Sources and recipes: `references/measuring-and-fitting.md`.
4. **Sanity-check without a model.** Compute throughput per unit (X/N) and efficiency X(N) / (N * X(1)). Linear means per-unit throughput is constant. Draw the ideal line on any chart you produce.
5. **Fit.** `python3 scripts/usl_fit.py data.csv --predict ... --latency-target ... --holdout 0.33`. The model is

   ```
   X(N) = lambda*N / (1 + sigma*(N-1) + kappa*N*(N-1))
   ```

   lambda is throughput at N = 1, sigma the contention (serialization) penalty, kappa the crosstalk (coherency) penalty. Fit in the (N, X) domain, never latency against throughput. Stop at the knee: points past the peak belong to a different regime.
6. **Judge the fit before using it.** R^2 and a plot; coefficients non-negative; fitted lambda near measured X(1); a hold-out fit on the first third predicting the rest; model latency N/X agreeing with observed. A negative sigma is a measurement problem until proven otherwise.
7. **Read the coefficients.**

   | Fit | Meaning | Where to look |
   |---|---|---|
   | sigma only | Amdahl: ceiling lambda/sigma, speedup limit 1/sigma (5 percent serial is 20x) | serial sections, global locks, single-threaded stage, sequential gather |
   | kappa > 0 | peak at Nmax = sqrt((1 - sigma)/kappa), then throughput falls | shared mutable state, all-to-all sync, consensus or replication fan-out |
   | both | both penalties; compare their terms at your operating N | the larger term first |

   Queueing can only cap throughput; only service-time inflation (crosstalk) makes it fall.
8. **Forecast.** Peak is X(Nmax) (or lambda/sigma when kappa = 0). Usable capacity is the throughput at the largest N whose mean response time meets the target, from R(N) = (1 + sigma*(N-1) + kappa*N*(N-1))/lambda. Do not forecast past 2x the measured size or throughput, whichever comes first. Report a range, treat the number as best case, and name limits the model cannot see (core count, bandwidth, queue caps).
9. **Recommend a change, with a prediction.** Reduce sigma by shrinking or removing serial sections and lock hold times. Reduce kappa by cutting shared mutable state and pairwise synchronisation. If crosstalk cannot be removed, partition into smaller independent systems. State which coefficient should move and by roughly how much.
10. **Re-measure after the change** with the same design and refit. If the targeted coefficient did not move, the bottleneck is elsewhere.

### Quick formulas

| Need | Formula | Note |
|---|---|---|
| Efficiency at N | X(N) / (N * X(1)); under the model 1 / (1 + sigma*(N-1) + kappa*N*(N-1)) | 72 percent at N = 4 for lambda 1800, sigma 0.05, kappa 0.02 (5,180 of 7,200) |
| Speedup ceiling, kappa = 0 | 1 / sigma; throughput ceiling lambda / sigma | sigma 0.05 is 20x, 0.03 about 33x |
| Peak load | sqrt((1 - sigma) / kappa) | needs kappa > 0 |
| Mean response time at concurrency N | (1 + sigma*(N-1) + kappa*N*(N-1)) / lambda | equivalent to N/X by Little's Law |
| Concurrency at latency target R | (kappa - sigma + sqrt(sigma^2 + kappa^2 + 2*kappa*(2*lambda*R + sigma - 2))) / (2*kappa) | then X = N/R; script: `--latency-target` |
| Best parallel degree of one request | N that minimises (1 + sigma*(N-1) + kappa*N*(N-1)) / (lambda*N) | same Nmax (my derivation) |

### Decision rules used most

- Maximum throughput is not capacity: near the peak, latency percentiles are poor. Quote throughput at the latency target.
- Latency is not a function of throughput when kappa > 0 (the curve folds into a nose); throughput is a function of latency.
- Percentiles, not means, for user experience; never average percentiles; measure on the client side. The USL gives means, so a percentile SLO needs separate evidence (`references/percentiles-and-load.md`).
- Peak exists only if kappa > 0. Tiny kappa still ends scaling: kappa under 0.001 stopped the Cisco benchmark at about 35 threads.
- A forecast from few small-N points is the least reliable at the peak: the ten-point example predicted 16,049 QPS against 12,341 from the full data.
- Forecast stance is optimistic-best-case; diagnosis stance is pessimistic-baseline. Say which one you are using.

### If the script is not an option

Any nonlinear least-squares fitter does the same job. With SciPy (adaptation, not from the book):

```python
from scipy.optimize import curve_fit
usl = lambda n, lam, sig, kap: lam*n/(1 + sig*(n-1) + kap*n*(n-1))
(lam, sig, kap), _ = curve_fit(usl, N, X, p0=(X[0], 0.05, 0.001), bounds=(0, [1e12, 1, 1]))
```

Good start values are lambda near the N = 1 throughput and small positive sigma and kappa (the source used 0.1 and 0.01 with R's nls). A fit pinned to a bound is a warning, not a result.

### Typical outcomes and what to tell the user

| Outcome | Say this |
|---|---|
| Clean USL shape, peak inside measured range | Here is the peak, here is usable capacity at your latency target; the operating point is at X percent of it |
| Clean shape, peak far beyond measured range | The peak figure is unreliable (over 2x the data); trust only the trend and the near-term forecast |
| Throughput flat then abrupt plateau | The model cannot see the cap; look for a saturated resource (cores, bandwidth, pool) and measure it directly |
| Negative sigma | Check setup first (fixed dataset, idle threads counted, warm caches) before reporting superlinear scaling |
| Scatter, no USL shape | Do not force a fit; fix the measurement (steady state, constant regime) or collect more points |

### Report template

Use this shape when handing results to the user; it forces the checks above to be visible.

```
Scale variable N: <definition, what is held constant per unit>
Data: <points, range, steady-state means, source>
Fit: lambda=<..> sigma=<..> kappa=<..>  method=<nls|linear>  R^2=<..>  hold-out error=<..>
Peak: Nmax=<..>, X(Nmax)=<..>   (or ceiling lambda/sigma if kappa ~ 0)
Usable at <latency target>: N=<..>, X=<..>; current load = <..> percent of usable
Dominant penalty: <contention|crosstalk>, suspected cause: <..>, how to confirm: <..>
Confidence: <inside 2x of measured range? signals the model cannot see?>
Next step: <change + predicted coefficient movement + re-measurement>
```

### Review questions for a scaling claim or design

1. What is N, and what is held constant as it grows? If unstated, the claim cannot be checked.
2. What is throughput per unit at the largest N compared with N = 1?
3. Where is the single point everything passes through (lock, leader, queue, sequence, coordinator)? That is sigma.
4. What must every unit tell or ask every other unit (invalidation, gossip, consensus, shared counter)? That is kappa.
5. What happens to latency percentiles at the claimed load, measured at the client?
6. Is the dataset, driver count or key space scaled with the nodes, or held fixed?
7. If the design is "just add nodes", what is the plan when the peak arrives: partition, or accept the plateau?

## Verify

Show the user evidence, not only conclusions.

1. **Tool self-check.** Run `python3 scripts/usl_fit.py --self-test`; it must report all checks passed before you rely on the script in a new environment.
2. **Data checks (state each result).** Number of points and N range; N defined and per-unit load held constant; steady-state means; X(1) measured or flagged as missing.
3. **Fit checks.** R^2, maximum relative error, coefficient signs, fitted lambda against X(1), hold-out mean and maximum error and which N was worst. If the script printed any WARNING, quote it and say what you did about it.
4. **Plot or table check.** The chart or table shows the ideal line, numbered axes from zero, points rather than only a smooth curve, and the fitted curve cut off at the knee.
5. **Forecast checks.** Every predicted N is within 2x the measured size and every predicted throughput within 2x measured throughput, or is labelled low confidence. Peak and usable capacity are both stated, and current load is expressed as a fraction of usable capacity.
6. **Latency cross-check.** Observed N/X at the claimed operating point is at or below the target (the Cisco example: the ten-point forecast said N = 17 met 1.5 ms, the data show 1.68 ms there and 1.49 ms at N = 14).
7. **Change check.** After an improvement, the refit shows the targeted coefficient lower and Nmax or peak higher; otherwise report that the change did not address the bottleneck.
8. **Claim audit.** For a scaling claim, show per-node throughput and efficiency computed from the cited numbers (for example 182k TPS at 3 nodes versus 449k at 12 is 60,700 versus 37,400 per node, 39 percent below linear).

Done means:
- N, throughput unit and held-constant factors are written down.
- Coefficients, fit quality and hold-out error are reported, with the script warnings addressed.
- Peak and usable capacity at a stated latency target are given, with forecast horizon and confidence.
- The dominant penalty is named with a concrete suspected cause and a way to confirm it, or the analysis says honestly that the data cannot tell.
- Any recommended change has a predicted effect on a named coefficient and a re-measurement step.
- Nothing is claimed beyond 2x the measured range without a label saying so.

## Proportion and limits

- Do not run the whole procedure for a small question. A ten-line answer built on per-unit throughput and an efficiency figure is enough when someone asks whether a claim is plausible.
- The USL is a macro model. It cannot see a hard cap (every core busy, a bandwidth limit, a saturated queue) and cannot predict regime shifts; use CPU, network and queue data for those. It is usually good up to the knee only.
- With fewer than about six points, or points clustered at low N, coefficients are unstable. Collect more data instead of fitting harder. The script's thresholds (R^2 below 0.95, lambda off by more than 10 percent) are heuristics, not the book's.
- Early products: scaling work done before the bottleneck dimension is known is wasted or locks in inflexibility. Plan about one order of magnitude ahead. A single well-sized machine often beats a distributed design.
- Contested or dated: variants such as logarithmic crosstalk and AISSL are conjectures without derived mechanism; do not adopt them without a reason from the system. Source examples (MySQL 5.0 era benchmark, hardware failure rates) are dated; the method is not. Whether to fix lambda at the N = 1 measurement (Gunther) or fit it (Schwartz) is a judgement; state which you used.
- Superlinear scaling is real in cases (more memory per node) but usually a measurement or setup artefact; check the setup first.
- Cost: the method needs controlled benchmarks across many N; production data is noisier but plentiful.

## References

- `references/usl-model.md`: equations, symbols, derived quantities (peak, efficiency, asymptote), response-time forms, speedup form, variants, which equations are reconstructed. Read when you need a formula or must explain the model.
- `references/measuring-and-fitting.md`: defining N, benchmark design, data sources, cleaning, fitting recipes (script, R, Python), judging a fit, bad-data symptoms. Read before collecting or fitting data.
- `references/interpreting-and-improving.md`: contention versus crosstalk causes and fixes, the partition rule, PayPal case, architecture families, searching a repository for causes, verifying an improvement. Read when scaling is poor and you must act.
- `references/capacity-planning.md`: forecast rules, maximum versus usable capacity, headroom example, back-of-envelope arithmetic, fan-out, autoscaler bounds, Pokemon GO lessons, capacity statement checklist. Read for sizing or forecast questions.
- `references/percentiles-and-load.md`: load parameters, response-time vocabulary, percentiles, tail amplification, retry storms, scale-up versus scale-out, scaling principles. Read when latency reporting or overload behaviour is in question.
- `references/limits-and-pitfalls.md`: what the model cannot see, superlinear checks, models to reject, claim and chart audits. Read when reviewing a claim, a chart, or a surprising fit.
- `references/worked-example.md`: full replay on the Cisco MySQL benchmark, with data, commands and numbers. Read to copy the method or to test your understanding.
- `scripts/usl_fit.py`: CSV to coefficients, goodness of fit, peak, predictions, usable load at a latency target, hold-out, warnings. Standard library only; `--help` and `--self-test` available. Refuses unusable input (missing file, fewer than three numeric rows or distinct N, non-positive values, throughput that never rises) with a message on stderr and exit code 2, and reports skipped unreadable rows as warnings.

## Sources

- Schwartz, Practical Scalability Analysis with the Universal Scalability Law (2015): scalability as a function, linearity tests, USL derivation, queueing relationship, measuring and fitting, response-time modelling, capacity planning, improving scalability, limits, superlinear scaling, hardware, software and MPP forms, conclusions.
- Site Reliability Workbook ch. 11 (Managing Load): autoscaling constraints, case studies, interaction failure modes.
- Site Reliability Workbook ch. 12 (Non-Abstract Large System Design): capacity arithmetic only.
- Designing Data-Intensive Applications 2e ch. 2: load parameters, fan-out case study, response time and percentiles, tail amplification, metastable failure, scalability architectures and principles.
