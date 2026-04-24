"""Round 3 strategy family v02 — Anchor-Free MM + Wider HYDROGEL Edge + Identity Vouchers.

v01 of this family was a disaster (-156k local). The mean-reversion band for
HYDROGEL was wrong: autocorrelation is tick-level, not daily-band, so a
15/30/60 XY band accumulated losing inventory when price drifted.

Revised diagnosis from data+hosted evidence:

  HYDROGEL microstructure:
    - spread 15.7, depth 24.7, stdev ~30, VR(5)=0.78
    - strong tick-level mean-reversion (autocorr -0.125)
    - MM is the correct family; band-reversion is not
    - BUT: hard anchor at 10000 creates drift risk (369524 disaster)
    - tight take-edge=1 picks off on a 15-pt spread -> adverse selection
    - wide take-edge=3 misses most opportunities
    - midrange take-edge=4 likely optimal: capture >1/4 spread, skip noise

  VFE: spread 4.99, depth 75.6 -> true MM product. Scale aggressively.

  Vouchers: identity arbs (intrinsic floor, upper bound, monotonicity) always
    profitable. Passive quoting adds 0 PnL across 3 hosted runs - DROP it.

v02 changes vs prior best (maximal_pnl_research_v01):

  HYDROGEL:
    - anchor REMOVED entirely. Pure EWMA microprice (protects against drift).
    - take_edge 1 -> 4. captures 1/4 of spread, avoids 1-tick adverse selection.
    - quote_edge 1 -> 3. passive quotes outside touch.
    - size 6 -> 4. reduce per-tick exposure.
    - cap 40 -> 30. tighter than mixed-family choice.
    - regime-guard kept: if current_mid deviates >120 from EWMA fair, halt taking.

  VFE:
    - size 8 -> 12 (evidence: tight spread, deep book, was under-sized).
    - take_edge 2 -> 1. vfe spread is 4.99, edge=1 captures 1 pt of 3-pt spread.
    - quote_edge 2 -> 1. quote just inside touch.
    - cap 50 unchanged.

  Vouchers:
    - ALL PASSIVE QUOTING REMOVED. Only intrinsic-floor / upper-bound /
      monotonicity identity arbs remain.
    - cap per voucher 25 -> 30 (restored).

Fundamentally different from maximal_pnl_research_v01:
  (a) No anchor on HYDROGEL -> protects against hosted-day drift.
  (b) Voucher passive killed -> removes adverse-selection noise that
      contributed 0 PnL in hosted tests.
  (c) VFE sized 50% larger on 33% tighter edge -> 2x expected trade count.
  (d) HYDROGEL edge quadrupled -> 4x fewer trades, but each with 4x edge.

Submission contract:
  run(state) -> (orders_dict, conversions=0, traderData_json_str)
  bid()      -> int
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

# HYDROGEL anchor-free MM
FV_EWMA_ALPHA_HYD = 0.10
HYD_TAKE_EDGE = 4
HYD_QUOTE_EDGE = 3
HYD_QUOTE_SIZE = 4
HYD_INV_SKEW_STRENGTH = 2.0
HYD_REGIME_GUARD_DEV = 120.0  # vs ewma fair, not anchor

# VFE aggressive MM
FV_EWMA_ALPHA_VFE = 0.20
VFE_TAKE_EDGE = 1
VFE_QUOTE_EDGE = 1
VFE_QUOTE_SIZE = 12
VFE_INV_SKEW_STRENGTH = 1.5

# Voucher identity-only
VOUCHER_SLACK_INTRINSIC = 1
VOUCHER_SLACK_UPPER = 1
VOUCHER_SLACK_MONO = 1
ENABLE_STRIKE_MONOTONICITY = True

TRADER_DATA_SCHEMA = 8
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


def _underlying_orders(
    symbol: str,
    depth: OrderDepth,
    position: int,
    cap: int,
    fair: float,
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
    buy_sz_raw = max(0, int(round(quote_size * max(0.0, 1.0 - inv_skew * inv))))
    sell_sz_raw = max(0, int(round(quote_size * max(0.0, 1.0 + inv_skew * inv))))
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

        # fair-value updates (pure microprice, no anchor)
        hyd_depth = order_depths.get(HYDROGEL)
        if hyd_depth is not None:
            m = _microprice(hyd_depth)
            if m is not None:
                fair_state[HYDROGEL] = _ewma(
                    fair_state.get(HYDROGEL), m, FV_EWMA_ALPHA_HYD
                )
        vfe_depth = order_depths.get(VFE)
        if vfe_depth is not None:
            m = _microprice(vfe_depth)
            if m is not None:
                fair_state[VFE] = _ewma(
                    fair_state.get(VFE), m, FV_EWMA_ALPHA_VFE
                )

        # HYDROGEL with regime guard on EWMA-relative deviation
        if hyd_depth is not None and HYDROGEL in fair_state:
            current_mid = _mid(hyd_depth)
            allow_take = True
            if current_mid is not None:
                if abs(current_mid - fair_state[HYDROGEL]) > HYD_REGIME_GUARD_DEV:
                    allow_take = False
            legs = _underlying_orders(
                HYDROGEL, hyd_depth, positions.get(HYDROGEL, 0),
                CAP_HYDROGEL, fair_state[HYDROGEL],
                HYD_TAKE_EDGE, HYD_QUOTE_EDGE, HYD_QUOTE_SIZE,
                HYD_INV_SKEW_STRENGTH, allow_take,
            )
            if legs:
                orders_out[HYDROGEL] = legs

        # VFE aggressive MM
        if vfe_depth is not None and VFE in fair_state:
            legs = _underlying_orders(
                VFE, vfe_depth, positions.get(VFE, 0),
                CAP_VFE, fair_state[VFE],
                VFE_TAKE_EDGE, VFE_QUOTE_EDGE, VFE_QUOTE_SIZE,
                VFE_INV_SKEW_STRENGTH, True,
            )
            if legs:
                orders_out[VFE] = legs

        # Vouchers identity-only
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
