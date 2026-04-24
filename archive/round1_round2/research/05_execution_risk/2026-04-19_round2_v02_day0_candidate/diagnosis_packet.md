# Diagnosis Packet: prosperity_rust_backtester/runs/round2-v02-day0-day0/candidate

## Primary Read

- Most likely dominant issue: `inventory_control`
- Total PnL: `101911.00` with drawdown `1803930.00`
- Aggressive edge h5 average: `1.942`
- Passive edge h5 average: `7.455`

## Failure Mode Ranking

- `inventory_control`: max_near_limit=0.810, avg_abs_position=74.7, drawdown=1803930.0
- `fair_value`: combined fill edge h5=4.614, total_pnl=101911.0
- `taking_thresholds`: aggressive_qty=2778, aggressive_edge_h5=1.942
- `passive_fill_quality`: passive_qty=2613, passive_edge_h5=7.455
- `state_path_handling`: missing_bundle_sets=0, set_count=1

## Worst Timestamps

| Set | Timestamp | Delta total | Total |
| --- | --- | --- | --- |
| prices_round_2_day_0 | 967700 | -1037400.00 | -938929.00 |
| prices_round_2_day_0 | 773700 | -1022311.50 | -942963.00 |
| prices_round_2_day_0 | 576600 | -1005680.00 | -948356.00 |
| prices_round_2_day_0 | 506800 | -1000511.00 | -949079.00 |
| prices_round_2_day_0 | 793800 | -998219.00 | -916922.00 |

## Use This Packet For

- Implementation chats: focus on one dominant failure mode only.
- Diagnosis chats: use the headline metrics, inventory summary, fill summary, and worst timestamps.
- Validation chats: compare this packet against a baseline run on the same dataset.

## Local Limits

- Local run artifacts are derived evidence, not canonical market data.
- Conversion-heavy behavior may not be faithfully simulated locally; do not overclaim from conversion PnL.
- Missing bundle data weakens state and inventory diagnosis confidence.
