"""Family F2 — Pure passive max-scale with huge voucher passive.

F1 failed (-8,197 local) proving pure signal-taking without MM collapses.
Passive MM IS the primary edge. F2 tests: keep proven passive MM, scale
voucher passive from 30 to 100 (3.3x).

Hypothesis: voucher strike 4000/4500 already +150 hosted with size 30. Size
100 could 3x that = +450 hosted. Plus activating dormant strikes if books
complete.
"""

import json, math
from typing import Dict, List, Optional, Tuple
from datamodel import Order, OrderDepth, TradingState

HYDROGEL = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"
CAP_HYDROGEL = 200
CAP_VFE = 200
CAP_VOUCHER = 300

HYDROGEL_ANCHOR = 10000.0
HYDROGEL_ANCHOR_WEIGHT = 0.40
FV_EWMA_ALPHA_HYD = 0.10
HYD_TAKE_EDGE = 4
HYD_QUOTE_EDGE = 3
HYD_QUOTE_SIZE = 20
HYD_INV_SKEW = 2.0
HYD_REGIME_DEV = 120.0
HYD_IMB_COEF = 5.0
HYD_IMB_LEAN = 0.5

FV_EWMA_ALPHA_VFE = 0.20
VFE_TAKE_EDGE = 1
VFE_QUOTE_EDGE = 1
VFE_QUOTE_SIZE = 60
VFE_INV_SKEW = 1.5

# *** AGGRESSIVE voucher scale ***
VOUCHER_PASSIVE_SIZE = 100        # was 30. 3.3x.
TV_A = 55.0
TV_W = 400.0
TV_POW = 1.8
TV_OTM_FLOOR = 0.5
VOUCHER_MKT_W = 0.70
VOUCHER_MDL_W = 0.30
ENABLE_STRIKE_MONO = True


def _bb(d): return max(d.buy_orders) if d.buy_orders else None
def _ba(d): return min(d.sell_orders) if d.sell_orders else None
def _mid(d):
    b, a = _bb(d), _ba(d)
    return None if b is None or a is None else (b + a) / 2.0
def _micro(d):
    b = _bb(d); a = _ba(d)
    if b is None or a is None: return None
    bv = d.buy_orders[b]; av = -d.sell_orders[a]
    t = bv + av
    return (b + a) / 2.0 if t <= 0 else (a * bv + b * av) / t
def _imb(d):
    b = _bb(d); a = _ba(d)
    if b is None or a is None: return 0.0
    bv = d.buy_orders[b]; av = -d.sell_orders[a]
    t = bv + av
    return 0.0 if t <= 0 else (bv - av) / t
def _strike(s):
    if s.startswith("VEV_"):
        try: return int(s[4:])
        except: return None
    return None
def _is_vev(s):
    k = _strike(s); return k is not None and 4000 <= k <= 6500
def _cb(p, cap, ad, w): return max(0, min(w, cap - (p + ad)))
def _cs(p, cap, ad, w): return max(0, min(w, cap + (p - ad)))
def _ewma(prior, s, a): return s if prior is None else prior * (1 - a) + s * a
def _tv(S, K):
    d = abs(S - K)
    if d >= TV_W: return TV_OTM_FLOOR
    x = 1.0 - d / TV_W
    return max(TV_OTM_FLOOR, TV_A * (x ** TV_POW)) if x > 0 else TV_OTM_FLOOR
def _vfair(S, K, vm):
    intr = max(S - K, 0.0)
    m = max(0.0, min(intr + _tv(S, K), S))
    if vm is None: return m
    return max(intr, min(VOUCHER_MKT_W * vm + VOUCHER_MDL_W * m, S))


def _hyd(depth, pos, fair, imb, take_ok):
    orders = []
    bid = _bb(depth); ask = _ba(depth)
    if bid is None and ask is None: return orders
    f = fair + HYD_IMB_COEF * imb
    b = s = 0
    if take_ok:
        if ask is not None and ask + HYD_TAKE_EDGE <= f:
            av = -depth.sell_orders[ask]
            sz = _cb(pos, CAP_HYDROGEL, b, min(av, CAP_HYDROGEL))
            if sz > 0: orders.append(Order(HYDROGEL, ask, sz)); b += sz
        if bid is not None and bid - HYD_TAKE_EDGE >= f:
            av = depth.buy_orders[bid]
            sz = _cs(pos, CAP_HYDROGEL, s, min(av, CAP_HYDROGEL))
            if sz > 0: orders.append(Order(HYDROGEL, bid, -sz)); s += sz
    inv = max(-1.0, min(1.0, (pos + b - s) / CAP_HYDROGEL))
    bp = int(math.floor(f - HYD_QUOTE_EDGE))
    sp = int(math.ceil(f + HYD_QUOTE_EDGE))
    if bid is not None: bp = min(bp, bid + 1)
    if ask is not None: bp = min(bp, ask - 1); sp = max(sp, ask - 1)
    if bid is not None: sp = max(sp, bid + 1)
    bl = max(0.0, 1 + HYD_IMB_LEAN * imb); sl = max(0.0, 1 - HYD_IMB_LEAN * imb)
    bsz = _cb(pos, CAP_HYDROGEL, b, max(0, int(round(HYD_QUOTE_SIZE * bl * max(0.0, 1 - HYD_INV_SKEW * inv)))))
    ssz = _cs(pos, CAP_HYDROGEL, s, max(0, int(round(HYD_QUOTE_SIZE * sl * max(0.0, 1 + HYD_INV_SKEW * inv)))))
    if bsz > 0 and (ask is None or bp < ask): orders.append(Order(HYDROGEL, bp, bsz))
    if ssz > 0 and (bid is None or sp > bid): orders.append(Order(HYDROGEL, sp, -ssz))
    return orders


def _vfe(depth, pos, fair):
    orders = []
    bid = _bb(depth); ask = _ba(depth)
    if bid is None and ask is None: return orders
    b = s = 0
    if ask is not None and ask + VFE_TAKE_EDGE <= fair:
        av = -depth.sell_orders[ask]
        sz = _cb(pos, CAP_VFE, b, min(av, CAP_VFE))
        if sz > 0: orders.append(Order(VFE, ask, sz)); b += sz
    if bid is not None and bid - VFE_TAKE_EDGE >= fair:
        av = depth.buy_orders[bid]
        sz = _cs(pos, CAP_VFE, s, min(av, CAP_VFE))
        if sz > 0: orders.append(Order(VFE, bid, -sz)); s += sz
    inv = max(-1.0, min(1.0, (pos + b - s) / CAP_VFE))
    bp = int(math.floor(fair - VFE_QUOTE_EDGE))
    sp = int(math.ceil(fair + VFE_QUOTE_EDGE))
    if bid is not None: bp = min(bp, bid + 1)
    if ask is not None: bp = min(bp, ask - 1); sp = max(sp, ask - 1)
    if bid is not None: sp = max(sp, bid + 1)
    bsz = _cb(pos, CAP_VFE, b, max(0, int(round(VFE_QUOTE_SIZE * max(0.0, 1 - VFE_INV_SKEW * inv)))))
    ssz = _cs(pos, CAP_VFE, s, max(0, int(round(VFE_QUOTE_SIZE * max(0.0, 1 + VFE_INV_SKEW * inv)))))
    if bsz > 0 and (ask is None or bp < ask): orders.append(Order(VFE, bp, bsz))
    if ssz > 0 and (bid is None or sp > bid): orders.append(Order(VFE, sp, -ssz))
    return orders


def _vouch(sym, k, depth, ref, pos):
    if ref is None: return []
    bid = _bb(depth); ask = _ba(depth)
    vm = _mid(depth)
    intr = max(ref - k, 0.0)
    fair = _vfair(ref, k, vm)
    orders = []
    b = s = 0
    if ask is not None and ask + 1 < intr:
        av = -depth.sell_orders[ask]
        sz = _cb(pos, CAP_VOUCHER, b, min(av, CAP_VOUCHER))
        if sz > 0: orders.append(Order(sym, ask, sz)); b += sz
    if bid is not None and bid - 1 > ref:
        av = depth.buy_orders[bid]
        sz = _cs(pos, CAP_VOUCHER, s, min(av, CAP_VOUCHER))
        if sz > 0: orders.append(Order(sym, bid, -sz)); s += sz
    # passive MASSIVE inside-book
    bp = sp = None
    if bid is not None and ask is not None and ask > bid + 1:
        cb = bid + 1; cs_ = ask - 1
        if cb + 1 <= fair: bp = cb
        if cs_ >= fair + 1: sp = cs_
    if bp is None:
        edge = 2 if k + 500 <= ref else 3
        px = int(math.floor(fair - edge))
        if px > 0 and (ask is None or px < ask): bp = px
    if sp is None:
        edge = 2 if k + 500 <= ref else 3
        px = int(math.ceil(fair + edge))
        maxp = int(math.floor(ref - 1))
        if px <= maxp and (bid is None or px > bid): sp = px
    inv = max(-1.0, min(1.0, (pos + b - s) / CAP_VOUCHER))
    br = max(0, int(round(VOUCHER_PASSIVE_SIZE * max(0.0, 1 - 1.5 * inv))))
    sr = max(0, int(round(VOUCHER_PASSIVE_SIZE * max(0.0, 1 + 1.5 * inv))))
    if bp is not None and bp > 0:
        sz = _cb(pos, CAP_VOUCHER, b, br)
        if sz > 0: orders.append(Order(sym, bp, sz)); b += sz
    if sp is not None and sp > (bp or 0):
        sz = _cs(pos, CAP_VOUCHER, s, sr)
        if sz > 0: orders.append(Order(sym, sp, -sz)); s += sz
    return orders


def _mono(ents, depths, positions):
    out = {}
    if not ENABLE_STRIKE_MONO: return out
    for i in range(len(ents) - 1):
        k1, s1 = ents[i]; k2, s2 = ents[i + 1]
        d1 = depths.get(s1); d2 = depths.get(s2)
        if d1 is None or d2 is None: continue
        a1 = _ba(d1); b2 = _bb(d2)
        if a1 is None or b2 is None: continue
        if b2 <= a1 + 1: continue
        sz = min(-d1.sell_orders[a1], d2.buy_orders[b2], CAP_VOUCHER)
        bsz = _cb(positions.get(s1, 0), CAP_VOUCHER, 0, sz)
        ssz = _cs(positions.get(s2, 0), CAP_VOUCHER, 0, sz)
        p = min(bsz, ssz)
        if p > 0:
            out.setdefault(s1, []).append(Order(s1, a1, p))
            out.setdefault(s2, []).append(Order(s2, b2, -p))
    return out


class Trader:
    def run(self, state: TradingState):
        out = {}
        try: prior = json.loads(state.traderData) if state.traderData else {}
        except: prior = {}
        fs = dict(prior.get("fair", {}) or {})
        positions = state.position or {}
        depths = state.order_depths or {}

        hd = depths.get(HYDROGEL)
        himb = 0.0
        if hd is not None:
            m = _micro(hd)
            if m is not None:
                blend = HYDROGEL_ANCHOR_WEIGHT * HYDROGEL_ANCHOR + (1 - HYDROGEL_ANCHOR_WEIGHT) * m
                fs[HYDROGEL] = _ewma(fs.get(HYDROGEL), blend, FV_EWMA_ALPHA_HYD)
            i = _imb(hd)
            if i is not None: himb = i

        vd = depths.get(VFE)
        if vd is not None:
            m = _micro(vd)
            if m is not None:
                fs[VFE] = _ewma(fs.get(VFE), m, FV_EWMA_ALPHA_VFE)

        if hd is not None and HYDROGEL in fs:
            cm = _mid(hd)
            take_ok = cm is None or abs(cm - fs[HYDROGEL]) <= HYD_REGIME_DEV
            legs = _hyd(hd, positions.get(HYDROGEL, 0), fs[HYDROGEL], himb, take_ok)
            if legs: out[HYDROGEL] = legs

        if vd is not None and VFE in fs:
            legs = _vfe(vd, positions.get(VFE, 0), fs[VFE])
            if legs: out[VFE] = legs

        ents = []
        for sym in depths:
            if sym in (HYDROGEL, VFE): continue
            if not _is_vev(sym): continue
            k = _strike(sym)
            if k is not None: ents.append((k, sym))
        ents.sort()
        ref = fs.get(VFE)
        if ref is None and vd is not None: ref = _mid(vd)
        for k, sym in ents:
            d_ = depths.get(sym)
            if d_ is None: continue
            legs = _vouch(sym, k, d_, ref, positions.get(sym, 0))
            if legs: out.setdefault(sym, []).extend(legs)
        mono = _mono(ents, depths, positions)
        for sym, legs in mono.items():
            out.setdefault(sym, []).extend(legs)

        blob = {"fair": {k: round(v, 4) for k, v in fs.items()}}
        return out, 0, json.dumps(blob, separators=(",", ":"))

    def bid(self) -> int:
        return 20
