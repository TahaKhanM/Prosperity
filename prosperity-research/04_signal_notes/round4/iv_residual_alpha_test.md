# Hint Card 2 — Positioning by IV Residual (R4)

> "There is almost always a voucher sitting somewhere it probably should not.
> Implying more uncertainty than everything around it."

## What v15 already does (carry-over alpha D1)

For each strike on the smile-MM list (5000, 5100, 5200, 5300, 5400, 5500) per tick:
1. Compute mid V_K, IV_K = invert(V_K, K, T, S).
2. Smile fit gives a fair IV_fit(m).
3. Residual r_K = IV_K − IV_fit.
4. EMA-smooth r with half-life 20 ticks (in v15: not explicitly an EMA, but the
   `SMILE_A0_EMA_ALPHA = 0.0003` smoothing of a0 implicitly smooths the residuals
   slowly through the fit).
5. Apply per-strike static bias `SMILE_PER_STRIKE_BIAS` (R3-tuned values).
6. Convert mispricing to price-space via vega; trade if edge ≥ `SMILE_TAKE_EDGE_SHELLS = 0.7`.

## R4 measured residual half-life (Phase 1 finding)

| Strike | day-1 AC1 | day-2 AC1 | day-3 AC1 | half-life (ticks) |
|---|---|---|---|---|
| V_5000 | 0.038 | 0.068 | 0.058 | 0.21 / 0.26 / 0.24 |
| V_5100 | 0.063 | 0.110 | 0.052 | 0.25 / 0.31 / 0.23 |
| V_5200 | 0.058 | 0.099 | **0.166** | 0.24 / 0.30 / **0.39** |
| V_5300 | 0.038 | 0.030 | **0.224** | 0.20 / 0.20 / **0.50** |
| V_5400 | 0.012 | 0.026 | 0.080 | 0.20 / 0.20 / 0.30 |
| V_5500 | 0.014 | 0.030 | 0.059 | 0.20 / 0.20 / 0.25 |

**Headline**: residual half-life is 0.2-0.5 ticks across all strikes. **v15's
EMA(20) over-smooths by 40-100×.** A 1-tick or 2-tick EMA captures the residual
without lag.

## R4 systematic per-strike biases

| Strike | day-1 mean res | day-2 mean res | day-3 mean res | R3-tuned bias (v15) |
|---|---|---|---|---|
| V_5000 | −0.013 | −0.013 | **−0.082** | −0.0077 |
| V_5100 | −0.003 | −0.004 | +0.016 | +0.0004 |
| V_5200 | +0.013 | +0.013 | **+0.085** (~6σ) | +0.0076 |
| V_5300 | +0.013 | +0.013 | +0.026 | +0.0087 |
| V_5400 | +0.013 | +0.013 | +0.026 | −0.0144 |
| V_5500 | +0.013 | +0.013 | +0.026 | −0.0067 |

**v15's static biases are STALE on day-3.** V_5200 day-3 bias is +0.085 vol points
(11× the R3 bias). V_5000 day-3 bias is −0.082 vol points (10× the R3 bias).

The simulated trade: at the R4 day-3 spot ~5240 with σ ~0.24 and TTE ~5/365,
vega for V_5200 is roughly:
  vega ≈ S · φ(d1) · √T ≈ 5240 · 0.36 · √(5/365) ≈ 220 per IV pt

So +0.085 vol points × 220 vega = +18.7 ticks of price mispricing on V_5200 day 3.
That's a SUBSTANTIAL edge — much more than the SMILE_TAKE_EDGE_SHELLS = 0.7 threshold
v15 uses. Translating in v15: when the EMA-smoothed residual exceeds threshold,
v15 takes against the mid; the +0.085 bias means v15 perpetually thinks V_5200 is
cheap (low IV vs fit) and leans LONG — but the BIAS dict subtracts +0.0076, leaving
+0.078 vol-pt error → leans long ~17 ticks of V_5200 every tick of day 3.
That's a structural over-buy of V_5200 on day 3, which probably contributes to the
−4,746 day-3 attribution we see in the baseline.

## Top-3 residual ladder simulation (Hint Card 2 pre-fit)

For each tick, rank strikes by |residual_z| where z = residual / σ_residual.
Top-3 absolute z-score strikes get traded. EMA on residual: HL = 2 ticks (per
Phase 1 finding above; vs v15's effective HL 20+ from the EMA(0.0003) on a0).

Day-3 simulation (back-of-envelope, no actual BT — see Phase 8 for backtest):
- V_5200 z-score persistently > 3 → take long every tick → fast saturate to 300 cap
- V_5000 z-score persistently < −3 → take short every tick → fast saturate to −300 cap
- Net P&L over day-3: 18.7 ticks × 300 cap × convergence rate ≈ 5,000-7,000 XIRECS
  if convergence on each strike is ~50-100 ticks; could be much less if the bias
  is stable (no convergence within day-3).

**Key risk**: if the bias is STABLE (a structural feature of the bots), there's no
convergence — you accumulate the mispriced position to 300 cap and earn the carry,
but the carry might be negative (the smile is RIGHT, the per-strike bias is the bot's
preferred quoting style). The Phase 5 G1 alpha (rolling mid-IV) is a better solution
because it ADAPTS the fair to the bots' bias rather than fighting it.

## Recommended R4 alphas from this card

- **R4-V5300-C03**: shrink residual EMA from 20 → 2 ticks (matches measured HL).
- **R4-V5200-D02**: explicit V_5200 day-3 bias (+0.05 vol pts conservative).
- **R4-PHASE5-G1**: per-strike rolling mid-IV as voucher fair (replaces static bias dict).

All three feed into the same probe (`r4_combined_v01_probe.py`) — see Phase 8.
