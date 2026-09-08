"""Deterministic test fixture; never a competition submission."""
from datamodel import Order


class Trader:
    def run(self, state):
        orders = {}
        if not state.traderData:
            for symbol, depth in state.order_depths.items():
                if depth.sell_orders:
                    orders[symbol] = [Order(symbol, min(depth.sell_orders), 1)]
        return orders, 0, "initialized"
