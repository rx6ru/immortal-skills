# Measuring scalability and fitting the USL

Source: Schwartz, USL booklet, "Measuring Scalability" and "Hardware, Software, and MPP" sections; DDIA 2e ch. 2 for what to record. Items marked (adaptation) are mine, not the book's.

Contents
1. Decide what N means
2. Design the measurement
3. Where the numbers come from
4. Clean the data
5. Fit
6. Judge the fit
7. Method differences you will see
8. Symptom to cause table for bad data
9. Procedure summary

## 1. Decide what N means

Three dimensions interact: drivers (things producing requests: benchmark threads, connections, users), servers (CPUs in a machine, nodes in a cluster) and data (dataset size, or number of logical partitions). Change one at a time and hold everything else constant per unit of scale.

- Scaling cluster size: grow driver threads and data in proportion to node count so each node gets the same work rate on the same data volume. If you hold the dataset fixed while adding nodes you will see spurious superlinear scaling (more of the data fits in memory per node).
- Scaling load on fixed hardware: vary concurrency; the USL then describes saturation and retrograde behaviour of the software as concurrency rises.
- Where a system's natural unit is the partition (the source's VoltDB example), express N in partitions.
- For a hardware-style fit, drivers grow with servers and each request is served by one server, so concurrency per server stays constant.

Write the definition of N, the unit of throughput and what is held constant at the top of any analysis. Without it the coefficients cannot be interpreted.

## 2. Design the measurement

- Collect pairs (N, throughput). Also record mean latency per N; it gives a second check (section 6) and the response-time forecast.
- At least six points for decent results. The author aims for a dozen or more in benchmarks and often thousands in production data.
- Spread points across the range, include low N (it anchors lambda) and, if safe, points past the knee, but see the rule below about modelling only up to the knee.
- Use steady-state mean throughput per N. Run each N long enough to be past warm-up (adaptation: discard warm-up, and record the run length).
- Keep the regime consistent across runs (same build, same data shape, same driver behaviour).
- The author wishes benchmarks were SLO-aware: back off when, say, p99 latency exceeds a bound and settle on a stable arrival rate, because throughput at saturation hides awful latency. If you control the harness, record latency percentiles at each N so the usable capacity can be read off later.

## 3. Where the numbers come from

| System | Concurrency | Throughput |
|---|---|---|
| Black-box networked software | average number of requests resident over a window, from packet arrivals and departures (IP, port, timestamps) | count of departures per window |
| MySQL | threads running status counter | queries or commands status counters |
| Linux block devices | time-weighted in-flight data from /proc/diskstats over a delta | I/Os completed |
| Benchmark output | driver thread or node count | reported completions per second |
| Anything with throughput and mean latency | N = X * R (Little's Law) | as measured |

Modern equivalents (adaptation): Prometheus counters give throughput via `rate()`, an in-flight gauge gives concurrency; load generators such as k6 or wrk report both.

## 4. Clean the data

- Plot a scatterplot (X against N) and a time series. Drop clear outliers, trim the time range, try averaging windows.
- Check the measurement itself: idle threads counted as concurrency shift all points to the right and fake superlinearity.
- For production (non-lab) data, bucket by concurrency and take the mean throughput per bucket rather than fitting raw noisy samples (adaptation).

## 5. Fit

Fit `X(N) = lambda*N / (1 + sigma*(N-1) + kappa*N*(N-1))` to the (N, X) points by nonlinear least squares. Fit in the (N, X) domain, never as latency against throughput: the latency curve folds back and is hard to regress.

Script (adaptation, standard library only):

```
python3 scripts/usl_fit.py data.csv --predict 20,40 --latency-target 0.0015 --holdout 0.33
python3 scripts/usl_fit.py data.csv --method linear          # linearised regression
python3 scripts/usl_fit.py data.csv --fix-lambda 955 --nonneg --max-n 32
```

CSV has two columns, N and throughput; a header and `#` comments are fine. Output: coefficients, R^2 and relative errors, Nmax and X(Nmax), predictions with efficiency and mean response time, usable load for a latency target, a hold-out score, and warnings.

R recipe from the source (code reconstructed from garbled text, same structure as the book):

```r
usl <- nls(throughput ~ lambda*size/(1 + sigma*(size-1) + kappa*size*(size-1)),
           benchmark, start=c(sigma=0.1, kappa=0.01, lambda=1000))
```

The author's start values were sigma 0.1, kappa 0.01, lambda 1000 (lambda is roughly throughput at N=1). nls can fail to converge from bad starts or refuse noisy data. The CRAN `usl` package is the ready-made option. In Python, `scipy.optimize.curve_fit` with bounds sigma, kappa >= 0 does the same job (the notes mark this as inferred).

Fixing lambda: Gunther's method measures lambda at N=1 and fixes it. The author often finds that infeasible and lets the regression estimate lambda as a third free parameter. Both are legitimate; say which you used. `--fix-lambda` implements the first.

## 6. Judge the fit

Do all of these; a good R^2 alone is not enough.

1. R^2 and a plot of data against the fitted curve. Look at where the residuals sit (systematically positive at the high end means the model is missing a regime).
2. Signs and sizes: sigma and kappa should be non-negative. A negative sigma is a red flag for the measurement (limits-and-pitfalls.md).
3. Fitted lambda against measured X(1). The source's example: 995 fitted against 955 measured (4 percent off) was fine. The script warns above 10 percent, which is a heuristic of mine.
4. Hold-out: fit on the first third of the points and see how well the curve predicts the rest. The author calls it educational: it shows how far out your forecasts can be trusted.
5. Latency cross-check: model R at the observed N should match observed N/X (the notes list this as an inferred check).
6. Shape: if the data does not have the shape a USL should produce, suspect measurement error before adopting a different curve. Know what shape each plot should have.
7. Do not model beyond the knee. After retrograde scaling starts the system's model has changed, so a single set of coefficients cannot explain it, and you are already in trouble. Trim with `--max-n` and investigate why it declines.

## 7. Method differences you will see

On the same 32-point table (worked-example.md), the nonlinear fit gave lambda 995.6, sigma 0.02672, kappa 0.000769 (the source's values); the script's linearised fit gave lambda 963, sigma 0.0215, kappa 0.00086 and a peak near N = 33.7 instead of 35.6. The linearised version minimises error in N/X (response time), which weights low-throughput points more. When the two disagree materially, trust neither blindly: look at the plot and the hold-out error, and report the range.

## 8. Symptom to cause table for bad data

| Symptom | Likely causes to check |
|---|---|
| Negative sigma, curve above the ideal line | dataset held fixed while nodes grow; idle threads inflating N; cache or memory effects; special-cased sizes 1 and 2 |
| Fit tracks, then data flatlines abruptly | saturated resource (cores, bandwidth, queue); step change when threads exceed cores; model blind to caps |
| Fit forecasts far above any measured value | extrapolating beyond 2x measured range; flatline ahead (source example: forecast about 150,000 against a real plateau near 80,000) |
| Fit refuses to converge | bad start values, noisy data, too few points |
| Very different coefficients after adding or removing a few points | too few points or drifting regime; add points, report the spread |

## 9. Procedure summary

1. Fix the definition of N and the unit of throughput; hold the other dimensions constant per unit.
2. Run at 12 or more distinct N across the range; record steady-state mean throughput and latency at each.
3. Plot, clean, fit; check R^2, residual pattern, signs, lambda against X(1).
4. Compute Nmax, X(Nmax), efficiency at the operating N, and which coefficient dominates.
5. Hold-out validate. Forecast no farther than 2x the measured size or throughput.
6. Report coefficients with the data, the plot with the ideal line drawn, and the assumptions.
