"""Round 3 maximal multi-product candidate v01.

Implements two identity-bounded voucher alphas on top of a worst-case-safe
multi-product scaffold:
  - R3-VFE-voucher-intrinsic-arb-v01   (active)
  - R3-VFE-voucher-strike-monotonicity-v01 (default-off; enable via
    `ENABLE_STRIKE_MONOTONICITY = True`)

No directional bets on the underlying. No Black-Scholes. No time-value model.

Symbols not in the Round 3 product allowlist are ignored (no-op). This makes
the trader safe to dry-run against Round 1 / Round 2 datasets for interface
validation.

Submission contract:
  run(state) -> (orders_dict, conversions=0, traderData_json_str)
  bid()      -> int  (Round 2 only; harmless elsewhere)
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

# conservative defaults; real caps unknown until Round 3 data is published.
DEFAULT_CAP_UNDERLYING = 20
DEFAULT_CAP_VOUCHER = 20

# strict safety slack used in the intrinsic-arb gate.
VOUCHER_SLACK_BUY = 2
VOUCHER_SLACK_SELL_UPPER = 2
VOUCHER_SLACK_MONO = 2

# strike-monotonicity alpha is gated off until Round 3 data confirms at least
# one observed violation.
ENABLE_STRIKE_MONOTONICITY = False

# voucher strike window we are willing to quote inside. Matches the briefing.
VOUCHER_STRIKE_MIN = 4000
VOUCHER_STRIKE_MAX = 6500

TRADER_DATA_MAX_BYTES = 8000
TRADER_DATA_SCHEMA = 1


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


def _is_voucher(symbol: str) -> bool:
    return _parse_voucher_strike(symbol) is not None


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


# --- strategy components ------------------------------------------------------


def _voucher_intrinsic_arb_orders(
    symbol: str,
    strike: int,
    depth: OrderDepth,
    underlying_mid: Optional[float],
    position: int,
    cap: int,
) -> List[Order]:
    if underlying_mid is None:
        return []
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    intrinsic = max(underlying_mid - strike, 0.0)
    orders: List[Order] = []
    bought = 0
    sold = 0

    if ask is not None and ask + VOUCHER_SLACK_BUY < intrinsic:
        available = -depth.sell_orders[ask]
        size = _clip_buy(position, cap, bought, min(available, cap))
        if size > 0:
            orders.append(Order(symbol, ask, size))
            bought += size

    if bid is not None and bid - VOUCHER_SLACK_SELL_UPPER > underlying_mid:
        available = depth.buy_orders[bid]
        size = _clip_sell(position, cap, sold, min(available, cap))
        if size > 0:
            orders.append(Order(symbol, bid, -size))
            sold += size

    return orders


def _strike_monotonicity_orders(
    voucher_symbols_sorted: List[Tuple[int, str]],
    order_depths: Dict[str, OrderDepth],
    positions: Dict[str, int],
    cap: int,
) -> Dict[str, List[Order]]:
    result: Dict[str, List[Order]] = {}
    if not ENABLE_STRIKE_MONOTONICITY:
        return result

    # Scan adjacent strike pairs (K1, K2) with K1 < K2. Monotonicity says
    # V_{K1} >= V_{K2}, so a violation is best_bid(V_{K2}) > best_ask(V_{K1}).
    for i in range(len(voucher_symbols_sorted) - 1):
        k1, s1 = voucher_symbols_sorted[i]
        k2, s2 = voucher_symbols_sorted[i + 1]
        d1 = order_depths.get(s1)
        d2 = order_depths.get(s2)
        if d1 is None or d2 is None:
            continue
        ask_low = _best_ask(d1)
        bid_high = _best_bid(d2)
        if ask_low is None or bid_high is None:
            continue
        if bid_high <= ask_low + VOUCHER_SLACK_MONO:
            continue
        size = 1
        vol_low = -d1.sell_orders[ask_low]
        vol_high = d2.buy_orders[bid_high]
        size = min(size, vol_low, vol_high)
        pos1 = positions.get(s1, 0)
        pos2 = positions.get(s2, 0)
        buy_size = _clip_buy(pos1, cap, 0, size)
        sell_size = _clip_sell(pos2, cap, 0, size)
        pair_size = min(buy_size, sell_size)
        if pair_size <= 0:
            continue
        result.setdefault(s1, []).append(Order(s1, ask_low, pair_size))
        result.setdefault(s2, []).append(Order(s2, bid_high, -pair_size))
    return result


# --- trader -------------------------------------------------------------------


class Trader:
    def run(self, state: TradingState):
        orders_out: Dict[str, List[Order]] = {}

        try:
            prior = json.loads(state.traderData) if state.traderData else {}
        except (ValueError, TypeError):
            prior = {}
        flagged = set(prior.get("flagged_symbols", []) or [])
        seen_vouchers = dict(prior.get("seen_vouchers", {}) or {})

        positions = state.position or {}
        order_depths = state.order_depths or {}

        underlying_mid: Optional[float] = None
        vfe_depth = order_depths.get(VFE)
        if vfe_depth is not None:
            underlying_mid = _mid(vfe_depth)

        voucher_entries: List[Tuple[int, str]] = []
        for symbol, depth in order_depths.items():
            if symbol in flagged:
                continue
            if not _known_round3_symbol(symbol):
                # deliberate no-op on unknown symbols (eg. Round 2 products
                # during a structural dry-run).
                continue
            if symbol in (HYDROGEL, VFE):
                # no directional alpha on underlying products in v01.
                continue
            strike = _parse_voucher_strike(symbol)
            if strike is None:
                flagged.add(symbol)
                continue
            voucher_entries.append((strike, symbol))
            seen_vouchers[symbol] = strike

        voucher_entries.sort()

        # intrinsic-arb per voucher
        for strike, symbol in voucher_entries:
            depth = order_depths.get(symbol)
            if depth is None:
                continue
            pos = positions.get(symbol, 0)
            leg = _voucher_intrinsic_arb_orders(
                symbol, strike, depth, underlying_mid, pos, DEFAULT_CAP_VOUCHER
            )
            if leg:
                orders_out.setdefault(symbol, []).extend(leg)

        # optional strike-monotonicity (default off)
        mono_orders = _strike_monotonicity_orders(
            voucher_entries, order_depths, positions, DEFAULT_CAP_VOUCHER
        )
        for sym, leg in mono_orders.items():
            orders_out.setdefault(sym, []).extend(leg)

        trader_data_obj = {
            "schema": TRADER_DATA_SCHEMA,
            "seen_vouchers": seen_vouchers,
            "flagged_symbols": sorted(flagged),
        }
        trader_data = json.dumps(trader_data_obj, separators=(",", ":"))
        if len(trader_data) > TRADER_DATA_MAX_BYTES:
            trader_data_obj["seen_vouchers"] = {}
            trader_data = json.dumps(trader_data_obj, separators=(",", ":"))

        return orders_out, 0, trader_data

    def bid(self) -> int:
        return 20
