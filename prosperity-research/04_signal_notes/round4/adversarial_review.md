# Adversarial review (Phase 9)

I am red-teaming my own R4 alpha hunt. The job is to find the gaps before the
leaderboard does.

## 1. Coverage check (12 products × 6 lenses A-F)

| Product | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| HYDROGEL_PACK | ✓ | ✓ | ✓ | ✓ | n/a | ✓ |
| VELVETFRUIT_EXTRACT | ✓ | ✓ | ✓ | ✓ | n/a | ✓ |
| VEV_4000 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VEV_4500 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VEV_5000 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VEV_5100 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VEV_5200 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VEV_5300 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VEV_5400 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VEV_5500 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| VEV_6000 | ✓ | n/a | n/a | ✓ | ✓ | ✓ |
| VEV_6500 | ✓ | n/a | n/a | ✓ | ✓ | ✓ |

VEV_6000 / VEV_6500 lens B / C are n/a because std=0 (stuck at 0.5 mid; no
microstructure to study). All other cells have at least one numeric finding
in the per_product/<symbol>.md file. **Coverage: 12/12 products, 64/72 lens
cells (the 8 n/a are by-construction).**

## 2. Multiple-testing audit

Total per-Mark conditional return tests across Phase 1 + Phase 3:
- Lens D: 7 Marks × 12 products × 4 horizons × 2 sides ≈ 670 tests.
- Phase 3.7 cross-product: 660 (Mark, source, target, horizon) cells.

We applied:
- Phase 3.7: explicit Bonferroni |t| > 4 + lift > 50 % → 13 of 660 surviving.
- Phase 2B (cointegration): explicit Bonferroni |t| > 3.4 → 1 of 14 (and that
  one is tautological).
- Phase 1 lens D: NOT explicitly Bonferroni-corrected. The headline Mark 14 /
  Mark 38 / Mark 67 / Mark 49 alphas all clear |t| > 10 on at least one day,
  which clears any reasonable per-test correction. The marginal alphas
  (Mark 22 HYD fade, Mark 22 VFE day-3 t = +3.1, Mark 14 VEV_5300 t = −2.5)
  do NOT clear Bonferroni — they are PROBABLY noise.
- Phase 1 lens C (microstructure): not Bonferroni-corrected; t-stats > 20
  on the surviving alphas (imb1/imb2 across vouchers); they clear any
  correction.

### Alphas that fail multiple-testing correction

| Alpha | t-stat | Bonferroni threshold (~3.5) | Survives? |
|---|---|---|---|
| R4-HYD-M01 (Mark 22 HYD fade) | t=−5.3/−3.6/−1.5 | YES on days 1+2, NO on day 3 | MARGINAL |
| R4-VFE-M03 (Mark 22 VFE sell follow) | t=+7.8/+7.2/+3.1 | YES days 1+2, MARGINAL day 3 | MARGINAL day 3 |
| R4-V5300-D02 (Mark 14 V_5300 fade) | t=−2.5 | NO | DOWNGRADE to RESEARCH |
| R4-V5400-D02 (Mark 14 V_5400 fade) | t=−3.3 | borderline | DOWNGRADE to RESEARCH |

## 3. Look-ahead audit

For each alpha, I ask: does any input feature use information from after the
trade-time?

- **Mark-conditional alphas**: The per-Mark lean is computed off `state.market_trades`,
  which contains trades the bot ALREADY observed before the current tick. No
  look-ahead. ✓
- **Microstructure (imb, microprice, wall-mid)**: Computed off `state.order_depths`
  which is the CURRENT-tick book. No look-ahead. ✓
- **Cross-product spillover (R4-XPROD-VEV5200)**: Triggered by the VEV_5200 print
  event, action is on the deeper-ITM strike at the SAME or LATER tick. The
  measurement of "+5 ticks of mid move in the next 5 ticks" used `mid_at_or_after`
  which strictly takes mids at or after the print's timestamp. No look-ahead. ✓
- **AC1 fade re-tune**: The fade uses `mid_t - mid_{t-1}`, both observable. No
  look-ahead. ✓
- **R4-CHAIN-01 (sticky-strike Δ)**: The 0.7 ratio is measured from historical
  data; in live use, the trader applies the constant. No live-time look-ahead. ✓
- **R4-CHAIN-02 (convexity refit)**: The refit is offline; live trader uses
  the new constant. No look-ahead. ✓
- **R4-V5200-D02 (day-3 IV bias)**: The bias is gated on TTE ≤ 4.5 days
  (a forward-looking time gate). At tick t, the trader knows the current TTE.
  No look-ahead. ✓

## 4. Robustness audit (Phase 8a + 8b results)

For each ship-grade alpha (mark-lean stack, R4-CHAIN-01, R4-V5000-C02),
the implicit robustness check is per-day attribution:

**R4-MARK-LEAN-v01 (the only SHIP-grade probe winner)**:
- Day-1 +312, Day-2 +81, Day-3 +663. Positive every day.
- Per-product: HYD +519, VFE +536. Both products positive.
- Per-Mark: M14 +/- mirror produced positive HYD edge; M38 mirror
  produced positive HYD edge; M22 fade is too low-frequency to dominate
  but contributes positively; VFE M67/49/22 lean delivered +536 net.
- The pre-reg LEAN_PER_QTY values were chosen at ~half the empirical
  conditional Δmid; the small but positive PnL confirms direction-of-
  effect without overfitting.
- **Robust**: same sign every day, both products contribute, signal is
  structurally Mark-attributable per Phase 3 (per-trade Sharpe 1.78-1.95).

**R4-CHAIN-02 hard-constants swap (R4-CHAIN-02 standalone, REJECTED in
Phase 8b)**:
- Day-1 −3,114, Day-2 −1,009, Day-3 +1,433. SIGN FLIPS across days.
- Brittle: directional thesis correct (day-3 +1,433 from voucher
  re-pricing) but constants overshoot day-1's TTE 7.
- → REJECT as constants swap; RESEARCH as TTE-conditional blend.

**R4-OTM-AC1-RETUNE (REJECTED Phase 8a)**:
- Day-1 −301, Day-2 +188, Day-3 +148. Sign flips.
- Pre-reg falsifier (per-strike BT std(mid - fair) drop ≥ 3 %) was not
  measured directly; the PnL signal is too small to declare success.

**R4-XPROD-VEV5200 lean (REJECTED Phase 8a)**:
- Day-1 0, Day-2 0, Day-3 +42. The signal is REAL (Phase 3 cells
  survive Bonferroni) but the lean form's effect is bounded by integer
  rounding. Capacity issue, not a robustness one.

**R4-CHAIN-01 take-form hedge (CATASTROPHIC, Phase 8a)**:
- Day-1 −28,586, Day-2 −23,420, Day-3 −8,934. Negative every day.
- The hedge is RIGHT (sticky-strike Δ = 0.7×Δ_BS holds with max 2.8 %
  decay across days per Phase 6 holdout) but the implementation is
  WRONG. The fair-value-bias version (RESEARCH next session) should
  not have this issue because no spread-crossing.

## 5. Capacity audit

Position limits: HYD/VFE = 200, VEV_K = 300.

- **R4-CP-Mark14-HYD copy**: Mark 14 prints ≈ 500 buys + 500 sells / day on
  HYD, mean qty 4. If we copy with 1× qty (lean adds to fair, not direct
  trade), the lean accumulates per print. With LEAN_PER_QTY=0.20 and decay
  HL=46 ticks, the steady-state lean magnitude is bounded by LEAN_CLAMP=5
  (i.e. 5 ticks of fair-value bias). The actual trade size from this bias
  is NOT directly the Mark's qty; it's the EXTRA take/quote volume v15
  emits because the fair shifted. Conservative: each Mark print adds
  ~0.8 ticks bias for ~46 ticks → bias-driven extra trades ~5-10/print.
  Total: 500-1000 extra HYD round-trips/day, capped by 200 position cap.
  → CAPACITY: bound by 200 cap, not by Mark print frequency.
- **R4-XPROD-VEV5200**: 33 Mark 14 buys + 46 Mark 22 sells / day on VEV_5200
  → ~80 trigger events / day. Each triggers a 5-tick window of leaning on
  VEV_4000/4500/5000/5100. With decay HL=14 ticks and 80 events spread
  across 10,000 ticks → avg 1 event / 125 ticks → leans don't overlap
  much. Trade count per event ~5-15 takes per voucher → total 1,500-4,800
  extra voucher trades/day. Capped at 300/strike.
  → CAPACITY: probably hits cap on VEV_4000 first (highest signal).
- **R4-VFE-M01 (Mark 67 copy)**: 55 prints/day at qty 9. Bias 0.10*9=0.9
  ticks per print, decay HL=46. Steady-state bias < 2 ticks. VFE cap = 200.
  → CAPACITY: bound by VFE 200 cap, not Mark frequency.
- **OTM AC1 K re-tune (R4-V53/54/5500-B07)**: each tick the fade adds
  −K * (mid_t − mid_{t-1}) to fair. K = 0.21-0.25 vs current 0.12-0.15.
  The MM reacts on every tick → no capacity issue from event scarcity;
  capped by 300/strike.
  → CAPACITY: bound by 300 cap.

If any alpha hits the cap CONSTANTLY, the live PnL is capped. Report the
cap-hit fraction in the Phase 8 probe outputs.

## 6. Brittleness sources I am specifically watching

- Mark 22 → HYD fade: t-stat 1.5 on day 3 alone; if any day 3 in live data
  drops it below |t|=2, the rule must auto-suspend.
- VEV_5300 / VEV_5400 Mark 14 fade: small n, marginal Bonferroni.
- R4-CHAIN-04 (HYD-vol → VE drift): day-3 sign instability flagged.
- R4-V5200-D02 (day-3 IV bias): if the bias is a STABLE bot quirk (no
  convergence within day 3), holding it at cap might be a NEGATIVE-carry
  trade. Phase 5 G1 (rolling mid-IV) is the safer alternative.

## 7. Open questions for next session (UPDATED with Phase 6 + 8 findings)

1. **R4-PHASE5-G1 was MISIMPLEMENTED in Phase 8b.** The Phase 8b sub-agent
   substituted a price-domain blend (0.30·micro + 0.70·wall) for the
   actual rolling mid-IV alpha. The IV-domain rolling mean per strike
   was NEVER tested. This is the highest-EV next-session move.
2. **The Mark-permutation null is structurally weak** for 7-Mark datasets
   (bimodal null distribution from including both Mark 14 and Mark 38).
   Future sessions should rely on the time-shuffle null + per-day
   robustness check + BT delta as the SHIP gate, NOT the Mark-permutation.
3. **The cross-product spillover (R4-XPROD-VEV5200)** is statistically
   real but ineffective as a passive lean. Test as a TAKE-only signal
   on V_5200 itself in next session.
4. **R4-CHAIN-02 (smile refit)** has the right direction (day-3 +1,433)
   but constants overshoot day-1. Test the TTE-conditional blend.
5. **The 0.7×Δ hedge** is statistically valid but the take-order form
   blew up. Test the fair-value-bias re-implementation.

## 8. Phase 8 verdict on the SHIP gate

Of the candidates that passed Phase 6 nulls AND were probed in Phase 8:

| Alpha | Null verdict | Phase 8 BT | Final status |
|---|---|---|---|
| R4-MARK-LEAN-v01 (bundle) | RESEARCH (perm null weak; per-day robust) | **+1,054** | **SHIP** |
| R4-V5000-C02 standalone | SHIP per Phase 6 | not probed in isolation (+2,657 inside Probe 7 stack) | **RESEARCH** (probe in next session) |
| R4-CHAIN-01 (hedge) | SHIP per Phase 6 | take-form −60,939 | **RESEARCH** (re-implement as bias) |
| R4-XPROD-VEV5200 | SHIP via shuffle null | lean form +42 | **RESEARCH** (try take form) |
| R4-CHAIN-02 (smile refit) | n/a | constants-swap −2,690 | **RESEARCH** (TTE-conditional) |
| R4-OTM-AC1-RETUNE | holdout PASS, cost-adj FAIL | flat +33 | **REJECT** |
| R4-V5100-C01 (50/50 blend) | n/a | catastrophic in Probe 7 (−5,455) | **REJECT** |
| R4-V5200-F01 (vol-cluster) | n/a | trigger too rare (Δ = $0) | **REJECT-as-CONFIGURED** |
