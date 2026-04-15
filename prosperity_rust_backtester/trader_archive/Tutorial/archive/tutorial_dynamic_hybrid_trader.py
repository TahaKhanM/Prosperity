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
TOM_IMBALANCE_WEIGHT = 0.8
TOM_RET1_WEIGHT = -0.4
TOM_POSITION_PENALTY = 0.035
TOM_SOFT_CAP = 35
TOM_POSITION_WARN = 25
TOM_SKEW = 0.015


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

    mid = (bid + ask) / 2.0
    micro = (bid * ask_volume + ask * bid_volume) / total
    imbalance = (bid_volume - ask_volume) / total
    return micro - mid, imbalance


def add_signed_order(
    orders: List[Order], symbol: str, price: int, signed_quantity: int
) -> None:
    if signed_quantity == 0:
        return

    price = int(price)
    for order in orders:
        if order.symbol == symbol and order.price == price:
            if (order.quantity > 0 and signed_quantity > 0) or (
                order.quantity < 0 and signed_quantity < 0
            ):
                order.quantity += signed_quantity
                return
    orders.append(Order(symbol, price, signed_quantity))


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
) -> Tuple[float, float, float, float, float, float]:
    mid = mid_price(depth)
    if mid is None:
        fallback = fe if fe is not None else 5000.0
        return fallback, fallback, fallback, fallback, 0.0, 0.0

    micro_delta, imbalance = book_signal(depth)
    raw_fair = mid + TOM_RAW_MICRO_WEIGHT * micro_delta

    if fe is None or se is None:
        new_fe = raw_fair
        new_se = raw_fair
    else:
        new_fe = TOM_FAST_ALPHA * raw_fair + (1.0 - TOM_FAST_ALPHA) * fe
        new_se = TOM_SLOW_ALPHA * raw_fair + (1.0 - TOM_SLOW_ALPHA) * se

    previous_mid = pm if pm is not None else mid
    ret1 = mid - previous_mid
    fair = (
        TOM_FAIR_FAST_WEIGHT * new_fe
        + TOM_FAIR_SLOW_WEIGHT * new_se
        + TOM_IMBALANCE_WEIGHT * imbalance
        + TOM_RET1_WEIGHT * ret1
        - TOM_POSITION_PENALTY * position
    )
    return fair, new_fe, new_se, mid, micro_delta, imbalance


def tomato_quote_edge(position: int, side: str, level: int) -> float:
    reducing = (side == "buy" and position < 0) or (side == "sell" and position > 0)
    same_side_heavy = (side == "buy" and position > TOM_POSITION_WARN) or (
        side == "sell" and position < -TOM_POSITION_WARN
    )

    if reducing:
        needed = 0.75
    elif same_side_heavy:
        needed = 2.0
    else:
        needed = 1.5

    if level == 2:
        needed += 0.75
    return needed


def trade_tomatoes(
    depth: OrderDepth, position: int, fe: Optional[float], se: Optional[float], pm: Optional[float]
) -> Tuple[List[Order], float, float, float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    fair, new_fe, new_se, mid, micro_delta, imbalance = tomato_state_fair(
        depth, position, fe, se, pm
    )

    if bid is None or ask is None or bid >= ask:
        return [], new_fe, new_se, mid

    spread = ask - bid
    ret1 = mid - (pm if pm is not None else mid)
    strong_buy = micro_delta >= 0.5 and imbalance >= 0.15
    strong_sell = micro_delta <= -0.5 and imbalance <= -0.15
    reversal_buy = ret1 <= -3.0 or mid <= new_se - 5.0
    reversal_sell = ret1 >= 3.0 or mid >= new_se + 5.0

    orders: List[Order] = []
    buy_budget = LIMITS["TOMATOES"] - position
    sell_budget = LIMITS["TOMATOES"] + position
    temp_position = position

    buy_take_edge = 1.25
    sell_take_edge = 1.50

    for ask_price in sorted(depth.sell_orders):
        if not (strong_buy or reversal_buy):
            break
        edge_needed = buy_take_edge + (1.5 if temp_position >= TOM_SOFT_CAP else 0.0)
        edge = fair - ask_price
        if edge < edge_needed:
            break
        size = -depth.sell_orders[ask_price]
        before = buy_budget
        buy_budget = add_buy(orders, "TOMATOES", ask_price, size, buy_budget)
        temp_position += before - buy_budget

    for bid_price in sorted(depth.buy_orders, reverse=True):
        if not (strong_sell or reversal_sell):
            break
        edge_needed = sell_take_edge + (1.5 if temp_position <= -TOM_SOFT_CAP else 0.0)
        edge = bid_price - fair
        if edge < edge_needed:
            break
        size = depth.buy_orders[bid_price]
        before = sell_budget
        sell_budget = add_sell(orders, "TOMATOES", bid_price, size, sell_budget)
        temp_position -= before - sell_budget

    skew = round(temp_position * TOM_SKEW)
    quote_levels = [(1, 7)]
    if spread >= 13:
        quote_levels.append((2, 4))
    else:
        quote_levels[0] = (1, 5)

    for level, size in quote_levels:
        buy_price = bid + level - skew
        same_side_buy_far = temp_position >= TOM_SOFT_CAP and level > 1
        if not same_side_buy_far and buy_price < ask:
            edge_needed = tomato_quote_edge(temp_position, "buy", level)
            if fair - buy_price >= edge_needed:
                before = buy_budget
                buy_budget = add_buy(orders, "TOMATOES", buy_price, size, buy_budget)
                temp_position += before - buy_budget

        sell_price = ask - level - skew
        same_side_sell_far = temp_position <= -TOM_SOFT_CAP and level > 1
        if not same_side_sell_far and sell_price > bid:
            edge_needed = tomato_quote_edge(temp_position, "sell", level)
            if sell_price - fair >= edge_needed:
                before = sell_budget
                sell_budget = add_sell(orders, "TOMATOES", sell_price, size, sell_budget)
                temp_position -= before - sell_budget

    if temp_position >= TOM_POSITION_WARN:
        liquidation_price = ask - min(2, max(1, spread - 1)) - skew
        liquidation_price = max(liquidation_price, bid + 1)
        if liquidation_price > bid:
            before = sell_budget
            extra = min(8, temp_position - (TOM_POSITION_WARN - 1))
            sell_budget = add_sell(
                orders, "TOMATOES", liquidation_price, extra, sell_budget
            )
            temp_position -= before - sell_budget

    elif temp_position <= -TOM_POSITION_WARN:
        liquidation_price = bid + min(2, max(1, spread - 1)) - skew
        liquidation_price = min(liquidation_price, ask - 1)
        if liquidation_price < ask:
            before = buy_budget
            extra = min(8, -temp_position - (TOM_POSITION_WARN - 1))
            buy_budget = add_buy(orders, "TOMATOES", liquidation_price, extra, buy_budget)
            temp_position += before - buy_budget

    return orders, new_fe, new_se, mid


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
