# r4_composite_v02_probe — REJECT (v08 machinery retired)

## Probe definition

- Two locked edits vs `r4_mark_dossier_v08_probe.py`:
  1. `VFE_W_M67 = 0.0` (drop Mark 67 leg from v08's stack).
  2. Add V_5000 imb2 → fair skew (β=3.0, cap=±1) inside `_smile_voucher_orders`.
- No other change. Pre-registered. No tuning.

## Backtest result (3-day BT, datasets/round4)

| set | day | own_trades | pnl | Δ vs v15 (+222,775) | Δ vs composite v01 (+228,510.50) |
|---|---|---|---|---:|---:|
| day-1 | 1 | 1280 | +67,559.50 | -65.5 | **-1,426.0** |
| day-2 | 2 | 1276 | +109,045.00 | +1,467.0 | **-980.5** |
| day-3 | 3 | 1189 | +48,519.50 | +948.5 | **-980.0** |
| total | | 3,745 | **+225,124.00** | **+2,349.0** | **−3,386.5** |

## Per-product attribution (3-day, sum across days)

| product | composite v02 | composite v01 floor | Δ |
|---|---:|---:|---:|
| HYDROGEL_PACK | 134,473 | 134,581 | -108 |
| VELVETFRUIT_EXTRACT | 19,700.5 | 22,979 | -3,278.5 |
| VEV_4500 | 17,506 | 17,506 | 0 |
| VEV_4000 | 18,684 | 18,684 | 0 |
| VEV_5100 | 12,078.5 | 12,078.5 | 0 |
| VEV_5200 | 2,850.5 | 2,850.5 | 0 |
| OTHER (V_5000+5300+5400+5500+6000+6500) | 19,831.5 | 19,831.5 | 0 |

The shortfall is entirely in VFE: -3,278.5 over 3 days. v08's
counterparty-conditional Mark-lean stack (Mark 14/22/49/01 with CP_MULT
gating, Mark 38 zeroed on VFE, Mark 55 disabled, M22 sell weight 0.15) is
LESS profitable than v01's flat lean (Mark 14, Mark 38 mirror, Mark 49 sell,
Mark 22 sell at default weights), even after Mark 67 is removed.

HYD is essentially flat (-108): v08's higher M14/M38 weights (0.30 vs 0.20)
are saturated by the position cap.

V_5000 piece composes additively (OTHER bucket matches the floor's V_5000
contribution to within $0).

## Decision rule outcome

Pre-registered rule: if composite v02 ≥ composite v01 + 500 → v02 becomes new
baseline. Otherwise composite v01 remains baseline.

**Actual: v02 = +225,124 < v01 + 500 = +229,011 by −3,887. REJECT.**

Composite v01 remains the floor for Phase 2-6. The v08 dossier-derived
per-Mark machinery is permanently retired: the counterparty-conditional
gating (CP_MULT) does not survive when Mark 67 is also removed. The
simpler v01 stack with the V_5000 imb2 skew is the structural template
for the production trader.

## Lesson

The v08 vs v01 +1,528 win that made v08 attractive was **entirely driven by
Mark 67 with the regime gate**. Once Mark 67 is removed, the rest of v08's
machinery (CP_MULT, M55 disabled, larger M14/M38 weights) is net-negative.
The v01 form is structurally cleaner and ships better with the V_5000
skew composed in.

## Verdict — REJECT

Composite v01 (`r4_composite_v01_probe.py`, +228,510.50) remains the floor
and structural template for Phase 2-6 stacking. v08's machinery is
permanently retired.
