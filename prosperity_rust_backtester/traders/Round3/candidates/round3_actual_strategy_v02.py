"""Round 3 actual strategy v02 — data-calibrated against round3 day_0..day_2.

Real multi-product trader for Round 3 (Salvinar).

Product names are taken from the actual round3 CSVs (NOT from the briefing):
  - HYDROGEL_PACK        (singular)
  - VELVETFRUIT_EXTRACT  (one word)
  - VEV_<strike>         (10 voucher strikes in {4000, 4500, 5000, 5100, 5200,
                          5300, 5400, 5500, 6000, 6500})

Facts observed in round3 day_0 timestamp=0:
  HYDROGEL_PACK mid ≈ 10000  (anchored; EMERALDS-style)
  VELVETFRUIT_EXTRACT mid ≈ 5250
  VEV_4000 mid=1250, intrinsic=1250    (deep-ITM, essentially at intrinsic)
  VEV_4500 mid=750,  intrinsic=750
  VEV_5000 mid=257,  intrinsic=250     (time-value ≈ 7)
  VEV_5100 mid=171.5, intrinsic=150    (time-value ≈ 21.5)
  VEV_5200 mid=101.5, intrinsic=50     (time-value ≈ 51.5)
  VEV_5300 mid=53,   intrinsic=0       (pure time-value)
  VEV_5400 mid=23,   intrinsic=0
  VEV_5500 mid=8.5,  intrinsic=0
  VEV_6000 mid=0.5,  intrinsic=0
  VEV_6500 mid=0.5,  intrinsic=0

This satisfies call-payoff structure: monotone non-increasing in K, convex in
K. The trader uses:

  - HYDROGEL_PACK: anchored market-making (anchor=10000, corrected by EWMA).
  - VELVETFRUIT_EXTRACT: EWMA-microprice market-making (no anchor, drifts).
  - Vouchers:
      * Intrinsic lower-bound arb:  buy if ask + slack < max(S-K, 0)
      * Upper-bound arb:            sell if bid - slack > S
      * Strike-monotonicity arb:    sell V_K1, buy V_K2 when bid(K2)>ask(K1)+slack (K1<K2)
      * Passive liquidity:          two-sided quotes around a fair = intrinsic
                                    + TV_est(moneyness), where TV_est is a
                                    piecewise proxy calibrated from day_0 t=0.

All orders are clipped against per-product caps. State lives in traderData.

Submission contract:
  run(state) -> (orders_dict, conversions=0, traderData_json_str)
  bid()      -> int
"""

import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


# --- product allowlist (from actual round3 CSV) -------------------------------

HYDROGEL = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"

# parse VEV_<int>. Keep the legacy prefixes as fallbacks in case IMC renames
# on the hosted venue.
VOUCHER_PREFIX_CANDIDATES = (
    "VEV_",
    "VELVET_FRUIT_EXTRACT_VOUCHER_",
    "VELVETFRUIT_EXTRACT_VOUCHER_",
    "VFE_VOUCHER_",
)

# observed strike universe (for safety clipping only; the parser accepts any
# parseable trailing int, then this window gates behaviour).
VOUCHER_STRIKE_MIN = 4000
VOUCHER_STRIKE_MAX = 6500

# position caps. Round 3 limits are unpublished; the observed day_0 books
# carry ~67 lots of quote size on the underlyings and 6-25 on vouchers, so a
# 50 cap on underlyings and 30 on vouchers is comfortably under any likely
# published cap and under the worst-case aggregate limit.
CAP_HYDROGEL = 50
CAP_VFE = 50
CAP_VOUCHER = 30

# --- underlying MM parameters -------------------------------------------------

HYDROGEL_ANCHOR = 10000.0       # observed t=0 mid on day_0
FV_EWMA_ALPHA_FAST = 0.15       # VFE: more adaptive
FV_EWMA_ALPHA_SLOW = 0.05       # HYDROGEL: anchored; small correction

TAKE_EDGE_UNDERLYING = 1        # take if the touch crosses fair by >=1
QUOTE_EDGE_UNDERLYING = 2
QUOTE_SIZE_UNDERLYING = 8

# --- voucher parameters -------------------------------------------------------

VOUCHER_SLACK_INTRINSIC = 1
VOUCHER_SLACK_UPPER = 1
VOUCHER_SLACK_MONO = 1

VOUCHER_PASSIVE_ENABLED = True
# passive quoting per strike. edges are chosen so the trader joins / leans on
# the observed book rather than cross. Sizes are small; these are ten
# correlated risks, so aggregate inventory matters.
VOUCHER_PASSIVE_SIZE = 3

# time-value proxy. Calibrated against day_0 t=0 observations above. Captures
# the hump near ATM and decay for deep OTM / deep ITM. Deliberately a single
# simple curve rather than a fitted surface; every parameter is named and
# commented.
# TV(S, K) = A * max(0, 1 - |S - K| / W)^POW  with a floor for very-OTM and
# zero for very-deep-ITM.
TV_A = 55.0          # peak time value at S == K
TV_W = 350.0         # half-width (in XY) where TV tapers to ~0
TV_POW = 1.8         # shape exponent; >1 for convex tapering
TV_OTM_FLOOR = 0.5   # minimum quote time-value for deep-OTM to stay non-negative
TV_DEEP_ITM_MAX_EXCESS = 2.0  # deep-ITM vouchers quoted no more than this above intrinsic

ENABLE_STRIKE_MONOTONICITY = True

TRADER_DATA_SCHEMA = 3
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
    if "_VOUCHER_" in symbol or "_VEV_" in symbol:
        tail = symbol.rsplit("_", 1)[-1]
        try:
            return int(tail)
        except ValueError:
            return None
    return None


def _is_voucher_symbol(symbol: str) -> bool:
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


def _ewma(prior: Optional[float], sample: float, alpha: float) -> float:
    if prior is None:
        return sample
    return prior * (1.0 - alpha) + sample * alpha


def _time_value_proxy(underlying: float, strike: int) -> float:
    """Piecewise time-value proxy, calibrated from day_0 t=0 observations."""
    dist = abs(underlying - strike)
    if dist >= TV_W:
        return TV_OTM_FLOOR
    x = 1.0 - dist / TV_W
    # clamp to [0, 1] before exponentiation
    if x <= 0.0:
        return TV_OTM_FLOOR
    return max(TV_OTM_FLOOR, TV_A * (x ** TV_POW))


def _voucher_fair(underlying: float, strike: int) -> float:
    intrinsic = max(underlying - strike, 0.0)
    tv = _time_value_proxy(underlying, strike)
    fair = intrinsic + tv
    # deep-ITM bound: V should not be much above intrinsic (we have no way to
    # claim the extra TV is real for very-ITM strikes). Cap the quote fair
    # at intrinsic + TV_DEEP_ITM_MAX_EXCESS when deep-ITM.
    if strike + 300 <= underlying:  # deep ITM (at least 300 XY in the money)
        fair = min(fair, intrinsic + TV_DEEP_ITM_MAX_EXCESS)
    # upper-bound: V <= S
    fair = min(fair, underlying)
    return max(0.0, fair)


# --- underlying MM module -----------------------------------------------------


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

    # take
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

    # make — inventory-skewed two-sided quotes
    inv_ratio = 0.0 if cap == 0 else (position + bought - sold) / float(cap)
    inv_ratio = max(-1.0, min(1.0, inv_ratio))

    buy_px = int(math.floor(fair - quote_edge))
    sell_px = int(math.ceil(fair + quote_edge))

    # join / improve by 1 where book already exists; never cross
    if bid is not None:
        buy_px = min(buy_px, bid + 1)
    if ask is not None:
        buy_px = min(buy_px, ask - 1)
        sell_px = max(sell_px, ask - 1)
    if bid is not None:
        sell_px = max(sell_px, bid + 1)

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
    orders: List[Order] = []
    bought = 0
    sold = 0

    # identity 1: buy below intrinsic floor
    if ask is not None and ask + VOUCHER_SLACK_INTRINSIC < intrinsic:
        avail = -depth.sell_orders[ask]
        size = _clip_buy(position, cap, bought, min(avail, cap))
        if size > 0:
            orders.append(Order(symbol, ask, size))
            bought += size

    # identity 2: sell above S upper bound
    if bid is not None and bid - VOUCHER_SLACK_UPPER > underlying_ref:
        avail = depth.buy_orders[bid]
        size = _clip_sell(position, cap, sold, min(avail, cap))
        if size > 0:
            orders.append(Order(symbol, bid, -size))
            sold += size

    # passive quoting around model fair
    if VOUCHER_PASSIVE_ENABLED:
        fair = _voucher_fair(underlying_ref, strike)
        # choose edges: tighter for deep-ITM (where intrinsic pins price),
        # wider near ATM where time-value uncertainty is larger.
        dist = abs(underlying_ref - strike)
        if strike + 500 <= underlying_ref:
            # deep-ITM: pin to intrinsic with tight band
            buy_edge = 2
            sell_edge = 2
        elif dist <= 200:
            # ATM: wide band to avoid adversely selecting time-value shocks
            buy_edge = 4
            sell_edge = 4
        else:
            buy_edge = 3
            sell_edge = 3

        buy_px = int(math.floor(fair - buy_edge))
        sell_px = int(math.ceil(fair + sell_edge))

        # respect hard bounds: never quote below 0, never quote above S,
        # never cross the book.
        buy_px = max(buy_px, 0)
        sell_px = min(sell_px, int(math.floor(underlying_ref - VOUCHER_SLACK_UPPER)))
        if ask is not None:
            buy_px = min(buy_px, ask - 1)
        if bid is not None:
            sell_px = max(sell_px, bid + 1)

        if buy_px > 0 and (ask is None or buy_px < ask):
            sz = _clip_buy(position, cap, bought, VOUCHER_PASSIVE_SIZE)
            if sz > 0:
                orders.append(Order(symbol, buy_px, sz))
                bought += sz
        if sell_px > 0 and sell_px > (bid or -1) and (bid is None or sell_px > bid):
            sz = _clip_sell(position, cap, sold, VOUCHER_PASSIVE_SIZE)
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
    result: Dict[str, List[Order]] = {}
    if not ENABLE_STRIKE_MONOTONICITY:
        return result
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
        size = min(-d1.sell_orders[ask1], d2.buy_orders[bid2], cap)
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

        # --- fair-value updates ---
        hyd_depth = order_depths.get(HYDROGEL)
        if hyd_depth is not None:
            micro = _microprice(hyd_depth)
            if micro is not None:
                # anchored blend: anchor heavily to 10000, correct slowly by microprice
                blended = 0.85 * HYDROGEL_ANCHOR + 0.15 * micro
                fair_state[HYDROGEL] = _ewma(
                    fair_state.get(HYDROGEL), blended, FV_EWMA_ALPHA_SLOW
                )

        vfe_depth = order_depths.get(VFE)
        if vfe_depth is not None:
            micro = _microprice(vfe_depth)
            if micro is not None:
                fair_state[VFE] = _ewma(
                    fair_state.get(VFE), micro, FV_EWMA_ALPHA_FAST
                )

        # --- HYDROGEL_PACK ---
        if hyd_depth is not None and HYDROGEL in fair_state:
            pos = positions.get(HYDROGEL, 0)
            legs = _underlying_orders(
                HYDROGEL, hyd_depth, pos, CAP_HYDROGEL,
                fair_state[HYDROGEL],
                TAKE_EDGE_UNDERLYING, QUOTE_EDGE_UNDERLYING, QUOTE_SIZE_UNDERLYING,
            )
            if legs:
                orders_out[HYDROGEL] = legs

        # --- VELVETFRUIT_EXTRACT ---
        if vfe_depth is not None and VFE in fair_state:
            pos = positions.get(VFE, 0)
            legs = _underlying_orders(
                VFE, vfe_depth, pos, CAP_VFE,
                fair_state[VFE],
                TAKE_EDGE_UNDERLYING, QUOTE_EDGE_UNDERLYING, QUOTE_SIZE_UNDERLYING,
            )
            if legs:
                orders_out[VFE] = legs

        # --- vouchers ---
        voucher_entries: List[Tuple[int, str]] = []
        for symbol in order_depths:
            if symbol in flagged or symbol in (HYDROGEL, VFE):
                continue
            if not _is_voucher_symbol(symbol):
                continue
            strike = _parse_voucher_strike(symbol)
            if strike is None:
                flagged.add(symbol)
                continue
            voucher_entries.append((strike, symbol))
            seen_vouchers[symbol] = strike
        voucher_entries.sort()

        # reference for voucher intrinsic: the EWMA fair of VFE, fallback to mid
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

        # --- traderData ---
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
