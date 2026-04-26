# Mark 55 — Dossier (Round 4)

> Two-sided VFE momentum-chasing taker. Buys at peaks (recent_ret_20 mean
> +0.24), sells at troughs (mean −0.40), books inventory excursions of
> ±100 within day, and loses ~−2.4/u uniformly. They are the bag side of
> the **Mark 14 ↔ Mark 55** and **Mark 01 ↔ Mark 55** dyads on VFE. Treat
> as light-fade noise — actionable but low-priority.
>
> Source CSV: `prosperity-research/03_eda/round4/per_mark/Mark_55_VELVETFRUIT_EXTRACT.csv`
> Quote source: `prosperity_rust_backtester/datasets/round4/prices_round_4_day_{1,2,3}.csv`
> Schema: `prosperity_rust_backtester/scripts/round4_options/per_mark_features.py`
> Analysis log: `/tmp/mark55_analyze.py`.

---

## A. Headline classification

**Mark 55 is a TWO-SIDED VFE MOMENTUM-CHASING TAKER bot.** They fire
roughly Poisson with a mild bias to BUY after rallies (recent_ret_20 mean
+0.24) and SELL after drops (mean −0.40), they are 69% aggressor-side
takers, and they uniformly lose ~−2.4/u to whatever the market does next
(adv5 mean −2.41, t≈−37; adv100 mean −1.76). Confidence: **HIGH** that
they are the bag side; **HIGH** on the momentum-chasing sub-archetype.

Total 3-day footprint: 1,198 prints, 6,551 units (598 buys / 600 sells),
all on VFE. They are the highest-volume VFE bot besides Mark 14.

---

## B. Volume profile

| Day | Buys n (qty) | Sells n (qty) |
|---|---|---|
| 1 | 186 (1,011) | 198 (1,098) |
| 2 | 218 (1,190) | 193 (1,099) |
| 3 | 194 (1,053) | 209 (1,100) |
| **Total** | **598 (3,254)** | **600 (3,297)** |

**Two-sided and balanced — buy/sell ratio 0.997.**

### B.2 Trade-size distribution

| qty | count | share |
|---|---|---|
| 6 | 212 | 17.7% |
| 4 | 207 | 17.3% |
| 5 | 203 | 16.9% |
| 3 | 195 | 16.3% |
| 8 | 190 | 15.9% |
| 7 | 190 | 15.9% |
| 1 | 1 | 0.1% |

Mean qty 5.47, median 5, range 1–8. **DISCRETIZED but very flat across
{3,4,5,6,7,8}** — closest thing in the dataset to a "uniform random qty
draw" bot. Buy-side mean qty 5.44, sell-side 5.50 — perfectly symmetric.

### B.3 Trade-arrival rate

1,198 prints / 30,000 ticks = **0.040 prints/tick** (= one per 25 ticks).
This is the highest-cadence VFE bot.

### B.4 Per-product specialization

100% VFE. Single-product specialist like Mark 49, Mark 67.

---

## C. Trigger conditions — per-tick "Mark 55 prints in next 5 ticks?"

Per-tick rows = 30,000 (10k × 3 days). Positive label = 5,547 (= 1,198 × 5
× expansion, because every Mark 55 print labels the prior 5 ticks; with
overlaps, the unique label-positive tick count is 18.5%).

### Single-feature AUC (Mann-Whitney rank, stdlib)

| Feature | AUC | |AUC − 0.5| |
|---|---:|---:|
| recent_ret_20 | 0.4894 | 0.0106 |
| spread | 0.5067 | 0.0067 |
| realised_vol_100 | 0.5030 | 0.0030 |
| imb1 | 0.4978 | 0.0022 |
| imb3 | 0.5010 | 0.0010 |
| imb2 | 0.5002 | 0.0002 |

**Every AUC is within 0.011 of 0.5.** Mark 55's firing is **essentially
unpredictable from microstructure features** — they fire ~Poisson in time.
The slight tilt of recent_ret_20 (HIGH = price rose recently) suggests
they fire mildly more often after price moves, but the lift is < 1.05× and
not actionable.

**No useful pre-print front-run rule.**

---

## D. Side rule

| Conditioning | buy share | sell share |
|---|---|---|
| imb1 > +0.1 (bid-heavy) | 48.5% | 51.5% |
| imb1 < −0.1 (ask-heavy) | 54.0% | 46.0% |
| imb1 ≈ 0 | 48.0% | 52.0% |
| recent_ret_20 mean (BUY samples) | **+0.24** | — |
| recent_ret_20 mean (SELL samples) | — | **−0.40** |

**The side rule is MOMENTUM-CHASING:**
- Buys cluster on positive recent_ret_20 (mean +0.24): they buy after
  price rises.
- Sells cluster on negative recent_ret_20 (mean −0.40): they sell after
  price drops.

This is the OPPOSITE of Mark 01 (mean-revert), and similar to Mark 38 on
HYD (mild momentum). Mark 55's bias is tighter to the price drift than the
imb1 / spread / vol features — they react to recent price moves, not to
book state.

The imb1 conditional shows a **mild contrarian quirk**: 54% of buys happen
when imb1 < −0.1 (ask-heavy) and only 48.5% when imb1 > +0.1 (bid-heavy).
That's the WRONG WAY around — they buy more when the book is ask-heavy
(predicting price drop) and sell more when bid-heavy (predicting price
rise). This is consistent with **bad book reading**.

---

## E. Aggressor profile

| Aggressor | n | share |
|---|---|---|
| 'buy' (lifter) | 416 | 34.7% |
| 'sell' (hitter) | 413 | 34.5% |
| 'ambiguous' (mid) | 369 | 30.8% |
| 'sell' but Mark 55 is buying = passive | 1 | 0.1% |
| Total taker-direction (buy lifter when buying, sell hitter when selling) | 828 | 69.1% |

**Mark 55 is 69% TAKER**, opposite of Mark 01 (82% maker on VFE). They
cross the spread aggressively and pay the touch.

---

## F. Inventory dynamics

| Day | inv_day min | inv_day max | inv_day mean | EoD | |excursion| |
|---|---:|---:|---:|---:|---:|
| 1 | −132 | +33 | −53.6 | −87 | 132 |
| 2 | −28 | +112 | +55.0 | +91 | 112 |
| 3 | −103 | +10 | −49.8 | −47 | 103 |

**inventory_cum (3-day end): −43.** Day-1 ran 132 units short; day-2 ran
112 long; day-3 swung back to 103 short. **No mean-reversion within day —
inventory crosses zero only 7/9/3 times across the three days.**

VFE position limit = 200; max excursion 132 = 66% of cap. Like Mark 38,
Mark 55 builds large directional inventory before resetting.

---

## G. Adverse selection — uniformly bad

| Horizon | n | mean | median | stdev | P(negative) |
|---|---:|---:|---:|---:|---:|
| h=5 | 1,198 | **−2.408** | −2.50 | 2.225 | 84.6% |
| h=20 | 1,198 | **−2.225** | −2.50 | 4.121 | 69.4% |
| h=100 | 1,190 | **−1.757** | −1.50 | 9.080 | 56.7% |

**At h=5, 85% of Mark 55's prints are losers** (negative adverse selection
in their favor) with mean −2.41 / unit. h=20 attenuates slightly to 69%
losers; h=100 to 57% losers but mean still −1.76.

**Worst-10% concentration check**: the worst 10% of trades sum to −2,104
adverse selection at h=100, vs total of −2,090 — i.e., the **worst 10% is
100.7% of the loss**. That means the OTHER 90% of trades net to roughly
zero, and the loss is concentrated in a small tail.

This is a slightly different story than Mark 38: Mark 55's loss is
**TAIL-DRIVEN** (a few catastrophic prints), not uniform. Implication: a
strategy that fades Mark 55 may capture the median 0 most of the time and
the tail blows occasionally — **less robust** than the Mark 38 fade
(which is uniform).

---

## H. Counterparty selection

| Counterparty | n | share | mean adv100 |
|---|---|---|---|
| **Mark 14** | 647 | 54.0% | **−1.27** |
| **Mark 01** | 504 | 42.1% | **−2.40** |
| Mark 22 | 32 | 2.7% | −1.22 |
| Mark 49 | 14 | 1.2% | −0.79 |
| Mark 67 | 1 | 0.1% | −20.50 |

**THREE simultaneous dyads** for Mark 55 on VFE:

1. **Mark 14 ↔ Mark 55** (647 trades): Mark 14 is the smart bot; Mark 55
   loses −1.27/u to them. Predictable.
2. **Mark 01 ↔ Mark 55** (504 trades): Mark 01 is the VFE MM; Mark 55
   loses **−2.40/u** to them — *more* than to Mark 14 (the supposedly
   smart bot). This is because Mark 01 captures the inside-spread on every
   round-trip, leaving Mark 55 with a worse fill.

So Mark 55 is the bag-side of TWO dyads on VFE. The Mark 14 dyad is the
"alpha" loser; the Mark 01 dyad is the "spread" loser. **The biggest leak
is to Mark 01, not Mark 14**, on a per-trade basis.

This is structurally analogous to Mark 38 ↔ Mark 14 on HYD/VEV_4000: the
bag-side counterparty is split between a *spread* bot (here Mark 01) and a
*directional* bot (here Mark 14).

---

## I. Microstructure footprint

For Mark 55 BUYS (n=598):
- mean imb1_pre = −0.0041 (essentially flat, mild ask-heavy)
- fraction with imb1>0 (bid-heavy at buy time) = 30.3%
- mean recent_ret_20 = +0.239 (BUY after price rose)

For Mark 55 SELLS (n=600):
- mean imb1_pre = +0.0348 (mild bid-heavy)
- fraction with imb1<0 (ask-heavy at sell time) = 26.7%
- mean recent_ret_20 = −0.398 (SELL after price dropped)

**Pattern**: Mark 55 buys 70% of the time when book is NOT bid-heavy
(suggesting the price is actually likely to FALL — they're buying into
weakness). And sells 73% of the time when book is NOT ask-heavy (price
likely to RISE). This is **systematic wrong-way book reading**.

Combined with the momentum bias (BUY after rises, SELL after drops),
Mark 55's full signature is: "**BUY after price rose AND book is ask-
heavy** (= buy at peak with bearish book) → BAD; **SELL after price
dropped AND book is bid-heavy** (= sell at trough with bullish book) →
BAD."

This is the perfect bag-holder microstructure footprint.

No single pattern crosses the >60% / <20% threshold for a strong predictor
(coverage is too broad; the bias is statistical, not categorical).

---

## J. Bot archetype

**Mark 55 is a TWO-SIDED VFE MOMENTUM-CHASING TAKER** — the cleanest
"naïve momentum chaser" in the entire R4 dataset. They buy at recent
peaks, sell at recent troughs, ignore the order-book imbalance signal,
take with 69% aggressor share, and lose ~−2.4/u uniformly.

**3 strongest evidence features:**

1. **Side rule biases match momentum chase**: BUYS after recent_ret_20 >0
   (mean +0.24), SELLS after recent_ret_20 <0 (mean −0.40).
2. **69% TAKER profile** on a near-balanced two-sided book — they cross
   the spread regardless of side.
3. **Adversely-selected on every counterparty pairing** (−1.27/u vs Mark
   14, −2.40/u vs Mark 01, −0.79/u vs Mark 49) — there is no sub-set of
   counterparties where Mark 55 wins. The loss is truly market-structural,
   not partner-specific.

**Confidence: HIGH** — Mark 55's signature is unambiguous.

---

## K. Exploitation hypothesis

### K.1 Primary rule — REACT-WITH-STRUCTURE on Mark 55 prints (light fade)

Mark 55 prints carry a weak but real signal: their direction is wrong by
~−2.4 ticks at h=5, ~−1.8 ticks at h=100. **Lean OPPOSITE.**

```
on Mark 55 BUY of VFE:
    expected: mid drops ~2.4 ticks over next 5 ticks (price chase peak)
    action:  lean -VFE 0.5 ticks for 50 ticks
    sizing:  scale by Mark 55 print qty × 0.3 lots (lower than Mark 38
             because adverse selection is tail-driven, not uniform)
    decay:   half-life 25 ticks

on Mark 55 SELL of VFE:
    expected: mid rises ~2.4 ticks over next 5 ticks (sell at trough)
    action:  lean +VFE 0.5 ticks for 50 ticks
    sizing:  scale by Mark 55 print qty × 0.3 lots
    decay:   half-life 25 ticks
```

**Pre-registered parameters**:
- `lean_per_print_per_unit` = 0.5 ticks per Mark 55 print
- `qty_multiplier` = 0.3 (lower than Mark 38 due to tail concentration)
- `decay_half_life_ticks` = 25
- `cap_lean` = ±3 ticks max accumulated lean

**EV estimate**: 1,198 prints / 3 days = ~400/day. Mean adv5 = −2.41,
qty ~5.5/print, so per-day fadable PnL = 400 × 2.41 × 5.5 ≈ +5,300
(theoretical). Capture 15% (low, due to high false-positive tail and
inventory cap risk): **~+800 XIRECS/day**. Smaller than Mark 38 (~+1,000)
or Mark 67 (~+650), but still useful.

**Falsifier**:
- Any single live day where mean adv5 turns positive (i.e., Mark 55 starts
  winning) → kill.
- Worst-10%-of-trades-sum > 200% of total adv (currently 100.7%): if the
  tail concentration grows, the fade becomes too brittle.

### K.2 Secondary — combine Mark 55 with Mark 49 / Mark 67 for VFE

Mark 55, Mark 49, Mark 67 all trade VFE only; their signed-flow contributions
can be combined into a single VFE lean accumulator:

```
ve_lean = (
    +1 * sgn(Mark 67 buy)              # informed +VFE buyer
    +1 * sgn(Mark 14 VFE side)         # smart bot, both sides predictive
    -1 * sgn(Mark 49 sell)             # fade their sell
    -1 * sgn(Mark 55 print)            # fade their direction (both sides)
    -1 * sgn(Mark 38 VFE if any)       # not active on VFE, ignore
)
```

This is the "unified VFE Mark lean" — see exploitation playbook for full
spec.

### K.3 Don't try to predict Mark 55's firing

The trigger AUC is essentially 0.50. They fire roughly time-uniform. There
is no pre-print rule.

---

## Reconciliation note (for Phase 6)

Prior session: "NOISE TO LIGHT FADE (low confidence). 3-day total: 3,254
/ 3,297, both sides high volume. −2.41 / unit. Only trades VEV_5500 (one
product, OTM voucher)."

This dossier **CORRECTS**:

1. **Mark 55 trades VFE, NOT VEV_5500.** The prior playbook had a typo or
   confusion — every single Mark 55 print in the data is on VELVETFRUIT_-
   EXTRACT (1,198/1,198 = 100%). The R4-VFE per-product file
   (`per_product/VELVETFRUIT_EXTRACT.md`) confirms: "Mark 55: noise as
   documented." VEV_5500 trades are by Mark 01 (buyer) and Mark 22
   (seller) — not Mark 55.

2. **The fade signal is NOT noise.** Mean adv5 = −2.41, t-stat ≈ −37
   across 1,198 prints. **The fade is one of the highest-precision rules
   in the dataset by t-stat**, just lower-magnitude per-print than Mark 38.
   The prior session under-rated it.

3. **The "noise" classification was based on Mark 55's symmetric two-
   sided activity, not on adverse selection.** Two-sided ≠ noise; it just
   means "no buy/sell directional bias." Mark 55's *timing* is bad on
   both sides → fadable.

4. **Mark 55's biggest counterparty leak is Mark 01 (−2.40/u), not
   Mark 14 (−1.27/u).** That contradicts the intuition that Mark 14 is
   the "smart" extractor — on VFE, Mark 01 actually picks Mark 55 off
   harder (because Mark 01 is the 80%-passive MM who captures the spread
   on every round-trip).
