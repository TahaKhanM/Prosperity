# Python Backtester and Visualizer Context For AI Tools In This Prosperity Repository

## Purpose

This file explains how the local Python backtester (`prosperity4bt`) and the
local visualizer (`imc-prosperity-4-visualizer`) work in this repository, and
how AI coding tools such as Codex and Claude Code should use them when designing,
implementing, and validating Prosperity 4 strategies.

It is not a replacement for:

- official Prosperity syntax and interface rules,
- the repo `AGENTS.md` files,
- either tool's own `README.md`.

Instead, it is a practical context file for AI-assisted strategy work in this
specific checkout.

---

## What These Tools Are

### Python Backtester (`prosperity4bt`)

A Python-based Prosperity 4 replay engine adapted from jmerle's Prosperity 3
backtester. It replays historical order book and trade data timestamp by
timestamp, calls the Python `Trader` implementation on each state, applies local
matching rules and position-limit checks, and produces a `.log` output file that
matches the format of the official Prosperity submission environment.

### Visualizer (`imc-prosperity-4-visualizer`)

A React/TypeScript web application that renders backtester output as interactive
charts. It displays order book depth, position history, PnL curves, trade
markers, and algorithm print output over time. It accepts `.log` files produced
by `prosperity4bt`, files loaded from a URL, or logs loaded directly from the
Prosperity API.

---

## Local Paths

- **Backtester root**:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester`
- **Backtester package**:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester/prosperity4bt`
- **Backtester data model**:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester/prosperity4bt/datamodel.py`
- **Backtester position limits and data loading**:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester/prosperity4bt/data.py`
- **Backtester replay engine**:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester/prosperity4bt/runner.py`
- **Backtester CLI entry point**:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester/prosperity4bt/__main__.py`
- **Root-level datamodel shim** (allows `from datamodel import ...`):
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester/datamodel.py`
- **Bundled tutorial data**:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester/prosperity4bt/resources/round0/`
- **Visualizer root**:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-visualizer`
- **Visualizer source code**:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-visualizer/src`

---

## How To Install The Backtester

From the backtester directory:

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester
python3 -m pip install --user .
```

Or, if pip supports PEP 517 editable installs:

```bash
pip install -e .
```

Dependencies: `ipython`, `jsonpickle`, `orjson`, `tqdm`, `typer`.

If dependencies fail to install automatically:

```bash
python3 -m pip install --user jsonpickle orjson ipython tqdm typer
```

---

## How To Run The Backtester

### Basic usage

```bash
# Run on all days in round 0 (tutorial)
prosperity4bt <path_to_trader.py> 0

# Run on a specific day
prosperity4bt <path_to_trader.py> 0--1

# Run on multiple specific days
prosperity4bt <path_to_trader.py> 0--2 0--1
```

### Common options

```bash
# Merge PnL across days into a single cumulative total
prosperity4bt trader.py 0 --merge-pnl

# Automatically open results in the visualizer when done
prosperity4bt trader.py 0 --vis

# Write output to a specific file
prosperity4bt trader.py 0 --out results.log

# Skip saving output to file
prosperity4bt trader.py 0 --no-out

# Print trader's stdout while running
prosperity4bt trader.py 0 --print

# Use custom data directory
prosperity4bt trader.py 0 --data /path/to/data

# Suppress progress bars
prosperity4bt trader.py 0 --no-progress

# Keep original timestamps across days
prosperity4bt trader.py 0 --original-timestamps
```

### Trade matching modes

```bash
# Match market trades with prices equal to or worse than your quotes (default)
prosperity4bt trader.py 0 --match-trades all

# Match market trades with prices strictly worse than your quotes
prosperity4bt trader.py 0 --match-trades worse

# Do not match against market trades at all (only order book)
prosperity4bt trader.py 0 --match-trades none
```

### Default output location

Output `.log` files are saved to:

```
<current_working_directory>/backtests/<timestamp>.log
```

---

## How To Use The Visualizer

### Option 1: Open from backtester

```bash
prosperity4bt trader.py 0 --vis
```

This automatically starts a local HTTP server and opens the P4 visualizer in
the browser, pointed at the output file.

### Option 2: Build and serve locally

```bash
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-visualizer
pnpm install
pnpm dev
```

Then drag and drop a `.log` file onto the home page, or paste a URL.

### Option 3: Use the hosted version

Open `https://jmerle.github.io/imc-prosperity-4-visualizer/` in a browser and
upload a `.log` file.

### Loading from Prosperity API

The visualizer can load algorithm logs directly from the Prosperity API. This
requires a Prosperity ID token extracted from the browser's local storage on
`prosperity.imc.com`. The token is stored under a key ending in `.idToken`.

---

## Trader File Requirements

The backtester expects a Python file exposing a `Trader` class with a `run`
method. This is identical to what the official Prosperity environment expects.

### Minimal trader template

```python
from datamodel import (
    Listing, Observation, Order, OrderDepth, ProsperityEncoder,
    Symbol, Trade, TradingState
)

class Trader:
    def run(self, state: TradingState) -> tuple[dict[str, list[Order]], int, str]:
        result = {}
        conversions = 0
        traderData = ""
        return result, conversions, traderData
```

### Key interface rules

- `run()` must return a tuple of `(result, conversions, traderData)`
- `result` is a `dict[str, list[Order]]` mapping product symbols to order lists
- `conversions` is an `int` (number of conversions to request)
- `traderData` is a `str` (persisted across timestamps, 50,000 char limit)
- Buy orders have positive quantity, sell orders have negative quantity
- Order prices must be `int`, quantities must be `int`

### Import path

The backtester has a root-level `datamodel.py` shim, so standard Prosperity
imports work:

```python
from datamodel import Order, OrderDepth, TradingState, ...
```

This is the same import path used in official Prosperity submissions.

---

## Logger Class For Visualizer Support

For the visualizer to display algorithm print output correctly, the trader
should use the Logger class pattern. This compresses state data into a format
the visualizer can parse:

```python
import json
from datamodel import ProsperityEncoder, TradingState

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects, sep=" ", end="\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict, conversions: int, trader_data: str) -> None:
        base_length = len(self.to_json([
            self.compress_state(state, ""),
            self.compress_orders(orders),
            conversions,
            "",
            "",
        ]))

        max_item_length = (self.max_log_length - base_length) // 3

        print(self.to_json([
            self.compress_state(state, self.truncate(state.traderData, max_item_length)),
            self.compress_orders(orders),
            conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings) -> list:
        compressed = []
        for listing in listings.values():
            compressed.append([listing.symbol, listing.product, listing.denomination])
        return compressed

    def compress_order_depths(self, order_depths) -> dict:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]
        return compressed

    def compress_trades(self, trades) -> list:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append([
                    trade.symbol,
                    trade.price,
                    trade.quantity,
                    trade.buyer,
                    trade.seller,
                    trade.timestamp,
                ])
        return compressed

    def compress_observations(self, observations) -> list:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sugarPrice,
                observation.sunlightIndex,
            ]
        return [observations.plainValueObservations, conversion_observations]

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value
        return value[:max_length - 3] + "..."

    def to_json(self, value) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

logger = Logger()
```

Usage in the trader:

```python
class Trader:
    def run(self, state: TradingState) -> tuple[dict[str, list[Order]], int, str]:
        result = {}
        conversions = 0
        traderData = ""

        logger.print("My custom debug output")

        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData
```

---

## Prosperity 4 Specifics Encoded In These Tools

### Currency

Prosperity 4 uses **XIRECS** as the denomination currency (not SEASHELLS from
Prosperity 3). This appears in:

- `Listing.denomination` is the string `"XIRECS"`
- Trade history JSON in output logs uses `"currency": "XIRECS"`

### Tutorial round products and position limits

| Product   | Position Limit |
|-----------|---------------|
| EMERALDS  | 80            |
| TOMATOES  | 80            |

These are defined in:

- Backtester: `prosperity4bt/data.py` in the `LIMITS` dict
- Visualizer: `src/pages/visualizer/PositionChart.tsx` in the `knownLimits` object

### Position limit enforcement

The backtester uses batch rejection: if all orders for a product would breach
the position limit assuming full execution, ALL orders for that product are
rejected. This matches the official Prosperity specification exactly.

### Observation handling

Observations are handled generically. The `ObservationRow` in `data.py` stores
fields as a dict with property accessors for known field names:

- `bidPrice`, `askPrice`, `transportFees`, `exportTariff`, `importTariff`
- `sugarPrice`, `sunlightIndex`

This means future rounds with conversion observations will work without code
changes to the observation parsing logic.

### Environment variables

During backtests, two environment variables are set:

- `PROSPERITY4BT_ROUND`: the round number
- `PROSPERITY4BT_DAY`: the day number

These do **not** exist in the official submission environment. Never write trader
code that requires them.

---

## How The Two Tools Work Together

### Output format compatibility

The backtester produces `.log` files with three sections:

1. **Sandbox logs**: JSON objects with `sandboxLog`, `lambdaLog`, `timestamp`
2. **Activities log**: Semicolon-separated rows with 17 columns (day, timestamp,
   product, bid/ask prices and volumes, mid price, PnL)
3. **Trade History**: JSON array of trade objects with `timestamp`, `buyer`,
   `seller`, `symbol`, `currency` ("XIRECS"), `price`, `quantity`

The visualizer parses all three sections. The `lambdaLog` field in sandbox logs
is where the Logger class output goes, which the visualizer decompresses to
reconstruct state, orders, and algorithm output.

### The `--vis` flag

Running the backtester with `--vis` automatically:

1. Saves the output to a `.log` file
2. Starts a temporary local HTTP server serving that file
3. Opens the P4 visualizer in the browser with a `?open=` parameter pointing
   at the local server

This is the fastest way to go from code change to visual inspection.

---

## Adding New Round Data

When new competition rounds are released, AI tools should update both tools:

### Backtester updates

1. Download sample data CSVs from the Prosperity platform
2. Create `prosperity4bt/resources/roundN/` with an `__init__.py` file
3. Place CSV files in the new directory:
   - `prices_round_N_day_X.csv`
   - `trades_round_N_day_X.csv`
   - `observations_round_N_day_X.csv` (if the round has conversion observations)
4. Update `LIMITS` in `prosperity4bt/data.py` with new product position limits
5. If the round has observations, update `OBSERVATION_PRODUCTS` in
   `prosperity4bt/data.py` with the round number and product name

### Visualizer updates

1. Update `knownLimits` in `src/pages/visualizer/PositionChart.tsx` with new
   product position limits

---

## How AI Tools Should Use These Tools

### 1. Use the backtester as the default validator

For any strategy change:

1. Write or modify a trader file
2. Run `prosperity4bt trader.py 0` (or the appropriate round)
3. Check the PnL summary printed to stdout
4. If needed, run with `--vis` to inspect visually
5. Compare against a known baseline

### 2. Use trade matching modes to test robustness

A strategy that only profits under `--match-trades all` may depend on optimistic
fill assumptions. Test under stricter modes:

```bash
# Default: optimistic matching
prosperity4bt trader.py 0 --match-trades all

# Conservative: only match trades at strictly worse prices
prosperity4bt trader.py 0 --match-trades worse

# Most conservative: order book only, no market trade matching
prosperity4bt trader.py 0 --match-trades none
```

If the strategy collapses under `worse` or `none`, the edge may not be real.

### 3. Use the visualizer for diagnosis, not just validation

The visualizer shows:

- **Price chart**: mid price over time with buy/sell trade markers
- **Order book depth**: bid/ask levels at each timestamp
- **Position chart**: position over time with limit lines
- **PnL chart**: cumulative profit and loss per product
- **Algorithm output**: print statements from the Logger class

Use these charts to understand **why** a strategy wins or loses, not just
whether the final PnL is positive.

### 4. Use the Logger class in all traders

Without the Logger class, the visualizer cannot display algorithm state or
debug output. Always include it unless there is a specific reason not to.

### 5. Keep trader code submission-compatible

The backtester exists to validate competition submissions. Trader code must:

- Expose a `Trader` class with a `run(self, state)` method
- Return `(result, conversions, traderData)` as a tuple
- Use negative quantities for sell orders
- Not depend on global state or persistent instance variables across timestamps
  (use `traderData` for persistence)
- Keep `traderData` under 50,000 characters
- Not import modules unavailable in the official environment
- Not depend on `PROSPERITY4BT_ROUND` or `PROSPERITY4BT_DAY` environment
  variables

---

## Differences From The Rust Backtester

This repository also contains a Rust-based backtester at
`prosperity_rust_backtester/`. The two backtesters serve different purposes:

| Feature | Python backtester (`prosperity4bt`) | Rust backtester |
|---------|-------------------------------------|-----------------|
| Speed | Slower (pure Python) | Faster (Rust with Python FFI) |
| Output format | Official `.log` format (visualizer-compatible) | Custom artifacts (metrics.json, bundle.json, etc.) |
| Visualization | Direct `--vis` flag opens P4 visualizer | Separate artifact inspection scripts |
| Matching modes | `all`, `worse`, `none` | `all`, `worse`, `none` + queue penetration + slippage |
| Setup | `pip install` | Rust toolchain + `maturin` + conda |
| Make targets | None (direct CLI) | Full Makefile surface |

For quick iteration with visual feedback, prefer the Python backtester.
For deeper execution analysis with stress testing options, prefer the Rust
backtester. Both should agree on the same strategy being profitable or not.

---

## Common Pitfalls AI Tools Should Avoid

1. **Do not assume `prosperity4bt` is globally installed.** Always check or
   install first. The backtester is a local Python package.

2. **Do not create traders that import from `prosperity4bt`** directly. Official
   submissions use `from datamodel import ...`, and the root-level shim
   handles this.

3. **Do not write traders that use environment variables** like
   `PROSPERITY4BT_ROUND`. These do not exist in the official environment.

4. **Do not skip the Logger class.** Without it, the visualizer cannot parse
   algorithm output. Always include it in traders intended for visualization.

5. **Do not treat default matching mode results as guaranteed.** The official
   exchange has its own matching behavior. Use `--match-trades worse` or
   `--match-trades none` to sanity-check edges.

6. **Do not forget to update LIMITS** when new rounds are released. The
   backtester will fall back to a default limit of 50 for unknown products,
   which may not be correct.

7. **Do not commit `node_modules/` or `dist/`** from the visualizer. These are
   in the visualizer's `.gitignore`.

8. **Do not treat the Prosperity API endpoints** in the visualizer as confirmed
   for P4. The endpoints in `LoadFromProsperity.tsx` are inherited from P3 and
   may need updating when P4 endpoints are known.

---

## Quick Reference Commands

```bash
# Install the backtester
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester
python3 -m pip install --user .

# Run tutorial backtest
prosperity4bt /path/to/trader.py 0

# Run tutorial backtest with visualization
prosperity4bt /path/to/trader.py 0 --vis

# Run specific day with conservative matching
prosperity4bt /path/to/trader.py 0--1 --match-trades worse

# Run with merged PnL and print output
prosperity4bt /path/to/trader.py 0 --merge-pnl --print

# Start visualizer dev server
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-visualizer
pnpm install && pnpm dev

# Build visualizer for production
cd /Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-visualizer
pnpm build
```

---

## High-Value Local Files To Pair With This Context

- Official syntax and interface context:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/Prosperity Context/Official Prosperity Context.md`
- Round 1 official context:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/Prosperity Context/Official Prosperity Context Round 1.md`
- Rust backtester context:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/Prosperity Context/RUST_BACKTESTER_CONTEXT_FOR_AI_TOOLS.md`
- Prompt-engineering context:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/Prosperity Context/CHATGPT_CONTEXT_FOR_CODEX_PROMPT_ENGINEERING.md`
- Repo-wide instructions:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/AGENTS.md`
- Backtester README:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-backtester/README.md`
- Visualizer README:
  `/Users/tahakhan/Documents/Work/Projects/Prosperity/imc-prosperity-4-visualizer/README.md`
