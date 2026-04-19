# moving_fair_value_mean_reversion_strategy_spec

Use when fair value should adapt over time and inventory should mean-revert
toward a dynamic center.

Required sections for a generated candidate:
- dynamic fair-value function
- residual / z-score logic
- take threshold block
- inventory recycle block
- traderData state for rolling signals

Primary validation target:
- improved future-edge metrics on aggressive fills
