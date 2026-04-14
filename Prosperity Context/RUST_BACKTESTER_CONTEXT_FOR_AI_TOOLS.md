# Rust Backtester Context For AI Tools In This Prosperity Repository

## Purpose

This file explains how the local Rust backtester works in this repository and
how AI coding tools such as Codex and Claude Code should use it when designing,
implementing, and validating Prosperity strategies.

It is not a replacement for:

- official Prosperity syntax and interface rules,
- the repo `AGENTS.md` files,
- the backtester's own `README.md`.

Instead, it is a practical context file for AI-assisted strategy work in this
specific checkout.

---

## The Most Important Local Fact

The active strategy-development workspace in this repository is:

- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester`

For most strategy tasks, AI tools should prefer that subtree over everything
else in the repo.

The Rust backtester is the main local evaluation engine for:

- testing trader variants,
- comparing baselines,
- generating run artifacts,
- inspecting inventory and execution behavior,
- deciding whether a strategy change actually helped.

---

## What The Rust Backtester Is

The local Rust backtester is a self-contained local Prosperity replay engine.

In practical terms it does all of the following:

1. Resolves a trader file.
2. Resolves one or more datasets from a path or dataset alias.
3. Replays the book and trade stream timestamp by timestamp.
4. Calls the Python `Trader` implementation on each state.
5. Applies local matching rules and position-limit checks.
6. Computes PnL summaries and optionally writes detailed artifacts.

The Rust CLI entry point is:

- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/src/main.rs`

which dispatches to:

- `rust_backtester::cli::run()`

The important implementation layers are in:

- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/src/cli.rs`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/src/runner.rs`

At a high level:

- `cli.rs` handles argument parsing, dataset selection, alias resolution,
  multi-file planning, `carry`, `flat`, and artifact mode routing.
- `runner.rs` handles the actual replay, matching, queue logic, metrics, and
  artifact generation.

---

## What It Is Not

AI tools should not treat this backtester as:

- the official Prosperity exchange,
- the official hidden matching engine,
- the sole authority on whether an edge is real.

It is the local evaluation surface for this repo.

That means it is extremely useful, but it is still a model of the competition,
not the competition itself.

---

## Current Local Working Paths

When AI tools operate in this repo, these are the default important paths:

- Active workspace:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester`
- Active traders:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders`
- Active datasets:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets`
- Active run outputs:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs`
- Preferred command surface:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/Makefile`
- Backtester docs:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/README.md`

---

## Current Local Caveats AI Tools Must Know

### 1. `latest_trader.py` is referenced but absent

Some local docs and tests still refer to:

- `traders/latest_trader.py`

That file is not present in this checkout.

Therefore AI tools should:

- not rely on auto-selection,
- not describe `latest_trader.py` as if it exists,
- use explicit trader paths in commands.

Example:

```bash
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py
```

### 2. The repo-root AGENTS file mentions `Trader1/`, but it is absent here

The root `AGENTS.md` conceptually refers to `Trader1/` as a legacy area.
That directory is not present in this checkout.

AI tools should therefore:

- ignore `Trader1/` in this repo,
- keep current work inside `prosperity_rust_backtester/`.

### 3. macOS has a real runtime caveat

In this checkout, the editable `rust_backtester` binary on macOS needs the
conda environment's `lib/` directory visible at runtime:

```bash
export DYLD_FALLBACK_LIBRARY_PATH="$CONDA_PREFIX/lib:${DYLD_FALLBACK_LIBRARY_PATH:-}"
```

This matters when AI tools try to run `rust_backtester` directly from the conda
environment.

---

## How AI Tools Should Think About The Backtester

AI tools should treat the Rust backtester as having four roles:

1. **Execution surface**
   - the place where a trader actually gets run
2. **Comparison surface**
   - the place where named baselines are compared
3. **Artifact generator**
   - the place where diagnostics are written
4. **Falsification surface**
   - the place where “good-looking” strategies get rejected when they depend too
     much on optimistic fills or one lucky slice

This is much more useful than treating it as “just a command that returns one
PnL number.”

---

## How The Rust Backtester Works In Practice

### 1. Trader resolution

The CLI accepts an explicit Python trader path via `--trader`.

Without an explicit path the backtester can auto-pick a trader, but in this
repo AI tools should avoid that because the local docs still assume an absent
`latest_trader.py`.

Preferred practice:

- always pass `TRADER=...` in `make` commands,
- or always pass `--trader ...` in direct CLI calls.

### 2. Dataset resolution

The CLI can resolve:

- a dataset alias such as `tutorial` or `round1`,
- a dataset folder path such as `datasets/tutorial`,
- a specific file such as `submission.log`.

In this checkout the main populated dataset is:

- `datasets/tutorial/`

which currently includes:

- `prices_round_0_day_-2.csv`
- `trades_round_0_day_-2.csv`
- `prices_round_0_day_-1.csv`
- `trades_round_0_day_-1.csv`
- `submission.log`
- `submission.json`

Future-round folders exist but may be placeholders until populated.

### 3. Multi-run planning

The CLI can:

- run a full round bundle,
- run a single day with `DAY=-1` or `--day=-1`,
- exclude submission data when a specific day filter is used,
- flatten multi-run output into one directory,
- carry state across non-submission day files.

These behaviors are managed primarily in:

- `src/cli.rs`

### 4. Replay and matching

For each replay step, the runner:

- constructs the local state,
- calls the Python `Trader`,
- evaluates generated orders,
- applies fill/match logic,
- updates positions, trades, PnL, and serialized state.

Important local knobs include:

- `--trade-match-mode`
  - `all`
  - `worse`
  - `none`
- `--queue-penetration`
- `--price-slippage-bps`

These are important because they let AI tools distinguish:

- likely robust edge,
- likely local fill-model-assisted edge,
- ambiguous edge that needs more validation.

### 5. Artifact generation

Depending on artifact mode, the backtester writes:

- `metrics.json`
- `submission.log`
- `bundle.json`
- `activity.csv`
- `pnl_by_product.csv`
- `trades.csv`
- `combined.log`
- `manifest.json`

The default output area is:

- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/runs`

---

## Preferred Command Surface For AI Tools

AI tools should prefer the local `Makefile` instead of inventing custom Rust
commands when normal workflows are sufficient.

Main commands:

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester
make doctor
make build
make test
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py DAY=-1
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py PERSIST=1
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py FLAT=1
make tutorial TRADER=traders/tutorial_submission_frontier_v5_trader.py CARRY=1
```

AI tools should switch to direct CLI calls when they need options not exposed by
the simple `make` target surface.

Example:

```bash
rust_backtester \
  --trader traders/tutorial_submission_frontier_v5_trader.py \
  --dataset tutorial \
  --trade-match-mode worse \
  --queue-penetration 0.5 \
  --artifact-mode none \
  --products full
```

---

## How Codex And Claude Code Should Use The Backtester

Before using the backtester, both Codex and Claude Code should ground
themselves in:

- `/Users/tahakhan/Documents/Work/Projects/Prosperity/AGENTS.md`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/AGENTS.md`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/.agents/skills/prosperity4-codex-skill/SKILL.md`

For strategy work in this repository, the backtester should be combined with:

- official context files for current rules and products,
- explicit local baselines,
- persisted artifact inspection when a result is non-obvious.

### 1. Use it as the default validator for strategy changes

For trader changes in this repository, AI tools should default to:

1. updating a trader file in `prosperity_rust_backtester/traders/`,
2. running a tutorial backtest,
3. comparing against a named baseline,
4. inspecting artifacts if the result is non-obvious.

### 2. Use explicit baselines

AI tools should compare strategies against named local references, not vague
“previous version” assumptions.

Examples of meaningful local baselines in this checkout include:

- `Original Trader.py`
- `tutorial_champion_scorer.py`
- `tutorial_overhaul_trader.py`
- `overhaul_v9_trader.py`
- `tutorial_submission_frontier_v4_trader.py`
- `tutorial_submission_frontier_v5_trader.py`

### 3. Use the full tutorial bundle before day-specific tuning

AI tools should not optimize directly to a single slice first.

Preferred order:

1. full tutorial bundle,
2. then day `-2` and day `-1` if diagnosis is needed,
3. then persisted artifact inspection,
4. then stricter fill settings if the result might be fragile.

### 4. Use persistence when behavior matters more than headline PnL

If a strategy change affects:

- inventory path,
- late-day carry,
- passive-vs-aggressive mix,
- drawdown,
- product contribution,

AI tools should use:

```bash
make tutorial TRADER=... PERSIST=1 FLAT=1
```

Then inspect the artifacts with:

- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/forensic_bundle.py`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/branch_scorecard.py`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/analyze_artifacts.py`

### 5. Use stress modes to separate real edge from convenient local edge

AI tools should not trust a strategy just because it wins in default mode.

When a candidate looks strong, rerun it under:

- `--trade-match-mode worse --queue-penetration 0.5`
- `--trade-match-mode none`

Interpretation:

- if it remains positive or competitive, the edge is more believable,
- if it collapses completely, the strategy may depend too much on local matching
  assumptions.

### 6. Use `carry` deliberately

`--carry` is not a generic performance flag. It changes the replay regime by
carrying positions, own trades, market trades, and trader state across
non-submission day files in the same round.

AI tools should use it only when they are intentionally testing that behavior,
not as a default replacement for ordinary evaluation.

### 7. Keep strategy code submission-compatible

AI tools must remember that the backtester is there to validate competition
submissions, not to justify local-only conveniences.

Submission-safe rules still matter:

- valid `Trader` class,
- valid `run(self, state)`,
- return `(result, conversions, traderData)`,
- sell quantities negative,
- no dependence on globals or persistent instance state,
- compact `traderData`,
- position-limit-safe logic under worst-case fills.

---

## How AI Tools Should Interpret The Main Artifacts

### `metrics.json`

Use for:

- total PnL,
- per-day PnL,
- product-level contribution,
- fast regression checks.

This is the first file to inspect after a run.

### `submission.log`

Use for:

- loading runs in the visualizer,
- comparing replay logs,
- checking what the trader emitted.

### `bundle.json`

Use for:

- deeper execution and state inspection,
- inventory path analysis,
- event-level forensic analysis,
- understanding why a strategy won or lost.

For strategy research, this is often the most informative artifact.

### `activity.csv`, `trades.csv`, `pnl_by_product.csv`

Use for:

- tabular analysis,
- plotting,
- debugging product-specific PnL and trade flow.

### `manifest.json` and `combined.log`

These matter most for persisted multi-run or flattened output bundles.

---

## Recommended AI Workflow In This Repo

For Codex or Claude Code, the preferred strategy loop is:

1. Read:
   - `/Users/tahakhan/Documents/Work/Projects/Prosperity/AGENTS.md`
   - `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/AGENTS.md`
   - official context files in `Prosperity Context/`
2. Choose an explicit trader baseline.
3. Form one clear market hypothesis.
4. Make one localized code change.
5. Run the full tutorial bundle through the Rust backtester.
6. Compare against named controls.
7. If needed, rerun with persistence and stress settings.
8. Only then decide whether to keep, reject, or extend the change.

This is better than:

- changing multiple strategy families at once,
- tuning directly to one submission slice,
- trusting one headline score,
- relying only on casual visual inspection.

---

## What AI Tools Should Not Do

AI tools should not:

- hallucinate absent local traders such as `latest_trader.py`,
- treat older public Prosperity repos as authority on current products or
  mechanics,
- skip the backtester and reason purely from static code,
- optimize to a single lucky day without checking the full tutorial bundle,
- assume default matching behavior equals official exchange truth,
- overwrite benchmark traders unless explicitly asked,
- treat `runs/` as if every artifact inside is meaningful or current.

---

## How This Fits With Official Prosperity Context

The source hierarchy should remain:

1. official Prosperity context files for current competition facts,
2. local backtester files and run artifacts for workflow and evidence,
3. older public Prosperity repos only for reusable ideas.

This file belongs in category 2.

It is about:

- the local evaluation engine,
- the local research workflow,
- how AI tools should use the repo safely and effectively.

It is not a source of official competition rules.

---

## High-Value Local Files To Pair With This Context

- Official syntax and interface context:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/Prosperity Context/Official Prosperity Context.md`
- Round 1 official context:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/Prosperity Context/Official Prosperity Context Round 1.md`
- Prompt-engineering context:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/Prosperity Context/CHATGPT_CONTEXT_FOR_CODEX_PROMPT_ENGINEERING.md`
- Repo-wide instructions:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/AGENTS.md`
- Active-workspace instructions:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/AGENTS.md`
- Active-workspace docs:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/README.md`
- Active-workspace command surface:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/Makefile`

---

## Bottom Line For AI Tools

For this repository, the Rust backtester should be treated as the default local
truth surface for strategy iteration.

Use it to:

- validate hypotheses,
- compare named strategies,
- inspect artifacts,
- falsify fragile ideas,
- preserve submission compatibility while iterating quickly.

Do not use it blindly, but do use it constantly.
