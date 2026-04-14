# Round 1 Execution Risk Report

Date: 2026-04-14

Scope:
- baseline: `prosperity_rust_backtester/traders/round1_baseline_v1.py`
- lower-concentration fallback: `prosperity_rust_backtester/traders/round1_candidate_v2.py`
- prior ship: `prosperity_rust_backtester/traders/round1_overhaul_v3.py`
- new contenders:
  - `prosperity_rust_backtester/traders/round1_overhaul_v5.py`
  - `prosperity_rust_backtester/traders/round1_overhaul_v6.py`
  - `prosperity_rust_backtester/traders/round1_overhaul_v7.py`

## Bottom Line

- `round1_overhaul_v6.py` is the new local best ship.
- `round1_overhaul_v5.py` confirms that Pepper trade processing contains useful secondary signal, but only a small amount.
- `round1_overhaul_v6.py` wins because it fixes the more important issue:
  - the Pepper fair curve in `v3` was too coarse by session phase.
- `round1_overhaul_v7.py` is rejected.
  - The extra residual × imbalance overlay added tactical complexity without beating `v6`.

## Score Under Stress

| Strategy | default | `worse` | `none` | `worse + q=0.35` |
| --- | ---: | ---: | ---: | ---: |
| Baseline | `152,305.5` | `156,131.0` | `159,915.5` | n/a |
| Candidate v2 | `239,372.0` | `239,584.0` | `216,731.5` | `227,724.0` |
| Overhaul v3 | `282,373.0` | `282,340.0` | `245,303.0` | `259,507.0` |
| Overhaul v5 | `282,407.0` | `282,374.0` | `245,314.0` | `259,542.0` |
| Overhaul v6 | `282,974.0` | `282,941.0` | `245,673.0` | `259,990.0` |
| Overhaul v7 | `282,920.0` | `282,887.0` | `245,630.0` | `259,919.0` |

Interpretation:
- `v5` validates the tape overlay, but only by `+34 / +34 / +11 / +35` over `v3`.
- `v6` is the real upgrade:
  - `+601 / +601 / +370 / +483` over `v3`
  - `+567 / +567 / +359 / +448` over `v5`
- `v7` gives back `54 / 54 / 43 / 71` versus `v6`.

## Concentration Profile

### Pepper default inventory

| Strategy | Avg abs pos | Time `|pos| >= 60` | Time `|pos| >= 70` | First `|pos| >= 78` |
| --- | ---: | ---: | ---: | --- |
| Candidate v2 | `58.66` | `45.58%` | `20.23%` | much later than overhaul family |
| Overhaul v3 | `78.96` | `99.94%` | `99.94%` | `[900, 1000, 300]` |
| Overhaul v5 | `78.96` | `99.94%` | `99.94%` | `[900, 1000, 300]` |
| Overhaul v6 | `78.88` | `99.94%` | `99.94%` | `[900, 1000, 300]` |
| Overhaul v7 | effectively unchanged from `v6` | effectively unchanged | effectively unchanged | effectively unchanged |

Interpretation:
- None of the post-`v3` upgrades reduce the basic Pepper concentration.
- The winning change set is better understood as a cleaner exploit of the same local generator, not a safer posture.

## Product-Level Risk Read

### Default contribution

| Strategy | `ASH_COATED_OSMIUM` | `INTARIAN_PEPPER_ROOT` |
| --- | ---: | ---: |
| Candidate v2 | `38,318.0` | `201,054.0` |
| Overhaul v3 | `45,608.0` | `236,765.0` |
| Overhaul v5 | `45,608.0` | `236,799.0` |
| Overhaul v6 | `45,608.0` | `237,366.0` |
| Overhaul v7 | `45,608.0` | `237,312.0` |

### `none` contribution

| Strategy | `ASH_COATED_OSMIUM` | `INTARIAN_PEPPER_ROOT` |
| --- | ---: | ---: |
| Candidate v2 | `10,627.0` | `206,104.5` |
| Overhaul v3 | `10,262.0` | `235,041.0` |
| Overhaul v5 | `10,262.0` | `235,052.0` |
| Overhaul v6 | `10,262.0` | `235,411.0` |
| Overhaul v7 | `10,262.0` | `235,368.0` |

Interpretation:
- All new gain is still Pepper.
- Ash remains stable but unchanged across `v3` through `v7`.
- The post-`v3` contest was a Pepper fair-model contest, not a portfolio rebalance.

## What Each New Variant Taught

### `round1_overhaul_v5.py`

- Useful lesson:
  - prior market-trade processing contains some real Pepper state information.
- Risk conclusion:
  - that signal is too small to justify large tactical rewrites by itself.

### `round1_overhaul_v6.py`

- Useful lesson:
  - fixing the Pepper phase curve matters more than adding more tactical logic.
- Risk conclusion:
  - the cleaner fair model improves score without making the architecture materially more brittle.

### `round1_overhaul_v7.py`

- Useful lesson:
  - residual × imbalance interactions are real in research, but the trader already had enough tactical conditioning.
- Risk conclusion:
  - adding that layer on top of `v6` increased complexity faster than it improved monetization.

## Main Remaining Risks

1. The core local edge is still a Pepper generator story, not a diversified two-product story.
2. The data set is still only three local Round 1 days.
3. If live Pepper is materially less template-like, `candidate_v2` remains the safer fallback.
4. Ash still looks improvable, but not enough to outweigh the current Pepper concentration in the total score.

## Execution-Risk Verdict

- `round1_overhaul_v6.py` is the best current ship if the goal is strongest local evidence-weighted performance.
- `round1_overhaul_v6.py` is not a de-risked design.
- The correct description is:
  - more faithful to the observed Pepper generator than `v3`,
  - slightly more profitable than `v3`,
  - still a high-conviction competition-specific Pepper carry-and-recycle strategy.
