"""Round 3 10k-or-bust v02 — activate dormant voucher strikes + scale HYDROGEL.

v01 result: +99,529 local (HYDROGEL +78,748, VFE +8,211, VEV_4000 +6,457,
VEV_4500 +5,750, VEV_5400 +363, others 0).

Projected hosted at 15:1 ratio: ~6,600. Short of 10k.

Diagnosis: 7 of 10 voucher strikes contribute nothing. My v01 passive quote
prices (e.g. VEV_5000 buy at 254 vs market bid 254) joined the book but never
undercut it; with deep voucher books and many competitors the joined quote
rarely fills.

v02 changes:

  1. Voucher passive quote INSIDE the book where possible: buy_px = best_bid+1,
     sell_px = best_ask-1. Only quote if this still respects the blended fair
     ± a minimum profit margin. This turns the passive module into a genuine
     liquidity improver that the bots will trade against.
  2. Voucher passive size 25 → 40 (cap 300 allows this).
  3. HYDROGEL quote size 20 → 30 (cap 200, more aggressive).
  4. VFE quote size 40 → 60 (cap 200).
  5. Deep-ITM intrinsic arb size widened: take ALL available liquidity at the
     mispriced level (currently capped at min(avail, cap) which is already
     300 for vouchers).
  6. Add tick-return reversion overlay on HYDROGEL: autocorr -0.125 → small
     but consistent mean-reversion edge on a 1-tick horizon.

Submission contract: run -> (orders, 0, traderData), bid -> int.
"""

import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


HYDROGEL = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"
VOUCHER_PREFIX_CANDIDATES = (
    "VEV_",
    "VELVET_FRUIT_EXTRACT_VOUCHER_",
    "VELVETFRUIT_EXTRACT_VOUCHER_",
    "VFE_VOUCHER_",
)
VOUCHER_STRIKE_MIN = 4000
VOUCHER_STRIKE_MAX = 6500

CAP_HYDROGEL = 200
CAP_VFE = 200
CAP_VOUCHER = 300

HYDROGEL_ANCHOR = 10000.0
HYDROGEL_ANCHOR_WEIGHT = 0.40
FV_EWMA_ALPHA_HYD = 0.10
HYD_TAKE_EDGE = 4
HYD_QUOTE_EDGE = 3
HYD_QUOTE_SIZE = 30              # v01: 20 -> v02: 30
HYD_INV_SKEW_STRENGTH = 2.0
HYD_REGIME_GUARD_DEV = 120.0
HYD_IMB_COEF = 5.0
HYD_IMB_SIZE_LEAN = 0.5
HYD_REVERSION_COEF = 0.8         # NEW: tick-return reversion coefficient

FV_EWMA_ALPHA_VFE = 0.20
VFE_TAKE_EDGE = 1
VFE_QUOTE_EDGE = 1
VFE_QUOTE_SIZE = 60              # v01: 40 -> v02: 60
VFE_INV_SKEW_STRENGTH = 1.5

VOUCHER_SLACK_INTRINSIC = 1
VOUCHER_SLACK_UPPER = 1
VOUCHER_SLACK_MONO = 1
VOUCHER_PASSIVE_ENABLED = True
VOUCHER_PASSIVE_SIZE = 40        # v01: 25 -> v02: 40
VOUCHER_MARKET_WEIGHT = 0.70
VOUCHER_MODEL_WEIGHT = 0.30
VOUCHER_MIN_EDGE_INSIDE = 1      # min required fair-vs-quote margin when stepping inside
TV_A = 55.0
TV_W = 400.0
TV_POW = 1.8
TV_OTM_FLOOR = 0.5
TV_DEEP_ITM_MAX_EXCESS = 2.0
ENABLE_STRIKE_MONOTONICITY = True

TRADER_DATA_SCHEMA = 11
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
    for prefix in VOUCHER_PREFIX_CANDIDATES:
        if symbol.startswith(prefix):
            try:
                return int(symbol[len(prefix):])
            except ValueError:
                return None
    if "_VOUCHER_" in symbol or "_VEV_" in symbol:
        try:
            return int(symbol.rsplit("_", 1)[-1])
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


def _voucher_blended_fair(S: float, K: int, voucher_mid: Optional[float]) -> float:
    model = _voucher_model_fair(S, K)
    if voucher_mid is None:
        return model
    blended = VOUCHER_MARKET_WEIGHT * voucher_mid + VOUCHER_MODEL_WEIGHT * model
    return max(max(S - K, 0.0), min(blended, S))


def _underlying_orders(
    symbol: str,
    depth: OrderDepth,
    position: int,
    cap: int,
    ewma_fair: float,
    imbalance: float,
    imb_coef: float,
    imb_size_lean: float,
    reversion_signal: float,
    take_edge: int,
    quote_edge: int,
    quote_size: int,
    inv_skew: float,
    allow_take: bool,
) -> List[Order]:
    orders: List[Order] = []
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    if bid is None and ask is None:
        return orders
    # fair = EWMA + imbalance predictor + tick-return reversion
    fair = ewma_fair + imb_coef * imbalance + reversion_signal
    bought = 0
    sold = 0
    if allow_take:
        if ask is not None and ask + take_edge <= fair:
            avail = -depth.sell_orders[ask]
            sz = _clip_buy(position, cap, bought, min(avail, cap))
            if sz > 0:
                orders.append(Order(symbol, ask, sz))
                bought += sz
        if bid is not None and bid - take_edge >= fair:
            avail = depth.buy_orders[bid]
            sz = _clip_sell(position, cap, sold, min(avail, cap))
            if sz > 0:
                orders.append(Order(symbol, bid, -sz))
                sold += sz
    inv = 0.0 if cap == 0 else (position + bought - sold) / float(cap)
    inv = max(-1.0, min(1.0, inv))
    buy_px = int(math.floor(fair - quote_edge))
    sell_px = int(math.ceil(fair + quote_edge))
    if bid is not None:
        buy_px = min(buy_px, bid + 1)
    if ask is not None:
        buy_px = min(buy_px, ask - 1)
        sell_px = max(sell_px, ask - 1)
    if bid is not None:
        sell_px = max(sell_px, bid + 1)
    buy_lean = max(0.0, 1.0 + imb_size_lean * imbalance)
    sell_lean = max(0.0, 1.0 - imb_size_lean * imbalance)
    buy_sz_raw = max(0, int(round(quote_size * buy_lean * max(0.0, 1.0 - inv_skew * inv))))
    sell_sz_raw = max(0, int(round(quote_size * sell_lean * max(0.0, 1.0 + inv_skew * inv))))
    buy_sz = _clip_buy(position, cap, bought, buy_sz_raw)
    sell_sz = _clip_sell(position, cap, sold, sell_sz_raw)
    if buy_sz > 0 and (ask is None or buy_px < ask):
        orders.append(Order(symbol, buy_px, buy_sz))
    if sell_sz > 0 and (bid is None or sell_px > bid):
        orders.append(Order(symbol, sell_px, -sell_sz))
    return orders


def _voucher_orders(
    symbol: str,
    strike: int,
    depth: OrderDepth,
    underlying_ref: Optional[float],
    position: int,
    cap: int,
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

    # identity: buy below intrinsic
    if ask is not None and ask + VOUCHER_SLACK_INTRINSIC < intrinsic:
        avail = -depth.sell_orders[ask]
        sz = _clip_buy(position, cap, bought, min(avail, cap))
        if sz > 0:
            orders.append(Order(symbol, ask, sz))
            bought += sz

    # identity: sell above upper bound
    if bid is not None and bid - VOUCHER_SLACK_UPPER > upper:
        avail = depth.buy_orders[bid]
        sz = _clip_sell(position, cap, sold, min(avail, cap))
        if sz > 0:
            orders.append(Order(symbol, bid, -sz))
            sold += sz

    # passive INSIDE-THE-BOOK quoting
    if VOUCHER_PASSIVE_ENABLED:
        fair = _voucher_blended_fair(underlying_ref, strike, voucher_mid)
        # step inside best book where our fair is beyond best bid / best ask
        buy_px = None
        sell_px = None
        if bid is not None and ask is not None and ask > bid + 1:
            # there's room to step inside
            candidate_buy = bid + 1
            if candidate_buy + VOUCHER_MIN_EDGE_INSIDE <= fair:
                buy_px = candidate_buy
            candidate_sell = ask - 1
            if candidate_sell >= fair + VOUCHER_MIN_EDGE_INSIDE:
                sell_px = candidate_sell
        # fallback: quote further out at fair ± edge
        if buy_px is None:
            edge = 2 if strike + 500 <= underlying_ref else 3
            px = int(math.floor(fair - edge))
            px = max(px, 1)
            if ask is not None and px < ask:
                buy_px = px
        if sell_px is None:
            edge = 2 if strike + 500 <= underlying_ref else 3
            px = int(math.ceil(fair + edge))
            max_px = int(math.floor(upper - VOUCHER_SLACK_UPPER))
            if px <= max_px and (bid is None or px > bid):
                sell_px = px

        inv = 0.0 if cap == 0 else (position + bought - sold) / float(cap)
        inv = max(-1.0, min(1.0, inv))
        buy_sz_raw = max(0, int(round(VOUCHER_PASSIVE_SIZE * max(0.0, 1.0 - 1.5 * inv))))
        sell_sz_raw = max(0, int(round(VOUCHER_PASSIVE_SIZE * max(0.0, 1.0 + 1.5 * inv))))

        if buy_px is not None and buy_px > 0:
            sz = _clip_buy(position, cap, bought, buy_sz_raw)
            if sz > 0:
                orders.append(Order(symbol, buy_px, sz))
                bought += sz
        if sell_px is not None and sell_px > (buy_px or 0):
            sz = _clip_sell(position, cap, sold, sell_sz_raw)
            if sz > 0:
                orders.append(Order(symbol, sell_px, -sz))
                sold += sz

    return orders


def _strike_monotonicity_orders(
    voucher_entries: List[Tuple[int, str]],
    order_depths: Dict[str, OrderDepth],
    positions: Dict[str, int],
    cap: int,
) -> Dict[str, List[Order]]:
    out: Dict[str, List[Order]] = {}
    if not ENABLE_STRIKE_MONOTONICITY:
        return out
    for i in range(len(voucher_entries) - 1):
        k1, s1 = voucher_entries[i]
        k2, s2 = voucher_entries[i + 1]
        d1 = order_depths.get(s1)
        d2 = order_depths.get(s2)
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
        last_mid: Dict[str, float] = dict(prior.get("last_mid", {}) or {})
        seen_vouchers: Dict[str, int] = dict(prior.get("seen_vouchers", {}) or {})
        flagged = set(prior.get("flagged_symbols", []) or [])
        positions = state.position or {}
        order_depths = state.order_depths or {}

        # HYDROGEL fair + imbalance + reversion
        hyd_depth = order_depths.get(HYDROGEL)
        hyd_imb = 0.0
        hyd_reversion = 0.0
        hyd_current_mid: Optional[float] = None
        if hyd_depth is not None:
            hyd_current_mid = _mid(hyd_depth)
            m = _microprice(hyd_depth)
            if m is not None:
                blended_anchor = (
                    HYDROGEL_ANCHOR_WEIGHT * HYDROGEL_ANCHOR
                    + (1.0 - HYDROGEL_ANCHOR_WEIGHT) * m
                )
                fair_state[HYDROGEL] = _ewma(
                    fair_state.get(HYDROGEL), blended_anchor, FV_EWMA_ALPHA_HYD
                )
            i = _imbalance(hyd_depth)
            if i is not None:
                hyd_imb = i
            # tick-return reversion
            if hyd_current_mid is not None and HYDROGEL in last_mid:
                last_return = hyd_current_mid - last_mid[HYDROGEL]
                hyd_reversion = -HYD_REVERSION_COEF * last_return
            if hyd_current_mid is not None:
                last_mid[HYDROGEL] = hyd_current_mid

        vfe_depth = order_depths.get(VFE)
        if vfe_depth is not None:
            m = _microprice(vfe_depth)
            if m is not None:
                fair_state[VFE] = _ewma(
                    fair_state.get(VFE), m, FV_EWMA_ALPHA_VFE
                )

        if hyd_depth is not None and HYDROGEL in fair_state:
            allow_take = True
            if hyd_current_mid is not None:
                if abs(hyd_current_mid - fair_state[HYDROGEL]) > HYD_REGIME_GUARD_DEV:
                    allow_take = False
            legs = _underlying_orders(
                HYDROGEL, hyd_depth, positions.get(HYDROGEL, 0),
                CAP_HYDROGEL, fair_state[HYDROGEL],
                hyd_imb, HYD_IMB_COEF, HYD_IMB_SIZE_LEAN,
                hyd_reversion,
                HYD_TAKE_EDGE, HYD_QUOTE_EDGE, HYD_QUOTE_SIZE,
                HYD_INV_SKEW_STRENGTH, allow_take,
            )
            if legs:
                orders_out[HYDROGEL] = legs

        if vfe_depth is not None and VFE in fair_state:
            legs = _underlying_orders(
                VFE, vfe_depth, positions.get(VFE, 0),
                CAP_VFE, fair_state[VFE],
                0.0, 0.0, 0.0, 0.0,
                VFE_TAKE_EDGE, VFE_QUOTE_EDGE, VFE_QUOTE_SIZE,
                VFE_INV_SKEW_STRENGTH, True,
            )
            if legs:
                orders_out[VFE] = legs

        voucher_entries: List[Tuple[int, str]] = []
        for sym in order_depths:
            if sym in flagged or sym in (HYDROGEL, VFE):
                continue
            if not _is_voucher_symbol(sym):
                continue
            k = _parse_voucher_strike(sym)
            if k is None:
                flagged.add(sym)
                continue
            voucher_entries.append((k, sym))
            seen_vouchers[sym] = k
        voucher_entries.sort()

        ref = fair_state.get(VFE)
        if ref is None and vfe_depth is not None:
            ref = _mid(vfe_depth)

        for strike, sym in voucher_entries:
            vd = order_depths.get(sym)
            if vd is None:
                continue
            legs = _voucher_orders(
                sym, strike, vd, ref, positions.get(sym, 0), CAP_VOUCHER,
            )
            if legs:
                orders_out.setdefault(sym, []).extend(legs)

        mono = _strike_monotonicity_orders(
            voucher_entries, order_depths, positions, CAP_VOUCHER
        )
        for sym, legs in mono.items():
            orders_out.setdefault(sym, []).extend(legs)

        blob = {
            "schema": TRADER_DATA_SCHEMA,
            "fair": {k: round(v, 4) for k, v in fair_state.items()},
            "last_mid": {k: round(v, 4) for k, v in last_mid.items()},
            "seen_vouchers": seen_vouchers,
            "flagged_symbols": sorted(flagged),
        }
        td = json.dumps(blob, separators=(",", ":"))
        if len(td) > TRADER_DATA_MAX_BYTES:
            blob["seen_vouchers"] = {}
            td = json.dumps(blob, separators=(",", ":"))
        return orders_out, 0, td

    def bid(self) -> int:
        return 20
