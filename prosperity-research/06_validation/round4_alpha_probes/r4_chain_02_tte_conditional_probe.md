# r4_chain_02_tte_conditional_probe (Phase 3 follow-up)

## Probe definition

- Based on: r4_baseline_v15.
- Single change: `_smile_prior` returns a2 from `_smile_a2_lookup(tte_days)` —
  a per-TTE-day lookup table with linear interpolation between buckets:
  TTE {7: 7.62, 6: 8.53, 5: 14.11, 4: 16.58, 3: 19.82}, clamp at endpoints.
- a0 and a1 untouched (still v15 linear formula).
- `SMILE_PER_STRIKE_BIAS` static dict KEPT (R3-tuned values).

## Backtest result (3-day BT, datasets/round4)

| day | own_trades | pnl | Δ vs v15 |
|---|---|---|---|
| day-1 | 1286 | +67,573.50 | −51.5 |
| day-2 | 1227 | +106,886.00 | −692.0 |
| day-3 | 1164 | +47,315.50 | −255.5 |
| total | 3,677 | **+221,775.00** | **−1,000** |

Per-product:
| product | baseline | probe | Δ |
|---|---:|---:|---:|
| HYDROGEL_PACK | 134,062 | 134,062 | 0 |
| VFE | 20,419 | 20,419 | 0 |
| VEV_4500 / VEV_4000 / VEV_5100 | 47,769 | 47,768 | −1 |
| VEV_5200 | 2,851 | 2,385 | **−466** |
| OTHER (V_5300/5400/5500/6000/6500) | 17,175 | 16,585 | **−590** |
| total | 222,775 | 221,775 | −1,000 |

## Verdict — REJECT

**Ship gate**: Δ ≥ +1,000 AND day-1 ≥ −500 AND day-3 ≥ +1,500.
**Actual**: Δ = −1,000, day-1 = −51 (passes), day-3 = −255 (fails by 1,755).

The lookup matches the per-TTE measured fit values exactly, but
**`SMILE_PER_STRIKE_BIAS` dict was calibrated to v15's specific (a2_base=7.21,
drift=0.815) combination**. Changing a2 alone breaks the alignment between
the parabolic fit and the per-strike bias correction.

Quantitative diagnostic:
- v15 a2 at TTE 7 = 7.21 + 0.815·1 = 8.025 (measured 7.62; v15 OVERSTATES by +0.405)
- v15 a2 at TTE 6 = 8.84 (measured 8.53; OVERSTATES by +0.31)
- v15 a2 at TTE 5 = 9.655 (measured 14.11; v15 UNDERSTATES by −4.46)
- Probe matches the measured value at every bucket.

So my probe LOWERS a2 by ~0.4 at TTE 7 and RAISES a2 by ~4.5 at TTE 5. The
smile re-shapes; the static biases were tuned for the OLD shape; trader
fights itself on the now-mis-aligned wings.

The Phase 8b `r4_smile_refit_probe` had the same root cause but with
constants overshoot (drift 1.62 → a2 9.24 at TTE 7, OVERSTATING by +1.62).
This probe corrects the overshoot but exposes the bias-misalignment.

## Recommendation for next session

Test BOTH together:
1. TTE-conditional a2 lookup AS HERE.
2. Zero out `SMILE_PER_STRIKE_BIAS` (set all to 0.0).

The static biases were R3-tuned and Phase 1 sub-agent confirmed they are
STALE on R4 day-3 anyway (V_5200 day-3 mean residual is +0.085, vs
biased +0.0076). Either:
- Replace the entire static dict with R4-PHASE5-G1 (per-strike rolling
  mid-IV) — DECOUPLES the per-strike adjustment from any specific smile
  shape.
- Re-fit the static biases against the NEW smile shape on R4 days 1+2 (not
  R3 data).

## Falsifier (live)

Confirmed: the alpha is REAL but cannot be shipped in this form. Do not
retry without the bias-decoupling.
