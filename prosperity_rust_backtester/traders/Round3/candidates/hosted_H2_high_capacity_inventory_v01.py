"""H2 High-capacity scaled baseline: every size 3x, official caps, same logic.
Hypothesis: 72k curve suggests much larger position-holding than our current size 20."""
import json, math
from datamodel import Order, OrderDepth, TradingState

HYD = "HYDROGEL_PACK"; VFE = "VELVETFRUIT_EXTRACT"
CAP_H = 200; CAP_V = 200; CAP_VOU = 300
ANCHOR = 10000.0; A_W = 0.40; A_HYD = 0.10
H_TAKE = 2; H_QE = 2; H_SIZE = 60; H_SKEW = 1.5; H_IMB = 5.0
A_VFE = 0.20; V_TAKE = 1; V_QE = 1; V_SIZE = 120; V_SKEW = 1.2
TV_A = 55.0; TV_W = 400.0; TV_POW = 1.8; TV_FL = 0.5
VMKT = 0.7; VMDL = 0.3; VOU_SIZE = 75

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
def _cb(p, c, ad, w): return max(0, min(w, c - (p + ad)))
def _cs(p, c, ad, w): return max(0, min(w, c + (p - ad)))
def _ew(p, s, a): return s if p is None else p * (1 - a) + s * a
def _tv(S, K):
    d = abs(S - K)
    if d >= TV_W: return TV_FL
    x = 1 - d / TV_W
    return max(TV_FL, TV_A * (x ** TV_POW)) if x > 0 else TV_FL
def _vfair(S, K, vm):
    intr = max(S - K, 0.0)
    m = max(0.0, min(intr + _tv(S, K), S))
    if vm is None: return m
    return max(intr, min(VMKT * vm + VMDL * m, S))

class Trader:
    def run(self, state):
        out = {}
        try: prior = json.loads(state.traderData) if state.traderData else {}
        except: prior = {}
        fs = dict(prior.get("fs", {}) or {})
        positions = state.position or {}
        depths = state.order_depths or {}

        hd = depths.get(HYD); himb = 0.0
        if hd is not None:
            m = _micro(hd)
            if m is not None:
                fs[HYD] = _ew(fs.get(HYD), A_W * ANCHOR + (1 - A_W) * m, A_HYD)
            himb = _imb(hd)
        vd = depths.get(VFE)
        if vd is not None:
            m = _micro(vd)
            if m is not None: fs[VFE] = _ew(fs.get(VFE), m, A_VFE)

        # HYDROGEL aggressive MM
        if hd is not None and HYD in fs:
            bid = _bb(hd); ask = _ba(hd); pos = positions.get(HYD, 0)
            fair = fs[HYD] + H_IMB * himb
            legs = []; b = s = 0
            if ask is not None and ask + H_TAKE <= fair:
                av = -hd.sell_orders[ask]
                sz = _cb(pos, CAP_H, b, min(av, CAP_H))
                if sz > 0: legs.append(Order(HYD, ask, sz)); b += sz
            if bid is not None and bid - H_TAKE >= fair:
                av = hd.buy_orders[bid]
                sz = _cs(pos, CAP_H, s, min(av, CAP_H))
                if sz > 0: legs.append(Order(HYD, bid, -sz)); s += sz
            inv = max(-1.0, min(1.0, (pos + b - s) / CAP_H))
            bp = int(math.floor(fair - H_QE))
            sp = int(math.ceil(fair + H_QE))
            if bid is not None: bp = min(bp, bid + 1)
            if ask is not None: bp = min(bp, ask - 1); sp = max(sp, ask - 1)
            if bid is not None: sp = max(sp, bid + 1)
            bsz = _cb(pos, CAP_H, b, max(0, int(round(H_SIZE * max(0.0, 1 - H_SKEW * inv)))))
            ssz = _cs(pos, CAP_H, s, max(0, int(round(H_SIZE * max(0.0, 1 + H_SKEW * inv)))))
            if bsz > 0 and (ask is None or bp < ask): legs.append(Order(HYD, bp, bsz))
            if ssz > 0 and (bid is None or sp > bid): legs.append(Order(HYD, sp, -ssz))
            if legs: out[HYD] = legs

        if vd is not None and VFE in fs:
            bid = _bb(vd); ask = _ba(vd); pos = positions.get(VFE, 0)
            fair = fs[VFE]
            legs = []; b = s = 0
            if ask is not None and ask + V_TAKE <= fair:
                av = -vd.sell_orders[ask]
                sz = _cb(pos, CAP_V, b, min(av, CAP_V))
                if sz > 0: legs.append(Order(VFE, ask, sz)); b += sz
            if bid is not None and bid - V_TAKE >= fair:
                av = vd.buy_orders[bid]
                sz = _cs(pos, CAP_V, s, min(av, CAP_V))
                if sz > 0: legs.append(Order(VFE, bid, -sz)); s += sz
            inv = max(-1.0, min(1.0, (pos + b - s) / CAP_V))
            bp = int(math.floor(fair - V_QE))
            sp = int(math.ceil(fair + V_QE))
            if bid is not None: bp = min(bp, bid + 1)
            if ask is not None: bp = min(bp, ask - 1); sp = max(sp, ask - 1)
            if bid is not None: sp = max(sp, bid + 1)
            bsz = _cb(pos, CAP_V, b, max(0, int(round(V_SIZE * max(0.0, 1 - V_SKEW * inv)))))
            ssz = _cs(pos, CAP_V, s, max(0, int(round(V_SIZE * max(0.0, 1 + V_SKEW * inv)))))
            if bsz > 0 and (ask is None or bp < ask): legs.append(Order(VFE, bp, bsz))
            if ssz > 0 and (bid is None or sp > bid): legs.append(Order(VFE, sp, -ssz))
            if legs: out[VFE] = legs

        ref = fs.get(VFE)
        if ref is None and vd is not None: ref = _mid(vd)
        for sym in depths:
            if sym in (HYD, VFE): continue
            k = _strike(sym)
            if k is None or not (4000 <= k <= 6500): continue
            d_ = depths.get(sym)
            if d_ is None or ref is None: continue
            bid = _bb(d_); ask = _ba(d_)
            vmid = _mid(d_); pos = positions.get(sym, 0)
            intr = max(ref - k, 0.0)
            fair = _vfair(ref, k, vmid)
            legs = []; b = s = 0
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
            if bid is not None and ask is not None and ask > bid + 1:
                cb = bid + 1
                if cb + 1 <= fair: bp = cb
                cs_ = ask - 1
                if cs_ >= fair + 1: sp = cs_
            if ask is not None: bp = min(bp, ask - 1)
            if bid is not None: sp = max(sp, bid + 1)
            bp = max(bp, 1)
            bsz = _cb(pos, CAP_VOU, b, VOU_SIZE)
            ssz = _cs(pos, CAP_VOU, s, VOU_SIZE)
            if bsz > 0 and bp > 0 and (ask is None or bp < ask): legs.append(Order(sym, bp, bsz))
            if ssz > 0 and sp > bp and (bid is None or sp > bid): legs.append(Order(sym, sp, -ssz))
            if legs: out[sym] = legs

        return out, 0, json.dumps({"fs": {k: round(v, 4) for k, v in fs.items()}})
    def bid(self): return 20
