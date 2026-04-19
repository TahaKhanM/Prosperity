# prosperity-research

This is the durable non-code workspace for Prosperity research, analysis, and
iteration support.

Keep active implementation in `prosperity_rust_backtester/`. Do not put trader
code here. `Trader1/` remains out of scope.

## Operating flow

`raw csvs -> assumptions -> analyzer / eda -> ai handoff artifacts -> signal hypotheses -> strategy spec -> implementation -> validation -> diagnosis -> experiment log`

1. Raw data authority
   - authoritative market CSVs live in `prosperity_rust_backtester/datasets/`
   - packaged Python reference data lives in
     `imc-prosperity-4-backtester/prosperity4bt/resources/`
   - raw CSVs are the source of truth
2. Assumptions
   - `prosperity-research/01_assumptions/`
3. Analyzer / EDA
   - Round 1 analyzer: `prosperity-research/03_eda/round1/`
   - other notebooks and figures: `prosperity-research/03_eda/`
4. AI handoff artifacts
   - `prosperity-research/03_eda/round1/ai_strategy_context/`
5. Signal notes
   - `prosperity-research/04_signal_notes/hypotheses/`
   - `prosperity-research/04_signal_notes/feature_rankings/`
6. Strategy specs and prompts
   - `prosperity-research/08_playbooks/strategy_templates/`
   - `prosperity-research/08_playbooks/runbooks/`
   - `prosperity-research/08_playbooks/prompt_library/`
7. Implementation
   - `prosperity_rust_backtester/`
8. Validation and diagnosis
   - `prosperity-research/06_validation/`
   - `prosperity-research/05_execution_risk/`
9. Experiment ledger
   - `prosperity-research/10_experiment_logs/`

Round 2 is the default local dataset context for the active backtester
workspace, but explicit dataset selection should still be used for controlled
comparisons.

## Repo policy reminders

- No separate normalization pipeline is part of the default workflow.
- Analyzer outputs are derived research artifacts, not canonical data.
- Compact diagnosis packets are preferred over dumping raw logs into AI tools.
- Existing loose historical notes directly under `01_assumptions/`, `03_eda/`,
  `04_signal_notes/`, `05_execution_risk/`, and `06_validation/` should remain
  in place.
- Use `prosperity-research/contracts.yaml` as the machine-readable contract for
  where each stage reads and writes artifacts.

## Ancillary routing

- `prosperity-research/00_inbox/`
  - untriaged material waiting to be routed
- `prosperity-research/07_manual_round/`
  - manual challenge outputs kept separate from algo-trading work
- `prosperity-research/09_master_reports/`
  - synthesized long-form reports
- `prosperity-research/10_experiment_logs/`
  - durable registry entries and dated working notes

## Naming defaults

- Narrative docs: `YYYY-MM-DD_<topic>.md`
- Notebooks: `YYYY-MM-DD_<topic>.ipynb`
- Figures: `YYYY-MM-DD_<topic>_<view>.png`
- Diagnosis packet folders: `YYYYMMDD_<run_label>/`
- Candidate vs baseline reports: `YYYY-MM-DD_<candidate>_vs_<baseline>/`
- Strategy specs: `<product_or_family>_strategy_spec.md`
