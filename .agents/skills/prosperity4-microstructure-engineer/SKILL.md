---
name: prosperity-4-microstructure-engineer
description: Analyze Prosperity 4 order-book mechanics, fill realism, adverse selection, and the gap between signal PnL and executed PnL. Produces execution-risk diagnoses that distinguish real edge from fill-model-assisted edge.
---

# Prosperity 4 Microstructure Engineer

## Mission
Separate signal quality from execution quality. A mid-price prediction that cannot actually be traded is worth zero. This skill quantifies where PnL is mechanically made or lost, so downstream decisions (hypothesis ranking, implementation planning, validation) weight execution realism correctly.

## Trigger conditions
- A hypothesis in the registry depends on specific fill behavior (passive make, take through level 1, joining the queue).
- A backtest-audit reports implausible fill rates or inventory trajectories.
- The Rust backtester's execution semantics are suspected of inflating local PnL.
- A new product's order book differs materially from prior rounds.

## Required inputs
- `prosperity-research/03_eda/roundN/data_forensics_report.md`.
- Run artifacts under `prosperity_rust_backtester/runs/<run_id>/`, especially `trades.csv`, `activity.csv`, `combined.log`.
- `Prosperity Context/30_REPO_AND_TOOLING_CONTEXT.md` for local backtester caveats.
- Relevant raw CSVs for ground truth of book shape.

## Concepts to separate explicitly
1. Signal PnL: the PnL a perfect-fill oracle would earn.
2. Executed PnL: the PnL our quotes and takes actually earn given queue / adverse selection / rejection.
3. Fill-model slack: the gap attributable to the local backtester being lenient.
4. Inventory drag: PnL lost to holding vs flat.
5. Opportunity cost: PnL lost to unplaced orders when limits block a desired side.

## Step-by-step workflow
### 1. Book-shape profile (per product)
- Spread: median, p90, p99 in ticks.
- Depth at level 1, 2, 3 (both sides).
- Frequency of empty level-2 or level-3.
- Frequency of crossed/locked books (treat as engine artifacts if present).

### 2. Trade-through analysis
For each tick, categorize market trades as:
- at-mid,
- inside-book (price between bid_1 and ask_1),
- at-touch buy or sell,
- through-touch (traded outside visible levels).

Report conditional distributions by product and by day.

### 3. Crossing vs posting
For the strategy under audit:
- share of own orders that crossed vs rested,
- fill rate of resting orders by distance from touch,
- adverse-selection proxy: mid-price move in the 5 ticks after each passive fill (signed with fill direction),
- share of taker fills that immediately had the touch move further in their favor (missed fills).

### 4. Position-limit events
- Count ticks where the strategy attempted an order and worst-case aggregated orders would have breached a limit, triggering rejection of *all* orders for that product that tick (worst-case rule).
- Quantify PnL attributable to those rejected ticks via counterfactual quote reasoning.

### 5. Fill-model slack check
- Do local fills occur at prices or volumes that require depth the book never showed?
- Do resting orders get filled at ticks where no market trade at that level actually printed?
- If either is true, flag the PnL contribution as `fill-model-assisted` and exclude it from validated edge claims.

### 6. Adverse selection decomposition
Per product, compute expected post-fill mark-to-mid change for passive buy fills and passive sell fills. Negative on both sides = bleed.

### 7. Execution risk report
Write to `prosperity-research/05_execution_risk/latest_execution_risk_report.md`. Archive the prior version. Write a compact diagnosis packet at `prosperity-research/05_execution_risk/diagnosis_packets/<date>_<run_label>/diagnosis_packet.md` using the existing convention.

## Evidence requirements
- Every fill-quality claim must cite specific ticks, prices, and trade counts.
- Adverse-selection numbers must report sample size.
- Fill-model-slack flags require at least one reproducible example line from `combined.log`.

## Failure modes to avoid
- Treating local fills as faithful without a slack check.
- Assuming bot behavior is identical across rounds.
- Conflating signal quality with fill quality when both drift together.
- Reporting averages that hide tail events.
- Ignoring the worst-case position-limit rule (the rule that rejects *all* product-side orders for the tick).

## Guardrails
- Never edit trader code.
- Do not update the alpha registry unless execution evidence is decisive; prefer handing findings to the hypothesis lab.
- Never rely on a single run to declare a microstructure pattern.

## Example invocation prompts
- "Use prosperity-4-microstructure-engineer to decompose run `<id>` into signal PnL vs executed PnL for HYDROGEL_PACKS."
- "Use prosperity-4-microstructure-engineer to quantify adverse selection on passive VELVET_FRUIT_EXTRACT fills for the last three days of data."
- "Use prosperity-4-microstructure-engineer to check whether fill-model slack explains the run's Pepper PnL."

## Concrete deliverable format
`prosperity-research/05_execution_risk/latest_execution_risk_report.md` plus a dated diagnosis packet under `diagnosis_packets/`.

## Integration
- Consumes: forensics report, run artifacts.
- Feeds: `prosperity-4-backtest-auditor`, `prosperity-4-inventory-risk-controller`, `prosperity-4-alpha-hypothesis-lab`, `prosperity-4-implementation-planner`.
