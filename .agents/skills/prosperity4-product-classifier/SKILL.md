---
name: prosperity-4-product-classifier
description: Classify each Prosperity 4 product into a market-behavior family (stationary, drifting, mean-reverting, trend, volatility-driven, spread-driven, liquidity-driven, cross-asset-linked, derivative-linked, manual-game-linked, regime-switching, or unknown) using evidence and confidence levels. Never assumes old-round behavior carries forward.
---

# Prosperity 4 Product Classifier

## Mission
Assign each active product to one or more behavior families with a stated confidence and an explicit "what evidence would change this" line. Classifications feed the hypothesis lab — a wrong label compounds into wasted implementation work.

## Trigger conditions
- After `prosperity-4-data-forensics` has produced a fresh report.
- When a product lacks any existing classification in `prosperity-research/04_signal_notes/`.
- When data shows a day-to-day regime flag that may invalidate an earlier classification.
- Before hypothesis generation for a product.

## Required inputs
- `prosperity-research/01_assumptions/current_assumptions.md` (products, vouchers, limits).
- `prosperity-research/03_eda/roundN/data_forensics_report.md` and per-product EDA notes.
- Any prior classification at `prosperity-research/04_signal_notes/` (especially `latest_signal_ranking.md`, `round2_alpha_registry.md`).
- Relevant CSVs for spot-checks via the Rust/Python tooling.

## Behavior families (exhaustive list; pick one or more)
1. Stationary (mid oscillates around a constant with small variance).
2. Drifting (persistent non-zero mean in first difference).
3. Mean-reverting (negative AR(1) coefficient, variance bounded).
4. Trend-following (positive autocorrelation across medium horizons).
5. Volatility-driven (conditional variance clustering dominates return structure).
6. Spread-driven (P&L lives in bid-ask spread, not price change).
7. Liquidity-driven (depth/absence of depth governs tradability more than price).
8. Cross-asset-linked (returns explained by another asset's returns).
9. Derivative-linked (voucher/option whose price is a function of an underlying).
10. Manual-game-linked (auction/game-theoretic mechanic, not a continuous market).
11. Regime-switching (distinct regimes with sharp transitions).
12. Unknown / insufficient evidence.

A product may carry multiple labels (e.g. "mean-reverting under calm regime + volatility-driven under opening regime").

## Diagnostic battery (minimum tests to run before labeling)
1. First-difference mean test: is the mean significantly non-zero at a given horizon?
2. Lag-1 autocorrelation of returns and of mid-differences.
3. Variance ratio test at lags 1, 5, 20, 100 ticks.
4. Spread persistence (lag-1 autocorrelation of bid-ask spread).
5. Depth stability (coefficient of variation of level-1 volume).
6. Regime segmentation by time-of-day / day-index (are first-moment or second-moment estimates unstable?).
7. Cross-asset regression: `return_A ~ return_B` for plausible pairs.
8. For vouchers: `price ~ intrinsic(K, underlying_mid)` fit quality.

Every label must be backed by at least two of these tests pointing the same way.

## Step-by-step workflow
### 1. Scope
List the products to classify. Do not classify products whose data is missing.

### 2. Run the diagnostic battery
Compute each test per product per day. Record per-day results, not just aggregates.

### 3. Assign labels with confidence
For each product, write:
- `primary_family`,
- `secondary_families` (if any),
- `confidence` (high | medium | low | unknown),
- `evidence` (the diagnostic values that justify the label),
- `falsifiers` (concrete observation that would force a relabel),
- `regime_notes` (days or time-of-day where the label breaks down),
- `historical_analogy` (optional: a prior-round product with similar behavior, explicitly marked as *analogy only*).

### 4. Cross-product structure
If vouchers exist, explicitly classify them as `derivative-linked` and record the underlying. Do not cascade the underlying's label onto the voucher.

### 5. Commit
Write to `prosperity-research/04_signal_notes/roundN_product_classification.md`. Update a table row in `prosperity-research/04_signal_notes/latest_signal_ranking.md` if present. Archive any prior classification under `prosperity-research/04_signal_notes/archive/`.

## Evidence requirements
- No label without two corroborating diagnostics.
- `confidence: high` requires stable labels across all available days.
- `confidence: low` requires an explicit falsifier plan.
- Never re-use a prior-round label without re-running the diagnostics on new data.

## Failure modes to avoid
- Classifying from a single day.
- Treating "looks stable on a plot" as stationarity.
- Forcing a label on a product that should be `unknown`.
- Inheriting a Round 2 ASH/Pepper classification onto a Round 3 product of similar name.
- Classifying vouchers without cross-referencing the underlying.

## Guardrails
- Never propose trades from this skill.
- Never collapse multi-regime products to a single label without flagging the regimes.
- Never overwrite `latest_signal_ranking.md` without archiving the prior version.

## Example invocation prompts
- "Use prosperity-4-product-classifier to classify HYDROGEL_PACKS, VELVET_FRUIT_EXTRACT, and the 10 vouchers using the latest Round 3 forensics report."
- "Use prosperity-4-product-classifier to re-evaluate INTARIAN_PEPPER_ROOT after the new regime flag in day 1."

## Concrete deliverable format
`prosperity-research/04_signal_notes/roundN_product_classification.md` with:
1. Product table (primary_family, secondary_families, confidence, regime_notes).
2. Per-product evidence block (diagnostic values, falsifiers, historical-analogy line).
3. Open questions fed to the hypothesis lab.

## Integration
- Consumes: assumptions doc, data forensics report.
- Feeds: `prosperity-4-alpha-hypothesis-lab`, `prosperity-4-derivatives-voucher-analyst`, `prosperity-4-microstructure-engineer`.
