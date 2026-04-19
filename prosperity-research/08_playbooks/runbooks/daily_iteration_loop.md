# Daily Iteration Loop

Use this loop for the repo's normal research and implementation cycle.

1. Run or refresh the analyzer outputs in `prosperity-research/03_eda/round1/`.
2. Review `strategy_brief.md`, `product_params.json`, and only the plots needed
   for the current question.
3. Write or update one hypothesis note in
   `prosperity-research/04_signal_notes/hypotheses/`.
4. Generate or patch one trader candidate in the active Rust workspace.
5. Run explicit local validation with an explicit trader path and explicit
   dataset. Round 2 is the default local dataset context, but keep dataset
   selection explicit in tooling and notes.
6. Extract a compact diagnosis packet from the run artifacts.
7. Compare the candidate against one baseline on the same dataset.
8. Update the experiment registry.
9. Either ship or reject the iteration.
10. Keep one dominant change per iteration.

Repo policy reminders:
- raw CSVs in dataset/resource folders are the source of truth
- the analyzer is the first-pass analysis layer
- there is no separate normalization pipeline
- compact diagnostics are preferred over dumping raw logs into AI tools
- local backtest artifacts are diagnostic evidence, not official truth
