# VELVETFRUIT_EXTRACT — Round 4 per-product lens battery

## Headline numbers (what's stable, what isn't)
- Mid mean: 5248 / 5255 / 5239; std rising 14.6 / 17.0 / 18.6. Range [5191, 5300].
- Spread locked: median=IQR=5 every day.
- Hurst 0.509 / 0.457 / 0.488; OU half-life 235 / 348 / 297. ρ1 = -0.169 / -0.155 / -0.156 (AC1 fade stable; B1 / v15 K=0.03 holds).
- Level-2 fill rate ~54%; level-3 ~2%. Wall-mid β=0.78 t=39 every day — robust despite sparse depth.
- **Mark 67's edge is the most stable signal in the dataset.** h=1 Δmid +1.99/+1.86/+2.09; t = +16.2/+16.1/+13.1. Mark 49 sell h=1: +1.88/+1.76/+2.07; t = +13.4/+10.0/+11.9.

## Lens A (distributional) — what's surprising
3-5 mid peaks; skew flips (-0.38, -0.33, +0.18). bv1 has **53-54 unique values** (vs 12 on HYDROGEL!). Top bv1 modes are qty 21/22/23 (~480/10000 each).

## Lens B (time-series) — what's surprising
Spectral on first 2k = 2000 / 666 / 2000 looked unstable. **Full 10k Goertzel scan: 2088 / 3296 / 3075 — more coherent (the 666 was a windowing artefact).** Variance ratios drop to ≤0.7 at k=200. CUSUM breaks at 6514 / 7441 / 5043 — different intra-day, no deterministic regime cycle.

## Lens C (microstructure) — what's surprising
- imb_k1 β=0.80 t=29 every day.
- **imb_k2 β = 3.22 / 3.16 / 2.95 in R4 vs 3 in R3 — unchanged.** No re-cal needed.
- imb_k3 β = -18 t=-34 every day (level-3 adversarial, same flavour as HYDROGEL).
- micro-mid β=0.28 t=23 vs wall-mid β=0.78 t=39: wall-mid dominates. Microprice does NOT beat mid+wall.

## Lens D (counterparty conditional return) — what's surprising
- **Mark 67 (buy-only): h=1 +1.99/+1.86/+2.09, t > +13 every day. Mean qty 9, max 15.**
- **Mark 49 sell: h=1 +1.88/+1.76/+2.07, t > +10 every day. Mean qty 10, max 15.**
- **Mark 22 sell: h=1 +1.65/+1.51/+1.25, t = +7.8/+7.2/+3.1** (day-3 weakening but copy still positive).
- Mark 55: noise as documented.
- Mark 14 buy day 2 ONLY: h=1 -0.40 t=-3.5; days 1/3 negligible. Not stable.

## Lens F (weird)
bv1 top modes are qty 21/22/23. **Wall threshold 20 is below the mode floor — bump to 22 to filter the noise floor.**

## Candidate alphas
- **R4-VFE-M01: Copy Mark 67 buy.** Lean +VE 1-5 ticks after Mark 67 prints.
   - Magnitude: +1.99/+1.86/+2.09 per unit at h=1, ≈ +120 XIRECS / day on ~55 prints @ qty 9.
   - t-stat: +16.2 / +16.1 / +13.1
   - Falsifier: t < +5 on any day.
   - Days: all 3.
- **R4-VFE-M02: Copy Mark 49 sell.** Lean -VE after Mark 49 sells.
   - Magnitude: +1.88/+1.76/+2.07; ≈ +60 XIRECS / day on ~35 prints @ qty 10.
   - t-stat: +13.4 / +10.0 / +11.9
   - Falsifier: t < +5 on any day.
   - Days: all 3.
- **R4-VFE-M03: Copy Mark 22 sell.** Lean -VE.
   - Magnitude: +1.65/+1.51/+1.25; ≈ +30 XIRECS / day on ~30 prints @ qty 7.
   - t-stat: +7.8 / +7.2 / +3.1
   - Falsifier: t<2 on any consecutive 2 days.
   - Days: all 3 (day-3 marginal).
- **R4-VFE-F01: Wall threshold bump 20 → 22.** Modes are 21-23.
   - Magnitude: RESEARCH — revalidate B1 backtest after change.
   - Falsifier: B1 PnL drops > 5%.

## Rejected here (do not re-test)
- R4-VFE-D04: Mark 14 / Mark 38 fade — CARRY-OVER, day-2-only signal, not stable.
- R4-VFE-C02: micro-mid → Δmid — REJECTED, wall-mid dominates.
- R4-VFE-E01: VFE ↔ voucher lead-lag — CARRY-OVER reject.
- R4-VFE-B02: VFE → voucher same-tick — CARRY-OVER reject.
