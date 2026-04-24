# Visual index — Round 2

These plots were curated from the full notebook. Each answers a specific question. `<PRODUCT>` is replaced per product.

| file | what it tells you |
|---|---|
| `plots/12_dashboard_<PRODUCT>.png` | 9-panel summary — start here. Classification, ACF, Z, spread, signals, spikes, fair, position, recommendation. |
| `plots/2A_fair_value_<PRODUCT>.png` | Overlay of simple/micro/wall/mm mids and deviations. Use to justify the `best_fair` choice. |
| `plots/3B_spread_distribution.png` | Spread histogram with p25/p50/p75 and take_edge/passive_edge suggestions. |
| `plots/5B_signal_decay_<PRODUCT>.png` | |corr| vs horizon for each candidate signal. Shows how fast edge dies. |
| `plots/14A_conditional_returns_<PRODUCT>.png` | Bucketed forward-return means (imbalance, OFI, fair_dev, z20, spread). Monotonic ρ is the key evidence for tradable conditional edge. |
| `plots/16A_markout_<PRODUCT>.png` | Signed markout of hypothetical take fills at h=1/5/20. Positive bars = paper edge survives. |
| `plots/17A_robust_<PRODUCT>.png` | Signal-vs-fwd_ret_1 correlation per day. Watch for sign flips across days. |
| `plots/15B_vol_regime_<PRODUCT>.png` | Mid price coloured by volatility regime. Useful for spotting regime-concentrated alpha. |
| `plots/8B_spike_reversion_<PRODUCT>.png` | Mean post-spike price path. Convergence toward zero after up/down spikes confirms reversion trade. |
| `plots/19A_feature_relevance_<PRODUCT>.png` | Standardised OLS coefficients of small feature set on fwd_ret_1. Rank-only, not a predictive model. |
| `plots/9B_correlation_matrix.png` | Return correlation across products. Use before any pair/basket hypothesis. |
