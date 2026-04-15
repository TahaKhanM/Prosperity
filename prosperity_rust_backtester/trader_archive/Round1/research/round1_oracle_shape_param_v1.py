import importlib.util
import json
import os
from pathlib import Path
from typing import Dict, List


BASE = (
    Path(__file__).resolve().parents[3]
    / "traders"
    / "Round1"
    / "active"
    / "round1_overhaul_v63.py"
)
spec = importlib.util.spec_from_file_location("base_v63", BASE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

Order = base.Order
ASH = base.ASH
PEPPER = base.PEPPER
LIMITS = base.LIMITS
clamp = base.clamp
best_bid = base.best_bid
best_ask = base.best_ask
add_buy = base.add_buy
add_sell = base.add_sell
trade_ash = base.trade_ash
ash_fair_and_state = base.ash_fair_and_state
pepper_state_and_fair = base.pepper_state_and_fair
pepper_caps_and_edges = base.pepper_caps_and_edges


def env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


PEPPER_EXTRA_BUY_RESID_MAX = env_float("PEPPER_EXTRA_BUY_RESID_MAX", -99.0)
PEPPER_EXTRA_BUY_POS_MAX = env_int("PEPPER_EXTRA_BUY_POS_MAX", -1)
PEPPER_EXTRA_BUY_SPREAD_MAX = env_int("PEPPER_EXTRA_BUY_SPREAD_MAX", 0)
PEPPER_EXTRA_BUY_QTY = env_int("PEPPER_EXTRA_BUY_QTY", 0)
PEPPER_EXTRA_BUY_PAD = env_float("PEPPER_EXTRA_BUY_PAD", 0.0)

PEPPER_EXTRA_RECYCLE_RESID_MIN = env_float("PEPPER_EXTRA_RECYCLE_RESID_MIN", 99.0)
PEPPER_EXTRA_RECYCLE_POS_MIN = env_int("PEPPER_EXTRA_RECYCLE_POS_MIN", 999)
PEPPER_EXTRA_RECYCLE_MKT_QTY_MIN = env_float("PEPPER_EXTRA_RECYCLE_MKT_QTY_MIN", 999.0)
PEPPER_EXTRA_RECYCLE_TAKE_QTY = env_int("PEPPER_EXTRA_RECYCLE_TAKE_QTY", 0)
PEPPER_EXTRA_RECYCLE_INSIDE_QTY = env_int("PEPPER_EXTRA_RECYCLE_INSIDE_QTY", 0)
PEPPER_EXTRA_RECYCLE_TARGET_SHIFT = env_int("PEPPER_EXTRA_RECYCLE_TARGET_SHIFT", 0)
PEPPER_EXTRA_RECYCLE_PAD = env_float("PEPPER_EXTRA_RECYCLE_PAD", 0.0)


def trade_pepper(
    depth,
    position: int,
    pepper_state: Dict[str, float],
    market_trades,
    timestamp: int,
):
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
    market_trade_qty = sum(int(trade.quantity) for trade in market_trades)
    market_trade_count = len(market_trades)
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

    extra_recycle_mode = (
        position >= PEPPER_EXTRA_RECYCLE_POS_MIN
        and residual >= PEPPER_EXTRA_RECYCLE_RESID_MIN
        and market_trade_qty >= PEPPER_EXTRA_RECYCLE_MKT_QTY_MIN
    )
    if extra_recycle_mode:
        target_long = max(0, target_long - PEPPER_EXTRA_RECYCLE_TARGET_SHIFT)
        sell_edge = max(1.0, min(sell_edge, PEPPER_EXTRA_RECYCLE_PAD))
        ask_edge = max(1.0, min(ask_edge, PEPPER_EXTRA_RECYCLE_PAD + 1.5))
        bid_size = max(4, bid_size - 2)

    buy_budget = max(0, min(LIMITS[PEPPER], long_cap) - position)
    sell_budget = max(0, position + min(LIMITS[PEPPER], short_cap))
    temp_position = position
    orders: List[Order] = []

    bid = best_bid(depth)
    ask = best_ask(depth)
    spread = (ask - bid) if bid is not None and ask is not None else 99

    extra_buy_mode = (
        PEPPER_EXTRA_BUY_QTY > 0
        and position <= PEPPER_EXTRA_BUY_POS_MAX
        and residual <= PEPPER_EXTRA_BUY_RESID_MAX
        and spread <= PEPPER_EXTRA_BUY_SPREAD_MAX
        and ask is not None
        and ask <= template_fair + PEPPER_EXTRA_BUY_PAD
    )
    if extra_buy_mode:
        before = buy_budget
        buy_budget = add_buy(orders, PEPPER, ask, PEPPER_EXTRA_BUY_QTY, buy_budget)
        temp_position += before - buy_budget

    if extra_recycle_mode and bid is not None and PEPPER_EXTRA_RECYCLE_TAKE_QTY > 0:
        before = sell_budget
        sell_budget = add_sell(orders, PEPPER, bid, PEPPER_EXTRA_RECYCLE_TAKE_QTY, sell_budget)
        temp_position -= before - sell_budget

    if (
        extra_recycle_mode
        and ask is not None
        and bid is not None
        and ask - bid > 1
        and PEPPER_EXTRA_RECYCLE_INSIDE_QTY > 0
    ):
        before = sell_budget
        sell_budget = add_sell(
            orders,
            PEPPER,
            ask - 1,
            PEPPER_EXTRA_RECYCLE_INSIDE_QTY,
            sell_budget,
        )
        temp_position -= before - sell_budget

    sweep_ceiling = diagnostics["template"] + sweep_pad
    for ask_price in sorted(depth.sell_orders):
        buy_ceiling = fair - buy_edge
        if temp_position < target_long:
            buy_ceiling = max(buy_ceiling, sweep_ceiling)
        if ask_price > buy_ceiling:
            break
        before = buy_budget
        buy_budget = add_buy(orders, PEPPER, ask_price, -depth.sell_orders[ask_price], buy_budget)
        temp_position += before - buy_budget

    recycle_trigger = 3.8 if 0.33 <= progress <= 0.75 else 4.1
    if carry_left < 220.0:
        recycle_trigger -= 0.3
    if extra_recycle_mode:
        recycle_trigger = min(recycle_trigger, PEPPER_EXTRA_RECYCLE_PAD)
    for bid_price in sorted(depth.buy_orders, reverse=True):
        sell_threshold = fair + sell_edge
        if strong_recycle:
            sell_threshold = min(sell_threshold, template_fair + recycle_trigger)
        if extra_recycle_mode:
            sell_threshold = min(sell_threshold, template_fair + recycle_trigger)
        if temp_position <= target_long or bid_price < sell_threshold:
            break
        before = sell_budget
        sell_budget = add_sell(orders, PEPPER, bid_price, depth.buy_orders[bid_price], sell_budget)
        temp_position -= before - sell_budget

    clear_edge = 0.35
    if temp_position > long_cap:
        for bid_price in sorted(depth.buy_orders, reverse=True):
            if bid_price < fair - clear_edge:
                break
            before = sell_budget
            sell_budget = add_sell(orders, PEPPER, bid_price, depth.buy_orders[bid_price], sell_budget)
            temp_position -= before - sell_budget
            if temp_position <= long_cap:
                break

    if temp_position < -short_cap + 8:
        for ask_price in sorted(depth.sell_orders):
            if ask_price > fair + clear_edge:
                break
            before = buy_budget
            buy_budget = add_buy(orders, PEPPER, ask_price, -depth.sell_orders[ask_price], buy_budget)
            temp_position += before - buy_budget
            if temp_position >= -short_cap + 8:
                break

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
        int(quote_fair - bid_edge),
        int(quote_fair - (bid_edge + 1.8)),
    ]
    sell_prices = [
        int(quote_fair + ask_edge + 0.9999),
        int(quote_fair + (ask_edge + 1.8) + 0.9999),
    ]
    buy_sizes = [bid_size, max(3, bid_size - 3)]
    sell_sizes = [ask_size, max(2, ask_size - 2)]

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

    if temp_position > target_long or recycle_mode or extra_recycle_mode or (mode == "overheated" and not buyflow) or sellflow:
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
    def run(self, state):
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
