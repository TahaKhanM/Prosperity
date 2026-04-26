# Round 4 voucher / counterparty / exotic-option toolkit

Stateless, stdlib-only research utilities for Round 4 ("The More The Merrier",
Salvinar). Mirrors the Round 3 toolkit (`scripts/round3_options/`) but updated
for the Round 4 dataset (days 1/2/3, TTE 7/6/5/4) and the disclosed
counterparty IDs (`Mark <NN>`).

## Contents

| Script | Purpose |
|---|---|
| `bs.py` | Black-Scholes call/put pricer + IV solver. Adds put pricer needed by exotics. |
| `build_voucher_panel.py` | Per-tick (S, voucher mid, intrinsic, time value, moneyness, IV) panel for Round 4 days 1/2/3. |
| `parity_scan.py` | Identity arbs (intrinsic floor, upper bound, monotonicity, butterfly convexity). |
| `vol_surface_fit.py` | Per-tick parabolic smile fit; ATM IV, skew, convexity, residuals per strike. |
| `counterparty_scan.py` | Per-`Mark <NN>` horizon-PnL rollup + temporal histogram + auto-classification. |
| `exotic_pricers.py` | Closed-form pricers for the Round 4 manual exotics: chooser (K=50), digital put (K=40, payoff 10), down-and-out put (K=45, B=35). |
| `stat_tests.py` | Stdlib stationarity / Hurst / OU half-life / variance-ratio / spectral peak. |
| `per_mark_features.py` | Per-(Mark, product) feature CSVs for the dossier project. Writes `prosperity-research/03_eda/round4/per_mark/<MARK>_<PRODUCT>.csv` with one row per print: pre/post mids, imb1/2/3, depth, microprice, recency counters, inferred inventory (per-day + cumulative), realised vol, aggressor flag, adverse-selection at h=5/20/100. Used by Phase 1 of the R4 Mark dossier project. |

## Usage

```sh
# 1. Build the per-tick voucher panel (writes prosperity-research/03_eda/round4/voucher_panel.csv)
python3 build_voucher_panel.py

# 2. Identity-only parity scan (writes prosperity-research/04_signal_notes/round4/parity_violations.csv)
python3 parity_scan.py

# 3. Vol-surface fit (writes vol_surface_coeffs.csv + vol_surface_residuals.csv)
python3 vol_surface_fit.py

# 4. Counterparty rollup (writes counterparty_scan.csv + temporal + findings.md)
python3 counterparty_scan.py

# 5. Manual-round exotic-option fair values (e.g. spot=50, sigma=0.30)
python3 exotic_pricers.py --spot 50 --sigma 0.30
```

## Defaults

- Dataset root: `prosperity_rust_backtester/datasets/round4/`
- Research output: `prosperity-research/03_eda/round4/` and
  `prosperity-research/04_signal_notes/round4/`
- All CSVs use `;` as the delimiter (matches the rest of the repo).

## Round 4 vs Round 3

The math is unchanged. The Round 4 toolkit:
- Uses TTE_BY_DAY = {1: 7, 2: 6, 3: 5} (live R4 = TTE 4); R3 used
  {0: 8, 1: 7, 2: 6}.
- Reads the named `Mark <NN>` strings in counterparty fields instead of
  treating them all as `_anon_`.
- Adds `exotic_pricers.py` for the new manual-round exotics; R3's manual
  challenge was Bio-Pods (no options).

The Round 3 toolkit is preserved at `scripts/round3_options/` and is safe to
import from. New work should default to `round4_options/` to avoid the
TTE-numbering mistake.
