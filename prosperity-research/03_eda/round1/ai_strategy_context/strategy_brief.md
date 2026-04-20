# Round 2 Strategy Brief
_Generated 2026-04-19T03:23:52_

This brief is the **curated** handoff for AI tools. The full exhaustive analysis lives in `analysis.ipynb` and the run logs under `plots/`. Read in this order:
1. This file — per-product archetype, edges, and top strategies.
2. `product_params.json` — machine-readable params and thresholds.
3. `metric_summary.csv` — one-row-per-product decision table.
4. `visual_index.md` — which curated plot answers which question.

## Data overview
- Round: **Round 2**
- Days: [-1, 0, 1]
- Price ticks (post-filter): 55,432
- Trades (public): 2,391
- Buyer/seller IDs present: no (anonymised)

## ASH_COATED_OSMIUM
- **Classification:** STABLE  &nbsp;&nbsp; **Archetype:** `fixed_fair_mm` (confidence **high** = 0.92)
  - Secondary archetypes: spike_reversion
  - Reasoning: within-day CV small, anchored mid
- **Best fair proxy:** `wall_mid` (stds: simple_mid=4.5899, microprice=4.5763, wall_mid=4.4631, mm_mid=4.4644)
- **Spread:** mean=16.234  p25/p50/p75=16.0/16.0/18.0  take_edge=4.0  passive_edge=5.33
- **Mean reversion:** lag-1 ACF=-0.4818 → **MEAN REVERTING**
  - Half-life (ticks) by day: d-1=2.3486975129141987, d0=2.8840975701109866, d1=2.9523226115665415

### Signals & predictiveness
| signal | corr(h1) | corr(h5) | corr(h20) | hit | verdict |
|---|---:|---:|---:|---:|---|
| wall_delta | +0.588 | +0.562 | +0.473 | 44.4% | ★ use |
| mm_delta | +0.543 | +0.524 | +0.441 | 7.0% | ★ use |
| z20 | -0.537 | -0.517 | -0.438 | 20.0% | ★ use |
| micro_delta | +0.503 | +0.477 | +0.404 | 29.5% | ★ use |
| ret1 | -0.482 | -0.465 | -0.386 | 12.5% | ★ use |
| imbalance | -0.092 | -0.085 | -0.071 | 13.5% | ★ use |
| spread_chg | -0.054 | -0.058 | -0.045 | 21.7% | ★ use |
Top signal: **wall_delta** (corr=+0.588).

### Monotonic conditional relationships
| bucket feature → fwd horizon | Spearman ρ | mean-range |
|---|---:|---:|
| imbalance__h1 | -0.80 | 1.743 |
| fair_dev_wall__h1 | -1.00 | 2.611 |
| fair_dev_wall__h5 | -1.00 | 2.636 |
| z20__h1 | -1.00 | 2.545 |
| spread__h1 | -0.90 | 1.176 |

### Microstructure fingerprint
- L1 imbalance std=0.2317, 3-level imbalance std=0.2692, OFI std=10.885
- Depth concentration (mean L1/total): bid=0.542, ask=0.539
- Quote-change rate=0.682, micro−mid std=1.7863
- Regime thresholds: vol [1.5096182856672888, 2.0930649900639926]  spread [16.0, 16.5]

### Execution & realised edge
- Buy takes:  n=0, edge@cross=0.0, markout(h5)=0.0, adverse(h1)=0.5
- Sell takes: n=0, edge@cross=0.0, markout(h5)=0.0, adverse(h1)=0.5
- Take-only sim: max_pos=0, pct_at_limit=0.0%, mtm_pnl=0.0
- Spikes: 43 (15.52/10k), avg mag=3.942, reversion tradeable=True

### Top-3 implementation ideas
1. Fixed-fair market making around `wall_mid` with take_edge≈4.0, passive_edge≈5.33, and clear when |position| ≥ 50% of limit.
2. Add small inventory-skew: shift passive quote centre by sign(position) × 0.5 × take_edge once |pos| > 30% of limit.
3. Opportunistic spike reversion: flat outside events, fade extreme ret in small size for ~5 ticks.

### Do NOT try
- Do not run trend-following signals here — lag-1 ACF is strongly negative.

### Confidence / caveats
- Confidence: high (0.92). Evidence is local-sample only.

---
## INTARIAN_PEPPER_ROOT
- **Classification:** DRIFTING  &nbsp;&nbsp; **Archetype:** `drifting_mm` (confidence **high** = 0.93)
  - Secondary archetypes: spike_reversion, imbalance_follower
  - Reasoning: daily means shift meaningfully
- **Best fair proxy:** `mm_mid` (stds: simple_mid=865.8538, microprice=865.8549, wall_mid=865.8529, mm_mid=865.8454)
- **Spread:** mean=14.122  p25/p50/p75=13.0/14.0/15.0  take_edge=3.25  passive_edge=4.67
- **Mean reversion:** lag-1 ACF=-0.4947 → **MEAN REVERTING**
  - Half-life (ticks) by day: d-1=0.5028014975651217, d0=0.4549211780834439, d1=0.4345222086933479

### Signals & predictiveness
| signal | corr(h1) | corr(h5) | corr(h20) | hit | verdict |
|---|---:|---:|---:|---:|---|
| z20 | -0.637 | -0.644 | -0.637 | 23.1% | ★ use |
| wall_delta | +0.573 | +0.576 | +0.572 | 32.1% | ★ use |
| mm_delta | +0.538 | +0.534 | +0.533 | 14.7% | ★ use |
| ret1 | -0.495 | -0.501 | -0.489 | 9.6% | ★ use |
| micro_delta | +0.464 | +0.464 | +0.459 | 26.8% | ★ use |
| imbalance | -0.117 | -0.127 | -0.118 | 11.5% | ★ use |
| spread_chg | -0.022 | -0.018 | -0.027 | 18.8% | skip |
Top signal: **z20** (corr=-0.637).

### Monotonic conditional relationships
| bucket feature → fwd horizon | Spearman ρ | mean-range |
|---|---:|---:|
| imbalance__h1 | -0.80 | 2.038 |
| fair_dev_wall__h1 | -1.00 | 3.460 |
| fair_dev_wall__h5 | -1.00 | 3.627 |
| z20__h1 | -1.00 | 3.021 |

### Microstructure fingerprint
- L1 imbalance std=0.192, 3-level imbalance std=0.2696, OFI std=8.864
- Depth concentration (mean L1/total): bid=0.551, ask=0.553
- Quote-change rate=0.6287, micro−mid std=1.4844
- Regime thresholds: vol [1.352142549320981, 2.106381282024501]  spread [13.55, 14.65]

### Execution & realised edge
- Buy takes:  n=363, edge@cross=4.49, markout(h5)=4.694, adverse(h1)=0.003
- Sell takes: n=225, edge@cross=3.929, markout(h5)=2.978, adverse(h1)=0.022
- Take-only sim: max_pos=80, pct_at_limit=7.37%, mtm_pnl=142519.0
- Spikes: 118 (42.56/10k), avg mag=2.992, reversion tradeable=True

### Top-3 implementation ideas
1. Use a rolling / EWMA `wall_mid` as dynamic fair; take when mid diverges by 3.25 and only clear at fair ± 1 tick.
2. Cap |position| ≤ 60% of limit because simulation shows the naïve take-only strategy pins at the limit — inventory risk dominates.
3. Add an OFI / L1-imbalance overlay: bias quote placement and take threshold in the direction of `imb_l1` once it exceeds its ±1σ band.

### Do NOT try
- Do not run trend-following signals here — lag-1 ACF is strongly negative.
- Do not anchor fair to a constant (e.g. 10000) — daily means shift ~1000.

### Confidence / caveats
- Confidence: high (0.93). Evidence is local-sample only.
- Sign-flip risk across days on: ofi_5.

---
## Cross-product
| | ASH_COATED_OSMIUM | INTARIAN_PEPPER_ROOT |
|---|---|---|
| ASH_COATED_OSMIUM | +1.00 | -0.00 |
| INTARIAN_PEPPER_ROOT | -0.00 | +1.00 |

## Implementation reminders
- State lives only in `traderData` (JSON-serialisable, ≤50k chars).
- Keep take→clear→make stages separable; route fair-value per product.
- Do NOT mix tutorial products with live Round 1/2 products.
- Re-run this analyzer with `--round roundN` for each round before trading.