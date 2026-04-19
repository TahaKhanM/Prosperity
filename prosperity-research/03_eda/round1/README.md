# 03_eda/round1 — Competition-grade Alpha Research Analyzer

First-pass research tool for Round 1 / Round 2 products
(`ASH_COATED_OSMIUM`, `INTARIAN_PEPPER_ROOT`). Works directly against the raw
CSVs under `prosperity_rust_backtester/datasets/<round>/`.

## How to run

```bash
# script (canonical, produces full plot set + curated AI export)
python analysis.py --round round1
python analysis.py --round round2

# notebook (same code, cell-by-cell; change ROUND in the setup cell)
jupyter lab analysis.ipynb
```

## Design principle

**Notebook / full analysis = exhaustive.**
**AI export = curated, compressed, context-window aware.**

The notebook walks through every section (1–19) and prints diagnostics and
plots to `plots/<round>/`. Section 20 collapses the findings into a compact
handoff under `ai_strategy_context/`.

## Analysis sections

| # | Topic | Primary output |
|---|---|---|
| 0 | Data loading & feature engineering | feature-rich per-product dataframes |
| 1 | Product classification (STABLE / DRIFTING / VOLATILE) | `1*_price_*`, verdict map |
| 2 | Fair-value estimation (simple / micro / wall / mm mids) | `2A_fair_value_*`, `2C_fv_ranking` |
| 3 | Spread & edge calibration | `3A/3B`, `take_edge`, `passive_edge` |
| 4 | Mean-reversion vs trend (ACF, z-score) | `4A/4B`, lag-1 ACF |
| 5 | Signal predictiveness (multi-horizon) | `5A/5B/5C`, corr + hit-rate table |
| 6 | Counterparty / trade-pattern / trader-ID | `6A–6E`, informed-trader flags |
| 7 | Intraday pattern & long-lag periodicity | `7A/7B/7C` |
| 8 | Spike detection & event study | `8A/8B`, post-spike path |
| 9 | Cross-product correlation / lead-lag | `9A/9B/9C`, correlation matrix |
| 10 | Position / inventory risk simulation | `10A`, pct-at-limit, MtM PnL |
| 11 | Parameter sensitivity (TE × CT) | `11A` heatmap |
| 12 | 9-panel strategy decision dashboard | `12_dashboard_<product>` |
| 13 | **Extended microstructure** — weighted spread, L1 imbalance, OFI (Cont–Kukanov–Stoikov), depth concentration, quote-change rate, book slope | `13A/13B` |
| 14 | **Conditional returns by state bucket** — E[fwd_ret] for quintile buckets of imbalance / OFI / fair_dev / z20 / spread, with Spearman monotonicity flagged | `14A` |
| 15 | **Regime segmentation** — vol × spread states, occupancy and abs-return per regime | `15A/15B` |
| 16 | **Execution quality & markout** — take-opp counts, signed markout h=1/5/20, adverse-selection rate | `16A/16B` |
| 17 | **Cross-day robustness** — per-day signal corr heatmap, sign-flip detection | `17A` |
| 18 | **AR(1) half-life by day** — supplementary mean-reversion timescale | console table |
| 19 | **Feature relevance (standardised OLS, rank-only)** — ridge-stabilised β on fwd_ret_1 | `19A` |
| 20 | **Curated AI export builder** | `ai_strategy_context/` |

## `ai_strategy_context/` export (what AI tools consume)

| file | purpose | why curated |
|---|---|---|
| `strategy_brief.md` | per-product archetype, edges, top-3 ideas, anti-ideas, caveats | human+AI readable end-to-end in < 2 min |
| `product_params.json` | schema v2 machine-readable payload: classification, archetype, fair proxy, spread, microstructure, signals, monotonic conditional relationships, per-day robustness, execution stats, feature relevance, daily stats, regime thresholds, recommended horizons, inventory posture | single source of truth for Codex |
| `metric_summary.csv` | one row per product, ~22 decision-relevant columns | compact for reasoning chat |
| `visual_index.md` | annotated index of the curated plots | tells AI which plot answers which question |
| `plots/` | ~11 plot templates × products + 1 shared ≈ 21 PNGs | avoids dumping the 50+ notebook plots |
| `data_samples/` | 200-row CSV samples per product (prices + trades) | enough for AI to see schema, bounded |

The live `ai_strategy_context/` directory is still overwritten on each run, but
the analyzer now also mirrors a clean round-specific snapshot to
`ai_strategy_context_by_round/<round>/` so Round 1 and Round 2 exports can be
compared side by side without manual copying.

**Curated plot set (template → one per product where `<P>` substitutes):**
`12_dashboard_<P>`, `2A_fair_value_<P>`, `3B_spread_distribution` (shared),
`5B_signal_decay_<P>`, `14A_conditional_returns_<P>`, `16A_markout_<P>`,
`17A_robust_<P>`, `15B_vol_regime_<P>`, `8B_spike_reversion_<P>`,
`19A_feature_relevance_<P>`, `9B_correlation_matrix` (shared).

## Data contract

- Raw CSVs under `prosperity_rust_backtester/datasets/round1/` and
  `.../round2/` are authoritative. This directory never caches raw data.
- Empty-book rows (L1 bid or ask missing, or mid = 0) are filtered on load.
- L2 and L3 are sparsely populated; OFI, imbalance, and book-slope features
  tolerate the NaNs.
- `buyer` / `seller` IDs are empty in Round 1 and Round 2 sample data. The
  trader-ID follower archetype activates automatically once IDs appear.

## Naming conventions

- Script entrypoint: `analysis.py` (default `--round round1`).
- Notebook entrypoint: `analysis.ipynb` (change `ROUND` in setup cell).
- Full-run plots: `plots/<round>/`.
- Curated AI export: `ai_strategy_context/` (overwritten per run — re-run
  for whichever round you want live).

Classification: canonical stage artifact directory.
