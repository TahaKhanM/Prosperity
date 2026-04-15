from typing import Dict, List

from datamodel import Order, OrderDepth, TradingState


ASH = "ASH_COATED_OSMIUM"
LIMIT = 80


def best_bid(depth: OrderDepth):
    return max(depth.buy_orders) if depth.buy_orders else None


def best_ask(depth: OrderDepth):
    return min(depth.sell_orders) if depth.sell_orders else None


class Trader:
    """Official probe trader for hosted Ash microstructure.

    The schedule is intentionally simple and deterministic so the returned
    official log can be replayed precisely:
    - alternate inside-spread quotes at 1 and 2 ticks
    - alternate aggressive takes and passive joins
    - keep inventory tiny so the probe is about exchange response, not PnL
    """

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}
        depth = state.order_depths.get(ASH)
        if depth is None:
            return result, 0, "ash_probe_v1"

        position = state.position.get(ASH, 0)
        bid = best_bid(depth)
        ask = best_ask(depth)
        orders: List[Order] = []

        if bid is None or ask is None:
            return result, 0, "ash_probe_v1"

        # Keep probe inventory small and flatten near the close.
        if state.timestamp >= 99000:
            if position > 0:
                orders.append(Order(ASH, bid, -min(position, 2)))
            elif position < 0:
                orders.append(Order(ASH, ask, min(-position, 2)))
            if orders:
                result[ASH] = orders
            return result, 0, "ash_probe_v1"

        if position >= 4:
            orders.append(Order(ASH, bid, -1))
            result[ASH] = orders
            return result, 0, "ash_probe_v1"
        if position <= -4:
            orders.append(Order(ASH, ask, 1))
            result[ASH] = orders
            return result, 0, "ash_probe_v1"

        spread = ask - bid
        phase = (state.timestamp // 100) % 10

        if phase == 0 and position < 4 and bid + 1 < ask and spread >= 12:
            orders.append(Order(ASH, bid + 1, 1))
        elif phase == 1 and position > -4 and bid < ask - 1 and spread >= 12:
            orders.append(Order(ASH, ask - 1, -1))
        elif phase == 2 and position < 4 and bid + 2 < ask and spread >= 18:
            orders.append(Order(ASH, bid + 2, 1))
        elif phase == 3 and position > -4 and bid < ask - 2 and spread >= 18:
            orders.append(Order(ASH, ask - 2, -1))
        elif phase == 4 and position < 4:
            orders.append(Order(ASH, ask, 1))
        elif phase == 5 and position > -4:
            orders.append(Order(ASH, bid, -1))
        elif phase == 6 and position < 4:
            orders.append(Order(ASH, bid, 1))
        elif phase == 7 and position > -4:
            orders.append(Order(ASH, ask, -1))

        if orders:
            result[ASH] = orders
        return result, 0, "ash_probe_v1"
