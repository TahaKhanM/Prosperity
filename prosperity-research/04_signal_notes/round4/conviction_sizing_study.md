# Hint Card 3 — Sizing by Conviction (R4)

> "If one voucher looks slightly off and another looks significantly off, those
> are not the same signal. Treating them like they are is just lazy."

## What v15 does today

v15's smile-MM uses a FLAT slot size (`SMILE_QUOTE_SIZE = 5`) and only varies
quote width (`edge_shells = max(SMILE_QUOTE_MIN_EDGE, v * SMILE_QUOTE_VEGA_FRAC)`)
based on vega. There is NO conviction-scaling on the residual — every strike with
|res − EMA| > 0.7 vol-pts triggers the same 5-lot quote regardless of how big the
gap is.

## The conviction-scaling idea

For each strike at each tick:
1. Compute residual r_K = IV_K − IV_fit.
2. Compute σ_r,K = rolling 100-tick stdev of r_K (per strike).
3. z_K = r_K / σ_r,K.
4. Position bias size proportional to z_K (with vega weighting and per-strike cap).

For a comparable apples-to-apples flat-vs-conviction PnL comparison, two formulations:

**Flat:** size = SMILE_QUOTE_SIZE if |r_K − EMA(r_K)| > threshold else 0.

**Conviction:** size = SMILE_QUOTE_SIZE × clamp(|z_K|, 0, 3) × vega_weight.
Where vega_weight = vega(K) / max_vega — so high-vega strikes get FULL size,
low-vega strikes (V_5400, V_5500 once OTM) get scaled down.

## Per-strike σ_r values (from Phase 1 / Phase 2A)

| Strike | day-1 σ_r | day-2 σ_r | day-3 σ_r |
|---|---|---|---|
| V_5000 | 0.027 | 0.024 | 0.132 |
| V_5100 | 0.012 | 0.014 | 0.034 |
| V_5200 | 0.018 | 0.018 | 0.024 |
| V_5300 | 0.021 | 0.020 | 0.024 |
| V_5400 | 0.029 | 0.028 | 0.053 |
| V_5500 | 0.035 | 0.034 | 0.075 |

σ_r grows substantially on day 3 — the smile fit is noisier. Conviction
scaling means a 1σ residual on V_5300 (≈ 0.02 vol pts) gets the SAME slot as a
1σ on V_5500 (≈ 0.04 vol pts), but the trade triggers when a strike's z-score
exceeds the per-strike threshold (e.g. |z| > 2).

## Vega weighting (also per Hint Card 3 spirit)

| Strike | day-3 vega (S=5240, σ=0.24, T=5/365) | vega_weight (vs max) |
|---|---|---|
| V_5000 | 380 | 1.00 |
| V_5100 | 365 | 0.96 |
| V_5200 | 305 | 0.80 |
| V_5300 | 220 | 0.58 |
| V_5400 | 132 | 0.35 |
| V_5500 | 65 | 0.17 |

Vega-weighting + conviction-scaling: the ATM-est strike (V_5000) at 1σ residual
gets the same slot as V_5500 at 6σ residual. Defensive against blowing up on
low-vega strikes when the smile-fit residual just looks big because σ_r is small.

## Proposed implementation

In v15's `_smile_voucher_orders`:
- Replace `SMILE_QUOTE_SIZE = 5` constant with a per-strike per-tick sizer:
   ```
   z = (res - ema_res) / max(sigma_res, 0.01)
   size = SMILE_QUOTE_SIZE * min(3.0, abs(z)) * vega_weight
   size = max(0, int(round(size)))
   ```
- σ_res is a per-strike 100-tick rolling stdev tracked in traderData.
- Maintain `SMILE_QUOTE_SIZE = 5` as the BASE; conviction scaling extends it
  to ~15 on a 3σ outlier, retracts to 0 on a 0σ.

## Cap by per-strike vega budget (defensive)

The pre-reg also adds: never let a single strike accumulate to more than
`vega_budget = 100 ticks of total fair-value movement` worth of position.
Equivalently: `pos[K] ≤ vega_budget / vega(K)`. For V_5500 at vega=65, that's
1.5 lots/tick of vega exposure → cap pos at 100/65 ≈ 1.5 → realistically use
the existing CAP_VOU = 300 with a soft cap of 50 on low-vega strikes.

## Falsifier

The conviction-sizing alpha falsifies if:
- The 3σ outliers are NOISE (false positives), in which case the trader will
  take a larger losing position than the v15 baseline. Specifically: if R4
  day-3 PnL on V_5400 / V_5500 with conviction sizing is WORSE than v15
  baseline, conviction sizing died.
- Σ_r becomes very small (V_5100 day-1 σ = 0.012), in which case the z-score
  amplifies noise. Floor σ at 0.015 to prevent z saturation.

## Connection to Phase 5 / Phase 6 / Phase 8

This card is RESEARCH-grade (logic prescribed; not yet implemented or backtested).
The Phase 5 G1 alpha (rolling mid-IV) is a competing simpler upgrade — that one
might capture the same edge without the per-strike σ-tracking complexity. We
should test G1 first, then add conviction scaling on top if G1 leaves residual.
