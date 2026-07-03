# Rust Backtester Context For AI Tools

## Purpose

This file is a code-backed reference for AI coding tools working in this
repository.

It explains how the local Rust backtester actually behaves in this checkout,
which files matter, which defaults are safe, and which assumptions are unsafe.

Use this together with:

- `AGENTS.md`
- `prosperity_rust_backtester/AGENTS.md`
- `prosperity_rust_backtester/README.md`

Repository root in this checkout:

- `/Users/tahakhan/Documents/Work/Projects/Prosperity`

Primary workspace:

- `prosperity_rust_backtester/`

---

## What This Tool Is

The Rust backtester is the main local replay and artifact-generation engine in
this repo.

It:

- loads a Python trader file,
- loads one or more datasets from CSV, normalized JSON, or submission payloads,
- replays ticks in timestamp order,
- invokes `Trader.run(...)` through embedded Python,
- applies local matching and position-limit logic,
- computes mark-to-mid PnL,
- writes structured artifacts under `runs/`.

Primary entrypoints:

- CLI entry: `prosperity_rust_backtester/src/main.rs`
- CLI orchestration: `prosperity_rust_backtester/src/cli.rs`
- Replay engine: `prosperity_rust_backtester/src/runner.rs`
- Python bridge: `prosperity_rust_backtester/src/pytrader.rs`
- Dataset parsing and normalization: `prosperity_rust_backtester/src/model.rs`

Adjacent analysis tooling:

- Official log analyzer: `prosperity_rust_backtester/official_log_analyzer/`
- Thin wrapper script: `prosperity_rust_backtester/scripts/analyze_official_logs.py`

---

## Current Repo Reality

These facts are true in this checkout on 2026-04-18 and matter for automation.

### 1. `traders/latest_trader.py` is still referenced in docs, but does not exist

AI tools should not assume a top-level default trader file exists.

The Rust CLI can auto-pick a trader, but that is unsafe here because there are
many experiment files containing `class Trader` under:

- `prosperity_rust_backtester/traders/Round1/work/ash/`

Current explicit active-looking trader file:

- `prosperity_rust_backtester/traders/Round1/Ash.py`

Safe rule:

- always pass an explicit trader path.

### 2. `latest` dataset alias currently resolves to `round1`, not `tutorial`

`cli.rs` picks the latest populated round directory under `datasets/`.
In this checkout both `tutorial/` and `round1/` are populated, so `latest`
means `round1`.

Safe rule:

- use `--dataset tutorial` or `make tutorial` when you actually want tutorial.

### 3. Populated dataset directories are not just placeholders anymore

Currently populated:

- `prosperity_rust_backtester/datasets/tutorial/`
- `prosperity_rust_backtester/datasets/round1/`

Current files include:

- tutorial: day `-2`, day `-1`, `submission.log`, `submission.json`
- round1: day `-2`, day `-1`, day `0`, and `prices_submission.csv`

### 4. Auto trader selection is especially risky in this repo

`resolve_trader()` scans:

- `scripts/`
- `traders/submissions/`
- `traders/`

and picks the most recently modified `.py` file containing `class Trader`.

Because there are many work-in-progress trader variants, AI tools should treat
auto-pick as non-deterministic for practical purposes.

---

## Preferred Command Surface

Use the `Makefile` first unless there is a reason to call the binary directly.

Main command surface:

- `prosperity_rust_backtester/Makefile`

Common targets:

- `make doctor`
- `make build`
- `make test`
- `make tutorial TRADER=...`
- `make round1 TRADER=...`
- `make submission ROUND=round1 TRADER=...`

The `Makefile` shells through:

- `prosperity_rust_backtester/scripts/cargo_local.sh`

On macOS that wrapper:

- uses a clean `PATH`,
- sets `PYO3_PYTHON`,
- sets `DYLD_FALLBACK_LIBRARY_PATH` using the Python lib dir,
- moves `CARGO_TARGET_DIR` to `~/Library/Caches/rust_backtester/target` unless overridden.

Diagnostics helper:

- `prosperity_rust_backtester/scripts/doctor_local.sh`

Use direct CLI only when necessary:

```bash
rust_backtester --trader prosperity_rust_backtester/traders/Round1/Ash.py --dataset tutorial
```

---

## CLI Behavior That AI Tools Must Know

### Dataset resolution

Implemented in `src/cli.rs`.

The CLI accepts:

- dataset aliases such as `tutorial`, `round1`, `latest`
- explicit directories such as `datasets/tutorial`
- explicit files such as `submission.log`, `submission.json`, or `prices_*.csv`

Important alias behavior:

- `latest` selects the latest populated round directory
- `tutorial` selects `datasets/tutorial`
- `round1` through `round8` map to those round folders
- `<round>-submission` selects the best submission-like dataset in that round

### Day behavior

- If a dataset has day values, the CLI fans out one run per day by default.
- `--day=-1` filters to that day.
- If a submission-like dataset is present and `--day` is used, submission-like
  inputs are excluded for the filtered run plan.

### Submission normalization

If the CLI sees a submission `.log` file with `activitiesLog`, it generates a
normalized `.json` dataset next to it if missing and then prefers that JSON.

This is handled by:

- `materialize_submission_json_if_missing(...)` in `src/model.rs`
- `ensure_submission_json_materialized(...)` in `src/cli.rs`

### Carry mode

`--carry` groups consecutive non-submission day datasets within the same round
into one synthetic dataset with continuous timestamps.

Important behavior:

- submission datasets stay separate
- positions, own trades, market trades, and `traderData` carry across day
  boundaries
- timestamps are renormalized so the next day starts immediately after the
  previous day ends

Relevant code:

- `build_carry_plans(...)`
- `build_carry_dataset(...)`
- `normalize_carry_timestamps(...)`

### Flat mode

`--flat` only changes multi-run output layout.

Instead of child directories, the CLI writes prefixed artifacts into one bundle
directory plus a `manifest.json`.

Relevant code:

- `write_flat_run_artifacts(...)`
- `write_flat_bundle(...)`

### Product summary mode

The terminal summary can show:

- `summary`
- `full`
- `off`

This affects console output only, not replay behavior.

---

## Artifact Modes And What They Mean

Artifact selection is controlled in `src/cli.rs` and materialized in
`src/runner.rs`.

### `--artifact-mode none`

Writes:

- `metrics.json`

### `--artifact-mode submission` (default when not persisting)

Writes:

- `metrics.json`
- `submission.log`

### `--artifact-mode diagnostic`

Writes:

- `metrics.json`
- `bundle.json`

### `--artifact-mode full`

Writes:

- `metrics.json`
- `bundle.json`
- `submission.log`
- `activity.csv`
- `pnl_by_product.csv`
- `combined.log`
- `trades.csv`

### Important file semantics

`submission.log`:

- JSON object with `submissionId`, `activitiesLog`, `logs`, and `tradeHistory`
- closest to official payload shape

`bundle.json`:

- custom diagnostic artifact
- includes run metadata, `pnl_series`, and full `timeline` only in full mode

`combined.log`:

- plaintext multi-section log with `Sandbox logs:`, `Activities log:`, and
  `Trade History:`
- closest to the older logger-style visualizer input format

For single-run persisted outputs, `combined.log` is the better visualizer input
when you want rich local timestamp detail from logger-style `lambdaLog`
payloads.

For stitched multi-run bundles, do not rely on the top-level `combined.log` as
visualizer input. Use child run artifacts instead.

---

## Replay Semantics

Implemented mainly in `src/runner.rs`.

### High-level flow per tick

1. Build `TradingState`-like payload for Python.
2. Call the Python trader.
3. Capture stdout.
4. Enforce position limits on the returned order set.
5. Match against book depth first.
6. Match remaining quantity against market trades if enabled.
7. Update positions and cash.
8. Mark positions to current mid-price for PnL.
9. Append artifacts and logs.

### Position limits

Position limits are hardcoded in:

- `position_limit(...)` in `src/runner.rs`

Unknown products fall back to `100`.

Limit enforcement is product-wide worst-case:

- if the total long or short exposure from that product's orders would breach
  the limit, all orders for that product are canceled for that tick.

### Matching rules

Book matching happens before market-trade matching.

Config knobs:

- `--trade-match-mode all|worse|none`
- `--queue-penetration <float>`
- `--price-slippage-bps <float>`

Specific local behavior worth knowing:

- queue penetration uses banker's rounding
- if queue penetration is positive and rounds to zero, it still exposes one lot
- slippage is applied to both depth fills and trade-matched fills
- equal-price market-trade fills account for visible queue ahead at that level

### PnL model

Pnl is:

- realized cash from fills
- plus mark-to-mid inventory value at each tick

Per-product and total final PnL are written into `RunMetrics`.

### Python bridge behavior

Implemented in `src/pytrader.rs`.

Important facts:

- the backtester embeds its own `datamodel` implementation
- trader files can still import with `from datamodel import ...`
- stdout is captured
- the bridge accepts slightly lenient return shapes locally:
  - dict only
  - tuple lengths `1`, `2`, or `3`
  - order objects or `(symbol, price, quantity)` tuples

Submission-compatible traders should still return the official 3-tuple:

```python
(orders, conversions, traderData)
```

### Hidden-state caveat

The Rust backtester creates one Trader instance per backtest run and reuses it
across ticks.

AI tools should still avoid relying on mutable instance or global state because
repo policy explicitly discourages it. Prefer `traderData`.

---

## Current Limitations And Mismatches

These are important when interpreting results.

### 1. CSV ingestion does not load observation CSV files

The Rust loader handles:

- normalized JSON
- submission payload JSON/log
- `prices_*.csv` plus paired `trades_*.csv`

It does not ingest `observations_round_*` CSV files.

Implication:

- conversion/plain observations are only available when already present in a
  normalized JSON dataset
- CSV-based local round data currently gives empty observations

### 2. Conversions are captured, not simulated

The Python bridge returns `conversions`, and the runner records them in the
timeline, but the replay engine does not apply conversion mechanics to
positions, cash, or observations.

Implication:

- conversion-heavy strategies are not faithfully simulated yet

### 3. `submission.log` and `combined.log` serve different consumers

`submission.log` is official-payload shaped.

`combined.log` is logger-style text.

This matters because the local visualizer currently treats JSON payloads and
logger-style logs differently.

### 4. README claims can lag behind code or repo state

The code is the authority when documentation conflicts.

Current examples of stale assumptions:

- top-level `latest_trader.py` references
- tutorial being implied as the default latest dataset

---

## Where To Edit For Common Tasks

If you need to change CLI flags or dataset selection:

- edit `prosperity_rust_backtester/src/cli.rs`

If you need to change replay mechanics, limits, fills, or artifacts:

- edit `prosperity_rust_backtester/src/runner.rs`

If you need to change dataset parsing or submission normalization:

- edit `prosperity_rust_backtester/src/model.rs`

If you need to change Python import compatibility or return normalization:

- edit `prosperity_rust_backtester/src/pytrader.rs`

If you need to change build/runtime environment behavior on macOS:

- edit `prosperity_rust_backtester/scripts/cargo_local.sh`
- inspect `prosperity_rust_backtester/scripts/doctor_local.sh`

If you need hosted-log research rather than local replay:

- inspect `prosperity_rust_backtester/official_log_analyzer/cli.py`

---

## AI Tool Working Rules

Use the Rust backtester by default for local strategy validation in this repo.

Do this:

- pass `TRADER=...` explicitly
- pass `--dataset` or a make target explicitly
- use `make tutorial` when validating tutorial behavior
- use `--persist` or `--artifact-mode full` when you need replay diagnostics
- inspect `metrics.json` first, then `bundle.json` or `combined.log`
- prefer child run artifacts over top-level stitched bundle files

Do not do this:

- do not rely on auto-picked traders
- do not assume `latest` means tutorial
- do not assume conversion behavior is simulated
- do not assume CSV datasets carry observation data
- do not treat local fills as official truth without hosted-log comparison

Recommended validation sequence:

1. Run an explicit trader against an explicit dataset.
2. Check `metrics.json` for headline outcome.
3. If behavior is unclear, persist full artifacts.
4. Use `combined.log` for single-run visualizer inspection.
5. Use official log analysis when local and hosted behavior diverge.

---

## Short Mental Model

The Rust backtester is best thought of as:

- the primary local validation engine,
- a structured artifact generator,
- a useful but imperfect execution model,
- and a better source of truth than stale docs, but not a substitute for hosted
  evidence.
