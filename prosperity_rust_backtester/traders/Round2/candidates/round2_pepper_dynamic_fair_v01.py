"""Round 2 candidate v01: dynamic-fair Pepper + baseline Ash, bid()=15."""


import json
import math
from collections import deque
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, Trade, TradingState


ASH = "ASH_COATED_OSMIUM"
PEPPER = "INTARIAN_PEPPER_ROOT"

LIMITS = {
    ASH: 80,
    PEPPER: 80,
}

ASH_ANCHOR = 10000.0
ASH_MID_WINDOW = 20

PEPPER_DAY_TICKS = 999900.0
PEPPER_LINEAR_DRIFT = 1000.0
PEPPER_EWMA_ALPHA = 0.075
PEPPER_RESID_WINDOW = 20


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def pepper_progress(timestamp: int) -> float:
    return clamp(timestamp / PEPPER_DAY_TICKS, 0.0, 1.0)


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


def top_imbalance(depth: OrderDepth) -> float:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return 0.0
    bv = depth.buy_orders[bid]
    av = -depth.sell_orders[ask]
    total = bv + av
    if total <= 0:
        return 0.0
    return (bv - av) / total


def wall_mid(depth: OrderDepth) -> Optional[float]:
    if not depth.buy_orders or not depth.sell_orders:
        return simple_mid(depth)
    wall_bid = max(depth.buy_orders.items(), key=lambda item: (item[1], item[0]))[0]
    wall_ask = min(depth.sell_orders.items(), key=lambda item: (item[1], -item[0]))[0]
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


def market_trade_flow_score(
    market_trades: List[Trade],
    prev_bid: Optional[int],
    prev_ask: Optional[int],
) -> int:
    score = 0
    for trade in market_trades:
        price = int(trade.price)
        quantity = int(trade.quantity)
        if prev_ask is not None and price >= prev_ask:
            score += quantity
        elif prev_bid is not None and price <= prev_bid:
            score -= quantity
        elif prev_bid is not None and prev_ask is not None:
            ask_gap = abs(price - prev_ask)
            bid_gap = abs(price - prev_bid)
            if ask_gap < bid_gap:
                score += quantity
            elif bid_gap < ask_gap:
                score -= quantity
    return score


def add_buy(orders: List[Order], product: str, price: int, quantity: int, budget: int) -> int:
    size = min(quantity, budget)
    if size > 0:
        orders.append(Order(product, int(price), int(size)))
        budget -= size
    return budget


def add_sell(orders: List[Order], product: str, price: int, quantity: int, budget: int) -> int:
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
    imb = top_imbalance(depth)

    last_mid = float(ash_state.get("last_mid", current_mid))
    ret1 = current_mid - last_mid

    hist = ash_state.get("mid_hist")
    if not isinstance(hist, list):
        hist = []
    hist.append(current_mid)
    if len(hist) > ASH_MID_WINDOW:
        hist = hist[-ASH_MID_WINDOW:]
    ash_state["mid_hist"] = hist
    if len(hist) >= 5:
        mu = sum(hist) / len(hist)
        var = sum((x - mu) ** 2 for x in hist) / len(hist)
        sd = math.sqrt(var) if var > 0 else 0.0
        z20 = (current_mid - mu) / sd if sd > 0 else 0.0
    else:
        mu = current_mid
        z20 = 0.0

    anchor_dev = clamp(book_mid - ASH_ANCHOR, -3.0, 3.0)
    anchor_pull = clamp(ASH_ANCHOR - book_mid, -4.0, 4.0)
    micro_bias = clamp(current_micro - current_mid, -1.5, 1.5)
    fade_bias = clamp(-0.45 * ret1, -1.5, 1.5)
    imb_bias = clamp(imb * 1.6, -1.6, 1.6)
    z20_bias = clamp(-z20 * 0.9, -1.8, 1.8)

    anchored_fair = (
        ASH_ANCHOR
        + 0.65 * anchor_dev
        + 0.25 * micro_bias
        + 0.35 * fade_bias
        + 0.25 * imb_bias
        + 0.30 * z20_bias
    )
    dynamic_fair = (
        0.72 * book_mid
        + 0.28 * ASH_ANCHOR
        + 0.30 * anchor_pull
        + 0.25 * micro_bias
        + 0.25 * fade_bias
        + 0.20 * imb_bias
        + 0.25 * z20_bias
    )
    fair = 0.45 * anchored_fair + 0.55 * dynamic_fair
    quote_fair = dynamic_fair
    shock = abs(current_mid - ASH_ANCHOR) >= 6.0 or abs(ret1) >= 3.5

    ash_state["last_mid"] = current_mid
    ash_state["last_fair"] = fair

    diagnostics = {
        "mid": current_mid,
        "quote_fair": quote_fair,
        "ret1": ret1,
        "shock": 1.0 if shock else 0.0,
        "imb": imb,
        "z20": z20,
        "signal_bias": imb_bias + z20_bias,
    }
    return fair, ash_state, diagnostics


def trade_ash(
    depth: OrderDepth,
    position: int,
    ash_state: Dict[str, float],
    timestamp: int,
) -> Tuple[List[Order], Dict[str, float]]:
    fair, ash_state, diag = ash_fair_and_state(depth, ash_state)
    current_mid = diag["mid"]
    shock = bool(diag["shock"])
    signal_bias = diag["signal_bias"]

    long_cap = 80
    short_cap = 80
    progress = clamp(timestamp / 999900.0, 0.0, 1.0)
    soft_cap = 20 if progress < 0.18 else 12

    take_edge = 1.75 if not shock else 1.25
    pre_bid = best_bid(depth)
    pre_ask = best_ask(depth)
    live_spread = (pre_ask - pre_bid) if pre_bid is not None and pre_ask is not None else 16
    bid_top_vol = depth.buy_orders.get(pre_bid, 0) if pre_bid is not None else 0
    ask_top_vol = -depth.sell_orders.get(pre_ask, 0) if pre_ask is not None else 0
    wide_spread = live_spread >= 9
    weak_buy_support = ask_top_vol >= bid_top_vol
    spread_penalty = 0.22 * max(0, live_spread - 8)
    inventory_penalty = 0.02 * max(0, position - soft_cap)
    flow_penalty = 0.15 if wide_spread and progress >= 0.18 and weak_buy_support else 0.0
    buy_take_edge = take_edge + spread_penalty + min(0.40, inventory_penalty) + flow_penalty
    wide_buy_cooldown_until = int(ash_state.get("wide_buy_cooldown_until", -1))
    cooldown_active = live_spread >= 9 and timestamp < wide_buy_cooldown_until
    aggressive_wide_buy = False
    clear_edge = 0.5
    skew = clamp(position * 0.04, -2.0, 2.0)

    buy_budget = max(0, min(LIMITS[ASH], long_cap) - position)
    sell_budget = max(0, position + min(LIMITS[ASH], short_cap))
    temp_position = position
    orders: List[Order] = []

    for ask in sorted(depth.sell_orders):
        effective_buy_take_edge = buy_take_edge
        if cooldown_active:
            effective_buy_take_edge += 1.0
        if ask > fair - effective_buy_take_edge:
            break
        before = buy_budget
        buy_budget = add_buy(orders, ASH, ask, -depth.sell_orders[ask], buy_budget)
        bought = before - buy_budget
        temp_position += bought
        if bought > 0 and live_spread >= 9:
            aggressive_wide_buy = True

    if aggressive_wide_buy:
        ash_state["wide_buy_cooldown_until"] = timestamp + 700
    elif timestamp >= wide_buy_cooldown_until:
        ash_state.pop("wide_buy_cooldown_until", None)

    for bid in sorted(depth.buy_orders, reverse=True):
        if bid < fair + take_edge:
            break
        before = sell_budget
        sell_budget = add_sell(orders, ASH, bid, depth.buy_orders[bid], sell_budget)
        temp_position -= before - sell_budget

    clear_reference = fair
    if temp_position > soft_cap:
        for bid in sorted(depth.buy_orders, reverse=True):
            if bid < clear_reference - clear_edge:
                break
            before = sell_budget
            sell_budget = add_sell(orders, ASH, bid, depth.buy_orders[bid], sell_budget)
            temp_position -= before - sell_budget
            if temp_position <= soft_cap:
                break
    if temp_position < -soft_cap:
        for ask in sorted(depth.sell_orders):
            if ask > clear_reference + clear_edge:
                break
            before = buy_budget
            buy_budget = add_buy(orders, ASH, ask, -depth.sell_orders[ask], buy_budget)
            temp_position += before - buy_budget
            if temp_position >= -soft_cap:
                break

    bid = best_bid(depth)
    ask = best_ask(depth)
    spread = (ask - bid) if bid is not None and ask is not None else 16
    quote_fair = float(diag.get("quote_fair", fair)) - skew
    prefer_inside_buy = spread >= 15
    prefer_inside_sell = spread >= 15

    disregard_edge = 1.2 if not shock else 1.6
    join_edge = 5.0 if spread >= 18 else 4.0
    default_edge = 3.8 if spread <= 16 else 4.2
    deep_step = 2 if spread <= 16 else 3

    asks_above_fair = [
        price for price in depth.sell_orders if price > quote_fair + disregard_edge
    ]
    bids_below_fair = [
        price for price in depth.buy_orders if price < quote_fair - disregard_edge
    ]

    base_bid = math.floor(quote_fair - default_edge)
    if bids_below_fair:
        best_bid_below_fair = max(bids_below_fair)
        inside_bid = best_bid_below_fair + 1
        if (
            prefer_inside_buy
            and ask is not None
            and inside_bid < ask
            and fair - inside_bid >= 1.0
        ):
            base_bid = inside_bid
        elif quote_fair - best_bid_below_fair <= join_edge:
            base_bid = best_bid_below_fair
        else:
            base_bid = best_bid_below_fair + 1

    base_ask = math.ceil(quote_fair + default_edge)
    if asks_above_fair:
        best_ask_above_fair = min(asks_above_fair)
        inside_ask = best_ask_above_fair - 1
        if (
            prefer_inside_sell
            and bid is not None
            and inside_ask > bid
            and inside_ask - fair >= 1.0
        ):
            base_ask = inside_ask
        elif best_ask_above_fair - quote_fair <= join_edge:
            base_ask = best_ask_above_fair
        else:
            base_ask = best_ask_above_fair - 1

    if position > 20:
        base_ask -= 1
    elif position < -20:
        base_bid += 1

    buy_prices = [base_bid, base_bid - deep_step]
    sell_prices = [base_ask, base_ask + deep_step]
    if spread >= 21:
        buy_sizes = [25, 18] if not shock else [17, 13]
        sell_sizes = [25, 18] if not shock else [17, 13]
    elif spread >= 19:
        buy_sizes = [22, 16] if not shock else [15, 12]
        sell_sizes = [22, 16] if not shock else [15, 12]
    elif spread >= 18:
        buy_sizes = [20, 13] if not shock else [14, 10]
        sell_sizes = [20, 13] if not shock else [14, 10]
    else:
        buy_sizes = [18, 9] if not shock else [12, 7]
        sell_sizes = [18, 9] if not shock else [12, 7]

    if prefer_inside_buy:
        buy_sizes[0] += 1

    # Signal-based size tilt: when signal strongly says "up", bias toward buy; when "down", bias toward sell.
    if signal_bias >= 1.2:
        buy_sizes[0] += 2
        sell_sizes[0] = max(4, sell_sizes[0] - 2)
    elif signal_bias <= -1.2:
        sell_sizes[0] += 2
        buy_sizes[0] = max(4, buy_sizes[0] - 2)

    if position > 42:
        buy_sizes = [max(6, size - 3) for size in buy_sizes]
        sell_sizes = [size + 2 for size in sell_sizes]
    elif position < -42:
        buy_sizes = [size + 2 for size in buy_sizes]
        sell_sizes = [max(6, size - 3) for size in sell_sizes]

    use_second_layer = spread >= 18 or abs(position) >= 42

    seen = set()
    buy_plan = list(zip(buy_prices, buy_sizes))
    if not use_second_layer:
        buy_plan = buy_plan[:1]
    for idx, (price, size) in enumerate(buy_plan):
        if bid is not None and idx == 0:
            price = min(price, bid + 1)
        if ask is not None and price >= ask:
            price = ask - 1
        if price in seen or (ask is not None and price >= ask) or fair - price < 0.0:
            continue
        seen.add(price)
        buy_budget = add_buy(orders, ASH, price, size, buy_budget)

    seen.clear()
    sell_plan = list(zip(sell_prices, sell_sizes))
    if not use_second_layer:
        sell_plan = sell_plan[:1]
    for idx, (price, size) in enumerate(sell_plan):
        if ask is not None and idx == 0:
            price = max(price, ask - 1)
        if bid is not None and price <= bid:
            price = bid + 1
        if price in seen or (bid is not None and price <= bid) or price - fair < 0.0:
            continue
        seen.add(price)
        sell_budget = add_sell(orders, ASH, price, size, sell_budget)

    return orders, ash_state


def pepper_state_and_fair(
    depth: OrderDepth,
    pepper_state: Dict[str, float],
    market_trades: List[Trade],
    timestamp: int,
) -> Tuple[float, str, Dict[str, float], Dict[str, float]]:
    current_wall = wall_mid(depth)
    current_mm = mm10_mid(depth) or current_wall
    current_mid = simple_mid(depth)
    current_micro = microprice(depth)

    fallback = float(pepper_state.get("last_fair", 11000.0))
    if current_mm is None:
        current_mm = current_mid or current_wall or fallback
    if current_wall is None:
        current_wall = current_mm
    if current_mid is None:
        current_mid = current_mm
    if current_micro is None:
        current_micro = current_mid

    last_ts = int(pepper_state.get("last_ts", -1))
    if not pepper_state or timestamp < last_ts:
        pepper_state = {
            "open_mid": current_mm,
            "ema_mm": current_mm,
            "last_fair": current_mm,
            "last_mid": current_mid,
            "flow_ema": 0.0,
            "resid_hist": [],
        }

    prev_bid = pepper_state.get("prev_bid")
    prev_ask = pepper_state.get("prev_ask")
    flow_now = market_trade_flow_score(
        market_trades,
        int(prev_bid) if prev_bid is not None else None,
        int(prev_ask) if prev_ask is not None else None,
    )
    flow_ema = 0.84 * float(pepper_state.get("flow_ema", 0.0)) + flow_now

    progress = pepper_progress(timestamp)
    open_mid = float(pepper_state.get("open_mid", current_mm))
    ema_mm_prev = float(pepper_state.get("ema_mm", current_mm))
    ema_mm = (1.0 - PEPPER_EWMA_ALPHA) * ema_mm_prev + PEPPER_EWMA_ALPHA * current_mm
    linear_anchor = open_mid + PEPPER_LINEAR_DRIFT * progress
    book_delta = clamp(ema_mm - linear_anchor, -20.0, 20.0)
    micro_bias = clamp((current_micro - current_mid) * 0.35, -0.8, 0.8)
    flow_bias = clamp(flow_ema / 18.0, -0.9, 0.9)
    fair = linear_anchor + 0.22 * book_delta + 0.25 * micro_bias + 0.45 * flow_bias

    residual = current_mid - fair
    resid_hist = pepper_state.get("resid_hist")
    if not isinstance(resid_hist, list):
        resid_hist = []
    resid_hist.append(residual)
    if len(resid_hist) > PEPPER_RESID_WINDOW:
        resid_hist = resid_hist[-PEPPER_RESID_WINDOW:]
    pepper_state["resid_hist"] = resid_hist

    resid_mean = sum(resid_hist) / len(resid_hist) if resid_hist else residual
    resid_var = sum((value - resid_mean) ** 2 for value in resid_hist) / len(resid_hist) if resid_hist else 0.0
    resid_sd = math.sqrt(resid_var) if resid_var > 0 else 0.0
    z20 = (residual - resid_mean) / resid_sd if resid_sd > 0 else 0.0

    imbalance_now = top_imbalance(depth)
    live_bid = best_bid(depth)
    live_ask = best_ask(depth)
    live_spread = None if live_bid is None or live_ask is None else live_ask - live_bid
    recent_slope = current_mid - float(pepper_state.get("last_mid", current_mid))

    if residual <= -3.0 or z20 <= -1.1:
        mode = "buy_dip"
    elif residual >= 4.0 or z20 >= 1.35:
        mode = "sell_rip"
    else:
        mode = "carry"

    pepper_state["ema_mm"] = ema_mm
    pepper_state["flow_ema"] = flow_ema
    pepper_state["last_mid"] = current_mid
    pepper_state["last_fair"] = fair
    pepper_state["last_ts"] = timestamp
    pepper_state["prev_bid"] = live_bid
    pepper_state["prev_ask"] = live_ask

    diagnostics = {
        "mid": current_mid,
        "fair": fair,
        "linear_anchor": linear_anchor,
        "progress": progress,
        "residual": residual,
        "z20": z20,
        "flow_ema": flow_ema,
        "flow_now": float(flow_now),
        "recent_slope": recent_slope,
        "imbalance": imbalance_now,
        "spread": float(live_spread) if live_spread is not None else -1.0,
        "carry_left": max(0.0, open_mid + PEPPER_LINEAR_DRIFT - current_mid),
    }
    return fair, mode, pepper_state, diagnostics


def trade_pepper(
    depth: OrderDepth,
    position: int,
    pepper_state: Dict[str, float],
    market_trades: List[Trade],
    timestamp: int,
) -> Tuple[List[Order], Dict[str, float]]:
    fair, mode, pepper_state, diagnostics = pepper_state_and_fair(
        depth, pepper_state, market_trades, timestamp,
    )
    residual = diagnostics["residual"]
    z20 = diagnostics["z20"]
    progress = diagnostics["progress"]
    carry_left = diagnostics["carry_left"]
    trade_ema = diagnostics["flow_ema"]
    live_spread = int(diagnostics["spread"]) if diagnostics["spread"] >= 0.0 else None
    imbalance_now = diagnostics["imbalance"]
    buyflow = trade_ema >= 6.0
    sellflow = trade_ema <= -6.0
    top_bid = best_bid(depth)
    top_ask = best_ask(depth)

    base_target = 76 if progress < 0.78 else 68 if progress < 0.92 else 54
    target_long = base_target
    if mode == "buy_dip":
        target_long += 4
    elif mode == "sell_rip":
        target_long -= 10
    if imbalance_now >= 0.15:
        target_long += 2
    elif imbalance_now <= -0.15:
        target_long -= 2
    if buyflow:
        target_long += 2
    elif sellflow:
        target_long -= 3
    if carry_left < 140.0:
        target_long = min(target_long, 60)
    target_long = int(clamp(target_long, 32, 80))

    long_cap = 80
    short_cap = 12
    buy_edge = 2.7
    sell_edge = 4.2
    refill_edge = 0.9
    bid_edge = 2.4
    ask_edge = 4.8
    bid_size = 18
    ask_size = 8

    if mode == "buy_dip":
        buy_edge = 1.6
        sell_edge = 5.0
        refill_edge = 1.3
        bid_edge = 1.8
        bid_size = 22
        ask_size = 5
    elif mode == "sell_rip":
        buy_edge = 3.5
        sell_edge = 2.8
        refill_edge = 0.6
        ask_edge = 3.8
        bid_size = 12
        ask_size = 14

    if z20 <= -1.6:
        buy_edge = max(1.2, buy_edge - 0.5)
        refill_edge += 0.4
        bid_size += 3
    elif z20 >= 1.7:
        sell_edge = max(2.2, sell_edge - 0.4)
        ask_edge = max(3.2, ask_edge - 0.5)
        ask_size += 3

    if live_spread is not None and live_spread <= 12:
        buy_edge += 0.2
        sell_edge += 0.2
    elif live_spread is not None and live_spread >= 15:
        bid_edge += 0.4
        ask_edge += 0.4

    buy_budget = max(0, long_cap - position)
    sell_budget = max(0, position + short_cap)
    temp_position = position
    orders: List[Order] = []

    for ask in sorted(depth.sell_orders):
        buy_ceiling = fair - buy_edge
        if temp_position < target_long:
            buy_ceiling = max(buy_ceiling, fair + refill_edge)
        if temp_position >= 74 and residual > -1.0:
            buy_ceiling = min(buy_ceiling, fair - max(0.6, buy_edge - 0.3))
        if ask > buy_ceiling:
            break
        before = buy_budget
        buy_budget = add_buy(orders, PEPPER, ask, -depth.sell_orders[ask], buy_budget)
        temp_position += before - buy_budget

    for bid in sorted(depth.buy_orders, reverse=True):
        sell_threshold = fair + sell_edge
        if temp_position > target_long:
            sell_threshold = min(sell_threshold, fair + 1.0)
        if carry_left < 120.0:
            sell_threshold = min(sell_threshold, fair + 0.8)
        if temp_position <= target_long or bid < sell_threshold:
            break
        before = sell_budget
        sell_budget = add_sell(orders, PEPPER, bid, depth.buy_orders[bid], sell_budget)
        temp_position -= before - sell_budget

    clear_edge = 0.35
    if temp_position > 78:
        for bid in sorted(depth.buy_orders, reverse=True):
            if bid < fair - clear_edge:
                break
            before = sell_budget
            sell_budget = add_sell(orders, PEPPER, bid, depth.buy_orders[bid], sell_budget)
            temp_position -= before - sell_budget
            if temp_position <= 78:
                break

    if temp_position < -4:
        for ask in sorted(depth.sell_orders):
            if ask > fair + clear_edge:
                break
            before = buy_budget
            buy_budget = add_buy(orders, PEPPER, ask, -depth.sell_orders[ask], buy_budget)
            temp_position += before - buy_budget
            if temp_position >= -4:
                break

    bid = top_bid
    ask = top_ask
    skew = clamp((temp_position - target_long) * 0.035, -1.8, 1.8)
    skew += clamp(imbalance_now * 1.2, -0.9, 0.9)
    skew += clamp(trade_ema / 28.0, -0.7, 0.7)
    if residual < -2.0 or z20 < -1.0:
        skew -= 0.5
    elif residual > 3.0 or z20 > 1.1:
        skew += 0.7
    if buyflow:
        skew -= 0.2
    elif sellflow:
        skew += 0.3
    quote_fair = fair - skew
    buy_prices = [
        math.floor(quote_fair - bid_edge),
        math.floor(quote_fair - (bid_edge + 2.0)),
    ]
    sell_prices = [
        math.ceil(quote_fair + ask_edge),
        math.ceil(quote_fair + (ask_edge + 2.1)),
    ]
    buy_sizes = [bid_size, max(6, bid_size - 4)]
    sell_sizes = [ask_size, max(3, ask_size - 3)]

    seen = set()
    for idx, (price, size) in enumerate(zip(buy_prices, buy_sizes)):
        if bid is not None and idx == 0:
            price = min(price, bid + 1)
        if ask is not None and price >= ask:
            price = ask - 1
        if price in seen or (ask is not None and price >= ask) or fair - price < 0.6:
            continue
        seen.add(price)
        buy_budget = add_buy(orders, PEPPER, price, size, buy_budget)

    if temp_position > target_long - 4 or mode == "sell_rip" or sellflow or carry_left < 120.0:
        seen.clear()
        for idx, (price, size) in enumerate(zip(sell_prices, sell_sizes)):
            if ask is not None and idx == 0:
                price = max(price, ask - 1)
            if bid is not None and price <= bid:
                price = bid + 1
            if price in seen or (bid is not None and price <= bid) or price - fair < 0.6:
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
                int(state.timestamp),
            )

        if PEPPER in state.order_depths:
            result[PEPPER], pepper_state = trade_pepper(
                state.order_depths[PEPPER],
                int(state.position.get(PEPPER, 0)),
                pepper_state,
                list(state.market_trades.get(PEPPER, [])),
                int(state.timestamp),
            )

        trader_data = json.dumps({"ash": ash_state, "pepper": pepper_state})
        return result, 0, trader_data

    def bid(self) -> int:
        return 20
