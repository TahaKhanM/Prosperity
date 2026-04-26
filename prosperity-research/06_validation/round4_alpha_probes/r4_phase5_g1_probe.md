# r4_phase5_g1_probe (Phase 1 follow-up)

## Probe definition

- Based on: r4_baseline_v15.
- Replaces v15's per-strike fair IV (`a0 + a1·m + a2·m² + SMILE_PER_STRIKE_BIAS[K]`)
  with a per-strike rolling EMA of observed mid-IV (HL=60 ticks).
- Code review confirmed: IV-domain (NOT price-domain — Phase 8b's bug was that it
  built a price-domain blend instead).
- `IV_EMA_ALPHA = 1 − exp(−ln(2)/60) ≈ 0.01149`.
- Seed per-strike from current observed iv on first valid tick.
- `iv_ema` persisted in `traderData["smile"]["iv_ema"]`.

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Δ vs v15 |
|---|---|---|---|
| day-1 | 1141 | +66,174.50 | −1,450.5 |
| day-2 | 1130 | +87,400.00 | **−20,178.0** |
| day-3 | 1113 | +49,956.50 | +2,385.5 |
| total | 3,384 | **+203,531.00** | **−19,244** |

Per-product:
| product | baseline | probe | Δ |
|---|---:|---:|---:|
| HYDROGEL_PACK | 134,062 | 134,062 | 0 |
| VELVETFRUIT_EXTRACT | 20,419 | 20,419 | 0 |
| VEV_4500 / VEV_4000 | 36,190 | 36,190 | 0 |
| VEV_5100 | 12,078.5 | 4,720.5 | **−7,358** |
| OTHER (V_5000 + V_5200 + V_5300/4/5/6/65) | 17,175 + V_5000 ≈ 17,175 | 5,656 + 2,483.5 = 8,139.5 | **~−9,036** |
| total | 222,775 | 203,531 | **−19,244** |

## Verdict — REJECT

**Ship gate**: Δ ≥ +1,500 AND day-3 ≥ +500 AND per-day Δ ≥ −500.

**Actual**:
- Δ total = −19,244 (FAIL)
- day-1 Δ = −1,451 (FAIL the −500 floor)
- day-2 Δ = −20,178 (catastrophic FAIL)
- day-3 Δ = +2,386 (PASS the +500 floor)

Day-3 PASS validates the directional hypothesis (rolling-IV adapts to late-TTE
better than v15's R3-frozen static bias). But day-1/2 fail catastrophically
because the EMA at HL=60 LAGS TTE regime shifts — the TTE 6→5 transition mid-day-2
takes ~5,000 ticks for the EMA to settle, during which the trader posts at
stale fairs.

## Root cause

Replacing the smile fit with per-strike independent EMAs loses
**CROSS-STRIKE CONSISTENCY**. v15's vega-weighted recovery of `a0_observed`
across the chain enforces a single ATM IV that all strikes share, plus a
deterministic skew/convexity shape. The rolling EMA per strike is independent
— each strike drifts to whatever bias the bots quote, and the trader stops
fighting biased quotes.

The CMU Physics R3 80k → 200k figure was for a DIFFERENT setup; in R4 with
v15's static SMILE_PER_STRIKE_BIAS already approximately right, the swap
LOSES information.

## Lessons for next session

1. **HL too long for TTE shifts.** HL=60 doesn't track day-boundary regime
   changes. Need HL ≤ 20 ticks to track within-day movements + reset at
   day boundaries.
2. **Hybrid not replacement.** Try `fair_iv = 0.5·rolling_iv + 0.5·smile_fit`
   to keep cross-strike consistency while adapting to per-strike drift.
3. **Adaptive bias not adaptive fair.** Compute the residual `iv_obs - iv_smile_fit`
   and EMA THAT as a per-strike adaptive bias replacing the static dict. This
   adds rolling-IV adaptation ON TOP of the smile fit, not in place of it.

The alpha is REAL but cannot be shipped in pure-replacement form.
