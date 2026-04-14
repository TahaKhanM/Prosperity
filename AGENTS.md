# AGENTS.md

## Repository overview
This repository is for developing, backtesting, and iterating IMC Prosperity 4 trading strategies.

There are two main areas:
- `prosperity_rust_backtester/` is the active workspace for current strategy development, local backtesting, and run artifacts.

## Instruction layering
- Follow this repo-root `AGENTS.md` for repository-wide routing and guardrails.
- When working inside `prosperity_rust_backtester/`, also follow `prosperity_rust_backtester/AGENTS.md`. The more specific file takes precedence for that subtree.
- Use the `prosperity-4-strategy-engineer` skill for reusable Prosperity strategy reasoning, market-type classification, and backtest diagnosis. Do not duplicate skill logic here.

## Source hierarchy
Use sources in this order:
1. Official Prosperity 4 round briefings and syntax/interface docs for current competition facts.
2. This repository's backtester docs, datasets, and run artifacts for local workflow and evidence.
3. Older public Prosperity repos only for strategy ideas, code architecture ideas, and diagnostics patterns.

Never treat older public repos as authority on current Prosperity 4 products, rules, or hidden mechanics.

## Default working locations
- Active trader files: `prosperity_rust_backtester/traders/`
- Active datasets: `prosperity_rust_backtester/datasets/`
- Active run outputs: `prosperity_rust_backtester/runs/`
- Backtester docs and commands: `prosperity_rust_backtester/README.md` and `prosperity_rust_backtester/Makefile`

## Legacy area
`Trader1/` contains an old Python backtester and older trader code. Treat it as reference only.
Do not:
- move current work into `Trader1/`
- use `Trader1/backtest.py` as the default validation path
- overwrite legacy files unless explicitly asked

## Repo-wide constraints
- Preserve valid Prosperity submission syntax in trader code.
- Prefer small, testable strategy changes over large rewrites.
- Prefer creating a new trader variant in `prosperity_rust_backtester/traders/` rather than overwriting the current best file unless explicitly asked to replace it.
- Do not add unsupported libraries to submission code.
- Do not rely on globals or class state persisting across `run()` calls.
- Keep `traderData` compact and purposeful.
- Do not optimize to one lucky backtest day while degrading the full tutorial bundle.
- Do not edit datasets unless explicitly asked.
- Do not delete old experiment files unless explicitly asked.

## Default task workflow
For normal strategy tasks:
1. Work in `prosperity_rust_backtester/`.
2. Read the more specific `prosperity_rust_backtester/AGENTS.md`.
3. Use the Prosperity skill for product reasoning and strategy design.
4. Implement the smallest defensible change.
5. Backtest locally.
6. Summarize what changed, why, how it was checked, and what should be tested next.

## Done means
A typical strategy task is done only when:
- the code remains submission-compatible,
- the change is localized and understandable,
- the relevant local backtest command has been identified or run,
- the expected effect on PnL, inventory, or execution is clearly stated,
- next validation steps are named.

## Codex multi-agent operating model

This repository uses project-scoped custom agents and role skills.

### Canonical role set
- `competition_research`
- `repo_librarian`
- `alpha_miner`
- `execution_risk`
- `strategy_engineer`
- `validator`

### Role boundaries
- Only `strategy_engineer` may edit trader code unless explicitly instructed otherwise.
- `competition_research` owns official current competition facts, syntax/interface facts, stale-assumption checks, and unknown tracking.
- `repo_librarian` owns public-repo discovery, pattern extraction, architecture notes, and stale-pattern warnings.
- `alpha_miner` owns local dataset analysis, signal discovery, regime/state slicing, and passive vs aggressive monetization mapping.
- `execution_risk` owns fill sensitivity, queue assumptions, inventory diagnostics, drawdown decomposition, and counterfactual quote studies.
- `validator` owns benchmark reruns, baseline comparisons, robustness assessment, and final ship or reject recommendation.

### Mandatory role order
1. `competition_research`
2. `repo_librarian` when external pattern search is relevant
3. `alpha_miner`
4. `execution_risk`
5. `strategy_engineer`
6. `validator`

### Non-negotiable rules
- Do all current strategy work in `prosperity_rust_backtester/`.
- Treat `Trader1/` as legacy reference only.
- Non-code role outputs must be written under `prosperity-research/`.
- Implementation changes must be narrow, attributable, and submission-compatible.
- One strategy iteration equals one dominant change.
- No role except `strategy_engineer` may edit files under `prosperity_rust_backtester/traders/`.
