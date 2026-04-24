---
name: prosperity-4-competitive-orchestrator
description: Coordinate the full Prosperity 4 skill suite into one winning workflow. Decides which skill runs first, when to stop exploring, when to promote a variant, when to reject, and how to preserve current best while exploring aggressively. Maintains research discipline under time pressure and prevents local-optimum tunnel vision.
---

# Prosperity 4 Competitive Orchestrator

## Mission
Turn this repository into a systematic research↔implementation↔validation machine and decide, at every branch point, which skill to call and what to do with its output. The orchestrator is the only skill that is allowed to reason about *strategy-of-strategy*: when a rabbit hole should be abandoned, when a structural bet is worth pausing small tweaks, and when to ship.

## When to invoke
- At the start of every round.
- At the start of every work session within a round.
- Whenever the user asks "what should we do next?".
- After any major decision (ship, reject, big-idea abandonment).
- Before the submission deadline (final readiness check).

## Required reading on invocation
1. `prosperity-research/01_assumptions/current_assumptions.md`.
2. `prosperity-research/04_signal_notes/roundN_alpha_registry.md`.
3. `prosperity-research/04_signal_notes/latest_signal_ranking.md`.
4. `prosperity-research/05_execution_risk/latest_execution_risk_report.md`.
5. `prosperity-research/06_validation/latest_validation_report.md`.
6. Current-best trader pointer (see "Current best discipline" below).

If any of these are missing, invoke the relevant skill to produce them before making any orchestration decision.

## Canonical workflow (standard loop)
The default iteration proceeds in this exact order. Stages may be skipped only with a recorded reason.

| # | Stage | Skill | Input | Output | Pass/Fail condition | Next |
|---|---|---|---|---|---|---|
| 1 | Context ingestion | `prosperity-4-round-context-ingestor` | briefing, official docs | `current_assumptions.md` | all products, limits, unknowns recorded | 2 |
| 2 | Data forensics | `prosperity-4-data-forensics` | assumptions, CSVs | `data_forensics_report.md` | coverage tables and sanity checks populated | 3 |
| 3 | Product classification | `prosperity-4-product-classifier` | forensics | `roundN_product_classification.md` | every product labeled with confidence | 4 or 4a |
| 3a | Voucher specification | `prosperity-4-derivatives-voucher-analyst` | assumptions, forensics | `roundN_voucher_spec.md` | parity ladder + settlement confirmed | 4 |
| 4 | Hypothesis generation & pre-registration | `prosperity-4-alpha-hypothesis-lab` | classification, voucher spec | updated alpha registry, top-5 list | ≥1 alpha with all template fields filled | 5 |
| 5 | Implementation planning | `prosperity-4-implementation-planner` | top alpha | `<date>_<alpha>_plan.md` | plan template complete and validation commands runnable | 6 |
| 6 | Code implementation | executing coding agent (Codex/Claude Code) | plan | new trader variant | variant file created; plan acceptance criteria runnable | 7 |
| 7 | Backtest audit | `prosperity-4-backtest-auditor` | candidate run, baseline run | `latest_validation_report.md` verdict | SHIP / FLAG / REJECT | 8 |
| 8 | Inventory audit | `prosperity-4-inventory-risk-controller` | candidate run | inventory audit | pass/flag/fail | 9 |
| 9 | Microstructure audit | `prosperity-4-microstructure-engineer` | candidate run | `latest_execution_risk_report.md` | signal vs executed PnL decomposed | 10 |
| 10 | Promotion or rejection | orchestrator | audits | current-best update or rejection | see decision tree | 11 |
| 11 | Manual challenge modeling | `prosperity-4-manual-game-theorist` | manual briefing | decision memo | EV/worst-case/regret recorded | 12 |
| 12 | Submission readiness check | orchestrator | current-best trader + manual memo | go/no-go | see submission checklist | end |

Stages 1–3a are run only when something changed (new round, new data, new voucher rules). The hot loop is 4–10 plus 11 in parallel. Stage 12 is final.

## Decision tree
### After backtest-auditor returns:
- SHIP and inventory PASS and microstructure PASS → promote to current best; update registry; return to stage 4 to pick the next alpha.
- SHIP but inventory FLAG or microstructure FLAG → do NOT promote; loop back to stage 5 with a plan addressing the flag.
- REJECT and cause is "inside noise" → raise rejection bar for this alpha family; park the alpha (`parked`) and pick a different family.
- REJECT and cause is "leakage" → falsify the alpha (`rejected`); update registry.
- REJECT and cause is "comparability invalid" → rerun the candidate and baseline with matched flags; do not treat as a strategy failure.
- BLOCK (determinism or leakage suspected) → stop building; fix the blocker first.

### When to stop exploring one idea
Stop when any of:
- Two consecutive REJECTs at different parameter values.
- Inventory audit fails for reasons inherent to the mechanism (not fixable without changing the mechanism).
- Microstructure engineer shows the gain is fill-model-assisted.
- Better-ranked alpha exists in the registry and has not been built.

### When to pause small tweaks
Pause tweaking the current best when any of:
- A structural opportunity exists (new product unaddressed, voucher family unmodeled, manual round unbuilt).
- Marginal PnL gains per iteration are smaller than the noise floor over three iterations.
- The remaining time budget is long enough to attempt a structural bet.

### When to ship
Ship a variant as current best only when:
- Backtest-auditor verdict is SHIP.
- Inventory audit is PASS.
- Microstructure audit shows non-trivial signal PnL distinct from executed PnL inflation.
- The variant survives determinism (two runs match).
- The variant is tested on all available days for the active round.
- No leakage flag is open.

## Current best discipline
Maintain a single pointer file: `prosperity-research/10_experiment_logs/current_best.md`.

Fields:
- `trader_path`,
- `round`,
- `commit` (git rev),
- `promoted_on` (ISO date),
- `promoted_by_audit_id`,
- `known_risks` (inventory flags, microstructure flags carried forward),
- `validated_on_datasets`.

Rules:
- Only update after a SHIP with all cross-audits passing.
- Never overwrite without archiving the prior pointer under `archive/`.
- The current-best trader is the only file that is considered submission-ready.

## Time-budget discipline
Under a 48- or 72-hour round:
- First 10% of time: stages 1–3a (context lock).
- Next 30%: stages 4–7 on one or two top hypotheses.
- Middle 30%: parallel structural exploration + manual round modeling.
- Last 20%: consolidation, determinism, submission readiness.
- Last 5%: freeze the current best, run the submission checklist, submit.

Do not spend the last 20% trying new ideas. The current best's determinism and submission compatibility are more valuable than one more tweak.

## Submission readiness checklist (stage 12)
Required before submission:
1. `current_best.md` points to an actual file that exists.
2. That file has the correct return shape `(orders, conversions, traderData)`.
3. `bid()` is present if and only if we want it for the current round; it does not reach into `run()` mutable state.
4. All product symbols used match `state.order_depths` keys exactly (verified by a dry-run against the dataset).
5. `traderData` stays under 50,000 characters across the full run.
6. No imports outside the hosted-allowed set.
7. Two consecutive runs produce identical metrics.
8. Per-day PnL on all available round days is known.
9. Per-product PnL decomposition is known.
10. Inventory audit pass recorded.
11. Microstructure audit recorded.
12. Manual round memo recorded and separately submitted via the UI.

## Anti-patterns the orchestrator must actively prevent
- Chaotic edits directly on a working baseline.
- Chasing a single lucky one-day PnL jump.
- Abandoning structural opportunities because small tweaks feel faster.
- Using tutorial data to validate live-round variants.
- Tuning parameters until a backtest passes (overfit).
- Mixing manual and algo reasoning in the same code path.
- Shipping a variant that no one audited.
- Letting the alpha registry become a graveyard of re-proposals.

## Research log discipline
After every major orchestrator decision, append one entry to `prosperity-research/10_experiment_logs/orchestrator_log.md` with:
- timestamp,
- stage transition (e.g. "stage 7 → stage 10 REJECT because fill-model slack"),
- links to the evidence artifacts,
- next planned stage.

This is the decision trail. Do not skip it.

## Example invocation prompts
- "Use prosperity-4-competitive-orchestrator to decide the next action for Round 3 now that the context ingestor has run."
- "Use prosperity-4-competitive-orchestrator to run the submission readiness checklist against the current best trader and list any blockers."
- "Use prosperity-4-competitive-orchestrator to reallocate effort: we have 12 hours left and three unbuilt alphas versus one tweak candidate."

## Concrete deliverable format
Every orchestrator invocation produces:
1. Current state snapshot (which skills have fresh outputs, which are stale).
2. Decision for the next action with explicit skill to call next.
3. Log entry appended to `orchestrator_log.md`.
4. If a promotion/rejection happened, updated `current_best.md` and alpha registry.

## Integration
- Consumes: outputs from every other skill.
- Feeds: the next skill in the workflow; the log; the current-best pointer.
- Does not directly edit trader code; delegates via `prosperity-4-implementation-planner` to an executing coding agent.
