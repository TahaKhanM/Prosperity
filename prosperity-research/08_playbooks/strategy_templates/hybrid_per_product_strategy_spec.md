# hybrid_per_product_strategy_spec

Use when products need clearly separate logic families inside one submission,
for example a stable maker on one product and a taker or event response on the
other.

Required sections for a generated candidate:
- per-product configuration map
- separate product handlers
- shared state serializer
- shared risk controls
- assumptions header that explains why the products differ

Primary validation target:
- improved per-product PnL without degrading the other product
