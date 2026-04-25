"""Round 3 10k-or-bust v03 — Scale HYDROGEL + add depth-ladder quoting.

v01 local: +99,529 (HYDROGEL 78,748, VFE 8,211, VEV_4000 6,458, VEV_4500 5,750).
v02 local: +94,836 (regressed on too-aggressive size, added inside-book voucher).

v03 = v01 base + depth-ladder quoting on HYDROGEL (two tiers) for higher capacity
utilization without one-tier adverse selection.
"""

import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


HYDROGEL = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"
VOUCHER_PREFIX_CANDIDATES = ("VEV_",)
VOUCHER_STRIKE_MIN = 4000
VOUCHER_STRIKE_MAX = 6500

CAP_HYDROGEL = 200
CAP_VFE = 200
CAP_VOUCHER = 300

HYDROGEL_ANCHOR = 10000.0
HYDROGEL_ANCHOR_WEIGHT = 0.40
FV_EWMA_ALPHA_HYD = 0.10
HYD_TAKE_EDGE = 4
HYD_QUOTE_EDGE_1 = 3
HYD_QUOTE_EDGE_2 = 6
HYD_QUOTE_SIZE_1 = 20
HYD_QUOTE_SIZE_2 = 30       # second tier further out
HYD_INV_SKEW_STRENGTH = 2.0
HYD_REGIME_GUARD_DEV = 120.0
HYD_IMB_COEF = 5.0
HYD_IMB_SIZE_LEAN = 0.5

FV_EWMA_ALPHA_VFE = 0.20
VFE_TAKE_EDGE = 1
VFE_QUOTE_EDGE = 1
VFE_QUOTE_SIZE = 40
VFE_INV_SKEW_STRENGTH = 1.5

VOUCHER_SLACK_INTRINSIC = 1
VOUCHER_SLACK_UPPER = 1
VOUCHER_SLACK_MONO = 1
VOUCHER_PASSIVE_ENABLED = True
VOUCHER_PASSIVE_SIZE = 25
VOUCHER_MARKET_WEIGHT = 0.70
VOUCHER_MODEL_WEIGHT = 0.30
TV_A = 55.0
TV_W = 400.0
TV_POW = 1.8
TV_OTM_FLOOR = 0.5
TV_DEEP_ITM_MAX_EXCESS = 2.0
ENABLE_STRIKE_MONOTONICITY = True

TRADER_DATA_SCHEMA = 12
TRADER_DATA_MAX_BYTES = 8000


def _best_bid(depth: OrderDepth) -> Optional[int]:
    return max(depth.buy_orders) if depth.buy_orders else None


def _best_ask(depth: OrderDepth) -> Optional[int]:
    return min(depth.sell_orders) if depth.sell_orders else None


def _mid(depth: OrderDepth) -> Optional[float]:
    b, a = _best_bid(depth), _best_ask(depth)
    return None if b is None or a is None else (b + a) / 2.0


def _microprice(depth: OrderDepth) -> Optional[float]:
    b = _best_bid(depth)
    a = _best_ask(depth)
    if b is None or a is None:
        return None
    bv = depth.buy_orders[b]
    av = -depth.sell_orders[a]
    tot = bv + av
    if tot <= 0:
        return (b + a) / 2.0
    return (a * bv + b * av) / tot


def _imbalance(depth: OrderDepth) -> Optional[float]:
    b = _best_bid(depth)
    a = _best_ask(depth)
    if b is None or a is None:
        return None
    bv = depth.buy_orders[b]
    av = -depth.sell_orders[a]
    tot = bv + av
    if tot <= 0:
        return 0.0
    return (bv - av) / tot


def _parse_voucher_strike(symbol: str) -> Optional[int]:
    if symbol.startswith("VEV_"):
        try:
            return int(symbol[4:])
        except ValueError:
            return None
    return None


def _is_voucher_symbol(symbol: str) -> bool:
    s = _parse_voucher_strike(symbol)
    return s is not None and VOUCHER_STRIKE_MIN <= s <= VOUCHER_STRIKE_MAX


def _clip_buy(pos: int, cap: int, already: int, want: int) -> int:
    return max(0, min(want, cap - (pos + already)))


def _clip_sell(pos: int, cap: int, already: int, want: int) -> int:
    return max(0, min(want, cap + (pos - already)))


def _ewma(prior: Optional[float], sample: float, alpha: float) -> float:
    return sample if prior is None else prior * (1 - alpha) + sample * alpha


def _tv_proxy(S: float, K: int) -> float:
    d = abs(S - K)
    if d >= TV_W:
        return TV_OTM_FLOOR
    x = 1.0 - d / TV_W
    if x <= 0.0:
        return TV_OTM_FLOOR
    return max(TV_OTM_FLOOR, TV_A * (x ** TV_POW))


def _voucher_model_fair(S: float, K: int) -> float:
    intrinsic = max(S - K, 0.0)
    fair = intrinsic + _tv_proxy(S, K)
    if K + 300 <= S:
        fair = min(fair, intrinsic + TV_DEEP_ITM_MAX_EXCESS)
    return max(0.0, min(fair, S))


def _voucher_blended_fair(S: float, K: int, vmid: Optional[float]) -> float:
    m = _voucher_model_fair(S, K)
    if vmid is None:
        return m
    b = VOUCHER_MARKET_WEIGHT * vmid + VOUCHER_MODEL_WEIGHT * m
    return max(max(S - K, 0.0), min(b, S))


def _hydrogel_orders(
    depth: OrderDepth,
    position: int,
    fair: float,
    imbalance: float,
    allow_take: bool,
) -> List[Order]:
    orders: List[Order] = []
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    if bid is None and ask is None:
        return orders
    adj_fair = fair + HYD_IMB_COEF * imbalance
    bought = 0
    sold = 0

    if allow_take:
        if ask is not None and ask + HYD_TAKE_EDGE <= adj_fair:
            avail = -depth.sell_orders[ask]
            sz = _clip_buy(position, CAP_HYDROGEL, bought, min(avail, CAP_HYDROGEL))
            if sz > 0:
                orders.append(Order(HYDROGEL, ask, sz))
                bought += sz
        if bid is not None and bid - HYD_TAKE_EDGE >= adj_fair:
            avail = depth.buy_orders[bid]
            sz = _clip_sell(position, CAP_HYDROGEL, sold, min(avail, CAP_HYDROGEL))
            if sz > 0:
                orders.append(Order(HYDROGEL, bid, -sz))
                sold += sz

    inv = (position + bought - sold) / float(CAP_HYDROGEL)
    inv = max(-1.0, min(1.0, inv))

    buy_lean = max(0.0, 1.0 + HYD_IMB_SIZE_LEAN * imbalance)
    sell_lean = max(0.0, 1.0 - HYD_IMB_SIZE_LEAN * imbalance)

    # tier 1 quotes
    buy_px1 = int(math.floor(adj_fair - HYD_QUOTE_EDGE_1))
    sell_px1 = int(math.ceil(adj_fair + HYD_QUOTE_EDGE_1))
    if bid is not None:
        buy_px1 = min(buy_px1, bid + 1)
    if ask is not None:
        buy_px1 = min(buy_px1, ask - 1)
        sell_px1 = max(sell_px1, ask - 1)
    if bid is not None:
        sell_px1 = max(sell_px1, bid + 1)

    buy_sz1 = _clip_buy(
        position, CAP_HYDROGEL, bought,
        max(0, int(round(HYD_QUOTE_SIZE_1 * buy_lean * max(0.0, 1.0 - HYD_INV_SKEW_STRENGTH * inv))))
    )
    sell_sz1 = _clip_sell(
        position, CAP_HYDROGEL, sold,
        max(0, int(round(HYD_QUOTE_SIZE_1 * sell_lean * max(0.0, 1.0 + HYD_INV_SKEW_STRENGTH * inv))))
    )
    if buy_sz1 > 0 and (ask is None or buy_px1 < ask):
        orders.append(Order(HYDROGEL, buy_px1, buy_sz1))
        bought += buy_sz1
    if sell_sz1 > 0 and (bid is None or sell_px1 > bid):
        orders.append(Order(HYDROGEL, sell_px1, -sell_sz1))
        sold += sell_sz1

    # tier 2 quotes (further from fair; catches bigger moves)
    buy_px2 = int(math.floor(adj_fair - HYD_QUOTE_EDGE_2))
    sell_px2 = int(math.ceil(adj_fair + HYD_QUOTE_EDGE_2))
    if ask is not None:
        buy_px2 = min(buy_px2, ask - 2)
        sell_px2 = max(sell_px2, ask - 1)

    buy_sz2 = _clip_buy(
        position, CAP_HYDROGEL, bought,
        max(0, int(round(HYD_QUOTE_SIZE_2 * buy_lean * max(0.0, 1.0 - HYD_INV_SKEW_STRENGTH * inv))))
    )
    sell_sz2 = _clip_sell(
        position, CAP_HYDROGEL, sold,
        max(0, int(round(HYD_QUOTE_SIZE_2 * sell_lean * max(0.0, 1.0 + HYD_INV_SKEW_STRENGTH * inv))))
    )
    if buy_sz2 > 0 and buy_px2 > 0 and buy_px2 < buy_px1:
        orders.append(Order(HYDROGEL, buy_px2, buy_sz2))
    if sell_sz2 > 0 and sell_px2 > sell_px1:
        orders.append(Order(HYDROGEL, sell_px2, -sell_sz2))

    return orders


def _vfe_orders(
    depth: OrderDepth, position: int, fair: float,
) -> List[Order]:
    orders: List[Order] = []
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    if bid is None and ask is None:
        return orders
    bought = 0
    sold = 0
    if ask is not None and ask + VFE_TAKE_EDGE <= fair:
        avail = -depth.sell_orders[ask]
        sz = _clip_buy(position, CAP_VFE, bought, min(avail, CAP_VFE))
        if sz > 0:
            orders.append(Order(VFE, ask, sz))
            bought += sz
    if bid is not None and bid - VFE_TAKE_EDGE >= fair:
        avail = depth.buy_orders[bid]
        sz = _clip_sell(position, CAP_VFE, sold, min(avail, CAP_VFE))
        if sz > 0:
            orders.append(Order(VFE, bid, -sz))
            sold += sz
    inv = (position + bought - sold) / float(CAP_VFE)
    inv = max(-1.0, min(1.0, inv))
    buy_px = int(math.floor(fair - VFE_QUOTE_EDGE))
    sell_px = int(math.ceil(fair + VFE_QUOTE_EDGE))
    if bid is not None:
        buy_px = min(buy_px, bid + 1)
    if ask is not None:
        buy_px = min(buy_px, ask - 1)
        sell_px = max(sell_px, ask - 1)
    if bid is not None:
        sell_px = max(sell_px, bid + 1)
    buy_sz = _clip_buy(
        position, CAP_VFE, bought,
        max(0, int(round(VFE_QUOTE_SIZE * max(0.0, 1.0 - VFE_INV_SKEW_STRENGTH * inv))))
    )
    sell_sz = _clip_sell(
        position, CAP_VFE, sold,
        max(0, int(round(VFE_QUOTE_SIZE * max(0.0, 1.0 + VFE_INV_SKEW_STRENGTH * inv))))
    )
    if buy_sz > 0 and (ask is None or buy_px < ask):
        orders.append(Order(VFE, buy_px, buy_sz))
    if sell_sz > 0 and (bid is None or sell_px > bid):
        orders.append(Order(VFE, sell_px, -sell_sz))
    return orders


def _voucher_orders(
    symbol: str, strike: int, depth: OrderDepth,
    underlying_ref: Optional[float], position: int, cap: int,
) -> List[Order]:
    if underlying_ref is None:
        return []
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    voucher_mid = _mid(depth)
    intrinsic = max(underlying_ref - strike, 0.0)
    upper = underlying_ref
    orders: List[Order] = []
    bought = 0
    sold = 0
    if ask is not None and ask + VOUCHER_SLACK_INTRINSIC < intrinsic:
        avail = -depth.sell_orders[ask]
        sz = _clip_buy(position, cap, bought, min(avail, cap))
        if sz > 0:
            orders.append(Order(symbol, ask, sz))
            bought += sz
    if bid is not None and bid - VOUCHER_SLACK_UPPER > upper:
        avail = depth.buy_orders[bid]
        sz = _clip_sell(position, cap, sold, min(avail, cap))
        if sz > 0:
            orders.append(Order(symbol, bid, -sz))
            sold += sz
    if VOUCHER_PASSIVE_ENABLED:
        fair = _voucher_blended_fair(underlying_ref, strike, voucher_mid)
        dist = abs(underlying_ref - strike)
        edge = 2 if strike + 500 <= underlying_ref else 3
        buy_px = int(math.floor(fair - edge))
        sell_px = int(math.ceil(fair + edge))
        buy_px = max(buy_px, 1)
        sell_px = min(sell_px, int(math.floor(upper - VOUCHER_SLACK_UPPER)))
        if ask is not None:
            buy_px = min(buy_px, ask - 1)
        if bid is not None:
            sell_px = max(sell_px, bid + 1)
        inv = (position + bought - sold) / float(cap)
        inv = max(-1.0, min(1.0, inv))
        bsz = _clip_buy(position, cap, bought, max(0, int(round(VOUCHER_PASSIVE_SIZE * max(0.0, 1.0 - 1.5 * inv)))))
        ssz = _clip_sell(position, cap, sold, max(0, int(round(VOUCHER_PASSIVE_SIZE * max(0.0, 1.0 + 1.5 * inv)))))
        if bsz > 0 and buy_px > 0 and (ask is None or buy_px < ask):
            orders.append(Order(symbol, buy_px, bsz))
            bought += bsz
        if ssz > 0 and sell_px > buy_px and (bid is None or sell_px > bid):
            orders.append(Order(symbol, sell_px, -ssz))
            sold += ssz
    return orders


def _strike_mono_orders(
    entries: List[Tuple[int, str]],
    depths: Dict[str, OrderDepth],
    positions: Dict[str, int],
    cap: int,
) -> Dict[str, List[Order]]:
    out: Dict[str, List[Order]] = {}
    if not ENABLE_STRIKE_MONOTONICITY:
        return out
    for i in range(len(entries) - 1):
        k1, s1 = entries[i]
        k2, s2 = entries[i + 1]
        d1 = depths.get(s1)
        d2 = depths.get(s2)
        if d1 is None or d2 is None:
            continue
        a1 = _best_ask(d1)
        b2 = _best_bid(d2)
        if a1 is None or b2 is None:
            continue
        if b2 <= a1 + VOUCHER_SLACK_MONO:
            continue
        sz = min(-d1.sell_orders[a1], d2.buy_orders[b2], cap)
        bsz = _clip_buy(positions.get(s1, 0), cap, 0, sz)
        ssz = _clip_sell(positions.get(s2, 0), cap, 0, sz)
        pair = min(bsz, ssz)
        if pair <= 0:
            continue
        out.setdefault(s1, []).append(Order(s1, a1, pair))
        out.setdefault(s2, []).append(Order(s2, b2, -pair))
    return out


class Trader:
    def run(self, state: TradingState):
        orders_out: Dict[str, List[Order]] = {}
        try:
            prior = json.loads(state.traderData) if state.traderData else {}
        except (ValueError, TypeError):
            prior = {}
        fair_state: Dict[str, float] = dict(prior.get("fair", {}) or {})
        seen: Dict[str, int] = dict(prior.get("seen", {}) or {})
        positions = state.position or {}
        depths = state.order_depths or {}

        hyd_depth = depths.get(HYDROGEL)
        hyd_imb = 0.0
        if hyd_depth is not None:
            m = _microprice(hyd_depth)
            if m is not None:
                blend = HYDROGEL_ANCHOR_WEIGHT * HYDROGEL_ANCHOR + (1 - HYDROGEL_ANCHOR_WEIGHT) * m
                fair_state[HYDROGEL] = _ewma(fair_state.get(HYDROGEL), blend, FV_EWMA_ALPHA_HYD)
            i = _imbalance(hyd_depth)
            if i is not None:
                hyd_imb = i

        vfe_depth = depths.get(VFE)
        if vfe_depth is not None:
            m = _microprice(vfe_depth)
            if m is not None:
                fair_state[VFE] = _ewma(fair_state.get(VFE), m, FV_EWMA_ALPHA_VFE)

        if hyd_depth is not None and HYDROGEL in fair_state:
            mm = _mid(hyd_depth)
            allow_take = True
            if mm is not None and abs(mm - fair_state[HYDROGEL]) > HYD_REGIME_GUARD_DEV:
                allow_take = False
            legs = _hydrogel_orders(hyd_depth, positions.get(HYDROGEL, 0),
                                    fair_state[HYDROGEL], hyd_imb, allow_take)
            if legs:
                orders_out[HYDROGEL] = legs

        if vfe_depth is not None and VFE in fair_state:
            legs = _vfe_orders(vfe_depth, positions.get(VFE, 0), fair_state[VFE])
            if legs:
                orders_out[VFE] = legs

        entries: List[Tuple[int, str]] = []
        for sym in depths:
            if sym in (HYDROGEL, VFE):
                continue
            if not _is_voucher_symbol(sym):
                continue
            k = _parse_voucher_strike(sym)
            if k is None:
                continue
            entries.append((k, sym))
            seen[sym] = k
        entries.sort()

        ref = fair_state.get(VFE)
        if ref is None and vfe_depth is not None:
            ref = _mid(vfe_depth)

        for strike, sym in entries:
            vd = depths.get(sym)
            if vd is None:
                continue
            legs = _voucher_orders(sym, strike, vd, ref, positions.get(sym, 0), CAP_VOUCHER)
            if legs:
                orders_out.setdefault(sym, []).extend(legs)

        mono = _strike_mono_orders(entries, depths, positions, CAP_VOUCHER)
        for sym, legs in mono.items():
            orders_out.setdefault(sym, []).extend(legs)

        blob = {"fair": {k: round(v, 4) for k, v in fair_state.items()}, "seen": seen}
        td = json.dumps(blob, separators=(",", ":"))
        if len(td) > TRADER_DATA_MAX_BYTES:
            blob["seen"] = {}
            td = json.dumps(blob, separators=(",", ":"))
        return orders_out, 0, td

    def bid(self) -> int:
        return 20
