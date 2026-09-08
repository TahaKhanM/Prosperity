# Rust replay harness

This directory adapts [GeyzsoN's Prosperity backtester](https://github.com/GeyzsoN/prosperity_rust_backtester)
to this team's trading workspace. Rust owns dataset parsing, order matching,
inventory and output artifacts; PyO3 runs the Python competition trader.
The [root README](../README.md) explains the strategies and attribution.

## Setup and a reproducible replay

Clone this portfolio repository, then enter this directory:

```bash
git clone https://github.com/TahaKhanM/Prosperity.git
cd Prosperity/prosperity_rust_backtester
make doctor
make test
make round4 TRADER=../submissions/r4_final_v01_imc_upload.py DAY=1 PRODUCTS=full
```

Install Rust with your usual rustup toolchain and use Python 3.11 or later with
a linkable Python library. `make` builds automatically. On macOS the build
wrapper selects a suitable interpreter and uses
`~/Library/Caches/rust_backtester/target`; override `PYO3_PYTHON` and
`CARGO_TARGET_DIR` if required. Linux and WSL use Cargo directly. CI tests Linux
with Python 3.11. Native Windows is not the maintained workflow.

There is no `traders/latest_trader.py` in this archive. The CLI's legacy automatic
selection uses file modification times and the latest populated round; do not
use those defaults to identify an experiment. Explicit trader/dataset pairs
avoid selecting incompatible products from another round.

## Execution model

1. Parse matching prices/trades CSVs, normalized JSON or a portal submission log.
2. Order ticks by day and timestamp. Construct the Python state with current
   visible depth and the previous tick's public/own trades.
3. Run the trader. Reject a product's full order set if either possible buy or
   sell exposure exceeds its position cap.
4. Match marketable orders against visible depth, then eligible remaining orders
   against historical trade prints under the queue approximation.
5. Mark inventory to the snapshot mid and emit metrics/replay artifacts.

The risk check uses separate worst-case buy and sell totals, because the venue
need not fill both sides. Nonzero conversions are unsupported and now abort the
replay. Unknown product caps cancel orders with a diagnostic. The implemented
Round 5 PEBBLES/SNACKPACK subset has 10-unit caps; other Round 5 products still
need verified definitions.

Visible queue depth is a proxy for queue priority, not a reconstruction of the
hidden matching engine. There is no impact, latency, fee or expiry-settlement
model. Missing mids carry the last observed mark without looking ahead; an open
position with no observed mark fails. Stale marks are not executable liquidation
prices, so use complete snapshots for performance comparisons.

## Commands and outputs

```bash
# Isolate each historical day; outputs reset by default.
make round4 TRADER=../submissions/r4_final_v01_imc_upload.py DAY=2
make round4 TRADER=../submissions/r4_final_v01_imc_upload.py DAY=3

# Preserve orders, fills, per-product PnL and replay material.
make round4 TRADER=../submissions/r4_final_v01_imc_upload.py DAY=1 PERSIST=1

# CLI help includes matching sensitivity and artifact controls.
./scripts/cargo_local.sh run -- --help
```

The reproduced artifact PnLs are 68,985.50, 110,025.50 and 49,499.50
(development-set results, default matching). That file starts every independent
day at seven days to expiry. From the repository root,
`python3 scripts/replay_round4.py --day 2` applies the retained briefing's
six-day assumption and produces 89,936.00; day3 at five days gives 56,170.00.
See the root README for this material sensitivity and its source boundary. `runs/<id>/metrics.json` records the
selected inputs and matching settings; default runs also write `submission.log`.
Use `--artifact-mode none` for metrics only, `diagnostic` for a PnL-series bundle or `full` for orders/trades and CSV output. `PERSIST=1` selects full artifacts.

`--carry` connects positions and trader state across non-submission days and
normalizes their timestamps into one timeline. That changes the experiment and
can affect timestamp-based expiry calculations. It was **not** used for the
reported independent-day table. `--flat` changes only the output layout.

## Source map and verification

| File | Responsibility |
|---|---|
| `src/model.rs` | Dataset and artifact types, CSV/JSON/log parsing |
| `src/pytrader.rs` | Python data model and trader invocation |
| `src/runner.rs` | Matching, risk limits, accounting and artifacts |
| `src/cli.rs` | Explicit input selection, multi-day/carry orchestration |
| `scripts/round4_options/` | Standalone offline pricing and signal analysis |
| `tests/fixtures/` | Small deterministic test trader, independent of submissions |

```bash
make test
cd ..
python3 -m unittest discover -s tests -v
```

The [numerical review](../docs/NUMERICAL_REVIEW.md) records the post-competition
corrections and their assumptions. Tests check price identities and independent
quadrature as well as replay interfaces and risk limits; passing them does not
certify parity with the hosted exchange.
