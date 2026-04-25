"""F4 — Time-regime gated trading. Bigger size mid-day, smaller near open/close.

Hypothesis: hosted log's top gains/drops cluster around ts 10k-90k. Mid-day
may have more MM opportunity; open/close more volatility. Gate size by
timestamp bucket. Test if adaptive sizing beats flat.
"""
import json, math
from typing import Dict, List, Optional
from datamodel import Order, OrderDepth, TradingState

HYD = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"
CAP_H = 200
CAP_V = 200
CAP_VOU = 300

ANCHOR = 10000.0
A_W = 0.40
A_HYD = 0.10
HTAKE = 4
HQUOTE = 3
HSKEW = 2.0
HGUARD = 120.0
HIMB = 5.0
HLEAN = 0.5

A_VFE = 0.20
VTAKE = 1
VQUOTE = 1
VSIZE = 60
VSKEW = 1.5

V_MKT_W = 0.7
V_MDL_W = 0.3
TV_A = 55.0
TV_W = 400.0
TV_POW = 1.8
TV_FLOOR = 0.5
V_SIZE = 25


def _hyd_size_for_ts(ts):
    # ts 0-99900. 0-10k open, 10k-90k main, 90k-100k close.
    if ts < 10000: return 10  # half size near open (more vol)
    if ts > 90000: return 15  # 75% near close
    return 30  # big mid-day


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
def _strike(s):
    if s.startswith("VEV_"):
        try: return int(s[4:])
        except: return None
    return None
def _cb(p, cap, a, w): return max(0, min(w, cap - (p + a)))
def _cs(p, cap, a, w): return max(0, min(w, cap + (p - a)))
def _ew(p, s, a): return s if p is None else p * (1 - a) + s * a
def _tv(S, K):
    d = abs(S - K)
    if d >= TV_W: return TV_FLOOR
    x = 1.0 - d / TV_W
    return max(TV_FLOOR, TV_A * (x ** TV_POW)) if x > 0 else TV_FLOOR
def _vfair(S, K, vm):
    intr = max(S - K, 0.0)
    m = max(0.0, min(intr + _tv(S, K), S))
    if vm is None: return m
    return max(intr, min(V_MKT_W * vm + V_MDL_W * m, S))


class Trader:
    def run(self, state: TradingState):
        out = {}
        try: prior = json.loads(state.traderData) if state.traderData else {}
        except: prior = {}
        fs = dict(prior.get("fs", {}) or {})
        positions = state.position or {}
        depths = state.order_depths or {}
        ts = state.timestamp or 0

        hd = depths.get(HYD)
        himb = 0.0
        if hd is not None:
            m = _micro(hd)
            if m is not None:
                blend = A_W * ANCHOR + (1 - A_W) * m
                fs[HYD] = _ew(fs.get(HYD), blend, A_HYD)
            himb = _imb(hd)
        vd = depths.get(VFE)
        if vd is not None:
            m = _micro(vd)
            if m is not None:
                fs[VFE] = _ew(fs.get(VFE), m, A_VFE)

        HSIZE_TS = _hyd_size_for_ts(ts)

        if hd is not None and HYD in fs:
            cm = _mid(hd)
            take_ok = cm is None or abs(cm - fs[HYD]) <= HGUARD
            legs = []
            f_adj = fs[HYD] + HIMB * himb
            bid = _bb(hd); ask = _ba(hd)
            pos = positions.get(HYD, 0)
            b = s = 0
            if take_ok:
                if ask is not None and ask + HTAKE <= f_adj:
                    av = -hd.sell_orders[ask]
                    sz = _cb(pos, CAP_H, b, min(av, CAP_H))
                    if sz > 0: legs.append(Order(HYD, ask, sz)); b += sz
                if bid is not None and bid - HTAKE >= f_adj:
                    av = hd.buy_orders[bid]
                    sz = _cs(pos, CAP_H, s, min(av, CAP_H))
                    if sz > 0: legs.append(Order(HYD, bid, -sz)); s += sz
            inv = max(-1.0, min(1.0, (pos + b - s) / CAP_H))
            bp = int(math.floor(f_adj - HQUOTE))
            sp = int(math.ceil(f_adj + HQUOTE))
            if bid is not None: bp = min(bp, bid + 1)
            if ask is not None: bp = min(bp, ask - 1); sp = max(sp, ask - 1)
            if bid is not None: sp = max(sp, bid + 1)
            bl = max(0.0, 1 + HLEAN * himb); sl = max(0.0, 1 - HLEAN * himb)
            bsz = _cb(pos, CAP_H, b, max(0, int(round(HSIZE_TS * bl * max(0.0, 1 - HSKEW * inv)))))
            ssz = _cs(pos, CAP_H, s, max(0, int(round(HSIZE_TS * sl * max(0.0, 1 + HSKEW * inv)))))
            if bsz > 0 and (ask is None or bp < ask): legs.append(Order(HYD, bp, bsz))
            if ssz > 0 and (bid is None or sp > bid): legs.append(Order(HYD, sp, -ssz))
            if legs: out[HYD] = legs

        if vd is not None and VFE in fs:
            legs = []
            bid = _bb(vd); ask = _ba(vd)
            pos = positions.get(VFE, 0)
            fair = fs[VFE]
            b = s = 0
            if ask is not None and ask + VTAKE <= fair:
                av = -vd.sell_orders[ask]
                sz = _cb(pos, CAP_V, b, min(av, CAP_V))
                if sz > 0: legs.append(Order(VFE, ask, sz)); b += sz
            if bid is not None and bid - VTAKE >= fair:
                av = vd.buy_orders[bid]
                sz = _cs(pos, CAP_V, s, min(av, CAP_V))
                if sz > 0: legs.append(Order(VFE, bid, -sz)); s += sz
            inv = max(-1.0, min(1.0, (pos + b - s) / CAP_V))
            bp = int(math.floor(fair - VQUOTE))
            sp = int(math.ceil(fair + VQUOTE))
            if bid is not None: bp = min(bp, bid + 1)
            if ask is not None: bp = min(bp, ask - 1); sp = max(sp, ask - 1)
            if bid is not None: sp = max(sp, bid + 1)
            bsz = _cb(pos, CAP_V, b, max(0, int(round(VSIZE * max(0.0, 1 - VSKEW * inv)))))
            ssz = _cs(pos, CAP_V, s, max(0, int(round(VSIZE * max(0.0, 1 + VSKEW * inv)))))
            if bsz > 0 and (ask is None or bp < ask): legs.append(Order(VFE, bp, bsz))
            if ssz > 0 and (bid is None or sp > bid): legs.append(Order(VFE, sp, -ssz))
            if legs: out[VFE] = legs

        ref = fs.get(VFE)
        if ref is None and vd is not None: ref = _mid(vd)
        ents = []
        for sym in depths:
            if sym in (HYD, VFE): continue
            k = _strike(sym)
            if k is None or not (4000 <= k <= 6500): continue
            ents.append((k, sym))
        ents.sort()
        for k, sym in ents:
            d_ = depths.get(sym)
            if d_ is None or ref is None: continue
            bid = _bb(d_); ask = _ba(d_)
            pos = positions.get(sym, 0)
            vmid = _mid(d_)
            intr = max(ref - k, 0.0)
            fair = _vfair(ref, k, vmid)
            legs = []
            b = s = 0
            if ask is not None and ask + 1 < intr:
                av = -d_.sell_orders[ask]
                sz = _cb(pos, CAP_VOU, b, min(av, CAP_VOU))
                if sz > 0: legs.append(Order(sym, ask, sz)); b += sz
            if bid is not None and bid - 1 > ref:
                av = d_.buy_orders[bid]
                sz = _cs(pos, CAP_VOU, s, min(av, CAP_VOU))
                if sz > 0: legs.append(Order(sym, bid, -sz)); s += sz
            edge = 2 if k + 500 <= ref else 3
            bp = int(math.floor(fair - edge))
            sp = int(math.ceil(fair + edge))
            if ask is not None: bp = min(bp, ask - 1)
            if bid is not None: sp = max(sp, bid + 1)
            bp = max(bp, 1)
            bsz = _cb(pos, CAP_VOU, b, V_SIZE)
            ssz = _cs(pos, CAP_VOU, s, V_SIZE)
            if bsz > 0 and bp > 0 and (ask is None or bp < ask):
                legs.append(Order(sym, bp, bsz))
            if ssz > 0 and sp > bp and (bid is None or sp > bid):
                legs.append(Order(sym, sp, -ssz))
            if legs: out.setdefault(sym, []).extend(legs)

        blob = {"fs": {k: round(v, 4) for k, v in fs.items()}}
        return out, 0, json.dumps(blob, separators=(",", ":"))

    def bid(self): return 20
