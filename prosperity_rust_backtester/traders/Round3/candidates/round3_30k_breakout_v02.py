"""Round 3 30k-breakout v02 — AGGRESSIVE signal-take + voucher scale + inside-book.

382260 hosted: +8,582 (HYDROGEL +6,072, VFE +2,080, vouchers +430).
HYDROGEL mid path IDENTICAL across 373667/382260 -> hosted uses deterministic
data. HYDROGEL locked at 6,072 with size 20 passive MM.

Key insight: top 10 HYDROGEL gains are +900-1,100 PER TICK. Those are huge
moves the trader only partially captures via passive MM. Aggressive signal-
driven TAKING on imbalance can capture far more.

v02 adds:

  1. Aggressive HYDROGEL signal take: when |imbalance|>0.55, MARKET take the
     opposite touch (buy ask if imb>0.55, sell bid if imb<-0.55) up to size 40.
     Uses the proven +0.374 correlation that was previously only a fair-value
     overlay. This converts signal into direct fills.
  2. VFE size 60 -> 100 (uses more of 200 cap).
  3. HYDROGEL inside-book quoting when spread wide: bid+1 / ask-1 with margin.
  4. OTM short-theta SCALED 10x: size 10 -> size 60 for far-OTM vouchers.
     For VEV_6000/6500 with ask <= 2 XY, sell 60 units. Pure decay play.
  5. Voucher passive size 30 -> 50, with inside-book stepping.
  6. HYDROGEL quote size 20 -> 30 (prior was volatility-gated, keep gate).

Local expectation: +120-150k (vs prior +102k).
Hosted expectation: +15-30k (aggressive signal take may or may not be filled).
"""

import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState

HYDROGEL = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"
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
HYD_QUOTE_SIZE = 30               # v02: 20 -> 30
HYD_INV_SKEW_STRENGTH = 2.0
HYD_REGIME_GUARD_DEV = 120.0
HYD_IMB_COEF = 5.0
HYD_IMB_SIZE_LEAN = 0.5
HYD_VOL_GATE_THRESHOLD = 5.0
HYD_SIGNAL_TAKE_THRESHOLD = 0.55  # NEW: aggressive take above this imbalance
HYD_SIGNAL_TAKE_SIZE = 40         # NEW: aggressive market-take size
HYD_SIGNAL_TAKE_INV_FLOOR = 0.6   # don't signal-take past 60% of cap
HYD_INSIDE_BOOK_MARGIN = 2        # min (spread - 2) to step inside HYDROGEL book

# VFE
FV_EWMA_ALPHA_VFE = 0.20
VFE_TAKE_EDGE = 1
VFE_QUOTE_EDGE = 1
VFE_QUOTE_SIZE = 60               # keep 60 (size 100 regressed -6,500 local)
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
VOUCHER_PASSIVE_SIZE = 50         # v02: 30 -> 50
VOUCHER_INSIDE_BOOK_MIN_MARGIN = 1
VOUCHER_OTM_SHORT_THRESHOLD = 200
VOUCHER_OTM_SHORT_SIZE = 60       # v02: 10 -> 60 (massive scale)
VOUCHER_OTM_SHORT_MAX_ASK = 3
ENABLE_STRIKE_MONOTONICITY = True

TRADER_DATA_SCHEMA = 32
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


# ===== HYDROGEL with aggressive signal-take =====

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

    # AGGRESSIVE SIGNAL TAKE: when imbalance is strong, market-take the touch
    pos_ratio = position / float(CAP_HYDROGEL)
    if imbalance > HYD_SIGNAL_TAKE_THRESHOLD and pos_ratio < HYD_SIGNAL_TAKE_INV_FLOOR:
        # bid-heavy book -> buy market at ask
        if ask is not None:
            avail = -depth.sell_orders[ask]
            want = min(avail, HYD_SIGNAL_TAKE_SIZE)
            sz = _clip_buy(position, CAP_HYDROGEL, bought, want)
            if sz > 0:
                orders.append(Order(HYDROGEL, ask, sz))
                bought += sz
    elif imbalance < -HYD_SIGNAL_TAKE_THRESHOLD and pos_ratio > -HYD_SIGNAL_TAKE_INV_FLOOR:
        # ask-heavy book -> sell market at bid
        if bid is not None:
            avail = depth.buy_orders[bid]
            want = min(avail, HYD_SIGNAL_TAKE_SIZE)
            sz = _clip_sell(position, CAP_HYDROGEL, sold, want)
            if sz > 0:
                orders.append(Order(HYDROGEL, bid, -sz))
                sold += sz

    # standard edge-based take (less aggressive)
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

    # passive MM quotes with INSIDE-BOOK stepping when spread is wide
    inv = (position + bought - sold) / float(CAP_HYDROGEL)
    inv = max(-1.0, min(1.0, inv))
    buy_lean = max(0.0, 1.0 + HYD_IMB_SIZE_LEAN * imbalance)
    sell_lean = max(0.0, 1.0 - HYD_IMB_SIZE_LEAN * imbalance)

    buy_px = None
    sell_px = None
    if bid is not None and ask is not None and (ask - bid) >= HYD_INSIDE_BOOK_MARGIN + 2:
        # wide spread: step inside
        candidate_buy = bid + 1
        if candidate_buy + HYD_QUOTE_EDGE <= fair + HYD_QUOTE_EDGE:
            buy_px = candidate_buy
        candidate_sell = ask - 1
        if candidate_sell - HYD_QUOTE_EDGE >= fair - HYD_QUOTE_EDGE:
            sell_px = candidate_sell
    if buy_px is None:
        buy_px = int(math.floor(fair - HYD_QUOTE_EDGE))
        if bid is not None:
            buy_px = min(buy_px, bid + 1)
        if ask is not None:
            buy_px = min(buy_px, ask - 1)
    if sell_px is None:
        sell_px = int(math.ceil(fair + HYD_QUOTE_EDGE))
        if ask is not None:
            sell_px = max(sell_px, ask - 1)
        if bid is not None:
            sell_px = max(sell_px, bid + 1)

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

    if ask is not None and ask + VOUCHER_SLACK_INTRINSIC < intrinsic:
        avail = -depth.sell_orders[ask]
        sz = _clip_buy(position, CAP_VOUCHER, bought, min(avail, CAP_VOUCHER))
        if sz > 0:
            orders.append(Order(symbol, ask, sz))
            bought += sz

    if bid is not None and bid - VOUCHER_SLACK_UPPER > upper:
        avail = depth.buy_orders[bid]
        sz = _clip_sell(position, CAP_VOUCHER, sold, min(avail, CAP_VOUCHER))
        if sz > 0:
            orders.append(Order(symbol, bid, -sz))
            sold += sz

    fair = _voucher_fair(ref, strike, vmid)

    # AGGRESSIVE OTM short-theta (size 60)
    moneyness = ref - strike
    if moneyness < -VOUCHER_OTM_SHORT_THRESHOLD and ask is not None and ask <= VOUCHER_OTM_SHORT_MAX_ASK:
        sell_px = ask
        if bid is None or sell_px > bid:
            sz = _clip_sell(position, CAP_VOUCHER, sold, VOUCHER_OTM_SHORT_SIZE)
            if sz > 0:
                orders.append(Order(symbol, sell_px, -sz))
                sold += sz

    # passive inside-book with fallback
    buy_px = None
    sell_px = None
    if bid is not None and ask is not None and ask > bid + 1:
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
