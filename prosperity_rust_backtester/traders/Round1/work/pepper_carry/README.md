# Pepper Carry Work Tree

This subtree holds the current post-`v63` Round 1 carry-family experiments for `INTARIAN_PEPPER_ROOT`, plus the Ash execution trims that were tested alongside them.

## Current milestone

- Promoted current frontier: `../../active/round1_pepper_dual_carry_v11.py`
  - Best current local frontier from this branch family.
  - Totals:
    - `default`: `295795.0`
    - `trade_match_mode=none`: `249785.0`
    - `queue_penetration=0.5`: `273452.5`
  - Why it is active:
    - keeps the `v9` local gains,
    - keeps the `v10` Ash join suppression,
    - halves official-replay Pepper passive clutter without losing local PnL.

## Validated chain

These files were actually backtested and are ordered by what they taught.

- `validated/round1_pepper_dual_carry_v1.py`
  - First clean submission-safe dual-carry branch.
  - Good default uplift, but weaker stressed robustness.
- `validated/round1_pepper_dual_carry_v2.py`
  - Tight-spread recycle suppression.
  - Small `none` recovery, but not good enough overall.
- `validated/round1_pepper_dual_carry_v3.py`
  - First robust carry frontier.
  - Fully removed the damaging mild-recycle aggressive sell path.
- `validated/round1_pepper_dual_carry_v4.py`
  - Wider passive carry sleeve.
  - Local no-op.
- `validated/round1_pepper_dual_carry_v5.py`
  - Over-pruned Ash execution redesign.
  - Rejected quickly; default collapsed.
- `validated/round1_pepper_dual_carry_v6.py`
  - Combined Ash exact-control trims.
  - Better than `v3`, but mixed two Ash changes together.
- `validated/round1_pepper_dual_carry_v7.py`
  - Ablation: remove second Ash passive layer only.
  - Local no-op.
- `validated/round1_pepper_dual_carry_v8.py`
  - Ablation: Ash best-level-only taking.
  - Real improvement in all tested local modes.
- `validated/round1_pepper_dual_carry_v9.py`
  - Add Pepper best-level-only aggressive sweep and recycle.
  - Major local carry gain over `v8`.
- `validated/round1_pepper_dual_carry_v10.py`
  - `v9` plus Ash join suppression.
  - Same local totals as `v9`, cleaner official Ash replay.

## Unvalidated chain

These files exist because they may still contain useful ideas, but they were not locally validated in the current pass.

- `unvalidated/round1_pepper_dual_carry_v12.py`
  - Start of the leaned-recycle family.
- `unvalidated/round1_pepper_dual_carry_v13.py`
  - Stronger leaned-recycle threshold.
- `unvalidated/round1_pepper_dual_carry_v14.py`
  - Follow-on leaned-recycle variation.
- `unvalidated/round1_pepper_dual_carry_v15.py`
  - Further leaned-recycle extension.
- `unvalidated/round1_pepper_dual_carry_v16.py`
  - Post-lean cleanup branch.
- `unvalidated/round1_pepper_dual_carry_v17.py`
  - Wide-carry spread threshold tweak.
- `unvalidated/round1_pepper_dual_carry_v18.py`
  - Later carry-follow-on branch.

Treat all `v12` to `v18` files as unproven until they are run on `default`, `none` and `q05`.

## Prototypes

These are research-style strategy variants, not current ship candidates.

- `prototypes/round1_pepper_direct_oracle_v2.py`
- `prototypes/round1_pepper_flow_oracle_v3.py`
- `prototypes/round1_pepper_microtrade_v4.py`
- `prototypes/round1_pepper_tradegated_v5.py`

These are useful when searching new Pepper control ideas, but they should be treated as prototype material first. Some earlier oracle/prototype branches were written with research-oriented imports and should not be assumed submission-ready.
