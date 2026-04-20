# scripts/diagnostics

Purpose: turn persisted local backtest artifacts into compact, model-friendly
diagnosis and comparison outputs.

Inputs:
- `prosperity_rust_backtester/runs/<run_label>/`
- `metrics.json`, `bundle.json`, `submission.log`, `combined.log`,
  `activity.csv`, `pnl_by_product.csv`, `trades.csv` when present

Outputs:
- diagnosis packets under `prosperity-research/05_execution_risk/diagnosis_packets/`
- baseline summaries under `prosperity-research/06_validation/baselines/`
- candidate-vs-baseline reports under
  `prosperity-research/06_validation/candidate_vs_baseline/`

Notes:
- these scripts consume derived run artifacts; they do not create a second data
  pipeline
- use explicit run folders from `scripts/run_harness.py` where possible
