# Round 2 Blocker Report

Date: 2026-04-19

## Blocker Type

Hard blocker:
- the declared local Round 2 validation surface is exhausted for additional
  official-limit-compliant baseline-beating retunes

This is no longer just a planning claim.
It is now supported by:

- failed dynamic-fair replacement variants
- failed Ash-only execution cleanup variants
- exact no-op Pepper carry-shell and flow-target variants
- one fresh-alpha Pepper donor-bucket branch that regressed materially
- one fresh-alpha Pepper gap-state family that got close only when overbroad
  and matched baseline exactly once narrowed correctly

## What Was Tried

Baseline:
- [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)

Provided-strategy and builder branches:
- [round2_pepper_dynamic_fair_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_dynamic_fair_v01.py)
- [round2_pepper_dynamic_fair_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_dynamic_fair_v02.py)
- [round2_pepper_carry_shell_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_carry_shell_v01.py)
- [round2_pepper_carry_shell_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_carry_shell_v02.py)
- [round2_pepper_flow_target_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_flow_target_v01.py)
- [round2_ash_exec_overlay_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_ash_exec_overlay_v01.py)
- [round2_ash_exec_overlay_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_ash_exec_overlay_v02.py)

Fresh-alpha branches from additional data / artifact analysis:
- [round2_pepper_opening_wide_gate_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_opening_wide_gate_v01.py)
- [round2_pepper_gap_state_guard_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v01.py)
- [round2_pepper_gap_state_guard_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v02.py)

Validation surface used:
- explicit non-carry day runs for Round 2 day `-1`, `0`, and `1`
- artifact mode `full`
- same named baseline on every run

## Best Achieved Delta Vs Baseline

Best validated candidate delta:
- `0.0`

Best candidates at that level:
- [round2_pepper_carry_shell_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_carry_shell_v02.py)
- [round2_pepper_gap_state_guard_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v02.py)

Closest distinct fresh-alpha near miss:
- [round2_pepper_gap_state_guard_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v01.py)
- total delta: `-23.0`

Reference regressions:
- dynamic-fair best patch: `-4004.0`
- Ash execution best patch: `-180.0`
- opening-wide-gate fresh-alpha branch: `-2321.0`

## What Frontier Was Exhausted

Exhausted local frontiers:

1. Pepper dynamic-fair replacement
   - real signal family, but not a better local monetization shell than the
     baseline carry profile
2. Pepper additive carry-shell retuning
   - explicit local no-op
3. Pepper flow-conditioned target retuning
   - explicit local no-op
4. Ash-only medium-spread execution cleanup
   - distinct but negative, with Pepper unchanged
5. Pepper early opening wide-spread take suppression
   - real donor bucket, but removing it loses too much carry occupancy
6. Pepper gap-state / empty-book recovery overlay
   - broad version nearly flat but still negative, narrowed version exact no-op

## Why Baseline Was Not Beaten

The local surface remains dominated by official-limit Pepper carry that the
baseline already monetizes extremely well:

- baseline Pepper total: `246449.5` out of `310101.5`
- baseline Pepper average absolute position:
  - day `-1`: `77.4709`
  - day `0`: `77.4326`
  - day `1`: `77.3212`
- baseline Pepper near-limit occupancy is already about `94%` on every day

Fresh-alpha work tightened that conclusion:

- the early opening wide-spread Pepper donor bucket is real, but deleting it
  lost `-2321.0` because local carry occupancy fell too much
- the gap-state guard family is the first orthogonal branch that got close:
  `-23.0`
- once the gap guard was narrowed to the true empty-book case, it became exact
  `0.0`, which means the additive local EV in that pocket is either already
  absorbed by baseline or too small to move final PnL

This is the key blocker:
- the remaining local ideas are either
  - already in baseline-equivalent form, or
  - only valuable as robustness / hosted-execution ideas rather than additive
    local final-PnL ideas

## What Remains Unproven

Still unproven:

- whether quote-intensity and MAF / extra-flow-sensitive branches would
  outrank the baseline on hosted or extra-quote-aware evidence
- whether gap-robustness or quote-side selectivity branches have value that
  the local final-PnL surface cannot measure

Not unproven anymore:

- another local Pepper threshold retune
- another local additive carry-shell rewrite
- another Ash-only cleanup branch as the main Round 2 answer

## Single Highest-EV Next Move

Move off the current local-only ranking surface for the next serious Round 2
branch.

Concrete recommendation:
- keep the explicit local day `-1/0/1` surface as a regression floor
- use hosted / official-log / MAF-sensitive evidence to rank quote-side and
  extra-flow branches next
- if that evidence is unavailable, stop local strategy churn here

Reason:
- the local frontier is now sufficiently explored that the expected value of
  another official-limit-compliant local retune is lower than the expected
  value of improving the validation surface itself
