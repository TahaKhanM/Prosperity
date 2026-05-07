# r4_adaptive_bias_ema_probe — REJECT

## Probe definition

Single delta on top of composite v01: replace v15's static
`SMILE_PER_STRIKE_BIAS` dict with a per-strike EMA of the residual
`iv_market_K - (a0 + a1·m + a2·m²)`. Smile fit preserved.

Pre-registered (locked): HL=100 ticks, ALPHA≈0.00693, seed = v15 dict,
clamp = ±0.10 IV-vol points.

## Backtest result (3-day BT, datasets/round4)

| set | day | own_trades | pnl | Δ vs composite v01 (+228,510.50) |
|---|---|---|---|---:|
| day-1 | 1 | 1173 | 66,766.50 | -2,219.0 |
| day-2 | 2 | 1177 | 89,212.00 | **-20,813.5** |
| day-3 | 3 | 1165 | 56,213.50 | +6,714.0 |
| total | | 3,515 | **212,192.00** | **−16,318.5** |

## Per-product Δ vs floor (3-day)

- HYD: 134,581 → 134,581 (Δ 0; expected — disjoint code path)
- VFE: 22,979 → 22,979 (Δ 0)
- V_5100: 12,078.5 → 4,454 (Δ -7,624)
- OTHER (V_5000 + V_5300..6500): 19,831.5 → 9,775 (Δ -10,056)

Voucher complex is bleeding. The per-strike EMA is drifting away from the
v15 static seed under R4 dynamics, and the resulting smile shifts are
worse for PnL than the static seeds (which were calibrated for PnL, not
residual fitting).

## Diagnosis

Same failure mode as the prior `r4_phase5_g1_probe` (Phase 1 of follow-up):
day-2 catastrophic regression at the TTE 7→6 transition. The EMA's HL=100
tick window fails to track the regime change in voucher pricing across
TTE buckets. v15's static dict was tuned to a specific (TTE-distribution,
microstructure) joint that v15 sees in the BT; an empirical residual
tracker drifts away from those PnL-optimal values.

Lesson reaffirmed: the static `SMILE_PER_STRIKE_BIAS` dict is calibrated
for PnL, not for residual mean. Replacing it with a residual tracker
breaks the calibration.

## Ship gate outcome

- 3-day Δ vs baseline ≥ +1,000: **FAIL (-16,318)**.
- Day-3 Δ ≥ +500: pass alone (+6,714) but fails the AND.

## Verdict — REJECT

Permanent retire. The G1 family of alphas (per-strike rolling IV) does not
work either as a smile-fit replacement (prior G1 attempt) or as an
adaptive bias on top of the smile fit (this attempt).
