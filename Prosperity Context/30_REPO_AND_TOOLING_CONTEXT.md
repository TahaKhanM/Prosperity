# Repository and Tooling Context (Round 3+)

## Scope

This file summarizes the verified repo/tooling reality at the start of
Round 3. Anything Round 1/2-specific has been archived under `archive/`.

Use this file when tasks involve:
- choosing a backtester
- selecting datasets or trader paths
- interpreting visualizer artifacts
- using repo-local skills or role agents
- running voucher analysis tooling

## Repository layout

Repository root: `/Users/tahakhan/Documents/Work/Projects/Prosperity`

Primary active workspace: `prosperity_rust_backtester/`

Key paths:
- `Data/ROUND_3/` — canonical Round 3 source data (prices + trades + hint image).
- `Prosperity Context/New Context/` — Round 3 official briefing + transcript.
- `Prosperity Context/Unrefined Context/` — original uploaded source files.
- `prosperity_rust_backtester/datasets/round3/` — copy used by the backtester.
- `prosperity_rust_backtester/traders/Round3/` — Round 3 trader variants.
- `prosperity_rust_backtester/scripts/round3_options/` — voucher analysis toolkit.
- `prosperity-research/03_eda/round3/` — EDA outputs (voucher panel, etc.).
- `prosperity-research/04_signal_notes/round3/` — parity, smile coeffs, etc.
- `prosperity-research/07_manual_round/round3_biopods/` — manual decision memos.
- `.agents/skills/` — Round-3-active skill suite; see skills INDEX.
- `.codex/agents/` — role TOML files.
- `archive/` — prior-round artefacts (R1/R2), kept for reference only.

## Rust backtester (primary local validator)

### Position limits

Round 3 products are wired into `src/runner.rs::position_limit`:
- `HYDROGEL_PACK: 200`
- `VELVETFRUIT_EXTRACT: 200`
- `VEV_{4000..6500}: 300` each
- Legacy R1/R2 (`ASH_COATED_OSMIUM`, `INTARIAN_PEPPER_ROOT`: 80) retained
  for completeness; legacy Prosperity 3 products retained for back-compat.
- Fallback default: 100.

### Safe defaults

- `make round3 TRADER=traders/Round3/your_trader.py` — explicit trader and
  dataset.
- Do **not** rely on auto-pick (`traders/latest_trader.py` does not exist and
  the scanner is nondeterministic).
- `latest` dataset alias resolves to round1 historically; do not use.
- CSV ingestion does **not** load `observations_round_*` files.
- Conversions are recorded but not simulated in positions/cash. Do not rely
  on conversion-heavy strategies in local PnL.

### Artifact modes

- `none` → `metrics.json`
- `submission` → `metrics.json`, `submission.log`
- `diagnostic` → `metrics.json`, `bundle.json`
- `full` → `metrics.json`, `bundle.json`, `submission.log`, `activity.csv`,
  `pnl_by_product.csv`, `combined.log`, `trades.csv`

## Python backtester

Secondary: `imc-prosperity-4-backtester/`. Use when you specifically want
`prosperity4bt` CLI behavior, plaintext logger output, or `--vis` auto-open.
Caveats match the Rust engine: conversions not simulated, observations
absent from CSV; unknown-product fallback limit = 50 (so unknown VEV strikes
would be under-sized here — always validate product list).

## Visualizer

`imc-prosperity-4-visualizer/` supports two parser families:
1. Official-style JSON payloads (`activitiesLog`).
2. Logger-style plaintext (`Sandbox logs:` / `Activities log:`).

Rules:
- Do not upload `.zip` bundles.
- Use Rust `combined.log` for rich local inspection.
- Use `submission.log` when official-style JSON suffices.
- Do not stitch multi-run bundles as primary visualizer inputs.

## Voucher analysis toolkit

`prosperity_rust_backtester/scripts/round3_options/`:

| Script | Purpose |
|---|---|
| `bs.py` | BS pricer, Greeks, IV solver. Pure stdlib. |
| `build_voucher_panel.py` | Per-tick panel: S, V_K, intrinsic, time value, moneyness, log-moneyness, IV. |
| `parity_scan.py` | Identity checks: floor, upper bound, monotonicity, convexity. |
| `vol_surface_fit.py` | Quadratic smile fit in log-moneyness; ATM IV + skew + convexity + residuals per strike. |
| `counterparty_scan.py` | Per-counterparty horizon-PnL rollup. |
| `stat_tests.py` | ρ1, Hurst, OU half-life, variance ratio, spectral peak. |

All scripts are stateless, stdlib-only, and write to
`prosperity-research/` subfolders. Safe to import from trader code *only*
during research (not on the hosted tick path).

## Prompting defaults

For Round 3 strategy work:
- Name the trader: `prosperity_rust_backtester/traders/Round3/<variant>.py`.
- Name the dataset: `--dataset round3` (optionally `--day 0|1|2`).
- Name the baseline: explicit path to a prior variant.
- One dominant change per iteration.
- Ask for a concrete validation step (named dataset + metric).
- Keep context pack reads to the relevant `10_/20_/30_` file.

For manual R3 work:
- Do not pretend backtester results answer the Bio-Pods optimization.
- Update `prosperity-research/07_manual_round/round3_biopods/decision_memo.md`
  each time the bid changes.

## One-paragraph handoff

The repo is a Rust-backtester-first Prosperity workspace in its Round 3
(GOAT) configuration. Round 1/2 artefacts sit under `archive/` and must not
feed into Round 3 traders. Active strategy work happens in
`prosperity_rust_backtester/traders/Round3/` with explicit `--dataset round3`
runs; voucher research uses the stateless toolkit under
`scripts/round3_options/`. The documented Rust tool is the primary validator
but does not simulate conversions, does not load observation CSVs, and has
an unsafe auto-pick path — always pass `--trader` explicitly.
