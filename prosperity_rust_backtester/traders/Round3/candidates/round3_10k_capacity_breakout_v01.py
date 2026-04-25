"""Round 3 10k-or-bust v01 — Capacity Breakout with Full Official Limits.

*** Step-change vs all prior submissions ***

The official Round 3 wiki page confirms (extracted to Prosperity Context/Notion Export):

  HYDROGEL_PACK               cap = 200    (my traders used 30)     6.67x
  VELVETFRUIT_EXTRACT         cap = 200    (my traders used 50)     4x
  each VEV_<K> voucher        cap = 300    (my traders used 30)    10x

Every hosted submission so far (+366, +318, +1,547) used 10-17% of the available
capacity. That is the primary structural cap. This trader uses the full official
limits proportionally scaled across quote sizes and identity arbs.

Additional evidence applied:

  - HYDROGEL book imbalance → next-tick mid correlation = +0.374 (hosted 371381)
    → kept as a predictive overlay on fair value.
  - VFE spread 4.99, depth 75.6, stdev 7.5: extremely stable. Aggressive MM.
  - Vouchers are European calls. TTE at Round 3 hosted start = 5 days, end = 3
    days. Local day_2 TTE = 6d, day_0 TTE = 8d. Hosted TV should be ~60-75%
    of day_0 calibration -> TV_A scaled down.
  - Strike monotonicity and intrinsic floor are identity-bounded arbs.
  - Passive voucher quoting at size 3-4 (prior) produced 0 PnL on 5 of 10
    strikes due to being too small to join a thick voucher book. At size 20-30
    with cap 300, passive quotes have enough size to get placed and filled.

Strategy:

  HYDROGEL module:
    fair = 0.40 * 10000 + 0.60 * EWMA(microprice) + HYD_IMB_COEF * imbalance
    take when ask+edge<=fair or bid-edge>=fair (edge=4)
    passive quote at fair±3 with inventory-skewed sizing up to 20 per side
    regime guard if |mid - fair| > 120
    cap 200

  VFE module:
    fair = EWMA(microprice)
    take edge=1, quote edge=1, size up to 40 per side, cap 200
    aggressive MM on tight spread (5.0) with deep book (75.6)

  Voucher module (per strike):
    reference = fair_VFE
    intrinsic = max(reference - K, 0)
    TV = TV_A_HOSTED * max(0, 1 - |S-K|/TV_W)^TV_POW
    fair = intrinsic + TV, bounded by [intrinsic, reference]
    identity floor buy: buy at ask if ask + slack < intrinsic
    identity ceiling sell: sell at bid if bid - slack > reference
    passive two-sided quoting around model fair with size 20-25, cap 300
    strike monotonicity arb across adjacent strikes

Expected local PnL: >> 50,000 (prior v02 at +24,565 with 10-17% of capacity).
Expected hosted PnL: target 5,000 - 12,000 based on 15:1 local-to-hosted ratio
observed on prior submissions.

All parameters cite evidence. All caps match the official wiki.

Submission contract: run -> (orders, 0, traderData), bid -> int.
"""

import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


# --- products (verified from round3 CSV headers) ---------------------------

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

# --- OFFICIAL CAPS (from wiki "Round 3 - Gloves Off" page) -----------------

CAP_HYDROGEL = 200
CAP_VFE = 200
CAP_VOUCHER = 300

# --- HYDROGEL params --------------------------------------------------------

HYDROGEL_ANCHOR = 10000.0
HYDROGEL_ANCHOR_WEIGHT = 0.40
FV_EWMA_ALPHA_HYD = 0.10
HYD_TAKE_EDGE = 4
HYD_QUOTE_EDGE = 3
HYD_QUOTE_SIZE = 20            # scaled 5x from v02's 4
HYD_INV_SKEW_STRENGTH = 2.0
HYD_REGIME_GUARD_DEV = 120.0
HYD_IMB_COEF = 5.0             # kept from v03 (imbalance->next-tick corr 0.37)
HYD_IMB_SIZE_LEAN = 0.5

# --- VFE params -------------------------------------------------------------

FV_EWMA_ALPHA_VFE = 0.20
VFE_TAKE_EDGE = 1
VFE_QUOTE_EDGE = 1
VFE_QUOTE_SIZE = 40            # scaled 3.3x from v02's 12
VFE_INV_SKEW_STRENGTH = 1.5

# --- voucher params (TTE-adjusted for hosted Round 3) -----------------------

VOUCHER_SLACK_INTRINSIC = 1
VOUCHER_SLACK_UPPER = 1
VOUCHER_SLACK_MONO = 1

# TV_A downward-adjusted for hosted TTE (5d hosted vs 8d day_0 calibration).
# 5/8 = 0.625, so a calibration around 0.65 * previous TV_A = 0.65*68 ≈ 44.
# But historical day_2 data (TTE 6d) is what my backtest runs on, so keep TV_A
# close to the 6/8 = 0.75 scaling to match local data, and let the code compute
# live time-value decay via voucher mid blend.
TV_A = 55.0            # midpoint calibration; market-mid blend adjusts in situ
TV_W = 400.0
TV_POW = 1.8
TV_OTM_FLOOR = 0.5
TV_DEEP_ITM_MAX_EXCESS = 2.0
VOUCHER_MARKET_WEIGHT = 0.70   # defer to observed voucher mid
VOUCHER_MODEL_WEIGHT = 0.30    # but bound by model
VOUCHER_PASSIVE_ENABLED = True
VOUCHER_PASSIVE_SIZE = 25      # scaled 6x from v02's 4. cap 300 allows this.
ENABLE_STRIKE_MONOTONICITY = True

TRADER_DATA_SCHEMA = 10
TRADER_DATA_MAX_BYTES = 8000


# --- helpers ----------------------------------------------------------------

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


# --- underlying MM w/ imbalance overlay ------------------------------------


def _underlying_orders(
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
    orders: List[Order] = []
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    if bid is None and ask is None:
        return orders
    fair = ewma_fair + imb_coef * imbalance
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


# --- voucher module (full passive on all strikes) --------------------------


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

    # identity: sell above upper bound (V <= S)
    if bid is not None and bid - VOUCHER_SLACK_UPPER > upper:
        avail = depth.buy_orders[bid]
        sz = _clip_sell(position, cap, sold, min(avail, cap))
        if sz > 0:
            orders.append(Order(symbol, bid, -sz))
            sold += sz

    # passive two-sided quoting on every strike
    if VOUCHER_PASSIVE_ENABLED:
        fair = _voucher_blended_fair(underlying_ref, strike, voucher_mid)
        # wider edge on near-ATM (more uncertain), tighter on deep-ITM
        dist = abs(underlying_ref - strike)
        if strike + 500 <= underlying_ref:
            edge = 2     # deep ITM
        elif dist <= 200:
            edge = 3     # near ATM
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
        # inventory-skew the voucher quote sizes too
        inv = 0.0 if cap == 0 else (position + bought - sold) / float(cap)
        inv = max(-1.0, min(1.0, inv))
        buy_sz_raw = max(0, int(round(VOUCHER_PASSIVE_SIZE * max(0.0, 1.0 - 1.5 * inv))))
        sell_sz_raw = max(0, int(round(VOUCHER_PASSIVE_SIZE * max(0.0, 1.0 + 1.5 * inv))))
        if buy_px > 0 and (ask is None or buy_px < ask):
            sz = _clip_buy(position, cap, bought, buy_sz_raw)
            if sz > 0:
                orders.append(Order(symbol, buy_px, sz))
                bought += sz
        if sell_px > 0 and sell_px > buy_px and (bid is None or sell_px > bid):
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

        hyd_depth = order_depths.get(HYDROGEL)
        hyd_imb = 0.0
        if hyd_depth is not None:
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

        vfe_depth = order_depths.get(VFE)
        if vfe_depth is not None:
            m = _microprice(vfe_depth)
            if m is not None:
                fair_state[VFE] = _ewma(
                    fair_state.get(VFE), m, FV_EWMA_ALPHA_VFE
                )

        if hyd_depth is not None and HYDROGEL in fair_state:
            current_mid = _mid(hyd_depth)
            allow_take = True
            if current_mid is not None:
                if abs(current_mid - fair_state[HYDROGEL]) > HYD_REGIME_GUARD_DEV:
                    allow_take = False
            legs = _underlying_orders(
                HYDROGEL, hyd_depth, positions.get(HYDROGEL, 0),
                CAP_HYDROGEL, fair_state[HYDROGEL],
                hyd_imb, HYD_IMB_COEF, HYD_IMB_SIZE_LEAN,
                HYD_TAKE_EDGE, HYD_QUOTE_EDGE, HYD_QUOTE_SIZE,
                HYD_INV_SKEW_STRENGTH, allow_take,
            )
            if legs:
                orders_out[HYDROGEL] = legs

        if vfe_depth is not None and VFE in fair_state:
            legs = _underlying_orders(
                VFE, vfe_depth, positions.get(VFE, 0),
                CAP_VFE, fair_state[VFE],
                0.0, 0.0, 0.0,   # VFE imbalance overlay disabled (v03 ablation)
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
