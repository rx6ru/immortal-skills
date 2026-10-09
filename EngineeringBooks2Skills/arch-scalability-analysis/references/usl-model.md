# The Universal Scalability Law: equations, meaning, derived quantities

Source: Schwartz, Practical Scalability Analysis with the USL (2015), sections 1-3 and 5; the response-time and MPP forms from the "Modeling Response Time" and "Hardware, Software, and MPP" sections. DDIA 2e ch. 2 for the general definition of scalability.

Contents
1. Symbols
2. What scalability is
3. Building the model in three steps
4. Behaviour table
5. Derived quantities (peak, efficiency, asymptote, speedup limit)
6. Response-time forms and the "nose"
7. Why the two penalties differ physically
8. Speedup form for parallel (scatter-gather) work
9. Variants and their status
10. Provenance of each equation (what is verbatim, derived, reconstructed)
11. Code sketch

## 1. Symbols

| Symbol | Meaning | Unit |
|---|---|---|
| N | the scale variable: size (cores, nodes) or load (threads, connections, concurrency) | count |
| X(N) | throughput: completed requests per second | req/s |
| lambda | coefficient of performance: throughput at N=1, slope of the ideal line | req/s |
| sigma | contention / serialization penalty (Gunther: contention) | dimensionless, 0 to 1 |
| kappa | crosstalk / coherency (consistency) penalty | dimensionless, usually small |
| R(N) | mean response time (= latency = residence time) | seconds |
| Nmax | N at which X(N) is largest | count |

## 2. What scalability is

Scalability is a function: scale variable on the x axis, throughput on the y axis. Do not mix it up with performance (how fast at one size), efficiency, capacity or availability (ch. 1 notes). Two systems with different lambda (say 1800 and 800 req/s) perform differently but scale identically if both are linear.

Pick the x axis deliberately. Either size (CPUs, nodes, with work per unit held constant) or load (threads, connections, concurrency on fixed hardware). Benchmark threads that send with zero think time and wait for each answer make the arrival rate depend on back pressure, so what you vary is "amount of work requested" and what you read is completion rate.

DDIA 2e ch. 2 adds the practical framing: "X is scalable" is not a meaningful sentence. Ask: if load grows in this particular way, what are the options, how do resources get added, and where does the current architecture stop?

## 3. Building the model in three steps

1. Ideal linear: `X(N) = lambda * N`. Equal return on every unit added.
2. Add contention, giving Amdahl's Law: `X(N) = lambda*N / (1 + sigma*(N-1))`. Throughput rises toward an asymptote `lambda/sigma`. Maximum speedup is `1/sigma`: sigma = 0.05 gives 20x, sigma = 0.03 about 33x. Shows up as the final gather step of scatter-gather, a global lock, a single-threaded stage.
3. Add crosstalk, giving the USL: `X(N) = lambda*N / (1 + sigma*(N-1) + kappa*N*(N-1))`. The kappa term counts pairwise interactions (N(N-1) edges of a fully connected directed graph, order N squared). Gunther's older name for a slightly different form is "superserial". Gunther also defines hardware and software forms of the USL: the same equation with different symbols, which the source treats as interchangeable; what matters is knowing exactly what N means. A quadratic term eventually beats the linear numerator however small kappa is, so throughput peaks and then falls (retrograde scaling).

Sanity numbers from the source: sigma = 0.05, kappa = 0.02, lambda = 1800, N = 4: denominator 1 + 0.15 + 0.24 = 1.39, so X = 4*1800/1.39 = 5180 req/s against an ideal 7200: 72 percent efficient. Plotted to N = 20 it is very inefficient and effort to scale past about 6 is wasted.

## 4. Behaviour table

| sigma | kappa | Behaviour |
|---|---|---|
| 0 | 0 | Linear, unbounded |
| > 0 | 0 | Amdahl: asymptote at lambda/sigma, no decline |
| >= 0 | > 0 | Peak at Nmax, then retrograde |
| < 0 | any | Superlinear region. Suspect the measurement first (see limits-and-pitfalls.md) |

## 5. Derived quantities

| Quantity | Formula | Status |
|---|---|---|
| Efficiency | `X(N) / (N * X(1))`; under the model this equals `1 / (1 + sigma*(N-1) + kappa*N*(N-1))` | definition from the source; model form stated there |
| Peak load | `Nmax = sqrt((1 - sigma) / kappa)`, exists only if kappa > 0 | source eq. 4; the notes show it follows from setting dX/dN = 0, which gives kappa*N^2 = 1 - sigma |
| Peak throughput | `X(Nmax)` by substituting into the USL | source |
| Asymptote when kappa = 0 | `lambda / sigma` | source |
| Per-node throughput | `X(N)/N`, constant iff linear | source: the test of linearity |
| Model value at N = 1 | `X(1) = lambda` (the denominator is 1) | direct from the equation |

Peak throughput is not usable capacity: near the peak, latency percentiles are almost always bad (see capacity-planning.md).

## 6. Response-time forms and the "nose"

Little's Law, eq. 5: `N = X * R` (mean number in the system = throughput times mean response time), valid for stable systems where requests finish.

Substituting into the USL gives eq. 6 (N is concurrency here):

```
R(N) = (1 + sigma*(N-1) + kappa*N*(N-1)) / lambda
```

It is quadratic in N. Contention adds linearly growing delay (queueing); crosstalk adds quadratically growing service time. With sigma = kappa = 0, R = 1/lambda, constant. R(1) = 1/lambda is the no-contention single-request latency, a free plausibility check.

Latency against throughput:
- Linear system: R is constant at 1/lambda.
- Amdahl (kappa = 0), eq. 7: `R(X) = (1 - sigma) / (lambda - sigma*X)`. A pole as X approaches lambda/sigma.
- With kappa > 0 the curve folds back like a nose: one throughput maps to two latencies. So latency is not a function of throughput; throughput is a function of latency. Regress on concurrency (compute N = X*R), not on latency vs throughput.

Usable load at a mean-latency target, eq. 10 (positive root of `kappa*N^2 + (sigma-kappa)*N + (1 - sigma - lambda*R) = 0`, verified algebraically in the notes):

```
N(R) = ( kappa - sigma + sqrt( sigma^2 + kappa^2 + 2*kappa*(2*lambda*R + sigma - 2) ) ) / (2*kappa)
```

Then throughput at that N from the USL (equivalently N/R). If kappa = 0 the same condition gives `N = (lambda*R - 1 + sigma)/sigma` (my algebra from eq. 6, same method). If R < 1/lambda there is no solution.

Do not confuse the USL latency curve with the queueing "hockey stick" (residence time against utilisation 0..1, vertical asymptote at 1). DDIA's Fig 2-3 is the hockey stick: low response time at low throughput, sharp rise near capacity. The USL plots against concurrency, which is unbounded.

## 7. Why the two penalties differ physically

- Contention (sigma) is queueing delay from competition for shared servers. Queueing can only cap throughput (a flat line); it cannot reduce it.
- Crosstalk (kappa) is an increase in service time that is not queueing: the job is already out of the queue and being served, but slower, because workers chat to stay consistent.
- Therefore a decline in throughput (retrograde) means service time inflation. An alternative theory attributed to John Little: the cost of managing queues grows with queue length. The author's experience: crosstalk in multi-node clusters, queue-management cost more often in a single server under high load.
- Gunther proved the USL is equivalent to the synchronous repairman model (closed system, finite population that waits for each answer). That is a worst case for queueing delay, which is why a well-built system should do at least as well (diagnosis use) and also why real forecasts should be treated as best case (planning use). See limits-and-pitfalls.md for how to hold both.

## 8. Speedup form for parallel (scatter-gather, MPP) work

Measure one request at concurrency 1 while varying the degree of parallelism N. Response time is the inverse of speedup, eq. 13:

```
R(N) = (1 + sigma*(N-1) + kappa*N*(N-1)) / (lambda * N)
```

Linear: latency falls toward zero. With sigma: falls toward a floor of sigma/lambda. With kappa: falls, bottoms out, then rises again. The best degree of parallelism is the minimum of R(N). (Derived by me: dR/dN = 0 gives N = sqrt((1 - sigma)/kappa), the same Nmax; check the algebra against your own fit before relying on it.)

## 9. Variants and their status

| Variant | Equation | Status |
|---|---|---|
| Logarithmic crosstalk (author's conjecture, eq. 11) | `X = lambda*N / (1 + sigma*(N-1) + kappa*log(N)*(N-1))` | motivated by pairwise algorithms that are N log N; fits some saturating data visually; no mechanism derived. Do not adopt without a reason from the system's mechanism |
| AISSL (Choudhury, eq. 12) | `X = lambda*N / (1 + sigma*(N-1) + sigma*kappa*N^beta*(N-1))`, 0 <= beta <= 1 | reconstructed from a garbled extraction; check the placement of sigma*kappa against the original; hard to fit |
| "Quadratic scalability" (parabola through rise-level-decline data) | n/a | reject: predicts negative throughput somewhere |
| Latency-vs-throughput smoothers and parabola fits (vendor charts) | n/a | assume throughput determines latency; with kappa > 0 that is false |

The author's own caution: you can invent models all day; proving one or deriving it from mechanism is the hard part.

## 10. Provenance

- Verbatim from the source: eqs. 1 to 6, 7, 10, 11, 13 and the peak formula.
- Derived or checked in the notes: eq. 4 derivation, eq. 7 from Amdahl plus Little's Law, eq. 10 root.
- Reconstructed or not reproduced: eq. 8 (the two-branch kappa case) is not reproduced; eq. 9 is reconstructed as X(R) = N(R)/R using eq. 10; eq. 12 is reconstructed.
- Items marked "my algebra" above are adaptations that follow directly from the stated equations.

## 11. Code sketch (Python)

```python
import math

def usl_x(n, lam, sigma, kappa):            # eq. 3
    return lam * n / (1 + sigma * (n - 1) + kappa * n * (n - 1))

def usl_r(n, lam, sigma, kappa):            # eq. 6, n is concurrency
    return (1 + sigma * (n - 1) + kappa * n * (n - 1)) / lam

def n_peak(sigma, kappa):                   # eq. 4, needs kappa > 0
    return math.sqrt((1 - sigma) / kappa)

def n_for_latency(r, lam, sigma, kappa):    # eq. 10
    return (kappa - sigma + math.sqrt(sigma**2 + kappa**2
            + 2 * kappa * (2 * lam * r + sigma - 2))) / (2 * kappa)
```

`scripts/usl_fit.py` implements all of these plus the fitting; run `python3 scripts/usl_fit.py --self-test` to confirm they agree with the numbers in the source.
