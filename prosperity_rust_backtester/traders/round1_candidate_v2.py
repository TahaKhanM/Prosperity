import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


ASH = "ASH_COATED_OSMIUM"
PEPPER = "INTARIAN_PEPPER_ROOT"

LIMITS = {
    ASH: 80,
    PEPPER: 80,
}

BASE_CONFIG = {
    ASH: {
        "take_edge": 4.0,
        "clear_edge": 1.0,
        "passive_edge": 5.0,
        "quote_size": 14,
        "soft_cap": 60,
        "inv_skew": 0.03,
    },
    PEPPER: {
        "take_edge": 3.0,
        "clear_edge": 0.5,
        "passive_edge": 4.0,
        "quote_size": 12,
        "soft_cap": 55,
        "inv_skew": 0.05,
    },
}

ASH_FAIR = 10000.0
PEPPER_LOOKAHEAD = 1000.0
PEPPER_MAX_TREND_BIAS = 4.5
PEPPER_FAIR_DECAY = 0.5


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def best_bid(depth: OrderDepth) -> Optional[int]:
    return max(depth.buy_orders) if depth.buy_orders else None


def best_ask(depth: OrderDepth) -> Optional[int]:
    return min(depth.sell_orders) if depth.sell_orders else None


def simple_mid(depth: OrderDepth) -> Optional[float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return None
    return (bid + ask) / 2.0


def wall_mid(depth: OrderDepth) -> Optional[float]:
    if not depth.buy_orders or not depth.sell_orders:
        return simple_mid(depth)
    wall_bid = max(depth.buy_orders.items(), key=lambda item: (item[1], item[0]))[0]
    wall_ask = min(
        depth.sell_orders.items(),
        key=lambda item: (item[1], -item[0]),
    )[0]
    return (wall_bid + wall_ask) / 2.0


def add_buy(
    orders: List[Order],
    product: str,
    price: int,
    quantity: int,
    budget: int,
) -> int:
    size = min(quantity, budget)
    if size > 0:
        orders.append(Order(product, int(price), int(size)))
        budget -= size
    return budget


def add_sell(
    orders: List[Order],
    product: str,
    price: int,
    quantity: int,
    budget: int,
) -> int:
    size = min(quantity, budget)
    if size > 0:
        orders.append(Order(product, int(price), -int(size)))
        budget -= size
    return budget


def size_for_position(base_size: int, temp_position: int, soft_cap: int) -> int:
    abs_pos = abs(temp_position)
    if abs_pos >= soft_cap:
        return max(2, base_size // 3)
    if abs_pos >= soft_cap - 10:
        return max(3, base_size // 2)
    return base_size


def take_orders(
    orders: List[Order],
    product: str,
    depth: OrderDepth,
    fair: float,
    position: int,
    take_edge: float,
) -> Tuple[int, int, int]:
    limit = LIMITS[product]
    buy_budget = limit - position
    sell_budget = limit + position
    temp_position = position

    for ask in sorted(depth.sell_orders):
        if ask > fair - take_edge:
            break
        before = buy_budget
        buy_budget = add_buy(
            orders,
            product,
            ask,
            -depth.sell_orders[ask],
            buy_budget,
        )
        temp_position += before - buy_budget

    for bid in sorted(depth.buy_orders, reverse=True):
        if bid < fair + take_edge:
            break
        before = sell_budget
        sell_budget = add_sell(
            orders,
            product,
            bid,
            depth.buy_orders[bid],
            sell_budget,
        )
        temp_position -= before - sell_budget

    return buy_budget, sell_budget, temp_position


def clear_inventory(
    orders: List[Order],
    product: str,
    depth: OrderDepth,
    fair: float,
    temp_position: int,
    buy_budget: int,
    sell_budget: int,
    soft_cap: int,
    clear_edge: float,
) -> Tuple[int, int, int]:
    if temp_position > soft_cap:
        for bid in sorted(depth.buy_orders, reverse=True):
            if bid < fair - clear_edge:
                break
            before = sell_budget
            sell_budget = add_sell(
                orders,
                product,
                bid,
                depth.buy_orders[bid],
                sell_budget,
            )
            temp_position -= before - sell_budget
            if temp_position <= soft_cap:
                break

    if temp_position < -soft_cap:
        for ask in sorted(depth.sell_orders):
            if ask > fair + clear_edge:
                break
            before = buy_budget
            buy_budget = add_buy(
                orders,
                product,
                ask,
                -depth.sell_orders[ask],
                buy_budget,
            )
            temp_position += before - buy_budget
            if temp_position >= -soft_cap:
                break

    return buy_budget, sell_budget, temp_position


def place_passive_quotes(
    orders: List[Order],
    product: str,
    depth: OrderDepth,
    fair: float,
    temp_position: int,
    buy_budget: int,
    sell_budget: int,
    passive_edge: float,
    quote_size: int,
    soft_cap: int,
    inv_skew: float,
) -> None:
    bid = best_bid(depth)
    ask = best_ask(depth)

    skewed_fair = fair - (temp_position * inv_skew)
    base_size = size_for_position(quote_size, temp_position, soft_cap)
    buy_size = max(2, base_size - max(0, temp_position // 25))
    sell_size = max(2, base_size + min(0, temp_position // 25))

    bid_price = math.floor(skewed_fair - passive_edge)
    ask_price = math.ceil(skewed_fair + passive_edge)

    if bid is not None:
        bid_price = min(bid_price, bid + 1)
    if ask is not None:
        ask_price = max(ask_price, ask - 1)

    if ask is not None and bid_price >= ask:
        bid_price = ask - 1
    if bid is not None and ask_price <= bid:
        ask_price = bid + 1

    if buy_budget > 0 and (ask is None or bid_price < ask) and fair - bid_price >= 1.0:
        add_buy(orders, product, bid_price, buy_size, buy_budget)

    if sell_budget > 0 and (bid is None or ask_price > bid) and ask_price - fair >= 1.0:
        add_sell(orders, product, ask_price, sell_size, sell_budget)


def trade_product(
    product: str,
    depth: OrderDepth,
    position: int,
    fair: float,
    config: Dict[str, float],
) -> List[Order]:
    orders: List[Order] = []
    buy_budget, sell_budget, temp_position = take_orders(
        orders,
        product,
        depth,
        fair,
        position,
        config["take_edge"],
    )

    buy_budget, sell_budget, temp_position = clear_inventory(
        orders,
        product,
        depth,
        fair,
        temp_position,
        buy_budget,
        sell_budget,
        config["soft_cap"],
        config["clear_edge"],
    )

    place_passive_quotes(
        orders,
        product,
        depth,
        fair,
        temp_position,
        buy_budget,
        sell_budget,
        config["passive_edge"],
        config["quote_size"],
        config["soft_cap"],
        config["inv_skew"],
    )
    return orders


def pepper_fair_with_trend_floor(
    depth: OrderDepth,
    session_state: Dict[str, float],
    timestamp: int,
) -> Tuple[float, Dict[str, float]]:
    current_wall = wall_mid(depth)
    current_mid = simple_mid(depth)

    if current_wall is None:
        fallback = current_mid
        if fallback is None:
            fallback = float(session_state.get("last_fair", 11000.0))
        session_state["last_fair"] = fallback
        session_state["last_ts"] = timestamp
        return fallback, session_state

    prior_ts = int(session_state.get("last_ts", -1))
    if not session_state or timestamp < prior_ts:
        session_state = {
            "open": current_wall,
            "start": timestamp,
        }

    elapsed = max(100, timestamp - int(session_state["start"]))
    slope = (current_wall - float(session_state["open"])) / float(elapsed)
    projected_fair = current_wall + clamp(
        slope * PEPPER_LOOKAHEAD,
        -PEPPER_MAX_TREND_BIAS,
        PEPPER_MAX_TREND_BIAS,
    )

    last_fair = float(session_state.get("last_fair", projected_fair))
    fair = max(projected_fair, last_fair - PEPPER_FAIR_DECAY)

    session_state["last_fair"] = fair
    session_state["last_ts"] = timestamp
    return fair, session_state


class Trader:
    def run(self, state: TradingState):
        session_state: Dict[str, float] = {}
        if state.traderData:
            try:
                raw = json.loads(state.traderData)
                if isinstance(raw, dict) and isinstance(raw.get("pepper"), dict):
                    session_state = raw["pepper"]
            except Exception:
                session_state = {}

        result: Dict[str, List[Order]] = {}

        if ASH in state.order_depths:
            result[ASH] = trade_product(
                ASH,
                state.order_depths[ASH],
                int(state.position.get(ASH, 0)),
                ASH_FAIR,
                BASE_CONFIG[ASH],
            )

        if PEPPER in state.order_depths:
            pepper_fair, session_state = pepper_fair_with_trend_floor(
                state.order_depths[PEPPER],
                session_state,
                int(state.timestamp),
            )
            result[PEPPER] = trade_product(
                PEPPER,
                state.order_depths[PEPPER],
                int(state.position.get(PEPPER, 0)),
                pepper_fair,
                BASE_CONFIG[PEPPER],
            )

        trader_data = json.dumps({"pepper": session_state}) if session_state else ""
        return result, 0, trader_data
