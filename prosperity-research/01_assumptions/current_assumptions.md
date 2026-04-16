# Prosperity 4 Round 1 Current Assumptions

Date: 2026-04-16

Scope: This note is limited to verified facts from these two files only:
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/Prosperity Context/Official Prosperity Context.md`
- `/Users/tahakhan/Documents/Work/Projects/Prosperity/Prosperity Context/Official Prosperity Context Round 1.md`

It focuses on Round 1 products, limits, trader interface constraints, and Round 1 mechanics relevant to `ASH_COATED_OSMIUM`.

## Verified Official Facts

### Round 1 products and limits

- Round 1 algorithmic trading uses exactly these products:
  - `ASH_COATED_OSMIUM`
  - `INTARIAN_PEPPER_ROOT`
- The Round 1 position limits are:
  - `ASH_COATED_OSMIUM`: `80`
  - `INTARIAN_PEPPER_ROOT`: `80`

### Round 1 product notes relevant to Ash

- The Round 1 briefing states that `ASH_COATED_OSMIUM` is "rumored to be a bit more volatile".
- The Round 1 briefing also states that its "apparent unpredictability may follow a hidden pattern".
- No stronger official product-specific trading rule, fair value anchor, or explicit generator mechanic for Ash is disclosed in the two source files.

### Submission interface constraints

- A submission must define a Python `Trader` class.
- The required method is `run(self, state)`.
- A `bid()` method is only relevant for Round 2. It may exist in submissions for other rounds, but it is ignored outside Round 2.
- The `run()` method returns `(result, conversions, traderData)`.
- `result` is a dictionary keyed by product name, with values that are lists of `Order` objects.
- In `OrderDepth.sell_orders`, sell quantities are negative.

### TradingState and persistence facts

- The simulation calls `run()` once per iteration with a `TradingState`.
- `TradingState` includes at least:
  - `order_depths`
  - `own_trades`
  - `market_trades`
  - `position`
  - `observations`
  - `traderData`
- Outstanding player quotes that are not traded on by bots are automatically cancelled at the end of the iteration.
- The trading container is stateless across calls. Class variables and globals are not guaranteed to persist.
- `traderData` is the official persistence mechanism between calls.
- The official context warns that `traderData` may be truncated to `50_000` characters.

### Exchange and risk constraints

- Position limits are enforced per product on an absolute basis.
- If the orders sent in an iteration would, under full execution, push the position beyond the limit, the exchange rejects the orders.
- Orders that can immediately match against existing bot quotes execute without delay.

### Round 1-specific mechanics

- The Round 1 objective is to earn a net profit of `200,000` XIRECs or more before the beginning of the third trading day.
- Round 1 also includes an Exchange Auction alongside the algorithmic trading challenge.
- Trading days on Intara last `72` hours.

## Inferred Working Assumptions

These are working assumptions for repo use. They are not official statements from the two files above.

- Round 1 Ash strategy work should focus on continuous-book trading logic, not the Exchange Auction.
- Because no Ash conversion mechanic is described in the Round 1 briefing, conversions should not be assumed to be part of the Ash edge without other evidence.
- Any Ash state that must persist across calls should be kept compact and passed through `traderData`, not globals or instance state.
- The Round 1 Ash note implies hidden structure may exist, but it does not specify whether that structure is mean-reverting, trend-following, regime-based, or event-based.

## Unknowns Not Settled By The Official Files

- The true price-generation or hidden-pattern mechanics for `ASH_COATED_OSMIUM`.
- Whether Ash has a stable anchor price.
- Whether Ash rewards passive market making, directional trading, spike fading, or some combination.
- Whether there are Ash-specific observation fields or non-book signals that matter in Round 1.

## Guardrails For Current Repo Work

- Keep Round 1 reasoning restricted to `ASH_COATED_OSMIUM` and `INTARIAN_PEPPER_ROOT`.
- Do not mix tutorial products into Round 1 logic.
- Preserve the official Round 1 `Trader` interface and position-limit safety rules.
