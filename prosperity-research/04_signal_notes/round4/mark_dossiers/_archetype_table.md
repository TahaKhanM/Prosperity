# Bot archetype reconciliation table — Round 4 Marks

> Synthesizes the per-Mark dossiers (Phase 2) + cross-Mark coordination
> (Phase 3). Predictability score = how well the trigger classifier (per-Mark
> §C) predicts the next print, on a 0–10 scale (10 = perfectly predictable
> from book state, 0 = unpredictable / time-uniform). Sub-archetype names
> are short labels for the playbook.

---

## Master table

| Mark | Archetype | Confidence | Sub-archetype | Pair partner(s) | Products | Predictability score |
|---|---|---|---|---|---|---|
| **Mark 01** | **Two-dyad market maker** | HIGH | OTM voucher MM (constant qty); VFE inside-spread MM | Mark 22 (OTM); Mark 55 (VFE) | VEV_5200/5300/5400/5500/6000/6500, VFE | **2** (counterparty-driven, no microstructure trigger) |
| **Mark 14** | **Inside-the-touch market maker / smart bot** | HIGH | Two-sided MM that captures spread + mid drift; structural extractor of Mark 38 | Mark 38 (HYD/VEV_4000); Mark 55 (VFE small); Mark 22 (VEV_5200 incidental) | HYD, VFE, VEV_4000, + small VEV_5200/5300/5400/5500 | **3** (mostly time-uniform, weak vol/drift bias) |
| **Mark 22** | **Multi-role: voucher MM + VFE seller + HYD adversary** | HIGH (per-product roles) | Voucher MM seller (vs Mark 01 OTM); Informed VFE seller; small-N HYD adversarial buyer; VEV_5200 smile-shift trigger | Mark 01 (OTM); Mark 14 (VEV_5200) | All 12 (12 products), but 96% on VEV_5300+/VFE | **4** (VFE sells gated on price-up, t≈+5; HYD buys n=11 only) |
| **Mark 38** | **Naïve two-sided taker / bag-holder** | HIGH | Pure-TAKER (60–67% lift/hit) with no inventory aversion; Mark 14's structural counterparty | Mark 14 (HYD/VEV_4000) | HYD, VEV_4000 | **3** (sell-side AUC 0.546 on `recent_ret_20<0`; buy-side AUC ~0.50) |
| **Mark 49** | **Naïve VFE seller / mean-revert mistimer** | HIGH | Sells into rallies, never unwinds, structural bag-side of Mark 67 | **Mark 67** (VFE) | VFE only | **5** (sell-side AUC ~0.55 on `recent_ret_20>0`; cleanest stateful trigger) |
| **Mark 55** | **Two-sided VFE momentum-chasing taker** | HIGH | Buys at peaks, sells at troughs, 69% taker, fires Poisson in time | Mark 14 (VFE 647), Mark 01 (VFE 504) | VFE only | **2** (trigger AUC ≤0.51 on every feature, time-uniform firing) |
| **Mark 67** | **Buy-only VFE specialist (informed at h≤20)** | HIGH (h≤20); LOW (h≥100) | Inside-the-touch passive buyer that wins ~+2/u short-horizon, decays past h=20; selection-bias-suspect at long horizons | **Mark 49** (VFE) | VFE only | **2** (trigger AUC ≤0.51, fires roughly time-uniform) |

---

## Notes on the predictability score

The score reflects how predictable the **TIMING** of the next print is from
book state (the §C trigger classifier of each dossier). Marks 22/49 score
higher because their side-rule is correlated with `recent_ret_20`. The
others fire roughly Poisson-in-time conditional on partner activity, so the
trigger classifier doesn't help — but **counterparty-conditional reaction**
(the Phase 3 dyad finding) is what makes them tradeable, not pre-print
prediction.

| Score | What it means for the playbook |
|---|---|
| 0–2 | Pre-print front-run impossible; only post-print reaction works |
| 3–5 | Mild pre-print gate possible (2× lift over base); use as filter only |
| 6–8 | Strong pre-print gate; can pre-position with edge |
| 9–10 | Perfect predictability; would be a "Mark predictor" alpha alone |

No Mark in the dataset scores above 5. **The exploitation strategy should
prioritize POST-PRINT reaction over PRE-PRINT prediction.**

---

## Counterparty-conditional cheat sheet

When acting on a Mark print, FIRST check the counterparty. The exploitation
edge is concentrated at specific (Mark, counterparty) pairings:

| Mark | counterparty | n | mean adv100 (signed for the Mark) | trader action |
|---|---|---|---|---|
| Mark 38 | Mark 14 | 999 (HYD) | **−8.65** | **FADE** Mark 38 (very high confidence) |
| Mark 38 | Mark 22 | 18 (HYD) | **+2.39** | DO NOT fade — sign flips |
| Mark 49 | Mark 67 | 88 (VFE sells) | **−1.27** | FADE Mark 49 sells (high confidence) |
| Mark 49 | Mark 55 | 9 | +3.17 | DO NOT fade |
| Mark 55 | Mark 14 | 647 | −1.27 | FADE Mark 55 (medium confidence) |
| Mark 55 | Mark 01 | 504 | −2.40 | FADE Mark 55 — bigger edge here |
| Mark 14 | Mark 38 | 999 (HYD) | **+8.65** | COPY Mark 14 (very high confidence) |
| Mark 67 | Mark 49 | 88 (VFE) | **+1.27** | COPY Mark 67 buys at h≤20 (high confidence short) |

**Critical**: the playbook MUST gate on counterparty identity, not just on
the Mark printing. A Mark 38 print with `counterparty == "Mark 22"` is
NOT the bag-hold pattern.

---

## Per-archetype playbook implications (preview of Phase 5)

| Archetype | Playbook category |
|---|---|
| Smart MM (Mark 14) | **MIRROR** — same-tick action: copy the direction, scaled by qty + counterparty filter |
| Bag-holder (Mark 38) | **REACT-WITH-STRUCTURE** — opposite direction, decay 50 ticks |
| Multi-role (Mark 22) | **PER-PRODUCT GATE** — VFE sell rule, HYD buy fade rule, OTM AVOID |
| Two-dyad MM (Mark 01) | **AVOID on OTM** (no signal); secondary lean on VFE (low priority) |
| VFE specialist informed (Mark 67) | **REACT-WITH-STRUCTURE** — copy direction at h≤20, exit before h=100 |
| VFE mistimer (Mark 49) | **REACT-WITH-STRUCTURE** — fade their sells, ignore their buys (small N) |
| Momentum chaser (Mark 55) | **REACT-WITH-STRUCTURE** — fade direction at low size (tail risk) |

The full playbook is in `mark_exploitation_playbook.md`.
