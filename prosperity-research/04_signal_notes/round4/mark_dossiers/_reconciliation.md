# Reconciliation vs prior session — Round 4 Mark dossiers

> Cross-checks the new per-Mark dossiers (Phase 2) and cross-Mark
> coordination (Phase 3) against the prior session's `counterparty_play_book.md`
> (archived to `archive/counterparty_play_book_pre_dossier_2026-04-26.md`),
> `counterparty_findings.md`, `headline_findings.md`, and `counterparty_deep.md`.
>
> Format: each section addresses one question from the project brief, then
> a final aggregate table of OVERTURNED / CONFIRMED / REFINED verdicts.

---

## Q1. Does Phase 4's archetype for Mark 14 = "smart bot, +5.71/u" still hold, or is it more nuanced?

**HOLDS, but REFINED.** The +5.71/u headline is correct in aggregate, but the
new dossier breaks it down by product:

- HYD adverse-selection-for-Mark-14 mean: **+8.05/u (buy) and +8.11/u (sell)
  at h=5** — robust across 3 days, both sides positive.
- VFE adverse-selection-for-Mark-14 mean: **+1.27/u at h=100, +2.20/u sell
  at h=5** — much smaller per-print edge than HYD.
- VEV_4000 adverse-selection-for-Mark-14 mean: **+10.55/u at h=100** —
  largest per-print edge, but driven mostly by the delta-1 spillover from
  VFE drift, not options alpha.
- VEV_5200..5500 adverse-selection: weak (+0.1 to +1.4/u), partner-noise-
  driven.

The Mark 14 dossier classifies them as **"inside-the-touch market maker"**
(not just "smart bot") — they extract SPREAD via passive resting MM that
captures the touch on every fill, with directional alpha as a secondary
consequence.

**Per-day stability check (from `counterparty_deep.md` §3.1)**: Mark 14 HYD
buyer h500 PnL across days: +6,052 / +4,708 / +5,240 (concentration 0.38).
Robust. The Mark 14 alpha is **NOT brittle** at h=500.

**However**, per the per-product HYD file: "Mark 14 / Mark 38 conditional
Δmid edge is BRITTLE at h=1." Day-1 t=±1.8, day-2 collapses to ±0.4, day-3
+1.3/+1.0. This is the SHORT-HORIZON edge that's brittle. The h=500 edge
is robust, the h=1 edge is brittle. The dossier refines the playbook to
target the **h=50–100 capture window** (long enough to escape the brittle
h=1 noise, short enough to be inside the alpha decay).

---

## Q2. Does Phase 6 (prior) Mark 67 null-failure get re-explained by the archetype here?

**YES, the dossier RE-FRAMES Mark 67 cleanly.** The Mark 67 dossier finds:

- h=5 mid move after Mark 67 buy: **+1.99/u (t=3.5–5.9 every day)** —
  ROBUST short-horizon edge.
- h=100 mid move: day-3 turns NEGATIVE (-1.37, t=-0.93). h=500 mean = +0.24/u
  (NOT the +1.19/u advertised in `counterparty_findings.md`).
- The +1.19/u headline column was **mislabeled** as "h500" but actually
  reproduces the +1,796 / +1,510 ratio = +1.19 only at **h=5**.

**Re-explanation**:
1. Mark 67's edge is REAL but **only at h≤20**. Beyond that, the signal
   decays to noise (or worse: on directional down days like day 3, they
   keep buying and lose).
2. The "selection bias on long-VFE days" hypothesis from the prior Phase 6
   is **partially right**: at h≥100, Mark 67's profit IS just whatever VFE
   does that day, not an informed signal. But at h≤20, the signal is real
   (likely a level-2 inside-the-touch fill that captures the immediate
   bid-ask bounce).
3. The Mark 67 dossier's `counterparty_findings.md` correction recommendation:
   change the column label from "h500 PnL" to "h5 PnL" or add both columns.

This OVERTURNS the prior playbook's Mark 67 rule (which had no decay
specified — implicitly long-horizon). The new rule pre-registers
**half-life = 20 ticks** to exit before the alpha decays.

---

## Q3. Does Phase 3.1 confirm the Mark 14 ↔ Mark 38 dyad as a structural informed/uninformed pair?

**YES, but the structure is different from what was assumed.** The dyad is
NOT "Mark 14 fires, then Mark 38 reacts" or vice versa — they are the
SAME TRADE at the SAME TICK. The cross-Mark file documents:

- 728 paired trades where `buyer == "Mark 14"` and `seller == "Mark 38"`.
- 714 paired trades where `buyer == "Mark 38"` and `seller == "Mark 14"`.
- **Median waiting time M14 BUY → M38 SELL = 0 ticks** — same tick.
- 97.7% of Mark 38's HYD prints have Mark 14 as counterparty.
- 98.0% of Mark 38's VEV_4000 prints have Mark 14 as counterparty.

So the dyad is a **one-tick structural pairing**, not a sequence. This
matters for the playbook:
- We CAN'T "pre-position before Mark 14 fires using Mark 38 as a leading
  indicator" — they fire simultaneously.
- We CAN "react to the dyad-print with confidence in the structural edge"
  (post-print mirror, decay 50 ticks).
- The "smart vs uninformed" framing is right: Mark 14 captures the spread
  + drift, Mark 38 pays it. But the asymmetry comes from the QUOTE STATE
  before the dyad fires, not from any sequential information.

---

## Q4. Were there Marks classified as "noise" that the dossier promotes to signal?

### Mark 49 (prior: "low-conf informed seller") → CORRECTED to "naïve mean-revert mistimer; FADE their sells"

The prior playbook classified Mark 49 as a "modest informed seller" and
recommended "lean weakly long ... or skip". The new dossier finds:

- Mark 49 BOTH SIDES LOSE at h=100 (sell mean adv100 = −1.11; buy mean
  adv100 = −2.34).
- The "informed seller" interpretation was **WRONG** — Mark 49 is the bag
  side, not the smart side.
- The +1.88/u h=1 mid-move-after-sell (per per-product VFE EDA file) is the
  FADER's edge from Mark 49 selling cheap, **not** Mark 49 being informed
  about future drops.

**Net rule**: the prior recommendation "lean weakly long" IS the fade
direction — semantically correct, but the rationale was wrong. The new
dossier pre-registers a stronger fade with concrete parameters
(`half-life=20`, `qty_multiplier=0.5`), explicit gate
(`counterparty == Mark 67` preferred), and EV estimate (~+130/day).

### Mark 22 HYD buys (prior: not a play) → PROMOTED to a small-N adversarial fade

The per-product HYD file flagged Mark 22 buys as adversarial (h=1 t = -5.3 /
-3.6 / -1.5 across days, 11 trades). The prior playbook did NOT include
this as a rule (it focused on Mark 22 as voucher MM noise). The new
playbook:

- Adds a SMALL-N rule: "fade Mark 22 HYD buys, qty 0.5×, half-life 50t."
- Estimated EV +50–100/day. Low capacity but high precision.

### Mark 55 (prior: "noise to light fade") → CONFIRMED but RE-RANKED upward

The prior playbook was right to fade Mark 55, but did not specify
parameters and called it "low confidence". The new dossier:

- Confirms the fade is a **t≈−37 across 1,198 prints** — extremely high
  statistical significance.
- Notes the worst-10% concentration of the loss = 100.7% (tail-driven, not
  uniform).
- Pre-registers `qty_multiplier=0.3` (lower than Mark 38) due to tail
  brittleness, and **5-tick wait before leaning** to avoid the immediate
  post-fill stickiness.
- EV estimate ~+500–800/day.

---

## Q5. Were there Marks classified as "signal" that the dossier demotes?

### Mark 01 OTM voucher prints (prior: not a play, but ambiguous on "Mark 01 prints on HYDROGEL or VE *might* be informative")

**DEMOTED**: the new dossier confirms Mark 01 has ZERO meaningful HYD
prints (all incidental). Their VFE flow is **pure spread capture** with
~+0.6/u directional residual — much smaller than the prior session's
implied "+1.4/u flow could be useful". The new playbook keeps Mark 01 VFE
as the LOWEST-priority rule (`+0.5 ticks per print`, EV ~+180/day) and
explicitly AVOIDS treating Mark 01 OTM prints as alpha.

### Mark 22 OTM voucher prints (prior: voucher MM noise)

**CONFIRMED.** No demotion needed; the dossier reinforces the avoid rule.

---

## Q6. Mark 14 short-horizon edge brittleness

**FLAGGED.** The per-product HYD file already documented "Mark 14 / Mark 38
Day-1-vs-Day-2/3 stability is poor" at h=1 (t = +1.8 / +0.5 / +1.3). This
remains true. The new playbook handles it by **NOT relying on h=1 capture**
— the half-life of 50 ticks targets the h=20–100 capture window, where the
edge is more stable (per `counterparty_deep.md` §3.1: per-day h500 PnL
+6052/+4708/+5240, robust).

**Implication for live R4 day 1**: do NOT panic if h=1 looks weak in the
early ticks. Wait for the h=50–100 horizon to manifest the edge.

---

## Q7. The smile-shift cross-product spillover (Mark 22/14 VEV_5200 → deeper-ITM)

**CONFIRMED + UNCHANGED.** The Phase 3 cross-Mark file reproduces the same
finding from `cross_product_mark_spillover.csv`: t=20.83 for Mark 22 sell
VEV_5200 → VEV_4000 at h=5; t=18.07 for the symmetric Mark 14 buy. **This
is already implicit in the D1 IV-residual scalp** (smile-shift coupling
across strikes). No new trade rule needed — the spillover is *informational*,
not a separate alpha.

---

## Q8. Time-of-day gating

**CONFIRMED REJECTED.** Per the headline_findings §4 and the per-product
files: peak hour-bucket share ≤14% across all Marks. The new dossiers
verify this in §B.3 of Mark 14 (decile firing within 88-116 range), and
the Phase 3 cross-Mark file does not surface any time-of-day pattern.
Continue NOT to gate on time of day.

---

## Q9. The OTM voucher Mark 01 / Mark 22 dyad — is there ANY alpha?

**CONFIRMED NO.** Mark 01's adverse-selection on every OTM voucher strike
is exactly +0.5/u (mid pinned at 0.5 on stuck strikes; round-trip mechanic).
Mark 22's mirror is exactly -0.5/u. The total contribution to PnL across
the Mark 01 + Mark 22 OTM round-trips is ZERO net of the spread capture
they each take from each other. This is mathematical noise, not alpha.

The new playbook explicitly AVOIDS treating these prints as actionable.

---

## Q10. The Mark 67 ↔ Mark 49 dyad — newly identified as a third dyad

**NEW STRUCTURAL FINDING.** The prior playbook treated Mark 67 (informed
buyer) and Mark 49 (informed seller, per their wrong classification) as
independent. The new dossiers find:

- 89 paired trades (Mark 67 buyer, Mark 49 seller) on VFE.
- Mark 49 LOSES specifically vs Mark 67 (mean adv100 = -1.27/u) but WINS
  vs Mark 55 (+3.17/u, n=9).
- Architecturally identical to the Mark 14 ↔ Mark 38 dyad: a smart bot
  (Mark 67 here) extracts edge from a counterparty (Mark 49 here) on a
  single product (VFE here, HYD/VEV_4000 there).

**Implication for the playbook**: when acting on a Mark 49 sell, gating on
`counterparty == Mark 67` raises confidence (use the higher multiplier).

---

## Q11. The Mark 01 ↔ Mark 55 VFE dyad — also newly identified

**NEW STRUCTURAL FINDING.** Mark 01's VFE flow (504 trades) is 100% paired
with Mark 55. The prior session identified this in the network CSV but
didn't reframe it as a structural dyad (treated Mark 01 VFE as "incidental
flow"). The new dossier:

- Mark 01 is the inside-spread MM on VFE; Mark 55 is the momentum-chasing
  taker.
- Mark 55 loses **−2.40/u to Mark 01** (greater than the −1.27/u they lose
  to Mark 14). The biggest leak on Mark 55 is to Mark 01, not Mark 14.
- Mark 01's adverse-selection on VFE = +2.7/u — pure spread capture.

**Implication for the playbook**: this re-confirms why the playbook has a
Mark 01 VFE mirror rule (we want to capture the same kind of spread Mark 01
captures); but our priority is to fade Mark 55 more aggressively when
counterparty is Mark 01 (because that's where Mark 55's biggest loss is).

---

## Aggregate verdict table

| Item | Prior verdict | New verdict | Status |
|---|---|---|---|
| Mark 14 = smart bot, +5.71/u | TRUE | TRUE, but per-product (HYD = +8/u, VFE = +1.3/u, VEV_4000 = +10.5/u) | **CONFIRMED + REFINED** |
| Mark 38 = bag-holder, fade | TRUE | TRUE, fade with structural-counterparty gate; mechanism is "naïve taker, no inventory aversion" | **CONFIRMED + REFINED** |
| Mark 67 = informed buyer +1.19/u h500 | PARTIALLY WRONG | TRUE at h≤20 only; h≥100 = noise / selection bias | **REFINED** (decay added) |
| Mark 67 column header in counterparty_findings.md | "h500 PnL" | Actually h=5 PnL; mislabeled | **CORRECTED** |
| Mark 49 = informed seller | WRONG | Mark 49 is the bag side; FADE their sells | **OVERTURNED** |
| Mark 22 = voucher MM noise | TRUE for OTM | Multi-role: voucher MM + informed VFE seller + small-N HYD adversarial buyer | **REFINED** |
| Mark 22 HYD buys are an alpha | NOT IDENTIFIED | YES, n=11/3day, fade with multiplier 0.5 | **PROMOTED** |
| Mark 55 = noise to light fade | TRUE | TRUE, but stronger statistical case (t≈−37); REFINED with tail-aware sizing | **CONFIRMED + REFINED** |
| Mark 01 = voucher MM noise | TRUE for OTM | TRUE for OTM; secondary VFE-MM role with small +0.6/u directional residual | **REFINED** |
| Mark 01 HYD prints are informative | NOT EVIDENCED | NO HYD prints exist; the speculation is unfounded | **DEMOTED** |
| Mark 14 ↔ Mark 38 dyad | "1,442 paired trades, closed loop" | TRUE; but the dyad is **same-tick paired**, not sequential. No predictive lift in the joint-firing matrix. | **CONFIRMED + CLARIFIED** |
| Mark 01 ↔ Mark 55 VFE dyad | NOT IDENTIFIED | YES, 504 paired trades, structural | **NEW** |
| Mark 67 ↔ Mark 49 VFE dyad | NOT IDENTIFIED (Mark 67 → Mark 49 was in network CSV but not framed) | YES, 89 paired trades, architecturally identical to M14↔M38 | **NEW** |
| Time-of-day gating | REJECTED | REJECTED | **CONFIRMED** |
| Sequential 3-Mark chain prediction | NOT TESTED | NO LIFT > 1.2× over base | **REJECTED** |
| Cross-product spillover (VEV_5200 → deeper-ITM) | TRUE (already in cross_product_mark_spillover.csv) | TRUE | **CONFIRMED** |
| Mark 14 short-horizon edge brittle at h=1 | NOTED in HYD per-product file | TRUE; new playbook targets h=50–100 capture window | **CONFIRMED + ADDRESSED** |
| HYDROGEL spectral 3330-tick rhythm | REJECTED | not re-tested (out of scope) | **N/A** |

### Summary

- **OVERTURNED**: 1 (Mark 49 informed-seller classification).
- **NEW STRUCTURAL FINDINGS**: 2 (Mark 01↔Mark 55 dyad, Mark 67↔Mark 49 dyad).
- **CORRECTIONS to prior CSVs/docs**: 1 (Mark 67 column header in
  counterparty_findings.md mislabels h=5 as h500).
- **PROMOTED to a new rule**: 1 (Mark 22 HYD buy fade, low capacity).
- **DEMOTED**: 1 (Mark 01 HYD prints — they don't exist).
- **CONFIRMED**: 9 (Mark 14, Mark 38, Mark 55, Mark 22 OTM, Mark 01 OTM,
  time-of-day gating, smile-shift, Mark 14↔38 dyad structure, Mark 14
  short-horizon brittleness).
- **REFINED with concrete parameters**: 5 (Mark 14 mirror, Mark 38 react,
  Mark 67 decay, Mark 49 fade, Mark 55 tail-aware fade).

The new playbook (`mark_exploitation_playbook.md`) ships **3,500–4,500
XIRECS/day total expected EV**, vs the prior playbook's roughly 1,054
XIRECS/day captured by `r4_mark_lean_v01_probe.py`. The delta comes
primarily from:
1. Counterparty-conditional gating (capturing the structural edge).
2. Per-Mark decay tuning (escaping the brittle h=1 noise on Mark 14, exiting
   before alpha decays on Mark 67).
3. Newly-identified per-product roles for Mark 22 (VFE sell, HYD buy fade).
4. Tail-aware sizing on Mark 55.
