# Round 2 Evaluation Loop

Date: 2026-04-19

Scope: explicit scoring and decision rules for autonomous Round 2 strategy
iteration.

## Primary Evaluation Surface

Primary local floor:

- dataset:
  [datasets/round2](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/datasets/round2)
- runs:
  explicit non-carry day `-1`, `0`, and `1`
- artifact mode:
  `full`
- baseline:
  [baseline.py](/Users/tahakhan/Documents/Work/Projects/Prosperity/prosperity_rust_backtester/traders/Round%202/baseline.py)
- scalar:
  summed total PnL across the three day runs

Use this surface as:

- required baseline-comparison floor
- attribution surface
- regression guardrail

## Secondary Sanity Surface

Secondary stricter local surface:

- same dataset and explicit day split
- stricter matching via direct Rust CLI as needed:
  - `--trade-match-mode worse`
  - `--queue-penetration 0.5`

Use this surface to answer:

- is the candidate still credible under harsher local fill assumptions?
- is a quote-quality or state-selectivity edge obviously fake?
- does the candidate remain more orthogonal than baseline under stricter
  matching?

## Required Artifacts Per Serious Iteration

For each serious candidate loop, keep:

- harness run roots for day `-1`, `0`, and `1`
- `metrics.json` for candidate and baseline
- `pnl_by_product.csv` for candidate and baseline
- `combined.log`
- `trades.csv`
- candidate-vs-baseline reports
- updated current candidate note
- updated diagnosis packet
- updated progress log
- updated alpha registry

## What Counts As A Baseline Beat

A candidate counts as beating baseline when all of the following are true:

1. It improves the primary local floor scalar versus baseline.
2. The gain is not obviously hidden by one catastrophic day or one product
   blow-up.
3. The strategy mechanism is coherent and materially distinct from baseline.

## What Counts As Likely Noise

Treat the result as likely noise when:

- the delta is very small and the behavior is nearly identical to baseline
- one good day masks broad flatness elsewhere
- the candidate only wins on the optimistic local surface and loses its
  rationale on the stricter sanity surface
- the branch differs only by minor threshold churn without a theory change

## What Counts As A Robust Improvement

Treat the result as robust when:

- the candidate improves total PnL on the primary local floor
- at least one of per-day or per-product decomposition confirms the intended
  donor bucket
- the stricter sanity surface does not expose an obvious transfer failure
- the branch is orthogonal enough to baseline that the improvement can be
  explained by a named alpha or monetization change

## What Counts As Branch Exhaustion

Mark a branch exhausted when:

- multiple variants converge to baseline behavior
- multiple variants reproduce the same dominant failure mode
- the registry and diagnosis both say the family is already absorbed by
  baseline
- more tuning would be threshold churn rather than a new state or alpha

## Metrics That Matter Besides Headline PnL

Track every loop:

- summed total PnL
- per-day PnL
- per-product PnL
- average absolute position by product
- near-limit fraction by product
- own trade count
- drawdown when available
- aggressive / passive edge summaries from the comparison report
- whether the candidate is orthogonal to baseline in:
  - inventory path
  - participation state
  - target-setting logic
  - quote/take selectivity

## Candidate-Class Decision Rules

### Base-stream carry replacement

- must beat or at least strongly challenge baseline on the primary local floor
- stricter sanity surface is still required as a regression check

### Quote-quality / extra-flow / state-selectivity branch

- must avoid a serious local-floor regression
- must show stronger selectivity or fill-quality diagnostics
- stricter sanity surface matters more than optimistic local headline PnL alone

### Ash overlay

- should improve Ash without harming Pepper
- is not expected to solve the entire Round 2 blocker alone

## Stop-And-Fix Validation Rule

- if run artifacts are missing, inconsistent, or incomparable, stop and fix the
  validation process before ranking the branch
- do not promote or reject branches on broken evidence
