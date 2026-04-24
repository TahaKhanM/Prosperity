# Round 2 Validation Surface

Date: 2026-04-19

Scope: declared comparison surface for Round 2 candidate-vs-baseline strategy
work in this checkout.

## Canonical Dataset Surface

Primary dataset:
- [datasets/round2](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets/round2)

Files required in the primary surface:
- `prices_round_2_day_-1.csv`
- `prices_round_2_day_0.csv`
- `prices_round_2_day_1.csv`
- matching `trades_round_2_day_*.csv`

Reason:
- this is the canonical local raw-data directory documented by the Rust
  backtester and the Round 2 dataset README
- all three raw days are required to avoid cherry-picking a convenient single
  day

## Primary Validation Configuration

- Backtester: Rust backtester workflow under
  `prosperity_rust_backtester/`
- Runner: `python3 scripts/run_harness.py`
- Trader path: explicit candidate path
- Baseline path: explicit baseline path
- Dataset: `datasets/round2`
- Day filter: explicit day runs for `-1`, `0`, and `1`
- Carry mode: `off`
- Flat mode: `off`
- Artifact mode: `full`

Standard form for the primary surface:

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester
python3 scripts/run_harness.py \
  --trader <candidate> \
  --baseline "traders/Round 2/baseline.py" \
  --dataset datasets/round2 \
  --day -1 \
  --artifact-mode full \
  --label <label>-dayneg1
python3 scripts/run_harness.py \
  --trader <candidate> \
  --baseline "traders/Round 2/baseline.py" \
  --dataset datasets/round2 \
  --day 0 \
  --artifact-mode full \
  --label <label>-day0
python3 scripts/run_harness.py \
  --trader <candidate> \
  --baseline "traders/Round 2/baseline.py" \
  --dataset datasets/round2 \
  --day 1 \
  --artifact-mode full \
  --label <label>-day1
```

Primary metric aggregation rule:
- sum the three explicit day results for day `-1`, `0`, and `1`

## Why Explicit Per-Day Runs Are Required

Current repo-local tooling issue:
- the multi-day Round 2 harness path collides artifact names for day `-1` and
  day `1`, so one artifact set overwrites the other in persisted outputs

Operational implication:
- the Round 2 primary surface must be executed as three explicit single-day
  runs and then aggregated
- this is a local workflow correction, not a change to the underlying dataset
  surface

## Why Carry Mode Is Not The Primary Surface

Carry mode remains useful for diagnostics, but it is not the primary scoring
surface for this loop because:

- the documented raw Round 2 bundle already provides the canonical three-day
  comparison set without requiring synthetic cross-day state carry
- the repo does not standardize carry mode as the main validation surface for
  Round 2
- the user explicitly asked for a robust, non-cherry-picked baseline surface,
  and the simplest robust surface is the full three-day non-carry bundle

Carry-mode use in this loop:
- allowed as a secondary diagnostic when state continuity or inventory path is
  the suspected failure mode
- not allowed to replace the primary score used for the `>10%` success claim

## Primary Metric

Primary score:
- summed total PnL across the three explicit non-carry Round 2 day runs:
  `-1`, `0`, and `1`

Primary threshold:
- candidate must beat baseline by more than `10%`

Exact formula:
- `candidate_total_pnl > 1.10 * baseline_total_pnl`

## Secondary Robustness Bundle

These do not replace the primary metric, but they gate whether a `>10%` gain is
credible:

- per-day PnL on day `-1`, day `0`, and day `1`
- per-product PnL contribution
- total drawdown when available from run artifacts
- average absolute position and near-limit fraction by product
- aggressive and passive fill-quality summaries from the comparison report

## What Counts As Beating Baseline By More Than 10%

A candidate counts as beating baseline only if all of the following are true:

1. It is compared directly against
   [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)
   on the same primary surface, using the same explicit day split.
2. The primary metric satisfies:
   - `candidate_total_pnl > 1.10 * baseline_total_pnl`
3. The comparison artifacts do not show an obvious invalidating issue such as:
   - a catastrophic single-day offset hidden by one huge day
   - a clear inventory blow-up
   - a large regression in one product that makes the result non-transferable

## Required Artifacts Per Serious Comparison

- harness manifest
- candidate `metrics.json`
- baseline `metrics.json`
- candidate `pnl_by_product.csv`
- baseline `pnl_by_product.csv`
- candidate `combined.log`
- baseline `combined.log`
- candidate-vs-baseline report
- diagnosis packet for the candidate and, when needed, for the baseline

## Declared Baseline Name

Named baseline on this surface:
- [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)

The baseline is not a vague concept.
Every candidate claim in this loop must trace back to a direct run against this
exact file on the declared primary surface.
