import importlib.util
from pathlib import Path
from typing import Dict, List


BASE = (
    Path(__file__).resolve().parents[3]
    / "traders"
    / "Round1"
    / "work"
    / "pepper_carry"
    / "unvalidated"
    / "round1_pepper_dual_carry_v13.py"
)
spec = importlib.util.spec_from_file_location("base_v13", BASE)
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(base)


ASH = base.ASH
PEPPER = base.PEPPER
LIMITS = base.LIMITS
Order = base.Order

clamp = base.clamp
best_bid = base.best_bid
best_ask = base.best_ask
add_buy = base.add_buy
add_sell = base.add_sell
trade_ash = base.trade_ash
pepper_state_and_fair = base.pepper_state_and_fair
pepper_caps_and_edges = base.pepper_caps_and_edges


def trade_pepper(depth, position: int, pepper_state: Dict[str, float], market_trades, timestamp: int):
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
    bid = best_bid(depth)
    ask = best_ask(depth)
    spread = (ask - bid) if bid is not None and ask is not None else 0
    top_imbalance = 0.0
    if bid is not None and ask is not None:
        bid_volume = int(depth.buy_orders[bid])
        ask_volume = int(-depth.sell_orders[ask])
        total_top = bid_volume + ask_volume
        if total_top > 0:
            top_imbalance = (bid_volume - ask_volume) / total_top

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

    carry_buy_pressure = (
        spread >= base.PEPPER_WIDE_MIN_SPREAD
        and base.PEPPER_WIDE_PROGRESS_START <= progress <= base.PEPPER_WIDE_PROGRESS_END
        and carry_left >= base.PEPPER_WIDE_CARRY_LEFT
        and base.PEPPER_WIDE_RESID_LOW <= residual <= base.PEPPER_WIDE_RESID_HIGH
        and position >= base.PEPPER_WIDE_MIN_POS
        and top_imbalance >= base.PEPPER_BOOK_LEAN_POSITIVE
    )
    carry_sell_pressure = (
        spread >= base.PEPPER_WIDE_MIN_SPREAD
        and base.PEPPER_WIDE_PROGRESS_START <= progress <= base.PEPPER_WIDE_PROGRESS_END
        and position >= 70
        and top_imbalance <= base.PEPPER_BOOK_LEAN_NEGATIVE
        and (
            base.PEPPER_WIDE_RESID_LOW <= residual <= base.PEPPER_WIDE_RESID_HIGH
            or residual >= 2.0
        )
    )

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

    if carry_buy_pressure:
        long_cap = LIMITS[PEPPER]
        target_long = max(target_long, 80)
        buy_edge = max(0.7, buy_edge - 0.45)
        sweep_pad += 0.6
        bid_edge = max(0.9, bid_edge - 0.35)
        bid_size += 3
        if not sellflow:
            ask_size = max(1, ask_size - 1)
    elif carry_sell_pressure and not buyflow:
        target_long = max(72, target_long - (6 if residual >= 2.0 else 3))
        buy_edge += 0.25
        sweep_pad = max(1.8, sweep_pad - 0.6)
        sell_edge = max(3.2, sell_edge - 0.8)
        ask_edge = max(4.5, ask_edge - 0.75)
        bid_size = max(6, bid_size - 3)
        ask_size += 3

    aggressive_recycle_mode = (
        position >= 68
        and 0.18 <= progress <= 0.92
        and residual >= 1.5
        and top_imbalance <= -0.15
        and not buyflow
        and spread >= 11
    )
    if aggressive_recycle_mode:
        target_long = max(72, target_long - (5 if residual >= 2.6 else 3))
        buy_edge += 0.10
        sweep_pad = max(1.7, sweep_pad - 0.5)
        sell_edge = max(2.6, sell_edge - 1.1)
        ask_edge = max(3.8, ask_edge - 1.0)
        bid_size = max(6, bid_size - 2)
        ask_size += 3

    exact_buy_mode = (
        position <= 72
        and 0.05 <= progress <= 0.92
        and residual <= -4.2
        and top_imbalance >= 0.15
    )
    if exact_buy_mode:
        long_cap = LIMITS[PEPPER]
        target_long = 80
        buy_edge = max(0.65, buy_edge - 0.35)
        sweep_pad += 1.0
        bid_edge = max(0.9, bid_edge - 0.25)
        bid_size += 3 if spread >= 7 else 5
        if not sellflow:
            ask_size = max(1, ask_size - 1)

    exact_sell_mode = (
        position >= 72
        and 0.10 <= progress <= 0.95
        and residual >= 3.8
        and top_imbalance <= -0.15
        and not buyflow
    )
    if exact_sell_mode:
        target_long = max(72, target_long - (4 if spread <= 7 else 2))
        buy_edge += 0.15
        sell_edge = max(2.8, sell_edge - 0.9)
        sweep_pad = max(1.8, sweep_pad - 0.5)
        ask_edge = max(4.0, ask_edge - 0.8)
        bid_size = max(6, bid_size - 2)
        ask_size += 3

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
        sell_edge = max(3.4, sell_edge - 1.1)
        sweep_pad = max(1.5, sweep_pad - 0.8)
        bid_edge += 0.2
        ask_edge = max(4.8, ask_edge - 0.8)
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
        sell_edge = max(3.2, sell_edge - 0.4)
        ask_size += 1

    buy_budget = max(0, min(LIMITS[PEPPER], long_cap) - position)
    sell_budget = max(0, position + min(LIMITS[PEPPER], short_cap))
    temp_position = position
    orders: List[Order] = []

    sweep_ceiling = diagnostics["template"] + sweep_pad
    best_ask_level = best_ask(depth)
    if best_ask_level is not None:
        buy_ceiling = fair - buy_edge
        if temp_position < target_long:
            buy_ceiling = max(buy_ceiling, sweep_ceiling)
        if best_ask_level <= buy_ceiling:
            before = buy_budget
            buy_budget = add_buy(
                orders,
                PEPPER,
                best_ask_level,
                -depth.sell_orders[best_ask_level],
                buy_budget,
            )
            temp_position += before - buy_budget

    recycle_trigger = 3.8 if 0.33 <= progress <= 0.75 else 4.1
    if carry_left < 220.0:
        recycle_trigger -= 0.3
    mild_recycle_resid = base.PEPPER_MILD_RECYCLE_RESID
    if carry_sell_pressure and not buyflow:
        mild_recycle_resid -= base.PEPPER_LEANED_RECYCLE_SHIFT
    mild_recycle = (
        temp_position >= 70
        and 0.12 <= progress <= 0.92
        and residual >= mild_recycle_resid
        and not (buyflow and carry_left < 160.0)
    )
    recycle_floor = target_long
    if aggressive_recycle_mode:
        recycle_floor = max(72, target_long - 2)
    best_bid_level = best_bid(depth)
    if best_bid_level is not None:
        sell_threshold = fair + sell_edge
        if strong_recycle:
            sell_threshold = min(sell_threshold, template_fair + recycle_trigger)
        if aggressive_recycle_mode:
            aggressive_threshold = template_fair + (2.6 if residual < 2.8 else 3.0)
            if carry_left < 220.0:
                aggressive_threshold -= 0.2
            sell_threshold = min(sell_threshold, aggressive_threshold)
        if temp_position > recycle_floor and best_bid_level >= sell_threshold:
            before = sell_budget
            sell_budget = add_sell(
                orders,
                PEPPER,
                best_bid_level,
                depth.buy_orders[best_bid_level],
                sell_budget,
            )
            temp_position -= before - sell_budget

    clear_edge = 0.35
    if temp_position > long_cap:
        for bid_price in sorted(depth.buy_orders, reverse=True):
            if bid_price < fair - clear_edge:
                break
            before = sell_budget
            sell_budget = add_sell(
                orders,
                PEPPER,
                bid_price,
                depth.buy_orders[bid_price],
                sell_budget,
            )
            temp_position -= before - sell_budget
            if temp_position <= long_cap:
                break

    if temp_position < -short_cap + 8:
        for ask_price in sorted(depth.sell_orders):
            if ask_price > fair + clear_edge:
                break
            before = buy_budget
            buy_budget = add_buy(
                orders,
                PEPPER,
                ask_price,
                -depth.sell_orders[ask_price],
                buy_budget,
            )
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
        base.math.floor(quote_fair - bid_edge),
        base.math.floor(quote_fair - (bid_edge + 1.8)),
    ]
    sell_prices = [
        base.math.ceil(quote_fair + ask_edge),
        base.math.ceil(quote_fair + (ask_edge + 1.8)),
    ]
    buy_sizes = [bid_size, max(3, bid_size - 3)]
    sell_sizes = [ask_size, max(2, ask_size - 2)]
    wide_carry_mode = (
        bid is not None
        and ask is not None
        and spread >= base.PEPPER_WIDE_MIN_SPREAD
        and base.PEPPER_WIDE_PROGRESS_START <= progress <= base.PEPPER_WIDE_PROGRESS_END
        and carry_left >= base.PEPPER_WIDE_CARRY_LEFT
        and base.PEPPER_WIDE_RESID_LOW <= residual <= base.PEPPER_WIDE_RESID_HIGH
        and temp_position >= base.PEPPER_WIDE_MIN_POS
    )
    if wide_carry_mode:
        buy_prices[0] = bid + 1
        sell_prices[0] = ask - 1
        if trade_ema >= base.PEPPER_FLOW_POSITIVE:
            buy_sizes[0] = max(
                buy_sizes[0],
                base.PEPPER_WIDE_BIG_BUY if temp_position <= 72 else base.PEPPER_WIDE_BASE_BUY,
            )
            sell_sizes[0] = max(sell_sizes[0], base.PEPPER_WIDE_BIG_SELL)
        elif trade_ema <= base.PEPPER_FLOW_NEGATIVE:
            buy_sizes[0] = max(
                buy_sizes[0],
                base.PEPPER_WIDE_BASE_BUY
                if temp_position <= 72
                else max(8, base.PEPPER_WIDE_BASE_BUY - 4),
            )
            sell_sizes[0] = max(
                sell_sizes[0],
                base.PEPPER_WIDE_BASE_SELL if temp_position < 74 else base.PEPPER_WIDE_BIG_SELL,
            )
        else:
            buy_sizes[0] = max(
                buy_sizes[0],
                base.PEPPER_WIDE_BASE_BUY
                if temp_position <= 72
                else max(8, base.PEPPER_WIDE_BASE_BUY - 4),
            )
            sell_sizes[0] = max(
                sell_sizes[0],
                base.PEPPER_WIDE_BASE_SELL if temp_position < 74 else base.PEPPER_WIDE_BIG_SELL,
            )
        if temp_position <= base.PEPPER_WIDE_LOW_POS and carry_left >= 180.0:
            buy_sizes[0] = max(buy_sizes[0], max(base.PEPPER_WIDE_BASE_BUY, 16))
        if temp_position >= 76:
            sell_sizes[0] = max(sell_sizes[0], base.PEPPER_WIDE_BIG_SELL)
        if carry_buy_pressure:
            buy_sizes[0] = max(
                buy_sizes[0],
                16 if temp_position <= 72 else base.PEPPER_WIDE_BASE_BUY,
            )
            if not sellflow:
                sell_sizes[0] = max(1, min(sell_sizes[0], base.PEPPER_WIDE_BASE_SELL))
        elif carry_sell_pressure:
            buy_sizes[0] = max(6, buy_sizes[0] - 4)
            sell_sizes[0] = max(
                sell_sizes[0],
                base.PEPPER_WIDE_BIG_SELL
                if temp_position >= 76
                else base.PEPPER_WIDE_BASE_SELL + 2,
            )

    seen = set()
    buy_plan = list(zip(buy_prices, buy_sizes))[:1]
    for idx, (price, size) in enumerate(buy_plan):
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
        or aggressive_recycle_mode
        or (mode == "overheated" and not buyflow)
        or sellflow
    ):
        seen.clear()
        sell_plan = list(zip(sell_prices, sell_sizes))[:1]
        for idx, (price, size) in enumerate(sell_plan):
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
                decoded = base.json.loads(state.traderData)
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

        trader_data = base.json.dumps(
            {
                "ash": ash_state,
                "pepper": pepper_state,
            }
        )
        return result, 0, trader_data
