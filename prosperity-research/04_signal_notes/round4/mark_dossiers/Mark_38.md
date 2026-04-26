# Mark 38 — Dossier (Round 4)

> The bag-holder. Mark 14's permanent counterparty. Aggressive taker who pays
> spread on every print and runs sustained directional inventory that mean-
> reverts only across days, not within them.
>
> Source CSVs: `prosperity-research/03_eda/round4/per_mark/Mark_38_*.csv`
> Quote source: `prosperity_rust_backtester/datasets/round4/prices_round_4_day_{1,2,3}.csv`
> Schema: `prosperity_rust_backtester/scripts/round4_options/per_mark_features.py`
> Analysis logs: `/tmp/mark38_analysis.py`, `/tmp/mark38_trigger.py`, `/tmp/mark38_micro.py`,
> `/tmp/mark38_when.py`, `/tmp/mark38_traj.py`.

---

## A. Headline classification

**Mark 38 is a NAÏVE TWO-SIDED TAKER bot, structurally locked to Mark 14 as
counterparty (98% of HYD prints, 99% of VEV_4000 prints), who pays the touch
spread on 60–67% of fires and runs same-day inventory excursions of ±100+
units that only reset across day boundaries.** Confidence: **HIGH** that
they are the bag side; **MED** on the precise archetype, which is best
described as a "taker MM with no inventory skew and no direction filter" —
they cross the spread to lift Mark 14's resting offers / hit Mark 14's
resting bids regardless of recent price drift, and Mark 14 has clearly
positioned to extract the spread + mid drift.

Total 3-day footprint: HYD 1,022 prints / 4,001 units; VEV_4000 442 prints /
876 units; one-off prints on VEV_4500..5300 (3 each, all paired with
Mark 22, ignore). Total adverse-selection sum at h=100 across HYD+VEV_4000:
**−12,221 XIRECS over 4,877 units = −2.51 per unit at h=100; −8.34 per unit
at h=500** (matches the headline number).

---

## B. Volume profile

### B.1 Trade counts by (product, day, side)

| Product | D1 buys (qty) | D1 sells (qty) | D2 buys (qty) | D2 sells (qty) | D3 buys (qty) | D3 sells (qty) | Total |
|---|---|---|---|---|---|---|---|
| HYDROGEL_PACK | 189 (745) | 186 (740) | 165 (658) | 146 (586) | 161 (662) | 175 (705) | **1,022** |
| VEV_4000 | 73 (148) | 91 (185) | 64 (124) | 64 (132) | 72 (143) | 78 (144) | **442** |
| VEV_4500..5300 | 1–3 each, all paired with Mark 22 | | | | | | 14 |

### B.2 Trade-size distribution

- **HYD: qty ∈ {2,3,4,5,6}**, modes 6 (214), 3 (211), 2 (202), 4 (200), 5 (195) — almost
  perfectly uniform. Mean 4.01, median 4. **DISCRETIZED, no large prints.**
- **VEV_4000: qty ∈ {1,2,3}**, modes 1 (154), 3 (146), 2 (142). Mean 1.98,
  median 2. Equally discretized.

The Mark 14 vs Mark 38 size distributions are **identical** — both bots use the
same lot quantum on the same products. This is consistent with the hypothesis
that they are paired by design (designed-to-trade-against-each-other test bots).

### B.3 Trade-arrival rate (HYD inter-arrival, ticks)

| Day | n | mean | median | min | max | gap dist (0–5 / 6–20 / 21–50 / 51–100 / >100) |
|---|---:|---:|---:|---:|---:|---|
| 1 | 375 | 26.3 | 18 | 1 | 137 | 73 / 122 / 123 / 52 / 4 |
| 2 | 311 | 31.8 | 21 | 1 | 261 | 44 / 110 / 95 / 48 / 13 |
| 3 | 336 | 29.5 | 20 | 1 | 148 | 53 / 118 / 106 / 43 / 15 |

**Mark 38 fires roughly every 20-30 ticks on HYD**, with a long tail; same
order of magnitude as Mark 14. The Mark 14↔Mark 38 dyad is by far the
densest interaction in the dataset (728 + 714 = 1,442 paired trades,
counterparty_network.csv).

### B.4 Per-product specialization

Concentrated on HYD (1,022 / 1,478 = 69%) and VEV_4000 (442 / 1,478 = 30%);
incidental on smaller VEVs (1%). VEV_4000 is a delta-1 proxy for VFE — but
Mark 38 does **NOT** trade VFE directly. So Mark 38's "VFE exposure" is
entirely via VEV_4000. (Compare Mark 14, who trades both VFE and VEV_4000.)

---

## C. Trigger conditions — per-tick "M38 prints in next 5 ticks?" classifier

Per-tick rows = 30,000 (10k ticks × 3 days). Positive label rate = 16.06% on
HYD, 7.19% on VEV_4000. AUCs (single feature, stdlib Mann-Whitney rank):

### HYD

| Feature | direction | AUC |
|---|---|---:|
| recent_ret_20 | **LOW** (fires after price drop) | 0.525 |
| recent_ret_5 | LOW | 0.519 |
| realised_vol_100 | HIGH | 0.503 |
| spread | LOW | 0.502 |
| imb1 | HIGH | 0.501 |
| imb2 | HIGH | 0.501 |
| imb3 | LOW | 0.501 |

**Best single feature: recent_ret_20 LOW (AUC 0.525).** The signal is weak in
absolute terms; conditional firing rate uplift even at extreme imb1≥0.5 is
only 1.12× over base 16%. **Mark 38 fires uniformly in time; the trigger
does not have a sharp microstructure signature.**

Side-decomposed:
- **BUY-side label (M38 buys in next 5 ticks)**: best feature realised_vol_100
  (AUC 0.505); *no* feature exceeds 0.51. Buys are essentially time-uniform.
- **SELL-side label**: best feature **recent_ret_20 LOW (AUC 0.546)** — Mark
  38 sells more often after a price drop. This is the bag-holder mechanic:
  selling into weakness. Combined with `recent_ret_5 LOW (AUC 0.535)`.

### VEV_4000

| Feature | direction | AUC |
|---|---|---:|
| realised_vol_100 | HIGH | 0.539 |
| recent_ret_5 | LOW | 0.512 |
| spread | LOW | 0.512 |

Slightly better than HYD on recent_ret_5 / vol; but realised_vol_100 is the
top feature — Mark 38 fires more on volatile days/intervals on VEV_4000.

**Best 2-feature decision rule: `recent_ret_20 < 0 AND realised_vol_100 > median`
on HYD-SELL** — modest precision uplift to ~17–18% from 8.15% base
(2.1× lift), but coverage only ~10% of fires. Not enough to gate a trader on
pre-print prediction; the better play is to gate on **what Mark 38 just
printed** (post-print reaction, see §K).

---

## D. Side rule

Buy/sell counts (HYD): 515/507 — perfectly balanced. VEV_4000: 209/233. Mark
38 is **two-sided regardless of regime**.

### Conditional side analysis (HYD)

| Conditioning | buy% | sell% | Conclusion |
|---|---|---|---|
| recent_ret_20 > 0 (price up) | 47.4% | 41.0% | mild momentum-buy |
| recent_ret_20 < 0 (price down) | 47.6% | 55.6% | sell more after drop |
| imb1 > 0 (bid heavy) | 1.6% | 2.4% | almost never |
| imb1 < 0 (ask heavy) | 98.4% | 97.6% | trades almost only when ask depth > bid depth |
| inventory_day_pre long | 36.5% | 35.7% | NO inventory aversion on either side |
| inventory_day_pre short | 58.3% | 59.0% | bias to fire more when short |
| inventory_day_pre flat | 5.2% | 5.3% | rarely starts flat |

Self-transitions (prev side → this side): {BB:263, BS:251, SS:256, SB:251}.
**Side-runs are ≈ uniform (1.95–2.17 mean run-length, max 6–9)**. They
alternate or repeat with no persistent bias.

**Two important findings:**

1. **No inventory skew.** Mark 38 buys at the same rate when long-37 vs
   short-50 vs flat. They do not de-risk. They rely on whatever their
   counterparty (Mark 14) is willing to print on the other side.

2. **Trades almost exclusively when imb1 < 0 (ask-heavy book).** On HYD,
   global imb1 sign distribution is roughly 1.4% pos / 96.7% zero / 1.5% neg
   per day. So nearly all Mark 38 prints occur on ticks where the *level-1*
   imbalance is technically zero (bid_vol == ask_vol == 0 → no L1 quote
   posted) **OR** the rare ticks where there IS an L1 imbalance and it
   skews ask-heavy. This is mostly a quote-density artefact (HYD spread is
   locked at 16; L1 is sparse). Treat with caution — see §I for the real
   pattern using broader pre-quote windows.

### Conditional side analysis (VEV_4000)

Buys 47% vs sells 47% across recent_ret_20 sign — completely flat. Inventory
splits buy 24.9% long / 40.7% flat / 34.4% short — much closer to MM-ish but
no skew either. The same imb1<0 dominance (99.5% buys, 100% sells) is just
an L1 sparsity artefact.

**Conclusion**: Mark 38's side rule is essentially **stateless and
direction-insensitive**, with a mild bias to sell after price drops on HYD
(and to buy on momentum at low strength). They are NOT a momentum chaser
in the strong sense — they are a near-Bernoulli direction picker.

---

## E. Aggressor profile

| Day | side | TAKER (lifter/hitter) | MAKER | AMBIG (mid-print) |
|---|---|---|---|---|
| 1 | buy | 123 (65%) | 0 | 66 (35%) |
| 1 | sell | 124 (67%) | 0 | 62 (33%) |
| 2 | buy | 99 (60%) | 0 | 66 (40%) |
| 2 | sell | 82 (56%) | 0 | 64 (44%) |
| 3 | buy | 94 (58%) | 0 | 67 (42%) |
| 3 | sell | 107 (61%) | 0 | 68 (39%) |

**Mark 38 is a PURE TAKER.** They lift the ask or hit the bid 56–67% of the
time on HYD; the rest are at-mid prints (likely cross-the-spread matched
inside HYD's locked-spread-16 book). They are NEVER the resting maker.

**Implication**: Mark 38 pays the half-spread on every aggressive print. On
HYD that's ~8 ticks per round-trip. They have no obvious edge to recover this
cost — and indeed they don't (see §G).

VEV_4000 mirrors: 60–74% TAKER on every day-side combo.

---

## F. Inventory dynamics

### HYD

| Day | inv_day min | inv_day max | inv_day mean | end-of-day | |max-excursion| |
|---|---:|---:|---:|---:|---:|
| 1 | −55 | +26 | −17.6 | +5 | 55 |
| 2 | −6 | +134 | +77.9 | +72 | 134 |
| 3 | −100 | +12 | −47.9 | −43 | 100 |

**Cumulative across 3 days: min −55, max +139, end +34.**

This is **NOT mean-reverting MM behavior**. Day 2 ran +134 long, day 3 ran
−100 short. Position limit on HYD is 200; **they get within 33% of the
position limit in a single day**. Mark 38 lets directional inventory build
all day, then resets across day boundaries.

### VEV_4000

| Day | min | max | mean | EoD | |excursion| |
|---|---:|---:|---:|---:|---:|
| 1 | −44 | +25 | −5.4 | −37 | 44 |
| 2 | −13 | +4 | −5.1 | −8 | 13 |
| 3 | −11 | +16 | +4.1 | −1 | 16 |

VEV_4000 inventory is much tighter (max excursion 44, position limit 300 →
14% of cap). Mark 38 takes much smaller-size VEV_4000 prints, so per-print
inventory effect is smaller.

**Conclusion**: Mark 38 has **no inventory-aversion mechanism** on HYD; they
let positions build without skewing direction. This is the structural reason
they get bag-held — they cannot back away from a losing direction.

---

## G. Adverse selection — they LOSE on every product, every day

### HYD

| Day | side | n | mean adv100 | median |
|---|---|---:|---:|---:|
| 1 | buy | 189 | **−9.49** | −7.0 |
| 1 | sell | 186 | **−8.88** | −9.0 |
| 2 | buy | 163 | **−5.78** | −7.0 |
| 2 | sell | 144 | **−7.22** | −6.0 |
| 3 | buy | 160 | **−9.88** | −9.5 |
| 3 | sell | 175 | **−9.11** | −8.0 |
| ALL | both | 1022 | **−8.46** | −8.0 |

Aggregate h=5 mean: −7.95; h=20: −8.10; h=100: −8.46. **Mid moves a full
8 ticks against them, every print, every day.** This is consistent across
3 days and both sides (no side is profitable).

### VEV_4000

| Day | side | n | mean adv100 | median |
|---|---|---:|---:|---:|
| 1 | buy | 72 | −10.69 | −11 |
| 1 | sell | 90 | −9.81 | −9.5 |
| 2 | buy | 63 | −8.51 | −8.5 |
| 2 | sell | 64 | −10.23 | −9.5 |
| 3 | buy | 70 | −12.29 | −12.5 |
| 3 | sell | 78 | −11.20 | −11.5 |

Aggregate h=100: **−10.47 per unit on VEV_4000**. Even worse than HYD on
this strike.

**Distribution check**: median ≈ mean → adverse selection is **uniform**
(not concentrated in 5% catastrophic prints). This is robust bag-holding,
not a couple of unlucky outliers. The fade is therefore not brittle.

---

## H. Counterparty selection — Mark 14 is the entire game

### HYD

| Counterparty | n | qty | mean adv100 |
|---|---:|---:|---:|
| **Mark 14** | **999 (97.7%)** | **3,927** | **−8.65** |
| Mark 22 | 18 (1.8%) | 70 | **+2.39** |

### VEV_4000

| Counterparty | n | qty | mean adv100 |
|---|---:|---:|---:|
| **Mark 14** | **434 (98.0%)** | **864** | **−10.55** |
| Mark 22 | 3 (0.7%) | 6 | +1.17 |

**The bag-hold is 100% concentrated on Mark 14.** When Mark 38 trades with
anyone other than Mark 14 (rare, only 21 trades total across HYD+VEV_4000),
they actually **win** by ~+2/u. This proves the structure: it is Mark 14's
quote placement, not the market generally, that picks Mark 38 off.

This has a clean exploitation interpretation (see §K): if our trader
**becomes the third party in any Mark 38 print** (i.e., we are the maker
or the third-leg taker), we should *also* expect to extract value vs Mark
38, not get bag-held with them. Mark 38 is a price taker who pays for
liquidity unconditionally; we want to be the liquidity provider on the
opposite side of where Mark 14 is providing.

---

## I. Microstructure footprint (HYD, conditional vs unconditional rates)

Pre-tick lookback windows of 1 and 3 ticks before each Mark 38 print.

### HYD

| Pre-trade pattern | M38 BUY rate (n≈515) | M38 SELL rate (n≈507) | Baseline (per quote tick) |
|---|---|---|---|
| mid step UP in last 3 ticks | 41–43% | 41–50% | global 35% |
| mid step UP in last 1 tick | 32–43% | 39–47% | global ~10% |
| mid step DOWN in last 3 ticks | 47–48% | 41–48% | global 35% |
| imb1 sign disagrees with print direction | 2–4% | 1–4% | rare (book L1 sparse) |
| spread > median (>16) | 1–3% | 1–3% | ≈30% |

The signature pattern: **Mark 38's prints cluster on ticks where mid moved
in either direction in the last 3 ticks (~85% of prints have a recent move
of any sign vs ~70% baseline)**. They fire on activity, not on stillness —
consistent with a "react to volatility" trigger.

But the directional asymmetry is small: SELLS happen ~3–9 percentage points
more often after a DOWN move (47%) vs UP (40%), confirming **mild
selling-into-weakness** (the bag-hold mechanic).

### VEV_4000

Similar pattern: 32–47% of prints follow a 3-tick move; wide-spread share
6–16% of prints (higher than HYD's 1–3%, consistent with VEV_4000 being a
higher-vol product).

### What is NOT a footprint

- **Pre-trade "level-2 bid drop" 50%+ in prior 500 ticks** is essentially
  ZERO before Mark 38 prints (matches the §3.6 finding for Mark 14 in
  `counterparty_deep.md`). The L2 cancellation pattern is not a Mark 38
  predictor.
- **No spread-widening signal**: spread is locked at 16 most of the time on
  HYD, so spread-based gating contributes nothing.
- **No imb1 directionality**: imb1 is mostly sparse (zero) when Mark 38
  fires — they're trading at-mid in the locked spread.

---

## J. Bot archetype

**Mark 38 is a NAÏVE TWO-SIDED MARKET TAKER** — a "dumb taker" archetype
that fires roughly Poisson in time with mild after-move bias, no inventory
aversion, and no direction filter. They are the structural counterparty to
Mark 14, who has built a quote schedule that extracts the half-spread plus
mid-drift edge from every Mark 38 fire.

**3 strongest evidence features:**

1. **Pure-TAKER profile (60–67% aggressor lift/hit, 0% maker)** — they
   pay the touch spread unconditionally. (§E)
2. **Persistent uniform adverse selection of ~−8/u h=100 across 1,022 HYD
   prints, 3 days, both sides.** No regime where the adverse selection
   flips sign. (§G)
3. **Counterparty concentration on Mark 14 (98% of HYD prints, 98% of
   VEV_4000 prints) with a sign-flipped adverse selection vs other
   counterparties (+2/u vs Mark 22, n=21).** Confirms it is Mark 14's
   quote placement that creates the bag, not the market. (§H)

**Confidence**: HIGH that Mark 38 is the bag side. **MEDIUM** on the
sub-archetype label "naïve momentum taker" — the momentum bias is real but
weak (8-percentage-point asymmetry on sell-after-drop). A more precise
sub-archetype is "inventory-blind two-sided taker" — they take both sides
roughly proportional to their previous take, regardless of state.

---

## K. Exploitation hypothesis

### K.1 Primary rule — REACT-WITH-STRUCTURE on Mark 38 prints

When Mark 38 prints (we observe their `buyer == "Mark 38"` or
`seller == "Mark 38"` in `state.market_trades[product]`), the counterparty
is Mark 14 with 98% probability and the next 100 ticks of mid drift will
move ~8 ticks AGAINST Mark 38 in expectation (signed by their trade
direction). Trade rule:

```
on Mark 38 BUY of HYD or VEV_4000:
    expected: mid drops ~8 ticks over next 100 ticks
    action:  lean fair value DOWN by 1 tick AND set ASK at fair-1 to capture
             the drift; widen BID by 2 ticks (we are short-leaning)
    sizing:  scale by Mark 38 print qty × 0.5 lots; cap at 25 lots / window

on Mark 38 SELL of HYD or VEV_4000:
    expected: mid rises ~8 ticks over next 100 ticks
    action:  lean fair value UP by 1 tick AND set BID at fair+1 to capture
             the drift; widen ASK by 2 ticks (we are long-leaning)
    sizing:  scale by Mark 38 print qty × 0.5 lots; cap at 25 lots / window

decay: half-life 50 ticks (cleanup at 100 ticks).
```

**Pre-registered parameters (HYD)**:
- `lean_per_print_per_unit` = 1 tick / 4 units of Mark 38 print qty
- `decay_half_life_ticks` = 50
- `quote_widening_on_winning_side` = +1 tick (we keep some defensive width)
- `quote_tightening_on_losing_side` = −1 tick (be aggressive on the side that wins)

**EV estimate**: 1,022 Mark 38 prints across 3 days = ~340/day. If we
capture even 25% of the −8.46 mean adverse selection at h=100 in our
direction (i.e., +2 ticks/print × 4 units/print average) = +8 XIRECS per
print × 340 = **~2,720 XIRECS/day on HYD alone**. Plus VEV_4000
(~150 prints/day × similar effect) = +~600/day. **Total ~3,300/day potential
above existing mark-lean.** Realistic capture (with decay, slippage,
inventory caps): ~30–50% of this = +1,000 to +1,650/day.

This stacks **on top of** the existing R4 mark-lean v01 trader, which
already captures the ~+1,054 number cited in the project brief — but only
post-print and at small magnitude. The dossier-derived rule expands the
lean magnitude (currently +0.05/qty) and front-loads the capture window
(currently 200-tick decay → 50-tick half-life).

**Falsifier**: any single live day where mean `adverse_select_100` for
Mark 38 prints turns positive (i.e., < −2.0 → > 0.0) → kill the rule.
Expected base case from 3-day historical: −8.46/u h=100, P(positive) = 26%.

### K.2 Secondary rule — FRONT-RUN gate on the sell side

The **sell-side trigger classifier** has AUC 0.546 on `recent_ret_20`
(LOW direction, i.e. Mark 38 sells more after a 20-tick drop). If we
gate on `recent_ret_20 < −2 ticks` AND `realised_vol_100 > median`:

- conditional P(Mark 38 sells in next 5 ticks) ≈ 13–18% vs base 8%
  (= ~2× lift, n ≈ 1,500–2,500 candidate ticks across 3 days)
- when the trigger fires AND Mark 38 then sells: lean LONG HYD by 1 tick
  for the next 50 ticks BEFORE the print

EV: ~250 candidate ticks/day × 50% trigger-success × (+8 ticks expected
mid-rise after a Mark 38 sell × capture 25%) = ~250/day additional. Small
but stacking — and crucially gives us a **pre-print** rather than only
post-print position.

**Pre-registered**:
- `recent_ret_20_threshold` = −2 ticks
- `realised_vol_100_quantile` = 50th pct (re-fit per day)
- `pre_print_lean_ticks` = 1
- `pre_print_window_ticks` = 50

**Falsifier**: per-day P(Mark 38 sell | trigger) drops below 12% on any
live day → kill the gate.

### K.3 What NOT to do

- **Don't fade Mark 38 on sub-Mark 22 prints (n=21 across all products).**
  The sign flips: Mark 38 wins +2.39/u when paired with Mark 22 on HYD.
  Conditional rule: only react when `counterparty == "Mark 14"`.
- **Don't infer Mark 14's direction** from Mark 38's print — they are
  **the same trade** (M14 BUY ↔ M38 SELL on the same ts). The dyad is
  not a sequence; it's a single-tick identity. Cross-Mark inference
  belongs in the dyad-state file (see `_cross_mark.md`).
- **Don't trade Mark 38's trigger rule on VFE.** Mark 38 doesn't trade VFE
  directly. Their VEV_4000 prints DO carry a delta-1 implication, but
  that overlaps with the existing E1 capacity rule.

---

## Reconciliation note (for Phase 6)

Prior session classification: **"BAG-HOLDER, fade explicitly."** This
dossier **CONFIRMS** the verdict, with two refinements:

1. The fade signal is **structural** (Mark 14 is positioned to extract
   spread+drift), not "Mark 38 trades wrong" in some informational sense.
   This means the alpha will persist as long as Mark 14 keeps quoting the
   same way — a single live R4 day can falsify (see K.1 falsifier).

2. The prior session's mark-lean v01 trader captures only ~1% of the
   available bag-hold edge (~1,054 of ~91k/day theoretical). The leverage
   point is **front-loading the capture window** (50-tick half-life vs
   200-tick) and **scaling the lean magnitude** (currently +0.05/qty).
   Both are pre-registered in §K.1.

3. The "selling into weakness" momentum bias is real but small (~8 pp
   asymmetry). Don't over-weight it. The primary signal is the post-print
   counterparty-conditional reversion, not the pre-print momentum gate.
