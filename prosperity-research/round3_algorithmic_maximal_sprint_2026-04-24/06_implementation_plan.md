# Implementation plan — Round 3 — 2026-04-24

## Two files

1. `prosperity_rust_backtester/traders/Round3/candidates/round3_no_trade_baseline_v01.py`
   — unconditional no-op returning empty orders per tick. Purpose: baseline PnL comparator.

2. `prosperity_rust_backtester/traders/Round3/candidates/round3_maximal_multi_product_v01.py`
   — the serious first candidate. Combines:
     - R3-STRUCT-submission-safe-scaffold-v01 (interface backbone)
     - R3-VFE-voucher-intrinsic-arb-v01 (active, identity-bounded)
     - R3-VFE-voucher-strike-monotonicity-v01 (implemented, default-off)
   — no directional bets on HYDROGEL_PACKS or VFE at the underlying level.

## Hard constraints enforced by code

- `run()` returns `(orders, 0, traderData)`.
- `bid()` returns `20` (safe Round 2 MAF, ignored in Round 3).
- Worst-case aggregate position-limit check per product per tick: the sum of
  buy volumes is capped so `(position + sum_buys)` never exceeds the assumed
  cap; the sum of sell volumes mirrors this for the short side.
- Default per-product cap: `20`. This is intentionally lower than the Round
  1/2 cap of 80 because we do not know the Round 3 caps.
- Unknown symbols: no-op. The trader explicitly whitelists its product set
  `{HYDROGEL_PACKS, VELVET_FRUIT_EXTRACT, VFE_VOUCHER_<K>}` and ignores any
  other symbol. This guarantees safe behaviour when dry-run on Round 2
  data (which contains only Round 1/2 symbols).
- Voucher strike parsing: take the integer after the last underscore in the
  symbol; if parsing fails, permanently skip that symbol (flag in traderData).
- `traderData`: single JSON blob with the keys `schema_version`, `seen_vouchers`, `flagged_symbols`. Capped at 8 KB defensively.
- No unsupported imports. Only `json`, `math`, `typing`, and `datamodel`.

## Validation commands

- Structural dry-run on Round 2 data (proves no-op on unknown symbols, no crashes, submission-interface correctness):

  ```
  cd prosperity_rust_backtester
  make round2 TRADER=traders/Round3/candidates/round3_no_trade_baseline_v01.py PERSIST=1
  make round2 TRADER=traders/Round3/candidates/round3_maximal_multi_product_v01.py PERSIST=1
  ```

- On Round 3 data (ONCE AVAILABLE):

  ```
  make round3 TRADER=traders/Round3/candidates/round3_no_trade_baseline_v01.py PERSIST=1
  make round3 TRADER=traders/Round3/candidates/round3_maximal_multi_product_v01.py PERSIST=1
  ```

## Success criterion for the dry-run

- Both traders run to completion on `round2` without raising.
- The `round3_maximal_multi_product_v01` trader produces **zero non-empty
  order dicts** on Round 2 days (because it no-ops on all Round-1/2 symbols).
- The baseline produces zero orders trivially.

That is the only empirical claim this sprint is entitled to make.
