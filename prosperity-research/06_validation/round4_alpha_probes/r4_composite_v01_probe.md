# r4_composite_v01_probe (Phase 7 follow-up — NEW SHIP)

## Probe definition

- Composes Phase 5 + Phase 2 (the two SHIP-grade survivors of the followup):
  - **Phase 5** (`r4_mark_lean_v02_no_m67`): per-product Mark-conditional lean
    on HYD/VFE; Mark 67 entry REMOVED from VFE rules.
  - **Phase 2** (`r4_v5000_c02_standalone`): imb2 → fair skew on V_5000 only,
    β=+3.0, capped ±1.0 tick.
- Disjoint code paths: Phase 5 mutates HYD/VFE MM fairs; Phase 2 mutates
  V_5000 smile MM fair.
- Pre-reg locked at constituent values (no tuning).

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Δ vs v15 | Δ vs Probe 1 | Δ vs Phase 5 |
|---|---|---|---|---|---|
| day-1 | 1300 | +68,985.50 | +1,360.5 | +1,049.0 | +214.0 |
| day-2 | 1285 | +110,025.50 | +2,447.5 | +2,367.0 | +1,541.5 |
| day-3 | 1195 | +49,499.50 | +1,928.5 | +1,266.0 | +901.0 |
| total | 3,780 | **+228,510.50** | **+5,735.5** | **+4,681.5** | **+2,656.5** |

## Per-product attribution (3-day Δ vs v15)

| product | baseline | composite | Δ |
|---|---:|---:|---:|
| HYDROGEL_PACK | 134,062 | 134,581 | +519 |
| VELVETFRUIT_EXTRACT | 20,419 | 22,979 | +2,560 |
| VEV_4500 | 17,506 | 17,506 | 0 |
| VEV_4000 | 18,684 | 18,684 | 0 |
| VEV_5100 | 12,078.5 | 12,078.5 | 0 |
| VEV_5200 | 2,850.5 | 2,850.5 | 0 |
| OTHER (V_5000 + V_5300/4/5/6/65) | 17,175 | 19,831.5 | **+2,656.5** |
| total | 222,775 | 228,510.5 | **+5,735.5** |

The HYD+VFE attribution exactly matches Phase 5 standalone (+519 / +2,560).
The OTHER attribution exactly matches Phase 2 standalone (+2,656.5).

## Verdict — SHIP (NEW HEADLINE)

**Composite ship gate**: Δ vs v15 ≥ +5,000 AND Δ vs Phase 5 ≥ +1,000.
**Actual**: Δ vs v15 = **+5,735.5** ✓; Δ vs Phase 5 = **+2,656.5** ✓.

The composite achieves **PERFECT additive composition**: sum-of-parts is
+3,079 (Phase 5) + +2,657 (Phase 2) = +5,736; the composite delivers
+5,735.5 — within 1 shell of the maximum achievable. Zero negative
interaction.

This is the new shipping recommendation, replacing the original session's
`r4_mark_lean_v01_probe.py` (+1,054). The composite is **5.4× the
improvement** of the prior ship at locked pre-reg parameters.

## Why this works (and prior composite failed)

The original session's `r4_combined_v01_probe.py` blew up −60.9k because
the 0.7×Δ_BS hedge was implemented as a TAKE-only on VFE, crossing the
spread on every rebalance. This composite STAYS in fair-value-bias land:
both components are pure modifications to a per-product `fair` calculation;
the existing v15 MM absorbs the orientation naturally without any
spread-crossing.

Disjointness of code paths:
- Phase 5 hits `fair = fs[HYD] + ... + lean_h` and `fair = fs[VFE] + ... + lean_v`
- Phase 2 hits `fair = fair + v5000_skew` inside `_smile_voucher_orders` for k=5000
- No cross-product position interaction (Mark-lean doesn't touch vouchers; V_5000
  imb2 only modifies V_5000 fair, not its position).

## Falsifiers (live)

- Per-day positive every day (+1,360 / +2,448 / +1,928); if any single day
  flips negative on a fresh combined.log, fall back to Phase 5 alone.
- Mark 22 sell on VFE OR Mark 22 buy on HYD t-stat drops below |t|=2 over
  any 1,000-tick window → suspend the corresponding lean.
- imb_k2 → next-tick V_5000 Δmid β drops below +1.5 over any 1,000-tick
  window → suspend the V_5000 imb2 skew.

## Sign-off

**SHIP `r4_composite_v01_probe.py` for the next R4 submission.**

Ship floor: **+228,511 / +5,736 vs v15.** All three days positive. All
component attributions match standalone probes. No negative interaction.
