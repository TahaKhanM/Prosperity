# R4 follow-up — session summary

Session: 2026-04-26 (follow-up to original alpha hunt).

## What was built

Six standalone follow-up probes targeting the alphas the original session
left unbuilt or misimplemented, plus one composite of survivors.

| Phase | Probe file | Hypothesis | Δ vs v15 | Verdict |
|---|---|---|---:|---|
| 1 | `r4_phase5_g1_probe.py` | per-strike rolling mid-IV (IV-domain replaces smile fit) | **−19,244** | REJECT |
| 2 | `r4_v5000_c02_standalone_probe.py` | imb2 → fair skew on V_5000 only (β=3, cap 1) | **+2,657** | **SHIP** |
| 3 | `r4_chain_02_tte_conditional_probe.py` | TTE-conditional a2 lookup (linear interp) | **−1,000** | REJECT |
| 4 | `r4_chain_01_fvbias_probe.py` | 0.7×Δ_BS portfolio delta as VFE fair-value bias (NOT take) | **−35,892** | REJECT |
| 5 | `r4_mark_lean_v02_no_m67_probe.py` | drop Mark 67 from the lean stack | **+3,079** | **SHIP** |
| 6 | `r4_xprod_v5200_event_take_probe.py` | event-triggered take on V_4000 from large V_5200 prints | **−1,814** | REJECT |
| 7 | `r4_composite_v01_probe.py` | Phase 5 + Phase 2 stack | **+5,735.5** | **SHIP** |

## What passed / what rejected

**SHIP (3 of 7)**:
- Phase 2: V_5000 imb2 skew works as predicted (+2,657 standalone, 100 % on V_5000).
- Phase 5: Removing Mark 67 from the lean is a STRICT improvement (+2,025 vs Probe 1)
  — Mark 67's lean was actively dragging down VFE PnL, not just neutral.
- Phase 7: Composite = lean_v02 + V_5000 imb2 → **+5,735.5 vs v15**, perfect
  additive composition (sum-of-parts +5,736; actual +5,735.5; zero interaction).

**REJECT (4 of 7)**:
- Phase 1 (G1 rolling IV): per-strike independent EMAs lose cross-strike consistency
  that v15's vega-weighted a0 recovery enforces. Day-2 catastrophic (−20k) at HL=60
  due to TTE 6→5 regime lag.
- Phase 3 (TTE-conditional smile): SMILE_PER_STRIKE_BIAS dict was R3-tuned to
  v15's specific (a2_base, drift) combo. Changing a2 alone breaks per-strike alignment.
- Phase 4 (FV-bias hedge): divisor=4 was too aggressive given v15's natural long-voucher
  inventory (D ~200-300 every tick, bias hits ±1 hard cap constantly). VFE crashes
  −35,892. Right alpha, wrong implementation scale.
- Phase 6 (event-take): V_4000 spread (21 ticks) exceeds the +5 tick spillover lift.
  Take-on-V_4000 pays ~16 ticks round-trip slippage; alpha real but not tradeable
  in this form.

## New ship recommendation

**Ship `traders/Round4/probes/r4_composite_v01_probe.py` for the next R4 submission.**

| Trader | 3-day BT | Δ vs v15 baseline |
|---|---:|---:|
| `r4_baseline_v15_probe.py` | +222,775 | — |
| `r4_mark_lean_v01_probe.py` (original session ship) | +223,829 | +1,054 |
| `r4_mark_lean_v02_no_m67_probe.py` (Phase 5 SHIP) | +225,854 | +3,079 |
| **`r4_composite_v01_probe.py` (Phase 7 NEW SHIP)** | **+228,510.50** | **+5,735.5** |

The composite is **5.4× the improvement** of the original session's ship at
locked pre-reg parameters. Per-day positive every day:
- Day 1: +1,361 vs v15
- Day 2: +2,448 vs v15
- Day 3: +1,929 vs v15

## New `Δ vs v15` total

**+5,735.5** — exceeds the stretch target (+5,000) at locked parameters.

## Lessons (what surprised, what was a wasted cycle)

1. **Mark 67 was a NET NEGATIVE leg in the lean stack, not just noise.**
   Removing it didn't just preserve the +1,054 Probe-1 lift — it ADDED
   another +2,025 on VFE alone. The pre-reg decision rule said "ship the
   lighter form if Δ vs Probe 1 ≥ −100". The actual was +2,025 — the
   strongest single-leg gain in this session. The Phase 6 nulls finding
   ("Mark 67 fails both perm and shuffle") was even more critical than
   it appeared at the time.

2. **Composite stacking with disjoint code paths is reliable.** Phase 5
   touches HYD/VFE fair, Phase 2 touches V_5000 fair. Sum-of-parts =
   +5,736; actual composite = +5,735.5 (within 1 shell). No surprise
   interactions when components don't share state or trade product.

3. **Spread cost dominates for take-side alphas on wide-book products.**
   The +5 tick spillover on V_4000 is REAL (Phase 6 nulls source-shuffle
   z=+12-19) but V_4000's 21-tick spread eats the alpha alive. The
   leaderboard-relevant alphas are all on tight-spread products (HYD 16,
   VFE 5, V_5000 6, etc.) or fair-value biases that don't cross.

4. **Replacing the smile fit is destructive.** Phase 1 (G1 rolling IV)
   replaced the fit with per-strike EMAs and lost cross-strike consistency.
   Adaptive bias ON TOP OF the smile fit (i.e., `iv_obs - iv_smile_fit`
   EMA replacing the static `SMILE_PER_STRIKE_BIAS` dict) is the right
   structural form. Not built this session — see #5.

5. **Hedge implementation matters more than hedge formula.** Phase 4
   (FV-bias) failed for the same fundamental reason as Phase 8a (TAKE-form):
   any constant-direction adjustment to VFE quotes overwhelms the existing
   MM. The 0.7×Δ_BS ratio is correct (Phase 6 nulls confirmed holdout PASS)
   but a deadband (no bias when |D| < 100) + larger divisor is required.

## Next-session priorities (probes I would build with another 24 h)

1. **R4-PHASE5-G1-V2 — adaptive bias not adaptive fair.** Compute
   `iv_residual_K = iv_market_K - iv_smile_fit_K` per strike. Maintain
   per-strike EMA of the residual (HL=20 ticks, NOT 60). Use as
   replacement for SMILE_PER_STRIKE_BIAS dict. Keeps cross-strike
   consistency from the smile fit while adapting per-strike drift.

2. **R4-CHAIN-01-V2 — deadband fair-value-bias hedge.** Same 0.7×Δ_BS
   formula but: vfe_fv_bias = 0 if |D| < 100; otherwise (|D|-100) / 12
   capped at ±0.5 ticks. Should add ~+200 to ~+800 if implemented.

3. **R4-XPROD-V5200-V2 — take V_5200 itself, not V_4000.** V_5200 spread
   is 3 ticks vs V_4000's 21. The +5 tick spillover should be visible
   on V_5200 too (since it's the source product). Buy V_5200 at the ask
   when a buyer-initiated print fires.

4. **R4-CHAIN-02-V2 — TTE-conditional smile + zero static bias.** Phase 3
   showed the static dict is calibrated to the specific v15 (a2_base, drift).
   Repeat Phase 3 with `SMILE_PER_STRIKE_BIAS` zeroed; the lookup table
   alone should track measured fit values without bias misalignment.

5. **Re-run nulls on the composite stack** to verify joint
   robustness. Mark-lean alphas survive their nulls weakly; composite
   adds another data point.

## Files written this session

Probe traders (`prosperity_rust_backtester/traders/Round4/probes/`):
- r4_phase5_g1_probe.py
- r4_v5000_c02_standalone_probe.py
- r4_chain_02_tte_conditional_probe.py
- r4_chain_01_fvbias_probe.py
- r4_mark_lean_v02_no_m67_probe.py
- r4_xprod_v5200_event_take_probe.py
- **r4_composite_v01_probe.py (NEW SHIP)**

BT reports (`prosperity-research/06_validation/round4_alpha_probes/`):
- One per probe above (7 total).

Decision log: `prosperity-research/04_signal_notes/round4/followup_decisions.md`
Journal: `prosperity-research/10_experiment_logs/r4_followup_journal.md`
