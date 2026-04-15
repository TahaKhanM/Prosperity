# Prosperity 4 Strategy Context For A New Codex Instance

Current note:

- This file is older and contains tutorial-era context.
- For current Round 1 work, start with `CODEX_ROUND1_STRATEGY_CONTEXT.md`.

This file is a handoff for a fresh Codex instance working in this repository.

Layout note:
- active traders now live under `traders/`
- historical tutorial traders referenced in this document were moved to `trader_archive/Tutorial/archive/`
- historical Round 1 traders, probes, and research traders were moved to `trader_archive/Round1/`

It is meant to answer:
- where to work
- what the important files are
- how to run the backtester
- what has already been tested
- what the evidence says about the tutorial-round products
- which current traders are useful baselines
- what failed, what worked, and what the next experiments should target

This document is intentionally evidence-driven. Do not assume the current best strategy family is near-optimal.

## 1. Repository Rules And Working Location

Primary workspace:
- `prosperity_rust_backtester/`

Do not use as primary workspace:
- `Trader1/` is legacy reference only

Follow these instructions first:
- repo root: `../AGENTS.md`
- subtree: `AGENTS.md` in this directory

Important repo guidance:
- Preserve official Prosperity submission compatibility.
- Do not overwrite benchmark traders unless explicitly asked.
- Prefer new clearly named variants under `traders/Round1/work/` unless the file is becoming the new default trader.
- Use the Rust backtester here, not `Trader1/backtest.py`.
- Keep `traderData` compact and intentional.
- Do not add unsupported libraries.
- Do not optimize one lucky slice while hiding worse full-bundle behavior.

If available in the environment, use the `prosperity-4-strategy-engineer` skill. Its job is:
- product classification
- fair-value hypothesis
- separating taking from making
- diagnosing PnL, inventory, and fill quality

## 2. Current Directory Map

Key directories:
- `traders/`: active submission-compatible traders
- `datasets/`: tutorial data plus round folders
- `runs/`: persisted backtest artifacts
- `scripts/`: research and diagnostic utilities
- `README.md`: backtester usage
- `Makefile`: preferred command surface

Current tutorial data actually available:
- `datasets/tutorial/prices_round_0_day_-2.csv`
- `datasets/tutorial/trades_round_0_day_-2.csv`
- `datasets/tutorial/prices_round_0_day_-1.csv`
- `datasets/tutorial/trades_round_0_day_-1.csv`
- `datasets/tutorial/submission.json`
- `datasets/tutorial/submission.log`

There are round folders, but for this research loop the validated work used tutorial data only.

## 3. Submission / Simulator Constraints

Any final trader must:
- expose a valid `Trader` class
- implement `run(self, state: TradingState)`
- return `(result, conversions, traderData)`
- use negative quantities for sell orders
- enforce aggregate worst-case position-limit safety
- use only compact `traderData`
- avoid unsupported dependencies

Tutorial products:
- `EMERALDS`
- `TOMATOES`

Tutorial position limits:
- `EMERALDS`: 80
- `TOMATOES`: 80

## 4. How To Run The Backtester

Run from this directory:

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester
```

Common commands:

```bash
make tutorial TRADER=trader_archive/Tutorial/archive/improved_final_trader.py
make tutorial TRADER=trader_archive/Tutorial/archive/improved_final_trader.py PERSIST=1 FLAT=1 PRODUCTS=full
make tutorial TRADER=trader_archive/Tutorial/archive/improved_final_trader.py CARRY=1 PERSIST=1 FLAT=1 PRODUCTS=full
```

Direct CLI:

```bash
./target/release/rust_backtester --trader trader_archive/Tutorial/archive/improved_final_trader.py --dataset tutorial --persist --flat --products full --run-id baseline-improved-final
```

Useful flags:
- `--persist`: write full artifacts
- `--flat`: one bundle directory for multi-run outputs
- `--carry`: carry positions / trades / state across non-submission day datasets
- `--products full`: print all product PnL rows

Artifact modes:
- no `--persist`: `metrics.json` + `submission.log`
- `--persist`: full artifact set including `bundle.json`, `trades.csv`, `activity.csv`, `pnl_by_product.csv`, `combined.log`

### Artifact files worth inspecting

For a persisted run:
- `*-metrics.json`: headline PnL, trade count, product totals
- `*-bundle.json`: timeline-level replay bundle, best source for inventory/fill forensics
- `*-trades.csv`: trade-level output
- `*-activity.csv`: state/activity view
- `*-pnl_by_product.csv`: product time series
- `combined.log`: stitched logs

## 5. Research / Diagnostic Scripts Added

### `scripts/market_discovery.py`
Purpose:
- raw tutorial market structure analysis directly from dataset files

What it computes:
- mid statistics
- spread distribution
- microprice delta stats
- imbalance stats
- return magnitudes
- future correlation of `micro_delta`, `imbalance`, `ret1`, `z20`, `spread`
- quote-distance opportunity counts

Run:

```bash
python3 scripts/market_discovery.py --dataset datasets/tutorial
python3 scripts/market_discovery.py --dataset datasets/tutorial --json
```

### `scripts/branch_scorecard.py`
Purpose:
- summarize multiple persisted run directories into one comparable table

What it computes:
- total PnL
- product PnL
- own trades
- TOMATOES inventory min/max/final
- average absolute TOMATOES inventory
- time near `abs(pos) >= 60`
- product drawdown
- average future edge after fills

Run:

```bash
python3 scripts/branch_scorecard.py baseline-improved-final reference-overhaul champion-scorer champion-robust carry-baseline-improved-final carry-reference-overhaul carry-champion-scorer carry-champion-robust
```

### `scripts/forensic_bundle.py`
Purpose:
- bundle-level fill classification and future-edge analysis

What it computes:
- passive vs aggressive fills
- fill counts and units
- position path stats
- drawdown
- average future edge at h5 and h20
- missed favorable edge counts

### `scripts/sweep_research_params.py`
Purpose:
- bounded parameter sweep over TOMATOES signal/take/passive settings using `traders/research_param_trader.py`

Note:
- a sorter bug in this script was fixed by sorting on numeric tuple prefixes only

## 6. Current Trader Map

### Historical / baseline traders

`traders/Original Trader.py`
- simple inside-spread market maker for both products
- size 5 both sides
- very little product-specific logic
- robust but blind

`traders/prosperity_best_variant.py`
- EMERALDS fixed-anchor ladder around `10000`
- TOMATOES micro/mid fair with EMA and fair-centered quoting
- useful as a historical branch, not a final answer

`traders/final_combined_trader.py`
- EMERALDS from `prosperity_best_variant.py`
- TOMATOES from `Original Trader.py`
- robust reference family before signal-heavy TOMATOES variants

`traders/improved_final_trader.py`
- scorer-style baseline
- EMERALDS unchanged from strong anchored ladder family
- TOMATOES uses signal fair:
  - micro component
  - 1-tick return reversion
  - rolling deviation reversion
  - active taking and passive inside quotes
- highest local tutorial submission score among tested named baselines
- not robust in carry

`traders/tutorial_overhaul_trader.py`
- robustness-oriented TOMATOES hybrid
- lower TOMATOES soft cap
- reduced directional persistence
- strong carry / day stability

### Branch traders from the orthogonal search

`traders/branch_anchor_passive_trader.py`
- passive-only / low-prediction branch

`traders/branch_hybrid_selective_trader.py`
- selective active-taking hybrid branch

`traders/branch_regime_switch_trader.py`
- spread / imbalance regime-gated branch

`traders/branch_dynamic_fair_trader.py`
- dynamic fair-centered branch

`traders/branch_risk_first_trader.py`
- low-inventory / aggressive flattening branch

### Final champion variants

`traders/tutorial_champion_scorer.py`
- scorer-max variant from the research loop
- slightly beats the local submission baseline
- not recommended as the robust default

`traders/tutorial_champion_robust.py`
- robust variant from the research loop
- best validated carry / inventory profile among the tested final variants

## 7. Validated Market Findings

### EMERALDS

Using `scripts/market_discovery.py`:
- mean mid: `9999.998`
- std: `0.7201`
- range: `9996.0` to `10004.0`
- spread is overwhelmingly `16`, sometimes `8`
- anchored/stationary behavior is clear

Interpretation:
- EMERALDS should be treated as anchored market making around `10000`
- fixed-anchor fair value is justified locally
- most upside is already extracted by the current ladder family

Important caution:
- the raw correlation numbers for EMERALDS are large, but they do not translate into a better practical strategy than the anchored ladder once spread structure and execution are considered
- do not overreact to those raw signal correlations

### TOMATOES

Using `scripts/market_discovery.py`:
- mean mid: `4992.6031`
- std: `18.9206`
- range: `4946.5` to `5036.0`
- spread mostly `13` / `14`, with occasional tighter regimes

Future mid correlation summary:
- h1:
  - `micro_delta`: `0.339`
  - `imbalance`: `0.3212`
  - `ret1`: `-0.4218`
  - `z20`: `-0.3662`
- h5:
  - `micro_delta`: `0.2726`
  - `imbalance`: `0.2576`
  - `ret1`: `-0.3413`
  - `z20`: `-0.3106`

Interpretation:
- TOMATOES is a hybrid product
- it is not a fixed-anchor market like EMERALDS
- there is real short-horizon information in:
  - book imbalance / microprice continuation
  - return / deviation mean reversion
- however, that signal is not strong enough to replace passive spread capture as the main edge

Most important practical takeaway:
- passive inside-spread quoting is the durable core edge
- predictive logic is best used to gate or bias quoting, not to justify large directional accumulation

## 8. Main Ablation Findings

These findings came from `traders/research_param_trader.py`, `scripts/sweep_research_params.py`, and persisted bundle inspection.

### High-signal ablation table

| Variant | D-2 | D-1 | Submission | TOM Submission |
|---|---:|---:|---:|---:|
| simple inside no fair | 15177.0 | 14302.0 | 2467.0 | 1417.0 |
| simple inside edge2 | 15208.0 | 14035.0 | 2516.5 | 1466.5 |
| signal passive only | 15134.0 | 14617.0 | 2511.5 | 1461.5 |
| signal active only | 7515.0 | 5172.0 | 1375.0 | 325.0 |
| signal take2 submission-heavy | 15539.5 | 13463.0 | 2834.5 | 1784.5 |
| signal active + passive take2.5 | 15231.0 | 14522.0 | 2653.5 | 1603.5 |
| micro EMA fair-centered | 13084.0 | 13034.0 | 2200.5 | 1150.5 |
| softcap25 | 15089.0 | 15027.0 | 2572.0 | 1522.0 |
| softcap35 | 15263.5 | 14870.0 | 2653.5 | 1603.5 |

### What these ablations mean

1. Passive inside-spread TOMATOES quoting is the main edge.
2. Active-only TOMATOES trading is destructive.
3. Fair-centered micro/EMA quoting is weak on this tutorial bundle.
4. Signal fair helps mostly by improving passive quote selection.
5. High submission PnL comes from a more aggressive active-taking variant, but that same mechanism hurts robustness.
6. Lower TOMATOES soft caps strongly improve day-level and carry behavior.

## 9. Branch Tournament Results

### Persisted run IDs

Primary comparison runs created in `runs/`:
- `baseline-improved-final`
- `reference-overhaul`
- `branch-anchor_passive`
- `branch-hybrid_selective`
- `branch-regime_switch`
- `branch-dynamic_fair`
- `branch-risk_first`
- `carry-baseline-improved-final`
- `carry-reference-overhaul`
- `carry-branch-anchor_passive`
- `carry-branch-hybrid_selective`
- `carry-branch-regime_switch`
- `carry-branch-dynamic_fair`
- `carry-branch-risk_first`
- `champion-scorer`
- `champion-robust`
- `carry-champion-scorer`
- `carry-champion-robust`

### Tournament summary

| Trader | D-2 | D-1 | Submission | Carry | Read |
|---|---:|---:|---:|---:|---|
| improved_final | 15539.5 | 13463.0 | 2834.5 | 27777.0 | scorer baseline |
| tutorial_overhaul | 15263.5 | 14870.0 | 2653.5 | 29435.0 | robustness reference |
| branch_anchor_passive | 14574.5 | 14278.0 | 2441.5 | 28493.0 | safe, capped |
| branch_hybrid_selective | 15080.0 | 14374.0 | 2653.5 | 28007.0 | decent, not best |
| branch_regime_switch | 14871.0 | 14750.0 | 2470.0 | 29207.0 | robust-ish |
| branch_dynamic_fair | 13077.0 | 13121.0 | 2205.5 | 25814.0 | rejected |
| branch_risk_first | 13768.0 | 13798.0 | 2240.0 | 27408.0 | too conservative |

Key takeaway:
- no orthogonal branch beat the current scorer baseline on both score and robustness
- the branch search still mattered because it ruled out whole families:
  - dynamic fair-centered TOMATOES
  - overly conservative risk-first TOMATOES

## 10. Final Champion Variants

### `traders/tutorial_champion_scorer.py`

What it is:
- scorer-max local tutorial variant
- anchored EMERALDS unchanged
- TOMATOES signal fair with:
  - lower micro weight (`0.25`)
  - return reversion (`-0.5`)
  - rolling deviation reversion (`-0.4`)
  - no TOMATOES inventory skew

Validated performance:
- D-2: `15781.0`
- D-1: `13099.0`
- submission: `2836.5`
- carry: `27063.0`

Why it is not the recommended default:
- gains only `+2.0` on submission vs `improved_final_trader.py`
- but becomes much more inventory-heavy
- TOMATOES inventory saturates to `+80`
- TOMATOES carry risk becomes unacceptable

Important red-team metrics:
- day -1 TOMATOES avg abs position: `59.73`
- day -1 TOMATOES near60 ticks: `6448`
- day -2 TOMATOES final position: `80`
- carry TOMATOES avg abs position: `60.18`
- carry TOMATOES near60 ticks: `12396`

### `traders/tutorial_champion_robust.py`

What it is:
- robust TOMATOES hybrid with lower soft cap
- anchored EMERALDS unchanged
- TOMATOES settings:
  - micro weight `0.5`
  - ret1 weight `-0.6`
  - z20 weight `-0.3`
  - take edge `2.5`
  - passive edge `1.5`
  - inventory skew `0.01`
  - soft cap `25`

Validated performance:
- D-2: `15089.0`
- D-1: `15027.0`
- submission: `2572.0`
- carry: `29456.0`

Why it matters:
- slightly beats `tutorial_overhaul_trader.py` on carry
- improves TOMATOES carry PnL and lowers risk metrics
- remains clearly below scorer-max submission variants

Important risk metrics:
- carry TOMATOES avg abs position: `13.30`
- carry TOMATOES near60 ticks: `0`
- carry TOMATOES drawdown: `638.0`

## 11. Artifact-Level Findings

Using `scripts/forensic_bundle.py`:

### Submission scorer baseline vs scorer champion

`improved_final_trader.py` submission TOMATOES:
- pnl: `1784.5`
- fills: `73`
- units: `263`
- pos range: `[-11, 52]`
- avg abs pos: `8.5`
- aggressive buy units: `32`
- future edge h5 avg: `18.88`

`tutorial_champion_scorer.py` submission TOMATOES:
- pnl: `1786.5`
- fills: `73`
- units: `263`
- same position stats as baseline on submission slice
- future edge h5 avg: `18.90`

Interpretation:
- the scorer champion’s local submission gain is tiny
- it is not coming from a meaningful structural change in submission behavior
- the real difference shows up in multi-day behavior, where it becomes much worse

### Robust champion carry TOMATOES

`tutorial_champion_robust.py` carry TOMATOES:
- pnl: `14945.0`
- fills: `747`
- units: `2625`
- pos range: `[-27, 29]`
- final pos: `-1`
- avg abs pos: `13.3`
- near60 ticks: `0`
- drawdown: `638.0`
- future edge h5 avg: `19.99`

Interpretation:
- robust champion is behaving like a controlled passive spread-capture engine with light active support
- this is the cleanest validated TOMATOES behavior found in the loop

## 12. High-Level Conclusions

### What is strongly supported by evidence

1. EMERALDS is locally close to solved with anchored market making.
2. TOMATOES is the dominant source of both upside and instability.
3. Passive spread capture is the real base edge in TOMATOES.
4. Active taking increases score only when it also increases fragility.
5. The prior optimization loop was trapped in a TOMATOES aggressiveness frontier, not just missing a better threshold.

### What is not supported

1. A dynamic fair-centered TOMATOES strategy replacing passive inside-spread quoting.
2. Active-only TOMATOES trading.
3. A clean single trader that beats both the scorer baseline and the robustness reference on this tutorial bundle using the same current feature set.

## 13. Recommended Starting Point For The Next Codex Instance

### If optimizing for raw local tutorial submission score
Start from:
- `traders/improved_final_trader.py`
- `traders/tutorial_champion_scorer.py`

But do not trust the scorer champion without strong new evidence. It is a red-team failure on robustness.

### If optimizing for repeatable tutorial robustness
Start from:
- `traders/tutorial_overhaul_trader.py`
- `traders/tutorial_champion_robust.py`

`tutorial_champion_robust.py` is the better robust foundation currently validated in this repo.

## 14. Best Next Experiments

These are the highest-value next steps based on the completed research loop.

1. Asymmetric TOMATOES active thresholds by inventory sign
- hypothesis: retain some submission upside without long inventory drift
- success signal: submission stays near `improved_final`, carry avg abs position drops materially
- risk: removes the exact aggressive buys that created the scorer edge

2. Spread-regime-based passive sizing
- hypothesis: size up passive quotes only in wide, balanced regimes
- success signal: higher TOMATOES carry PnL without worse drawdown
- risk: more adverse passive fills

3. Inventory liquidation ladder instead of hard soft-cap blocking
- hypothesis: flatten earlier without abandoning too much edge
- success signal: lower final and average inventory with less submission sacrifice than softcap25
- risk: pays spread too often

4. Post-fill adverse-selection filter for active taking
- hypothesis: allow active fills only when h5/h20 forward edge is strong for that regime
- success signal: higher future-edge average per aggressive fill, lower carry damage
- risk: active fills become too rare to matter

5. Cleaner regime-gated TOMATOES hybrid
- hypothesis: split TOMATOES behavior into:
  - wide-spread passive regime
  - narrow-spread cautious regime
  - only limited active taking in a confirmed favorable regime
- success signal: robust PnL improves while inventory stays bounded
- risk: extra complexity with little real gain

## 15. Practical Workflow Recommendation

When continuing from here:

1. Read this file.
2. Read both AGENTS files.
3. Read:
   - `trader_archive/Tutorial/archive/improved_final_trader.py`
   - `trader_archive/Tutorial/archive/tutorial_overhaul_trader.py`
   - `trader_archive/Tutorial/archive/tutorial_champion_scorer.py`
   - `trader_archive/Tutorial/archive/tutorial_champion_robust.py` if present in your local copy
4. Run:

```bash
python3 scripts/market_discovery.py --dataset datasets/tutorial
python3 scripts/branch_scorecard.py baseline-improved-final reference-overhaul champion-scorer champion-robust carry-baseline-improved-final carry-reference-overhaul carry-champion-scorer carry-champion-robust
```

5. Use `scripts/forensic_bundle.py` on the run you are targeting.
6. Create a new trader variant under `traders/Round1/work/` unless it is replacing `traders/latest_trader.py`.
7. Compare it against both:
   - scorer baseline
   - robustness reference

Do not go back to blind threshold tuning as the first move.

## 16. Current Worktree Caution

This repository may be dirty when you open it. Before changing anything:

```bash
git status --short
```

At the time this context file was written:
- `traders/latest_trader.py` had existing modifications not made in this handoff
- multiple strategy and script files were untracked

Do not revert user work or unrelated changes.
