# Diagnosis Packet: prosperity_rust_backtester/runs/round2-baseline-dayneg1-day-1/candidate

## Primary Read

- Most likely dominant issue: `inventory_control`
- Total PnL: `102962.50` with drawdown `1455131.00`
- Aggressive edge h5 average: `1.378`
- Passive edge h5 average: `17.331`

## Failure Mode Ranking

- `inventory_control`: max_near_limit=0.945, avg_abs_position=77.5, drawdown=1455131.0
- `fair_value`: combined fill edge h5=10.331, total_pnl=102962.5
- `taking_thresholds`: aggressive_qty=2205, aggressive_edge_h5=1.378
- `passive_fill_quality`: passive_qty=2820, passive_edge_h5=17.331
- `state_path_handling`: missing_bundle_sets=0, set_count=1

## Worst Timestamps

| Set | Timestamp | Delta total | Total |
| --- | --- | --- | --- |
| prices_round_2_day_-1 | 792000 | -943360.00 | -861651.00 |
| prices_round_2_day_-1 | 696800 | -935520.00 | -864812.00 |
| prices_round_2_day_-1 | 398200 | -911824.00 | -871330.00 |
| prices_round_2_day_-1 | 309600 | -904840.00 | -873380.00 |
| prices_round_2_day_-1 | 199100 | -896848.00 | -875712.00 |

## Use This Packet For

- Implementation chats: focus on one dominant failure mode only.
- Diagnosis chats: use the headline metrics, inventory summary, fill summary, and worst timestamps.
- Validation chats: compare this packet against a baseline run on the same dataset.

## Local Limits

- Local run artifacts are derived evidence, not canonical market data.
- Conversion-heavy behavior may not be faithfully simulated locally; do not overclaim from conversion PnL.
- Missing bundle data weakens state and inventory diagnosis confidence.
