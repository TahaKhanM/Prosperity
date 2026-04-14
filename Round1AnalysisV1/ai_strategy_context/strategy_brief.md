# Round 1 Strategy Brief
Generated: 2026-04-14 14:17:40

## Data Overview
- Days available: [np.int64(-2), np.int64(-1), np.int64(0)]
- Price ticks: 55,332 total (after filtering empty books)
- Trades: 2,276 total
- Buyer/seller IDs: **empty** (anonymised in Round 1 sample data)


---
## ASH_COATED_OSMIUM
**Position limit:** 80
**Classification:** STABLE (within-day CV=0.000459)
**Recommended strategy:** Fixed Fair Value Market Making

### Price Behavior
- Day -2: open=10000, close=9994, low=9984, high=10012, mean=9998, std=4.7
- Day -1: open=9992, close=10002, low=9986, high=10014, mean=10001, std=3.8
- Day 0: open=10003, close=10007, low=9982, high=10018, mean=10002, std=5.2
- Overall mean: 10000.2, overall std: 4.9
- Return autocorrelation: lag-1=-0.4937 → **MEAN REVERTING**
- Price anchored at ~10000. Deviations revert.

### Spread & Edge Parameters
- Spread: mean=16.2, median (p50)=16.0, p25=16.0, p75=18.0
- **take_edge = 4.00** (= p25/4, sweep when ask < FV - take_edge)
- **passive_edge = 5.33** (= p50/3, quote at FV ± passive_edge)

### Fair Value Estimator
- **Best: mm_mid** (lowest std = most stable)
  - simple_mid: std=4.8582
  - microprice: std=4.8483
  - wall_mid: std=4.7538
  - mm_mid: std=4.7523 ← USE
- MM-filtered mid uses orders >= 10 lots (filters noise from small orders)

### Signal Predictiveness (correlation with next-tick return)
| Signal | Corr(h=1) | Corr(h=5) | Corr(h=20) | Hit Rate | Direction |
|--------|-----------|-----------|------------|----------|-----------|
| wall_delta | 0.5881 | 0.5530 | 0.4667 | 43.9% | momentum **USE** |
| mm_delta | 0.5536 | 0.5146 | 0.4311 | 7.4% | momentum **USE** |
| z20 | -0.5423 | -0.5091 | -0.4406 | 19.9% | contrarian **USE** |
| micro_delta | 0.4987 | 0.4647 | 0.3991 | 29.6% | momentum **USE** |
| ret1 | -0.4937 | -0.4559 | -0.3850 | 12.3% | contrarian **USE** |
| imbalance | -0.0765 | -0.0790 | -0.0662 | 13.9% | contrarian **USE** |
| spread_chg | -0.0339 | -0.0340 | -0.0342 | 21.8% | contrarian **USE** |

**Best signal: wall_delta** (corr=0.5881, hit=43.9%)

### Spike Behavior
- Spikes detected: 61 (22.1 per 10k ticks)
- Average spike magnitude: 4.29
- **Reversion tradeable: YES**

### Position & Risk (simulated take-only strategy)
- Max position reached: 0
- Time at limit (≥90%): 0.0%
- Simulated MtM PnL: 0

### Periodicities (significant ACF peaks)
- Lag 5: ACF=0.0155
- Lag 18: ACF=0.0133
- Lag 40: ACF=-0.0141
- Lag 73: ACF=0.0197
- Lag 95: ACF=-0.0233
- Lag 104: ACF=0.0179
- Lag 112: ACF=0.0150
- Lag 130: ACF=0.0167
- These could indicate bot trading cycles. Consider using as timing signals.

---
## INTARIAN_PEPPER_ROOT
**Position limit:** 80
**Classification:** DRIFTING (within-day CV=0.025161)
**Drift:** 1000/day (upward)
**Recommended strategy:** Dynamic / Rolling Fair Value Market Making

### Price Behavior
- Day -2: open=9998, close=11002, low=9998, high=11002, mean=10501, std=287.9
- Day -1: open=10998, close=11998, low=10998, high=12001, mean=11501, std=287.6
- Day 0: open=11998, close=13000, low=11998, high=13000, mean=12501, std=288.2
- Overall mean: 11502.3, overall std: 866.2
- Return autocorrelation: lag-1=-0.0072 → **NEUTRAL**
- Fair value shifts ~1000 per day. Must track with rolling window.

### Spread & Edge Parameters
- Spread: mean=13.0, median (p50)=13.0, p25=12.0, p75=14.0
- **take_edge = 3.00** (= p25/4, sweep when ask < FV - take_edge)
- **passive_edge = 4.33** (= p50/3, quote at FV ± passive_edge)

### Fair Value Estimator
- **Best: wall_mid** (lowest std = most stable)
  - simple_mid: std=866.1518
  - microprice: std=866.1548
  - wall_mid: std=866.1437 ← USE
  - mm_mid: std=866.1492
- Wall mid = midpoint of largest-volume bid and ask levels

### Signal Predictiveness (correlation with next-tick return)
| Signal | Corr(h=1) | Corr(h=5) | Corr(h=20) | Hit Rate | Direction |
|--------|-----------|-----------|------------|----------|-----------|
| z20 | -0.0704 | -0.0391 | -0.0149 | 24.0% | contrarian **USE** |
| mm_delta | 0.0687 | 0.0281 | 0.0113 | 15.1% | momentum **USE** |
| wall_delta | 0.0671 | 0.0299 | 0.0040 | 32.1% | momentum **USE** |
| micro_delta | 0.0395 | 0.0191 | -0.0059 | 26.9% | momentum **USE** |
| imbalance | -0.0151 | -0.0032 | 0.0072 | 11.6% | contrarian skip |
| ret1 | -0.0072 | -0.0039 | -0.0017 | 10.2% | contrarian skip |
| spread_chg | -0.0048 | -0.0045 | -0.0024 | 19.2% | contrarian skip |

**Best signal: z20** (corr=-0.0704, hit=24.0%)

### Spike Behavior
- Spikes detected: 131 (47.3 per 10k ticks)
- Average spike magnitude: 25.82
- **Reversion tradeable: YES**

### Position & Risk (simulated take-only strategy)
- Max position reached: 80
- Time at limit (≥90%): 22.4%
- Simulated MtM PnL: 132895

---
## Cross-Product Relationships
- ASH_COATED_OSMIUM ↔ INTARIAN_PEPPER_ROOT: correlation = 0.0039 (uncorrelated — trade independently)

---
## Implementation Notes
- Execution model: Trader class, `run()` called each tick with TradingState
- Stateless (AWS Lambda): persist state via `traderData` (str, 50k char limit)
- Order types: limit orders only, via `{product: [Order(symbol, price, quantity)]}` dict
- Positive qty = buy, negative qty = sell
- Position limits enforced server-side: violating = all orders cancelled
- Three-phase pattern from top teams: **TAKE** (sweep mispriced) → **CLEAR** (reduce risk) → **MAKE** (passive quotes)