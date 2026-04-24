---
name: prosperity-4-manual-game-theorist
description: Analyze Prosperity 4 manual challenges as formal games. Extracts rules, variables, payoff functions, opponent dependencies, and uncertainty. Produces submission-ready decision memos for auction and budget-allocation tasks without pretending algorithmic backtests answer the problem.
---

# Prosperity 4 Manual Game Theorist

## Mission
Manual rounds are independent profit sources with mathematically specifiable mechanics. This skill formalizes them, models opponent behavior where relevant, and produces a decision memo that is auditable rather than vibes-based.

## Trigger conditions
- A round introduces or activates a manual challenge (auction, budget allocation, biopod auction, investment game).
- A prior manual decision needs re-evaluation under new information (updated reserve distribution, new rumor about resale value).
- The user asks for a submission-ready manual recommendation.

## Required inputs
- `prosperity-research/01_assumptions/current_assumptions.md` (manual task section).
- `Prosperity Context/20_MANUAL_TRADING_CONTEXT.md`.
- Official round doc text (in briefing or `Prosperity Context/Unrefined Context/`).
- Existing solvers: `prosperity_rust_backtester/scripts/manual_round/round1_auction_solver.py`, `round2_budget_allocator.py` (adapt, do not overwrite).
- Any prior notes under `prosperity-research/07_manual_round/`.

## Formalization template
For every manual task, write down explicitly:
- `N`: number of independent sub-problems (gardeners, items, pillars).
- `decision_variables`: list with domain (`integer in [0,100]`, `real`, `discrete set`, `two bids`, etc.).
- `constraints`: bounds, monotonicity, discretization, tie-breaks.
- `payoff_function`: exact formula, with every term defined.
- `opponent_dependence`: independent | crowd-average (A) | rank-based | auction-clearing | reserve-price-distributed.
- `known_values`: resale value V, terminal value, fees, budget.
- `unknowns`: hidden reserves, opponent bid distribution, probability rules.
- `ambiguities`: statements in the briefing that are not mathematically precise (for Round 3: "probability decreases rapidly"; "flowering fives" — record both interpretations).

## Step-by-step workflow
### 1. Rewrite the problem as math
Reproduce the payoff and constraints in formal notation. Replace narrative phrases with variables. If a rule is ambiguous, enumerate plausible interpretations and flag which one you are solving first.

### 2. Solve the independent structure
If sub-problems are independent (e.g. each gardener is a separate decision), solve per sub-problem first and aggregate last.

### 3. Model opponent distributions
For crowd-average rules: specify a prior over the average `A` (e.g. uniform on a range, unimodal around V, empirical from past rounds if comparable).
For rank-based rules: specify a prior over the competitor allocation distribution.
For auction clearing: reconstruct standing demand/supply and simulate marginal effects.

### 4. Compute expected value
For each candidate decision:
- compute EV under each plausible opponent prior,
- compute worst-case payoff,
- compute variance or a simple risk measure,
- report sensitivity to the key uncertain parameter.

### 5. Dominance and regret
Rule out strictly dominated decisions. Prefer decisions on the efficient frontier of (EV, worst-case). Report max-regret for the recommended decision under each plausible opponent prior.

### 6. Discretization
If the submission interface requires integer or coarse bids (e.g. multiples of 5), restrict the search to that grid and explicitly record any loss vs the continuous optimum.

### 7. Decision memo
Write a final memo that a teammate could submit from without reading the working.

## Round 3 Salvinar biopod auction specifics
According to the in-session briefing, each gardener `i` has private reserve `R_i`. Our bids are `(b_{1,i}, b_{2,i})`. Rules:
- If `b_{1,i} > R_i` and our first bid is among the lowest such first bids from any crew, we win at `b_{1,i}`.
- Else if `b_{2,i} > A` (global average of all crews' second bids), we win at `b_{2,i}`.
- Else "probability decreases rapidly" (ambiguous).
- Rumor: reserves set "a flowering five apart" (ambiguous — multiples-of-5 vs spacing-of-5).
- Resale: biopods autoliquidate at ~920 XY.

Required modeling steps before recommending bids:
- Prior over `R_i`: bounded uniform or discrete (multiples of 5) on a plausible range below 920.
- Prior over `A`: use competitor-plausible distribution; note that aggregated second bids likely cluster below 920.
- Two-stage EV: `EV(b1, b2) = P(win on b1) * (V - b1) + P(miss on b1) * [P(win on b2) * (V - b2)]` under the priors.
- Discretization: integer XY (confirm), or multiples of 5 if "flowering fives" is interpreted that way for bids too.
- Optimize per gardener; aggregate only at the end; check portfolio-level downside.

## Round 2 budget allocation specifics
Payoff: `PnL = Research(r) * Scale(s) * Speed_rank(p) - Budget_Used`.
- `Research(r) = 200000 * ln(1 + r) / ln(101)` (logarithmic).
- `Scale(s) = 7 * s / 100` (linear).
- `Speed_rank` is rank-based 0.1–0.9 across players.
- Total `r + s + p ≤ 100`.

Required steps: model plausible crowd speed distribution, use best-response reasoning for `p`, confirm interior optimum does not require spending full budget, report EV vs worst-case rank.

## Round 1 exchange auction specifics
Frozen book, single clearing price, maximum-volume criterion, high-price tiebreak, price-time priority. Required steps: reconstruct the standing curves, simulate marginal price/size effects of our order, report clearing price basins and bunching points.

## Evidence requirements
- Every EV number must cite the prior and sample size it used.
- Every ambiguity must be enumerated with at least two interpretations and a recommended interpretation plus reason.
- Every final bid must state: EV, worst-case, and regret.

## Failure modes to avoid
- Pretending a backtest can validate a manual answer.
- Treating an ambiguous rule as known.
- Using a point estimate for opponent behavior.
- Over-optimizing to one opponent prior and ignoring sensitivity.
- Submitting continuous values when the interface requires integers.
- Spending full budget just because it is available.

## Guardrails
- Never fabricate probability functions to fill an ambiguity; flag it.
- Never claim certainty about opponent behavior.
- Never edit trader code.
- Never blend manual payoff into algo PnL accounting.

## Example invocation prompts
- "Use prosperity-4-manual-game-theorist to produce a decision memo for the Round 3 biopod auction with per-gardener `(b1, b2)` recommendations."
- "Use prosperity-4-manual-game-theorist to refresh the Round 2 budget-allocation plan under two plausible speed-competitor distributions."
- "Use prosperity-4-manual-game-theorist to check the Round 1 exchange-auction memo against marginal-order sensitivity."

## Concrete deliverable format
Write to `prosperity-research/07_manual_round/roundN_<task>/decision_memo.md` with:
1. Formal problem statement.
2. Assumed priors and ambiguity interpretations.
3. EV and worst-case table per candidate decision.
4. Recommended decision, rationale, and regret.
5. Sensitivity analysis.
6. Open uncertainties and what would update the memo.

## Integration
- Consumes: assumptions, manual context, existing solver scripts.
- Feeds: `prosperity-4-competitive-orchestrator` for final submission readiness.
- Strictly independent of algo backtests.
