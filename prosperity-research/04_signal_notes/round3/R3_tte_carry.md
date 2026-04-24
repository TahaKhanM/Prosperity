# R3 — Smile TTE-drift carry (axis L1 re-investigation)

Status: **PARK** — signal is real and measurable, but structural butterfly
costs exceed forecast edge by 5–20× on every historical entry.

Cache: `prosperity-research/03_eda/round3/notebooks/_cache/r3_{tte_fit,
live_residuals,fly_pnl,wingbody_pnl,forecast_vs_realized}.json`.

---

## 1. TTE linear models

Per-day means (30 000 per-tick fits aggregated):

| day | TTE (d) | a0 (ATM IV) | a1 (skew) | a2 (convexity) |
|---|---|---|---|---|
| 0 | 8 | 0.24200 | −0.01071 | 7.2145 |
| 1 | 7 | 0.24495 | −0.08635 | 7.8545 |
| 2 | 6 | 0.24745 | −0.16058 | 8.8393 |

OLS `coef ~ TTE_days` — **per-day means** (n = 3) and **per-tick** (n = 30 000):

| coef | per-day slope (σ) | per-day R² | per-tick slope (σ) | per-tick R² | TTE=5 forecast | TTE=4 forecast |
|---|---|---|---|---|---|---|
| a0 | −0.00273 (0.00013) | 0.998 | −0.00274 (4.5e−5) | 0.109 | 0.2503 | 0.2530 |
| a1 | +0.07493 (0.00041) | 1.000 | +0.07470 (9.2e−4) | 0.180 | −0.2357 | −0.3107 |
| a2 | −0.81240 (0.09950) | 0.985 | −0.81279 (0.00440) | 0.533 | **9.594** | **10.407** |

Notes.
- Slope sign: coefficient **drops** with TTE, i.e. convexity **rises** as
  TTE shrinks. Same for |skew|; a0 also rises (−0.00273 × TTE slope).
- Per-tick and per-day slopes agree to three significant figures. The
  three-point per-day fit has tight SE (t = −8.2 for a2); the per-tick
  fit has an absurdly tight SE (t = −185) because it's averaging 10 000
  ticks per day around a very stable daily mean.
- Prediction SE at TTE = 5 (per-day fit): σ(a2) ≈ 0.21, so the 1σ band
  for live day-0 convexity is **a2 ∈ [9.38, 9.81]**.

---

## 2. Live-smile residuals vs frozen-smile residuals

For every tick I computed `r_K = iv_K − (a0(t) + a1(t)·m + a2(t)·m²)`
where the smile coeffs come from the **per-tick** fit (`vol_surface_coeffs.csv`)
and compared to the frozen-smile numbers in `smile_stability_report.md` §G.

| K | frozen μ / σ / ρ₁ / HL | live μ / σ / ρ₁ / HL |
|---|---|---|
| 5100 | +0.0004 / 0.0064 / 0.408 / 0.77 | +0.00044 / 0.00640 / 0.408 / 0.77 |
| 5200 | +0.0076 / 0.0044 / 0.402 / 0.76 | +0.00757 / 0.00439 / 0.402 / 0.76 |
| 5300 | +0.0087 / 0.0042 / 0.683 / 1.82 | +0.00870 / 0.00419 / 0.683 / 1.82 |
| 5400 | −0.0144 / 0.0053 / 0.772 / 2.68 | −0.01445 / 0.00527 / 0.772 / 2.68 |

**They are identical to 3 decimals.** That is because "per-tick smile" and
"frozen smile" are structurally the same object up to a constant: a per-tick
quadratic fit already absorbs the *current* a0/a1/a2. The frozen report's
coefficients are pooled medians; once you subtract the per-tick mean fit
you recover exactly the per-strike bias that axis G measured. The TTE drift
is **between** daily means, not within them — so re-using the per-tick fit
does not improve the residual.

Practical conclusion: the **live** model and the **frozen** model give the
same tick-by-tick residuals. TTE-drift is a between-day, not within-day,
effect.

---

## 3. Butterfly simulations (mid-to-mid, "brief TC" = 4 seashells)

Fly A = −1·5100 + 2·5200 − 1·5300. Fly B = −1·5200 + 2·5300 − 1·5400.
Entry / exit at first tick of entry day / first tick of exit day; the
day-2 leg exits at `ts=999 900` (intra-day proxy).

| fly | day→day | S_entry→S_exit | pnl_raw | pnl_net (4 sh TC) | hedge pnl | pnl_hedged_net |
|---|---|---|---|---|---|---|
| A | 0→1 | 5250→5245 | +0.5 | **−3.5** | +0.15 | −3.35 |
| A | 1→2 | 5245→5267.5 | −3.0 | **−7.0** | −0.68 | −7.68 |
| A | 2→eod2 | 5267.5→5295.5 | +2.5 | **−1.5** | −1.47 | −2.97 |
| A total | — | — | 0.0 | **−12.0** | — | −13.99 |
| B | 0→1 | 5250→5245 | +0.5 | −3.5 | −0.17 | −3.66 |
| B | 1→2 | 5245→5267.5 | +3.0 | −1.0 | +0.96 | −0.04 |
| B | 2→eod2 | 5267.5→5295.5 | −8.0 | −12.0 | +0.97 | −11.03 |
| B total | — | — | −4.5 | **−16.5** | — | −14.73 |

Realistic transaction cost check. Mean day-0 full spreads are
`K=5100: 4.32`, `K=5200: 2.93`, `K=5300: 2.16`, `K=5400: 1.43`. A
market-cross entry + exit pays `Σ|w_k|·spread_k` per cycle. That is
**12.34 seashells** for Fly A and **8.68** for Fly B — 2–3× the 4-shell
assumption in the brief. Using the realistic TC, every single historical
round-trip is −10 to −20 seashells per fly.

---

## 4. Wing-vs-body direct convexity (long 5200, short 5400)

Two-leg variant, TC ≈ 2 seashells per cycle at 1-shell half-spread, or
`spread_5200 + spread_5400 ≈ 4.3` seashells at real spreads.

| day→day | pnl_raw | pnl_net (2 sh TC) | fly_delta | hedge pnl | pnl_hedged_net |
|---|---|---|---|---|---|
| 0→1 | +0.5 | −1.5 | +0.385 | +1.92 | **+0.42** |
| 1→2 | +8.0 | +6.0 | +0.398 | −8.95 | **−2.95** |

Raw-vega (unhedged) this trade **wins** day 1→2 because VE ran +22.5 up
and the long-body call captures more delta. Delta-hedged, it is a
coin-flip: +0.42 then −2.95. The realised convexity increase (a2 rose
+0.99 day1→2) shows up as a tiny gamma/vanna effect relative to the
dominant first-order gamma and the hedging error.

---

## 5. Forecast vs realised for a "pure convexity" fly hold day 0 → eod day 2

Fly A held from day-0 `ts=0` to day-2 `ts=999 900`. Δa2 predicted from
per-day fit = slope × ΔTTE = −0.8124 × −2 = +1.625 vol points.

PnL attribution: `ΔV_fly ≈ (Δa2) · Σ w_k · vega_k · m_k²` where
`m_k = log(S/K)`. At `S = 5250`, TTE 8d:

| K | m | m² | vega | w | w·vega·m² |
|---|---|---|---|---|---|
| 5100 | +0.02899 | 8.4e−4 | 23.49 | −1 | −0.01976 |
| 5200 | +0.00957 | 9.2e−5 | 23.66 | +2 | +0.00434 |
| 5300 | −0.00948 | 9.0e−5 | 23.95 | −1 | −0.00216 |
| sum | | | | | **−0.01758** |

Wait — the m²-weighted vega sum on a symmetric fly is ≈ 0 by construction
(the fly is flat to a2 only to *second order* in strike spacing; log-moneyness
is unequal because strikes are unequal). The raw code returned a sensitivity
of **−0.160**, dominated by the 5100 wing (large |m|).

Forecast PnL = `Δa2 · sensitivity = 1.625 × −0.160 = −0.26` seashells.
Realised PnL = `−V_5100(T) + 2·V_5200(T) − V_5300(T) − (same at t=0) =` **0.0**
(within tick rounding). Forecast and realised are both essentially zero.

**Reason:** a log-moneyness butterfly is a *bet on the 2nd derivative of
IV w.r.t. log-moneyness, evaluated at the fly's centre*. But a2 is a
*global* coefficient — if the smile's mean rises parallel (like a0 does)
the fly pays nothing. Only *local* convexity change around the fly centre
pays off, and the a2 drift is a global quadratic-shape change that barely
distinguishes 5100/5300 from 5200.

---

## 6. Proposed entry rule (would need live corroboration)

*If* we did want to harvest the drift, the cleanest instrument is **not** a
log-money butterfly. It is a **short-vega-near-wing + long-vega-near-ATM**
that captures the skew component too, sized by vega-weighted notional rather
than 1-fly counts. Rule sketch:

- Estimate live smile `(a0, a1, a2)` on rolling 500 ticks.
- Compute forecast at live TTE: `a2_fc = 13.656 − 0.8124·TTE_d`.
- 1σ band = ±0.21. Enter long-convexity when observed `a2 < a2_fc − 0.5σ`
  (≈ 0.10 below forecast) and short-convexity when `a2 > a2_fc + 0.5σ`.
- Instrument: +1 VEV_5100 short + a vega-weighted long of VEV_5300 or
  VEV_5200 to zero out aggregate vega; hedge VE-delta.
- Size cap: 20 contracts per strike, ≤ 50 % of best-level book depth,
  max gross vega 30. That caps single-trade theoretical edge at 0.5–1
  seashell — below break-even once crossing costs are paid.

---

## 7. Falsifier

Abandon if any of the following fires during live Round 3:

- **F1.** On day 0 live, observed 100-tick rolling `a2 < a2_fc(5d) − 1σ`
  (i.e. a2 < 9.38) for > 30 sustained minutes → regime break.
- **F2.** Live day-0→day-1 Δa2 < 0 (convexity fell when it should rise) →
  the TTE-drift reverses or is dataset-specific.
- **F3.** Per-day `a2` SE widens beyond historical std (0.34–0.83) — signal
  would be swamped by intra-day noise.

---

## 8. Verdict

**PARK** for Round 3 submission. Reasons:

1. **Edge is ~0.3 seashell per fly per 2-day hold** (forecast), vs **8–12
   seashell real-spread cost** per round-trip. Negative edge by 1–2 orders
   of magnitude.
2. **Three historical entries, three losses.** Fly A −12 / −14; Fly B
   −16.5 / −14.7 (gross / delta-hedged). This is a 0/6 success rate.
3. **The TTE drift is real** (|t| = 8 on three-point fit; |t| = 185 on
   per-tick fit) but a symmetric butterfly is the wrong lens — a2 moves
   with m², the payoff structure means a global a2 rise does not translate
   into fly PnL. The log-moneyness m-values for {5100, 5200, 5300} at
   S ≈ 5250 are {+0.029, +0.010, −0.009}; |m|² is tiny, so the fly barely
   moves on a2 changes.
4. **Residual stats identical to frozen.** Using the drifting live smile
   as a reference does not expose tradeable scalp residuals that a frozen
   smile misses.

Revisit post-Round-3 with a **vega-weighted wing trade** (no m²-weighting),
or park permanently. Card L1 stays in `alpha_registry.md` as **research-more**
with this note appended.

---

*Methodology:* all computations stdlib Python (no numpy/scipy). BS pricer
and IV solver imported from `prosperity_rust_backtester/scripts/round3_options/bs.py`
read-only. Heavy results cached under
`prosperity-research/03_eda/round3/notebooks/_cache/r3_*.json`. Analysis
script lives at `/tmp/r3_tte_carry_analysis.py` (ephemeral; not committed).
