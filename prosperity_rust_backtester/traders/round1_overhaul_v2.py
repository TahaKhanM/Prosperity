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

ASH_ANCHOR = 10000.0


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


def wall_mid(depth: OrderDepth) -> Optional[float]:
    if not depth.buy_orders or not depth.sell_orders:
        return simple_mid(depth)

    wall_bid = max(depth.buy_orders.items(), key=lambda item: (item[1], item[0]))[0]
    wall_ask = min(
        depth.sell_orders.items(),
        key=lambda item: (item[1], -item[0]),
    )[0]
    return (wall_bid + wall_ask) / 2.0


def mm10_mid(depth: OrderDepth) -> Optional[float]:
    if not depth.buy_orders or not depth.sell_orders:
        return simple_mid(depth)

    bid = next(
        (price for price, volume in sorted(depth.buy_orders.items(), reverse=True) if volume >= 10),
        None,
    )
    ask = next(
        (price for price, volume in sorted(depth.sell_orders.items()) if -volume >= 10),
        None,
    )
    if bid is None or ask is None:
        return wall_mid(depth)
    return (bid + ask) / 2.0


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


def ash_fair_and_state(
    depth: OrderDepth,
    ash_state: Dict[str, float],
) -> Tuple[float, Dict[str, float], Dict[str, float]]:
    current_mid = simple_mid(depth)
    book_mid = mm10_mid(depth) or wall_mid(depth) or current_mid or ASH_ANCHOR
    current_mid = current_mid if current_mid is not None else book_mid
    current_micro = microprice(depth) or current_mid

    last_mid = float(ash_state.get("last_mid", current_mid))
    ret1 = current_mid - last_mid

    anchor_dev = clamp(book_mid - ASH_ANCHOR, -3.0, 3.0)
    micro_bias = clamp(current_micro - current_mid, -1.5, 1.5)
    fade_bias = clamp(-0.45 * ret1, -1.5, 1.5)

    fair = ASH_ANCHOR + 0.65 * anchor_dev + 0.25 * micro_bias + 0.35 * fade_bias
    shock = abs(current_mid - ASH_ANCHOR) >= 6.0 or abs(ret1) >= 3.5

    ash_state["last_mid"] = current_mid
    ash_state["last_fair"] = fair

    diagnostics = {
        "mid": current_mid,
        "ret1": ret1,
        "shock": 1.0 if shock else 0.0,
    }
    return fair, ash_state, diagnostics


def trade_ash(
    depth: OrderDepth,
    position: int,
    ash_state: Dict[str, float],
) -> Tuple[List[Order], Dict[str, float]]:
    fair, ash_state, diag = ash_fair_and_state(depth, ash_state)
    current_mid = diag["mid"]
    shock = bool(diag["shock"])

    long_cap = 70
    short_cap = 70
    soft_cap = 55

    take_edge = 3.5 if not shock else 3.0
    clear_edge = 0.5
    skew = clamp(position * 0.04, -2.0, 2.0)

    buy_budget = max(0, min(LIMITS[ASH], long_cap) - position)
    sell_budget = max(0, position + min(LIMITS[ASH], short_cap))
    temp_position = position
    orders: List[Order] = []

    for ask in sorted(depth.sell_orders):
        if ask > fair - take_edge:
            break
        before = buy_budget
        buy_budget = add_buy(orders, ASH, ask, -depth.sell_orders[ask], buy_budget)
        temp_position += before - buy_budget

    for bid in sorted(depth.buy_orders, reverse=True):
        if bid < fair + take_edge:
            break
        before = sell_budget
        sell_budget = add_sell(orders, ASH, bid, depth.buy_orders[bid], sell_budget)
        temp_position -= before - sell_budget

    anchor_clear = ASH_ANCHOR
    if temp_position > soft_cap:
        for bid in sorted(depth.buy_orders, reverse=True):
            if bid < anchor_clear - clear_edge:
                break
            before = sell_budget
            sell_budget = add_sell(orders, ASH, bid, depth.buy_orders[bid], sell_budget)
            temp_position -= before - sell_budget
            if temp_position <= soft_cap:
                break
    if temp_position < -soft_cap:
        for ask in sorted(depth.sell_orders):
            if ask > anchor_clear + clear_edge:
                break
            before = buy_budget
            buy_budget = add_buy(orders, ASH, ask, -depth.sell_orders[ask], buy_budget)
            temp_position += before - buy_budget
            if temp_position >= -soft_cap:
                break

    bid = best_bid(depth)
    ask = best_ask(depth)
    quote_fair = fair - skew
    buy_prices = [
        math.floor(quote_fair - 4.5),
        math.floor(quote_fair - 6.5),
    ]
    sell_prices = [
        math.ceil(quote_fair + 4.5),
        math.ceil(quote_fair + 6.5),
    ]
    buy_sizes = [8, 10] if not shock else [6, 8]
    sell_sizes = [8, 10] if not shock else [6, 8]

    seen = set()
    for idx, (price, size) in enumerate(zip(buy_prices, buy_sizes)):
        if bid is not None and idx == 0:
            price = min(price, bid + 1)
        if ask is not None and price >= ask:
            price = ask - 1
        if price in seen or (ask is not None and price >= ask) or fair - price < 1.0:
            continue
        seen.add(price)
        buy_budget = add_buy(orders, ASH, price, size, buy_budget)

    seen.clear()
    for idx, (price, size) in enumerate(zip(sell_prices, sell_sizes)):
        if ask is not None and idx == 0:
            price = max(price, ask - 1)
        if bid is not None and price <= bid:
            price = bid + 1
        if price in seen or (bid is not None and price <= bid) or price - fair < 1.0:
            continue
        seen.add(price)
        sell_budget = add_sell(orders, ASH, price, size, sell_budget)

    return orders, ash_state


def pepper_state_and_fair(
    depth: OrderDepth,
    pepper_state: Dict[str, float],
    timestamp: int,
) -> Tuple[float, str, Dict[str, float], Dict[str, float]]:
    current_wall = wall_mid(depth)
    current_mid = simple_mid(depth)
    current_micro = microprice(depth)

    last_ts = int(pepper_state.get("last_ts", -1))
    if not pepper_state or timestamp < last_ts:
        reset_level = current_wall or current_mid or float(pepper_state.get("last_fair", 11000.0))
        pepper_state = {
            "open_wall": reset_level,
            "ema_wall": reset_level,
            "last_fair": reset_level,
            "last_mid": current_mid or reset_level,
            "ramp_ema": 0.0,
            "steps": 0,
        }

    fallback = float(pepper_state.get("last_fair", 11000.0))
    if current_wall is None:
        current_wall = current_mid or fallback
    if current_mid is None:
        current_mid = current_wall
    if current_micro is None:
        current_micro = current_mid

    pepper_state["steps"] = int(pepper_state.get("steps", 0)) + 1
    steps = max(1, int(pepper_state["steps"]))

    ema_wall = 0.92 * float(pepper_state.get("ema_wall", current_wall)) + 0.08 * current_wall
    pepper_state["ema_wall"] = ema_wall

    last_mid = float(pepper_state.get("last_mid", current_mid))
    mid_delta = current_mid - last_mid
    ramp_ema = 0.92 * float(pepper_state.get("ramp_ema", 0.0)) + 0.08 * mid_delta
    pepper_state["ramp_ema"] = ramp_ema
    pepper_state["last_mid"] = current_mid

    open_wall = float(pepper_state.get("open_wall", current_wall))
    trend_per_step = (ema_wall - open_wall) / steps
    trend_bias = clamp(trend_per_step * 40.0, -4.5, 4.5)
    micro_bias = clamp((current_micro - current_mid) * 0.35, -1.0, 1.0)

    ramp_base = max(current_wall + trend_bias, fallback - 0.25) + 0.2 * micro_bias
    neutral_base = current_wall + 0.35 * micro_bias
    overshoot = current_mid - ramp_base

    ramp_confident = trend_per_step > 0.05 and ramp_ema > -0.12 and current_wall >= ema_wall - 1.5

    if ramp_confident and overshoot > 2.5:
        mode = "ramp_overheated"
        fair = ramp_base - 1.2
    elif ramp_confident and overshoot < -2.5:
        mode = "ramp_discount"
        fair = ramp_base + 0.8
    elif ramp_confident:
        mode = "ramp"
        fair = ramp_base
    elif abs(overshoot) > 3.0:
        mode = "neutral_revert"
        fair = neutral_base - clamp(0.45 * overshoot, -1.5, 1.5)
    else:
        mode = "neutral"
        fair = neutral_base

    pepper_state["last_fair"] = fair
    pepper_state["last_ts"] = timestamp

    diagnostics = {
        "trend_per_step": trend_per_step,
        "overshoot": overshoot,
        "mid": current_mid,
        "ramp_ema": ramp_ema,
        "observed_drift": current_wall - open_wall,
        "steps": float(steps),
    }
    return fair, mode, pepper_state, diagnostics


def pepper_caps_and_edges(mode: str, diagnostics: Dict[str, float]) -> Dict[str, float]:
    observed_drift = max(0.0, diagnostics.get("observed_drift", 0.0))
    trend_per_step = max(0.0, diagnostics.get("trend_per_step", 0.0))
    ramp_ema = max(0.0, diagnostics.get("ramp_ema", 0.0))
    confidence = clamp(observed_drift / 35.0 + 1.5 * trend_per_step + ramp_ema, 0.0, 1.0)
    base_long_cap = int(round(34 + 42 * confidence))
    base_short_cap = int(round(24 - 14 * confidence))

    if mode == "ramp_discount":
        return {
            "long_cap": min(78, base_long_cap + 4),
            "short_cap": max(8, base_short_cap - 4),
            "buy_edge": 2.0,
            "sell_edge": 5.2,
            "bid_edge": 2.5,
            "ask_edge": 6.5,
            "bid_size": 12,
            "ask_size": 4,
            "confidence": confidence,
        }
    if mode == "ramp":
        return {
            "long_cap": min(76, base_long_cap + 2),
            "short_cap": max(10, base_short_cap - 2),
            "buy_edge": 2.4,
            "sell_edge": 4.8,
            "bid_edge": 2.8,
            "ask_edge": 6.2,
            "bid_size": 11,
            "ask_size": 5,
            "confidence": confidence,
        }
    if mode == "ramp_overheated":
        return {
            "long_cap": max(42, base_long_cap - 10),
            "short_cap": max(18, base_short_cap + 4),
            "buy_edge": 3.4,
            "sell_edge": 3.0,
            "bid_edge": 3.4,
            "ask_edge": 5.0,
            "bid_size": 8,
            "ask_size": 7,
            "confidence": confidence,
        }
    if mode == "neutral_revert":
        return {
            "long_cap": min(48, base_long_cap),
            "short_cap": 48,
            "buy_edge": 2.8,
            "sell_edge": 2.8,
            "bid_edge": 3.5,
            "ask_edge": 3.5,
            "bid_size": 8,
            "ask_size": 8,
            "confidence": confidence,
        }
    return {
        "long_cap": min(52, base_long_cap),
        "short_cap": 50,
        "buy_edge": 3.0,
        "sell_edge": 3.0,
        "bid_edge": 3.8,
        "ask_edge": 3.8,
        "bid_size": 8,
        "ask_size": 8,
        "confidence": confidence,
    }


def trade_pepper(
    depth: OrderDepth,
    position: int,
    pepper_state: Dict[str, float],
    timestamp: int,
) -> Tuple[List[Order], Dict[str, float]]:
    fair, mode, pepper_state, diagnostics = pepper_state_and_fair(depth, pepper_state, timestamp)
    cfg = pepper_caps_and_edges(mode, diagnostics)
    overshoot = diagnostics["overshoot"]

    long_cap = int(cfg["long_cap"])
    short_cap = int(cfg["short_cap"])
    soft_cap = max(40, long_cap - 10)

    buy_budget = max(0, min(LIMITS[PEPPER], long_cap) - position)
    sell_budget = max(0, position + min(LIMITS[PEPPER], short_cap))
    temp_position = position
    orders: List[Order] = []

    for ask in sorted(depth.sell_orders):
        if ask > fair - cfg["buy_edge"]:
            break
        before = buy_budget
        buy_budget = add_buy(orders, PEPPER, ask, -depth.sell_orders[ask], buy_budget)
        temp_position += before - buy_budget

    for bid in sorted(depth.buy_orders, reverse=True):
        if bid < fair + cfg["sell_edge"]:
            break
        before = sell_budget
        sell_budget = add_sell(orders, PEPPER, bid, depth.buy_orders[bid], sell_budget)
        temp_position -= before - sell_budget

    clear_edge = 0.75
    if temp_position > soft_cap:
        for bid in sorted(depth.buy_orders, reverse=True):
            if bid < fair - clear_edge:
                break
            before = sell_budget
            sell_budget = add_sell(orders, PEPPER, bid, depth.buy_orders[bid], sell_budget)
            temp_position -= before - sell_budget
            if temp_position <= soft_cap:
                break

    if temp_position < -short_cap + 8:
        for ask in sorted(depth.sell_orders):
            if ask > fair + clear_edge:
                break
            before = buy_budget
            buy_budget = add_buy(orders, PEPPER, ask, -depth.sell_orders[ask], buy_budget)
            temp_position += before - buy_budget
            if temp_position >= -short_cap + 8:
                break

    bid = best_bid(depth)
    ask = best_ask(depth)
    skew = clamp(temp_position * 0.03, -2.0, 2.0)
    if mode.startswith("ramp"):
        skew -= 0.2 + 0.6 * float(cfg.get("confidence", 0.0))
    if overshoot > 2.5:
        skew += 0.8
    elif overshoot < -2.5:
        skew -= 0.6

    quote_fair = fair - skew
    buy_prices = [
        math.floor(quote_fair - cfg["bid_edge"]),
        math.floor(quote_fair - (cfg["bid_edge"] + 1.8)),
    ]
    sell_prices = [
        math.ceil(quote_fair + cfg["ask_edge"]),
        math.ceil(quote_fair + (cfg["ask_edge"] + 1.8)),
    ]
    buy_sizes = [int(cfg["bid_size"]), max(3, int(cfg["bid_size"]) - 3)]
    sell_sizes = [int(cfg["ask_size"]), max(2, int(cfg["ask_size"]) - 2)]

    seen = set()
    for idx, (price, size) in enumerate(zip(buy_prices, buy_sizes)):
        if bid is not None and idx == 0:
            price = min(price, bid + 1)
        if ask is not None and price >= ask:
            price = ask - 1
        if price in seen or (ask is not None and price >= ask) or fair - price < 0.8:
            continue
        seen.add(price)
        buy_budget = add_buy(orders, PEPPER, price, size, buy_budget)

    seen.clear()
    for idx, (price, size) in enumerate(zip(sell_prices, sell_sizes)):
        if ask is not None and idx == 0:
            price = max(price, ask - 1)
        if bid is not None and price <= bid:
            price = bid + 1
        if price in seen or (bid is not None and price <= bid) or price - fair < 0.8:
            continue
        seen.add(price)
        sell_budget = add_sell(orders, PEPPER, price, size, sell_budget)

    return orders, pepper_state


class Trader:
    def run(self, state: TradingState):
        raw_state: Dict[str, Dict[str, float]] = {}
        if state.traderData:
            try:
                decoded = json.loads(state.traderData)
                if isinstance(decoded, dict):
                    raw_state = decoded
            except Exception:
                raw_state = {}

        ash_state = raw_state.get("ash", {})
        pepper_state = raw_state.get("pepper", {})

        result: Dict[str, List[Order]] = {}

        if ASH in state.order_depths:
            result[ASH], ash_state = trade_ash(
                state.order_depths[ASH],
                int(state.position.get(ASH, 0)),
                ash_state,
            )

        if PEPPER in state.order_depths:
            result[PEPPER], pepper_state = trade_pepper(
                state.order_depths[PEPPER],
                int(state.position.get(PEPPER, 0)),
                pepper_state,
                int(state.timestamp),
            )

        trader_data = json.dumps(
            {
                "ash": ash_state,
                "pepper": pepper_state,
            }
        )
        return result, 0, trader_data
