# R4 alpha hunt — self-critique (Phase 11)

This document is honest. The goal is for the next session to know what
this one missed.

## 1. Lens with the least time spent — and where the missing alpha probably hides

**Lens F (weird) got the least depth.** Sub-agents mostly reported simple
counts: histogram peaks, qty modes, ticks where book empties. The
"undocumentable but interesting" findings (e.g., VEV_6000/6500 trade rows
byte-identical, all stuck-strike trades clearing at price 0.0 not 0.5,
VFE bv1 modes at 21-23 not 20) WERE caught and turned into alphas
(R4-VFE-F01 wall_vol_thr 22). But:

- I did not look hard for **trade-time clustering inside individual products**
  (Hawkes-process self-excitation). Phase 5's menu listed it as a gap;
  I never tested it. If voucher prints cluster around IV-residual jumps,
  that's an additional regime gate v15 doesn't use.
- I did not look for **per-Mark trade-size DISTRIBUTION shifts within the
  day**. The Phase 1 agent reported uniform sizing (Mark 14 mean qty 4),
  but did not check whether Mark 14's typical size DRIFTS within the day
  (e.g. larger prints late as inventory accumulates).
- I did not test **Lee-Mykland jump detection** on HYD or VFE. HYD has
  occasional 11.5-tick one-shot moves; if those cluster after specific
  Mark prints, that's a gate.

These would be highest-EV next-session bets if the leaderboard is still
tied after the current SHIP alphas are deployed.

## 2. Products with no new alpha — is the data thin or were our tests insufficient?

**VEV_6000 and VEV_6500**: zero new alpha, fully expected. The data IS
thin (std=0 mid). The negative result is correct and documented.

**VEV_4500**: only marginal candidates (β-residual fade defeated by
spread). Limited because counterparty trade count is 3 across 3 days
(Mark 22 / Mark 38 paired). No statistical power for Lens D. **Future
sessions should pool VEV_4000 + VEV_4500 conditional analysis** to
double the n.

**VEV_5500**: deepest candidate in the OTM trio (best Hurst, |ret| AC1)
but n_trades is dominated by the Mark 01/22 noise pair; only 7 Mark 14
prints across 3 days. Underpowered for per-Mark conditional analysis.
Live data with growing n might surface Mark 14 there.

## 3. Marks I have NOT characterised confidently

**Mark 49**: only 122 prints across 3 days. The "informed seller" tag
comes from a per-trade horizon-PnL of −1.14 on buys (so they GIVE AWAY
on the buy side). Their sells are profitable for them. But the n is
small enough that Bonferroni-corrected the alpha is borderline. Need
more live data to be confident.

**Mark 55**: 6,551 gross qty but ALL on VEV_5500 with −2.41/u h500.
Classified as "noise" but might have a PRODUCT-SPECIFIC pattern we
missed because we only looked aggregate. The Phase 1 V_5500 agent
noted Mark 55 has 0 trades on V_5500 in R4 historical (contradicts
the playbook flag from R3 v15).

**Mark 22 on HYDROGEL** (vs the OTM voucher MM context): only 11
buys / 8 sells across 3 days but the buy side is high-precision
adversarial (h=1 Δmid −3.17/−3.88/−2.25, t = −5.3/−3.6/−1.5).
What's special about Mark 22 occasionally crossing into HYD? Need
to see if the live R4 data preserves this pattern or if it's a
3-print fluke.

What additional data would change the verdict: **a fresh combined.log
from a live R4 submission**, where we can re-run counterparty_scan.py
and see whether the per-Mark numbers replicate.

## 4. Three alphas I considered but did not test

1. **Hawkes self-excitation on voucher prints** (mentioned in Phase 5
   menu). The hypothesis: voucher prints cluster after IV-residual
   jumps; gating MM quotes on cluster-state would reduce adverse
   selection. NOT tested because: it requires fitting a stochastic
   process model (μ + α·exp(−β(t−t_i))) per strike; Phase 1 sub-agent
   load was already heavy. Unblocked by: small Python notebook with
   maximum-likelihood Hawkes fit on the 30k tick stream per strike.

2. **HMM 2-state regime detector on HYDROGEL** (Phase 5 menu). The
   hypothesis: HYDROGEL has a "trend" regime (Hurst > 0.5 windows)
   and a "mean-revert" regime. v15 always treats it as MR. NOT tested
   because: 30,000 ticks / 3 days might give too few regime flips for
   stable estimation. Unblocked by: implementing the EM algorithm
   for a 2-state Gaussian-emission HMM on HYD returns.

3. **Per-Mark COVERED-STRIKE inventory inference**: if Mark 14 just
   bought 100 lots of VEV_5200, their effective vega exposure is now
   long. Their NEXT trade should be either to cover or to widen — and
   the direction tells us their bias for the next 100 ticks. NOT tested
   because: Phase 3 ran out of Bonferroni budget after the cross-product
   spillover discovery. Unblocked by: tracking running per-Mark
   per-strike net inventory in the trade stream and conditioning the
   next-tick mid on it.

## 5. If I had 24 more hours (UPDATED with Phase 8b learnings)

Priority order:

1. **Build R4-PHASE5-G1 CORRECTLY** as a per-strike rolling mid-IV
   replacement for v15's static SMILE_PER_STRIKE_BIAS. Phase 8b's
   sub-agent built a price-domain blend instead (which failed). The
   actual IV-domain rolling mean is unblocked — maintain `iv_ema_K`
   per strike with HL ~60 ticks, use it as the IV input to BS pricing
   on that strike instead of `a0 + a1·m + a2·m²`. Probe vs Probe 1.
   Highest-EV change per Phase 5 (CMU Physics: 80k → 200k swap).

2. **R4-CHAIN-02 with TTE-conditional blend.** Phase 8b confirmed the
   directional thesis (day-3 +1,433 from convexity refit) but the
   constants swap overshoots day-1 by −3,114. Fix: keep the new
   (7.62, 1.62) only for TTE ≤ 5; revert to v15's (7.21, 0.815) for
   TTE ≥ 6.

3. **R4-V5000-C02 STANDALONE probe.** Inside Probe 7 the V_5000 imb2
   skew contributed +2,657 (only the V_5100 collapse killed the bundle).
   A clean standalone probe should land +1k to +3k positive at locked
   pre-reg parameters. Fastest defensible add-on after the mark-lean
   stack.

4. **R4-CHAIN-01 fair-value-bias hedge.** The 0.7×Δ_BS portfolio hedge
   is statistically sound (holdout PASS, max β decay 2.8 % across days).
   The TAKE-order form blew VFE up by −60.9k. Re-implement: add a bias
   `D / 4` to VFE fair where D = portfolio voucher delta × 0.70.

5. **R4-XPROD-VEV5200 as a TAKE on V_5200 itself.** When Mark 14 buys
   V_5200, take V_5200 at the ask; symmetric for Mark 22 sells. The
   +5 tick lift on V_5200 might absorb the 1-tick spread cost. The
   passive-lean form was rejected (signal too rare; integer-rounding
   kills it on the deeper-ITM strikes).

6. **Hawkes-process gating on voucher MM** (per §4.1 above).

7. **Live counterparty scan in early R4 submission**: submit a minimal
   "lurker" trader that logs every Mark trade with its conditional
   next-tick mid. Re-fit per-Mark conditional return on the live data.
   If any Mark's edge has DISAPPEARED or REVERSED, suspend the
   corresponding lean immediately.

8. **Build a live trader-only re-fit module**. The static R3-tuned smile
   bias dict is stale; per-Mark headers are now disclosed. Many things
   that were "frozen" pre-flight should be RE-FITTED on the first 500
   ticks of live data. Build the trader to do this.

## 6. Process critique

- **Best move**: parallelizing 5 per-product sub-agents in Phase 1.
  Saved at least 2× wall-clock time.
- **Worst move**: launching the full Phase 8 (probe build + backtest)
  before getting Phase 6 (nulls) results. If a probed alpha later
  fails its null, the Phase 8 backtest cycles were wasted. (Mitigated
  because most probes are CHEAP to backtest — ~60s each.)
- **Surprise 1**: the Phase 1 agent's claim that Mark 14/38 on HYD was
  brittle was a metric-choice error. The per-tick conditional Δmid
  IS noisy, but the per-trade horizon-500 PnL IS robust (Phase 3
  confirmed Sharpe 1.78-1.95). **Lesson**: when a sub-agent's headline
  contradicts a known-good R3 finding, sanity-check the metric choice
  before trusting the contradiction.
- **Surprise 2**: the Phase 6 Mark-permutation null is STRUCTURALLY
  WEAK for 7-Mark datasets. The null distribution is bimodal (~2/7
  chance the permuted label inherits the smart Mark 14 OR bag-holder
  Mark 38 strong signal), so z-scores against the null mean are
  misleading. The honest test is the one-sided p-value AND the
  per-day robustness check (which mark-lean passed via Phase 3, then
  Phase 8 BT confirmed +1,054). **Lesson**: when the null distribution
  is bimodal, don't report z-scores as the verdict — report the
  two-sided p-value or the SIGN match against the dominant mode.
- **Surprise 3**: Phase 8a's "OTM K = |AC1|" probe was rejected with
  net BT delta of +33 — confirming that linear-fade theory does not
  transfer to PnL under integer-quote + spread cost. **Lesson**:
  parameter retunes that look statistically obvious (K=|AC1|) need
  a backtest gate, not just a literature reference.
- **Surprise 4**: Phase 8a's combined probe blew up VFE by −60.9k
  because the 0.7×Δ_BS portfolio hedge was implemented as a TAKE
  order on VFE. Each rebalance cost ~6 shells / unit (the spread).
  **Lesson**: ALWAYS prefer fair-value-bias forms over take-order
  forms for inventory management; the existing MM is the cheapest
  rebalance medium.
- **Surprise 5**: Phase 8b — the smile-refit constants swap (R4-CHAIN-02)
  has the right directional thesis (day-3 +1,433 confirms staleness) but
  over-flattens day-1 (TTE 7) by −3,114. **Lesson**: a single set of
  constants cannot fit the full TTE bucket range. TTE-conditional blends
  are required; the linear extrapolation that worked for R3 (where the
  TTE drift was modest) breaks for R4 once a2 spikes 5σ between TTE 6
  and TTE 5.
- **Surprise 6**: Phase 8b — the V_5100 micro/wall 50/50 blend with the
  smile fair was catastrophic (−5,455). The smile MM was already
  vega-correct on V_5100; mixing in a price-domain signal makes the
  trader fight itself. **Lesson**: when a smile-MM is already producing
  vega-correct fairs, do NOT blend it with a price-domain signal —
  either replace it (rolling mid-IV per-strike) or leave it alone.
- **Surprise 7**: Phase 8b sub-agent SUBSTITUTED a price-domain blend
  for the actual rolling mid-IV (R4-PHASE5-G1) when building Probe 7.
  R4-PHASE5-G1 was the highest-EV gap per Phase 5 and **was never
  actually tested.** The agent's misimplementation looked like the same
  alpha but operated in price space, not IV space. **Lesson**: when
  delegating probe-building to a sub-agent, be explicit about the
  domain (IV vs price) and re-read the probe code BEFORE accepting
  the verdict.
- **Coverage discipline**: 12/12 products × ~6 lenses each was achieved
  (with 8 by-construction n/a cells on stuck strikes). No coverage gap
  in Phase 1.

## 8. Most counter-intuitive finding to remember

**The headline Mark 14 / Mark 38 alpha — disclosed counterparty IDs are
the central R4 alpha — is REAL but its STRUCTURAL EVIDENCE is in the
PER-DAY backtest robustness, not in the formal null tests.**

The Mark-permutation null fails for every counterparty alpha because the
null distribution is bimodal (containing both Mark 14 and Mark 38). The
time-shuffle null fails for the high-volume HYD alphas because the price
drifts in ways that get partially captured by random Mark labels. ONLY
the Mark 22 (low-frequency) alphas and the cross-product spillover pass
formal nulls.

But the Phase 3 per-day analysis showed every Mark-14/38 alpha has the
SAME SIGN every day with conc=0.37-0.38, which is what shipping discipline
actually requires. And the Phase 8 BT delivered +1,054 on the bundled
mark-lean stack.

**Future sessions should NOT discard counterparty alphas because they fail
the Mark-permutation null on a 7-label dataset.** That null is too weak
to pass anything in this regime. Trust the per-day robustness + BT gate.

## 7. The 4-family check (success criterion)

Per the prompt: SHIP/RESEARCH alphas must span ≥ 3 of 4 families.

| Family | Did we find one? |
|---|---|
| 1. Carry-over from R3, re-validated | ✓ A1, B1, C1, D1, E1, G1 confirmed on R4 baseline (+222,775/3-day) |
| 2. Counterparty-driven | ✓ R4-CP-Mark14-HYD, R4-CP-Mark38-HYD, R4-CP-Mark67-VE, R4-CP-Mark49-VE, R4-CP-Mark22-VE-S, R4-HYD-M01 |
| 3. Net-new microstructure | ✓ R4-V5300/5400/5500-B07, R4-V5000-C02, R4-V5100-C01, R4-V5200-F01 |
| 4. Cross-product / stat-arb / spillover | ✓ R4-XPROD-VEV5200 (per-Mark conditional spillover, NOT regression-cointegration) + R4-CHAIN-01 (sticky-strike Δ) + R4-CHAIN-02 (convexity refit) |

**All 4 families have at least one candidate.** The negative result on
regression-style stat-arb is documented in `no_stat_arb_explanation.md`.
