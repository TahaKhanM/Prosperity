# Round 4 trader variants

This folder is the active workspace for Round 4 trader iteration. Round 3
traders under `prosperity_rust_backtester/traders/Round3/candidates/`
remain available: `v15.py` is the strongest R3 baseline and is the
recommended starting point for porting to Round 4 (the products and
position limits are unchanged; only the counterparty fields are new).

## Files in this folder

| File | Purpose |
|---|---|
| `round4_no_trade_baseline.py` | Returns no orders. Smoke-test target for `make round4 TRADER=traders/Round4/round4_no_trade_baseline.py`. Confirms Round 4 dataset wiring. |
| `round4_mark_observer.py` | Observation-only trader: reads `trade.buyer` / `trade.seller`, accumulates a per-product Mark-aware lean signal in `traderData`. No orders. Useful for confirming counterparty IDs reach trader code. |

## Recommended iteration plan

The full plan lives in
`prosperity-research/08_playbooks/round4_strategy_playbook.md`. Short version:

1. `round4_no_trade_baseline.py`: verify dataset wiring (this file).
2. `round4_mark_observer.py`: verify Mark IDs reach trader code (this file).
3. **`round4_baseline_v01.py`** (NOT yet built): port `Round3/candidates/v15.py`
   1:1 into `Round4/`. Confirm it matches its R3 PnL on the R4 dataset
   within ±5 %.
4. **`round4_mark_lean_v01.py`** (NOT yet built): add the Mark-lean overlay
   on top of v01's HYDROGEL and VE quote logic. Single dominant change.
5. **`round4_mark_lean_v02.py`**: extend the lean to E1 (deep-ITM as VE
   capacity).
6. **`round4_mark_lean_v03.py`**: tune the lean half-life and per-unit
   weight via a parameter sweep.

Each iteration should:
- Have a named baseline (the previous variant).
- Make exactly one dominant change.
- State the validation step (`make round4 TRADER=... DAY=all` + a delta on
  the metrics.json `pnl_total`).
- Preserve `(orders, conversions, traderData)` return shape.

## Data wiring sanity check

After running any trader against `--dataset round4`, inspect
`runs/<run_id>/combined.log` and grep for `"buyer":"Mark`. If you see
non-`None` strings, the counterparty fields are flowing through correctly.

## Do not

- Ship logic from `archive/round1_round2/` into Round 4 traders.
- Modify the Round 3 trader files in-place. Copy them into Round 4 first.
- Hardcode HYDROGEL fair value at 10000: empirical mean is 9992–10003;
  use a soft anchor `clamp(EMA, 9980, 10010)`.
- Trust counterparty time-of-day patterns: R4 EDA shows weak temporal
  structure (peak hour-bucket share ≤ 14 %).
