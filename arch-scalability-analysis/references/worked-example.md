# Worked example: a full USL analysis, replayable

Source: USL booklet (Cisco server MySQL benchmark by Vadim Tkachenko; PayPal Java and NodeJS; Isilon S210 SPEC NFS). Lines marked "script" are outputs I produced with `scripts/usl_fit.py` from the table below; the rest are the source's figures. The benchmark table was garbled in the source PDF and decoded by the note-takers (digits recovered by consistent substitution and checked against numbers in the text: N = 1 gives 955, N = 10 gives 7,867). The fit of the decoded table reproduces the book's coefficients to the quoted precision, which is good evidence the decoding is right.

Contents
1. The data
2. Fit and what it says
3. Hold-out and small-sample forecast
4. Usable capacity at a latency target
5. A check the source did not make
6. Response time and the nose
7. Diagnosis example: PayPal
8. Wrong-model example: Isilon
9. Parallel-degree example (derived)
10. Replaying everything

## 1. The data

Size = threads, throughput = queries per second (QPS), saved as `cisco.csv`:

```
threads,qps
1,955.16
2,1878.91
3,2688.01
4,3548.68
5,4315.54
6,5130.43
7,5931.37
8,6531.08
9,7219.80
10,7867.61
11,8278.71
12,8646.70
13,9047.84
14,9426.55
15,9645.37
16,9897.24
17,10097.60
18,10240.50
19,10532.39
20,10798.52
21,11151.43
22,11518.63
23,11806.00
24,12089.37
25,12075.41
26,12177.29
27,12211.41
28,12158.93
29,12155.27
30,12118.04
31,12140.40
32,12074.39
```

Sanity first: per-thread throughput is 955 at N = 1 and 787 at N = 10 (7,867/10), then 452 at N = 27 (12,211/27). Efficiency at N = 10 is 7,867/(10 * 955) = 82 percent. Not linear, and the flattening is visible without any model.

## 2. Fit and what it says

Source fit (nonlinear least squares): lambda = 995.6486, sigma = 0.02671591, kappa = 0.0007690945. Script (nls) gives the same: lambda 995.649, sigma 0.0267159, kappa 0.000769094, R^2 = 0.9972, mean relative error 1.9 percent, maximum 5 percent.

- Fitted lambda 995 against measured X(1) = 955: 4 percent off, acceptable.
- Peak: `Nmax = sqrt((1 - 0.02671591)/0.0007690945) = sqrt(1265.5) = 35.6`, so about 35 threads. Predicted peak throughput about 12,341 QPS (script: 12,343). The observed maximum was about 12,211 around N = 27, so the model is slightly optimistic, as the source says forecasts are.
- Kappa is below 0.001 yet it ends scaling by N near 35. At Nmax the contention term sigma*(Nmax-1) is about 0.92 and the crosstalk term about 0.95, so both matter, with crosstalk slightly larger (script's comparison, my heuristic).
- Model efficiency: 76 percent at N = 10, 56 percent at N = 20, 35 percent at N = 35 (script).
- Without kappa (Amdahl) there would be no peak, only the asymptote lambda/sigma, about 37,000 here (my arithmetic). The observed flattening near 12,000 shows kappa is needed.

Linearised variant (script `--method linear`): lambda 963, sigma 0.0215, kappa 0.00086, Nmax 33.7, peak 12,247. Close to the nonlinear fit, which is what you want to see; large disagreement would signal a poor model or poor data.

## 3. Hold-out and small-sample forecast

Hold-out (script, `--holdout 0.33`): fit on the first 11 points, predict the other 21. Mean relative error 3.8 percent, worst 5.8 percent (at N = 18). The hold-out fit gives lambda 920, sigma 0.0063, kappa 0.00138 and a peak of about 11,650: coefficients move a lot even though predictions stay within a few percent, which is the typical message: forecast numbers are more stable than the individual coefficients.

Source's production-style scenario: only N = 1 to 10 measured, observed 7,867 QPS at N = 10.
- Fit predicts a peak of 16,049 QPS at 46 threads (script on the first ten points: 16,052 at N = 46.9). The full data later gave 12,341 at 35, so the small-sample peak was 30 percent high.
- Forecast at N = 20: 12,572 QPS, under twice the observed maximum (15,734), so acceptable by the 2x rule. Source's judgement: no more than about 12,500. Real maximum: 12,211.
- Script warns that the predicted peak (N = 46.9) is more than twice the largest measured N (10). Heed it: the peak figure was the least reliable output.

## 4. Usable capacity at a latency target

Requirement: mean response at most 1.5 ms. Predicted mean at N = 20 from the ten-point fit: 0.00159 s (too slow). Solve eq. 10 with R = 0.0015:
- Source: N = 17, about 11,450 QPS, which is roughly 1.46 times the current 7,867 (the source's wording "grow about 145 percent" is read this way; marked inferred in the notes).
- Script on the ten-point data: N = 17.4, about 11,450 at N = 17.

Current 7,867 is about two thirds of the usable throughput, and current is about half of the predicted maximum: headroom is much smaller than the maximum suggests.

## 5. A check the source did not make

This section is my own computation from the decoded table. In a closed benchmark with no think time, the observed mean response time is N/X (Little's Law). From the table: 1.485 ms at N = 14, 1.555 ms at N = 15, 1.684 ms at N = 17. So the 1.5 ms target is actually met only up to N = 14 (9,427 QPS), not N = 17. The full-data fit agrees: eq. 10 gives N = 14.1 and about 9,400 QPS (script). The ten-point forecast of about 11,450 QPS was optimistic by roughly 20 percent. This is exactly the behaviour the source predicts ("treat forecasts as best case") and a good reason to re-fit as soon as more load data arrives and to quote a range.

## 6. Response time and the nose

Model mean response (script, full fit): 1.00 ms at N = 1, 1.32 ms at N = 10, 1.81 ms at N = 20, 2.84 ms at N = 35, 5.81 ms at N = 64 (beyond the data; extrapolation). Throughput at 64 would be about 11,000, falling from the peak, so one throughput of about 11,000 QPS corresponds to two latencies (about 1.8 ms at N = 20 and about 5.8 ms at N = 64): that is the nose. Do not fit latency against throughput; the source shows a rational-function fit badly underestimates the latency growth on this data.

## 7. Diagnosis example: PayPal

| System | sigma | kappa | Nmax from eq. 4 |
|---|---|---|---|
| Java, multi-threaded, five cores | 0.000011 | 0.006323 | Nmax about 12.6 |
| NodeJS, single-threaded event loop, one core | 0.080319 | 0.000222 | Nmax about 64 |

Nmax column is my arithmetic from eq. 4 with the source's coefficients; the source gives only the coefficients and its reading: Java high crosstalk, NodeJS high contention from queueing and serialization, both poor in absolute terms. Use as a template for the write-up: coefficients, family of cause, matching architectural fact.

## 8. Wrong-model example: Isilon

Throughput (ops/s) to response (ms): 25,504 to 0.7; 51,054 to 0.6; 76,667 to 0.7; 102,288 to 0.8; 127,879 to 0.9; 153,497 to 1.0; 179,261 to 1.2; 205,226 to 1.4; 231,069 to 2.0; 253,357 to 5.7.
A rational-function fit to all but the last row matches the earlier points and predicts far lower latency at 253k than the real 5.7 ms. The USL models the knee more closely but is somewhat pessimistic here. Lesson: the wrong model misjudges the approach to saturation badly, and the last benchmark row can hold all the information. Always include the point nearest saturation in the fit and in the chart.

## 9. Parallel-degree example (derived)

For a scatter-gather query with eq. 13 `R(N) = (1 + sigma*(N-1) + kappa*N*(N-1))/(lambda*N)`, take illustrative values lambda = 1, sigma = 0.03, kappa = 0.0005 (mine, not the book's). Script arithmetic: R is 1.00 at N = 1, 0.13 at N = 10, 0.088 at N = 20, 0.0735 at N = 44, 0.0757 at N = 60. The minimum sits near Nmax = sqrt(0.97/0.0005) = 44, and beyond that more parallelism makes the query slower. Choose the degree of parallelism at the minimum, not "as many as possible".

## 10. Replaying everything

```
python3 scripts/usl_fit.py cisco.csv --predict 10,17,20,35,64 --latency-target 0.0015 --holdout 0.33
head -11 cisco.csv > cisco10.csv
python3 scripts/usl_fit.py cisco10.csv --predict 20 --latency-target 0.0015
python3 scripts/usl_fit.py cisco.csv --method linear
python3 scripts/usl_fit.py --self-test
```

The self-test checks exact recovery from synthetic data, the peak formula against a brute-force scan, the latency inverse, warnings, CSV parsing, and the Cisco numbers above.
