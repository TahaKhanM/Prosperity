# Round 2 Strategy Build Plan

Date: 2026-04-19

Scope: post-builder Round 2 strategy iteration focused on the next
non-redundant Pepper monetization branch.

## Verified Repo Surface

- Root guidance:
  AGENTS.md
- Active workspace guidance:
  prosperity_rust_backtester/AGENTS.md
- Current assumptions:
  [current_assumptions.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/01_assumptions/current_assumptions.md)
- Baseline to beat:
  [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)
- Candidate workspace:
  [traders/Round2/candidates](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates)
- Helper / workflow file:
  [workflow_common.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/workflow_common.py)
- Preferred Round 2 runner:
  [run_harness.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/run_harness.py)
- Comparison tool:
  [candidate_vs_baseline_report.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/diagnostics/candidate_vs_baseline_report.py)
- Required post-builder research files confirmed present:
  - [round2_postbuilder_alpha_report.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_postbuilder_alpha_report.md)
  - [round2_builder_next_steps.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_builder_next_steps.md)
  - [round2_research_verdict.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_research_verdict.md)
  - [round2_alpha_registry.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_alpha_registry.md)

## Target Candidate

- New candidate path:
  [round2_pepper_carry_shell_v01.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_carry_shell_v01.py)
- Exact baseline path:
  [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)

## Exact Strategy Hypothesis

Implement the next Pepper branch as:

- baseline carry shell
- plus harvest-aware refill guard
- plus late cap-streak recycle
- with no new Pepper fair-model change in the same patch

Why this branch goes next:

- the failed `v01` / `v02` branch rewrote the Pepper sleeve around a
  dynamic-fair residual shell and stayed too close to "same trade, different
  thresholds"
- post-builder research says the missing edge is more likely in Pepper
  monetization discipline than in another predictor rewrite
- the current baseline already contains the right shell shape to preserve:
  high Pepper carry occupancy, stateful caps / edges, and selective recycle

## What "Baseline Carry Shell" Means In Code Terms

After inspection of
[baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py),
the Pepper shell to preserve is:

- `pepper_state_and_fair(...)` stays intact as the fair / state computation
  entrypoint
- the `opening`, `discount`, `carry`, and `overheated` regime split stays
  intact
- `pepper_caps_and_edges(mode)` remains the base cap / edge / size template
- the baseline flow and residual adjustments to `target_long`, `buy_edge`,
  `sell_edge`, `bid_edge`, `ask_edge`, and quote sizes remain the core shell
- the `pullback_finish_buy` behavior remains intact because it is part of the
  shell's carry completion logic
- Ash stays baseline-consistent and is not part of the main change

This means the iteration does not replace the shell. It only changes how the
shell protects harvested gains and how it recycles late in prolonged rich cap
states.

## How The Two New Mechanics Will Be Encoded

### Harvest-aware refill guard

Implementation intent:

- keep the existing baseline concept of tracking a profitable Pepper harvest in
  `traderData`
- make post-harvest refill stricter only while inventory is still high and the
  shell has not earned a clearly better re-entry
- require at least one of:
  - materially cheaper price than the harvest exit
  - clearly stronger discount versus the unchanged Pepper fair / buy edge
  - strong continuation evidence from recent slope plus buy flow
  - enough inventory released that the strategy is no longer effectively
    "reloading on top of the same rich state"

Encoding plan:

- keep `last_harvest_ts`, `last_harvest_px`, `last_harvest_qty`, and
  `refill_guard_until` in `pepper_state`
- extend the guard window only after genuine rich-state harvests
- tighten the refill gate near `76-80` inventory first, not at all inventory
  levels
- preserve baseline carry occupancy by letting the guard relax quickly once
  inventory is recycled far enough

### Late cap-streak recycle

Implementation intent:

- preserve the baseline idea that recycling should happen late, not early
- make late recycle more explicit after prolonged `78+` occupancy in rich
  states
- improve reopening of capacity after a long profitable streak without turning
  the branch into a broad soft-cap flattening variant

Encoding plan:

- keep `cap_streak` state in `pepper_state`
- only tighten recycle thresholds after repeated high inventory occupancy plus
  rich residual state
- modestly reduce `target_long` and make rich-state sells easier once the cap
  streak is long enough
- allow faster capacity reuse later in the streak by preserving the refill
  gate state from the harvest rather than immediately rebuying weak pullbacks

## What Must Not Change In This Iteration

- no new Pepper dynamic fair machinery
- no new Pepper OFI or imbalance model family
- no broad quote-EV / one-sided no-quote redesign
- no broad Ash redesign
- no baseline path edits
- no unrelated cleanup refactor

## Validation Surface

Use the currently declared Round 2 base-stream surface:

- dataset:
  [datasets/round2](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets/round2)
- explicit day runs for `-1`, `0`, and `1`
- carry mode: off
- artifact mode: `full`
- baseline comparison path fixed to
  [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)

Standard command pattern:

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester
python3 scripts/run_harness.py \
  --trader traders/Round2/candidates/round2_pepper_carry_shell_v01.py \
  --baseline "traders/Round 2/baseline.py" \
  --dataset datasets/round2 \
  --day -1 \
  --artifact-mode full \
  --label round2-pepper-carry-shell-v01-dayneg1
```

Repeat for day `0` and day `1`, then aggregate.

## Success Criteria For This Iteration

Primary tactical success:

- cleanly implement a baseline-shell Pepper candidate that is genuinely
  distinct from `v01` / `v02`
- keep Ash behavior effectively unchanged
- verify from artifacts that:
  - Pepper near-limit fraction stays close to baseline
  - refill behavior is more selective after rich-state harvests
  - late cap streaks recycle inventory more deliberately

Performance success for the branch:

- candidate total PnL on explicit day `-1/0/1` improves on baseline, or
- if headline PnL is close, the diagnostics show the intended mechanism worked
  and justify one more narrow patch inside the same family

Global program threshold remains:

- `candidate_total_pnl > 1.10 * baseline_total_pnl`

But post-builder evidence says this iteration should first be judged on clean
mechanism expression and whether it improves or preserves local carry while
shrinking recycle give-back.

## Reject / Patch / Branch Criteria

Patch this same family if:

- Pepper occupancy stays near baseline but recycle give-back still looks too
  loose
- the refill guard clearly fires but is either too strict or too weak
- late recycle logic triggers too rarely or too late to matter

Keep this branch as current best if:

- the candidate improves total PnL versus baseline or becomes the best
  non-dynamic-fair branch with convincing mechanism evidence

Reject this branch if:

- the implementation is effectively a no-op versus baseline
- the refill guard materially damages carry occupancy without better recycle
  monetization
- late recycle devolves into the already-rejected broad early soft-cap family

Only branch to the next family after at least one narrow patch if:

- this carry-shell branch is honestly exhausted, or
- the artifacts show the dominant remaining gap is now flow-conditioned target
  inventory rather than refill / recycle discipline
