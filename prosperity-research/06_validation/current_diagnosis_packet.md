# Current Diagnosis Packet

Date: 2026-04-19

Current candidate:
- [round2_pepper_gap_state_guard_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v02.py)

Same-family prior patch:
- [round2_pepper_gap_state_guard_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v01.py)

Named baseline:
- [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)

Validation surface:
- explicit non-carry day runs on day `-1`, `0`, and `1`

Supporting comparison reports:
- [v02 day -1](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/candidate_vs_baseline/round2-pepper-gap-state-guard-v02-dayneg1/candidate_vs_baseline_report.md)
- [v02 day 0](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/candidate_vs_baseline/round2-pepper-gap-state-guard-v02-day0/candidate_vs_baseline_report.md)
- [v02 day 1](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/candidate_vs_baseline/round2-pepper-gap-state-guard-v02-day1/candidate_vs_baseline_report.md)
- [v01 day 0](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/candidate_vs_baseline/round2-pepper-gap-state-guard-v01-day0/candidate_vs_baseline_report.md)
- [v01 day 1](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/candidate_vs_baseline/round2-pepper-gap-state-guard-v01-day1/candidate_vs_baseline_report.md)

## Headline Result

- baseline total: `310101.5`
- current candidate total: `310101.5`
- delta vs baseline: `0.0`
- delta vs baseline: `0.00%`

Per-day deltas for `v02`:

| Day | Candidate | Baseline | Delta |
| --- | ---: | ---: | ---: |
| `-1` | `102962.5` | `102962.5` | `0.0` |
| `0` | `102777.0` | `102777.0` | `0.0` |
| `1` | `104362.0` | `104362.0` | `0.0` |

Per-product deltas for `v02`:

| Product | Candidate | Baseline | Delta |
| --- | ---: | ---: | ---: |
| `ASH_COATED_OSMIUM` | `63652.0` | `63652.0` | `0.0` |
| `INTARIAN_PEPPER_ROOT` | `246449.5` | `246449.5` | `0.0` |

## Dominant Failure Mode

Dominant failure mode:
- the empty-book gap overlay is economically real as a drawdown / robustness
  pocket, but not as an additive local final-PnL frontier over the named
  baseline

What happened:
- fresh artifact analysis found two orthogonal Pepper pockets:
  - early opening wide-spread Pepper aggressive buys
  - Pepper empty-book / gap recovery states
- the opening wide-spread take gate was a real behavior change, but removing
  that bucket lost much more normal Pepper carry than it saved:
  `-2321.0` total
- the first gap-state implementation (`v01`) was too broad because it fired on
  one-sided books as well:
  `-23.0` total with a day `1` gain offset by a day `0` loss
- the narrowed empty-book-only patch (`v02`) then matched the baseline exactly

## Key Evidence

Fresh-alpha donor evidence:

- baseline Pepper early opening aggressive buys with `target_long=45` and
  spread `12+` had negative `20`-tick edge across the three days
- removing them in
  [round2_pepper_opening_wide_gate_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_opening_wide_gate_v01.py)
  eliminated the donor bucket completely but still lost `-2321.0` total
  because local Pepper carry occupancy fell too much

Gap-state evidence:

- `v01` gap guard:
  - day `-1`: `0.0`
  - day `0`: `-163.0`
  - day `1`: `+140.0`
  - total: `-23.0`
- `v02` gap guard:
  - exact `0.0` delta on day `-1`, `0`, and `1`

Interpretation:

- the local baseline already captures the useful local Pepper carry shape
- the remaining orthogonal Pepper pockets are either:
  - too entwined with that carry to extract cleanly, or
  - too small to move final local PnL once narrowed enough to be safe

## Diagnosis Verdict

- `R2-PEPPER-flow-conditioned-target` is locally exhausted as an additive
  target-setting frontier
- `R2-ASH-medium-spread-taker-suppression` is too small and too negative to be
  the next dollar
- `R2-PEPPER-opening-wide-spread-take-gate` found a real donor bucket but
  failed as a net monetization branch
- `R2-PEPPER-gap-state-guard` is the closest fresh orthogonal idea tested in
  this loop, but its empty-book version collapsed to exact baseline behavior

## Next Action

- Treat the declared local Round 2 surface as exhausted for additional
  official-limit-compliant baseline-beating retunes.
- Keep the current local floor as a regression surface only.
- The single highest-EV next move is off-surface evidence:
  hosted / MAF-sensitive or extra-flow-aware validation for quote-intensity and
  robustness ideas that the local stream cannot rank honestly.
