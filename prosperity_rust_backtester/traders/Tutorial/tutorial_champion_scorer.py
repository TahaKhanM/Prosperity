import json
from datamodel import Order, OrderDepth, TradingState
from typing import Dict, List, Optional, Tuple


LIMITS = {"EMERALDS": 80, "TOMATOES": 80}

EMERALD_FAIR = 10000
EMERALD_TAKE_EDGE = 2
EMERALD_OFFSETS = (7, 6, 5)
EMERALD_SIZES = (25, 20, 20)

TOMATO_HISTORY = 25
TOMATO_SIGNAL_WINDOW = 20
TOMATO_MICRO_WEIGHT = 0.4
TOMATO_RET1_WEIGHT = -0.7
TOMATO_Z20_WEIGHT = -0.4
TOMATO_TAKE_EDGE = 2.0
TOMATO_PASSIVE_EDGE = 1.5
TOMATO_PASSIVE_SIZE = 5
TOMATO_INV_SKEW = 0.0


def best_bid(depth: OrderDepth) -> Optional[int]:
    return max(depth.buy_orders) if depth.buy_orders else None


def best_ask(depth: OrderDepth) -> Optional[int]:
    return min(depth.sell_orders) if depth.sell_orders else None


def mid_price(depth: OrderDepth) -> Optional[float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return None
    return (bid + ask) / 2.0


def microprice(depth: OrderDepth) -> Optional[float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return None
    bid_volume = depth.buy_orders[bid]
    ask_volume = -depth.sell_orders[ask]
    total = bid_volume + ask_volume
    return (bid * ask_volume + ask * bid_volume) / total if total > 0 else (bid + ask) / 2.0


def add_buy(orders: List[Order], symbol: str, price: int, quantity: int, buy_budget: int) -> int:
    size = min(quantity, buy_budget)
    if size > 0:
        orders.append(Order(symbol, int(price), size))
        buy_budget -= size
    return buy_budget


def add_sell(orders: List[Order], symbol: str, price: int, quantity: int, sell_budget: int) -> int:
    size = min(quantity, sell_budget)
    if size > 0:
        orders.append(Order(symbol, int(price), -size))
        sell_budget -= size
    return sell_budget


def trade_emeralds(depth: OrderDepth, position: int) -> List[Order]:
    orders: List[Order] = []
    buy_budget = LIMITS["EMERALDS"] - position
    sell_budget = LIMITS["EMERALDS"] + position

    for ask in sorted(depth.sell_orders):
        if ask > EMERALD_FAIR - EMERALD_TAKE_EDGE:
            break
        buy_budget = add_buy(orders, "EMERALDS", ask, -depth.sell_orders[ask], buy_budget)

    for bid in sorted(depth.buy_orders, reverse=True):
        if bid < EMERALD_FAIR + EMERALD_TAKE_EDGE:
            break
        sell_budget = add_sell(orders, "EMERALDS", bid, depth.buy_orders[bid], sell_budget)

    for offset, size in zip(EMERALD_OFFSETS, EMERALD_SIZES):
        buy_budget = add_buy(orders, "EMERALDS", EMERALD_FAIR - offset, size, buy_budget)
    for offset, size in zip(EMERALD_OFFSETS, EMERALD_SIZES):
        sell_budget = add_sell(orders, "EMERALDS", EMERALD_FAIR + offset, size, sell_budget)
    return orders


def tomato_fair(depth: OrderDepth, recent_mids: List[float]) -> float:
    current_mid = mid_price(depth)
    if current_mid is None:
        return recent_mids[-1] if recent_mids else 5000.0

    prior_mid = recent_mids[-1] if recent_mids else current_mid
    ret1 = current_mid - prior_mid
    window = recent_mids[-TOMATO_SIGNAL_WINDOW:] + [current_mid]
    z20 = current_mid - sum(window) / len(window)
    mp = microprice(depth)
    micro_delta = 0.0 if mp is None else mp - current_mid
    return current_mid + TOMATO_MICRO_WEIGHT * micro_delta + TOMATO_RET1_WEIGHT * ret1 + TOMATO_Z20_WEIGHT * z20


def trade_tomatoes(depth: OrderDepth, position: int, recent_mids: List[float]) -> List[Order]:
    orders: List[Order] = []
    buy_budget = LIMITS["TOMATOES"] - position
    sell_budget = LIMITS["TOMATOES"] + position
    fair = tomato_fair(depth, recent_mids)

    for ask in sorted(depth.sell_orders):
        if ask > fair - TOMATO_TAKE_EDGE:
            break
        buy_budget = add_buy(orders, "TOMATOES", ask, -depth.sell_orders[ask], buy_budget)

    for bid in sorted(depth.buy_orders, reverse=True):
        if bid < fair + TOMATO_TAKE_EDGE:
            break
        sell_budget = add_sell(orders, "TOMATOES", bid, depth.buy_orders[bid], sell_budget)

    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None or bid >= ask:
        return orders

    skew = round(position * TOMATO_INV_SKEW)
    passive_bid = bid + 1 - skew
    passive_ask = ask - 1 - skew
    if passive_bid < ask and fair - passive_bid >= TOMATO_PASSIVE_EDGE:
        buy_budget = add_buy(orders, "TOMATOES", passive_bid, TOMATO_PASSIVE_SIZE, buy_budget)
    if passive_ask > bid and passive_ask - fair >= TOMATO_PASSIVE_EDGE:
        sell_budget = add_sell(orders, "TOMATOES", passive_ask, TOMATO_PASSIVE_SIZE, sell_budget)
    return orders


class Trader:
    def bid(self):
        return 0

    def run(self, state: TradingState) -> Tuple[Dict[str, List[Order]], int, str]:
        data = {}
        if state.traderData:
            try:
                data = json.loads(state.traderData)
            except Exception:
                data = {}

        tomato_mids = data.get("tm", [])
        if not isinstance(tomato_mids, list):
            tomato_mids = []

        result: Dict[str, List[Order]] = {}
        if "EMERALDS" in state.order_depths:
            result["EMERALDS"] = trade_emeralds(
                state.order_depths["EMERALDS"],
                int(state.position.get("EMERALDS", 0)),
            )
        if "TOMATOES" in state.order_depths:
            depth = state.order_depths["TOMATOES"]
            result["TOMATOES"] = trade_tomatoes(
                depth,
                int(state.position.get("TOMATOES", 0)),
                [float(value) for value in tomato_mids[-TOMATO_HISTORY:]],
            )
            current_mid = mid_price(depth)
            if current_mid is not None:
                tomato_mids = (tomato_mids + [round(current_mid, 3)])[-TOMATO_HISTORY:]

        trader_data = json.dumps({"tm": tomato_mids}) if tomato_mids else ""
        return result, 0, trader_data
