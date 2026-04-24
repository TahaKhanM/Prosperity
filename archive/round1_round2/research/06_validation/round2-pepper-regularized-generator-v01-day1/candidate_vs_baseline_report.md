# Candidate Vs Baseline

## Inputs

- Candidate run: `prosperity_rust_backtester/runs/round2-pepper-regularized-generator-v01-day1-day1/candidate`
- Baseline run: `prosperity_rust_backtester/runs/round2-pepper-regularized-generator-v01-day1-day1/baseline`
- Same dataset signature: `True`

## Headline Deltas

- `total_pnl`: candidate `101735.0` vs baseline `104362.0` (delta `-2627.0`)
- `total_drawdown`: candidate `1724885.5` vs baseline `1723817.0` (delta `1068.5`)
- `total_own_trades`: candidate `860` vs baseline `990` (delta `-130.0`)

## Product Outcome Deltas

- `ASH_COATED_OSMIUM.pnl` delta `0.0`
- `INTARIAN_PEPPER_ROOT.pnl` delta `-2627.0`

## Likely Cause Categories

- `passive_fill_quality` delta_score `22.71`. Candidate: passive_qty=2405, passive_edge_h5=-13.395. Baseline: passive_qty=2863, passive_edge_h5=-10.270.
- `fair_value` delta_score `15.11`. Candidate: combined fill edge h5=-15.331, total_pnl=101735.0. Baseline: combined fill edge h5=-12.812, total_pnl=104362.0.
- `taking_thresholds` delta_score `11.33`. Candidate: aggressive_qty=2111, aggressive_edge_h5=-17.536. Baseline: aggressive_qty=2269, aggressive_edge_h5=-16.020.
- `inventory_control` delta_score `2.46`. Candidate: max_near_limit=0.965, avg_abs_position=78.2, drawdown=1724885.5. Baseline: max_near_limit=0.942, avg_abs_position=77.3, drawdown=1723817.0.
- `state_path_handling` delta_score `0.00`. Candidate: missing_bundle_sets=0, set_count=1. Baseline: missing_bundle_sets=0, set_count=1.

## One Next Change

- Recommendation: Reshade passive quotes by state and inventory rather than widening everything.
- Metric to watch: Passive `edge_h5_avg` should improve without collapsing passive quantity.

## Guardrails

- This report is analysis-only. It does not imply a trader patch by itself.
- If the dataset signature differs, rerun the comparison on matching data before acting on the diagnosis.
