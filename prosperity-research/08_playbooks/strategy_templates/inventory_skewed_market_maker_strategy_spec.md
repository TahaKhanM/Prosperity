# inventory_skewed_market_maker_strategy_spec

Use when the baseline fair value is acceptable but inventory control and quote
skew are the dominant remaining problems.

Required sections for a generated candidate:
- fair-value block
- inventory skew parameters
- danger-zone flattening
- passive quote placement
- traderData inventory state

Primary validation target:
- lower drawdown and lower near-limit time
