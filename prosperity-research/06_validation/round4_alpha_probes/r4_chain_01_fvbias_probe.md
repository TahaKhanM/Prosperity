# r4_chain_01_fvbias_probe (Phase 4 follow-up)

## Probe definition

- Based on: r4_baseline_v15.
- Each tick, in the VFE MM block:
  - Compute `D = sum_K Δ_BS(S, K, T, σ_K) * pos_K * 0.70` (sticky-strike-adjusted)
  - `vfe_fv_bias = -D / 4.0`, capped at ±1.0 tick
  - Add to local VFE fair: `fair = fs[VFE] + skew + vfe_fade + vfe_fv_bias`
- The bias is INLINE only (not persisted to fs[VFE] state).
- Pre-reg: `HEDGE_DELTA_MULT=0.70`, `VFE_BIAS_DIVISOR=4.0`, `BIAS_HARD_CAP=1.0`.

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Δ vs v15 |
|---|---|---|---|
| day-1 | 960 | +47,104.50 | −20,520.5 |
| day-2 | 976 | +91,303.00 | −16,275.0 |
| day-3 | 993 | +48,475.50 | +904.5 |
| total | 2,929 | **+186,883.00** | **−35,892** |

Per-product:
| product | baseline | probe | Δ |
|---|---:|---:|---:|
| HYDROGEL_PACK | 134,062 | 134,062 | 0 |
| VELVETFRUIT_EXTRACT | 20,419 | **−15,473** | **−35,892** |
| Vouchers | 68,294 | 68,294 | 0 |
| total | 222,775 | 186,883 | −35,892 |

## Verdict — REJECT

**Ship gate**: Δ ≥ +500 AND VFE trade count drops ≥ 5 % AND VFE PnL improves.

**Actual**:
- Δ = −35,892 (FAIL)
- VFE trade count: 1238 → 976 = −21 % (PASS the drop bound, but for the WRONG reason)
- VFE PnL: 20,419 → −15,473 (FAIL — got worse, not better)

## Root cause

V15 baseline naturally accumulates LARGE long voucher positions via:
- Accumulation block on V_4000/V_4500 (ACC_SIZE_PER_TICK=50, hits +100 to +150 per strike)
- Smile MM on V_5000-5500 (SMILE_QUOTE_SIZE=5, smaller but positive bias)

Net portfolio Δ = sum_K(Δ_K × pos_K × 0.70) is typically **+200 to +300**
every tick. With divisor=4 and cap=1, `vfe_fv_bias = -D/4` saturates at -1
tick almost constantly.

A constant -1 tick bias on VFE fair makes the MM:
- Post buys at `fair - 1` (= market_mid - 1 - skew) — usually NOT hit
- Post sells at `fair + 1` (= market_mid - 1 + skew) — hit too often

Net result: the MM accumulates SHORT VFE, gets adverse-selected on the
way back. Trade count drops because some quotes are too far from mid;
VFE PnL crashes because the MM is being run with a permanent wrong-side
bias.

## Lesson for next session

Locked params are wrong for the v15 baseline's inventory profile. To
salvage the alpha:

1. Add a **deadband**: `vfe_fv_bias = 0` when `|D| < 100`. Only fire when
   portfolio is meaningfully unbalanced (above natural MM inventory).
2. **Larger divisor** (e.g. 12-16) so the bias scales smoothly with D
   and rarely hits the hard cap.
3. Cap LOWER (e.g. 0.5 ticks) so a single tick doesn't overwhelm the
   existing skew.
4. Apply ONLY to TAKE thresholds, not to QUOTE prices (let the MM
   continue posting at the unbiased fair, but be more aggressive on
   takes when inventory is large).

The 0.7×Δ ratio is statistically valid (Phase 6 nulls confirmed holdout
PASS) but the IMPLEMENTATION at locked params is wrong. Not a parameter
sweep — needs a structural rethink.

## Falsifier (live)

Confirmed: do NOT ship as-is. Re-implement with deadband or skip.
