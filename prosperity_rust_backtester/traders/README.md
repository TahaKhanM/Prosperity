# Trader Layout

The root of this directory is intentionally minimal so AI tools and humans see the default path first.

- `latest_trader.py`: default trader used by the local backtester
- `Round1/`: active structured Round 1 traders
- `Tutorial/`: active tutorial-trader placeholders and documentation

Historical trader code lives in `../trader_archive/`.
Avoid adding new strategy files directly to this root unless the file is becoming the new default trader.
