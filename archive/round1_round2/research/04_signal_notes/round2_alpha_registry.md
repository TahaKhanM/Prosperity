# Round 2 Alpha Registry

Date: 2026-04-19

Scope: durable Round 2 alpha inventory for `ASH_COATED_OSMIUM` and
`INTARIAN_PEPPER_ROOT`, updated after the first strategy-builder loop.

Status meanings:

- `promising`: still a live frontier worth building around
- `needs validation`: plausible and distinct, but not yet strong enough to
  anchor the next build alone
- `likely redundant`: real only as a helper or merge target
- `rejected`: do not revisit naively

Post-builder status meanings:

- `confirmed by implementation`
- `weakened by implementation`
- `neutral / unresolved`
- `dominated by baseline`
- `blocked by local-surface ambiguity`

Key evidence:

- [round2_alpha_report.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_alpha_report.md)
- [round2_carryover_report.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_carryover_report.md)
- [round2_postbuilder_feedback_audit.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_postbuilder_feedback_audit.md)
- [round2_validation_surface_audit.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_validation_surface_audit.md)
- [round2_postbuilder_behavior_summary.csv](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_postbuilder_behavior_summary.csv)

## Core Inventory

| alpha_id | product | short_name | type | evidence summary | Round 1 carryover | monetization style | expected horizon | key thresholds or params | key risks | confidence | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `R2-ASH-fixed-fair-wallmid-maker` | `ASH_COATED_OSMIUM` | anchored fair passive maker | structural | Ash remains the stable anchored product; `wall_mid`, `z20`, `ret1`, and fair-deviation reversion all carry over cleanly | carries over directly | passive / hybrid | 1-5 ticks | fair=`wall_mid`; take edge around `4`; passive edge around `5.3` | passive-fill optimism if overexpanded | high | promising |
| `R2-ASH-spike-fade` | `ASH_COATED_OSMIUM` | spike reversion overlay | spike | spike reversion remains tradeable in both rounds even with lower event frequency in Round 2 | carries over directly | taking / hybrid | 1-5 ticks post-event | trigger on large short-term return vs rolling vol; keep size small | low sample count relative to Pepper | medium-high | promising |
| `R2-ASH-medium-spread-taker-suppression` | `ASH_COATED_OSMIUM` | medium/wide-spread taker cleanup | execution | prior Ash validation and baseline cooldown logic both point to medium-spread aggressive action quality as the main donor bucket, but Ash-only `v01` / `v02` stayed negative with Pepper unchanged | carries over with retuning | execution / risk overlay | immediate | suppress weak buy/sell takers in spread states roughly `9-13` | over-suppressing still-good fades | medium-high | likely redundant |
| `R2-ASH-passive-inside-placement` | `ASH_COATED_OSMIUM` | passive-inside quote-state placement | execution | prior Ash validation says passive inside fills are good; remaining edge is stateful placement, not a new Ash fair | carries over with retuning | passive | 1-3 ticks | join/step-out/second-layer choice by spread and signal state | queue-position artefact risk | medium | needs validation |
| `R2-ASH-quote-state-overlay` | `ASH_COATED_OSMIUM` | imbalance/spread quote-state bias | microstructure | imbalance and spread-change effects remain sign-stable, but they are secondary to the anchored fair shell | carries over directly | passive / hybrid | 1 tick | side bias only when imbalance or spread-change agrees with the core fair | easily collapses into the base fair logic | medium | likely redundant |
| `R2-ASH-faster-flatten` | `ASH_COATED_OSMIUM` | earlier flatten / narrower recycle | risk overlay | consistent with the anchored shell and path-risk control, but not a headline edge by itself | carries over with retuning | risk overlay | 5-20 ticks | start recycling earlier once inventory leaves the center | underparticipation | medium | needs validation |
| `R2-ASH-trend-follow` | `ASH_COATED_OSMIUM` | directional trend fair | rejected | both rounds remain strongly mean reverting; this fights the dominant Ash structure | does not carry over | taking | 5-20 ticks | n/a | wrong-side market model | high | rejected |
| `R2-ASH-ofi-standalone` | `ASH_COATED_OSMIUM` | standalone OFI alpha | rejected | OFI remains weak and unnecessary relative to fair-deviation signals | does not carry over | taking | 1 tick | n/a | noisy and redundant | high | rejected |
| `R2-PEPPER-core-residual-stack` | `INTARIAN_PEPPER_ROOT` | dynamic fair plus residual reversion stack | structural | the real Pepper predictor family is one stack: moving fair, `z20`, and fair residual deltas; the builder weakened it locally only when it gave up too much carry | carries over with retuning | taking / hybrid | 1-20 ticks | dynamic fair around `mm_mid` or regularised blend; deviation edge around `3-4` | fails if treated as a full carry-shell replacement without monetization discipline | high | promising |
| `R2-PEPPER-regime-conditioned-carry-shell` | `INTARIAN_PEPPER_ROOT` | stateful high-carry Pepper shell | hybrid | the baseline winner is this family already; carry-shell `v01` / `v02` confirmed the shell locally but did not create additive delta over baseline | weak in Round 1, stronger in Round 2 | hybrid | 5-50 ticks | opening/discount/carry/overheated-style states; preserve high carry only in the right regimes | slides into template overfit if made too literal | high | promising |
| `R2-PEPPER-early-soft-cap-flatten` | `INTARIAN_PEPPER_ROOT` | early broad soft cap | risk overlay | `v01` and `v02` both show that broad early soft caps give up too much local Pepper carry | carries over with major weakening | risk overlay | 5-20 ticks | broad soft caps at `50%-60%` of hard limit | dominated by the baseline on the current local surface | high | rejected |
| `R2-PEPPER-late-cap-streak-recycle` | `INTARIAN_PEPPER_ROOT` | late recycle after prolonged cap occupancy | execution / risk overlay | distinct from broad soft caps, but explicit carry-shell `v01` / `v02` retunes produced zero local delta over baseline and suggest the meaningful local version is already absorbed there | carries over with retuning | hybrid | 5-20 ticks | trigger only after repeated `78+` inventory plus rich residual state | too rare or too weak if thresholds are off | medium-high | likely redundant |
| `R2-PEPPER-harvest-refill-guard` | `INTARIAN_PEPPER_ROOT` | harvest-aware refill guard | execution | explicit richer refill gating and post-harvest clamp in carry-shell `v01` / `v02` produced zero local delta over baseline, suggesting the local baseline already embodies the useful part of this family | new Round 2 refinement | hybrid | immediate to 10 ticks | refill only if materially cheaper, strongly discounted, or continuation-backed | underfills carry if too strict | high | likely redundant |
| `R2-PEPPER-pullback-finish-carry` | `INTARIAN_PEPPER_ROOT` | pullback-finish long carry completion | regime / execution | baseline-like carry completion on benign pullbacks looks distinct from generic fair-value buying | new Round 2 refinement | taking / hybrid | 1-5 ticks | mid-inventory, tight spread, negative slope, non-panicked pullback | buys real reversals if state filter is weak | medium-high | needs validation |
| `R2-PEPPER-flow-conditioned-target` | `INTARIAN_PEPPER_ROOT` | flow-conditioned inventory target | regime | builder candidate used flow mostly as skew; explicit `round2_pepper_flow_target_v01` retune matched baseline exactly, so the additive local version appears absorbed already | stronger in Round 2 | hybrid | 1-20 ticks | target inventory and edge shift by recent trade-flow state | endogenous local-flow overfit | medium-high | likely redundant |
| `R2-PEPPER-opening-wide-spread-take-gate` | `INTARIAN_PEPPER_ROOT` | opening wide-spread take suppression | execution | fresh artifact analysis found early opening Pepper aggressive buys with `target_long=45` and spread `12+` had negative `20`-tick edge, but removing them in `round2_pepper_opening_wide_gate_v01` lost too much normal carry | new fresh-alpha refinement | execution / participation gate | immediate to 20 ticks | gate aggressive Pepper buys only in early opening wide-spread states | underbuilds the baseline carry trade | medium-high | rejected |
| `R2-PEPPER-gap-state-guard` | `INTARIAN_PEPPER_ROOT` | empty-book Pepper recovery guard | execution / robustness | fresh artifact analysis found Pepper empty-book gaps as a real drawdown pocket; broad one-sided `v01` got close at `-23`, while narrowed empty-book-only `v02` matched baseline exactly locally and was later reported by the user as about `-2.5%` on the official backtester | new fresh-alpha refinement | state / risk overlay | gap window | only de-risk during empty-book Pepper windows and the immediate recovery | may be robustness-only with no local final-PnL edge | medium | rejected |
| `R2-PEPPER-quote-side-noquote-gate` | `INTARIAN_PEPPER_ROOT` | quote-side / no-quote EV gate | execution | late-rich Pepper quote-side gating finally produced the first real positive local branch: suppressing passive rebids while already long improved local total by `+325.0` without changing the fair model or Ash | weak direct carryover, stronger post-builder | passive / hybrid | immediate to 5 ticks | gate by spread, side, inventory, and residual state | default local surface may still underprice hosted-only variants; local edge so far is real but small | medium-high | promising |
| `R2-PEPPER-spike-fade` | `INTARIAN_PEPPER_ROOT` | spike reversion overlay | spike | tradeable but secondary; should remain an overlay, not a main strategy family | carries over directly | taking / hybrid | 1-5 ticks | event-only entries, not always-on trading | overlaps with the core residual stack if triggers are too loose | medium | needs validation |
| `R2-MAF-extra-flow-convexity` | `INTARIAN_PEPPER_ROOT` / `ASH_COATED_OSMIUM` | extra-flow convexity strategy selection | Round 2 specific | accepted MAF bids get `25%` more quotes, but local backtests do not model that; quote-intensive strategies can therefore be misranked locally | not applicable | validation / strategy selection | session-scale | separate base-stream and extra-flow candidate classes | locally untestable; fee can dominate | medium | needs validation |
| `R2-PEPPER-exact-template-hardcode` | `INTARIAN_PEPPER_ROOT` | exact session path hardcoding | rejected | still the cleanest overfit failure mode; baseline statefulness does not justify exact replay templates | does not carry over | taking | session-scale | n/a | one-day / one-template overfit | high | rejected |
| `R2-PEPPER-ofi-standalone` | `INTARIAN_PEPPER_ROOT` | standalone OFI alpha | rejected | OFI remains weak, unstable, and unnecessary relative to residual/fair signals | does not carry over | taking | 1 tick | n/a | unstable and redundant | high | rejected |

## Post-Builder Refinement Status

| alpha_id | builder status | post-builder read | do not revisit naively |
| --- | --- | --- | --- |
| `R2-PEPPER-core-residual-stack` | weakened by implementation | real predictor stack, but not a superior local monetization shell when detached from high carry occupancy | do not retest as “same Pepper residual trade with different thresholds” |
| `R2-PEPPER-regime-conditioned-carry-shell` | confirmed by implementation | baseline already embodies this family; carry-shell `v01` / `v02` were exact zero-delta local copies rather than a new additive edge | do not spend another cycle restating the same shell without a more orthogonal state change |
| `R2-PEPPER-early-soft-cap-flatten` | dominated by baseline | broad early Pepper soft caps were the clearest local donor in `v01` | do not revive as a general safety improvement |
| `R2-PEPPER-late-cap-streak-recycle` | weakened by implementation | explicit carry-shell retunes over the baseline produced zero local delta, so the standalone additive overlay looks mostly absorbed by baseline on the declared surface | do not keep nudging recycle thresholds inside the existing shell without a new trigger source |
| `R2-PEPPER-harvest-refill-guard` | weakened by implementation | richer refill gating and a post-harvest target clamp still produced zero local delta, so the standalone additive overlay looks mostly absorbed by baseline locally | do not bury it inside a generic `fill-quality gate` label |
| `R2-PEPPER-pullback-finish-carry` | neutral / unresolved | not tested directly; consistent with why the baseline keeps refilling effectively | do not confuse it with generic dip-buying |
| `R2-PEPPER-flow-conditioned-target` | weakened by implementation | explicit flow-target retune matched baseline exactly, so the additive local target-setting version looks absorbed already | do not revisit as another target-only Pepper retune |
| `R2-PEPPER-quote-side-noquote-gate` | confirmed by implementation | narrow late-rich passive quote suppression beat baseline locally and stayed non-regressive on the stricter proxy matrix, but the gain is still far below the `>5%` target | do not revert to broader calm-execution or generic fill-quality gates; patch this exact family next |
| `R2-MAF-extra-flow-convexity` | blocked by local-surface ambiguity | important Round 2-specific family, but unpriced locally because `bid()` is ignored | do not let the default local surface close this question |
| `R2-ASH-medium-spread-taker-suppression` | weakened by implementation | Ash-only `v01` / `v02` were distinct but stayed negative, so this looks like helper-level cleanup rather than the main Round 2 dollar | do not expect Ash alone to solve the Round 2 blocker |
| `R2-ASH-passive-inside-placement` | neutral / unresolved | still a valid Ash execution refinement, not a new Ash predictor family | do not combine it with broad passive suppression |
| `R2-ASH-quote-state-overlay` | likely redundant | still useful only as a helper around the Ash anchored shell | do not launch a standalone Ash microstructure branch from this |
| `R2-PEPPER-opening-wide-spread-take-gate` | rejected | the donor bucket is real, but deleting it costs too much local Pepper carry occupancy to win on the declared surface | do not revisit as blanket opening Pepper take suppression |
| `R2-PEPPER-gap-state-guard` | rejected | the broad one-sided version nearly tied baseline, but the properly narrowed empty-book version became exact `0.0` locally and the user later reported official regression, so this should not remain a promoted strategy branch | do not keep retuning this locally unless the objective changes to robustness-only investigation |
| `R2-PEPPER-exact-template-hardcode` | rejected | nothing in the builder feedback rescues this idea | do not revisit |

## Registry Notes

Important registry changes from the first-wave inventory:

- `R2-PEPPER-dynamic-fair-mr`, `R2-PEPPER-zscore-taker`, and
  `R2-PEPPER-wall-mm-delta` should now be treated as one core predictor stack,
  not three separate frontiers.
- the old `R2-PEPPER-fill-quality-gate` bucket was too coarse and is now split
  into:
  - `R2-PEPPER-harvest-refill-guard`
  - `R2-PEPPER-quote-side-noquote-gate`
  - `R2-MAF-extra-flow-convexity`
- the old `R2-PEPPER-soft-limit-recycle` bucket was too coarse and is now split
  into:
  - `R2-PEPPER-early-soft-cap-flatten`
  - `R2-PEPPER-late-cap-streak-recycle`
- `R2-ASH-imbalance-side-selection` and `R2-ASH-spreadchg-filter` are merged
  into `R2-ASH-quote-state-overlay`, because they are not distinct build
  frontiers now

## 2026-04-19 Carry-Shell Builder Update

- Implemented:
  - [round2_pepper_carry_shell_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_carry_shell_v01.py)
  - [round2_pepper_carry_shell_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_carry_shell_v02.py)
- Affected alphas:
  - `R2-PEPPER-regime-conditioned-carry-shell`
  - `R2-PEPPER-late-cap-streak-recycle`
  - `R2-PEPPER-harvest-refill-guard`
- Observed monetization result:
  - both carry-shell variants matched the baseline exactly on explicit day
    `-1`, `0`, and `1`
  - no total-PnL, product-PnL, drawdown, or trade-count delta was created
- Read:
  - the baseline already seems to encode the useful local version of these
    mechanics
  - these overlays did not help in isolation over the current baseline
  - the next additive Pepper frontier should be more orthogonal than another
    carry-shell restatement

## 2026-04-19 Autonomous Iteration Update

- Implemented:
  - [round2_pepper_flow_target_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_flow_target_v01.py)
  - [round2_ash_exec_overlay_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_ash_exec_overlay_v01.py)
  - [round2_ash_exec_overlay_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_ash_exec_overlay_v02.py)
  - [round2_pepper_opening_wide_gate_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_opening_wide_gate_v01.py)
  - [round2_pepper_gap_state_guard_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v01.py)
  - [round2_pepper_gap_state_guard_v02.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_gap_state_guard_v02.py)
- Observed monetization result:
  - flow-target retuning was exact `0.0`
  - Ash-only execution cleanup improved from `-307.0` to `-180.0`, but never
    beat baseline
  - opening wide-spread Pepper take suppression was a real behavior change but
    lost `-2321.0`
  - broad Pepper gap guard got close at `-23.0`
  - narrowed empty-book-only gap guard became exact `0.0`
- Read:
  - the remaining local additive Pepper edge is either already in baseline or
    too entwined with baseline carry occupancy to extract cleanly
  - the declared local surface should now be treated as a regression floor, not
    the place to keep spinning new local-only retunes

## 2026-04-19 Quote-Gate Update

- Implemented:
  - [round2_pepper_quote_gate_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_quote_gate_v01.py)
- Affected alpha:
  - `R2-PEPPER-quote-side-noquote-gate`
- Observed monetization result:
  - explicit local day `-1/0/1` total delta: `+325.0`
  - product attribution: entirely Pepper
  - stricter proxy matrix:
    - `default`: `+291.0`
    - `worse`: `+282.0`
    - `queue05`: `+64.0`
    - `none`: `0.0`
- Read:
  - the family is real and finally distinct from the baseline in monetization
    terms
  - the useful local version is narrow: late-rich passive rebuy suppression,
    not broad calm execution
  - this alpha should remain the active frontier, but its current magnitude is
    still too small to satisfy the requested `>5%` win bar
