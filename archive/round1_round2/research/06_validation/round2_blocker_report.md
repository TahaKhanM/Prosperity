# Round 2 Blocker Report

Date: 2026-04-19

## Status

No final hard blocker is declared right now.

This file is kept as a rolling limit report because the earlier
"local frontier exhausted" conclusion was invalidated once the Pepper
quote-side gate branch produced a real positive delta.

## Current Best Result

Best current local branch:
- [round2_pepper_quote_gate_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_quote_gate_v01.py)

Baseline:
- [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)

Best achieved delta on the explicit local day `-1/0/1` surface:
- `+325.0`
- about `+0.10%`

This is a real improvement, but still far below the requested `>5%` target.

## What Was Tried In The Reopened Loop

Hosted-aware baseline-adjacent branches:
- [round2_pepper_calm_execution_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_calm_execution_v01.py)
- [round2_pepper_calm_execution_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_calm_execution_v02.py)
- calm-execution best: `-76.0`

Legacy-shell imports tested on Round 2:
- `Ash.py`
- `ash_follow_take_v18.py`
- `ash_controller_v1.py`
- `ash_controller_v2.py`
- `ash_controller_v3.py`
- `ash_rebuild_v1.py`
- all materially below baseline

Fresh hosted-aware late-rich Pepper family:
- temp quote-gate sweep variants
- temp quote-gate refinement variants
- promoted winner:
  [round2_pepper_quote_gate_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_quote_gate_v01.py)

## Current Limiting Factors

1. The positive branch is real but small.
   - the first robust local gain is only a few hundred dollars
   - more aggressive versions quickly recreate day `0` underfill losses

2. The local surface still appears carry-saturated.
   - simple imported shells do not outscore the baseline
   - broad execution suppression gives back too much carry
   - late-rich quote-side gating helps, but not by enough

3. Official/local mismatch remains unresolved.
   - the user-reported official `-2.5%` result on
     [round2_pepper_gap_state_guard_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v02.py)
     proves that local ties are not sufficient to rank candidates honestly

## What Remains Unproven

- whether the current quote-side gate family scales to a materially larger edge
  with one more disciplined patch
- whether hosted evidence would rank `round2_pepper_quote_gate_v01.py` much
  higher than the local floor does
- whether any non-overfit local branch can honestly reach `>5%` versus the
  current baseline

## Single Highest-EV Next Move

Stay inside the live `R2-PEPPER-quote-side-noquote-gate` family for one more
clean patch.

Reason:
- it is the only reopened branch that beat baseline locally
- it also stayed non-regressive on the stricter local proxy matrix
- every broader or more aggressive branch tested in this reopened loop was
  worse
