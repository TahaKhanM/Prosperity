---
name: prosperity-4-backtest-auditor
description: Audit Prosperity 4 backtest results against a named baseline to prevent false confidence. Checks full-bundle comparability, per-day / per-product decomposition, determinism, leakage, one-day overfit, and noise-vs-signal. Produces SHIP or REJECT verdicts with evidence.
---

# Prosperity 4 Backtest Auditor

## Mission
A backtest does not validate a strategy unless it survives the right comparisons. This skill is the gatekeeper between "looks promising" and "promoted to candidate".

## Trigger conditions
- A candidate variant finished running and the user wants ship/reject judgment.
- Two variants look close and a decision is needed.
- A prior ship decision is being questioned.
- The backtest-auditor is invoked by the orchestrator as part of the standard iteration.

## Required inputs
- Candidate run: `prosperity_rust_backtester/runs/<candidate_id>/` (prefer `--artifact-mode full`).
- Baseline run with a named baseline trader: `prosperity_rust_backtester/runs/<baseline_id>/` generated with the same dataset, same day split, same commit/build, same flags.
- Existing harness: `prosperity_rust_backtester/scripts/run_harness.py`, `scripts/diagnostics/candidate_vs_baseline_report.py`, `scripts/diagnostics/extract_diagnosis_packet.py`.
- `prosperity-research/05_execution_risk/latest_execution_risk_report.md` and inventory audit, if produced.

## Hard rules for valid comparisons
1. Same dataset, same days, same order.
2. Same backtester binary / commit.
3. Same `--artifact-mode`.
4. Same `CARRY` / `FLAT` / `PERSIST` flags.
5. Same trader interface shape on both sides.
6. A baseline must be *named* (trader file path recorded, not "the last one we ran").
7. At least 2 days of data, and ideally all available days, covered.

If any of these fail, the audit verdict is automatic `REJECT - invalid comparison`.

## Step-by-step workflow
### 1. Verify comparability
Check the rules above. Record the verification.

### 2. Determinism check
Run the candidate twice. If run-to-run PnL differs beyond floating-point noise, flag nondeterminism. Require seed or state fix before proceeding.

### 3. Headline comparison
Total PnL, per-day PnL, per-product PnL, own-trade count, inventory summary. Report absolute and relative deltas.

### 4. Day-by-day stability
Did the candidate beat baseline on all days, most days, or just one? One-day improvements that reverse other days are high-overfit risk and default to REJECT unless justified.

### 5. Product-by-product stability
Same question at product granularity. If the gain is concentrated on a single product, check whether the change should have affected that product at all.

### 6. Drawdown and trade count
Compare max drawdown, drawdown duration, and trade count. A candidate that wins PnL while collapsing trade count may be taking fewer, larger bets (higher variance) and should be flagged.

### 7. Noise vs signal
Estimate a noise floor: split baseline by day halves and compute self-variation. Any candidate improvement smaller than the baseline's own intra-day variability is noise. Default to REJECT.

### 8. Sensitivity / parameter check
If the candidate introduces parameters, run 2–3 nearby parameter values. If the improvement only holds at one exact value, flag brittleness.

### 9. Leakage check
Inspect `combined.log` for decisions that appear to use future information (e.g. signal computed at `t` referencing a value from `t+1`). If suspect, block until reproduced or cleared.

### 10. Cross-reference with inventory and microstructure
A variant that passes PnL but fails the inventory audit or has fill-model-slack flags from the microstructure engineer should not ship.

### 11. Verdict
Write SHIP, FLAG, or REJECT. No ship without a positive signal on every mandatory check.

## Verdict table
| Check | Mandatory? | Fail consequence |
|---|---|---|
| Comparability | Yes | REJECT (invalid) |
| Determinism | Yes | BLOCK until fixed |
| Headline PnL improved | Yes | REJECT |
| Day stability | Yes | REJECT unless single-day concentration is explained by the mechanism |
| Product stability | Yes | FLAG at minimum |
| Drawdown not worse | Yes | FLAG or REJECT |
| Noise-vs-signal | Yes | REJECT if inside noise |
| Parameter sensitivity | If new params | FLAG if brittle |
| Leakage | Yes | BLOCK until resolved |
| Inventory audit passes | Yes | REJECT |
| Microstructure audit passes | Yes | REJECT or FLAG |

## Evidence requirements
- Every claim must cite the specific metric value and artifact path.
- Every verdict must link to the specific checks that drove it.
- Keep raw numbers; do not round past two significant figures.

## Failure modes to avoid
- Celebrating a single favorable run.
- Comparing across different dataset subsets.
- Forgetting to regenerate the baseline with the same build.
- Using `metrics.json` as the only source of truth.
- Ignoring inventory and microstructure outputs.
- Treating the candidate trader as "best" because it is the newest file.

## Guardrails
- Never ship a variant without a named baseline and a passing full-bundle comparison.
- Never promote a variant to current-best based on tutorial data only.
- Never overwrite `latest_validation_report.md` without archiving the prior version.

## Example invocation prompts
- "Use prosperity-4-backtest-auditor to compare `traders/Round3/<candidate>.py` vs `traders/Round3/<baseline>.py` on all Round 3 days with PERSIST=1 and produce a ship/reject verdict."
- "Use prosperity-4-backtest-auditor to check whether the voucher addition actually improved anything or just added noise."
- "Use prosperity-4-backtest-auditor to run a two-run determinism check on the current candidate before shipping."

## Concrete deliverable format
Write to `prosperity-research/06_validation/latest_validation_report.md` (archive prior) with:
1. Candidate and baseline references (file paths, commit, dataset, days, flags).
2. Comparability verification.
3. Determinism result.
4. Headline + per-day + per-product decomposition.
5. Noise-vs-signal analysis.
6. Parameter sensitivity (if applicable).
7. Leakage check.
8. Cross-reference to inventory & microstructure verdicts.
9. Verdict: SHIP | FLAG | REJECT, with reasons.
10. Next-step recommendation.

## Integration
- Consumes: run artifacts, inventory audit, microstructure report.
- Feeds: `prosperity-4-competitive-orchestrator` (promotion/rejection), `prosperity-4-alpha-hypothesis-lab` (status updates for alphas).
