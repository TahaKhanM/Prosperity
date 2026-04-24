"""Round 3 no-trade baseline.

Submission-compatible interface reference. Returns zero orders every tick.
Exists solely to produce a stable PnL baseline against which serious Round 3
candidates are compared.
"""

from typing import Dict, List

from datamodel import Order, TradingState


TRADER_DATA_SCHEMA = 1


class Trader:
    def run(self, state: TradingState):
        orders: Dict[str, List[Order]] = {}
        trader_data = "{\"schema\":%d}" % TRADER_DATA_SCHEMA
        return orders, 0, trader_data

    def bid(self) -> int:
        return 20
