# Diagnosis Packet: prosperity_rust_backtester/runs/round2-v02-day1-day1/candidate

## Primary Read

- Most likely dominant issue: `inventory_control`
- Total PnL: `102858.00` with drawdown `1724749.50`
- Aggressive edge h5 average: `-10.877`
- Passive edge h5 average: `-11.304`

## Failure Mode Ranking

- `inventory_control`: max_near_limit=0.794, avg_abs_position=73.7, drawdown=1724749.5
- `passive_fill_quality`: passive_qty=2693, passive_edge_h5=-11.304
- `taking_thresholds`: aggressive_qty=3073, aggressive_edge_h5=-10.877
- `fair_value`: combined fill edge h5=-11.077, total_pnl=102858.0
- `state_path_handling`: missing_bundle_sets=0, set_count=1

## Worst Timestamps

| Set | Timestamp | Delta total | Total |
| --- | --- | --- | --- |
| prices_round_2_day_1 | 679100 | -1094160.00 | -1026246.00 |
| prices_round_2_day_1 | 553900 | -1083782.00 | -1028317.00 |
| prices_round_2_day_1 | 524300 | -1081800.00 | -1028661.00 |
| prices_round_2_day_1 | 483100 | -1078629.50 | -1029727.50 |
| prices_round_2_day_1 | 415300 | -1033207.00 | -991637.00 |

## Use This Packet For

- Implementation chats: focus on one dominant failure mode only.
- Diagnosis chats: use the headline metrics, inventory summary, fill summary, and worst timestamps.
- Validation chats: compare this packet against a baseline run on the same dataset.

## Local Limits

- Local run artifacts are derived evidence, not canonical market data.
- Conversion-heavy behavior may not be faithfully simulated locally; do not overclaim from conversion PnL.
- Missing bundle data weakens state and inventory diagnosis confidence.
