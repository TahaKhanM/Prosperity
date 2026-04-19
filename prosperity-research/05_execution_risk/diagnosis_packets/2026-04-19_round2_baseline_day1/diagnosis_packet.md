# Diagnosis Packet: prosperity_rust_backtester/runs/round2-baseline-day1-day1/candidate

## Primary Read

- Most likely dominant issue: `inventory_control`
- Total PnL: `104362.00` with drawdown `1723817.00`
- Aggressive edge h5 average: `-16.020`
- Passive edge h5 average: `-10.270`

## Failure Mode Ranking

- `inventory_control`: max_near_limit=0.942, avg_abs_position=77.3, drawdown=1723817.0
- `taking_thresholds`: aggressive_qty=2269, aggressive_edge_h5=-16.020
- `passive_fill_quality`: passive_qty=2863, passive_edge_h5=-10.270
- `fair_value`: combined fill edge h5=-12.812, total_pnl=104362.0
- `state_path_handling`: missing_bundle_sets=0, set_count=1

## Worst Timestamps

| Set | Timestamp | Delta total | Total |
| --- | --- | --- | --- |
| prices_round_2_day_1 | 679100 | -1094160.00 | -1024878.00 |
| prices_round_2_day_1 | 559900 | -1084800.00 | -1026850.00 |
| prices_round_2_day_1 | 553900 | -1083782.00 | -1027088.00 |
| prices_round_2_day_1 | 536500 | -1082920.00 | -1027349.00 |
| prices_round_2_day_1 | 524300 | -1081800.00 | -1027457.00 |

## Use This Packet For

- Implementation chats: focus on one dominant failure mode only.
- Diagnosis chats: use the headline metrics, inventory summary, fill summary, and worst timestamps.
- Validation chats: compare this packet against a baseline run on the same dataset.

## Local Limits

- Local run artifacts are derived evidence, not canonical market data.
- Conversion-heavy behavior may not be faithfully simulated locally; do not overclaim from conversion PnL.
- Missing bundle data weakens state and inventory diagnosis confidence.
