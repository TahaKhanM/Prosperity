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
TOMATO_FAST_WINDOW = 5

TOMATO_MICRO_WEIGHT = 0.4
TOMATO_RET1_WEIGHT = -0.7
TOMATO_Z20_WEIGHT = -0.4

TOMATO_NEUTRAL_BUY_EDGE = 1.30
TOMATO_NEUTRAL_SELL_EDGE = 1.50
TOMATO_NEUTRAL_TAKE_EDGE = 2.0
TOMATO_NEUTRAL_SIZE = 6

TOMATO_OVERSOLD_BUY_EDGE = 1.10
TOMATO_OVERSOLD_BUY_TAKE_EDGE = 1.75
TOMATO_OVERSOLD_BUY_SIZE = 8

TOMATO_SELL_OFF_BUY_EDGE = 1.65
TOMATO_SELL_OFF_BUY_TAKE_EDGE = 2.5
TOMATO_SELL_OFF_TREND = -2.0

TOMATO_EXTRA_BUY_SIZE = 4
TOMATO_EXTRA_BUY_EDGE = 1.75

TOMATO_HIGH_POS_SELL_EDGE = 1.00
TOMATO_HIGH_POS_THRESHOLD = 60

TOMATO_BUY_LOCK_TRIGGER = 40
TOMATO_BUY_UNLOCK = 25

TOMATO_SOFT_CAP = 80
TOMATO_CAP_EXTRA_EDGE = 1.0
TOMATO_REDUCE_EDGE = 0.75
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


def rolling_mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def tomato_features(depth: OrderDepth, recent_mids: List[float]) -> Tuple[float, float, float, float, float, float]:
    current_mid = mid_price(depth)
    if current_mid is None:
        fallback = recent_mids[-1] if recent_mids else 5000.0
        return fallback, fallback, 0.0, 0.0, 0.0, 0.0

    prior_mid = recent_mids[-1] if recent_mids else current_mid
    ret1 = current_mid - prior_mid

    z_window = recent_mids[-TOMATO_SIGNAL_WINDOW:] + [current_mid]
    z20 = current_mid - rolling_mean(z_window)

    fast_window = recent_mids[-TOMATO_FAST_WINDOW:] + [current_mid]
    slow_window = recent_mids[-TOMATO_SIGNAL_WINDOW:] + [current_mid]
    trend = rolling_mean(fast_window) - rolling_mean(slow_window)

    mp = microprice(depth)
    micro_delta = 0.0 if mp is None else mp - current_mid

    fair = (
        current_mid
        + TOMATO_MICRO_WEIGHT * micro_delta
        + TOMATO_RET1_WEIGHT * ret1
        + TOMATO_Z20_WEIGHT * z20
    )
    return fair, current_mid, ret1, z20, micro_delta, trend


def trade_tomatoes(
    depth: OrderDepth,
    position: int,
    recent_mids: List[float],
    buy_lock: bool,
) -> Tuple[List[Order], bool]:
    orders: List[Order] = []
    buy_budget = LIMITS["TOMATOES"] - position
    sell_budget = LIMITS["TOMATOES"] + position
    fair, current_mid, ret1, z20, micro_delta, trend = tomato_features(depth, recent_mids)

    if position <= TOMATO_BUY_UNLOCK:
        buy_lock = False

    selloff = trend <= TOMATO_SELL_OFF_TREND and ret1 <= -0.5
    oversold_rebound = z20 <= -4.0 and trend >= -1.0 and micro_delta >= -0.25
    strong_rebound = oversold_rebound and (micro_delta >= 0.5 or ret1 >= 0.5)

    if selloff and position >= TOMATO_BUY_LOCK_TRIGGER:
        buy_lock = True

    buy_passive_edge = TOMATO_NEUTRAL_BUY_EDGE
    buy_take_edge = TOMATO_NEUTRAL_TAKE_EDGE
    buy_passive_size = TOMATO_NEUTRAL_SIZE
    extra_buy_level = False

    if oversold_rebound:
        buy_passive_edge = TOMATO_OVERSOLD_BUY_EDGE
        buy_take_edge = TOMATO_OVERSOLD_BUY_TAKE_EDGE
        buy_passive_size = TOMATO_OVERSOLD_BUY_SIZE
        extra_buy_level = strong_rebound

    if selloff:
        buy_passive_edge = TOMATO_SELL_OFF_BUY_EDGE
        buy_take_edge = TOMATO_SELL_OFF_BUY_TAKE_EDGE
        extra_buy_level = False

    sell_passive_edge = TOMATO_HIGH_POS_SELL_EDGE if position >= TOMATO_HIGH_POS_THRESHOLD else TOMATO_NEUTRAL_SELL_EDGE
    sell_take_edge = TOMATO_NEUTRAL_TAKE_EDGE

    temp_position = position
    for ask in sorted(depth.sell_orders):
        edge = fair - ask
        if edge < buy_take_edge:
            break
        if temp_position >= TOMATO_SOFT_CAP and edge < buy_take_edge + TOMATO_CAP_EXTRA_EDGE:
            continue
        before = buy_budget
        buy_budget = add_buy(orders, "TOMATOES", ask, -depth.sell_orders[ask], buy_budget)
        temp_position += before - buy_budget

    for bid in sorted(depth.buy_orders, reverse=True):
        edge = bid - fair
        if edge < sell_take_edge:
            break
        if temp_position <= -TOMATO_SOFT_CAP and edge < sell_take_edge + TOMATO_CAP_EXTRA_EDGE:
            continue
        before = sell_budget
        sell_budget = add_sell(orders, "TOMATOES", bid, depth.buy_orders[bid], sell_budget)
        temp_position -= before - sell_budget

    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None or bid >= ask:
        return orders, buy_lock

    skew = round(temp_position * TOMATO_INV_SKEW)
    passive_bid = bid + 1 - skew
    passive_ask = ask - 1 - skew

    if (
        not buy_lock
        and temp_position < TOMATO_SOFT_CAP
        and passive_bid < ask
        and fair - passive_bid >= buy_passive_edge
    ):
        before = buy_budget
        buy_budget = add_buy(
            orders, "TOMATOES", passive_bid, buy_passive_size, buy_budget
        )
        temp_position += before - buy_budget

    if (
        temp_position > -TOMATO_SOFT_CAP
        and passive_ask > bid
        and passive_ask - fair >= sell_passive_edge
    ):
        before = sell_budget
        sell_budget = add_sell(
            orders, "TOMATOES", passive_ask, TOMATO_NEUTRAL_SIZE, sell_budget
        )
        temp_position -= before - sell_budget

    spread = ask - bid
    extra_buy_price = bid + 2 - skew
    if (
        extra_buy_level
        and not buy_lock
        and spread >= 13
        and temp_position < TOMATO_SOFT_CAP
        and extra_buy_price < ask
        and fair - extra_buy_price >= TOMATO_EXTRA_BUY_EDGE
    ):
        buy_budget = add_buy(
            orders, "TOMATOES", extra_buy_price, TOMATO_EXTRA_BUY_SIZE, buy_budget
        )

    if temp_position <= -TOMATO_HIGH_POS_THRESHOLD:
        reducing_buy_price = min(ask - 1, bid + 2 - skew)
        if reducing_buy_price < ask:
            buy_budget = add_buy(
                orders, "TOMATOES", reducing_buy_price, 4, buy_budget
            )
    elif temp_position >= TOMATO_HIGH_POS_THRESHOLD:
        reducing_sell_price = max(bid + 1, ask - 2 - skew)
        if reducing_sell_price > bid and reducing_sell_price - fair >= TOMATO_REDUCE_EDGE:
            sell_budget = add_sell(
                orders, "TOMATOES", reducing_sell_price, 4, sell_budget
            )

    return orders, buy_lock


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

        buy_lock = bool(data.get("bl", 0))

        result: Dict[str, List[Order]] = {}
        if "EMERALDS" in state.order_depths:
            result["EMERALDS"] = trade_emeralds(
                state.order_depths["EMERALDS"],
                int(state.position.get("EMERALDS", 0)),
            )

        if "TOMATOES" in state.order_depths:
            depth = state.order_depths["TOMATOES"]
            mids = [float(value) for value in tomato_mids[-TOMATO_HISTORY:]]
            tomato_orders, buy_lock = trade_tomatoes(
                depth,
                int(state.position.get("TOMATOES", 0)),
                mids,
                buy_lock,
            )
            result["TOMATOES"] = tomato_orders

            current_mid = mid_price(depth)
            if current_mid is not None:
                tomato_mids = (mids + [round(current_mid, 3)])[-TOMATO_HISTORY:]

        out = {}
        if tomato_mids:
            out["tm"] = tomato_mids
        if buy_lock:
            out["bl"] = 1
        return result, 0, json.dumps(out) if out else ""
