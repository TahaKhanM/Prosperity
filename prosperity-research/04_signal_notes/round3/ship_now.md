# Round 3 — ship-now alphas

Three alpha cards pass every rejection gate and are ready to be coded. One
fourth (G1) is a trivial defensive guard.

## Recommendation

Build one trader, `round3_v1`, that combines A1 + B1 + C1 behind three
feature flags in `traderData`. Keep G1 always-on but size-capped. Do **not**
include IV-scalping, deep-ITM overlay, or counterparty copy in the first
submission.

## A1 — HYDROGEL_PACK soft-anchor MM

**The one-sentence rule.**
> Treat HYDROGEL as a slowly-mean-reverting series around `fair = 9991`
> (not 10 000). Use an EMA-200 clamped to [9 980, 10 010]. Take anything
> ≤ fair − 1; quote ±4; skew quotes by 1 tick at |pos| > 80.

**Why.** `structural_quirks.md` §1 + `alpha_registry.md` card A1.
HYDROGEL is anchored but **not pinned**. Hardcoding 10 000 would ignore
the 9-shell downward bias in the empirical mean.

**Parameters.**
```
ANCHOR_MEAN     = 9991
ANCHOR_LO       = 9980
ANCHOR_HI       = 10010
EMA_HALF_LIFE   = 200   # ~ observed OU half-life
TAKE_EDGE       = 1
CLEAR_EDGE      = 0
QUOTE_EDGE      = 4
SOFT_POS_LIMIT  = 80
HARD_POS_LIMIT  = 200
ADVERSE_VOL_THR = 15
```

**Test plan in Rust backtester.**
- Backtest on each of day 0, 1, 2 in isolation. Expect positive PnL each
  day.
- Backtest on day 2 only with params tuned on day 0 (hold-out). Expect
  ≥ 60 % of day-0 PnL.
- Sanity: max drawdown in any 500-tick window < 1 k.

**Falsifier (live).** Average HYDROGEL mid in first 1 000 live ticks is
> 20 shells away from 9 991. Flip to `fair = market_mid`.

## B1 — VELVETFRUIT_EXTRACT wall-mid adaptive MM

**The one-sentence rule.**
> Fair = mid of the bid / ask levels with max volume ≥ 20 (within the top
> 3). Take at edge 1; quote ±3; skew on imbalance (card C1).

**Why.** Axis B regressed `Δmid_{t+1}` on `(wall_mid_t − top_mid_t)` and
got slope 0.77, t = 39, stable across 3 days. Wall-mid leads top-mid.

**Parameters.**
```
WALL_VOL_THR   = 20       # ignore thin resting levels
TAKE_EDGE      = 1
CLEAR_EDGE     = 1
QUOTE_EDGE     = 3
SOFT_POS_LIMIT = 80
AR1_BETA       = 0.0      # no AR(1) in first pass
```

Leave AR(1) disabled in v1. The regression slope says wall-mid *is* the
predictor; adding AR(1) doubles up on the same edge.

**Test plan.** Same as A1.

**Falsifier (live).** (wall_mid − top_mid) predictor slope < 0.15 over
2 000 live ticks → revert to top-of-book mid.

## C1 — Order-book imbalance skew (additive to A1 & B1)

**The one-sentence rule.**
> Let `imb = (Σbid_1+Σbid_2 − Σask_1−Σask_2) / (all volume)`. Skew `fair`
> by `k × imb` where `k ≈ 12` for HYDROGEL and `k ≈ 3` for VE. Cap the
> skew at ±2 ticks.

**Why.** Axis C, k=2, h=1: t = 35 on HYDROGEL, t = 20 on VE. Coefficient
is stable across 3 days. **Do not** use k = 3 — the sign flips (level 3
quotes are adversarial).

**Parameters.**
```
IMB_K         = 2                 # top-2 levels
HYDROGEL_SKEW = 12                # slope from axis C
VE_SKEW       = 3                 # slope from axis C
SKEW_CAP_TICK = 2                 # never move fair > 2 ticks
```

**Falsifier.** Live imbalance-vs-next-tick-return correlation falls below
0.15.

## G1 — Defensive parity guard

**The one-sentence rule.**
> If `best_ask(K) + 1 ≤ best_bid(S) − K`, buy up to 10 vouchers and short
> the same number of VE contracts. Never the reverse direction (cap
> violations are 0 historically, and false positives on cap are costly).

**Why.** Identity-only — can never be negative-EV. Cheap feature-flag
guard.

**Parameters.**
```
PARITY_MIN_EDGE = 1      # seashells
PARITY_SIZE_CAP = 10     # contracts
```

**Expected PnL.** < 100 / day historical; could be higher live if an
opposing bot posts crossed quotes.

## Integration

Propose a single `Trader` class with:

```python
FLAGS = {
    "mm_hydrogel":   True,
    "mm_ve":         True,
    "imbalance_skew": True,
    "parity_guard":  True,
    "iv_scalp":      False,     # card D1
    "deep_itm":      False,     # card E1
    "counterparty":  False,     # card F1
}
```

Everything behind a flag so individual blocks can be toggled without
re-deploying.

## Success criterion (self-set)

On the Round 3 Rust backtester across day 0 + day 1 + day 2:
- Cumulative PnL ≥ 30 000 seashells.
- No single day < 5 000.
- Max drawdown in any 500-tick window ≤ 2 000.

If all three pass, submit as `round3_v1`. Else halt and investigate which
card regressed.

## Intentionally NOT in v1

- **D1 IV residual scalp.** Signal exists but residual σ × vega is too
  small vs spread; backtester fill-model over-reports. Revisit only after
  D1 fill model tightened.
- **E1 deep-ITM overlay.** Structurally valid (zero time value → synthetic
  delta-1), but end-of-round liquidation semantics in the Rust backtester
  must be verified against hosted before we commit capital to a held
  position that settles at expiry.
- **F1 counterparty copy.** No historical counterparty name. Behind a
  live-discovery feature flag only.
