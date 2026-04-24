# Current best — Round 3

Updated: 2026-04-24

## Active champion

- File: `prosperity_rust_backtester/traders/Round3/candidates/round3_maximal_data_driven_v01.py`
- Dataset: `datasets/round3/` (day_0, day_1, day_2).
- Total PnL across 3 days: **+36,062 XY**

## Three-day PnL breakdown

| day | PnL | trades |
|---|---:|---:|
| day_0 | 8,415.00 | 490 |
| day_1 | 13,586.50 | 492 |
| day_2 | 14,060.50 | 492 |
| **total** | **36,062.00** | **1,474** |

## Per-product contribution (3-day sum)

| product | pnl |
|---|---:|
| HYDROGEL_PACK | 23,801 |
| VELVETFRUIT_EXTRACT | 5,270 |
| VEV_4000 | 3,670 |
| VEV_4500 | 1,788 |
| VEV_5200 | 752 |
| VEV_5300 | 535 |
| VEV_5000 | 156 |
| VEV_5400 | 90 |

## Verdict: PROVISIONAL SHIP

Reason: submission-compatible, positive on every day, diversified across four
product categories, and clearly dominant over no-trade (0) and the prior
candidate `round3_actual_strategy_v02.py` (+26,022).

## Promote / replace

Only replace this file after a new candidate has:
- a strictly higher 3-day round3 total, AND
- no losing day, AND
- no single product contributing >90% of the gain, AND
- a clean audit against the backtest-auditor skill.

## Commands to reproduce

```
cd prosperity_rust_backtester
make round3 TRADER=traders/Round3/candidates/round3_maximal_data_driven_v01.py PRODUCTS=full
```
