# Prosperity 4 Claude Skills

This repo now carries two tiers of skills:

## Primary suite (round-agnostic, Round 3+ ready)

See `PROSPERITY_4_SKILLS_INDEX.md` for the full pipeline diagram and orchestration rules.

Start with the orchestrator; it tells you which skill to invoke next.

1. `prosperity-4-round-context-ingestor` — assemble/refresh `current_assumptions.md`
2. `prosperity-4-data-forensics` — evidence-only EDA over the round's CSVs
3. `prosperity-4-product-classifier` — label each product with behavior family + falsifiers
4. `prosperity-4-alpha-hypothesis-lab` — generate falsifiable alphas, maintain alpha registry
5. `prosperity-4-microstructure-engineer` — separate signal PnL from executed PnL, detect fill-model slack
6. `prosperity-4-inventory-risk-controller` — audit position paths, loss clusters, drawdowns
7. `prosperity-4-derivatives-voucher-analyst` — voucher/option semantics, parity ladder, settlement
8. `prosperity-4-manual-game-theorist` — formalize auction/budget/biopod problems; decision memo
9. `prosperity-4-backtest-auditor` — SHIP / FLAG / REJECT gatekeeper
10. `prosperity-4-strategy-refactor-engineer` — behavior-preserving refactors only
11. `prosperity-4-implementation-planner` — validated idea → copy-paste build plan
12. `prosperity-4-competitive-orchestrator` — top-level coordinator and decision tree

## Legacy Round 2 skills (kept for reference)

- `prosperity-4-round2-alpha-finder`
- `prosperity-4-strategy-engineer` (a.k.a. `prosperity4-codex-skill`)
- `prosperity-4-round2-log-analyst`
- `prosperity-4-round2-autopilot`

Shared coordination file expected by the legacy skills:
- `prosperity-research/04_signal_notes/round2_alpha_registry.md`

The primary suite maintains a round-scoped registry at
`prosperity-research/04_signal_notes/roundN_alpha_registry.md` and a cross-round
current-best pointer at `prosperity-research/10_experiment_logs/current_best.md`.
