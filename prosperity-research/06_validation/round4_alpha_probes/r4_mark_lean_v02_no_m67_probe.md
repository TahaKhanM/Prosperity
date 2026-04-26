# r4_mark_lean_v02_no_m67_probe (Phase 5 follow-up)

## Probe definition

- Based on: `r4_mark_lean_v01_probe.py`.
- Single edit: Mark 67 entry REMOVED from `MARK_RULES_VFE`.
- Pre-reg: single-rule edit. No tuning.
- Phase 6 nulls finding (the trigger): Mark 67 fails BOTH the Mark-permutation
  null (perm p=0.47, ~indistinguishable from a random label) and the
  time-shuffle null (z=+2.0, marginal). Headline +1.19/u h500 PnL on Mark 67
  is likely DRIFT-CORRELATED, not causal.

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Δ vs v15 baseline | Δ vs Probe 1 (lean v01) |
|---|---|---|---|---|
| day-1 | 1280 | +68,771.50 | +1,146.5 | +835.0 |
| day-2 | 1240 | +108,484.00 | +906.0 | +825.5 |
| day-3 | 1162 | +48,598.50 | +1,027.5 | +364.5 |
| total | 3,682 | **+225,854.00** | **+3,079** | **+2,025** |

## Per-product attribution (3-day Δ vs v15)

| product | baseline | probe | Δ vs v15 | Δ vs Probe 1 |
|---|---:|---:|---:|---:|
| HYDROGEL_PACK | 134,062 | 134,581 | +519 | +0 |
| VELVETFRUIT_EXTRACT | 20,419 | 22,979 | **+2,560** | **+2,024** |
| VEV_4500 | 17,506 | 17,506 | 0 | 0 |
| VEV_4000 | 18,684 | 18,684 | 0 | 0 |
| VEV_5100 | 12,078.5 | 12,078.5 | 0 | 0 |
| VEV_5200 | 2,850.5 | 2,850.5 | 0 | 0 |
| OTHER(+6) | 17,175 | 17,175 | 0 | 0 |
| total | 222,775 | 225,854 | +3,079 | +2,025 |

**The entire +2,025 improvement vs Probe 1 is on VFE.** Mark 67's positive
buy-only lean (+0.10 per qty unit) was actively dragging down VFE PnL by
contaminating the directional read with drift-following noise.

## Verdict

**SHIP — replaces Probe 1 as the current shipping candidate.**

Pre-reg decision rule: "Δ vs Probe 1 ≥ −100 → ship the lighter form."
Actual: +2,025 vs Probe 1 — far exceeds the threshold and the floor.

This validates the Phase 6 nulls finding: Mark 67 has no Mark-attributable
identity edge. The +1.19/u h500 PnL was drift-correlation, and adding a
positive lean on Mark 67 buys was actually moving the VFE fair AGAINST
profitable trades on average (because Mark 67 prints land in regime windows
where v15's existing wall-mid + AC1 fade was already capturing the drift).

**Updated baseline for downstream composites: +225,854 (probe 5).**

## Falsifier (live)

If a fresh combined.log shows Mark 67 buy → next-h500 mid drift exceeds the
unconditional drift over the same window with t > 4, re-add Mark 67 to the
lean. Otherwise keep removed.

## Sign-off

This is the highest single-probe edge gain so far in either session.
Probe 5's +2,025-over-Probe-1 alone is larger than the +1,054 Probe 1 lift
above v15 baseline.
