# Round 1 Strategy Brief
_Generated 2026-04-19T03:15:41_

This brief is the **curated** handoff for AI tools. The full exhaustive analysis lives in `analysis.ipynb` and the run logs under `plots/`. Read in this order:
1. This file — per-product archetype, edges, and top strategies.
2. `product_params.json` — machine-readable params and thresholds.
3. `metric_summary.csv` — one-row-per-product decision table.
4. `visual_index.md` — which curated plot answers which question.

## Data overview
- Round: **Round 1**
- Days: [-2, -1, 0]
- Price ticks (post-filter): 55,332
- Trades (public): 2,276
- Buyer/seller IDs present: no (anonymised)

## ASH_COATED_OSMIUM
- **Classification:** STABLE  &nbsp;&nbsp; **Archetype:** `fixed_fair_mm` (confidence **high** = 0.92)
  - Secondary archetypes: spike_reversion
  - Reasoning: within-day CV small, anchored mid
- **Best fair proxy:** `mm_mid` (stds: simple_mid=4.8582, microprice=4.8483, wall_mid=4.7538, mm_mid=4.7523)
- **Spread:** mean=16.175  p25/p50/p75=16.0/16.0/18.0  take_edge=4.0  passive_edge=5.33
- **Mean reversion:** lag-1 ACF=-0.4937 → **MEAN REVERTING**
  - Half-life (ticks) by day: d-2=2.595098688519435, d-1=2.2734777834374436, d0=2.59072172701953

### Signals & predictiveness
| signal | corr(h1) | corr(h5) | corr(h20) | hit | verdict |
|---|---:|---:|---:|---:|---|
| wall_delta | +0.588 | +0.553 | +0.467 | 43.9% | ★ use |
| mm_delta | +0.554 | +0.515 | +0.431 | 7.4% | ★ use |
| z20 | -0.542 | -0.509 | -0.441 | 19.9% | ★ use |
| micro_delta | +0.499 | +0.465 | +0.399 | 29.6% | ★ use |
| ret1 | -0.494 | -0.456 | -0.385 | 12.3% | ★ use |
| imbalance | -0.076 | -0.079 | -0.066 | 13.9% | ★ use |
| spread_chg | -0.034 | -0.034 | -0.034 | 21.8% | skip |
Top signal: **wall_delta** (corr=+0.588).

### Monotonic conditional relationships
| bucket feature → fwd horizon | Spearman ρ | mean-range |
|---|---:|---:|
| imbalance__h1 | -0.80 | 1.665 |
| fair_dev_wall__h1 | -1.00 | 2.673 |
| fair_dev_wall__h5 | -1.00 | 2.627 |
| z20__h1 | -1.00 | 2.650 |

### Microstructure fingerprint
- L1 imbalance std=0.2335, 3-level imbalance std=0.2723, OFI std=10.744
- Depth concentration (mean L1/total): bid=0.541, ask=0.541
- Quote-change rate=0.6792, micro−mid std=1.7842
- Regime thresholds: vol [1.5327563750522049, 2.136616853567192]  spread [15.95, 16.45]

### Execution & realised edge
- Buy takes:  n=0, edge@cross=0.0, markout(h5)=0.0, adverse(h1)=0.5
- Sell takes: n=0, edge@cross=0.0, markout(h5)=0.0, adverse(h1)=0.5
- Take-only sim: max_pos=0, pct_at_limit=0.0%, mtm_pnl=0.0
- Spikes: 62 (22.43/10k), avg mag=4.282, reversion tradeable=True

### Top-3 implementation ideas
1. Fixed-fair market making around `mm_mid` with take_edge≈4.0, passive_edge≈5.33, and clear when |position| ≥ 50% of limit.
2. Add small inventory-skew: shift passive quote centre by sign(position) × 0.5 × take_edge once |pos| > 30% of limit.
3. Opportunistic spike reversion: flat outside events, fade extreme ret in small size for ~5 ticks.

### Do NOT try
- Do not run trend-following signals here — lag-1 ACF is strongly negative.

### Confidence / caveats
- Confidence: high (0.92). Evidence is local-sample only.
- Sign-flip risk across days on: ofi_5.

---
## INTARIAN_PEPPER_ROOT
- **Classification:** DRIFTING  &nbsp;&nbsp; **Archetype:** `drifting_mm` (confidence **medium** = 0.52)
  - Secondary archetypes: spike_reversion
  - Reasoning: daily means shift meaningfully
- **Best fair proxy:** `wall_mid` (stds: simple_mid=866.1518, microprice=866.1548, wall_mid=866.1437, mm_mid=866.1492)
- **Spread:** mean=13.047  p25/p50/p75=12.0/13.0/14.0  take_edge=3.0  passive_edge=4.33
- **Mean reversion:** lag-1 ACF=-0.0072 → **NEUTRAL**
  - Half-life (ticks) by day: d-2=0.5636840972253737, d-1=0.4864005628216873, d0=0.4595052212708501

### Signals & predictiveness
| signal | corr(h1) | corr(h5) | corr(h20) | hit | verdict |
|---|---:|---:|---:|---:|---|
| z20 | -0.070 | -0.039 | -0.015 | 24.0% | ★ use |
| mm_delta | +0.069 | +0.028 | +0.011 | 15.1% | ★ use |
| wall_delta | +0.067 | +0.030 | +0.004 | 32.1% | ★ use |
| micro_delta | +0.040 | +0.019 | -0.006 | 26.9% | skip |
| imbalance | -0.015 | -0.003 | +0.007 | 11.6% | skip |
| ret1 | -0.007 | -0.004 | -0.002 | 10.2% | skip |
| spread_chg | -0.005 | -0.004 | -0.002 | 19.2% | skip |
Top signal: **z20** (corr=-0.070).

### Monotonic conditional relationships
| bucket feature → fwd horizon | Spearman ρ | mean-range |
|---|---:|---:|
| imbalance__h1 | -0.80 | 1.973 |
| ofi_5__h1 | +0.90 | 0.204 |
| fair_dev_wall__h1 | -1.00 | 1.873 |
| fair_dev_wall__h5 | -1.00 | 1.767 |
| z20__h1 | -1.00 | 2.231 |
| spread__h1 | -0.80 | 0.781 |

### Microstructure fingerprint
- L1 imbalance std=0.1925, 3-level imbalance std=0.2694, OFI std=8.84
- Depth concentration (mean L1/total): bid=0.55, ask=0.547
- Quote-change rate=0.6318, micro−mid std=1.3774
- Regime thresholds: vol [1.2763022245430604, 1.9303667499810433]  spread [12.45, 13.6]

### Execution & realised edge
- Buy takes:  n=371, edge@cross=4.22, markout(h5)=4.398, adverse(h1)=0.022
- Sell takes: n=113, edge@cross=3.885, markout(h5)=2.92, adverse(h1)=0.027
- Take-only sim: max_pos=80, pct_at_limit=22.45%, mtm_pnl=132895.0
- Spikes: 131 (47.31/10k), avg mag=25.817, reversion tradeable=True

### Top-3 implementation ideas
1. Use a rolling / EWMA `wall_mid` as dynamic fair; take when mid diverges by 3.0 and only clear at fair ± 1 tick.
2. Cap |position| ≤ 60% of limit because simulation shows the naïve take-only strategy pins at the limit — inventory risk dominates.
3. Opportunistic spike reversion: flat outside events, fade extreme ret in small size for ~5 ticks.

### Do NOT try
- Do not anchor fair to a constant (e.g. 10000) — daily means shift ~1000.
- Do not run the naïve take-only strategy — simulation pins at limit 22.45% of ticks.
- Do not overfit a predictive ML model — linear R² is only 0.00624.

### Confidence / caveats
- Confidence: medium (0.52). Evidence is local-sample only.
- Sign-flip risk across days on: ofi_5.

---
## Cross-product
| | ASH_COATED_OSMIUM | INTARIAN_PEPPER_ROOT |
|---|---|---|
| ASH_COATED_OSMIUM | +1.00 | +0.02 |
| INTARIAN_PEPPER_ROOT | +0.02 | +1.00 |

## Implementation reminders
- State lives only in `traderData` (JSON-serialisable, ≤50k chars).
- Keep take→clear→make stages separable; route fair-value per product.
- Do NOT mix tutorial products with live Round 1/2 products.
- Re-run this analyzer with `--round roundN` for each round before trading.