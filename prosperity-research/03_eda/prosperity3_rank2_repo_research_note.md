# Repo name

**TimoDiehm/imc-prosperity-3**

## Why it matters

This repo matters because it is not just a writeup from a strong team, it is the published final strategy file from a team that finished 2nd globally in Prosperity 3. The repository is also unusually useful because the code is concentrated in a single main trading file, so you can inspect how the abstractions, thresholds, persistence, and execution rules actually fit together rather than inferring them from prose alone.

It is especially valuable for Prosperity research because it shows a full-stack competition mindset: they explicitly describe using a custom dashboard, a forked open-source backtester, the official site backtester, and fast notebook-based prototyping depending on the type of strategy being tested.

## What the team appears to believe about the market

The central market belief in the code is that Prosperity is primarily a microstructure game, not a continuous-time prediction game. Their README says they treated WallMid as a proxy for true price, and the code operationalizes that by computing `wall_mid` from the outer “walls” of visible liquidity rather than from last trade or a predictive model. For Rainforest Resin and Kelp, the code assumes the current book already contains most of the fair-value information worth using.

A second belief is that some bots are systematically informative and can be tracked as stateful counterparties. The code hardcodes `INFORMED_TRADER_ID = 'Olivia'`, stores her latest buy/sell timestamps in `traderData`, and derives a long/short/neutral directional signal from that history. The README confirms that identifying Olivia’s repeatable behavior was a major source of edge in Squid Ink and Croissants.

A third belief is that not all risk should be hedged away. In the ETF block they only half-hedge some basket exposure with `ETF_HEDGE_FACTOR = 0.5`, and in the options section the README explicitly says their hybrid options approach was not a traditional delta hedge but a deliberate hedge against “bad luck” and relative leaderboard risk.

## Products / rounds covered

The code covers the main Prosperity 3 product families: Rainforest Resin, Kelp, Squid Ink, the two Picnic Baskets plus constituents, Volcanic Rock plus five voucher strikes, and Magnificent Macarons. The README ties those to Round 1 market making, Round 2 ETF stat arb, Round 3 options, Round 4 location arbitrage, and Round 5 trader-ID refinement.

## Fair value logic

For the generic base class, fair value starts from order-book structure. `ProductTrader` reads the local book, computes best bid/ask, computes `bid_wall` and `ask_wall`, then defines `wall_mid = (bid_wall + ask_wall) / 2`. That is a very specific Prosperity-style fair-value proxy: they are using the book walls, not a predictive filter, VWAP, or trade-based estimate.

For Rainforest Resin, the fair value is effectively the fixed mid-level around 10,000. The README says the true price was permanently fixed at 10,000, and the code implements a simple take-then-make routine around `wall_mid`, buying below it, selling above it, and using zero-edge fills to flatten inventory.

For Kelp, the code still uses `wall_mid` as fair value. The README explains the team’s view that the next move was basically not forecastable, so the best estimate was the current one. In code, that means they keep the same market-making skeleton as Resin, but overlay informed-trader logic when Olivia has traded recently.

For Squid Ink, the fair value model is not a price model at all. The code targets position from Olivia’s inferred direction, and the README says the strategy was to follow a trader who repeatedly bought at daily lows and sold at daily highs. So the “fair value” is really a directional state variable, not a continuous price estimate.

For ETFs, the fair value is synthetic index price plus a premium estimate. The code computes constituent wall mids, applies basket weights `[[6,3,1],[4,2,0]]`, gets `raw_spread = etf_price - index_price`, and then subtracts a running premium estimate stored in `traderData`, seeded by `INITIAL_ETF_PREMIUMS = [5,53]`. That is a useful pattern: fair value is not raw synthetic NAV, but NAV plus a learned persistent premium.

For options, fair value is explicitly model-based. The code fits implied vol as a quadratic in moneyness over sqrt time, with coefficients `[0.27362531, 0.01007566, 0.14876677]`, then plugs that IV into Black-Scholes to get theoretical call value, delta, and vega. It also imputes an option mid from a one-sided book when needed, which is a practical competition hack.

For Macarons, fair value is conversion-adjusted external price, not the island book. The code computes local candidate prices from external bid/ask rounded by ±0.5, adjusts external prices for tariffs and transport, and defines long/short arbitrage from those adjusted values.

## Execution logic

The execution pattern for Resin is very clear and reusable: first take mispriced liquidity, then improve the best passive quotes while staying on the profitable side of fair value. The code buys any sell order at or below `wall_mid - 1`, sells any bid at or above `wall_mid + 1`, then sets base passive prices to `bid_wall + 1` and `ask_wall - 1`, with “overbid/undercut” refinements based on existing size.

Kelp keeps the same broad structure, but the execution becomes event-driven when the informed trader appears. If Olivia bought recently, the code is willing to cross the ask and push inventory toward +40; if she sold recently, it crosses the bid and pushes toward -40. Outside those windows it reverts to quoting around the walls.

Squid Ink execution is much more direct. The code computes an `expected_position` of full long, full short, or flat from the informed signal, then crosses the market at `ask_wall` or `bid_wall` to move toward that target. This is not quote optimization, it is signal monetization.

ETF execution is threshold-based and mostly aggressive. When spread exceeds threshold, the basket is sold at `bid_wall`; when spread is below negative threshold, the basket is bought at `ask_wall`. Then the code trades Croissants directionally from the informed signal and uses the remaining constituents as partial hedges against `expected_position`. That makes the execution logic closer to stat-arb entry plus structured follow-up hedging than to classic passive ETF market making.

Options execution is split into two engines. One engine does IV-scalping on strikes `>= 9750`: it tracks the current deviation of option mid from model price relative to an EMA of that deviation, then opens when the deviation clears `THR_OPEN` and closes when it comes back to `THR_CLOSE`. The second engine only trades the 9500 strike as a mean-reversion vehicle, combining underlying EMA deviation with the option’s own IV deviation.

Macarons execution is one of the cleanest competition-specific routines in the file. The code chooses the better of long or short arb, sweeps through visible local liquidity only while preserving more than 58% of the headline arbitrage, then leaves the rest as a passive quote at the locally rounded conversion threshold. That is a nice example of “take what is still good, then rest passively at the acceptance edge.”

## Inventory / risk logic

The base class does inventory control mechanically and early. Position limits are hardcoded per symbol, max buy/sell capacity is computed immediately from current inventory, and each `bid()` / `ask()` call reduces remaining allowable volume as orders are created. That pattern is robust and worth copying.

Resin and Kelp both include inventory-neutralization logic. In Resin, if the trader is short and sees sells at the mid, it buys to flatten; if long and sees bids at the mid, it sells to flatten. The README explicitly says they used 10,000 or the current wall-mid estimate to unwind skew and free risk capacity.

ETF risk is handled through `expected_position`, not just actual current position. After basket orders are staged, the code estimates what exposure those orders imply, then uses constituent orders to move the informed leg and hedge the rest at `ETF_HEDGE_FACTOR = 0.5`. That is a strong design pattern because it coordinates legs before fills actually happen.

Options risk handling is intentionally asymmetric. The README says they did not do full delta hedging, and the code reflects that: one mean-reversion sleeve in the underlying, one in the deep ITM option, and a separate IV-scalping sleeve. This is portfolio-level risk design rather than product-by-product neutrality.

Macarons risk handling is conservative and practical. They only use the 10-unit conversion limit per timestep, keep short and long arb histories, and set conversions to pull inventory back toward zero with `clip(-initial_position, ±CONVERSION_LIMIT)`. That means conversions are mainly an inventory reset tool, not a maximal carry mechanism.

## State / memory usage

State persistence is one of the best parts of the repo. The strategy serializes compact JSON in `traderData`, reloads it each step, and stores only what it really needs: informed-trader timestamps, ETF premium estimates and counts, EMA values, mean option-theo deviations, average absolute deviations, and Macaron arbitrage histories.

This is exactly the right competition pattern: keep persistent state small, numeric, and incremental. They are not storing huge histories, just enough running statistics to reconstruct filters and signals every step.

## Backtesting / diagnostics workflow

Their diagnostics culture looks strong. The README says they built a custom dashboard with synchronized logs, position and PnL panels, order-book visualization, filtering by trader group, indicator overlays, and normalization by reference series like WallMid. That is much more important than the specific strategy ideas.

Their backtesting workflow is also well thought through. They say they used the official Prosperity website when strategy performance depended mainly on bot interactions, used an open-source backtester for simpler taking/quoting logic, and often used fast vectorized notebook backtests for early screening. That is exactly the kind of staged workflow Codex or Claude should emulate.

The code also logs aggressively. It prints structured JSON each run, and the product blocks log internal indicators such as ETF index values, premiums, arbitrage measures, market book levels, and conversion actions.

## Architecture choices

Architecturally, this is a monolithic but logically segmented single-file strategy. The file is about 925 lines, with a base `ProductTrader`, then specialized traders for single-product logic, plus composite managers for ETFs and options, and a top-level `Trader.run` dispatcher.

That architecture is good for competition speed: one file, one deploy target, shared helpers, product-specific logic in separate classes, and composite traders controlling multi-leg books internally. The dispatch map only keys off one representative symbol per strategy family, so the ETF and option blocks own the cross-symbol logic themselves.

The main downside is maintainability. The file also uses a lot of `try/except: pass`, including around book parsing and trader execution, which makes the code resilient during competition but can hide serious bugs during development.

## What looks robust

The most robust ideas here are not the exact thresholds. They are the patterns:

Using one product abstraction with shared book parsing, position accounting, and bounded order creation is robust.

Separating fair-value estimation from execution is robust. Resin/Kelp use take-then-make around fair value, ETFs use spread normalization then threshold entries, options use model price plus short-horizon deviation filters, and Macarons use conversion-adjusted price thresholds.

Persisting compact running statistics instead of raw history is robust. That includes ETF premium means, EMAs, and short rolling arb histories.

Using `expected_position` to coordinate basket and hedge legs is robust. That is one of the most reusable architecture choices in the repo.

## What looks round-specific

A lot of this repo is deliberately Prosperity-3-specific. `Olivia` is hardcoded as the informed trader. The ETF weights, premium seeds, threshold shifts, option vol-smile coefficients, day-count assumptions, and the Macarons 58% acceptance-style heuristic are all tied to that competition’s exact bot ecology and data-generating process.

The README also makes clear that early-round bot behavior in Prosperity 3 was unusually close to prior years and that hardcoding exploits were later banned. That means some of the edge in this ecosystem came from historical continuity that you should not assume for Prosperity 4.

## What Codex should learn from this repo

Codex should learn to build separate alpha engines for separate market archetypes rather than forcing one universal strategy. This repo uses different logic for fixed-fair-value market making, dynamic-but-unpredictable quoting, informed-flow following, threshold stat-arb, model-based option scalping, and conversion arbitrage.

Codex should also learn the workflow discipline here: build diagnostics first, persist compact state, use the right backtester for the right problem, and keep execution logic simple once the signal is identified. Those habits are more transferable than any particular threshold.

Most importantly, Codex should learn the team’s attitude toward fair value. They repeatedly normalize the market into a simpler object: fixed price, wall mid, basket premium, option-theo deviation, or conversion-adjusted local threshold. That reduction step is where most of the edge is created.

## What Codex should NOT copy blindly

Do not copy the exact constants. The thresholds, premium seeds, product lists, Olivia logic, option smile coefficients, and Macarons heuristics are too round-specific.

Do not copy the exact `wall_mid` assumption without revalidating it. Here it works because the team believed Prosperity books had meaningful walls and short-lived orders. In a different simulator, that could be a poor proxy for fair value.

Do not copy the silent-error style. The published file appears to contain some inconsistencies or polishing artifacts in the ETF and options sections, such as list-like `self.spreads` later being indexed by `basket.name`, and references like `self.new_switch_mean` and `self.vegas` without a visible assignment in the published file. Even if the original competition version worked, this published artifact is not something to trust blindly as production code.

Do not copy the monolithic structure unless speed matters more than extensibility. For a coding agent building a new Prosperity 4 system, the right takeaway is the decomposition into alpha engines and shared utilities, not the one-file implementation style itself.
