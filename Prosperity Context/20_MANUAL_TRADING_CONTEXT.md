# Manual Trading Context (Rounds 1 and 2)

## Scope

This file condenses the manual-trading facts from the uploaded Prosperity 4
materials.

It covers:
- Round 1 Exchange Auction
- Round 2 Invest & Expand

It also captures the Round 1 prompt-card hints that materially affect auction
reasoning.

## Relationship to algorithmic trading

The uploaded uplinks explicitly frame the manual challenge as a separate,
one-off opportunity that does **not** alter the mechanics of the algorithmic
challenge. Treat manual work as an independent profit source.

## Round 1 manual challenge: Exchange Auction

### Provenance note

For Round 1 manual work:
- the official Round 1 doc confirms that an **Exchange Auction** exists as a
  side task
- the detailed product/mechanics below come from the uploaded `ARIA Uplink.md`
  summary rather than the written Round 1 official page

Therefore, treat the detailed auction mechanics below as lower-authority than a
future direct UI export or official written auction page, while still retaining
all of them because they are likely important.

### Official and narrative facts

The uploaded Round 1 materials describe a manual exchange auction with:

Products:
- `ember mushrooms`
- `dryland flax`

Mechanics:
- the order books are **static / frozen**
- only final submitted participant orders affect the outcome
- the auction determines a **single clearing price**
- primary objective of the clearing rule is **maximum traded volume**
- if multiple prices achieve the same total volume, the tie is broken in favor
  of the **higher price**
- price-time priority applies among same-price orders
- after the auction clears, there is **no continuous trading**

Post-auction liquidation / terminal value:
- dryland flax can be sold for `30` Zyrex per piece
- ember mushrooms can be sold for `20` Zyrex per piece

Fee:
- ember mushrooms incur a `0.05` Zyrex per-unit fee on both buys and sells

Operational implication:
- this is not “submit and forget”; the final order can change the clearing
  outcome and therefore the total payoff

### Strategy-relevant Round 1 auction hints

The uploaded prompt-hint file strongly suggests:

- your final order can move the clearing price
- you should simulate the marginal effect of both **price** and **size**
- candidate clear prices may form stable basins or snap points
- bunching in aggregate supply/demand curves is likely informative

Suggested workflow:
1. reconstruct the standing demand/supply schedule
2. simulate candidate final orders
3. measure resulting clearing price, fill, and profit
4. identify stable local basins and bunching points
5. choose the order that maximizes payoff, not just fill probability

### What not to overclaim for Round 1 auction

The hint file does **not** prove:
- the exact hidden auction implementation beyond the official volume-first,
  higher-price-tiebreak description
- that a more aggressive final order is always better
- that the best action always moves the clear instead of joining it

Treat the prompt-card material as directional guidance below official rules.

## Round 2 manual challenge: Invest & Expand

### Official facts

Round name:
- `Invest & Expand`

Budget:
- `50,000 XIRECs`

Decision variables:
- allocate percentages across three pillars:
  - `Research`
  - `Scale`
  - `Speed`

Constraints:
- choose each pillar as a percentage in `0–100`
- total allocation cannot exceed `100`

Objective:
- maximize final PnL, where the official uploaded formula is

`PnL = (Research × Scale × Speed) - Budget_Used`

### Pillar definitions

#### Research

- Represents trading edge / alpha capacity.
- Grows **logarithmically** from `0` at `0` invested to `200,000` at `100`
  invested.
- Uploaded exact formula:

`research(x) = 200_000 * np.log(1 + x) / np.log(1 + 100)`

Implication:
- very high marginal value early
- diminishing marginal returns later

#### Scale

- Represents breadth of deployment across markets.
- Grows **linearly** from `0` at `0` invested to `7` at `100` invested.

Implication:
- constant marginal effect per extra unit invested

#### Speed

- Represents execution / hit-rate advantage.
- Is **rank-based across all players**, not a simple function of your raw spend.
- Highest speed investor gets `0.9`.
- Lowest gets `0.1`.
- Players in between are linearly interpolated by **rank**.
- Equal speed investments share the same rank.

Implication:
- Speed is a competitive positioning problem, not an isolated optimization
- its value depends on where others cluster

### Strategic implications for Round 2 manual play

Safe high-level conclusions:
- Research has diminishing returns and usually dominates early allocations.
- Scale is predictable and linear.
- Speed is discontinuous in strategic value because it depends on the crowd.
- Because Speed is rank-based, you should think in terms of threshold placement
  and crowd distributions, not just raw percentage.
- A solution that ignores the budget deduction can overinvest and lose net PnL.
- Unused budget is allowed implicitly because total allocation cannot exceed 100
  and the formula subtracts only the used budget.

### What to model

A good solver should model:
- the exact Research log curve
- the Scale linear curve
- the budget deduction
- rank-based Speed under plausible competitor allocations
- sensitivity to ties and clustered speed bids

### What not to assume

Do not assume:
- the optimal plan spends 100% of the budget
- Speed should always be maximized
- the best solution can be found from single-player calculus alone
- the crowd distribution is smooth or uniform

## Cross-round manual reminders

- Round 1 manual work is an auction-clearing optimization problem.
- Round 2 manual work is a budget-allocation / game-theory problem.
- Manual tasks are independent of the algorithmic task mechanics.
- Do not let lower-authority narrative wording override official formulas or
  clearing rules.

## Condensed handoff

Round 1 manual work:
- frozen book
- single clearing price
- maximize payoff through order-price/order-size simulation
- include terminal values and mushroom fees

Round 2 manual work:
- optimize `(Research × Scale × Speed) - Budget_Used`
- Research is logarithmic
- Scale is linear
- Speed is rank-based across players
- model competitor-response scenarios, especially for Speed
