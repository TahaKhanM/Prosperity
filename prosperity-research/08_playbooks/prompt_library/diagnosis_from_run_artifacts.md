# Diagnosis From Run Artifacts

```text
You are diagnosing a local Prosperity backtest run.

Inputs:
- run_summary.md
- headline_metrics.json
- diagnosis_packet.md
- worst_timestamps.csv
- fill_summary.csv
- inventory_summary.csv

Task:
1. rank likely failure causes:
   fair value, taking thresholds, passive fill quality, inventory control, state/path handling
2. explain the strongest evidence for the top cause
3. recommend one next change only
4. name the metric that should move next if that change is correct

Prefer compact evidence over raw logs unless a specific timestamp must be audited.
```
