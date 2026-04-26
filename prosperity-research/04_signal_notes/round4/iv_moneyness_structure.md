# Hint Card 1 — IV & Moneyness Structure (R4)

> "The Velvetfruit Extract Vouchers are not just prices on a screen. They have
> structure underneath."

## Per-TTE smile fits (from Phase 2A clean re-fit)

Quadratic form: `IV(m) = a0 + a1·m + a2·m²` where `m = log(S/K)`.
Fit per tick with `iv ∈ (1e-5, 2.0)` to drop stuck-OTM bisection-bound clamps.

| TTE_d | source | a0 (ATM IV) | a1 (skew) | a2 (cvx) | σ_a0 | σ_a1 | σ_a2 |
|-------|--------|-------------|-----------|----------|------|------|------|
| 7 | day 1 | 0.2441 | −0.131 | 7.62 | 0.0063 | 0.152 | 0.75 |
| 6 | day 2 | 0.2466 | −0.228 | 8.53 | 0.0067 | 0.201 | 1.03 |
| 5 | day 3 | 0.2403 | −0.025 | **14.11** | 0.0101 | 0.154 | 1.21 |
| 4 | extrap (live) | 0.2398 | −0.022 | **16.58** | (interp) | (interp) | (interp) |
| 3 | extrap | 0.2379 | +0.031 | **19.82** | (interp) | (interp) | (interp) |

**Headline finding (R4-CHAIN-02): convexity SPIKES from 8.5 → 14.1 between TTE 6
and TTE 5 — a 5σ deformation.** The R3 carry-over surface (a2 ≈ 8.8 at TTE=6) is
DANGEROUSLY WRONG for wing strikes once TTE ≤ 5. v15's `SMILE_A2_BASE = 7.21` and
`SMILE_A2_DRIFT_PER_DAY = 0.815` linear extrapolation underestimates by ~5 vol-pts
of curvature on day 3.

ATM IV is flat at ~0.24 across all TTE buckets. Skew is non-monotonic (−0.13 → −0.23 →
−0.03 → +0.03 extrapolated). The skew sign-flip near TTE = 4 is REAL but the magnitude
is small relative to convexity drift.

**Falsifier**: if live a2 fitted on first 1,000 R4 day-1 ticks < 12, revert to the R3
TTE=6 surface. (Day-3 R4 hist had a2=14.1; live should start at 16-17.)

## Per-strike residual stability (freeze TTE=5 day-3 fit, apply on day-1)

| K | median |residual| (vol-pts) | comment |
|---|---|---|
| 4500 | 0.10 | wing drift |
| 5000 | 0.02 | core stable |
| 5100..5500 | 0.01-0.014 | core stable |
| 6000 | 0.087 | wing drift |
| 6500 | 0.272 | stuck-strike noise |

ATM strikes (5000-5500) are stable to within 1.5 vol-pts; the wings drift more,
which is expected (and consistent with the convexity-spike finding).

## Structural quirks (carry-over from R3, confirmed on R4)

- VEV_4000 / VEV_4500: TV ≈ 0; IV solver returns 0; ALWAYS exclude from D1 scalp.
- VEV_6000 / VEV_6500: stuck at mid 0.50; IV ≈ stuck at solver upper bound;
  ALWAYS exclude from smile fit.
- Smile fit should restrict to K ∈ {4500, 5000, 5100, 5200, 5300, 5400, 5500}
  with `|m| < 0.35` cutoff.

## How v15 uses this (carry-over alpha D1 + E1)

v15's `_smile_voucher_orders` fits the smile per tick using a vega-weighted average,
EMA-smooths a0, and uses the resulting `(a0, a1, a2)` to price each strike. Per-strike
static biases (`SMILE_PER_STRIKE_BIAS`) try to absorb residual mispricings — but R3-
tuned biases are STALE on R4 (e.g., R4 day-3 V_5200 mean residual = +0.085 vs R3-bias
+0.0076).

## How to upgrade for live R4 (alphas)

1. **R4-PHASE5-G1 (per-strike rolling mid-IV)**: Replace v15's static
   SMILE_PER_STRIKE_BIAS with a rolling-mean of mid-IV per strike (HL ~60 ticks).
   CMU Physics (P3 7th) showed this swap took their backtest from 80k to 200k.
2. **R4-CHAIN-02 (convexity refit)**: Bump `SMILE_A2_BASE` and `SMILE_A2_DRIFT_PER_DAY`
   to match the day-3 a2 = 14.1. New constants: A2_BASE = 7.62, A2_DRIFT_PER_DAY = 1.62
   (linear from TTE=7 to TTE=5).
3. **R4-V5300-C03 (residual EMA)**: Replace EMA(20) on residual with EMA(2-3); true
   half-life of residual is 0.2-0.5 ticks.

CSVs:
- prosperity-research/04_signal_notes/round4/term_structure_smile.csv
- prosperity-research/04_signal_notes/round4/vol_surface_residuals.csv (regenerate after
  any smile change)
