# Round 2 Progress Log

## 2026-04-19

- Wrote the Round 2 strategy build plan:
  [round2_strategy_build_plan.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_strategy_build_plan.md)
- Declared the validation surface:
  [round2_validation_surface.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_validation_surface.md)
- Verified the named baseline path:
  [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)
- Found two repo-local workflow issues that materially affect Round 2 validation:
  - `run_harness.py` emitted negative days as `--day -1`, which the Rust CLI
    rejected
  - multi-day Round 2 persisted outputs collide day `-1` and day `1` artifact
    names
- Fixed the negative-day CLI issue in:
  [workflow_common.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/workflow_common.py)
- Switched the primary surface to explicit per-day runs aggregated over day
  `-1`, `0`, and `1`.
- Baseline snapshot recorded in:
  [round2_baseline_snapshot.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_baseline_snapshot.md)
- First candidate implemented:
  [round2_pepper_dynamic_fair_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_dynamic_fair_v01.py)
- `v01` result on the explicit `-1/0/1` surface:
  `-9171.0` vs baseline, with the entire loss in Pepper.
- Follow-up candidate implemented:
  [round2_pepper_dynamic_fair_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_dynamic_fair_v02.py)
- `v02` result on the explicit `-1/0/1` surface:
  `-4004.0` vs baseline, again entirely in Pepper.
- Main diagnosis:
  the current local Round 2 surface is dominated by near-max-long Pepper carry,
  and the baseline already almost saturates that trade under the official `80`
  limit.
- Current diagnosis recorded in:
  [current_diagnosis_packet.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/current_diagnosis_packet.md)
- Blocker recorded in:
  [round2_blocker_report.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_blocker_report.md)
- Started the post-builder carry-shell branch:
  [round2_pepper_carry_shell_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_carry_shell_v01.py)
- `round2_pepper_carry_shell_v01.py` kept the baseline Pepper fair / state
  shell intact and only retuned:
  - harvest-aware refill gating
  - late cap-streak recycle thresholds
- `round2_pepper_carry_shell_v01.py` result on the explicit `-1/0/1` surface:
  exact `0.0` delta versus baseline on total PnL, per-product PnL, drawdown,
  and own-trade count.
- Patched the same family with an explicit post-harvest rebuild clamp:
  [round2_pepper_carry_shell_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_carry_shell_v02.py)
- `round2_pepper_carry_shell_v02.py` result on the explicit `-1/0/1` surface:
  exact `0.0` delta versus baseline again.
- Carry-shell branch conclusion:
  the named local baseline already appears to contain materially equivalent
  Pepper refill / late recycle behavior, so this branch is rejected as a
  standalone additive frontier on the declared local surface.
- Wrote the autonomous iteration loop files:
  - [round2_autonomous_iteration_plan.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_autonomous_iteration_plan.md)
  - [round2_evaluation_loop.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_evaluation_loop.md)
- Implemented the provided-strategy follow-up:
  [round2_pepper_flow_target_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_flow_target_v01.py)
- `round2_pepper_flow_target_v01.py` result on the explicit `-1/0/1` surface:
  exact `0.0` delta versus baseline again, so flow-target retuning is treated
  as locally absorbed by the baseline shell.
- Implemented Ash execution redistribution branch:
  - [round2_ash_exec_overlay_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_ash_exec_overlay_v01.py)
  - [round2_ash_exec_overlay_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_ash_exec_overlay_v02.py)
- Ash execution branch results on the explicit `-1/0/1` surface:
  - `v01`: `-307.0`
  - `v02`: `-180.0`
- Ash execution branch conclusion:
  the targeted donor bucket is real, but Ash-only cleanup does not beat the
  Round 2 baseline while Pepper stays unchanged.
- Fresh artifact analysis found a real Pepper donor bucket:
  early opening Pepper aggressive buys with `target_long=45` and spread `12+`
  were consistently negative over `20` ticks.
- Implemented fresh-alpha branch:
  [round2_pepper_opening_wide_gate_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_opening_wide_gate_v01.py)
- `round2_pepper_opening_wide_gate_v01.py` result on the explicit `-1/0/1`
  surface:
  `-2321.0`
- Opening-wide-gate conclusion:
  the donor bucket exists, but removing it gives up too much normal local
  Pepper carry.
- Fresh artifact analysis then isolated the next orthogonal pocket:
  Pepper empty-book / gap recovery states.
- Implemented gap-state guard branch:
  - [round2_pepper_gap_state_guard_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v01.py)
  - [round2_pepper_gap_state_guard_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v02.py)
- Gap-state guard results on the explicit `-1/0/1` surface:
  - `v01`: `-23.0`
  - `v02`: exact `0.0`
- Gap-state conclusion:
  the broad one-sided-book version was the first fresh branch to get close, but
  the properly narrowed empty-book version collapsed back to exact baseline
  behavior.
- Current local-frontier conclusion:
  no official-limit-compliant candidate beat the named baseline on the declared
  local surface.
- Best validated non-baseline result remains a tie at `0.0` delta:
  - [round2_pepper_carry_shell_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_carry_shell_v02.py)
  - [round2_pepper_gap_state_guard_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v02.py)

## 2026-04-19 Hosted-Aware Reopen

- User-provided official evidence changed the ranking surface:
  [round2_pepper_gap_state_guard_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v02.py)
  reportedly loses about `-2.5%` PnL versus
  [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)
  on the official backtester despite the local tie.
- Reopened the strategy frontier around hosted-aware Pepper execution rather
  than treating local ties as good enough.
- Benchmarked imported legacy Round 1 / Ash-family traders on Round 2:
  - `Ash.py`: `-12534.0`
  - `ash_follow_take_v18.py`: `-11953.0`
  - `ash_controller_v1.py`: `-22284.0`
  - `ash_controller_v2.py`: `-54119.0`
  - `ash_controller_v3.py`: `-41185.0`
  - `ash_rebuild_v1.py`: `-41501.0`
- Legacy-shell conclusion:
  importing earlier shells is not the fastest path to beating the current
  Round 2 baseline.
- Implemented hosted-aware calm Pepper execution branch:
  - [round2_pepper_calm_execution_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_calm_execution_v01.py)
  - [round2_pepper_calm_execution_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_calm_execution_v02.py)
- Calm-execution results:
  - `v01`: `-76.0`
  - `v02`: `-76.0`
- Calm-execution conclusion:
  hosted-aware urgency reduction is directionally better than prior negative
  branches, but too broad and too small.
- Ran a dedicated Pepper quote-side / noquote sweep on top of the baseline
  shell.
- First positive local family found:
  a late-rich Pepper passive quote gate that suppresses rebids while already
  long.
- Best sweep result:
  `quote_gate_refine_01` at `+325.0` total on the explicit day `-1/0/1`
  surface.
- Materialized that branch as:
  [round2_pepper_quote_gate_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_quote_gate_v01.py)
- `round2_pepper_quote_gate_v01.py` results:
  - full explicit `-1/0/1` local surface: `+325.0`
  - stricter proxy surfaces on the currently available benchmark matrix:
    - `default`: `+291.0`
    - `worse`: `+282.0`
    - `queue05`: `+64.0`
    - `none`: `0.0`
- Current best branch conclusion:
  the live frontier is now `R2-PEPPER-quote-side-noquote-gate`, but the gain is
  still far below the requested `>5%` target.
