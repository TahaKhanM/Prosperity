# Probe: r4_mark_dossier_v02 — dossier-derived counterparty-gated Mark lean

> Phase 7 stretch deliverable from the R4 Mark dossier project (2026-04-26).
> Trader: `prosperity_rust_backtester/traders/Round4/probes/r4_mark_dossier_v02_probe.py`
> Built on top of `r4_mark_lean_v01_probe.py` with the playbook updates from
> `prosperity-research/04_signal_notes/round4/mark_exploitation_playbook.md`.

## Changes vs v01

1. **Counterparty-conditional gating** (`CP_MULT` table): Mark 14/38/49/55
   contributions are scaled by the structural-dyad partner identity. e.g.
   Mark 38 BUY × counterparty=Mark 14 → multiplier 1.0; Mark 38 BUY ×
   counterparty=Mark 22 → multiplier 0.0 (sign flips).
2. **Per-Mark decay**: Mark 67's contribution uses HL ~20 ticks
   (`LEAN_DECAY_FAST = 0.966`) vs the standard HL ~50 (`LEAN_DECAY_DEFAULT
   = 0.986`). Other Marks use the slower default.
3. **Larger Mark 14 / Mark 38 weights on HYD** (0.40 vs v01's 0.20) and on
   VEV_4000 (0.20 vs v01's 0.10).
4. **Mark 22 HYD buy fade** added (n=11 over 3 days; small capacity, high
   precision per the per-product HYD findings).
5. **Smaller Mark 55 weight** (0.10) reflecting tail-driven loss
   distribution.
6. **Lean clamp widened** from ±3.0 to ±5.0 per product.

## 3-day backtest results

```
Trader               | Day 1     | Day 2     | Day 3     | 3-day total
---------------------|-----------|-----------|-----------|-------------
v01 (baseline)       | 67,936.50 | 107,658.50| 48,233.50 | 223,828.50
v02 (dossier-derived)| 67,035.50 | 111,224.50| 46,876.50 | 225,136.50
delta                |   -901.00 |  +3,566.00|  -1,357.00|   +1,308.00
```

**Net delta vs v01: +1,308 XIRECS over 3 days (= +436/day).** Just clears
the +1,000 / 3-day bar from the project brief.

### Per-product attribution

```
PRODUCT          v01 3-day   v02 3-day   delta
HYDROGEL_PACK     134,581     134,438       -143  (~flat)
VFE                20,953      22,404     +1,451  (← all the gain)
VEV_4000           18,684      18,684          0
VEV_4500           17,506      17,506          0
others             32,103      32,103          0
TOTAL             223,827     225,135     +1,308
```

The win is **entirely on VFE** (+1,451). HYD is essentially flat — the
larger Mark 14/38 weights are canceled by the Mark 22 HYD buy fade and the
slight skew/timing change. The VFE win comes from:
- Mark 67 short-horizon mirror (HL 20 vs HL 46 in v01).
- Counterparty-gated Mark 14/38 contribution.
- Newly-added Mark 49 fade and Mark 55 fade rules.

### Per-day stability — BRITTLE

The +3,566 day-2 win is offset by -901 day-1 and -1,357 day-3 losses. The
per-day stability is **POOR**: 1-of-3 days positive vs v01.

This suggests either:
1. The day-2 over-shooting is a fluke that wouldn't replicate, OR
2. The day-1/day-3 mild losses are from too-aggressive HYD weighting that
   needs tuning down.

## Shipping decision

**DO NOT SHIP v02 as-is.** The +1,308 / 3-day delta clears the threshold
but the per-day stability bar (positive on ≥2/3 days) FAILS.

**Recommended next iteration (v03)**:
- Reduce HYD weights from 0.40 back toward 0.30 (compromise between v01's
  0.20 and v02's 0.40).
- Keep the counterparty gating (it's the structural alpha source).
- Keep the Mark 67 fast-decay (it's the cleanest VFE alpha).
- Drop the Mark 55 light fade (low magnitude, tail risk).
- Re-test 3-day stability.

## Reproducer

```sh
cd prosperity_rust_backtester
make round4 TRADER=traders/Round4/probes/r4_mark_dossier_v02_probe.py
make round4 TRADER=traders/Round4/probes/r4_mark_lean_v01_probe.py
```

Compare per-day FINAL_PNL.

## Note on the playbook EV estimate

The playbook §A.3 estimated +1,000–1,650 XIRECS/day delta from Mark 14's
shorter decay + counterparty gating alone. The realised delta is much
smaller (+436/day total). Two reasons:

1. **The v01 baseline already captures most of the structural alpha.** The
   counterparty-gating refinement only helps at the margin — when the
   gating multiplier is 0 (e.g. Mark 38 vs Mark 22), v02 holds back on a
   trade that v01 would have made. But those rare cases (~21 of 1003 HYD
   prints = 2%) don't move the per-day total much.
2. **HYD MM is already saturating capacity.** Increasing the lean weight
   from 0.20 to 0.40 doesn't double our PnL — the position cap of ±200
   units binds, and the wider lean just increases inventory churn without
   capturing more spread.

The playbook EV estimates assumed independent stacking of all rules.
Capacity binds in practice, especially on HYD and VFE position limits.
The realised stacking is much closer to MAX(rules) than SUM(rules).
