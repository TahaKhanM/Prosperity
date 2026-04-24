---
name: prosperity-4-data-forensics
description: Statistically interrogate Prosperity 4 CSVs, backtest logs, and run artifacts to produce an evidence-grounded data report. Covers schema, coverage, spreads, depth, trade intensity, book imbalance, day-vs-day drift, and sanity checks against official docs. Never proposes strategies; only evidence.
---

# Prosperity 4 Data Forensics

## Mission
Turn raw CSVs and run artifacts into a defensible evidence base. Nothing else downstream (hypothesis lab, product classifier, microstructure engineer, backtest auditor) is trustworthy if the underlying data view is wrong.

## Trigger conditions
- New round data has just landed under `prosperity_rust_backtester/datasets/roundN/` or `Data/ROUND_N/`.
- A run has completed with artifacts under `prosperity_rust_backtester/runs/<id>/` and needs audit-grade inspection.
- A product's behavior is being questioned ("is this noise or signal?").
- An existing EDA in `prosperity-research/03_eda/` is older than the last data refresh.

Do NOT invoke to propose an alpha or to validate a strategy; use hypothesis-lab or backtest-auditor instead.

## Required inputs
- `prosperity-research/01_assumptions/current_assumptions.md` (to know expected products and limits).
- `prosperity_rust_backtester/datasets/roundN/prices_round_N_day_*.csv` and `trades_round_N_day_*.csv`.
- `prosperity_rust_backtester/runs/<run_id>/{metrics.json,bundle.json,combined.log,activity.csv,pnl_by_product.csv,trades.csv}` when auditing runs.
- Existing helper scripts: `scripts/market_discovery.py`, `scripts/forensic_bundle.py`, `scripts/analyze_artifacts.py`, `scripts/deep_analysis.py`.

Prefer running these existing scripts before writing new ones.

## Expected outputs
1. `prosperity-research/03_eda/roundN/data_forensics_report.md` (primary).
2. Optional per-product notes under `prosperity-research/03_eda/roundN/per_product/<PRODUCT>.md`.
3. Optional figures under `prosperity-research/03_eda/roundN/figures/` (only when a figure encodes a fact not expressible in a table).

## Step-by-step workflow
### 1. Schema and coverage check (per CSV)
For every `prices_*.csv`:
- Confirm delimiter (semicolon for IMC price snapshots).
- Confirm columns: `day, timestamp, product, bid_price_1..3, bid_volume_1..3, ask_price_1..3, ask_volume_1..3, mid_price, profit_and_loss`.
- Report row count, unique timestamps, unique products.
- Flag missing levels (`NaN` at level 1 vs 2 vs 3), zero volumes, non-monotonic timestamps, timestamp gaps.

For every `trades_*.csv`:
- Confirm columns: `timestamp, buyer, seller, symbol, currency, price, quantity`.
- Report row count, distinct symbols, distinct counterparties (note: `SUBMISSION` is us), currency consistency.

Produce a coverage table with one row per (product, day) and columns: `snapshots, first_ts, last_ts, mid_price_range, spread_median, spread_p99, depth_l1_median, trades_count, volume_total`.

### 2. Mid-price and spread distributions (per product per day)
Report: min, p1, p10, p50, p90, p99, max, mean, std for mid-price and (ask1 - bid1). Compare day-to-day.

### 3. Depth distributions
For each side, report level-1, level-2, level-3 volume distributions. Note how often level-2 or level-3 is empty. Depth asymmetry: `log(bid_vol_l1 / ask_vol_l1)` distribution.

### 4. Trade intensity
Trades per 100 timestamps, per product. Share of trades involving `SUBMISSION` vs bot-to-bot. Average trade size. Fraction of trades that cross the posted book vs print at mid.

### 5. Order-book imbalance
Compute microprice `m = (ask_l1*bid_vol_l1 + bid_l1*ask_vol_l1)/(bid_vol_l1+ask_vol_l1)` and report `m - mid_price` distribution. Note autocorrelation at lag 1..10 (only report, do not interpret as alpha here).

### 6. Day-to-day differences
Test whether each statistic in steps 2-5 is stable day-over-day. Report relative deltas. Flag any stat whose day-to-day relative change exceeds 25% as a potential regime/microstructure shift.

### 7. Cross-product relationships
For pairs where one is a derivative of another (e.g. voucher and underlying): report contemporaneous correlation of returns and of spreads. Do not call this a tradable signal; forward it to the hypothesis lab.

### 8. Sanity checks
- Do observed symbols match the assumptions doc?
- Are observed mid-price ranges plausible given strikes (for vouchers)?
- Is `OrderDepth.sell_orders` convention (negative volumes in code, positive in CSV) documented in the report?
- Are tutorial products (EMERALDS, TOMATOES) accidentally present in a live-round folder?

### 9. Run-artifact forensics (when auditing a run)
From `metrics.json`: per-day PnL, total ticks, own-trade count.
From `pnl_by_product.csv`: product contribution decomposition.
From `trades.csv`: fill patterns, aggression (crossing vs resting), fill prices vs posted levels, inventory path.
From `combined.log`: decision log versus observed book state at each timestamp.

## Evidence requirements
- Every claim in the report must cite a row count, statistic, or file path.
- Bucket claims into: `descriptive fact`, `cross-day delta`, `sanity flag`, `unexplained anomaly`.
- Never write "looks mean-reverting", "seems trendy", or similar interpretation. Leave interpretation to the classifier and hypothesis lab.

## Failure modes to avoid
- Running EDA on only one day and generalizing.
- Confusing tutorial-round data with live-round data.
- Treating small-sample tail statistics as durable.
- Reporting a single correlation without sample size or lag.
- Quietly dropping rows with missing levels instead of counting them.
- Using aggregated statistics that hide regime changes.

## Guardrails
- Never write a trading recommendation.
- Never modify raw dataset files.
- Do not delete old forensics reports; archive them under `prosperity-research/03_eda/roundN/archive/`.
- If a run's `metrics.json` disagrees with `pnl_by_product.csv`, report the discrepancy and stop forensics until resolved.

## Example invocation prompts
- "Use prosperity-4-data-forensics to produce the Round 3 Salvinar per-product EDA once the new CSVs land in `datasets/round3/`."
- "Use prosperity-4-data-forensics to audit `runs/<id>/` against the Round 2 baseline and flag inventory-path anomalies."
- "Use prosperity-4-data-forensics to compare depth and spread distributions day-over-day for VELVET_FRUIT_EXTRACT and report regime-shift flags."

## Concrete deliverable format
`prosperity-research/03_eda/roundN/data_forensics_report.md` with sections:
1. Scope & Data Inventory
2. Schema & Coverage Tables
3. Per-Product Price & Spread Statistics
4. Depth & Imbalance Statistics
5. Trade Intensity & Fill Shape
6. Day-to-Day Deltas & Regime Flags
7. Cross-Product Relationships (descriptive only)
8. Run-Artifact Findings (if applicable)
9. Sanity-Check Failures
10. Open Evidence Questions (hand-off to hypothesis lab / classifier)

## Integration
- Consumes: `current_assumptions.md`, raw CSVs, run artifacts.
- Feeds: `prosperity-4-product-classifier`, `prosperity-4-alpha-hypothesis-lab`, `prosperity-4-microstructure-engineer`, `prosperity-4-backtest-auditor`.
- Rerun: whenever new data arrives, a new run completes, or assumptions change.
