# R2 — Fill-model patch spec (unblocks card D1)

**Goal.** The Rust backtester currently over-reports PnL on tight-edge
voucher scalps by ~2×. Card D1 (IV-residual scalp on K=5100–5500) fails
gate 4 (mid-fill dependence). This note proposes a tightened fill model
so D1 and other tight-edge strategies can be evaluated honestly.

Do-nothing verdict: DO NOT implement immediately — this is a design
spec for a follow-up implementation session.

---

## 1. Current fill behavior — code citations

File: `prosperity_rust_backtester/src/runner.rs`.
Function: `match_orders_for_symbol` (lines **582–780**), called once per
product per tick from the main loop at line **237**.

### 1a. Aggressive (taker) path — book match, lines **643–691**

```rust
if remaining > 0 {
    for level in asks.iter_mut() {
        if remaining <= 0 { break; }
        if level.price > order.price || level.volume <= 0 { continue; }
        let fill = remaining.min(level.volume);
        let trade_price =
            slippage_adjusted_price(level.price, true, config.price_slippage_bps);
        own_trades.push(Trade { price: trade_price, quantity: fill, ... });
        adjust_position(position, symbol, fill);
        adjust_cash(cash_by_product, symbol, -(trade_price as f64 * fill as f64));
        level.volume -= fill;
        remaining -= fill;
    }
}
```

**Good.** Taker fills already walk the ladder level-by-level, price =
level price (ask for buys, bid for sells), volume is consumed in
priority. No mid-fill on this path. The mirror `remaining < 0` block
(lines 667–691) does the same for sells against bids.

### 1b. Passive (maker) path — market-trade match, lines **693–772**

```rust
if remaining != 0 && !config.mode_is_none() {
    for trade in &mut market_available {
        ...
        if !eligible_trade_price(order.price, trade.price, remaining,
                                 &config.trade_match_mode) { continue; }
        // queue-position consumption: subtract 'ahead' volume at order.price
        ...
        let fill = remaining.abs().min(trade.quantity);
        let execution_price =
            slippage_adjusted_price(order.price, remaining > 0,
                                    config.price_slippage_bps);
        own_trades.push(Trade { price: execution_price, ... });
        ...
    }
}
```

With `eligible_trade_price` (lines 813–829):

```rust
if quantity > 0 {                                 // buy
    if mode == "all" { return trade_price <= order_price; }
    return trade_price < order_price;             // mode "strict"
}
```

### 1c. The bug

1. `market_available` (lines 606–621) is built from **all** market
   trades in the tick, regardless of timestamp. There is no filter
   `trade.timestamp > tick.timestamp_when_trader_saw_state`. Because
   the trader's order is notionally posted at the current tick, every
   market trade in that tick — *including ones that executed before
   the trader could have been present* — is treated as a possible
   counterparty.
2. Fill **price** = `order.price` (the trader's quote), not
   `trade.price`. This is actually benign in isolation (passive fills
   at your own quote is the correct model), **but** combined with (1)
   it means a maker buy@100 fills against a trade printed at 99 or 100
   even though the book never crossed 100 in a tick posted *after*
   ours.
3. In `mode = "all"` (default) the condition is `trade_price <=
   order_price` for buys. That is a *non-strict* inequality. A resting
   maker bid at 100 trades against a market trade printed *at* 100,
   even though price-time priority says the market trade cleared a
   resting seller at 100 before our order arrived.

Net effect: a near-top, zero-edge quote is treated as if it filled
every time a trade touched our price, independent of direction and
independent of whether the book actually crossed our level. For thick
OB products (HYDROGEL, VE) the error is small because we mostly quote
inside the spread. For thin voucher books with 0.5–1 shell edges, the
error doubles fill volume.

### 1d. Worked example

State at tick `t`: best_bid = 99, best_ask = 101, mid = 100. Market
trade prints in this tick at 100 size 5 (buyer = X, seller = Y, both
anonymous). Trader posts passive buy@100 size 5.

- `eligible_trade_price(order=100, trade=100, qty=+5, mode="all")`
  → `100 <= 100` → **true**.
- Queue-ahead consumption runs: `buy_queue_remaining[100]` is empty
  (best_bid was 99, not 100), so `ahead = 0`; trade.quantity not
  reduced.
- Fill = min(5, 5) = 5 at `execution_price = order.price = 100`.
- Trader books +5 HYDROGEL at 100 without the book ever having
  crossed 100 in a post-our-order tick.

True market: the trade at 100 cleared before the trader existed. The
trader should have filled 0. PnL over-reported by ~5 × (spread / 2)
per such event.

---

## 2. Proposed tightened behavior

Introduce a `FillModel` enum: `Legacy` (current behavior, default) and
`Tight`. In `Tight` mode, fills obey strict price-time priority:

**Taker orders (aggressive).** Unchanged — already correct. Price =
book level price, volume cascades through levels 1 → 2 → 3 until
`remaining == 0` or ladder exhausted. **Never mid.**

**Maker orders (passive).** A maker order fills only if at least one
of these conditions holds in the tick AFTER posting:
1. The *opposite* side of the book crosses our quote: `best_ask ≤
   our_bid` (for a buy) or `best_bid ≥ our_ask` (for a sell). In that
   case the crossed portion fills at **our quote price** (maker
   passive), size capped by the crossing level's volume.
2. A market trade prints at a price **strictly** beyond our quote
   (`trade.price < our_bid` for buys, `trade.price > our_ask` for
   sells). A strict cross means the market was willing to trade
   through our level; fill at our quote price, size capped by
   `max(0, trade.quantity − queue_ahead)`.
3. Market trades printed exactly *at* our quote price do **not** fill
   unless queue-ahead volume is fully consumed (the current
   `buy_queue_remaining` bookkeeping is retained; the new rule is
   that it must go to **zero** before our order participates, rather
   than just decrementing by whatever the trade ate).

Explicit rejections in `Tight` mode:
- Market trades at exactly our quote price when we were not already
  on the book at that price in the prior tick's snapshot → reject.
  Operational proxy: if `buy_queue_remaining[order.price]` was not
  seeded from the book at the current tick, we had no queue position.
- No fill at mid, at best_ask/best_bid, or at any book level interior
  under any maker path.
- `eligible_trade_price` strict-inequality form is the default for
  tight; the "all" (≤) form is rejected.

**Timestamp handling.** The current code does not propagate a "trader
posted at" timestamp into `match_orders_for_symbol`. Simplest fix:
treat all market trades in the same tick as *pre-post* and ignore them
for maker fills unless they strictly cross. Only the *next* tick's
trades/crossings are candidates. This is slightly pessimistic (tail of
tick `t` is unreachable) but eliminates the mid-fill inflation.

---

## 3. CLI proposal

Add one flag to `cli.rs`:

```
--fill-model {legacy,tight}    default: legacy
```

Propagation:

```rust
// cli.rs Args
#[arg(long = "fill-model", value_enum, default_value_t = FillModel::Legacy)]
fill_model: FillModel,

// cli.rs run()
let matching = MatchingConfig {
    trade_match_mode: args.trade_match_mode.clone(),
    queue_penetration: args.queue_penetration,
    price_slippage_bps: args.price_slippage_bps,
    fill_model: args.fill_model,   // NEW
};
```

Extend `MatchingConfig` in `model.rs`:

```rust
pub struct MatchingConfig {
    pub trade_match_mode: String,
    pub queue_penetration: f64,
    pub price_slippage_bps: f64,
    pub fill_model: FillModel,         // NEW, #[serde(default)]
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, ValueEnum, Default)]
pub enum FillModel { #[default] Legacy, Tight }
```

Default `Legacy` preserves every existing baseline metric. `Tight` is
opt-in (`make round3 TRADER=... FILL_MODEL=tight` after a one-line
Makefile addition).

---

## 4. Diff sketch (pseudo-diff, **not applied**)

`match_orders_for_symbol` does NOT need a new signature parameter —
`FillModel` already rides on `config: &MatchingConfig`. Three change
sites:

**Site A — `eligible_trade_price` (runner.rs:813).** Force strict
inequality in tight mode:

```
-if quantity > 0 {
-    if mode == "all" { return trade_price <= order_price; }
-    return trade_price < order_price;
-}
+if quantity > 0 {
+    if fill_model == FillModel::Tight {
+        return trade_price < order_price;     // strict cross only
+    }
+    if mode == "all" { return trade_price <= order_price; }
+    return trade_price < order_price;
+}
```

(and mirror for `quantity < 0`). Signature gains `fill_model:
FillModel` — a single extra arg threaded from line 705.

**Site B — queue-ahead must reach zero (runner.rs:709–727).** In
tight mode, a maker order may consume the trade *only* if
`buy_queue_remaining[order.price]` had a seeded entry (meaning we were
quoting at a level that already existed on the book) AND that entry
has fully decremented:

```
-if remaining > 0 && trade.price == order.price {
-    if let Some(ahead) = buy_queue_remaining.get_mut(&order.price) {
-        let consumed = trade.quantity.min(*ahead);
-        trade.quantity -= consumed;
-        *ahead -= consumed;
-        if *ahead <= 0 { buy_queue_remaining.remove(&order.price); }
-    }
-}
+if remaining > 0 && trade.price == order.price {
+    match buy_queue_remaining.get_mut(&order.price) {
+        Some(ahead) => {
+            let consumed = trade.quantity.min(*ahead);
+            trade.quantity -= consumed;
+            *ahead -= consumed;
+            if *ahead <= 0 { buy_queue_remaining.remove(&order.price); }
+        }
+        None if fill_model == FillModel::Tight => {
+            // no seeded queue position -> no fill at equal price
+            trade.quantity = 0;
+        }
+        None => {}
+    }
+}
```

**Site C — book-crossing pass (new, inserted before or folded into
the maker loop at runner.rs:693).** In tight mode, in addition to
market-trade matching, check whether the tick's book snapshot itself
crosses our quote. This is the "next-tick cross" semantic, evaluated
at tick start since we have no intra-tick state:

```
+if fill_model == FillModel::Tight && remaining != 0 {
+    // maker buy: only fill if best_ask <= our bid (book crossed)
+    if remaining > 0 {
+        for level in asks.iter_mut() {
+            if level.price > order.price || level.volume <= 0 { continue; }
+            let fill = remaining.min(level.volume);
+            let trade_price = order.price;         // pay our quote
+            own_trades.push(Trade { price: trade_price, ... });
+            level.volume -= fill; remaining -= fill;
+            if remaining == 0 { break; }
+        }
+    } else { /* mirror for sells vs bids */ }
+}
```

Note: this block resembles the existing taker path but fills at
`order.price`, not `level.price`, because we are the resting side.
Legacy mode skips this block and falls into the existing
market-trade loop.

No change to the taker-path blocks at 643–691 — they are already
correct.

---

## 5. Unit-test recipe (3 cases)

Add to the `tests` module near `runner.rs:1318`. Each case constructs
a hand-built `TickSnapshot` + one-tick market trade list, calls
`match_orders_for_symbol` twice (Legacy then Tight), and asserts the
own-trade list.

**Case A — maker bid posted after the last print.** Book:
bids=[(99,10)], asks=[(101,10)]. Market trade at 100 size 5. Order:
buy@100 size 5.
- Legacy → 1 fill, 5 @ 100.
- Tight → **0 fills** (trade did not strictly cross; no seeded queue
  position at 100).

**Case B — taker buy walks 3 levels.** Book: asks=[(100,3),(101,4),
(102,5)]. Order: buy@102 size 10.
- Legacy and Tight → 3 fills: 3@100, 4@101, 3@102. Total notional =
  300+404+306 = 1010. **No** 10 @ 101 (mid) under either model. This
  pins the "never mid" invariant on the taker path.

**Case C — maker bid filled by subsequent cross.** Book at tick t:
bids=[(100,2),(99,8)], asks=[(101,10)]. Order: buy@100 size 3 (we are
*behind* 2 in the queue at 100). Market trade: 5 prints at 99.
- Legacy → fills up to 3 @ 100 (strict cross allows it; queue-ahead
  decrements to 0 after consuming 2, then we take 3).
- Tight → fills up to 3 @ 100 **at our quote price of 100**, queue
  bookkeeping identical. Equivalent behavior on this case — it
  verifies tight does not break the legitimate-cross path.

Supporting assertion in all three: no own trade's price equals
`(best_bid+best_ask)/2` unless that mid happens to coincide with a
bona-fide ladder level.

---

## 6. Expected PnL impact

Candidate baseline for the sanity run: `traders/Round1/Ash.py`
(static-fair MM) on `datasets/round3`.

| strategy class            | maker PnL | taker PnL | expected delta |
|---------------------------|-----------|-----------|----------------|
| HYDROGEL soft-anchor (A1) | unchanged | −5–10 %   | small, bounded |
| VE wall-mid MM (B1)       | unchanged | −5–15 %   | small          |
| D1 IV residual scalp      | −40–60 %  | −30 %     | ~50 % drop     |
| E1 deep-ITM delta-1       | unchanged | unchanged | 0              |

Rationale: A1 and B1 already quote inside wide-ish spreads so the
mid-fill inflation is a minor component of their PnL. D1 harvests
0.05-shell residuals where every spurious mid-fill is ~100 % of the
per-tick edge; halving its reported PnL matches the 2× hypothesis.
Taker PnL drops modestly because the legacy `eligible_trade_price
<= order.price` let some taker-style fills happen through the maker
loop at `order.price` instead of the (worse) ladder price.

---

## 7. Go / no-go

**Verdict: GO — but sequenced *after* the A1/B1/C1/G1 ship-now
submission has been uploaded with Legacy.**

Justification. Ship-now cards A1, B1, C1, G1 all passed gate 4 on the
live hunt precisely because their expected PnL is dominated by
ladder-takeable fills (already correct under Legacy) and by passive
quoting inside the spread where the Legacy/Tight gap is small. Holding
the first submission on fill-model work risks missing the 48-hour
window. Once the first submission is in:
1. Land the Tight model behind `--fill-model tight` (default Legacy —
   no baseline drift).
2. Re-run A1/B1/C1 under Tight; expect ≤ 15 % PnL drop. If > 25 %,
   investigate before resubmitting.
3. Re-evaluate D1 under Tight. If PnL is still > 0.3 k / day and
   variance is acceptable, promote D1 from research-more to ship-now
   for submission 2.
4. E1 is gate-4-blocked on *settlement* logic, not fill logic; R2 does
   not unblock it. Tracked separately.

Word count ≈ 1180.
