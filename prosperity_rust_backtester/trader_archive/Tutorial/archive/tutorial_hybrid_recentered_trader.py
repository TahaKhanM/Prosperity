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
TOM_RAW_MICRO_WEIGHT = 0.4
TOM_FAIR_FAST_WEIGHT = 0.75
TOM_FAIR_SLOW_WEIGHT = 0.25
TOM_TOP_IMBALANCE_WEIGHT = 0.6
TOM_FULL_IMBALANCE_WEIGHT = -0.6
TOM_RET1_WEIGHT = -0.45
TOM_MEAN_DEV_WEIGHT = -0.25
TOM_POSITION_PENALTY = 0.05
TOM_SOFT_CAP = 35
TOM_POSITION_WARN = 20
TOM_SKEW = 0.015
TOM_BUY_TAKE_EDGE = 1.25
TOM_SELL_TAKE_EDGE = 1.75


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


def add_signed_order(
    orders: List[Order], symbol: str, price: int, signed_quantity: int
) -> None:
    if signed_quantity == 0:
        return
    for order in orders:
        if order.symbol == symbol and order.price == int(price):
            if (order.quantity > 0 and signed_quantity > 0) or (
                order.quantity < 0 and signed_quantity < 0
            ):
                order.quantity += signed_quantity
                return
    orders.append(Order(symbol, int(price), signed_quantity))


def add_buy(
    orders: List[Order], symbol: str, price: int, quantity: int, buy_budget: int
) -> int:
    fill = min(quantity, buy_budget)
    if fill > 0:
        add_signed_order(orders, symbol, int(price), fill)
        buy_budget -= fill
    return buy_budget


def add_sell(
    orders: List[Order], symbol: str, price: int, quantity: int, sell_budget: int
) -> int:
    fill = min(quantity, sell_budget)
    if fill > 0:
        add_signed_order(orders, symbol, int(price), -fill)
        sell_budget -= fill
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
) -> Tuple[float, float, float, float, float, float, float]:
    current_mid = mid_price(depth)
    if current_mid is None:
        fallback = fe if fe is not None else 5000.0
        return fallback, fallback, fallback, fallback, 0.0, 0.0, 0.0

    micro_delta, top_imbalance = top_book_signal(depth)
    raw_fair = current_mid + TOM_RAW_MICRO_WEIGHT * micro_delta

    if fe is None or se is None:
        new_fe = raw_fair
        new_se = raw_fair
    else:
        new_fe = TOM_FAST_ALPHA * raw_fair + (1.0 - TOM_FAST_ALPHA) * fe
        new_se = TOM_SLOW_ALPHA * raw_fair + (1.0 - TOM_SLOW_ALPHA) * se

    previous_mid = pm if pm is not None else current_mid
    ret1 = current_mid - previous_mid
    mean_dev = current_mid - new_se
    depth_imbalance = full_depth_imbalance(depth)
    fair = (
        TOM_FAIR_FAST_WEIGHT * new_fe
        + TOM_FAIR_SLOW_WEIGHT * new_se
        + TOM_TOP_IMBALANCE_WEIGHT * top_imbalance
        + TOM_FULL_IMBALANCE_WEIGHT * depth_imbalance
        + TOM_RET1_WEIGHT * ret1
        + TOM_MEAN_DEV_WEIGHT * mean_dev
        - TOM_POSITION_PENALTY * position
    )
    return fair, new_fe, new_se, current_mid, micro_delta, top_imbalance, mean_dev


def quote_edge_needed(position: int, side: str, level: int) -> float:
    reducing = (side == "buy" and position < 0) or (side == "sell" and position > 0)
    same_side_heavy = (side == "buy" and position >= TOM_POSITION_WARN) or (
        side == "sell" and position <= -TOM_POSITION_WARN
    )
    if reducing:
        needed = 0.75
    elif same_side_heavy:
        needed = 2.25
    else:
        needed = 1.75
    if level == 2:
        needed += 0.75
    return needed


def trade_tomatoes(
    depth: OrderDepth, position: int, fe: Optional[float], se: Optional[float], pm: Optional[float]
) -> Tuple[List[Order], float, float, float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    fair, new_fe, new_se, current_mid, micro_delta, top_imbalance, mean_dev = tomato_state_fair(
        depth, position, fe, se, pm
    )

    if bid is None or ask is None or bid >= ask:
        return [], new_fe, new_se, current_mid

    spread = ask - bid
    ret1 = current_mid - (pm if pm is not None else current_mid)
    strong_buy = fair - current_mid >= 0.75 or (micro_delta >= 0.5 and top_imbalance >= 0.15)
    strong_sell = fair - current_mid <= -0.9 or (micro_delta <= -0.5 and top_imbalance <= -0.15)
    reversal_buy = ret1 <= -3.0 or mean_dev <= -4.0
    reversal_sell = ret1 >= 3.0 or mean_dev >= 5.0

    orders: List[Order] = []
    buy_budget = LIMITS["TOMATOES"] - position
    sell_budget = LIMITS["TOMATOES"] + position
    temp_position = position

    for ask_price in sorted(depth.sell_orders):
        edge_needed = TOM_BUY_TAKE_EDGE + (1.5 if temp_position >= TOM_SOFT_CAP else 0.0)
        edge = fair - ask_price
        if edge < edge_needed or not (strong_buy or reversal_buy):
            break
        before = buy_budget
        buy_budget = add_buy(orders, "TOMATOES", ask_price, -depth.sell_orders[ask_price], buy_budget)
        temp_position += before - buy_budget

    for bid_price in sorted(depth.buy_orders, reverse=True):
        edge_needed = TOM_SELL_TAKE_EDGE + (1.5 if temp_position <= -TOM_SOFT_CAP else 0.0)
        edge = bid_price - fair
        if edge < edge_needed or not (strong_sell or reversal_sell):
            break
        before = sell_budget
        sell_budget = add_sell(orders, "TOMATOES", bid_price, depth.buy_orders[bid_price], sell_budget)
        temp_position -= before - sell_budget

    skew = round(temp_position * TOM_SKEW)
    quote_levels = [(1, 6)]
    confidence = abs(fair - current_mid) >= 0.75 or strong_buy or strong_sell
    if spread >= 13 and confidence:
        quote_levels.append((2, 3))

    for level, size in quote_levels:
        buy_price = bid + level - skew
        if (
            buy_price < ask
            and not (temp_position >= TOM_SOFT_CAP and level > 1)
            and fair - buy_price >= quote_edge_needed(temp_position, "buy", level)
        ):
            before = buy_budget
            buy_budget = add_buy(orders, "TOMATOES", buy_price, size, buy_budget)
            temp_position += before - buy_budget

        sell_price = ask - level - skew
        if (
            sell_price > bid
            and not (temp_position <= -TOM_SOFT_CAP and level > 1)
            and sell_price - fair >= quote_edge_needed(temp_position, "sell", level)
        ):
            before = sell_budget
            sell_budget = add_sell(orders, "TOMATOES", sell_price, size, sell_budget)
            temp_position -= before - sell_budget

    if temp_position >= TOM_POSITION_WARN:
        liquidation_price = max(bid + 1, ask - 2 - skew)
        if liquidation_price > bid:
            extra = min(10, temp_position - TOM_POSITION_WARN + 1)
            sell_budget = add_sell(
                orders, "TOMATOES", liquidation_price, extra, sell_budget
            )
    elif temp_position <= -TOM_POSITION_WARN:
        liquidation_price = min(ask - 1, bid + 2 - skew)
        if liquidation_price < ask:
            extra = min(10, -temp_position - TOM_POSITION_WARN + 1)
            buy_budget = add_buy(
                orders, "TOMATOES", liquidation_price, extra, buy_budget
            )

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
                state.order_depths["EMERALDS"],
                int(state.position.get("EMERALDS", 0)),
            )

        if "TOMATOES" in state.order_depths:
            tomato_orders, fe, se, pm = trade_tomatoes(
                state.order_depths["TOMATOES"],
                int(state.position.get("TOMATOES", 0)),
                fe,
                se,
                pm,
            )
            result["TOMATOES"] = tomato_orders

        trader_data = ""
        if fe is not None and se is not None and pm is not None:
            trader_data = json.dumps(
                {"fe": round(fe, 3), "se": round(se, 3), "pm": round(pm, 3)}
            )

        return result, 0, trader_data
