# Round 3 counterparty findings

Source: `Data/ROUND_3/trades_round_3_day_{0,1,2}.csv`, 4 049 trades total.

## Named counterparties

**None.** Across all 3 historical days the `buyer` and `seller` columns are
empty strings on every single row. The aggregate `counterparty_scan.csv`
output collapses to a single bucket `_anon_` per (day, product, side).

```
day=0: 1 308 trades, 0 named parties
day=1: 1 407 trades, 0 named parties
day=2: 1 333 trades, 0 named parties
```

Compare to P3, where `Olivia` appeared from day 0 on `KELP` and `SQUID_INK`
— the very first place a winning team would have found alpha. R3 historical
does not expose that signal.

## Horizon-PnL of the anonymous aggregate

From the baseline `counterparty_scan.csv`:

| day | product | side | n_trades | total_qty | mean horizon PnL |
|---|---|---|---|---|---|
| 0 | VELVETFRUIT_EXTRACT | buyer | 445 | 2 689 | +0.12 |
| 0 | VEV_5400 | buyer | 64 | 218 | +0.61 |
| 1 | VELVETFRUIT_EXTRACT | buyer | 495 | 3 152 | +0.14 |
| 1 | VEV_5100 | buyer | 48 | 189 | +0.93 |
| 2 | VELVETFRUIT_EXTRACT | buyer | 488 | 3 108 | +0.10 |
| 2 | VEV_5200 | buyer | 42 | 191 | +1.01 |

The buy side is mildly positive-horizon (buyers on average win ~0.1–1 shell
per trade at 100-tick horizon). That signal is **unusable** without a name
attached: it says "the pool of market-takers is slightly profitable" but
you cannot selectively copy one.

## Trade-size distribution (axis L)

No obvious "bot-modal" quantity emerges:

| product | n | median qty | top 3 modes |
|---|---|---|---|
| VELVETFRUIT_EXTRACT | 1 372 | 6 | 8 (n=233), 7 (224), 5 (223) |
| HYDROGEL_PACK | 1 010 | 4 | 5 (212), 6 (205), 4 (202) |
| VEV_4000 | 464 | 2 | 2 (160), 3 (158), 1 (146) |
| VEV_5400 | 225 | 4 | 2 (62), 4 (60), 5 (57) |
| VEV_5500 | 267 | 4 | 2 (73), 4 (73), 5 (68) |
| VEV_6000 | 284 | 4 | 4 (78), 2 (76), 5 (74) |
| VEV_6500 | 284 | 4 | 4 (78), 2 (76), 5 (74) |

Sizes span a flat 2–8 range for VE and 1–5 for vouchers. No single "big
print" mode worth trading against.

**Note:** VEV_6000 and VEV_6500 have **identical** trade counts (284)
and identical mode distributions. Those two tickers appear to share a
trade generator or trade lockstep in historical data (worth confirming
live).

## Implication

- The alpha card **"copy named bot"** sits in `research-more`, not `ship-now`.
- Live hook: after the first live tick, inspect `state.market_trades[symbol]`
  for any non-empty buyer/seller; if a name appears, begin a rolling
  horizon-PnL computation against it and lift the feature flag in
  `traderData` once it clears 2 × SE on ≥ 20 trades.
- Size-based filter (bot-modal take) is disqualified — the size distribution
  is uniform retail-looking.
