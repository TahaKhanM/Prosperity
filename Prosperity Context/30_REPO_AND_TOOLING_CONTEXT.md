# Repository and Tooling Context (Round 4)

## Scope

This file summarizes the verified repo/tooling reality at the start of
Round 4. Anything Round 1/2-specific has been archived under `archive/`.
Round 3 work is preserved alongside Round 4 because the algorithmic
products and dynamics are unchanged across the two rounds.

Use this file when tasks involve:
- choosing a backtester
- selecting datasets or trader paths
- interpreting visualizer artifacts
- using repo-local skills or role agents
- running voucher / counterparty / exotic-option analysis tooling

## Repository layout

Repository root: `/Users/tahakhan/Documents/Work/Projects/Prosperity`

Primary active workspace: `prosperity_rust_backtester/`

Key paths:
- `Data/ROUND_4/` — canonical Round 4 source data (prices + trades, with
  Mark IDs in trades). Original zip at `Data/ROUND_4.zip`.
- `Data/ROUND_4 ARIA UPLINK.txt` — Round 4 uplink (raw text).
- `Data/ROUND 4 Context.txt` — Round 4 official Notion-wiki briefing (raw).
- `Data/ROUND 4 Hints.txt` — Round 4 cinematic prompt cards (raw).
- `Data/ROUND_3/` — Round 3 source data, retained as reference.
- `Prosperity Context/New Context/` — Round 3 + Round 4 official briefings.
- `Prosperity Context/Unrefined Context/` — original uploaded source files.
- `prosperity_rust_backtester/datasets/round4/` — copy used by the backtester.
- `prosperity_rust_backtester/datasets/round3/` — Round 3 data (kept).
- `prosperity_rust_backtester/traders/Round4/` — Round 4 trader variants.
- `prosperity_rust_backtester/traders/Round3/` — Round 3 trader history.
- `prosperity_rust_backtester/scripts/round4_options/` — Round 4 voucher +
  counterparty + exotic-option toolkit.
- `prosperity_rust_backtester/scripts/round3_options/` — Round 3 toolkit
  (preserved; safe to import from round4 scripts).
- `prosperity-research/03_eda/round4/` — Round 4 EDA outputs (counterparty
  summary, price summary, headline findings).
- `prosperity-research/04_signal_notes/round4/` — alpha registry, vol
  surface, parity, counterparty findings (Round 4).
- `prosperity-research/07_manual_round/round4_aether/` — manual decision
  memos for the Aether Crystal options.
- `prosperity-research/08_playbooks/round4_strategy_playbook.md` — ranked
  alpha playbook.
- `.agents/skills/` — Round-4-active skill suite; see skills INDEX.
- `.codex/agents/` — role TOML files.
- `archive/` — prior-round artefacts (R1/R2), kept for reference only.

## Rust backtester (primary local validator)

### Position limits

Round 4 products are wired into `src/runner.rs::position_limit` (unchanged
from Round 3 — same product set):
- `HYDROGEL_PACK: 200`
- `VELVETFRUIT_EXTRACT: 200`
- `VEV_{4000..6500}: 300` each
- Legacy R1/R2 (`ASH_COATED_OSMIUM`, `INTARIAN_PEPPER_ROOT`: 80) retained
  for completeness; legacy Prosperity 3 products retained for back-compat.
- Fallback default: 100.

### Counterparty fields

The Round 4 trades CSVs include `buyer` and `seller` columns populated with
`Mark <NN>` strings. The Rust backtester ingests them into `Trade` objects
on the `market_trades` channel just like Round 3 (where they were `None`),
so trader code that reads `trade.buyer` / `trade.seller` works without
backtester changes — verify the strings are non-`None` after the first run.

### Safe defaults

- `make round4 TRADER=traders/Round4/<your_trader>.py` — explicit trader
  and dataset.
- Do **not** rely on auto-pick (`traders/latest_trader.py` does not exist
  and the scanner is nondeterministic).
- `latest` dataset alias resolves to round1 historically; do not use.
- CSV ingestion does **not** load `observations_round_*` files.
- Conversions are recorded but not simulated in positions/cash. Do not rely
  on conversion-heavy strategies in local PnL.

### Make targets

The Makefile already has `round4` and `round4-submission` targets. No
changes required to ship Round 4 — the dataset folder name (`round4`) and
the make target are already wired.

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

## Round 4 analysis toolkit (NEW)

`prosperity_rust_backtester/scripts/round4_options/`:

| Script | Purpose |
|---|---|
| `bs.py` | BS pricer, Greeks, IV solver. Pure stdlib. (Re-exported from R3.) |
| `build_voucher_panel.py` | Per-tick panel: S, V_K, intrinsic, time value, moneyness, log-moneyness, IV, for Round 4 days 1/2/3 (TTE 7/6/5). |
| `parity_scan.py` | Identity checks: floor, upper bound, monotonicity, convexity. Round 4 dataset. |
| `vol_surface_fit.py` | Quadratic smile fit in log-moneyness; ATM IV + skew + convexity + residuals per strike. TTE-indexed. |
| `counterparty_scan.py` | Per-counterparty horizon-PnL rollup with named Mark IDs. Drops the `_anon_` placeholder used in R3 and emits per-Mark, per-product, per-side stats. |
| `exotic_pricers.py` | Closed-form fair value for the Round 4 manual exotics: chooser, digital put, down-and-out put. |
| `stat_tests.py` | ρ1, Hurst, OU half-life, variance ratio, spectral peak. |

All scripts are stateless, stdlib-only, and write to
`prosperity-research/` subfolders. Safe to import from trader code *only*
during research (not on the hosted tick path).

The Round 3 toolkit at `scripts/round3_options/` is preserved and safe to
import from. New work should default to `scripts/round4_options/` because
TTE indexing differs.

## Prompting defaults

For Round 4 strategy work:
- Name the trader: `prosperity_rust_backtester/traders/Round4/<variant>.py`.
- Name the dataset: `--dataset round4` (optionally `--day 1|2|3`).
- Name the baseline: explicit path to a prior variant.
- One dominant change per iteration.
- Ask for a concrete validation step (named dataset + metric).
- Keep context pack reads to the relevant `10_/20_/30_` file.

For manual R4 work:
- Do not pretend backtester results answer the Aether Crystal optimization
  — the underlying does not appear in algo `order_depths` and there is no
  historical price file.
- Update
  `prosperity-research/07_manual_round/round4_aether/decision_memo.md` each
  time the prices in the Manual Challenge window change.

## One-paragraph handoff

The repo is a Rust-backtester-first Prosperity workspace in its Round 4
configuration. Round 1/2 artefacts sit under `archive/` and must not feed
into Round 4 traders. Round 3 trader history under `traders/Round3/` is the
starting point for Round 4 iteration; Round 3 research artefacts under
`prosperity-research/04_signal_notes/round3/` describe alphas (HYDROGEL
soft-anchor, VE wall-mid MM, voucher IV-residual, deep-ITM as VE capacity,
parity guard) that all carry over because the products are unchanged.
The new R4 work is centered on the disclosed counterparty IDs (`Mark <NN>`):
copy Mark 14, fade Mark 38, lean long VE on Mark 67. The documented Rust
tool is the primary validator but does not simulate conversions, does not
load observation CSVs, and has an unsafe auto-pick path — always pass
`--trader` explicitly.
