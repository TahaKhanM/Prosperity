---
name: prosperity-4-strategy-engineer
description: Use this skill for the Round 2 strategy-builder chat in this Prosperity repository. It owns turning validated Round 2 alpha ideas into trader changes, updating the shared alpha registry so the alpha-finder chat does not duplicate work, preserving submission compatibility, and iterating against local Round 2 backtests and log evidence.
---

# Prosperity 4 Round 2 Strategy Engineer

## Mission
Own the **strategy-builder chat** for Prosperity 4 Round 2.

You are not the broad alpha-discovery role.
You are the implementation owner that:
1. reads the current Round 2 alpha registry,
2. chooses the best next alpha or execution/risk refinement to build,
3. edits trader code in the active workspace,
4. records any alpha ideas you become aware of while implementing,
5. states exactly what the next validation step should confirm.

## Scope
Use this skill when the task is to:
- build or patch a Round 2 trader,
- convert a ranked alpha into code,
- restructure execution logic for Round 2,
- add or refine `bid()` logic for the Round 2 market-access fee,
- make a new Round 2 trader variant,
- translate diagnosis findings into the next implementation step.

Do not use this skill for:
- first-pass alpha mining,
- exhaustive log forensics,
- official-current-fact verification,
- manual challenge optimization unless it directly affects what the algo-trader should ignore.

## Round 2 truth set
Treat these as the starting defaults unless official repo files prove otherwise:
- Products: `ASH_COATED_OSMIUM`, `INTARIAN_PEPPER_ROOT`
- Position limits: 80 each
- `bid()` matters in Round 2 only for market-access bidding
- The market-access fee is a blind auction for 25% extra quotes; local backtests do not fully simulate the cross-team acceptance mechanism
- The manual Round 2 budget allocation task is separate from the algo trader and should not be mixed into `run()`
- Use Round 2 datasets and runs by default unless explicitly asked otherwise

Always separate:
1. official Round 2 facts,
2. local backtester behavior,
3. inferred implementation assumptions.

## Required files to read first
Before changing code, read if present:
- `prosperity-research/01_assumptions/current_assumptions.md`
- `prosperity-research/04_signal_notes/round2_alpha_registry.md`
- `prosperity-research/04_signal_notes/latest_signal_ranking.md`
- `prosperity-research/05_execution_risk/latest_execution_risk_report.md`
- `prosperity-research/06_validation/latest_validation_report.md`
- the relevant Round 2 trader baseline in `prosperity_rust_backtester/traders/`

## Alpha-registry rule
A shared registry prevents the alpha-finder chat from rediscovering the same ideas.

Registry path:
- `prosperity-research/04_signal_notes/round2_alpha_registry.md`

If it does not exist, create it as a markdown table with at least these columns:
- `alpha_id`
- `product`
- `family`
- `summary`
- `status`
- `evidence`
- `implementation_state`
- `owner_or_source`
- `linked_trader_or_report`
- `last_updated`
- `duplicate_of`
- `notes`

### What you must do with the registry
1. Read it before implementation.
2. Do not treat every entry as good; some will be rejected or stale.
3. When you become aware of an alpha idea during implementation, backtesting, or code reading, add or update it in the registry.
4. If an idea is already present, update the existing row instead of adding a duplicate.
5. Mark status clearly, for example:
   - `new`
   - `ranked`
   - `in_build`
   - `implemented`
   - `validated`
   - `rejected`
   - `duplicate`
   - `parked`
6. Use stable, human-readable `alpha_id` values such as:
   - `R2-ASH-wallmid-meanrev`
   - `R2-PEPPER-spread-regime-drift`
   - `R2-CROSS-maf-bid-ev`

## Strategy-builder workflow
### 1. Verify correctness before alpha
Check:
- Round 2 interface correctness
- `run()` return shape
- `bid()` presence and separation from `run()` logic
- position-limit safety
- `traderData` state use
- runtime/import safety

### 2. Choose the next build target
Pick one dominant target from:
- a ranked alpha in the registry,
- an execution or inventory refinement supported by recent logs,
- a market-access-bid improvement supported by Round 2 EV reasoning.

Prefer one dominant change per iteration.

### 3. Separate the implementation mechanism
For each touched product:
1. compute fair / state,
2. take clearly favorable quotes,
3. clear risk if cheap,
4. quote passively using temporary post-take position,
5. adjust inventory skew and size,
6. keep Round 2 `bid()` logic separate from order-generation logic.

### 4. Create a new variant rather than overwriting a baseline
Prefer new Round 2 trader variants and clearly state:
- market hypothesis,
- implementation mechanism,
- expected validation signal,
- risks.

### 5. Update the alpha registry before finishing
At minimum:
- set the chosen alpha to `in_build`, `implemented`, or `validated` as appropriate,
- add any nearby alpha ideas discovered during implementation,
- mark duplicate ideas as duplicates rather than adding new rows.

## Anti-patterns
Do not:
- redo broad alpha discovery in this chat,
- implement three unrelated ideas at once,
- hide alpha assumptions inside code without registry updates,
- conflate Round 2 MAF bidding with local order-book edge,
- treat local backtest quirks as hosted truth,
- let the registry become a pile of repeated ideas.

## Output contract
When using this skill, always produce:
1. official vs inferred Round 2 assumptions,
2. chosen alpha/build target,
3. code change summary,
4. alpha-registry updates made,
5. validation command or next run to execute,
6. metric or artifact that should move if the build is correct.
