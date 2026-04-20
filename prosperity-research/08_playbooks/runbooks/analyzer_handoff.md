# Analyzer Handoff

Use the analyzer outputs in `prosperity-research/03_eda/round1/` as the compact
handoff layer between raw data and implementation work.

Preferred inputs:
- `ai_strategy_context/strategy_brief.md`
- `ai_strategy_context/product_params.json`
- a small curated set of plots
- optional sample tables if the notebook exported them

For alpha discovery chats:
1. Start with `strategy_brief.md`.
2. Add `product_params.json`.
3. Attach only the plots needed to confirm one suspected pattern.
4. Ask for one hypothesis at a time.

For implementation chats:
1. Provide the hypothesis note from `04_signal_notes/hypotheses/`.
2. Provide `strategy_brief.md` and `product_params.json`.
3. State the target trader path and explicit dataset.
4. Ask for one narrow patch.

For diagnosis chats:
1. Provide the diagnosis packet first.
2. Add `strategy_brief.md` only if the failure mode depends on market context.
3. Prefer compact packet files over raw logs unless a specific timestamp must be
   audited.

Do not treat analyzer outputs as canonical data. Raw CSVs in dataset folders
remain authoritative.
