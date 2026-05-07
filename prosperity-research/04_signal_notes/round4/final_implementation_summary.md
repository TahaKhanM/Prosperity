# R4 Final Implementation — Session Summary

Session: 2026-04-26 (final-implementation; builds on the original alpha
hunt + dossier follow-up).

## Headline

**Ship `prosperity_rust_backtester/traders/Round4/r4_final_v01.py`** with
IMC twin at `submissions/r4_final_v01_imc_upload.py` for the next R4
submission. The trader encodes composite v01 verbatim with kill
switches, traderData budget enforcement, and an inlined BS pricer.

3-day Rust BT: **+228,510.50 (+5,735.5 vs v15 baseline, +2.57 %)**.
Per-day positive every day: +1,361 / +2,448 / +1,929 vs v15.

## What was built (Phases 1-4)

Seven probes on top of composite v01 (`r4_composite_v01_probe.py`,
+228,510.50 floor). Each probe was one dominant change with locked
pre-registered parameters; no BT tuning.

| Phase | Probe | Hypothesis | Δ vs floor | Verdict |
|---|---|---|---:|---|
| 1 | `r4_composite_v02_probe.py` | (v08 minus M67) + V_5000 imb2 | **-3,387** | REJECT |
| 2.A | `r4_adaptive_bias_ema_probe.py` | per-strike EMA replaces static SMILE_PER_STRIKE_BIAS | **-16,318** | REJECT |
| 2.B | `r4_v5200_self_take_probe.py` | event-take V_5200 on aggressive prints | **-492** | REJECT |
| 2.C | `r4_fv_bias_deadband_probe.py` | -D/8 deadband bias to VFE fair | **-37,455** | REJECT |
| 3 | `r4_race_to_touch_probe.py` | inside-touch HYD quoting vs Mark 14 | **-551** | REJECT |
| 4.A | `r4_mark_inventory_gate_probe.py` | per-Mark inventory threshold lean reducer | **-1,092** | REJECT |
| 4.B | `r4_tte_smile_zero_bias_probe.py` | TTE-conditional a2 + zeroed bias dict | **-328** | REJECT |

**Zero ship-grade probes.** The R4 alpha space is well-explored at this
point; the easy wins have been booked, and incremental improvements all
break under the rejection-gate discipline.

## What shipped (composite v01 verbatim)

The production trader encodes composite v01 unchanged:

1. **v15 baseline (carry-over from R3, all SHIP-CARRY)**
   - A1: HYDROGEL soft-anchor MM (clamp toward [9980,10010]).
   - B1: VELVETFRUIT_EXTRACT wall-mid MM with 1-tick AC1 fade.
   - C1: top-2 imbalance skew on VFE.
   - D1: TTE-indexed voucher smile MM (a0+a1·m+a2·m² fit).
   - E1: deep-ITM accumulation overlay on VEV_4000/VEV_4500.
   - G1: parity guard.

2. **R4 SHIP alphas**
   - Mark-conditional lean stack (HYD: M14 mirror, M38 mirror, M22 buy
     fade; VFE: M14 mirror, M38 mirror, M49 sell follow, M22 sell follow).
     **Mark 67 EXCLUDED** (Phase 6 nulls reject; perm p=0.47, shuffle
     z=+2.0).
   - V_5000 imb_k2 → fair-value skew (β=+3.0, cap=±1 tick).

## What was rejected (and why)

1. **v08 dossier machinery (Phase 1).** The +1,528 lift over v01 was
   ENTIRELY the Mark 67 leg. Once Mark 67 is removed (which Phase 6
   nulls require), the rest of v08 (CP_MULT gating, M55 disabled,
   larger HYD weights) is net-negative compared to the simpler v01
   stack. v08 machinery permanently retired.

2. **Adaptive bias EMA (2.A).** Same failure mode as the prior G1
   probe: per-strike EMA tracks empirical IV residual but the v15
   static dict is calibrated for PnL, not residual mean. Replacing the
   dict with an empirical tracker breaks the calibration. Day-2
   catastrophic at the TTE 7→6 transition. G1 family permanently
   retired.

3. **V_5200 self-take (2.B).** Aggressor inference fires mostly on
   Mark 22 prints (the OTM voucher MM is noise). Mark 14's V_5200
   prints are mostly qty=4, below our threshold of 5. Day-3 worst
   (momentum-following on down day).

4. **Deadband FV-bias hedge (2.C).** Even with deadband=100 and
   divisor=8, the bias hits the ±1 cap most ticks because v15's natural
   deep-ITM accumulation pushes |D| ~280. VFE quoting suppressed -22%.
   FV-bias family retired.

5. **Race-to-the-touch (3).** Pre-registered formula
   `bp = min(default_bp, mark14_bid+1)` only LOOSENS our quote (never
   tightens), opposite of "race-to-the-touch." Falsifier triggered:
   HYD trade count DROPPED. The dossier's K.2 hypothesis remains
   plausible but needs a different formula.

6. **Mark inventory gate (4.A).** Threshold of 50 units reached too
   quickly; gates Mark 49's VFE sells spuriously. Marks in our lean
   stack are flow-consistent, not inventory-mean-reverting.

7. **TTE-conditional smile + zero bias (4.B).** Day-3 +19,884 lift on
   V_5200 (TTE 5 = a2 14.11) is real and large, but day-1/2 cancel it
   (-2,636 / -17,576). Static bias dict was tuned for v15's a2
   trajectory; replacing a2 alone with zeroed bias breaks per-strike
   alignment. Need TTE-conditional bias too — outside pre-reg.

## Final BT numbers (production trader)

### Rust backtester (datasets/round4)

| set | own_trades | pnl | composite v01 floor | Δ |
|---|---|---|---|---:|
| day-1 | 1,300 | +68,985.50 | +68,985.50 | 0 |
| day-2 | 1,285 | +110,025.50 | +110,025.50 | 0 |
| day-3 | 1,195 | +49,499.50 | +49,499.50 | 0 |
| total | 3,780 | **+228,510.50** | +228,510.50 | **0** |

**Bit-identical to composite v01.** Determinism confirmed (re-ran twice
with identical numbers).

### Python backtester (`prosperity4bt`)

| day | pnl | Rust | Δ % |
|---|---:|---:|---:|
| 1 | +54,500 | +68,985.50 | -21.0 % |
| 2 | +104,468 | +110,025.50 | -5.1 % |
| 3 | +15,177 | +49,499.50 | -69.3 % |
| total | **+174,144** | +228,510.50 | -23.8 % |

**Structural divergence on Mark-lean overlay.** v15 baseline reconciles
within +1.7 %; V_5000 imb2 alone reconciles within +1.7 %. The Mark-lean
specifically causes the gap (Python BT credits market-trade fills at our
limit price; HYD's 16-tick spread amplifies the difference). Python BT
is a conservative lower bound; still positive every day.

### Per-product attribution (3-day, vs v15 baseline)

| product | Δ vs v15 | source |
|---|---:|---|
| HYDROGEL_PACK | +519 | Mark lean |
| VELVETFRUIT_EXTRACT | +2,560 | Mark lean (Mark 67 EXCLUDED) |
| OTHER (V_5000 only) | +2,656.5 | imb2 skew |
| V_4000/V_4500/V_5100/V_5200 | 0 | (disjoint code paths) |
| **TOTAL** | **+5,735.5** | |

## traderData budget headroom

Across 30,000 ticks of the persisted Rust BT bundle:
- min: 294 chars
- median: 462 chars
- max: 488 chars
- budget: 49,000 chars
- **headroom: 98.96 %**

The compact JSON serialisation (separators=(",",":")) plus float rounding
on `fs`/`mark_lean` (4 decimals) keeps the trader well within budget.

## Kill-switch documentation

Module-level dict in `r4_final_v01.py`:
```
KILL_SWITCHES = {
    "mark_lean":     False,  # True → zero out all counterparty leans
    "v5000_imb":     False,  # True → disable V_5000 imb2 skew
    "adaptive_bias": False,  # reserved
    "race_to_touch": False,  # reserved
    "v5200_take":    False,  # reserved
    "fv_bias_hedge": False,  # reserved
}
```

To trip a switch live: inject `traderData` seed with
`{"kill_switches": {"mark_lean": true}}`. The next tick's run honors it.
The trader resets `KILL_SWITCHES` from the module dict each tick, so
the override needs to persist via prior-tick traderData.

## Falsifier monitoring plan (live R4 day 1)

Per the production trader docstring's "Aggregate falsifier triggers":

1. **Mean h=100 mid-after-Mark-14-print < +2.0 (HYD)**: Mark 14 has
   stopped being the smart bot. → set `mark_lean = True`.

2. **Mark 14 ↔ Mark 38 pairing rate on HYD < 70 %**: dyad has broken;
   the closed loop is gone. → set `mark_lean = True`.

3. **V_5000 imb2 → next-tick Δmid β < +1.5 over any 1k-tick window**:
   imb2 signal has degraded. → set `v5000_imb = True`.

4. **Day-1 PnL < r4_mark_lean_v01 fallback by > 500 XIRECS**: composite
   is underperforming a known-good baseline. → revert to
   `r4_baseline_v15_probe.py` for day 2.

The live monitor stub at
`prosperity_rust_backtester/scripts/round4_options/live_falsifier_monitor.py`
runs these checks against a fresh combined.log.

## Lessons (what surprised, what was a wasted cycle)

1. **The R4 alpha space is well-explored.** Three sessions (original
   alpha hunt + dossier follow-up + this final implementation) have run
   ~25 probes total. The earlier sessions found 4 SHIP-grade alphas
   (mark-lean, V_5000 imb2, V_5200 spillover-as-event,
   delta-fair-value-bias). This session ran 7 incremental probes; **all
   7 REJECTED**. The remaining alphas are knife-edge: small
   under-performance regions all around them.

2. **v08 was a mirage.** The +1,528 vs v01 reported in the prior
   session was entirely the Mark 67 leg. Removing Mark 67 from v08 and
   adding the V_5000 imb2 (composite v02) loses to composite v01 by
   -3,387. v08's CP_MULT gating, larger HYD weights, and disabled M55
   are all NEGATIVE-EV without the Mark 67 leg. The dossier work was
   useful for the playbook understanding but didn't beat the simpler
   form once Mark 67 was excluded.

3. **Pre-registration is unforgiving.** Several probes (race-to-touch
   formula, FV-bias divisor, TTE-conditional + zeroed bias combination)
   showed clear directional signal but failed because the
   pre-registered values weren't optimal. The discipline to NOT tune
   parameters to BT after seeing the result is what makes the rejection
   honest. (Round 3 v12 overfit lesson sticks.)

4. **Backtester reconciliation is structural for lean overlays.** The
   v15 baseline reconciles within 2 % across Rust and Python BTs. With
   the Mark-lean overlay, the gap explodes to 24 %. The Python BT's
   "fill at our limit price" model penalizes lean-shifted aggressive
   quotes more than the Rust BT does. This is structural; not a bug.
   For live submissions, watch BOTH BTs but trust live exchange
   behaviour more than either backtester after day 1.

5. **The static SMILE_PER_STRIKE_BIAS dict is fragile.** Two attempts
   to replace it (G1 in prior session; 2.A in this session) both
   failed. The dict's values aren't empirical residuals — they're
   PnL-tuned values. Any empirical residual tracker drifts away from
   them. Lesson: don't try to replace it without re-tuning the entire
   smile (a0, a1, a2, bias) jointly, which is a major project.

## Next-round priorities (anything left unbuilt)

The R4 alpha space is broadly mined. Remaining ideas (lower priority,
require new infrastructure):

1. **TTE-conditional bias dict + TTE-conditional a2** (joint). 4.B
   showed the day-3 lift potential is +19,884; the day-1/2 cost is
   from per-strike bias misalignment. A joint TTE-conditional bias +
   a2 (one bias dict per TTE bucket) could capture the day-3 win
   without the day-1/2 cost. EV: +5k to +15k. Effort: significant —
   need to fit per-TTE biases, validate that the same MM strategy works
   under each TTE bucket.

2. **Race-to-the-touch with corrected formula.**
   `bp = max(default_bp, mark14_bid+1)` (actually tightens). The
   dossier estimates +1,500 to +4,000 EV. Risk: Mark 14 may react.
   This is a parameter-tuning extension outside this session's scope.

3. **VFE-drift regime gate (without the rest of v08).** v08's regime
   gate on Mark 67 protected on day-3. Could that gating principle
   apply to the existing v01 stack? Specifically, suppress the M14
   buy-side lean when VFE recent return < 0. EV: +200 to +500 (minor).

4. **A joint trader-level null infrastructure.** Run composite v01
   against a permuted-Mark dataset to check joint robustness. Required
   modifying the dataset CSVs in place; significant infrastructure
   work; punted to a future session.

5. **Per-product position-trajectory-conditional take size.** v15's
   take logic uses a fixed `H_TAKE=4`. A position-aware variant could
   take more aggressively when at low inventory and back off when at
   high inventory. EV: speculative; needs careful BT under several
   parameter ranges.
