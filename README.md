# Prosperity 4: Round 4 (GOAT) workspace

This repository is a local IMC Prosperity 4 strategy-development workspace for
the GOAT (Great Orbital Ascension Trials) phase. The competition PnL was reset
to zero at the start of Round 3; Rounds 3 and 4 PnL accumulate on the same
ledger. Round 1/2 work has been moved under `archive/` and is reference-only.

## Current round

**Round 4: Salvinar ("The More The Merrier").** Live algorithmic products
(unchanged from Round 3):
- `HYDROGEL_PACK` (delta-1, pos limit 200, oscillates ~9990–10005)
- `VELVETFRUIT_EXTRACT` (VE: delta-1 underlying, pos limit 200, ~5240)
- Ten call vouchers on VE: `VEV_{4000,4500,5000,5100,5200,5300,5400,5500,6000,6500}` (pos limit 300 each)

Voucher TTE at Round 4 start = **4 days**. Historical days 1/2/3 correspond to
TTE 7/6/5. Expiry settles cash at `max(S_T - K, 0)`.

**What is new in Round 4: the Frontier Trade Watch has disclosed counterparty
IDs.** Every other participant in `market_trades` now carries a `Mark <NN>`
identifier: historical CSVs show 7 of them: Mark 01, 14, 22, 38, 49, 55, 67.
Headline finding: **Mark 14 is the smart bot (+5.71/unit horizon-500 PnL),
Mark 38 is the bag-holder (−8.34/unit). Copy Mark 14, fade Mark 38.**

**Round 4 manual task:** Aether Crystal vanilla + 3 exotic options.
- Chooser (K=50, decision day 14, expiry 21d, auto-converts to ITM side).
- Binary put (K=40, expiry 21d, pays 10 if `S_T < 40`).
- Knockout (down-and-out) put (K=45, barrier 35, expiry 21d).
Manual is independent of algo PnL.

## Start here

1. `CLAUDE.md`: Claude Code entry point (loaded every session).
2. `AGENTS.md`: Codex entry point.
3. `Prosperity Context/00_PROSPERITY_CONTEXT_OVERVIEW.md`: source of truth map.
4. `Prosperity Context/10_ALGO_TRADING_CONTEXT.md`: Round 4 algo playbook.
5. `Prosperity Context/20_MANUAL_TRADING_CONTEXT.md`: Aether Crystal manual playbook.
6. `Prosperity Context/30_REPO_AND_TOOLING_CONTEXT.md`: backtester + tooling.
7. `prosperity-research/03_eda/round4/headline_findings.md`: counterparty
   findings + actionable bullets from the Round 4 EDA.
8. `prosperity-research/08_playbooks/round4_strategy_playbook.md`: ranked
   alpha playbook for Round 4.

## Repo layout

### Active strategy workspace
- [`prosperity_rust_backtester/`](./prosperity_rust_backtester/): Rust backtester
  (primary local validator). Key subfolders:
  - `traders/Round4/`: live trader variants (mirrors Round3 starting set).
  - `traders/Round3/`: Round 3 trader history; baselines for R4 iteration.
  - `datasets/round4/`: Round 4 price + trade CSVs (with Mark IDs).
  - `datasets/round3/`: Round 3 historical (anonymous) CSVs (kept for ref).
  - `scripts/round4_options/`: voucher + counterparty + exotic-option
    analysis toolkit.

### Secondary tools
- [`imc-prosperity-4-backtester/`](./imc-prosperity-4-backtester/): Python
  backtester (`prosperity4bt` CLI). Useful for cross-check and `--vis` auto-open.
- [`imc-prosperity-4-visualizer/`](./imc-prosperity-4-visualizer/): frontend
  visualizer. Supports official-JSON and logger-plaintext parser families.

### Official context and briefings
- [`Prosperity Context/`](./Prosperity%20Context/)
  - `New Context/`: Round 4 official doc + ARIA uplink + hint cards
    (Round 3 versions retained as `Round 3 Trading round.md` and
    `Video Transcript.pdf`).
  - `Unrefined Context/`: original upload (lower authority).

### Research and notes
- [`prosperity-research/`](./prosperity-research/)
  - `01_assumptions/`, `03_eda/round4/`, `04_signal_notes/round4/`,
    `05_execution_risk/`, `06_validation/`, `07_manual_round/round4_aether/`,
    `08_playbooks/`, `10_experiment_logs/`.
  - Round 3 research artefacts remain at `03_eda/round3/`,
    `04_signal_notes/round3/`, `07_manual_round/round3_biopods/` for
    reference (alphas often carry over).

### Skills and agents
- `.agents/skills/`: Round 4 skill suite (voucher
  analyst, counterparty-flow analyst, alpha hypothesis lab, backtest auditor,
  etc). See `.agents/skills/PROSPERITY_4_SKILLS_INDEX.md`.
- `.codex/agents/`: Codex role TOML files.

### Data
- [`Data/ROUND_4/`](./Data/ROUND_4/): canonical Round 4 source data (prices
  + trades with Mark IDs). The original zip is at `Data/ROUND_4.zip`.
- [`Data/ROUND_3/`](./Data/ROUND_3/): Round 3 source data (kept).

### Archive (reference only)
- [`archive/round1_round2/`](./archive/round1_round2/): Round 1 and Round 2
  artefacts. Do not ship logic from here into Round 4 traders.

## Common commands

```sh
# Build the backtester
( cd prosperity_rust_backtester && ./scripts/cargo_local.sh build )

# Run a trader against Round 4 day 1
( cd prosperity_rust_backtester && \
  make round4 TRADER=traders/Round4/round4_baseline_v01.py DAY=1 )

# Regenerate the voucher analytical panel for Round 4
python3 prosperity_rust_backtester/scripts/round4_options/build_voucher_panel.py

# Identity-only parity arbitrage scan
python3 prosperity_rust_backtester/scripts/round4_options/parity_scan.py

# Smile fit: ATM IV, skew, convexity per tick (Round 4 TTE indexing)
python3 prosperity_rust_backtester/scripts/round4_options/vol_surface_fit.py

# Counterparty horizon-PnL rollup with named Mark IDs
python3 prosperity_rust_backtester/scripts/round4_options/counterparty_scan.py

# Price the three R4 exotics (chooser, binary put, knockout put)
python3 prosperity_rust_backtester/scripts/round4_options/exotic_pricers.py
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

## Round 4 quick tips

- **Counterparty data is the headline alpha.** Mark 14 = copy, Mark 38 = fade,
  Mark 67 = lean long VE.
- HYDROGEL_PACK is **not** pinned at 10000: empirical mean ≈ 9992–10003.
  Use `clamp(EMA, 9980, 10010)` style soft anchor.
- VEV_6000 and VEV_6500 are stuck at ~0.5: exclude from scalping unless data
  proves otherwise.
- Deep-ITM vouchers (VEV_4000, VEV_4500) have essentially zero time value
  (delta-1 proxies for VE).
- Smile has deterministic TTE drift; use a TTE-indexed smile, not frozen
  coefficients.
- Tradeable parity is clean (0–2 violations / 10,000 ticks); ship the parity
  guard as a defensive feature, not as alpha.
- Manual exotics: replicate with vanillas first to bound fair value before
  taking outright exposure.
