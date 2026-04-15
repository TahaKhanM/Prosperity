import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, Trade, TradingState


ASH = "ASH_COATED_OSMIUM"
PEPPER = "INTARIAN_PEPPER_ROOT"

LIMITS = {
    ASH: 80,
    PEPPER: 80,
}

ASH_ANCHOR = 10000.0
PEPPER_TEMPLATE_OFFSETS = [
    0.0,
    13.5,
    25.5,
    39.0,
    50.3,
    64.0,
    76.8,
    88.8,
    103.2,
    114.0,
    126.0,
    138.0,
    151.3,
    163.8,
    176.5,
    189.0,
    201.5,
    214.0,
    226.0,
    239.0,
    251.0,
    264.0,
    276.5,
    288.5,
    301.5,
    314.0,
    326.5,
    339.5,
    350.5,
    364.0,
    376.2,
    391.7,
    399.8,
    414.0,
    426.8,
    439.0,
    451.5,
    464.0,
    474.3,
    489.0,
    501.2,
    513.5,
    526.3,
    538.5,
    551.0,
    564.5,
    576.5,
    588.3,
    602.0,
    613.5,
    626.5,
    639.0,
    651.0,
    663.5,
    677.0,
    688.8,
    701.0,
    714.0,
    725.5,
    739.5,
    751.0,
    762.8,
    776.3,
    789.0,
    803.5,
    813.7,
    826.3,
    838.7,
    851.8,
    864.7,
    876.3,
    888.7,
    900.8,
    912.5,
    927.3,
    940.5,
    951.3,
    963.7,
    975.8,
    988.2,
    1001.3,
]

PEPPER_WIDE_MIN_SPREAD = 11
PEPPER_WIDE_MIN_POS = 60
PEPPER_WIDE_RESID_LOW = -2.4
PEPPER_WIDE_RESID_HIGH = 1.8
PEPPER_WIDE_PROGRESS_START = 0.10
PEPPER_WIDE_PROGRESS_END = 0.93
PEPPER_WIDE_CARRY_LEFT = 90.0
PEPPER_MILD_RECYCLE_RESID = 3.4
PEPPER_MILD_RECYCLE_OFFSET = 4
PEPPER_FLOW_POSITIVE = 4.0
PEPPER_FLOW_NEGATIVE = -4.0
PEPPER_WIDE_BASE_BUY = 12
PEPPER_WIDE_BIG_BUY = 20
PEPPER_WIDE_BASE_SELL = 4
PEPPER_WIDE_BIG_SELL = 8
PEPPER_WIDE_LOW_POS = 66


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
    progress = clamp(progress, 0.0, 1.0)
    scaled = progress * (len(PEPPER_TEMPLATE_OFFSETS) - 1)
    lo = int(math.floor(scaled))
    hi = min(len(PEPPER_TEMPLATE_OFFSETS) - 1, lo + 1)
    frac = scaled - lo
    return PEPPER_TEMPLATE_OFFSETS[lo] + frac * (
        PEPPER_TEMPLATE_OFFSETS[hi] - PEPPER_TEMPLATE_OFFSETS[lo]
    )


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
    anchor_pull = clamp(ASH_ANCHOR - book_mid, -4.0, 4.0)
    micro_bias = clamp(current_micro - current_mid, -1.5, 1.5)
    fade_bias = clamp(-0.45 * ret1, -1.5, 1.5)

    anchored_fair = ASH_ANCHOR + 0.65 * anchor_dev + 0.25 * micro_bias + 0.35 * fade_bias
    dynamic_fair = (
        0.72 * book_mid
        + 0.28 * ASH_ANCHOR
        + 0.30 * anchor_pull
        + 0.25 * micro_bias
        + 0.25 * fade_bias
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

    long_cap = 80
    short_cap = 80
    progress = clamp(timestamp / 999900.0, 0.0, 1.0)
    soft_cap = 20 if progress < 0.18 else 12

    anchor_gap = abs(current_mid - ASH_ANCHOR)
    take_edge = 1.75 if not shock else 1.25
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

    if position > 28:
        base_ask -= 1
    elif position < -28:
        base_bid += 1

    buy_prices = [base_bid, base_bid - deep_step]
    sell_prices = [base_ask, base_ask + deep_step]
    if spread >= 21:
        buy_sizes = [18, 16] if not shock else [13, 12]
        sell_sizes = [18, 16] if not shock else [13, 12]
    elif spread >= 19:
        buy_sizes = [16, 15] if not shock else [12, 11]
        sell_sizes = [16, 15] if not shock else [12, 11]
    elif spread >= 18:
        buy_sizes = [14, 12] if not shock else [11, 9]
        sell_sizes = [14, 12] if not shock else [11, 9]
    else:
        buy_sizes = [12, 8] if not shock else [9, 6]
        sell_sizes = [12, 8] if not shock else [9, 6]

    if prefer_inside_buy:
        buy_sizes[0] += 1

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
        if price in seen or (ask is not None and price >= ask) or fair - price < 1.0:
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
        if price in seen or (bid is not None and price <= bid) or price - fair < 1.0:
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

    progress = clamp(timestamp / 999900.0, 0.0, 1.0)
    template_fair = float(pepper_state.get("open_mid", current_mid)) + interp_template_offset(progress)
    close_estimate = float(pepper_state.get("open_mid", current_mid)) + PEPPER_TEMPLATE_OFFSETS[-1]

    micro_bias = clamp((current_micro - current_mid) * 0.35, -1.0, 1.0)
    book_fair = current_mm + 0.20 * micro_bias
    residual = current_mid - template_fair
    flow_bias = clamp(trade_ema / 18.0, -0.7, 0.7)
    fair = max(template_fair - 0.35 + 0.10 * max(flow_bias, 0.0), book_fair, fallback - 0.12)

    pepper_state["last_mid"] = current_mid
    pepper_state["trade_ema"] = trade_ema

    if progress < 0.020 and residual < 2.5:
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
        "progress": progress,
        "carry_left": max(0.0, close_estimate - current_mid),
        "trade_ema": trade_ema,
        "flow_now": float(flow_now),
    }
    return fair, mode, pepper_state, diagnostics


def pepper_caps_and_edges(mode: str) -> Dict[str, float]:
    if mode == "opening":
        return {
            "long_cap": 80,
            "short_cap": 4,
            "target_long": 78,
            "buy_edge": 1.2,
            "sell_edge": 8.0,
            "sweep_pad": 8.5,
            "bid_edge": 1.6,
            "ask_edge": 8.5,
            "bid_size": 18,
            "ask_size": 1,
        }
    if mode == "discount":
        return {
            "long_cap": 80,
            "short_cap": 4,
            "target_long": 80,
            "buy_edge": 1.0,
            "sell_edge": 8.5,
            "sweep_pad": 7.0,
            "bid_edge": 1.4,
            "ask_edge": 8.5,
            "bid_size": 16,
            "ask_size": 1,
        }
    if mode == "overheated":
        return {
            "long_cap": 78,
            "short_cap": 10,
            "target_long": 76,
            "buy_edge": 2.4,
            "sell_edge": 5.0,
            "sweep_pad": 2.0,
            "bid_edge": 2.8,
            "ask_edge": 6.2,
            "bid_size": 10,
            "ask_size": 2,
        }
    return {
        "long_cap": 78,
        "short_cap": 6,
        "target_long": 78,
        "buy_edge": 1.6,
        "sell_edge": 8.0,
        "sweep_pad": 3.2,
        "bid_edge": 2.0,
        "ask_edge": 8.0,
        "bid_size": 14,
        "ask_size": 1,
    }


def trade_pepper(
    depth: OrderDepth,
    position: int,
    pepper_state: Dict[str, float],
    market_trades: List[Trade],
    timestamp: int,
) -> Tuple[List[Order], Dict[str, float]]:
    fair, mode, pepper_state, diagnostics = pepper_state_and_fair(
        depth,
        pepper_state,
        market_trades,
        timestamp,
    )
    cfg = pepper_caps_and_edges(mode)
    residual = diagnostics["residual"]
    progress = diagnostics["progress"]
    carry_left = diagnostics["carry_left"]
    template_fair = diagnostics["template"]
    trade_ema = diagnostics["trade_ema"]
    buyflow = trade_ema >= 6.0
    sellflow = trade_ema <= -6.0

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

    # New monetization layer: when Pepper is already full and moderately overheated,
    # the local data support recycling inventory rather than only waiting for the
    # coarse overheated mode. Make this most aggressive in the middle of the session,
    # when the observed recycle edge is strongest.
    recycle_mode = (
        position >= 76
        and 4.0 <= residual < 6.5
        and 0.08 <= progress <= 0.92
        and not buyflow
    )
    strong_recycle = recycle_mode and (0.33 <= progress <= 0.75 or carry_left < 220.0)
    if recycle_mode:
        if 0.33 <= progress <= 0.75:
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

    soft_cap = max(44, target_long - 2)

    buy_budget = max(0, min(LIMITS[PEPPER], long_cap) - position)
    sell_budget = max(0, position + min(LIMITS[PEPPER], short_cap))
    temp_position = position
    orders: List[Order] = []

    sweep_ceiling = diagnostics["template"] + sweep_pad
    for ask in sorted(depth.sell_orders):
        buy_ceiling = fair - buy_edge
        if temp_position < target_long:
            buy_ceiling = max(buy_ceiling, sweep_ceiling)
        if ask > buy_ceiling:
            break
        before = buy_budget
        buy_budget = add_buy(orders, PEPPER, ask, -depth.sell_orders[ask], buy_budget)
        temp_position += before - buy_budget

    recycle_trigger = 3.8 if 0.33 <= progress <= 0.75 else 4.1
    if carry_left < 220.0:
        recycle_trigger -= 0.3
    mild_recycle = (
        temp_position >= 70
        and 0.12 <= progress <= 0.92
        and residual >= PEPPER_MILD_RECYCLE_RESID
        and not (buyflow and carry_left < 160.0)
    )
    recycle_floor = max(70, target_long - PEPPER_MILD_RECYCLE_OFFSET) if mild_recycle else target_long
    for bid in sorted(depth.buy_orders, reverse=True):
        sell_threshold = fair + sell_edge
        if strong_recycle:
            sell_threshold = min(sell_threshold, template_fair + recycle_trigger)
        elif mild_recycle:
            sell_threshold = min(sell_threshold, template_fair + recycle_trigger + 0.2)
        if temp_position <= recycle_floor or bid < sell_threshold:
            break
        before = sell_budget
        sell_budget = add_sell(orders, PEPPER, bid, depth.buy_orders[bid], sell_budget)
        temp_position -= before - sell_budget

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

    bid = best_bid(depth)
    ask = best_ask(depth)
    spread = (ask - bid) if bid is not None and ask is not None else 0
    skew = clamp((temp_position - target_long) * 0.03, -1.5, 1.5)
    if residual < -2.0:
        skew -= 0.6
    elif residual > 5.0:
        skew += 0.8
    if buyflow:
        skew -= 0.3
    elif sellflow:
        skew += 0.3

    quote_fair = fair - skew
    if strong_recycle:
        quote_fair = min(quote_fair, template_fair + 1.1)
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
    wide_carry_mode = (
        bid is not None
        and ask is not None
        and spread >= PEPPER_WIDE_MIN_SPREAD
        and PEPPER_WIDE_PROGRESS_START <= progress <= PEPPER_WIDE_PROGRESS_END
        and carry_left >= PEPPER_WIDE_CARRY_LEFT
        and PEPPER_WIDE_RESID_LOW <= residual <= PEPPER_WIDE_RESID_HIGH
        and temp_position >= PEPPER_WIDE_MIN_POS
    )
    if wide_carry_mode:
        buy_prices[0] = bid + 1
        sell_prices[0] = ask - 1
        if trade_ema >= PEPPER_FLOW_POSITIVE:
            buy_sizes[0] = max(
                buy_sizes[0],
                PEPPER_WIDE_BIG_BUY if temp_position <= 72 else PEPPER_WIDE_BASE_BUY,
            )
            sell_sizes[0] = max(sell_sizes[0], PEPPER_WIDE_BIG_SELL)
        elif trade_ema <= PEPPER_FLOW_NEGATIVE:
            buy_sizes[0] = max(
                buy_sizes[0],
                PEPPER_WIDE_BASE_BUY if temp_position <= 72 else max(8, PEPPER_WIDE_BASE_BUY - 4),
            )
            sell_sizes[0] = max(
                sell_sizes[0],
                PEPPER_WIDE_BASE_SELL if temp_position < 74 else PEPPER_WIDE_BIG_SELL,
            )
        else:
            buy_sizes[0] = max(
                buy_sizes[0],
                PEPPER_WIDE_BASE_BUY if temp_position <= 72 else max(8, PEPPER_WIDE_BASE_BUY - 4),
            )
            sell_sizes[0] = max(
                sell_sizes[0],
                PEPPER_WIDE_BASE_SELL if temp_position < 74 else PEPPER_WIDE_BIG_SELL,
            )
        if temp_position <= PEPPER_WIDE_LOW_POS and carry_left >= 180.0:
            buy_sizes[0] = max(buy_sizes[0], max(PEPPER_WIDE_BASE_BUY, 16))
        if temp_position >= 76:
            sell_sizes[0] = max(sell_sizes[0], PEPPER_WIDE_BIG_SELL)

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

    if (
        temp_position > target_long
        or recycle_mode
        or mild_recycle
        or wide_carry_mode
        or (mode == "overheated" and not buyflow)
        or sellflow
    ):
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

        trader_data = json.dumps(
            {
                "ash": ash_state,
                "pepper": pepper_state,
            }
        )
        return result, 0, trader_data
