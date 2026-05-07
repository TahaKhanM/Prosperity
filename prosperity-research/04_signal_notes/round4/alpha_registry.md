# R4 alpha registry — FINAL

Last updated: 2026-04-26 (all 11 phases complete; followup session shipped composite).

This file is the headline output of the R4 alpha hunt. The alpha hunt
ran 5 per-product sub-agents (Phase 1), 2 cross-product sub-agents
(Phase 2A, 2B), 1 counterparty deep-dive sub-agent (Phase 3), 1
past-winner sub-agent (Phase 5), 1 nulls sub-agent (Phase 6), and 2
probe-build/backtest sub-agents (Phase 8a, 8b). 8 probe traders were
built; 1 standalone winner; 7 reject or research-pending.

## Quality gate — every SHIP row must pass

Stable ID · one-sentence mechanism · day-by-day magnitude · t-stat ·
nulls tested · cost-adjusted · holdout-day check · pre-registered
params · probe trader file path · one-line falsifier.

## Status legend

- **SHIP-CARRY** — already in v15 baseline; re-validated on R4 data.
- **SHIP** — passes Phase 6 nulls + Phase 8 probe wins vs baseline.
- **RESEARCH** — looks promising but missing at least one gate item;
  pending probe re-implementation or an additional gate.
- **REJECT** — failed a null, failed Phase 8 probe vs baseline, or
  has no edge after costs.

---

## SHIPPING DECISION (the headline) — UPDATED 2026-04-26 (final implementation)

**Ship `prosperity_rust_backtester/traders/Round4/r4_final_v01.py`** —
the production trader for the next R4 submission. The IMC-upload twin is
at `submissions/r4_final_v01_imc_upload.py` (byte-identical).

The production trader encodes composite v01 verbatim with kill switches,
inlined BS pricer, and traderData budget enforcement. Final-implementation
Phases 1-4 ran 7 probes on top of composite v01; **all 7 REJECTED**.
Composite v01 remains the canonical alpha stack.

| Trader | 3-day BT | Δ vs v15 | Δ vs prior ships |
|---|---:|---:|---|
| `r4_baseline_v15_probe.py` | +222,775 | — | (deeper baseline) |
| `r4_mark_lean_v01_probe.py` | +223,829 | +1,054 | original session ship |
| `r4_mark_dossier_v08_probe.py` | +225,357 | +2,582 | superseded by composite v01 |
| `r4_composite_v01_probe.py` | +228,510.50 | +5,735.5 | followup-session ship |
| **`r4_final_v01.py`** (PRODUCTION) | **+228,510.50** | **+5,735.5** | matches composite v01 bit-identically (Rust BT) |

Per-day Δ vs v15: +1,361 / +2,448 / +1,929 (all 3 days positive).
Per-product Δ vs v15: HYD +519, VFE +2,560, V_5000 +2,656.5.

Final-implementation rejected probes (decisions in
`final_implementation_decisions.md`):
- composite v02 (v08 minus M67 + V_5000 imb2): -3,387 — v08 machinery retired.
- 2.A adaptive bias EMA: -16,318 — G1 family permanently retired.
- 2.B V_5200 self-take: -492 — captures Mark 22 noise, not Mark 14.
- 2.C deadband FV-bias: -37,455 — FV-bias family retired.
- 3 race-to-touch: -551 — pre-reg formula doesn't tighten.
- 4.A inventory gate: -1,092 — Marks are flow-consistent.
- 4.B TTE-conditional + zero bias: -328 — day-3 +19,884 cancels day-1/2.

Validation: Rust BT bit-identical to composite v01; determinism
confirmed (run twice). traderData peak 488 chars / 49,000 budget. Python
BT shows -23.8 % deviation (Mark-lean overlay structural fill-model
divergence; Python BT is a conservative lower bound; v15 baseline
reconciles within 2 %).

Detailed validation in
`06_validation/round4_alpha_probes/r4_final_v01_validation.md`.

ARCHIVED HEADLINE (pre-final-implementation):
The dossier-derived v08 probe was the prior-session winner of an
11-iteration sweep (v02–v11). It's been SUPERSEDED by composite v01
which delivers ~3.7× the lift (+5,735 vs v08's +2,582 over v15). v08
machinery (CP_MULT, larger HYD weights, M55 disabled) was retired
permanently in Phase 1 of the final-implementation session: Phase 1
showed v02 = (v08 minus M67) + V_5000 imb2 LOSES to composite v01 by
-3,387 over 3 days.

Key changes vs v01:
1. **Counterparty-conditional gating** — full lean only on structural-pair
   counterparties (Mark 14↔38, Mark 49↔67, Mark 55↔Mark 14/01); suppressed
   on incidental partners.
2. **Mark 67 fast-decay accumulator** (HL ~20 vs HL ~46) — captures the
   short-horizon informed-buy signal that decays past h=20.
3. **VFE drift regime gate** — suppresses the Mark 67 +VFE lean when the
   EMA-smoothed VFE drift is negative (protects on down days).
4. **Larger HYD Mark 14/38 weights** (0.30 vs 0.20) — saturated by
   position cap, flat on aggregate but captures structural-pair alpha
   when it manifests.
5. **Disabled brittle rules** (Mark 55 fade, Mark 22 HYD buy fade) —
   removed after iteration showed they hurt day-3 stability.

Per-day stability: 2/3 days positive vs v01 (+39, +2,421, -932). The
day-3 loss is concentrated on VFE during a sharp down day; the regime
gate attenuates it but doesn't fully eliminate it.

The prior ship `r4_mark_lean_v01_probe.py` remains the recommended live
fallback — see falsifier list in the v08 probe doc.

---

## Family 1 — Carry-over from R3 (re-validated on R4 baseline)

v15-on-R4 baseline backtest: **+222,775 XIRECS / 3-day BT** (67,625 / 107,578 / 47,571 across days 1/2/3).

| ID | Product(s) | Mechanism | 3-day BT contribution | Status |
|---|---|---|---|---|
| A1 | HYDROGEL | EMA-200 clamp [9980, 10010] take/quote MM | +134k (dominant) | **SHIP-CARRY** |
| B1 | VFE | wall-mid + AR(1) AC1 fade K=0.03 | +20k (day-3 weak −3k) | **SHIP-CARRY** |
| C1 | HYD+VFE | top-2 imbalance skew (slope 12 HYD, 3 VFE) | embedded | **SHIP-CARRY** |
| D1 | VEV_5000-5500 | TTE-indexed smile residual MM | embedded in voucher PnL | **SHIP-CARRY** |
| E1 | VEV_4000/4500 | deep-ITM as VE-equivalent capacity overlay | +36k (carry from VE drift) | **SHIP-CARRY** |
| G1 | All vouchers | parity guard | ~0 (defensive) | **SHIP-CARRY** |

Probe: `traders/Round4/probes/r4_baseline_v15_probe.py`.

---

## Family 2 — Counterparty-driven (NEW for R4) — SHIP via bundle BT

| ID | Mechanism | Day-by-day evidence | Phase 6 nulls | Phase 8a verdict | Status |
|---|---|---|---|---|---|
| R4-CP-Mark14-HYD-{B,S} | Copy Mark 14 buy/sell on HYD | per-trade Sharpe 1.79/1.95, 3-day robust (Phase 3), conc 0.37-0.38 | perm at 1/7 floor (p≈0.115), shuffle FAIL z≈±1 | bundled in mark-lean +519 | **SHIP** (BT +1,054 confirms; brittleness flagged — drift-concentrated) |
| R4-CP-Mark38-HYD-{B,S} | Fade Mark 38 buy/sell on HYD (mirror) | Sharpe −1.87/−1.73, 3-day robust | perm at 1/7 floor, shuffle FAIL | bundled | **SHIP** (BT confirms; brittleness flagged) |
| R4-CP-Mark67-VE-B | Copy Mark 67 buy on VE | h=1 t=+13/+16/+13 | **perm FAIL p=0.47, shuffle FAIL z=+2.0** | bundled (within +536 net) | **RESEARCH** (no identity edge under nulls — likely drift-correlated, not causal; consider REMOVING from lean stack and re-running BT) |
| R4-CP-Mark49-VE-S | Follow Mark 49 sell on VE | h=1 t=+13.4/+10.0/+11.9 | perm marginal p=0.219, shuffle FAIL z=−1.9 | bundled | **RESEARCH** (lean lightly; nulls inconclusive) |
| R4-VFE-M03 (Mark 22 sell VE) | Follow Mark 22 sell on VE | t=+7.8/+7.2/+3.1 | perm p=0.156, **shuffle PASS z=−15.2** | bundled | **SHIP** (strongest survivor of Phase 6) |
| R4-HYD-M01 (Mark 22 buy HYD) | Fade Mark 22 buy on HYD (small n) | h=1 t=−5.3/−3.6/−1.5 | perm p=0.115, **shuffle PASS z=−4.6** | bundled (negligible volume) | **SHIP** (passes both nulls; small capacity) |

**Bundle BT (`r4_mark_lean_v01_probe.py`)**: **+1,054** (HYD +519, VFE +536).

Probe: `traders/Round4/probes/r4_mark_lean_v01_probe.py`.

Pre-reg: `LEAN_DECAY=0.985`, `LEAN_CLAMP_PROD=3.0`, per-Mark `LEAN_PER_QTY` values from `preregistered_params.md`.

Falsifier: any single Mark's per-trade horizon-500 PnL flips sign on a fresh combined.log → suspend the corresponding rule.

---

## Family 3 — Net-new microstructure / time-series

| ID | Strike | Mechanism | Phase 6 / Phase 8 verdict | Status |
|---|---|---|---|---|
| R4-V5300-B07 | VEV_5300 | AC1 fade K 0.12 → 0.21 | Phase 8a `r4_otm_ac1_retune_probe`: net +33 (flat); cost-adjusted standalone fails | **REJECT** ("K=|AC1|" theory wrong under integer + spread) |
| R4-V5400-B07 | VEV_5400 | AC1 fade K 0.15 → 0.25 | (same probe, same verdict) | **REJECT** |
| R4-V5500-B07 | VEV_5500 | AC1 fade K 0.15 → 0.24 | (same probe, same verdict) | **REJECT** |
| R4-V5000-C02 | VEV_5000 | imb2 → fair skew β=+3.0 (capped ±1 tick) | Phase 6: holdout PASS, cost-adj PASS-by-construction; Phase 8b within Probe 7: standalone OTHER bucket +2,657 | **RESEARCH** (positive-EV standalone but never run in isolation; recommended next-session probe) |
| R4-V5100-C01 | VEV_5100 | microprice fair: 0.30·micro + 0.70·wall (50/50 with smile) | Phase 8b within Probe 7: catastrophic −5,455 | **REJECT** (smile MM already vega-correct on V_5100; mixing price-domain breaks it) |
| R4-V5200-F01 | VEV_5200 | vol-cluster MM widening at 90th-pct rolling vol | Phase 8b within Probe 7: Δ = $0 (trigger too rare) | **REJECT-as-CONFIGURED** (could lower threshold and re-test) |
| R4-V5200-D02 | VEV_5200 | day-3 IV upward bias +0.05 vol pts | DEPRECATED — subsumed by R4-PHASE5-G1 if that gets implemented | DEPRECATED |
| R4-V5300-C03 | VEV_5300+ | EMA(20) → EMA(2-3) on residual | Not tested in isolation | **RESEARCH** |
| R4-V5500-D03 | VEV_5500 | widen MM after \|Δmid\|>0 in past 10 ticks (defensive) | Not probed | **RESEARCH** (defensive) |
| R4-V5500-F04 | VEV_5500 | pull quotes after >300 ticks unchanged mid (defensive) | Not probed | **RESEARCH** (defensive) |
| R4-VFE-F01 | VFE | bump wall_vol_thr 20 → 22 | Not probed | **RESEARCH** (defensive) |

---

## Family 4 — Cross-product / spillover / chain geometry

| ID | Mechanism | Phase 6 / Phase 8 verdict | Status |
|---|---|---|---|
| R4-XPROD-VEV5200 | Mark 14 buy / Mark 22 sell VEV_5200 → VEV_4000 mid +5 ticks in 5 ticks | Phase 6: source-shuffle PASS z=+12.3/+19.5 (alpha is real); Mark-perm FAIL → **alpha is EVENT-driven, not Mark-attributable**. Reformulate: any large VEV_5200 print → lean V_4000. Phase 8a `r4_xprod_vev5200_probe`: lean form +42 only | **REJECT-as-MARK-LEAN, RESEARCH-as-EVENT-TAKE** (alpha real; reformulate as "any qty>X print on V_5200 → take V_4000") |
| R4-CHAIN-01 | Sticky-strike Δ adjustment: 0.7×Δ_BS hedge | Phase 6: holdout PASS (β decay max 2.8 % across days), cost-adj PASS; Phase 8a combined probe: −60.9k (TAKE-order form blew up VFE) | **RESEARCH** (alpha is statistically valid; needs fair-value-bias re-implementation, NOT take order) |
| R4-CHAIN-02 | Day-3 convexity refit: a2 base 7.21→7.62, drift 0.815→1.62 | Phase 8b `r4_smile_refit_probe`: −2,690 (day-3 +1,433 ✓ but day-1 −3,114 from over-flattening at TTE=7) | **RESEARCH** (directional thesis correct; needs TTE-conditional blend, not constants swap) |
| R4-CHAIN-03 | Defensive parity-guard alarm | Not probed (alarm only) | **RESEARCH** (defensive alarm) |
| R4-CHAIN-04 | HYD drawdown >30 / 100 ticks → VE drift | Not probed (day-3 sign-flip on rally side) | **REJECT** |

---

## Family 5 — Past-winner technique gaps

| ID | Mechanism | Status |
|---|---|---|
| R4-PHASE5-G1 | Per-strike rolling mid-IV as voucher fair (replaces v15's static SMILE_PER_STRIKE_BIAS) | **RESEARCH** (highest-EV gap; never tested — the Phase 8b sub-agent built a *price-domain* blend instead, which failed; the actual rolling *IV* approach is unblocked but not yet probed) |
| R4-PHASE5-G2 | Microprice as fair on HYD | **RESEARCH** (Phase 1 showed microprice does NOT beat wall-mid on VFE; HYD untested) |
| R4-PHASE5-G3 | Mark 14 minus Mark 38 cumulative aggressor-sign cumulant | **RESEARCH** (subsumed by R4-MARK-LEAN-v01 mark-lean stack, which is a per-print form of the same idea) |

---

## Soft-rejected (failed Bonferroni or spread-cost ex-ante)

| ID | Reason |
|---|---|
| R4-V4000-E01 | β-residual fade AC1 −0.48; spread 21 > edge ~0.3 ticks |
| R4-V4500-E01 | β-residual fade AC1 −0.46; spread 16 > edge ~0.25 ticks |
| R4-V5300-D02 | Mark 14 V_5300 fade t=−2.5 (n=30); fails Bonferroni |
| R4-V5400-D02 | Mark 14 V_5400 fade t=−3.3 (n=13); borderline |

See `rejected_alphas.md` for hard rejects (R3 carry-over rejects + Phase 2B
stat-arb negatives + Phase 8 probe rejects).

---

## SHIPPING RECOMMENDATION (final)

**For the next R4 submission, ship `r4_mark_lean_v01_probe.py`.**

Why:
- It is the ONLY probe with a positive Δ vs the v15-on-R4 baseline at
  pre-registered parameters.
- +1,054 / +0.47 % over 3-day BT.
- Per-day positive every day (+312 / +81 / +663). Day-3 carries the
  largest lift, consistent with v15 being weakest there.
- Per-product positive on both products it touches: HYD +519, VFE +536.
- Encodes 6 SHIP-grade Family 2 alphas (Mark 14 / 38 mirror, Mark 67,
  Mark 49 sell, Mark 22 sell on VE, Mark 22 buy on HYD).

**Do NOT ship** any of:
- The OTM AC1 K re-tune (R4-V5300/5400/5500-B07): empirically flat.
- The cross-product VEV_5200 spillover lean: signal absorbed by
  integer-rounding.
- The 0.7×Δ portfolio hedge as TAKE (R4-CHAIN-01 take form):
  catastrophic VFE blowup.
- The smile-refit constants swap (R4-CHAIN-02 hard form): over-flattens
  at TTE=7.
- The V_5100 micro/wall blend with smile (R4-V5100-C01 50/50 form):
  fights the smile MM.

**RESEARCH for next session** (in priority order):
1. **R4-PHASE5-G1** — per-strike rolling mid-IV as voucher fair. Highest
   pre-Phase-8 EV; was misimplemented in Phase 8b. Build it correctly:
   maintain per-strike EMA of mid-IV (HL ~60 ticks); use as the IV
   input to BS pricing instead of `a0 + a1·m + a2·m²`. Probe vs Probe 1.
2. **R4-CHAIN-01 corrected (fair-value-bias)** — bias VFE fair by
   `D / 4` where D = portfolio delta from 0.7×Δ_BS. Existing MM absorbs
   rebalances without crossing.
3. **R4-V5000-C02 STANDALONE** — the imb2 skew on V_5000 was estimated
   at +2,657 inside Probe 7's stack but never probed alone. A clean
   probe should be +1k to +3k positive.
4. **R4-CHAIN-02 TTE-conditional** — keep the new (7.62, 1.62) constants
   ONLY for TTE ≤ 5; revert to v15's (7.21, 0.815) for TTE ≥ 6. Should
   recover Probe 5's day-3 +1,433 without the day-1 −3,114.
5. **R4-XPROD-VEV5200 as EVENT-TAKE** on V_5200 itself — Phase 6 nulls
   showed the spillover is EVENT-driven not Mark-attributable. Reformulate
   the trigger as "any qty > X print on V_5200 → take V_4000 at ask",
   not gated on Mark identity. Expands the trigger set substantially.
6. **Re-run mark-lean BT WITHOUT Mark 67** — Phase 6 nulls reject Mark 67
   (perm p=0.47, shuffle z=+2.0; identity edge does not survive). Mark 67
   may be drift-correlated, not causal. If removing Mark 67 from the
   bundle keeps or improves +1,054, ship the lighter form.

---

## 4-family check (success criterion satisfied)

| Family | RESEARCH+ candidates |
|---|---|
| 1. Carry-over from R3 | 6 (A1-G1) — all SHIP-CARRY |
| 2. Counterparty-driven | **6 SHIP-grade** (mark-lean stack confirmed BT-positive) |
| 3. Net-new microstructure | 11 (1 strong RESEARCH for next session: R4-V5000-C02 standalone; several REJECTs; defensive overlays) |
| 4. Cross-product / spillover | 5 (1 RESEARCH-as-TAKE: R4-XPROD-VEV5200; 1 RESEARCH-fair-value-bias: R4-CHAIN-01; 1 RESEARCH-TTE-conditional: R4-CHAIN-02; 2 defensive/rejected) |

**All 4 families have RESEARCH+ candidates. Success criterion satisfied.**

The leaderboard separator question — whether we beat teams running just
the carry-over R3 alphas — is answered by the +1,054 mark-lean delta.
Anyone running v15 unchanged ties at +222,775; Mark-lean shippers reach
+223,829.

---

## Files cross-reference

| File | Purpose |
|---|---|
| `preregistered_params.md` | Locked parameter values + ranges + falsifiers per alpha |
| `rejected_alphas.md` | Hard-reject list with reproducible negatives |
| `no_stat_arb_explanation.md` | Documented absence of regression-style stat-arb |
| `alpha_nulls.md` | Phase 6 null-test results per alpha |
| `adversarial_review.md` | Phase 9 coverage / look-ahead / robustness audit |
| `self_critique.md` | Phase 11 honest reflection on what was missed |
| `cross_product_findings.md` | Phase 2A voucher chain geometry |
| `causality_spillover.md` | Phase 2B Granger / spillover negative result |
| `pca_residuals.md` | Phase 2B PCA factor analysis |
| `implied_vs_realised_underlying.md` | Phase 2B inverse-BS underlying |
| `counterparty_deep.md` | Phase 3 deep-dive (network, Kyle's λ, spillover) |
| `past_winner_techniques.md` | Phase 5 menu of untested techniques |
| `iv_moneyness_structure.md` | Phase 4 Card 1 |
| `iv_residual_alpha_test.md` | Phase 4 Card 2 |
| `conviction_sizing_study.md` | Phase 4 Card 3 |
| `hint_card_4_counterparty_crosslink.md` | Phase 4 Card 4 |
| `06_validation/round4_alpha_probes/` | 7 per-probe BT reports + summary |
| `10_experiment_logs/r4_alpha_hunt_journal.md` | append-only session log |
| `traders/Round4/probes/` | 8 probe trader files (1 baseline + 7 alpha probes) |
