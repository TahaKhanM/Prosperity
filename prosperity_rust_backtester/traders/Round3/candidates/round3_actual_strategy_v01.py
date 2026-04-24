"""Round 3 actual strategy v01.

Live-state adaptive multi-product trader for the Round 3 product set:
  - HYDROGEL_PACKS
  - VELVET_FRUIT_EXTRACT (VFE)
  - VELVET_FRUIT_EXTRACT vouchers (strike parsed from symbol tail)

Design:

  * Fair-value estimator:   EWMA of microprice, bootstrapped from first mid.
  * Market-making module:   two-sided quotes around fair, inventory-skewed.
  * Taking module:          cross the book only when the ask is < fair - take_edge
                            or the bid is > fair + take_edge.
  * Voucher intrinsic arb:  buy voucher when ask + slack < max(S-K, 0);
                            sell voucher when bid - slack > S.
  * Voucher passive fair:   quote passive bid/ask around intrinsic + small
                            adaptive time-value, inside a conservative band.
  * Strike monotonicity:    V_{K1} >= V_{K2} for K1 < K2; sell K1 / buy K2
                            on a confirmed violation.
  * Risk clipping:          every order passes _clip_buy / _clip_sell.
  * No-op fallback:         unknown symbols, empty books, or missing VFE mid
                            for voucher module.

All parameters are conservative because Round 3 data is not in the sandbox;
they are the live-state fallbacks that become recalibration targets once
`datasets/round3/` is populated.

Submission contract:
  run(state) -> (orders_dict, conversions=0, traderData_json_str)
  bid()      -> int
"""

import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


# --- product allowlist --------------------------------------------------------

HYDROGEL = "HYDROGEL_PACKS"
VFE = "VELVET_FRUIT_EXTRACT"
VOUCHER_PREFIX_CANDIDATES = (
    "VELVET_FRUIT_EXTRACT_VOUCHER_",
    "VFE_VOUCHER_",
)

# position caps. 50 is mid-range between Round1/2's 80 and a safe floor.
# If the real Round 3 caps are published lower, clipping still blocks breach.
CAP_HYDROGEL = 50
CAP_VFE = 50
CAP_VOUCHER = 50

# voucher strike window from the briefing. Symbols outside this skip.
VOUCHER_STRIKE_MIN = 4000
VOUCHER_STRIKE_MAX = 6500

# EWMA on microprice. Small alpha so the fair adapts but is not whipped by a
# single tick.
FV_EWMA_ALPHA = 0.08

# taking thresholds (in XY per unit). Conservative: require meaningful edge.
TAKE_EDGE = 2

# passive quote edge (distance from fair for each side).
QUOTE_EDGE_UNDERLYING = 2
QUOTE_SIZE_UNDERLYING = 6

# voucher identity slack. Small, because these are hard identities.
VOUCHER_SLACK_INTRINSIC = 1
VOUCHER_SLACK_UPPER = 1
VOUCHER_SLACK_MONO = 1

# voucher passive quoting. Provide liquidity around intrinsic + conservative
# time-value proxy.
VOUCHER_PASSIVE_ENABLED = True
VOUCHER_PASSIVE_EDGE_BID = 4   # willing to be long at intrinsic - 4
VOUCHER_PASSIVE_EDGE_ASK = 6   # willing to be short at intrinsic + 6
VOUCHER_PASSIVE_SIZE = 3

# enable strike-monotonicity arb. This is an identity, safe to leave on.
ENABLE_STRIKE_MONOTONICITY = True

TRADER_DATA_SCHEMA = 2
TRADER_DATA_MAX_BYTES = 8000


# --- helpers ------------------------------------------------------------------


def _best_bid(depth: OrderDepth) -> Optional[int]:
    return max(depth.buy_orders) if depth.buy_orders else None


def _best_ask(depth: OrderDepth) -> Optional[int]:
    return min(depth.sell_orders) if depth.sell_orders else None


def _mid(depth: OrderDepth) -> Optional[float]:
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    if bid is None or ask is None:
        return None
    return (bid + ask) / 2.0


def _microprice(depth: OrderDepth) -> Optional[float]:
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    if bid is None or ask is None:
        return None
    bv = depth.buy_orders[bid]
    av = -depth.sell_orders[ask]
    total = bv + av
    if total <= 0:
        return (bid + ask) / 2.0
    return (ask * bv + bid * av) / total


def _parse_voucher_strike(symbol: str) -> Optional[int]:
    for prefix in VOUCHER_PREFIX_CANDIDATES:
        if symbol.startswith(prefix):
            tail = symbol[len(prefix):]
            try:
                return int(tail)
            except ValueError:
                return None
    if "_VOUCHER_" in symbol:
        tail = symbol.rsplit("_", 1)[-1]
        try:
            return int(tail)
        except ValueError:
            return None
    return None


def _known_round3_symbol(symbol: str) -> bool:
    if symbol in (HYDROGEL, VFE):
        return True
    strike = _parse_voucher_strike(symbol)
    if strike is None:
        return False
    return VOUCHER_STRIKE_MIN <= strike <= VOUCHER_STRIKE_MAX


def _clip_buy(current_pos: int, cap: int, already_buying: int, want: int) -> int:
    headroom = cap - (current_pos + already_buying)
    return max(0, min(want, headroom))


def _clip_sell(current_pos: int, cap: int, already_selling: int, want: int) -> int:
    headroom = cap + (current_pos - already_selling)
    return max(0, min(want, headroom))


def _update_fair_ewma(prior: Optional[float], sample: float) -> float:
    if prior is None:
        return sample
    return prior * (1.0 - FV_EWMA_ALPHA) + sample * FV_EWMA_ALPHA


# --- underlying market-making module -----------------------------------------


def _underlying_orders(
    symbol: str,
    depth: OrderDepth,
    position: int,
    cap: int,
    fair: float,
    take_edge: int,
    quote_edge: int,
    quote_size: int,
) -> List[Order]:
    orders: List[Order] = []
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    if bid is None and ask is None:
        return orders

    bought = 0
    sold = 0

    # --- take ---
    if ask is not None and ask + take_edge <= fair:
        avail = -depth.sell_orders[ask]
        size = _clip_buy(position, cap, bought, min(avail, cap))
        if size > 0:
            orders.append(Order(symbol, ask, size))
            bought += size

    if bid is not None and bid - take_edge >= fair:
        avail = depth.buy_orders[bid]
        size = _clip_sell(position, cap, sold, min(avail, cap))
        if size > 0:
            orders.append(Order(symbol, bid, -size))
            sold += size

    # --- make ---
    # inventory skew: reduce the side that would grow our position further.
    inv_ratio = 0.0 if cap == 0 else (position + bought - sold) / float(cap)
    inv_ratio = max(-1.0, min(1.0, inv_ratio))

    # fair rounded down for bid, up for ask so our quote never crosses fair.
    buy_px = int(math.floor(fair - quote_edge))
    sell_px = int(math.ceil(fair + quote_edge))

    # if book has a best quote, do not quote through it in a silly way.
    if bid is not None:
        buy_px = min(buy_px, bid + 1)  # be willing to join / step in front by 1
        buy_px = min(buy_px, ask - 1) if ask is not None else buy_px
    if ask is not None:
        sell_px = max(sell_px, ask - 1)
        sell_px = max(sell_px, bid + 1) if bid is not None else sell_px

    # size skew by inventory
    buy_size_raw = max(0, int(round(quote_size * (1.0 - inv_ratio))))
    sell_size_raw = max(0, int(round(quote_size * (1.0 + inv_ratio))))

    buy_size = _clip_buy(position, cap, bought, buy_size_raw)
    sell_size = _clip_sell(position, cap, sold, sell_size_raw)

    if buy_size > 0 and (ask is None or buy_px < ask):
        orders.append(Order(symbol, buy_px, buy_size))
    if sell_size > 0 and (bid is None or sell_px > bid):
        orders.append(Order(symbol, sell_px, -sell_size))

    return orders


# --- voucher module -----------------------------------------------------------


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
    intrinsic = max(underlying_ref - strike, 0.0)
    upper_bound = underlying_ref  # V <= S

    orders: List[Order] = []
    bought = 0
    sold = 0

    # --- identity arb: buy below intrinsic floor ---
    if ask is not None and ask + VOUCHER_SLACK_INTRINSIC < intrinsic:
        avail = -depth.sell_orders[ask]
        size = _clip_buy(position, cap, bought, min(avail, cap))
        if size > 0:
            orders.append(Order(symbol, ask, size))
            bought += size

    # --- identity arb: sell above S upper bound ---
    if bid is not None and bid - VOUCHER_SLACK_UPPER > upper_bound:
        avail = depth.buy_orders[bid]
        size = _clip_sell(position, cap, sold, min(avail, cap))
        if size > 0:
            orders.append(Order(symbol, bid, -size))
            sold += size

    # --- passive quoting around intrinsic ---
    if VOUCHER_PASSIVE_ENABLED:
        # conservative: only quote if intrinsic > 0 (ITM / ATM). Deep-OTM we
        # abstain because the fair is near zero and unmodelled time value
        # could swamp our slack.
        if intrinsic > 0:
            passive_bid_px = int(math.floor(intrinsic - VOUCHER_PASSIVE_EDGE_BID))
            passive_ask_px = int(math.ceil(intrinsic + VOUCHER_PASSIVE_EDGE_ASK))
            # never quote above the structural upper bound
            passive_ask_px = min(
                passive_ask_px, int(math.floor(upper_bound - VOUCHER_SLACK_UPPER))
            )
            # respect the best book so we never cross
            if ask is not None:
                passive_bid_px = min(passive_bid_px, ask - 1)
            if bid is not None:
                passive_ask_px = max(passive_ask_px, bid + 1)

            buy_sz = _clip_buy(position, cap, bought, VOUCHER_PASSIVE_SIZE)
            sell_sz = _clip_sell(position, cap, sold, VOUCHER_PASSIVE_SIZE)

            if buy_sz > 0 and passive_bid_px > 0 and (ask is None or passive_bid_px < ask):
                orders.append(Order(symbol, passive_bid_px, buy_sz))
                bought += buy_sz
            if sell_sz > 0 and passive_ask_px > passive_bid_px and (
                bid is None or passive_ask_px > bid
            ):
                orders.append(Order(symbol, passive_ask_px, -sell_sz))
                sold += sell_sz

    return orders


def _strike_monotonicity_orders(
    voucher_entries: List[Tuple[int, str]],
    order_depths: Dict[str, OrderDepth],
    positions: Dict[str, int],
    cap: int,
) -> Dict[str, List[Order]]:
    result: Dict[str, List[Order]] = {}
    if not ENABLE_STRIKE_MONOTONICITY:
        return result
    # V_{K1} >= V_{K2} for K1 < K2  =>  violation: bid(V_{K2}) > ask(V_{K1}).
    for i in range(len(voucher_entries) - 1):
        k1, s1 = voucher_entries[i]
        k2, s2 = voucher_entries[i + 1]
        d1 = order_depths.get(s1)
        d2 = order_depths.get(s2)
        if d1 is None or d2 is None:
            continue
        ask1 = _best_ask(d1)
        bid2 = _best_bid(d2)
        if ask1 is None or bid2 is None:
            continue
        if bid2 <= ask1 + VOUCHER_SLACK_MONO:
            continue
        vol_ask1 = -d1.sell_orders[ask1]
        vol_bid2 = d2.buy_orders[bid2]
        size = min(vol_ask1, vol_bid2, cap)
        pos1 = positions.get(s1, 0)
        pos2 = positions.get(s2, 0)
        bsz = _clip_buy(pos1, cap, 0, size)
        ssz = _clip_sell(pos2, cap, 0, size)
        pair = min(bsz, ssz)
        if pair <= 0:
            continue
        result.setdefault(s1, []).append(Order(s1, ask1, pair))
        result.setdefault(s2, []).append(Order(s2, bid2, -pair))
    return result


# --- trader -------------------------------------------------------------------


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

        # ---- underlying fair-value updates ----
        for underlying in (HYDROGEL, VFE):
            depth = order_depths.get(underlying)
            if depth is None:
                continue
            micro = _microprice(depth)
            if micro is None:
                continue
            fair_state[underlying] = _update_fair_ewma(
                fair_state.get(underlying), micro
            )

        # ---- HYDROGEL_PACKS trading ----
        hyd_depth = order_depths.get(HYDROGEL)
        if hyd_depth is not None and HYDROGEL in fair_state:
            pos = positions.get(HYDROGEL, 0)
            legs = _underlying_orders(
                HYDROGEL,
                hyd_depth,
                pos,
                CAP_HYDROGEL,
                fair_state[HYDROGEL],
                TAKE_EDGE,
                QUOTE_EDGE_UNDERLYING,
                QUOTE_SIZE_UNDERLYING,
            )
            if legs:
                orders_out[HYDROGEL] = legs

        # ---- VELVET_FRUIT_EXTRACT trading ----
        vfe_depth = order_depths.get(VFE)
        if vfe_depth is not None and VFE in fair_state:
            pos = positions.get(VFE, 0)
            legs = _underlying_orders(
                VFE,
                vfe_depth,
                pos,
                CAP_VFE,
                fair_state[VFE],
                TAKE_EDGE,
                QUOTE_EDGE_UNDERLYING,
                QUOTE_SIZE_UNDERLYING,
            )
            if legs:
                orders_out[VFE] = legs

        # ---- voucher module ----
        voucher_entries: List[Tuple[int, str]] = []
        for symbol in order_depths:
            if symbol in flagged or symbol in (HYDROGEL, VFE):
                continue
            if not _known_round3_symbol(symbol):
                continue
            strike = _parse_voucher_strike(symbol)
            if strike is None:
                flagged.add(symbol)
                continue
            voucher_entries.append((strike, symbol))
            seen_vouchers[symbol] = strike

        voucher_entries.sort()

        # reference underlying for voucher intrinsic: prefer fair EWMA, fall
        # back to VFE mid, then to nothing.
        underlying_ref: Optional[float] = fair_state.get(VFE)
        if underlying_ref is None and vfe_depth is not None:
            underlying_ref = _mid(vfe_depth)

        for strike, symbol in voucher_entries:
            vdepth = order_depths.get(symbol)
            if vdepth is None:
                continue
            pos = positions.get(symbol, 0)
            legs = _voucher_orders(
                symbol, strike, vdepth, underlying_ref, pos, CAP_VOUCHER
            )
            if legs:
                orders_out.setdefault(symbol, []).extend(legs)

        mono_orders = _strike_monotonicity_orders(
            voucher_entries, order_depths, positions, CAP_VOUCHER
        )
        for sym, legs in mono_orders.items():
            orders_out.setdefault(sym, []).extend(legs)

        # ---- traderData ----
        blob = {
            "schema": TRADER_DATA_SCHEMA,
            "fair": {k: round(v, 4) for k, v in fair_state.items()},
            "seen_vouchers": seen_vouchers,
            "flagged_symbols": sorted(flagged),
        }
        trader_data = json.dumps(blob, separators=(",", ":"))
        if len(trader_data) > TRADER_DATA_MAX_BYTES:
            blob["seen_vouchers"] = {}
            trader_data = json.dumps(blob, separators=(",", ":"))

        return orders_out, 0, trader_data

    def bid(self) -> int:
        return 20
