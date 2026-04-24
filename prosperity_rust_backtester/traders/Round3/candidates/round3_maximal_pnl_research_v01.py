"""Round 3 maximal-PnL research v01.

Evidence used (hosted submission 370531 activities log, 1000 ticks of day 2):

  Total PnL             : +366
  HYDROGEL_PACK         :  -52   (max_dd 1838; 31 trades; anchored ~10000,
                                  range [9915, 10031], stdev 29.7)
  VELVETFRUIT_EXTRACT   : +220   (58 trades; range [5241.5, 5276.5] stdev 7.52)
  VEV_4000              :  +74   (12 trades, held +15 at close)
  VEV_4500              :  +76   (12 trades, +15 at close)
  VEV_5000              :  +31   (4 trades, +9)
  VEV_5100              :   +3   (4 trades, +9)
  VEV_5200              :  +14   (4 trades, +9)
  VEV_5300..VEV_6500    :   0    (3..10 trades each, NO PnL — dead weight)

  Top-10 per-tick gains: 9/10 HYDROGEL.
  Top-10 per-tick drops: 10/10 HYDROGEL.

Interpretation: the prior drawdown-repair WORKED (HYDROGEL -1059 -> -52, VFE
held), but I over-corrected. 31 HYDROGEL trades is far too few; mid wanders
only ~30 pts, so edge=3 filters out almost every real opportunity. VFE is
extremely stable (stdev 7.52) and should take much more risk. Deep-ITM
voucher intrinsic arb and the VEV_5000/5100/5200 near-ATM strikes produce
reliable small PnL. VEV_5300-6500 passive quoting is dead. The top-10 gains
being 9-out-of-10 HYDROGEL proves HYDROGEL is a strong bidirectional
market-making alpha, not a pure loss source.

Design changes vs drawdown_repair_v01 (the submitted trader):

  (1) HYDROGEL: reinstate a MODERATE anchor (40% anchor at 10000 + 60% pure
      microprice EWMA). 85% was too hard, 0% leaves scaffolding money on
      the table. Tighten edges back: take_edge 3->1, quote_edge 3->1,
      size 4->6, cap 30->40. Stronger inventory skew 2.0 kept.
  (2) HYDROGEL regime guard: if |microprice - anchor| > 80, disable taking
      (still quote passively). Prevents repeating the 369524-style runaway.
  (3) VFE: take_edge 3->2, quote_edge 3->2, size 4->8, cap 50->50.
  (4) Vouchers: PASSIVE QUOTING KILLED for VEV_5300/5400/5500/6000/6500.
      These five strikes only place intrinsic-arb / monotonicity-arb orders.
      Passive quoting remains for VEV_4000/4500/5000/5100/5200 only.
  (5) Voucher passive size 3->4 on active strikes.
  (6) Voucher cap 20->25.
  (7) Kill-switch removed. The realized-PnL proxy misattributed on the hosted
      own_trades format (buyer/seller flags are empty strings, not "SUBMISSION")
      so the switch may have throttled wrongly. Inventory skew + caps +
      regime guard replace it.

Submission contract:
  run(state) -> (orders_dict, conversions=0, traderData_json_str)
  bid()      -> int
"""

import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


# --- products ---------------------------------------------------------------

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

# Active passive-quoting strikes (evidence-based from hosted trade counts).
ACTIVE_PASSIVE_STRIKES = (4000, 4500, 5000, 5100, 5200)

# position caps
CAP_HYDROGEL = 40
CAP_VFE = 50
CAP_VOUCHER = 25

# --- HYDROGEL ---------------------------------------------------------------

HYDROGEL_ANCHOR = 10000.0
HYDROGEL_ANCHOR_WEIGHT = 0.40       # soft anchor
FV_EWMA_ALPHA_HYD = 0.10
HYD_TAKE_EDGE = 1
HYD_QUOTE_EDGE = 1
HYD_QUOTE_SIZE = 6
HYD_INV_SKEW_STRENGTH = 2.0
HYD_REGIME_GUARD_DEVIATION = 80.0   # disable taking if |mid-anchor|>80

# --- VFE --------------------------------------------------------------------

FV_EWMA_ALPHA_VFE = 0.15
VFE_TAKE_EDGE = 2
VFE_QUOTE_EDGE = 2
VFE_QUOTE_SIZE = 8
VFE_INV_SKEW_STRENGTH = 1.5

# --- vouchers ---------------------------------------------------------------

VOUCHER_SLACK_INTRINSIC = 1
VOUCHER_SLACK_UPPER = 1
VOUCHER_SLACK_MONO = 1
VOUCHER_PASSIVE_SIZE = 4
VOUCHER_MARKET_WEIGHT = 0.7
VOUCHER_MODEL_WEIGHT = 0.3
TV_A = 68.0
TV_W = 400.0
TV_POW = 1.8
TV_OTM_FLOOR = 0.5
TV_DEEP_ITM_MAX_EXCESS = 2.0
ENABLE_STRIKE_MONOTONICITY = True

TRADER_DATA_SCHEMA = 6
TRADER_DATA_MAX_BYTES = 8000


# --- helpers ----------------------------------------------------------------

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


def _voucher_blended_fair(S: float, K: int, voucher_mid: Optional[float]) -> float:
    model = _voucher_model_fair(S, K)
    if voucher_mid is None:
        return model
    blended = VOUCHER_MARKET_WEIGHT * voucher_mid + VOUCHER_MODEL_WEIGHT * model
    return max(max(S - K, 0.0), min(blended, S))


# --- underlying MM (HYDROGEL + VFE) -----------------------------------------


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


# --- voucher module ---------------------------------------------------------


def _voucher_orders(
    symbol: str,
    strike: int,
    depth: OrderDepth,
    underlying_ref: Optional[float],
    position: int,
    cap: int,
    passive_enabled: bool,
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

    if passive_enabled:
        fair = _voucher_blended_fair(underlying_ref, strike, voucher_mid)
        edge = 2 if strike + 500 <= underlying_ref else 3
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


# --- trader -----------------------------------------------------------------


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

        # ---- fair-value updates ----
        hyd_depth = order_depths.get(HYDROGEL)
        if hyd_depth is not None:
            m = _microprice(hyd_depth)
            if m is not None:
                blended = (
                    HYDROGEL_ANCHOR_WEIGHT * HYDROGEL_ANCHOR
                    + (1.0 - HYDROGEL_ANCHOR_WEIGHT) * m
                )
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

        # ---- HYDROGEL with regime guard ----
        if hyd_depth is not None and HYDROGEL in fair_state:
            current_mid = _mid(hyd_depth)
            allow_take = True
            if current_mid is not None:
                if abs(current_mid - HYDROGEL_ANCHOR) > HYD_REGIME_GUARD_DEVIATION:
                    allow_take = False
            legs = _underlying_orders(
                HYDROGEL, hyd_depth, positions.get(HYDROGEL, 0),
                CAP_HYDROGEL, fair_state[HYDROGEL],
                HYD_TAKE_EDGE, HYD_QUOTE_EDGE, HYD_QUOTE_SIZE,
                HYD_INV_SKEW_STRENGTH, allow_take,
            )
            if legs:
                orders_out[HYDROGEL] = legs

        # ---- VFE ----
        if vfe_depth is not None and VFE in fair_state:
            legs = _underlying_orders(
                VFE, vfe_depth, positions.get(VFE, 0),
                CAP_VFE, fair_state[VFE],
                VFE_TAKE_EDGE, VFE_QUOTE_EDGE, VFE_QUOTE_SIZE,
                VFE_INV_SKEW_STRENGTH, True,
            )
            if legs:
                orders_out[VFE] = legs

        # ---- vouchers ----
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
            passive_enabled = strike in ACTIVE_PASSIVE_STRIKES
            legs = _voucher_orders(
                sym, strike, vd, ref, positions.get(sym, 0),
                CAP_VOUCHER, passive_enabled,
            )
            if legs:
                orders_out.setdefault(sym, []).extend(legs)

        mono = _strike_monotonicity_orders(
            voucher_entries, order_depths, positions, CAP_VOUCHER
        )
        for sym, legs in mono.items():
            orders_out.setdefault(sym, []).extend(legs)

        # ---- traderData ----
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
