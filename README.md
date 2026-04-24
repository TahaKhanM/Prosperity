# Prosperity 4: Round 3+ (GOAT) workspace

This repository is a local IMC Prosperity 4 strategy-development workspace for
the GOAT (Great Orbital Ascension Trials) phase starting Round 3. The competition
PnL was reset to zero at the start of Round 3: all prior round work has been
moved under `archive/` and is reference-only.

## Current round

**Round 3: Salvinar (Gloves Off).** Live algorithmic products:
- `HYDROGEL_PACK` (delta-1, pos limit 200, anchored near 10000)
- `VELVETFRUIT_EXTRACT` (VE: delta-1 underlying, pos limit 200, ~5250)
- Ten call vouchers on VE: `VEV_{4000,4500,5000,5100,5200,5300,5400,5500,6000,6500}` (pos limit 300 each)

Voucher TTE at Round 3 start = 5 days. Historical days 0/1/2 correspond to TTE
8/7/6. Expiry settles cash at `max(S_T - K, 0)`.

**Round 3 manual task:** Bio-Pods / Celestial Gardeners two-bid auction
(resale value 920; reserves on multiples of 5).

## Start here

1. `CLAUDE.md`: Claude Code entry point (loaded every session).
2. `AGENTS.md`: Codex entry point.
3. `Prosperity Context/00_PROSPERITY_CONTEXT_OVERVIEW.md`: source of truth map.
4. `Prosperity Context/10_ALGO_TRADING_CONTEXT.md`: Round 3 algo playbook.
5. `Prosperity Context/20_MANUAL_TRADING_CONTEXT.md`: Bio-Pods manual playbook.
6. `Prosperity Context/30_REPO_AND_TOOLING_CONTEXT.md`: backtester + tooling.
7. `prosperity-research/08_playbooks/round3_strategy_playbook.md`: ranked alpha playbook.
8. `prosperity-research/08_playbooks/prompt_library/round3_autonomous_alpha_discovery.md` -
   drop-in prompt for a full autonomous alpha hunt.

## Repo layout

### Active strategy workspace
- [`prosperity_rust_backtester/`](./prosperity_rust_backtester/): Rust backtester
  (primary local validator). Key subfolders:
  - `traders/Round3/`: live trader variants.
  - `datasets/round3/`: Round 3 price + trade CSVs.
  - `scripts/round3_options/`: voucher analysis toolkit (BS, IV fit,
    parity scan, counterparty scan, stationarity tests).

### Secondary tools
- [`imc-prosperity-4-backtester/`](./imc-prosperity-4-backtester/): Python
  backtester (`prosperity4bt` CLI). Useful for cross-check and `--vis` auto-open.
- [`imc-prosperity-4-visualizer/`](./imc-prosperity-4-visualizer/): frontend
  visualizer. Supports official-JSON and logger-plaintext parser families.

### Official context and briefings
- [`Prosperity Context/`](./Prosperity%20Context/)
  - `New Context/`: Round 3 official doc + uplink transcript.
  - `Unrefined Context/`: original upload (lower authority).

### Research and notes
- [`prosperity-research/`](./prosperity-research/)
  - `01_assumptions/`, `03_eda/round3/`, `04_signal_notes/round3/`,
    `05_execution_risk/`, `06_validation/`, `07_manual_round/round3_biopods/`,
    `08_playbooks/`, `10_experiment_logs/`.

### Skills and agents
- `.agents/skills/`: Round 3 skill suite (voucher
  analyst, alpha hypothesis lab, backtest auditor, etc). See
  `.agents/skills/PROSPERITY_4_SKILLS_INDEX.md`.
- `.codex/agents/`: Codex role TOML files.

### Data
- [`Data/ROUND_3/`](./Data/ROUND_3/): canonical Round 3 source data, including
  the "Ceci n'est pas une pipe" Magritte hint image.

### Archive (reference only)
- [`archive/round1_round2/`](./archive/round1_round2/): Round 1 and Round 2
  artefacts. Do not ship logic from here into Round 3 traders.

## Common commands

```sh
# Build the backtester
( cd prosperity_rust_backtester && ./scripts/cargo_local.sh build )

# Run a trader against Round 3 day 0
( cd prosperity_rust_backtester && \
  make round3 TRADER=traders/Round3/round3_actual_strategy_v02.py DAY=0 )

# Regenerate the voucher analytical panel
python3 prosperity_rust_backtester/scripts/round3_options/build_voucher_panel.py

# Identity-only parity arbitrage scan
python3 prosperity_rust_backtester/scripts/round3_options/parity_scan.py

# Smile fit: ATM IV, skew, convexity per tick
python3 prosperity_rust_backtester/scripts/round3_options/vol_surface_fit.py

# Counterparty horizon-PnL rollup (hunt for planted bots)
python3 prosperity_rust_backtester/scripts/round3_options/counterparty_scan.py
```

## Non-negotiable rules

- PnL reset at Round 3 start. Ignore R1/R2 traders and datasets.
- Return `(orders, conversions, traderData)` for submission compatibility.
- Use `traderData` (<50k chars) for persistence; no globals or class state.
- One dominant change per iteration; name the validation step.
- Prefer explicit `--trader` and `--dataset` on every backtest; auto-pick is
  nondeterministic in this repo.
- Conversions and observations are NOT faithfully simulated locally.
- Official written docs outrank narrative transcripts.

## Round 3 quick tips

- HYDROGEL_PACK is pinned near 10000: treat as RAINFOREST_RESIN analogue.
- VEV_6000 and VEV_6500 are stuck at ~0.5 historically: exclude from scalping
  until data proves otherwise.
- Deep-ITM vouchers (VEV_4000, VEV_4500) show essentially zero time value.
  This may be by design; exploit but validate on best-ask/best-bid, not mid.
- Smile is roughly parabolic in log-moneyness with ATM IV ~0.24, negative
  skew, positive convexity.
- Dead-band the delta hedge; every-tick rebalancing burns ~40k/day in spread.
