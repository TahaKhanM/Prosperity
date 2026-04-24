---
name: prosperity-4-inventory-risk-controller
description: Audit Prosperity 4 trader variants for inventory paths, exposure concentration, drawdown clusters, and asymmetric tail risk. Flags high-PnL runs that hide blow-up states. Distinct from backtest auditing and microstructure analysis.
---

# Prosperity 4 Inventory Risk Controller

## Mission
PnL is not the only metric. A variant that scores high while spending hours trapped long a losing product, or while bleeding on tail events, is not safe to submit. This skill audits the *state trajectory* of trader variants.

## Trigger conditions
- A new variant has produced run artifacts.
- Baseline-vs-candidate review is in progress.
- Headline PnL improved but the user suspects hidden risk.
- Day-to-day PnL is volatile even when the mean is good.

## Required inputs
- `prosperity_rust_backtester/runs/<run_id>/{metrics.json,pnl_by_product.csv,trades.csv,activity.csv,bundle.json,combined.log}`.
- Official position limits from `prosperity-research/01_assumptions/current_assumptions.md`.
- Prior inventory notes under `prosperity-research/05_execution_risk/inventory/`.

## Metrics to compute
For each product, each day:
1. Position path over time; fraction of ticks at each decile of limit.
2. Max long, max short, average absolute position.
3. Time spent `|pos| > 0.8 * limit` (danger zone).
4. Mark-to-mid PnL decomposition per tick; cluster consecutive negative ticks (loss streaks).
5. Drawdown series on cumulative PnL: max drawdown, average drawdown, time-to-recovery.
6. Inventory-gated realized PnL vs flatten-on-every-tick counterfactual (inventory drag).
7. Cross-product exposure correlation (do both products go long at the same time?).
8. Tail events: ticks contributing > 1% of total PnL (positive or negative). If a small set of ticks drives the total, flag.
9. Getting-trapped diagnostic: whenever position reaches a limit side, how long until it reverses? How much PnL is lost before reversal?

## Step-by-step workflow
### 1. Load artifacts
Prefer `bundle.json` / `combined.log` when persisted; fall back to `activity.csv` + `trades.csv` otherwise.

### 2. Position path and concentration
Build the per-product position time series. Report metrics 1–3.

### 3. Loss-cluster analysis
Segment the PnL series. Identify the 3 worst clusters per product per day. For each cluster record: start/end timestamp, duration, realized loss, position at entry, triggering book state (from `combined.log`).

### 4. Drawdown & tail audit
Report metrics 5 and 8. Distinguish drawdowns caused by inventory drag from drawdowns caused by adverse selection.

### 5. Counterfactual flatten
Compute the counterfactual where the trader holds no overnight inventory between bar boundaries (or, more aggressively, flattens every 100 ticks). Compare.

### 6. Cross-product correlation
If multiple products traded, report the correlation of signed positions. A variant that goes long everything simultaneously carries concentrated directional risk.

### 7. Tail-event check
List the top 10 PnL ticks (positive and negative). If the total is dominated by fewer than 20 ticks, flag the variant as tail-driven.

### 8. Pass / flag / fail judgment
- `pass`: no limit-pin longer than 10% of day, no tail-dominated PnL, max drawdown < X% (record the X used).
- `flag`: conditions partially met; ship only with explicit user acknowledgement.
- `fail`: any of: limit-pinned > 25% of day, drawdown > 50% of final PnL, tail-dominated PnL (< 20 ticks drive > 50% PnL).

## Evidence requirements
- Every flag/fail must cite the exact clusters, timestamps, and positions.
- Never report an aggregated number without the associated sample size and timestamp range.

## Failure modes to avoid
- Reading only `metrics.json` summary.
- Ignoring cross-product directional stacking.
- Missing tail events by using only averages.
- Confusing inventory drag with adverse selection (both can coexist).
- Treating one lucky recovery as proof of safety.

## Guardrails
- Never propose code changes directly; hand findings to the implementation planner.
- A "pass" from this skill is necessary but not sufficient for shipping; the backtest-auditor and microstructure-engineer must also agree.

## Example invocation prompts
- "Use prosperity-4-inventory-risk-controller to audit run `<id>` vs the current baseline and flag any tail-dominated PnL."
- "Use prosperity-4-inventory-risk-controller to check whether the new trader gets trapped long on VELVET_FRUIT_EXTRACT during regime-2 hours."

## Concrete deliverable format
Write to `prosperity-research/05_execution_risk/inventory/<date>_<variant>_inventory_audit.md` with:
1. Variant and baseline references.
2. Per-product position-path metrics.
3. Loss-cluster table.
4. Drawdown & tail table.
5. Pass/flag/fail verdict with thresholds used and reasons.
6. Recommended fix direction (but not code).

## Integration
- Consumes: run artifacts, assumptions, prior audits.
- Feeds: `prosperity-4-backtest-auditor`, `prosperity-4-implementation-planner`, `prosperity-4-competitive-orchestrator`.
