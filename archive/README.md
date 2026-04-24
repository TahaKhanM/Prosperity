# Archive: pre-Round 3 artefacts

Everything under this directory is from Round 1 and Round 2 of Prosperity 4,
before the PnL reset that kicks off the GOAT (Round 3+) phase. It is preserved
for reference only and must not be imported into Round 3 traders or research.

## Why this folder exists

Round 3 (`Salvinar`, "Gloves Off") starts a new competition phase. The official
Round 3 briefing states: "all teams begin with zero PnL and the leaderboard is
reset." Keeping the old work in the live paths would have polluted Round 3
traders (different products, different position limits, different mechanics).

## Layout

- `round1_round2/context/`: stale round-specific context docs
  (`Official Prosperity Context Round 1.md`, `Prosperity Round 2.md`,
  `Default_A.R.I.A Uplink_ Round 2.txt`, `ROUND1_PROMPT_HINTS_CONTEXT.md`).
- `round1_round2/data_zips/`: original Round 1 and Round 2 competition data
  (zipped and unpacked), kept as an audit trail.
- `round1_round2/datasets/round{1,2}/`: copies of the CSVs that used to live
  under `prosperity_rust_backtester/datasets/`.
- `round1_round2/manual/round2_manual_research/`: the `fix_speed.ipynb` and
  `v1.ipynb` workbooks for the Round 2 Invest & Expand budget challenge.
- `round1_round2/research/`: the `03_eda/round1`, `04_signal_notes/round{1,2}`,
  `05_execution_risk/*`, `06_validation/*`, `07_manual_round{1,2}*` trees that
  were rendered stale by the PnL reset.
- `round1_round2/runs/`: 161+ historical backtest / bench artefacts from
  Round 1 and Round 2 trader development.
- `round1_round2/scripts/`: `round1_ash_*` / `round1_benchmark.py` /
  `round1_exact_control.py` scripts that only work on the old products.
- `round1_round2/skills/`: `prosperity4-round2-*` skill suite and the
  `round2_autopilot.toml` Codex role.
- `round1_round2/traders/`: all ASH_COATED_OSMIUM / INTARIAN_PEPPER_ROOT
  trader variants.

## Rules for agents

- **Never** edit anything under `archive/`.
- **Never** import a trader or script from `archive/` into a Round 3
  submission path.
- When in doubt, treat this tree as git-blame history, not working code.

## If you need an old behavior

If you find yourself wanting a specific bit of Round 1/2 logic in Round 3:
1. Confirm the intent matches a Round 3 product's mechanics.
2. Rewrite it from scratch inside `prosperity_rust_backtester/traders/Round3/`,
   citing the archived file in a short comment.
3. Do not `import` from the archive path.
