# Round 2 Analyzer Audit

Date: 2026-04-19

Scope: audit the existing analyzer for Round 2 readiness, rerun it on the
canonical Round 2 dataset, and record any minimal changes made for carryover
work.

## Canonical Run Surface

Analyzer entrypoint from the repo README:

```bash
python analysis.py --round round2
```

Repo reality in this shell:

- bare `python` failed because the active interpreter lacked `numpy`
- the declared repo environment exists as the Conda env `prosperity`

Working repo-backed command used:

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1
conda run -n prosperity python analysis.py --round round2
```

Matched carryover run:

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1
conda run -n prosperity python analysis.py --round round1
```

## What The Existing Analyzer Already Covered Well

The existing analyzer was already materially Round-2-ready. It successfully
produced:

- product classification,
- fair-proxy ranking,
- spread calibration,
- mean-reversion diagnostics,
- multi-horizon signal ranking,
- spike studies,
- microstructure features,
- conditional bucket returns,
- regime segmentation,
- execution markouts,
- within-round cross-day robustness,
- half-life estimates,
- feature relevance,
- curated AI-facing exports.

For core Round 2 alpha search, no redesign was needed.

## Round 2 Run Result

Round 2 rerun completed successfully on the canonical local raw dataset:

- data source:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets/round2`
- plots:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1/plots/round2/`
- live curated export:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1/ai_strategy_context/`

Round 2 high-level outcome from the rerun:

- `ASH_COATED_OSMIUM`: stable, anchored, strong mean reversion, wall-mid best
  fair, spike reversion confirmed.
- `INTARIAN_PEPPER_ROOT`: drifting, strong dynamic-fair reversion, mm-mid best
  fair, strong take markouts and materially cleaner monetization than Round 1.

## Real Gap Found

The analyzer had one practical carryover gap:

- the curated export lived only in the shared `ai_strategy_context/` directory
- each rerun overwrote the previous round's export
- that made systematic Round 1 vs Round 2 comparison fragile and order-dependent

This was a real workflow problem for the requested carryover analysis, even
though the analytical sections themselves were already strong enough.

## Minimal Changes Made

Minimal change to the analyzer:

- `analysis.py` now mirrors the curated export to
  `ai_strategy_context_by_round/<round>/`
- existing live `ai_strategy_context/` behavior remains unchanged
- README was updated to document the new snapshot behavior

Changed files:

- [analysis.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1/analysis.py)
- [README.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1/README.md)

New snapshot outputs now available:

- Round 1:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1/ai_strategy_context_by_round/round1/`
- Round 2:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1/ai_strategy_context_by_round/round2/`

## Sufficiency Verdict

### Sufficient for Round 2 alpha mining

Yes.

The analyzer is sufficient for:

- product classification,
- fair-value search,
- primary signal ranking,
- spike and regime inspection,
- execution-opportunity screening,
- within-round robustness checks.

### Not sufficient by itself

Not by itself for:

- explicit Round 1 vs Round 2 carryover tables,
- durable side-by-side signal carryover matrices,
- final alpha registry construction,
- final strategy-family ranking.

Those gaps were filled downstream with:

- [build_round2_carryover_tables.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/build_round2_carryover_tables.py)
- [round2_round_comparison_metrics.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_round_comparison_metrics.csv)
- [round2_fair_proxy_comparison.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_fair_proxy_comparison.csv)
- [round2_signal_carryover_matrix.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_signal_carryover_matrix.csv)

## Audit Conclusion

- The analyzer did not need conceptual redesign for Round 2.
- It did need one small export-preservation fix to support the requested
  carryover workflow cleanly.
- The analytical sections are strong enough that the remaining work belongs in
  comparison/reporting artifacts, not in more analyzer complexity.
