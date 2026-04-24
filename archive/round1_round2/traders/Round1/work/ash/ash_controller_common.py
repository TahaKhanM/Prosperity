import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import datamodel as datamodel_module
from datamodel import Order, OrderDepth, TradingState


ASH = "ASH_COATED_OSMIUM"
PEPPER = "INTARIAN_PEPPER_ROOT"
ASH_ANCHOR = 10000.0
LIMITS = {
    ASH: 80,
    PEPPER: 80,
}

_BASELINE_MODULE = None


def baseline_module():
    global _BASELINE_MODULE
    if _BASELINE_MODULE is None:
        baseline_path = Path(__file__).resolve().parents[2] / "Ash.py"
        sys.modules.setdefault("datamodel", datamodel_module)
        spec = importlib.util.spec_from_file_location("_ash_baseline_module", baseline_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"unable to load baseline trader from {baseline_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _BASELINE_MODULE = module
    return _BASELINE_MODULE


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
    bid_volume = int(depth.buy_orders[bid])
    ask_volume = int(-depth.sell_orders[ask])
    total = bid_volume + ask_volume
    if total <= 0:
        return (bid + ask) / 2.0
    return (bid * ask_volume + ask * bid_volume) / total


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


def add_buy(
    orders: List[Order],
    price: int,
    quantity: int,
    budget: int,
) -> int:
    size = min(quantity, budget)
    if size > 0:
        orders.append(Order(ASH, int(price), int(size)))
        budget -= size
    return budget


def add_sell(
    orders: List[Order],
    price: int,
    quantity: int,
    budget: int,
) -> int:
    size = min(quantity, budget)
    if size > 0:
        orders.append(Order(ASH, int(price), -int(size)))
        budget -= size
    return budget


def _decay_runs(
    positive: bool,
    negative: bool,
    positive_run: int,
    negative_run: int,
) -> Tuple[int, int]:
    if positive and not negative:
        return min(4, positive_run + 1), max(0, negative_run - 1)
    if negative and not positive:
        return max(0, positive_run - 1), min(4, negative_run + 1)
    return max(0, positive_run - 1), max(0, negative_run - 1)


def ash_fair_context(
    depth: OrderDepth,
    ash_state: Dict[str, float],
) -> Tuple[float, Dict[str, float], Dict[str, float]]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    book_mid = mm10_mid(depth) or wall_mid(depth) or simple_mid(depth) or ASH_ANCHOR
    current_mid = simple_mid(depth) or book_mid
    current_micro = microprice(depth) or current_mid

    top_bid_volume = int(depth.buy_orders[bid]) if bid is not None else 0
    top_ask_volume = int(-depth.sell_orders[ask]) if ask is not None else 0
    top_total = top_bid_volume + top_ask_volume
    top_imbalance = (top_bid_volume - top_ask_volume) / top_total if top_total > 0 else 0.0

    last_mid = float(ash_state.get("last_mid", current_mid))
    ret1 = current_mid - last_mid
    anchor_dev = clamp(book_mid - ASH_ANCHOR, -8.0, 8.0)
    micro_gap = clamp(current_micro - current_mid, -4.0, 4.0)
    shock = abs(anchor_dev) >= 6.0 or abs(ret1) >= 3.5

    prev_bid = ash_state.get("prev_bid")
    prev_ask = ash_state.get("prev_ask")
    move_bias = 0
    if prev_bid is not None and bid is not None:
        if bid > int(prev_bid):
            move_bias += 1
        elif bid < int(prev_bid):
            move_bias -= 1
    if prev_ask is not None and ask is not None:
        if ask > int(prev_ask):
            move_bias += 1
        elif ask < int(prev_ask):
            move_bias -= 1

    buy_signal = top_imbalance >= 0.20 and micro_gap >= 0.10
    sell_signal = top_imbalance <= -0.20 and micro_gap <= -0.10
    if anchor_dev <= -3.5 and top_imbalance >= 0.10:
        buy_signal = True
    if anchor_dev >= 3.5 and top_imbalance <= -0.10:
        sell_signal = True

    buy_run, sell_run = _decay_runs(
        buy_signal,
        sell_signal,
        int(ash_state.get("buy_run", 0)),
        int(ash_state.get("sell_run", 0)),
    )
    up_run, down_run = _decay_runs(
        move_bias > 0,
        move_bias < 0,
        int(ash_state.get("up_run", 0)),
        int(ash_state.get("down_run", 0)),
    )

    direction_pressure = clamp(
        0.55 * top_imbalance
        + 0.25 * clamp(micro_gap / 2.5, -1.0, 1.0)
        + 0.10 * (buy_run - sell_run)
        + 0.06 * (up_run - down_run),
        -1.6,
        1.6,
    )

    anchor_pull = clamp(ASH_ANCHOR - book_mid, -5.0, 5.0)
    micro_bias = clamp(current_micro - current_mid, -1.5, 1.5)
    fade_bias = clamp(-0.35 * ret1, -1.5, 1.5)
    anchored_fair = ASH_ANCHOR + 0.55 * clamp(anchor_dev, -4.0, 4.0) + 0.22 * micro_bias + 0.22 * fade_bias
    dynamic_fair = (
        0.70 * book_mid
        + 0.30 * ASH_ANCHOR
        + 0.22 * anchor_pull
        + 0.25 * micro_bias
        + 0.18 * fade_bias
    )
    fair = 0.42 * anchored_fair + 0.58 * dynamic_fair

    ash_state["last_mid"] = current_mid
    ash_state["prev_bid"] = float(bid) if bid is not None else ash_state.get("prev_bid", 0.0)
    ash_state["prev_ask"] = float(ask) if ask is not None else ash_state.get("prev_ask", 0.0)
    ash_state["buy_run"] = float(buy_run)
    ash_state["sell_run"] = float(sell_run)
    ash_state["up_run"] = float(up_run)
    ash_state["down_run"] = float(down_run)
    ash_state["last_fair"] = fair

    ctx = {
        "bid": bid,
        "ask": ask,
        "spread": (ask - bid) if bid is not None and ask is not None else 99,
        "book_mid": book_mid,
        "mid": current_mid,
        "micro": current_micro,
        "anchor_dev": anchor_dev,
        "micro_gap": micro_gap,
        "top_bid_volume": top_bid_volume,
        "top_ask_volume": top_ask_volume,
        "top_imbalance": top_imbalance,
        "pressure": direction_pressure,
        "buy_run": buy_run,
        "sell_run": sell_run,
        "up_run": up_run,
        "down_run": down_run,
        "ret1": ret1,
        "shock": shock,
        "bid_only": bid is not None and ask is None,
        "ask_only": ask is not None and bid is None,
    }
    return fair, ash_state, ctx


def step_in_buy_price(depth: OrderDepth) -> Optional[int]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None:
        return None
    candidate = bid + 1
    if ask is not None and candidate >= ask:
        return None
    return candidate


def step_in_sell_price(depth: OrderDepth) -> Optional[int]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if ask is None:
        return None
    candidate = ask - 1
    if bid is not None and candidate <= bid:
        return None
    return candidate


def passive_buy_price(
    depth: OrderDepth,
    fair: float,
    min_edge: float,
    *,
    promote: bool,
) -> Optional[int]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    stepped = step_in_buy_price(depth)
    if stepped is not None and fair - stepped >= min_edge:
        if ask is None or promote or bid is None or ask - bid >= 2:
            return stepped

    candidate = math.floor(fair - max(min_edge, 1.0))
    if ask is not None and candidate >= ask:
        candidate = ask - 1
    if bid is not None:
        if ask is None:
            if promote and fair - (bid + 1) >= min_edge:
                candidate = bid + 1
            elif candidate <= bid:
                candidate = bid - 1
        elif candidate <= bid:
            candidate = bid - 1
    return candidate if fair - candidate >= max(0.6, min_edge * 0.5) else None


def passive_sell_price(
    depth: OrderDepth,
    fair: float,
    min_edge: float,
    *,
    promote: bool,
) -> Optional[int]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    stepped = step_in_sell_price(depth)
    if stepped is not None and stepped - fair >= min_edge:
        if bid is None or promote or ask is None or ask - bid >= 2:
            return stepped

    candidate = math.ceil(fair + max(min_edge, 1.0))
    if bid is not None and candidate <= bid:
        candidate = bid + 1
    if ask is not None:
        if bid is None:
            if promote and (ask - 1) - fair >= min_edge:
                candidate = ask - 1
            elif candidate >= ask:
                candidate = ask + 1
        elif candidate >= ask:
            candidate = ask + 1
    return candidate if candidate - fair >= max(0.6, min_edge * 0.5) else None


def post_passive_buy(
    orders: List[Order],
    depth: OrderDepth,
    fair: float,
    budget: int,
    size: int,
    *,
    min_edge: float = 1.0,
    promote: bool = False,
) -> int:
    price = passive_buy_price(depth, fair, min_edge, promote=promote)
    if price is None:
        return budget
    return add_buy(orders, price, size, budget)


def post_passive_sell(
    orders: List[Order],
    depth: OrderDepth,
    fair: float,
    budget: int,
    size: int,
    *,
    min_edge: float = 1.0,
    promote: bool = False,
) -> int:
    price = passive_sell_price(depth, fair, min_edge, promote=promote)
    if price is None:
        return budget
    return add_sell(orders, price, size, budget)


def post_cross_buy(
    orders: List[Order],
    depth: OrderDepth,
    fair: float,
    budget: int,
    max_size: int,
    *,
    edge: float,
) -> Tuple[int, int]:
    ask = best_ask(depth)
    if ask is None or fair - ask < edge:
        return budget, 0
    size = min(max_size, int(-depth.sell_orders[ask]))
    before = budget
    budget = add_buy(orders, ask, size, budget)
    return budget, before - budget


def post_cross_sell(
    orders: List[Order],
    depth: OrderDepth,
    fair: float,
    budget: int,
    max_size: int,
    *,
    edge: float,
) -> Tuple[int, int]:
    bid = best_bid(depth)
    if bid is None or bid - fair < edge:
        return budget, 0
    size = min(max_size, int(depth.buy_orders[bid]))
    before = budget
    budget = add_sell(orders, bid, size, budget)
    return budget, before - budget


def size_for_side(base: int, position: int, side: str) -> int:
    size = base
    if side == "buy":
        if position >= 60:
            size -= 8
        elif position >= 40:
            size -= 4
    else:
        if position <= -60:
            size -= 8
        elif position <= -40:
            size -= 4
    return max(3, size)


def run_variant(
    state: TradingState,
    ash_trade_fn: Callable[[OrderDepth, int, Dict[str, float], int], Tuple[List[Order], Dict[str, float]]],
):
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
        result[ASH], ash_state = ash_trade_fn(
            state.order_depths[ASH],
            int(state.position.get(ASH, 0)),
            ash_state,
            int(state.timestamp),
        )

    if PEPPER in state.order_depths:
        baseline = baseline_module()
        result[PEPPER], pepper_state = baseline.trade_pepper(
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
