# R4 follow-up — append-only journal

Session start: 2026-04-26 (follow-up to original alpha hunt).

## Goal

Build the 6 named, sized, documented opportunities the original alpha hunt
left unbuilt. Stack survivors into a composite that beats the +1,054 ship.

## Phase 0 — context audit (existing probes)

Read all 4 prior probes. Three key findings from CODE INSPECTION (not re-relying
on the prior session's verdicts):

1. **Probe 4 (`r4_combined_v01_probe.py`) hedge mechanism (lines 727–774)**:
   the hedge appends a single TAKE order to `out[VFE]` per tick when |D| > 40,
   targeting needed_qty = |D| − 20. It does NOT replace the existing VFE MM
   legs — they coexist. The blow-up came from the MM legs being already
   spread-tight + the take crossing the same spread aggressively, so the
   existing maker fills get paired with the now-take-driven inventory swing.
   Confirmed: re-implementing as fair-value bias is the right fix — the
   existing MM will absorb naturally.

2. **Probe 7 (`r4_mark_lean_plus_microstructure_probe.py`) V_5100 mistake
   (lines 471–477)**: `fair = (smile_fair + 0.30·micro + 0.70·wall) / 2`.
   This is a PRICE-DOMAIN blend, not the IV-domain rolling mean alpha
   R4-PHASE5-G1 was supposed to be. Confirmed: misimplementation; the
   actual G1 alpha (rolling per-strike mid-IV → BS price) was never tested.

3. **Probe 5 (`r4_smile_refit_probe.py`) constants change**: `SMILE_A2_BASE`
   7.21 → 7.62, `SMILE_A2_DRIFT_PER_DAY` 0.815 → 1.62. These are fed through
   `_smile_prior(tte_days)` which computes `a2 = base + drift × max(0, 8 − tte_days)`.
   At TTE 7 (R4 day 1), drift × 1 = 1.62 → a2 = 9.24. v15 baseline at TTE 7
   gives a2 = 7.21 + 0.815 = 8.03 (closer to the measured 7.62!). So the
   constants change actually OVERSHOOTS at TTE 7 by +1.21 vol-units of
   convexity. This is the day-1 −3,114 in the BT. **TTE-conditional fix:
   keep v15 base for TTE ≥ 6; switch to refit base for TTE ≤ 5.**

## v15 baseline (as starting point)

`r4_baseline_v15_probe.py` BT:
| day | own_trades | pnl |
|---|---|---|
| 1 | 1281 | +67,625 |
| 2 | 1238 | +107,578 |
| 3 | 1162 | +47,571 |
| total | 3,681 | **+222,775** |

Per-product 3-day: HYD +134,062, VFE +20,419, V_4500 +17,506, V_4000 +18,684,
V_5100 +12,078, V_5200 +2,851, OTHER +17,175.

## Current ship (`r4_mark_lean_v01_probe.py`)

3-day BT: +223,829 / Δ +1,054. HYD +519, VFE +536. Day-3 +663 (largest lift).

## Phases to run

| Phase | Probe | Hypothesis | Ship gate |
|---|---|---|---|
| 1 | r4_phase5_g1 | Per-strike rolling mid-IV (IV-domain) replaces SMILE_PER_STRIKE_BIAS | Δ ≥ +1,500 AND day-3 ≥ +500 |
| 2 | r4_v5000_c02_standalone | imb2 skew on V_5000 (β=3, cap 1) | Δ ≥ +1,500 AND V_5000 carries ≥ 80 % |
| 3 | r4_chain_02_tte_conditional | TTE lookup table for a2 | Δ ≥ +1,000 AND day-1 ≥ −500 AND day-3 ≥ +1,500 |
| 4 | r4_chain_01_fvbias | 0.7×Δ_BS as fair-value bias on VFE | Δ ≥ +500 AND VFE trade count drops ≥ 5 % |
| 5 | r4_mark_lean_v02_no_m67 | Drop Mark 67 from lean stack | Δ vs Probe 1 ≥ −100 |
| 6 | r4_xprod_v5200_event_take | Event-triggered take on V_5200 (any qty ≥ 5) | Δ ≥ +200 AND ≥ 10 events fire AND day-3 dominates |
| 7 | composite | stack survivors | Δ ≥ sum-of-parts × 0.7 |

---

## Final results

| Phase | Probe | Δ vs v15 | Verdict |
|---|---|---:|---|
| 1 | r4_phase5_g1 | −19,244 | REJECT |
| 2 | r4_v5000_c02_standalone | **+2,657** | **SHIP** |
| 3 | r4_chain_02_tte_conditional | −1,000 | REJECT |
| 4 | r4_chain_01_fvbias | −35,892 | REJECT |
| 5 | r4_mark_lean_v02_no_m67 | **+3,079** | **SHIP** (replaces Probe 1) |
| 6 | r4_xprod_v5200_event_take | −1,814 | REJECT |
| 7 | **r4_composite_v01 (lean_v02 + V_5000 imb2)** | **+5,735.5** | **NEW SHIP** |

**Composite +5,735.5 = sum-of-parts (+3,079 + +2,657 = +5,736).** Within 1 shell.
Zero negative interaction. All 3 days positive (+1,361 / +2,448 / +1,929).

**5.4× the improvement** of the original session's +1,054 mark-lean ship.

Stretch target met: composite Δ vs v15 ≥ +5,000 ✓.

## Surprises

1. Mark 67 was a NET NEGATIVE leg, not just noise (−2,025 contamination).
   The Phase 6 nulls were prophetic.
2. Composite stacking with disjoint code paths is exactly additive — no
   interaction surprises.
3. V_4000 spread (21 ticks) eats the +5 tick spillover signal alive — alpha
   real but not tradeable as TAKE on this product.
4. Replacing the smile fit (Phase 1) breaks cross-strike consistency badly;
   the smile-fit IS doing useful work even with stale per-strike biases.
5. The 0.7×Δ_BS hedge formula is correct but ANY constant-direction
   adjustment to VFE quotes overwhelms the existing MM. Right alpha,
   wrong implementation scale.

## What was NOT built (next session)

1. R4-PHASE5-G1-V2: adaptive bias EMA on residual (replaces SMILE_PER_STRIKE_BIAS
   only, not the smile fit).
2. R4-CHAIN-01-V2: deadband fair-value-bias hedge (no bias when |D| < 100).
3. R4-XPROD-V5200-V2: take V_5200 itself, not V_4000.
4. R4-CHAIN-02-V2: TTE-conditional smile + zero static bias dict.
5. Re-run Phase 6 nulls on the composite stack.

