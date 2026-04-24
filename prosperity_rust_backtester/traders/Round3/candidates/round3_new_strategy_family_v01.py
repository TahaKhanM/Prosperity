"""Round 3 new strategy family v01 — Mean-Reversion Band + Tight MM + Voucher.

Fundamentally different from prior iterations. Driven by microstructure evidence
from 3-day round3 CSVs + hosted 370893 result:

    HYDROGEL_PACK:
      spread=15.7, depth=24.7, VR(5)=0.78, lag1-autocorr=-0.125.
      WIDE spread + LOW depth + MEAN-REVERTING. Market-making inside a 15pt
      spread = adverse-selection trap. This is a mean-reversion BAND product.

    VELVETFRUIT_EXTRACT:
      spread=4.99, depth=75.6, VR(5)=0.75, lag1-autocorr=-0.155.
      TIGHT spread + DEEP book + mean-reverting. THIS is the MM product.

    HYDROGEL-VFE cross-correlation = 0.01. Independent. No cross-hedge.

    Vouchers: VFE-VEV_5000 corr=0.75. Vouchers track VFE; intrinsic identity
    arb works; strike-monotonicity is an identity. Passive quoting on vouchers
    has been net-zero every hosted run — keep only identity trades.

Prior model (all v01-v06 of same family) treated both products as identical MM
products. This one applies the RIGHT mechanism per product:

  HYDROGEL module: MEAN-REVERSION BAND.
    - hard anchor 10000, band 1/2/3 sigma at 15/30/60 XY.
    - NO inside-spread passive quoting.
    - Enter long when mid <= anchor-15; add at -30 and -60.
    - Enter short when mid >= anchor+15; add at +30 and +60.
    - Flatten aggressively when mid crosses anchor.
    - Size scales with deviation bucket.

  VFE module: TIGHT SYMMETRIC MM.
    - EWMA microprice fair. Take-edge=1, quote-edge=1, size=12.
    - Inventory skew.
    - High cap (50), high trade rate.

  Voucher module: IDENTITY-ONLY.
    - buy voucher when ask + 1 < max(S-K, 0).
    - sell voucher when bid - 1 > S.
    - strike-monotonicity pair arb.
    - NO passive quoting. Evidence: 3 hosted runs showed ~0 passive PnL.

Expected behaviour:
- HYDROGEL: far fewer trades, each in a mean-reverting sweet spot. Lower
  drawdown because no inside-spread MM to get picked off. PnL comes from
  reversion, not spread capture.
- VFE: MUCH more trades, tight spread capture, large notional.
- Vouchers: small consistent PnL from identities only.

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

# position caps
CAP_HYDROGEL = 50
CAP_VFE = 50
CAP_VOUCHER = 30

# --- HYDROGEL mean-reversion band -------------------------------------------

HYDROGEL_ANCHOR = 10000.0
# deviation thresholds (XY from anchor). 1-sigma ~ 15, 2-sigma ~ 30, 3-sigma ~ 60.
HYD_BAND_1 = 15
HYD_BAND_2 = 30
HYD_BAND_3 = 60
# target signed inventory at each deviation bucket.
HYD_TARGET_1 = 15   # 1-sigma: moderate position
HYD_TARGET_2 = 30   # 2-sigma: bigger
HYD_TARGET_3 = 50   # 3-sigma: max
HYD_FLATTEN_BAND = 5   # within 5 XY of anchor, target 0
# kill-switch: if mid deviates beyond this, stop adding (stale regime)
HYD_MAX_DEVIATION = 120
# take size per tick (max per side, regardless of book availability)
HYD_MAX_TAKE_PER_TICK = 15

# --- VFE tight MM ------------------------------------------------------------

FV_EWMA_ALPHA_VFE = 0.20
VFE_TAKE_EDGE = 1
VFE_QUOTE_EDGE = 1
VFE_QUOTE_SIZE = 12
VFE_INV_SKEW_STRENGTH = 1.5

# --- voucher identity-only --------------------------------------------------

VOUCHER_SLACK_INTRINSIC = 1
VOUCHER_SLACK_UPPER = 1
VOUCHER_SLACK_MONO = 1
ENABLE_STRIKE_MONOTONICITY = True

TRADER_DATA_SCHEMA = 7
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


# --- HYDROGEL mean-reversion band module ------------------------------------


def _target_hydrogel_position(mid: float) -> int:
    """Signed target position based on deviation from anchor.

    Positive = long (when price is below anchor).
    Negative = short (when price is above anchor).
    """
    dev = mid - HYDROGEL_ANCHOR
    abs_dev = abs(dev)
    sign = -1 if dev > 0 else 1
    if abs_dev > HYD_MAX_DEVIATION:
        return 0  # stale regime; do not add
    if abs_dev < HYD_FLATTEN_BAND:
        return 0
    if abs_dev < HYD_BAND_1:
        return 0
    if abs_dev < HYD_BAND_2:
        return sign * HYD_TARGET_1
    if abs_dev < HYD_BAND_3:
        return sign * HYD_TARGET_2
    return sign * HYD_TARGET_3


def _hydrogel_orders(
    depth: OrderDepth,
    position: int,
) -> List[Order]:
    orders: List[Order] = []
    mid = _mid(depth)
    if mid is None:
        return orders
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    target = _target_hydrogel_position(mid)
    gap = target - position  # positive = need to buy, negative = need to sell

    if gap == 0:
        return orders

    if gap > 0:
        # need to buy: take from best ask
        if ask is None:
            return orders
        avail = -depth.sell_orders[ask]
        want = min(abs(gap), avail, HYD_MAX_TAKE_PER_TICK)
        sz = _clip_buy(position, CAP_HYDROGEL, 0, want)
        if sz > 0:
            orders.append(Order(HYDROGEL, ask, sz))
            # additional level-2 depth fill if deviation is large
            # (skip second level to stay conservative)
    else:
        # need to sell: hit best bid
        if bid is None:
            return orders
        avail = depth.buy_orders[bid]
        want = min(abs(gap), avail, HYD_MAX_TAKE_PER_TICK)
        sz = _clip_sell(position, CAP_HYDROGEL, 0, want)
        if sz > 0:
            orders.append(Order(HYDROGEL, bid, -sz))

    return orders


# --- VFE tight MM module ----------------------------------------------------


def _vfe_orders(
    depth: OrderDepth,
    position: int,
    cap: int,
    fair: float,
) -> List[Order]:
    orders: List[Order] = []
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    if bid is None and ask is None:
        return orders

    bought = 0
    sold = 0

    # take
    if ask is not None and ask + VFE_TAKE_EDGE <= fair:
        avail = -depth.sell_orders[ask]
        sz = _clip_buy(position, cap, bought, min(avail, cap))
        if sz > 0:
            orders.append(Order(VFE, ask, sz))
            bought += sz
    if bid is not None and bid - VFE_TAKE_EDGE >= fair:
        avail = depth.buy_orders[bid]
        sz = _clip_sell(position, cap, sold, min(avail, cap))
        if sz > 0:
            orders.append(Order(VFE, bid, -sz))
            sold += sz

    # make with inventory skew
    inv = 0.0 if cap == 0 else (position + bought - sold) / float(cap)
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

    buy_sz_raw = max(0, int(round(VFE_QUOTE_SIZE * max(0.0, 1.0 - VFE_INV_SKEW_STRENGTH * inv))))
    sell_sz_raw = max(0, int(round(VFE_QUOTE_SIZE * max(0.0, 1.0 + VFE_INV_SKEW_STRENGTH * inv))))
    buy_sz = _clip_buy(position, cap, bought, buy_sz_raw)
    sell_sz = _clip_sell(position, cap, sold, sell_sz_raw)

    if buy_sz > 0 and (ask is None or buy_px < ask):
        orders.append(Order(VFE, buy_px, buy_sz))
    if sell_sz > 0 and (bid is None or sell_px > bid):
        orders.append(Order(VFE, sell_px, -sell_sz))

    return orders


# --- voucher identity module -------------------------------------------------


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

        # ---- VFE fair (MM product) ----
        vfe_depth = order_depths.get(VFE)
        if vfe_depth is not None:
            m = _microprice(vfe_depth)
            if m is not None:
                fair_state[VFE] = _ewma(
                    fair_state.get(VFE), m, FV_EWMA_ALPHA_VFE
                )

        # ---- HYDROGEL mean-reversion band ----
        hyd_depth = order_depths.get(HYDROGEL)
        if hyd_depth is not None:
            legs = _hydrogel_orders(
                hyd_depth, positions.get(HYDROGEL, 0),
            )
            if legs:
                orders_out[HYDROGEL] = legs

        # ---- VFE tight MM ----
        if vfe_depth is not None and VFE in fair_state:
            legs = _vfe_orders(
                vfe_depth, positions.get(VFE, 0),
                CAP_VFE, fair_state[VFE],
            )
            if legs:
                orders_out[VFE] = legs

        # ---- vouchers (identity-only) ----
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
