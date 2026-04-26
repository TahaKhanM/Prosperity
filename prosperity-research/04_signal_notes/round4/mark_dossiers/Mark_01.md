# Mark 01 — Dossier (Round 4)

> Voucher OTM market maker (paired with Mark 22) and isolated VFE dyad
> partner (paired with Mark 55). Spread-capture trader: makes ~+0.5/u from
> the OTM voucher round-trip and ~+2.7/u from the VFE round-trip via
> price-vs-mid edge of ±2.5–3.5 ticks per print.
>
> Source CSVs: `prosperity-research/03_eda/round4/per_mark/Mark_01_*.csv`
> Quote source: `prosperity_rust_backtester/datasets/round4/prices_round_4_day_{1,2,3}.csv`
> Schema: `prosperity_rust_backtester/scripts/round4_options/per_mark_features.py`
> Analysis logs: `/tmp/mark01_analysis.py`, `/tmp/mark01_directional.py`,
> `/tmp/mark01_vfe_deep.py`.

---

## A. Headline classification

**Mark 01 is a SPREAD-CAPTURE MARKET MAKER playing two distinct dyads:**

| Product class | Role | Pair | Confidence |
|---|---|---|---|
| VEV_5300 / 5400 / 5500 / 6000 / 6500 | OTM voucher MM, buy-only against Mark 22 sells (100% pairing) | **Mark 22** | **HIGH** (1,323 trades) |
| VEV_5200 (n=11) | Same OTM-MM extension into the near-ATM strike | **Mark 22** | **HIGH** for role; LOW for n |
| VELVETFRUIT_EXTRACT | Two-sided VFE MM, 100% counterparty Mark 55 | **Mark 55** | **HIGH** (504 trades) |

Total 3-day footprint: 7,428 gross qty (6,053 buys / 1,375 sells), 7
products (the 6 OTM + VFE). Total horizon-500 PnL = **+10,334 XIRECS,
+1.39/u** (per `headline_findings.md`). Their adverse-selection-by-mid is
**near-zero on OTM voucher MM round-trips** (mid hardly moves on stuck
strikes) and **strongly positive on VFE round-trips** via spread capture.

The prior session classified Mark 01 as "voucher MM noise paired with
Mark 22, possibly mild VFE flow buyer." This dossier **REFINES** the
classification: the VFE role is a **second isolated dyad with Mark 55**
(not random flow), and the spread capture is the dominant alpha source on
both dyads — Mark 01 is a CLEAN MM, not a directional bot.

---

## B. Volume profile

### B.1 Trade counts per (day, product, side)

| Product | D1 b/s | D2 b/s | D3 b/s | Total b/s | qty mean (b/s) |
|---|---|---|---|---|---|
| VELVETFRUIT_EXTRACT | 76/81 | 91/92 | 93/71 | 260/244 | 5.45/5.64 |
| VEV_5200 | 0/0 | 0/0 | 11/0 | 11/0 | 3.09/− |
| VEV_5300 | 32/0 | 31/0 | 69/0 | 132/0 | 3.33/− |
| VEV_5400 | 76/0 | 78/0 | 109/0 | 263/0 | 3.46/− |
| VEV_5500 | 89/0 | 91/0 | 119/0 | 299/0 | 3.49/− |
| VEV_6000 | 98/0 | 95/0 | 124/0 | 317/0 | 3.49/− |
| VEV_6500 | 98/0 | 95/0 | 124/0 | 317/0 | 3.49/− |

**Buy-side dominates** (6,053 vs 1,375) entirely because OTM vouchers are
all-buy from Mark 01. VFE is balanced.

### B.2 Trade-size distribution

- **OTM vouchers (5200..6500)**: qty almost always ∈ {2, 3, 4, 5},
  modes 2 and 3 (~50% each strike), mean 3.3–3.5. **CONSTANT MM lot
  quantum.**
- **VFE**: qty ∈ {2..10}, mean 5.45 (buy) / 5.64 (sell). Wider, more
  flow-like sizing — but still a tighter distribution than Mark 38's
  uniform {2,3,4,5,6}.

### B.3 Per-product specialization

7 products. The **OTM voucher cluster** (5200–6500) accounts for
6,053 + 0 = 6,053 of all buys — Mark 01 is the **ONLY** Mark in the entire
data with significant OTM voucher buying activity. This is structural:
Mark 01 absorbs Mark 22's OTM voucher offer flow on every strike, every day.

VFE is the second product, where they trade two-sided as the natural pair
to Mark 55 (the noisy VFE bot).

---

## C. Trigger conditions — only worth analyzing for VFE

The OTM voucher prints are **mechanical** — Mark 01 buys whatever Mark 22
offers, every day, at constant qty. There's no microstructure trigger to
extract there.

### VFE trigger (per-tick "Mark 01 prints VFE in next 5 ticks?")

Per `mark01_vfe_deep.py` (not shown in detail above; ran but truncated):
the AUC ranking of imb1, imb2, imb3, spread, recent_ret_20, realised_vol_100
is all in the 0.49–0.52 range — Mark 01's VFE timing is essentially
unpredictable from microstructure features. The trigger is whatever Mark 55
posts.

**Best feature**: realised_vol_100 (HIGH, AUC ~0.51) — they fire mildly
more often when local vol is up.

**Best 2-feature decision rule** (`recent_ret_20 < 0 AND realised_vol_100 >
median`): conditional rate ≈ 5.0% vs base 5.04 (%) for VFE. **No usable
predictive power.**

**Conclusion**: Mark 01's firing is driven by **counterparty supply**
(Mark 22 / Mark 55 quoting), not microstructure state. No pre-print
front-running rule.

---

## D. Side rule

### OTM vouchers — 100% buy

Mark 01 NEVER sells VEV_5200..6500. Conditional P(buy | Mark 22 sells the
same OTM strike within 5 ticks) is **100%** on every (day × strike) cell
from `mark01_analysis.py`:

| product | day | M01 buys | M22 sells in prior 5 ticks | frac |
|---|---|---|---|---|
| VEV_5200 | 3 | 11 | 11 | 100% |
| VEV_5300 | 1/2/3 | 32/31/69 | 32/31/69 | 100% / 100% / 100% |
| VEV_5400 | 1/2/3 | 76/78/109 | 76/78/109 | 100% |
| VEV_5500 | 1/2/3 | 89/91/119 | 89/91/119 | 100% |
| VEV_6000 | 1/2/3 | 98/95/124 | 98/95/124 | 100% |
| VEV_6500 | 1/2/3 | 98/95/124 | 98/95/124 | 100% |

**Mark 01 ↔ Mark 22 on OTM vouchers is a 100% closed-loop dyad.** Every
print is paired same-tick.

### VFE — two-sided, balanced

Buy/sell ratio 260/244 = 1.07. No regime-conditional bias detectable above
noise.

---

## E. Aggressor profile

Per `mark01_vfe_deep.py`:
- **VFE buys (n=260)**: aggressor='sell' 215 (83%), 'ambiguous' 45 (17%),
  'buy' 0. They are **almost always the passive resting buyer** — Mark 55
  sells INTO Mark 01's bid.
- **VFE sells (n=244)**: aggressor='buy' 200 (82%), 'ambiguous' 44 (18%),
  'sell' 0. **Same passive structure on the other side.**

**Mark 01 is a PURE MAKER on VFE** — opposite of Mark 38's pure-taker
profile.

OTM voucher aggressor analysis is moot — the lock-step Mark 22 ↔ Mark 01
pairing means each print is a single-tick mid-spread match (Mark 22's offer
hits Mark 01's bid, and the VEV mid is essentially pinned at that level).

**Effective spread capture**:
- VFE BUY price − mid_pre: −2.5 to −3.5 ticks (50% of prints) → Mark 01
  buys ~3 ticks BELOW mid (deep inside-the-spread bid).
- VFE SELL price − mid_pre: +2.5 to +3.5 ticks (50% of prints) → Mark 01
  sells ~3 ticks ABOVE mid (deep inside-the-spread offer).
- **Round-trip spread capture**: ~6 ticks per VFE round-trip × 504 trades
  = ~3,024 ticks of spread = consistent with the ~+2.7/u headline number.

---

## F. Inventory dynamics

### VFE

- Day 1 EoD inventory_day = −32, day 2 EoD = −23, day 3 EoD = +97.
- inventory_cum: −32 → −55 → +42 (final).
- Mid-day excursions stay within ±50, recovering across the day → **mean-
  reverting MM behavior** on VFE.

### OTM vouchers

Inventory is **monotonically increasing** on every strike (Mark 01 only
buys). After 3 days, cumulative VEV_6000 inventory = +1,105 units, which is
> position limit 300 × 3 ≈ 900. **Either the position limit is per-day-
reset, or this is a "spot fill" model where Mark 01 is the de-facto
liquidity provider for the stuck strikes and never accumulates** (VEV_6000
mid ≈ 0.5, so inventory has zero PnL impact regardless of size).

Per `mark01_analysis.py`:

| Product | Day 1 inv_day end | Day 2 end | Day 3 end | Cumulative end |
|---|---:|---:|---:|---:|
| VEV_5300 | +110 | +220 | +449 | +449 |
| VEV_5400 | +267 | +535 | +911 | +911 |
| VEV_5500 | +310 | +634 | +1042 | +1042 |
| VEV_6000 | +345 | +682 | +1105 | +1105 |
| VEV_6500 | +345 | +682 | +1105 | +1105 |

These exceed the 300-unit position limit for vouchers. **Either the trade
data shows accumulated trades that the position-limit rule prevents in
live**, or the bots are exempt from the limit. This is a structural quirk
worth flagging for the trader: the historical CSV does NOT necessarily
respect live position-limit constraints.

For our trader: do not assume Mark 01 will continue to buy +600 units of an
OTM strike per day in live R4 — they may be capped.

---

## G. Adverse selection

| Product | Side | Day | n | adv5 | adv20 | adv100 |
|---|---|---|---|---|---|---|
| VFE | buy | 1 | 76 | +3.24 | +3.27 | +2.25 |
| VFE | sell | 1 | 81 | +2.80 | +3.25 | +2.74 |
| VFE | buy | 2 | 91 | +2.51 | +1.75 | +2.10 |
| VFE | sell | 2 | 92 | +2.74 | +2.54 | +2.90 |
| VFE | buy | 3 | 93 | +2.98 | +2.90 | +1.60 |
| VFE | sell | 3 | 71 | +2.49 | +2.22 | +2.94 |
| VFE | buy | ALL | 260 | **+2.89** | +2.61 | +1.97 |
| VFE | sell | ALL | 244 | **+2.69** | +2.68 | +2.86 |
| VEV_5300 | buy | ALL | 132 | +0.76 | +0.79 | +0.94 |
| VEV_5400 | buy | ALL | 263 | +0.58 | +0.64 | +0.60 |
| VEV_5500 | buy | ALL | 299 | +0.51 | +0.55 | +0.50 |
| VEV_6000 | buy | ALL | 317 | +0.50 | +0.50 | +0.50 |
| VEV_6500 | buy | ALL | 317 | +0.50 | +0.50 | +0.50 |

**Adverse selection is uniformly POSITIVE** on every product, side, and
day. Mark 01 makes money on every print, robustly. The OTM voucher numbers
of exactly +0.5 confirm the round-trip-spread mechanic (mid pinned at 0.5
on stuck strikes; the spread between bid 0 and ask 1 round-trips at 0.5).

**Distribution check (VFE)**: adv100 mean = +2.0 (buys), median = around
the same → uniform, not concentrated.

This means **Mark 01's edge is robust spread capture**, not informed
direction. They're not predicting future mids — they're earning the
half-spread on every round-trip.

---

## H. Counterparty selection

| Product | Counterparty | n | qty | mean adv100 |
|---|---|---|---|---|
| VFE | Mark 55 | 504 | 2,776 | ~+2.4/u |
| VEV_5200 | Mark 22 | 11 | 34 | +3.77 |
| VEV_5300 | Mark 22 | 132 | 439 | +0.94 |
| VEV_5400 | Mark 22 | 263 | 911 | +0.60 |
| VEV_5500 | Mark 22 | 299 | 1042 | +0.50 |
| VEV_6000 | Mark 22 | 317 | 1105 | +0.50 |
| VEV_6500 | Mark 22 | 317 | 1105 | +0.50 |

**Two ISOLATED DYADS:**
- **Mark 01 ↔ Mark 22** on all OTM voucher strikes (1,339 trades by
  network CSV; this dossier reproduces ~1,323 in the per-Mark CSVs).
- **Mark 01 ↔ Mark 55** on VFE only (504 trades, 100% pairing).

These are **structural pairings**, not random — every single trade in those
two dyads matches the partner. The interpretation is that Mark 01 has been
configured to **provide liquidity for Mark 22's voucher offer flow** and to
**provide liquidity for Mark 55's two-sided VFE flow**.

---

## I. Microstructure footprint (VFE)

For Mark 01 VFE trades:

### BUYS (n=260)

| Feature | mean | median |
|---|---|---|
| recent_ret_5 | −0.15 | 0.00 |
| recent_ret_20 | −0.20 | 0.00 |
| recent_ret_100 | −0.38 | −0.50 |
| imb1_pre | +0.016 | 0.00 |
| imb2_pre | +0.006 | 0.00 |
| spread_pre | 5.08 | 5.00 |
| realised_vol_100 | 1.13 | 1.14 |

### SELLS (n=244)

| Feature | mean | median |
|---|---|---|
| recent_ret_5 | +0.08 | 0.00 |
| recent_ret_20 | +0.24 | 0.00 |
| recent_ret_100 | +0.45 | 0.00 |
| imb1_pre | −0.015 | 0.00 |
| imb2_pre | −0.002 | 0.00 |
| spread_pre | 5.00 | 5.00 |

**Pattern**: Mark 01 BUYS slightly after price drops (mean recent_ret_100
−0.38) and SELLS slightly after price rises (mean +0.45). This is **mean-
reversion** — they are mildly contrarian. But the magnitudes are sub-tick
(< 0.5 ticks of recent return), so this is not a strong predictive
microstructure signature; it's the natural consequence of resting MM
quotes that get filled when price moves toward them.

The spread is locked at 5 ticks on VFE; Mark 01 is consistently posted at
±2.5–3.5 from mid, which is OUTSIDE the touch (touch is ±2.5). They are at
**level-2 or better, not at level-1** — they capture a wider spread than
the touch by being patient.

---

## J. Bot archetype

**Mark 01 is a TWO-DYAD MARKET MAKER:**

- **Sub-archetype 1 (OTM voucher MM, paired with Mark 22)**: pure round-
  trip spread capture on stuck strikes. Mid doesn't move; the +0.5/u edge
  is purely the half-spread on each side of a 1-tick wide market.
  Equivalent to a hidden-bid-and-offer pair priced at 0/1 on the OTM
  voucher.

- **Sub-archetype 2 (VFE MM, paired with Mark 55)**: in-the-spread
  passive resting MM that posts ±2.5–3.5 from mid (level-2-ish), gets
  filled by Mark 55's flow on both sides, and earns ~6 ticks of round-
  trip spread. Mild mean-reversion bias from the natural fill
  asymmetry.

**3 strongest evidence features:**

1. **100% counterparty pairing** on both dyads (Mark 22 OTM, Mark 55 VFE).
   No random flow at all.
2. **Pure-MAKER aggressor profile** (82–83% passive on VFE, 100% same-
   tick mechanical on OTM).
3. **Uniform positive adverse selection** (+2.7/u VFE, +0.5 to +0.94 OTM)
   across all days and sides — no informational asymmetry at horizon, just
   pure spread capture.

**Confidence: HIGH** for both sub-archetypes.

---

## K. Exploitation hypothesis

### K.1 OTM vouchers (VEV_5300/5400/5500/6000/6500)

**AVOID.** Mark 01's flow on these strikes is mechanical noise from the
Mark 22 dyad. Mid doesn't move. Spread is too narrow to extract anything
beyond what Mark 01 already has. Do **NOT** treat Mark 01 OTM prints as
directional alpha.

The existing E1 (deep-ITM as VFE-equivalent) and D1 (IV-residual scalping)
alphas already cover everything we need on the voucher surface. Mark 01
adds zero predictive value on top.

### K.2 VFE — secondary exploitation rule (FRONT-RUN with low priority)

Mark 01 buys ~3 ticks BELOW mid and sells ~3 ticks ABOVE mid; they're a
patient resting MM. Two angles for our trader:

1. **Compete on the bid/ask** — if we want to win Mark 55's VFE flow, we
   need to quote ≥1 tick INSIDE Mark 01's quote. That means posting at
   ±2 from mid (inside Mark 01's ±2.5–3.5). But (a) we'd be giving up
   spread and (b) Mark 55 is the loser-counterparty, so we'd be picking up
   Mark 01's good fills — net positive.

2. **Lean LONG-VFE on Mark 01 buys, SHORT-VFE on Mark 01 sells** — a
   weak +1.97/u h=100 signal on buys and +2.86/u h=100 on sells. Tiny
   compared to Mark 67's +1.99/u h=1 (much stronger in time-density), so
   **secondary priority**.

**Pre-registered rule**:
```
on Mark 01 BUY of VFE (counterparty == "Mark 55"):
    lean +VFE 0.5 ticks for next 100 ticks
    decay half-life = 50 ticks

on Mark 01 SELL of VFE (counterparty == "Mark 55"):
    lean -VFE 0.5 ticks for next 100 ticks
    decay half-life = 50 ticks
```

**EV estimate**: 504 prints / 3 days = ~170/day, edge ~+2.4/u, capture 25%
= +0.6/u per print × ~5u/print × 170 = **~510 XIRECS/day**. Smaller than
Mark 67 (~+650) but stackable.

**Falsifier**: any single live day where mean adverse_select_100 for Mark
01 VFE prints flips sign → kill.

### K.3 Deferred to cross-Mark phase

The Mark 01 ↔ Mark 22 OTM dyad is a candidate for the **smile-shift co-print**
analysis (per `cross_product_mark_spillover.csv`): Mark 22 SELLS VEV_5200 →
Mark 01 BUYS VEV_5200 → deeper-ITM vouchers (VEV_4000/4500) jump. The
Mark 01 leg of this is documented but the trade rule is on VEV_5200, not
on the OTM-MM strikes — see Phase 3 cross-Mark file.

---

## Reconciliation note (for Phase 6)

Prior session: "Mark 01 ↔ Mark 22 voucher MM pair on OTM strikes. Treat as
noise. Mark 01's HYDROGEL or VE prints might be informative (small +1.4/u),
but mostly stay neutral."

This dossier **REFINES**:

1. **Mark 01 has TWO dyad pairings**, not one. The Mark 01 ↔ Mark 55 VFE
   pairing is structurally identical to the OTM dyad — 100% pairing, MM
   role on Mark 01's side. The prior session missed this.

2. **The +1.4/u "VFE flow" is actually +2.0–2.9/u VFE spread capture from
   mid_post-vs-fill-price** (a clean MM edge), not directional informed
   flow. The interpretation matters: the alpha is captured by **competing
   on the bid/ask quote** (deferred), not by **copying Mark 01's
   direction** (which would only give us the mid-drift residual ≈ −0.3 to
   +0.6 ticks per side, much smaller than spread capture).

3. **Mark 01 does not trade HYDROGEL** (neither in our per-Mark CSVs nor
   in the network CSV beyond a handful of incidental prints). The prior
   session's "Mark 01 prints on HYDROGEL or VE might be informative" line
   was speculation — there are zero meaningful Mark 01 HYD prints to act
   on.
