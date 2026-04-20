# Diagnosis Packet: prosperity_rust_backtester/runs/round2-baseline-day0-day0/candidate

## Primary Read

- Most likely dominant issue: `inventory_control`
- Total PnL: `102777.00` with drawdown `1803898.00`
- Aggressive edge h5 average: `1.369`
- Passive edge h5 average: `7.245`

## Failure Mode Ranking

- `inventory_control`: max_near_limit=0.946, avg_abs_position=77.4, drawdown=1803898.0
- `fair_value`: combined fill edge h5=4.812, total_pnl=102777.0
- `taking_thresholds`: aggressive_qty=1940, aggressive_edge_h5=1.369
- `passive_fill_quality`: passive_qty=2745, passive_edge_h5=7.245
- `state_path_handling`: missing_bundle_sets=0, set_count=1

## Worst Timestamps

| Set | Timestamp | Delta total | Total |
| --- | --- | --- | --- |
| prices_round_2_day_0 | 984800 | -1038800.00 | -937571.00 |
| prices_round_2_day_0 | 967700 | -1037400.00 | -938000.00 |
| prices_round_2_day_0 | 931300 | -1034286.00 | -937970.00 |
| prices_round_2_day_0 | 793800 | -1023807.00 | -941502.00 |
| prices_round_2_day_0 | 773700 | -1022311.50 | -941818.00 |

## Use This Packet For

- Implementation chats: focus on one dominant failure mode only.
- Diagnosis chats: use the headline metrics, inventory summary, fill summary, and worst timestamps.
- Validation chats: compare this packet against a baseline run on the same dataset.

## Local Limits

- Local run artifacts are derived evidence, not canonical market data.
- Conversion-heavy behavior may not be faithfully simulated locally; do not overclaim from conversion PnL.
- Missing bundle data weakens state and inventory diagnosis confidence.
