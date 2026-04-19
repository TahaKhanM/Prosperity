# scripts/reports

Purpose: maintain durable experiment tracking outside chat history.

Inputs:
- `prosperity_rust_backtester/runs/<run_label>/run_manifest.json`
- candidate run summaries
- operator-supplied hypothesis tags, strategy-family tags, and ship/reject
  status

Outputs:
- `prosperity-research/10_experiment_logs/experiment_registry.csv`
- `prosperity-research/10_experiment_logs/latest_experiment_summary.md`

Notes:
- the registry is an experiment ledger, not a source of raw market truth
- update it after each explicit candidate run or candidate-vs-baseline decision
