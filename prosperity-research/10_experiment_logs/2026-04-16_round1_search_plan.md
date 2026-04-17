# Round 1 Search Plan - 2026-04-16

## Official vs inferred

Official:
- Round 1 products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
- Position limits are `80` for both products.
- Trader interface is the standard Prosperity `Trader.run()` contract; `bid()` is irrelevant for Round 1.
- The environment is stateless across calls except for `traderData`.

Inferred from local evidence:
- `INTARIAN_PEPPER_ROOT` remains the dominant local edge surface.
- The strongest local Round 1 family is still Pepper carry plus tactical execution overlays.
- `ASH_COATED_OSMIUM` redesigns have repeatedly failed to beat the current Ash leg inside the best Pepper family.
- The likely remaining edge is tactical execution quality, not another small fair-value tweak.

## Named baseline and comparison set

Target dataset:
- `round1` in `prosperity_rust_backtester/datasets/round1/`

Named baseline:
- `traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v13.py`
- Fresh benchmark confirmation:
  - `default`: `295902.0`
  - `worse`: `295845.0`
  - `queue05`: `273575.5`
  - `none`: `249785.0`
  - robust score: `625976.125`

Strongest current comparison baselines:
- `trader_archive/Round1/research/round1_v13_pepper_recycle_overlay_v1.py`
  - best fresh weighted near-miss
  - `default`: `295996.0`
  - `worse`: `295939.0`
  - `queue05`: `273634.5`
  - `none`: `249685.0`
  - robust delta vs `v13`: `+88.25`
  - verdict: too small and regresses `none`
- `traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v15.py`
  - higher headline default but weaker robust profile
  - `default`: `295955.0`
  - `worse`: `295904.0`
  - `queue05`: `273588.5`
  - `none`: `249244.0`
  - robust delta vs `v13`: `-207.75`
  - verdict: lucky-default style variant, reject as benchmark replacement
- `traders/Round1/active/round1_pepper_dual_carry_v11.py`
  - active milestone but no longer the best local benchmark

## Current frontier

What has already been tried:
- Pepper carry/recycle threshold families through `v18`
- Ash overlays based on inside sizing, signal thresholds, and exact-regime ideas
- Pepper oracle / microtrade / trade-gated prototypes
- Hosted-winner-inspired candidate ports
- Broad archive sweep across Round 1 historical variants

What failed:
- Ash-first redesigns as the main source of improvement
- Generic fair-value sweeps and parameter nudges
- Hosted-winner style replacements for the local Pepper baseline
- Prototype Pepper controllers that abandoned the carry posture without replacing it with better execution quality

What remains underexplored:
- Pepper quote-worthiness gating at the passive-order level
- Spread-intention / leaning-state gating layered on top of the carry baseline
- Action-template controllers that choose among `hold`, one-sided quote, recycle, improve, or pause
- Sequence-motif and short-horizon state cluster logic for toxic-fill suppression
- Execution residuals that only modify `v13` where tactical fills are weak

What counts as a significant improvement:
- Primary bar: robust, non-regressing improvement that is materially larger than the `+88.25` recycle near-miss.
- Promotion bar for this search:
  - no regression on `default`, `queue05`, or `none`
  - clear mechanism credibility from artifacts, not only headline PnL
  - robust score improvement large enough to matter in practice, not a sub-`500` point noise move
- Stretch goal:
  - multi-thousand robust-score improvement or roughly `>5%` over the current robust benchmark

## Deep-report extraction

Most promising report ideas still not seriously exhausted locally:
1. Pepper fill-quality hazard / execution gate
2. Pepper spread-intention / leaning-state controller
3. Pepper action-template / finite-state controller
4. Pepper dynamic carry-target plus recycler
5. Pepper sequence-motif strategy
6. Stationarized OFI / pressure-aware execution gate
7. Osmium episodic redesign only after Pepper execution families are seriously tested
8. Residual-on-top-of-best-strategy execution overlays

## Additional local evidence used for this run

Exact-control summary for `INTARIAN_PEPPER_ROOT`:
- dominant actions are still `hold`, `buy_take1_16`, `sell_take1_12`, `carry_inside`, and `sell_inside_8`
- optimal Pepper inventory remains high for most of the day
- this supports preserving the broad carry posture while improving tactical timing and quote selection

Fresh benchmark product mix for `v13`:
- `default`: `ASH +55231`, `PEPPER +240671`
- `queue05`: `ASH +34387.5`, `PEPPER +239188`
- `none`: `ASH +13569`, `PEPPER +236216`

## Ranked build order

1. Pepper fill-quality hazard gate on top of `v13`
2. Pepper spread-intention / leaning-state gate on top of `v13`
3. Pepper action-template controller if the gate families show signal but remain too smooth
4. Pepper dynamic carry-target plus recycler refinement
5. Pepper sequence-motif overlay
6. Stationarized OFI / pressure-aware execution gate
7. Osmium episodic redesign
8. Residual hybrid cleanup on top of the best surviving candidate

## Metrics and validation surface

Primary metrics:
- `default`, `worse`, `queue05`, `none`
- robust score = `default + 0.75 * queue05 + 0.5 * none`
- per-day PnL deltas
- product-level contribution

Artifact checks for promising runs:
- `metrics.json`
- `bundle.json`
- `activity.csv`
- `pnl_by_product.csv`
- `trades.csv`
- inventory path and time near limits
- evidence of toxic passive fills or improved suppression

## Promotion and rejection rules

Promote a candidate only if:
- it beats `v13` on the main benchmark surface,
- it survives `queue05` and `none`,
- the mechanism is attributable and inspectable.

Reject quickly if:
- gain is tiny or isolated to one day,
- `none` drops materially,
- the change is just another threshold reshuffle with no new execution mechanism,
- Ash dominates the diff while Pepper remains unchanged.
