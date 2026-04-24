# Round 3 vol-smile stability report

Source: `prosperity-research/04_signal_notes/round3/vol_surface_coeffs.csv`
(30 000 rows, per-tick quadratic fit of `IV(m) = a0 + a1·m + a2·m²` in
log-moneyness `m = log(S/K)`, year-basis 365, TTE sub-tick-decayed).

## Per-day coefficient summary

| day | TTE (d) | ATM IV (a0) mean | ATM IV std | skew (a1) mean | skew std | convexity (a2) mean | conv std |
|---|---|---|---|---|---|---|---|
| 0 | 8 | 0.2420 | 0.0045 | −0.0107 | 0.073 | 7.21 | 0.34 |
| 1 | 7 | 0.2449 | 0.0068 | −0.0863 | 0.128 | 7.85 | 0.59 |
| 2 | 6 | 0.2475 | 0.0075 | −0.1606 | 0.171 | 8.84 | 0.83 |

Pooled median: ATM IV = 0.2437, skew = −0.077, convexity = 7.70.

## Intra-day stability (per-day only)

Per-day σ(ATM IV) is 0.005–0.008 and ρ₁(ATM IV) is 0.67–0.78. OU half-life
of the ATM IV series is 1.7–2.8 ticks — the ATM IV is **very sticky** at
intra-day scale. Fitting a per-tick smile is therefore robust enough for
live residual work **within** a day.

## Inter-day drift

- **ATM IV rises ~0.003 per day** as TTE shrinks (8→6d: +0.005 total).
- **Skew becomes more negative** by roughly −0.075 per day (−0.01 → −0.16).
- **Convexity rises** by roughly +0.8 per day (7.21 → 8.84).

This is not intra-day noise — it is a **deterministic TTE-drift**. A
frozen-smile trader using day-0 coefficients on day 2 would underprice
skew and convexity and over-trade the residual.

## Residual mean-reversion per strike (axis G)

Per-strike residual `res_K = IV_market(K) − IV_fit(m_K)`, 30 000-tick
series, stats from `stat_tests.py`:

| K | n | mean | std | ρ₁ | OU half-life (ticks) | Hurst | VR(5) |
|---|---|---|---|---|---|---|---|
| 4000 | 2 986 | −0.016 | 0.012 | 0.324 | 0.62 | 0.05 | 0.22 |
| 4500 | 8 823 | +0.019 | 0.025 | 0.213 | 0.45 | 0.02 | 0.20 |
| 5000 | 29 976 | −0.0077 | 0.0066 | 0.183 | 0.41 | 0.00 | 0.20 |
| 5100 | 30 000 | +0.0004 | 0.0064 | 0.408 | 0.77 | 0.00 | 0.20 |
| 5200 | 30 000 | +0.0076 | 0.0044 | 0.402 | 0.76 | 0.00 | 0.20 |
| 5300 | 30 000 | +0.0087 | 0.0042 | **0.683** | 1.82 | 0.01 | 0.20 |
| 5400 | 30 000 | −0.0144 | 0.0053 | **0.772** | 2.68 | 0.01 | 0.21 |
| 5500 | 30 000 | −0.0067 | 0.0054 | 0.616 | 1.43 | 0.03 | 0.22 |
| 6000 | 30 000 | +0.0124 | 0.0081 | 0.726 | 2.17 | 0.01 | 0.20 |
| 6500 | 30 000 | −0.0042 | 0.0044 | 0.441 | 0.85 | 0.01 | 0.20 |

Findings.

1. **All strikes are extremely mean-reverting** in IV-residual space. Hurst
   < 0.05 (vs 0.5 random walk) and VR(5) ≈ 0.20 (vs 1.0 random walk).
2. **Half-life is < 3 ticks** for every strike — mean reversion is so fast
   that you need tick-level decisions. A trader that looks at residuals
   every 10 ticks will see the reversion ride past it.
3. **Residual magnitudes are tiny.** σ(res) of 0.004–0.025 IV points. At
   vega ≈ 5–15 seashells per IV point for near-ATM strikes, that's an
   expected move of 0.02–0.4 seashell per residual reset — below the
   1-tick minimum trade edge. Trading this requires either **very tight
   spreads** (you pay 1 tick to cross) or large aggregate size that the
   book won't supply.
4. **Strike-consistent bias.** Non-zero mean residuals (|mean| ≥ 1σ of
   the series) at K=4500 (+0.019), K=5000 (−0.008), K=5400 (−0.014),
   K=6000 (+0.012). The fit systematically misprices these strikes by a
   constant.

## Frozen-smile recommendation

For a single submission with no refitting:

```python
ATM_IV   = 0.244
SKEW     = -0.077     # log-moneyness coefficient a1
CONV     = 7.70       # log-moneyness coefficient a2
IV(m)    = 0.244 - 0.077 * m + 7.70 * m**2
```

Use this as the **prior** and **refit `a0` only** on rolling 100 ticks of
near-ATM strikes (5000–5400). Do not refit skew or convexity live on 3 days
of data — the `skew std ≈ 0.14` across days swamps the day-0 fit uncertainty.

## Trading implications

- **Scalp only K ∈ {5100, 5200, 5300, 5400, 5500}.** Above that, vega and
  spread kill edge. At K ≤ 4500 the option is not really an option.
- **Watch K=5300–5500 residuals with the longest half-life (1.4–2.7 ticks).**
  These are the best residual-scalp candidates because you have time to fill.
- **Do not trade VEV_6000 or VEV_6500 on residual.** The std (0.0081 / 0.0044)
  × vega is negligible; residuals likely driven by the 1-tick price floor.
- **Expect smile drift day-to-day.** For live Round 3 (TTE = 5d), extrapolate
  skew to ≈ −0.24 and convexity to ≈ 9.9 if the linear drift continues; do
  **not** freeze the day-2 values.
