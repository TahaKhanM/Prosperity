import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


# ============= BEGIN HELPERS FOR PEBBLES_XL (BASKET RESIDUAL + GUARDRAILS) =============
PEBBLES_XL = "PEBBLES_XL"
PEBBLES_BASKET = ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L"]

LIMITS = {PEBBLES_XL: 10}

# --- Mean-rev knobs (same as v1 baseline) ---
LOOKBACK = 200
ENTRY_Z = 1.4
EXIT_Z = 0.35
TAKE_EDGE = 2.0
MAX_TAKE_SIZE = 4
PASSIVE_SIZE = 3

# --- Round-1-style fair-value blending ---
# Microprice / flow tilt: how much we let microprice and short-term return
# bias the fair away from the rolling mean. Clamped tight so we never let
# flow drag fair across the spread.
MICRO_TILT = 0.30        # weight on (micro - mid) into fair
FADE_TILT = 0.40         # weight on -ret1 into fair (don't chase)
FAIR_CLAMP_BAND = 1.5    # max amount fair can deviate from rolling mean due to tilts

# --- Shock detector (block entries, never exits) ---
# Triggered when the per-tick residual move is large (regime break in progress)
# or when the raw 1-tick mid return is unusually large.
SHOCK_RESID_RET = 6.0    # |Δ(residual)| in seashells
SHOCK_MID_RET = 4.0      # |Δ(mid)| in seashells

# --- Residual-breakout / decoupling guardrails ---
# When the residual makes a new extreme of the last EXTREME_LOOKBACK ticks
# we stop trading the side that's expanding (basket model is breaking).
EXTREME_LOOKBACK = 500
# Decoupling: short-window corr(Δxl, Δbasket). When it drops below MIN_CORR,
# the family is no longer co-moving and the basket residual signal is
# meaningless; pause until it recovers.
CORR_LOOKBACK = 100
MIN_CORR = 0.3

# --- Daily drawdown kill ---
# Track session realised+unrealised PnL versus the day's high. If we draw
# down by more than DD_KILL seashells from the day high, go flat and refuse
# to trade for the rest of the day.
DD_KILL = 1500.0


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


def wall_mid(depth: OrderDepth) -> Optional[float]:
    """Volume-weighted mid using the deepest level on each side."""
    if not depth.buy_orders or not depth.sell_orders:
        return None
    bid_p, bid_v = max(depth.buy_orders.items(), key=lambda kv: abs(kv[1]))
    ask_p, ask_v = max(depth.sell_orders.items(), key=lambda kv: abs(kv[1]))
    return (bid_p + ask_p) / 2.0


def microprice(depth: OrderDepth) -> Optional[float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return None
    bv = abs(depth.buy_orders[bid])
    av = abs(depth.sell_orders[ask])
    if bv + av <= 0:
        return (bid + ask) / 2.0
    # microprice formula — leans toward the side with less size
    return (bid * av + ask * bv) / (av + bv)


def book_mid(depth: OrderDepth, anchor: float) -> float:
    """Cascading fallback: simple_mid → wall_mid → anchor."""
    m = simple_mid(depth)
    if m is not None:
        return m
    m = wall_mid(depth)
    if m is not None:
        return m
    return anchor


def imbalance(depth: OrderDepth) -> float:
    if not depth.buy_orders or not depth.sell_orders:
        return 0.0
    bv = sum(abs(v) for v in depth.buy_orders.values())
    av = sum(abs(v) for v in depth.sell_orders.values())
    if bv + av <= 0:
        return 0.0
    return (bv - av) / (bv + av)


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


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


def pearson_corr(xs: List[float], ys: List[float]) -> float:
    n = min(len(xs), len(ys))
    if n < 5:
        return 1.0  # not enough data → assume coupled
    mx = sum(xs[-n:]) / n
    my = sum(ys[-n:]) / n
    num = sum((xs[-n + i] - mx) * (ys[-n + i] - my) for i in range(n))
    dx = math.sqrt(sum((xs[-n + i] - mx) ** 2 for i in range(n)))
    dy = math.sqrt(sum((ys[-n + i] - my) ** 2 for i in range(n)))
    if dx <= 1e-9 or dy <= 1e-9:
        return 1.0
    return num / (dx * dy)


def trade_pebbles_xl_basket_guarded(
    state: TradingState,
    position: int,
    px_state: Dict[str, object],
) -> Tuple[List[Order], Dict[str, object], Dict[str, float]]:
    diagnostics: Dict[str, float] = {}
    orders: List[Order] = []

    if PEBBLES_XL not in state.order_depths:
        return orders, px_state, diagnostics

    xl_depth = state.order_depths[PEBBLES_XL]
    bid = best_bid(xl_depth)
    ask = best_ask(xl_depth)
    if bid is None or ask is None:
        return orders, px_state, diagnostics

    # --- Mids: cascading fallback for XL, simple_mid for the basket legs ---
    last_mid = float(px_state.get("last_mid", (bid + ask) / 2.0))
    xl_mid = book_mid(xl_depth, anchor=last_mid)
    xl_micro = microprice(xl_depth) or xl_mid

    basket_mids: List[float] = []
    for sym in PEBBLES_BASKET:
        d = state.order_depths.get(sym)
        if d is None:
            return orders, px_state, diagnostics
        m = simple_mid(d)
        if m is None:
            return orders, px_state, diagnostics
        basket_mids.append(m)
    basket_mid = sum(basket_mids) / len(basket_mids)

    # --- Residual ---
    resid = xl_mid - basket_mid
    resids = px_state.get("resids", [])
    if not isinstance(resids, list):
        resids = []
    last_resid = resids[-1] if resids else resid
    resid_ret = resid - last_resid
    resids.append(float(resid))
    if len(resids) > max(LOOKBACK, EXTREME_LOOKBACK):
        resids = resids[-max(LOOKBACK, EXTREME_LOOKBACK):]
    px_state["resids"] = resids

    # Track XL and basket diffs for decoupling check
    xl_diffs = px_state.get("xl_diffs", [])
    bk_diffs = px_state.get("bk_diffs", [])
    if not isinstance(xl_diffs, list): xl_diffs = []
    if not isinstance(bk_diffs, list): bk_diffs = []
    last_basket = float(px_state.get("last_basket", basket_mid))
    xl_diffs.append(xl_mid - last_mid)
    bk_diffs.append(basket_mid - last_basket)
    if len(xl_diffs) > CORR_LOOKBACK: xl_diffs = xl_diffs[-CORR_LOOKBACK:]
    if len(bk_diffs) > CORR_LOOKBACK: bk_diffs = bk_diffs[-CORR_LOOKBACK:]
    px_state["xl_diffs"] = xl_diffs
    px_state["bk_diffs"] = bk_diffs

    px_state["last_mid"] = xl_mid
    px_state["last_basket"] = basket_mid

    if len(resids) < 50:
        return orders, px_state, diagnostics

    # --- Rolling stats on residual ---
    window = resids[-LOOKBACK:]
    mean_r = sum(window) / len(window)
    var_r = sum((x - mean_r) ** 2 for x in window) / max(1, len(window) - 1)
    std_r = math.sqrt(var_r)
    if std_r < 1e-9:
        return orders, px_state, diagnostics

    z = (resid - mean_r) / std_r

    # --- Round-1-style fair: rolling mean + microprice tilt + return fade ---
    micro_bias = clamp(MICRO_TILT * (xl_micro - xl_mid), -FAIR_CLAMP_BAND, FAIR_CLAMP_BAND)
    fade_bias = clamp(-FADE_TILT * (xl_mid - last_mid), -FAIR_CLAMP_BAND, FAIR_CLAMP_BAND)
    fair = basket_mid + mean_r + micro_bias + fade_bias

    # --- GUARDRAIL 1: shock flag ---
    mid_ret = xl_mid - last_mid
    shock = abs(resid_ret) >= SHOCK_RESID_RET or abs(mid_ret) >= SHOCK_MID_RET

    # --- GUARDRAIL 2: residual breakout / decoupling ---
    extreme_window = resids[-EXTREME_LOOKBACK:]
    at_resid_high = resid >= max(extreme_window)
    at_resid_low = resid <= min(extreme_window)

    corr = pearson_corr(xl_diffs, bk_diffs)
    decoupled = corr < MIN_CORR

    # --- GUARDRAIL 3: daily drawdown (fill-agnostic MTM tracker) ---
    # Honest MTM PnL increment per tick: (position carried into this tick) * (mid change).
    # Uses only state.position (which reflects ACTUAL fills) and last/current mid.
    # No cost-basis tracking, no fill assumptions, so unfilled orders can't desync it.
    mtm_pnl = float(px_state.get("mtm_pnl", 0.0))
    last_mid_for_pnl = float(px_state.get("last_mid_for_pnl", xl_mid))
    mtm_pnl += position * (xl_mid - last_mid_for_pnl)
    px_state["last_mid_for_pnl"] = xl_mid
    px_state["mtm_pnl"] = mtm_pnl

    eq_high = float(px_state.get("eq_high", mtm_pnl))
    if mtm_pnl > eq_high:
        eq_high = mtm_pnl
    px_state["eq_high"] = eq_high
    drawdown = eq_high - mtm_pnl
    dd_killed = bool(px_state.get("dd_killed", False)) or drawdown >= DD_KILL
    px_state["dd_killed"] = dd_killed

    # Reset DD on day rollover
    last_ts = px_state.get("last_ts")
    ts = int(getattr(state, "timestamp", 0))
    if isinstance(last_ts, (int, float)) and ts < int(last_ts):
        # New day: reset DD tracking and the PnL counter
        px_state["eq_high"] = mtm_pnl
        px_state["dd_killed"] = False
        dd_killed = False
        eq_high = mtm_pnl
    px_state["last_ts"] = ts

    # When entries are blocked we still allow EXITS (toward zero inventory).
    block_long_entry = shock or decoupled or at_resid_low or dd_killed
    block_short_entry = shock or decoupled or at_resid_high or dd_killed

    diagnostics.update({
        "z": z,
        "mean_r": mean_r,
        "std_r": std_r,
        "resid": resid,
        "shock": 1.0 if shock else 0.0,
        "decoupled": 1.0 if decoupled else 0.0,
        "corr": corr,
        "at_resid_high": 1.0 if at_resid_high else 0.0,
        "at_resid_low": 1.0 if at_resid_low else 0.0,
        "drawdown": drawdown,
        "dd_killed": 1.0 if dd_killed else 0.0,
    })
    px_state.update({
        "last_z": z, "last_corr": corr, "last_drawdown": drawdown,
    })

    buy_budget = max(0, LIMITS[PEBBLES_XL] - position)
    sell_budget = max(0, LIMITS[PEBBLES_XL] + position)

    # --- KILL: dd_killed → flatten any inventory, place no new entries ---
    if dd_killed and position != 0:
        if position > 0:
            qty = min(position, abs(xl_depth.buy_orders[bid]), MAX_TAKE_SIZE)
            sell_budget = add_sell(orders, PEBBLES_XL, bid, qty, sell_budget)
        else:
            qty = min(-position, abs(xl_depth.sell_orders[ask]), MAX_TAKE_SIZE)
            buy_budget = add_buy(orders, PEBBLES_XL, ask, qty, buy_budget)
        return orders, px_state, diagnostics

    # --- AGGRESSIVE TAKE (gated) ---
    if z <= -ENTRY_Z and not block_long_entry:
        edge = fair - ask
        if edge >= TAKE_EDGE:
            qty = min(abs(xl_depth.sell_orders[ask]), MAX_TAKE_SIZE)
            buy_budget = add_buy(orders, PEBBLES_XL, ask, qty, buy_budget)
    elif z >= ENTRY_Z and not block_short_entry:
        edge = bid - fair
        if edge >= TAKE_EDGE:
            qty = min(abs(xl_depth.buy_orders[bid]), MAX_TAKE_SIZE)
            sell_budget = add_sell(orders, PEBBLES_XL, bid, qty, sell_budget)

    # --- INVENTORY EXIT (always allowed; this is what saves us in trends) ---
    if position > 0 and z >= -EXIT_Z:
        qty = min(position, abs(xl_depth.buy_orders[bid]), MAX_TAKE_SIZE)
        sell_budget = add_sell(orders, PEBBLES_XL, bid, qty, sell_budget)
    if position < 0 and z <= EXIT_Z:
        qty = min(-position, abs(xl_depth.sell_orders[ask]), MAX_TAKE_SIZE)
        buy_budget = add_buy(orders, PEBBLES_XL, ask, qty, buy_budget)

    # --- PASSIVE QUOTES (gated; never quote into a shocked book) ---
    if z <= -ENTRY_Z and not block_long_entry and buy_budget > 0:
        px = min(bid + 1, ask - 1)
        if px < ask:
            buy_budget = add_buy(
                orders, PEBBLES_XL, px, min(PASSIVE_SIZE, buy_budget), buy_budget
            )
    if z >= ENTRY_Z and not block_short_entry and sell_budget > 0:
        px = max(ask - 1, bid + 1)
        if px > bid:
            sell_budget = add_sell(
                orders, PEBBLES_XL, px, min(PASSIVE_SIZE, sell_budget), sell_budget
            )

    return orders, px_state, diagnostics

# ============= END HELPERS FOR PEBBLES_XL (BASKET + GUARDRAILS) =============


class Trader:
    def run(self, state: TradingState):
        raw_state: Dict[str, Dict[str, object]] = {}
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

        result: Dict[str, List[Order]] = {}
        result[PEBBLES_XL], pebbles_xl_state, _diag = trade_pebbles_xl_basket_guarded(
            state,
            int(state.position.get(PEBBLES_XL, 0)),
            pebbles_xl_state,
        )

        trader_data = json.dumps({"pebbles_xl": pebbles_xl_state})
        return result, 0, trader_data
