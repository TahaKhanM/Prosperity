# r4_mark_lean_plus_microstructure_probe (Probe 7)

## Probe definition

- Based on: r4_baseline_v15.
- Composes Probe 1 mark-lean + per-strike voucher microstructure tweaks:
  - **R4-V5000-C02**: V_5000 imb_k2 -> fair skew (`beta=+3.0`, capped
    +/-1 tick).
  - **R4-V5100-C01**: V_5100 microprice/wall blend at 50/50 with the
    smile fair: `fair = (smile + 0.30*micro + 0.70*wall)/2`. Wall uses
    `WALL_VOL_THR_VOU=5`. Falls back to smile fair if either input
    invalid.
  - **R4-V5200-F01**: V_5200 vol-cluster MM widening. Track 100-tick
    rolling realised vol per strike; widen `edge_shells` by +2 when
    the current rolling vol exceeds the trailing-1000-obs median (warm-up
    50 obs). Persists in `traderData["vol_state_5200"]`.
- All locked at pre-registered values. No tuning.

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Delta vs v15 |
|---|---|---|---|
| day-1 | 1268 | +67,207.00 | -418.0 |
| day-2 | 1260 | +103,906.50 | -3,672.0 |
| day-3 | 1168 | +49,916.50 | +2,345.0 |
| total | 3,696 | **+221,030.00** | **-1,745** |

## Per-product attribution (3-day Delta vs v15)

| product | baseline | probe | Delta |
|---|---:|---:|---:|
| HYDROGEL_PACK | 134,062 | 134,581 | +519 |
| VELVETFRUIT_EXTRACT | 20,419 | 20,953.5 | +535 |
| VEV_4500 | 17,506 | 17,506 | 0 |
| VEV_4000 | 18,684 | 18,684 | 0 |
| VEV_5100 | 12,078.5 | 6,623.5 | -5,455 |
| VEV_5200 | 2,850.5 | 2,850.5 | 0 |
| OTHER(+6) | 17,175 | 19,831.5 | +2,657 |
| total | 222,775 | 221,030 | -1,745 |

## Verdict

**REJECT.** Mark-lean component delivers as expected (HYD +519, VFE +535).
The microstructure stack costs net -2,798 vs Probe 1.

Findings per feature:
- **V_5100 microprice/wall blend** is a disaster (-5,455). Blending the
  smile fair 50/50 with a momentum/microprice signal pushes the fair
  away from the smile-MM equilibrium and the trader fights itself --
  the smile MM was already vega-weighted-correct on V_5100 in v15.
- **V_5000 imb_k2 skew** moves PnL into OTHER's V_5000 bucket (+2,657
  attributable since V_4000/V_4500 are unchanged). Sign is positive
  but small.
- **V_5200 vol-cluster widening** has **zero effect** -- `cur_vol`
  rarely exceeds the median *while* the smile is actively quoting,
  and the +2 edge bonus is then absorbed by the existing `bid+1/ask-1`
  pinning. The state persists across days (rolling history), but the
  median condition simply doesn't trigger often enough at the locked
  threshold.

The V_5100 collapse alone outweighs the wins. Pre-reg theory was that
V_5100 was the highest-EV gap because the rolling-mid-IV approach (R4-
PHASE5-G1) outperforms the static smile -- but a 50/50 blend with a
*price-domain* signal is not the same as the rolling mid-IV.

**Recommendation**: do NOT ship. Drop the V_5100 blend; the V_5000 imb2
skew and V_5200 vol-cluster widen could be retested individually.
