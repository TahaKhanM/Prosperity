# Mark 22 — Dossier (Round 4)

Source CSVs: `prosperity-research/03_eda/round4/per_mark/Mark_22_*.csv`
Quote source: `prosperity_rust_backtester/datasets/round4/prices_round_4_day_{1,2,3}.csv`
Schema: `prosperity_rust_backtester/scripts/round4_options/per_mark_features.py`
All horizons in ticks (1 tick = 100 ts units). adverse_select_h is signed by Mark 22's
trade direction (positive = good for Mark 22). dmid_h is the raw `mid_post_h - mid_pre`.

---

## A. Headline classification

**Mark 22 is a HYBRID**: voucher-MM seller on OTM strikes (paired with Mark 01),
informed/mean-revert seller on VFE, smile-shift trigger on VEV_5200 (paired with
Mark 14), and a small-volume adversarial buyer on HYDROGEL_PACK.

| Product | Role | Confidence |
|---|---|---|
| VEV_5300 / 5400 / 5500 | Voucher MM (sell-only, 80–98% Mark 01) | **HIGH** |
| VEV_6000 / VEV_6500 | Voucher MM on stuck strikes (sell-only, 100% Mark 01, ~0.5 mid) | **HIGH** (zero vega — noise) |
| VEV_5200 | Smile-shift trigger seller (72% Mark 14) | **MED** |
| VELVETFRUIT_EXTRACT | Mostly sells (101/126), mildly informed at h=100–500 (mean-revert) | **MED** |
| HYDROGEL_PACK | Tiny n=19 sample — buys are adversarial (price drops after) | **LOW** (n) / **HIGH** (effect size) |
| VEV_4000 / 4500 / 5000 / 5100 | n=3 each — ignore | n/a |

The roles are not interchangeable: do **NOT** apply the OTM-MM "noise" classification
to VFE or VEV_5200 prints. The dossier from here treats the products separately.

---

## B. Volume profile

Total: 2,098 prints across 12 products. Buy/sell counts confirm the asymmetry:
**206 buys vs 1,892 sells** — Mark 22 is overwhelmingly a seller.

| Product | n | qty mode | qty mean | day1 b/s | day2 b/s | day3 b/s |
|---|---|---|---|---|---|---|
| VELVETFRUIT_EXTRACT | 126 | 5 (29×) | 6.69 | 10/40 | 9/37 | 6/24 |
| HYDROGEL_PACK | 19 | 4 (5×) | 3.89 | 3/2 | 4/4 | 4/2 |
| VEV_5200 | 47 | 2 (14×) | 3.45 | 0/7 | 0/8 | 1/31 |
| VEV_5300 | 164 | 2 (53×) | 3.34 | 0/39 | 0/45 | 1/79 |
| VEV_5400 | 276 | 2 (79×) | 3.47 | 0/81 | 0/80 | 0/115 |
| VEV_5500 | 306 | 2 (87×) | 3.49 | 0/92 | 0/94 | 0/120 |
| VEV_6000 | 317 | 2 (90×) | 3.49 | 0/98 | 0/95 | 0/124 |
| VEV_6500 | 317 | 2 (90×) | 3.49 | 0/98 | 0/95 | 0/124 |
| VEV_4000/4500/5000/5100 | 3 each | — | 2.0 | minor | — | minor |

**Trade-size diagnostic** (the quantum question in the brief):
- OTM vouchers (5300+): qty in {2, 3, 4, 5}, modes overwhelmingly 2 (50–55% of prints) — **constant lot quantum**, MM-like.
- VFE: qty in {3..10}, mode = 5 (29×), much wider distribution — **variable / aggressive sizing**, not MM-like.
- HYD: qty in {2..6}, no clear mode — variable.
- VEV_5200: qty in {1..5}, mode 2 — between MM and informed.

This alone supports the multi-role classification: the mode-2 OTM behavior is a
fingerprint distinct from the variable-size VFE/HYD activity.

VEV_6000/6500 prints are **identical** day-by-day (98/95/124 sells, all to Mark 01) —
classic stuck-strike voucher MM noise, exactly as the headline (Mark 01 ↔ Mark 22) predicted.

---

## C. Trigger classifier — "Will Mark 22 sell in the next 5 ticks?"

Per-tick logistic-style binning over all three days of `prices_round_4_day_*.csv`.
Label = 1 if Mark 22 sold within 5 ticks of (or at) this quote's timestamp.

### VFE (n=30,000 ticks; positive = 603; base rate = **2.01 %**)

| Feature | AUC | Sign |
|---|---|---|
| spread     | 0.584 | tighter spread → more likely |
| imb3       | 0.573 | more bid-heavy → more likely |
| imb1       | 0.569 | more bid-heavy → more likely |
| imb2       | 0.525 | (weak) bid-heavy |
| rv100      | 0.522 | higher vol slightly more likely |
| recent_ret_20 | 0.501 | no signal |

All AUCs are weak (best 0.58). VFE sell prints are **not strongly forecastable from
microstructure alone** — Mark 22 trades when they trade, regardless of book state.

**Best 2-feature rule (VFE)**: `spread <= 5` AND `imb1 >= 0.528` →
`P(Mark 22 sells next 5 ticks) = 4.68 %` vs base 2.01 % (**lift ≈ 2.33×**).
Translation: when the spread is at the floor and the bid is heavy, Mark 22 is
more likely to be hitting a fat resting bid. Useful as a confirming filter, but
not a stand-alone trigger.

### VEV_5200 (n=30,000; positive = 275; base rate = **0.92 %**)

| Feature | AUC | Sign |
|---|---|---|
| **rv100**    | **0.699** | **lower vol → more likely** |
| spread     | 0.648 | tighter → more likely |
| imb3       | 0.579 | ask-heavy → more likely |
| imb2       | 0.572 | ask-heavy → more likely |
| recent_ret_20 | 0.568 | mid rising → more likely |
| imb1       | 0.556 | ask-heavy → more likely |

**Much cleaner signal on VEV_5200**: `rv100` AUC 0.70 alone is meaningful. Mark 22
sells VEV_5200 when realised vol is low and spread is tight — the
"calm-market sweep" pattern of a passive provider working an order.

**Best 2-feature rule (VEV_5200)**: `rv100 <= 0.628` AND `spread <= 2` →
`P(sell next 5) = 2.24 %` vs base 0.92 % (**lift ≈ 2.44×**).

The VEV_5200 trigger is more practical because the signal is stronger and the
downstream effect (smile-shift spillover into deeper-ITM vouchers) is documented
in Phase 3.

---

## D. Side rule

### VFE — direction & timing
- 101 sells, 25 buys (sell ratio 80 %).
- **Sells**: prior `recent_ret_20` mean = **+0.23**, median = **+0.50**, pos/neg/zero = 54/44/3 → Mark 22 sells **slightly after price rose** (mild mean-revert taker on the sell side).
- **Buys**: prior `recent_ret_20` mean = **−0.78**, median = **+1.00**, pos/neg/zero = 13/12/0 → roughly symmetric, no consistent timing.
- **Day breakdown** day1/2/3: 10/40, 9/37, 6/24 — sells dominate every day; buy share rises from 20 % d1 to 20 % d3 (stable).

The sell side is the actionable side: prints land **at small local peaks** then
the price drifts down at h=100–500 (see G).

### HYD — only 19 prints; both sides odd
- 11 buys, 8 sells.
- **Buys**: `recent_ret_20` mean = +1.82, 7/4/0 — buys land *after* the price ROSE, dmid_h100 = **−9.82** (t = −1.96): the price **drops** after Mark 22 buys. Adversarial.
- **Sells**: `recent_ret_20` mean = +5.19, 8/0/0 — sells **also** land after the price rose, dmid_h100 = **−8.43** (t = −1.05): price ALSO drops after Mark 22 sells.
- HYD sample is tiny and Mark 22 trades 100 % against **Mark 38** here — the bag-holder. Both Mark 22 sides on HYD look like "trades that follow Mark 38's bad timing" rather than informed Mark 22 activity. Treat as Mark 38's adversarial signal showing through.
- Counterparty 100 % Mark 38 → the right framing is "what Mark 38 chooses to do with Mark 22".

### OTM vouchers — sidedness
| Product | Buys | Sells | % Mark 01 | Pattern |
|---|---|---|---|---|
| VEV_5300 | 1 | 163 | 80 % | sell-only MM with Mark 01 (some Mark 14 too) |
| VEV_5400 | 0 | 276 | 95 % | sell-only MM |
| VEV_5500 | 0 | 306 | 98 % | sell-only MM |
| VEV_6000 | 0 | 317 | 100 % | stuck-strike, all Mark 01 |
| VEV_6500 | 0 | 317 | 100 % | stuck-strike, all Mark 01 |

VEV_5500/6000/6500 are **100 %-or-near-100 % Mark 01 paired sells** with mode-2 size — pure
MM behavior. VEV_5200 starts the smile shift (only 72 % Mark 14, 24 % Mark 01) and so
behaves differently (see H).

---

## E. Aggressor profile

| Product | Side | n | Aggressor mix |
|---|---|---|---|
| VFE | sell | 101 | ambiguous 89 %, sell 8 %, buy 3 % |
| VFE | buy  | 25  | ambiguous 100 % |
| HYD | sell | 8   | ambiguous 100 % |
| HYD | buy  | 11  | ambiguous 100 % |
| VEV_5200 | sell | 46 | sell 65 %, ambiguous 35 % |
| VEV_5300 | sell | 163 | sell 80 %, ambiguous 20 % |
| VEV_5400 | sell | 276 | sell 95 %, ambiguous 5 % |
| VEV_5500 | sell | 306 | sell 98 %, ambiguous 2 % |
| VEV_6000 | sell | 317 | sell 100 % |
| VEV_6500 | sell | 317 | sell 100 % |

Mark 22's **OTM voucher sells are passive** (resting offers being lifted) — the higher
the strike, the more clean-passive: 100 % at the stuck strikes. Confirms the
"voucher MM offer at the ask" archetype.

VFE sells are nearly all **ambiguous** (89 %): trades happen between bid and ask,
so the book is trading INSIDE the quoted spread (suggests a single-tick spread
was met by both sides simultaneously, or trades printed at the mid). Only 8 % are
"sell-aggressor" (resting bid hit). Mark 22 is **not** strongly aggressive on VFE
either — they are slow / patient sellers, not market sweeping.

VEV_5200 is in between (65 % sell-passive, 35 % ambiguous) — a blend.

---

## F. Inventory dynamics

End-of-day `inventory_day` per product (negative = net short / sold):

| Product | day1 | day2 | day3 | end_cum |
|---|---|---|---|---|
| VFE | −213 | −190 | −148 | **−551** |
| VEV_5200 | −22 | −26 | −108 | **−156** |
| VEV_5300 | −130 | −162 | −250 | **−542** |
| VEV_5400 | −286 | −283 | −390 | **−959** |
| VEV_5500 | −321 | −335 | −413 | **−1069** |
| VEV_6000 | −345 | −337 | −423 | **−1105** |
| VEV_6500 | −345 | −337 | −423 | **−1105** |
| HYD | +4 | −2 | +8 | **+10** |

Observations:
- **OTM vouchers**: inventory grows essentially **linearly** in the negative direction — the
  classic "MM accumulates a short position by selling at the offer". VEV_6000/6500 are
  identical to the share — confirms structural symmetric pair behavior with Mark 01.
- **VFE**: inventory range each day is 195–210 — Mark 22 nets short 150–215 every day,
  much wider swings, two-sided trading. Day-over-day shrinking trend in absolute size
  (213 → 190 → 148) suggests Mark 22 is **scaling down VFE** through the historical sample.
- **HYD**: inventory hovers near zero (+4, −2, +8) → **two-sided market making**, not
  directional. Net cum +10 on n=19.
- **VEV_5200**: day3 alone is **−108** (vs −22, −26 on d1/d2) — the smile-shift
  catalyst was concentrated on day 3.

Position-limit context: VEV cap is 300; Mark 22's per-day VEV inventory frequently
exceeds 300. Mark 22 is unconstrained by the limit — likely the **market** itself,
not a position-limited trader.

---

## G. Adverse selection

`adverse_select_100 = (mid_post_100 − price)` for buys, `(price − mid_post_100)` for sells.
Positive = good for Mark 22.

### VFE (the headline question — reconciling negative h500 PnL)
| Side | n | adv5 (t) | adv20 (t) | adv100 (t) | adv500 (t) |
|---|---|---|---|---|---|
| **buy**  | 25  | +0.48 (+0.93) | **+2.02 (+2.49)** | +3.08 (+1.55) | +3.40 (+0.92) |
| **sell** | 101 | **−0.84 (−4.15)** | −0.76 (−1.79) | +0.35 (+0.37) | +1.33 (+0.68) |

- **Sells** are short-term **adversely selected**: adv5 = −0.84 with t = −4.15
  means the price moves AGAINST Mark 22 by 0.84 in the next 5 ticks (price ticks
  up immediately after their sell — not informed at h=5).
- **By h=100**, sign flips: adv100 mean = +0.35 (small, t insignificant). At h=500,
  adv500 = +1.33 t=0.68. So Mark 22's sells are **slow-horizon mildly profitable**.
- **Day breakdown**: day1 adv100 = −2.74 t=−1.76 (bad), day2 = +1.22 (neutral), day3 = +4.19 (t=2.15, good). Day-3 sell-side improves materially.
- **Buys are clean**: adv20 = +2.02 t = +2.49 — significant, n=25. Mark 22's small
  number of VFE buys are well-timed mean-revert dips.

**Reconciling the negative h500 PnL** (-3,058 XIRECS, -0.52/unit per the brief):
the loss comes from the OTM voucher MM book bleeding (see below), **not** VFE.
On VFE alone, Mark 22 is roughly net flat to mildly profitable on slow horizons.

### OTM vouchers (the bleed)

All have **sell-side adv100 negative** (sometimes only marginally because the strikes
are stuck near 0.5):

| Product | adv5 (t) | adv20 (t) | adv100 (t) |
|---|---|---|---|
| VEV_5300 | −0.68 (−11.1) | −0.75 (−5.9) | −1.06 (−4.2) |
| VEV_5400 | −0.56 (−22.6) | −0.61 (−12.8) | −0.55 (−6.1) |
| VEV_5500 | −0.50 (−35.5) | −0.54 (−22.0) | −0.49 (−11.9) |
| VEV_6000 | −0.50 (0.0)*  | −0.50 (0.0)*  | −0.50 (n/a)* |
| VEV_6500 | −0.50 (0.0)*  | −0.50 (0.0)*  | −0.50 (n/a)* |

*Stuck at 0.5 — they sell a unit at price=1.0 against a mid=0.5, instant −0.50/unit
mark-to-market that never recovers. Aggregate over ~317 sells per stuck strike: ≈
−158 XIRECS per stuck strike per day. Two stuck strikes × 3 days ≈ **~950 XIRECS** of
the −3,058 XIRECS comes from this stuck pricing alone.

### VEV_5200
| Side | adv5 (t) | adv20 (t) | adv100 (t) |
|---|---|---|---|
| sell vs Mark 14 (n=33) | −0.76 (−4.5) | −1.02 (−1.7) | −0.91 (−0.8) |
| sell vs Mark 01 (n=11) | −0.82 (−2.4) | −1.86 (−1.8) | −3.77 (−2.2) |
| sell ALL (n=46)        | −0.73 (−4.9) | −1.16 (−2.4) | −1.82 (−2.0) |

Both halves of VEV_5200 sells are **negatively selected** (Mark 22 is the loser per
unit). The VEV_5200 sell prints predict that the voucher's **mid_pre is too LOW**
(i.e. the trader on the other side has the better short-term view); on the
**deeper-ITM** vouchers the same prints trigger the smile-shift co-print that
Phase 3 will pick up.

### HYD
| Side | adv5 (t) | adv20 (t) | adv100 (t) |
|---|---|---|---|
| buy (n=11)  | +1.41 (+1.5) | −1.77 (−0.7) | **−9.00 (−1.83)** |
| sell (n=8)  | +0.38 (+0.2) | +2.25 (+1.2) | +8.00 (+1.0) |

HYD buys are catastrophically adverse at h=100 (mean −9.0 in price units → about
**$99 lost per buy** at qty ≈ 4). Sells are nominally positive but n=8 and noisy.

Important: HYD adv100 buy = −9.00 (t = −1.83) and dmid_h100 = −9.82 (t = −1.96).
Both directions agree — when Mark 22 buys HYD, the price reliably drops by about
~10 ticks. **High effect size, low n.** The signal is real but needs gating in deployment.

---

## H. Counterparty selection

| Product | Mark 22 side | Top counterparties |
|---|---|---|
| VFE   | sell (n=101) | Mark 67 = 75 (74 %), Mark 55 = 14 (14 %), Mark 49 = 12 (12 %) |
| VFE   | buy  (n=25)  | Mark 55 = 18 (72 %), Mark 49 = 7 (28 %) |
| VEV_5200 | sell (n=46) | **Mark 14 = 33 (72 %)**, Mark 01 = 11 (24 %), Mark 38 = 2 (4 %) |
| VEV_5300 | sell (n=163) | Mark 01 = 132 (81 %), Mark 14 = 30 (18 %) |
| VEV_5400 | sell (n=276) | Mark 01 = 263 (95 %), Mark 14 = 13 (5 %) |
| VEV_5500 | sell (n=306) | **Mark 01 = 299 (98 %)**, Mark 14 = 7 |
| VEV_6000 | sell (n=317) | **Mark 01 = 317 (100 %)** |
| VEV_6500 | sell (n=317) | **Mark 01 = 317 (100 %)** |
| HYD   | sell (n=8)  | **Mark 38 = 8 (100 %)** |
| HYD   | buy  (n=11) | **Mark 38 = 11 (100 %)** |

Three structural counterparty pairs:

1. **Mark 22 ↔ Mark 01** on OTM vouchers (cross-cutting, hardest at stuck strikes).
   This is the disclosed "voucher MM dyad" mentioned in `headline_findings.md`.
2. **Mark 22 ↔ Mark 14** on VEV_5200 (33/46 = 72 %, day-3 dominant: 19/30 sells).
   Day-3 jump (8 d1+d2 sells → 19 d3) suggests Mark 14 ramped a directional bet
   in this strike on day 3. Mark 22 was the passive seller they hit. Smile-shift
   downstream is the cross-product signal worth scraping.
3. **Mark 22 ↔ Mark 38** on HYD (100 %, both sides). Tiny n, but Mark 38's
   adversarial reputation (the "bag-holder" per headline) suggests Mark 22's
   counterparty selection on HYD is itself a tell — they're trading with the
   weakest hand in the market. The price drops shown in (G) likely reflect
   **Mark 38's adversity** propagating, not Mark 22's directional view.

VFE counterparties are different: Mark 22 sells **into Mark 67** (74 %) and buys
from Mark 55 / Mark 49. Recall Mark 67 is the buy-only VFE bot tagged in the
headline (1,510 buys, 0 sells, +1.19/unit). So Mark 22 is **the supply that
Mark 67 keeps absorbing**: Mark 22 sells, Mark 67 buys, both make slow-horizon
positive PnL — they're trading at slightly different price points.

---

## I. Microstructure footprint

### VFE Mark 22 SELLS (the informed signal — n=101)
| Pre-trade condition | Conditional rate | Unconditional |
|---|---|---|
| recent_ret_5 > 0 (mid up in last 5)        | 50 %  | ~50 % |
| recent_ret_5 ≥ 1 tick (mid up ≥ 1)         | 46 %  | ~50 % |
| recent_ret_20 > 0                          | 53 %  | ~50 % |
| imb1 > 0 (bid heavy)                       | 28 %  | ~50 % |
| imb1 < 0 (ask heavy)                       | 33 %  | ~50 % |
| spread > median (5)                        | 20 %  | 50 % |
| depth_ask < median (60)                    | 48 %  | 50 % |

**No strong microstructure tell** — VFE sells happen across all book states.
The sells lean slightly bid-light/ask-light (imb1 < 0 33 % vs imb1 > 0 28 %), but
the effect is too weak to gate on. Spreads are usually at the floor (5).

### HYD Mark 22 BUYS (the adversarial signal — n=11)
| Pre-trade condition | Conditional rate |
|---|---|
| recent_ret_5 > 0     | 36 % |
| recent_ret_5 ≥ 1     | 36 % |
| recent_ret_20 > 0    | 64 % (mid up over last 20) |
| recent_ret_20 < 0    | 36 % |
| imb1 > 0             | **0 %** |
| imb1 < 0             | **0 %** |
| spread > median (16) | 0 % |
| depth_ask < median (38) | 45 % |

The 0/0 on imb1 (and 0 % spread > 16) is interesting: every HYD buy print
happened on a **flat-imbalance** book (imb1 = 0) with the **maximum tight
spread** for HYD. Combined with `recent_ret_20 > 0 64 %`, the picture is "Mark 22
buys HYD at narrow-spread peaks". With only 11 prints though, the book-state
constraint is more a footprint than a usable trigger.

### VEV_5200 Mark 22 SELLS — see C above for rv100/spread feature ranking
The strongest microstructure tell is at VEV_5200 (rv100 AUC 0.70). Use that.

---

## J. Bot archetype (per product)

1. **OTM vouchers (VEV_5300/5400/5500/6000/6500)** — *Voucher MM provider*.
   Sell-only, paired with Mark 01 buyer (80–100 %), passive aggressor (sell or
   ambiguous), inventory grows linearly negative, mode-2 lot. Stuck strikes
   (6000/6500) bleed −0.5/unit by construction. **Confidence: HIGH.**

2. **VEV_5200** — *Smile-shift trigger / passive seller*. 72 % paired with
   Mark 14, 65 % sell-aggressor (lifting bids), microstructure-predictable
   (rv100 AUC 0.70). The downstream effect on deeper-ITM vouchers is the value;
   Mark 22's own VEV_5200 PnL is mildly negative. **Confidence: MED.**

3. **VELVETFRUIT_EXTRACT** — *Slow informed seller* (mean-revert flavour).
   Two-sided but heavy sell skew (101 vs 25), variable size (mode 5),
   ambiguous-aggressor (89 % of sells), prior `recent_ret_20` slightly positive
   (sells follow small price rises), short-term adversely selected (adv5 t=−4.15)
   but slow-horizon profitable (adv500 +1.33). Sells "into the rally" then get a
   mean-revert payoff at h=100–500. **Confidence: MED.**

4. **HYDROGEL_PACK** — *Wrong-way-buyer* on n=11. dmid_h100 = −9.8 t=−1.96 on buys
   says price falls hard after Mark 22 buys. But 100 % counterparty is Mark 38
   (the disclosed bag-holder), so the signal may be "Mark 38 forces Mark 22 to
   accept a bad fill" rather than Mark 22 being intrinsically informed-wrong.
   **Confidence: LOW (n) / HIGH (effect size).**

5. **VEV_4000/4500/5000/5100** — n=3 each, ignore.

---

## K. Exploitation hypothesis (per product)

### K-VFE: lean −VFE on Mark 22 sells (carry-over **R4-VFE-M03**)
The brief's prior signal: h=1 t = +7.8/+7.2/+3.1 was strong. Our re-run
confirms a slow but real signal: dmid_h100 = −1.04 (n=100), dmid_h500 = −1.33
(n=92). Caveats:
- adv5 is **negative** for Mark 22 (price ticks UP immediately after their sell)
  → the immediate t+1..t+3 reaction is the OPPOSITE direction. Don't fade
  Mark 22 within 1-2 ticks; wait for h=20+ for the reversion.
- Day-1 sells lose money for Mark 22 (adv100 t=-1.76); day-3 sells make money
  for them (adv100 t=+2.15). Fade strength is non-stationary.
- **Suggested rule**: when Mark 22 prints a VFE sell, set a target lean of
  −X units of VFE (X scaled by qty) with target horizon 100 ticks (10,000 ts).
  Position-limit budget on VFE = 200; allocate ≤ 30 to Mark 22 lean so other
  alphas (B1 wall-mid MM) have room.
- **Filter**: gate on `recent_ret_20 > 0` (sell-after-rally case) — the brief's
  "h=1 t=+7.8" likely captured the after-rally subset.

### K-HYD: fade Mark 22 buys (NEW — but small-n)
- Effect: dmid_h100 = −9.82 t=−1.96 on n=11. Fading them ≈ +9 ticks per print
  (≈ +36 expected per buy at qty 4) IF the signal holds.
- Counterparty filter: 100 % Mark 38. The cleaner framing in deployment is
  "fade trades where Mark 38 sells HYD to Mark 22" — that captures the same
  prints with two confirming names.
- **Suggested rule**: when a HYD print appears with `seller=Mark 38, buyer=Mark 22`,
  open a short HYD position of size = qty (capped 10 units), target 100 ticks.
  HYD limit = 200; cap total Mark-driven exposure at 50.
- Risk: **n=11**. Need ≥ 30 prints in live before scaling beyond 1× qty. Treat
  as "experimental" rather than carry-over alpha.
- Re-evaluate after the first day of live data; if the per-trade effect is
  attenuated (< 50 % of the historical magnitude), kill.

### K-OTM vouchers: AVOID — pure MM noise
- VEV_5300/5400/5500/6000/6500 prints from Mark 22 are paired with Mark 01 in
  80–100 % of cases. Both sides are constant-quantum mode-2 sells against
  constant-quantum buys. Stuck-strike vouchers (6000/6500) are mid-pinned at 0.5.
- Do **NOT** use Mark 22 sell prints on these strikes as a directional signal.
  They are voucher MM activity, **not** directional.
- D1 (the IV-residual scalp) operates on the smile fit, not on Mark 22 prints —
  no overlap with this dossier.

### K-VEV_5200: cross-product co-print (Phase 3 territory)
- Mark 22 ↔ Mark 14 sells on VEV_5200 trigger smile-shift downstream; the
  Phase 3 cross-product analysis will pick this up properly. Note here only.
- Day-3 concentration (19 of 30 d3 VEV_5200 sells go Mark 22 → Mark 14) means
  the live signal is **time-uneven**: don't expect uniform daily firing. If the
  live R4 day shows Mark 22's VEV_5200 sells clustering in a single window,
  expect a downstream smile shift in the next 100 ticks.

---

## Priorities going into Round 4 live

1. **Ship**: K-VFE (`lean −VFE on Mark 22 sells`, gated on `recent_ret_20 > 0`,
   horizon 100 ticks). Already validated by the brief and confirmed on h=100/500
   here.
2. **Experimental**: K-HYD (fade Mark 22 buys = `seller=Mark 38, buyer=Mark 22`
   prints). Real effect, tiny n. Start at 1× qty; scale only after ≥ 30 live prints.
3. **Defer to Phase 3**: K-VEV_5200 cross-product smile-shift exploitation.
4. **Ignore**: all OTM voucher Mark 22 activity.
