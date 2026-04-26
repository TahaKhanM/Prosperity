# Mark 67 — VELVETFRUIT_EXTRACT buy-only resting bidder

> Source rows: 165 (`per_mark/Mark_67_VELVETFRUIT_EXTRACT.csv`).
> Quote stream: `prosperity_rust_backtester/datasets/round4/prices_round_4_day_{1,2,3}.csv`
> (VFE rows only).

## A. Headline classification

**Passive-side, buy-only specialist on VELVETFRUIT_EXTRACT.** Mean qty 9, max
15, ~55 prints/day, all `side='buy'`. **Edge is real at short horizons
(h=5 mean +1.19/unit, t=3.45–5.90 every day) but DECAYS to noise / loss at
horizons ≥ 100 ticks (h=100 day-3 mean −1.37, t=−0.93; h=500 day-3
−1.38/u).** Confidence: short-horizon edge HIGH; long-horizon edge LOW
(selection-bias suspect — see §K reconciliation).

## B. Volume profile

| Day | Prints | Total qty | qty mean | qty median | qty max | Span (ticks) |
|---|---|---|---|---|---|---|
| 1 | 58 | 519 | 8.95 | 8.5 | 15 | 9,759 |
| 2 | 61 | 567 | 9.30 | 9 | 15 | 9,926 |
| 3 | 46 | 424 | 9.22 | 9 | 15 | 9,529 |
| **Σ** | **165** | **1,510** | — | — | — | — |

`qty` is integer-valued and discrete with NO single mode — bimodal across
{5,7,8,9,10}. Distribution: 1×1, 2×1, 5×16, 6×11, 7×17, 8×29, 9×24,
10×18, 11×12, 12×11, 13×7, 14×11, 15×7. Modal qty=8 (29 prints).
Inter-arrival median ≈ 14,000 ts units (140 ticks); mean ≈ 18,000;
range 300–90,000. Print rate ≈ 1 print per 180 ticks ≈ **5.5
prints / 1,000 ticks**.

## C. Trigger conditions (per-tick "Mark 67 buys in next 5 ticks?" classifier)

Built over all 30,000 VFE quote-ticks/day; 820 positive ticks, 29,180
negative. **All single-feature AUCs are within 0.482–0.510 of 0.500 — the
firing time is essentially unpredictable from microstructure.**

| Feature | AUC | pos mean | neg mean |
|---|---|---|---|
| imb1_pre | 0.5104 | +0.013 | +0.001 |
| depth_ask | 0.5101 | +60.6 | +60.4 |
| depth_bid | 0.5063 | +60.6 | +60.4 |
| spread | 0.5056 | 5.00 | 4.98 |
| imb2_pre | 0.5025 | +0.001 | +0.000 |
| realised_vol_100 | 0.4984 | +1.131 | +1.129 |
| imb3_pre | 0.4967 | −0.001 | +0.000 |
| ask_volume_1 | 0.4927 | 37.3 | 37.7 |
| recent_ret_20 | 0.4927 | −0.083 | −0.005 |
| recent_ret_5 | **0.4822** | **−0.140** | +0.002 |

The strongest signal is `recent_ret_5` (pre-tick 5-tick mid drift): Mark 67
fires slightly more often after a 5-tick DIP. But |AUC − 0.5| = 0.018, so
the gate is weak.

**Best 2-feature gate** (`imb2_pre > 0` AND `recent_ret_20 < 0`):
- day 1: 180 hits / 5 fires (precision 2.78 %)
- day 2: 206 hits / 2 fires (precision 0.97 %)
- day 3: 192 hits / 4 fires (precision 2.08 %)

Marginal lift over base rate (820/30000 ≈ 2.7 %). **Conclusion: Mark 67
fires on a hidden schedule, not on visible microstructure.** Do NOT try to
predict their print times.

## D. Side rule — N/A

Mark 67 has 165 buy rows, 0 sell rows. The "non-fire" condition is
**flat-quote silence**: when no large counterparty seller (Mark 22 / Mark 49)
is dumping, Mark 67 doesn't print. Their book is one-sided — they
accumulate, never trim.

## E. Aggressor profile

| Aggressor | n | % | mean(price − mid_pre) |
|---|---|---|---|
| `buy` (lifted ask) | 3 | 1.8 % | +1.50 |
| `sell` (was passive at bid, hit by seller) | 21 | 12.7 % | −2.45 |
| `ambiguous` (between bid–ask) | 141 | **85.5 %** | −0.81 |

Effective spread paid (price − mid_pre) full sample: mean **−0.98 ticks**,
median **−1.0**.

**Mark 67 buys CHEAP** — they nearly always (97 %+) get hit at or below
mid. The print-price distribution is concentrated:

| price − mid_pre | n |
|---|---|
| −2.5 | 14 |
| **−1.5** | **56** |
| −1.0 | 15 |
| −0.5 | 43 |
| 0.0 | 8 |
| +0.5 | 17 |

With modal `spread_pre = 5` (127 of 165 fires) and `spread_pre = 6` (30 of
165), Mark 67 prints almost exclusively when the book is wide (≥ 5 ticks).
Their typical print at `mid − 1.5` corresponds to `bid_1 + 1` — i.e.
**they appear to be a resting LIMIT BUYER one tick inside best bid**, and
get filled when an aggressive seller crosses into them. (Mid_pre is
quote-AT-PRIOR-TICK; the book then steps down between snapshots, so mid_pre
overstates fill-time mid.)

This is consistent with `aggressor='ambiguous'` (price strictly between
bid_1_pre and ask_1_pre on the prior snapshot) being 85 % of fires.

## F. Inventory dynamics

| Day | Inv start | Inv end | Max | Monotonic? |
|---|---|---|---|---|
| 1 | 12 | 519 | 519 | No (some same-ts ties) |
| 2 | 8 | 567 | 567 | No |
| 3 | 7 | 424 | 424 | No |

`inventory_day` resets each day. **Cumulative inventory ends day 3 at +1,510
— well above the VFE position limit of 200.** Either Mark 67 is an
algorithmic specialist with no per-product limit (a "research bot" /
market-watcher), or their accounting differs from ours.

Practical implication: **WE cannot replicate their accumulation** — at +200
we are forced flat.

## G. Adverse-selection by day (the critical decay table)

| h | Day 1 mean | Day 2 mean | Day 3 mean | Day 1 t | Day 2 t | Day 3 t |
|---|---|---|---|---|---|---|
| 5 | +1.36 | +0.94 | +1.15 | **5.90** | **4.05** | **3.45** |
| 20 | +1.20 | +0.64 | +1.40 | 2.38 | 1.31 | 2.18 |
| 100 | +2.31 | +0.68 | **−1.37** | 1.70 | 0.69 | **−0.93** |
| 500 | +2.17 | −0.94 | −0.29 | — | — | — |

**At h=5 the edge is robust** (mean ≈ +1.0–1.5, t ≥ 3.4 every day).
**At h=100 the day-3 sign FLIPS** — Mark 67's prints adverse-select the
buyer (mid drops by −1.37 in 100 ticks). **At h=500 only day 1 is a winner
on a per-unit basis.**

Concentration of `adverse_select_5`: top-10 % of fires deliver 37 % of total
adv-select sum — moderately spiked but not brittle. h=20 is more brittle
(top-10 % share 72 %); h=100 has total close to zero so concentration ratio
explodes (>200 %).

**Replicated Mark 67 PnL** (Σ qty × (mid_post_h − price)):

| h | Total PnL | Per-unit |
|---|---|---|
| 5 | **+1,796** | **+1.189** ← matches headline number |
| 20 | +1,551 | +1.027 |
| 100 | +1,252 | +0.837 |
| 500 | +338 | +0.240 |

The widely-quoted "+1.19/unit, +1,796 total" headline is **horizon-5**, not
horizon-500. **At horizon 500 (the standard h500 PnL convention) Mark 67
makes only +0.24/u, and day 3 alone loses −1.38/u.**

## H. Counterparty selection

| Counterparty | trades | qty | adv100 mean | h500 mean |
|---|---|---|---|---|
| Mark 49 | 89 | 963 | **+1.27** | +0.24 |
| Mark 22 | 75 | 546 | −0.27 | +0.04 |
| Mark 55 | 1 | 1 | +20.50 | +30.00 (singleton) |

**Mark 67 → Mark 49 is the edge-bearing pair.** Mark 49 is the modest
informed VFE seller from the round-context table; on Mark 67's buys facing
Mark 49, average h=100 mid-move is +1.27 ticks. By contrast facing
Mark 22, h=100 average is −0.27 (Mark 22 is the bigger volume on the
voucher side — these VFE prints are likely Mark 22 unwinding stale inventory
into Mark 67's resting bid).

**Day-by-day counterparty edge:**

| Day | vs Mark 22 (n, adv100) | vs Mark 49 (n, adv100) |
|---|---|---|
| 1 | n=32, +2.75 | n=26, +1.77 |
| 2 | n=26, **−1.54** | n=35, +2.37 |
| 3 | n=17, **−4.03** | n=28, **−0.54** |

Day-3 collapse is driven by Mark 22's flow: Mark 22 dumps INTO Mark 67 at
adverse −4.03 mean, suggesting Mark 22 has an information edge on the
day-3 down-leg of VFE that Mark 67 does not.

## I. Microstructure footprint (5-tick prior window)

165 fires vs 29,991 baseline VFE quote-ticks:

| Pattern | Fire rate | Baseline | Conditional uplift |
|---|---|---|---|
| ask1 stepped down (3-ticks prior to now) | 32.7 % | 39.0 % | **negative** |
| ask_volume_1 dropped | 50.9 % | 48.3 % | +2.6 pp |
| mid stepped down 3 ticks back | 40.6 % | 42.4 % | −1.8 pp |
| imb1_pre > 0 | 30.3 % | 29.5 % | +0.8 pp |
| imb2_pre > 0 | 2.4 % | 3.7 % | −1.3 pp |
| spread_pre = 1 | 1.2 % | 0.6 % | +0.6 pp |

**No pattern exceeds 60 % conditional rate or substantially deviates from
baseline.** `ask_volume_1 < median(24)` ALSO does not differentiate
(`ask_volume_1` mean at fire = 37.6 vs baseline 37.7; medians 25 vs 24).

The microstructure is silent before each Mark 67 print. They are NOT firing
on book signals — they are firing on either (a) an internal alpha
(invisible to us) or (b) randomly at a fixed cadence with passive-rest
fills.

## J. Bot archetype

**"Resting passive-buyer at bid+1 on VFE"** — likely a slow accumulating bot
that posts hidden / mid-pegged limit buys at `mid_pre − 1.5` (i.e. bid + 1
when spread is 5) and waits to be hit by aggressive sellers.

Three evidence features:
1. **Aggressor distribution: 85 % ambiguous, 1.8 % lifting** — they almost
   never cross the spread aggressively.
2. **Modal price = mid_pre − 1.5 with modal spread = 5** — they rest
   one tick inside best bid; the book then steps down to them and they fill.
3. **Trigger micro-features all AUC ≈ 0.50** — they don't react to the
   book; they just sit there.

**Confidence: HIGH on archetype (passive bidder); MEDIUM on
"informed-vs-noise" classification — see reconciliation below.**

## K. Exploitation hypothesis

### Pre-registered rule (PRIMARY, h=5 carry trade)

> When Mark 67 prints a buy on VELVETFRUIT_EXTRACT, lean +VFE for **N=5
> ticks** at skew **M=1 tick** above mid (i.e. willing to bid up to mid+1
> for 5 ticks; max position +30).

Expected per-fill mid-move at h=5: +1.0 to +1.5 ticks. With ~55 fires/day
and edge per fire ≈ 0.5 ticks net of spread cost, expected daily gross PnL
≈ 25 ticks × 5 contracts ≈ 100–150 XIRECS.

### Pre-registered rule (SECONDARY, counterparty-gated)

> When Mark 67 prints a buy AND counterparty == "Mark 49", extend lean to
> N=20 ticks. (Mark 49 trades have +1.27 mean adv100 stable across 2 of 3
> days.)

### Falsifiers (kill conditions, in priority order)

1. **h=5 t-stat null:** if in any live day the per-fire `mid(t+5) − price`
   mean drops below +0.5 with t < 2.0, kill the rule that day.
2. **Day-3-style flip:** if `mid(t+100) − price` mean turns negative with
   t < −1, downgrade horizon from 5 to 1 (immediate rebate exit).
3. **Counterparty Mark-49 edge null:** if Mark 67 → Mark 49 fires for
   the day register adv100 mean < 0, switch off the secondary rule.
4. **Microstructure shift:** if Mark 67's fire-time `aggressor='buy'` rate
   rises above 20 % (they start lifting ask), they have changed character;
   recompute everything.

### Anti-rules

- DO NOT pre-position before Mark 67 fires — fire-time prediction AUC ≈
  0.50, no edge.
- DO NOT extend horizon beyond 100 ticks — h=500 has only +0.24/u and the
  per-day variance dominates.
- DO NOT copy their entry style (passive at bid+1) — we cannot replicate
  their unbounded inventory accumulation; at our 200-cap we will be
  forced flat exactly when they are still buying.

## Reconciliation note (the prior-session "null-failure")

**Hypothesis tested:** is +1.19/u evidence of Mark 67 being informed, or is
it just selection bias on long-VFE drift days?

**Evidence:**

| Day | VFE mid drift (start→end) | Mark 67 prints | adv5 mean | adv100 mean | h500/u |
|---|---|---|---|---|---|
| 1 | 5245 → 5266 (**+20.5**) | 58 | +1.36 | +2.31 | **+1.19** |
| 2 | 5268 → 5296 (**+28.0**) | 61 | +0.94 | +0.68 | +0.55 |
| 3 | 5296 → 5232 (**−63.5**) | 46 | +1.15 | **−1.37** | **−1.38** |

**Two answers, depending on horizon:**

1. **At h=5 the edge is REAL and robust to direction.** All three days
   produce mean adverse-select 5 ≥ +0.94 and t ≥ 3.45. Even on day 3
   (sharply negative drift) Mark 67's *immediate* 5-tick post-mid is
   significantly above price. This means **there is genuine 5-tick
   continuation when Mark 67 fires** — likely because the seller they are
   matched with stops selling immediately after the print, and the book
   re-prices off the now-stale ask. This is a microstructure rebound, not
   "informed buying."

2. **At h ≥ 100 the edge is mostly drift.** The per-day h500/u correlates
   1:1 with VFE drift sign (rank order: day 1 +20 → +1.19, day 2 +28 →
   +0.55, day 3 −63 → −1.38). Print-rate also correlates with drift
   magnitude (day 3 sees fewer prints — 46 vs 58/61). **The "+1.19/u"
   headline is the h=5 number; at h=500 the figure collapses to +0.24/u.**

**Conclusion on the null-failure:** the prior session's null-failure was
correct in spirit. **Mark 67's headline is REAL only at very short horizons
(≤ 20 ticks) where mean reversion / passive-fill rebound dominates.** At
medium-to-long horizons, what looked like alpha is selection bias on
direction-of-drift days. Day 3 — a sharp down day — is a clean
counterfactual: Mark 67 keeps buying, and at h=100 their prints LOSE on
average.

**Implication for our R4 trader:** Use the Mark 67 print as a **5-tick
mean-reversion signal**, not as a directional informed-flow signal.
Specifically: if Mark 67 prints, the 5-tick post-mid is ~1 tick above their
fill price → we can sell into the bounce or tighten our short-term ask
quote by 1 tick. We should NOT carry +VFE inventory for 100+ ticks on the
basis of a Mark 67 print.

## Sanity-check artefacts

| Quantity | Value |
|---|---|
| Total prints | 165 |
| Total qty | 1,510 (matches counterparty_findings.md) |
| Σ qty × (mid_post_5 − price) | +1,796 (matches +1,796 headline) |
| Per-unit at h=5 | +1.189 (matches +1.19) |
| Per-unit at h=500 | **+0.240** (NOT +1.19 as labelled in counterparty_findings.md) |
| Days where h=100 t-stat ≥ 2.0 | 0 |
| Days where h=5 t-stat ≥ 3.0 | 3 |

> The `counterparty_findings.md` table labels Mark 67's PnL column as
> "h500 PnL" but the +1,796 / +1.19 numbers reproduce exactly only at
> h=5. Recommend correcting the column header in that file.
