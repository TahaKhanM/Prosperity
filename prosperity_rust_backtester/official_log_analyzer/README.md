# Official Log Analyzer

This toolchain analyzes official IMC Prosperity backtester payloads and turns them into structured research artifacts.

It supports:

- official `.zip` bundles returned by IMC,
- extracted official `.log` payloads,
- extracted official `.json` summaries,
- directories containing any mix of the above.

## What it measures

- per-run official profit and final per-product PnL
- submission trade classification:
  - `take_a1`, `take_b1`
  - `passive_inside_buy`, `passive_inside_sell`
  - `passive_join_buy`, `passive_join_sell`
  - fallback `other_*`
- trade markouts at horizons `1, 5, 10, 20`
- next-book response after our trades
- non-submission trade behavior
- optional replay of a local trader file against the official snapshots to compare intended orders with actual hosted fills

## CLI

Primary entrypoint:

```bash
python3 prosperity_rust_backtester/scripts/analyze_official_logs.py \
  /path/to/official-run.zip
```

You can also point it at a directory:

```bash
python3 prosperity_rust_backtester/scripts/analyze_official_logs.py \
  /path/to/log-folder/
```

### Replay a local trader against official snapshots

```bash
python3 prosperity_rust_backtester/scripts/analyze_official_logs.py \
  /path/to/official-run.zip \
  --replay-trader prosperity_rust_backtester/traders/latest_trader.py
```

### Export normalized datasets

```bash
python3 prosperity_rust_backtester/scripts/analyze_official_logs.py \
  /path/to/official-runs/ \
  --export-dir prosperity-research/exports/official-log-analyzer
```

That export directory will contain:

- `<label>_summary.json`
- `<label>_book_snapshots.csv`
- `<label>_submission_trade_events.csv`
- `<label>_external_trade_events.csv`
- `run_comparison.csv` when multiple runs are analyzed together

## Typical workflow

1. Collect official zip bundles from IMC.
2. Run the analyzer on one bundle to understand a single strategy.
3. Run it on multiple bundles together to compare runs.
4. Use `--replay-trader` for probe submissions or known local traders.
5. Load the exported CSV/JSON into the notebook in `output/jupyter-notebook/` or the visualizer.

## Why this exists

The official payload contains simulator information that the local backtester cannot reveal directly:

- which quotes get hit on the hosted surface,
- whether our trades are followed by book resets,
- whether the hosted market rewards passive spread capture or aggressive taking,
- and where official/local behavior diverges.

This folder keeps that analysis separate from the core trader scripts.
