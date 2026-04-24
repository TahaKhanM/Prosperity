"""Temp Round 2 aggressive quote gate variant 01."""


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

PEPPER_TEMPLATE_OFFSETS = [
    0.0, 13.5, 25.5, 39.0, 50.3, 64.0, 76.8, 88.8, 103.2, 114.0,
    126.0, 138.0, 151.3, 163.8, 176.5, 189.0, 201.5, 214.0, 226.0, 239.0,
    251.0, 264.0, 276.5, 288.5, 301.5, 314.0, 326.5, 339.5, 350.5, 364.0,
    376.2, 391.7, 399.8, 414.0, 426.8, 439.0, 451.5, 464.0, 474.3, 489.0,
    501.2, 513.5, 526.3, 538.5, 551.0, 564.5, 576.5, 588.3, 602.0, 613.5,
    626.5, 639.0, 651.0, 663.5, 677.0, 688.8, 701.0, 714.0, 725.5, 739.5,
    751.0, 762.8, 776.3, 789.0, 803.5, 813.7, 826.3, 838.7, 851.8, 864.7,
    876.3, 888.7, 900.8, 912.5, 927.3, 940.5, 951.3, 963.7, 975.8, 988.2,
    1001.3,
]
PEPPER_TEMPLATE_TIME_DENOM = 999900.0
PEPPER_REGIME_TIME_DENOM = 99900.0
PEPPER_TEMPLATE_END_PROGRESS = PEPPER_REGIME_TIME_DENOM / PEPPER_TEMPLATE_TIME_DENOM
PEPPER_REFILL_GUARD_TICKS = 1200


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def pepper_template_progress(timestamp: int) -> float:
    return clamp(timestamp / PEPPER_TEMPLATE_TIME_DENOM, 0.0, 1.0)


def pepper_regime_progress(timestamp: int) -> float:
    return clamp(timestamp / PEPPER_REGIME_TIME_DENOM, 0.0, 1.0)


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


def interp_template_offset(progress: float) -> float:
    return 0.0


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

    last_ts = int(pepper_state.get("last_ts", -1))
    if not pepper_state or timestamp < last_ts:
        reset_level = current_mm or current_mid or float(pepper_state.get("last_fair", 11000.0))
        pepper_state = {
            "open_mid": reset_level,
            "last_fair": reset_level,
            "last_mid": current_mid or reset_level,
            "trade_ema": 0.0,
        }

    fallback = float(pepper_state.get("last_fair", 11000.0))
    if current_mm is None:
        current_mm = current_mid or current_wall or fallback
    if current_wall is None:
        current_wall = current_mm
    if current_mid is None:
        current_mid = current_mm
    if current_micro is None:
        current_micro = current_mid

    prev_bid = pepper_state.get("prev_bid")
    prev_ask = pepper_state.get("prev_ask")
    flow_now = market_trade_flow_score(
        market_trades,
        int(prev_bid) if prev_bid is not None else None,
        int(prev_ask) if prev_ask is not None else None,
    )
    trade_ema = 0.86 * float(pepper_state.get("trade_ema", 0.0)) + flow_now
    imbalance_now = top_imbalance(depth)
    live_bid = best_bid(depth)
    live_ask = best_ask(depth)
    live_spread = None if live_bid is None or live_ask is None else live_ask - live_bid

    template_progress = pepper_template_progress(timestamp)
    regime_progress = pepper_regime_progress(timestamp)
    open_mid = float(pepper_state.get("open_mid", current_mid))
    template_fair = open_mid + interp_template_offset(template_progress)
    close_estimate = open_mid + interp_template_offset(PEPPER_TEMPLATE_END_PROGRESS)

    micro_bias = clamp((current_micro - current_mid) * 0.35, -1.0, 1.0)
    book_fair = current_mm + 0.20 * micro_bias
    residual = current_mid - template_fair
    flow_bias = clamp(trade_ema / 18.0, -0.7, 0.7)
    fair = max(template_fair - 0.35 + 0.10 * max(flow_bias, 0.0), book_fair, fallback - 0.12)

    recent_slope = current_mid - float(pepper_state.get("last_mid", current_mid))
    pepper_state["last_mid"] = current_mid
    pepper_state["trade_ema"] = trade_ema

    if regime_progress < 1.01 and residual < 1000.0:
        mode = "opening"
    elif residual < -2.0:
        mode = "discount"
    elif residual > 5.5:
        mode = "overheated"
    else:
        mode = "carry"

    pepper_state["last_fair"] = fair
    pepper_state["last_ts"] = timestamp
    pepper_state["prev_bid"] = best_bid(depth)
    pepper_state["prev_ask"] = best_ask(depth)

    diagnostics = {
        "mid": current_mid,
        "template": template_fair,
        "residual": residual,
        "template_progress": template_progress,
        "regime_progress": regime_progress,
        "carry_left": max(0.0, close_estimate - current_mid),
        "carry_terminal": close_estimate,
        "trade_ema": trade_ema,
        "flow_now": float(flow_now),
        "recent_slope": recent_slope,
        "imbalance": imbalance_now,
        "spread": float(live_spread) if live_spread is not None else -1.0,
    }
    return fair, mode, pepper_state, diagnostics


def pepper_caps_and_edges(mode: str) -> Dict[str, float]:
    if mode == "opening":
        return {
            "long_cap": 80, "short_cap": 4, "target_long": 45,
            "buy_edge": 1.2, "sell_edge": 8.0, "sweep_pad": 8.5,
            "bid_edge": 1.6, "ask_edge": 8.5, "bid_size": 18, "ask_size": 8,
        }
    if mode == "discount":
        return {
            "long_cap": 80, "short_cap": 4, "target_long": 80,
            "buy_edge": 1.0, "sell_edge": 8.5, "sweep_pad": 7.0,
            "bid_edge": 1.4, "ask_edge": 8.5, "bid_size": 16, "ask_size": 1,
        }
    if mode == "overheated":
        return {
            "long_cap": 78, "short_cap": 10, "target_long": 76,
            "buy_edge": 2.4, "sell_edge": 5.0, "sweep_pad": 2.0,
            "bid_edge": 2.8, "ask_edge": 6.2, "bid_size": 10, "ask_size": 2,
        }
    return {
        "long_cap": 78, "short_cap": 6, "target_long": 78,
        "buy_edge": 1.6, "sell_edge": 8.0, "sweep_pad": 3.2,
        "bid_edge": 2.0, "ask_edge": 8.0, "bid_size": 14, "ask_size": 1,
    }


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
    cfg = pepper_caps_and_edges(mode)
    residual = diagnostics["residual"]
    template_progress = diagnostics["template_progress"]
    regime_progress = diagnostics["regime_progress"]
    carry_left = diagnostics["carry_left"]
    template_fair = diagnostics["template"]
    trade_ema = diagnostics["trade_ema"]
    live_spread = int(diagnostics["spread"]) if diagnostics["spread"] >= 0.0 else None
    imbalance_now = diagnostics["imbalance"]
    buyflow = trade_ema >= 6.0
    sellflow = trade_ema <= -6.0
    cap_streak = int(pepper_state.get("cap_streak", 0))
    cap_streak = cap_streak + 1 if position >= 78 else 0
    pepper_state["cap_streak"] = cap_streak
    last_harvest_px = float(pepper_state.get("last_harvest_px", 0.0))
    last_harvest_qty = int(pepper_state.get("last_harvest_qty", 0))
    refill_guard_until = int(pepper_state.get("refill_guard_until", -1))

    long_cap = int(cfg["long_cap"])
    short_cap = int(cfg["short_cap"])
    target_long = int(cfg["target_long"])
    buy_edge = float(cfg["buy_edge"])
    sell_edge = float(cfg["sell_edge"])
    sweep_pad = float(cfg["sweep_pad"])
    bid_edge = float(cfg["bid_edge"])
    ask_edge = float(cfg["ask_edge"])
    bid_size = int(cfg["bid_size"])
    ask_size = int(cfg["ask_size"])
    top_bid = best_bid(depth)
    top_ask = best_ask(depth)

    pullback_finish_buy = (
        live_spread is not None
        and live_spread <= 12
        and 52 <= position <= 71
        and diagnostics["recent_slope"] <= -1.5
        and imbalance_now >= -0.10
        and residual <= 2.5
    )

    if pullback_finish_buy:
        target_long = max(target_long, 80)
        buy_edge = max(0.9, buy_edge - 0.15)
        sweep_pad += 0.5
        bid_edge = max(1.1, bid_edge - 0.2)
        bid_size += 2
        sell_edge += 1.0
        ask_edge += 0.8

    recycle_mode = (
        position >= 76 and 4.0 <= residual < 6.5
        and 0.08 <= regime_progress <= 0.92 and not buyflow
    )
    strong_recycle = recycle_mode and (0.33 <= regime_progress <= 0.75 or carry_left < 220.0)
    recycle_exit_push = (
        position >= 76 and residual >= 4.0 and regime_progress >= 0.33 and trade_ema <= 2.0
    )
    cap_timer_recycle = (
        position >= 78 and residual >= 3.8 and regime_progress >= 0.33
        and trade_ema <= 2.0 and cap_streak >= 10
    )
    if recycle_mode:
        if 0.33 <= regime_progress <= 0.75:
            target_long = 72
            ask_size = max(ask_size, 5)
        else:
            target_long = 74
            ask_size = max(ask_size, 4)
        if carry_left < 260.0:
            target_long = min(target_long, 72)
        buy_edge += 0.55
        sell_edge = min(sell_edge, 4.2)
        sweep_pad = min(sweep_pad, 2.2)
        bid_edge += 0.45
        ask_edge = min(ask_edge, 5.0)
        bid_size = max(6, bid_size - 4)

    if buyflow:
        target_long = min(long_cap, target_long + 2)
        buy_edge = max(0.8, buy_edge - 0.25)
        sell_edge += 1.4
        sweep_pad += 1.0
        bid_edge = max(1.0, bid_edge - 0.2)
        ask_edge += 0.8
        bid_size += 2
        ask_size = max(1, ask_size - 1)
    elif sellflow:
        target_long = max(72, target_long - (4 if residual > 1.5 else 2))
        buy_edge += 0.35
        sell_edge = max(3.6, sell_edge - 1.1)
        sweep_pad = max(1.5, sweep_pad - 0.8)
        bid_edge += 0.2
        ask_edge = max(5.0, ask_edge - 0.8)
        bid_size = max(8, bid_size - 2)
        ask_size += 2

    if residual <= -2.5 and buyflow:
        long_cap = 80
        target_long = 80
        buy_edge = max(0.7, buy_edge - 0.15)
        sweep_pad += 1.2
        bid_size += 2
    if residual >= 4.0 and sellflow:
        target_long = max(70, target_long - 2)
        sell_edge = max(3.4, sell_edge - 0.4)
        ask_size += 1
    if cap_timer_recycle:
        target_long = min(target_long, 74 if regime_progress < 0.66 else 72)
        sell_edge = max(3.4, sell_edge - (0.3 if cap_streak < 24 else 0.55))
        ask_edge = max(4.2, ask_edge - (0.35 if cap_streak < 24 else 0.6))
        ask_size = max(ask_size, 3 if cap_streak < 24 else 4)

    refill_guard_active = (
        timestamp <= refill_guard_until
        and last_harvest_qty > 0
        and position >= max(68, target_long - 6)
    )
    top_bid = best_bid(depth)
    top_ask = best_ask(depth)
    live_spread = None if top_bid is None or top_ask is None else top_ask - top_bid
    wide_high_inventory_guard = (
        live_spread is not None and live_spread >= 7
        and position >= 74 and regime_progress >= 0.14
        and (refill_guard_active or residual > -1.6)
    )

    pepper_state["diag_template_progress"] = round(template_progress, 4)
    pepper_state["diag_regime_progress"] = round(regime_progress, 4)
    pepper_state["diag_carry_left"] = round(carry_left, 2)
    pepper_state["diag_target_long"] = target_long
    pepper_state["diag_gate_mask"] = (
        (1 if recycle_mode else 0)
        | (2 if strong_recycle else 0)
        | (4 if recycle_exit_push else 0)
        | (8 if cap_timer_recycle else 0)
        | (16 if refill_guard_active else 0)
        | (64 if wide_high_inventory_guard else 0)
    )
    pepper_state["diag_signal_mask"] = 1 if pullback_finish_buy else 0

    buy_budget = max(0, min(LIMITS[PEPPER], long_cap) - position)
    sell_budget = max(0, position + min(LIMITS[PEPPER], short_cap))
    temp_position = position
    orders: List[Order] = []

    if pullback_finish_buy and top_ask is not None and temp_position < target_long:
        finish_need = max(0, min(target_long, 80) - temp_position)
        take_qty = min(16, finish_need)
        if take_qty > 0:
            before = buy_budget
            buy_budget = add_buy(orders, PEPPER, top_ask, take_qty, buy_budget)
            temp_position += before - buy_budget

    sweep_ceiling = diagnostics["template"] + sweep_pad
    for ask in sorted(depth.sell_orders):
        buy_ceiling = fair - buy_edge
        if temp_position < target_long:
            buy_ceiling = max(buy_ceiling, sweep_ceiling)
        if wide_high_inventory_guard and temp_position >= 74:
            extra_discount = 0.45
            if refill_guard_active:
                extra_discount += 0.45
            if temp_position >= 78:
                extra_discount += 0.25
            buy_ceiling = min(buy_ceiling, fair - (buy_edge + extra_discount))
        if refill_guard_active:
            materially_cheaper = ask <= last_harvest_px - 2.0
            stronger_discount = residual <= -2.5 or ask <= fair - (buy_edge + 1.0)
            continuation_override = (
                buyflow
                and diagnostics["recent_slope"] >= 0.8
                and ask <= fair - max(0.55, buy_edge - 0.2)
            )
            inventory_reset = temp_position <= max(64, target_long - 8)
            if not (materially_cheaper or stronger_discount or continuation_override or inventory_reset):
                break
        if ask > buy_ceiling:
            break
        before = buy_budget
        buy_budget = add_buy(orders, PEPPER, ask, -depth.sell_orders[ask], buy_budget)
        temp_position += before - buy_budget

    recycle_trigger = 3.8 if 0.33 <= regime_progress <= 0.75 else 4.1
    if carry_left < 220.0:
        recycle_trigger -= 0.3
    if cap_timer_recycle:
        recycle_trigger -= 0.2 if cap_streak < 24 else 0.45
    discretionary_sell_qty = 0
    discretionary_sell_px = None
    for bid in sorted(depth.buy_orders, reverse=True):
        sell_threshold = fair + sell_edge
        if strong_recycle:
            sell_threshold = min(sell_threshold, template_fair + recycle_trigger)
        if recycle_exit_push:
            sell_threshold -= 1.0
        if temp_position <= target_long or bid < sell_threshold:
            break
        before = sell_budget
        sell_budget = add_sell(orders, PEPPER, bid, depth.buy_orders[bid], sell_budget)
        sold_now = before - sell_budget
        if sold_now > 0:
            discretionary_sell_qty += sold_now
            discretionary_sell_px = bid
        temp_position -= sold_now

    if discretionary_sell_qty > 0 and position >= 76 and (
        recycle_mode or recycle_exit_push or cap_timer_recycle or mode == "overheated"
    ):
        pepper_state["last_harvest_ts"] = timestamp
        pepper_state["last_harvest_px"] = float(discretionary_sell_px or 0.0)
        pepper_state["last_harvest_qty"] = discretionary_sell_qty
        pepper_state["refill_guard_until"] = timestamp + PEPPER_REFILL_GUARD_TICKS
    elif timestamp > refill_guard_until or position <= max(64, target_long - 8):
        pepper_state["last_harvest_qty"] = 0
        pepper_state["refill_guard_until"] = -1

    clear_edge = 0.35
    if temp_position > long_cap:
        for bid in sorted(depth.buy_orders, reverse=True):
            if bid < fair - clear_edge:
                break
            before = sell_budget
            sell_budget = add_sell(orders, PEPPER, bid, depth.buy_orders[bid], sell_budget)
            temp_position -= before - sell_budget
            if temp_position <= long_cap:
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

    bid = top_bid
    ask = top_ask
    skew = clamp((temp_position - target_long) * 0.03, -1.5, 1.5)
    if residual < -2.0:
        skew -= 0.6
    elif residual > 5.0:
        skew += 0.8
    if buyflow:
        skew -= 0.3
    elif sellflow:
        skew += 0.3
    if pullback_finish_buy:
        skew -= 0.25

    quote_fair = fair - skew
    if strong_recycle:
        quote_fair = min(quote_fair, template_fair + 1.1)
    if recycle_exit_push:
        quote_fair = min(quote_fair, template_fair + 0.6)
    if cap_timer_recycle:
        quote_fair = min(quote_fair, template_fair + (0.9 if cap_streak < 24 else 0.5))
    passive_buy_gate = (
        temp_position >= 70
        and regime_progress >= 0.12
        and residual >= -0.5
        and not buyflow
    )
    if passive_buy_gate:
        bid_edge += 1.2
        ask_edge = max(3.4, ask_edge - 0.6)

    buy_prices = [
        math.floor(quote_fair - bid_edge),
        math.floor(quote_fair - (bid_edge + 1.8)),
    ]
    sell_prices = [
        math.ceil(quote_fair + ask_edge),
        math.ceil(quote_fair + (ask_edge + 1.8)),
    ]
    buy_sizes = [bid_size, max(3, bid_size - 3)]
    sell_sizes = [ask_size, max(2, ask_size - 2)]
    if passive_buy_gate:
        buy_sizes[0] = max(0, int(round(buy_sizes[0] * 0.2)))
        buy_sizes[1] = 0
        sell_sizes[0] += 2
    if recycle_exit_push:
        sell_sizes[0] = max(sell_sizes[0], 3)

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

    if temp_position > target_long or recycle_mode or (mode == "overheated" and not buyflow) or sellflow:
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
        return 15