---
name: prosperity-4-strategy-refactor-engineer
description: Safely improve Prosperity 4 trader code structure without changing behavior unless explicitly requested. Enforces submission compatibility, datamodel interface correctness, `traderData` discipline, determinism, and localized diffs. Produces refactor plans plus minimal diffs.
---

# Prosperity 4 Strategy Refactor Engineer

## Mission
Keep the trader code healthy so other skills can build on it. A refactor under this skill must not change trading behavior unless the user explicitly opts in to a behavior change.

## Trigger conditions
- A trader file has grown unmanageable (repeated logic, hidden state, >1000 lines of ad hoc blocks).
- Submission compatibility is at risk (wrong return shape, mutable globals, `bid()` misplacement).
- A new skill output (microstructure, inventory) requires restructuring before implementation.
- Determinism issues are suspected.

Do NOT invoke to introduce a new alpha; use `prosperity-4-implementation-planner` instead.

## Required inputs
- Target trader path (explicit).
- `prosperity-research/01_assumptions/current_assumptions.md` (interface constraints).
- `Prosperity Context/10_ALGO_TRADING_CONTEXT.md` (submission rules, `traderData` 50k truncation, `bid()` scoping).
- Any recent baseline runs to validate behavior unchanged.

## Non-negotiable invariants
1. Return shape from `run(state)` must be `(orders, conversions, traderData)`.
2. `bid()` must be defined at class scope and is ignored outside Round 2; it must never call into `run()` side-effects.
3. Persistent state lives only in `traderData` (string), not in class or module globals.
4. `traderData` serialized size must stay < 50,000 characters.
5. Product symbols used in `Order(symbol, price, quantity)` must match strings from `state.listings` / `state.order_depths` exactly.
6. Order quantities: positive buy, negative sell. Respect worst-case position-limit rule.
7. No file system access, no network, no non-standard imports beyond what the hosted environment supports.
8. Trader instance reuse across ticks is allowed locally but must not be relied on for correctness (hosted AWS Lambda is stateless).
9. No randomness without a seed recorded in `traderData`.
10. No debug prints to stdout that would break `combined.log` structure; use the repo's existing logger if any.

## Step-by-step workflow
### 1. Produce a refactor plan first
Before touching code, write a plan listing: files affected, functions affected, invariants being preserved, exact intended behavioral diff (must be "none" unless user opted in).

### 2. Create a new variant rather than overwriting a working baseline
Path: `prosperity_rust_backtester/traders/RoundN/<baseline_name>_refactor_v<NN>.py`. Preserve the prior baseline.

### 3. Decompose logic cleanly
Typical good decomposition per product:
- compute fair value / state,
- take clearly favorable quotes,
- clear risk if cheap,
- quote passively using temporary post-take position,
- adjust inventory skew and size.

Keep Round 2 `bid()` logic strictly separate from `run()`.

### 4. Apply minimal diffs
Every edit must be the smallest change that satisfies the plan. Do not re-flow untouched code. Do not reorder imports gratuitously.

### 5. Localize state
Every mutable variable in a function must be local or explicitly passed via `traderData`. No module-level mutable state.

### 6. Behavior-equivalence verification
Run the refactored variant against the same dataset the baseline used, with the same flags. Compare `metrics.json`, `trades.csv`, `pnl_by_product.csv`. Any difference must be explained; unexplained differences mean the refactor changed behavior and must be reverted or justified.

### 7. Determinism verification
Run twice. Any non-floating-point difference is a determinism bug.

### 8. Document
Write a short change summary at the top of the new variant (or in a sibling `.md`) listing: files changed, invariants preserved, behavior-equivalence check result.

## Evidence requirements
- Every refactor variant must come with a behavior-equivalence table vs the previous baseline.
- No refactor ships without two-run determinism confirmation.
- No refactor ships without the backtest-auditor confirming no PnL or inventory changes.

## Failure modes to avoid
- Overwriting a working baseline.
- "Improving" naming while accidentally changing control flow.
- Introducing a new import that is not guaranteed hosted-available.
- Adding try/except that swallows real errors.
- Moving state out of `traderData` into a module-level dict — wrong and breaks hosted.
- Letting `bid()` share a mutable with `run()`.

## Guardrails
- No alpha change under this skill.
- No parameter tweaks dressed up as refactor.
- No "while I was at it" side edits.
- Never exceed `traderData` 50k; compress JSON if needed.
- Never remove a branch of logic because it looked unused unless the backtest-auditor agrees.

## Example invocation prompts
- "Use prosperity-4-strategy-refactor-engineer to split `traders/Round1/Ash.py` into per-product modules while preserving behavior exactly."
- "Use prosperity-4-strategy-refactor-engineer to move all mutable state in `<trader>` into `traderData` and verify determinism."
- "Use prosperity-4-strategy-refactor-engineer to create `round3_baseline_refactor_v01.py` with the decomposition (fair → take → clear → make → skew) without changing behavior."

## Concrete deliverable format
1. Refactor plan (in chat or under `prosperity-research/10_experiment_logs/refactor_<date>.md`).
2. New trader variant file under `prosperity_rust_backtester/traders/RoundN/`.
3. Behavior-equivalence + determinism check results appended to `prosperity-research/06_validation/latest_validation_report.md`.

## Integration
- Consumes: trader baseline, assumptions, context docs.
- Feeds: `prosperity-4-backtest-auditor` (for equivalence confirmation), `prosperity-4-implementation-planner` (cleaner base to build on).
