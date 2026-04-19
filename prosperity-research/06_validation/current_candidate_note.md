# Current Candidate Note

Date: 2026-04-19

Candidate under test:
- [round2_pepper_gap_state_guard_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v02.py)

Same-family prior patch:
- [round2_pepper_gap_state_guard_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v01.py)

Baseline:
- [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)

## What Changed Vs Baseline

- `v01` kept the baseline Pepper fair model, carry shell, and Ash behavior
  intact.
- `v01` only added a Pepper post-gap overlay:
  - detect Pepper degenerate-book states
  - temporarily tighten Pepper rebuying and quote size after the gap
  - gently lean inventory back down only while the guard is active
- `v02` narrowed the same overlay further:
  - trigger only on fully empty Pepper books
  - shorten the recovery window from `1600` ticks to `600`
- Ash stayed baseline-identical in both versions.

## Why This Branch Was Orthogonal

- no Pepper fair-model rewrite
- no Pepper flow-target retune
- no Pepper carry-shell refill / recycle restatement
- no Ash execution change

This branch came from fresh artifact analysis, not from the earlier provided
strategy frontier.

## Expected Improvement Mechanism

If the fresh read had been right on the declared local surface:

- Pepper would keep the baseline carry trade in normal two-sided books
- empty-book or gap-recovery windows would stop adding low-quality Pepper risk
- Pepper drawdown pockets around gap timestamps would improve without giving up
  normal carry monetization

## Observed Result

- `v01` produced the first genuinely distinct fresh-alpha behavior in this
  loop:
  - day `-1`: `0.0`
  - day `0`: `-163.0`
  - day `1`: `+140.0`
  - total: `-23.0`
- `v02` narrowed the overlay to the true empty-book case and then matched the
  baseline exactly on day `-1`, `0`, and `1`.

Aggregate result for `v02`:
- candidate total: `310101.5`
- baseline total: `310101.5`
- delta: `0.0`

## Interpretation

- the broad one-sided-book version was too active and gave up local Pepper
  carry
- the properly narrowed empty-book version created no aggregate local PnL
  delta at all
- on the declared local surface, the useful local version of this family is
  therefore already absorbed by the baseline or too small to monetize

## Branch Status

- `round2_pepper_gap_state_guard_v02.py` is implemented and validated.
- This branch should be treated as exhausted on the declared local surface.
- It may still matter as a hosted / robustness idea, but it did not beat the
  named local baseline.
