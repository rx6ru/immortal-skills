# Alerting on SLOs: burn rates, every approach, exact numbers

Contents: 1 goal and four attributes; 2 arithmetic; 3 the six approaches; 4 scorecard; 5 recommended rule set and deriving it for your SLO and window; 6 flagged discrepancies in the source; 7 low-traffic services; 8 extreme targets; 9 alerting at scale; 10 inhibition; 11 implementation sketch; 12 verification procedure; 13 worked checks.

Sources: SRE Workbook ch. 5 (all numbers), ch. 4 (testing alert logic), ch. 16 referenced for canarying. `scripts/burn_rate.py` reproduces the tables here; run it instead of calculating by hand.

## 1. Goal and attributes

Goal: notify a human about a significant event, meaning an event that consumes a large fraction of the error budget. Pages and tickets are the only valid ways to get a human to act. For any SLI the error budget is the allowed number or fraction of bad events, and the error rate is bad events over total events.

Judge any alerting strategy on four attributes:

- Precision: share of alerts that correspond to significant events. Fragile in low-traffic periods.
- Recall: share of significant events that raise an alert.
- Detection time: how long until a human is notified under various conditions. Long detection burns budget.
- Reset time: how long the alert keeps firing after the problem is fixed. A long reset time confuses people and trains them to ignore alerts.

## 2. Arithmetic (reproduce exactly)

Notation: SLO as a fraction, allowed error ratio (1 - SLO), period P (the SLO window), alert window W, burn rate B, observed error ratio e. Example constants: SLO 99.9%, P = 30 days = 720 h = 43,200 min, allowed ratio 0.001.

| Quantity | Formula |
|---|---|
| Burn rate | B = e / (1 - SLO). B = 1 spends the budget exactly at the end of the window |
| Time to exhaust the whole budget at B | P / B |
| Budget consumed when a rule fires on window W at burn rate B | B x W / P |
| Error-ratio threshold to put in the rule | B x (1 - SLO) |
| Burn rate for a target budget fraction f in window W | B = f x P / W (5% in 1 h: 0.05 x 720 / 1 = 36) |
| Detection time for an incident with error ratio e | ((1 - SLO) / e) x W x B; for a full outage e = 1 |

Table (99.9%, 30 days): burn rate 1 means error rate 0.1% and the budget lasts 30 days; 2 means 0.2% and 15 days; 10 means 1% and 3 days; 1,000 means 100% (full outage) and 43 minutes.

## 3. The six approaches, in increasing fidelity

Approaches 1 to 3 are stepping stones that are not viable. 4 is viable but incomplete. 6 is recommended; 5 is its precursor.

### Approach 1: error rate over a short window at or above the SLO's allowed ratio

Alert if the error ratio over 10 minutes is at least 0.001 (99.9% SLO). Budget spend detected = alert window / period = 10 min / 30 d, about 0.02%.

- For: excellent detection (0.6 s for a total outage); fires on anything threatening the SLO, so good recall.
- Against: low precision. It fires on events that barely touch the budget; with six 10-minute windows an hour you could get up to 144 alerts a day, ignore all of them and still meet the SLO.

### Approach 2: increase the alert window

Choose the fraction of budget (5% of a 30-day budget gives a 36-hour window). Detection time = (1 - SLO) / e x window; a total outage is noticed in about 2 min 10 s.

- For: good detection, better precision (errors must be sustained).
- Against: very poor reset time. A total outage fires after about 2 minutes and keeps firing for roughly the next 36 hours because the long-window average stays over threshold. Computing rates over long windows is also expensive (many data points to read).

### Approach 3: increase the alert duration (`for:` clause)

Cheap emulation of a long window: alert when the 1-minute ratio exceeds 0.001 for an hour.

- For: more precise, since errors must persist.
- Against: poor recall and poor detection, because the duration does not scale with severity: a 100% outage alerts after 1 hour, the same as a 0.2% outage, though the 100% outage burns about 140% of the 30-day budget in that hour. The timer resets when the metric briefly returns within SLO, so a flapping SLI may never alert: five-minute 100% error spikes every 10 minutes with a 10-minute duration never fire while consuming 35% of the budget (each spike is nearly 12% of the 30-day budget).
- Use only to filter very short ephemeral noise. Do not use as the main SLO alert condition.

### Approach 4: alert on burn rate

Fixed 1-hour window and 5% budget gives B = 36: alert when the 1-hour ratio exceeds 36 x 0.001.

- For: good precision, shorter window is cheaper, good detection, reset time 58 minutes.
- Against: low recall. A 35x burn never alerts yet consumes the entire 30-day budget in 20.5 hours (720 / 35). Reset time of 58 minutes is still too long.

### Approach 5: multiple burn rates and windows

Several (burn rate, window) pairs catch slow-but-significant burns. Slow burns that leave time to react go to tickets. Starting points for 99.9% over 30 days:

| Budget consumed | Window | Burn rate | Notification |
|---|---|---|---|
| 2% | 1 hour | 14.4 | Page |
| 5% | 6 hours | 6 | Page |
| 10% | 3 days | 1 | Ticket |

Shape: page if the 1-hour ratio exceeds 14.4 x 0.001 or the 6-hour ratio exceeds 6 x 0.001; ticket if the 3-day ratio exceeds 0.001. The numbers depend on the service and its baseline page load; busy services or weekend and holiday on-call constraints may justify making the 6-hour row a ticket.

- For: adapts to criticality, good precision and recall (3-day window), alert type matches urgency.
- Against: more parameters; even longer reset time (3-day window); needs inhibition so one event does not raise three notifications (10% in 5 minutes implies 5% in 6 hours and 2% in 1 hour as well).

### Approach 6: multiwindow, multi-burn-rate alerts (recommended)

Add a short confirming window so the alert fires only while the budget is still being burned. Guideline: short window = 1/12 of the long window. Example behaviour (15% errors for 10 minutes): the short-window average crosses the threshold at once; the long-window average crosses after 5 minutes, so the alert starts then; the short window drops below threshold 5 minutes after errors stop, so the alert stops; the long window alone would stay over for 60 minutes. Reset time falls from 1 hour to 5 minutes.

Recommended parameters (99.9% SLO, 30 days):

| Severity | Long window | Short window | Burn rate | Budget consumed |
|---|---|---|---|---|
| Page | 1 hour | 5 minutes | 14.4 | 2% |
| Page | 6 hours | 30 minutes | 6 | 5% |
| Ticket | 3 days | 6 hours | 1 | 10% |

Rule shape (condition is long AND short; OR across rows of the same severity):

```
page:   (ratio_1h  > 14.4 * 0.001 AND ratio_5m  > 14.4 * 0.001)
     OR (ratio_6h  > 6    * 0.001 AND ratio_30m > 6    * 0.001)
ticket: (ratio_3d  > 1    * 0.001 AND ratio_6h  > 1    * 0.001)
     [optional, in the book's printed example:]
     OR (ratio_24h > 3    * 0.001 AND ratio_2h  > 3    * 0.001)
```

- For: flexible; precision from a fixed budget fraction per alert; good recall; short reset; page or ticket by urgency.
- Against: many parameters, hard to manage per service (see section 9).

Book's verdict: in most cases multiwindow, multi-burn-rate alerting is the most appropriate way to defend an SLO.

## 4. Scorecard

| # | Approach | Precision | Recall | Detection | Reset |
|---|---|---|---|---|---|
| 1 | error rate at SLO threshold, short window | low | good | excellent | short |
| 2 | longer window (36 h) | better | good | 2 min 10 s for total outage | 36 h, very poor |
| 3 | `for:` duration | high | poor | poor (1 h whatever the severity) | timer resets on flap |
| 4 | single burn rate (36x, 1 h) | good | low (35x never alerts) | good | 58 min |
| 5 | multiple burn rates | good | good | good | long (3 d window) |
| 6 | multiwindow multi-burn-rate | good | good | good | about 5 min for the fast page |

## 5. Deriving the rule set for your own SLO and window

1. Pick budget fractions and windows: defaults 2% in 1 h (page), 5% in 6 h (page), 10% in 3 d (ticket).
2. B = f x P / W using your window P. For a 28-day window, 2% in 1 h is 0.02 x 672 = 13.44; 5% in 6 h is 5.6; 10% in 3 d is 0.933. Keep the fractions and let burn rates be non-round, or round them and accept slightly different fractions.
3. Threshold ratio = B x (1 - SLO). For a 99.99% SLO the same burn rates apply with thresholds 14.4 x 0.0001 and so on.
4. Short window = long window / 12.
5. Check each row: consumed = B x W / P; full-outage detection = (1 - SLO) x W x B; the threshold must be at most 1.0 or the rule can never fire (section 8).
6. Confirm the pair of pages plus ticket gives the human enough time: time to exhaustion at the ticket burn rate must leave room for a human response in working hours (adaptation).

Run `python3 scripts/burn_rate.py --slo 99.9 --window 28d` to print all of this.

For SLIs other than "errors" (latency, freshness, coverage), the same arithmetic applies once the SLI is a good/valid ratio; the "error ratio" is the share of events missing the threshold.

## 6. Discrepancies in the source (do not copy blindly)

- Ticket row: the book's printed ticket expression has two rows (24 h with 2 h short at burn rate 3, and 3 d with 6 h short at burn rate 1), while Table 5-8 lists only the 3-day row. Both consume 10% of the budget in their window. The 3-day row alone is the tabulated recommendation; the 24-hour row is optional (`--include-day-ticket`).
- Low-traffic example: the text calls a single failure at 10 requests an hour on a 99.9% SLO a "1,000x burn rate". The arithmetic (10% hourly error ratio over 0.1% allowed) gives 100x. Use 100x and say why if you cite it.

## 7. Low-traffic services

Problem: at 10 requests an hour, one failed request is a 10% hourly error ratio. On a 99.9% SLO the 30-day volume is 7,200 requests, so only about 7 failures are allowed, and a single failure consumes about 13.9% of the budget and would page immediately. Single requests fail for ephemeral reasons that rarely deserve a systematic response.

First ask what a single failed request costs the user. High-value, non-retried requests may justify investigating each failure, but then alerting is late by nature.

Options, usually combined:

1. Generate artificial traffic (probers, integration tests) to get signal and reuse the same SLO logic. Costs: needs a system designed for it; only part of the request types and states can be synthesised; synthetic successes can mask failures that only real users hit.
2. Combine services into a higher-level group for alerting (microservices of one product, request types of one binary), better if they share a failure domain such as a common backend database. Downside: a total failure of one member may not matter to the group; add longer-period alerts to catch 100% failures of members.
3. Change the service: client retries with exponential backoff and jitter; fallback paths that capture the request for later execution. More failures fit in the budget, more signal, more time to respond.
4. Lower the SLO or lengthen the alert window (for example 99.9% to 99%) if a single failure does not truly warrant a page. This is a product decision because it changes expectations and when the policy triggers. It is simple if reporting and alerting are parameterised by SLO.

`burn_rate.py --requests-per-hour N` shows the failures needed to trip each rule and warns when one failure is enough.

## 8. Extreme availability goals

- Very low target, for example 90%: the 2%-in-1-hour page can never fire, because a 100% outage consumes only 1.4% of a 30-day budget in an hour. Its threshold ratio would be 1.44, above 1. Retune parameters when budget windows are long relative to the target.
- Very high target, for example 99.999% monthly: a 100% outage exhausts the budget in about 26 seconds (2,592,000 s x 1e-5), shorter than a metric scrape interval, let alone alert plus SMS or email latency. Alerts cannot defend it. Design so a 100% outage is very unlikely: for example roll changes to 1% of users first, which burns at 1% of the rate and leaves about 43 minutes before exhaustion (canarying; see `arch-production-operations`).

## 9. Alerting at scale

Do not hand-tune windows and burn rates per service; with 100 microservices or 100 request types it is toil and cognitive load. Pick one parameter set and apply it everywhere (exception: temporary overrides while fixing an ongoing outage). Bucket request types by availability need and attach objectives per bucket:

| Request class | Availability | Latency at 90% | Latency at 99% | Meaning |
|---|---|---|---|---|
| CRITICAL | 99.99% | 100 ms | 200 ms | most important, for example user login |
| HIGH_FAST | 99.9% | 100 ms | 200 ms | core interactive, for example a button showing earnings |
| HIGH_SLOW | 99.9% | 1,000 ms | 5,000 ms | important but not latency-sensitive, for example a multi-year report |
| LOW | 99% | none | none | needs some availability, outages mostly invisible, for example notification polling |
| NO_SLO | none | none | none | invisible to users, for example dark launches and alpha features |

Trade-off: slightly lower fidelity to user experience in return for far less toil.

## 10. Inhibition and routing

Nested burn-rate rules fire together on one big event. Suppress lower-severity alerts for the same service and SLO while a higher one is firing, so one incident is one page (the on-call chapter counts one incident however many alerts fire). Also suppress your alerts when a dependency's alert is firing for the same cause, and alert once on a global error rate when every node shows the same rate (Workbook ch. 4). Make sure suppression ends when the event ends.

## 11. Implementation sketch (adaptation; Prometheus syntax illustrative)

```yaml
# rules.yml: one error ratio per window, from two counters named slo_errors and slo_requests
groups:
  - name: slo-recording
    rules:
      - record: job:slo_error_ratio:rate5m   # repeat for 30m, 1h, 6h, 3d (and 2h, 24h for the optional ticket row)
        expr: sum by (job) (rate(slo_errors[5m])) / sum by (job) (rate(slo_requests[5m]))
  - name: slo-alerts
    rules:
      - alert: SLOBurnPage        # 99.9% over 30 d: threshold = burn rate x 0.001
        expr: |
          (job:slo_error_ratio:rate1h > (14.4 * 0.001) and job:slo_error_ratio:rate5m > (14.4 * 0.001))
          or
          (job:slo_error_ratio:rate6h > (6 * 0.001) and job:slo_error_ratio:rate30m > (6 * 0.001))
        labels: {severity: page}
      - alert: SLOBurnTicket
        expr: job:slo_error_ratio:rate3d > (1 * 0.001) and job:slo_error_ratio:rate6h > (1 * 0.001)
        labels: {severity: ticket}
```

The file parses as YAML (checked with a YAML parser). `promtool check rules rules.yml` was not available when this skill was reviewed, so run it before deploying. Adaptation: if an outage drops traffic to zero, the ratio is empty or NaN and the rules stay silent, so add a separate check on request volume or a prober.

If your metrics are not named for the SLO, create the alias with a recording rule (as the book does for `slo_errors` from raw error counters). Use counters, not gauges, so rates over windows up to a month are computable. Any system that can compute a ratio of counters over several windows works (Datadog, Cloud Monitoring and others). Compute very long windows from recorded sub-ratios if raw rate queries are too expensive. Alert annotations should link to the SLO dashboard and runbook (`monitoring-design.md`).

## 12. Verification procedure for a proposed rule set

1. For each rule compute consumed = B x W / P and full-outage detection = (1 - SLO) x W x B. Check consumed matches the intended fraction and detection is acceptable.
2. Check the threshold ratio is at most 1 and that a full outage exhausts the budget slower than your evaluation interval plus notification latency.
3. Check a total outage trips the page; a sustained 1x burn trips the ticket; a short blip does not page (30 s of 100% errors gives a 0.83% one-hour ratio, under the 1.44% threshold, while a 5-minute full outage gives 8.3% and does page, having spent 11.6% of the budget); a 35x burn is caught by something (the 6x or 1x rule, not only a 36x rule).
4. Backtest against historical SLI data: count pages and tickets versus actual budget-burning events (precision and recall).
5. Run synthetic time series through the rules (Workbook ch. 4 test tiers, `monitoring-design.md`).
6. Confirm inhibition so a nested event is one page, not three.
7. For low-traffic services, run the failures-to-fire calculation and the 10-per-hour sanity case.
8. New paging rules run in non-paging mode (email the author) for about a week before they page (`pager-load-targets.md`).

## 13. Worked checks

- 99.9%, 30 d, page row 1: consumed 14.4 x 1 / 720 = 2%; threshold 0.0144; full outage detected after about 52 s (limited by the 1-hour window average).
- 99.9%, 30 d, ticket row: consumed 1 x 72 / 720 = 10%; threshold 0.001; exhaustion at that rate in 30 days, so a human has time.
- Error ratio 1.44% sustained: burn 14.4; budget gone in 2.1 days; the 1-hour page trips after about 1 hour, the 6-hour page after about 2.5 hours.
- A 0.2% error ratio sustained (burn 2): trips only the ticket rule; budget gone in 15 days.
- 99.99%, 4 weeks: a full outage exhausts the budget in about 4 minutes. The page rules still fire but leave almost no time; consider staged rollouts (section 8).
