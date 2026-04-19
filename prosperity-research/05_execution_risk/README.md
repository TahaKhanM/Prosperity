# 05_execution_risk

Purpose: store post-validation diagnosis artifacts covering fill quality,
inventory behavior and counterfactual quote studies.

Expected inputs: candidate-vs-baseline validation results, persisted run
artifacts and official log analysis exports when available.

Expected outputs: dated diagnosis notes and supporting figures in the leaf
directories below this folder.

Naming conventions: use `YYYY-MM-DD_<topic>.md` and
`YYYY-MM-DD_<topic>_<view>.png`. Use `latest_<topic>.md` only where that naming
pattern is already maintained.

Classification: canonical stage artifact directory.

Existing loose top-level files remain valid historical material. New work should
go into the leaf directories.
