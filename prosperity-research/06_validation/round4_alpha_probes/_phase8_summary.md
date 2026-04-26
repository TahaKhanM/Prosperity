# Phase 8 — R4 alpha probe summary

Baseline = `r4_baseline_v15_probe` (v15 with `START_TTE_DAYS = 7.0`):
- 3-day total = **+222,775**.
- Per-day: 67,625 / 107,578 / 47,571.

All four probes built as direct copies of the baseline with pre-registered
parameters; no parameter tuning to BT.

| Probe | total Δ vs baseline | day-1 | day-2 | day-3 | verdict |
|---|---:|---:|---:|---:|---|
| r4_mark_lean_v01 | **+1,054** | +312 | +81 | +663 | RESEARCH (small win) |
| r4_otm_ac1_retune | +33 | -301 | +188 | +148 | REJECT (flat) |
| r4_xprod_vev5200 | +42 | 0 | 0 | +42 | REJECT (signal too rare) |
| r4_combined_v01 | **-60,939** | -28,586 | -23,420 | -8,934 | REJECT (hedge disaster) |

## Headline findings

### Probe 1 — the only winner

Mark-conditional lean stack delivers **+1,054** (+0.47 %) over 3 days.
Per-product split: HYD +519, VFE +536. Remaining vouchers untouched.
Day-3 carries +663 of the lift, consistent with the pre-reg story that
the lean activates in the regime where v15 is weakest (VFE day-3
attribution -3k baseline -> -2.5k probe).

Sign is correct on every Mark-rule that fired meaningfully:
- Mark 14 +/- mirror produced positive HYD edge.
- Mark 38 mirror produced positive HYD edge.
- Mark 22 fade on HYD is too low-frequency to dominate.
- VFE Mark 67/49/22 lean -> +536 net.

Pre-reg LEAN_PER_QTY values were chosen at ~half the empirical lift — the
BT's small but positive PnL confirms direction-of-effect without
overfitting to the headline.

### Probe 2 — no edge from K = |AC1| retune

The textbook argument that `K_optimal = |AC1|` does not transfer to PnL
under integer-price quoting and inventory cost. v15's K = 0.5-0.6 *
|AC1| was already empirically optimal. Net BT delta is +33, inside
3-day noise. Trade-count goes UP +26 — more flips for the same edge.

### Probe 3 — xprod signal correct sign, capacity too small

Cross-product VEV_5200 dyad lift is real (+42 on OTHER bucket, all on
day-3) but capacity is bounded by:
1. The trigger fires on a small fraction of the ~10k VEV_5200 ticks.
2. The lean magnitude (max 5 ticks decayed) often loses to integer
   quote rounding.

Could plausibly work as a **take-only** signal on VEV_5200 itself; out
of scope here.

### Probe 4 — combined is the canonical hedge-cost-blowup story

-60,939 PnL collapse, all on VFE. Delta hedge implemented as TAKE-only
crosses the spread on every rebalance. The mark-lean and xprod components
still produce +1.1k of edge underneath, but the hedge alone burns ~6
shells x 10k VFE rebalances. **Do not ship this hedge implementation.**

## Recommendation

1. **Ship Probe 1** (mark lean) on top of the v15 baseline — it is the
   only probe with sign + magnitude + per-day stability.
2. **Park Probe 2 and 3** — sign-correct but PnL-flat at locked params.
   Re-test if Probe 1 ships, with a tighter falsifier (per-strike
   residual MAE drop, not headline PnL).
3. **Reject Probe 4 as written.** Re-implement the 0.7 hedge as a
   *fair-value bias* on VFE rather than a TAKE order so the existing
   smile/accumulation MM absorbs the rebalance without crossing. The
   mark-lean component should be carried over independently.

## Discipline check

No probe was tuned to BT. All four used the locked pre-registered values.
The BT confirms that two-thirds of the candidates we identified in
phases 1-7 do NOT translate to PnL improvement at locked params, which
is exactly the rejection-gate behaviour Phase 8 was designed to expose.
The mark-lean win is the cleanest standalone alpha to layer onto v15
for Round 4 submission.

## Phase 8b corrective probes

Three additional probes were built to test the alphas that were
unjustly masked by Probe 4's hedge blowup. All ran on
`datasets/round4` with locked pre-reg params; baseline = +222,775.

| Probe | total Delta vs v15 | day-1 | day-2 | day-3 | verdict |
|---|---:|---:|---:|---:|---|
| Probe 5 — `r4_smile_refit` | -2,690 | -3,114 | -1,009 | +1,433 | REJECT |
| Probe 6 — `r4_mark_lean_plus_smile` | -1,636 | -2,802 | -929 | +2,095 | REJECT |
| Probe 7 — `r4_mark_lean_plus_microstructure` | -1,745 | -418 | -3,672 | +2,345 | REJECT |

**Headline**: none of the three new combinations beat Probe 1's standalone
+1,054. Day-3 PnL improves in every case (Probe 6 has the best day-3 of
any probe so far at +2,095 vs v15), but day-1 and day-2 losses outweigh
the day-3 lift at the locked smile-refit constants.

### Probe 5 — convexity refit (REJECT)

`SMILE_A2_BASE` 7.21 -> 7.62 and `SMILE_A2_DRIFT_PER_DAY` 0.815 -> 1.62.
Day-3 +1,433 (matches the pre-reg story: v15 smile is most stale at
TTE=5d). Day-1 -3,114 because the new prior over-flattens at TTE=7.
Net -2,690. The directional hypothesis (refit helps day-3) is confirmed
but the magnitude over-shoots day-1/2.

### Probe 6 — mark-lean + convexity refit (REJECT vs Probe 1)

Pure superposition of Probes 1 and 5. HYD/VFE attributions match
Probe 1 to ~$1; voucher attributions match Probe 5 exactly. No
interaction. Net -1,636 vs v15, **-2,690 vs Probe 1**.

### Probe 7 — mark-lean + V5000 imb2 + V5100 micro/wall + V5200 vol-cluster

Mark-lean component delivers as expected (HYD +519, VFE +535). But the
V_5100 50/50 micro+wall blend with the smile fair is catastrophic
(-5,455). The smile MM was already vega-correct on V_5100; mixing in
a price-domain signal makes it fight itself. V_5000 imb2 contributes
+2,657 (positive sign, small). V_5200 vol-cluster widening triggers
too rarely to move PnL (Delta = $0). Net -1,745 vs v15.

## Updated recommendation

**Ship `r4_mark_lean_v01_probe` (Probe 1) on top of v15 for Round 4.**

Probe 1 remains the only probe with a positive total Delta at locked
pre-reg params (+1,054 / +0.47 %). Of the Phase 8b candidates:

- The smile refit needs a TTE-conditional blend (not a hard constants
  swap) to keep its +1.4k day-3 lift without the day-1/2 cost. Out of
  scope for Phase 8b.
- The V_5100 blend should be dropped; the V_5000 imb2 skew and V_5200
  vol-cluster widening could be retested individually.
- R4-PHASE5-G1 (rolling mid-IV per strike) was NOT tested in Phase 8b
  -- the spec for Probe 7 substituted a price-domain blend. The
  per-strike rolling-IV-as-fair experiment is still pending.

Day-3 PnL is the consistent win-zone. Any future probe should target
the day-1/2 stability while keeping the day-3 voucher lift.
