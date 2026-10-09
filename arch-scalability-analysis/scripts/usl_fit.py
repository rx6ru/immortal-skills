#!/usr/bin/env python3
"""usl_fit.py - fit the Universal Scalability Law (USL) to (load-or-size, throughput) data.

Model (plain text):
    X(N) = lambda*N / (1 + sigma*(N-1) + kappa*N*(N-1))
    X = throughput, N = size or load (nodes, cores, threads, concurrency),
    lambda = throughput at N=1 (slope of the ideal line),
    sigma  = contention / serialization, kappa = crosstalk / coherency.

What it does
    * reads two columns (N, throughput) separated by comma, semicolon, tab or spaces; a header row
      and '#' comments are allowed; any other unreadable row is skipped and reported as a warning
    * fits lambda, sigma, kappa by least squares, standard library only:
        - "linear": linearised regression. Uses N/X = (1 + sigma*(N-1) + kappa*N*(N-1)) / lambda,
          which is linear in (1/lambda, sigma/lambda, kappa/lambda). This minimises error in the
          response-time domain (N/X), so it weights low-throughput points more than the
          throughput-domain fit does. Cheap and always solvable, but not the same optimum.
        - "nls": nonlinear least squares in the (N, X) domain (Levenberg-Marquardt, started from the
          linear solution). This is the method the source recommends (R's nls). Default.
    * prints coefficients, goodness of fit (R^2 and relative errors in the X domain), the peak
      load Nmax = sqrt((1-sigma)/kappa) and peak throughput X(Nmax), the asymptote lambda/sigma when
      kappa is not positive, and predictions at requested loads (throughput, efficiency,
      mean response time R = (1 + sigma*(N-1) + kappa*N*(N-1))/lambda via Little's Law)
    * optionally finds the usable load for a mean-response-time target (--latency-target)
    * optionally fits on the first part of the data and scores predictions on the rest (--holdout)
    * refuses (message on stderr, exit code 2) when: the file is missing or unreadable, fewer than 3
      numeric rows or distinct N values, N or throughput not positive, or throughput never rises
      above its value at the smallest N (nothing to model)
    * warns about: too few points, negative coefficients, poor fit, lambda far from measured X(1),
      an observed decline past the peak (the model is only valid up to the knee), and
      extrapolation beyond 2x the measured size or throughput

Limits (read before trusting output)
    * The USL has no notion of a hard resource cap (cores, bandwidth, a saturated queue). It cannot
      predict a step change; it is a macro model that is usually good up to the knee and no further.
    * Treat forecasts as best case; do not use them beyond ~2x the measured range.
    * Fitting three parameters to a handful of points can return unphysical values (negative
      sigma or kappa). --nonneg clips them to zero during the fit (projected, not an exact
      constrained optimum); a clipped fit is a warning sign, not a result.
    * N is taken as given. If N is concurrency, response-time output is meaningful; if N is node
      count with load per node held constant, R is the per-request time at that size.
    * Warning thresholds (R^2 < 0.95, lambda off by more than 10 percent, fewer than 6 points) are
      this tool's heuristics except the point count, which follows the source's "at least half a
      dozen". Treat them as prompts to look at the plot, not as pass/fail tests.

Usage
    python3 usl_fit.py data.csv
    python3 usl_fit.py data.csv --predict 20,40,64 --latency-target 0.0015 --holdout 0.33
    python3 usl_fit.py data.csv --method linear --nonneg --max-n 32 --json
    python3 usl_fit.py --self-test
"""

import argparse
import csv
import json
import math
import random
import re
import sys

MIN_POINTS = 6          # source: "at least half a dozen" for decent results
R2_WARN = 0.95          # tool heuristic
LAMBDA_WARN = 0.10      # tool heuristic: relative gap between fitted lambda and measured X(1)


# ----------------------------------------------------------------- model

def denom(n, sigma, kappa):
    return 1.0 + sigma * (n - 1.0) + kappa * n * (n - 1.0)


def usl_x(n, lam, sigma, kappa):
    return lam * n / denom(n, sigma, kappa)


def usl_r(n, lam, sigma, kappa):
    """Mean response time at concurrency n (Little's Law: N = X*R)."""
    return denom(n, sigma, kappa) / lam


def usl_efficiency(n, sigma, kappa):
    return 1.0 / denom(n, sigma, kappa)


def peak(lam, sigma, kappa):
    """Return (Nmax, Xmax) or (None, None) when there is no finite peak."""
    if kappa > 0 and sigma < 1:
        nmax = math.sqrt((1.0 - sigma) / kappa)
        return nmax, usl_x(nmax, lam, sigma, kappa)
    return None, None


def asymptote(lam, sigma, kappa):
    if kappa <= 0 and sigma > 0:
        return lam / sigma
    return None


def usable_n(lam, sigma, kappa, r_target):
    """Largest N whose mean response time is <= r_target (positive root of R(N) = r_target).

    R(N) is increasing in N when sigma, kappa >= 0, so the root is unique. Returns None if the
    target is below R(1) = 1/lambda or no finite solution exists.
    """
    if r_target * lam < 1.0:
        return None
    c = 1.0 - sigma - lam * r_target            # kappa*N^2 + (sigma-kappa)*N + c = 0
    if kappa > 0:
        b = sigma - kappa
        disc = b * b - 4.0 * kappa * c
        if disc < 0:
            return None
        return (-b + math.sqrt(disc)) / (2.0 * kappa)
    if sigma > 0:
        return (lam * r_target - 1.0 + sigma) / sigma
    return None  # sigma = kappa = 0: R is constant, no bound from latency


# ----------------------------------------------------------------- linear algebra

def solve(a, b):
    """Solve a x = b for small dense systems by Gaussian elimination with partial pivoting."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[piv][col]) < 1e-300:
            raise ValueError("singular system")
        m[col], m[piv] = m[piv], m[col]
        for r in range(col + 1, n):
            f = m[r][col] / m[col][col]
            for c in range(col, n + 1):
                m[r][c] -= f * m[col][c]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = m[i][n] - sum(m[i][j] * x[j] for j in range(i + 1, n))
        x[i] = s / m[i][i]
    return x


def lstsq(rows, ys):
    """Ordinary least squares via normal equations with column scaling."""
    k = len(rows[0])
    scale = [math.sqrt(sum(r[j] ** 2 for r in rows)) or 1.0 for j in range(k)]
    sr = [[r[j] / scale[j] for j in range(k)] for r in rows]
    ata = [[sum(r[i] * r[j] for r in sr) for j in range(k)] for i in range(k)]
    aty = [sum(r[i] * y for r, y in zip(sr, ys)) for i in range(k)]
    beta = solve(ata, aty)
    return [beta[j] / scale[j] for j in range(k)]


# ----------------------------------------------------------------- fitting

def fit_linear(ns, xs, fix_lambda=None):
    """Linearised fit. Returns (lam, sigma, kappa)."""
    if fix_lambda is not None:
        # lam*N/X - 1 = sigma*(N-1) + kappa*N*(N-1), a regression through the origin
        rows = [[n - 1.0, n * (n - 1.0)] for n in ns]
        ys = [fix_lambda * n / x - 1.0 for n, x in zip(ns, xs)]
        sigma, kappa = lstsq(rows, ys)
        return fix_lambda, sigma, kappa
    # N/X = a + b*(N-1) + c*N*(N-1), a = 1/lam, b = sigma/lam, c = kappa/lam
    rows = [[1.0, n - 1.0, n * (n - 1.0)] for n in ns]
    ys = [n / x for n, x in zip(ns, xs)]
    a, b, c = lstsq(rows, ys)
    if a <= 0:
        raise ValueError("linearised fit gave non-positive 1/lambda; data not USL-shaped")
    return 1.0 / a, b / a, c / a


def sse(ns, xs, p):
    return sum((x - usl_x(n, *p)) ** 2 for n, x in zip(ns, xs))


def fit_nls(ns, xs, start, free, nonneg=False, max_iter=500):
    """Levenberg-Marquardt on X = lam*N/D. `free` lists indexes in (lam, sigma, kappa) to fit."""
    p = list(start)
    cur = sse(ns, xs, p)
    mu = 1e-3
    for _ in range(max_iter):
        jac = []
        res = []
        for n, x in zip(ns, xs):
            d = denom(n, p[1], p[2])
            f = p[0] * n / d
            res.append(x - f)
            full = [n / d, -p[0] * n * (n - 1.0) / d ** 2, -p[0] * n * n * (n - 1.0) / d ** 2]
            jac.append([full[j] for j in free])
        k = len(free)
        jtj = [[sum(r[i] * r[j] for r in jac) for j in range(k)] for i in range(k)]
        jtr = [sum(r[i] * e for r, e in zip(jac, res)) for i in range(k)]
        improved = False
        for _try in range(40):
            damped = [[jtj[i][j] + (mu * jtj[i][i] if i == j else 0.0) for j in range(k)]
                      for i in range(k)]
            try:
                delta = solve(damped, jtr)
            except ValueError:
                mu *= 10
                continue
            cand = p[:]
            for idx, dv in zip(free, delta):
                cand[idx] += dv
            if cand[0] <= 0:
                mu *= 10
                continue
            if nonneg:
                cand[1] = max(cand[1], 0.0)
                cand[2] = max(cand[2], 0.0)
            new = sse(ns, xs, cand)
            if new < cur:
                rel = (cur - new) / (cur if cur > 0 else 1.0)
                p, cur = cand, new
                mu = max(mu / 10, 1e-12)
                improved = True
                break
            mu *= 10
        if not improved or rel < 1e-14 or cur < 1e-24:
            break
    return tuple(p)


def goodness(ns, xs, p):
    mean = sum(xs) / len(xs)
    ss_tot = sum((x - mean) ** 2 for x in xs) or 1e-300
    ss_res = sse(ns, xs, p)
    rel = [abs(x - usl_x(n, *p)) / x for n, x in zip(ns, xs)]
    return {"r2": 1.0 - ss_res / ss_tot,
            "rmse": math.sqrt(ss_res / len(xs)),
            "mean_rel_err": sum(rel) / len(rel),
            "max_rel_err": max(rel)}


def do_fit(ns, xs, method="nls", nonneg=False, fix_lambda=None):
    lin = fit_linear(ns, xs, fix_lambda)
    if method == "linear":
        p = lin
        if nonneg:
            p = (p[0], max(p[1], 0.0), max(p[2], 0.0))
        return p
    free = [1, 2] if fix_lambda is not None else [0, 1, 2]
    start = list(lin)
    if nonneg:
        start[1] = max(start[1], 0.0)
        start[2] = max(start[2], 0.0)
    return fit_nls(ns, xs, start, free, nonneg)


# ----------------------------------------------------------------- IO

def read_csv(path, skipped=None):
    """Read (N, throughput) pairs. Fields may be separated by comma, semicolon, tab or spaces.

    Blank lines, '#' comments and a non-numeric first data row (a header) are skipped silently.
    Any other row that cannot be read as two finite numbers is skipped and recorded in `skipped`
    (a list of (line number, text)) so the caller can report it instead of losing data quietly.
    """
    ns, xs = [], []
    seen_data_line = False
    with open(path, newline="") as fh:
        for lineno, line in enumerate(fh, 1):
            text = line.strip()
            if not text or text.startswith("#"):
                continue
            row = [c for c in re.split(r"[,;\t ]+", text) if c]
            try:
                if len(row) < 2:
                    raise ValueError("fewer than two fields")
                n, x = float(row[0]), float(row[1])
                if not (math.isfinite(n) and math.isfinite(x)):
                    raise ValueError("not finite")
            except ValueError:
                try:
                    float(row[0])
                    first_is_number = True
                except ValueError:
                    first_is_number = False
                # a first row whose first field is not a number is a header; anything else is reported
                if (seen_data_line or first_is_number) and skipped is not None:
                    skipped.append((lineno, text))
                seen_data_line = True
                continue
            seen_data_line = True
            ns.append(n)
            xs.append(x)
    order = sorted(range(len(ns)), key=lambda i: ns[i])
    return [ns[i] for i in order], [xs[i] for i in order]


def analyse(ns, xs, args, extra_warnings=None):
    """Run the fit and build a result dict (also used by the self-test)."""
    warnings = []
    if args.max_n is not None:
        keep = [i for i, n in enumerate(ns) if n <= args.max_n]
        ns, xs = [ns[i] for i in keep], [xs[i] for i in keep]
    for lineno, text in (extra_warnings or []):
        warnings.append("skipped unreadable row on line %d: %r (expected two numbers: N, throughput)"
                        % (lineno, text))
    if len(ns) < 3:
        raise ValueError("need at least 3 numeric (N, throughput) rows to fit 3 coefficients, found %d%s"
                         % (len(ns), "; %d row(s) were skipped as unreadable (first: line %d)"
                            % (len(extra_warnings), extra_warnings[0][0]) if extra_warnings else ""))
    if any(n <= 0 or x <= 0 for n, x in zip(ns, xs)):
        raise ValueError("N and throughput must be positive")
    if len(set(ns)) < 3:
        raise ValueError("need at least 3 distinct N values (found %d); average repeated runs per N "
                         "and measure at more than %d size(s)" % (len(set(ns)), len(set(ns))))
    if xs[0] >= max(xs):
        raise ValueError("throughput never rises above its value at the smallest N (%g at N=%g): "
                         "there is no scaling region to model; check the scale variable and the "
                         "measurement, or report that adding units does not help" % (xs[0], ns[0]))
    if len(ns) < MIN_POINTS:
        warnings.append("only %d points; the source asks for at least six (aim for a dozen or more)"
                        % len(ns))
    if len(set(ns)) != len(ns):
        warnings.append("repeated N values; average repeats first (steady-state mean per N)")

    lam, sigma, kappa = do_fit(ns, xs, args.method, args.nonneg, args.fix_lambda)
    gf = goodness(ns, xs, (lam, sigma, kappa))
    nmax, xmax = peak(lam, sigma, kappa)

    if sigma < 0:
        warnings.append("negative sigma (sigma=%.6g, kappa=%.6g): suspect measurement first "
                        "(idle threads counted in N, dataset not scaled with nodes, caches growing) "
                        "before believing superlinear scaling" % (sigma, kappa))
    elif kappa < 0:
        warnings.append("negative kappa (%.3g): no crosstalk is detectable in this range, so the "
                        "data look Amdahl-like (or noisy); refit with --nonneg and read the result "
                        "as sigma only. A negative kappa does not mean cheaper coordination at "
                        "larger N" % kappa)
    if args.nonneg and (sigma == 0.0 or kappa == 0.0):
        warnings.append("a coefficient was clipped to zero by --nonneg; read the fit as approximate")
    if gf["r2"] < R2_WARN:
        warnings.append("R^2 = %.4f is low; plot the data and the curve before using the numbers"
                        % gf["r2"])
    if ns[0] == 1:
        gap = abs(lam - xs[0]) / xs[0]
        if gap > LAMBDA_WARN:
            warnings.append("fitted lambda %.4g differs from measured X(1) %.4g by %.0f%%"
                            % (lam, xs[0], 100 * gap))
    imax = max(range(len(xs)), key=lambda i: xs[i])
    if imax < len(xs) - 1 and xs[-1] < 0.97 * xs[imax]:
        warnings.append("measured throughput falls after N=%g; the source advises modelling only up "
                        "to the knee/peak (use --max-n) and finding out why it declines" % ns[imax])
    if kappa > 0 and nmax is not None and nmax > 2 * ns[-1]:
        warnings.append("predicted peak N=%.4g is more than 2x the largest measured N=%g: treat the "
                        "peak as unreliable%s" % (nmax, ns[-1],
                        "; kappa is negligible in this range, so read this as Amdahl-style "
                        "(asymptote lambda/sigma = %.6g)" % (lam / sigma) if nmax > 20 * ns[-1] and sigma > 0
                        else ""))

    result = {"n_points": len(ns), "method": args.method,
              "lambda": lam, "sigma": sigma, "kappa": kappa, "fit": gf,
              "nmax": nmax, "xmax": xmax, "asymptote": asymptote(lam, sigma, kappa),
              "max_measured_n": ns[-1], "max_measured_x": max(xs),
              "predictions": [], "warnings": warnings}

    for n in args.predict or []:
        x = usl_x(n, lam, sigma, kappa)
        row = {"n": n, "x": x, "efficiency": usl_efficiency(n, sigma, kappa),
               "r": usl_r(n, lam, sigma, kappa)}
        if n > 2 * ns[-1] or x > 2 * max(xs):
            row["extrapolation_warning"] = "beyond 2x measured size or throughput"
            warnings.append("prediction at N=%g is beyond 2x the measured range; do not rely on it" % n)
        result["predictions"].append(row)

    if args.latency_target is not None:
        nu = usable_n(lam, sigma, kappa, args.latency_target)
        if nu is None:
            result["usable"] = {"target_r": args.latency_target, "n": None,
                                "note": "no solution (target below R(1)=1/lambda, or sigma=kappa=0)"}
        else:
            nf = math.floor(nu)
            result["usable"] = {"target_r": args.latency_target, "n": nu, "n_floor": nf,
                                "x_at_n": usl_x(nu, lam, sigma, kappa),
                                "x_at_n_floor": usl_x(nf, lam, sigma, kappa) if nf >= 1 else None,
                                "fraction_of_peak": (usl_x(nu, lam, sigma, kappa) / xmax)
                                if xmax else None}
            if nu > 2 * ns[-1]:
                warnings.append("usable N=%.1f is beyond 2x the measured size; low confidence" % nu)

    if args.holdout:
        k = max(3, int(math.ceil(args.holdout * len(ns))))
        if k >= len(ns):
            warnings.append("--holdout leaves no points to test")
        else:
            hp = do_fit(ns[:k], xs[:k], args.method, args.nonneg, args.fix_lambda)
            errs = [(n, x, usl_x(n, *hp)) for n, x in zip(ns[k:], xs[k:])]
            rel = [abs(f - x) / x for _, x, f in errs]
            result["holdout"] = {"fit_points": k, "test_points": len(errs),
                                 "lambda": hp[0], "sigma": hp[1], "kappa": hp[2],
                                 "mean_rel_err": sum(rel) / len(rel), "max_rel_err": max(rel),
                                 "worst_n": errs[rel.index(max(rel))][0],
                                 "predicted_peak": peak(*hp)[1]}
    return result


def print_text(r):
    f = r["fit"]
    print("USL fit (%s, %d points)" % (r["method"], r["n_points"]))
    print("  lambda = %.6g   sigma = %.6g   kappa = %.6g" % (r["lambda"], r["sigma"], r["kappa"]))
    print("  fit quality (throughput domain): R^2 = %.4f  RMSE = %.4g  mean rel err = %.2f%%  "
          "max rel err = %.2f%%" % (f["r2"], f["rmse"], 100 * f["mean_rel_err"], 100 * f["max_rel_err"]))
    if r["nmax"] is not None:
        print("  predicted peak: Nmax = %.2f, X(Nmax) = %.6g   (measured max X = %.6g at N<=%g)"
              % (r["nmax"], r["xmax"], r["max_measured_x"], r["max_measured_n"]))
    elif r["asymptote"] is not None:
        print("  no peak (kappa <= 0): Amdahl-style asymptote lambda/sigma = %.6g, max speedup 1/sigma = %.4g"
              % (r["asymptote"], 1.0 / r["sigma"]))
    else:
        print("  no peak and no asymptote (sigma, kappa <= 0): linear or superlinear in this fit")
    if r["sigma"] > 0 and r["kappa"] > 0:
        share_s = r["sigma"] * (r["nmax"] - 1)
        share_k = r["kappa"] * r["nmax"] * (r["nmax"] - 1)
        print("  at Nmax the penalty terms are: contention %.3g vs crosstalk %.3g (larger: %s)"
              % (share_s, share_k, "contention" if share_s > share_k else "crosstalk"))
    if r["predictions"]:
        print("  predictions:")
        print("    %10s %14s %12s %14s" % ("N", "throughput", "efficiency", "mean R (s)"))
        for p in r["predictions"]:
            print("    %10g %14.6g %11.1f%% %14.6g%s" % (p["n"], p["x"], 100 * p["efficiency"], p["r"],
                  "   (extrapolation)" if "extrapolation_warning" in p else ""))
    if "usable" in r:
        u = r["usable"]
        if u["n"] is None:
            print("  usable load at mean R <= %g s: %s" % (u["target_r"], u["note"]))
        else:
            print("  usable load at mean R <= %g s: N = %.2f (floor %d), X = %.6g (X at floor = %s)"
                  % (u["target_r"], u["n"], u["n_floor"], u["x_at_n"],
                     "%.6g" % u["x_at_n_floor"] if u["x_at_n_floor"] else "n/a"))
            if u["fraction_of_peak"]:
                print("    that is %.0f%% of the predicted peak throughput" % (100 * u["fraction_of_peak"]))
    if "holdout" in r:
        h = r["holdout"]
        print("  hold-out: fit on first %d points, tested on %d: mean rel err %.2f%%, max %.2f%% (N=%g)"
              % (h["fit_points"], h["test_points"], 100 * h["mean_rel_err"], 100 * h["max_rel_err"],
                 h["worst_n"]))
        print("    hold-out coefficients: lambda=%.6g sigma=%.6g kappa=%.6g%s"
              % (h["lambda"], h["sigma"], h["kappa"],
                 ", predicted peak X=%.6g" % h["predicted_peak"] if h["predicted_peak"] else ""))
    for w in r["warnings"]:
        print("  WARNING: " + w)


# ----------------------------------------------------------------- self-test

CISCO = [(1, 955.16), (2, 1878.91), (3, 2688.01), (4, 3548.68), (5, 4315.54), (6, 5130.43),
         (7, 5931.37), (8, 6531.08), (9, 7219.80), (10, 7867.61), (11, 8278.71), (12, 8646.70),
         (13, 9047.84), (14, 9426.55), (15, 9645.37), (16, 9897.24), (17, 10097.60), (18, 10240.50),
         (19, 10532.39), (20, 10798.52), (21, 11151.43), (22, 11518.63), (23, 11806.00),
         (24, 12089.37), (25, 12075.41), (26, 12177.29), (27, 12211.41), (28, 12158.93),
         (29, 12155.27), (30, 12118.04), (31, 12140.40), (32, 12074.39)]
# The table is the one reconstructed in the study notes (font-cipher decoded); the published fit
# quoted there is lambda=995.6486, sigma=0.02671591, kappa=0.0007690945.


class _Args:
    def __init__(self, **kw):
        self.method = "nls"
        self.nonneg = False
        self.fix_lambda = None
        self.max_n = None
        self.predict = None
        self.latency_target = None
        self.holdout = None
        self.__dict__.update(kw)


def _close(a, b, rel=1e-6, ab=1e-9):
    return abs(a - b) <= max(rel * abs(b), ab)


def self_test():
    ok = True

    def check(name, cond, detail=""):
        nonlocal ok
        print("%-62s %s %s" % (name, "PASS" if cond else "FAIL", detail))
        ok = ok and cond

    # 1. exact recovery from noise-free synthetic data, both methods
    true = (1000.0, 0.03, 0.0005)
    ns = list(range(1, 33))
    xs = [usl_x(n, *true) for n in ns]
    for method in ("linear", "nls"):
        r = analyse(ns, xs, _Args(method=method))
        check("synthetic exact recovery (%s)" % method,
              _close(r["lambda"], true[0]) and _close(r["sigma"], true[1], 1e-5)
              and _close(r["kappa"], true[2], 1e-5),
              "lambda=%.4f sigma=%.6f kappa=%.7f" % (r["lambda"], r["sigma"], r["kappa"]))

    # 2. peak formula matches a brute-force scan
    nmax, xmax = peak(*true)
    best = max(range(1, 400), key=lambda n: usl_x(n, *true))
    check("Nmax formula vs brute-force scan", abs(nmax - best) <= 1.0,
          "formula %.2f, scan %d" % (nmax, best))

    # 3. 2% multiplicative noise, deterministic seed
    rng = random.Random(7)
    noisy = [x * (1 + rng.uniform(-0.02, 0.02)) for x in xs]
    r = analyse(ns, noisy, _Args())
    check("2% noise: coefficients within tolerance",
          abs(r["lambda"] - true[0]) / true[0] < 0.05 and abs(r["sigma"] - true[1]) < 0.01
          and abs(r["kappa"] - true[2]) < 0.0003,
          "lambda=%.1f sigma=%.4f kappa=%.5f" % (r["lambda"], r["sigma"], r["kappa"]))

    # 4. fixed-lambda (Gunther-style) fit
    r = analyse(ns, xs, _Args(fix_lambda=1000.0, method="linear"))
    check("fixed lambda, linear fit recovers sigma/kappa",
          _close(r["sigma"], 0.03, 1e-5) and _close(r["kappa"], 0.0005, 1e-5))

    # 5. latency-target inverse: R(N(R)) == R, and X(N) == N/R
    for tgt in (0.002, 0.0035, 0.01):
        nu = usable_n(*true, tgt)
        check("usable_n inverse at R=%g" % tgt,
              nu is not None and _close(usl_r(nu, *true), tgt, 1e-9)
              and _close(usl_x(nu, *true), nu / tgt, 1e-9), "N=%.3f" % nu)
    check("usable_n None below R(1)", usable_n(*true, 0.0005) is None)

    # 6. Cisco data from the notes (reconstructed table): compare to the quoted fit
    cn = [float(n) for n, _ in CISCO]
    cx = [x for _, x in CISCO]
    r = analyse(cn, cx, _Args(predict=[20.0], holdout=0.33))
    check("Cisco table: lambda near 995.65",
          abs(r["lambda"] - 995.6486) / 995.6486 < 0.02, "got %.2f" % r["lambda"])
    check("Cisco table: sigma near 0.026716",
          abs(r["sigma"] - 0.02671591) < 0.003, "got %.6f" % r["sigma"])
    check("Cisco table: kappa near 0.000769",
          abs(r["kappa"] - 0.0007690945) < 0.00008, "got %.7f" % r["kappa"])
    check("Cisco table: Nmax near 35.6 and peak X near 12,341",
          abs(r["nmax"] - 35.6) < 3.0 and abs(r["xmax"] - 12341) / 12341 < 0.03,
          "Nmax=%.2f Xmax=%.0f" % (r["nmax"], r["xmax"]))
    check("Cisco table: R^2 above 0.99", r["fit"]["r2"] > 0.99, "R^2=%.4f" % r["fit"]["r2"])
    # published coefficients applied directly reproduce the notes' peak numbers
    pub = (995.6486, 0.02671591, 0.0007690945)
    pn, px = peak(*pub)
    check("published coefficients give Nmax 35.57, X 12,341 +/- 1",
          abs(pn - 35.57) < 0.01 and abs(px - 12341) < 2, "Nmax=%.2f X=%.1f" % (pn, px))

    # 7. first-10-points forecast from the notes (best fit differs a little by method)
    r10 = analyse(cn[:10], cx[:10], _Args(predict=[20.0]))
    check("Cisco first 10 points: peak prediction is optimistic (> 12,341)",
          r10["xmax"] > 12341, "Nmax=%.1f Xmax=%.0f (notes: 46 and 16,049)" % (r10["nmax"], r10["xmax"]))
    check("Cisco first 10 points: warns that predicted peak is far outside measured range",
          any("2x" in w for w in r10["warnings"]))

    # 8. warnings
    r = analyse([1, 2, 3, 4], [100, 190, 270, 340], _Args())
    check("few points warns", any("only 4 points" in w for w in r["warnings"]))
    sup = [(n, 100 * n * (1 + 0.02 * (n - 1))) for n in range(1, 13)]  # superlinear
    r = analyse([a for a, _ in sup], [b for _, b in sup], _Args())
    check("superlinear data -> negative coefficient warning",
          any("negative sigma" in w for w in r["warnings"]) and r["sigma"] < 0,
          "sigma=%.4f" % r["sigma"])
    r = analyse([a for a, _ in sup], [b for _, b in sup], _Args(nonneg=True))
    check("--nonneg clips and says so", r["sigma"] >= 0 and r["kappa"] >= 0
          and any("clipped" in w for w in r["warnings"]))
    amd = [usl_x(n, 500.0, 0.05, 0.0) for n in range(1, 25)]
    r = analyse(list(range(1, 25)), amd, _Args(nonneg=True))
    check("Amdahl data: sigma=0.05, kappa ~ 0, peak flagged as unreliable",
          abs(r["sigma"] - 0.05) < 1e-4 and r["kappa"] < 1e-8
          and any("more than 2x" in w or "negligible" in w for w in r["warnings"]),
          "sigma=%.5f kappa=%.2e" % (r["sigma"], r["kappa"]))
    check("Amdahl asymptote helper: lambda/sigma = 10000", _close(asymptote(500.0, 0.05, 0.0), 10000.0))

    # 9. decline past the peak is flagged
    r = analyse(cn[:32], cx[:25] + [12075.0, 12000.0, 11500.0, 11000.0, 10500.0, 10000.0, 9500.0], _Args())
    check("decline after peak flagged", any("falls after" in w for w in r["warnings"]))

    # 10. CSV parsing with header and comments
    import os
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fh:
        fh.write("# comment\nthreads,qps\n2,190\n1,100\n3,270\n")
        path = fh.name
    try:
        a, b = read_csv(path)
        check("csv: header/comment skipped, sorted by N", a == [1.0, 2.0, 3.0] and b == [100.0, 190.0, 270.0])
    finally:
        os.unlink(path)

    # 11. bad input is refused with a clear message, or reported
    import contextlib
    import io
    import os
    import tempfile

    def run_cli(text):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as fh:
            fh.write(text)
            path = fh.name
        err, out = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
                code = main([path])
        finally:
            os.unlink(path)
        return code, err.getvalue(), out.getvalue()

    code, err, _ = run_cli("1,100\n2,190\n")
    check("two points: exit 2 with 'at least 3'", code == 2 and "at least 3" in err)
    code, err, _ = run_cli("N,X\na,b\nfoo,bar\n")
    check("non-numeric rows: exit 2, says rows were skipped", code == 2 and "skipped" in err)
    code, err, _ = run_cli("1,100\n2,x\n3,270\n4,330\n5,380\n6,420\n7,450\n")
    check("one bad row among good ones: fits, warns with the line number",
          code == 0 and "line 2" in _)
    code, err, _ = run_cli("1,100\n2,90\n3,80\n4,70\n5,60\n6,50\n")
    check("decreasing-only data: exit 2, 'no scaling region'", code == 2 and "no scaling region" in err)
    code, err, _ = run_cli("1,100\n1,100\n1,100\n1,100\n")
    check("one distinct N: exit 2, 'distinct N'", code == 2 and "distinct N" in err)
    code, err, _ = run_cli("1,100\n2,nan\n3,270\n")
    check("nan throughput is treated as an unreadable row", code == 2 and "skipped" in err)
    with contextlib.redirect_stderr(io.StringIO()) as e2:
        code = main(["/nonexistent/usl.csv"])
    check("missing file: exit 2 with the OS message", code == 2 and "No such file" in e2.getvalue())

    print("\nself-test: %s" % ("all checks passed" if ok else "FAILURES"))
    return 0 if ok else 1


# ----------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Fit the Universal Scalability Law X(N)=lambda*N/(1+sigma*(N-1)+kappa*N*(N-1)) to "
                    "CSV pairs (N, throughput). Standard library only. See module docstring for limits.")
    ap.add_argument("csv", nargs="?", help="CSV with columns N,throughput (header and # comments allowed)")
    ap.add_argument("--method", choices=("nls", "linear"), default="nls",
                    help="nls: nonlinear least squares in the throughput domain (default); "
                         "linear: linearised regression on N/X")
    ap.add_argument("--fix-lambda", type=float, default=None,
                    help="fix lambda (e.g. the measured throughput at N=1) and fit only sigma and kappa")
    ap.add_argument("--nonneg", action="store_true", help="clip sigma and kappa to be >= 0 during the fit")
    ap.add_argument("--max-n", type=float, default=None,
                    help="ignore points with N above this (use to stop at the knee)")
    ap.add_argument("--predict", type=lambda s: [float(v) for v in s.split(",") if v],
                    default=None, help="comma-separated N values to predict, e.g. 20,40,64")
    ap.add_argument("--latency-target", type=float, default=None,
                    help="mean response time target in seconds; reports usable N and throughput "
                         "(assumes N is concurrency and lambda is per second)")
    ap.add_argument("--holdout", type=float, default=None,
                    help="fraction (0-1) of the lowest-N points to fit; the rest score the forecast")
    ap.add_argument("--json", action="store_true", help="print machine-readable output")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks and exit")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if not args.csv:
        ap.error("a CSV file is required (or use --self-test)")
    try:
        skipped = []
        ns, xs = read_csv(args.csv, skipped)
        result = analyse(ns, xs, args, skipped)
    except (OSError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_text(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
