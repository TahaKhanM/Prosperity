"""P3 HYDROGEL curve-shape breakout.

Hosted 384674 data: HYDROGEL has top 10 gains summing +9,702 and drops -9,614.
Net on extremes ~0. Passive MM captures +6,072. If we can just BUY at the 10
extreme dips and SELL at the 10 extreme peaks we'd get ~18-19k HYDROGEL alone.

P3 mechanism: Binary anchor band at FULL cap 200.
  - mid < 9985: buy aggressively, size up to cap 200
  - mid > 10015: sell aggressively, size up to cap 200
  - mid in [9990, 10010]: flatten toward 0
  - No passive MM (proved to cap at 6k)

This differs from R7 (which used size 30 and caps 200). P3 uses size 80 per tick
for aggressive accumulation when price dislocates from anchor.

Plus keep baseline VFE MM and voucher identity arbs for floor PnL.
"""
import json, math
from datamodel import Order, OrderDepth, TradingState

HYD = "HYDROGEL_PACK"; VFE = "VELVETFRUIT_EXTRACT"
CAP_H = 200; CAP_V = 200; CAP_VOU = 300
ANCHOR = 10000.0
BAND_IN = 15  # buy/sell when |mid-anchor|>=15
BAND_OUT = 5  # flatten when |mid-anchor|<=5
ACC_SIZE = 80
FLATTEN_SIZE = 60
A_VFE = 0.20; V_TAKE = 1; V_QE = 1; V_SIZE = 40

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
def _strike(s):
    if s.startswith("VEV_"):
        try: return int(s[4:])
        except: return None
    return None
def _cb(p, c, ad, w): return max(0, min(w, c - (p + ad)))
def _cs(p, c, ad, w): return max(0, min(w, c + (p - ad)))
def _ew(p, s, a): return s if p is None else p * (1 - a) + s * a

class Trader:
    def run(self, state):
        out = {}
        try: prior = json.loads(state.traderData) if state.traderData else {}
        except: prior = {}
        fs = dict(prior.get("fs", {}) or {})
        positions = state.position or {}
        depths = state.order_depths or {}

        # HYDROGEL curve-shape band
        hd = depths.get(HYD)
        if hd is not None:
            bid = _bb(hd); ask = _ba(hd)
            m = _mid(hd)
            pos = positions.get(HYD, 0)
            if m is not None:
                dev = m - ANCHOR
                legs = []
                if dev <= -BAND_IN and ask is not None:
                    # price below band: BUY aggressively
                    av = -hd.sell_orders[ask]
                    sz = _cb(pos, CAP_H, 0, min(av, ACC_SIZE))
                    if sz > 0: legs.append(Order(HYD, ask, sz))
                elif dev >= BAND_IN and bid is not None:
                    # price above band: SELL aggressively
                    av = hd.buy_orders[bid]
                    sz = _cs(pos, CAP_H, 0, min(av, ACC_SIZE))
                    if sz > 0: legs.append(Order(HYD, bid, -sz))
                elif abs(dev) <= BAND_OUT:
                    # flatten when back at anchor
                    if pos > 0 and bid is not None:
                        av = hd.buy_orders[bid]
                        sz = _cs(pos, CAP_H, 0, min(av, min(pos, FLATTEN_SIZE)))
                        if sz > 0: legs.append(Order(HYD, bid, -sz))
                    elif pos < 0 and ask is not None:
                        av = -hd.sell_orders[ask]
                        sz = _cb(pos, CAP_H, 0, min(av, min(-pos, FLATTEN_SIZE)))
                        if sz > 0: legs.append(Order(HYD, ask, sz))
                if legs: out[HYD] = legs

        # VFE baseline MM
        vd = depths.get(VFE)
        if vd is not None:
            m = _micro(vd)
            if m is not None:
                fs[VFE] = _ew(fs.get(VFE), m, A_VFE)
            if VFE in fs:
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
                bsz = _cb(pos, CAP_V, b, max(0, int(round(V_SIZE * max(0.0, 1 - 1.5 * inv)))))
                ssz = _cs(pos, CAP_V, s, max(0, int(round(V_SIZE * max(0.0, 1 + 1.5 * inv)))))
                if bsz > 0 and (ask is None or bp < ask): legs.append(Order(VFE, bp, bsz))
                if ssz > 0 and (bid is None or sp > bid): legs.append(Order(VFE, sp, -ssz))
                if legs: out[VFE] = legs

        # Voucher identity only (no accumulation after H3 failure)
        ref = fs.get(VFE)
        if ref is None and vd is not None: ref = _mid(vd)
        for sym in depths:
            if sym in (HYD, VFE): continue
            k = _strike(sym)
            if k is None or not (4000 <= k <= 6500): continue
            d_ = depths.get(sym)
            if d_ is None or ref is None: continue
            bid = _bb(d_); ask = _ba(d_)
            pos = positions.get(sym, 0)
            intr = max(ref - k, 0.0)
            legs = []
            if ask is not None and ask + 1 < intr:
                av = -d_.sell_orders[ask]
                sz = _cb(pos, CAP_VOU, 0, min(av, CAP_VOU))
                if sz > 0: legs.append(Order(sym, ask, sz))
            if bid is not None and bid - 1 > ref:
                av = d_.buy_orders[bid]
                sz = _cs(pos, CAP_VOU, 0, min(av, CAP_VOU))
                if sz > 0: legs.append(Order(sym, bid, -sz))
            if legs: out[sym] = legs

        return out, 0, json.dumps({"fs": {k: round(v, 4) for k, v in fs.items()}})
    def bid(self): return 20
