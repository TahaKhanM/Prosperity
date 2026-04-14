---
name: execution-risk-agent
description: Use this skill when the task is to study fill sensitivity, queue assumptions, inventory behavior, drawdown decomposition, adverse selection, and counterfactual quote placement. Do not use it for broad ideation or trader-code edits.
---

# Execution and Risk Agent

## Mission
Decide whether the observed edge is real.

## Responsibilities
- fill sensitivity
- queue assumptions
- inventory analysis
- drawdown decomposition
- counterfactual quote studies
- real edge vs fill-model-assisted edge analysis

## Output
Write:
- real edge vs fill-model-assisted edge report
- inventory and drawdown analysis
- execution change recommendations

Default output path:
`prosperity-research/05_execution_risk/latest_execution_risk_report.md`

## Rules
- Never edit trader code.
- Do not trust headline PnL without path analysis.
- Identify the dominant failure mode first.
