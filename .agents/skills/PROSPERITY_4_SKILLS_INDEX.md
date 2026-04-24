# Prosperity 4 Winning Skills Suite — Index

All skills live under `.agents/skills/prosperity4-<slug>/SKILL.md` and follow the same frontmatter pattern (`name:`, `description:`). They are designed to work as one pipeline, coordinated by `prosperity-4-competitive-orchestrator`.

## Pipeline at a glance

```
[round-context-ingestor] -> [data-forensics] -> [product-classifier]
                                              -> [derivatives-voucher-analyst]  (when vouchers exist)
   -> [alpha-hypothesis-lab]
   -> [implementation-planner]
   -> (coding agent implements new trader variant)
   -> [backtest-auditor]  +  [inventory-risk-controller]  +  [microstructure-engineer]
   -> promote / reject  (decided by [competitive-orchestrator])

[manual-game-theorist]  runs in parallel on the manual challenge.
[strategy-refactor-engineer]  runs whenever code hygiene blocks the pipeline.
[competitive-orchestrator]  is invoked at every decision point.
```

## Skill list

| Skill | Role | When to invoke |
|---|---|---|
| [prosperity-4-round-context-ingestor](./prosperity4-round-context-ingestor/SKILL.md) | Fact assembler. Locks the current round's products, limits, rules, unknowns. | Start of every round; briefing changes. |
| [prosperity-4-data-forensics](./prosperity4-data-forensics/SKILL.md) | Evidence-only EDA. Coverage, spreads, depth, trade intensity, day-vs-day deltas. | After new data lands; after any run audit. |
| [prosperity-4-product-classifier](./prosperity4-product-classifier/SKILL.md) | Labels each product's behavior family with confidence and falsifiers. | After fresh forensics; after regime flag. |
| [prosperity-4-derivatives-voucher-analyst](./prosperity4-derivatives-voucher-analyst/SKILL.md) | Voucher/option specification, parity, settlement. | When vouchers are active. |
| [prosperity-4-alpha-hypothesis-lab](./prosperity4-alpha-hypothesis-lab/SKILL.md) | Generates falsifiable hypotheses; maintains alpha registry. | After classification; on registry refresh. |
| [prosperity-4-microstructure-engineer](./prosperity4-microstructure-engineer/SKILL.md) | Separates signal PnL from executed PnL; flags fill-model slack. | On any variant under audit. |
| [prosperity-4-inventory-risk-controller](./prosperity4-inventory-risk-controller/SKILL.md) | Audits position paths, loss clusters, tail-driven PnL. | On any variant under audit. |
| [prosperity-4-backtest-auditor](./prosperity4-backtest-auditor/SKILL.md) | Ship/reject gatekeeper vs a named baseline. | Before any promotion. |
| [prosperity-4-strategy-refactor-engineer](./prosperity4-strategy-refactor-engineer/SKILL.md) | Behavior-preserving code hygiene. | When submission compatibility or determinism is at risk. |
| [prosperity-4-implementation-planner](./prosperity4-implementation-planner/SKILL.md) | Turns a validated idea into a copy-paste-ready build plan. | After a hypothesis is pre-registered and ranked. |
| [prosperity-4-manual-game-theorist](./prosperity4-manual-game-theorist/SKILL.md) | Formalizes manual rounds as games; produces decision memo. | Whenever a manual challenge is active. |
| [prosperity-4-competitive-orchestrator](./prosperity4-competitive-orchestrator/SKILL.md) | Decides which skill runs next; runs submission readiness. | At every decision point; first on every session. |

## Existing complementary skills (kept)

| Skill | Keep because |
|---|---|
| `prosperity-4-strategy-engineer` (`prosperity4-codex-skill/`) | Round 2 strategy-builder. The new suite supersedes it for Round 3+; keep for archived Round 2 workflow. |
| `prosperity-4-round2-alpha-finder` | Round 2 alpha mining; subset of new alpha-hypothesis-lab. |
| `prosperity-4-round2-log-analyst` | Round 2 log analysis; subset of new microstructure + backtest-auditor. |
| `prosperity-4-round2-autopilot` | Single-chat end-to-end Round 2 loop; superseded by orchestrator for Round 3+. |

The new suite is round-agnostic; the older Round 2 skills are kept intact and not modified.

## Source hierarchy reminder

1. Official written Prosperity docs (`Prosperity Context/Unrefined Context/`).
2. In-session briefing from the user (treat as official when explicitly stated).
3. `Prosperity Context/00_PROSPERITY_CONTEXT_OVERVIEW.md` summaries.
4. Narrative / uplink / transcript material.
5. Older round notes and prior public repos (reference only).

Never let a lower-tier source override a higher-tier one.

## Research layout used by these skills

- `prosperity-research/01_assumptions/current_assumptions.md`
- `prosperity-research/03_eda/roundN/data_forensics_report.md`
- `prosperity-research/04_signal_notes/roundN_product_classification.md`
- `prosperity-research/04_signal_notes/roundN_voucher_spec.md`
- `prosperity-research/04_signal_notes/roundN_alpha_registry.md`
- `prosperity-research/04_signal_notes/latest_signal_ranking.md`
- `prosperity-research/05_execution_risk/latest_execution_risk_report.md`
- `prosperity-research/05_execution_risk/inventory/<date>_<variant>_inventory_audit.md`
- `prosperity-research/06_validation/latest_validation_report.md`
- `prosperity-research/07_manual_round/roundN_<task>/decision_memo.md`
- `prosperity-research/10_experiment_logs/current_best.md`
- `prosperity-research/10_experiment_logs/orchestrator_log.md`
- `prosperity_rust_backtester/traders/RoundN/<variant>.py`
- `prosperity_rust_backtester/runs/<run_id>/...`

## Recommended first command of a new round

```
Use prosperity-4-competitive-orchestrator to plan the next action: we just entered Round 3 (Salvinar).
Check current_assumptions.md, and if stale, invoke prosperity-4-round-context-ingestor first.
```

That call will (a) notice assumptions are stale, (b) run context ingestion, (c) decide whether to go to forensics or directly to the manual solver depending on data availability, and (d) log the decision to `orchestrator_log.md`.
