"""Round 3 v2 — v1 (A1+B1+C1+G1) plus voucher MM.

Single-file, hosted-submission-compatible trader. No external imports from
sibling modules — everything needed is inlined.

Alphas in this trader:
  A1 HYDROGEL_PACK soft-anchor MM (fair = anchored-blend at 10000)
  B1 VELVETFRUIT_EXTRACT wall-mid adaptive MM
  C1 top-2 order-book imbalance skew on A1 + B1
  G1 defensive parity guard on vouchers
  V2 voucher identity take (floor + upper bound) + passive MM on near-ATM
     strikes + strike-monotonicity butterfly.

Submission contract: run(state) -> (orders, conversions, traderData).
traderData is JSON and stays well under 50,000 chars.
"""

from __future__ import annotations

import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


TRADER_DATA_SCHEMA = 2
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
    "voucher_mm":       True,
    "iv_scalp":         False,
    "deep_itm_overlay": False,
    "counterparty":     False,
}

# ----- A1 HYDROGEL soft-anchor MM ------------------------------------------
# Research proposed fair = clamp(EMA_200, 9980, 10010) seeded 9991. Empirically
# in this backtester the anchored blend `0.85*10000 + 0.15*micro` with
# EWMA_alpha=0.05 beats a plain EMA at 9991 by ~36k/day. Upward anchor at
# 10000 biases fair 7-8 shells above the empirical mean, which lines up the
# MM so that bids at best+1 always look cheap vs fair. Live falsifier: if
# mean HYDROGEL mid in first 1000 live ticks is > 20 below 9991, the anchor
# assumption fails and we should flip to raw micro.
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

# ----- V2 voucher MM -------------------------------------------------------
VOUCHER_SOFT_CAP = 50
VOUCHER_TAKE_SLACK = 1
VOUCHER_UPPER_SLACK = 1
VOUCHER_MONO_SLACK = 1
VOUCHER_PASSIVE_SIZE = 3
VOUCHER_PASSIVE_STRIKES = (5000, 5100, 5200, 5300, 5400, 5500)
# v02-calibrated time-value proxy: peak 55 at ATM, taper over 350-shell
# half-width, power 1.8. Capped at +2 for deep-ITM since TV is empirically 0.
TV_A = 55.0
TV_W = 350.0
TV_POW = 1.8
TV_OTM_FLOOR = 0.5
TV_DEEP_ITM_MAX_EXCESS = 2.0


# ---------- book helpers ---------------------------------------------------


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
    return sorted(((p, -q) for p, q in depth.sell_orders.items()), key=lambda x: x[0])


def _levels_descending_bid(depth: OrderDepth) -> List[Tuple[int, int]]:
    return sorted(((p, q) for p, q in depth.buy_orders.items()), key=lambda x: -x[0])


def _wall_mid(depth: OrderDepth, wall_qty: int) -> Optional[float]:
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
    bids = _levels_descending_bid(depth)[:k]
    asks = _levels_ascending_ask(depth)[:k]
    bv = sum(q for _, q in bids)
    av = sum(q for _, q in asks)
    total = bv + av
    if total <= 0:
        return 0.0
    return (bv - av) / total


# ---------- order clip helpers --------------------------------------------


def _clip_buy(position: int, cap: int, already_buying: int, want: int) -> int:
    headroom = cap - (position + already_buying)
    return max(0, min(want, headroom))


def _clip_sell(position: int, cap: int, already_selling: int, want: int) -> int:
    headroom = cap + (position - already_selling)
    return max(0, min(want, headroom))


# ---------- shared take-and-quote for underlyings -------------------------


def _take_and_quote(
    symbol: str,
    depth: OrderDepth,
    fair: float,
    position: int,
    take_edge: float,
    quote_edge: float,
    quote_size: int,
    soft_limit: int,
) -> List[Order]:
    cap = POS_LIMIT[symbol]
    orders: List[Order] = []
    bought = 0
    sold = 0

    bb = _best_bid(depth)
    ba = _best_ask(depth)
    if bb is None and ba is None:
        return orders

    if ba is not None and ba + take_edge <= fair:
        avail = -depth.sell_orders[ba]
        sz = _clip_buy(position, cap, bought, min(avail, cap))
        if sz > 0:
            orders.append(Order(symbol, ba, sz))
            bought += sz
    if bb is not None and bb - take_edge >= fair:
        avail = depth.buy_orders[bb]
        sz = _clip_sell(position, cap, sold, min(avail, cap))
        if sz > 0:
            orders.append(Order(symbol, bb, -sz))
            sold += sz

    inv_ratio = 0.0 if cap == 0 else max(-1.0, min(1.0, (position + bought - sold) / float(cap)))

    buy_px = int(math.floor(fair - quote_edge))
    sell_px = int(math.ceil(fair + quote_edge))

    if bb is not None:
        buy_px = min(buy_px, bb + 1)
    if ba is not None:
        sell_px = max(sell_px, ba - 1)
    if ba is not None:
        buy_px = min(buy_px, ba - 1)
    if bb is not None:
        sell_px = max(sell_px, bb + 1)

    if buy_px >= sell_px:
        return orders

    buy_size_raw = max(0, int(round(quote_size * (1.0 - inv_ratio))))
    sell_size_raw = max(0, int(round(quote_size * (1.0 + inv_ratio))))
    if position > soft_limit:
        buy_size_raw = 0
    if position < -soft_limit:
        sell_size_raw = 0

    bsz = _clip_buy(position, cap, bought, buy_size_raw)
    ssz = _clip_sell(position, cap, sold, sell_size_raw)
    if bsz > 0 and (ba is None or buy_px < ba):
        orders.append(Order(symbol, buy_px, bsz))
    if ssz > 0 and (bb is None or sell_px > bb):
        orders.append(Order(symbol, sell_px, -ssz))

    return orders


# ---------- A1 HYDROGEL / B1 VE / C1 skew ---------------------------------


def _run_hydrogel(state: Dict, depth: OrderDepth, position: int, imbalance: float, enable_skew: bool) -> List[Order]:
    micro = _microprice(depth)
    if micro is None:
        return []
    blended = H_ANCHOR_WEIGHT * H_ANCHOR + (1.0 - H_ANCHOR_WEIGHT) * micro
    prev = state.get("h_ema")
    fair = blended if prev is None else prev * (1.0 - H_EWMA_ALPHA) + blended * H_EWMA_ALPHA
    state["h_ema"] = fair

    if enable_skew:
        skew = max(-SKEW_CAP_TICK, min(SKEW_CAP_TICK, H_SKEW_BETA * imbalance))
        fair += skew

    return _take_and_quote(HYDROGEL, depth, fair, position, H_TAKE_EDGE, H_QUOTE_EDGE, H_QUOTE_SIZE, H_SOFT_POS_LIMIT)


def _run_ve(state: Dict, depth: OrderDepth, position: int, imbalance: float, enable_skew: bool) -> List[Order]:
    wall = _wall_mid(depth, VE_WALL_QTY)
    if wall is None:
        return []
    state["ve_last_mid"] = wall
    fair = wall
    if enable_skew:
        skew = max(-SKEW_CAP_TICK, min(SKEW_CAP_TICK, VE_SKEW_BETA * imbalance))
        fair += skew
    return _take_and_quote(VE, depth, fair, position, VE_TAKE_EDGE, VE_QUOTE_EDGE, VE_QUOTE_SIZE, VE_SOFT_POS_LIMIT)


# ---------- G1 parity guard ----------------------------------------------


def _run_parity_guard(order_depths: Dict[str, OrderDepth], positions: Dict[str, int]) -> Dict[str, List[Order]]:
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
        intrinsic_floor = s_bid - k
        if best_ask + PARITY_MIN_EDGE > intrinsic_floor:
            continue
        v_pos = positions.get(sym, 0)
        ve_pos = positions.get(VE, 0)
        v_cap = POS_LIMIT[sym] - v_pos
        ve_short_cap = POS_LIMIT[VE] + ve_pos
        ve_best_bid = _best_bid(ve_depth)
        ve_bid_qty = ve_depth.buy_orders.get(ve_best_bid, 0) if ve_best_bid is not None else 0
        fill = min(PARITY_SIZE_CAP, ask_qty, v_cap, ve_short_cap, ve_bid_qty)
        if fill <= 0 or ve_best_bid is None:
            continue
        out.setdefault(sym, []).append(Order(sym, best_ask, fill))
        out.setdefault(VE, []).append(Order(VE, ve_best_bid, -fill))
    return out


# ---------- V2 voucher MM -------------------------------------------------


def _tv_proxy(S: float, K: int) -> float:
    dist = abs(S - K)
    if dist >= TV_W:
        return TV_OTM_FLOOR
    x = 1.0 - dist / TV_W
    if x <= 0.0:
        return TV_OTM_FLOOR
    return max(TV_OTM_FLOOR, TV_A * (x ** TV_POW))


def _voucher_fair(S: float, K: int) -> float:
    intrinsic = max(S - K, 0.0)
    tv = _tv_proxy(S, K)
    fair = intrinsic + tv
    if K + 300 <= S:
        fair = min(fair, intrinsic + TV_DEEP_ITM_MAX_EXCESS)
    fair = min(fair, S)
    return max(0.0, fair)


def _voucher_identity_orders(symbol: str, strike: int, depth: OrderDepth, s_bid: Optional[int], s_ask: Optional[int], position: int) -> List[Order]:
    orders: List[Order] = []
    bought = sold = 0
    cap = VOUCHER_SOFT_CAP
    bb = _best_bid(depth)
    ba = _best_ask(depth)
    if ba is not None and s_bid is not None:
        intrinsic = max(s_bid - strike, 0)
        if ba + VOUCHER_TAKE_SLACK <= intrinsic:
            avail = -depth.sell_orders[ba]
            sz = _clip_buy(position, cap, bought, min(avail, cap))
            if sz > 0:
                orders.append(Order(symbol, ba, sz))
                bought += sz
    if bb is not None and s_ask is not None:
        if bb - VOUCHER_UPPER_SLACK >= s_ask:
            avail = depth.buy_orders[bb]
            sz = _clip_sell(position, cap, sold, min(avail, cap))
            if sz > 0:
                orders.append(Order(symbol, bb, -sz))
                sold += sz
    return orders


def _voucher_passive_orders(symbol: str, strike: int, depth: OrderDepth, S: float, position: int) -> List[Order]:
    orders: List[Order] = []
    bought = sold = 0
    cap = VOUCHER_SOFT_CAP
    bb = _best_bid(depth)
    ba = _best_ask(depth)
    if bb is None and ba is None:
        return orders

    fair = _voucher_fair(S, strike)
    dist = abs(S - strike)
    if strike + 500 <= S:
        buy_edge = sell_edge = 2
    elif dist <= 200:
        buy_edge = sell_edge = 4
    else:
        buy_edge = sell_edge = 3

    buy_px = int(math.floor(fair - buy_edge))
    sell_px = int(math.ceil(fair + sell_edge))
    buy_px = max(buy_px, 0)
    if S > 0:
        sell_px = min(sell_px, int(math.floor(S - VOUCHER_UPPER_SLACK)))
    if bb is not None:
        buy_px = min(buy_px, bb + 1)
    if ba is not None:
        buy_px = min(buy_px, ba - 1)
        sell_px = max(sell_px, ba - 1)
    if bb is not None:
        sell_px = max(sell_px, bb + 1)

    if buy_px > 0:
        sz = _clip_buy(position, cap, bought, VOUCHER_PASSIVE_SIZE)
        if sz > 0 and (ba is None or buy_px < ba):
            orders.append(Order(symbol, buy_px, sz))
            bought += sz
    if sell_px > 0:
        sz = _clip_sell(position, cap, sold, VOUCHER_PASSIVE_SIZE)
        if sz > 0 and (bb is None or sell_px > bb):
            orders.append(Order(symbol, sell_px, -sz))
            sold += sz
    return orders


def _voucher_mono_orders(order_depths: Dict[str, OrderDepth], positions: Dict[str, int]) -> Dict[str, List[Order]]:
    """For K1 < K2, V_K1 >= V_K2. If bid(K2) > ask(K1) + slack, buy K1 / sell K2 for a risk-free arb (bounded payoff)."""
    out: Dict[str, List[Order]] = {}
    strikes = sorted(VOUCHER_STRIKES)
    syms = {k: f"VEV_{k}" for k in strikes}
    for i in range(len(strikes) - 1):
        k1, k2 = strikes[i], strikes[i + 1]
        s1, s2 = syms[k1], syms[k2]
        d1 = order_depths.get(s1)
        d2 = order_depths.get(s2)
        if d1 is None or d2 is None:
            continue
        a1 = _best_ask(d1)
        b2 = _best_bid(d2)
        if a1 is None or b2 is None:
            continue
        if b2 <= a1 + VOUCHER_MONO_SLACK:
            continue
        size = min(-d1.sell_orders[a1], d2.buy_orders[b2], VOUCHER_SOFT_CAP)
        p1 = positions.get(s1, 0)
        p2 = positions.get(s2, 0)
        bsz = _clip_buy(p1, VOUCHER_SOFT_CAP, 0, size)
        ssz = _clip_sell(p2, VOUCHER_SOFT_CAP, 0, size)
        pair = min(bsz, ssz)
        if pair <= 0:
            continue
        out.setdefault(s1, []).append(Order(s1, a1, pair))
        out.setdefault(s2, []).append(Order(s2, b2, -pair))
    return out


# ---------- state ---------------------------------------------------------


def _load_state(raw: str) -> Dict:
    base = {"schema": TRADER_DATA_SCHEMA, "flags": dict(DEFAULT_FLAGS), "h_ema": None, "ve_last_mid": None}
    if not raw:
        return base
    try:
        data = json.loads(raw)
    except Exception:
        return base
    flags = dict(DEFAULT_FLAGS)
    flags.update(data.get("flags", {}))
    return {
        "schema": TRADER_DATA_SCHEMA,
        "flags": flags,
        "h_ema": data.get("h_ema"),
        "ve_last_mid": data.get("ve_last_mid"),
    }


def _dump_state(state: Dict) -> str:
    raw = json.dumps({
        "schema": TRADER_DATA_SCHEMA,
        "flags": state["flags"],
        "h_ema": state["h_ema"],
        "ve_last_mid": state["ve_last_mid"],
    }, separators=(",", ":"))
    if len(raw) > TRADER_DATA_MAX_BYTES:
        raw = raw[:TRADER_DATA_MAX_BYTES]
    return raw


# ---------- Trader --------------------------------------------------------


class Trader:
    def run(self, state: TradingState):
        td = _load_state(state.traderData or "")
        flags = td["flags"]
        orders: Dict[str, List[Order]] = {}

        h_depth = state.order_depths.get(HYDROGEL)
        ve_depth = state.order_depths.get(VE)

        h_imb = _top_k_imbalance(h_depth, IMB_K_LEVELS) if h_depth is not None else 0.0
        ve_imb = _top_k_imbalance(ve_depth, IMB_K_LEVELS) if ve_depth is not None else 0.0
        enable_skew = bool(flags.get("imbalance_skew", True))

        if flags.get("mm_hydrogel", True) and h_depth is not None:
            legs = _run_hydrogel(td, h_depth, state.position.get(HYDROGEL, 0), h_imb, enable_skew)
            if legs:
                orders[HYDROGEL] = legs

        if flags.get("mm_ve", True) and ve_depth is not None:
            legs = _run_ve(td, ve_depth, state.position.get(VE, 0), ve_imb, enable_skew)
            if legs:
                orders[VE] = legs

        if flags.get("parity_guard", True):
            for sym, legs in _run_parity_guard(state.order_depths, state.position).items():
                orders.setdefault(sym, []).extend(legs)

        if flags.get("voucher_mm", True):
            S_ref = _microprice(ve_depth) if ve_depth is not None else None
            s_bid = _best_bid(ve_depth) if ve_depth is not None else None
            s_ask = _best_ask(ve_depth) if ve_depth is not None else None
            if S_ref is not None:
                for k in VOUCHER_STRIKES:
                    sym = f"VEV_{k}"
                    depth = state.order_depths.get(sym)
                    if depth is None:
                        continue
                    pos = state.position.get(sym, 0)
                    legs = _voucher_identity_orders(sym, k, depth, s_bid, s_ask, pos)
                    if legs:
                        orders.setdefault(sym, []).extend(legs)
                    if k in VOUCHER_PASSIVE_STRIKES:
                        legs = _voucher_passive_orders(sym, k, depth, S_ref, pos)
                        if legs:
                            orders.setdefault(sym, []).extend(legs)
                for sym, legs in _voucher_mono_orders(state.order_depths, state.position).items():
                    orders.setdefault(sym, []).extend(legs)

        return orders, 0, _dump_state(td)

    def bid(self) -> int:
        return 20
