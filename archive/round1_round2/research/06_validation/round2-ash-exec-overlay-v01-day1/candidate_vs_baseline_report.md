# Candidate Vs Baseline

## Inputs

- Candidate run: `prosperity_rust_backtester/runs/round2-ash-exec-overlay-v01-day1-day1/candidate`
- Baseline run: `prosperity_rust_backtester/runs/round2-ash-exec-overlay-v01-day1-day1/baseline`
- Same dataset signature: `True`

## Headline Deltas

- `total_pnl`: candidate `104155.0` vs baseline `104362.0` (delta `-207.0`)
- `total_drawdown`: candidate `1723830.0` vs baseline `1723817.0` (delta `13.0`)
- `total_own_trades`: candidate `957` vs baseline `990` (delta `-33.0`)

## Product Outcome Deltas

- `ASH_COATED_OSMIUM.pnl` delta `-207.0`
- `INTARIAN_PEPPER_ROOT.pnl` delta `0.0`

## Likely Cause Categories

- `taking_thresholds` delta_score `4.36`. Candidate: aggressive_qty=2171, aggressive_edge_h5=-16.626. Baseline: aggressive_qty=2269, aggressive_edge_h5=-16.020.
- `fair_value` delta_score `1.12`. Candidate: combined fill edge h5=-12.999, total_pnl=104155.0. Baseline: combined fill edge h5=-12.812, total_pnl=104362.0.
- `passive_fill_quality` delta_score `-0.13`. Candidate: passive_qty=2866, passive_edge_h5=-10.251. Baseline: passive_qty=2863, passive_edge_h5=-10.270.
- `inventory_control` delta_score `0.00`. Candidate: max_near_limit=0.942, avg_abs_position=77.3, drawdown=1723830.0. Baseline: max_near_limit=0.942, avg_abs_position=77.3, drawdown=1723817.0.
- `state_path_handling` delta_score `0.00`. Candidate: missing_bundle_sets=0, set_count=1. Baseline: missing_bundle_sets=0, set_count=1.

## One Next Change

- Recommendation: Tighten aggressive taking thresholds before touching passive quoting.
- Metric to watch: Aggressive `edge_h5_avg` should improve with flat or lower aggressive quantity.

## Guardrails

- This report is analysis-only. It does not imply a trader patch by itself.
- If the dataset signature differs, rerun the comparison on matching data before acting on the diagnosis.
