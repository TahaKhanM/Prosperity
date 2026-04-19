# Round 2 Autonomous Iteration Plan

Date: 2026-04-19

Scope: end-to-end autonomous Round 2 strategy improvement across provided
strategy directions plus fresh alpha discovery when the provided frontier is
exhausted.

## Verified Repo Surface

- Baseline path:
  [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)
- Round 2 trader workspace:
  [traders/Round2](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2)
- Current candidate trader files:
  - [round2_pepper_dynamic_fair_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_dynamic_fair_v01.py)
  - [round2_pepper_dynamic_fair_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_dynamic_fair_v02.py)
  - [round2_pepper_carry_shell_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_carry_shell_v01.py)
  - [round2_pepper_carry_shell_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_carry_shell_v02.py)
- Preferred Round 2 backtest harness:
  [run_harness.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/run_harness.py)
- Helper / workflow file:
  [workflow_common.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/workflow_common.py)
- Analyzer location:
  [analysis.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1/analysis.py)
- Round 2 AI-facing export:
  [ai_strategy_context_by_round/round2](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/03_eda/round1/ai_strategy_context_by_round/round2)
- Alpha registry:
  [round2_alpha_registry.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_alpha_registry.md)
- Progress / validation files:
  - [round2_progress_log.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_progress_log.md)
  - [round2_validation_surface.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_validation_surface.md)
  - [round2_blocker_report.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_blocker_report.md)

## Current Best-Known Frontier

Current frontier after the dynamic-fair and carry-shell branches:

1. `R2-PEPPER-flow-conditioned-target`
2. `R2-PEPPER-quote-side-noquote-gate`
3. narrow Ash execution overlay while Pepper stays fixed
4. fresh alpha discovery only after the above branches are no longer clearly
   distinct from baseline

Reason:

- dynamic-fair Pepper was real but did not out-monetize the baseline locally
- carry-shell refill / late-recycle overlays were exact zero-delta local
  restatements of the baseline
- the next honest provided-strategy branch must be more orthogonal than
  "baseline shell with slightly different recycle thresholds"

## Current Weakest Assumptions

The highest-risk assumptions right now are:

- the explicit local `-1/0/1` surface is necessary as a floor, but not
  sufficient as the only ranking surface
- quote-quality and extra-flow-sensitive ideas may be misranked by the default
  optimistic local matching surface
- the local baseline may already absorb the useful version of several
  carry-shell monetization overlays
- the best remaining additive Pepper edge may be structural target-state logic
  rather than a new fair model

## Primary And Secondary Evaluation Surfaces

### Primary declared local floor

Keep the repo-declared surface:

- dataset: `prosperity_rust_backtester/datasets/round2`
- explicit day runs: `-1`, `0`, `1`
- non-carry
- artifact mode: `full`
- comparison target:
  [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)
- primary scalar:
  summed total PnL across the three explicit day runs

### Secondary sanity surface

Add a stricter local execution surface for state / quote-quality candidates:

- same explicit day `-1`, `0`, `1` split
- stricter matching knobs via direct Rust CLI if needed:
  - `--trade-match-mode worse`
  - `--queue-penetration 0.5`
- same baseline comparison

Role of the secondary surface:

- reject ideas that only win on optimistic local matching
- keep quote/state ideas alive if they are orthogonal and robust but not fully
  priced by the default local stream

## Iteration Order

1. Lock the evaluation loop and artifact requirements.
2. Exploit the strongest remaining provided-strategy branch:
   - Pepper flow-conditioned target on top of the existing baseline shell
   - no new fair model in the same patch
3. If that branch yields a distinct but weak behavior:
   - patch only the target-state mechanics once
4. If the provided frontier stalls again:
   - switch into fresh alpha discovery
   - use the raw Round 2 data, current candidate artifacts, and the analyzer
     stack to find non-redundant ideas
5. Build the best fresh alpha branch with one dominant change.
6. Continue until:
   - baseline is beaten on the declared primary local surface, or
   - the frontier is honestly exhausted and a blocker is proven

## When To Exploit Existing Strategy Directions

Stay in provided-strategy mode when:

- the registry still has a distinct high-confidence unbuilt or underbuilt
  branch
- the new branch is materially different from both the dynamic-fair and
  carry-shell families
- the expected improvement mechanism can be attributed cleanly in code

Current first branch to exploit:

- `R2-PEPPER-flow-conditioned-target` implemented on top of the baseline Pepper
  shell

## When To Switch Into Fresh Alpha Discovery

Switch when any of these hold:

- the chosen branch converges to baseline behavior with no real local delta
- multiple variants land on the same failure mode
- the registry says the obvious family is exhausted
- the local floor remains carry-saturated and the next idea is not orthogonal
  enough
- the only remaining live ideas require new evidence rather than more threshold
  churn

## How To Avoid Repeating Already-Tested Ideas

- treat `round2_pepper_dynamic_fair_v01.py` / `v02.py` as the exhausted
  dynamic-fair replacement branch
- treat `round2_pepper_carry_shell_v01.py` / `v02.py` as the exhausted
  additive carry-shell restatement branch
- do not open a new branch unless its alpha description differs materially from
  both the baseline and those prior candidates
- require every loop to name the exact alpha IDs being expressed
- update the alpha registry immediately after each serious run

## Files Updated Each Loop

Always update:

- [current_candidate_note.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/current_candidate_note.md)
- [current_diagnosis_packet.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/current_diagnosis_packet.md)
- [round2_progress_log.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_progress_log.md)
- [round2_alpha_registry.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_alpha_registry.md)

Update when changed materially:

- [round2_evaluation_loop.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_evaluation_loop.md)
- [round2_postbuilder_alpha_report.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_postbuilder_alpha_report.md)
- [round2_blocker_report.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_blocker_report.md)
- [round2_winning_candidate.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_winning_candidate.md)

## Success / Patch / Reject / Branch Criteria

### Success

- named candidate beats the baseline on the declared local floor
- improvement survives the required secondary sanity checks
- the improvement has a coherent alpha / monetization explanation

### Patch

- the candidate creates a distinct behavior change
- the dominant failure mode is still inside the same alpha family
- only one more clean mechanism change is needed

### Reject

- the branch is a local no-op or a clear regression
- the dominant failure mode is the hypothesis itself rather than a retunable
  implementation detail
- the branch is not materially distinct from baseline or prior branches

### Branch

- the prior family is exhausted
- the next candidate expresses a clearly different alpha family
- the registry and diagnosis packet both support the change in frontier

## Stop-And-Fix Rule

- if validation commands, artifacts, or comparison reports are incomplete or
  inconsistent, stop the strategy loop and fix the validation pipeline before
  ranking the next idea
- no candidate should be promoted or rejected on ambiguous or broken evidence

## Execution Update

- `R2-PEPPER-flow-conditioned-target` was implemented as
  [round2_pepper_flow_target_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_flow_target_v01.py)
  and matched the baseline exactly.
- narrow Ash execution redistribution was implemented as
  [round2_ash_exec_overlay_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_ash_exec_overlay_v01.py)
  and
  [round2_ash_exec_overlay_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_ash_exec_overlay_v02.py),
  but both stayed negative.
- fresh alpha discovery found two distinct Pepper pockets:
  - early opening wide-spread aggressive-buy donor bucket
  - empty-book Pepper gap-recovery pocket
- those were implemented as:
  - [round2_pepper_opening_wide_gate_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_opening_wide_gate_v01.py)
  - [round2_pepper_gap_state_guard_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v01.py)
  - [round2_pepper_gap_state_guard_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v02.py)
- final local read:
  the declared Round 2 local floor is exhausted for official-limit-compliant
  baseline-beating retunes; the next honest move is off-surface evidence, not
  another local threshold patch.
