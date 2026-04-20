# Research Note: CarterT27/imc-prosperity-3

**Team:** Alpha Animals (UC San Diego) — 9th Global, 2nd USA, IMC Prosperity 3
**Codebase:** 1,810-line single-file Python trader (`trader.py`), 7 Jupyter notebooks, 5 rounds of historical data
**Date reviewed:** April 2026

---

## 1. Why This Repo Matters

This is one of the highest-placing open-source submissions for IMC Prosperity 3, a 15-day algorithmic trading competition with over 13,500 teams. The code covers nearly every archetype you encounter in short-horizon electronic market-making: stable-value market-making (Rainforest Resin), microstructure-aware market-making (Kelp), mean-reversion on volatility spikes (Squid Ink), statistical arbitrage on ETF-like baskets (Picnic Baskets), Black-Scholes options pricing and cross-strike arbitrage (Volcanic Rock Vouchers), cross-venue conversion arbitrage with regime switching (Macarons), and counterparty-informed copy-trading (Olivia). Crucially it contains mistakes the team made, dead code left behind, and hardcoded constants that reveal the gap between "works in backtest" and "works live." That makes it an unusually honest reference implementation.

---

## 2. Market Assumptions Implicit in the Code

**Rainforest Resin is pegged.** The code uses a rolling VWAP but in the README explicitly calls the fair value "hardcoded at 10000." The VWAP merely drifts near this anchor. The assumption is that the product has essentially zero drift and the only PnL comes from capturing spread.

**Large orders reveal the market-maker mid.** In `product_orders`, the code filters the order book to only consider levels with size ≥ 10 (lines 326-337). This constructs a "market-maker mid" (`mm_mid`) distinct from the raw BBO mid. The belief is that small orders are noise (retail, or adversarial probing) and the large resting quotes from consistent market-makers represent a more stable fair value signal.

**Squid Ink is mean-reverting on short timescales.** Entry requires both a volatility threshold (>3 std devs over 10 ticks) AND a percentage deviation threshold (>5% from 30-tick mean). Exit is time-capped at 5 timestamps. The assumption is that extreme moves in this product overextend and snap back quickly.

**Baskets are cointegrated with their components.** The synthetic value uses a linear model with regression coefficients (`pb1_intercept = -57.71`, component weights of 6, 3, 1) fit from rounds 1-3 data. The code assumes this linear relationship is stationary across rounds.

**Options are fairly priced by Black-Scholes.** Vouchers are treated as European call options with a 7-day expiry, zero risk-free rate, and a rolling-window implied volatility. The code assumes the volatility surface is flat enough that averaging IV across strikes and over time produces a usable fair value.

**Macarons have two regimes driven by sunlight.** When the sunlight index drops below a threshold (`CSI_THRESHOLD = 0`), the code switches from balanced two-way arbitrage to an aggressive one-way long-accumulation strategy with no selling.

**One counterparty is an insider.** The code hardcodes `insider_id = "Olivia"` and assumes her trades are predictive: buying signals bullish, selling signals bearish. This assumption was validated empirically (see `counterparty_edge.ipynb`) and is directly exploited via copy-trading.

---

## 3. Strategy Components

### 3a. Fair Value Logic

There are four distinct fair-value models in the codebase:

**Simple mid-price** (`calculate_fair_value`): `(best_bid + best_ask) / 2`. Used as the fallback everywhere and as the primary fair value for products where no special model exists.

**Market-maker-filtered VWAP** (inside `product_orders`): For Kelp and Resin, the code constructs a rolling VWAP over 20 ticks, using only the top-of-book bid/ask volumes. This is the primary fair value for market-making. The filtering of orders ≥ 10 lots to find the "real" market-maker mid is a separate but related signal—it determines `mm_mid_price`, which seeds the VWAP when no history exists.

**Regression-based synthetic value** (`calculate_synthetic_value`): For baskets, fair value = intercept + weighted sum of component mid-prices. Coefficients were fitted offline (the notebook `kalman.ipynb` shows Kalman filter experiments on these spreads). The two sets of coefficients visible in `__init__` (lines 142-160) show an earlier regression fit was overwritten by a simpler integer-weight model.

**Black-Scholes theoretical price** (`black_scholes_call`): For vouchers, the theoretical price comes from BS with spot = rock mid, strike = voucher strike, T = days remaining / 365, r = 0, σ = rolling mean of per-strike implied volatilities over a 30-tick window. Newton-Raphson IV solver runs up to 50 iterations with σ clamped to [0.01, 2.0].

### 3b. Taking Logic

Taking (crossing the spread aggressively) happens in multiple places:

**Generic product taking** (lines 389-402): If the best ask is below `fair_value - take_width`, the code lifts the offer. If the best bid is above `fair_value + take_width`, it hits the bid. A critical guard: it only takes if the order size is ≤ 20 lots—this is an adverse-selection filter to avoid trading against large informed flow.

**Squid Ink mean-reversion entry** (lines 500-516): When volatility exceeds the threshold and price deviates sufficiently from the mean, the code aggressively takes liquidity at the BBO to enter a position. It does not use limit orders for entry—it wants immediate execution.

**Basket arbitrage taking** (`execute_basket_arbitrage`): When the basket ask is below the synthetic bid (or basket bid above synthetic ask), the code lifts offers on the cheap side and hits bids on the expensive side simultaneously across basket + components. Volume is capped by position limits and available liquidity.

**Macaron arbitrage taking** (`macaron_arb_take`): A multi-layer take function. In low-sun regime, it sweeps all sell-side liquidity up to the position limit with no selling. In normal regime, it (1) takes if local ask < implied_bid - threshold, (2) takes mid-to-mid discrepancy trades when local and foreign mids diverge by > 2× threshold, and (3) does small opportunistic sweeps of remaining cheap liquidity. Position-ratio scaling widens thresholds as inventory grows.

### 3c. Passive Quote Logic

**Generic market-making quotes** (lines 414-433): After taking and position-clearing, the code places passive quotes. The buy quote goes at `best_bid_below_fair + 1` (pennying the best bid that's below fair value), and the sell quote at `best_ask_above_fair - 1`. Remaining capacity (position_limit - filled) goes entirely to these two levels—a single-level, full-size quote.

**Voucher market-making** (`volcanic_rock_voucher_orders`, lines 933-952): Quotes at `int(theoretical_price)` on the buy side and `int(theoretical_price + 1)` on the sell side, with full remaining position capacity. The 1-tick spread is tight for an options market—the assumption is that the BS theoretical price is accurate enough that quoting a penny wide is still profitable.

**Macaron market-making** (`macaron_arb_make`): In low-sun regime, places aggressive buy orders at best ask (or outbids existing orders). In normal regime, constructs bid = implied_bid - edge + price_adjustment, ask = implied_ask + edge + price_adjustment, where price_adjustment tilts quotes toward the foreign mid when local-foreign divergence exists. Position skew factor reduces order size on the stretched side when position exceeds 50% of limit.

### 3d. Inventory and Risk Handling

**Position limits** are hardcoded per product (lines 190-206) and strictly enforced at order construction time—every order quantity is clamped by `position_limit - position` or `position_limit + position`.

**Position clearing** (`clear_position_order`): After taking, if the position (including pending orders) is long and there's a buyer at `ceil(fair_value)`, the code sells into it. If short and there's a seller at `floor(fair_value)`, the code buys from it. This is an inventory-reduction mechanism that fires every tick.

**Time-based position exits** (Squid Ink): Positions older than 5 timestamps are forcibly closed at the BBO. This is a hard risk cutoff.

**Regime-aware inventory** (Macarons): The `macaron_arb_clear` function uses conversions (import/export with the foreign island) to manage inventory. In low-sun regime, it only imports (to build longs). In normal regime, it computes a target position based on implied spread and nudges toward it, capped at ±10 conversions.

**Product disable switches** (`active_products` dict): Several products are set to `False`—Picnic Basket 2, Volcanic Rock, and 3 of 5 voucher strikes. Inactive products with existing positions trigger automatic close via `close_position`. This is a manual kill-switch, presumably used after discovering bugs or unprofitable strategies.

**Daily PnL tracking** (lines 250-254): Variables for `max_daily_loss` (50000) and `profit_target` (20000) exist but are never checked or enforced in the code—they are aspirational dead code.

**Stop-loss and take-profit** (`should_stop_loss`, `should_take_profit`): Defined for vouchers but never called from the main `run()` loop. These functions track entry price and premium but appear to be abandoned features.

---

## 4. Architecture and Workflow

The entire strategy runs inside a single `Trader` class with one entry point: `run(state: TradingState)`. The competition framework calls `run()` on every tick, passing the full order book, market trades, positions, and observations. The method returns a dictionary of orders per product, a conversion count, and serialized state.

**State persistence** is handled via `traderData`—a JSON string serialized with `jsonpickle` and passed back to the framework. On each tick, the code deserializes this to restore price histories, VWAP buffers, insider regime states, and volatility histories. This is necessary because the Trader object is re-instantiated each tick (the `__init__` defaults are overwritten by deserialized state).

**Execution order** in `run()` is: (1) process insider trades and update sunlight regime, (2) compute macaron conversions, (3) generate macaron take+make orders, (4) generate Olivia copy-trades for Croissants and Squid Ink, (5) process vouchers and Volcanic Rock, (6) iterate remaining products for generic market-making or basket arbitrage. Products are marked as "handled" in a set to avoid double-processing.

**Logger** is a custom class that compresses state into a compact JSON format for the competition's visualization tools. It uses binary search to truncate log strings to a max JSON-encoded length of 2000 bytes, omitting own_trades and market_trades entirely to save space. This is a pragmatic workaround for the competition's logging limits.

**Caching** (`self.cache`): Black-Scholes and IV computations are cached by input parameters to avoid recomputation. The cache is flushed when it exceeds 1000 entries.

**No modularization**: The 1800+ lines live in a single file with no imports from local modules, no strategy abstraction layer, no test file, and no configuration file. This is typical of competition code but would be a maintenance hazard in production.

---

## 5. What Is Reusable

**The market-maker-filtered mid-price idea** (filtering for orders ≥ N lots to separate market-maker quotes from noise) is a robust microstructure insight that generalizes beyond this competition. The specific threshold (10 lots) is data-dependent but the principle ports well.

**The take-then-make-then-clear order construction pattern**: taking mispriced orders first, then clearing stale inventory toward fair value, then posting passive quotes with remaining capacity. This three-phase approach prevents self-crossing and naturally prioritizes high-EV actions.

**The Black-Scholes + Newton-Raphson IV solver** (lines 692-770) is a clean, self-contained implementation with caching and sensible bounds. The Horner-form rational approximation of the normal CDF is numerically stable and avoids scipy dependencies.

**Position-ratio scaling for thresholds and order sizes**: The pattern of widening take thresholds and reducing order sizes as `abs(position) / limit` grows is a simple, effective inventory penalty that appears in both macaron and generic market-making code.

**The implied bid/ask calculation for cross-venue arbitrage** (`calculate_implied_bid_ask`): computing the effective local-equivalent price after accounting for transport fees, tariffs, and slippage is a clean abstraction that maps directly to any multi-venue or cross-border trading problem.

**The Kalman filter notebook** for estimating basket-component relationships dynamically (rather than using a static regression) is a stronger approach than what made it into production. Worth studying even though it was not deployed.

---

## 6. What Is Risky or Stale

**Hardcoded regression intercepts** (`pb1_intercept = -57.71`, `pb2_intercept = -22.59`) are fit from rounds 1-3 data and assumed stable. In a competition where product dynamics can shift between rounds, these become stale. The code even contains a visibly overwritten earlier fit (lines 142-150 are immediately superseded by lines 153-160), suggesting the team was manually re-fitting and forgot to clean up.

**The insider copy-trading strategy** is entirely specific to Prosperity 3's Round 5 mechanic where counterparty identities were revealed. The hardcoded `insider_id = "Olivia"` has zero portability. The regime detection (bullish/bearish based on one trader's direction) is also simplistic—it doesn't account for trade size, timing patterns, or the possibility of the insider being wrong.

**Abandoned risk management code**: `should_stop_loss`, `should_take_profit`, `max_daily_loss`, `profit_target`, `stop_loss_hits`, `position_scale`, and `daily_pnl` are all defined but never used in the execution path. This dead code creates false confidence that risk controls exist. In production, unreachable risk checks are worse than no risk checks because they may discourage building real ones.

**The sunlight threshold `CSI_THRESHOLD = 0`** is a tuned constant that the team themselves noted they weren't confident about (from the README: they "weren't confident whether our sunlight threshold was overfit to previous data or not"). For Round 5, they disabled it entirely for macarons. The regime switch is a binary toggle with no hysteresis or smoothing—a sunlight reading oscillating near 0 would cause rapid regime flipping.

**Single-tick trade lag on insider signals**: The `process_insider_trades` function reads `state.market_trades`, which are trades from the *previous* tick. By the time the copy-trade fires, Olivia's signal is at least one tick old. In a mean-reverting product, this lag can turn a profitable signal into a loss.

**Voucher strikes selectively disabled**: Only the 9750 and 10000 vouchers are active; the other three are turned off. The code still computes IV and theoretical prices for all five but only trades two. If the disabled strikes had bugs or lost money, those issues may still exist in the shared pricing code.

---

## 7. What Codex/Claude Should Learn From It

**Structure your order generation in phases.** The take → clear → make pattern prevents accidental self-crossing, ensures aggressive opportunities are captured before passive quotes are placed, and makes position accounting straightforward.

**Filter the order book before computing fair value.** Using only large orders to estimate the market-maker mid is a practical way to reduce noise in thinly-traded or adversarially-populated order books.

**Use per-product configuration dictionaries.** The `make_width`, `take_width`, `position_limits`, and `active_products` dictionaries make it easy to tune and disable individual products without touching strategy logic. This is better than scattered if/else branches.

**Serialize and deserialize state carefully.** The `traderData` round-trip via jsonpickle is essential in a framework that re-instantiates the Trader each tick. Any AI-generated trading code for similar frameworks must handle state persistence correctly or lose all history.

**Cache expensive computations.** The BS/IV cache avoids redundant math. The cache-clear at 1000 entries prevents unbounded memory growth. Both are good practices for tick-level systems.

**Dead code is a signal, not a mistake.** The abandoned stop-loss, delta-hedging, and position-scale code tells you what the team *tried and couldn't make work*. When generating similar systems, it's better to strip dead code than leave it as aspiration.

---

## 8. What Should Not Be Copied Directly

**Do not copy the hardcoded product names, position limits, or intercepts.** Every constant in this code is calibrated to Prosperity 3's specific product universe. Resin at 10000, baskets with 6/3/1 component weights, voucher strikes at 250-tick intervals, macaron position limit of 75—none of these transfer.

**Do not copy the Olivia copy-trading logic.** This is a competition-specific exploit based on the revelation of counterparty IDs in Round 5. Real markets do not reveal counterparty identity, and copying one participant's flow is not a viable strategy outside this game.

**Do not copy the sunlight regime logic.** The `CSI_THRESHOLD = 0` toggle and the one-way accumulator in low-sun mode are responses to a specific data-generating process (the competition's macaron pricing model driven by a sunlight index). The regime logic has no hysteresis and was reportedly unreliable.

**Do not copy the single-file monolithic architecture for anything beyond a hackathon.** 1,810 lines with no tests, no strategy abstraction, no separate configuration, and manually overwritten constants is acceptable for a 15-day competition but would create serious maintenance and correctness risks in any ongoing system.

**Do not copy the abandoned risk parameters as if they work.** The stop-loss, daily-loss-limit, and profit-target variables are defined but never enforced. If you need risk controls, implement and test them; do not inherit decorative constants.

**Do not trust the VWAP calculation blindly.** The formula on lines 347-350 computes VWAP using `best_bid * |best_ask_volume| + best_ask * |best_bid_volume|` divided by total volume—this inverts the price-quantity pairing (bid price weighted by ask volume), which produces a mid-price-like estimator rather than a true VWAP. It may work adequately as a smoothing mechanism but is not a standard VWAP.
