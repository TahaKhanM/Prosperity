# Round 1 Ash Working Note - 2026-04-16

## Official vs inferred

Official:
- Round 1 products are `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
- Position limits are `80` for both products.
- Round 1 uses the standard `Trader.run()` interface; `bid()` is not used.
- Orders that would breach worst-case position limits are rejected.

Inferred from local and hosted evidence:
- Current working baseline is [`round1_pepper_dual_carry_v29.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py).
- `v29` is locally strong overall because of Pepper, not because Ash broke out.
- Hosted Ash evidence still points to passive inside-spread monetization and selective resets as the main transferable edge surface.
- The current Ash bottleneck is more likely quote translation and regime gating than a missing new fair-value model.

## Named trader, dataset, and artifacts

Baseline under test:
- [`round1_pepper_dual_carry_v29.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v29.py)

Useful older comparison:
- [`round1_pepper_dual_carry_v23.py`](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round1/work/pepper_carry/unvalidated/round1_pepper_dual_carry_v23.py)

Hosted Ash anchor:
- `round1_overhaul_v22_summary.json` in `prosperity-research/official_log_analysis_20260415/`
- hosted `ASH_COATED_OSMIUM` final PnL: `3178.53125`

Target dataset:
- `prosperity_rust_backtester/datasets/round1/`

Current local artifact:
- `prosperity_rust_backtester/runs/persist-v29-default-20260416/`

## Diagnosis

`v29` Ash is probably not failing because the fair value is grossly wrong. The stronger evidence is that the execution policy is too coarse. The current code allows one-tick-inside quoting on both sides whenever the spread is at least `15`, even though the hosted-informed Ash line was more selective: buys could be loosened earlier, but sells stayed stricter and both were gated away from shock states. That makes the current Ash leg look too symmetric and too willing to advertise inside liquidity in regimes that are locally acceptable but less likely to transfer to the official matcher.

## Ranked hypotheses

1. Hosted-informed asymmetric inside quoting on top of `v29`
   - keep fair and takes unchanged
   - restore regime gating for inside quotes
   - buy side slightly more permissive than sell side
2. Maker/taker regime split
   - raise `take_edge` in shock or stale adverse states
   - preserve inside quoting only in calm wide states
3. Inventory-aware inside-size throttling
   - reduce inside bids when already long
   - reduce inside asks when already short
4. Mild micropressure-aware quote-side controller
   - use micro bias only to gate inside quotes, not as a full directional model
5. Ash recycle timing overlay
   - tighten flattening only when inventory is large and the book is no longer supportive

## Promotion rules

Promote only if a candidate:
- beats `v29` on Ash contribution by a meaningful amount,
- does not rely on `default`-only gains,
- survives `worse`, `queue05`, and `none` without obvious collapse,
- shows better execution quality through reduced weak fills or cleaner inventory behavior.

Near miss:
- Ash improves a bit but the gain is small or fragile.

Reject:
- no real Ash uplift,
- gain is obviously fill-model-sensitive,
- or Pepper changes dominate the observed delta.
