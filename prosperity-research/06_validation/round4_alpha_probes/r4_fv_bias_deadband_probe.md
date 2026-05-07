# r4_fv_bias_deadband_probe — REJECT

## Probe definition

R4-CHAIN-01-V2 (corrected with deadband + larger divisor). Each tick,
compute portfolio voucher delta D using prior tick's smile state; if
|D|≥100, set VFE fair-value bias = -D/8 clipped to ±1 tick.

Pre-registered: FV_BIAS_DELTA_RATIO=0.70, DEADBAND=100, DIVISOR=8.0,
HARD_CAP=1.0. No tuning.

## Backtest result (3-day BT, datasets/round4)

| set | day | own_trades | pnl | Δ vs composite v01 (+228,510.50) |
|---|---|---|---|---:|
| day-1 | 1 | 1001 | 47,506.50 | **-21,479.0** |
| day-2 | 2 | 1024 | 95,562.50 | -14,463.0 |
| day-3 | 3 | 1038 | 47,986.50 | -1,513.0 |
| total | | 3,063 | **191,055.50** | **−37,455.0** |

Trade count dropped 717 across 3 days (~22%). VFE quoting is being
suppressed dramatically.

## Diagnosis

Even with the deadband and divisor=8, the bias hits ±1 cap on most ticks.
Reason: v15's natural deep-ITM voucher accumulation puts position[VEV_4000]
and position[VEV_4500] near 100-200 each on long stretches. Δ_BS≈1 for
deep-ITM, so D = 0.7 × 1 × (200+200) = ~280. After divisor=8, raw bias =
-35 ticks → clipped to ±1.

Once the bias saturates at ±1, the VFE MM is biased a constant -1 tick.
This systematically:
- Lowers VFE fair, suppressing buy-side quoting
- Reduces VFE trade count → -22% trades
- Loses the natural VFE PnL contribution (-21k on day-1 alone)

The follow-up summary's prediction stood: "any constant-direction
adjustment to VFE quotes overwhelms the existing MM" remains true even
with deadband + larger divisor at the pre-registered values.

## Ship gate outcome

- 3-day Δ vs baseline ≥ +500: **FAIL (-37,455)**.
- VFE own_trades drops by ≥5%: actually drops 22% (excessive).
- No single-day Δ < -500: FAIL (-21,479 / -14,463 / -1,513).

Falsifier "VFE own_trades INCREASES by >10%" did not trip — but the
strategy still failed because the bias is correctly-signed but
magnitudes-too-large for the existing MM to absorb. The MM is being
shut off, not absorbing the rebalance.

## Verdict — REJECT

The fair-value-bias hedge family is permanently retired. To work, this
would need divisor in the range 30-100 (giving bias magnitudes of
0.3-1.0 ticks even under accumulated deep-ITM positions of ~200 units).
That's outside the pre-registered range; would require a separate
research cycle to justify.
