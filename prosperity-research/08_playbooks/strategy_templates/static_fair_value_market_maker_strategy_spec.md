# static_fair_value_market_maker_strategy_spec

Use when the product has a stable anchor and most value comes from controlled
passive quoting around a fixed or slowly moving fair value.

Required sections for a generated candidate:
- assumptions header
- parameter block
- per-product quote builder
- inventory skew / clear logic
- traderData state serialization

Primary validation target:
- better passive fill quality without a worse inventory profile
