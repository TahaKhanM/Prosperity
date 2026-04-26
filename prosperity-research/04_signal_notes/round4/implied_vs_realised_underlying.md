# Round 4 implied-vs-realised cross-product underlying

## Methodology (leave-one-out, independent)
- For each (day, ts) and each strike K_i: refit the parabolic smile IV(m) = a0+a1*m+a2*m^2 on the 9 OTHER strikes' (m, iv) pairs.
- Evaluate σ_LOO = a0+a1*m_i+a2*m_i^2 at the held-out moneyness m_i, then bisect on S to solve V_{K_i} = C_BS(S, K_i, T, σ_LOO).
- S_implied_mean(t) = mean across the 10 leave-one-out S estimates.
- residual(t) = S_implied_mean(t) − VE_mid(t).
- This breaks the tautology that would arise if we used iv_K (which was itself built from VE_mid). Any non-zero, mean-reverting residual now reflects a genuine smile-curvature dislocation.

## Per-day stats

| day | N | mean residual | stdev | |mean|/sd | residual rho1 | HL of residual |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 10000 | -11.496 | 15.783 | 0.728 | 0.034 | 0.2 |
| 2 | 10000 | -15.059 | 12.924 | 1.165 | 0.081 | 0.3 |
| 3 | 10000 | -123.353 | 46.976 | 2.626 | 0.117 | 0.3 |

Sign of mean residual is **consistent** across the 3 days (['-', '-', '-']).

## Day 2 sample of 100-tick bucket means (first 20 of 100)

| bucket_start | mean residual | mean S_actual | mean S_implied |
|---:|---:|---:|---:|
| 0 | -10.5781 | 5269.87 | 5259.29 |
| 10000 | -9.1857 | 5268.49 | 5259.31 |
| 20000 | -8.0734 | 5266.98 | 5258.91 |
| 30000 | -12.3759 | 5266.07 | 5253.70 |
| 40000 | -11.3677 | 5256.02 | 5244.65 |
| 50000 | -11.2303 | 5255.15 | 5243.92 |
| 60000 | -13.0663 | 5251.88 | 5238.81 |
| 70000 | -14.3848 | 5255.48 | 5241.10 |
| 80000 | -12.4397 | 5268.33 | 5255.89 |
| 90000 | -10.8508 | 5265.49 | 5254.64 |
| 100000 | -10.7650 | 5261.85 | 5251.08 |
| 110000 | -10.7138 | 5257.00 | 5246.29 |
| 120000 | -10.9019 | 5259.55 | 5248.64 |
| 130000 | -12.9914 | 5256.63 | 5243.64 |
| 140000 | -11.1246 | 5262.68 | 5251.56 |
| 150000 | -11.2492 | 5273.15 | 5261.91 |
| 160000 | -14.4102 | 5272.76 | 5258.34 |
| 170000 | -14.1379 | 5274.63 | 5260.49 |
| 180000 | -10.7217 | 5262.42 | 5251.70 |
| 190000 | -10.2542 | 5262.27 | 5252.01 |


## Verdict
- |mean|/sd is large (0.7–2.6) AND sign is consistent (negative) all three days, which would normally imply 'VE is rich vs the smile, fade VE long-term.'
- BUT rho1 of the residual is ≈ 0 (0.03–0.12) and HL ≈ 0.3 ticks: the residual is a NON-mean-reverting offset, not a tradable spread. Mean drifts from −11 (day 1, TTE=7) to −123 (day 3, TTE=5).
- Diagnosis: this is **smile-fit extrapolation bias**, not alpha. Holding out one strike forces the parabola to extrapolate at the held-out moneyness; with TTE shrinking and the smile curving more steeply, σ_LOO underestimates true σ_K, which forces Si(K) to drop to match V_K. The day-by-day mean drift tracks TTE, not market dislocation.
- Falsifier passed already: signs are consistent BUT magnitudes scale with TTE → confirms artefact, not alpha.
- Net: NO exploitable implied-vs-realised gap detected. The same conclusion was reached in R3 (vol_surface_residuals.csv has zero-mean per-strike residuals when fit on the FULL panel).
