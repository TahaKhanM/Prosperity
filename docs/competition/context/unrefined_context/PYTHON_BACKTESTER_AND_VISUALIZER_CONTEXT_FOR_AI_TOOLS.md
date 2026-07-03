# Python Backtester And Visualizer Context For AI Tools

## Purpose

This file explains the older Python backtester and the local React visualizer in
this repository from an AI-tooling perspective.

It is meant to answer:

- when to use these tools instead of the Rust backtester,
- which files implement which behavior,
- what log formats the visualizer actually understands,
- and which repo-specific caveats matter before editing or relying on them.

Repository root in this checkout:

- `/Users/tahakhan/Documents/Work/Projects/Prosperity`

Tools covered here:

- Python backtester: `imc-prosperity-4-backtester/`
- Visualizer: `imc-prosperity-4-visualizer/`

---

## What These Tools Are

### Python backtester

`imc-prosperity-4-backtester/` is a Python replay engine packaged as
`prosperity4bt`.

It:

- loads a Python trader module,
- reads round/day CSV data,
- builds a `TradingState`,
- calls `Trader.run(...)` on each timestamp,
- applies local matching and position-limit logic,
- writes a text log in the classic backtester format,
- can optionally open the visualizer.

### Visualizer

`imc-prosperity-4-visualizer/` is a React 19 + TypeScript + Vite app using
Mantine, Zustand, and Highcharts.

It:

- loads logs from file, URL, or the Prosperity API,
- parses either official-style JSON payloads or logger-style text logs,
- stores the loaded algorithm in Zustand,
- renders symbol-by-symbol charts and timestamp drill-down views.

---

## When To Use These Tools

Use the Python backtester when you want:

- the older `prosperity4bt` CLI flow,
- a plaintext logger-style output file,
- quick compatibility with the visualizer's logger parser,
- optional `--vis` auto-open behavior.

Use the visualizer when you want:

- interactive inspection of price, PnL, positions, trades, and timestamps,
- direct loading of official extracted payload files,
- quick comparison of logger-style local runs versus official-style hosted runs.

Do not confuse this with the Rust backtester:

- the Rust backtester is now the main local validation engine in this repo
- the Python backtester is still useful, but it is secondary here

---

## Current Repo Reality

These facts are true in this checkout on 2026-04-18.

### Python backtester resources are not tutorial-only

Bundled package data currently includes:

- `imc-prosperity-4-backtester/prosperity4bt/resources/round0/`
- `imc-prosperity-4-backtester/prosperity4bt/resources/round1/`

So round 1 data is already present in this checkout.

### The visualizer supports two parser families, not one

The parser in `src/utils/algorithm.tsx` accepts:

1. official-style JSON payloads containing `activitiesLog`
2. logger-style plaintext logs containing `Sandbox logs:` and `Activities log:`

This distinction matters because different local tools generate different output
shapes.

### The visualizer does not parse zip bundles in-browser

Uploading a `.zip` is explicitly rejected in `LoadFromFile.tsx`.

You must extract the official `.log` or `.json` file first.

---

## Python Backtester Architecture

Main files:

- CLI and orchestration: `imc-prosperity-4-backtester/prosperity4bt/__main__.py`
- Data loading and limits: `imc-prosperity-4-backtester/prosperity4bt/data.py`
- Replay engine: `imc-prosperity-4-backtester/prosperity4bt/runner.py`
- Output row models: `imc-prosperity-4-backtester/prosperity4bt/models.py`
- File access abstraction: `imc-prosperity-4-backtester/prosperity4bt/file_reader.py`
- Visualizer opener HTTP server: `imc-prosperity-4-backtester/prosperity4bt/open.py`
- Log-to-resource extractor: `imc-prosperity-4-backtester/prosperity4bt/parse_submission_logs.py`
- Submission-compatible datamodel: `imc-prosperity-4-backtester/prosperity4bt/datamodel.py`
- Root shim so `from datamodel import ...` works:
  `imc-prosperity-4-backtester/datamodel.py`

Package metadata:

- `imc-prosperity-4-backtester/pyproject.toml`

---

## Python Backtester CLI Behavior

Entry script:

- `prosperity4bt = prosperity4bt.__main__:main`

### Day argument syntax

The CLI accepts day arguments as strings.

Important detail:

- a single round/day is parsed by splitting on the first `-`
- so negative days are written like `0--1` and `0--2`

Examples:

```bash
prosperity4bt trader.py 0
prosperity4bt trader.py 0--1
prosperity4bt trader.py 0--2 0--1
```

### Output behavior

Default output path:

- `backtests/<timestamp>.log` under the current working directory

Mutually exclusive flags:

- `--out`
- `--no-out`

### Optional behaviors

- `--merge-pnl` merges PnL across multiple day outputs
- `--vis` opens the result in the visualizer
- `--print` tees trader stdout to terminal while preserving captured logs
- `--data` points to a custom resource root
- `--no-progress` disables tqdm progress bars
- `--original-timestamps` preserves original timestamps when merging multi-day
  results

### Module loading behavior

`parse_algorithm(...)`:

- injects `prosperity4bt.datamodel` into `sys.modules["datamodel"]`
- appends the trader's parent directory to `sys.path`
- imports the trader module by filename stem

For multi-day runs:

- the module is reloaded between days
- a new `Trader()` instance is created for each day

Within one day:

- the same Trader instance is reused across ticks

AI tools should still prefer `traderData` over hidden mutable instance state.

---

## Python Replay Semantics

Implemented in `prosperity4bt/runner.py`.

### High-level per-timestamp flow

1. Read prices, trades, and optional observations into `BacktestData`.
2. Set environment variables:
   - `PROSPERITY4BT_ROUND`
   - `PROSPERITY4BT_DAY`
3. Build `TradingState`.
4. Call `Trader.run(state)`.
5. Capture stdout into `lambda_log`.
6. Type-check returned orders.
7. Write activity rows.
8. Enforce per-product position limits.
9. Match orders against book depth, then market trades.
10. Append remaining market trades and own trades to output.

### Position limits

Configured in:

- `LIMITS` in `prosperity4bt/data.py`

Unknown products:

- emit a warning
- default to limit `50`

If worst-case exposure breaches the limit:

- all orders for that product are canceled for that timestamp

### Matching rules

Matching is similar in spirit to the Rust engine:

- book depth first
- remaining quantity optionally matches against market trades
- market-trade fills execute at the trader's quoted price

Trade matching options:

- `all`
- `worse`
- `none`

Enum location:

- `TradeMatchingMode` in `prosperity4bt/models.py`

### PnL model

Per-product PnL is stored in `BacktestData.profit_loss`.

Displayed activity PnL is:

- realized cash
- plus mark-to-mid value of open inventory

### Observations support

Unlike the Rust CSV loader, the Python backtester does read optional
`observations_round_*` CSV files.

Important behavior in `data.py`:

- if a `product` column exists, observations are attached to that product
- otherwise a round-to-product fallback is used through `OBSERVATION_PRODUCTS`

### Conversions caveat

The trader can return `conversions`, but the replay engine does not simulate
conversion execution. Like the Rust backtester, conversions are effectively
ignored by the matching logic.

---

## Python Output Format

The Python backtester writes a plaintext log with three sections:

1. `Sandbox logs:`
2. `Activities log:`
3. `Trade History:`

This is produced by `write_output(...)` in `__main__.py`.

Important consequence:

- this is not a single JSON object like an official payload
- it is the format the visualizer's logger-style parser expects

The per-sandbox row JSON objects come from:

- `SandboxLogRow.__str__()` in `prosperity4bt/models.py`

The log is rich only if the trader uses the logger boilerplate that emits the
compressed `[[...]]` payload through `print()` / `logger.flush(...)`.

Without that logger pattern:

- activity and trade history still render
- but the visualizer cannot reconstruct full orders, traderData, and detailed
  timestamp state

---

## Visualizer Architecture

Main files:

- app router and Mantine provider: `imc-prosperity-4-visualizer/src/App.tsx`
- Vite config and base path: `imc-prosperity-4-visualizer/vite.config.ts`
- global state: `imc-prosperity-4-visualizer/src/store.ts`
- shared types: `imc-prosperity-4-visualizer/src/models.ts`
- parser and download helpers: `imc-prosperity-4-visualizer/src/utils/algorithm.tsx`
- authenticated axios instance: `imc-prosperity-4-visualizer/src/utils/axios.ts`
- home loaders: `src/pages/home/*`
- main visualizer layout: `src/pages/visualizer/VisualizerPage.tsx`
- timestamp drilldown: `src/pages/visualizer/TimestampDetail.tsx`

Base path and router basename are both:

- `/imc-prosperity-4-visualizer/`

---

## Visualizer Input Families

Implemented in `parseAlgorithmLogs(...)` in `src/utils/algorithm.tsx`.

### 1. Official-style JSON payloads

If `JSON.parse(...)` succeeds and the payload contains `activitiesLog`, the
visualizer uses `parseOfficialAlgorithm(...)`.

Supported fields include:

- `activitiesLog`
- optional `tradeHistory`
- optional `logs`
- optional `graphLog`
- optional `profit`
- optional `status`
- optional `positions`

Important behavior:

- orders are synthesized as empty
- `traderData` is synthesized as empty
- observations are synthesized as empty
- `algorithmLogs` become a textual trade summary, not the original trader print
  output

This means official payloads are good for:

- price and PnL inspection
- trade marker overlays
- position reconstruction from `tradeHistory`

They are not good for:

- recovering the trader's intended order list
- recovering next `traderData`
- recovering rich local debug logs unless the parser is extended

### 2. Logger-style plaintext logs

If the content is not parsed as official JSON, the visualizer falls back to the
logger-style parser.

It expects:

- `Sandbox logs:`
- per-timestamp pretty JSON rows containing `sandboxLog` and `lambdaLog`
- `Activities log:`
- `Trade History:`

The rich state reconstruction comes from compressed `[[...]]` rows embedded in
`lambdaLog`.

This is the format generated by:

- the Python backtester output file
- a single-run Rust `combined.log` when the trader prints logger-style rows

---

## Important Rust/Visualizer Interaction

This repo contains a subtle but important format mismatch.

### Rust `submission.log`

The Rust backtester writes `submission.log` as official-style JSON with:

- `submissionId`
- `activitiesLog`
- `logs`
- `tradeHistory`

The visualizer therefore parses it through the official parser path.

Effect:

- it shows price, PnL, positions, and trade markers
- but it does not reconstruct local orders or `traderData`

### Rust `combined.log`

The Rust backtester writes `combined.log` as logger-style plaintext sections.

For a single persisted run, this is the better visualizer input when the trader
uses the logger boilerplate, because the visualizer can reconstruct:

- per-timestamp state
- orders
- conversions field
- previous and next `traderData`
- algorithm logs

Safe AI rule:

- use Rust `combined.log` for rich local visualizer inspection
- use Rust `submission.log` for official-payload-shaped inspection
- do not rely on stitched top-level multi-run bundle files as primary visualizer
  inputs

---

## Visualizer Load Surfaces

### Load from file

File:

- `src/pages/home/LoadFromFile.tsx`

Behavior:

- accepts extracted official `.log` or `.json`
- accepts logger-style local log text files
- rejects `.zip`

### Load from URL

File:

- `src/pages/home/LoadFromUrl.tsx`

Behavior:

- fetches the URL with axios
- parses the content client-side
- supports `?open=<url>` query parameter

### Load from Prosperity

Files:

- `src/pages/home/LoadFromProsperity.tsx`
- `src/utils/axios.ts`
- `src/pages/home/AlgorithmDetail.tsx`

Behavior:

- stores an ID token in persisted Zustand state
- calls Prosperity API endpoints directly
- uses a CORS proxy for the "Open in visualizer" workflow
- lists submissions and supports downloading logs/results

Important maintenance note:

- round selection metadata and availability gating are hardcoded in
  `LoadFromProsperity.tsx`

---

## Visualizer Page Composition

Main composition file:

- `src/pages/visualizer/VisualizerPage.tsx`

It builds the page by symbol and conditionally renders charts such as:

- `ProductPriceChart`
- `VolumeChart`
- `SpreadChart`
- `OrderBookImbalanceChart`
- `MicrostructureChart`
- `TradeFlowChart`
- `FillQualityChart`
- `ConversionPriceChart`
- `TransportChart`
- `EnvironmentChart`
- `PlainValueObservationChart`
- `ProfitLossChart`
- `PositionChart`
- `TimestampsCard`

Timestamp detail panel:

- `src/pages/visualizer/TimestampDetail.tsx`

That component is where listings, order depths, trades, orders, observations,
sandbox logs, algorithm logs, and trader data are shown together.

If an AI tool needs to change what the detailed inspector shows, start there.

If it needs to change parser support for a new log schema, start in:

- `src/utils/algorithm.tsx`

---

## Where To Edit For Common Tasks

If you need to change Python CLI flags or output behavior:

- edit `imc-prosperity-4-backtester/prosperity4bt/__main__.py`

If you need to change matching or replay logic:

- edit `imc-prosperity-4-backtester/prosperity4bt/runner.py`

If you need to add limits or observation-product mappings:

- edit `imc-prosperity-4-backtester/prosperity4bt/data.py`

If you need to change the visualizer parser:

- edit `imc-prosperity-4-visualizer/src/utils/algorithm.tsx`

If you need to change file upload behavior:

- edit `src/pages/home/LoadFromFile.tsx`

If you need to change Prosperity API loading:

- edit `src/pages/home/LoadFromProsperity.tsx`
- edit `src/utils/axios.ts`

If you need to add, remove, or reorder charts:

- edit `src/pages/visualizer/VisualizerPage.tsx`

If you need to change the detailed timestamp inspector:

- edit `src/pages/visualizer/TimestampDetail.tsx`

---

## AI Tool Working Rules

Use the Python backtester when you specifically need its logger-style output or
`--vis` workflow.

Use the visualizer with the right input shape:

- official extracted `.log` or `.json` for hosted-style inspection
- Python backtester `.log` for logger-style local inspection
- Rust `combined.log` for rich local inspection from the Rust engine
- Rust `submission.log` only when official-style JSON is good enough

Do this:

- keep trader state in `traderData`
- use the logger boilerplate when you want deep visualizer support
- update parser code when IMC payload schema changes
- update `LIMITS` and `OBSERVATION_PRODUCTS` when new round data arrives

Do not do this:

- do not upload zip bundles directly to the visualizer
- do not assume official JSON payloads contain orders or traderData
- do not assume conversions are simulated by the Python engine
- do not assume multi-run stitched logs are the best visualizer input

---

## Short Mental Model

The Python backtester is the older text-log replay tool.

The visualizer is a dual-parser UI:

- official JSON payloads on one side,
- logger-style plaintext logs on the other.

Most confusion around these tools comes from giving the visualizer the wrong
artifact for the kind of detail you want.
