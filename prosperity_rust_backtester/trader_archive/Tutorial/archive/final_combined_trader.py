from datamodel import Order, OrderDepth, TradingState
from typing import Dict, List


LIMITS = {
    "EMERALDS": 80,
    "TOMATOES": 80,
}


def build_orders(sym, pos, lim, tb, ts, pb, ps):
    bb, sb = lim - pos, lim + pos
    orders = []
    for p, q in tb:
        f = min(q, bb)
        if f > 0:
            orders.append(Order(sym, p, f))
            bb -= f
    for p, q in ts:
        f = min(q, sb)
        if f > 0:
            orders.append(Order(sym, p, -f))
            sb -= f
    for p, q in pb:
        f = min(q, bb)
        if f > 0:
            orders.append(Order(sym, p, f))
            bb -= f
    for p, q in ps:
        f = min(q, sb)
        if f > 0:
            orders.append(Order(sym, p, -f))
            sb -= f
    return orders


def trade_emeralds(od, pos):
    fair, lim = 10000, 80
    tb, ts = [], []
    for ap in sorted(od.sell_orders.keys()):
        if ap > fair - 2:
            break
        tb.append((ap, -od.sell_orders[ap]))
    for bp in sorted(od.buy_orders.keys(), reverse=True):
        if bp < fair + 2:
            break
        ts.append((bp, od.buy_orders[bp]))
    skew = round(pos * 0.00)
    pb = [(fair - 7 - skew, 25), (fair - 6 - skew, 20), (fair - 5 - skew, 20)]
    ps = [(fair + 7 - skew, 25), (fair + 6 - skew, 20), (fair + 5 - skew, 20)]
    return build_orders("EMERALDS", pos, lim, tb, ts, pb, ps)


class Trader:
    LIMITS = {
        "EMERALDS": 80,
        "TOMATOES": 80,
    }
    QUOTE_SIZE = 5

    def run(self, state: TradingState):
        orders_by_product: Dict[str, List[Order]] = {}

        if "EMERALDS" in state.order_depths:
            orders_by_product["EMERALDS"] = trade_emeralds(
                state.order_depths["EMERALDS"],
                int(state.position.get("EMERALDS", 0)),
            )

        if "TOMATOES" in state.order_depths:
            position = int(state.position.get("TOMATOES", 0))
            orders_by_product["TOMATOES"] = self.quote_both_sides(
                "TOMATOES",
                state.order_depths["TOMATOES"],
                position,
            )

        return orders_by_product, 0, ""

    def quote_both_sides(
        self,
        product: str,
        order_depth: OrderDepth,
        position: int,
    ) -> List[Order]:
        if not order_depth.buy_orders or not order_depth.sell_orders:
            return []

        best_bid = max(order_depth.buy_orders)
        best_ask = min(order_depth.sell_orders)
        if best_bid >= best_ask:
            return []

        if best_ask - best_bid > 1:
            bid_price = best_bid + 1
            ask_price = best_ask - 1
        else:
            bid_price = best_bid
            ask_price = best_ask

        limit = self.LIMITS[product]
        buy_size = min(self.QUOTE_SIZE, max(0, limit - position))
        sell_size = min(self.QUOTE_SIZE, max(0, limit + position))

        orders: List[Order] = []
        if buy_size > 0:
            orders.append(Order(product, bid_price, buy_size))
        if sell_size > 0:
            orders.append(Order(product, ask_price, -sell_size))
        return orders
