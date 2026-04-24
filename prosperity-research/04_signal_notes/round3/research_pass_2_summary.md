# Research pass 2 — synthesis

*Deep research on the five axes parked by the first alpha hunt. Five
sub-agents ran R1–R5 in parallel; this memo is the synthesis.*

## TL;DR

| axis | verdict | for the implementation session |
|---|---|---|
| R1 deep-ITM overlay (E1) | **GO post-first-submission** | Do NOT enter v1. Add to a follow-up variant after R2's settlement logic is verified AND an `ask ≤ intrinsic + 1` entry gate is in place. |
| R2 fill-model patch | **GO post-first-submission** | Do NOT hold first submission. Land the `--fill-model tight` CLI flag after v1 ships, then re-evaluate D1. |
| R3 TTE-drift carry (L1) | **PARK** | The drift is real but the butterfly trade loses to structural cost 5–20× the forecast edge. Vega-weighted wing is a possible revisit, but not in this round. |
| R4 HYDROGEL 3330-tick rhythm | **PARK** | Spectral leakage from a slow OU walk. True amplitude ≈ 1.2 seashells peak-to-peak, not 19.5. Phase is incoherent across days. Negative OOS R². A1's EMA-200 anchor already captures the slow drift. |
| R5 deep-OTM naked short | **PARK** | Historical bid = 0, ask = 1 — the 0.5 "mid" is not a fillable price. Empirical tail is ~5,600× fatter than lognormal; max upside ~115 seashells vs downside 100k+ on a tail event. |

Net result: **v1 (A1+B1+C1+G1) stays the first submission**. Exactly
one new shippable improvement (E1 deep-ITM overlay) is queued for
submission 2, conditional on a pre-ship settlement test. No structural
finding from the first alpha hunt survives re-investigation as a
stand-alone tradeable alpha for v1.

## Actionable next steps (for the implementation session)

### For `round3_v1` (first submission)

Nothing changes. Ship A1+B1+C1+G1 per `ship_now.md`. None of R1–R5
produced a v1-shippable alpha.

### Post-first-submission (submission 2)

In priority order:

1. **Verify settlement + land fill-model patch (R2).**
   - Read `R2_fill_model_patch.md`. Implement the `--fill-model tight`
     CLI flag per the spec (current path stays default). Re-run v1 under
     tight fills; expect ≤ 15 % PnL drop. If > 25 %, diagnose before
     resubmitting.
   - Re-evaluate **D1 IV-residual scalp** under the tight model. If PnL
     is still > 0.3 k / day and variance is acceptable, promote D1 to
     `round3_v2_iv_scalp` in the tournament.
   - Note: R2's patch does NOT unblock E1 — E1 is gated on settlement
     logic, not fill logic.

2. **Validate voucher end-of-round settlement, then ship E1 (R1).**
   - Build a probe trader that holds +1 VEV_4000 into the final tick of
     a Round 3 day. Confirm the backtester's cash settlement matches
     `max(S_T − K, 0)`. If it does not, patch before shipping E1 capital.
   - Add the E1 overlay to the tournament as `round3_v2_deep_itm` with:
     - `deep_itm_strikes = [4000, 4500]`
     - Size cap **50 contracts per strike** (not 100), start conservative.
     - Entry gate: **ask ≤ intrinsic + 1**. Do NOT pay retail asks.
     - Stand-alone alpha is 0–1 k / day; primary value is as a hedge
       vehicle for a larger short-vol book.

### What to drop from the Phase-2 plan

Remove these three variants from the implementation prompt's Phase 2:
- `round3_v2_tte_carry` — R3 parked. Butterfly loses to cost.
- `round3_v2_hydrogel_rhythm` — R4 parked. No real phase-locked signal.
- A `round3_v2_otm_short` variant (if the prompt queued one) — R5
  parked. Asymmetric catastrophic tail.

This simplifies Phase 2 to: **v1 baseline → v2_deep_itm → v2_iv_scalp**.
Three variants max, not six.

## Key evidence links

- R1 cache: `_cache/r1_deep_itm_overlay.json` — residual distribution,
  dV/dS beta, book depth show-stoppers.
- R2 cache: see `R2_fill_model_patch.md` §1 (lines 582–780 of runner.rs).
- R3 cache: `_cache/r3_{tte_fit, live_residuals, fly_pnl,
  wingbody_pnl, forecast_vs_realized}.json` — per-day TTE fits and
  butterfly PnL simulation.
- R4 cache: `_cache/r4_hydrogel_rhythm{,_v2}.json` — bucket table,
  phase analysis, harmonic fit R².
- R5 cache: `_cache/r5_{empirical, summary}.json` — lognormal vs
  empirical tail, bootstrap stats, book depth.

## Correction to the published record

`seasonality_report.md` currently cites HYDROGEL's 3330-tick rhythm at
"19.5 seashells peak-to-peak". R4 measured the true amplitude at ~1.2
seashells peak-to-peak once DC leakage is removed. The 19.5 figure
should be struck the next time that report is touched.

## What the next session should pick up

When submission 2 is being prepared:
1. Re-read this file and `R2_fill_model_patch.md` first.
2. Do the settlement probe for E1 before adding deep-ITM capital.
3. Keep the tournament narrow (v2_deep_itm + v2_iv_scalp); do not
   re-introduce R3/R4/R5 variants unless new live data changes the
   verdict.
4. If R5 re-opens in live (visible bid > 0 on VEV_6000/6500, or a
   trade printing ≥ 1), revisit R5 with live data.
