# Diagnosis Packet: prosperity_rust_backtester/runs/round2-v02-dayneg1-day-1/candidate

## Primary Read

- Most likely dominant issue: `inventory_control`
- Total PnL: `101328.50` with drawdown `1455166.00`
- Aggressive edge h5 average: `1.562`
- Passive edge h5 average: `19.087`

## Failure Mode Ranking

- `inventory_control`: max_near_limit=0.889, avg_abs_position=75.8, drawdown=1455166.0
- `fair_value`: combined fill edge h5=9.630, total_pnl=101328.5
- `taking_thresholds`: aggressive_qty=2893, aggressive_edge_h5=1.562
- `passive_fill_quality`: passive_qty=2468, passive_edge_h5=19.087
- `state_path_handling`: missing_bundle_sets=0, set_count=1

## Worst Timestamps

| Set | Timestamp | Delta total | Total |
| --- | --- | --- | --- |
| prices_round_2_day_-1 | 792000 | -943360.00 | -863189.00 |
| prices_round_2_day_-1 | 424000 | -913910.00 | -872106.00 |
| prices_round_2_day_-1 | 398200 | -911824.00 | -872581.00 |
| prices_round_2_day_-1 | 322400 | -905759.00 | -874269.50 |
| prices_round_2_day_-1 | 309600 | -904840.00 | -874504.00 |

## Use This Packet For

- Implementation chats: focus on one dominant failure mode only.
- Diagnosis chats: use the headline metrics, inventory summary, fill summary, and worst timestamps.
- Validation chats: compare this packet against a baseline run on the same dataset.

## Local Limits

- Local run artifacts are derived evidence, not canonical market data.
- Conversion-heavy behavior may not be faithfully simulated locally; do not overclaim from conversion PnL.
- Missing bundle data weakens state and inventory diagnosis confidence.
