# Prosperity 4 Round 1 Current Assumptions

Date: 2026-04-14

Scope: Round 1 algorithmic strategy work only. Keep official facts separate from soft hints, local evidence, public-repo analogy, and still-unproven mechanism stories.

Primary official files:
- `Prosperity Context/Official Prosperity Context.md`
- `Prosperity Context/Official Prosperity Context Round 1.md`

Soft-hint files only:
- `Prosperity Context/ROUND1_PROMPT_HINTS_CONTEXT.md`
- `Prosperity Context/CHATGPT_CONTEXT_FOR_CODEX_PROMPT_ENGINEERING.md`

## Official Facts

- Round 1 algorithmic products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
- Official position limits are `80` for both products.
- Round 1 also includes an Exchange Auction, but the local official docs present it as a parallel Round 1 task, not as a change to the continuous-book trader interface.
- Submission code is a Python `Trader` class with `run(self, state)`.
- `run()` returns `(result, conversions, traderData)`.
- Buy quantities are positive and sell quantities are negative.
- `sell_orders` volumes in `OrderDepth` are negative.
- Position-limit checks are worst-case by side. If aggregated buy-side or sell-side exposure breaches the limit, the exchange rejects all orders on that side for that iteration.
- Globals and persistent instance fields are not safe state. `traderData` is the intended persistence channel and must stay compact.
- `bid()` is a Round 2 method only and is ignored outside Round 2.

## Soft Hints, Not Rules

- The official Round 1 note describes `INTARIAN_PEPPER_ROOT` as relatively steady and `ASH_COATED_OSMIUM` as more volatile, possibly patterned. That is narrative guidance, not a mechanism guarantee.
- The local hints file explicitly says the prompt cards are signal-rich clues, not formal rules.
- Hint themes about calm execution, spread intent, and slow Pepper growth are useful for research ideas only.
- The auction hints are useful for later manual-side simulation work, not as authority for this continuous-book trader.

## Official Narrative Versus Local Data

- The official screenshot is genuine and matches the local Round 1 file verbatim.
- The Pepper clue is only loosely grounded in truth:
  - locally, Pepper is indeed extremely steady in shape,
  - but it is not steady around a fixed fair,
  - it is better described as a near-deterministic rising session fair.
- The Ash clue is even softer:
  - Ash does show more local microstructure noise than Pepper,
  - but the data still do not support a strong clocked hidden pattern,
  - the strongest Ash structure remains anchored fair plus imbalance-sensitive short-horizon behavior.

## Local Empirical Findings

- `ASH_COATED_OSMIUM` behaves like an anchored wide-spread market with fair value centered near `10000`, replenishing liquidity, and modest book-driven lean.
- `INTARIAN_PEPPER_ROOT` does not look fixed-anchor in the local bundle. All three local days rise by about `+1000` from open to close.
- Pepper's normalized intraday path is extremely similar across days on the cleaned two-sided effective mid. Smoothed cross-day correlation is effectively `1.0`.
- Pepper one-sided books are short refresh artifacts, not long regimes:
  - non-two-sided streak median: `1`
  - max streak: `3`
- Ash one-sided states are also brief:
  - max streak: `4`
- Pepper drift remains present after conditioning on spread state, non-extreme imbalance, and after excluding extreme moves.

## Re-Tested Current-Ship Hypotheses

These are local working hypotheses, not official truths.

What the current ship family appears to get right:
- `ASH` is still best modeled as anchored replenishing-maker microstructure, not as a clock-template market.
- `PEPPER` should not be traded as fixed-anchor market making.
- Owning Pepper inventory early is locally rewarded.

What the post-`v3` evidence added:
- `round1_overhaul_v5.py` showed that Pepper trade-tape pressure is real, but only a small overlay on the core template story.
- `round1_overhaul_v6.py` showed that the bigger remaining miss was the coarse Pepper template itself.
- A finer phase-corrected Pepper curve beat `round1_overhaul_v3.py` in every tested mode.
- `round1_overhaul_v7.py` then showed that adding extra residual × imbalance tactical logic on top of `v6` gave some of that gain back.

What the new template-aware counterfactuals added:
- A slower-build Pepper counterfactual was tested in `round1_overhaul_v4.py`.
- It still beat the older ships, but it lost to the more explicit template-owning design in `round1_overhaul_v3.py` in every tested mode.
- That does not prove the live generator must reward immediate max-long ownership.
- It does strengthen the local working assumption that, in this bundle, early template-aware Pepper acquisition is a real competition-specific edge rather than just a lucky threshold choice inside `round1_overhaul_v1.py`.

Current local best interpretation:
- `round1_overhaul_v6.py` is the best current ship because it keeps the competition-specific template-owning Pepper architecture, confirms a smaller trade-tape overlay from `v5`, and improves the core fair curve without adding decorative complexity.

## Public-Repo Analogy Only

- Older Prosperity 3 repos are useful for workflow and architecture ideas:
  - fair-proxy diagnostics,
  - take -> clear -> make sequencing,
  - separate alpha / inventory / execution layers,
  - disciplined artifact review.
- Older public repos are not authority on Round 1 products, syntax, limits, hidden rules, or bot behavior.
- Optiver-style external material is useful for time-split validation ideas, not for importing a high-dimensional feature stack into submission code.

## Unproven Mechanism Hypotheses

- Pepper may be generated by a smooth session-template latent fair that lagged quote bots reveal through the book.
- Pepper may instead be a hidden-state drift process that only happened to look near-deterministic in the three local days.
- Ash may be generated by anchored replenishing makers with small predictable skew and spike-fade behavior.
- One-sided books may be mostly a bot-refresh artifact rather than a predictive regime.

These are testable strategy hypotheses, not official facts.

## Rejected Assumptions

- Reject: tutorial products or tutorial limits carry into Round 1.
- Reject: prompt hints are stronger authority than official docs.
- Reject: Pepper must trend live just because one local bundle trends.
- Reject: old Prosperity repos can be treated as current competition truth.
- Reject: the Exchange Auction implies a required trader-interface change for Round 1.

## Working Guardrail

Use this safe foundation for Round 1 trader work:
- code only for `run(self, state)`,
- trade only `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`,
- enforce `80`-limit worst-case safety,
- keep `traderData` compact,
- treat auction work as a separate side note unless a new official auction interface source appears.
