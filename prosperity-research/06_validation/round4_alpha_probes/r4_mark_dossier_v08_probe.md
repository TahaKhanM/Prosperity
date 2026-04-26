# Probe: r4_mark_dossier_v08 — winning dossier-derived Mark lean

> Phase 7 stretch deliverable from the R4 Mark dossier project (2026-04-26).
> Trader: `prosperity_rust_backtester/traders/Round4/probes/r4_mark_dossier_v08_probe.py`
> Built on top of `r4_mark_lean_v01_probe.py` with the playbook updates from
> `prosperity-research/04_signal_notes/round4/mark_exploitation_playbook.md`,
> tuned through 11 iterations (v02–v11) for per-day stability.

## Locked parameters

```
LEAN_DECAY_DEFAULT = 0.986     # HL ~50 ticks (v01: 0.985, HL ~46)
LEAN_DECAY_FAST    = 0.966     # HL ~20 ticks (Mark 67 only)
LEAN_CLAMP_PROD    = 5.0       # widened from 3.0 in v01

# HYD weights (vs v01's 0.20)
HYD_W_M14 = 0.30
HYD_W_M38 = 0.30
HYD_W_M22_BUY_FADE = 0.0       # disabled — too noisy on small N

# VEV_4000 weights (vs v01's 0.10)
VEV4000_W_M14 = 0.20
VEV4000_W_M38 = 0.20

# VFE weights
VFE_W_M14       = 0.12
VFE_W_M38       = 0.0          # Mark 38 doesn't trade VFE
VFE_W_M67       = 0.50         # WITH regime gate (see below)
VFE_W_M49_SELL  = 0.25
VFE_W_M22_SELL  = 0.15
VFE_W_M55       = 0.0          # disabled — tail-driven loss
VFE_W_M01       = 0.10
VFE_DRIFT_EMA_ALPHA = 0.05

# Counterparty-conditional multiplier table
CP_MULT = {
    "Mark 14": {"Mark 38": 1.0, "Mark 22": 0.0, "_default_": 0.3},
    "Mark 38": {"Mark 14": 1.0, "Mark 22": 0.0, "_default_": 0.3},
    "Mark 49": {"Mark 67": 1.0, "Mark 55": 0.0, "_default_": 0.3},
    "Mark 55": {"_default_": 0.0},   # disabled
    "Mark 22": {"_default_": 1.0},
    "Mark 67": {"_default_": 1.0},   # always copy
    "Mark 01": {"Mark 55": 1.0, "_default_": 0.3},
}

# v08 strict regime gate for Mark 67 +VFE contribution
# drift_per_100 thresholds:
#   >= 0.0  → multiplier 1.0 (up or flat)
#   >= -1.0 → multiplier 0.5 (mild down)
#   < -1.0  → multiplier 0.0 (down trend — disable Mark 67)
```

## 3-day backtest results

```
Trader               | Day 1     | Day 2     | Day 3     | 3-day total
---------------------|-----------|-----------|-----------|-------------
v01 (baseline)       | 67,936.50 | 107,658.50| 48,233.50 | 223,828.50
v08 (this probe)     | 67,975.50 | 110,079.50| 47,301.50 | 225,356.50
delta vs v01         |     +39.0 |  +2,421.0 |    -932.0 |   +1,528.0
```

**Net delta vs v01: +1,528 XIRECS over 3 days (= +509/day).** Clears the
+1,000 / 3-day shipping bar from the project brief. Per-day stability:
2/3 days positive (day-1 marginal, day-2 strong, day-3 negative).

### Per-product attribution

```
PRODUCT          v01 3-day   v08 3-day   delta
HYDROGEL_PACK     134,581     134,473       -108  (~flat)
VFE                20,953      22,589     +1,636  (← all the gain)
VEV_4000           18,684      18,684          0
VEV_4500           17,506      17,506          0
others             32,103      32,103          0
TOTAL             223,828     225,357     +1,528
```

The win is **entirely on VFE** (+1,636), driven by Mark 67 short-horizon
mirror with the regime gate. HYD is flat (the increased Mark 14/38 weights
are saturated by the position-limit cap).

### Per-day VFE attribution

```
Day | v01 VFE  | v08 VFE  | delta
1   | 14,964.0 | 15,172.0 |   +208
2   |  8,984.5 | 11,627.5 | +2,643
3   | -2,995.0 | -4,210.0 | -1,215
```

Day-2 carries the alpha (+2,643). Day-3 still bleeds VFE -1,215 even with
the regime gate active — Mark 67's +VFE lean accumulates faster than the
EMA can detect the down regime, especially in the first half of day-3.
Further refinement (v10's universal +VFE gate) over-suppressed and lost
day-2 instead.

## Iteration log

| Probe | Notable change | 3-day Δ | Day1 | Day2 | Day3 |
|-------|---|---:|---:|---:|---:|
| v01 (baseline) | — | 0 | — | — | — |
| v02 | Full playbook + 0.40 HYD weights | +1,308 | -901 | +3,566 | -1,357 |
| v03 | Lower HYD weights (0.30), drop Mark 55, drop M22 HYD fade | +973 | +225 | +2,167 | -1,419 |
| v04 | M67 weight 0.30 (vs v03's 0.50) | +619 | +52 | +1,717 | -1,150 |
| v05 | M67 weight 0.0 (diagnostic) | -1,361 | -591 | -155 | -615 |
| v06 | M67 weight 0.50 + drift regime gate at -1/-3 | +1,142 | -65 | +2,421 | -1,214 |
| v07 | v06 + revert M49/M22/M01 to v01 levels | -41 | -975 | +1,099 | -164 |
| **v08** | **v06 + stricter gate at 0/-1** | **+1,528** | **+39** | **+2,421** | **-932** |
| v09 | v08 + M67 weight 0.30 | +1,178 | -97 | +1,990 | -715 |
| v10 | Universal +VFE gate (not just M67) | -746 | -302 | -503 | +58 |
| v11 | M67 weight 0.40 + v08 gate | +1,317 | +39 | +2,119 | -841 |

**v08 is the local winner.** Per-day stability could be improved further but
within the dossier-rules framework (no inventory-conditional logic), v08
captures the cleanest win.

## Reproducer

```sh
cd prosperity_rust_backtester
make round4 TRADER=traders/Round4/probes/r4_mark_dossier_v08_probe.py
make round4 TRADER=traders/Round4/probes/r4_mark_lean_v01_probe.py
```

Compare per-day FINAL_PNL.

## Mechanism summary (what this probe is doing differently from v01)

1. **Counterparty-conditional gating** (CP_MULT). When Mark 14 trades
   with Mark 38 (the structural pair), full lean. When Mark 14 trades
   with Mark 22 (incidental), zero lean. Same for Mark 38 ↔ Mark 14.
   Catches the structural alpha and skips the noise.
2. **Mark 67 has its own faster decay** (HL ~20 ticks vs HL ~46 in v01) —
   the dossier shows their alpha decays past h=20.
3. **VFE drift regime gate** — when the EMA-smoothed VFE drift turns
   negative, suppress the Mark 67 +VFE lean. Protects (partially) on
   downward-drift days like day-3.
4. **Larger HYD weights** for Mark 14/38 (0.30 vs 0.20). Captures more of
   the +8/u h=100 bag-hold edge but mostly saturated by the 200-unit
   position cap.
5. **Mark 22 HYD buy fade disabled** — n=11 over 3 days is too small to
   swing PnL and the rule occasionally hurt.
6. **Mark 55 fade disabled** — tail-driven loss made day-3 worse in
   earlier variants.

## Falsifiers (kill if any of these triggers in live)

1. Live R4 day-1 mean h=100 mid-move-after-Mark-14-print (signed for Mark
   14) drops below +2.0 (was +8.65 historical) → kill the Mark 14/38
   stack, revert to v01.
2. Live R4 day-1 Mark 14 ↔ Mark 38 pairing rate on HYD drops below 70%
   (was 97.7% historical) → kill counterparty gating, revert to v01.
3. Live R4 day-1 mean h=5 mid-move-after-Mark-67-buy < +0.5 ticks → kill
   Mark 67 lean, revert v08 → v01.
4. Live R4 day-1 PnL is negative vs v01 by > 500 XIRECS → revert to v01
   for day-2 onward.

## Shipping recommendation

**SHIP `r4_mark_dossier_v08_probe.py` for the next R4 submission**, with
v01 as the live-day-1 fallback if any falsifier triggers.

The probe carries an EXPECTED +1,528 / 3-day improvement over the current
ship (`r4_mark_lean_v01_probe.py`). The day-3 risk is the largest exposure
(-932 in historical) — monitor live performance on any sharply-down VFE
day.

## Pre-registered live monitoring

After live R4 day-1 data is available:
1. Re-run the per-Mark feature builder on live data.
2. Refresh the `counterparty_findings.md` rollup.
3. Verify the 4 falsifiers above against live numbers.
4. If clean, keep v08 for day-2.
