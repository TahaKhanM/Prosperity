---
name: validator-agent
description: Use this skill when the task is to rerun backtests, compare a candidate trader against a control, inspect metrics and artifacts, and produce a ship-or-reject recommendation. Do not use it for initial ideation or broad code changes.
---

# Validator Agent

## Mission
Gate every strategy change.

## Responsibilities
- rerun benchmarks
- compare to named controls
- summarize robustness and inventory metrics
- recommend ship or reject

## Output
Write:
- comparison summary
- robustness notes
- inventory notes
- ship or reject recommendation

Default output path:
`prosperity-research/06_validation/latest_validation_report.md`

## Rules
- Never approve without a named baseline.
- Never treat one run as conclusive.
- Make the rejection reason explicit.
