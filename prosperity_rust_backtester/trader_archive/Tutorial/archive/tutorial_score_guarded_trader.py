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
TOMATO_BUY_TAKE_EDGE = 1.75
TOMATO_SELL_TAKE_EDGE = 2.0
TOMATO_PASSIVE_EDGE = 1.45
TOMATO_REDUCE_EDGE = 0.75
TOMATO_HEAVY_EDGE = 2.1
TOMATO_PASSIVE_SIZE = 6
TOMATO_INV_SKEW = 0.01
TOMATO_WARNING = 25
TOMATO_SOFT_CAP = 45
TOMATO_CAP_EXTRA_EDGE = 1.5


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
    if total <= 0:
        return (bid + ask) / 2.0
    return (bid * ask_volume + ask * bid_volume) / total


def add_buy(
    orders: List[Order], symbol: str, price: int, quantity: int, buy_budget: int
) -> int:
    size = min(quantity, buy_budget)
    if size > 0:
        orders.append(Order(symbol, int(price), size))
        buy_budget -= size
    return buy_budget


def add_sell(
    orders: List[Order], symbol: str, price: int, quantity: int, sell_budget: int
) -> int:
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


def tomato_fair(depth: OrderDepth, recent_mids: List[float]) -> Tuple[float, float, float, float]:
    current_mid = mid_price(depth)
    if current_mid is None:
        fallback = recent_mids[-1] if recent_mids else 5000.0
        return fallback, fallback, 0.0, 0.0

    prior_mid = recent_mids[-1] if recent_mids else current_mid
    ret1 = current_mid - prior_mid
    window = recent_mids[-TOMATO_SIGNAL_WINDOW:] + [current_mid]
    rolling_mean = sum(window) / len(window)
    z20 = current_mid - rolling_mean
    mp = microprice(depth)
    micro_delta = 0.0 if mp is None else mp - current_mid
    fair = (
        current_mid
        + TOMATO_MICRO_WEIGHT * micro_delta
        + TOMATO_RET1_WEIGHT * ret1
        + TOMATO_Z20_WEIGHT * z20
    )
    return fair, current_mid, ret1, z20


def aggressive_buy_signal(fair: float, mid: float, ret1: float, z20: float) -> bool:
    return fair - mid >= 0.6 or ret1 <= -1.0 or z20 <= -2.0


def aggressive_sell_signal(fair: float, mid: float, ret1: float, z20: float) -> bool:
    return (fair - mid <= -0.8 and ret1 >= 1.0) or z20 >= 3.5


def passive_edge_needed(position: int, side: str) -> float:
    reducing = (side == "buy" and position < 0) or (side == "sell" and position > 0)
    same_side_heavy = (side == "buy" and position >= TOMATO_WARNING) or (
        side == "sell" and position <= -TOMATO_WARNING
    )
    if reducing:
        return TOMATO_REDUCE_EDGE
    if same_side_heavy:
        return TOMATO_HEAVY_EDGE
    return TOMATO_PASSIVE_EDGE


def trade_tomatoes(depth: OrderDepth, position: int, recent_mids: List[float]) -> List[Order]:
    orders: List[Order] = []
    buy_budget = LIMITS["TOMATOES"] - position
    sell_budget = LIMITS["TOMATOES"] + position
    fair, current_mid, ret1, z20 = tomato_fair(depth, recent_mids)

    temp_position = position
    can_buy_aggr = aggressive_buy_signal(fair, current_mid, ret1, z20)
    can_sell_aggr = aggressive_sell_signal(fair, current_mid, ret1, z20)

    for ask in sorted(depth.sell_orders):
        edge = fair - ask
        edge_needed = TOMATO_BUY_TAKE_EDGE + (
            TOMATO_CAP_EXTRA_EDGE if temp_position >= TOMATO_SOFT_CAP else 0.0
        )
        if edge < edge_needed or not can_buy_aggr:
            break
        before = buy_budget
        buy_budget = add_buy(orders, "TOMATOES", ask, -depth.sell_orders[ask], buy_budget)
        temp_position += before - buy_budget

    for bid in sorted(depth.buy_orders, reverse=True):
        edge = bid - fair
        edge_needed = TOMATO_SELL_TAKE_EDGE + (
            TOMATO_CAP_EXTRA_EDGE if temp_position <= -TOMATO_SOFT_CAP else 0.0
        )
        if edge < edge_needed or not can_sell_aggr:
            break
        before = sell_budget
        sell_budget = add_sell(orders, "TOMATOES", bid, depth.buy_orders[bid], sell_budget)
        temp_position -= before - sell_budget

    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None or bid >= ask:
        return orders

    skew = round(temp_position * TOMATO_INV_SKEW)
    passive_bid = bid + 1 - skew
    passive_ask = ask - 1 - skew

    if (
        temp_position < TOMATO_SOFT_CAP
        and passive_bid < ask
        and fair - passive_bid >= passive_edge_needed(temp_position, "buy")
    ):
        before = buy_budget
        buy_budget = add_buy(
            orders, "TOMATOES", passive_bid, TOMATO_PASSIVE_SIZE, buy_budget
        )
        temp_position += before - buy_budget

    if (
        temp_position > -TOMATO_SOFT_CAP
        and passive_ask > bid
        and passive_ask - fair >= passive_edge_needed(temp_position, "sell")
    ):
        before = sell_budget
        sell_budget = add_sell(
            orders, "TOMATOES", passive_ask, TOMATO_PASSIVE_SIZE, sell_budget
        )
        temp_position -= before - sell_budget

    if temp_position >= TOMATO_WARNING:
        liquidation_price = max(bid + 1, ask - 2 - skew)
        if liquidation_price > bid:
            extra = min(10, temp_position - TOMATO_WARNING + 1)
            sell_budget = add_sell(
                orders, "TOMATOES", liquidation_price, extra, sell_budget
            )
    elif temp_position <= -TOMATO_WARNING:
        liquidation_price = min(ask - 1, bid + 2 - skew)
        if liquidation_price < ask:
            extra = min(10, -temp_position - TOMATO_WARNING + 1)
            buy_budget = add_buy(
                orders, "TOMATOES", liquidation_price, extra, buy_budget
            )

    return orders


class Trader:
    def bid(self) -> int:
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
            mids = [float(value) for value in tomato_mids[-TOMATO_HISTORY:]]
            result["TOMATOES"] = trade_tomatoes(
                depth, int(state.position.get("TOMATOES", 0)), mids
            )
            current_mid = mid_price(depth)
            if current_mid is not None:
                tomato_mids = (mids + [round(current_mid, 3)])[-TOMATO_HISTORY:]

        trader_data = json.dumps({"tm": tomato_mids}) if tomato_mids else ""
        return result, 0, trader_data
