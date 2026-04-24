# Round 3 Maximal Algorithmic Sprint — 2026-04-24

Fresh, isolated workspace. Algorithmic-only.

## Artifacts

- `01_current_assumptions.md` — locked facts, unknowns, BLOCKERS.
- `02_data_inventory.md` — what datasets actually exist on disk.
- `03_product_classification.md` — best-effort classification from the briefing.
- `04_voucher_analysis.md` — parity ladder, intrinsic/time-value framework.
- `05_alpha_cards.md` — falsifiable hypotheses + rejections.
- `06_implementation_plan.md` — plan for baseline + serious candidate.
- `07_dry_run_results.md` — Round 2 structural validation (interface correctness only).
- `08_audit_verdict.md` — SHIP / FLAG / REJECT with reasons.

## Trader files

- `prosperity_rust_backtester/traders/Round3/candidates/round3_no_trade_baseline_v01.py`
- `prosperity_rust_backtester/traders/Round3/candidates/round3_maximal_multi_product_v01.py`

## Context

This sprint is the first serious Round 3 algorithmic build in this repo. At sprint
start, there is no Round 3 `current_best.md`, no Round 3 datasets on disk, and
the uploaded Prosperity Context pack explicitly does not cover rounds beyond 2.
See `01_current_assumptions.md` for the full blocker analysis.
