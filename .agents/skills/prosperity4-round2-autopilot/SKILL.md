---
name: prosperity-4-round2-autopilot
description: Use this skill when one Codex chat should run the whole Round 2 loop: read assumptions, inspect the alpha registry, discover or refine alphas, build the best next trader change, analyze resulting logs, update the registry, and state the next iteration.
---

# Prosperity 4 Round 2 Autopilot

## Mission
Own the **end-to-end Round 2 workflow** in one chat.

This skill may do the work that would otherwise be split across:
- alpha finding,
- strategy building,
- log analysis,
- validation handoff.

Use it when you explicitly want one chat to run the whole loop.

## Scope
This skill may:
- read assumptions and Round 2 context,
- maintain the Round 2 alpha registry,
- rank and deduplicate alphas,
- implement one Round 2 trader change,
- inspect local or official logs,
- decide the next iteration.

It should still keep the stages separate in reasoning and outputs.

## Mandatory order of operations
### 1. Read the current truth set
Read if present:
- `prosperity-research/01_assumptions/current_assumptions.md`
- `prosperity-research/04_signal_notes/round2_alpha_registry.md`
- `prosperity-research/04_signal_notes/latest_signal_ranking.md`
- `prosperity-research/05_execution_risk/latest_execution_risk_report.md`
- `prosperity-research/06_validation/latest_validation_report.md`
- Round 2 trader baseline and latest Round 2 runs.

### 2. Refresh the alpha picture
Determine:
- which Round 2 alphas are already known,
- which are duplicates,
- which are unbuilt,
- which are disproven,
- which one best deserves the next iteration.

### 3. Build one dominant change
Implement the smallest defensible Round 2 change.
Do not stack multiple unrelated ideas.

### 4. Analyze evidence
After code changes, inspect the relevant local artifacts or specify the exact next validation command.
If logs are available, perform a compact diagnosis.

### 5. Update the alpha registry
Always update:
- the chosen alpha status,
- any new nearby alpha you became aware of,
- duplicates and rejections,
- linked trader or report.

### 6. Finish with a clean handoff
State:
- what changed,
- what alpha it corresponds to,
- what evidence supports it,
- what should be tested next,
- whether the next chat should be alpha-finding, strategy-building, or log-analysis.

## Alpha-registry rule
Registry path:
- `prosperity-research/04_signal_notes/round2_alpha_registry.md`

If absent, create it with the shared schema used by the other Round 2 skills.
Deduplicate aggressively.

## Round 2 defaults
Start from:
- ASH and Pepper only unless current assumptions add more,
- Round 2 datasets and runs by default,
- `bid()` exists for MAF only,
- local backtests are useful but not authority for the blind-auction acceptance mechanism.

## Anti-patterns
Do not:
- merge broad alpha mining and code edits into an unstructured blob,
- forget registry updates,
- redo a known rejected alpha without explicit new evidence,
- let one lucky run override weak structure.

## Output contract
Always produce:
1. stage-by-stage summary,
2. registry updates made,
3. code or report changes made,
4. exact next validation step,
5. recommendation for the next chat mode if another chat continues the loop.
