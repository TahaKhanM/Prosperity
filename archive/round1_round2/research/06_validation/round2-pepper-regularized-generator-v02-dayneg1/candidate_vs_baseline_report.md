# Candidate Vs Baseline

## Inputs

- Candidate run: `prosperity_rust_backtester/runs/round2-pepper-regularized-generator-v02-dayneg1-day-1/candidate`
- Baseline run: `prosperity_rust_backtester/runs/round2-pepper-regularized-generator-v02-dayneg1-day-1/baseline`
- Same dataset signature: `True`

## Headline Deltas

- `total_pnl`: candidate `100144.0` vs baseline `102962.5` (delta `-2818.5`)
- `total_drawdown`: candidate `1455294.0` vs baseline `1455131.0` (delta `163.0`)
- `total_own_trades`: candidate `803` vs baseline `959` (delta `-156.0`)

## Product Outcome Deltas

- `ASH_COATED_OSMIUM.pnl` delta `0.0`
- `INTARIAN_PEPPER_ROOT.pnl` delta `-2818.5`

## Likely Cause Categories

- `inventory_control` delta_score `2.68`. Candidate: max_near_limit=0.971, avg_abs_position=78.2, drawdown=1455294.0. Baseline: max_near_limit=0.945, avg_abs_position=77.5, drawdown=1455131.0.
- `fair_value` delta_score `0.00`. Candidate: combined fill edge h5=11.230, total_pnl=100144.0. Baseline: combined fill edge h5=10.331, total_pnl=102962.5.
- `taking_thresholds` delta_score `0.00`. Candidate: aggressive_qty=1991, aggressive_edge_h5=1.073. Baseline: aggressive_qty=2205, aggressive_edge_h5=1.378.
- `passive_fill_quality` delta_score `0.00`. Candidate: passive_qty=2289, passive_edge_h5=20.065. Baseline: passive_qty=2820, passive_edge_h5=17.331.
- `state_path_handling` delta_score `0.00`. Candidate: missing_bundle_sets=0, set_count=1. Baseline: missing_bundle_sets=0, set_count=1.

## One Next Change

- Recommendation: Strengthen inventory skew or flattening at the product level.
- Metric to watch: Near-limit fraction and drawdown should fall before headline PnL is trusted.

## Guardrails

- This report is analysis-only. It does not imply a trader patch by itself.
- If the dataset signature differs, rerun the comparison on matching data before acting on the diagnosis.
