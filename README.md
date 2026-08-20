# IMC Prosperity 4

IMC Prosperity is an algorithmic trading competition run by IMC Trading. It runs
over five rounds plus a tutorial and draws more than 22,000 teams. Each round
adds new tradeable products and a separate manual trading puzzle. Rounds last 48
to 72 hours. This repository is our team's workspace for Prosperity 4: the Python
traders we submitted, a Rust backtester that runs them against historical order
book data, the options and volatility tooling we built for the voucher products
and the research pipeline behind the decisions. After Rounds 1 and 2, the team
placed in the top 32 for manual trading and the top 20 in the UK. These were
interim results, not the final overall placement.

## The team

Authorship is preserved in the git history. A `.mailmap` at the repository root
consolidates each contributor's several git identities under one name.

- Muhammad Taha ([@TahaKhanM](https://github.com/TahaKhanM))
- Andy Si ([@andy586586](https://github.com/andy586586))
- Arham Shuaib ([@javaxhaskell](https://github.com/javaxhaskell))
- Mahmoud Khoder ([@Mkhod51](https://github.com/Mkhod51))
- Ryan Whalen

## What is in here

### Rust backtest harness (`prosperity_rust_backtester/src/`)

The centerpiece. It runs the exact Python `Trader` class we submitted to IMC
against historical order book data, so iteration is fast, deterministic and
local instead of waiting on the hosted environment. `src/pytrader.rs` embeds a
Python interpreter through pyo3, loads the trader file, calls `Trader.run(state)`
each tick and normalizes the `(orders, conversions, traderData)` tuple that IMC
expects. `src/runner.rs` matches orders against the book, applies fills and
writes per-run artifacts (metrics, a submission log and PnL by product). It is
about 5,000 lines of Rust across seven modules, driven by a Makefile. One
command replays a full trading day in a few seconds.

### Options and volatility tooling (`prosperity_rust_backtester/scripts/round4_options/`)

Stateless, standard-library-only Python for the voucher products (European call
vouchers on an underlying) and the manual exotics:

- `bs.py`: Black-Scholes call and put pricer with an implied volatility solver.
- `vol_surface_fit.py`: per-tick quadratic smile fit that extracts the at-the-money
  implied vol, skew, convexity and per-strike residuals.
- `parity_scan.py`: put-call parity and identity checks (intrinsic floor, upper
  bound, monotonicity and butterfly convexity).
- `exotic_pricers.py`: closed-form fair values for the Round 4 manual puzzle, a
  chooser option (K=50), a binary put (K=40, pays 10) and a down-and-out barrier
  put (K=45, barrier 35).
- `stat_tests.py`: stationarity, Hurst exponent, Ornstein-Uhlenbeck half-life,
  variance ratio and spectral peak, all without third-party dependencies.

### Counterparty intelligence (`round4_options/counterparty_scan.py`, `per_mark_features.py`)

Round 4 was the round where the exchange disclosed counterparty IDs: every other
participant is named `Mark <NN>`. We built per-counterparty horizon PnL analysis
over three days of historical trades and found participants worth trading around:

- Mark 14 is an informed bot: about +49,777 in horizon-500 PnL over three days,
  +5.71 per unit, winning on both sides of HYDROGEL_PACK and VELVETFRUIT_EXTRACT.
  When it trades, we lean with its flow.
- Mark 38 is the mirror image: about -41,696, -8.34 per unit. We take the other
  side of its prints.
- Mark 67 is buy-only on VELVETFRUIT_EXTRACT (1,510 buys and 0 sells), so we lean
  long when it prints.

We shipped this as a live signal in the Round 4 trader rather than leaving it as
a note. We also checked and rejected a time-of-day angle: no Mark concentrates
more than 14% of its trades in any hour bucket, so the trader does not gate on
time. The full numbers are in
`prosperity-research/03_eda/round4/headline_findings.md`.

### Market-making strategies (`submissions/`, `prosperity_rust_backtester/traders/`)

The shipped traders make markets around estimated fair values with inventory
control:

- HYDROGEL_PACK is anchored but not pinned to 10,000. Fair value is an EMA
  (half-life 200) clamped to [9,980, 10,010] and seeded at 9,991, with
  position-dependent quote skew.
- VELVETFRUIT_EXTRACT uses a wall-mid fair value, the mid of the highest-volume
  resting levels, which led next-tick mid moves with a regression slope of 0.77
  across three days.
- Both skew quotes on top-two order book imbalance, with the skew coefficient fit
  from data (t-statistic 35 on HYDROGEL, 20 on VELVETFRUIT) and capped at two
  ticks.

Each block sits behind a feature flag in `traderData` so it can be toggled
without redeploying. The parameters and the rejection gate each one passed are in
`prosperity-research/04_signal_notes/round3/ship_now.md`.

### Research pipeline (`prosperity-research/`)

A numbered workflow from raw CSVs through assumptions, EDA, signal notes with
explicit rejection gates, validation, execution-risk analysis and dated
experiment logs. This is where the discipline under deadline shows. Several
signals that looked good in EDA were held out of the first submission on purpose.
An implied-vol residual scalp was dropped because the backtester's fill model
over-reported it. A deep in-the-money overlay was dropped because its settlement
semantics were not yet verified against the hosted exchange.
`prosperity-research/README.md` is the map.

### Manual round work (`round3_manual_research/`, `prosperity_rust_backtester/traders/Round4/manual_trading_sims/`)

Each round has a manual puzzle that is independent of the algorithmic trader. We
solved them by simulation: the Round 3 sealed-bid puzzle by searching bid pairs
against an assumed distribution of opponent bids and the Round 4 Aether Crystal
options by pricing the chooser, binary put and knockout put directly with the
exotic pricers above.

## Repository map

```text
.
├── prosperity_rust_backtester/   Rust backtester, submitted traders and options tooling
│   ├── src/                        the harness (pytrader.rs runs the trader, runner.rs matches orders)
│   ├── traders/                    per-round trader variants and single-idea probes
│   ├── scripts/round4_options/     Black-Scholes, vol surface, parity, exotics, counterparty analysis
│   ├── datasets/                   canonical historical round data the backtester reads from
│   └── Makefile                    per-round run targets
├── prosperity-research/          numbered research pipeline (assumptions, EDA, signals, validation, logs)
├── submissions/                  traders submitted to the IMC portal, as uploaded
├── round3_manual_research/       Round 3 manual-puzzle simulation notebooks
├── official_replays/             logs pulled back from the official exchange, kept as reference
├── archive/                      Round 1 and 2 material, kept for reference only
├── vendor/                       adapted third-party tools (jmerle's Python backtester and visualizer)
├── docs/competition/             frozen competition-era agent instructions, context and briefings
├── scripts/                      cross-tool probe and environment-setup helpers
├── environment.yml               conda environment
└── .mailmap                      contributor identity consolidation
```

## Running it

### Setup

The Rust backtester needs a Rust toolchain and a Python interpreter (it embeds
Python to run the trader). The full analysis environment is captured in
`environment.yml`:

```bash
conda env create -f environment.yml
conda activate prosperity
```

Install Rust once with rustup if you do not have it:

```bash
curl https://sh.rustup.rs -sSf | sh
```

### Build and replay a strategy

From the backtester directory, this builds the harness and replays the shipped
Round 4 trader against Round 4 day 1 order book data:

```bash
cd prosperity_rust_backtester
make round4 TRADER=../submissions/r4_final_v01_imc_upload.py DAY=1
```

On this dataset it returns about 69,000 in PnL and prints a per-product
breakdown (HYDROGEL_PACK, VELVETFRUIT_EXTRACT and the vouchers). The macOS
`make` targets build through a wrapper and write Rust artifacts outside the repo;
see `prosperity_rust_backtester/README.md` for the details and the other round
targets.

### Run an analysis script

The options tooling is standard-library only, so it runs with a plain
interpreter:

```bash
cd prosperity_rust_backtester/scripts/round4_options
python3 bs.py                                   # Black-Scholes pricer and IV solver self-test
python3 exotic_pricers.py --spot 48 --sigma 0.20   # chooser, binary put and knockout put fair values
```

## Acknowledgments

- The Rust backtester is adapted from
  [GeyzsoN's prosperity_rust_backtester](https://github.com/GeyzsoN/prosperity_rust_backtester).
  The team added the traders, the options tooling and the counterparty analysis
  on top of it.
- The Python backtester and the web visualizer under `vendor/` are adapted from
  jmerle's (Jasper van Merle) Prosperity 3
  [backtester](https://github.com/jmerle/imc-prosperity-3-backtester) and
  visualizer.
- IMC Trading for running the competition.

## Limitations

- This is competition code written under 48 to 72 hour round deadlines, not a
  packaged library. It reads best as a working strategy workspace.
- The local backtester is close to the hosted exchange but does not reproduce it
  exactly. The fill model in particular is approximate, which is why some signals
  were deliberately held back from the first submission.
- Some datasets, logs and research artifacts are kept for provenance, not because
  they are active entry points.
