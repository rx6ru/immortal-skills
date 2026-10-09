#!/usr/bin/env python3
"""burn_rate.py - error-budget and burn-rate alert arithmetic for an SLO.

What it does
------------
Given an SLO target and a compliance window it prints the error budget and,
for a set of burn-rate alert rules, the long and short windows, the error-ratio
threshold to put in the rule, the share of budget consumed when the rule fires,
the time to exhaust the budget at that burn rate, and the time a 100% outage
needs to trip the rule. Optionally it takes an observed error ratio and reports
its burn rate, which rules it would trip and how long each would take, and a
traffic volume (requests per hour) to show how many failures a rule needs.

Formulas (Site Reliability Workbook ch. 5; P = window length, W = alert window,
B = burn rate, e = error ratio, SLO as a fraction, budget = 1 - SLO):
    burn rate            B = e / (1 - SLO)
    time to exhaustion   P / B
    budget consumed      B * W / P
    threshold ratio      B * (1 - SLO)
    B for fraction f     B = f * P / W
    detection time       ((1 - SLO) / e) * W * B     (e = 1 for a full outage)
    short window         long window / 12 (guideline from the book)

Default rule set (the multiwindow, multi-burn-rate set from the book, derived
from budget fractions so it adapts to any window):
    page    2% of budget in 1 h   (long 1 h,  short 5 min)
    page    5% of budget in 6 h   (long 6 h,  short 30 min)
    ticket 10% of budget in 3 d   (long 3 d,  short 6 h)
For a 99.9% / 30-day SLO these give burn rates 14.4, 6 and 1.
The book's printed rule example also contains a ticket row at burn rate 3 over
24 h with a 2 h short window (10% of budget in a day); add it with
--include-day-ticket. The book's Table 5-8 lists only the 3-day ticket row.

Limits
------
* Pure arithmetic on ratios. It does not read metrics, and it assumes errors
  are spread evenly through the window and traffic is steady.
* Detection time assumes the error ratio is constant from the start of the
  incident and ignores scrape and evaluation delay. It uses the slower of the
  long and short windows (the long one unless the rule is malformed).
* Warnings ("cannot fire", "full outage exhausts budget in under 5 minutes") are
  heuristics added by this script; the 5-minute cut is an adaptation, not a
  figure from the book.

Examples
--------
    burn_rate.py --slo 99.9 --window 30d
    burn_rate.py --slo 99.9 --window 28d --observed-error-ratio 0.0144
    burn_rate.py --slo 99.9 --window 30d --requests-per-hour 10
    burn_rate.py --slo 99.99 --window 4w --rule 1h:5m:14.4:page --rule 3d:6h:1:ticket
    burn_rate.py --self-test
"""

import argparse
import json
import math
import re
import sys

UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
DEFAULT_FRACTIONS = [
    # (budget fraction, long window seconds, severity)
    (0.02, 3600, "page"),
    (0.05, 6 * 3600, "page"),
    (0.10, 3 * 86400, "ticket"),
]
DAY_TICKET = (0.10, 86400, "ticket")  # burn rate 3 on 24 h in a 30-day window


def parse_duration(text):
    """Parse '30d', '4w', '90m', '1h30m' style durations into seconds."""
    text = text.strip().lower()
    parts = re.findall(r"(\d+(?:\.\d+)?)([smhdw])", text)
    if not parts or "".join(n + u for n, u in parts) != text:
        raise ValueError("cannot parse duration %r (use e.g. 30d, 4w, 6h, 5m)" % text)
    return sum(float(n) * UNITS[u] for n, u in parts)


def fmt_duration(seconds):
    """Human readable duration, two units at most."""
    if seconds is None:
        return "never"
    if seconds < 1:
        return "%.2f s" % seconds
    if seconds < 120:
        return "%.1f s" % seconds if seconds < 60 else "%d s" % round(seconds)
    if seconds < 2 * 86400 and seconds >= 3600 and seconds % 3600 == 0:
        return "%d h" % (seconds // 3600)
    if seconds < 7200:
        m = seconds / 60
        return "%.1f min" % m if m < 100 and abs(m - round(m)) > 0.05 else "%d min" % round(m)
    if seconds < 2 * 86400:
        h = seconds / 3600
        return "%.1f h" % h if abs(h - round(h)) > 0.05 else "%d h" % round(h)
    d = seconds / 86400
    return "%.1f d" % d if abs(d - round(d)) > 0.05 else "%d d" % round(d)


def make_rule(burn, long_s, short_s, severity):
    return {"burn": burn, "long": long_s, "short": short_s, "severity": severity}


def default_rules(period_s, include_day_ticket=False):
    """Rules derived from budget fractions: B = f * P / W, short = long / 12."""
    spec = list(DEFAULT_FRACTIONS)
    if include_day_ticket:
        spec.insert(2, DAY_TICKET)
    rules = []
    for frac, long_s, sev in spec:
        burn = frac * period_s / long_s
        short_s = long_s / 12.0
        if abs(burn - round(burn)) < 1e-9:
            burn = float(round(burn))
        rules.append(make_rule(burn, long_s, short_s, sev))
    return rules


def parse_rule(text):
    """'long:short:burn[:severity]' -> rule dict."""
    bits = text.split(":")
    if len(bits) not in (3, 4):
        raise ValueError("rule must look like long:short:burn[:severity], got %r" % text)
    severity = bits[3] if len(bits) == 4 else "page"
    try:
        burn = float(bits[2])
    except ValueError:
        raise ValueError("burn rate in rule %r is not a number" % text)
    long_s, short_s = parse_duration(bits[0]), parse_duration(bits[1])
    if not math.isfinite(burn) or burn <= 0:
        raise ValueError("burn rate in rule %r must be a positive finite number" % text)
    if long_s <= 0 or short_s <= 0:
        raise ValueError("windows in rule %r must be longer than zero" % text)
    return make_rule(burn, long_s, short_s, severity)


def analyse_rule(rule, slo, period_s, observed=None, req_per_hour=None):
    """Compute the per-rule quantities. slo is a fraction (0.999)."""
    budget = 1.0 - slo
    b, w = rule["burn"], rule["long"]
    out = dict(rule)
    out["threshold_ratio"] = b * budget
    out["budget_consumed"] = b * w / period_s
    out["time_to_exhaustion_s"] = period_s / b
    # e = 1: both windows must exceed the threshold, so the slower one decides.
    out["full_outage_detection_s"] = budget * max(w, rule["short"]) * b
    out["can_fire"] = out["threshold_ratio"] <= 1.0
    if not out["can_fire"]:
        out["full_outage_detection_s"] = None  # a full outage never trips it
    out["warnings"] = []
    if not out["can_fire"]:
        out["warnings"].append(
            "threshold ratio %.3g exceeds 1.0: even a 100%% outage cannot trip this rule" % out["threshold_ratio"]
        )
    if w > period_s:
        out["warnings"].append(
            "long window is longer than the SLO window: the burn-rate arithmetic no longer describes the budget")
    if rule["short"] > rule["long"]:
        out["warnings"].append("short window is longer than the long window")
    elif abs(rule["short"] * 12 - rule["long"]) > 1e-6 * rule["long"]:
        out["warnings"].append("short window is not long/12 (book guideline)")
    if observed is not None:
        trips = observed >= out["threshold_ratio"] and out["can_fire"]
        out["observed_trips"] = trips
        out["observed_detection_s"] = (budget / observed) * max(w, rule["short"]) * b if trips else None
    if req_per_hour is not None:
        n_long = req_per_hour * w / 3600.0
        out["requests_in_long_window"] = n_long
        out["failures_to_fire"] = out["threshold_ratio"] * n_long
        if n_long > 0 and out["threshold_ratio"] * n_long <= 1.0:
            out["warnings"].append(
                "a single failed request within the long window would trip this rule (low-traffic problem)"
            )
    return out


def summarise(slo_pct, period_s, rules, observed=None, req_per_hour=None):
    slo = slo_pct / 100.0
    budget = 1.0 - slo
    result = {
        "slo_percent": slo_pct,
        "period_s": period_s,
        "error_budget_ratio": budget,
        "full_outage_exhaustion_s": period_s * budget,
        "downtime_budget_s": period_s * budget,
        "rules": [analyse_rule(r, slo, period_s, observed, req_per_hour) for r in rules],
        "warnings": [],
    }
    if result["full_outage_exhaustion_s"] < 300:
        result["warnings"].append(
            "a 100%% outage exhausts the whole budget in %s: alerting cannot defend this target, "
            "limit blast radius by design (staged rollout) instead" % fmt_duration(result["full_outage_exhaustion_s"])
        )
    if req_per_hour is not None:
        total = req_per_hour * period_s / 3600.0
        result["requests_in_period"] = total
        result["allowed_failures_in_period"] = total * budget
        if total * budget < 20:
            result["warnings"].append(
                "only %.1f failures fit in the budget for the whole window: a handful of failures "
                "decides the SLO (consider synthetic traffic, grouping, retries or a lower SLO)" % (total * budget)
            )
    if observed is not None:
        b = observed / budget
        result["observed"] = {
            "error_ratio": observed,
            "burn_rate": b,
            "time_to_exhaustion_s": period_s / b if b > 0 else None,
        }
    return result


def render(res):
    lines = []
    p = res["period_s"]
    lines.append("SLO %.4g%% over %s" % (res["slo_percent"], fmt_duration(p)))
    lines.append("Error budget: %.6g (%.4g%% of events); full outage exhausts it in %s"
                 % (res["error_budget_ratio"], res["error_budget_ratio"] * 100,
                    fmt_duration(res["full_outage_exhaustion_s"])))
    if "requests_in_period" in res:
        lines.append("Traffic: %.0f requests per window, %.1f allowed failures"
                     % (res["requests_in_period"], res["allowed_failures_in_period"]))
    lines.append("")
    head = "%-7s %-9s %-9s %-7s %-12s %-9s %-12s %-12s" % (
        "sev", "long", "short", "burn", "threshold", "consumed", "exhaust@B", "100% outage")
    lines.append(head)
    lines.append("-" * len(head))
    for r in res["rules"]:
        lines.append("%-7s %-9s %-9s %-7.4g %-12.6g %-9s %-12s %-12s" % (
            r["severity"], fmt_duration(r["long"]), fmt_duration(r["short"]), r["burn"],
            r["threshold_ratio"], "%.2f%%" % (r["budget_consumed"] * 100),
            fmt_duration(r["time_to_exhaustion_s"]), fmt_duration(r["full_outage_detection_s"])))
    lines.append("")
    lines.append("Rule shape: fire when error_ratio(long) > threshold AND error_ratio(short) > threshold;")
    lines.append("            page rules use OR across page rows, ticket rules across ticket rows.")
    if "observed" in res:
        o = res["observed"]
        lines.append("")
        lines.append("Observed error ratio %.6g -> burn rate %.4g, budget gone in %s if sustained"
                     % (o["error_ratio"], o["burn_rate"], fmt_duration(o["time_to_exhaustion_s"])))
        for r in res["rules"]:
            if r.get("observed_trips"):
                lines.append("  trips %-6s %s/%s rule after about %s"
                             % (r["severity"], fmt_duration(r["long"]), fmt_duration(r["short"]),
                                fmt_duration(r["observed_detection_s"])))
            else:
                lines.append("  does not trip %-6s %s/%s rule" % (r["severity"], fmt_duration(r["long"]),
                                                                  fmt_duration(r["short"])))
    if any("requests_in_long_window" in r for r in res["rules"]):
        lines.append("")
        lines.append("Failures needed in the long window to trip each rule:")
        for r in res["rules"]:
            lines.append("  %-6s %-8s %.2f failures (of %.0f requests)"
                         % (r["severity"], fmt_duration(r["long"]), r["failures_to_fire"],
                            r["requests_in_long_window"]))
    warns = list(res["warnings"])
    for r in res["rules"]:
        for w in r["warnings"]:
            warns.append("%s %s/%s rule: %s" % (r["severity"], fmt_duration(r["long"]), fmt_duration(r["short"]), w))
    if warns:
        lines.append("")
        lines.append("Warnings:")
        lines.extend("  - " + w for w in warns)
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Self-test: reproduces the figures in the Site Reliability Workbook ch. 5.
# --------------------------------------------------------------------------

def _close(a, b, rel=1e-3, abs_=1e-9):
    return abs(a - b) <= max(abs_, rel * abs(b))


def self_test():
    failures = []

    def check(name, cond, detail=""):
        if not cond:
            failures.append("%s %s" % (name, detail))
        print(("ok   " if cond else "FAIL ") + name)

    P = 30 * 86400
    slo = 0.999
    # Table 5-8 / 5-6: 2% in 1 h -> 14.4, 5% in 6 h -> 6, 10% in 3 d -> 1.
    rules = default_rules(P)
    check("default burn rates 14.4/6/1", [round(r["burn"], 6) for r in rules] == [14.4, 6.0, 1.0],
          str([r["burn"] for r in rules]))
    check("short windows are 5 min, 30 min, 6 h",
          [r["short"] for r in rules] == [300, 1800, 21600], str([r["short"] for r in rules]))
    res = summarise(99.9, P, rules)
    consumed = [round(r["budget_consumed"], 6) for r in res["rules"]]
    check("budget consumed 2%/5%/10%", consumed == [0.02, 0.05, 0.10], str(consumed))
    check("threshold ratios 0.0144/0.006/0.001",
          [round(r["threshold_ratio"], 6) for r in res["rules"]] == [0.0144, 0.006, 0.001])
    # B = f*P/W: 5% in 1 h -> 36.
    check("5% in 1 h is burn rate 36", _close(0.05 * P / 3600, 36.0))
    # Table 5-4: burn 1,2,10,1000 -> 30 d, 15 d, 3 d, 43 min.
    exh = [P / b for b in (1, 2, 10, 1000)]
    check("Table 5-4 exhaustion times",
          _close(exh[0], 30 * 86400) and _close(exh[1], 15 * 86400) and _close(exh[2], 3 * 86400)
          and abs(exh[3] / 60 - 43.2) < 0.1, str(exh))
    # Approach 1: 10 min window, full outage detected in 0.6 s.
    check("approach 1 detection 0.6 s", _close((1 - slo) * 600, 0.6))
    # Approach 1: 0.1% errors for 10 min uses 0.02% of the monthly budget.
    check("approach 1 spends about 0.02% of budget (10 min / 30 d = 0.023%)",
          round(600 / P * 100, 2) == 0.02)
    # Approach 2: 36 h window = 5% budget, full outage detected in 2 min 10 s.
    check("approach 2: 36 h window is 5% of 30 d", _close(36 * 3600 / P, 0.05))
    check("approach 2 detection 2 min 10 s", abs((1 - slo) * 36 * 3600 - 129.6) < 0.01)
    # Approach 3: 1 h of 100% outage burns 140% of a 30-day budget? (1 h / 43.2 min)
    check("approach 3: 1 h full outage = 139% of budget", abs(3600 / (P * (1 - slo)) - 1.389) < 0.01)
    # Approach 4: 36x for 1 h; 35x burn exhausts the budget in ~20.5 h.
    check("approach 4: 35x exhausts in 20.5 h", abs(P / 35 / 3600 - 20.57) < 0.02)
    # Reset time of the 1 h single-window alert is about 58 min.
    check("approach 4 reset about 58 min at 36x", abs(3600 * (1 - 1.0 / 36) / 60 - 58.3) < 0.1)
    # Approach 6: full outage trips the 1 h / 14.4x page after ~52 s.
    r0 = res["rules"][0]
    check("full outage trips 14.4x/1 h page in ~52 s", abs(r0["full_outage_detection_s"] - 51.84) < 0.01)
    # Extreme targets.
    r90 = summarise(90.0, P, default_rules(P))
    check("90% SLO: 2%/1 h page cannot fire", r90["rules"][0]["can_fire"] is False)
    check("90% SLO: 1 h of full outage uses 1.4% of budget", abs(3600 / (P * 0.1) - 0.0139) < 0.0005)
    r5 = summarise(99.999, P, default_rules(P))
    check("99.999%: full outage exhausts budget in ~26 s",
          abs(r5["full_outage_exhaustion_s"] - 25.92) < 0.01 and len(r5["warnings"]) == 1)
    # Canary exposure: 1% of users failing burns at 1% of the rate -> ~43 min.
    check("1% rollout exposure gives ~43 min to exhaustion at 99.999%",
          abs(r5["full_outage_exhaustion_s"] / 0.01 / 60 - 43.2) < 0.1)
    # Low traffic: 10 req/h, 99.9%, 30 d -> 7,200 requests, 7.2 failures allowed,
    # one failure is 13.9% of budget and a 10% hourly error ratio (100x burn).
    lt = summarise(99.9, P, default_rules(P), req_per_hour=10)
    check("low traffic: 7,200 requests, 7.2 allowed failures",
          _close(lt["requests_in_period"], 7200) and _close(lt["allowed_failures_in_period"], 7.2))
    check("low traffic: one failure is 13.9% of budget", abs(1 / 7.2 - 0.1389) < 0.001)
    check("low traffic: one failure in an hour is a 100x burn", _close(0.1 / 0.001, 100.0))
    check("low traffic: 1 h page rule trips on a single failure",
          any("single failed request" in w for w in lt["rules"][0]["warnings"]))
    # Observed error ratio: 1.44% is exactly the 14.4x threshold; trips pages.
    ob = summarise(99.9, P, default_rules(P), observed=0.0144)
    check("observed 1.44% = burn 14.4", _close(ob["observed"]["burn_rate"], 14.4))
    check("observed 1.44% trips the 1 h page", ob["rules"][0]["observed_trips"] is True)
    ob2 = summarise(99.9, P, default_rules(P), observed=0.002)
    check("observed 0.2% trips only the ticket rule",
          [r["observed_trips"] for r in ob2["rules"]] == [False, False, True])
    # 28-day window: 2% in 1 h is 13.44.
    r28 = default_rules(28 * 86400)
    check("28-day window: 2% in 1 h is 13.44", abs(r28[0]["burn"] - 13.44) < 1e-9)
    # Day ticket row: burn 3 over 24 h with 2 h short window.
    rd = default_rules(P, include_day_ticket=True)
    check("optional 24 h ticket row is burn 3 / 2 h short",
          rd[2]["burn"] == 3.0 and rd[2]["long"] == 86400 and rd[2]["short"] == 7200)
    # Duration parsing and rule parsing.
    check("parse_duration", parse_duration("1h30m") == 5400 and parse_duration("4w") == 28 * 86400)
    pr = parse_rule("1h:5m:14.4:page")
    check("parse_rule", pr["long"] == 3600 and pr["short"] == 300 and pr["burn"] == 14.4)
    # Input validation (a zero window or non-positive burn rate must be rejected, not crash).
    for bad in ("1h:5m:0", "1h:5m:-3", "1h:5m:nan", "0h:5m:6", "1h:5m", "1h:5m:abc"):
        try:
            parse_rule(bad)
            ok = False
        except ValueError:
            ok = True
        check("parse_rule rejects %r" % bad, ok)
    # A rule that cannot fire reports no full-outage detection time.
    check("unfireable rule has no detection time", r90["rules"][0]["full_outage_detection_s"] is None)
    # Independent hand arithmetic: 99.95% over 90 d, rule 2 h / 8x.
    rr = analyse_rule(make_rule(8.0, 7200, 600, "page"), 0.9995, 90 * 86400)
    check("99.95%/90 d 2 h at 8x: consumed 0.74%, threshold 0.004, full outage 28.8 s",
          _close(rr["budget_consumed"], 0.00741, rel=1e-2) and _close(rr["threshold_ratio"], 0.004)
          and _close(rr["full_outage_detection_s"], 28.8))
    # Render does not crash on every path.
    render(summarise(99.9, P, default_rules(P, True), observed=0.01, req_per_hour=1000))
    check("render runs", True)

    if failures:
        print("\n%d self-test(s) failed" % len(failures))
        for f in failures:
            print("  " + f)
        return 1
    print("\nall self-tests passed")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Error budget and burn-rate alert arithmetic for an SLO (see module docstring).")
    ap.add_argument("--slo", type=float, help="SLO target in percent, e.g. 99.9")
    ap.add_argument("--window", default="30d", help="SLO window, e.g. 30d, 28d, 4w (default 30d)")
    ap.add_argument("--rule", action="append", default=[],
                    help="custom rule long:short:burn[:severity], repeatable; replaces the default set")
    ap.add_argument("--include-day-ticket", action="store_true",
                    help="add the book's ticket row: 10%% of budget in 24 h (burn 3 for 30 d), short 2 h")
    ap.add_argument("--observed-error-ratio", type=float,
                    help="observed error ratio (0.01 = 1%%): report its burn rate and which rules trip")
    ap.add_argument("--requests-per-hour", type=float,
                    help="steady traffic volume: report requests per window and failures needed to fire")
    ap.add_argument("--json", action="store_true", help="print machine-readable JSON")
    ap.add_argument("--self-test", action="store_true", help="run built-in checks against the book's figures")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.slo is None:
        ap.error("--slo is required (or use --self-test)")
    if not 0 < args.slo < 100:
        ap.error("--slo must be between 0 and 100 exclusive (a 100% SLO has no error budget)")
    if args.observed_error_ratio is not None and not 0 <= args.observed_error_ratio <= 1:
        ap.error("--observed-error-ratio is a ratio between 0 and 1 (0.01 means 1%)")
    if args.requests_per_hour is not None and not (math.isfinite(args.requests_per_hour) and args.requests_per_hour > 0):
        ap.error("--requests-per-hour must be a positive number")
    try:
        period = parse_duration(args.window)
        if period <= 0:
            raise ValueError("--window must be longer than zero")
        rules = [parse_rule(r) for r in args.rule] if args.rule else default_rules(period, args.include_day_ticket)
    except ValueError as exc:
        ap.error(str(exc))
    res = summarise(args.slo, period, rules, args.observed_error_ratio, args.requests_per_hour)
    print(json.dumps(res, indent=2) if args.json else render(res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
