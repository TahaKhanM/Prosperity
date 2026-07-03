# Prosperity

IMC Prosperity trading-system workspace covering options pricing, market making, statistical arbitrage, research notebooks and local backtesting.

## Context

This repository contains my strategy-development workspace for IMC Prosperity. The project combines Python trading logic, a Rust backtester, market-data analysis and round-specific research notes.

**Result:** top 0.15% globally, #32 overall and #20 UK out of 22,000+ teams.

## What I Built

- Python trading strategies for multi-product market making and statistical arbitrage.
- Options-pricing research for voucher products, including Black-Scholes style fair-value analysis, implied volatility, skew and parity checks.
- Counterparty-flow analysis and execution-risk notes for deciding when to copy, fade or avoid market participants.
- A Rust backtesting workflow for faster local validation of strategy variants.
- Structured research folders for assumptions, EDA, validation, experiment logs and round playbooks.

## Technical Ideas Demonstrated

- Market-making around estimated fair values with inventory/risk controls.
- Options pricing with time-to-expiry handling, implied-volatility surfaces and parity constraints.
- Statistical analysis of historical price/trade CSVs with Python tooling.
- Backtesting and simulation-driven iteration under competition time pressure.
- Separating active strategies, archived rounds, datasets and research notes so the repo remains inspectable.

## Repository Structure

```text
.
├── prosperity_rust_backtester/     # Primary local Rust backtester and trader variants
├── prosperity-research/            # Research notes, EDA, validation, playbooks, experiment logs
├── imc-prosperity-4-backtester/    # Python backtester dependency/vendor copy
├── imc-prosperity-4-visualizer/    # Optional visualizer frontend
├── Data/                           # Round data and official CSV inputs
├── Official Replays/               # Replay/log artefacts used during validation
├── archive/                        # Earlier-round material kept for reference
└── README.md
```

## Tech Stack

- Python 3.11
- Rust 2024 edition
- pandas, NumPy, SciPy, scikit-learn, statsmodels
- Typer, orjson, jsonpickle
- Vite/React visualizer tooling

## Setup

The most complete environment is captured in `environment.yml`.

```bash
conda env create -f environment.yml
conda activate prosperity
```

The Rust backtester can also be used directly:

```bash
cd prosperity_rust_backtester
./scripts/cargo_local.sh build
```

## Example Commands

Run Rust unit tests:

```bash
cd prosperity_rust_backtester
./scripts/cargo_local.sh test
```

Run a trader against a round dataset:

```bash
cd prosperity_rust_backtester
make round4 TRADER=traders/Round4/round4_baseline_v01.py DAY=1
```

Run options/counterparty analysis scripts:

```bash
python3 prosperity_rust_backtester/scripts/round4_options/build_voucher_panel.py
python3 prosperity_rust_backtester/scripts/round4_options/parity_scan.py
python3 prosperity_rust_backtester/scripts/round4_options/vol_surface_fit.py
python3 prosperity_rust_backtester/scripts/round4_options/counterparty_scan.py
```

## Results and Evidence

- Competition placement: top 0.15% globally, #32 overall, #20 UK.
- The repo includes round-specific strategy variants, historical data, validation notes and research outputs used to iterate on trading logic.
- The strongest technical evidence is in `prosperity_rust_backtester/traders/`, `prosperity_rust_backtester/scripts/round4_options/` and `prosperity-research/`.

## Limitations

- Some datasets and logs are competition artefacts, so this is best read as a strategy-development workspace rather than a polished library.
- Local backtests are useful for iteration but do not perfectly reproduce the live exchange environment.
- Several folders are retained for provenance and post-competition analysis, not because they are active entry points.

## Future Improvements

- Add a small, deterministic smoke-test dataset for quicker reviewer validation.
- Move the most reusable pricing and signal code into a documented Python package.
- Add concise result tables for each major strategy family and validation run.

## Usage Note

This repository is public for portfolio review and educational inspection. It should not be interpreted as financial advice or production trading software.
