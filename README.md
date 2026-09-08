# IMC Prosperity 4

Team algorithmic-trading research with Python strategies and a Rust/Python replay backtester. The Round 4 trader combines inventory-aware market making, pricing for ten call vouchers and signals from disclosed counterparties.

The work connects strategy research to execution: fair values become orders subject to position limits, visible depth and a configurable fill model. The same `Trader.run(state)` interface runs in the competition and local replay.

## Strategy and tooling

- **Market making:** HYDROGEL_PACK combines a fixed anchor with volume-wall estimates. VELVETFRUIT_EXTRACT uses resting depth, autocorrelation and order-book imbalance. Inventory capacity controls quote sizes and taking thresholds.
- **Voucher pricing:** a quadratic smile in log-moneyness supplies strike-dependent values. Expiry assumptions, strike biases and an adaptive at-the-money component adjust the fit.
- **Counterparty signals:** decaying state shifts quotes after selected buyer and seller prints. The final submission excludes Mark 67 after its historical signal failed the recorded null checks.
- **Replay:** Rust calls the Python trader each tick, matches visible depth and approximates queue participation in historical trades. Runs retain per-product PnL and replay logs.

The [submitted trader](submissions/r4_final_v01_imc_upload.py) is a single standard-library Python file. Research dependencies stay outside the upload. Start with the [matching engine](prosperity_rust_backtester/src/runner.rs) and [numerical review](docs/NUMERICAL_REVIEW.md) for the execution and pricing details.

## Recorded Round 4 replay

Independent daily runs of the retained submission produced the following development-set results on 8 September 2026:

| Dataset | Ticks | Local marked PnL |
| --- | ---: | ---: |
| Day 1 | 10,000 | 68,985.50 |
| Day 2 | 10,000 | 110,025.50 |
| Day 3 | 10,000 | 49,499.50 |
| Total | 30,000 | 228,510.50 |

Expiry materially changes those numbers. The archived trader starts each independent run at seven days to expiry. Using the retained briefing's 7/6/5-day schedule gives **215,091.50** in total. The [run evidence](docs/verification/2026-09-08.json) records both configurations. These are local development results, not official competition PnL or returns on unseen data.

From the root, `python3 scripts/replay_round4.py --day 2` runs the explicit expiry configuration and saves its source hash and parameters. The original submission stays unchanged.

The team's retained interim standing was top 32 in manual trading and top 20 in the UK after Rounds 1 and 2. This does not establish a final overall placing.

## Run the reviewed paths

The core replay needs Rust and a linkable Python installation; the pricing and
bid-model checks use the Python standard library. Python 3.11 is the CI baseline.
Run these commands from the repository root:

```bash
python3 -m unittest discover -s tests -v
make -C prosperity_rust_backtester test

cd prosperity_rust_backtester
make round4 TRADER=../submissions/r4_final_v01_imc_upload.py DAY=1 PRODUCTS=full
```

Change `DAY=1` to `2` or `3` to reproduce the table. Always select both trader
and dataset explicitly: filesystem modification times and the newest populated
round are poor experiment identifiers. Each run writes `metrics.json` and a
submission-style log under `prosperity_rust_backtester/runs/`. See the
[replay guide](prosperity_rust_backtester/README.md) for matching controls and
artifact modes.

Other small entry points, from the root:

```bash
python3 prosperity_rust_backtester/scripts/round4_options/bs.py
python3 prosperity_rust_backtester/scripts/round4_options/exotic_pricers.py --spot 40 --sigma 0.20
python3 round3_manual_research/bids.py
python3 prosperity_rust_backtester/scripts/round4_options/counterparty_scan.py --out-dir /tmp/prosperity-counterparties
```

For notebooks and broader statistical analysis, `environment.yml` describes the
larger Conda environment. It is optional for the commands above.

## Research beyond the submitted trader

| Area | Entry point | What to inspect |
|---|---|---|
| Options mathematics | [Round 4 tools](prosperity_rust_backtester/scripts/round4_options/) | Call/put valuation, bracketed IV inversion, smile residuals and manual exotics |
| Counterparty analysis | [Headline findings](prosperity-research/03_eda/round4/headline_findings.md) | Historical mark-outs, identity hypotheses and where the final submission differs |
| Validation decisions | [Signal notes](prosperity-research/04_signal_notes/round4/) | Rejected candidates, null checks and recorded execution concerns |
| Round 3 manual bids | [Bid-model explanation](round3_manual_research/README.md) | Exact reserve-grid EV and sensitivity to assumed opponent behavior |
| Round 5 exploration | [Round 5 diagnostic](prosperity_rust_backtester/traders/Round5/README.md) | Basket residuals and a rejected positive-correlation gate on negatively correlated products |
| Earlier rounds | [Archive](archive/round1_round2/) | Previous product families and development history |
| Hosted observations | [Official replay archive](official_replays/) | Retained portal outputs for comparison, distinct from local replay |

The numerical review found and corrected an IV bisection error, the knockout-put
formula and rate-sensitive deterministic limits. It also fixed censored
counterparty mark-outs, added checked Round 5 caps for the implemented product
subset and removed fabricated default limits for unknown products. The bid
notebooks now have a corrected deterministic companion. Those improvements are
dated **after** the competition; submitted files and historical notebook outputs
remain unchanged. CI runs the numerical and replay tests on future changes.

## Replay limits

The fill model approximates queue position and omits impact, latency, fees and settlement. Nonzero conversions fail explicitly. Unknown position limits reject orders; Round 5 coverage is limited to the implemented PEBBLES and SNACKPACK products. Stale midpoint marks may differ from liquidation value.

Repeated tuning on the same three days creates selection bias. The next strategy evaluation needs a frozen candidate set, chronological holdout and fill-model sensitivity checks, followed by comparison with hosted replays.

## Team and upstream work

Muhammad Taha ([@TahaKhanM](https://github.com/TahaKhanM)), Andy Si ([@andy586586](https://github.com/andy586586)), Arham Shuaib ([@javaxhaskell](https://github.com/javaxhaskell)), Mahmoud Khoder ([@Mkhod51](https://github.com/Mkhod51)) and Ryan Whalen.

Taha's recorded work includes replay integration, Round 4 counterparty and options research, strategy iteration and the later engineering review. Contributions overlap and individual attribution remains in Git and `.mailmap`.

The Rust harness adapts [GeyzsoN/prosperity_rust_backtester](https://github.com/GeyzsoN/prosperity_rust_backtester). Vendored tools adapt [Jasper van Merle's backtester](https://github.com/jmerle/imc-prosperity-3-backtester) and visualizer. Their notices remain with the source. Historical competition and development notes are archived alongside the research.
