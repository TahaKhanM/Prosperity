import json
from typing import Dict, List

from datamodel import Order, OrderDepth, TradingState


PEPPER = "INTARIAN_PEPPER_ROOT"


def best_bid(depth: OrderDepth):
    return max(depth.buy_orders) if depth.buy_orders else None


def best_ask(depth: OrderDepth):
    return min(depth.sell_orders) if depth.sell_orders else None


class Trader:
    """Official probe trader for hosted Pepper exchange behavior.

    This trader alternates small passive and aggressive actions across the
    session while keeping position bounded. The goal is to measure:
    - whether Pepper inside quotes are ever hit reliably on official
    - whether small aggressive buys/sells move the next displayed book
    - whether early-session Pepper buys still capture carry
    """

    def run(self, state: TradingState):
        result: Dict[str, List[Order]] = {}
        depth = state.order_depths.get(PEPPER)
        if depth is None:
            return result, 0, state.traderData or "pepper_probe_v1"

        bid = best_bid(depth)
        ask = best_ask(depth)
        if bid is None or ask is None:
            return result, 0, state.traderData or "pepper_probe_v1"

        position = state.position.get(PEPPER, 0)
        spread = ask - bid
        progress = state.timestamp / 99900.0
        phase = (state.timestamp // 100) % 8
        orders: List[Order] = []

        # Persist the opening mid so later analysis can compare actions by phase.
        data = {"open_mid": None}
        if state.traderData:
            try:
                data = json.loads(state.traderData)
            except json.JSONDecodeError:
                data = {"open_mid": None}
        if data.get("open_mid") is None:
            data["open_mid"] = (bid + ask) / 2.0

        if state.timestamp >= 99000:
            if position > 0:
                orders.append(Order(PEPPER, bid, -min(position, 2)))
            elif position < 0:
                orders.append(Order(PEPPER, ask, min(-position, 2)))
            if orders:
                result[PEPPER] = orders
            return result, 0, json.dumps(data, separators=(",", ":"))

        if position >= 3:
            orders.append(Order(PEPPER, bid, -1))
        elif position <= -3:
            orders.append(Order(PEPPER, ask, 1))
        elif progress < 0.05:
            if phase in (0, 4):
                orders.append(Order(PEPPER, ask, 1))
        elif 0.10 <= progress <= 0.90:
            if phase == 0 and bid + 1 < ask and spread >= 2:
                orders.append(Order(PEPPER, bid + 1, 1))
            elif phase == 1 and bid < ask - 1 and spread >= 2:
                orders.append(Order(PEPPER, ask - 1, -1))
            elif phase == 2:
                orders.append(Order(PEPPER, ask, 1))
            elif phase == 3:
                orders.append(Order(PEPPER, bid, -1))
            elif phase == 4:
                orders.append(Order(PEPPER, bid, 1))
            elif phase == 5:
                orders.append(Order(PEPPER, ask, -1))

        if orders:
            result[PEPPER] = orders
        return result, 0, json.dumps(data, separators=(",", ":"))
