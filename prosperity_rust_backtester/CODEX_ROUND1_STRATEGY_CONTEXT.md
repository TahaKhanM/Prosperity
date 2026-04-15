# Round 1 Codex Handoff

Date: 2026-04-15

This is the current Round 1 handoff for a fresh Codex instance working inside `prosperity_rust_backtester/`.

## Objective

The active objective is still:

- find a strategy that is **significantly** better than `round1_overhaul_v63.py`,
- target more than a tiny local increment,
- avoid overfitting to one day or one matching mode,
- stay submission-compatible with the Prosperity 4 Round 1 interface.

The latest pass improved materially over `v63`, but it did **not** achieve the user’s desired `>5%` robust breakout.

## Where to start

Read and use these in this order:

1. `AGENTS.md`
2. `traders/Round1/README.md`
3. `CODEX_ROUND1_STRATEGY_CONTEXT.md` (this file)
4. `traders/Round1/work/pepper_carry/README.md`
5. Official context files under `../Prosperity Context/`
6. Official hosted-log notes under `../prosperity-research/09_master_reports/`

## Current Round 1 file map

### Active milestones

- `traders/Round1/active/round1_overhaul_v63.py`
  - benchmark baseline and clean control
- `traders/Round1/active/round1_pepper_dual_carry_v11.py`
  - current best local frontier from the recent carry/execution pass

### Work tree

- `traders/Round1/work/pepper_carry/validated/`
  - evidence-backed carry-branch evolution from `v1` through `v10`
- `traders/Round1/work/pepper_carry/unvalidated/`
  - `v12` through `v18`, not validated in the latest pass
- `traders/Round1/work/pepper_carry/prototypes/`
  - oracle / flow / microtrade / trade-gated prototypes

### Research and diagnostics

- `scripts/round1_exact_control.py`
  - exact-control dynamic program on the public Round 1 path
- `scripts/analyze_official_logs.py`
  - official hosted-log parser and replay tool
- `trader_archive/Round1/research/round1_pepper_dual_carry_param_v2.py`
  - Pepper carry parameter sweep branch
- `trader_archive/Round1/research/round1_overhaul_param_v1.py`
  - Ash parameter sweep branch
- `trader_archive/Round1/research/round1_oracle_shape_param_v1.py`
  - oracle-shape research branch
- `trader_archive/Round1/research/round1_ml_fair_param_v1.py`
  - ML-fair research branch
- `trader_archive/Round1/probes/round1_probe_ash_microstructure_v1.py`
- `trader_archive/Round1/probes/round1_probe_pepper_microstructure_v1.py`

## Current benchmark and frontier

### Benchmark: `round1_overhaul_v63.py`

- Local totals:
  - `default`: `293261.0`
  - `trade_match_mode=none`: `249378.0`
  - `queue_penetration=0.5`: `272026.5`
- Product totals:
  - `default`: `ASH=55103.0`, `PEPPER=238158.0`
  - `none`: `ASH=13456.0`, `PEPPER=235922.0`
  - `q05`: `ASH=34256.5`, `PEPPER=237770.0`
- Interpretation:
  - strong clean baseline,
  - Ash already contains the hosted-log-driven inside-fill improvements,
  - still leaves meaningful public-path headroom versus exact control.

### Current frontier: `round1_pepper_dual_carry_v11.py`

- Local totals:
  - `default`: `295795.0`
  - `trade_match_mode=none`: `249785.0`
  - `queue_penetration=0.5`: `273452.5`
- Improvement versus `v63`:
  - `default`: `+2534`
  - `none`: `+407`
  - `q05`: `+1426`
- Product totals:
  - `default`: `ASH=55231.0`, `PEPPER=240564.0`
  - `none`: `ASH=13569.0`, `PEPPER=236216.0`
  - `q05`: `ASH=34380.5`, `PEPPER=239072.0`
- Why this is the active frontier:
  - best current local result across all three tested modes,
  - still submission-safe,
  - keeps the official-hosted replay shape cleaner than `v9` / `v10`.

## Carry-family evolution

### High-signal milestones

| Variant | Result | Main lesson |
| --- | --- | --- |
| `v1` | `default=295094.0` | first clean dual-carry uplift |
| `v3` | `295066.0 / 249378.0 / 273008.5` | first robust carry frontier |
| `v8` | `295194.0` default | isolated Ash best-level-only taking improvement |
| `v9` | `295795.0 / 249785.0 / 273452.5` | Pepper best-level-only sweep/recycle improvement |
| `v10` | same local as `v9` | cleaner official Ash join profile |
| `v11` | same local as `v10` | cleaner official Pepper passive profile |

### Low-signal or rejected validated branches

- `v2`
  - tight-spread recycle suppression
  - not enough net gain
- `v4`
  - wider passive carry sleeve
  - local no-op
- `v5`
  - aggressive Ash simplification
  - rejected quickly
- `v6`
  - combined Ash execution trim
  - useful, but mixed two Ash edits together
- `v7`
  - proved second Ash passive layer removal is locally neutral

### Unvalidated branches

- `v12` to `v15`
  - leaned-recycle family
  - no current local validation
- `v16` to `v18`
  - later carry follow-on edits
  - no current local validation

Do not assume any `v12+` file is better than `v11` until it has been run on `default`, `none`, and `q05`.

## Exact-control findings

The public Round 1 path still contains a large latent gap.

### Oracle totals

- Ash exact control: `64826.0`
- Pepper exact control: `247981.0`
- Combined exact-control ceiling on the public path: `312807.0`
- Gap over `v63`: `+19546.0`, about `+6.7%`

### Ash exact-control action pattern

The oracle mostly used:

- `mm_inside_12`
- `buy_take1_16`
- `sell_take1_16`

It used very little:

- join quoting
- deep quoting
- `take2`

Portable lesson:

- Ash still looks like an inside-maker plus selective best-level-taker product.
- Default multi-level sweeping is usually wasteful.

### Pepper exact-control action pattern

The oracle mostly used:

- `buy_take1_16`
- `carry_inside`
- `sell_inside_8`
- `sell_take1_12`

It used very little:

- deeper aggressive sweeps
- multi-layer passive clutter
- repeated passive layering after already loading inventory

Portable lesson:

- Pepper wants sparser, better-timed control than the older quote stack provided.
- Best-level-only Pepper sweeping/recycling was a real improvement.

## Official hosted facts that still matter

These came from:

- `../prosperity-research/09_master_reports/official-log-simulator-analysis-2026-04-15.md`
- `../prosperity-research/09_master_reports/round1-hosted-market-dynamics-2026-04-15-v2.md`

Highest-confidence facts:

- hosted `activitiesLog` path is fixed across compared submissions
- Pepper is **not** a hosted passive-fill market
- Ash hosted gains come from:
  - one-tick-inside passive capture
  - selective aggressive best-level takes

Do not chase:

- Pepper hosted passive market making as the main second edge
- market-impact stories on the official displayed path

## Official replay comparison of the latest frontier

Replaying against `round1_overhaul_v22.zip`:

### `v10` / `v11` Ash effect versus `v63`

- Ash `passive_join_buy` attempts dropped from `318` to `38`
- Ash inside-fill and take counts stayed unchanged

Interpretation:

- the newer Ash execution stack keeps the useful hosted Ash mechanisms,
- while wasting far less join inventory.

### `v11` Pepper effect versus `v10`

- Pepper `passive_inside_buy` attempts dropped from `1584` to `801`
- Pepper `passive_join_sell` attempts dropped from `181` to `88`
- Pepper `other_buy` attempts dropped from `135` to `56`
- Pepper take counts stayed unchanged

Interpretation:

- `v11` is cleaner on the hosted Pepper surface without losing local PnL.

## What the next Codex instance should do

### Highest-priority next steps

1. Validate `v12` through `v18`
   - They are currently structured and discoverable, but still unproven.
   - Run all of them on `default`, `none`, and `q05`.
   - Archive them if they do not beat `v11`.

2. Continue exact-control state slicing
   - The remaining headroom is still too large.
   - Bucket exact-control choices by:
     - spread
     - inventory
     - residual
     - progress
     - trade flow
   - Turn those buckets into explicit suppression rules instead of adding new predictors.

3. Keep pruning Pepper passive clutter
   - `v11` suggests the current live Pepper quote stack is still too chatty.
   - Test further quote suppression only when:
     - inventory is already high,
     - carry_left is limited,
     - spread is narrow,
     - flow is neutral or negative.

4. Refine Ash quote translation, not Ash prediction
   - Exact control still says Ash wants mostly:
     - inside quoting
     - best-level taking
   - Avoid adding another directional Ash fair model before fully exhausting execution translation.

5. Use the hosted probes if more official submissions are available
   - especially for Ash inside-versus-join behavior
   - and for Pepper passive suppression versus aggressive carry timing

### Lower-priority or likely-wasteful directions

- broad ML fair-value changes before execution bottlenecks are exhausted
- Pepper hosted passive-MM ideas
- large architectural rewrites that mix multiple new strategy families at once

## Commands that currently work

Run from:

- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester`

Validation template:

```bash
CARGO_TARGET_DIR=/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/target \
PYO3_PYTHON=/opt/miniconda3/envs/prosperity/bin/python \
./scripts/cargo_local.sh run -- \
  --trader traders/Round1/active/round1_pepper_dual_carry_v11.py \
  --dataset round1 \
  --artifact-mode none \
  --products off \
  --run-id round1-v11-default
```

Stress modes:

```bash
--trade-match-mode none
```

```bash
--trade-match-mode worse --queue-penetration 0.5
```

Official replay template:

```bash
/opt/miniconda3/envs/prosperity/bin/python scripts/analyze_official_logs.py \
  "../IMC Backtester Official Logs/round1_overhaul_v22.zip" \
  --replay-trader traders/Round1/active/round1_pepper_dual_carry_v11.py \
  --json
```

Exact-control script:

```bash
/opt/miniconda3/envs/prosperity/bin/python scripts/round1_exact_control.py --json
```

## Guardrails

- keep submission code free of `import os` and similar forbidden patterns
- preserve the Round 1 `run()`-only trader interface
- do not assume object state persists across calls
- do not ship a branch that only wins one optimistic mode
- do not treat older public Prosperity repos as authority on current Round 1 mechanics
