# Prosperity strategy review rules

Review every trader change for:

1. Submission interface and return-shape correctness
2. Position-limit and sign-convention correctness
3. Clear fair-value logic per product
4. Clear separation of taking logic and passive quoting logic
5. Inventory-aware skew or flattening behavior
6. No accidental over-coupling across products
7. Minimal and attributable strategy changes
8. Backtest evidence against a named baseline
9. No dependence on one unusually favorable day
10. Metrics or artifacts that would falsify the claimed improvement
