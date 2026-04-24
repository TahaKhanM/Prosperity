# Round 2 Post-Builder Research Plan

Date: 2026-04-19

Scope: second-wave Round 2 alpha research for the dedicated alpha-finder
instance after the first strategy-builder loop failed to beat the named
baseline on the current local validation surface.

This plan is deliberately research-first.
It does not own trader implementation except for tiny analysis helpers if
strictly necessary.

## Starting Point

### What the strategy-builder results imply

Current builder evidence is not “the Pepper thesis is false.”
What it currently shows is narrower:

- the named baseline under the current explicit `-1/0/1` non-carry local Round
  2 surface is already an extremely strong Pepper carry baseline
- `round2_pepper_dynamic_fair_v01.py` under-carried relative to that surface
  and lost badly
- `round2_pepper_dynamic_fair_v02.py` moved Pepper inventory back toward the
  baseline carry shape, recovered most of the loss, but still finished about
  `-1.29%` behind baseline
- Ash stayed unchanged, so the whole observed gap lives in Pepper monetization
  versus a carry-saturated baseline
- the current blocker is therefore not “missing any Pepper idea at all,” but:
  - whether the validation surface is the right success surface
  - whether the baseline already saturates the obvious local Pepper trade
  - whether the remaining EV sits outside the builder’s current Pepper family

### High-level inference from the blocker

The blocker pivots the research away from broad “stronger Pepper dynamic fair”
iterations and toward four concrete questions:

1. Is the current local success surface misaligned with real Round 2
   differentiators, especially MAF / extra-flow access?
2. Is the baseline already almost maximally harvesting the obvious official-80
   Pepper carry on the local default surface?
3. If yes, is the remaining EV mostly in:
   - quote quality / monetization,
   - state gating,
   - Ash execution overlays,
   - MAF-aware strategy selection,
   - or validation-surface redesign?
4. Which current registry items are too coarse and need to be split,
   downgraded, or marked as locally saturated?

## Repo Reality Confirmed For This Pass

### Guidance and official context

- Root guidance: `AGENTS.md`
- Strategy-workspace guidance: `prosperity_rust_backtester/AGENTS.md`
- Current assumptions: `prosperity-research/01_assumptions/current_assumptions.md`
- Official context remains under `Prosperity Context/` and
  `Prosperity Context/Unrefined Context/`

### Prior Round 2 research

- `prosperity-research/04_signal_notes/round2_research_plan.md`
- `prosperity-research/04_signal_notes/round2_analyzer_audit.md`
- `prosperity-research/04_signal_notes/round2_alpha_report.md`
- `prosperity-research/04_signal_notes/round2_alpha_registry.md`
- `prosperity-research/04_signal_notes/round2_carryover_report.md`
- `prosperity-research/04_signal_notes/round2_strategy_candidates.md`
- Round comparison CSVs already exist and should be reused, not recreated
  blindly

### Strategy-builder artifacts

- `prosperity-research/06_validation/round2_strategy_build_plan.md`
- `prosperity-research/06_validation/round2_validation_surface.md`
- `prosperity-research/06_validation/round2_baseline_snapshot.md`
- `prosperity-research/06_validation/current_candidate_note.md`
- `prosperity-research/06_validation/current_diagnosis_packet.md`
- `prosperity-research/06_validation/round2_progress_log.md`
- `prosperity-research/06_validation/round2_blocker_report.md`

### Candidate / baseline inspection surface

- Baseline actual path in repo:
  `prosperity_rust_backtester/traders/Round 2/baseline.py`
- Candidate paths:
  - `prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_dynamic_fair_v01.py`
  - `prosperity_rust_backtester/traders/Round2/candidates/round2_pepper_dynamic_fair_v02.py`
- Shared workflow helper:
  `prosperity_rust_backtester/scripts/workflow_common.py`

Note:
- the prompt named `baseline.py` at repo root, but the actual file is under the
  legacy `traders/Round 2/` path
- this is now resolved and is not a blocker

### Available Round 2 role support

Repo-local Round 2 research support is available and should be used where it
helps:

- alpha-finder skill:
  `.agents/skills/prosperity4-round2-alpha-finder/`
- log-analysis skill:
  `.agents/skills/prosperity4-round2-log-analyst/`
- role configs:
  `.codex/agents/alpha_miner.toml`
  `.codex/agents/log_analyst.toml`
  `.codex/agents/execution_risk.toml`

Plan for their use in this pass:

- use the alpha-finder workflow to prevent naive rediscovery of already-known
  Round 2 ideas
- use the log-analysis workflow to decompose whether the builder failure is
  really alpha failure, monetization failure, or surface mismatch
- do not use the strategy-builder or autopilot roles because this instance is
  explicitly not the builder

## Hypotheses Now Weakened Or Stale

These should not be revisited naively in this pass:

### Weakened by builder evidence

- `Pepper dynamic fair residual mean reversion` as a direct local baseline
  replacement on the current explicit-day surface
  - still structurally real
  - no longer enough by itself to justify “top next build” without a new
    monetization or validation-surface argument

- `Pepper soft-limit recycle` as a likely local winner
  - current evidence says it sacrifices too much carry on the dominant local
    surface

- `Pepper same-trade-better-thresholds` variants
  - likely to converge back toward the baseline’s near-max-long carry shape
  - should be treated as low-novelty until proven otherwise

### Previously weak and still stale

- standalone OFI alpha in either product
- exact Pepper session hardcoding
- trend-following Ash fair drift
- generic “more Pepper signal complexity” without a distinct monetization path

## New Top-Priority Research Questions

### 1. Validation-surface question

Is the explicit local `-1/0/1` non-carry Round 2 surface the right primary
success surface for a Round 2 trader at all?

Subquestions:

- Does it systematically miss the round’s actual differentiator: accepted MAF
  extra-flow access?
- Is it too narrow and too dominated by baseline Pepper carry to rank
  candidate quality honestly?
- What should become the primary research surface and what should remain the
  secondary safety surface?

### 2. Baseline-saturation question

Has the baseline already almost saturated the obvious local Pepper carry /
residual taker trade under the official `80` limit?

Subquestions:

- Is the remaining local headroom too small for honest `>10%` wins?
- Are current Pepper candidates just the same trade with slightly different
  fair logic and inventory shape?
- Does any real orthogonal EV remain inside Pepper on the local default stream?

### 3. Missed-alpha / monetization-gap question

If the obvious Pepper trade is locally saturated, where is the next EV most
likely to come from?

Main candidates to investigate:

- quote-EV gating / quote-quality alpha
- regime-conditioned Pepper participation
- state-conditioned inventory target logic
- Ash execution overlays that were underweighted in the first wave
- MAF / extra-flow sensitivity and strategy selection
- builder-surface metrics that hide realized-execution improvement

## Files, Scripts, And Analyzer Sections To Use

### Required read / audit surface

- `current_assumptions.md`
- all listed Round 2 research artifacts
- all listed strategy-builder validation artifacts
- baseline and `v01` / `v02` candidate files

### Analyzer and data surface

- analyzer code:
  `prosperity-research/03_eda/round1/analysis.py`
- analyzer README:
  `prosperity-research/03_eda/round1/README.md`
- by-round curated exports under:
  `prosperity-research/03_eda/round1/ai_strategy_context_by_round/`
- canonical raw Round 2 data:
  `prosperity_rust_backtester/datasets/round2/`

### Most relevant analyzer sections for this pass

- Section 3: spread and edge calibration
- Section 5: signal predictiveness
- Section 8: spike detection
- Section 10: inventory-risk simulation
- Section 13: extended microstructure
- Section 14: conditional returns by state bucket
- Section 15: regime segmentation
- Section 16: execution quality and markout
- Section 17: cross-day robustness
- Section 19: feature relevance

These sections matter more now than product-classification rediscovery.

### Validation / diagnosis scripts to inspect or reuse

- `prosperity_rust_backtester/scripts/run_harness.py`
- `prosperity_rust_backtester/scripts/diagnostics/candidate_vs_baseline_report.py`
- `prosperity_rust_backtester/scripts/diagnostics/extract_diagnosis_packet.py`
- `prosperity_rust_backtester/scripts/workflow_common.py`

## Whether The Analyzer Needs Extensions

Default assumption:
- do not extend the analyzer unless the current analysis surface cannot answer
  the post-builder questions directly

Likely minimal extension targets if needed:

- baseline-vs-candidate state tables by product and regime
- “same trade / same state, different monetization” diagnostics
- a crude proxy for whether extra quotes would matter in a given state
- clearer split between predictive signal and realized execution edge

Decision rule:

- if existing analyzer outputs plus validation artifacts are enough, do not
  touch `analysis.py`
- if they are not, add one small comparison-oriented extension only

If changes are needed, document them in:
- `prosperity-research/04_signal_notes/round2_postbuilder_analyzer_extensions.md`

## Artifacts To Write In This Pass

### Phase 0

- `prosperity-research/04_signal_notes/round2_postbuilder_research_plan.md`

### Phase 1

- `prosperity-research/04_signal_notes/round2_postbuilder_feedback_audit.md`

### Phase 2

- `prosperity-research/04_signal_notes/round2_validation_surface_audit.md`

### Phase 3 / 4

- optional targeted helper tables or CSVs under
  `prosperity-research/04_signal_notes/`
- `round2_postbuilder_analyzer_extensions.md` only if analyzer changes are
  actually necessary

### Phase 5

- update `prosperity-research/04_signal_notes/round2_alpha_registry.md`

### Phase 6

- `prosperity-research/04_signal_notes/round2_postbuilder_alpha_report.md`
- `prosperity-research/04_signal_notes/round2_missing_alpha_hypotheses.md`
- `prosperity-research/04_signal_notes/round2_builder_next_steps.md`

### Phase 7

- `prosperity-research/04_signal_notes/round2_research_verdict.md`

## How This Pass Avoids Duplicating Known Alpha Work

### 1. Start from the current registry, not from brainstorming

- read the existing `round2_alpha_registry.md` first
- treat each existing alpha as something to confirm, split, downgrade, reject,
  or mark unresolved
- do not create fresh names for the same Pepper dynamic-fair family unless the
  monetization path is genuinely different

### 2. Explicitly separate “same signal, different monetization”

Do not keep these bundled:

- Pepper dynamic fair residual mean reversion
- Pepper carry saturation behavior
- Pepper quote-EV gating
- Pepper state-conditioned inventory discipline

Those are now distinct registry lines because the builder evidence split them.

### 3. Use blocker evidence as a stale-idea filter

Any idea that is just:

- “Pepper, but with slightly different fair smoothing”
- “Pepper, but carry a bit less”
- “Pepper, but carry a bit more”

should be treated as low novelty unless the evidence shows it targets a
different failure mode than `v01` / `v02`.

### 4. Keep Ash and Pepper roles separate

- Pepper may be locally saturated on the obvious carry trade
- Ash may still have underexplored execution EV
- do not let “Pepper is strongest structurally” suppress investigation into Ash
  monetization overlays

## Milestone Order

1. Audit the builder feedback and write what it proved versus what it did not.
2. Audit the validation surface against official Round 2 mechanics and local
   tool limits.
3. Search for missed alphas specifically in monetization, state selection,
   Ash overlays, and MAF-sensitive effects.
4. Extend the analyzer only if the current surfaces cannot answer those
   questions.
5. Split and update the alpha registry based on post-builder evidence.
6. Write a compact handoff package back to the strategy-builder.
7. Force a decisive verdict on whether the blocker is:
   missing alpha, monetization failure, validation-surface mismatch, or some
   combination.

## Success Criteria For This Pass

This pass is successful only if it ends with:

- a written audit of what the builder loop actually proved
- an explicit decision on whether the current local surface is trustworthy
- at least one of:
  - genuinely new remaining alpha families,
  - meaningful registry downgrades / splits,
  - or a strong case that the current optimization target is wrong
- a builder handoff that names non-redundant next directions rather than
  “more Pepper dynamic fair”
- a decisive final verdict file that does not leave the main blocker ambiguous

## Immediate Next Actions

1. Read and classify the strategy-builder artifacts into:
   alpha failure, monetization failure, inventory-shape mismatch,
   validation-surface mismatch, baseline saturation, or combination.
2. Audit the validation surface against official Round 2 MAF mechanics and the
   local backtester’s inability to model `bid()` / extra-flow access.
3. Build a post-builder alpha inventory update centered on:
   quote-EV gating, regime/state logic, Ash execution overlays, and
   MAF-sensitive strategy selection.
