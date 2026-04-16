# AGENTS.md

## Repository overview
This repository is for developing, backtesting, analyzing, and iterating IMC Prosperity 4 trading strategies.

The main top-level areas are:
- `prosperity_rust_backtester/` active strategy-development workspace
- `prosperity-research/` structured research notes, reports, and validation writeups
- `Prosperity Context/` official context files and prompt aids
- `IMC Backtester Official Logs/` downloaded official hosted backtester bundles
- `Data/` local datasets and snapshots
- `Round1AnalysisV1/` earlier exported analysis artifacts
- `imc-prosperity-4-backtester/` older Python backtester reference
- `imc-prosperity-4-visualizer/` separate visualization app
- `scripts/` repo-level helper scripts outside the Rust workspace
- `.agents/`, `.codex/`, and `.claude/` local agent tooling and prompt/config areas; touch only when the task is about repository tooling or agent behavior

## Instruction layering
- Follow this repo-root `AGENTS.md` for repository-wide routing and cleanup rules.
- When working inside `prosperity_rust_backtester/`, also follow `prosperity_rust_backtester/AGENTS.md`. The more specific file takes precedence for that subtree.
- Use the `prosperity-4-strategy-engineer` skill for reusable Prosperity strategy reasoning, market-type classification, and backtest diagnosis. Do not duplicate skill logic here.

## Source hierarchy
Use sources in this order:
1. Official Prosperity 4 round briefings and syntax/interface docs for current competition facts.
2. This repository's backtester docs, datasets, run artifacts, and official hosted logs for local workflow and evidence.
3. Older public Prosperity repos only for strategy ideas, code architecture ideas, and diagnostics patterns.

Never treat older public repos as authority on current Prosperity 4 products, rules, or hidden mechanics.

## Working map
- Repo-level orientation docs: `README.md` and `RESOURCES.md`
- Repo-level helper scripts: `scripts/`
- Active default trader entrypoint: `prosperity_rust_backtester/traders/latest_trader.py`
- Active structured traders: `prosperity_rust_backtester/traders/Round1/` and `prosperity_rust_backtester/traders/Tutorial/`
- Historical trader archive: `prosperity_rust_backtester/trader_archive/`
- Active datasets: `prosperity_rust_backtester/datasets/` with `tutorial/` plus round-organized folders such as `round1/` through `round8/`
- Generated run outputs: `prosperity_rust_backtester/runs/`
- Generated backtest console logs: `prosperity_rust_backtester/backtests/`
- Backtester docs and commands: `prosperity_rust_backtester/README.md`, `prosperity_rust_backtester/Makefile`, `prosperity_rust_backtester/docs/`, and `prosperity_rust_backtester/scripts/`
- Official-log replay and comparison tooling: `prosperity_rust_backtester/official_log_analyzer/` and `prosperity_rust_backtester/scripts/analyze_official_logs.py`
- Non-code research outputs live under `prosperity-research/`, especially:
  - `01_assumptions/` current verified assumptions
  - `04_signal_notes/` signal and alpha notes
  - `05_execution_risk/` fill, inventory, and robustness diagnostics
  - `06_validation/` benchmark and ship or reject decisions
  - `09_master_reports/` longer-form research reports
  - `10_experiment_logs/` working notes and iteration logs

## Legacy area
`Trader1/` contains an old Python backtester and older trader code. Treat it as reference only.
Do not:
- move current work into `Trader1/`
- use `Trader1/backtest.py` as the default validation path
- overwrite legacy files unless explicitly asked

## Cleanup policy
Safe-to-remove generated clutter includes:
- `**/.DS_Store`
- `**/.Rhistory`
- `**/__pycache__/`
- `**/*.pyc`
- `**/*.egg-info/`
- `output/`
- `imc-prosperity-4-visualizer/node_modules/`
- `imc-prosperity-4-visualizer/dist/`
- `prosperity_rust_backtester/backtests/*`
- `prosperity_rust_backtester/target/`
- `prosperity_rust_backtester/runs/*` except `.gitkeep`

Do not delete or rewrite downloaded official logs, datasets, or research notes unless explicitly asked.
When cleaning strategy history, prefer archiving superseded experiments into the round-specific archive area instead of deleting them.

## Repo-wide constraints
- Preserve valid Prosperity submission syntax in trader code.
- Prefer small, testable strategy changes over large rewrites.
- Keep `prosperity_rust_backtester/traders/` minimal so AI tools see only the default trader and active structured subdirectories first.
- Prefer creating a new trader variant in the round-specific work area or, for historical/reference-only code, in `prosperity_rust_backtester/trader_archive/`, rather than the root of `prosperity_rust_backtester/traders/`, unless explicitly asked otherwise.
- Do not add unsupported libraries to submission code.
- Do not rely on globals or class state persisting across `run()` calls.
- Keep `traderData` compact and purposeful.
- Do not optimize to one lucky backtest day while degrading the full tutorial bundle.
- Do not edit datasets unless explicitly asked.
- Do not delete experiment history when archiving it is sufficient.

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
- Non-code role outputs must be written under `prosperity-research/`, typically in the matching structured area such as `01_assumptions/`, `04_signal_notes/`, `05_execution_risk/`, `06_validation/`, or `10_experiment_logs/`.
- Implementation changes must be narrow, attributable, and submission-compatible.
- One strategy iteration equals one dominant change.
- No role except `strategy_engineer` may edit files under `prosperity_rust_backtester/traders/`.
