# Candidate Vs Baseline

## Inputs

- Candidate run: `prosperity_rust_backtester/runs/round2-v01-day1-day1/candidate`
- Baseline run: `prosperity_rust_backtester/runs/round2-v01-day1-day1/baseline`
- Same dataset signature: `True`

## Headline Deltas

- `total_pnl`: candidate `101452.0` vs baseline `104362.0` (delta `-2910.0`)
- `total_drawdown`: candidate `1724646.5` vs baseline `1723817.0` (delta `829.5`)
- `total_own_trades`: candidate `1220` vs baseline `990` (delta `230.0`)

## Product Outcome Deltas

- `ASH_COATED_OSMIUM.pnl` delta `0.0`
- `INTARIAN_PEPPER_ROOT.pnl` delta `-2910.0`

## Likely Cause Categories

- `taking_thresholds` delta_score `-45.16`. Candidate: aggressive_qty=3286, aggressive_edge_h5=-9.739. Baseline: aggressive_qty=2269, aggressive_edge_h5=-16.020.
- `inventory_control` delta_score `-44.37`. Candidate: max_near_limit=0.507, avg_abs_position=68.3, drawdown=1724646.5. Baseline: max_near_limit=0.942, avg_abs_position=77.3, drawdown=1723817.0.
- `fair_value` delta_score `-20.54`. Candidate: combined fill edge h5=-9.390, total_pnl=101452.0. Baseline: combined fill edge h5=-12.812, total_pnl=104362.0.
- `passive_fill_quality` delta_score `-8.88`. Candidate: passive_qty=3090, passive_edge_h5=-9.017. Baseline: passive_qty=2863, passive_edge_h5=-10.270.
- `state_path_handling` delta_score `0.00`. Candidate: missing_bundle_sets=0, set_count=1. Baseline: missing_bundle_sets=0, set_count=1.

## One Next Change

- Recommendation: Strengthen inventory skew or flattening at the product level.
- Metric to watch: Near-limit fraction and drawdown should fall before headline PnL is trusted.

## Guardrails

- This report is analysis-only. It does not imply a trader patch by itself.
- If the dataset signature differs, rerun the comparison on matching data before acting on the diagnosis.
