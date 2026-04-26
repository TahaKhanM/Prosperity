# Round 4 Granger causality and volatility spillover

_Day rows used: day1=10000, day2=10000, day3=10000._

## Methodology
- Granger F-stat: ΔY_t = a + Σ α_k ΔY_{t-k} + Σ β_k ΔX_{t-k}, lags k=1..5.
- Compares restricted (own lags) vs full (own + cross). F threshold for p<0.05 at q=5, n>>k is ~2.21.
- Bonferroni for 12 directional tests * 2 days = 24 → corrected threshold F ≈ 3.0.
- Spillover: rolling 100-tick realised vol; cross-corr at lag k∈[−20,20].

## Granger (causality direction)

| Cause | Effect | F_d2 | F_d3 | n_d2 | n_d3 |
|---|---|---:|---:|---:|---:|
| HYDROGEL | VE | 0.67 | 0.591 | 9994 | 9994 |
| VE | HYDROGEL | 1.55 | 0.92 | 9994 | 9994 |
| VE | VEV_5000 | 37.914 | 38.581 | 9994 | 9994 |
| VEV_5000 | VE | 155.391 | 140.718 | 9994 | 9994 |
| VE | VEV_5100 | 32.58 | 41.015 | 9994 | 9994 |
| VEV_5100 | VE | 142.122 | 139.163 | 9994 | 9994 |
| VE | VEV_5200 | 59.22 | 43.566 | 9994 | 9994 |
| VEV_5200 | VE | 119.762 | 124.234 | 9994 | 9994 |
| VEV_5000 | VEV_5500 | 47.013 | 12.477 | 9994 | 9994 |
| VEV_5500 | VEV_5000 | 2.805 | 1.186 | 9994 | 9994 |
| VEV_4000 | VE | 42.504 | 34.763 | 9994 | 9994 |
| VE | VEV_4000 | 221.246 | 239.631 | 9994 | 9994 |

Interpretation: a directional Granger only means the past of X helps predict ΔY beyond ΔY's own past — at sub-second tick basis it is mostly stale-quote ordering, not exploitable info.

## Volatility spillover (realised vol cross-correlation, day 2)

| Pair | corr(0) | best_lag | best_corr |
|---|---:|---:|---:|
| vol(VE) ↔ vol(VEV_5000) | 0.516 | 0 | 0.516 |
| vol(VE) ↔ vol(VEV_5100) | 0.444 | 0 | 0.444 |
| vol(VE) ↔ vol(VEV_5200) | 0.308 | 0 | 0.308 |
| vol(HYDROGEL) ↔ vol(VE) | -0.039 | 3 | -0.041 |
| vol(VEV_4000) ↔ vol(VEV_5000) | 0.620 | 0 | 0.620 |
| vol(VEV_5500) ↔ vol(VEV_5000) | 0.148 | -1 | 0.148 |

Interpretation: a same-tick correlation > 0.5 with a near-zero best lag means vols co-move but neither leads. Look for asymmetry — e.g. vol(VE) leading vol(VEV_K) by k>0 — to time voucher quoting.

## Conditional response curves (day 2, compact)

Q1..Q5 = quintiles of |ΔX_t|. Cells = E[sign(ΔX_t)·ΔY_{t+1}] | E[sign(ΔX_t)·ΔY_{t+5}].

| Pair | Q1 (h1\|h5) | Q2 | Q3 | Q4 | Q5 | verdict |
|---|---|---|---|---|---|---|
| HYDROGEL→VE | +0.001\|+0.007 | -0.003\|-0.015 | -0.009\|-0.066 | +0.014\|-0.019 | -0.011\|+0.003 | non-mono |
| VE→HYDROGEL | +0.000\|+0.000 | -0.033\|-0.127 | +0.070\|-0.003 | -0.044\|+0.007 | -0.026\|+0.103 | non-mono |
| VE→VEV_5000 | +0.000\|+0.000 | +0.274\|+0.261 | +0.646\|+0.652 | +0.805\|+0.817 | +1.267\|+1.231 | monotone+ |
| VEV_5000→VE | +0.000\|+0.000 | +0.304\|+0.315 | +0.657\|+0.609 | +0.906\|+0.850 | +1.480\|+1.515 | monotone+ |

## Conclusion
- HYDROGEL ↔ VE Granger F < 1.6 both directions, both days → no causal link. Confirms the two products are mechanically independent (not the same factor).
- VE ↔ voucher Granger F is large in BOTH directions (e.g. VE→VEV_5000 F≈38, VEV_5000→VE F≈155). This is contemporaneous co-movement leaking into 1-tick lags via stale quotes — standard high-frequency Granger artefact, not exploitable alpha. The asymmetry (vouchers Granger-cause VE more strongly than the reverse) is consistent with the ATM voucher being more liquid / faster-quoted than VE, NOT with vouchers leading the underlying.
- Spillover: realised vol of VE and ATM vouchers co-move at same-tick (corr 0.3–0.6, best lag = 0). HYDROGEL vol is independent from VE vol (|corr| ≈ 0.04, best lag 3). No exploitable lead.
- Conditional response is monotone for VE→VEV_5000 and VEV_5000→VE — but this is just delta replication (E[ΔVEV/ΔVE] ≈ 0.6 per tick matches the static delta from the smile fit, not new info). HYDROGEL → VE is non-monotone = pure noise.
- Net: no Granger / spillover / conditional alpha that survives the 'is this just contemporaneous co-movement / delta replication?' test.
