# Candidate Vs Baseline

## Inputs

- Candidate run: `prosperity_rust_backtester/runs/round2-pepper-opening-wide-gate-v01-day1-day1/candidate`
- Baseline run: `prosperity_rust_backtester/runs/round2-pepper-opening-wide-gate-v01-day1-day1/baseline`
- Same dataset signature: `True`

## Headline Deltas

- `total_pnl`: candidate `102956.0` vs baseline `104362.0` (delta `-1406.0`)
- `total_drawdown`: candidate `1723817.0` vs baseline `1723817.0` (delta `0.0`)
- `total_own_trades`: candidate `988` vs baseline `990` (delta `-2.0`)

## Product Outcome Deltas

- `ASH_COATED_OSMIUM.pnl` delta `0.0`
- `INTARIAN_PEPPER_ROOT.pnl` delta `-1406.0`

## Likely Cause Categories

- `inventory_control` delta_score `-3.98`. Candidate: max_near_limit=0.904, avg_abs_position=75.4, drawdown=1723817.0. Baseline: max_near_limit=0.942, avg_abs_position=77.3, drawdown=1723817.0.
- `taking_thresholds` delta_score `-0.51`. Candidate: aggressive_qty=2245, aggressive_edge_h5=-15.972. Baseline: aggressive_qty=2269, aggressive_edge_h5=-16.020.
- `passive_fill_quality` delta_score `0.28`. Candidate: passive_qty=2857, passive_edge_h5=-10.309. Baseline: passive_qty=2863, passive_edge_h5=-10.270.
- `fair_value` delta_score `-0.07`. Candidate: combined fill edge h5=-12.801, total_pnl=102956.0. Baseline: combined fill edge h5=-12.812, total_pnl=104362.0.
- `state_path_handling` delta_score `0.00`. Candidate: missing_bundle_sets=0, set_count=1. Baseline: missing_bundle_sets=0, set_count=1.

## One Next Change

- Recommendation: Strengthen inventory skew or flattening at the product level.
- Metric to watch: Near-limit fraction and drawdown should fall before headline PnL is trusted.

## Guardrails

- This report is analysis-only. It does not imply a trader patch by itself.
- If the dataset signature differs, rerun the comparison on matching data before acting on the diagnosis.
