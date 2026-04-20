# 02_data

Purpose: store canonical data artifacts used by downstream feature generation,
EDA, validation support and diagnosis.

Expected inputs: raw CSVs, submission payloads, official log extracts and
dataset metadata.

Expected outputs: normalized datasets, feature datasets, manifests and schemas
in the leaf directories below this folder.

Naming conventions: use `<round>_<day>_<source>.parquet`,
`<dataset>__<feature_set>.parquet`, `<artifact_name>.manifest.yaml` and
`<artifact_family>.schema.yaml`.

Classification: canonical stage artifact directory.
