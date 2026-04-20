# chrispyroberts/imc-prosperity-3

## Why it matters

This repo is useful because it shows a full competition workflow rather than a single polished final file. The repository is split by round and includes final trading files, exploratory notebooks, manual-trading work, grid-search scripts, backtest artifacts, and CSV parameter sweeps. The code also makes the team’s style very legible: simple fair-value proxies, aggressive spread capture when they believe they have edge, hard position caps, and repeated reuse of old round logic as new products are layered in.

It is also valuable because you can see the evolution of the strategy stack across rounds:
- Round 1: basic market making and taking in book-driven products.
- Round 2: basket-premium stat arb plus residual market making.
- Round 3: volatility-surface-based option market making with delta hedging.
- Round 4: same option engine kept, but risk posture relaxed and conversion arbitrage added.
- Round 5: counterparty-ID alpha added on top of the existing stack, especially Olivia-following logic.

The most important lesson is not any one threshold. It is the workflow: detect a simple edge, express it with very direct execution logic, then optimize a small number of parameters with backtests instead of overcomplicating the model.

## What the team appears to believe about the market

The code suggests several strong beliefs:

1. **Simple book-derived fair value is often enough.**
   For Rainforest Resin, Kelp, Squid Ink, and later even basket market making, they repeatedly define fair value as the midpoint of the visible book and then quote around it. They do not try to fit elaborate predictive models for these products.

2. **Aggressive taking is justified when the edge is clear.**
   The search functions sweep up to three levels of the book whenever prices are better than fair value. In baskets and Olivia-following legs, they often go straight to the best bid/ask instead of waiting passively.

3. **A large part of edge comes from structure, not forecasting.**
   Basket premiums, option IV smiles, and conversion break-even prices are all structural transforms of the market. The code repeatedly trades residual mispricings around those transforms.

4. **Signals can be counterparty-specific.**
   In Round 5 they explicitly monitor trades by `Olivia` across `SQUID_INK`, `KELP`, and `CROISSANTS`, then use that to override or suppress the default quoting logic.

5. **Inventory is something to bound, not necessarily eliminate.**
   Earlier option code delta-hedges. Later code keeps the hedge plumbing but effectively disables underlying hedging, implying the team decided spread costs were larger than the residual underlying risk in that environment.

6. **Competition code can be cumulative and pragmatic.**
   Later round files keep older round logic inside one growing `Trader` class. This is fast to iterate with, even if it is not clean production architecture.

## Products / rounds covered

- **ROUND 1 / `final_round_1_trader.py`**
  `RAINFOREST_RESIN`, `KELP`, `SQUID_INK`

- **ROUND 2 / `FINAL_FRENCH_GUY.py`**
  Keeps Round 1 logic and adds `CROISSANTS`, `JAMS`, `DJEMBES`, `PICNIC_BASKET1`, `PICNIC_BASKET2`

- **ROUND 3 / `big_volcano_man.py`**
  Keeps earlier logic and adds `VOLCANIC_ROCK` plus all five voucher strikes

- **ROUND 4 / `algo run for round 4.py`**
  Keeps prior stack and adds `MAGNIFICENT_MACARONS`

- **ROUND 5 / `OLIVIA IS THE GOAT.py`**
  Keeps the earlier stack and adds counterparty-based signal following, mainly around Olivia

## Fair value logic

### Round 1

**Rainforest Resin**
- Fair value is hard-coded as `10000`.
- The strategy takes anything better than 10000 and then quotes inside the spread.
- If someone is already quoting better, it simply steps one tick inside them.

This is a classic fixed-anchor market-making strategy.

**Kelp**
- Fair value is the midpoint of the visible book, computed from the worst displayed ask and bid in the dictionary ordering they use.
- It then market-takes any prices better than that midpoint and quotes around it.
- If the best competing quote is still on the correct side of fair value, it joins one tick better.

So Kelp is treated as a drifting but still book-revealed fair-value product.

**Squid Ink**
- In the earliest file, Squid Ink uses the same midpoint-based fair value as Kelp.
- The more interesting part is that the file overlays volatility and trend logic to selectively turn off one side of quoting or to “full send” against extreme volatility moves.

That means the fair value is still local midpoint, but execution aggressiveness is conditioned on volatility regime.

### Round 2

**Baskets**
- Theoretical basket values are computed exactly from constituents:
  - `basket1_theo = 6*CROISSANTS + 3*JAMS + 1*DJEMBES`
  - `basket2_theo = 4*CROISSANTS + 2*JAMS`
- Premiums are defined as actual basket mid minus theoretical value.
- The main signal is the difference between basket premiums:
  - `premium_diff = basket1_premium - basket2_premium`
- They use hard-coded long-run means and rolling standard deviations to form z-scores.

This is a clean residual-value model: fair value is synthetic NAV plus an empirically learned premium baseline.

### Round 3

**Volcanic Rock vouchers**
- They fit implied volatility as a quadratic function of moneyness.
- Moneyness is `log(S/K) / sqrt(T)` in code.
- They use separate fitted coefficients for bid-side and ask-side vol, then convert those to Black-Scholes bid and ask values.
- That generates an internal fair market for each voucher.

This is the strongest model-based fair-value component in the repo.

### Round 4

**Macarons**
- Fair value is not forecast from sunlight or sugar despite the README discussion.
- Instead, the code computes conversion break-even prices directly from observed conversion prices, tariffs, and transport costs.
- It then places local sell quotes at or above the break-even sell level.

So the Macarons code is pure conversion-value trading, not a predictive commodity model.

### Round 5

**Olivia signal products**
- Fair value itself is mostly unchanged from older files.
- What changes is the decision priority: if Olivia has traded, the strategy treats her action as the dominant signal and may stop doing the default stat-arb or market-making behavior on that product family.

The repo therefore distinguishes between **value estimation** and **signal hierarchy**.

## Execution logic

### Taking logic

Across the repo, the basic taking primitive is reusable and simple:
- `search_buys` sweeps sell orders at prices below acceptable fair value.
- `search_sells` sweeps buy orders above acceptable fair value.
- Depth is usually capped at 3 levels.

That means the default execution pattern is:
1. compute a fair value
2. immediately lift/hit clearly mispriced liquidity
3. only then place passive quotes

This is used in Round 1 products, reused in basket market making, and mirrored in options where they cross existing quotes when their IV-based market is better.

### Passive quote logic

The standard quote engine is highly consistent across products:
- start with midpoint-based quotes, typically `fair - 2` and `fair + 2`
- inspect existing best quotes
- if another trader is quoting more aggressively but still on the correct side of fair value, step one tick inside them
- quote the remaining size up to a position cap

This same pattern appears in Resin, Kelp, Squid, and later basket market making.

### Squid Ink execution evolution

Round 1 Squid uses directional heuristics to disable one side of the market when short-window and long-window means diverge, and it turns both sides back on when inventory gets too large.

By Round 2 onward, Squid becomes cleaner:
- market make by default with reduced size
- detect spikes using a threshold on recent price differences
- if a spike is detected, fully buy or sell the book based on the deviation from the long-window mean

That is a much more modular design: quote in normal conditions, cross aggressively only on shock regimes.

### Basket execution

The basket logic is not abstract statistical arbitrage in the code. It is concrete multi-leg sizing:
- determine all required hedge ratios from the basket definitions
- compute the maximum executable size based on visible constituent volumes and position limits
- fire every leg immediately so the submitted basket trade is hedged by construction

This is one of the best parts of the repo. The team avoids complex post-fill hedge repair by only sending sizes that already fit the hedge ratios.

### Option execution

The option logic makes a bid/ask from an IV smile fit, then:
- crosses existing quotes if their computed bid is above market asks or their computed ask is below market bids
- after crossing, re-posts around its own fair values
- caps position per voucher

So it is both a taker and a market maker. It is not waiting passively for mispricings to come to it.

### Macarons execution

The Macarons code is brutally simple:
- convert existing inventory toward flat, limited by the per-step conversion cap
- compute local sell break-even from conversion economics
- place a large local sell order at that threshold or above

This is not a two-sided conversion market maker. It is a one-sided extraction of a repeatedly favorable local-selling edge.

### Olivia execution

Round 5 adds event-driven execution:
- detect Olivia’s prints in current-step own trades and market trades
- set directional signals by product
- if Olivia buys Croissants, go long Croissants and both baskets while selling Jams and Djembes
- if Olivia sells Croissants, do the reverse
- if Olivia trades Squid, stop relying on the default Squid logic and simply follow the signal

This is an example of a codebase moving from “mispricing trading” to “agent-response trading”.

## Inventory / risk logic

### Shared inventory mechanics

Inventory control is mostly implemented through hard limits and local max-size calculations:
- each product has an explicit limit
- outstanding order sizes are tracked separately from filled inventory
- every quoting function computes `max_buy` and `max_sell` from position plus already-sent orders

This is one of the repo’s more reusable ideas.

### Round 1 risk handling

- Resin and Kelp are straightforward capped market makers.
- Squid adds a crude regime switch: reduce exposure via one-sided quoting when it detects trend or high volatility.
- There is also logic to reopen both quote sides when inventory approaches the position limit.

So inventory is managed with a mixture of hard caps and quote-direction throttling.

### Basket risk handling

The round 2 basket code is almost always hedge-first.
- Basket 1 trades are paired against Basket 2 and constituents.
- Basket 2 trades are paired against Croissants and Jams.
- The code computes the smallest executable quantity across all legs before trading.

This is strong because it avoids accidental partial hedges from naive basket sizing.

There is also a second inventory layer for basket market making:
- `basket2_market_make_pos` is tracked separately from the strategy’s stat-arb positions.
- fills from the previous turn update that MM-only position state.

That separation is clever and worth reusing.

### Option risk handling

Round 3 is the most explicitly risk-managed part of the repo:
- deltas are estimated for every voucher
- total portfolio delta is summed
- the strategy trades `VOLCANIC_ROCK` to offset it
- voucher position caps are intentionally reduced so the hedge is always tractable

By Round 4 and Round 5, the hedge machinery remains in the code, but `trade_underlying` defaults to `dont_hedge=True`, so the hedge path returns immediately unless manually re-enabled.

This is a very important repo-level lesson: **the team did not just build one options strategy, they actively changed the risk posture when they decided hedging costs dominated the benefit**.

### Conversion risk handling

Macarons risk is managed in a competition-specific way:
- convert existing inventory in chunks up to 10
- hold a persistent short bias to exploit negative import tariff economics
- accept some inventory and price-move risk in exchange for materially higher throughput

This is economically sensible for that dataset, but highly round-specific.

## State / memory usage

A notable feature of this repo is that it mostly **does not** use serialized `traderData` in any meaningful way.
- `self.traderData` is usually initialized to `"SAMPLE"`
- rolling windows, previous prices, signal flags, and MM inventory are all stored in normal instance attributes
- later `run()` methods return `self.traderData` unchanged

That means the repo assumes in-process object persistence rather than building a portable state-serialization layer.

This makes iteration faster, but it is less robust than repos that deliberately serialize compact state and reconstruct it every timestep.

## Backtesting / diagnostics workflow

The repo’s workflow is visible from its structure, not just the README:
- round folders contain notebooks like `analysis.ipynb`, `bottleeda.ipynb`, `round 5 analysis.ipynb`
- there are explicit optimizer scripts in Round 1 and Round 5
- there are saved CSV search results such as `dense_window_optimization.csv`, `basket_gridsearch_results.csv`, and voucher grid-search outputs
- there is a `backtests` folder in Round 1

The optimizer scripts are revealing:
- they copy a trader file to a temp file
- use regex substitution to patch parameter values into code
- run the backtester via `python -m prosperity3bt ...`
- scrape `Total profit:` from stdout
- sort all parameter combinations by PnL and save to CSV

This is a very pragmatic workflow. It is not elegant, but it is fast and reproducible enough for a competition.

Diagnostics inside the strategy files also matter:
- several files include a logger that compresses state, orders, trades, and observations into bounded JSON output
- there are counters like `total_trades`, `total_takes`, `total_hedges`, `total_exits`, and `total_fills`
- some methods update separate MM positions from filled trades on the previous turn

The big workflow takeaway is that this team likes **simple parameterized strategies + brute-force tuning + lots of logging**.

## Architecture choices

The repo’s architecture is practical rather than elegant.

### What it does well

1. **Round-based organization**
   Each round gets its own folder with code, notebooks, and supporting data.

2. **Single-file competition deployment**
   Each round’s live strategy is mostly one `Trader` class in one file. This makes submission simple.

3. **Code reuse across rounds**
   Later round trader files keep older round methods and add new sections below them. This lets them reuse tested logic quickly.

4. **Reusable primitives**
   Many helpers are reused across all products:
   - `search_buys`
   - `search_sells`
   - `get_bid`
   - `get_ask`
   - send-order helpers
   - standardized reset methods

### What it does poorly

1. **Monolithic accumulation**
   By Round 4 and Round 5, the trader files are large and contain old logic, new logic, partially disabled logic, and several overlapping strategy ideas in one class.

2. **State is not modularized**
   Product-specific state all lives on the same object.

3. **Some code paths are clearly experimental or stale**
   There are commented-out runs, alternate thresholds, and strategy variants that look like they were kept for convenience.

So the architecture is good for speed under deadline pressure, but not ideal for maintainability or agent reuse without refactoring.

## What looks robust

The most reusable and genuinely strong ideas in this repo are:

### 1. Mispricing-first execution template
Compute fair value, sweep obvious edge, then quote the remainder. This is a very transferable pattern.

### 2. Multi-leg size calculation before trading baskets
Their basket code sizes every leg from visible liquidity and limits before sending anything. This is much safer than “trade first, hedge later”.

### 3. Internal model price for options
The IV-smile-to-Black-Scholes pipeline is a good example of turning descriptive analysis into executable pricing.

### 4. Position accounting with outstanding-order tracking
They repeatedly subtract already-sent buy/sell orders from remaining capacity. This is simple and very useful.

### 5. Separate residual market making after alpha trading
In baskets and options, they often do alpha trading first and then use leftover capacity for passive quoting. That layered structure is worth copying.

### 6. Parameter search infrastructure
Even though the implementation is rough, the habit is right: define a few knobs, sweep them systematically, save results, inspect top runs.

### 7. Counterparty-aware signal routing
The Olivia code is not just “copy the trade”. It changes which sub-strategy is allowed to run. That kind of signal-priority logic is a strong design pattern.

## What looks round-specific

Several parts are clearly tied to Prosperity 3 mechanics or even to specific round datasets.

### 1. Exact hard-coded premium means and thresholds
The basket premium means, z-score thresholds, Squid thresholds, and voucher thresholds are all calibrated to their sample data and backtests.

### 2. The fitted IV smile coefficients
Those quadratic coefficients are extremely environment-specific.

### 3. Macarons one-sided economics
The conversion formula and especially the willingness to maintain a short stockpile rely on the exact tariff structure they observed.

### 4. Olivia-following logic
This is the clearest round-specific alpha in the repo. It only makes sense because the competition explicitly revealed counterparty IDs and because Olivia’s behavior was stable in their data.

### 5. Dictionary-order assumptions about the book
The code often uses the first or last item from order dictionaries as if that corresponds to best or worst price. That may match Prosperity datamodel ordering, but it is not a universally safe market-data assumption.

## What Codex should learn from this repo

Codex should learn the following patterns:

### 1. Build separate alpha engines for separate product types
Do not force one trading template onto every product. This repo uses:
- fixed-anchor market making
- midpoint market making
- shock-regime trading
- basket residual stat arb
- IV-surface option market making
- conversion arbitrage
- counterparty-following logic

### 2. Keep fair value simple unless structure forces complexity
Most products here do not use prediction models. The team only moves to heavier modeling when product design really demands it, as with options.

### 3. Hedge by construction where possible
The basket code is strong because the hedge ratio is embedded in the order generation step.

### 4. Treat execution as part of the alpha
Their best strategies are not just “predict price”. They carefully decide when to cross, when to quote, and how aggressively to size.

### 5. Use lightweight but explicit optimization loops
Agent-built strategies should support parameter sweeps, batch backtests, and CSV result dumps. This repo does that in a rough but effective way.

### 6. Support signal overrides
The Round 5 Olivia logic is a good example of a hierarchy:
- if strong counterparty signal exists, prioritize it
- otherwise run baseline market making or stat arb

That is often better than blending every signal into one score.

### 7. Track residual inventory separately by strategy sleeve
The `basket2_market_make_pos` idea is very useful. Separate alpha inventory from passive-MM inventory whenever possible.

## What Codex should NOT copy blindly

### 1. Do not copy the exact thresholds or coefficients
They are too tied to this team’s backtests and the Prosperity 3 environment.

### 2. Do not copy the monolithic file structure as-is
For an agent, it is better to refactor into:
- shared execution utils
- per-product strategy modules
- centralized config
- explicit backtest harness

### 3. Do not copy the state model blindly
Relying on instance attributes instead of serialized state is convenient, but brittle if runtime behavior changes or if you want portable replay/debugging.

### 4. Do not assume their order-book indexing convention is universally safe
The code often treats the first or last dictionary item as economically meaningful. Revalidate this in your own backtester.

### 5. Do not assume hedging should be on just because hedge code exists
Round 4 and Round 5 keep delta-hedge code but effectively disable it. Agents should infer the intended behavior from the active path, not from dead code.

### 6. Do not assume every file is a literal final submission snapshot
This repo is part writeup, part experiment log, part evolving codebase. There are inactive branches, commented-out run paths, and old logic retained in later files.

### 7. Do not copy Macarons logic without re-deriving the economics
That code depends on exact tariff signs, conversion limits, and observed local-flow behavior.

## Source files inspected

Primary code inspected for this note:
- `ROUND 1/final_round_1_trader.py`
- `ROUND 2/FINAL_FRENCH_GUY.py`
- `ROUND 3/big_volcano_man.py`
- `ROUND 4/algo run for round 4.py`
- `ROUND5/OLIVIA IS THE GOAT.py`
- `ROUND 1/optimizer.py`
- `ROUND5/optimizer.py`

Supporting repo context inspected:
- repo root structure
- README round descriptions and workflow notes
