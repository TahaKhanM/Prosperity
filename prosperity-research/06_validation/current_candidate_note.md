# Current Candidate Note

Date: 2026-04-19

Candidate under test:
- [round2_pepper_quote_gate_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_quote_gate_v01.py)

Baseline:
- [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)

## What Changed Vs Baseline

- Ash is baseline-identical.
- Pepper fair, carry shell, refill guard, and recycle state logic stay baseline-identical.
- The only change is a late-state Pepper passive quote gate:
  - when Pepper is already long (`72+`), past the early session
    (`regime_progress >= 0.18`), mildly rich (`residual >= 0.0`), and not in
    active buyflow, the candidate:
  - widens the passive buy edge
  - removes the second passive buy layer
  - cuts the first passive buy size to `35%`
  - nudges the first passive sell quote slightly more aggressive and slightly
    larger

## Why This Branch Is Orthogonal

- no new Pepper fair model
- no dynamic-fair rewrite
- no new Ash overlay
- no broad carry-shell restatement
- no gap-state logic

This branch is a narrow implementation of
`R2-PEPPER-quote-side-noquote-gate`, which had not been expressed cleanly in
prior candidate files.

## Expected Improvement Mechanism

- keep the baseline carry shell in the states where it clearly works
- stop donating low-quality passive Pepper rebuys when already rich and long
- preserve occupancy better than the failed calm-execution branch by changing
  quote-side participation only in the donor state

## Observed Result

Explicit local day `-1/0/1` surface:

- day `-1`: `+34.0`
- day `0`: `-26.0`
- day `1`: `+317.0`
- total: `+325.0`

Headline:

- candidate total: `310426.5`
- baseline total: `310101.5`
- delta: `+325.0`

Secondary stricter local evidence on the currently available benchmark surface:

- `default`: `+291.0`
- `worse`: `+282.0`
- `queue05`: `+64.0`
- `none`: `0.0`

## Interpretation

- this is the first non-trivial branch that beats the baseline locally rather
  than tying it or regressing
- the edge remains small relative to the user target, but the mechanism looks
  real and attributable
- the branch is still far from the requested `>5%` win threshold, so it should
  be patched rather than shipped as final

## Branch Status

- implemented and validated
- current best local branch
- keep and patch inside the same quote-side / late-rich Pepper family
