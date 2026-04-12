# Prosperity 4 - Claude Code Context Pack

## What this document is

This is a single context pack for building IMC Prosperity 4 trading code with Claude Code.

It is designed to give Claude the information it actually needs:
- the competition structure
- the trading environment and syntax
- the hard constraints that will break submissions
- the main strategy patterns that have worked in previous Prosperity editions
- the architecture and workflow Claude should build around

## Important source caveat

The public Notion link provided for the Prosperity 4 Wiki returned a public 404 when accessed. Because of that, this pack is grounded in:
1. the official Prosperity 4 website and terms
2. the public Google Doc you provided on syntax
3. Mark Brezina's public guide repo
4. public writeups from strong previous teams

Anything in this document marked as a pattern, hypothesis, or previous-year lesson should be treated as guidance, not as an official Prosperity 4 rule.

---

# 1. Official competition picture

## Core format
Prosperity 4 is a five-round team-based trading challenge. Each round has:
- 1 algorithmic challenge
- 1 manual challenge

The algorithmic and manual scores are independent, but both contribute to overall standing.

## Dates and structure
Official schedule:
- Tutorial round: March 16 to April 13
- Round 1: April 14 to 17
- Round 2: April 17 to 20
- Intermission: April 20 to 24
- Round 3: April 24 to 26
- Round 4: April 26 to 28
- Round 5: April 28 to 30

## Team structure
- Teams can have up to 5 players.
- Team composition can change during the first two rounds.
- After Round 2, teams are locked.

## Objective
Build Python trading code that maximizes simulated PnL in the market environment for each round.

## Ranking and prizes
The final ranking is based on final simulated account balance.
If two teams tie, the earlier final algorithm submission is ranked higher.
Prize pool:
- 1st: USD 25,000
- 2nd: USD 10,000
- 3rd: USD 5,000
- 4th: USD 3,500
- 5th: USD 1,500
- Manual top score: USD 5,000

## Practical competition interpretation
For coding purposes, the most important implications are:
- every round can change the tradable products and mechanics
- you should expect new product types and new edges rather than one universal strategy
- the tutorial round is useful for environment understanding, logging, and pipeline setup even if later rounds differ materially

---

# 2. Trading environment and syntax you must respect

## Submission shape
Your submission is a Python file containing a `Trader` class.

The key method is:
- `run(self, state: TradingState)`

For Algorithmic Round 2, the syntax doc says the trader should also define:
- `bid(self)`

It is safe to include `bid()` in all rounds. It will only matter where the round uses it.

## What `run()` returns
`run()` returns a triple:

1. `result`
   - dictionary mapping product name -> list of `Order`
2. `conversions`
   - integer conversion request count
3. `traderData`
   - string used to persist state across calls

Conceptually:

```python
return result, conversions, traderData
```

## Key objects

### TradingState
This is the market snapshot passed into `run()`. The important fields are:

- `traderData`
- `timestamp`
- `listings`
- `order_depths`
- `own_trades`
- `market_trades`
- `position`
- `observations`

### OrderDepth
For each product:
- `buy_orders`: dict of price -> positive quantity
- `sell_orders`: dict of price -> negative quantity

That negative sign on `sell_orders` matters and is an easy source of bugs.

### Order
Each order has:
- `symbol`
- `price`
- `quantity`

Quantity sign convention:
- positive quantity = buy
- negative quantity = sell

### Trade
Trade objects contain:
- `symbol`
- `price`
- `quantity`
- `buyer`
- `seller`
- `timestamp`

Counterparty info is usually hidden unless your own submission is involved. In that case buyer or seller may be `"SUBMISSION"`. In previous editions, counterparty information sometimes became strategically useful later in the challenge.

### Observations / conversions
The syntax page describes:
- `plainValueObservations`
- `conversionObservations`

Conversion observations can include fields such as:
- bidPrice
- askPrice
- transportFees
- exportTariff
- importTariff
- sunlight / humidity style signals

These matter when a round introduces conversion-style trading between markets or locations.

## Matching and execution behaviour
The public syntax doc implies the following mechanics:
- you receive a full market snapshot each iteration
- you can immediately match against existing bot quotes by crossing them
- any unfilled remainder becomes your resting quote for that iteration
- if bots do not trade against your quote, it is automatically cancelled by the end of the iteration

This means you should think in terms of per-timestep decisions, not persistent orders across long horizons.

## Position limits
Position limits are enforced per product.
A crucial rule:

If the aggregate buy or sell quantity you submit in one iteration would breach the allowed position limit if fully filled, then all of those orders for that side/product can be rejected.

This means Claude must implement pre-trade position checks before emitting orders.

## Performance and environment constraints
The public syntax doc states:
- each `run()` call must respond within 900ms
- average runtime should be far below that
- `traderData` is truncated at 50,000 characters
- only supported Python libraries may be used
- external libraries are not supported

## Supported libraries
The syntax doc says Python 3.12 standard libraries are supported, and explicitly mentions:
- pandas
- NumPy
- statistics
- math
- typing
- jsonpickle

This means Claude should avoid any dependency outside the standard library plus these allowed packages.

## State persistence
Do not rely on class globals or process memory surviving between calls.
The syntax doc explicitly notes that the container is effectively stateless and that persistent strategy state should be serialized into `traderData`.

Best practice:
- keep `traderData` compact
- store only rolling features and state actually needed next tick
- avoid huge histories unless compressed or windowed
- prefer lightweight dictionaries or short arrays
- use jsonpickle only when useful, not by default everywhere

---

# 3. What the environment means strategically

The strongest repeated lesson from public Prosperity writeups is this:

Do not start by throwing generic quant indicators at every product.

Start by asking:
1. what is the hidden fair value or anchor?
2. what type of bot behaviour is being simulated?
3. where is the edge: spread capture, predictable reversion, relationship arbitrage, conversion arbitrage, or trader-ID information?
4. how do the mechanics of the environment change what would normally matter in real markets?

In other words, Prosperity is often less about beautiful forecasting models and more about reverse-engineering the simulation.

---

# 4. High-probability strategy patterns from previous successful teams

These are not guaranteed Prosperity 4 truths. They are recurring patterns from prior editions and strong public writeups.

## Pattern A: stable fair-value product
Recurring setup:
- one product is almost stationary
- fair value is effectively constant or very tightly anchored

Typical playbook:
- aggressively take quotes that are clearly better than fair value
- market make around fair value
- flatten inventory near zero-edge levels to free position capacity
- tune spread/edge versus fill probability

Previous high-performing teams repeatedly used this pattern on assets like AMETHYSTS or Rainforest Resin.

## Pattern B: slowly moving product with noisy order book
Recurring setup:
- price moves, but not in a highly forecastable way
- naive mid-price is noisy
- one larger market maker or quote wall can provide a better fair-value proxy

Typical playbook:
- estimate fair value from dominant large quotes or wall-mid rather than raw mid
- opportunistically take stale or mispriced quotes
- otherwise quote around that fair value
- use inventory management to avoid getting stuck at limits

A major repeated theme is that a robust fair estimator often beats a fancy predictive model.

## Pattern C: spiky / volatile product
Recurring setup:
- product has tighter spreads relative to movement
- occasional sharp spikes
- naive market making becomes high variance

Typical playbook:
- detect unusually large deviations relative to rolling volatility
- trade smaller
- apply mean-reversion or event-response logic
- use strict stop, time, or inventory controls
- do not assume every volatile product should be market made

Some teams used spike-detection plus mean reversion. Others found hidden trader behaviour instead.

## Pattern D: relationship / spread / basket arbitrage
Recurring setup:
- later rounds introduce products with structural links
- baskets, ETFs, synthetic products, or cross-asset relationships appear

Typical playbook:
- compute synthetic fair value from constituents
- trade the spread when it diverges enough from expected relationship
- size carefully under position constraints
- hedge the exposure if the round mechanics reward it
- debug position-limit logic early, because that is a common failure mode

## Pattern E: option-like products
Recurring setup:
- later rounds can include derivative-like instruments
- some strong teams used Black-Scholes or implied-volatility logic

Typical playbook:
- infer implied vol from market prices
- compare option prices against model values
- look for structure across strikes rather than one instrument in isolation
- use underlyings and related instruments together

## Pattern F: conversion / cross-market arbitrage
Recurring setup:
- one market plus another location or island
- conversion costs, tariffs, fees, transport, and extra observations

Typical playbook:
- calculate fully loaded cross-market economics
- include bid/ask, tariffs, and transport costs exactly
- understand conversion mechanics before scaling
- build conservative checks because misunderstanding conversions can destroy PnL
- adapt to regime variables such as environmental observations if the round uses them

## Pattern G: exploiting identifiable bot behaviour
Recurring setup:
- the most profitable edge is not in the price series itself
- it is in repeatable bot actions

Typical playbook:
- identify special agents, recurring order sizes, repeated extrema behaviour, or trader-ID signals
- build detection logic from market trades and book events
- trade the bot, not the chart

This is one of the biggest lessons from prior writeups: sometimes the edge is behavioural rather than statistical.

---

# 5. Lessons from public previous-team writeups

## Lesson 1: build tooling before trying to be clever
Strong public teams repeatedly emphasized:
- a backtester
- a visualizer / dashboard
- structured logs
- parameter sweeps or at least rapid configuration testing

Without tooling, you will spend too long guessing.

## Lesson 2: understand the simulator mechanics early
Public prior-team writeups repeatedly found edges by understanding details like:
- order lifetime
- sequential processing
- fair-value proxies used by the environment
- how conversions are charged
- when trader identity matters
- how inventory should be unwound

So Claude should prioritize simulator understanding over generic indicator libraries.

## Lesson 3: inventory management is not optional
Even when the edge is real, bad inventory handling can ruin results.
Repeated common behaviour:
- flatten near fair value
- skew quotes by current position
- reduce aggressiveness near limits
- use position to decide whether to take or rest

## Lesson 4: simple edges often outperform fancy models
Public strong teams frequently used:
- hardcoded fair values for stable assets
- rolling fair estimates for drifting assets
- simple spread signals
- direct arbitrage calculations
- trader-behaviour detection

That does not mean modeling is useless. It means you should only use complexity when the product demands it.

## Lesson 5: previous editions suggest a progression in product difficulty
A useful public rule of thumb:
- early rounds often reward fair value + market making
- mid rounds often add relationships and arbitrage
- later rounds may add derivative structure, conversions, regime variables, or extra information like trader IDs

Claude should therefore build reusable modules rather than one round-specific monolith.

---

# 6. Public guide takeaways from the Mark Brezina repo

This repo is unofficial, but it is useful because it organizes the challenge around actual implementation concerns.

## Useful takeaways
- think in terms of alpha type, not just indicators
- split work across research, execution/risk, and software/tooling
- tutorial rounds often contain one stable asset and one more dynamic asset
- market making, mean reversion, trend, pairs, basket arb, and order-flow ideas are all relevant families
- a toy moving-average strategy is easy to write but not sufficient on its own
- good execution and inventory management are what turn a weak edge into something usable
- the repo explicitly points newcomers toward prior strong team writeups rather than pretending there is one magic starter strategy

## Important caution
The repo also suggests it appears there may be no market impact or transaction fees. Treat that as a hypothesis to test in Prosperity 4, not as an official rule unless the live materials or data confirm it.

---

# 7. What Claude Code should build

Claude should not just build a single `trader.py` blob.

It should build a small competition system with modular pieces that can be recombined quickly between rounds.

## Required architecture
Claude should produce code with these components:

### A. Core state and utilities
- datamodel-compatible imports and wrappers
- compact serialization / deserialization for `traderData`
- helpers for best bid, best ask, mid, wall-mid, spread, book imbalance
- position-safe order builder
- logging helpers that can be turned on/off

### B. Execution layer
- functions to:
  - take favorable liquidity
  - place passive quotes
  - cap order size by position limits
  - skew quotes by inventory
  - flatten inventory when necessary

### C. Product-specific strategy modules
Claude should make each product pluggable.
Examples:
- `StableFairMarketMaker`
- `DynamicFairMarketMaker`
- `SpikeMeanReverter`
- `BasketArbitrageStrategy`
- `ConversionArbitrageStrategy`
- `CounterpartySignalStrategy`

### D. Fair-value estimation layer
The system should support multiple fair-value estimators:
- constant fair value
- simple mid-price
- rolling average
- dominant-quote / wall-mid
- synthetic basket fair
- model-derived fair
- foreign-market net fair after fees

### E. Risk and inventory layer
- hard position-limit checks
- product-level inventory targets
- quote skewing by current position
- emergency flattening logic
- optional cool-down logic after abnormal moves

### F. Research / backtesting support
Claude should create scripts for:
- loading sample trade CSVs and order-book CSVs
- reconstructing per-timestep state features
- testing fair-value estimates
- plotting spreads, inventory, fills, and PnL proxies
- parameter sweeps

If Claude cannot perfectly recreate the official engine, it should still build a research harness for feature inspection and idea testing.

---

# 8. Minimum viable algorithm blueprint for the tutorial / first round

If the first tradable products look like previous editions, Claude should begin with this baseline:

## Product type 1: anchored / stable product
- identify fixed or near-fixed fair value
- buy asks below fair
- sell bids above fair
- rest passive quotes around fair if spread allows positive edge
- flatten inventory near fair

## Product type 2: drifting but orderly product
- compute robust fair with rolling wall-mid or large-quote mid
- opportunistically take mispriced quotes
- quote around fair with configurable spread
- inventory-skew quoting
- simple optional short-horizon mean reversion only if data supports it

## Product type 3: volatile / jumpy product
- do not default to market making
- test:
  - spike reversal
  - short-window z-score signals
  - move-size filters
  - reduced size
- only keep it if backtests or sample diagnostics support it

---

# 9. Common failure modes Claude must avoid

## Syntax / environment failures
- wrong return signature
- forgetting `bid()` when the round requires it
- relying on globals instead of `traderData`
- oversize `traderData`
- using unsupported libraries
- too much compute inside `run()`

## Trading-logic failures
- mishandling negative quantities in `sell_orders`
- breaching aggregate position limits
- taking every apparent signal without inventory control
- using naive mid-price when a cleaner fair-value proxy exists
- treating conversions as free
- assuming a previous-year product maps exactly to a current-year product

## Research failures
- optimizing on one sample path and overfitting
- treating public writeups as exact blueprints rather than patterns
- spending too much time on generic ML before understanding the simulator
- ignoring manual challenges completely

---

# 10. Prioritized build plan for Claude Code

## Phase 1: environment-safe baseline
Build:
- working Trader class
- safe order builder
- state serialization
- best bid / ask / mid / wall-mid utilities
- stable-product market maker
- dynamic-product market maker
- lightweight logging

## Phase 2: research harness
Build:
- CSV readers
- feature extraction notebooks or scripts
- plots for price, spread, fair value, inventory, and trade events
- parameter config files
- local evaluation scripts

## Phase 3: strategy extensions
Add:
- spike mean reversion
- synthetic basket valuation
- conversion economics module
- counterparty / trade-pattern detection module

## Phase 4: round-specific adaptation
When a round opens:
1. inspect products and observations
2. classify each product by edge type
3. plug the right module in
4. validate position/risk logic
5. keep the simplest profitable version first
6. only then add complexity

---

# 11. Direct instructions to Claude Code

Use the following as the intended behaviour:

You are building a Prosperity 4 trading system in Python for the official submission environment.

Hard constraints:
- output valid Prosperity submission code
- use only standard Python 3.12 libraries plus pandas, NumPy, statistics, math, typing, and jsonpickle
- assume `run()` must finish comfortably within 900ms
- do not rely on globals surviving across calls
- persist necessary state in compact `traderData`
- enforce position limits before emitting orders
- handle negative sell-side quantities correctly
- support conversions and observations when relevant
- keep the system modular so new product logic can be inserted quickly round by round

Build order:
1. create a clean submission-safe Trader skeleton
2. implement reusable execution, fair-value, and risk utilities
3. implement strong baselines for:
   - fixed-fair-value market making
   - rolling-fair-value market making
   - spike mean reversion
4. create research scripts for sample CSV analysis
5. add optional modules for basket arb, conversion arb, and counterparty-based signals
6. keep code readable, configurable, and fast

Strategic philosophy:
- reverse-engineer the market mechanics first
- prefer simple robust edges over fancy models
- use public previous-team ideas as templates, not as assumptions about Prosperity 4
- optimize for fast adaptation between rounds

---

# 12. Best single-sentence mental model

Prosperity is usually won by teams that combine simulator understanding, strong tooling, clean fair-value estimation, disciplined inventory control, and quick adaptation to each round's specific market structure.

---

# 13. Source notes used for this pack

## Official / primary
- Official Prosperity 4 website
- Official Prosperity 4 terms and conditions PDF
- Public Google Doc on Trader syntax / TradingState / datamodel / supported libraries

## Secondary but useful
- Mark Brezina's `Ctrl-Alt-DefeatTheMarket` guide repo
- Public prior-team writeups including:
  - TimoDiehm `imc-prosperity-3`
  - CarterT27 `imc-prosperity-3`
  - ericcccsliu `imc-prosperity-2`
- Public community tools:
  - jmerle backtester
  - jmerle visualizer

## Final caveat
The exact public Notion URL supplied for the Prosperity 4 Wiki was not accessible, so this pack should be treated as a best-effort, high-signal context document built from corroborated public sources rather than a full mirror of the internal challenge wiki.