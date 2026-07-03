# Round 2 Validation Surface Audit

Date: 2026-04-19

Scope: determine whether the current explicit Round 2 local surface is the
right surface to optimize for after the strategy-builder blocker.

Key inputs:

- [current_assumptions.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/01_assumptions/current_assumptions.md)
- [round2_validation_surface.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_validation_surface.md)
- [round2_baseline_snapshot.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_baseline_snapshot.md)
- [current_diagnosis_packet.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/current_diagnosis_packet.md)
- [round2_blocker_report.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity-research/06_validation/round2_blocker_report.md)
- official Round 2 docs under
  [prosperity_round_2.md](/Users/tahakhan/Documents/Work/Projects/Prosperity/Prosperity%20Context/Unrefined%20Context/Prosperity%20Round%202.md)

## Short Verdict

The current explicit `-1/0/1` local Rust surface is useful as a base-stream
attribution and regression surface, but it is not trustworthy as the sole
primary ranking surface for Round 2.

## Where The Current Surface Is Good

The current surface is still valuable because it:

- uses the canonical local raw Round 2 CSVs
- avoids the multi-day artifact collision bug by running explicit day `-1`,
  `0`, and `1`
- prevents cherry-picking a single day
- gives clean candidate-vs-baseline attribution on the base visible quote
  stream

That means it should be kept.
It should not keep its current status as the only success surface.

## Surface Mismatch Table

| Dimension | Official / live Round 2 reality | Current local surface | Consequence |
| --- | --- | --- | --- |
| `bid()` / MAF | accepted bids get `25%` more quotes and pay a one-time fee; top `50%` of bids accepted | local backtests do not call `bid()` at all | local ranking cannot price extra-flow strategies or bid-sensitive tradeoffs |
| Testing quote set | official testing uses a slightly randomized `80%` quote set | local uses fixed raw CSV days | local ranking can overstate deterministic path stability |
| Matching model | official exchange rules do not expose the exact local replay knobs | current runs use `trade_match_mode=all`, `queue_penetration=1.0`, `price_slippage_bps=0.0` | quote-quality and passive-edge differences may be misranked on an optimistic surface |
| Success objective | final objective is net Round 2 PnL including any accepted MAF fee | current local objective is `>10%` over baseline on explicit base-stream day `-1/0/1` | local objective is not aligned with the full Round 2 economic problem |
| State continuity | official evaluation is not the same thing as three independent explicit-day local runs | current primary surface is explicit non-carry daily splits | good for attribution, but not a full path or access simulation |

## What The Builder Blocker Means For Surface Trust

The blocker evidence makes the current surface especially weak as a ranking
surface:

- baseline Pepper already sits near the official long limit about `94%` of the
  time on all three days
- remaining official-limit Pepper carry headroom is only about `7775`
- even generous Ash upside still leaves the local `>10%` threshold out of
  reach
- `v02` improved Pepper execution proxies in places, but local headline PnL was
  still mostly determined by lower carry occupancy

Interpretation:

- the surface is heavily saturated by one obvious local trade
- this makes it poor at ranking orthogonal but smaller monetization edges
- it is especially poor at ranking Round 2-specific quote-intensity or MAF-like
  strategies

## Better Primary Research Surface

The best replacement is not another single local scalar.
It is a split primary surface with two required lenses.

### Primary lens A: base-stream attribution

Keep the current explicit day `-1/0/1` non-carry surface, but demote it from
`optimize this scalar at all costs` to `base-stream attribution floor`.

Use it to answer:

- is the candidate obviously worse than baseline on the base quote stream?
- which product caused the delta?
- did inventory shape, quote quality, or fill mix change?

### Primary lens B: extra-flow / quote-intensity relevance

Rank any Round 2 candidate that depends on quote quality, passivity, or MAF
using an additional research lens:

- positive-edge aggressive quantity and passive quantity
- state-conditioned quote quality rather than headline PnL alone
- whether the candidate creates more positive-edge quote opportunities than the
  baseline
- whether the candidate is orthogonal to the baseline’s simple Pepper carry
  shell
- hosted evidence, if later available, should outrank this proxy lens

Reason:

- Round 2 is the only round where more quotes can matter economically
- the current local surface cannot measure that directly
- therefore local base-stream PnL alone is an incomplete objective

## Recommended Secondary Safety Surface

Use a stricter local execution stress surface as the secondary safety check:

- same explicit day `-1/0/1` split
- same official-limit-compliant traders
- but rerun under stricter matching such as:
  - `--trade-match-mode worse`
  - `--queue-penetration 0.5`

Why:

- the CLI already supports these knobs
- they are a better filter for quote-gating or passive-quality ideas than the
  default optimistic `all` / `1.0` / `0.0` surface
- they help distinguish transfer-shaped quote improvements from local replay
  artefacts

Current workflow gap:

- [run_harness.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/scripts/run_harness.py)
  does not yet expose those stricter knobs directly
- until it does, the builder should either run the Rust CLI directly or add a
  minimal pass-through later

## What Should Change In The Builder Validation Process

Stop using this rule as the only decision rule:

- `candidate_total_pnl > 1.10 * baseline_total_pnl` on the default explicit-day
  local surface

Replace it with a candidate-class-aware process:

1. Base-stream carry replacement candidate:
   - must beat or at least clearly challenge baseline on the current explicit
     local surface
   - this is the right gate for another Pepper carry-shell rewrite

2. Quote-quality / extra-flow / MAF-sensitive candidate:
   - must avoid a large local base-stream regression
   - must improve quote-quality or state-selectivity diagnostics
   - should be judged on the stricter local safety surface and, when possible,
     hosted evidence

3. Ash execution overlay:
   - should be judged by transfer-shaped execution improvement, not by expecting
     Ash alone to clear the entire `>10%` target

## Recommended Surface Roles

| Surface | Role | Keep / change |
| --- | --- | --- |
| explicit local `-1/0/1`, non-carry, default matching | attribution floor and regression guardrail | keep, but demote |
| stricter local `worse` / `queue05` explicit-day reruns | secondary safety surface for quote-EV ideas | add |
| hosted / official repeated evidence if available later | true Round 2 ranking surface | prefer when available |

## Surface Verdict

The current local explicit-day surface should remain in the workflow, but only
as a secondary safety and attribution surface.
It should not remain the sole primary success surface for Round 2 strategy
ranking.
