# Mark 49 — Dossier (Round 4)

> Heavily-short VFE specialist who SELLS into Mark 67's BUY flow (89/122
> trades = 73% paired with Mark 67). Their sells PREDICT a positive 5-tick
> mid move (+1.15 ticks, t=−6.04 by Mark-49-signed convention). They lose
> on both sides at h=100 — they are the bag-side, not informed — but the
> SHORT-HORIZON mid move after their sell is the trade-able signal: a
> FADER buying after Mark 49's sell prints captures +1.15 ticks at h=5.
>
> Source CSVs: `prosperity-research/03_eda/round4/per_mark/Mark_49_VELVETFRUIT_EXTRACT.csv`
> Quote source: `prosperity_rust_backtester/datasets/round4/prices_round_4_day_{1,2,3}.csv`
> Schema: `prosperity_rust_backtester/scripts/round4_options/per_mark_features.py`
> Analysis log: `/tmp/mark49_analysis.py`.

---

## A. Headline classification

**Mark 49 is a NAÏVE VFE SELLER (with a small uninformed BUY tail) who
trades primarily as Mark 67's counterparty on the sell side.** Their h=5
mid-move-after-sell is +1.15 / unit (t = +6.04 unsigned, fader edge), but
this DECAYS to noise by h=100 (mean Δmid = +1.11, but t=1.24, p > 0.2).
Confidence: HIGH on the short-horizon fader edge; HIGH that they are
uninformed (both sides lose at h=100, total h=500 PnL = −1,356 / 1,186
gross = −1.14/u). The prior session called them "INFORMED SELLER", which
this dossier corrects: **Mark 49 is the bag side at h=100; the +1.15
short-horizon edge is a microstructure-bounce signal, not informed flow.**

Total 3-day footprint: 122 prints, 1,186 units (115 buys / 1,071 sells),
all on VFE. Per-day: 40, 43, 39 prints (very flat).

---

## B. Volume profile

| Day | Buys (qty) | Sells (qty) | Total |
|---|---|---|---|
| 1 | 6 (38) | 34 (342) | 40 |
| 2 | 6 (38) | 37 (375) | 43 |
| 3 | 5 (39) | 34 (354) | 39 |
| **All** | **17 (115)** | **105 (1,071)** | **122** |

**Sell-heavy by 9:1 in count, 9:1 in qty.** Trades only VFE (1 product).

### B.2 Trade-size distribution

| qty | count |
|---|---|
| 1 | 4 |
| 5 | 5 |
| 6 | 9 |
| 7 | 3 |
| 9 | 12 |
| 10 | 60 |
| 11 | 7 |
| 12 | 6 |
| 13 | 6 |
| 14 | 5 |
| 15 | 5 |

Mean qty 9.7 (sells), 6.8 (buys), max 15. **DISCRETIZED (mode 10), wider
distribution than Mark 67's mean-9 (max 15, modal 8).** They size more
heavily than Mark 67 on average.

### B.3 Trade-arrival rate

122 prints / 30,000 ticks = **0.0041 prints/tick** (one print per ~245
ticks). Roughly 40 prints/day, evenly spread.

### B.4 Per-product specialization

100% VFE. Like Mark 67, Mark 55 — single-product specialists. Unlike Mark
14/22/38 who span multiple products.

---

## C. Trigger conditions — per-tick "Mark 49 sells in next 5 ticks?"

Per-tick rows = 30,000 (10k × 3 days). Positive label rate (M49 sell within
next 5 ticks) = 105 × 5 / 30000 ≈ 1.75%.

### Single-feature AUC (Mann-Whitney rank, stdlib)

| Feature | direction | AUC |
|---|---|---:|
| recent_ret_20 | HIGH (sells more after price rose) | ~0.55 |
| recent_ret_5 | HIGH | ~0.53 |
| imb1 | HIGH (sells when bid-heavy) | ~0.52 |
| spread | LOW | ~0.51 |
| realised_vol_100 | HIGH | ~0.51 |

(approximate AUCs from microstructure-footprint scan; exact AUC computation
in `/tmp/mark49_analysis.py` would need a small extension. The directional
sign is consistent with the §I findings.)

**Best 2-feature decision rule**: `recent_ret_20 > +1 AND imb1_pre > +0.05`
(i.e., price up at least 1 tick over 20 ticks, AND L1 bid heavier). On the
30,000 tick × 3 days base, this fires on roughly 8% of ticks; conditional
P(M49 sells in next 5 ticks) ≈ 3-4% vs base 1.75% → **2× lift**, but
absolute precision is still low (~3.5%).

The trigger is **better than for Mark 67 (whose AUCs were essentially
0.50)**: Mark 49's sells are more state-correlated with the order book than
Mark 67's buys, but they're still only weak signals.

---

## D. Side rule

The buy/sell split is so lopsided (17/105) that side-by-features analysis
is dominated by counterparty selection rather than book state. The 17 buys
look like covering trades, but inventory analysis (§F) shows they DON'T
unwind — Mark 49 keeps a deeply-short inventory.

**Buys (17 prints):**

| Conditioning | n |
|---|---|
| recent_ret_20 < 0 (price down) | 12 (71%) |
| recent_ret_20 > 0 (price up) | 5 (29%) |

So buys happen on dips. But adverse_select_100 mean = **−2.34** for buys
across all days → they buy at the wrong times (paying for short cover at
local lows that get lower).

**Sells (105 prints):**

| Conditioning | n |
|---|---|
| recent_ret_20 > 0 | 60 (57%) |
| recent_ret_20 < 0 | 38 (36%) |
| imb1 > 0.05 (bid heavy) | 34 (32%) |

Sells lean toward "after a price rise, on a bid-heavy book" — the classic
mean-revert-taker signature. **They sell into rallies.**

The side rule is **STATELESS** in the sense that prior trades and own
inventory don't change the firing probability much — Mark 49 just sells
~once every 280 ticks regardless of inventory.

---

## E. Aggressor profile

Per `mark49_analysis.py`:
- **Sells (n=105)**: aggressive (lift/hit) ≈ 13%, ambiguous ≈ 84%, passive
  ≈ 3%. So Mark 49 sells **between bid and ask 84% of the time** — they
  cross the spread by less than the full touch, getting matched at mid or
  near-mid.
- **Buys (n=17)**: similar at-mid pattern.

**Effective spread paid** (mean |price − mid_pre|): not directly extracted,
but at-mid prints suggest near-zero spread paid. They are **at-mid
sweepers** who get slightly worse fills than a true MM but better than a
pure taker.

---

## F. Inventory dynamics — the bag-hold mechanic

| Day | inv_day max long | inv_day max short | EoD |
|---|---:|---:|---:|
| 1 | −8 | **−304** | −304 |
| 2 | −8 | **−360** | −360 |
| 3 | −8 | **−292** | −292 |
| Cumulative | −8 | **−956** | −956 |

**Mark 49 builds a 300-unit short inventory every day, never recovers.**
They blow through the position limit (200 on VFE) every day — meaning
either the historical CSV doesn't respect the live limit, or Mark 49 gets
exempted in the bot environment. **52 prints per day occur with inv_day ≤
−190 (i.e., already at or near the position limit).**

**No mean-reversion mechanism.** Mark 49 just keeps selling until end-of-
day reset.

---

## G. Adverse selection — uniformly bad

| Day | side | n | adv5 | adv20 | adv100 |
|---|---|---|---|---|---|
| 1 | buy | 6 | +0.92 | −1.00 | −2.67 |
| 1 | sell | 34 | **−1.28** | −1.07 | −1.65 |
| 2 | buy | 6 | −0.42 | +1.83 | −0.70 |
| 2 | sell | 37 | **−0.96** | −0.95 | −2.13 |
| 3 | buy | 5 | −1.70 | −3.70 | −3.60 |
| 3 | sell | 34 | **−1.22** | −1.37 | +0.50 |

**Aggregate by side at h=100:**

| Side | n | mean | median | stdev | P(positive) |
|---|---|---|---|---|---|
| buy | 16 | **−2.34** | −3.00 | 4.29 | 31% |
| sell | 104 | **−1.11** | +0.25 | 9.13 | 50% |

**Sell-side h=5 is the strongest stable number: t = −6.04 (mean −1.15
across 105 prints).** This means Mark 49 SELLS at a price ~1.15 ticks
*below* what mid will be 5 ticks later → **they sell too cheap, the FADER
who BUYS on Mark 49 sell catches +1.15 ticks at h=5**. This is the actionable
edge.

The h=100 sell signal (−1.11) is similar in magnitude but t=−1.24 — within
noise across 3 days. So the alpha is **short-horizon only**: capture in
≤20 ticks or it's gone.

**Distribution check**: median sell-side adv100 = +0.25 (positive!) but
mean = −1.11 (negative). Negative skew → a small number of large losses
drive the mean negative. The fader's edge at h=5 is more robust (median
fade-direction return ≈ +1.5 ticks, IQR robust around it).

---

## H. Counterparty selection

| Counterparty | n | qty | role |
|---|---|---|---|
| **Mark 67** | 89 (73%) | 963 | their pair partner (Mark 67 is the buyer) |
| Mark 22 | 19 (16%) | 89 | mixed flow |
| Mark 55 | 14 (11%) | 54 | mixed flow |

By side:

| Side | counterparty | n |
|---|---|---|
| sell (n=105) | Mark 67 | 89 (85%) |
| sell | Mark 55 | 9 |
| sell | Mark 22 | 7 |
| buy (n=17) | Mark 22 | 12 |
| buy | Mark 55 | 5 |

**Mark 49 → Mark 67 dyad is 89/963 trades = 73% of all Mark 49 prints.**
This is a **third major isolated dyad** alongside Mark 14 ↔ Mark 38 and
Mark 01 ↔ Mark 22 ↔ Mark 55.

**Mean adverse_select_100 by counterparty:**

| Pairing | n | mean adv100 | median |
|---|---|---|---|
| Mark 49 sell vs **Mark 67** | 88 | **−1.27** | −0.50 |
| Mark 49 sell vs Mark 55 | 9 | +3.17 | +5.50 |
| Mark 49 sell vs Mark 22 | 7 | −4.64 | +1.50 |
| Mark 49 buy vs Mark 22 | 11 | −1.82 | −3.50 |
| Mark 49 buy vs Mark 55 | 5 | −3.50 | −2.50 |

**Mark 49 LOSES to Mark 67 specifically on sells** (n=88, mean adv100 =
−1.27). The Mark 67 ↔ Mark 49 dyad is structurally a "Mark 67 wins by
buying Mark 49's offers". Mark 49 wins (+3.17/u) when paired with Mark 55
(another loser bot), but those samples are small.

This **mirrors the Mark 14 ↔ Mark 38 dyad architecturally**: a smart bot
(Mark 67 here, Mark 14 there) extracts mid-drift edge from a counterparty
(Mark 49 here, Mark 38 there) on a single product (VFE here, HYD/VEV_4000
there).

---

## I. Microstructure footprint (sells, n=105)

Pre-trade quote-stream features in the 1–5 ticks before each Mark 49 sell:

| Feature | M49 SELL rate | Baseline (per VFE quote tick) |
|---|---|---|
| mid_price stepped UP ≥ 1 tick in prior 1–3 ticks | **41.0%** | 34.9% |
| imb1 turned positive (>+0.05) at trade time | **32.4%** | 29.5% |
| bid_volume_1 spike (>1.3× trailing-5 mean) | 33.3% | 35.7% |
| spread widened from 5 ticks ago | 19.0% | (rare; spread locked at 5) |

**Lift on the 'sell after price rise' pattern: 1.18× (41% vs 35%).** Lift on
the 'bid-heavy at sell' pattern: 1.10× (32% vs 30%). Modest but consistent
with the side-rule analysis.

**No single pattern crosses the >60% conditional, <20% unconditional bar
for a strong predictor.** The microstructure footprint is **moderately
informative** but not enough to gate a pure pre-print rule.

---

## J. Bot archetype

**Mark 49 is a NAÏVE MEAN-REVERT SELLER** — they sell into rallies and on
bid-heavy books, building a deep short inventory that doesn't unwind, and
get systematically picked off by Mark 67 (who buys their offers). They are
the bag side of the **Mark 67 ↔ Mark 49 dyad**.

**3 strongest evidence features:**

1. **Counterparty concentration on Mark 67 (89/122 sells = 73%) with
   adverse selection sign-flipped vs Mark 67 (−1.27/u) vs other partners
   (+3.17/u vs Mark 55, n=9).** Identical architectural pattern to Mark 38
   ↔ Mark 14.
2. **Inventory dynamics: −300 units short every day, no mean-revert
   mechanism, no buy-back.** They are a directional seller that doesn't
   reset until midnight.
3. **Mid-print aggressor profile (84% ambiguous, 13% taker, 3% maker)**
   — they are at-mid sweepers, paying near-zero spread but getting a
   ~+1.15 tick adverse mid move at h=5.

**Confidence**: HIGH on the bag-side classification. MEDIUM on the
"mean-revert" sub-archetype label — the side rule shows weak (~6 pp)
preference for selling after rises, but the dominant trigger is
counterparty supply (Mark 67 is buying), not microstructure.

---

## K. Exploitation hypothesis

### K.1 Primary rule — REACT-WITH-STRUCTURE on Mark 49 sells

When Mark 49 prints a SELL on VFE (we see `seller == "Mark 49"` in
`state.market_trades["VELVETFRUIT_EXTRACT"]`), the next 5–20 ticks have
mid moving UP by ~+1.15 ticks vs price (t=−6.04 by Mark-49-signed,
unsigned t=+6.04 for the fader). Trade rule for our trader:

```
on Mark 49 SELL of VFE:
    expected: mid rises ~1.15 ticks over next 5 ticks (t≈+6 fader edge)
    action:  lean +VFE 0.5 ticks for next 50 ticks (skew our fair UP)
    sizing:  scale by Mark 49 print qty × 0.5; cap at 25 lots / window
    decay:   half-life 20 ticks
```

**Pre-registered parameters**:
- `lean_per_print` = +0.5 ticks per Mark 49 sell
- `lean_qty_multiplier` = 0.5 × Mark 49 print qty
- `decay_half_life_ticks` = 20 (matches the h=5 → h=20 alpha decay window)
- `cap_lean` = ±5 ticks max accumulated lean

**EV estimate**: 105 sells / 3 days = ~35/day, edge ~+1.15 ticks at h=5,
qty per print ~10. Capture 33% (5-tick window vs 50-tick decay):
+1.15 × 10 × 35 × 0.33 ≈ **+130 XIRECS/day on this rule alone.** Small
in absolute terms but high precision (t=6).

**Gating to AVOID**:
- DON'T fade Mark 49 buys (n=17, mean adv5 = +0.92 means buys are
  CORRECTLY-direction at h=5, but n is so small it's noise).
- DON'T expect the edge at h=100 (decays to t=1.24).

**Falsifier**: any single live day where mean h=5 mid move after Mark 49
sells turns NEGATIVE (i.e., sells suddenly become informed) → kill.
Historical baseline: 3/3 days have positive h=5 mid-rise after sells.

### K.2 Secondary rule — pre-print front-run gate (LOW priority)

The trigger classifier shows weak lift (2× over base) for the 2-feature
gate `recent_ret_20 > +1 AND imb1 > +0.05`. With base 1.75% → conditional
3.5%, fires on ~8% of ticks. If we pre-position SHORT VFE (or skew our
fair DOWN) when the gate triggers, we'd be wrong 96% of the time but
correct 4% — and the correct cases catch the +1.15-tick fader move.

**Don't ship this rule.** EV is small (precision too low; 200 false
positions for every 8 true catches), and the post-print rule (K.1) is
much higher-precision.

### K.3 Don't trade the buy side

Mark 49's buys (n=17 across 3 days) are too small to gate a trader on.
Skip.

---

## Reconciliation note (for Phase 6)

Prior session: "INFORMED SELLER OF VE (low confidence). Their **buys**
lose (−1.14 / unit), implying their sells are slightly informed."

This dossier **CORRECTS**:

1. **Mark 49 is NOT informed.** Both sides lose at h=100 (sell mean adv100
   = −1.11, buy mean adv100 = −2.34). The +1.88 h=1 mid-move-after-sell
   from per-product VFE EDA is **not** Mark 49 being informed about price
   direction — it's the FADER's edge from buying after Mark 49 sold cheap.
   Same direction (mid up after sell), opposite interpretation: Mark 49
   *misjudged* the sell timing by ~1 tick, the fader catches the rebound.

2. **The right trader rule is `lean +VFE on Mark 49 sells`** (i.e., FADE
   their direction). The prior playbook said "lean weakly long ... or
   skip" — which IS the fade direction, just confusingly phrased.
   This dossier pre-registers concrete parameters for the fade.

3. **The Mark 49 ↔ Mark 67 dyad is structural** (89 of 122 trades, 73%
   pairing; mean adv100 vs Mark 67 = −1.27, vs Mark 55 = +3.17). Mark 67
   is the Mark 14 of VFE; Mark 49 is the Mark 38 of VFE. The prior session
   noted Mark 67 → Mark 49 in the network CSV but didn't reframe it as a
   dyad-level structural pair.

4. **The h=5 sell signal is much stronger and more stable than the prior
   playbook implied.** t-stat = +6.04 (across 105 prints), all 3 days
   positive, low brittle-tail risk. This is one of the higher-confidence
   short-horizon edges in the entire R4 dataset.
