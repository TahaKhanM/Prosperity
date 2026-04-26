# Mark 14 dossier — "The smart inside-touch market maker"

> Author: Round 4 counterparty-flow phase. Sources: per-mark feature CSVs at
> `prosperity-research/03_eda/round4/per_mark/Mark_14_*.csv` (3 days, 7
> products, 2,172 rows total) plus the raw quote stream
> `prosperity_rust_backtester/datasets/round4/prices_round_4_day_{1,2,3}.csv`.
> Stdlib-only analysis (csv, statistics, collections, math). Raw logs in
> `/tmp/mark14_analysis/section_*.log`.

---

## A. Headline classification

**Mark 14 is an inside-the-touch, two-sided market maker who consistently
captures the touch spread, with a small but real positive expected mid-drift
on every fill (mean adverse_select_100 = +8.65/unit on HYDROGEL_PACK,
+10.55/unit on VEV_4000, +1.27/unit on VFE; 95.8% / 100% / 84.2% of fills
profitable at h=5 ticks).** Confidence: **high**. Total Mark 14 footprint
across the 3 days: 1,003 HYD prints (4,022 units), 647 VFE prints (3,524
units), 439 VEV_4000 prints (864 units), and 83 deep-OTM voucher buys
(VEV_5200..5500). Total horizon-100 PnL across HYD+VFE+VEV_4000:
**46,457 XIRECS / 8,394 units ≈ +5.53 per unit**, matching the known
+5.71/unit headline within attribution noise.

---

## B. Volume profile

Trades, qty distribution, per-day breakdown.

### B.1 Trade counts by (product, day, side)

| Product | Day 1 buys | D1 sells | D2 buys | D2 sells | D3 buys | D3 sells | Total |
|---|---|---|---|---|---|---|---|
| HYDROGEL_PACK | 183 | 187 | 142 | 161 | 171 | 159 | **1,003** |
| VELVETFRUIT_EXTRACT | 114 | 97 | 92 | 118 | 110 | 116 | **647** |
| VEV_4000 | 91 | 72 | 64 | 64 | 77 | 71 | **439** |
| VEV_5200 | 6 | 0 | 8 | 0 | 19 | 0 | 33 |
| VEV_5300 | 6 | 0 | 14 | 0 | 10 | 0 | 30 |
| VEV_5400 | 5 | 0 | 2 | 0 | 6 | 0 | 13 |
| VEV_5500 | 3 | 0 | 3 | 0 | 1 | 0 | 7 |

Mark 14 is **two-sided on HYD/VFE/VEV_4000** and **buy-only on VEV_5200..5500**
(consistent with the deep-OTM "junk" voucher noise pattern documented in the
counterparty findings). The buy-only behaviour on the 4 stuck OTMs is
**entirely facilitated by Mark 22** (sole counterparty), so it is the
Mark 22 → Mark 14 noise corridor, not a tradeable Mark 14 alpha.

### B.2 Trade arrival rate

- HYD: 1,003 prints / 30,000 ticks = **0.0334 prints/tick**
  (≈ 1 print every 30 ticks). Median inter-arrival = **20 ticks**, p10 = 4,
  p90 = 69, p99 = 126 ticks.
- VFE: 647 / 30,000 = **0.0216 prints/tick**. Median inter-arrival = 30 ticks.
- VEV_4000: 439 / 30,000 = **0.0146 prints/tick**.

The inter-arrival distribution looks Poisson-like (long tail, mode at 4-5
ticks). **Mark 14 is approximately uniformly distributed in time** — see
also B.3 and trigger AUCs in §C.

### B.3 Per-decile firing distribution (10 buckets, decile of day)

| Decile (×100k ts) | HYD prints | VFE prints | VEV_4000 prints |
|---|---|---|---|
| 0 | 88 | 58 | 35 |
| 1 | 107 | 59 | 58 |
| 2 | 107 | 73 | 44 |
| 3 | 116 | 65 | 54 |
| 4 | 93 | 69 | 45 |
| 5 | 95 | 62 | 41 |
| 6 | 101 | 55 | 40 |
| 7 | 93 | 74 | 41 |
| 8 | 91 | 71 | 42 |
| 9 | 112 | 61 | 39 |

Range 88-116 (HYD), 55-74 (VFE), 35-58 (VEV_4000). **Time of day is not a
trigger** (peak/trough ratio ~ 1.3×); the existing `headline_findings.md`
note about ≤14 % peak-hour-bucket share is reproduced here.

### B.4 Trade-size distribution

| Product | Mean | Median | IQR | Min | Max | Top qtys |
|---|---|---|---|---|---|---|
| HYDROGEL_PACK | 4.01 | 4 | [3, 5] | 2 | 6 | {6:211, 3:206, 2:199, 4:195, 5:192} |
| VELVETFRUIT_EXTRACT | 5.45 | 5 | [4, 7] | 3 | 8 | {4:113, 3:112, 5:109, 7:107, 6:103} |
| VEV_4000 | 1.98 | 2 | [1, 3] | 1 | 3 | {1:153, 3:145, 2:141} |
| VEV_5200 | 3.70 | 4 | [3, 5] | 2 | 5 | — |
| VEV_5300 | 3.50 | 3.5 | [2, 5] | 2 | 5 | — |
| VEV_5400 | 3.69 | 4 | [3, 5] | 2 | 5 | — |
| VEV_5500 | 3.86 | 4 | [2, 5] | 2 | 5 | — |

Qty is **DISCRETIZED across [2, 6] for HYD, [3, 8] for VFE, [1, 3] for VEV_4000**
with roughly uniform mass over the discrete support. This is *not* constant
but it is **not** a continuous Pareto either — looks like the strategy
randomises the qty within a fixed bucket per product.

### B.5 Per-product specialisation

Mark 14 is **product-diversified but HYD-dominated** (46 % of prints,
48 % of horizon-100 PnL). VEV_4000 is *the* highest unit-PnL product
(+10.4/unit) — that is the deep-ITM voucher and, given parity, it's a
delta-1 proxy for the underlying. VEV_5200..5500 are buy-only flow paid for
by Mark 22 — small noise contribution.

---

## C. Trigger conditions — **NULL RESULT**

Section spec: fit a 2-3-feature classifier predicting "Will Mark 14 print
in the next 5 ticks?" using imb1, imb2, spread, recent_ret_*,
realised_vol_100, depth_imbalance.

### C.1 Per-tick AUC (panel = 30,000 ticks/day × 3 days, label = print
within next 5 ticks; positive base rate 15.79 % HYD, 10.23 % VFE)

| Feature | AUC HYD | \|0.5−AUC\| HYD | AUC VFE | \|0.5−AUC\| VFE |
|---|---|---|---|---|
| imb1 | 0.502 | 0.002 | 0.499 | 0.001 |
| imb2 | 0.501 | 0.001 | 0.499 | 0.001 |
| imb3 | 0.499 | 0.001 | 0.502 | 0.002 |
| spread | 0.498 | 0.002 | 0.506 | 0.006 |
| depth_imb | 0.499 | 0.001 | 0.502 | 0.002 |
| recent_ret_5 | 0.480 | 0.020 | 0.497 | 0.003 |
| recent_ret_20 | 0.472 | 0.028 | 0.491 | 0.009 |
| recent_ret_100 | 0.489 | 0.011 | 0.494 | 0.006 |
| realised_vol_100 | 0.505 | 0.005 | 0.500 | 0.000 |
| micro_dev | 0.502 | 0.002 | 0.499 | 0.001 |
| abs(imb1) | 0.501 | 0.001 | 0.501 | 0.001 |
| abs(imb2) | 0.501 | 0.001 | 0.493 | 0.007 |
| abs(ret_5) | 0.502 | 0.002 | 0.502 | 0.002 |
| abs(ret_20) | 0.495 | 0.005 | 0.481 | 0.019 |
| abs(micro_dev) | 0.501 | 0.001 | 0.506 | 0.006 |

**Every feature AUC is within ±0.03 of 0.50.** The strongest signal
(`recent_ret_20` → 0.472 on HYD) implies a *slight* anti-correlation with
positive momentum — i.e., Mark 14 is marginally more likely to print right
after a small DROP — but the lift is < 1.05× over the base rate.

### C.2 Decision rules tried (HYD baseline 15.79 %)

| Rule | Fired | Hits | Precision | Recall | Lift |
|---|---|---|---|---|---|
| abs(imb1) > 0.05 | 943/30,000 (3.14 %) | 157 | 16.6 % | 3.3 % | 1.05× |
| abs(imb1) > 0.10 | 880 (2.93 %) | 141 | 16.0 % | 3.0 % | 1.01× |
| abs(imb1) > 0.20 | 664 (2.21 %) | 103 | 15.5 % | 2.2 % | 0.98× |
| spread > 1 | 30,000 (100 %) | 4,736 | 15.8 % | 100 % | 1.00× |
| spread > 2 | 30,000 (100 %) | 4,736 | 15.8 % | 100 % | 1.00× |
| abs(ret_20) > 1 | 25,949 (86.5 %) | 4,076 | 15.7 % | 86.1 % | 1.00× |
| abs(ret_20) > 2 | 23,296 (77.7 %) | 3,662 | 15.7 % | 77.3 % | 1.00× |
| realised_vol_100 > 2 | 23,763 (79.2 %) | 3,778 | 15.9 % | 79.8 % | 1.01× |
| abs(imb1)>0.10 ∧ abs(ret_20)>1 | 785 (2.62 %) | 128 | 16.3 % | 2.7 % | 1.03× |

**The best rule we found has lift 1.05× — operationally indistinguishable
from random.** The same is true on VFE.

### C.3 Why the AUCs are flat

This is itself the headline finding of §C: Mark 14 prints are essentially
**Poisson-arrival** events conditional on the order book state. The
microstructure context immediately before a Mark 14 fill is **statistically
indistinguishable from a random non-Mark-14 tick**. That is what we expect
if Mark 14's strategy is **passive, two-sided, continuously resting**:
their orders are in the book *all the time*, and the print timing is
governed by when *takers* (e.g. Mark 38) arrive, not by Mark 14's reaction
function. See §E (aggressor profile) and §I (microstructure footprint) for
the orthogonal evidence.

**Operational implication for Phase 7**: do **not** try to predict
Mark 14's print timing from the public book state. Instead, predict the
*direction* once a print fires (§D, §K) and copy/lean.

---

## D. Side rule — mild mean-reverter, stateless

### D.1 Buy/sell ratio per day

| Product | D1 buy_frac | D2 buy_frac | D3 buy_frac |
|---|---|---|---|
| HYDROGEL_PACK | 0.495 | 0.469 | 0.518 |
| VELVETFRUIT_EXTRACT | 0.540 | 0.438 | 0.487 |
| VEV_4000 | 0.558 | 0.500 | 0.520 |

Mark 14 is **roughly two-sided** with mild day-to-day drift on VFE
(0.540 → 0.438 → 0.487).

### D.2 Side conditional on `recent_ret_20` (HYD)

| Bucket | n | buy_frac |
|---|---|---|
| ret_20 < −2 | 428 | **0.519** |
| [−2, −0.5) | 91 | **0.582** |
| [−0.5, +0.5] | 51 | 0.431 |
| (+0.5, +2] | 78 | 0.526 |
| ret_20 > +2 | 355 | **0.445** |

Net: **mild mean-revert taker on side selection**. When recent_ret_20 is
strongly negative (price has dropped > 2 ticks over last 20 ticks),
buy_frac = 0.519 (HYD) and 0.558 (VFE). When recent_ret_20 > 2,
buy_frac = 0.445 (HYD) and 0.445 (VFE). The lift is small (~ +5 pp
over the unconditional 0.49) but **consistent across both products and
all three days**.

### D.3 Side conditional on `imb1_pre` (HYD)

| imb1 bucket | n | buy_frac |
|---|---|---|
| < −0.4 (strong ask) | 4 | 0.250 |
| [−0.4, −0.1) | 10 | 0.800 |
| [−0.1, +0.1] | 971 | 0.490 |
| (+0.1, +0.4] | 13 | 0.615 |
| > +0.4 (strong bid) | 5 | 0.600 |

Sample sizes are tiny in the imbalanced buckets because HYD is
extraordinarily balanced at the touch (all but 32/1003 prints sit in
[−0.1, +0.1]). On VFE the imb1 distribution is wider but the side
dependence is barely above noise (buy_frac 0.525 in strong_bid vs 0.424
in strong_ask).

### D.4 Side conditional on inventory_day_pre

| Bucket | HYD buy_frac | VFE buy_frac |
|---|---|---|
| short_heavy (<−50) | 0.487 (n=226) | 0.475 (n=59) |
| short_mild (−50..−10) | 0.482 (n=112) | 0.472 (n=163) |
| neutral (−10..+10) | 0.550 (n=109) | 0.494 (n=85) |
| long_mild (+10..+50) | 0.489 (n=413) | 0.491 (n=283) |
| long_heavy (>+50) | 0.490 (n=143) | 0.526 (n=57) |

**Inventory does not move buy_frac materially.** Mark 14 is **stateless on
side selection** — they continue to print buys even when long, and sells
even when short. This is the opposite of an inventory-mean-reverting MM.

### D.5 Last-trade direction — no autocorrelation

Last-print same-side fraction: **HYD 50.7 %, VFE 55.8 %.** Mark 14's side
on consecutive prints is essentially independent (the +5 pp lift on VFE is
within day-noise).

---

## E. Aggressor profile — **passive provider, inside the touch**

### E.1 Aggressor share by side

| Product | side=buy aggressor=buy(lifter) | aggressor=sell(passive) | ambiguous |
|---|---|---|---|
| HYDROGEL_PACK (n=496 buys) | **0.00 %** | 63.1 % | 36.9 % |
| HYDROGEL_PACK (n=507 sells) | 62.3 % | **0.00 %** | 37.7 % |
| VFE (n=316 buys) | 0.32 % | 62.7 % | 37.0 % |
| VFE (n=331 sells) | 65.0 % | 0.00 % | 35.1 % |
| VEV_4000 (n=232 buys) | 0.00 % | 71.6 % | 28.4 % |
| VEV_4000 (n=207 sells) | 65.7 % | 0.00 % | 34.3 % |

`aggressor=='buy'` means the trade printed at or above the prior ask;
`aggressor=='sell'` means at or below the prior bid; `ambiguous` means
between. **For Mark 14's BUY rows, 100 % of non-ambiguous fills are
`aggressor=='sell'`** (= the trade is at the bid → Mark 14 was the
resting buyer). Mark 14 is **never** the lifter on HYD/VEV_4000, and is the
lifter on only 1/316 VFE buys. **Mark 14 is a pure passive provider.**

### E.2 Effective spread paid (price − mid_pre on buys, mid_pre − price on
sells)

| Product | BUYS mean | SELLS mean |
|---|---|---|
| HYDROGEL_PACK | **−7.99** | **−8.01** |
| VFE | −2.31 | −2.38 |
| VEV_4000 | −10.56 | −10.40 |
| VEV_5200 | −0.91 | — |

The "negative effective spread vs `mid_pre`" looks paradoxical until we
break it down by *prior bid/ask* (not prior mid):

### E.3 Where Mark 14's price actually sits relative to the prior touch

HYDROGEL_PACK BUYS (n=496):
- below prior bid: 202/496 (40.7 %)
- at prior bid: 111/496 (22.4 %)
- inside prior touch: 294/496 (59.3 %) (above bid AND below ask)
- at or above prior ask: **0/496** (0.00 %)
- price − bid_pre median = **0.00**, mean = −0.18
- price − ask_pre median = **−16.00** (i.e., 16 ticks below the prior ask)

HYDROGEL_PACK SELLS (n=507): mirror image. price − ask_pre median = 0.00,
price − bid_pre median = +16.00. **0/507 trades at or below the prior bid.**

VELVETFRUIT_EXTRACT BUYS: 25.6 % below prior bid, 37.0 % at prior bid,
74.4 % inside prior touch, 0.32 % at prior ask, 0 above. Median
(price − bid_pre) = 0, median (price − ask_pre) = −5.

VEV_4000 BUYS: 31.5 % below prior bid, 40.1 % at prior bid, 68.5 % inside.
Median (price − ask_pre) = −21.

**Interpretation**: the HYD spread normally sits at 16 ticks (bid 9988 /
ask 10004). Mark 14 quotes **inside that touch**, often at the prior bid
itself. The "below prior bid" case is when Mark 14 quotes a NEW, even
tighter bid — a price that did not exist at ts−100. By definition that
new bid is *above* the prior mid (since the spread shrank), but the
features here pull `bid_pre` from the ts−100 snapshot, so `price − bid_pre`
shows up as 0 or slightly negative. **Mark 14 is making the touch tighter
and immediately collecting.**

### E.4 Liquidity provider vs taker — verdict

**100 % liquidity provider.** Across ~1,950 directional fills,
**Mark 14 is the lifter on exactly 1 trade** (one VFE buy). The remaining
fills are a mix of (a) resting at the prior bid/ask and getting hit /
lifted, and (b) resting at a new tighter inside-the-touch quote and getting
hit on the same tick.

---

## F. Inventory dynamics

| Product | Day | n | mean | stdev | min | max | final | range |
|---|---|---|---|---|---|---|---|---|
| HYD | 1 | 370 | +18.6 | 19.9 | −30 | +57 | −9 | 87 |
| HYD | 2 | 303 | −82.1 | 36.5 | **−139** | +6 | −70 | 145 |
| HYD | 3 | 330 | +45.3 | 28.3 | −12 | +98 | +35 | 110 |
| VFE | 1 | 211 | +37.8 | 28.7 | −30 | **+117** | +117 | 147 |
| VFE | 2 | 210 | −35.5 | 27.5 | −95 | +20 | −85 | 115 |
| VFE | 3 | 226 | +15.8 | 24.2 | −41 | +53 | −34 | 94 |
| VEV_4000 | 1 | 163 | +6.1 | 20.6 | −25 | +45 | +38 | 70 |
| VEV_4000 | 2 | 128 | +5.1 | 3.7 | −4 | +13 | +8 | 17 |
| VEV_4000 | 3 | 148 | −4.3 | 5.8 | −17 | +10 | 0 | 27 |

Observations:
- **Inventory does not mean-revert to 0 within day**: per-day means span
  −82 to +45 on HYD. Same on VFE (+37.8, −35.5, +15.8). Mark 14 takes
  meaningful directional positions over multi-tick horizons.
- **Position-limit headroom**: max excursion is 139 (HYD day 2 short) and
  117 (VFE day 1 long). Both are well inside the 200 product limit, so
  Mark 14 is *not* hard-stopping at any self-imposed limit < 200.
- **Inventory range vs hit rate**: inventory_day_pre histogram shows
  Mark 14 prints uniformly across inventory buckets, including
  short_heavy (<−50: 226 prints) and long_heavy (>+50: 143 prints).
  No skip pattern.
- **Final-of-day inventory is non-zero**: ends D1=−9 / D2=−70 / D3=+35 on
  HYD. Mark 14 carries position across the daily boundary — the running
  `inventory_cum` is what matters, not `inventory_day`.

---

## G. Adverse selection — strong, broadly distributed

`adverse_select_h` = signed mid-move at horizon h. Positive means good for
Mark 14 (price moved with their direction).

### G.1 Aggregate by product (h=100)

| Product | n | mean | stdev | sum | %pos | %neg | %zero |
|---|---|---|---|---|---|---|---|
| HYDROGEL_PACK | 999 | **+8.65** | 18.21 | +8,643.5 | 67.7 % | 30.2 % | 2.1 % |
| VELVETFRUIT_EXTRACT | 639 | **+1.27** | 8.80 | +810.5 | 55.1 % | 43.8 % | 1.1 % |
| VEV_4000 | 434 | **+10.55** | 8.87 | +4,580.5 | 88.5 % | 10.8 % | 0.7 % |
| VEV_5200 | 33 | +0.91 | 6.27 | +30.0 | — | — | — |
| VEV_5300 | 30 | +1.40 | 3.05 | +42.0 | — | — | — |
| VEV_5400 | 13 | −0.42 | 2.07 | −5.5 | — | — | — |
| VEV_5500 | 7 | −0.07 | 0.62 | −0.5 | — | — | — |

### G.2 Horizon comparison (HYD)

| Horizon | mean | %pos | %neg |
|---|---|---|---|
| h=5 | +8.08 | **95.8 %** | 2.3 % |
| h=20 | +8.26 | 81.6 % | 16.2 % |
| h=100 | +8.65 | 67.7 % | 30.2 % |

**At h=5, 96 % of Mark 14's HYD fills are profitable.** This is the
hallmark of **edge from the touch**: as soon as the trade prints, the mid
has already moved 8 ticks in Mark 14's favour because Mark 14 was *quoting
inside* what later became the prevailing mid. This is the same as
"adverse-select for the COUNTERPARTY" — Mark 38 is paying 8 ticks of
adverse selection on every HYD print.

### G.3 Per (day, side) breakdown (HYD)

| (day, side) | n | mean adv100 | sum |
|---|---|---|---|
| 1, buy | 183 | +9.12 | +1669.5 |
| 1, sell | 187 | +9.62 | +1799.0 |
| 2, buy | 140 | +7.69 | +1077.0 |
| 2, sell | 160 | +5.88 | +941.5 |
| 3, buy | 171 | +9.57 | +1637.0 |
| 3, sell | 158 | +9.62 | +1519.5 |

**Stable across days and sides.** Day 2 is slightly weaker (mean +6-8 vs
+9 elsewhere) but every cell is positive.

### G.4 Top-10 % concentration

- HYD: top 10 % rows (99 prints) sum to +4,176 of total +8,643 → **48.3 %
  share**. Top 10 % of |adv100| = 26.6 % of total absolute. **Edge is
  somewhat concentrated but not all-or-nothing**: removing the best 99
  fills still leaves ~+5/unit on the remaining 900 fills.
- VEV_4000: top 10 % rows = +1,158/+4,580 → 25.3 % share. **Most
  uniform PnL distribution of the three products.** Every single VEV_4000
  fill is positive at h=5 (100 %).
- VFE: top 10 % rows = +1,051 of +810 → 130 % share (i.e., the bottom 90 %
  are net-negative; PnL on VFE is driven entirely by the top decile).
  This is consistent with the much smaller per-unit average (+1.27).

---

## H. Counterparty selection

Per-trade adverse_select_100 mean by counterparty.

### H.1 Counterparty share

| Product | Counterparty | n | mean adv100 | sum |
|---|---|---|---|---|
| HYDROGEL_PACK | Mark 38 | **1,003 (100 %)** | +8.65 | +8,643.5 |
| VELVETFRUIT_EXTRACT | Mark 55 | **647 (100 %)** | +1.27 | +810.5 |
| VEV_4000 | Mark 38 | **439 (100 %)** | +10.55 | +4,580.5 |
| VEV_5200..5500 | Mark 22 | **83 (100 %)** | +1.04 (avg) | — |

**Each Mark-14 product has a single counterparty.** Mark 14's three
productive corridors are:
- HYD ↔ Mark 38 (1,003 prints, +8.65/unit)
- VEV_4000 ↔ Mark 38 (439 prints, +10.55/unit)
- VFE ↔ **Mark 55** (647 prints, +1.27/unit)
- VEV_5200..5500 ↔ Mark 22 (noise — buy-only, no observed PnL story)

This is a critical update over the existing `headline_findings.md`
narrative: **the closed Mark 14 ↔ Mark 38 loop is HYD + VEV_4000, NOT
HYD + VFE.** VFE adversary is Mark 55, not Mark 38. VFE is a separate
duel.

### H.2 Implication for partner-detection logic

If we want a "Mark 14 just printed" signal in live R4, we can reduce it
to: **"Mark 38 (or Mark 55) just printed in HYD/VEV_4000/VFE."** Since
Round 4 discloses both names, we can build the signal directly without
needing to identify Mark 14's footprint.

---

## I. Microstructure footprint — bid/ask collapse on VFE only

Per Mark 14 print, look at the quote stream in the 5 ticks PRIOR.

### I.1 Pattern detection table

| Pattern | HYD cond / unc | HYD ratio | VFE cond / unc | VFE ratio | VEV_4000 cond / unc |
|---|---|---|---|---|---|
| bid_step_down ≥ 1 tick (1-3 ticks prior) | 63.5 % / 61.1 % | 1.04× | 52.1 % / 55.0 % | 0.95× | 57.6 % / 53.5 % |
| ask_step_up ≥ 1 tick (1-3 ticks prior) | 61.1 % / 61.8 % | 0.99× | 53.8 % / 56.0 % | 0.96× | 49.7 % / 53.6 % |
| imb1 sign flip (5 ticks) | 0.0 % / 0.04 % | 0× | 14.4 % / 17.8 % | 0.81× | 0.0 % / 0.02 % |
| **bid_volume_1 collapse > 30 %** | 11.2 % / 11.4 % | 0.98× | **74.0 % / 52.8 %** | **1.40×** | 36.2 % / 36.2 % |
| **ask_volume_1 collapse > 30 %** | 10.7 % / 11.6 % | 0.92× | **72.0 % / 52.3 %** | **1.38×** | 36.2 % / 36.3 % |

### I.2 The VFE side-conditional pattern — strongest finding in §I

Splitting by Mark 14 side on VFE:

| Pattern | VFE BUY cond | VFE SELL cond | VFE unc |
|---|---|---|---|
| bid_volume_1 collapse > 30 % (prior 5 ticks) | **97.2 %** | 52.0 % | 52.8 % |
| ask_volume_1 collapse > 30 % (prior 5 ticks) | 45.6 % | **97.3 %** | 52.3 % |

**Interpretation**: when Mark 14 BUYS VFE, the bid_volume_1 collapsed > 30 %
in the prior 5 ticks 97.2 % of the time. When Mark 14 SELLS VFE,
ask_volume_1 collapsed > 30 % 97.3 % of the time. **This is Mark 14's
own resting order being eaten** — the depth disappears one tick before the
trade prints because the trade IS the disappearance. The 50 % unc baseline
is the natural VFE quote churn.

### I.3 Verification by direct depth-diff arithmetic

Using `bid_diff = bid_volume_1@(ts−100) − bid_volume_1@(ts)` and
comparing to Mark 14's qty:

VFE BUY (n=316):
- bid_diff ≥ qty: 178/316 (**56.3 %**) → Mark 14 was the resting bid
  whose level was eaten by their own qty.
- ask_diff ≥ qty: 97/316 (30.7 %) → Mark 14 lifted the ask in
  ~30 % of cases (these will mostly be the `aggressor=='ambiguous'` rows
  where the trade printed inside, or where the order book had multiple
  size at the same level).

VFE SELL (n=331):
- ask_diff ≥ qty: 181/331 (**54.7 %**) → resting ask filled.
- bid_diff ≥ qty: 114/331 (34.4 %).

VEV_4000 BUY (n=232):
- bid_diff ≥ qty: 75/232 (32.3 %)
- ask_diff ≥ qty: 78/232 (33.6 %)

HYD BUY (n=496):
- bid_diff ≥ qty: 50/496 (10.1 %)
- ask_diff ≥ qty: 50/496 (10.1 %)

HYD has very low matches because the standard HYD touch is 16 ticks
wide — Mark 14 is quoting INSIDE the touch on a brand-new price level
(see §E.3) that didn't exist at ts−100, so the bid_diff arithmetic at the
*old* level can't pick up the fill. On VFE, the touch is 5-6 ticks wide
and Mark 14 quotes much closer to (or AT) the existing bid_1, so the
self-impact arithmetic resolves cleanly.

### I.4 Pattern flagging

Per spec: flag patterns with cond > 60 % AND unc < 20 %.
- bid_step_down (HYD): cond 63.5 %, unc 61.1 % → **NOT FLAGGED** (unc too high).
- bid_volume_1 collapse, VFE BUY: cond 97.2 %, unc 52.8 % → **NOT FLAGGED**
  (unc too high) — but strong asymmetry vs SELL side (51.96 %), and **the
  ratio of 1.84× cond/unc is the strongest microstructure signal we
  observe**. The pattern is real but it's a self-impact artifact, not a
  prior-state signal.

**No pattern reaches the formal flag threshold.** The strongest signal
(VFE bid-collapse on BUYS) is mechanistically explained as Mark 14's own
order being filled — it cannot be used as a forward-looking trigger.

---

## J. Bot archetype

**Archetype: market maker (passive two-sided quoter, inside-the-touch).**
Confidence: **high.**

### J.1 Three strongest evidence features

1. **0 % aggressor rate**. 0/496 HYD buys, 0/232 VEV_4000 buys, and 1/316
   VFE buys are aggressive lifts. Pure resting-order fills (§E.1).
2. **Inside-the-touch pricing.** 0/496 HYD buys ever print at or above the
   prior ask; median price − ask_pre = −16 (HYD), −5 (VFE), −21
   (VEV_4000). Mark 14 quotes inside the displayed touch (§E.3).
3. **Two-sided pairing.** 96.4 % of HYD prints have an opposite-side
   Mark 14 print within 100 ticks; 78-85 % on VEV_4000/VFE. Inter-arrival
   gap mode = 4-5 ticks. Consistent with continuous two-sided book
   provision (§B.2, §F).

### J.2 Why NOT each of the alternatives

- **Momentum taker**: aggressor rate is 0 %; momentum-taker would lift
  the ask, not rest. Also recent_ret_20 sign rule is mean-reverting, not
  pro-momentum.
- **Mean-revert taker**: §D.2 shows a *mild* mean-revert tilt on side, but
  rate is identical to a passive two-sided MM whose *quotes* survive
  longer when the price moves the right way. Also — taker would need
  positive aggressor rate.
- **Hedger / basket**: cross-product correlation does not show forced
  hedge timing (the VEV_4000 / VFE cross-product spillover is opportunistic,
  not synchronous; see `cross_product_findings.md`).
- **Gamma scalper**: would need delta-driven refresh; would not have a
  near-Poisson timing distribution and would not be flat-AUC vs realised
  vol.
- **Latency arb**: would lift in both directions, sometimes mid-tick;
  Mark 14 is 0 % aggressor.
- **Quote provider at edge**: Mark 14 is the OPPOSITE — quotes INSIDE the
  touch, not at the edge of the displayed book.

---

## K. Exploitation hypothesis — pre-registered

### K.1 The headline alpha

**"When Mark 38 prints in HYDROGEL_PACK or VEV_4000, or when Mark 55 prints
in VELVETFRUIT_EXTRACT, lean WITH the Mark 14 side (= AGAINST Mark 38 /
Mark 55) for a 100-tick horizon."**

By identity: Mark 14 BUY ⇔ Mark 38/55 SELL. So the rule reduces to
"fade Mark 38 in HYD/VEV_4000 and fade Mark 55 in VFE." This is the same
fade rule that comes out of the Mark 38 dossier viewed from the other
side, but Mark 14 is the cleaner anchor because their adverse-selection
distribution is sharper (95-100 % positive at h=5).

### K.2 Two flavors

#### Flavor 1 (**REACT**): copy-the-fill structure

```
Trigger: a trade prints with counterparty=='Mark 38' and product in
         {HYDROGEL_PACK, VEV_4000}.
         OR counterparty=='Mark 55' and product=='VELVETFRUIT_EXTRACT'.
Side:    take the OPPOSITE side of Mark 38/55 (= the SAME side as Mark 14).
Size:    1 contract per Mark 38/55 unit, capped at our position-limit
         headroom.
Hold:    20 ticks.
Exit:    take-profit at +5 ticks of mid move (HYD: +5 = ~57 % of mean
         h=20 adv); stop-loss at −12 ticks (= mean adv h=100 stdev 18.21
         × 0.66).
```

EV pre-registration:
- HYD: at h=20, mean adverse_select_20 = +8.26/unit; at h=5, +8.08/unit;
  fraction positive at h=5 = 95.8 %, at h=20 = 81.6 %.
- Daily fires expected: ~333 HYD prints × 0.5 (we mirror only one side
  to avoid double-counting) ≈ 166 fires.
- EV/day (HYD only) ≈ 166 × 8.0 ≈ **+1,328 ticks of mid-move** at qty=1.
  At avg qty 4 (Mark 14's mean), this is ≈ 5,300 ticks of pure mid-move
  if we match qty.
- BUT: realised PnL has to overcome our own taker spread (HYD touch ~16),
  so we'd be a taker paying 8 ticks to capture 8 ticks of expected
  drift → roughly break-even on HYD as a pure copy unless we *also*
  improve our entry (post a passive limit at the same price level as
  Mark 14, or one tick worse, and only fall back to taker after k ticks).
- VEV_4000: mean adv h=20 = +10.23, std 8.87, h=5 mean = +10.27, 100 %
  positive at h=5. ~146 fires/day. EV ≈ 146 × 10 = **+1,460 ticks/day**.
  VEV_4000 spread is ~42 ticks (the 2× ITM intrinsic spread), so
  taker-only is unprofitable. **Must be quoted passively.**
- VFE: mean adv h=20 = +1.99, std 7.91, 68.8 % positive. ~216 fires/day.
  EV ≈ 216 × 2 = **+432 ticks/day**.

#### Flavor 2 (**COMPETE**): inside-the-touch quoting against Mark 14

```
Strategy: continuously quote one tick INSIDE Mark 38/55's apparent
          resting size. On HYD: if Mark 38 has resting bid_1 at price B,
          we post a buy at B+1 with size 1, refreshed every tick.
          Symmetric on the ask side.
Risk:     position-limit-bounded (HYD 200, VFE 200, VEV_4000 300).
          Skip the offer if ABS(inventory_day) > 0.7 × limit.
Stop:     if we observe 5 consecutive losses against Mark 14 (i.e., they
          quoted even tighter), revert to mid quoting.
```

This is a **race-to-the-touch** play that splits the +8 tick edge with
Mark 14 (since both of us would be inside-the-touch resters). EV is
harder to estimate because it depends on Mark 14's reaction; the
falsifier here is "Mark 14 widens / disappears when we quote tighter."
Worst case we cede the alpha back to Mark 38; best case we capture half.

### K.3 Pre-registered parameters

For Phase 7 probe trader. Use exactly these:

| Parameter | Value | Source |
|---|---|---|
| trigger_marks | {Mark 38, Mark 55} | §H |
| products | HYDROGEL_PACK, VELVETFRUIT_EXTRACT, VEV_4000 | §B.1 |
| side_rule | mirror_mark_14_inferred (opposite of Mark 38/55) | §K.1 |
| qty_rule | min(mark_38_qty, our_pos_headroom) | §B.4 |
| hold_ticks | 20 | §G.2 |
| tp_ticks (HYD) | +5 | §G.2 (≈ 60 % of mean adv h=20) |
| sl_ticks (HYD) | −12 | §G.1 stdev × 0.66 |
| tp_ticks (VEV_4000) | +6 | §G.1 mean +10, std 8.87 |
| sl_ticks (VEV_4000) | −10 | |
| tp_ticks (VFE) | +2 | §G.1 mean +1.27, std 8.80 |
| sl_ticks (VFE) | −5 | |
| inventory_skip | abs(inventory_day) > 0.7 × position_limit | §F |
| daily_fire_expectation | 166 HYD + 146 VEV_4000 + 216 VFE = 528/day | §B.2 |
| ev_target | +1,300 (HYD) + +1,460 (VEV_4000) + +432 (VFE) ≈ +3,200 ticks/day | §K.2 |

### K.4 Falsifiers

Each of these observations would kill the hypothesis:
1. **Live aggressor flip**: if in live Round 4, Mark 38's effective
   spread profile flips from 0 % aggressor to >30 %, the entire role
   has been swapped — back-test alpha is dead.
2. **Adv h=5 sign flip**: if in any 1k-print rolling window in live
   data, the share of adverse_select_5 > 0 falls below 70 % (vs the
   95 % historical), the partnership is no longer one-sided.
3. **Counterparty re-routing**: if Mark 38 prints with a Mark other
   than Mark 14 on > 20 % of HYD prints in live, the closed loop is
   broken (and Mark 14 may have been replaced).
4. **Crowding by competitors**: if our taker mirroring fails on
   ≥ 30 % of triggers because Mark 14 (or another fast bot) lifted
   first, the alpha has been arbed away.
5. **Per-day collapse**: if any single live day's mean
   `adverse_select_100` for the mirror trades is < 0, abort the
   strategy until next day's open.

### K.5 What the cross-product VEV spillover note does NOT add

The known "Mark 14 buys VEV_5200 → deeper-ITM jump" is not re-derived
here (per spec). For the record: VEV_5200..5500 are the 4 stuck-OTM
vouchers, all bought from Mark 22, with weak marginal PnL (+0.91, +1.40,
−0.42, −0.07 mean adv100). They are NOT in the K.1 trigger set. The
spillover is treated as orthogonal information for §C of the
`derivatives-voucher-analyst` phase.

---

## Appendix — raw computational notes

- 30,000 quote ticks per product per day, 3 days = 90,000 panel rows for
  the AUC analysis (HYD).
- Positive label rate (within 5 ticks of any Mark 14 print): HYD
  **15.79 %**, VFE **10.23 %**, VEV_4000 not run (sample of 439 prints
  is small).
- All computations use stdlib (`csv`, `statistics`, `collections`).
  Mann-Whitney AUC is computed with tie-aware average ranks.
- Quote-stream join uses last-tick-≤-target-ts lookup via binary search
  on per-day sorted `mids`.
- Self-impact arithmetic compares quote at ts−100 vs quote at ts (the
  trade tick is the post-quote of the prior tick + the trade itself).
- Logs: `/tmp/mark14_analysis/section_b_to_h.log`,
  `/tmp/mark14_analysis/section_c.log`,
  `/tmp/mark14_analysis/section_c_plus.log`,
  `/tmp/mark14_analysis/section_i.log`,
  `/tmp/mark14_analysis/section_extra.log`,
  `/tmp/mark14_analysis/section_extra2.log`.
