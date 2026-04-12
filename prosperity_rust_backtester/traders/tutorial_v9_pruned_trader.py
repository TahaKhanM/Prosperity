import json
from datamodel import Order, OrderDepth, TradingState
from typing import Dict, List, Optional, Tuple


LIMITS = {"EMERALDS": 80, "TOMATOES": 80}

EMERALD_FAIR = 10000
EMERALD_TAKE_EDGE = 2
EMERALD_OFFSETS = (7, 6, 5)
EMERALD_SIZES = (25, 20, 20)

TOM_FAST_ALPHA = 2.0 / 6.0
TOM_SLOW_ALPHA = 2.0 / 21.0
TOM_MICRO_WEIGHT = 0.4
TOM_FAST_WEIGHT = 0.75
TOM_RET1_WEIGHT = -0.4
TOM_TOP_IMBALANCE_WEIGHT = 0.55
TOM_FULL_IMBALANCE_WEIGHT = -0.55
TOM_MEAN_DEV_WEIGHT = -0.22
TOM_POSITION_PENALTY = 0.05
TOM_SOFT_CAP = 35
TOM_WARNING = 20
TOM_CAP_EXTRA_EDGE = 1.75
TOM_BUY_TAKE_EDGE = 1.0
TOM_SELL_TAKE_EDGE = 1.5
TOM_SKEW = 0.015
TOM_LEVELS = ((1, 10), (2, 5))
TOM_BASE_EDGE = 1.0
TOM_REDUCE_EDGE = 0.75
TOM_HEAVY_EDGE = 1.75
TOM_LEVEL2_EXTRA = 0.75


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


def top_book_signal(depth: OrderDepth) -> Tuple[float, float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return 0.0, 0.0
    bid_volume = depth.buy_orders[bid]
    ask_volume = -depth.sell_orders[ask]
    total = bid_volume + ask_volume
    if total <= 0:
        return 0.0, 0.0
    mid = (bid + ask) / 2.0
    micro = (bid * ask_volume + ask * bid_volume) / total
    imbalance = (bid_volume - ask_volume) / total
    return micro - mid, imbalance


def full_depth_imbalance(depth: OrderDepth) -> float:
    total_bid = sum(depth.buy_orders.values()) if depth.buy_orders else 0
    total_ask = sum(-value for value in depth.sell_orders.values()) if depth.sell_orders else 0
    total = total_bid + total_ask
    if total <= 0:
        return 0.0
    return (total_bid - total_ask) / total


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


def tomato_state_fair(
    depth: OrderDepth, position: int, fe: Optional[float], se: Optional[float], pm: Optional[float]
) -> Tuple[float, float, float, float, float, float]:
    current_mid = mid_price(depth)
    if current_mid is None:
        fallback = fe if fe is not None else 5000.0
        return fallback, fallback, fallback, fallback, 0.0, 0.0

    micro_delta, top_imbalance = top_book_signal(depth)
    raw = current_mid + TOM_MICRO_WEIGHT * micro_delta
    if fe is None or se is None:
        new_fe = raw
        new_se = raw
    else:
        new_fe = TOM_FAST_ALPHA * raw + (1.0 - TOM_FAST_ALPHA) * fe
        new_se = TOM_SLOW_ALPHA * raw + (1.0 - TOM_SLOW_ALPHA) * se

    previous_mid = pm if pm is not None else current_mid
    ret1 = current_mid - previous_mid
    depth_imbalance = full_depth_imbalance(depth)
    mean_dev = current_mid - new_se
    fair = (
        TOM_FAST_WEIGHT * new_fe
        + (1.0 - TOM_FAST_WEIGHT) * new_se
        + TOM_RET1_WEIGHT * ret1
        + TOM_TOP_IMBALANCE_WEIGHT * top_imbalance
        + TOM_FULL_IMBALANCE_WEIGHT * depth_imbalance
        + TOM_MEAN_DEV_WEIGHT * mean_dev
        - TOM_POSITION_PENALTY * position
    )
    return fair, new_fe, new_se, current_mid, micro_delta, top_imbalance


def quote_edge_needed(position: int, side: str, level: int) -> float:
    reducing = (side == "buy" and position < 0) or (side == "sell" and position > 0)
    same_side_heavy = (side == "buy" and position >= TOM_WARNING) or (
        side == "sell" and position <= -TOM_WARNING
    )
    if reducing:
        needed = TOM_REDUCE_EDGE
    elif same_side_heavy:
        needed = TOM_HEAVY_EDGE
    else:
        needed = TOM_BASE_EDGE
    if level == 2:
        needed += TOM_LEVEL2_EXTRA
    return needed


def directional_confidence(fair: float, mid: float, micro_delta: float, top_imbalance: float) -> Tuple[bool, bool]:
    buy = fair - mid >= 0.75 or (micro_delta >= 0.5 and top_imbalance >= 0.1)
    sell = fair - mid <= -0.75 or (micro_delta <= -0.5 and top_imbalance <= -0.1)
    return buy, sell


def trade_tomatoes(
    depth: OrderDepth, position: int, fe: Optional[float], se: Optional[float], pm: Optional[float]
) -> Tuple[List[Order], float, float, float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    fair, new_fe, new_se, current_mid, micro_delta, top_imbalance = tomato_state_fair(
        depth, position, fe, se, pm
    )
    if bid is None or ask is None or bid >= ask:
        return [], new_fe, new_se, current_mid

    spread = ask - bid
    buy_signal, sell_signal = directional_confidence(
        fair, current_mid, micro_delta, top_imbalance
    )
    orders: List[Order] = []
    buy_budget = LIMITS["TOMATOES"] - position
    sell_budget = LIMITS["TOMATOES"] + position
    temp_position = position

    for ask_price in sorted(depth.sell_orders):
        edge = fair - ask_price
        edge_needed = TOM_BUY_TAKE_EDGE + (
            TOM_CAP_EXTRA_EDGE if temp_position >= TOM_SOFT_CAP else 0.0
        )
        if edge < edge_needed or not buy_signal:
            break
        before = buy_budget
        buy_budget = add_buy(orders, "TOMATOES", ask_price, -depth.sell_orders[ask_price], buy_budget)
        temp_position += before - buy_budget

    for bid_price in sorted(depth.buy_orders, reverse=True):
        edge = bid_price - fair
        edge_needed = TOM_SELL_TAKE_EDGE + (
            TOM_CAP_EXTRA_EDGE if temp_position <= -TOM_SOFT_CAP else 0.0
        )
        if edge < edge_needed or not sell_signal:
            break
        before = sell_budget
        sell_budget = add_sell(orders, "TOMATOES", bid_price, depth.buy_orders[bid_price], sell_budget)
        temp_position -= before - sell_budget

    skew = round(temp_position * TOM_SKEW)
    strong_passive = abs(fair - current_mid) >= 0.75 or buy_signal or sell_signal
    for level, base_size in TOM_LEVELS:
        if level == 2 and (spread < 13 or not strong_passive):
            continue

        bid_size = base_size
        ask_size = base_size
        if temp_position > 0:
            bid_size = max(0, round(base_size * max(0.0, (TOM_SOFT_CAP - temp_position) / TOM_SOFT_CAP)))
        if temp_position < 0:
            ask_size = max(0, round(base_size * max(0.0, (TOM_SOFT_CAP + temp_position) / TOM_SOFT_CAP)))

        passive_bid = bid + level - skew
        if (
            bid_size > 0
            and passive_bid < ask
            and fair - passive_bid >= quote_edge_needed(temp_position, "buy", level)
        ):
            before = buy_budget
            buy_budget = add_buy(orders, "TOMATOES", passive_bid, bid_size, buy_budget)
            temp_position += before - buy_budget

        passive_ask = ask - level - skew
        if (
            ask_size > 0
            and passive_ask > bid
            and passive_ask - fair >= quote_edge_needed(temp_position, "sell", level)
        ):
            before = sell_budget
            sell_budget = add_sell(orders, "TOMATOES", passive_ask, ask_size, sell_budget)
            temp_position -= before - sell_budget

    if temp_position >= TOM_WARNING:
        liquidation_price = max(bid + 1, ask - 2 - skew)
        if liquidation_price > bid:
            extra = min(10, temp_position - TOM_WARNING + 1)
            sell_budget = add_sell(orders, "TOMATOES", liquidation_price, extra, sell_budget)
    elif temp_position <= -TOM_WARNING:
        liquidation_price = min(ask - 1, bid + 2 - skew)
        if liquidation_price < ask:
            extra = min(10, -temp_position - TOM_WARNING + 1)
            buy_budget = add_buy(orders, "TOMATOES", liquidation_price, extra, buy_budget)

    return orders, new_fe, new_se, current_mid


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

        fe = data.get("fe")
        se = data.get("se")
        pm = data.get("pm")
        if fe is not None:
            fe = float(fe)
        if se is not None:
            se = float(se)
        if pm is not None:
            pm = float(pm)

        result: Dict[str, List[Order]] = {}
        if "EMERALDS" in state.order_depths:
            result["EMERALDS"] = trade_emeralds(
                state.order_depths["EMERALDS"], int(state.position.get("EMERALDS", 0))
            )
        if "TOMATOES" in state.order_depths:
            orders, fe, se, pm = trade_tomatoes(
                state.order_depths["TOMATOES"],
                int(state.position.get("TOMATOES", 0)),
                fe,
                se,
                pm,
            )
            result["TOMATOES"] = orders

        out = {}
        if fe is not None:
            out["fe"] = round(fe, 3)
        if se is not None:
            out["se"] = round(se, 3)
        if pm is not None:
            out["pm"] = round(pm, 3)
        return result, 0, json.dumps(out) if out else ""
