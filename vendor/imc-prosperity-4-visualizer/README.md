# IMC Prosperity 4 Visualizer

Interactive visualizer for Prosperity algorithms and official IMC Round 1 log payloads.

This app now supports two input families:

1. Logger-style text logs produced by a trader that uses the visualizer logger boilerplate.
2. Extracted official IMC payload files from a hosted submission bundle:
   - the extracted `.log` JSON payload
   - or the extracted `.json` summary payload

It does **not** currently parse the `.zip` bundle directly in-browser. Extract the file first, then upload the extracted `.log` or `.json`.

## What the visualizer can show

- per-product price history
- top-3 book levels
- total and per-product running PnL
- position history
- timestamp-by-timestamp state inspection
- own trades
- market trades
- submission trade markers and external trade markers overlaid on the price chart

For official payloads, the app reconstructs a best-effort `TradingState` per timestamp from:

- `activitiesLog`
- `tradeHistory`
- per-timestamp hosted log rows when present

Official payloads do not contain full local logger details such as:

- submitted orders per timestamp
- next traderData
- custom algorithm print logs

So those fields are synthesized as empty or summary values where necessary.

## Supported file formats

### A. Official IMC hosted submission output

Typical official bundle contents:

- `123456.log`
- `123456.json`
- `123456.py`

To view an official run:

1. Extract the IMC zip bundle.
2. Upload either the extracted `.log` file or the extracted `.json` file.
3. The visualizer will parse the current official payload format directly.

Notes:

- the extracted `.log` file is usually richer because it includes `tradeHistory`
- the extracted `.json` file is still useful for activity/PnL inspection, but may omit trade history

### B. Local logger-style text logs

If you want the fullest timestamp detail for local runs, use the logger boilerplate shown on the home page and upload the resulting log text file.

## Current official format compatibility

The current parser handles official payloads that contain:

- `activitiesLog`
- optional `tradeHistory`
- optional `logs`
- optional `graphLog`
- optional `profit`, `status`, and final `positions`

If IMC changes that schema materially, parser updates may be needed.

## Recommended workflow for current Round 1 research

### Visual inspection of hosted runs

Use the extracted official `.log` payload when possible.

Best pages/features for Round 1:

- `Price` chart:
  - inspect bid/ask ladder movement
  - inspect submission buy/sell markers
  - inspect external trade markers
- `Profit / Loss` chart:
  - compare total and per-product contributions
- `Position` chart:
  - identify carry phases vs recycle phases
- timestamp slider:
  - inspect book state, own trades, market trades, positions, and synthesized official trade summaries

### Deeper mechanical analysis

For official market-mechanics research, pair the visualizer with:

```bash
python3 prosperity_rust_backtester/scripts/analyze_official_logs.py /path/to/run.zip
```

or:

```bash
python3 prosperity_rust_backtester/scripts/analyze_official_logs.py /path/to/log-folder --export-dir /tmp/official-log-analysis
```

That analyzer produces normalized CSV/JSON exports that complement the interactive visualizer.

## Local development

Requirements:

- Node.js 22+
- pnpm

Install and run:

```bash
pnpm install
pnpm dev
```

Build:

```bash
pnpm build
```

## Implementation notes

- Old logger-style parsing still works.
- Official payload parsing is now handled directly in `src/utils/algorithm.tsx`.
- Price charts now include trade markers:
  - submission buys
  - submission sells
  - external trades
- Zip parsing is intentionally left out of the browser app to keep the dependency surface smaller and the workflow explicit.
