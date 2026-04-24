---
name: prosperity-4-round-context-ingestor
description: Build a disciplined, source-grounded understanding of the currently active Prosperity 4 round before any strategy work begins. Extracts product list, position limits, submission rules, manual mechanics, voucher/derivative specs, and unknowns into a single handoff document. Never proposes strategy.
---

# Prosperity 4 Round Context Ingestor

## Mission
Produce a single source-grounded `current_round_context.md` that every downstream skill (classifier, hypothesis lab, voucher analyst, manual solver, implementation planner) can trust.

This skill is a *fact assembler*, not a strategist. It must not suggest, rank, or sketch trading ideas.

## Trigger conditions
Invoke when any of the following is true:
- a new round is announced or just started,
- competition context has materially changed (new products, new rules, new manual task),
- `prosperity-research/01_assumptions/current_assumptions.md` is missing, stale, or contradicts the in-session briefing,
- a downstream skill asks "what round are we in and what are the confirmed products/limits?"

Do NOT invoke for minor tweaks or between backtests within the same round.

## Required inputs
Read, in this order, whichever exist:
1. In-session briefing text the user has pasted.
2. `Prosperity Context/00_PROSPERITY_CONTEXT_OVERVIEW.md` (trust hierarchy, cross-round facts).
3. `Prosperity Context/10_ALGO_TRADING_CONTEXT.md` and `20_MANUAL_TRADING_CONTEXT.md`.
4. `Prosperity Context/Unrefined Context/Official Prosperity Context.md` and `Prosperity Round 2.md`.
5. `prosperity-research/01_assumptions/current_assumptions.md` (previous snapshot).
6. `prosperity_rust_backtester/datasets/roundN/` to confirm what data actually exists on disk.
7. `prosperity_rust_backtester/Makefile` for which `make roundN` targets are wired.

## Source hierarchy
When facts conflict, use this exact order:
1. Official written docs in `Prosperity Context/Unrefined Context/`.
2. In-session briefing from the user (treat as official if user explicitly states it is).
3. `Prosperity Context/00_PROSPERITY_CONTEXT_OVERVIEW.md` summaries.
4. Narrative / uplink / transcript material.
5. Older round notes and public repos (reference only).

Never let a lower-tier source override a higher-tier one. Record the conflict explicitly instead.

## Step-by-step workflow
### 1. Identify the active round
State: round number, round name, planet/setting, exact start/end if given, profit-reset flag, remaining round count.

### 2. Enumerate algorithmic products
For each product name, fill a row with these columns:
- `symbol` (exact string as it will appear in `order_depths`),
- `type` (commodity | voucher/option | conversion | manual-only),
- `underlying` (if derivative),
- `strike` (if voucher),
- `expiry` (absolute round or "N rounds remaining"),
- `position_limit` (integer or Unknown),
- `denomination_currency`,
- `data_available_locally` (yes/no, path),
- `source` (official | briefing | inferred | unknown),
- `confidence` (confirmed | likely | unknown).

If a symbol has not been confirmed, write `UNKNOWN_SYMBOL_<purpose>` and mark `confidence: unknown`.

### 3. Enumerate manual challenges
For each manual task, record:
- task name,
- decision variables and their domain,
- exact payoff formula,
- opponent dependence (independent | crowd-average | rank-based | auction-clearing),
- constraints (budget, max bids per item, discretization, etc.),
- tie-breaking rules,
- known resale/terminal values,
- source and confidence.

### 4. Record submission interface facts
Fix: `Trader.run(state)` return shape (`orders, conversions, traderData`), `bid()` presence/scope, `traderData` 50k character truncation, worst-case position-limit rejection semantics, listings/order_depths/own_trades/market_trades/position/observations fields, `OrderDepth.sell_orders` volumes are negative.

### 5. Record backtester-local caveats
- Rust engine captures conversions but does not simulate them.
- CSV ingestion does not load `observations_round_*` CSVs.
- `latest` dataset alias resolves to the highest populated round folder.
- Auto-picked trader is unsafe; always pass `--trader` explicitly.
- `make tutorial` is tutorial-only; do not mix with live round.

### 6. Assemble the Unknowns & Ambiguities table
Columns: `id`, `topic`, `statement`, `why_it_matters`, `what_would_resolve_it`. Every unknown must have a resolution path (a file to read, a dataset to inspect, a question to ask the user).

### 7. Write the handoff document
Write to `prosperity-research/01_assumptions/current_assumptions.md`, overwriting only after preserving the previous version to `prosperity-research/01_assumptions/archive/current_assumptions_<YYYY-MM-DD>.md`.

Required sections in order:
1. Round Identification
2. Products Table (algo)
3. Vouchers / Derivatives Table (if any)
4. Manual Challenges
5. Submission Interface Facts
6. Position Limits & Execution Semantics
7. Local Backtester Caveats
8. Datasets Available
9. Unknowns & Ambiguities
10. Source-of-Truth Map (which claim came from which file)
11. Do-Not-Do list (common mistakes for this round)

## Evidence requirements
- Every confirmed fact must cite its source file and section or the verbatim briefing quote.
- Every inferred fact must be labeled `inferred` with a one-line justification.
- Every unknown must appear in the Unknowns table with a resolution path.
- Do not round or paraphrase numbers (strikes, limits, expiries) without keeping the raw value alongside.

## Failure modes to avoid
- Copying old-round product names into a new round.
- Treating narrative uplinks as official.
- Inventing strike ladders when only a range is given.
- Silently dropping ambiguities to look decisive.
- Mixing tutorial products (EMERALDS, TOMATOES) with live products.
- Writing any line that suggests a trade, threshold, or parameter value.

## Guardrails
- Never propose a strategy, threshold, or parameter.
- Never claim a symbol exists in the trading interface without the user or a dataset confirming it.
- Never say "probably" without also writing `confidence: likely` and listing what would upgrade it to `confirmed`.
- Never write outside `prosperity-research/01_assumptions/`.

## Example invocation prompts
- "Use prosperity-4-round-context-ingestor to produce a Round 3 (Salvinar) context document from the official docs and the pasted briefing."
- "Use prosperity-4-round-context-ingestor to refresh current_assumptions.md after the user confirms the voucher symbol naming."
- "Use prosperity-4-round-context-ingestor to diff the new briefing against the existing Round 2 assumptions and flag conflicts."

## Concrete deliverable format
Output is one markdown file at `prosperity-research/01_assumptions/current_assumptions.md` structured exactly as section 7 above, plus the archived prior version at `prosperity-research/01_assumptions/archive/`.

## Integration
- Feeds: `prosperity-4-data-forensics`, `prosperity-4-product-classifier`, `prosperity-4-derivatives-voucher-analyst`, `prosperity-4-manual-game-theorist`, `prosperity-4-implementation-planner`, `prosperity-4-competitive-orchestrator`.
- Does not consume outputs from other skills except the prior `current_assumptions.md` snapshot.
- Must be re-run whenever a new round starts or the briefing changes materially.
