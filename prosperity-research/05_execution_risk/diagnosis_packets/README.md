# 05_execution_risk/diagnosis_packets

Purpose: keep compact per-run diagnosis bundles that are small enough to feed
back into AI tools after a local validation run.

Expected inputs: persisted run artifacts from `prosperity_rust_backtester/runs/`
plus the matching validation summary in `prosperity-research/06_validation/`.

Expected outputs: one packet directory per analyzed run containing
`diagnosis_packet.md`, `worst_timestamps.csv`, `inventory_summary.csv`, and
`fill_summary.csv`.

Naming conventions: use a stable packet id derived from run label and timestamp,
for example `<packet_id>/diagnosis_packet.md`.

Classification: canonical stage artifact directory.
