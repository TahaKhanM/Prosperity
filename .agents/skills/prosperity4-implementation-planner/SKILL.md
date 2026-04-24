---
name: prosperity-4-implementation-planner
description: Convert a validated Prosperity 4 research idea into a precise, copy-paste-ready implementation prompt for Codex or Claude Code. Specifies file targets, functions, expected behavior, non-goals, tests, acceptance criteria, rollback, and validation commands. Preserves the current best.
---

# Prosperity 4 Implementation Planner

## Mission
A good research idea still loses PnL if the implementation is vague. This skill is the bridge between a validated hypothesis and a reproducible code change. Output is a fully specified plan a coding agent (Codex or another Claude session) can execute without asking clarifying questions.

## Trigger conditions
- An alpha is `ranked` and ready to be built.
- A microstructure or inventory finding produced a specific code-level remedy.
- A refactor plan is ready to be applied as a build.
- The orchestrator has decided the next build target.

## Required inputs
- `prosperity-research/04_signal_notes/roundN_alpha_registry.md` (with the target alpha).
- `prosperity-research/04_signal_notes/latest_signal_ranking.md` or the specific hypothesis memo.
- `prosperity-research/05_execution_risk/latest_execution_risk_report.md` (execution realism constraints).
- Target trader baseline path.
- Current round assumptions doc.

## Plan template (all fields required)
1. **Title** (imperative, short).
2. **Target alpha_id** and one-line hypothesis.
3. **Baseline trader path** (do not overwrite).
4. **New variant path**: `prosperity_rust_backtester/traders/RoundN/<baseline>_<alpha_slug>_v<NN>.py`.
5. **Files to touch** (only the new variant; never the baseline).
6. **Functions to add / modify** with one-line purpose each.
7. **Exact intended behavior**: for each trigger condition, which orders are placed, at what size, with which guard.
8. **Non-goals**: explicit list of what this change must NOT do (no new params beyond those listed, no unrelated refactor, no touching other products).
9. **State additions**: new `traderData` keys, their types, and serialization notes.
10. **Parameters**: names, defaults, allowed ranges, sensitivity plan.
11. **Tests**: what `make round<N> TRADER=<new_variant>` must show (e.g. per-product PnL delta sign, inventory bound).
12. **Expected metrics to move**: total PnL, per-day PnL, trade count, specific inventory behavior — with direction and approximate magnitude prior.
13. **Acceptance criteria** (must all pass): a checklist the backtest-auditor will run.
14. **Rollback plan**: exact steps to revert if rejected (delete new variant file; leave baseline untouched).
15. **Validation commands** (copy-pasteable):
    - `cd prosperity_rust_backtester`
    - `make round<N> TRADER=traders/RoundN/<new_variant>.py PERSIST=1`
    - plus day-specific and baseline-comparison invocations.
16. **Naming convention for follow-up variants**: `_v02`, `_v03`, etc.

## Step-by-step workflow
### 1. Read the hypothesis in full
Confirm it has a causal mechanism, null, and falsification test. If it does not, bounce back to `prosperity-4-alpha-hypothesis-lab` before planning.

### 2. Decide the minimal change
One dominant mechanism per variant. If two ideas are being considered, produce two plans, not one combined plan.

### 3. Name the variant
Use a slug that encodes the mechanism and version: `ash_wallmid_meanrev_v01`, `vfe_voucher_parity_v01`. No generic names like `newtrader.py`.

### 4. Write the plan
Fill every template field. Omit nothing. Avoid prose; use bullets and code blocks.

### 5. Include validation commands verbatim
Use the actual Makefile targets and flags (`make round1|round2|...|round8`, `TRADER=`, `DAY=`, `PERSIST=1`, `FLAT=1`, `CARRY=1`). Also include the harness and diagnostics:
```
python3 scripts/run_harness.py --trader <new> --baseline <baseline> --dataset datasets/round<N> --artifact-mode full
python3 scripts/diagnostics/extract_diagnosis_packet.py --run runs/<label> --set candidate
python3 scripts/diagnostics/candidate_vs_baseline_report.py --run-root runs/<label>
python3 scripts/reports/update_experiment_registry.py --run-root runs/<label> --hypothesis-tag <alpha_id> --strategy-family-tag <family> --ship-reject-status <pending|reject|ship>
```

### 6. Hand off
Save plan to `prosperity-research/10_experiment_logs/<date>_<alpha_id>_plan.md`. Output the plan inline for immediate paste into the coding agent. Update the alpha registry status to `in_build`.

## Evidence requirements
- Every claimed "expected metric to move" must trace back to a line in the alpha hypothesis.
- Every validation command must be runnable as-is from `prosperity_rust_backtester/`.
- Every acceptance criterion must be a binary check (yes/no), not vibes.

## Failure modes to avoid
- Vague prompts like "improve the Pepper strategy".
- Multi-mechanism plans.
- Plans that edit the baseline instead of creating a new variant.
- Missing rollback steps.
- Plans that rely on conversions (not simulated locally).
- Plans that depend on observations CSVs (not loaded locally).
- Plans that add >2 new parameters without a sensitivity-sweep plan.

## Guardrails
- Never finalize a plan without confirming baseline exists at the given path.
- Never write a plan that touches `traders/Round1/Ash.py` or other known baselines directly (always new variant).
- Never include code in the plan beyond necessary signatures and pseudocode; coding is delegated.
- Never exceed one dominant change per plan.

## Example invocation prompts
- "Use prosperity-4-implementation-planner to write a Codex prompt that builds `R3-VFE-voucher-parity-v01` as a new variant with explicit acceptance criteria."
- "Use prosperity-4-implementation-planner to turn the pepper regime-guard idea into a minimal implementation plan."
- "Use prosperity-4-implementation-planner to convert the inventory-controller finding into a concrete patch plan with a single parameter."

## Concrete deliverable format
A single markdown document at `prosperity-research/10_experiment_logs/<date>_<alpha_id>_plan.md` using the plan template above, also echoed in chat for the executing agent.

## Integration
- Consumes: alpha registry, hypothesis memo, execution-risk report, assumptions.
- Feeds: executing coding agent (Codex / Claude Code), then `prosperity-4-backtest-auditor`.
- Upstream of: code edits in `prosperity_rust_backtester/traders/`.
