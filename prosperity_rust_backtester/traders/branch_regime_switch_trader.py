import json
from datamodel import Order, OrderDepth, TradingState
from typing import Dict, List, Optional, Tuple


LIMITS = {"EMERALDS": 80, "TOMATOES": 80}
EMERALD_FAIR = 10000
TOMATO_HISTORY = 25


def best_bid(depth: OrderDepth) -> Optional[int]:
    return max(depth.buy_orders) if depth.buy_orders else None


def best_ask(depth: OrderDepth) -> Optional[int]:
    return min(depth.sell_orders) if depth.sell_orders else None


def mid_price(depth: OrderDepth) -> Optional[float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    return (bid + ask) / 2.0 if bid is not None and ask is not None else None


def book_signal(depth: OrderDepth) -> Tuple[float, float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return 0.0, 0.0
    bid_volume = depth.buy_orders[bid]
    ask_volume = -depth.sell_orders[ask]
    total = bid_volume + ask_volume
    if total <= 0:
        return 0.0, 0.0
    micro = (bid * ask_volume + ask * bid_volume) / total
    mid = (bid + ask) / 2.0
    imbalance = (bid_volume - ask_volume) / total
    return micro - mid, imbalance


def add_buy(orders: List[Order], product: str, price: int, quantity: int, budget: int) -> int:
    size = min(quantity, budget)
    if size > 0:
        orders.append(Order(product, int(price), size))
        budget -= size
    return budget


def add_sell(orders: List[Order], product: str, price: int, quantity: int, budget: int) -> int:
    size = min(quantity, budget)
    if size > 0:
        orders.append(Order(product, int(price), -size))
        budget -= size
    return budget


def trade_emeralds(depth: OrderDepth, position: int) -> List[Order]:
    orders: List[Order] = []
    buy_budget = LIMITS["EMERALDS"] - position
    sell_budget = LIMITS["EMERALDS"] + position
    for ask in sorted(depth.sell_orders):
        if ask > EMERALD_FAIR - 2:
            break
        buy_budget = add_buy(orders, "EMERALDS", ask, -depth.sell_orders[ask], buy_budget)
    for bid in sorted(depth.buy_orders, reverse=True):
        if bid < EMERALD_FAIR + 2:
            break
        sell_budget = add_sell(orders, "EMERALDS", bid, depth.buy_orders[bid], sell_budget)
    for offset, size in ((7, 25), (6, 20), (5, 20)):
        buy_budget = add_buy(orders, "EMERALDS", EMERALD_FAIR - offset, size, buy_budget)
    for offset, size in ((7, 25), (6, 20), (5, 20)):
        sell_budget = add_sell(orders, "EMERALDS", EMERALD_FAIR + offset, size, sell_budget)
    return orders


def tomato_fair(depth: OrderDepth, history: List[float]) -> float:
    mid = mid_price(depth)
    if mid is None:
        return history[-1] if history else 5000.0
    prior = history[-1] if history else mid
    ret1 = mid - prior
    window = history[-20:] + [mid]
    z20 = mid - sum(window) / len(window)
    micro_delta, imbalance = book_signal(depth)
    return mid + 0.45 * micro_delta + 0.3 * imbalance - 0.55 * ret1 - 0.25 * z20


def trade_tomatoes(depth: OrderDepth, position: int, history: List[float]) -> List[Order]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None or bid >= ask:
        return []

    orders: List[Order] = []
    buy_budget = LIMITS["TOMATOES"] - position
    sell_budget = LIMITS["TOMATOES"] + position
    fair = tomato_fair(depth, history)
    spread = ask - bid
    micro_delta, imbalance = book_signal(depth)
    soft_cap = 45
    wide = spread >= 13
    strong_buy = micro_delta > 0.25 and imbalance > 0.15
    strong_sell = micro_delta < -0.25 and imbalance < -0.15
    take_edge = 2.2 if wide else 3.0

    for ask_price in sorted(depth.sell_orders):
        edge = fair - ask_price
        if edge < take_edge:
            break
        if (wide or strong_buy) and (position < soft_cap or edge >= take_edge + 2.0):
            buy_budget = add_buy(orders, "TOMATOES", ask_price, -depth.sell_orders[ask_price], buy_budget)

    for bid_price in sorted(depth.buy_orders, reverse=True):
        edge = bid_price - fair
        if edge < take_edge:
            break
        if (wide or strong_sell) and (position > -soft_cap or edge >= take_edge + 2.0):
            sell_budget = add_sell(orders, "TOMATOES", bid_price, depth.buy_orders[bid_price], sell_budget)

    skew = round(position * (0.015 if wide else 0.03))
    passive_bid = bid + 1 - skew
    passive_ask = ask - 1 - skew
    size = 6 if wide else 3
    buy_edge = 1.2 if position <= -soft_cap else (1.5 if wide else 2.0)
    sell_edge = 1.2 if position >= soft_cap else (1.5 if wide else 2.0)
    if position < soft_cap and passive_bid < ask and fair - passive_bid >= buy_edge:
        buy_budget = add_buy(orders, "TOMATOES", passive_bid, size, buy_budget)
    if position > -soft_cap and passive_ask > bid and passive_ask - fair >= sell_edge:
        sell_budget = add_sell(orders, "TOMATOES", passive_ask, size, sell_budget)
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
        mids = data.get("tm", [])
        if not isinstance(mids, list):
            mids = []
        result: Dict[str, List[Order]] = {}
        if "EMERALDS" in state.order_depths:
            result["EMERALDS"] = trade_emeralds(state.order_depths["EMERALDS"], int(state.position.get("EMERALDS", 0)))
        if "TOMATOES" in state.order_depths:
            depth = state.order_depths["TOMATOES"]
            result["TOMATOES"] = trade_tomatoes(depth, int(state.position.get("TOMATOES", 0)), [float(x) for x in mids[-TOMATO_HISTORY:]])
            mid = mid_price(depth)
            if mid is not None:
                mids = (mids + [round(mid, 3)])[-TOMATO_HISTORY:]
        return result, 0, json.dumps({"tm": mids}) if mids else ""
