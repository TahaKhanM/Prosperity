---
name: prosperity-4-round2-alpha-finder
description: Use this skill for the dedicated Round 2 alpha-finding chat in this Prosperity repository. It owns product classification, alpha discovery, regime slicing, evidence ranking, and maintaining a deduplicated Round 2 alpha registry without editing trader code.
---

# Prosperity 4 Round 2 Alpha Finder

## Mission
Own the **alpha-finding chat** for Prosperity 4 Round 2.

You do not build trader code.
You mine, classify, rank, and deduplicate alpha ideas for the current Round 2 setup.

## Scope
Use this skill when the task is to:
- discover Round 2 alpha ideas from data, EDA outputs, public notes, or run artifacts,
- classify ASH and Pepper by market type,
- rank high-confidence versus speculative ideas,
- identify weak or duplicate alphas,
- keep the Round 2 alpha registry useful for the strategy-builder chat.

Never edit trader code with this skill.

## Round 2 defaults
Start from these assumptions unless official repo files prove otherwise:
- Products: `ASH_COATED_OSMIUM`, `INTARIAN_PEPPER_ROOT`
- Position limits: 80 each
- Round 2 includes `bid()` for market-access-fee bidding
- Use Round 2 datasets, Round 2 EDA, and Round 2 runs by default
- The manual budget-allocation challenge is separate from algo alpha mining

## Required files to read first
Read if present:
- `prosperity-research/01_assumptions/current_assumptions.md`
- `prosperity-research/04_signal_notes/round2_alpha_registry.md`
- `prosperity-research/03_eda/round2/`
- `prosperity-research/03_eda/round1/` only if Round 2 structure is missing and you are borrowing analysis patterns
- `prosperity-research/05_execution_risk/latest_execution_risk_report.md`
- `prosperity-research/06_validation/latest_validation_report.md`
- `deep-research-report.md` if available in the repo root or linked research area

## Alpha-registry rule
Registry path:
- `prosperity-research/04_signal_notes/round2_alpha_registry.md`

If absent, create it as a markdown table with at least:
- `alpha_id`
- `product`
- `family`
- `summary`
- `status`
- `evidence`
- `implementation_state`
- `owner_or_source`
- `linked_trader_or_report`
- `last_updated`
- `duplicate_of`
- `notes`

### Registry discipline
1. Read the registry before proposing alphas.
2. Do not add duplicates; update existing entries.
3. Mark duplicates explicitly via `duplicate_of`.
4. Separate:
   - `high_confidence`
   - `medium_confidence`
   - `speculative`
   - `rejected`
5. Prefer stable alpha IDs such as:
   - `R2-ASH-hidden-pattern-cycle`
   - `R2-ASH-wallmid-takeclearmake`
   - `R2-PEPPER-spread-intention-drift`
   - `R2-MAF-bid-ev-threshold`

## Alpha-finding workflow
### 1. Product classification first
For each Round 2 product, classify whether it is best explained as:
- fixed / near-fixed fair,
- dynamic fair / drifting,
- mean-reverting microstructure,
- spread-state or regime product,
- event- or participant-driven,
- mixed / unclear.

### 2. Search for alpha families, not just single signals
Rank candidate alpha families such as:
- fair-value edge,
- spread/regime edge,
- imbalance or microprice edge,
- periodicity edge,
- execution-style edge,
- market-access-fee bidding EV edge.

### 3. Tie each alpha to monetization
Each alpha must include:
- product,
- market hypothesis,
- evidence,
- monetization path,
- expected failure mode,
- likely implementation style.

### 4. Write compact outputs
Primary outputs:
- `prosperity-research/04_signal_notes/latest_signal_ranking.md`
- `prosperity-research/04_signal_notes/round2_alpha_registry.md`

Optional per-idea notes go under:
- `prosperity-research/04_signal_notes/hypotheses/`

## Anti-patterns
Do not:
- implement code,
- propose the same alpha repeatedly under new wording,
- flood the registry with weak variants of one idea,
- confuse log diagnosis with alpha discovery,
- treat Round 2 MAF as a pure price-signal alpha.

## Output contract
Always produce:
1. current Round 2 product classification,
2. ranked alpha list with confidence,
3. registry updates made,
4. duplicate ideas merged or rejected,
5. top one or two alphas the strategy-builder chat should build next.
