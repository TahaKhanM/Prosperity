"""Round 3 maximal data-driven strategy v01.

Calibrated from the actual round3 day_0..day_2 CSVs installed at
`prosperity_rust_backtester/datasets/round3/`. This is the first data-driven
iteration; the predecessor `round3_actual_strategy_v02.py` scored +26,022 XY
net over 3 days, with per-product attribution:

  HYDROGEL_PACK:        +23,801 (3/3 days profitable)   <- main driver
  VEV_4000:             +3,668  (deep-ITM intrinsic arb)
  VEV_4500:             +1,788  (deep-ITM intrinsic arb)
  VEV_5000..VEV_5500:   +569    (sparse trades; ATM not participating)
  VEV_6000, VEV_6500:   0       (no fills)
  VELVETFRUIT_EXTRACT:  -3,805  (-1674, +2851, -4981)   <- main bleeder

Fixes in v01 relative to v02:

  (A) Voucher passive quoting now anchors to *observed voucher mid* blended
      with the intrinsic-plus-TV model. That stops the ATM strikes from
      quoting below the book and lets us actually capture spread.
  (B) VFE take edge widened from 1 -> 3; VFE quote size reduced 8 -> 4.
      This removes the adverse-selection losses while keeping participation.
  (C) TV_A bumped 55 -> 68 to match observed ATM premium (51.5 at dist 50,
      53 at dist 50, 23 at dist 150).
  (D) Voucher caps stay at 30; 10 correlated strikes -> aggregate risk must
      be bounded.

All changes are attributable to a specific diagnostic from v02 logs.

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

VOUCHER_PREFIX_CANDIDATES = (
    "VEV_",
    "VELVET_FRUIT_EXTRACT_VOUCHER_",
    "VELVETFRUIT_EXTRACT_VOUCHER_",
    "VFE_VOUCHER_",
)
VOUCHER_STRIKE_MIN = 4000
VOUCHER_STRIKE_MAX = 6500

CAP_HYDROGEL = 50
CAP_VFE = 50
CAP_VOUCHER = 30

# --- HYDROGEL (anchored) -----------------------------------------------------

HYDROGEL_ANCHOR = 10000.0
FV_EWMA_ALPHA_HYD = 0.05       # slow; HYDROGEL is anchored
HYD_TAKE_EDGE = 1
HYD_QUOTE_EDGE = 2
HYD_QUOTE_SIZE = 8

# --- VFE (drifting; de-risked in v01) ----------------------------------------

FV_EWMA_ALPHA_VFE = 0.15       # fast EWMA on microprice
VFE_TAKE_EDGE = 3              # v02: 1 -> v01: 3. requires real edge before crossing
VFE_QUOTE_EDGE = 3             # v02: 2 -> v01: 3. wider passive quotes
VFE_QUOTE_SIZE = 4             # v02: 8 -> v01: 4. halve size on the bleeder

# --- voucher parameters (data-driven) ----------------------------------------

VOUCHER_SLACK_INTRINSIC = 1
VOUCHER_SLACK_UPPER = 1
VOUCHER_SLACK_MONO = 1

VOUCHER_PASSIVE_ENABLED = True
VOUCHER_PASSIVE_SIZE = 4       # v02: 3 -> v01: 4 (we now quote at sensible prices)

# weight on the *observed voucher mid* vs the intrinsic+TV model.
# 0.7 observed + 0.3 model means we defer to the market but model bounds it.
VOUCHER_MARKET_WEIGHT = 0.7
VOUCHER_MODEL_WEIGHT = 0.3

# time-value proxy calibrated from day_0 t=0. See v02 docstring for table.
TV_A = 68.0          # v02: 55 -> v01: 68 (match ATM peak)
TV_W = 400.0         # v02: 350 -> v01: 400 (slightly wider skirt)
TV_POW = 1.8
TV_OTM_FLOOR = 0.5
TV_DEEP_ITM_MAX_EXCESS = 2.0

ENABLE_STRIKE_MONOTONICITY = True

TRADER_DATA_SCHEMA = 4
TRADER_DATA_MAX_BYTES = 8000


# --- helpers ------------------------------------------------------------------

def _best_bid(depth: OrderDepth) -> Optional[int]:
    return max(depth.buy_orders) if depth.buy_orders else None


def _best_ask(depth: OrderDepth) -> Optional[int]:
    return min(depth.sell_orders) if depth.sell_orders else None


def _mid(depth: OrderDepth) -> Optional[float]:
    b = _best_bid(depth)
    a = _best_ask(depth)
    if b is None or a is None:
        return None
    return (b + a) / 2.0


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


def _voucher_blended_fair(
    S: float, K: int, voucher_mid: Optional[float]
) -> float:
    model = _voucher_model_fair(S, K)
    if voucher_mid is None:
        return model
    blended = VOUCHER_MARKET_WEIGHT * voucher_mid + VOUCHER_MODEL_WEIGHT * model
    # bound by identities
    intrinsic = max(S - K, 0.0)
    blended = max(blended, intrinsic)
    blended = min(blended, S)
    return blended


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

    # make
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

    buy_sz = _clip_buy(
        position, cap, bought, max(0, int(round(quote_size * (1 - inv))))
    )
    sell_sz = _clip_sell(
        position, cap, sold, max(0, int(round(quote_size * (1 + inv))))
    )

    if buy_sz > 0 and (ask is None or buy_px < ask):
        orders.append(Order(symbol, buy_px, buy_sz))
    if sell_sz > 0 and (bid is None or sell_px > bid):
        orders.append(Order(symbol, sell_px, -sell_sz))

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
    voucher_mid = _mid(depth)
    intrinsic = max(underlying_ref - strike, 0.0)
    upper = underlying_ref

    orders: List[Order] = []
    bought = 0
    sold = 0

    # identity 1: buy below intrinsic
    if ask is not None and ask + VOUCHER_SLACK_INTRINSIC < intrinsic:
        avail = -depth.sell_orders[ask]
        sz = _clip_buy(position, cap, bought, min(avail, cap))
        if sz > 0:
            orders.append(Order(symbol, ask, sz))
            bought += sz

    # identity 2: sell above upper bound
    if bid is not None and bid - VOUCHER_SLACK_UPPER > upper:
        avail = depth.buy_orders[bid]
        sz = _clip_sell(position, cap, sold, min(avail, cap))
        if sz > 0:
            orders.append(Order(symbol, bid, -sz))
            sold += sz

    # passive market-making around blended fair
    if VOUCHER_PASSIVE_ENABLED:
        fair = _voucher_blended_fair(underlying_ref, strike, voucher_mid)
        dist = abs(underlying_ref - strike)
        if strike + 500 <= underlying_ref:
            edge = 2
        elif dist <= 200:
            edge = 3
        else:
            edge = 3
        buy_px = int(math.floor(fair - edge))
        sell_px = int(math.ceil(fair + edge))
        buy_px = max(buy_px, 0)
        sell_px = min(sell_px, int(math.floor(upper - VOUCHER_SLACK_UPPER)))
        if ask is not None:
            buy_px = min(buy_px, ask - 1)
        if bid is not None:
            sell_px = max(sell_px, bid + 1)

        if buy_px > 0 and (ask is None or buy_px < ask):
            sz = _clip_buy(position, cap, bought, VOUCHER_PASSIVE_SIZE)
            if sz > 0:
                orders.append(Order(symbol, buy_px, sz))
                bought += sz
        if sell_px > 0 and sell_px > buy_px and (bid is None or sell_px > bid):
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

        # update fair state
        hyd_depth = order_depths.get(HYDROGEL)
        if hyd_depth is not None:
            m = _microprice(hyd_depth)
            if m is not None:
                blended = 0.85 * HYDROGEL_ANCHOR + 0.15 * m
                fair_state[HYDROGEL] = _ewma(
                    fair_state.get(HYDROGEL), blended, FV_EWMA_ALPHA_HYD
                )
        vfe_depth = order_depths.get(VFE)
        if vfe_depth is not None:
            m = _microprice(vfe_depth)
            if m is not None:
                fair_state[VFE] = _ewma(
                    fair_state.get(VFE), m, FV_EWMA_ALPHA_VFE
                )

        # HYDROGEL_PACK
        if hyd_depth is not None and HYDROGEL in fair_state:
            legs = _underlying_orders(
                HYDROGEL, hyd_depth, positions.get(HYDROGEL, 0),
                CAP_HYDROGEL, fair_state[HYDROGEL],
                HYD_TAKE_EDGE, HYD_QUOTE_EDGE, HYD_QUOTE_SIZE,
            )
            if legs:
                orders_out[HYDROGEL] = legs

        # VELVETFRUIT_EXTRACT
        if vfe_depth is not None and VFE in fair_state:
            legs = _underlying_orders(
                VFE, vfe_depth, positions.get(VFE, 0),
                CAP_VFE, fair_state[VFE],
                VFE_TAKE_EDGE, VFE_QUOTE_EDGE, VFE_QUOTE_SIZE,
            )
            if legs:
                orders_out[VFE] = legs

        # vouchers
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
                sym, strike, vd, ref, positions.get(sym, 0), CAP_VOUCHER
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
