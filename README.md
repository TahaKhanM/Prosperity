# Prosperity

This repository is a local IMC Prosperity 4 strategy-development workspace. It
combines:

- an active Rust backtesting workspace for building and iterating traders,
- a Python backtester and visualizer for cross-checking logs and replay output,
- official round/context material,
- research notes and experiment artifacts,
- Codex/agent setup files used to guide strategy work.

If you only use one part of this repo day to day, it should usually be
[`prosperity_rust_backtester/`](./prosperity_rust_backtester/).

## What Is In This Repo

### Active strategy workspace

- [`prosperity_rust_backtester/`](./prosperity_rust_backtester/)
  - Main place for current strategy development.
  - Contains active trader files, datasets, helper scripts, Rust source and
    generated run artifacts.
  - This is the default workspace for new trading strategy work.

### Python backtester

- [`imc-prosperity-4-backtester/`](./imc-prosperity-4-backtester/)
  - Python backtester adapted for Prosperity 4.
  - Useful for log-compatible replay and cross-checking behavior.
  - Exposes the `prosperity4bt` CLI.

### Visualizer

- [`imc-prosperity-4-visualizer/`](./imc-prosperity-4-visualizer/)
  - Frontend visualizer for Prosperity logs.
  - Useful for replaying algorithm output and inspecting behavior visually.

### Official and strategy context

- [`Prosperity Context/`](./Prosperity%20Context/)
  - Official and prompt-engineering context files.
  - Includes:
    - `Official Prosperity Context.md`
    - `CHATGPT_CONTEXT_FOR_CODEX_PROMPT_ENGINEERING.md`
    - `prosperity4_claude_code_context.md`

### Research and notes

- [`prosperity-research/`](./prosperity-research/)
  - Research notes, source maps, pattern libraries, reports and experiment
    logs.
  - This is supporting material, not the main execution environment.

### Older standalone analysis material

- [`Analyser/`](./Analyser/)
  - Older notebook/script-based tutorial data exploration.
- [`Data/`](./Data/)
  - Older copied tutorial-round CSVs.

### Codex / agent support

- `.agents/`
  - Local skills and Codex-specific guidance.
  - Includes the repo-local Prosperity skill:
    `prosperity4-codex-skill`.

### Root tooling

- [`environment.yml`](./environment.yml)
  - Shared conda environment spec for the Python and research tooling in this
    repo.
- [`scripts/setup_conda_env.sh`](./scripts/setup_conda_env.sh)
  - Bootstrap script for creating or updating the root conda environment.

## Recommended Starting Point

If you are new to this repo, use this order:

1. Create the shared conda environment from the repo root.
2. Read [`prosperity_rust_backtester/README.md`](./prosperity_rust_backtester/README.md).
3. Work inside [`prosperity_rust_backtester/traders/`](./prosperity_rust_backtester/traders/).
4. Run local tutorial backtests with the Rust backtester `Makefile`.
5. Use the visualizer only when you need replay/inspection.

## Repository Layout

```text
Prosperity/
├── .agents/                         Codex skills and local agent guidance
├── AGENTS.md                        Repo-wide instructions and routing
├── Analyser/                        Older notebook/script-based analysis
├── Data/                            Older copied tutorial CSVs
├── Prosperity Context/              Official context and prompt files
├── environment.yml                  Shared conda environment
├── imc-prosperity-4-backtester/     Python backtester (prosperity4bt)
├── imc-prosperity-4-visualizer/     Visualizer frontend
├── prosperity-research/             Research notes and reports
├── prosperity_rust_backtester/      Active Rust backtester + traders + runs
└── scripts/                         Root setup helpers
```

## Environment Setup

### 1. Create the shared conda environment

From the repo root:

```bash
./scripts/setup_conda_env.sh
```

To create the environment under a different name:

```bash
./scripts/setup_conda_env.sh my-env-name
```

The script works with `conda`, `mamba` or `micromamba` and falls back to
common local conda install paths if `conda` is not already on your `PATH`.

### 2. Activate the environment

```bash
conda activate prosperity
```

### 3. macOS only: expose conda libraries for the editable Rust CLI

The editable Rust CLI installed from
[`prosperity_rust_backtester/`](./prosperity_rust_backtester/) needs the conda
environment's `lib/` directory visible at runtime on macOS:

```bash
export DYLD_FALLBACK_LIBRARY_PATH="$CONDA_PREFIX/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"
```

This is mainly needed if you want to invoke the installed `rust_backtester`
binary from the conda environment. It is not required for ordinary Python
imports like `duckdb`, `pandas`, `polars` or `prosperity4bt`.

### 4. What the conda environment contains

The shared environment is aimed at local strategy research and backtesting:

- Python 3.11
- JupyterLab
- `pandas`
- `polars`
- `duckdb`
- `pyarrow`
- `matplotlib`
- `seaborn`
- `maturin`
- `ruff`
- `mypy`
- editable installs for:
  - [`imc-prosperity-4-backtester`](./imc-prosperity-4-backtester/)
  - [`prosperity_rust_backtester`](./prosperity_rust_backtester/)

## Active Workspace: `prosperity_rust_backtester`

This is the main strategy-development environment.

Important paths:

- [`prosperity_rust_backtester/traders/`](./prosperity_rust_backtester/traders/)
  - Active trader variants.
- [`prosperity_rust_backtester/datasets/`](./prosperity_rust_backtester/datasets/)
  - Tutorial data plus round placeholders.
- [`prosperity_rust_backtester/runs/`](./prosperity_rust_backtester/runs/)
  - Generated backtest artifacts.
- [`prosperity_rust_backtester/scripts/`](./prosperity_rust_backtester/scripts/)
  - Research and diagnostics utilities.
- [`prosperity_rust_backtester/docs/`](./prosperity_rust_backtester/docs/)
  - Longer-form local documentation and generated guides.
- [`prosperity_rust_backtester/Makefile`](./prosperity_rust_backtester/Makefile)
  - Preferred command surface.
- [`prosperity_rust_backtester/README.md`](./prosperity_rust_backtester/README.md)
  - Local backtester-specific workflow details.

### How to set up `prosperity_rust_backtester`

This subproject is essentially a local checkout of the upstream Rust backtester
repo:
[GeyzsoN/prosperity_rust_backtester](https://github.com/GeyzsoN/prosperity_rust_backtester).

For this monorepo, the recommended setup is:

1. Activate the shared root conda environment.
2. Change into [`prosperity_rust_backtester/`](./prosperity_rust_backtester/).
3. Run the local diagnostics.
4. Build or run the backtester through the provided `Makefile`.

#### Recommended setup in this repo

From the repo root:

```bash
conda activate prosperity
export DYLD_FALLBACK_LIBRARY_PATH="$CONDA_PREFIX/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"  # macOS only
cd prosperity_rust_backtester
make doctor
make build
make test
```

After that, run a tutorial backtest with an explicit trader:

```bash
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py
```

#### What the setup commands do

- `make doctor`
  - Prints local environment diagnostics.
  - Especially useful on macOS when Cargo or execution-policy issues are
    causing build hangs or launch failures.
- `make build`
  - Builds the Rust binary in debug mode.
- `make test`
  - Runs Rust unit and integration tests.
- `make tutorial ...`
  - Runs the tutorial dataset bundle through the Rust backtester.

#### macOS setup details

The upstream Rust backtester is designed to work on macOS using a wrapped Cargo
command rather than your full interactive shell environment. In this checkout:

- [`scripts/cargo_local.sh`](./prosperity_rust_backtester/scripts/cargo_local.sh)
  manages the wrapped Cargo invocation,
- [`scripts/doctor_local.sh`](./prosperity_rust_backtester/scripts/doctor_local.sh)
  prints local diagnostics,
- build artifacts default to:

```bash
~/Library/Caches/rust_backtester/target
```

If you want to override the Rust target directory:

```bash
CARGO_TARGET_DIR=/path/to/target make build-release
```

On macOS you should also have:

```bash
xcode-select --install
```

and a working Rust toolchain, for example via:

```bash
curl https://sh.rustup.rs -sSf | sh
source "$HOME/.cargo/env"
```

#### Linux / WSL setup details

The upstream repo recommends WSL2 rather than native Windows shells. For this
checkout, the same advice applies:

- use Linux directly or
- use WSL2 with Ubuntu on Windows.

Native Windows PowerShell / Command Prompt is not the intended environment for
`prosperity_rust_backtester`.

#### Optional: install the Rust CLI into your local environment

If you want the standalone `rust_backtester` command available after build:

```bash
cd prosperity_rust_backtester
make install
```

In normal day-to-day use, this is optional because:

- `make tutorial`
- `make backtest`
- `make round1`
- other `make` run targets

all use `cargo run`, which builds automatically when needed.

#### Optional: install the Python package form

The root conda environment already installs
[`prosperity_rust_backtester`](./prosperity_rust_backtester/) in editable mode.
If you want to install it separately from inside the subproject itself, the
available options are:

```bash
cd prosperity_rust_backtester
make install-pip
```

or:

```bash
cd prosperity_rust_backtester
make install-uv
```

or editable with `uv`:

```bash
cd prosperity_rust_backtester
make install-uv-editable
```

#### Verifying that the backtester is working

The fastest practical verification sequence is:

```bash
cd prosperity_rust_backtester
make doctor
make build
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py DAY=-1
```

If that succeeds, the basic setup is working.

To generate fuller artifacts for inspection:

```bash
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py PERSIST=1 FLAT=1
```

That should write outputs under:

- [`prosperity_rust_backtester/runs/`](./prosperity_rust_backtester/runs/)

#### Data expectations

The Rust backtester is organized by round. In this checkout the main populated
dataset is:

- [`prosperity_rust_backtester/datasets/tutorial/`](./prosperity_rust_backtester/datasets/tutorial/)

Additional round folders exist as placeholders:

- `datasets/round1/` through `datasets/round8/`

If you add new official sample CSVs or portal submission logs, place them into
the relevant round folder instead of mixing them into the tutorial directory.

#### Important local caveat vs upstream README

The upstream backtester README assumes a bundled default trader named
`traders/latest_trader.py`.

That file is not present in this checkout, so in this repo you should prefer
explicit trader paths such as:

```bash
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py
```

instead of relying on auto-selection.

### What is inside `traders/`

This folder contains explicit named trader variants rather than a single stable
baseline file. Notable examples currently present include:

- `Original Trader.py`
- `tutorial_champion_scorer.py`
- `tutorial_overhaul_trader.py`
- `overhaul_v9_trader.py`
- `tutorial_dynamic_hybrid_trader.py`
- `tutorial_submission_frontier_trader.py`
- `tutorial_submission_frontier_v2_trader.py`
- `tutorial_submission_frontier_v3_trader.py`
- `tutorial_submission_frontier_v4_trader.py`
- `tutorial_submission_frontier_v5_trader.py`

Important local caveat:

- Some instructions inside `AGENTS.md` and subproject docs still mention
  `traders/latest_trader.py`.
- That file is not present in this checkout.
- Use an explicit trader path instead when running commands.

### What is inside `datasets/`

Current active data:

- [`datasets/tutorial/`](./prosperity_rust_backtester/datasets/tutorial/)
  - `prices_round_0_day_-2.csv`
  - `trades_round_0_day_-2.csv`
  - `prices_round_0_day_-1.csv`
  - `trades_round_0_day_-1.csv`
  - `submission.log`
  - `submission.json`

Future-round placeholders are present but mostly empty:

- `datasets/round1/` through `datasets/round8/`

### What is inside `scripts/`

Current local helper scripts include:

- [`market_discovery.py`](./prosperity_rust_backtester/scripts/market_discovery.py)
  - Market-structure discovery and product diagnostics.
- [`forensic_bundle.py`](./prosperity_rust_backtester/scripts/forensic_bundle.py)
  - Persisted artifact inspection.
- [`branch_scorecard.py`](./prosperity_rust_backtester/scripts/branch_scorecard.py)
  - Strategy comparison and run scorecards.
- [`analyze_artifacts.py`](./prosperity_rust_backtester/scripts/analyze_artifacts.py)
  - Artifact summarization.
- [`sweep_research_params.py`](./prosperity_rust_backtester/scripts/sweep_research_params.py)
  - Parameterized research sweeps.
- [`cargo_local.sh`](./prosperity_rust_backtester/scripts/cargo_local.sh)
  - Wrapped local Cargo invocation, especially for macOS.
- [`doctor_local.sh`](./prosperity_rust_backtester/scripts/doctor_local.sh)
  - Local environment diagnostics.

### What is inside `runs/`

`runs/` stores generated backtest outputs. Each run directory typically contains
at least:

- `metrics.json`
- `submission.log`

When persistence is enabled, runs may also include:

- `bundle.json`
- `activity.csv`
- `pnl_by_product.csv`
- `trades.csv`
- `combined.log`
- `manifest.json`

This folder is intentionally noisy. It is an experiment artifact store, not a
hand-curated document directory.

### What is inside `docs/`

Current local docs include:

- `docs/codex_prosperity_preparation_guide.md`
- [`docs/codex_prosperity_preparation_guide.pdf`](./prosperity_rust_backtester/docs/codex_prosperity_preparation_guide.pdf)

These are support documents for improving the strategy-development workflow,
especially when using Codex for research and implementation.

## Common Rust Backtester Workflows

All commands below are run from
[`prosperity_rust_backtester/`](./prosperity_rust_backtester/).

### Sanity and setup

```bash
make doctor
make build
make test
```

### Run the tutorial bundle with an explicit trader

```bash
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py
```

### Run one tutorial day only

```bash
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py DAY=-1
```

### Persist full artifacts for later inspection

```bash
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py PERSIST=1
```

### Flatten multi-run output into one directory

```bash
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py PERSIST=1 FLAT=1
```

### Carry state across the non-submission day files

```bash
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py CARRY=1
```

### Run direct CLI commands instead of `make`

```bash
rust_backtester \
  --trader traders/tutorial_submission_frontier_v5_trader.py \
  --dataset tutorial
```

or:

```bash
rust_backtester \
  --trader traders/tutorial_submission_frontier_v5_trader.py \
  --dataset datasets/tutorial
```

## Python Backtester: `imc-prosperity-4-backtester`

This subproject gives you a Python backtester with output that is close to the
official environment format.

The conda environment already installs it in editable mode, so once the shared
env is active you can run:

```bash
prosperity4bt prosperity_rust_backtester/traders/tutorial_submission_frontier_v5_trader.py 0
```

Useful examples:

```bash
prosperity4bt prosperity_rust_backtester/traders/tutorial_submission_frontier_v5_trader.py 0 --merge-pnl
prosperity4bt prosperity_rust_backtester/traders/tutorial_submission_frontier_v5_trader.py 0--1
prosperity4bt prosperity_rust_backtester/traders/tutorial_submission_frontier_v5_trader.py 0 --vis
```

Local caveat:

- The upstream Python backtester README still references `example/starter.py`.
- That example file is not present in this checkout.
- Use any real trader file from `prosperity_rust_backtester/traders/` instead.

When to use it:

- sanity-checking output/log compatibility,
- comparing behavior against a Python-side implementation,
- using the visualizer-friendly output pipeline.

When not to use it:

- as the default current strategy iteration loop.

For that, prefer `prosperity_rust_backtester/`.

## Visualizer: `imc-prosperity-4-visualizer`

This is a Node/Vite frontend for viewing Prosperity log output.

### Install

From [`imc-prosperity-4-visualizer/`](./imc-prosperity-4-visualizer/):

```bash
pnpm install
```

You will need:

- Node.js 22+
- `pnpm`

### Development server

```bash
pnpm dev
```

### Production build

```bash
pnpm build
pnpm preview
```

The visualizer can load:

- local `.log` files,
- a URL to a log file,
- Prosperity API data if you provide the required token.

## Official Context And Research Material

### `Prosperity Context/`

This folder is the main local source for official and semi-official competition
context. Use it before relying on older public repos or memory.

Key files:

- [`Official Prosperity Context.md`](./Prosperity%20Context/Official%20Prosperity%20Context.md)
- `CHATGPT_CONTEXT_FOR_CODEX_PROMPT_ENGINEERING.md`
- `prosperity4_claude_code_context.md`

### `prosperity-research/`

This folder contains supporting research material such as:

- source maps,
- notes on older public Prosperity repos,
- pattern libraries,
- strategy playbooks,
- evaluation framework notes,
- Codex/Claude context,
- master reports and experiment logs.

Examples:

- [`02_source_map/prosperity_source_map.md`](./prosperity-research/02_source_map/prosperity_source_map.md)
- [`03_repo_notes/`](./prosperity-research/03_repo_notes/)
- [`09_master_reports/deep_research_master_report.md`](./prosperity-research/09_master_reports/deep_research_master_report.md)

Subfolder overview:

- `01_raw_sources/`
  - raw collected material and source captures
- `02_source_map/`
  - source index and provenance map
- `03_repo_notes/`
  - notes on older public Prosperity repositories
- `04_pattern_library/`
  - reusable strategy and architecture patterns
- `05_strategy_playbooks/`
  - strategy-family notes and playbooks
- `06_eval_framework/`
  - evaluation and validation framework material
- `07_codex_skill/`
  - Codex-oriented skill and workflow material
- `08_claude_context/`
  - Claude-oriented context material
- `09_master_reports/`
  - long-form synthesis and master reports
- `10_experiment_logs/`
  - experiment notes and logs

### Round Analyzer and `Data/`

The active round analyzer now lives in the research layer:

- `prosperity-research/03_eda/round1/analysis.ipynb`
- `prosperity-research/03_eda/round1/analysis.py`

It can target `round1` or `round2` separately against the canonical raw CSVs in
the Rust dataset tree.

Raw CSVs remain authoritative in the dataset trees used by the local backtesters.
Older copied tutorial CSVs in `Data/TUTORIAL_ROUND_1/` are supporting reference
material rather than the main active workflow.

## Codex / Agent Files

This repo includes local Codex support files:

- `AGENTS.md`
- `prosperity_rust_backtester/AGENTS.md`
- `.agents/skills/prosperity4-codex-skill/`

These are for agent guidance, not runtime behavior. They matter if you are
using Codex or other agent tooling to help develop strategies in this repo.

## Suggested End-To-End Workflow

### If you want to build or improve a trader

1. Activate the root conda environment.
2. Read:
   - `AGENTS.md`
   - `prosperity_rust_backtester/AGENTS.md`
   - [`prosperity_rust_backtester/README.md`](./prosperity_rust_backtester/README.md)
3. Pick an explicit trader file from `prosperity_rust_backtester/traders/`.
4. Make a small, isolated change.
5. Run a tutorial backtest in `prosperity_rust_backtester/`.
6. Persist artifacts if you need deeper diagnosis.
7. Use the visualizer or forensic scripts to inspect behavior.

### If you want to study the tutorial data first

1. Start in:
   - [`prosperity_rust_backtester/datasets/tutorial/`](./prosperity_rust_backtester/datasets/tutorial/)
   - [`prosperity_rust_backtester/scripts/market_discovery.py`](./prosperity_rust_backtester/scripts/market_discovery.py)
2. Cross-reference older notebooks in `Analyser/`.
3. Use `forensic_bundle.py` and `branch_scorecard.py` once you have run
   candidate strategies.

### If you want to visualize a run

1. Generate a `submission.log` via either backtester.
2. Start the visualizer in `imc-prosperity-4-visualizer/`.
3. Load the `.log` file via upload or URL.

## Known Local Caveats

- `traders/latest_trader.py` is referenced in some AGENTS/docs but is not
  present in the current checkout.
- The repo-root `AGENTS.md` mentions a legacy `Trader1/` area, but that
  directory is not present in this checkout.
- The editable `rust_backtester` CLI needs the conda `lib/` path exposed on
  macOS:

  ```bash
  export DYLD_FALLBACK_LIBRARY_PATH="$CONDA_PREFIX/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"
  ```

- `runs/` contains many generated outputs; avoid treating it as curated source
  material.

## Quick Reference

### Repo root

```bash
./scripts/setup_conda_env.sh
conda activate prosperity
export DYLD_FALLBACK_LIBRARY_PATH="$CONDA_PREFIX/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"  # macOS only
```

### Active workspace

```bash
cd prosperity_rust_backtester
make doctor
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py PERSIST=1 FLAT=1
```

### Visualizer

```bash
cd imc-prosperity-4-visualizer
pnpm install
pnpm dev
```

### Python backtester

```bash
conda activate prosperity
prosperity4bt prosperity_rust_backtester/traders/tutorial_submission_frontier_v5_trader.py 0
```

## Where To Read Next

- Repo-wide guidance:
  `AGENTS.md`
- Active backtester workflow:
  [`prosperity_rust_backtester/README.md`](./prosperity_rust_backtester/README.md)
- Official competition context:
  [`Prosperity Context/`](./Prosperity%20Context/)
- Research and reports:
  [`prosperity-research/`](./prosperity-research/)
