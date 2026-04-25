# Rust BT — fill-granularity fix (E13/E15 divergence)

**Status:** diagnosis confirmed by v1 probes; concrete fix path
conditional on v2 probe results. *Do not ship a code change before
v2 lands.*

## What we know

From `runs/probes/diff_summary.md` (v1 trader, official replay 387956):

| eid | intent | local fills | official fills |
|---|---|---|---|
| E13_POSLIMIT_EXACT | BUY 17 @ 1 (VEV_6500) | `17@1` (1 row) | `13@1; 4@1` (2 rows) |
| E15_FLATTEN_V65 | SELL 16 @ 0 (VEV_6500) | `16@0` (1 row) | `11@0; 5@0` (2 rows) |

- All 27 other eids match exactly across python / rust / official.
- Net qty, side, price, ts all agree on E13/E15. Only the *fill row count
  and per-row qty* differ.
- Both divergent cases are at VEV_6500 boundary prices (1 = floor ask,
  0 = floor bid) — i.e. exactly where bots stack quotes.

## Why our local code emits a single row

`prosperity_rust_backtester/src/runner.rs::match_orders_for_symbol`
(currently lines ~582–780) consumes the book one **`BookLevel`** at a
time:

```rust
for level in asks.iter_mut() {
    if remaining <= 0 { break; }
    if level.price > order.price || level.volume <= 0 { continue; }
    let fill = remaining.min(level.volume);            // <-- atomic
    own_trades.push(Trade { quantity: fill, price: ..., ... }); // 1 row
    level.volume -= fill;
    remaining -= fill;
}
```

A `BookLevel` is `(price, total_volume)` aggregated from `prices_*.csv`.
The CSV schema is `bid_price_1, bid_volume_1, …, ask_price_3,
ask_volume_3` — three aggregated levels per side, **no per-counterparty
breakdown**. So our matching loop has nothing finer to split on, and
emits one Trade per `BookLevel` it consumes.

The `market_available` fallback at the bottom of the loop only runs
**after** the book is exhausted (`if remaining != 0 …`), so it doesn't
participate when the book has enough volume to fully fill the order
(which is the E13/E15 case).

## Hypothesis (to be confirmed by v2)

IMC's matching engine, when it consumes liquidity at price *p* on tick
*T*, splits the resulting fill across the `trades_*.csv` rows whose
`(symbol, price, timestamp) == (s, p, T)`, treating each row as one
counterparty quote. Concretely:

```
n_official_fills(s, p, T, qty) ==
    count of trades-CSV rows with (symbol=s, price=p, timestamp=T)   if qty fits
    that count + spillover behaviour                                  if qty exceeds
```

This is consistent with:

1. The split sizes (13/4 vs 11/5) — they are **not** uniform, so
   the split rule isn't "max fill per pass = N". They look like
   they're carrying real counterparty lot sizes.
2. The trades CSV is the only data source that **has** per-counterparty
   info (`buyer`, `seller`, `quantity`).
3. The two observed divergences both happen at VEV_6500 boundary prices,
   where the trades CSV is dense (bots stacking).
4. The locals' agreement on E07 (waterfall_excess) and similar non-floor
   sweeps — those probably hit ticks where there are 0 or 1 trades-CSV
   rows at the swept price, so the split equals 1, indistinguishable from
   our coalesced behaviour.

## Validation plan: probe v2

`probe_v2_fill_granularity.py` (created) fires VEV_6500 BUY @ 1 across
qtys {1, 5, 11, 17, 30, 100, 250} × 4 samples each, plus a SELL @ 0
× qty=17 × 4 samples. After submission, `probe_analyze.py` will produce
per-(qty, sample) fill-row counts. Then **for each probe**, cross-check:

```
n_official_fills(F<i>_BUY_q<q>_s<j>) ==
    count of trades_round_3_day_0.csv rows where
      symbol=VEV_6500 AND price=1 AND timestamp=<probe_ts>
```

If this equality holds across the panel, the hypothesis is confirmed
and the fix is mechanical (Path A below). If it doesn't hold, fall back
to Path B.

## Fix Path A — preferred, if v2 confirms hypothesis

**Idea:** rebuild the per-tick book from the trades CSV (per row) layered
under the prices CSV (residual aggregate), so each `BookLevel` carries a
list of `LotEntry { quantity, counterparty }`. Matching consumes lots
in arrival order and emits one Trade per lot consumed.

### Data-side change (`src/model.rs` + the loader)

```rust
pub struct LotEntry {
    pub quantity: i64,
    pub counterparty: String,   // empty string for residual aggregate
}

pub struct BookLevel {
    pub price: i64,
    pub volume: i64,            // sum of lots[*].quantity (kept as fast-path)
    pub lots: Vec<LotEntry>,    // NEW — populated from trades CSV
}
```

Loader rule (run once per (symbol, ts)):

1. Start from the prices-CSV aggregate: one `LotEntry` per
   `(price, volume)` with `counterparty=""`.
2. For each row in `trades_*.csv` with that `(symbol, ts, price)`: pop
   `row.quantity` worth of volume off the residual aggregate (smallest
   first if multiple lots remain), and append a fresh `LotEntry { qty,
   counterparty: row.buyer | row.seller }`.
3. The final `BookLevel.lots` is in trades-CSV row order, with any
   remainder living in the residual lot at index 0.

### Matching-side change (`src/runner.rs::match_orders_for_symbol`)

Replace the inner book-sweep loop:

```rust
for level in asks.iter_mut() {
    if remaining <= 0 { break; }
    if level.price > order.price { continue; }
    while remaining > 0 && !level.lots.is_empty() {
        let lot = &mut level.lots[0];
        let fill = remaining.min(lot.quantity);
        if fill <= 0 { level.lots.remove(0); continue; }
        own_trades.push(Trade {
            symbol: symbol.to_string(),
            price: slippage_adjusted_price(level.price, true,
                                           config.price_slippage_bps),
            quantity: fill,
            buyer: "SUBMISSION".to_string(),
            seller: lot.counterparty.clone(),
            timestamp,
        });
        adjust_position(position, symbol, fill);
        adjust_cash(cash_by_product, symbol,
                    -(level.price as f64 * fill as f64));
        lot.quantity -= fill;
        level.volume -= fill;
        remaining -= fill;
        if lot.quantity == 0 { level.lots.remove(0); }
    }
}
```

…with the symmetric block for `remaining < 0` against `bids`. The
`market_available` fallback further down stays as-is — it now only
catches the truly excess-of-book case, which `eligible_trade_price`
already gates correctly.

### Why this is safe

- Net behaviour is preserved: `level.volume` still goes from N to 0
  monotonically; PnL math is unchanged.
- The 27 currently-matching eids stay matching: ticks with 0 or 1 rows
  in `trades_*.csv` at the swept price produce the same single Trade as
  today (the residual lot consumes everything).
- `market_trades` consumed during fills are still removed from the
  `market_available` pool (because the loader pre-deducted them in
  step 2), so the resting-quote / fallback path doesn't double-count.

## Fix Path B — fallback, if v2 disproves Path A

If the equality `n_official_fills == count_of_trades_csv_rows` does
*not* hold, the most likely alternatives are:

1. **Fixed lot cap.** IMC may enforce "no Trade with quantity > K"
   for some K. If samples show the same split across all qtys at the
   same ts, this is the rule. Fix: clamp each emitted Trade's qty to K
   inside the existing book-sweep loop.

2. **Pre-tick vs post-tick separation.** IMC may split into "fills
   against pre-tick book state" + "fills against new market_trades
   that arrived this tick". Fix: rebuild the book from the previous
   tick's prices CSV, run the sweep against that snapshot, then run a
   second pass against this tick's market_trades.

Decide between (1) and (2) by inspecting the v2 panel: if split sizes
correlate with qty, it's (1); if they correlate with trades-CSV ts
state, it's (2). Both are smaller patches than Path A.

## Validation steps after a fix lands

1. Re-run v1 probe locally — E13/E15 must now match official exactly.
   All other 27 eids must still match.
2. Re-run v2 probe locally — every `F<i>_BUY_q<q>_s<j>` row in
   `diff_summary.md` should report `fill_shape_local_vs_official: no`
   and identical fill tuples.
3. Run a regression on the existing R3 traders (`SoftAnchorMM`,
   `Vev_WallMid_MM`, etc.) and confirm PnL is unchanged within
   floating-point tolerance — the fix is supposed to change *fill
   granularity*, not net PnL.
4. Add a unit test in `prosperity_rust_backtester/tests/` that loads a
   minimal fixture (one tick, one symbol, two trades-CSV rows at the
   same price) and asserts the matching loop emits two Trades with the
   right per-row quantities.

## Open questions

- **Does the rule extend to non-VEV_6500 products?** v1 didn't show it
  on HYDROGEL/VE, but those rarely have multi-row trades-CSV entries
  at a single price. v2 is VEV_6500-only; a v3 should add a few
  HYDROGEL / VE samples on dense ticks if v2 proves Path A.
- **Spillover when `qty` exceeds the price level.** What does IMC do
  when n trades-CSV rows have total qty < submission qty? Probably
  spills to the next price level and re-applies the rule. Confirm with
  the q=250 series in v2 (will sweep multiple levels, possibly multiple
  ticks via `market_available` fallback).
- **`buyer`/`seller` field population.** Once we have per-lot
  counterparty in our loop, we can finally populate the non-empty
  side of the Trade (currently always empty in the book-sweep path).
  This may matter for downstream traders that read `trade.buyer` /
  `trade.seller` to identify counterparties.
