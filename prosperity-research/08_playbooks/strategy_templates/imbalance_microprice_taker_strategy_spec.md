# imbalance_microprice_taker_strategy_spec

Use when short-horizon edge comes from imbalance, microprice, or book-leaning
signals and the candidate should mostly act as a taker.

Required sections for a generated candidate:
- signal block
- aggressiveness thresholds
- position caps
- separate per-product logic
- traderData signal state

Primary validation target:
- better aggressive fill edge with controlled trade count
