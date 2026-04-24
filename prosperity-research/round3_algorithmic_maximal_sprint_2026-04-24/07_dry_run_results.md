# Dry-run results — Round 3 candidate on Round 2 data — 2026-04-24

**Purpose: structural / interface validation only.** No Round-3 edge is being
claimed. The Round 2 symbols (`ASH_COATED_OSMIUM`, `INTARIAN_PEPPER_ROOT`) are
not in the Round 3 allowlist; the candidate is required to no-op on them.

## Commands

```
cd prosperity_rust_backtester
make round2 TRADER=traders/Round3/candidates/round3_no_trade_baseline_v01.py
make round2 TRADER=traders/Round3/candidates/round3_maximal_multi_product_v01.py
```

## Results table

| trader | dataset | set | day | ticks | own_trades | final_pnl |
|---|---|---|---|---|---|---|
| round3_no_trade_baseline_v01 | round2 | D-1 | -1 | 10000 | 0 | 0.00 |
| round3_no_trade_baseline_v01 | round2 | day-0 | 0 | 10000 | 0 | 0.00 |
| round3_no_trade_baseline_v01 | round2 | day-1 | 1 | 10000 | 0 | 0.00 |
| round3_maximal_multi_product_v01 | round2 | D-1 | -1 | 10000 | 0 | 0.00 |
| round3_maximal_multi_product_v01 | round2 | day-0 | 0 | 10000 | 0 | 0.00 |
| round3_maximal_multi_product_v01 | round2 | day-1 | 1 | 10000 | 0 | 0.00 |

Total: 30,000 ticks of execution, zero exceptions, zero orders, zero PnL for
both traders on each day.

## What this proves

1. Both trader files import `datamodel` and build without errors under the
   Rust backtester's PyO3 binding.
2. Both traders satisfy the `(orders, conversions, traderData)` return shape.
3. `traderData` round-trips between ticks (JSON parse / dump of the serious
   candidate's blob never raised across 30k invocations).
4. The serious candidate correctly no-ops on every symbol that is not on the
   Round 3 allowlist. This is the designed behaviour and the main reason the
   dry-run is safe: seeing `ASH_COATED_OSMIUM` does not cause the trader to
   misapply a voucher identity to an unrelated product.
5. No position-limit breach anywhere (zero orders ⇒ no breach possible).

## What this does NOT prove

1. Anything about Round 3 PnL, Sharpe, drawdown, or inventory path.
2. Whether the voucher intrinsic-arb gate fires at the right frequency.
3. Whether the assumed voucher symbol prefix (`VELVET_FRUIT_EXTRACT_VOUCHER_<K>`
   or `VFE_VOUCHER_<K>`) actually matches the live feed.
4. Whether voucher position limits are compatible with the assumed cap of 20.
5. Whether the briefing's call-payoff interpretation of vouchers is correct.

A zero-order day is not a claim of edge. It is a claim that the trader is safe
to submit in the sense that it will not crash, will not violate the interface,
and will not mis-trade when products it was not designed for appear in the
feed.
