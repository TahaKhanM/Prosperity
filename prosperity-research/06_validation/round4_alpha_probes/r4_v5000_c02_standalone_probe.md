# r4_v5000_c02_standalone_probe (Phase 2 follow-up)

## Probe definition

- Based on: r4_baseline_v15.
- Single change: in `_smile_voucher_orders`, when k==5000, add `+V5000_IMB_BETA × imb_k2(d_)`
  to the per-strike fair, capped at ±V5000_IMB_CAP ticks.
- Pre-reg: V5000_IMB_BETA = 3.0, V5000_IMB_CAP = 1.0 (matches v15's VFE
  V_IMB_K2/V_SKEW_CAP convention).
- All other v15 logic byte-for-byte identical.

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Δ vs v15 |
|---|---|---|---|
| day-1 | 1301 | +67,839.00 | +214.0 |
| day-2 | 1283 | +109,120.00 | +1,542.0 |
| day-3 | 1195 | +48,472.50 | +901.5 |
| total | 3,779 | **+225,431.50** | **+2,657** |

Per-product:
| product | baseline | probe | Δ |
|---|---:|---:|---:|
| HYDROGEL_PACK | 134,062 | 134,062 | 0 |
| VELVETFRUIT_EXTRACT | 20,419 | 20,419 | 0 |
| VEV_4500 / VEV_4000 / VEV_5100 / VEV_5200 | 51,119 | 51,119 | 0 |
| OTHER (V_5000 + V_5300/5400/5500/6000/6500) | 17,175 | 19,832 | **+2,657** |
| total | 222,775 | 225,432 | **+2,657** |

Since the only code-path change is for k==5000, **100 % of the +2,657 lift is V_5000**.
The other strikes in the OTHER bucket (V_5300/5400/5500/6000/6500) are unchanged.

## Verdict — SHIP

Pre-reg ship gate:
- Δ ≥ +1,500 → **PASS** (+2,657)
- V_5000 carries ≥ 80 % of the lift → **PASS** (100 %)
- Per-day positive each day → PASS (+214 / +1,542 / +902)

Day-2 carries +1,542 of the +2,657 — consistent with V_5000 being the
highest-vega strike most sensitive to order-book imbalance.

Trade count goes UP from 3,681 to 3,779 (+98), all at V_5000 — the imb2
skew nudges the smile fair, generating MORE quote-in-and-out turnover at
V_5000 levels where the smile MM previously sat passive.

## Falsifier (live)

If imb_k2 → next-tick V_5000 Δmid β drops below +1.5 over any 1,000-tick
window of R4 day 1 live, suspend.

## Sign-off

The pre-reg estimate (+2,657 inside Probe 7 stack) was accurate.
The original Phase 8b stack got dragged into REJECT by the V_5100 micro/wall
disaster (−5,455). Isolating V_5000 gives +2,657.

**Combined with Probe 5 (lean_v02_no_m67, +3,079 vs v15), the composite
floor is potentially +5,736 vs v15 if no negative interaction.**
