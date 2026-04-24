# Round 2 Research Plan

_Created 2026-04-19 for deep alpha research on `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`._

## Objective

Produce a durable, evidence-backed Round 2 research package that:

- verifies official Round 2 facts and local repo behavior separately,
- re-runs and audits the existing analyzer on Round 2 raw data,
- searches broadly for product-specific alpha families without jumping straight
  into trader implementation,
- tests which Round 1 findings actually carry over to Round 2,
- writes a deduplicated alpha inventory and ranked strategy families,
- leaves implementation-ready guidance for the next coding step.

## Repo Reality Confirmed Before Research

### Canonical raw datasets

- Round 1 raw CSVs: `prosperity_rust_backtester/datasets/round1/`
- Round 2 raw CSVs: `prosperity_rust_backtester/datasets/round2/`
- Packaged zip references also exist:
  - `Data/ROUND_1.zip`
  - `Data/ROUND_2.zip`
- Working assumption: the extracted CSVs under
  `prosperity_rust_backtester/datasets/` are the canonical local analysis and
  backtest inputs unless a mismatch with the zip archives is discovered.

### Analyzer surface

- Primary analyzer: `prosperity-research/03_eda/round1/analysis.py`
- Notebook companion: `prosperity-research/03_eda/round1/analysis.ipynb`
- Existing curated export target:
  `prosperity-research/03_eda/round1/ai_strategy_context/`
- Analyzer README confirms `python analysis.py --round round1|round2` as the
  canonical entrypoint and states the export is overwritten per run.

### Validation and backtesting surface

- Primary local validator: `prosperity_rust_backtester/`
- Rust backtester docs: `prosperity_rust_backtester/README.md`
- Repo-local strategy workspace rules:
  `prosperity_rust_backtester/AGENTS.md`
- Secondary tools:
  - `imc-prosperity-4-backtester/`
  - `imc-prosperity-4-visualizer/`
- Operational default: prefer the Rust backtester with explicit trader and
  dataset paths.

### Strategy / candidate trader surface

- Active trader root: `prosperity_rust_backtester/traders/`
- Current live Round 1 trader path present:
  `prosperity_rust_backtester/traders/Round1/Ash.py`
- Historical variants and probes live under `prosperity_rust_backtester/trader_archive/`
- `Trader1/` remains read-only reference only and out of scope unless needed.

### Current research / registry surface

- Existing signal-ranking note:
  `prosperity-research/04_signal_notes/latest_signal_ranking.md`
- Existing execution-risk note:
  `prosperity-research/05_execution_risk/latest_execution_risk_report.md`
- Existing assumptions note:
  `prosperity-research/01_assumptions/current_assumptions.md`
- No dedicated `prosperity-research/04_signal_notes/round2_alpha_registry.md`
  exists yet, so this task will create it.

### Repo-local Round 2 support assets

Local Round 2 skills and role configs are present and should be used in the
appropriate phase:

- `.agents/skills/prosperity4-round2-alpha-finder/`
- `.agents/skills/prosperity4-round2-log-analyst/`
- `.agents/skills/prosperity4-round2-autopilot/`
- `.codex/agents/alpha_miner.toml`
- `.codex/agents/log_analyst.toml`
- `.codex/agents/execution_risk.toml`
- `.codex/agents/competition_research.toml`
- `.codex/agents/round2_autopilot.toml`

## What Existing Tools Already Answer

### Existing analyzer already covers

The current analyzer is not a bare notebook; it already includes decision-useful
sections for both rounds:

- product classification,
- fair-value proxy comparisons,
- spread and edge calibration,
- mean reversion diagnostics,
- multi-horizon signal predictiveness,
- periodicity / intraday checks,
- spike event studies,
- cross-product checks,
- inventory-risk simulation,
- microstructure features,
- conditional returns by state bucket,
- regime segmentation,
- execution markouts,
- cross-day robustness and sign-flip detection,
- compact AI-facing exports.

### Existing repo outputs already provide partial prior context

- Round 2 curated analyzer export appears to have been run recently even though
  it is stored in the Round 1 analyzer directory.
- Existing validation and execution-risk notes may contain prior Round 1-era
  lessons about carry, adverse selection, and local-vs-hosted mismatches.
- Existing run artifacts under `prosperity_rust_backtester/runs/` provide
  concrete local replay evidence if deeper execution diagnosis is required.

## Gaps That Still Need Work For This Task

The current repo state does not yet satisfy the requested Round 2 research task.
Main gaps:

- no dedicated Round 2 alpha registry with durable per-idea tracking,
- no explicit Round 1 vs Round 2 carryover report,
- no strategy-family ranking file for Round 2,
- no compact implementation-ready candidate file focused on Round 2,
- current assumptions file has to be refreshed against the official context and
  current local tooling reality,
- the analyzer must be re-run and audited rather than trusted from stale export
  timestamps,
- the sufficiency of analyzer sections for Round 2 must be checked explicitly,
- monetization and execution realism must be separated from raw predictive
  signal strength.

## Milestone Order

### Milestone 1: Facts and Assumptions

Write or refresh `prosperity-research/01_assumptions/current_assumptions.md`
with three sections:

- official facts,
- local tool behavior,
- inferred assumptions.

This milestone must explicitly settle:

- active Round 2 products,
- position limits,
- whether `bid()` matters in Round 2,
- separation of manual challenge mechanics from algo strategy,
- Rust backtester defaults and caveats.

### Milestone 2: Analyzer Audit and Round 2 Rebuild

Run the analyzer exactly from its documented command surface and inspect whether
Round 2 runs cleanly and produces the expected plot/export outputs.

If anything is missing or incorrect for Round 2:

- patch only the smallest necessary part of `analysis.py`,
- preserve Round 1 behavior,
- document the reason for the change,
- rerun until the curated Round 2 export is trustworthy.

### Milestone 3: Targeted Alpha Search

Use the analyzer outputs and small targeted scripts or tables to search for:

- structural fair-value edges,
- reversion edges,
- microstructure and book-state edges,
- regime-specific edges,
- spike/event edges,
- execution-dependent edges,
- risk overlays that convert predictive signal into robust strategy behavior.

### Milestone 4: Round 1 to Round 2 Carryover

Use the same analysis framework on Round 1 and compare it directly with Round 2.
The carryover step is mandatory and must classify each major idea as:

- carries over directly,
- carries over with retuning,
- weak / unstable carryover,
- does not carry over.

### Milestone 5: Durable Alpha Inventory

Create `prosperity-research/04_signal_notes/round2_alpha_registry.md` and
record every distinct alpha family or small edge with evidence, monetization
path, carryover status, risks, confidence, and status.

### Milestone 6: Strategy Ranking and Handoff

Translate the registry into strategy families and write:

- `prosperity-research/04_signal_notes/round2_alpha_report.md`
- `prosperity-research/04_signal_notes/round2_carryover_report.md`
- `prosperity-research/04_signal_notes/round2_strategy_candidates.md`

If one or two strategies are overwhelmingly supported, optionally add precise
implementation hooks after the analysis artifacts are complete.

## Round 1 to Round 2 Carryover Test Design

Carryover will not be guessed from memory. It will be tested through the same
measurement framework on both rounds.

### Comparison targets by product

For `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`, compare:

- product classification,
- daily price-level stability and drift,
- fair-proxy rankings,
- spread distributions,
- mean-reversion strength and half-life,
- signal rank ordering by horizon,
- conditional state-bucket monotonicity,
- regime occupancy and regime-specific returns,
- spike frequency and tradeability,
- execution markouts and take opportunities,
- cross-day sign stability,
- inventory-pressure implications.

### Carryover verdict rule

Each major idea gets a carryover label based on:

- same sign and similar rank across rounds,
- monetization still plausible under Round 2 spread / execution conditions,
- not dependent on one single day,
- not dominated by a better proxy in Round 2,
- not invalidated by material regime drift.

## Outputs To Write

### Required outputs

- `prosperity-research/04_signal_notes/round2_research_plan.md`
- `prosperity-research/01_assumptions/current_assumptions.md`
- `prosperity-research/04_signal_notes/round2_alpha_registry.md`
- `prosperity-research/04_signal_notes/round2_alpha_report.md`
- `prosperity-research/04_signal_notes/round2_carryover_report.md`
- `prosperity-research/04_signal_notes/round2_strategy_candidates.md`

### Supporting outputs if needed

- small targeted CSVs or markdown comparison tables under
  `prosperity-research/04_signal_notes/`
- hypothesis notes under
  `prosperity-research/04_signal_notes/hypotheses/`
- execution-risk addendum only if local artifacts materially change alpha status
- validation note only if optional candidate trader stubs are actually tested

## How Repo-Local Skills / Agents Will Be Used

### Alpha-finding stage

Use the local Round 2 alpha-finder workflow to keep discovery separate from
implementation and to deduplicate ideas before they reach strategy ranking.

### Log / execution diagnosis stage

Use the local Round 2 log-analysis workflow only when persisted local runs or
existing run artifacts are needed to confirm monetization, inventory, or adverse
selection concerns.

### Autopilot boundary

Do not use the autopilot workflow to jump straight into trader code. If it is
used at all, use it only after the analysis artifacts exist and only for a
clearly bounded implementation-handoff step.

## Validation Criteria By Milestone

### Milestone 1 success

- assumptions file cleanly separates official facts, local behavior, and
  inference,
- all Round 2 mechanics relevant to alpha search are explicitly stated,
- local backtester caveats are recorded.

### Milestone 2 success

- analyzer runs on Round 2 from the documented command surface,
- curated export is refreshed,
- any Round-2-specific analyzer patch is minimal and justified,
- gaps in analysis coverage are explicitly identified.

### Milestone 3 success

- both products have product-specific classifications,
- multiple alpha families are tested rather than one favored narrative,
- promising ideas are distinguished from noisy or redundant ones,
- monetization path is discussed for each serious candidate.

### Milestone 4 success

- Round 1 and Round 2 are compared side-by-side with explicit verdicts,
- carryover is evidence-based and product-specific,
- rejected or weakened Round 1 ideas are named, not buried.

### Milestone 5 success

- the alpha registry captures distinct small edges instead of collapsing them,
- duplicates are merged,
- confidence and status fields are assigned,
- Round 1 carryover status is included.

### Milestone 6 success

- strategy families are ranked, not just listed,
- conservative, balanced, aggressive, and product-specific next strategies are
  specified,
- each recommended family has a smallest sensible implementation description.

## Decision Notes To Avoid Oscillation

- Favor one dominant market hypothesis per product before adding overlays.
- Do not reword the same fair-value idea as multiple alphas unless the
  monetization path is genuinely different.
- Treat predictive correlation and monetizable edge as separate gates.
- Reject ideas that only look strong on one day unless they have a structural
  explanation and pass threshold robustness checks.
- Prefer minimal analyzer changes over framework redesign.
- Preserve submission-compatible assumptions even in research-only work.
- Keep manual-round bidding / budget-allocation logic separate from algo alpha.
- Do not escalate to trader implementation until the registry and carryover
  files are written.

## Immediate Next Actions

1. Refresh `prosperity-research/01_assumptions/current_assumptions.md` from the
   official context files and current repo docs.
2. Inspect the current analyzer implementation and run it for Round 2.
3. Audit the resulting Round 2 export and decide whether any minimal analyzer
   extension is necessary before deeper alpha mining.
