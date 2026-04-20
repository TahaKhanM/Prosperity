# scripts

This directory contains both older one-off research helpers and the newer
durable workflow scripts that support the repo's research -> implementation ->
validation loop.

Primary workflow scripts:
- `run_harness.py`
  - run an explicit trader on an explicit dataset and write a stable
    `runs/<run_label>/run_manifest.json`
- `generate_strategy_scaffold.py`
  - generate a new submission-compatible candidate scaffold under
    `traders/<Round>/candidates/`
- `diagnostics/extract_diagnosis_packet.py`
  - turn one persisted run into a compact diagnosis packet
- `diagnostics/candidate_vs_baseline_report.py`
  - compare two runs on the same dataset and recommend one next change
- `reports/update_experiment_registry.py`
  - update the durable experiment ledger in `prosperity-research/10_experiment_logs/`
- `manual_round/round1_auction_solver.py`
  - evaluate final-order grids for the Round 1 manual auction
- `manual_round/round2_budget_allocator.py`
  - evaluate Research / Scale / Speed allocations for the Round 2 manual game

These scripts wrap the existing backtester and dataset layout. They do not
introduce a second data pipeline and they do not change trader logic by
themselves.
