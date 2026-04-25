"""F5 — HYDROGEL-ONLY subset. Strip VFE + vouchers.

Hypothesis: passive MM on HYDROGEL generates +6,072 hosted alone. VFE/voucher
modules may dilute that. Test: HYDROGEL at full cap 200, size 40, no other
trading. If local >= 85k, this subset dominates.
"""
import json, math
from typing import Dict, List, Optional
from datamodel import Order, OrderDepth, TradingState

HYD = "HYDROGEL_PACK"
CAP = 200
ANCHOR = 10000.0
ANCHOR_W = 0.40
ALPHA = 0.10
TAKE_E = 4
QUOTE_E = 3
SIZE = 40  # 2x v01
SKEW = 2.0
GUARD = 120.0
IMB_COEF = 5.0
IMB_LEAN = 0.5


def _bb(d): return max(d.buy_orders) if d.buy_orders else None
def _ba(d): return min(d.sell_orders) if d.sell_orders else None
def _mid(d):
    b, a = _bb(d), _ba(d)
    return None if b is None or a is None else (b + a) / 2.0
def _micro(d):
    b, a = _bb(d), _ba(d)
    if b is None or a is None: return None
    bv = d.buy_orders[b]; av = -d.sell_orders[a]
    t = bv + av
    return (b + a) / 2.0 if t <= 0 else (a * bv + b * av) / t
def _imb(d):
    b, a = _bb(d), _ba(d)
    if b is None or a is None: return 0.0
    bv = d.buy_orders[b]; av = -d.sell_orders[a]
    t = bv + av
    return 0.0 if t <= 0 else (bv - av) / t
def _cb(p, cap, a, w): return max(0, min(w, cap - (p + a)))
def _cs(p, cap, a, w): return max(0, min(w, cap + (p - a)))
def _ew(p, s, a): return s if p is None else p * (1 - a) + s * a


class Trader:
    def run(self, state: TradingState):
        out = {}
        try: prior = json.loads(state.traderData) if state.traderData else {}
        except: prior = {}
        fair = prior.get("f")
        pos = (state.position or {}).get(HYD, 0)
        depths = state.order_depths or {}
        d = depths.get(HYD)
        if d is None:
            return out, 0, json.dumps({"f": fair}) if fair is not None else "{}"
        m = _micro(d)
        if m is not None:
            blend = ANCHOR_W * ANCHOR + (1 - ANCHOR_W) * m
            fair = _ew(fair, blend, ALPHA)
        cm = _mid(d)
        if fair is None:
            return out, 0, "{}"
        take_ok = cm is None or abs(cm - fair) <= GUARD
        imb = _imb(d)
        f_adj = fair + IMB_COEF * imb
        bid = _bb(d); ask = _ba(d)
        legs = []
        b = s = 0
        if take_ok:
            if ask is not None and ask + TAKE_E <= f_adj:
                av = -d.sell_orders[ask]
                sz = _cb(pos, CAP, b, min(av, CAP))
                if sz > 0: legs.append(Order(HYD, ask, sz)); b += sz
            if bid is not None and bid - TAKE_E >= f_adj:
                av = d.buy_orders[bid]
                sz = _cs(pos, CAP, s, min(av, CAP))
                if sz > 0: legs.append(Order(HYD, bid, -sz)); s += sz
        inv = max(-1.0, min(1.0, (pos + b - s) / CAP))
        bp = int(math.floor(f_adj - QUOTE_E))
        sp = int(math.ceil(f_adj + QUOTE_E))
        if bid is not None: bp = min(bp, bid + 1)
        if ask is not None: bp = min(bp, ask - 1); sp = max(sp, ask - 1)
        if bid is not None: sp = max(sp, bid + 1)
        bl = max(0.0, 1 + IMB_LEAN * imb); sl = max(0.0, 1 - IMB_LEAN * imb)
        bsz = _cb(pos, CAP, b, max(0, int(round(SIZE * bl * max(0.0, 1 - SKEW * inv)))))
        ssz = _cs(pos, CAP, s, max(0, int(round(SIZE * sl * max(0.0, 1 + SKEW * inv)))))
        if bsz > 0 and (ask is None or bp < ask): legs.append(Order(HYD, bp, bsz))
        if ssz > 0 and (bid is None or sp > bid): legs.append(Order(HYD, sp, -ssz))
        if legs: out[HYD] = legs
        return out, 0, json.dumps({"f": round(fair, 4)})

    def bid(self): return 20
