"""Round 4 no-trade baseline.

Returns no orders for any product. Useful as the absolute zero on backtests
and as a smoke-test target to confirm that the Round 4 dataset wiring
(`make round4 TRADER=traders/Round4/round4_no_trade_baseline.py`) loads,
ingests prices_round_4_day_*.csv and trades_round_4_day_*.csv (with `Mark
<NN>` IDs), and reports zero PnL across all products.

Why this file exists
--------------------
- Sanity: confirms `position_limit` wiring, dataset file naming, and that
  the backtester does not crash on the new counterparty strings.
- Baseline: any Round 4 trader's PnL delta should be measured against this
  zero baseline as well as against a meaningful R3 carry-over baseline
  such as `traders/Round3/candidates/v15.py`.

Submission contract: run(state) -> (orders, conversions, traderData).
"""
from __future__ import annotations

from typing import Dict, List


class Trader:
    def run(self, state):  # noqa: D401, ANN001
        orders: Dict[str, List[object]] = {}
        conversions = 0
        trader_data = state.traderData if state.traderData else ""
        return orders, conversions, trader_data
