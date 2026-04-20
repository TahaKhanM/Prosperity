# Algorithmic Trading Context (Rounds 1 and 2)

## Scope

This file condenses the algorithmic-trading facts and hints from the uploaded
Prosperity 4 materials.

Use it for:
- trader implementation
- backtest interpretation
- round-specific rule checks
- alpha search on `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`
- deciding whether and how to include a Round 2 `bid()`

Do **not** use this file as the sole source for repo/tooling behavior. For that,
read `30_REPO_AND_TOOLING_CONTEXT.md`.

## Hard official interface facts

From the official general context:

- The hosted algorithm interface is a Python `Trader` class with `run(self,
  state)`.
- The official general context says testing uses `1,000` simulation iterations
  on historical data and final scoring uses `10,000` iterations.
- For **Algorithmic Round 2**, `Trader` should also define `bid(self)`.
- Including `bid()` in all rounds is acceptable; it is ignored outside Round 2.
- The official submission-compatible return shape is:
  `orders, conversions, traderData`
- `traderData` is the intended persistence channel across hosted calls.
- Hosted execution is stateless with respect to class/global variables because
  the container is AWS Lambda based.
- `traderData` is truncated at 50,000 characters by the external framework.
- `TradingState` includes at minimum:
  - `traderData`
  - `timestamp`
  - `listings`
  - `order_depths`
  - `own_trades`
  - `market_trades`
  - `position`
  - `observations`
- `OrderDepth.sell_orders` volumes are negative.
- If you post an order and bots do not trade against the remaining quantity, the
  remainder is canceled at the end of the iteration.
- If all product-side orders in one iteration would breach the worst-case
  position limit, the exchange rejects all orders for that product in that
  iteration.
- Official hosted execution is effectively instantaneous versus bots.

## Shared official product facts for uploaded Rounds 1 and 2

Products:
- `ASH_COATED_OSMIUM`
- `INTARIAN_PEPPER_ROOT`

Position limits in both uploaded round docs:
- `ASH_COATED_OSMIUM`: `80`
- `INTARIAN_PEPPER_ROOT`: `80`

Shared qualitative description:
- `INTARIAN_PEPPER_ROOT` is the steadier product.
- `ASH_COATED_OSMIUM` is the more volatile product and may hide a pattern.

## Round 1: official facts

Round name:
- `Trading groundwork`

Official objective:
- deploy the first trading algorithm for `ASH_COATED_OSMIUM` and
  `INTARIAN_PEPPER_ROOT`
- also participate in the manual Exchange Auction for extra profit

Official algorithm framing:
- `INTARIAN_PEPPER_ROOT` is relatively steady, similar in spirit to tutorial
  stable products
- `ASH_COATED_OSMIUM` appears more volatile and may contain hidden structure

Operational implication:
- Round 1 should be treated as a two-product market with different regimes, not
  as a single generic mean-reversion problem

## Round 1: soft strategic hints from prompt cards

The uploaded prompt-hint context is **not formal rules**, but it contains
important directional clues.

### Pepper Root hints

`INTARIAN_PEPPER_ROOT` is described as:
- slow growth
- predictable supply
- no drama

Yet the prompt cards suggest:
- subtle directional leaning can exist
- repeated moods or micro-regimes may exist
- spread behavior can sometimes encode intent rather than noise

Useful hypothesis families:
- small repeated drift
- order-book imbalance persistence
- spread-state persistence
- “lean before move” behavior
- subtle regime detection rather than loud trend detection

### Quoting / execution hints

The prompt cards warn against:
- conspicuously eager pricing
- outsized size that broadcasts urgency
- orders that look too generous or rushed

Useful execution hypotheses:
- calmer fair-relative quoting may preserve more edge than naive aggression
- context-matched sizing may outperform fixed sizing
- spread state and book “mood” may matter for placement
- patience can be a decision variable, not just price

### What these hints do NOT prove

Do not overclaim that the prompt cards prove:
- trend-following beats mean reversion
- spread predicts returns in a specific way
- aggressive orders are always wrong
- any exact model family must win Round 1

Treat them as strong clues to test, not settled truth.

## Round 2: official facts

Round name:
- `Growing Your Outpost`

Official objective:
- continue trading the same two products
- refine the algorithm
- optionally bid for extra market access using `bid()`

### Market Access Fee (MAF)

Round 2 introduces a **blind auction** for extra flow.

Facts:
- accepted bids get access to **25% more quotes**
- acceptance depends on being in the **top 50% of bids**
- if accepted, you pay your own bid as a **one-time fee**
- if not accepted, you pay nothing and remain on the base quote set
- the MAF affects Round 2 profit only through the fee and extra flow; it does
  **not** change simulation dynamics beyond quote access
- `bid()` is unique to Round 2 and is ignored in other rounds

Example logic from official doc:
- bids above the median threshold are accepted
- you do **not** need the highest bid, only a bid high enough to land in the
  top half

### Testing caveat in Round 2

Official Round 2 doc says:
- during testing, the visible quote set defaults to **80%** of all generated
  quotes, i.e. no extra market access
- this 80% is slightly randomized per submission
- repeated resubmission can slightly change visible outcomes but the payoff from
  gaming that randomness is limited

Operational implication:
- treat local/hosted testing noise carefully
- do not mistake slightly changed submission outcomes for proof of a structural
  edge
- separate “strategy quality” from “MAF game-theory choice”

### Practical MAF implications

Safe conclusions:
- MAF sizing is a game-theory problem, not a signal-model problem
- extremely high bids can secure access but may destroy net PnL
- the optimum is likely near the acceptance boundary, not at the maximum bid
- because MAF is ignored outside final comparison, backtests that do not model
  accepted extra flow cannot tell you the true best bid directly

## Round 2: algorithm strategy implications

Keep these layers separate:

1. **Core trader quality**
   - edge on the two products
   - fair value
   - taking thresholds
   - passive execution quality
   - inventory control
2. **MAF choice**
   - how much extra flow is worth in expectation
   - how much to sacrifice in guaranteed fee cost to reach top-half acceptance

A poor core trader with a good MAF guess is still weak.
A strong core trader can be harmed by an unnecessarily large MAF.

## Submission-compatibility rules that matter in both rounds

- Hosted submissions generate a UUID-style submission identifier and a run ID;
  keep them when analyzing official results or asking staff/debugging hosted
  behavior.

- Return the official 3-tuple shape even if local tools accept looser shapes.
- Prefer `traderData` over hidden instance state.
- Keep persistence compact enough for the hosted 50k truncation limit.
- Size orders against the official position limits, not against optimistic local
  fill assumptions.
- Separate official facts from backtester-specific behavior.

## Backtester-aware caveats for algorithm work

These are local-repo caveats, not official exchange rules:

- The uploaded Rust backtester context says the Rust engine is the **primary**
  local validator for this repo.
- That same context says the Rust engine captures conversions but does **not**
  simulate them, and CSV ingestion does **not** load observation CSV files.
- The uploaded Python backtester context says the older Python engine also does
  not actually simulate conversions, even though the trader can return a
  conversion request.
- Therefore, conversion-heavy ideas are not faithfully tested by the documented
  local tools.

## Minimal checklist for any algorithm task

Before editing or evaluating a trader, confirm all of the following:

- Which round?
- Which dataset?
- Which trader file?
- Are you working on tutorial data or live round data?
- Are you relying on official facts or on narrative hints?
- Are you evaluating core alpha / execution or MAF game theory?
- Are you assuming conversion behavior that the documented local backtesters do
  not actually simulate?

## High-value condensed reminders

- `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT` are the official Round 1 and
  Round 2 algorithmic products in the uploaded docs.
- Pepper Root may still hide subtle short-horizon structure despite looking
  stable.
- Spread state may be signal, not only cost.
- Avoid visibly desperate quote placement.
- Round 2 `bid()` only matters in Round 2.
- Top-half bidding, not highest bidding, wins extra flow.
- Hosted persistence should go through `traderData`, not mutable globals.
