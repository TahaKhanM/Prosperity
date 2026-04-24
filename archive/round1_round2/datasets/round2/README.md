# datasets/round2

Purpose: canonical Rust local raw-data location for Round 2 backtests.

Expected inputs: official Round 2 raw CSVs copied from `Data/ROUND_2/`.

Expected outputs: the unchanged raw CSV set plus any round-level submission
artifacts the Rust CLI already knows how to consume, such as `submission.log`
or `submission.json`.

Naming conventions: keep the official filenames
`prices_round_2_day_<day>.csv` and `trades_round_2_day_<day>.csv`; keep any
submission artifacts in the existing CLI-expected names.

Source provenance for the raw CSVs in this folder is the top-level
`Data/ROUND_2/` directory. Keep these files byte-for-byte raw.

Classification: canonical local raw-data directory.
