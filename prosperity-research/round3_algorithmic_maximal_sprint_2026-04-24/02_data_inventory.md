# Round 3 data inventory — 2026-04-24

Method: enumerate every dataset path under `prosperity_rust_backtester/datasets/`
and `Data/`, then filter for Round 3 symbols.

## Dataset directories present

- `prosperity_rust_backtester/datasets/tutorial/` — populated (Tutorial day `-2`, day `-1`, sample submission).
- `prosperity_rust_backtester/datasets/round1/` — populated (day `-2`, `-1`, `0`, submission).
- `prosperity_rust_backtester/datasets/round2/` — populated (day `-1`, `0`, `1`).
- `prosperity_rust_backtester/datasets/round3/` — **EMPTY placeholder**.
- `prosperity_rust_backtester/datasets/round4/` through `round8/` — empty placeholders.
- `Data/ROUND_1/`, `Data/ROUND_2/`, `Data/TUTORIAL_ROUND_1/` — populated.
- `Data/ROUND_3/` — **does not exist**.

## Round 3 symbols observed in any dataset

None. A literal check for `HYDROGEL_PACKS`, `VELVET_FRUIT_EXTRACT`, or any
`*_VOUCHER_*` string across the populated Round 1 and Round 2 CSVs would find
nothing; those datasets only contain `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
Those two products are explicitly Round 1 / Round 2 and must not be used as
round-specific baselines for Round 3 strategy claims.

## CSV schema confirmed on Round 2 data

Prices CSV header (semicolon-separated):

```
day;timestamp;product;bid_price_1;bid_volume_1;bid_price_2;bid_volume_2;bid_price_3;bid_volume_3;ask_price_1;ask_volume_1;ask_price_2;ask_volume_2;ask_price_3;ask_volume_3;mid_price;profit_and_loss
```

Trades CSV header: `timestamp;buyer;seller;symbol;currency;price;quantity`.

Round 3 CSVs are expected to follow the same schema once IMC releases them.

## Implication

Every data-driven research step (product classifier, data-forensics diagnostic
battery, voucher-underlying correlation, parity-ladder measurement) is BLOCKED
until Round 3 CSVs appear in `datasets/round3/`. Only structural / interface
work can be completed in this sandbox.
