"""Round 3 30k-breakout v01 — Activate dormant vouchers + scale VFE.

Hosted 373667 (prior v01) scored +8,359. Per-product:
  HYDROGEL  +6,072 (cap 200/200 = 100% util, max_dd 16,388)
  VFE       +2,080 (cap 112/200 = 56% util)
  VEV_4000  +75    (pos 18/300 = 6%)
  VEV_4500  +76    (pos 18/300 = 6%)
  VEV_5000  +36    (pos 8/300 = 2.7%)
  VEV_5100  +21    (pos 9/300 = 3%)
  VEV_5200..6500: ZERO. 6 strikes completely dormant.

Hosted:local ratio 0.084 (vs prior 0.015). Big win. Remaining gaps to 30k:
  - VFE has 44% spare capacity: size 40 -> 80.
  - 6 voucher strikes dormant: need INSIDE-BOOK passive quoting at larger size
    to displace existing passive bots.
  - HYDROGEL drawdown 16,388 is intrinsic to anchored MM on volatile product;
    volatility gate reduces size when recent tick volatility is high.

New features in v01:
  1. Voucher passive: step INSIDE the book (bid+1 / ask-1) when fair supports.
     Falls back to fair±edge if not room. Size 30 per strike per side.
  2. VFE quote size 40 -> 80 (cap 200 allows 2.5x quoting per side).
  3. OTM voucher short-theta: for far-OTM strikes (S-K < -200), sell passively
     at best_ask (pure decay trade). Small size (5), bounded by identity.
  4. HYDROGEL volatility-adaptive sizing: if |last_mid_change|>5, halve quote
     size next tick. Kills the worst adverse-selection streaks.
  5. Kept: imbalance overlay, strike monotonicity, intrinsic arbs.

Submission contract: run -> (orders, 0, traderData), bid -> int.
"""

import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState

HYDROGEL = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"
VOUCHER_PREFIX_CANDIDATES = ("VEV_",)
VOUCHER_STRIKE_MIN = 4000
VOUCHER_STRIKE_MAX = 6500

CAP_HYDROGEL = 200
CAP_VFE = 200
CAP_VOUCHER = 300

# HYDROGEL
HYDROGEL_ANCHOR = 10000.0
HYDROGEL_ANCHOR_WEIGHT = 0.40
FV_EWMA_ALPHA_HYD = 0.10
HYD_TAKE_EDGE = 4
HYD_QUOTE_EDGE = 3
HYD_QUOTE_SIZE = 20
HYD_INV_SKEW_STRENGTH = 2.0
HYD_REGIME_GUARD_DEV = 120.0
HYD_IMB_COEF = 5.0
HYD_IMB_SIZE_LEAN = 0.5
HYD_VOL_GATE_THRESHOLD = 5.0    # if |last_move|>this, halve quote size

# VFE
FV_EWMA_ALPHA_VFE = 0.20
VFE_TAKE_EDGE = 1
VFE_QUOTE_EDGE = 1
VFE_QUOTE_SIZE = 60              # 30k_v01: 60 (scaled from 40 but not 80 which regressed)
VFE_INV_SKEW_STRENGTH = 1.5

# Vouchers
VOUCHER_SLACK_INTRINSIC = 1
VOUCHER_SLACK_UPPER = 1
VOUCHER_SLACK_MONO = 1
TV_A = 55.0
TV_W = 400.0
TV_POW = 1.8
TV_OTM_FLOOR = 0.5
TV_DEEP_ITM_MAX_EXCESS = 2.0
VOUCHER_MARKET_WEIGHT = 0.70
VOUCHER_MODEL_WEIGHT = 0.30
VOUCHER_PASSIVE_SIZE = 30        # v01: 25 -> 30k_v01: 30
VOUCHER_INSIDE_BOOK_MIN_MARGIN = 1  # min fair vs quoted-px margin for inside-book
VOUCHER_OTM_SHORT_THRESHOLD = 200    # if S-K < -200, do OTM short-theta
VOUCHER_OTM_SHORT_SIZE = 10
VOUCHER_OTM_SHORT_MAX_ASK = 3        # only short OTM voucher if its ask <= 3 XY
ENABLE_STRIKE_MONOTONICITY = True

TRADER_DATA_SCHEMA = 30
TRADER_DATA_MAX_BYTES = 8000


def _best_bid(d: OrderDepth) -> Optional[int]:
    return max(d.buy_orders) if d.buy_orders else None


def _best_ask(d: OrderDepth) -> Optional[int]:
    return min(d.sell_orders) if d.sell_orders else None


def _mid(d: OrderDepth) -> Optional[float]:
    b, a = _best_bid(d), _best_ask(d)
    return None if b is None or a is None else (b + a) / 2.0


def _microprice(d: OrderDepth) -> Optional[float]:
    b = _best_bid(d)
    a = _best_ask(d)
    if b is None or a is None:
        return None
    bv = d.buy_orders[b]
    av = -d.sell_orders[a]
    tot = bv + av
    if tot <= 0:
        return (b + a) / 2.0
    return (a * bv + b * av) / tot


def _imbalance(d: OrderDepth) -> Optional[float]:
    b = _best_bid(d)
    a = _best_ask(d)
    if b is None or a is None:
        return None
    bv = d.buy_orders[b]
    av = -d.sell_orders[a]
    tot = bv + av
    if tot <= 0:
        return 0.0
    return (bv - av) / tot


def _parse_strike(sym: str) -> Optional[int]:
    if sym.startswith("VEV_"):
        try:
            return int(sym[4:])
        except ValueError:
            return None
    return None


def _is_voucher(sym: str) -> bool:
    s = _parse_strike(sym)
    return s is not None and VOUCHER_STRIKE_MIN <= s <= VOUCHER_STRIKE_MAX


def _clip_buy(pos: int, cap: int, already: int, want: int) -> int:
    return max(0, min(want, cap - (pos + already)))


def _clip_sell(pos: int, cap: int, already: int, want: int) -> int:
    return max(0, min(want, cap + (pos - already)))


def _ewma(prior: Optional[float], sample: float, alpha: float) -> float:
    return sample if prior is None else prior * (1 - alpha) + sample * alpha


def _tv(S: float, K: int) -> float:
    d = abs(S - K)
    if d >= TV_W:
        return TV_OTM_FLOOR
    x = 1.0 - d / TV_W
    if x <= 0.0:
        return TV_OTM_FLOOR
    return max(TV_OTM_FLOOR, TV_A * (x ** TV_POW))


def _voucher_fair(S: float, K: int, vmid: Optional[float]) -> float:
    intrinsic = max(S - K, 0.0)
    model = intrinsic + _tv(S, K)
    if K + 300 <= S:
        model = min(model, intrinsic + TV_DEEP_ITM_MAX_EXCESS)
    model = max(0.0, min(model, S))
    if vmid is None:
        return model
    blended = VOUCHER_MARKET_WEIGHT * vmid + VOUCHER_MODEL_WEIGHT * model
    return max(intrinsic, min(blended, S))


# --- HYDROGEL module with vol gate ----------------------------------------


def _hydrogel_orders(
    depth: OrderDepth,
    position: int,
    ewma_fair: float,
    imbalance: float,
    allow_take: bool,
    vol_gate_active: bool,
) -> List[Order]:
    orders: List[Order] = []
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    if bid is None and ask is None:
        return orders
    fair = ewma_fair + HYD_IMB_COEF * imbalance
    bought = 0
    sold = 0
    effective_size = HYD_QUOTE_SIZE // 2 if vol_gate_active else HYD_QUOTE_SIZE

    if allow_take:
        if ask is not None and ask + HYD_TAKE_EDGE <= fair:
            avail = -depth.sell_orders[ask]
            sz = _clip_buy(position, CAP_HYDROGEL, bought, min(avail, CAP_HYDROGEL))
            if sz > 0:
                orders.append(Order(HYDROGEL, ask, sz))
                bought += sz
        if bid is not None and bid - HYD_TAKE_EDGE >= fair:
            avail = depth.buy_orders[bid]
            sz = _clip_sell(position, CAP_HYDROGEL, sold, min(avail, CAP_HYDROGEL))
            if sz > 0:
                orders.append(Order(HYDROGEL, bid, -sz))
                sold += sz

    inv = (position + bought - sold) / float(CAP_HYDROGEL)
    inv = max(-1.0, min(1.0, inv))
    buy_px = int(math.floor(fair - HYD_QUOTE_EDGE))
    sell_px = int(math.ceil(fair + HYD_QUOTE_EDGE))
    if bid is not None:
        buy_px = min(buy_px, bid + 1)
    if ask is not None:
        buy_px = min(buy_px, ask - 1)
        sell_px = max(sell_px, ask - 1)
    if bid is not None:
        sell_px = max(sell_px, bid + 1)
    buy_lean = max(0.0, 1.0 + HYD_IMB_SIZE_LEAN * imbalance)
    sell_lean = max(0.0, 1.0 - HYD_IMB_SIZE_LEAN * imbalance)
    buy_sz = _clip_buy(
        position, CAP_HYDROGEL, bought,
        max(0, int(round(effective_size * buy_lean * max(0.0, 1.0 - HYD_INV_SKEW_STRENGTH * inv))))
    )
    sell_sz = _clip_sell(
        position, CAP_HYDROGEL, sold,
        max(0, int(round(effective_size * sell_lean * max(0.0, 1.0 + HYD_INV_SKEW_STRENGTH * inv))))
    )
    if buy_sz > 0 and (ask is None or buy_px < ask):
        orders.append(Order(HYDROGEL, buy_px, buy_sz))
    if sell_sz > 0 and (bid is None or sell_px > bid):
        orders.append(Order(HYDROGEL, sell_px, -sell_sz))
    return orders


def _vfe_orders(depth: OrderDepth, position: int, fair: float) -> List[Order]:
    orders: List[Order] = []
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    if bid is None and ask is None:
        return orders
    bought = 0
    sold = 0
    if ask is not None and ask + VFE_TAKE_EDGE <= fair:
        avail = -depth.sell_orders[ask]
        sz = _clip_buy(position, CAP_VFE, bought, min(avail, CAP_VFE))
        if sz > 0:
            orders.append(Order(VFE, ask, sz))
            bought += sz
    if bid is not None and bid - VFE_TAKE_EDGE >= fair:
        avail = depth.buy_orders[bid]
        sz = _clip_sell(position, CAP_VFE, sold, min(avail, CAP_VFE))
        if sz > 0:
            orders.append(Order(VFE, bid, -sz))
            sold += sz
    inv = (position + bought - sold) / float(CAP_VFE)
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
    buy_sz = _clip_buy(
        position, CAP_VFE, bought,
        max(0, int(round(VFE_QUOTE_SIZE * max(0.0, 1.0 - VFE_INV_SKEW_STRENGTH * inv))))
    )
    sell_sz = _clip_sell(
        position, CAP_VFE, sold,
        max(0, int(round(VFE_QUOTE_SIZE * max(0.0, 1.0 + VFE_INV_SKEW_STRENGTH * inv))))
    )
    if buy_sz > 0 and (ask is None or buy_px < ask):
        orders.append(Order(VFE, buy_px, buy_sz))
    if sell_sz > 0 and (bid is None or sell_px > bid):
        orders.append(Order(VFE, sell_px, -sell_sz))
    return orders


# --- voucher module with inside-book + OTM short-theta --------------------


def _voucher_orders(
    symbol: str,
    strike: int,
    depth: OrderDepth,
    ref: Optional[float],
    position: int,
) -> List[Order]:
    if ref is None:
        return []
    bid = _best_bid(depth)
    ask = _best_ask(depth)
    vmid = _mid(depth)
    intrinsic = max(ref - strike, 0.0)
    upper = ref
    orders: List[Order] = []
    bought = 0
    sold = 0

    # identity: buy below intrinsic
    if ask is not None and ask + VOUCHER_SLACK_INTRINSIC < intrinsic:
        avail = -depth.sell_orders[ask]
        sz = _clip_buy(position, CAP_VOUCHER, bought, min(avail, CAP_VOUCHER))
        if sz > 0:
            orders.append(Order(symbol, ask, sz))
            bought += sz

    # identity: sell above upper bound
    if bid is not None and bid - VOUCHER_SLACK_UPPER > upper:
        avail = depth.buy_orders[bid]
        sz = _clip_sell(position, CAP_VOUCHER, sold, min(avail, CAP_VOUCHER))
        if sz > 0:
            orders.append(Order(symbol, bid, -sz))
            sold += sz

    fair = _voucher_fair(ref, strike, vmid)

    # OTM short-theta: far out of money, ask ≤ few XY, pure decay trade
    moneyness = ref - strike
    if moneyness < -VOUCHER_OTM_SHORT_THRESHOLD and ask is not None and ask <= VOUCHER_OTM_SHORT_MAX_ASK:
        # sell at ask (passive) expecting price to decay
        sell_px = ask
        if bid is None or sell_px > bid:
            sz = _clip_sell(position, CAP_VOUCHER, sold, VOUCHER_OTM_SHORT_SIZE)
            if sz > 0:
                orders.append(Order(symbol, sell_px, -sz))
                sold += sz

    # Passive quoting: try inside-book first, fall back to fair±edge
    buy_px = None
    sell_px = None
    if bid is not None and ask is not None and ask > bid + 1:
        # step inside if fair supports
        candidate_buy = bid + 1
        if candidate_buy + VOUCHER_INSIDE_BOOK_MIN_MARGIN <= fair:
            buy_px = candidate_buy
        candidate_sell = ask - 1
        if candidate_sell >= fair + VOUCHER_INSIDE_BOOK_MIN_MARGIN:
            sell_px = candidate_sell
    if buy_px is None:
        edge = 2 if strike + 500 <= ref else 3
        px = int(math.floor(fair - edge))
        if px > 0 and (ask is None or px < ask):
            buy_px = px
    if sell_px is None:
        edge = 2 if strike + 500 <= ref else 3
        px = int(math.ceil(fair + edge))
        max_px = int(math.floor(upper - VOUCHER_SLACK_UPPER))
        if px <= max_px and (bid is None or px > bid):
            sell_px = px

    inv = (position + bought - sold) / float(CAP_VOUCHER)
    inv = max(-1.0, min(1.0, inv))
    buy_sz_raw = max(0, int(round(VOUCHER_PASSIVE_SIZE * max(0.0, 1.0 - 1.5 * inv))))
    sell_sz_raw = max(0, int(round(VOUCHER_PASSIVE_SIZE * max(0.0, 1.0 + 1.5 * inv))))

    if buy_px is not None and buy_px > 0:
        sz = _clip_buy(position, CAP_VOUCHER, bought, buy_sz_raw)
        if sz > 0:
            orders.append(Order(symbol, buy_px, sz))
            bought += sz
    if sell_px is not None and sell_px > (buy_px or 0):
        sz = _clip_sell(position, CAP_VOUCHER, sold, sell_sz_raw)
        if sz > 0:
            orders.append(Order(symbol, sell_px, -sz))
            sold += sz

    return orders


def _strike_mono(
    entries: List[Tuple[int, str]],
    depths: Dict[str, OrderDepth],
    positions: Dict[str, int],
) -> Dict[str, List[Order]]:
    out: Dict[str, List[Order]] = {}
    if not ENABLE_STRIKE_MONOTONICITY:
        return out
    for i in range(len(entries) - 1):
        k1, s1 = entries[i]
        k2, s2 = entries[i + 1]
        d1 = depths.get(s1)
        d2 = depths.get(s2)
        if d1 is None or d2 is None:
            continue
        a1 = _best_ask(d1)
        b2 = _best_bid(d2)
        if a1 is None or b2 is None:
            continue
        if b2 <= a1 + VOUCHER_SLACK_MONO:
            continue
        sz = min(-d1.sell_orders[a1], d2.buy_orders[b2], CAP_VOUCHER)
        bsz = _clip_buy(positions.get(s1, 0), CAP_VOUCHER, 0, sz)
        ssz = _clip_sell(positions.get(s2, 0), CAP_VOUCHER, 0, sz)
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
        seen: Dict[str, int] = dict(prior.get("seen", {}) or {})
        positions = state.position or {}
        depths = state.order_depths or {}

        hyd_depth = depths.get(HYDROGEL)
        hyd_imb = 0.0
        hyd_current_mid: Optional[float] = None
        hyd_vol_gate = False
        if hyd_depth is not None:
            hyd_current_mid = _mid(hyd_depth)
            m = _microprice(hyd_depth)
            if m is not None:
                blend = HYDROGEL_ANCHOR_WEIGHT * HYDROGEL_ANCHOR + (1 - HYDROGEL_ANCHOR_WEIGHT) * m
                fair_state[HYDROGEL] = _ewma(fair_state.get(HYDROGEL), blend, FV_EWMA_ALPHA_HYD)
            i = _imbalance(hyd_depth)
            if i is not None:
                hyd_imb = i
            # volatility gate: |last tick move| > threshold
            if hyd_current_mid is not None and HYDROGEL in last_mid:
                move = abs(hyd_current_mid - last_mid[HYDROGEL])
                if move > HYD_VOL_GATE_THRESHOLD:
                    hyd_vol_gate = True
            if hyd_current_mid is not None:
                last_mid[HYDROGEL] = hyd_current_mid

        vfe_depth = depths.get(VFE)
        if vfe_depth is not None:
            m = _microprice(vfe_depth)
            if m is not None:
                fair_state[VFE] = _ewma(fair_state.get(VFE), m, FV_EWMA_ALPHA_VFE)

        if hyd_depth is not None and HYDROGEL in fair_state:
            allow_take = True
            if hyd_current_mid is not None:
                if abs(hyd_current_mid - fair_state[HYDROGEL]) > HYD_REGIME_GUARD_DEV:
                    allow_take = False
            legs = _hydrogel_orders(
                hyd_depth, positions.get(HYDROGEL, 0),
                fair_state[HYDROGEL], hyd_imb, allow_take, hyd_vol_gate,
            )
            if legs:
                orders_out[HYDROGEL] = legs

        if vfe_depth is not None and VFE in fair_state:
            legs = _vfe_orders(vfe_depth, positions.get(VFE, 0), fair_state[VFE])
            if legs:
                orders_out[VFE] = legs

        entries: List[Tuple[int, str]] = []
        for sym in depths:
            if sym in (HYDROGEL, VFE):
                continue
            if not _is_voucher(sym):
                continue
            k = _parse_strike(sym)
            if k is None:
                continue
            entries.append((k, sym))
            seen[sym] = k
        entries.sort()

        ref = fair_state.get(VFE)
        if ref is None and vfe_depth is not None:
            ref = _mid(vfe_depth)

        for strike, sym in entries:
            vd = depths.get(sym)
            if vd is None:
                continue
            legs = _voucher_orders(sym, strike, vd, ref, positions.get(sym, 0))
            if legs:
                orders_out.setdefault(sym, []).extend(legs)

        mono = _strike_mono(entries, depths, positions)
        for sym, legs in mono.items():
            orders_out.setdefault(sym, []).extend(legs)

        blob = {
            "fair": {k: round(v, 4) for k, v in fair_state.items()},
            "last_mid": {k: round(v, 4) for k, v in last_mid.items()},
            "seen": seen,
        }
        td = json.dumps(blob, separators=(",", ":"))
        if len(td) > TRADER_DATA_MAX_BYTES:
            blob["seen"] = {}
            td = json.dumps(blob, separators=(",", ":"))
        return orders_out, 0, td

    def bid(self) -> int:
        return 20
