"""Round 3 strategy family v03 — Imbalance-Signal Predictive MM.

*** Fundamentally different from v02 ***

v02 scored hosted +1,547 (vs +318 prior). VFE +1127, HYDROGEL +314, vouchers +106.
PnL trajectory: -631 -> +366 -> +318 -> +1547. Sharply improving, not plateauing.

Deep analysis of hosted log 371381 revealed a new exploitable signal:

  book_imbalance(t) = (bid_vol_1 - ask_vol_1) / (bid_vol_1 + ask_vol_1)

  correlation with next-tick mid-return:
    HYDROGEL_PACK   : +0.3744
    VFE             : +0.3135

Both strong. v02 does not use this — it reacts via microprice EWMA only.

v03 adds a PREDICTIVE overlay: shift fair value by an imbalance-derived expected
next-tick move. This converts the MM module from reactive to forecasting:

  fair_v03 = microprice_ewma + beta * imbalance * sigma_tick

Where sigma_tick is the 1-tick move scale. For HYDROGEL with stdev 30 and book
spread 15.7, typical 1-tick move is ~2-5 XY; imbalance 0.37 * 0.8 * 5 ≈ 1.5 XY
shift when book heavily leans. For VFE stdev 7.5 and spread 5, 1-tick move ~1-2
XY; imbalance * 0.31 * 2 ≈ 0.5 XY shift.

PnL source is now:
  - Spread capture from MM base (preserved from v02)
  - Directional edge from imbalance signal (NEW)
  - Identity arbs on vouchers (preserved)

Why this should scale beyond v02: imbalance 0.37 correlation is a real predictor,
not a spread-capture artifact. In a 1000-tick hosted day with ~500 strong-
imbalance signals, even 0.5-1 XY edge per signal at size 8 = 2000-4000 XY
extra PnL.

Why drawdown should stay controlled: imbalance shift is CAPPED (clamped to a
max shift). Regime guard kept. Caps kept. If imbalance misfires, the loss is
one-tick bounded.

Reused components (justified):
  - Anchor-free EWMA microprice fair (v02) — base still needed; imbalance is
    an OVERLAY, not a replacement.
  - Wider HYDROGEL take-edge (4) — still needed; imbalance cannot fix the
    wide-spread adverse selection, only bias the quote.
  - Identity-only vouchers — passive on vouchers has been net 0 across 4
    hosted runs; no evidence to re-enable.
  - VFE sized 12/cap 50 — hosted evidence (+1127) validates.

New in v03:
  - Imbalance signal per product
  - Fair-value shift formula
  - Imbalance-biased quote-size asymmetry: lean size toward signal direction

Submission contract: same. run -> (orders, 0, traderData), bid -> int.
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

CAP_HYDROGEL = 30
CAP_VFE = 50
CAP_VOUCHER = 30

# HYDROGEL
FV_EWMA_ALPHA_HYD = 0.10
HYD_TAKE_EDGE = 4
HYD_QUOTE_EDGE = 3
HYD_QUOTE_SIZE = 4
HYD_INV_SKEW_STRENGTH = 2.0
HYD_REGIME_GUARD_DEV = 120.0
# imbalance overlay for HYDROGEL
HYD_IMB_COEF = 5.0       # max fair shift = 5 XY when |imbalance|=1
HYD_IMB_SIZE_LEAN = 0.5  # asymmetry in quote size based on imbalance

# VFE
FV_EWMA_ALPHA_VFE = 0.20
VFE_TAKE_EDGE = 1
VFE_QUOTE_EDGE = 1
VFE_QUOTE_SIZE = 12
VFE_INV_SKEW_STRENGTH = 1.5
# imbalance overlay for VFE
VFE_IMB_COEF = 0.0       # disabled: local backtest showed VFE overlay hurts
VFE_IMB_SIZE_LEAN = 0.0

# Voucher identity-only
VOUCHER_SLACK_INTRINSIC = 1
VOUCHER_SLACK_UPPER = 1
VOUCHER_SLACK_MONO = 1
ENABLE_STRIKE_MONOTONICITY = True

TRADER_DATA_SCHEMA = 9
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
    """Level-1 book imbalance in [-1, 1]. +1 = all bid, -1 = all ask."""
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


def _underlying_orders_v3(
    symbol: str,
    depth: OrderDepth,
    position: int,
    cap: int,
    ewma_fair: float,
    imbalance: float,
    imb_coef: float,
    imb_size_lean: float,
    take_edge: int,
    quote_edge: int,
    quote_size: int,
    inv_skew: float,
    allow_take: bool,
) -> List[Order]:
    """MM with imbalance-shifted fair value and imbalance-leaned quote sizes."""
    orders: List[Order] = []
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    if bid is None and ask is None:
        return orders

    # predictive fair: ewma + imbalance * coef
    fair = ewma_fair + imb_coef * imbalance

    bought = 0
    sold = 0

    # take (now using predictive fair)
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

    # make with inventory skew AND imbalance lean
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

    # imbalance-leaned sizes: positive imbalance -> bigger buy quote
    buy_lean = max(0.0, 1.0 + imb_size_lean * imbalance)
    sell_lean = max(0.0, 1.0 - imb_size_lean * imbalance)

    buy_sz_raw = max(0, int(round(
        quote_size * buy_lean * max(0.0, 1.0 - inv_skew * inv)
    )))
    sell_sz_raw = max(0, int(round(
        quote_size * sell_lean * max(0.0, 1.0 + inv_skew * inv)
    )))
    buy_sz = _clip_buy(position, cap, bought, buy_sz_raw)
    sell_sz = _clip_sell(position, cap, sold, sell_sz_raw)

    if buy_sz > 0 and (ask is None or buy_px < ask):
        orders.append(Order(symbol, buy_px, buy_sz))
    if sell_sz > 0 and (bid is None or sell_px > bid):
        orders.append(Order(symbol, sell_px, -sell_sz))

    return orders


def _voucher_identity_orders(
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
        seen_vouchers: Dict[str, int] = dict(prior.get("seen_vouchers", {}) or {})
        flagged = set(prior.get("flagged_symbols", []) or [])
        positions = state.position or {}
        order_depths = state.order_depths or {}

        # EWMA fair updates
        hyd_depth = order_depths.get(HYDROGEL)
        hyd_imb = 0.0
        if hyd_depth is not None:
            m = _microprice(hyd_depth)
            if m is not None:
                fair_state[HYDROGEL] = _ewma(
                    fair_state.get(HYDROGEL), m, FV_EWMA_ALPHA_HYD
                )
            i = _imbalance(hyd_depth)
            if i is not None:
                hyd_imb = i

        vfe_depth = order_depths.get(VFE)
        vfe_imb = 0.0
        if vfe_depth is not None:
            m = _microprice(vfe_depth)
            if m is not None:
                fair_state[VFE] = _ewma(
                    fair_state.get(VFE), m, FV_EWMA_ALPHA_VFE
                )
            i = _imbalance(vfe_depth)
            if i is not None:
                vfe_imb = i

        # HYDROGEL with imbalance overlay
        if hyd_depth is not None and HYDROGEL in fair_state:
            current_mid = _mid(hyd_depth)
            allow_take = True
            if current_mid is not None:
                if abs(current_mid - fair_state[HYDROGEL]) > HYD_REGIME_GUARD_DEV:
                    allow_take = False
            legs = _underlying_orders_v3(
                HYDROGEL, hyd_depth, positions.get(HYDROGEL, 0),
                CAP_HYDROGEL, fair_state[HYDROGEL],
                hyd_imb, HYD_IMB_COEF, HYD_IMB_SIZE_LEAN,
                HYD_TAKE_EDGE, HYD_QUOTE_EDGE, HYD_QUOTE_SIZE,
                HYD_INV_SKEW_STRENGTH, allow_take,
            )
            if legs:
                orders_out[HYDROGEL] = legs

        # VFE with imbalance overlay
        if vfe_depth is not None and VFE in fair_state:
            legs = _underlying_orders_v3(
                VFE, vfe_depth, positions.get(VFE, 0),
                CAP_VFE, fair_state[VFE],
                vfe_imb, VFE_IMB_COEF, VFE_IMB_SIZE_LEAN,
                VFE_TAKE_EDGE, VFE_QUOTE_EDGE, VFE_QUOTE_SIZE,
                VFE_INV_SKEW_STRENGTH, True,
            )
            if legs:
                orders_out[VFE] = legs

        # Voucher identities
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
            legs = _voucher_identity_orders(
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
