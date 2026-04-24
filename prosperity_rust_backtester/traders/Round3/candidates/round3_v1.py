"""Round 3 v1 — ship-now alphas (A1 + B1 + C1 + G1).

A1: HYDROGEL_PACK soft-anchor MM around fair = clamp(EMA_200, 9980, 10010)
    seeded at 9991 (empirical mean; NOT 10000).
B1: VELVETFRUIT_EXTRACT wall-mid MM (top-3 levels with qty >= 20 lead top-mid).
C1: top-2 order-book imbalance skew, additive to A1 and B1, capped at +/- 2 ticks.
G1: defensive voucher parity guard (ask + 1 <= S_bid - K) -> buy voucher + short VE.

All other alphas (IV scalp D1, deep-ITM overlay E1, counterparty F1, smile
carry L1, rhythm R4) remain behind feature flags = False by default and are
not implemented here.

Submission contract: run(state) -> (orders, conversions, traderData).
"""

from __future__ import annotations

import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


TRADER_DATA_SCHEMA = 1
TRADER_DATA_MAX_BYTES = 8000

HYDROGEL = "HYDROGEL_PACK"
VE = "VELVETFRUIT_EXTRACT"
VOUCHER_STRIKES = (4000, 4500, 5000, 5100, 5200, 5300, 5400, 5500, 6000, 6500)
VOUCHER_SYMBOLS = tuple(f"VEV_{k}" for k in VOUCHER_STRIKES)

POS_LIMIT = {
    HYDROGEL: 200,
    VE: 200,
    **{s: 300 for s in VOUCHER_SYMBOLS},
}

DEFAULT_FLAGS = {
    "mm_hydrogel":      True,
    "mm_ve":            True,
    "imbalance_skew":   True,
    "parity_guard":     True,
    "iv_scalp":         False,
    "deep_itm_overlay": False,
    "counterparty":     False,
}

# ----- A1 HYDROGEL soft-anchor MM ------------------------------------------
# Research proposed fair = clamp(EMA_200, 9980, 10010) seeded 9991. Empirically
# in this backtester the anchored blend `0.85*10000 + 0.15*micro` with
# EWMA_alpha=0.05 crushes a plain EMA at 9991 by ~36k/day. The upward anchor
# at 10000 creates MM edge: we buy cheap below fair, unload on mean reversion.
# Live falsifier still applies: if live mean drifts > 20 below 9991, switch
# to raw micro.
H_ANCHOR = 10000.0
H_ANCHOR_WEIGHT = 0.85
H_EWMA_ALPHA = 0.05
H_TAKE_EDGE = 1
H_QUOTE_EDGE = 4
H_SOFT_POS_LIMIT = 80
H_QUOTE_SIZE = 20

# ----- B1 VE wall-mid adaptive MM ------------------------------------------
VE_WALL_QTY = 20
VE_TAKE_EDGE = 1
VE_CLEAR_EDGE = 1
VE_QUOTE_EDGE = 3
VE_SOFT_POS_LIMIT = 80
VE_QUOTE_SIZE = 20

# ----- C1 imbalance skew ---------------------------------------------------
IMB_K_LEVELS = 2                # top-2 levels only (k=3 flips sign)
H_SKEW_BETA = 12.0
VE_SKEW_BETA = 3.0
SKEW_CAP_TICK = 2.0

# ----- G1 parity guard -----------------------------------------------------
PARITY_MIN_EDGE = 1
PARITY_SIZE_CAP = 10


# ---------- helpers --------------------------------------------------------


def _best_bid(depth: OrderDepth) -> Optional[int]:
    return max(depth.buy_orders) if depth.buy_orders else None


def _best_ask(depth: OrderDepth) -> Optional[int]:
    return min(depth.sell_orders) if depth.sell_orders else None


def _mid(depth: OrderDepth) -> Optional[float]:
    bb = _best_bid(depth)
    ba = _best_ask(depth)
    if bb is None or ba is None:
        return None
    return (bb + ba) / 2.0


def _levels_ascending_ask(depth: OrderDepth) -> List[Tuple[int, int]]:
    # (price, volume positive) sorted ascending by price.
    return sorted(((p, -q) for p, q in depth.sell_orders.items()), key=lambda x: x[0])


def _levels_descending_bid(depth: OrderDepth) -> List[Tuple[int, int]]:
    # (price, volume positive) sorted descending by price.
    return sorted(((p, q) for p, q in depth.buy_orders.items()), key=lambda x: -x[0])


def _wall_mid(depth: OrderDepth, wall_qty: int) -> Optional[float]:
    """Midpoint of the first-thick bid level and first-thick ask level.

    A 'thick' level is one with qty >= wall_qty within the top-3 levels. If
    neither side has a thick level, fall back to plain mid.
    """
    bids = _levels_descending_bid(depth)[:3]
    asks = _levels_ascending_ask(depth)[:3]

    thick_bid = next((p for p, q in bids if q >= wall_qty), None)
    thick_ask = next((p for p, q in asks if q >= wall_qty), None)

    if thick_bid is not None and thick_ask is not None:
        return (thick_bid + thick_ask) / 2.0
    if thick_bid is not None:
        return float(thick_bid) + 0.5
    if thick_ask is not None:
        return float(thick_ask) - 0.5
    return _mid(depth)


def _filtered_mmmid(depth: OrderDepth, adverse_qty: int) -> Optional[float]:
    """Mid computed from levels whose resting size >= adverse_qty on each side."""
    bids = _levels_descending_bid(depth)
    asks = _levels_ascending_ask(depth)
    bb = next((p for p, q in bids if q >= adverse_qty), None)
    ba = next((p for p, q in asks if q >= adverse_qty), None)
    if bb is not None and ba is not None:
        return (bb + ba) / 2.0
    return _mid(depth)


def _microprice(depth: OrderDepth) -> Optional[float]:
    bb = _best_bid(depth)
    ba = _best_ask(depth)
    if bb is None or ba is None:
        return None
    bv = depth.buy_orders[bb]
    av = -depth.sell_orders[ba]
    total = bv + av
    if total <= 0:
        return (bb + ba) / 2.0
    return (ba * bv + bb * av) / total


def _top_k_imbalance(depth: OrderDepth, k: int) -> float:
    """Signed imbalance over top k levels. In [-1, +1]."""
    bids = _levels_descending_bid(depth)[:k]
    asks = _levels_ascending_ask(depth)[:k]
    bv = sum(q for _, q in bids)
    av = sum(q for _, q in asks)
    total = bv + av
    if total <= 0:
        return 0.0
    return (bv - av) / total


def _ema_alpha_from_half_life(half_life: float) -> float:
    # Half-life h corresponds to alpha = 1 - 0.5 ** (1/h).
    return 1.0 - 0.5 ** (1.0 / half_life)


# ---------- order building blocks ------------------------------------------


def _clip_buy(position: int, cap: int, already_buying: int, want: int) -> int:
    headroom = cap - (position + already_buying)
    return max(0, min(want, headroom))


def _clip_sell(position: int, cap: int, already_selling: int, want: int) -> int:
    headroom = cap + (position - already_selling)
    return max(0, min(want, headroom))


def _take_and_quote_symmetric(
    symbol: str,
    depth: OrderDepth,
    fair: float,
    position: int,
    take_edge: float,
    quote_edge: float,
    quote_size: int,
    soft_limit: int,
) -> List[Order]:
    """Take top-of-book at edge, then post inventory-skewed two-sided quotes.

    Single aggressive level per side (no ladder walk), no separate clear order.
    Make size scales inversely with inventory (lighter bid when long).
    """
    cap = POS_LIMIT[symbol]
    orders: List[Order] = []
    bought = 0
    sold = 0

    best_bid = _best_bid(depth)
    best_ask = _best_ask(depth)
    if best_bid is None and best_ask is None:
        return orders

    # --- take top level if edge available
    if best_ask is not None and best_ask + take_edge <= fair:
        avail = -depth.sell_orders[best_ask]
        size = _clip_buy(position, cap, bought, min(avail, cap))
        if size > 0:
            orders.append(Order(symbol, best_ask, size))
            bought += size
    if best_bid is not None and best_bid - take_edge >= fair:
        avail = depth.buy_orders[best_bid]
        size = _clip_sell(position, cap, sold, min(avail, cap))
        if size > 0:
            orders.append(Order(symbol, best_bid, -size))
            sold += size

    # --- make: inventory-skewed two-sided quotes
    inv_ratio = 0.0 if cap == 0 else max(-1.0, min(1.0, (position + bought - sold) / float(cap)))

    buy_px = int(math.floor(fair - quote_edge))
    sell_px = int(math.ceil(fair + quote_edge))

    # join inside book; never cross
    if best_bid is not None:
        buy_px = min(buy_px, best_bid + 1)
    if best_ask is not None:
        sell_px = max(sell_px, best_ask - 1)
    # never cross the book
    if best_ask is not None:
        buy_px = min(buy_px, best_ask - 1)
    if best_bid is not None:
        sell_px = max(sell_px, best_bid + 1)

    if buy_px >= sell_px:
        return orders  # spread collapsed; skip makes

    # inventory-scaled make sizes
    buy_size_raw = max(0, int(round(quote_size * (1.0 - inv_ratio))))
    sell_size_raw = max(0, int(round(quote_size * (1.0 + inv_ratio))))

    # hard soft-limit pullback: stop adding to the losing side past |pos| > soft
    if position > soft_limit:
        buy_size_raw = 0
    if position < -soft_limit:
        sell_size_raw = 0

    buy_size = _clip_buy(position, cap, bought, buy_size_raw)
    sell_size = _clip_sell(position, cap, sold, sell_size_raw)

    if buy_size > 0 and (best_ask is None or buy_px < best_ask):
        orders.append(Order(symbol, buy_px, buy_size))
    if sell_size > 0 and (best_bid is None or sell_px > best_bid):
        orders.append(Order(symbol, sell_px, -sell_size))

    return orders


# ---------- state management ----------------------------------------------


def _load_state(raw: str) -> Dict:
    if not raw:
        return {"schema": TRADER_DATA_SCHEMA, "flags": dict(DEFAULT_FLAGS), "h_ema": None, "ve_last_mid": None}
    try:
        data = json.loads(raw)
    except Exception:
        return {"schema": TRADER_DATA_SCHEMA, "flags": dict(DEFAULT_FLAGS), "h_ema": None, "ve_last_mid": None}

    flags = dict(DEFAULT_FLAGS)
    flags.update(data.get("flags", {}))
    return {
        "schema": TRADER_DATA_SCHEMA,
        "flags": flags,
        "h_ema": data.get("h_ema", None),
        "ve_last_mid": data.get("ve_last_mid", None),
    }


def _dump_state(state: Dict) -> str:
    raw = json.dumps({
        "schema": TRADER_DATA_SCHEMA,
        "flags": state["flags"],
        "h_ema": state["h_ema"],
        "ve_last_mid": state["ve_last_mid"],
    }, separators=(",", ":"))
    # truncate defensively (should never happen at <200 bytes typical)
    if len(raw) > TRADER_DATA_MAX_BYTES:
        raw = raw[:TRADER_DATA_MAX_BYTES]
    return raw


# ---------- strategy entry points -----------------------------------------


def _run_hydrogel(state_dict: Dict, depth: OrderDepth, position: int, imbalance: float, enable_skew: bool) -> List[Order]:
    micro = _microprice(depth)
    if micro is None:
        return []

    # Anchored blend then EWMA smoothing. Anchor weight 0.85 pulls fair
    # toward 10000; 0.15 lets market micro inform the drift component.
    blended = H_ANCHOR_WEIGHT * H_ANCHOR + (1.0 - H_ANCHOR_WEIGHT) * micro
    prev = state_dict.get("h_ema")
    if prev is None:
        fair = blended
    else:
        fair = prev * (1.0 - H_EWMA_ALPHA) + blended * H_EWMA_ALPHA
    state_dict["h_ema"] = fair

    if enable_skew:
        skew = max(-SKEW_CAP_TICK, min(SKEW_CAP_TICK, H_SKEW_BETA * imbalance))
        fair += skew

    return _take_and_quote_symmetric(
        HYDROGEL, depth, fair, position,
        H_TAKE_EDGE, H_QUOTE_EDGE, H_QUOTE_SIZE, H_SOFT_POS_LIMIT,
    )


def _run_ve(state_dict: Dict, depth: OrderDepth, position: int, imbalance: float, enable_skew: bool) -> List[Order]:
    wall = _wall_mid(depth, VE_WALL_QTY)
    if wall is None:
        return []
    state_dict["ve_last_mid"] = wall

    fair = wall
    if enable_skew:
        skew = max(-SKEW_CAP_TICK, min(SKEW_CAP_TICK, VE_SKEW_BETA * imbalance))
        fair += skew

    return _take_and_quote_symmetric(
        VE, depth, fair, position,
        VE_TAKE_EDGE, VE_QUOTE_EDGE, VE_QUOTE_SIZE, VE_SOFT_POS_LIMIT,
    )


def _run_parity_guard(
    order_depths: Dict[str, OrderDepth],
    positions: Dict[str, int],
) -> Dict[str, List[Order]]:
    """Identity-only: if best_ask(K) + edge <= best_bid(VE) - K, buy VEV_K and short VE."""
    out: Dict[str, List[Order]] = {}

    ve_depth = order_depths.get(VE)
    if ve_depth is None:
        return out
    s_bid = _best_bid(ve_depth)
    if s_bid is None:
        return out

    for k, sym in zip(VOUCHER_STRIKES, VOUCHER_SYMBOLS):
        depth = order_depths.get(sym)
        if depth is None:
            continue
        asks = _levels_ascending_ask(depth)
        if not asks:
            continue
        best_ask, ask_qty = asks[0]
        intrinsic_floor = s_bid - k  # conservative: use best bid of underlying
        if best_ask + PARITY_MIN_EDGE > intrinsic_floor:
            continue

        # Size: min of parity cap, voucher capacity, VE short capacity, available book sizes
        v_pos = positions.get(sym, 0)
        ve_pos = positions.get(VE, 0)
        v_cap = POS_LIMIT[sym] - v_pos
        ve_short_cap = POS_LIMIT[VE] + ve_pos  # room to short
        ve_best_bid = _best_bid(ve_depth)
        ve_bid_qty = ve_depth.buy_orders.get(ve_best_bid, 0) if ve_best_bid is not None else 0
        fill = min(PARITY_SIZE_CAP, ask_qty, v_cap, ve_short_cap, ve_bid_qty)
        if fill <= 0 or ve_best_bid is None:
            continue
        out.setdefault(sym, []).append(Order(sym, best_ask, fill))
        out.setdefault(VE, []).append(Order(VE, ve_best_bid, -fill))

    return out


# ---------- Trader ---------------------------------------------------------


class Trader:
    def run(self, state: TradingState):
        td = _load_state(state.traderData or "")
        flags = td["flags"]
        orders: Dict[str, List[Order]] = {}

        h_depth = state.order_depths.get(HYDROGEL)
        ve_depth = state.order_depths.get(VE)
        h_pos = state.position.get(HYDROGEL, 0)
        ve_pos = state.position.get(VE, 0)

        # Imbalances (used by C1 skew)
        h_imb = _top_k_imbalance(h_depth, IMB_K_LEVELS) if h_depth is not None else 0.0
        ve_imb = _top_k_imbalance(ve_depth, IMB_K_LEVELS) if ve_depth is not None else 0.0

        enable_skew = bool(flags.get("imbalance_skew", True))

        if flags.get("mm_hydrogel", True) and h_depth is not None:
            h_orders = _run_hydrogel(td, h_depth, h_pos, h_imb, enable_skew)
            if h_orders:
                orders[HYDROGEL] = h_orders

        if flags.get("mm_ve", True) and ve_depth is not None:
            ve_orders = _run_ve(td, ve_depth, ve_pos, ve_imb, enable_skew)
            if ve_orders:
                orders[VE] = ve_orders

        if flags.get("parity_guard", True):
            guard = _run_parity_guard(state.order_depths, state.position)
            for sym, sym_orders in guard.items():
                orders.setdefault(sym, []).extend(sym_orders)

        return orders, 0, _dump_state(td)

    def bid(self) -> int:
        return 20
