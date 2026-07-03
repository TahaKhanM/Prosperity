import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


# ============= BEGIN HELPERS FOR PEBBLES_XL (TREND-FILTERED) =======================
PEBBLES_XL = "PEBBLES_XL"

LIMITS = {
    PEBBLES_XL: 10,
}

LOOKBACK = 200
ENTRY_Z = 1.4
EXIT_Z = 0.35
TAKE_EDGE = 2.0
MAX_TAKE_SIZE = 4
PASSIVE_SIZE = 3

# Trend filter parameters.
# DAY_DRIFT_BLOCK_SIGMA: if same-day drift exceeds this many standard deviations
#   of one-tick returns (scaled by sqrt(elapsed ticks)), block entries that lean
#   into the trend. The day-4 blowup had a same-day drift of ~+10% which is
#   tens of sigmas; even a conservative threshold of 3 will gate this regime.
DAY_DRIFT_BLOCK_SIGMA = 3.0
# EXTREME_LOOKBACK: don't enter on a side where the current mid is at the
#   N-tick rolling extreme — i.e. don't short into a fresh high, don't long
#   into a fresh low.
EXTREME_LOOKBACK = 500
# Hard per-position stop. If the unrealised loss on the current position
# exceeds this many seashells per unit, flatten regardless of z-score.
STOP_LOSS_PER_UNIT = 12.0


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


def trade_pebbles_xl_trendfiltered(
    depth: OrderDepth,
    position: int,
    timestamp: int,
    avg_entry_price: Optional[float],
    px_state: Dict[str, object],
) -> Tuple[List[Order], Dict[str, object], Optional[float]]:
    orders: List[Order] = []

    bid = best_bid(depth)
    ask = best_ask(depth)
    mid = simple_mid(depth)
    if bid is None or ask is None or mid is None:
        return orders, px_state, avg_entry_price

    mids = px_state.get("mids", [])
    if not isinstance(mids, list):
        mids = []
    mids.append(float(mid))
    # Keep enough history for both the z-window and the extreme window.
    keep = max(LOOKBACK, EXTREME_LOOKBACK)
    if len(mids) > keep:
        mids = mids[-keep:]
    px_state["mids"] = mids

    # Reset the day anchor at the start of each day (timestamp resets to 0).
    last_ts = px_state.get("last_ts")
    day_open = px_state.get("day_open")
    new_day = (
        not isinstance(day_open, (int, float))
        or (isinstance(last_ts, (int, float)) and timestamp < int(last_ts))
    )
    if new_day:
        day_open = float(mid)
        px_state["day_open"] = day_open
    px_state["last_ts"] = int(timestamp)

    if len(mids) < 50:
        return orders, px_state, avg_entry_price

    # Z-score on the most recent LOOKBACK mids.
    window = mids[-LOOKBACK:]
    mean = sum(window) / len(window)
    var = sum((x - mean) ** 2 for x in window) / max(1, len(window) - 1)
    std = math.sqrt(var)
    if std < 1e-9:
        return orders, px_state, avg_entry_price

    z = (mid - mean) / std
    px_state["last_z"] = z
    px_state["mean"] = mean
    px_state["std"] = std

    # ---- TREND FILTER ----
    # 1) Same-day drift: block entries that lean into a strong trend.
    one_tick_diffs = [mids[i] - mids[i - 1] for i in range(max(1, len(mids) - LOOKBACK), len(mids))]
    if one_tick_diffs:
        m_d = sum(one_tick_diffs) / len(one_tick_diffs)
        v_d = sum((d - m_d) ** 2 for d in one_tick_diffs) / max(1, len(one_tick_diffs) - 1)
        sigma_tick = math.sqrt(v_d)
    else:
        sigma_tick = 0.0
    elapsed = max(1, timestamp // 100 + 1)
    expected_random_walk_sd = sigma_tick * math.sqrt(elapsed)
    day_drift = float(mid) - float(day_open)
    drift_sigma = day_drift / expected_random_walk_sd if expected_random_walk_sd > 1e-9 else 0.0

    block_short = drift_sigma > DAY_DRIFT_BLOCK_SIGMA   # uptrend → don't add to shorts
    block_long = drift_sigma < -DAY_DRIFT_BLOCK_SIGMA   # downtrend → don't add to longs

    # 2) Don't fire entries at fresh N-tick extremes.
    extreme_window = mids[-EXTREME_LOOKBACK:] if len(mids) >= EXTREME_LOOKBACK else mids
    if extreme_window:
        if mid >= max(extreme_window):
            block_short = True
        if mid <= min(extreme_window):
            block_long = True

    px_state["drift_sigma"] = drift_sigma
    px_state["block_short"] = bool(block_short)
    px_state["block_long"] = bool(block_long)

    fair = mean
    buy_budget = max(0, LIMITS[PEBBLES_XL] - position)
    sell_budget = max(0, LIMITS[PEBBLES_XL] + position)

    # ---- HARD STOP-LOSS ----
    # If the position is deep underwater, flatten immediately.
    if position != 0 and avg_entry_price is not None:
        if position > 0 and (avg_entry_price - mid) >= STOP_LOSS_PER_UNIT:
            qty = min(position, depth.buy_orders[bid], LIMITS[PEBBLES_XL])
            sell_budget = add_sell(orders, PEBBLES_XL, bid, qty, sell_budget)
            return orders, px_state, avg_entry_price
        if position < 0 and (mid - avg_entry_price) >= STOP_LOSS_PER_UNIT:
            qty = min(-position, -depth.sell_orders[ask], LIMITS[PEBBLES_XL])
            buy_budget = add_buy(orders, PEBBLES_XL, ask, qty, buy_budget)
            return orders, px_state, avg_entry_price

    # ---- AGGRESSIVE TAKE (gated by trend filter) ----
    if z <= -ENTRY_Z and not block_long:
        edge = fair - ask
        if edge >= TAKE_EDGE:
            qty = min(-depth.sell_orders[ask], MAX_TAKE_SIZE)
            buy_budget = add_buy(orders, PEBBLES_XL, ask, qty, buy_budget)
    elif z >= ENTRY_Z and not block_short:
        edge = bid - fair
        if edge >= TAKE_EDGE:
            qty = min(depth.buy_orders[bid], MAX_TAKE_SIZE)
            sell_budget = add_sell(orders, PEBBLES_XL, bid, qty, sell_budget)

    # ---- INVENTORY EXIT (always allowed; trend filter only gates entries) ----
    if position > 0 and z >= -EXIT_Z:
        qty = min(position, depth.buy_orders[bid], MAX_TAKE_SIZE)
        sell_budget = add_sell(orders, PEBBLES_XL, bid, qty, sell_budget)
    if position < 0 and z <= EXIT_Z:
        qty = min(-position, -depth.sell_orders[ask], MAX_TAKE_SIZE)
        buy_budget = add_buy(orders, PEBBLES_XL, ask, qty, buy_budget)

    # ---- PASSIVE QUOTES (also gated) ----
    if z <= -ENTRY_Z and not block_long and buy_budget > 0:
        px = min(bid + 1, ask - 1)
        if px < ask:
            buy_budget = add_buy(
                orders, PEBBLES_XL, px, min(PASSIVE_SIZE, buy_budget), buy_budget
            )
    if z >= ENTRY_Z and not block_short and sell_budget > 0:
        px = max(ask - 1, bid + 1)
        if px > bid:
            sell_budget = add_sell(
                orders, PEBBLES_XL, px, min(PASSIVE_SIZE, sell_budget), sell_budget
            )

    return orders, px_state, avg_entry_price

# ============= END HELPERS FOR PEBBLES_XL (TREND-FILTERED) =======================


def update_avg_entry_price(
    prev_pos: int,
    new_pos: int,
    avg_entry: Optional[float],
    own_trades: List,
) -> Optional[float]:
    """Track avg entry price across own_trades since last call to drive the stop."""
    pos = prev_pos
    avg = avg_entry if avg_entry is not None else 0.0
    for t in own_trades:
        qty = int(t.quantity) if t.buyer == "SUBMISSION" else -int(t.quantity)
        price = float(t.price)
        new_pos_step = pos + qty
        if pos == 0 or (pos > 0) != (new_pos_step > 0):
            avg = price
        elif (pos > 0 and qty > 0) or (pos < 0 and qty < 0):
            avg = (avg * abs(pos) + price * abs(qty)) / abs(new_pos_step)
        pos = new_pos_step
    if new_pos == 0:
        return None
    return avg


class Trader:
    def run(self, state: TradingState):
        raw_state: Dict[str, object] = {}
        if state.traderData:
            try:
                decoded = json.loads(state.traderData)
                if isinstance(decoded, dict):
                    raw_state = decoded
            except Exception:
                raw_state = {}

        pebbles_xl_state = raw_state.get("pebbles_xl", {})
        if not isinstance(pebbles_xl_state, dict):
            pebbles_xl_state = {}

        prev_pos = int(raw_state.get("prev_pos_xl", 0))
        avg_entry = raw_state.get("avg_entry_xl")
        if avg_entry is not None and not isinstance(avg_entry, (int, float)):
            avg_entry = None

        own_trades = state.own_trades.get(PEBBLES_XL, []) if state.own_trades else []
        cur_pos = int(state.position.get(PEBBLES_XL, 0))
        avg_entry = update_avg_entry_price(prev_pos, cur_pos, avg_entry, own_trades)

        result: Dict[str, List[Order]] = {}
        if PEBBLES_XL in state.order_depths:
            result[PEBBLES_XL], pebbles_xl_state, avg_entry = trade_pebbles_xl_trendfiltered(
                state.order_depths[PEBBLES_XL],
                cur_pos,
                int(state.timestamp),
                float(avg_entry) if avg_entry is not None else None,
                pebbles_xl_state,
            )

        trader_data = json.dumps({
            "pebbles_xl": pebbles_xl_state,
            "prev_pos_xl": cur_pos,
            "avg_entry_xl": avg_entry,
        })
        return result, 0, trader_data
