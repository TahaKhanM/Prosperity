# Round 4 PCA / principal-component residuals

## Variance explained

| PC | eigenvalue | share | cumulative |
|---|---:|---:|---:|
| PC1 | 6.0823 | 49.57% | 49.57% |
| PC2 | 4.7043 | 38.34% | 87.90% |
| PC3 | 0.7913 | 6.45% | 94.35% |

PC1 dominance: HYDROGEL has its own ~10000 axis; VE has its ~5240 axis. The 12-product cov matrix has highly heterogeneous variances (HYDROGEL stdev ≈ 1.4 per tick vs VE ≈ 0.6 vs deep-OTM vouchers ≈ 0). PC1 will load mostly on the highest-variance axes. The variance share is therefore not the same as 'fraction of common factor' — interpret loadings with stdev in mind.

## PC loadings (read with stdev)

See `pca_loadings.csv`. Sanity: PC1 should put high weight on VE (the underlying), midweight on ATM vouchers, ~0 on stuck deep-ITM/OTM.

## Per-product residual diagnostics
Residual = r_i(t) - Σ_k load_{i,k} * f_k(t). Half-life is computed on the cumulated residual (pseudo-price); rho1 is on the residual return itself.

| Product | stdev raw | stdev PC1-res | stdev PC1+2-res | rho1 PC1-res | rho1 PC1+2-res | HL PC1-res | HL PC1+2-res |
|---|---:|---:|---:|---:|---:|---:|---:|
| HYDROGEL | 2.169 | 2.169 | 0.001 | -0.124 | -0.427 | 356.290 | 164.285 |
| VE | 1.138 | 0.717 | 0.717 | -0.469 | -0.469 | 32.509 | 32.530 |
| VEV_4000 | 1.452 | 0.526 | 0.526 | -0.419 | -0.419 | 116.263 | 116.902 |
| VEV_4500 | 1.277 | 0.408 | 0.408 | -0.472 | -0.472 | 75.518 | 75.784 |
| VEV_5000 | 0.995 | 0.328 | 0.328 | -0.466 | -0.466 | 36.549 | 36.448 |
| VEV_5100 | 0.874 | 0.343 | 0.343 | -0.456 | -0.456 | 109.113 | 108.506 |
| VEV_5200 | 0.681 | 0.348 | 0.348 | -0.455 | -0.455 | 312.040 | 313.538 |
| VEV_5300 | 0.478 | 0.335 | 0.335 | -0.454 | -0.454 | 302.853 | 302.612 |
| VEV_5400 | 0.254 | 0.212 | 0.212 | -0.387 | -0.387 | 220.015 | 220.728 |
| VEV_5500 | 0.159 | 0.150 | 0.150 | -0.285 | -0.285 | 169.070 | 169.584 |
| VEV_6000 | 0.000 | 0.000 | 0.000 | nan | nan | nan | nan |
| VEV_6500 | 0.000 | 0.000 | 0.000 | nan | nan | nan | nan |

## Candidate alphas
- All non-stuck products show negative rho1 on PC1-residual returns (rho1 = −0.29 to −0.47). This is consistent with the rest of the EDA: every algo product mean-reverts at the tick scale (half spread bounce). It is NOT a new alpha — it is the same B1/C1 mid-fade signal already captured by per-product MM and imbalance skew.
- HYDROGEL PC1+2-residual shows rho1 = −0.43 with HL = 164. Read with extreme caution: PC2 absorbs ~100% of HYDROGEL's variance because it has the largest single-product stdev (PC2 loading on HYDROGEL is 1.0, all others ≈ 0). The 'residual' is therefore numerical leftover, NOT independent information. This is an artefact of variance-based PCA on an unscaled, heterogeneous-variance asset universe.
- Verdict: PCA on raw mid returns (no normalisation) reveals NO new stat-arb leg. The two visible factors are 'HYDROGEL alone' (PC2) and 'VE complex' (PC1) — both already exploited by existing alphas.

## Falsifier
- If we standardise (scale each product to unit variance) before PCA, PC1 should still load on every VE-cluster product roughly proportionally to delta. Any product whose standardised residual half-life is <200 ticks AND whose loading is stable across days IS a real stat-arb leg. Deferred — see workplan.
