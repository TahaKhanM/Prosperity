# Candidate Vs Baseline

## Inputs

- Candidate run: `prosperity_rust_backtester/runs/round2-pepper-gap-state-guard-v01-day1-day1/candidate`
- Baseline run: `prosperity_rust_backtester/runs/round2-pepper-gap-state-guard-v01-day1-day1/baseline`
- Same dataset signature: `True`

## Headline Deltas

- `total_pnl`: candidate `104502.0` vs baseline `104362.0` (delta `140.0`)
- `total_drawdown`: candidate `1723581.0` vs baseline `1723817.0` (delta `-236.0`)
- `total_own_trades`: candidate `996` vs baseline `990` (delta `6.0`)

## Product Outcome Deltas

- `ASH_COATED_OSMIUM.pnl` delta `0.0`
- `INTARIAN_PEPPER_ROOT.pnl` delta `140.0`

## Likely Cause Categories

- `passive_fill_quality` delta_score `-1.01`. Candidate: passive_qty=2886, passive_edge_h5=-10.129. Baseline: passive_qty=2863, passive_edge_h5=-10.270.
- `fair_value` delta_score `-0.61`. Candidate: combined fill edge h5=-12.711, total_pnl=104502.0. Baseline: combined fill edge h5=-12.812, total_pnl=104362.0.
- `taking_thresholds` delta_score `-0.22`. Candidate: aggressive_qty=2272, aggressive_edge_h5=-15.991. Baseline: aggressive_qty=2269, aggressive_edge_h5=-16.020.
- `inventory_control` delta_score `0.10`. Candidate: max_near_limit=0.944, avg_abs_position=77.3, drawdown=1723581.0. Baseline: max_near_limit=0.942, avg_abs_position=77.3, drawdown=1723817.0.
- `state_path_handling` delta_score `0.00`. Candidate: missing_bundle_sets=0, set_count=1. Baseline: missing_bundle_sets=0, set_count=1.

## One Next Change

- Recommendation: Strengthen inventory skew or flattening at the product level.
- Metric to watch: Near-limit fraction and drawdown should fall before headline PnL is trusted.

## Guardrails

- This report is analysis-only. It does not imply a trader patch by itself.
- If the dataset signature differs, rerun the comparison on matching data before acting on the diagnosis.
