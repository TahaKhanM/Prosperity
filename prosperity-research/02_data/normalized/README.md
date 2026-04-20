# 02_data/normalized

Purpose: store canonical normalized datasets produced from raw market data,
submission payloads or official log extracts.

Expected inputs: raw CSVs, extracted payloads and source metadata from
`prosperity-research/02_data/manifests/`.

Expected outputs: normalized Parquet datasets ready for feature generation and
EDA.

Naming conventions: use `<round>_<day>_<source>.parquet`.

Classification: canonical stage artifact directory.
