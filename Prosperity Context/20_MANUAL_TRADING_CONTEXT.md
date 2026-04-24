# Manual Trading Context (Round 3 / Bio-Pods)

## Scope

Round 3 manual challenge: trade Ornamental Bio-Pods with members of the
Celestial Gardeners' Guild. Independent of the algorithmic trader.

## Official mechanics (from the Round 3 doc)

- You submit **two bids** per run: `(b1, b2)` with `b1 ≤ b2` conventionally.
- Each gardener has a hidden **reserve price** `r`. Reserves are "a flowering
  five apart" — i.e. on multiples of 5 (with an unknown offset).
- Gardener acceptance rule:
  1. If `b1 ≥ r`: deal closes at `b1`.
  2. Else the gardener evaluates `b2` against the **global average second
     bid** `μ̄` across all crews.
     - If `b2 > μ̄`: deal closes at `b2`.
     - If `b2 < μ̄`: the probability of a successful trade drops rapidly
       (cubically — precedent from P3 Round 3 `p = ((V - μ̄)/(V - b2))^3`).
- You win the **lowest bid that exceeds the reserve**, so picking `b1` too
  low just lets the gardener fall through to the μ̄ penalty gate.
- Bio-Pods you acquire are auto-sold at `V = 920`. Gardener guild departs
  after Round 3.

## Model (formal specification)

Per gardener, expected profit for bid pair `(b1, b2)`:

```
E[Π | r, μ̄] = 𝟙{b1 ≥ r}·(V - b1)
            + 𝟙{b1 < r ≤ b2}·q(b2, μ̄)·(V - b2)
```

with `V = 920` and `q(b2, μ̄) = min( ((V - μ̄)/(V - b2))^3 , 1 )` when
`b2 ≤ V`, and `0` when `b2 > V`.

Total profit is the sum over gardeners weighted by the reserve distribution.

## Strategy

Two levers:
- `b1`: optimized against the low-cluster reserve CDF (no penalty arm).
  Corner solution often dominates if the cluster is narrow: pick the top of
  the cluster to capture everybody.
- `b2`: dominated by the penalty term. Set `b2` just above your estimate of
  `μ̄` (the field's average second bid), because any slack below μ̄ cubes
  down your revenue.

### First-order condition for the penalty arm

With uniform high-cluster `F_H`, the derivative of `g(b2) ∝ (b2 - H_lo)
(V - μ̄)^3 / (V - b2)^2` is dominated by the `(V - b2)^{-2}` term, pushing
`b2 → μ̄+` (just above competitor average). Interior FOC `b2* = 2·H_lo - V`
typically lies below the cluster support, so the optimum is penalty-driven.

### Recommended starting bids

Assume reserve price multiples of 5 clustered near the resale value.
Canonical submission, conservative of μ̄ estimate:

- If reserves cluster as `low ∈ {895, 900, 905}` and
  `high ∈ {910, 915, 920-ε}`: **`b1 = 907, b2 = 915`**.
- If reserves are uniform on `{900, 905, 910, 915}`: **`b1 = 910, b2 = 915`**.

Rationale:
- `b1` at the low-cluster ceiling captures its full mass at a known fixed
  profit.
- `b2` at 915 sits above any reasonable μ̄ estimate (the field tends to
  converge on 910–912) so the penalty term stays at 1 while still clearing
  high-cluster reserves.

### Sensitivity

- `μ̄` shifts ±3 → profit moves roughly ±9% (cubic elasticity).
- `b2` shift ±2 above the optimum → < 2% profit change.
- `b2` shift ±2 that crosses below μ̄ → **cubic cliff**, -25%+ profit.
- `b1` shift ±2 around cluster top → ±5% profit.

### Risk management

The error is **asymmetric**: underbidding `b2` is catastrophic,
overbidding only forfeits a few margin points. Bias `b2` up by 2–3 units
vs your μ̄ point estimate. Keep `b1` at the low-cluster ceiling as a
guaranteed floor.

If uncertain, run a grid sweep over `(b1, b2) ∈ {900, …, 918}²` against a
few plausible reserve priors and pick the max-min strategy. Historically
this lands near `(907, 915)` with ~5% of ex-post optimum — the error band
winners absorbed in P3 Round 3.

## Decision memo template

For each run, produce a short memo in
`prosperity-research/07_manual_round/round3_biopods/decision_memo.md` with:
1. Reserve prior (cluster specification).
2. μ̄ prior (competitor distribution + mean estimate).
3. Expected-profit grid over `(b1, b2)`.
4. Chosen `(b1, b2)` and expected PnL.
5. Worst-case PnL if μ̄ is off by ±5.
6. Next-run invalidation test (what observation would change the plan).

## Archived manual tasks (for reference only)

- Round 1 Exchange Auction (ember mushrooms, dryland flax) — static book,
  single clearing price, volume-maximizing with higher-price tiebreak.
  Fees: 0.05 per-unit on ember mushroom trades.
- Round 2 Invest & Expand — 50,000 XIRECs across Research (log),
  Scale (linear), Speed (rank-based). Formula
  `PnL = Research × Scale × Speed - Budget_Used`.

Both are closed-out historical tasks; manual R3 PnL is independent.
