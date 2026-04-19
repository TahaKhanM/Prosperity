# 06_validation

Purpose: store baseline snapshots and candidate-vs-baseline validation writeups
for implemented strategy changes.

Expected inputs: implementation outputs from `prosperity_rust_backtester/`,
benchmark baselines, and persisted run artifacts.

Expected outputs: baseline notes and candidate comparison decisions in the leaf
directories below this folder.

Naming conventions: use `YYYY-MM-DD_<baseline>.md`,
`YYYY-MM-DD_<candidate>_vs_<baseline>.md`, and `latest_<topic>.md` only for
maintained rolling summaries.

Classification: canonical stage artifact directory.

Existing loose top-level files remain valid historical material. New work should
go into the leaf directories.
