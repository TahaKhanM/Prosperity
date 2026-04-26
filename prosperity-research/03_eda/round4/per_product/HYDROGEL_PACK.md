# HYDROGEL_PACK — Round 4 per-product lens battery

## Headline numbers (what's stable, what isn't)
- Mid mean drifts: 9992 / 9989 / 10003 across days; std 38 / 32 / 33; range [9908, 10081]. Confirms the "not pinned at 10000" story.
- Spread is locked: median = IQR = 16 every day. Tightest book always shown at the same level.
- Hurst 0.484 / 0.471 / 0.469; OU half-life 419 / 294 / 314 ticks. Random-walk-with-mean-reversion is stable.
- imb1/imb2/imb3 microstructure t-stats are ROCK-SOLID across days (t≈±31, ±35, -35). Wall-mid β≈0.85 t≈36 every day.
- **Mark 14 / Mark 38 conditional Δmid edge is BRITTLE.** Day 1 h=1 t=±1.8; day 2 collapses to ±0.4; day 3 +1.3/+1.0. The R3 +5.71/-8.34/unit headline number is concentrated in day 1.

## Lens A (distributional) — what's surprising
4–6 mid histogram peaks per day, not 1. Excess kurt negative every day (-0.84 / -0.10 / -0.91): mid is plateau-distributed, not Gaussian. Skew flips sign across days (+0.09, -0.59, -0.22). bv1 has only 12 unique values per day with the top three modes being qty 10/11/12/15 — depth quantum is small.

## Lens B (time-series) — what's surprising
Spectral peak on first 2k = 1000 / 2000 / 2000 — looked stable. **But on the FULL 10k mids (one-off Goertzel scan) the peaks land at 5000 / 1603 / 5000.** No stable rhythm survives — the R3 3330-tick claim does NOT replicate. Variance ratios collapse to ~0.6 at k=200 every day (mean reversion confirmed). CUSUM breaks at idx 7223 / 2790 / 9219 — different location each day, not a structural intra-day regime.

## Lens C (microstructure) — what's surprising
imb_k3 β = -44 every day at h=1 with t=-35 (level-3 adversarial signal — already documented). Wall-mid β=0.85 t=36 dominates micro-mid (β=2.72 but per-unit smaller signal once normalised). imb_k2 still β=+12 t=+35 — C1 alpha holds.

## Lens D (counterparty conditional return) — what's surprising
- **Mark 14 / Mark 38 Day-1-vs-Day-2/3 stability is poor.** Mark 14 buy h=1: +0.27 / +0.07 / +0.20 (t = +1.8/+0.5/+1.3). Mark 38 buy h=1: -0.25 / +0.02 / +0.07. Edge halves from day 1 → days 2/3.
- Mark 14 trade size is UNIFORM (mean 4, max 6) — edge spread, not concentrated in big prints. So no "follow only large Mark 14" filter.
- **Mark 22 buy is a strong NEW adversarial signal on HYDROGEL.** h=1 Δmid: -3.17 / -3.88 / -2.25, t = -5.3 / -3.6 / -1.5. Only 3-4 trades/day so low capacity, but precision is high.

## Lens F (weird)
bv1 mode count ~1700/10000 (qty 10) — same depth quantum used as ASH/PEPPER R1. Mid range covers 170 ticks but only 4-6 detectable peaks → discrete "operating points".

## Candidate alphas
- **R4-HYD-M01: Fade Mark 22 buy on HYDROGEL.** Sell into 1–5 ticks ahead when Mark 22 prints buy.
   - Magnitude: -3.17/-3.88/-2.25 per Mark-22-buy unit at h=1; aggregate ≈ 30 XIRECS / day if we capture full move.
   - t-stat: -5.3 / -3.6 / -1.5
   - Falsifier: Mark 22 buy n<3 in any sub-day.
   - Days: all 3 (t≥1.5).

## Rejected here (do not re-test)
- R4-HYD-D01: Copy-Mark-14 / Fade-Mark-38 unaltered — CARRY-OVER but with caveat: edge brittleness flagged. Recommend confirmation gate (min Mark-14-trades-in-window) before sizing.
- R4-HYD-B05: spectral 3330-tick rhythm — REJECTED, no stable peak across 3 days.
- R4-HYD-B01: 1-tick AC1 fade — CARRY-OVER reject (ρ1=-0.124 every day, spread cost still > edge).
- R4-HYD-C03: imb_k1, imb_k2, wall-mid — CARRY-OVER (already shipped C1).
- R4-HYD-C04: imb_k3 negative β skew — CARRY-OVER reject.
