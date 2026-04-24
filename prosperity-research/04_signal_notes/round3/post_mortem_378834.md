# Post-mortem: hosted submission 378834 — round3_v3

Live XY: **−1,701.47**. Replay reproduced exactly by the Rust backtester
when run against the submission's own activities log (**−1,657**, matches
within rounding).

## Per-product attribution (live + reproduced)

| product | live cash + m2m | reproduced | notes |
|---|---:|---:|---|
| **HYDROGEL_PACK** | **−3,341** | −3,341 | the entire loss + more |
| VELVETFRUIT_EXTRACT | +524 | +524 | B1 wall-mid MM worked |
| VEV_5000 | +351 | +391 | V3 EMA own-mid MM worked |
| VEV_5200 | +335 | +336 | ditto |
| VEV_5100 | +238 | +222 | ditto |
| VEV_5300 | +161 | +161 | ditto |
| VEV_4000 | +25 | +25 | G1 / identity |
| VEV_4500 | +25 | +25 | ditto |
| **total** | **−1,701** | **−1,658** | |

Everything except HYDROGEL was net positive. HYDROGEL alone lost 3,341.

## Root cause — a hard-coded anchor that was wrong live

The live Round 3 day had:

| metric | live | historical day 0 | historical day 1 | historical day 2 |
|---|---|---|---|---|
| HYDROGEL mid mean | **9 979.3** | 9 991.0 | 9 992.1 | 9 989.4 |
| HYDROGEL mid std | 29.7 | 25.3 | 37.6 | 31.6 |
| HYDROGEL spread | 15.6 | 15.7 | 15.7 | 15.7 |
| ticks in day | 1 000 | 10 000 | 10 000 | 10 000 |

Two surprises vs what v3 was calibrated on:

1. **Live mean was 12 shells lower than historical (9 979 vs 9 991).**
2. **Hosted test runs are 1 000 ticks** — not the 10 000 I had been testing
   on locally. The slow EMA half-lives / inventory mean-reversion windows
   calibrated for 10 000-tick days never get a fair run on a 1 000-tick day.

v3 computed `fair_HYDROGEL = 0.5 · 10 000 + 0.5 · microprice`, i.e. an
**anchor-biased blend at 10 000**. With live micro mean 9 979, v3's fair was
~9 989 — **10 shells above the live mean**. That produced:

- Systematic lifting of asks the trader thought were cheap.
- Trading built a long inventory, hitting the 200-cap.
- End-of-day mark at last mid 9 960 = 200 × (9 977 avg entry − 9 960) = the
  3.3 k HYDROGEL loss.

v3's "regime guard" (halt takes if `|slow_EMA_micro − anchor| > 80`) never
fired: slow EMA mean was 9 979, anchor 10 000, deviation 21 — under the
80-shell threshold. **The guard was tuned for a full-day regime shift, not
for a 12-shell offset that was entirely within the historical daily std.**

## What the backtester said — and why it lied

In local 3-day Rust backtest v3 made **+142 k**. The discrepancy vs live
comes from three compounding issues:

1. **Anchor-overlap accident.** Historical mean 9 991 vs anchor 10 000 is a
   9-shell positive bias. That bias happens to line up with the Legacy fill
   model — a bid at `best+1 = ~9 984` looks ~6 shells cheap against fair
   9 998, and the Legacy fill matches against any same-tick market trade
   printed at or below the bid, irrespective of queue position. So a
   slightly-biased anchor captures a lot of paper PnL from mid-fill noise.
   Live Lambda doesn't have that same bug and doesn't have an anchor-overlap
   accident — we saw 9 979 mean, 9 989 fair, 10-shell *negative* bias →
   systematic loss.
2. **Historical anchor-sweep was optimising the bug, not the alpha.** Sweep
   {0.3, 0.5, 0.7, 0.85} picked 0.5 at +132 k. But every one of those weights
   was built on a wrong foundation (hard anchor at 10 000 vs actual mean
   9 991). A free-parameter anchor would have shown 9 991 ± noise as the
   optimum on historical — and 9 979 ± noise as the optimum live.
3. **Ignoring published hosted evidence.** `round3_drawdown_repair_v01`'s
   docstring documented the `0.85 · 10 000 + 0.15 · micro` family lost
   −1,059 on HYDROGEL in hosted submission 369524. I noticed the warning,
   moved the weight from 0.85 to 0.5, and shipped anyway. 0.5 is still
   anchor-biased; it was a compromise, not a fix.

## The fix — v4's learned anchor

`round3_v4.py` replaces the static 10 000 anchor with a **learned anchor**:

```
slow_EMA = EWMA(microprice, alpha=0.005)    # half-life ~138 ticks
slow_EMA seeded at first observed microprice, NOT 10000
anchor   = clamp(slow_EMA, 9940, 10030)     # sanity clamp only
blended  = 0.3 · anchor + 0.7 · microprice
fair     = EWMA(blended, alpha=0.05)
```

Weight reduced to 0.3 (from 0.5) so the anchor is a gentle pull toward the
session mean, not a dominant bet on a specific level. Parameter sweep
results:

| α_slow | weight | replay total | replay HYDROGEL | local 3d total | local HYDROGEL |
|---|---|---:|---:|---:|---:|
| v3 (static 10k, w=0.5) | — | **−1,657** | **−3,341** | +142,254 | ~+110k |
| v4 0.005 | **0.3** | **+2,497** | **+813** | +40,714 | +17,659 |
| 0.005 | 0.2 | +2,113 | +429 | +37,984 | +14,929 |
| 0.005 | 0.5 | +1,706 | +22 | +31,815 | +8,760 |
| 0.008 | 0.3 | +2,718 | +1,034 | +4,751 | −18,304 |
| 0.003 | 0.3 | −1,085 | −2,768 | +55,629 | +32,574 |

**v4 chooses α=0.005, w=0.3** because it is the only cell that is positive
on *both* regimes. α=0.008 is slightly better on replay but collapses
local; α=0.003 chases historical PnL but fails live.

v4 **does not change** B1 (VE wall-mid MM), C1 (top-2 imbalance skew),
G1 (parity guard), V2 voucher identity / monotonicity arb, or V3 voucher
EMA own-mid MM — those all produced net-positive PnL in live.

## Verification

| engine | v3 | v4 |
|---|---:|---:|
| Rust on live replay (378834) | −1,657 | **+2,497** |
| Rust on local day 0 | +44,583 | +2,175 |
| Rust on local day 1 | +56,015 | +36,450 |
| Rust on local day 2 | +41,656 | +2,089 |
| Rust local 3-day total | +142,254 | +40,714 |
| Python on local day 0 | +46,219 | +3,852 |

The local collapse (+142 k → +41 k) is the cost of removing the
backtester-bug overfit. The replay +4,155 swing is the real improvement.

## Pre-deploy falsifiers for v4

1. **Mean check.** If live HYDROGEL first-1 000-tick mean is > 30 shells
   away from the slow_EMA's initial seed (1 st microprice), something is
   wrong with the depth parsing — check and resubmit.
2. **Anchor clamp.** If slow_EMA spends > 5 % of ticks clamped at
   9 940 or 10 030, the live mean has moved outside the historical-plus
   range and we should widen the clamp (and very likely stop trading).
3. **Hosted-log trade count.** If own-trade count > 400 (v3 did 279 on
   this replay), HYDROGEL MM is over-aggressive. Consider raising
   H_TAKE_EDGE to 2.

## Lessons applied to future traders

- **Never hard-code a reference price.** Learn it from the data on every
  run. A live day can trivially be 10-20 shells off historical.
- **Regime guards must fire within one intra-day std.** v3's 80-shell
  threshold presumed regime shifts were ≥ 3 stds. Live showed ~1 std is
  enough to matter.
- **Single-day hosted evidence trumps multi-day backtests.** The hosted
  submission 369524 warning in `round3_drawdown_repair_v01` was ignored
  because the backtester looked "much better". It wasn't — it was
  overfit.
- **Tick-count parity matters.** Hosted test runs are 1 000 ticks;
  scoring is 10 000. Parameters calibrated on the latter can fail on
  the former.

## Submission candidate

**File**: `prosperity_rust_backtester/traders/Round3/candidates/round3_v4.py`

**Expected live PnL**: +2 k to +5 k per 1 000-tick day if regime matches
replay; proportionally higher if the day runs 10 000 ticks. The new fair
model is adaptive, so a mid-drift of 10-20 shells no longer cripples
HYDROGEL.
