---
name: prosperity-4-alpha-hypothesis-lab
description: Generate, formalize, and pre-falsify Prosperity 4 alpha hypotheses with causal mechanisms, null hypotheses, leakage checks, and expected failure modes. Maintains a deduplicated alpha registry for the active round. Does not implement code.
---

# Prosperity 4 Alpha Hypothesis Lab

## Mission
Convert vague intuitions into falsifiable alpha hypotheses, each with a causal story, a monetization path, and an explicit null. Rank only after falsifiability is locked in. Implementation is delegated to `prosperity-4-implementation-planner`.

## Definition of alpha
An alpha is a *repeatable* expected PnL source caused by one of:
- mispricing vs a defensible fair value,
- predictable order flow / imbalance,
- a structural rule (position limits, voucher expiry, conversion, manual auction),
- microstructure (spread, queue, depth, adverse selection),
- derivative/underlying relationship,
- manual-game-theoretic edge.

If the mechanism cannot be stated in one sentence, it is not an alpha.

## Trigger conditions
- A fresh product classification has landed.
- The user asks for new ideas for a product.
- A backtest audit rejected a variant and hypotheses need to be refreshed.
- The registry has grown stale or duplicative.

## Required inputs
- `prosperity-research/01_assumptions/current_assumptions.md`.
- `prosperity-research/04_signal_notes/roundN_product_classification.md`.
- `prosperity-research/03_eda/roundN/data_forensics_report.md`.
- Prior registry: `prosperity-research/04_signal_notes/roundN_alpha_registry.md` (create if missing; for Round 3 use `round3_alpha_registry.md`).
- `prosperity-research/05_execution_risk/latest_execution_risk_report.md` (to filter execution-hopeless ideas).

## Hypothesis template (every entry must fill every field)
- `alpha_id` (stable slug, e.g. `R3-VFE-basket-voucher-parity`).
- `product` (or product set).
- `family` (fair-value | imbalance | regime | microstructure | derivative | manual | execution | cross-asset).
- `mechanism` (one-sentence causal story).
- `required_evidence` (what must be true in data).
- `null_hypothesis` (what the world looks like if the alpha is not real).
- `falsification_test` (the *one* test that kills the idea cheaply).
- `monetization_path` (how this turns into signed orders).
- `expected_failure_mode` (what will most likely go wrong in live).
- `leakage_risk` (does the signal use information from the same bar it trades on?).
- `overfit_risk` (low | medium | high, plus reason).
- `implementation_complexity` (low | medium | high, plus reason).
- `expected_edge_sign_and_magnitude_prior` (directional only; no fabricated numbers).
- `backtest_validation_plan` (trader path, dataset, day split, baseline, metric that should move).
- `status` (new | ranked | pre-registered | in_build | implemented | validated | rejected | duplicate | parked).
- `duplicate_of` (if an older alpha_id supersedes it).
- `last_updated` (ISO date).

## Step-by-step workflow
### 1. Read the registry first
List existing `alpha_id`s and statuses. Do not re-propose rejected ideas unless new evidence has changed.

### 2. Generate candidate hypotheses from classifications
For each labeled family, enumerate the canonical alphas that family admits:
- Stationary → fair-value market making, threshold-based take.
- Drifting → trend filter, slope estimation.
- Mean-reverting → bollinger / zscore take; inventory-asymmetric quoting.
- Volatility-driven → vol-scaled quoting width.
- Spread-driven → passive-make in wide-spread regimes.
- Liquidity-driven → depth-gated quoting; fade depletion.
- Derivative-linked → parity / intrinsic floors, ladder-arbitrage, calendar/strike structure.
- Manual-game-linked → bid design under crowd-average or reserve.
- Regime-switching → state-gated switch between the above.
- Cross-asset-linked → lead-lag, hedged basket.

### 3. Attach a causal mechanism
Each hypothesis must state *why* the edge should exist and *who pays for it*. "Someone has to lose for us to win" — name the counterparty type (impatient taker, passive quoter, uninformed trade-through, auction-overbidder).

### 4. Lock in a falsification test before anything else
The test must be:
- cheap to run,
- independent of the backtest PnL,
- decisive (binary or strict threshold).

Examples: "lag-1 return autocorrelation must exceed 0.05 on at least 2 of 3 days", "voucher mid must stay within 2 ticks of intrinsic at lattice close", "opponent second-bid distribution must have a stable mode within 5 ticks of reserve".

If the falsification test fails, the hypothesis is `rejected` immediately; do not soft-redefine it.

### 5. Assess leakage
Check whether the signal uses information not available at decision time. Hand-compute the time boundary: signal at `t` must use only data from `<= t`.

### 6. Rank
Rank by, in strict order:
1. evidence quality (how strong is the pre-registered data behind it),
2. robustness (survives day-over-day splits),
3. implementation feasibility,
4. expected edge magnitude prior,
5. independence from already-ranked alphas.

Numeric ranks do not override these criteria.

### 7. Commit to registry
Update `prosperity-research/04_signal_notes/roundN_alpha_registry.md`. Merge duplicates via `duplicate_of`. Move falsified ideas to `status: rejected` with a one-line reason.

## Evidence requirements
- Every hypothesis must cite a specific finding from the forensics report or classification.
- No "try threshold X" without a causal story.
- No "this looked good in one day" without a multi-day plan in `backtest_validation_plan`.

## Failure modes to avoid
- Re-generating alphas already marked rejected without new evidence.
- Proposing "optimize parameters" as if it were a hypothesis.
- Writing a hypothesis that survives only under a tailored backtest.
- Skipping the null hypothesis.
- Importing a Round 2 alpha onto a Round 3 product because the names rhyme.

## Guardrails
- Never edit trader code.
- Never rank alphas by a single backtest PnL; ranking is pre-backtest.
- Never collapse two ideas into one row if their mechanisms differ.
- Never leave a hypothesis with empty fields.

## Example invocation prompts
- "Use prosperity-4-alpha-hypothesis-lab to generate Round 3 hypotheses for HYDROGEL_PACKS and VELVET_FRUIT_EXTRACT given the latest classification, and update `round3_alpha_registry.md`."
- "Use prosperity-4-alpha-hypothesis-lab to pre-register falsification tests for the 10 voucher strikes before any backtest runs."
- "Use prosperity-4-alpha-hypothesis-lab to dedupe and re-rank the current registry and mark stale entries."

## Concrete deliverable format
Updates to `prosperity-research/04_signal_notes/roundN_alpha_registry.md` plus, when the session produces 3+ new ideas, a short ranked handoff at `prosperity-research/04_signal_notes/latest_signal_ranking.md` with the top 5 alphas and their falsification tests.

## Integration
- Consumes: assumptions, classification, forensics, execution-risk report.
- Feeds: `prosperity-4-implementation-planner`, `prosperity-4-backtest-auditor`, `prosperity-4-competitive-orchestrator`.
