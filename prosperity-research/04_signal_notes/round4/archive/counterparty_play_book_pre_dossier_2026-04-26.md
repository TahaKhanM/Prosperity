# Counterparty play-book — Round 4

The Round 4 hint card "Anticipating Activity" tells you to read each Mark
and act on it. This file translates the EDA findings into explicit per-Mark
trading rules, ranked by confidence.

Source data: `prosperity-research/03_eda/round4/counterparty_summary.csv`,
`prosperity-research/04_signal_notes/round4/counterparty_scan.csv`,
`headline_findings.md`.

## Per-Mark rules

### Mark 14 — SMART (high confidence)

- 3-day total: 4,510 buys / 4,208 sells, 8,718 gross. +49,777 horizon-500
  PnL, +5.71 / unit. Profitable on **both** buy and sell sides of HYDROGEL,
  VE, and (deep-ITM) VEV_4000/4500.
- Most active in HYDROGEL_PACK and VELVETFRUIT_EXTRACT.
- **Rule.** When `Mark 14` appears as the **buyer** of any product in
  `state.market_trades[product]` within the last ~200 ticks, lean **long**
  that product. When they appear as the **seller**, lean short. Decay the
  lean linearly over ~500 ticks.
- Sizing: scale lean magnitude by trade quantity. A single 50-lot Mark 14
  print is a stronger signal than a 5-lot one.
- Caveat: a Mark 14 print on a *deep-ITM voucher* (VEV_4000, VEV_4500) is a
  proxy for a VE directional bet; treat it as a VE signal, not a separate
  options signal.

### Mark 38 — BAG-HOLDER (high confidence)

- 3-day total: 2,493 / 2,507, 5,000 gross. −41,696 horizon-500 PnL,
  −8.34 / unit. Mirror image of Mark 14 (they trade against each other 1,442
  times in the historical data).
- **Rule.** When `Mark 38` appears as the **buyer**, lean **short** that
  product. When they appear as the **seller**, lean long. Same magnitude as
  Mark 14, opposite direction.
- Implementation tip: the Mark 14 / Mark 38 signals are usually anti-
  correlated and can be combined into a single per-product `lean` accumulator
  with `+1` for Mark 14 buyer or Mark 38 seller, `−1` for Mark 14 seller or
  Mark 38 buyer. (Same logic, halved noise.)

### Mark 67 — BUY-ONLY ON VE (medium confidence)

- 3-day total: 1,510 buys, **0 sells**. +1,796 horizon-500 PnL, +1.19 / unit.
  Trades **only** `VELVETFRUIT_EXTRACT` (1 product).
- **Rule.** When `Mark 67` is the buyer of VE, add a small long-VE lean. They
  never sell, so there is no symmetric short-side rule.
- Confidence is medium because the per-unit PnL (+1.19) is well below
  Mark 14's (+5.71). This is a useful confirming signal more than a
  standalone alpha.

### Mark 49 — INFORMED SELLER OF VE (low confidence)

- 3-day total: 115 buys / 1,071 sells, all on VE. Their **buys** lose
  (−1.14 / unit), implying their sells are slightly informed.
- **Rule.** When `Mark 49` sells VE in size, lean weakly long (i.e., follow
  their sells if they are draining inventory at favourable prices) or skip
  (the magnitude is small).

### Mark 01 ↔ Mark 22 — VOUCHER MM PAIR (no signal)

- Mark 01: 6,053 buys / 1,375 sells, mostly OTM voucher buyer.
- Mark 22: 206 buys / 5,683 sells, mostly OTM voucher seller.
- They trade against each other 1,339 times, dominating the OTM strike
  prints (VEV_5300+, including stuck VEV_6000/VEV_6500).
- **Rule.** **Do not** treat Mark 01 / Mark 22 prints on those strikes as
  alpha. They are noise from a market-maker pair.
- Mark 01 prints on HYDROGEL or VE *might* be informative (they have a
  small +1.4 / unit overall), but mostly stay neutral.

### Mark 55 — NOISE TO LIGHT FADE (low confidence)

- 3-day total: 3,254 / 3,297, both sides high volume. −2.41 / unit.
  Only trades VEV_5500 (one product, OTM voucher).
- **Rule.** Light fade if you must, but the per-unit number is small and the
  product is illiquid OTM. Easy to ignore.

## Combined "Mark lean" implementation

```python
# Pseudocode for run() — uses traderData to track decaying per-product lean.
state = json.loads(state.traderData) if state.traderData else {}
lean = state.setdefault("mark_lean", {})  # product -> float
DECAY = 0.985  # per tick; half-life ≈ 46 ticks
for product, lean_val in list(lean.items()):
    lean[product] = lean_val * DECAY

for product, trades in state.market_trades.items():
    for t in trades:
        weight = float(t.quantity) * 0.05  # tune
        if t.buyer == "Mark 14" or t.seller == "Mark 38":
            lean[product] = lean.get(product, 0.0) + weight
        elif t.seller == "Mark 14" or t.buyer == "Mark 38":
            lean[product] = lean.get(product, 0.0) - weight
        if product == "VELVETFRUIT_EXTRACT" and t.buyer == "Mark 67":
            lean[product] = lean.get(product, 0.0) + 0.5 * weight

# Use `lean[product]` to skew the MM fair value or the take threshold.
```

## Falsifiers

Each rule above is falsifiable in the next live submission:
- If Mark 14 starts losing (per-unit horizon PnL turns negative on a fresh
  R4-live counterparty scan), **stop copying**.
- If Mark 38 starts winning, **stop fading**.
- If Mark 67 starts selling, the buy-only rule is dead.
- If the Mark 01 / Mark 22 pair starts producing > ±2 / unit on HYDROGEL or
  VE prints, re-classify them.

Re-run `python3 scripts/round4_options/counterparty_scan.py` after every
new submission's `combined.log` to refresh the table.
