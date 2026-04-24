# Round 2 Builder Next Steps

Date: 2026-04-19

Scope: concrete handoff back to the strategy-builder after the post-builder
alpha audit.

Supporting files:

- [round2_postbuilder_alpha_report.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_postbuilder_alpha_report.md)
- [round2_missing_alpha_hypotheses.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_missing_alpha_hypotheses.md)
- [round2_validation_surface_audit.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/04_signal_notes/round2_validation_surface_audit.md)

## Top 3 Next Strategy Directions

### 1. Pepper carry shell plus harvest-aware refill guard

Why this is not redundant with what was tried:

- `v01` / `v02` mostly replaced the Pepper sleeve with a dynamic-fair residual
  shell
- this direction keeps baseline-like carry occupancy and changes the refill
  discipline after profitable recycle events

What metric should improve if this is right:

- Pepper near-limit fraction should stay close to baseline
- Pepper PnL should improve without needing a higher trade count
- give-back after recycle events should shrink

What failure mode it is trying to solve:

- monetization failure from giving back harvested Pepper gains while trying to
  re-enter the carry trade

### 2. Pepper stateful carry shell plus late cap-streak recycle and flow-conditioned target

Why this is not redundant with what was tried:

- it is not another fair-model retune
- it explicitly tests the missing `state machine` hypothesis: when should
  Pepper stay max-long, when should it recycle, and when should it push target
  inventory up or down

What metric should improve if this is right:

- Pepper PnL on the richer / overheated states
- drawdown or bad recycle give-back without losing too much occupancy
- weaker day-1 monetization should improve first

What failure mode it is trying to solve:

- same-trade thresholding that still loses because it never gets the carry /
  recycle timing right

### 3. Unchanged Pepper shell plus narrow Ash execution overlay

Why this is not redundant with what was tried:

- the builder has not yet run a serious Ash-only execution overlay while
  keeping Pepper fixed
- this isolates the only Ash donor family that still looks transfer-shaped

What metric should improve if this is right:

- Ash PnL should rise with same or lower Ash own-trade count
- Pepper PnL should stay flat, making attribution clean

What failure mode it is trying to solve:

- leaving small but real Ash execution EV untouched while over-focusing on
  another Pepper rewrite

## What The Builder Should Not Try Next

Do not spend the next cycle on:

- another generic Pepper dynamic-fair retune
- another broad early Pepper soft-cap variant
- exact Pepper path hardcoding
- a broad Ash signal rewrite

## Validation Guardrails For The Next Cycle

1. Keep the current explicit local `-1/0/1` surface as the base-stream
   attribution floor.
2. For quote-quality or state-gated candidates, add stricter local reruns under
   `worse` or `queue05` style matching before rejecting the idea.
3. Split candidates into two classes:
   - base-stream carry candidate
   - extra-flow / quote-EV candidate
4. Do not require every quote-EV or MAF-sensitive idea to clear the current
   local `>10%` hurdle before it is considered worth further evidence.

## Single Best Next Instruction For The Builder

Build the next Pepper candidate on top of the baseline carry shell and add only
`harvest-aware refill guard` plus `late cap-streak recycle`, with no new fair
model change in the same iteration.
