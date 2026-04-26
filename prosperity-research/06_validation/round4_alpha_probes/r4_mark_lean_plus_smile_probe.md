# r4_mark_lean_plus_smile_probe (Probe 6)

## Probe definition

- Based on: r4_baseline_v15.
- Composes:
  - Probe 1 -- per-product Mark-conditional lean stack on HYD/VFE.
  - Probe 5 -- R4-CHAIN-02 day-3 convexity refit
    (`SMILE_A2_BASE = 7.62`, `SMILE_A2_DRIFT_PER_DAY = 1.62`).
- All component constants identical to the standalone probes. No tuning.

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Delta vs v15 |
|---|---|---|---|
| day-1 | 1261 | +64,823.00 | -2,802.0 |
| day-2 | 1271 | +106,649.50 | -928.5 |
| day-3 | 1208 | +49,666.50 | +2,095.0 |
| total | 3,740 | **+221,139.00** | **-1,636** |

## Per-product attribution (3-day Delta vs v15)

| product | baseline | probe | Delta |
|---|---:|---:|---:|
| HYDROGEL_PACK | 134,062 | 134,581 | +519 |
| VELVETFRUIT_EXTRACT | 20,419 | 20,953.5 | +535 |
| VEV_4500 | 17,506 | 17,506 | 0 |
| VEV_4000 | 18,684 | 18,684 | 0 |
| VEV_5100 | 12,078.5 | 11,603.5 | -475 |
| VEV_5200 | 2,850.5 | 4,878.5 | +2,028 |
| OTHER(+6) | 17,175 | 12,932.5 | -4,243 |
| total | 222,775 | 221,139 | -1,636 |

## Verdict

**REJECT vs Probe 1.** The composition is additive in attribution:
mark-lean delivers its expected +1,054 on HYD/VFE, but the smile-refit
component drags voucher PnL by -2,690 (identical to the standalone Probe
5 split, since the two changes touch disjoint products). Net -1,636 vs
v15, i.e. **-2,690 vs Probe 1 standalone.**

There is NO interaction effect: HYD/VFE deltas equal Probe 1's HYD/VFE
deltas to within ~$1, and voucher deltas equal Probe 5's voucher deltas
exactly. The mark-lean signal does not help the voucher chain (consistent
with its design -- it only mutates HYD/VFE fair).

Day-3 net +2,095 is the largest of any probe so far. If a future
recalibration of the smile (a TTE-conditional blend rather than a hard
constants swap) recovers Probe 5's day-3 lift while keeping day-1/2 flat,
THIS combination would dominate Probe 1. As written, however, the smile
component over-flattens on day-1 (TTE=7) and the loss outweighs the gain.

**Recommendation**: do NOT ship. Use Probe 1 (mark-lean alone) as the
ship-now candidate. Park the smile refit until a per-day convexity blend
is re-validated.
