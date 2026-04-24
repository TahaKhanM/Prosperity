# Candidate Vs Baseline

## Inputs

- Candidate run: `prosperity_rust_backtester/runs/round2-v02-day0-day0/candidate`
- Baseline run: `prosperity_rust_backtester/runs/round2-v02-day0-day0/baseline`
- Same dataset signature: `True`

## Headline Deltas

- `total_pnl`: candidate `101911.0` vs baseline `102777.0` (delta `-866.0`)
- `total_drawdown`: candidate `1803930.0` vs baseline `1803898.0` (delta `32.0`)
- `total_own_trades`: candidate `1052` vs baseline `912` (delta `140.0`)

## Product Outcome Deltas

- `ASH_COATED_OSMIUM.pnl` delta `0.0`
- `INTARIAN_PEPPER_ROOT.pnl` delta `-866.0`

## Likely Cause Categories

- `inventory_control` delta_score `-13.81`. Candidate: max_near_limit=0.810, avg_abs_position=74.7, drawdown=1803930.0. Baseline: max_near_limit=0.946, avg_abs_position=77.4, drawdown=1803898.0.
- `fair_value` delta_score `0.00`. Candidate: combined fill edge h5=4.614, total_pnl=101911.0. Baseline: combined fill edge h5=4.812, total_pnl=102777.0.
- `taking_thresholds` delta_score `0.00`. Candidate: aggressive_qty=2778, aggressive_edge_h5=1.942. Baseline: aggressive_qty=1940, aggressive_edge_h5=1.369.
- `passive_fill_quality` delta_score `0.00`. Candidate: passive_qty=2613, passive_edge_h5=7.455. Baseline: passive_qty=2745, passive_edge_h5=7.245.
- `state_path_handling` delta_score `0.00`. Candidate: missing_bundle_sets=0, set_count=1. Baseline: missing_bundle_sets=0, set_count=1.

## One Next Change

- Recommendation: Strengthen inventory skew or flattening at the product level.
- Metric to watch: Near-limit fraction and drawdown should fall before headline PnL is trusted.

## Guardrails

- This report is analysis-only. It does not imply a trader patch by itself.
- If the dataset signature differs, rerun the comparison on matching data before acting on the diagnosis.
