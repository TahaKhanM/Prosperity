"""R9 product-isolation: VFE only. No HYDROGEL, no vouchers. Aggressive VFE MM size 80 cap 200."""
import json, math
from datamodel import Order, OrderDepth, TradingState
VFE = "VELVETFRUIT_EXTRACT"; CAP = 200; SIZE = 80; A = 0.20
def _bb(d): return max(d.buy_orders) if d.buy_orders else None
def _ba(d): return min(d.sell_orders) if d.sell_orders else None
def _micro(d):
    b, a = _bb(d), _ba(d)
    if b is None or a is None: return None
    bv = d.buy_orders[b]; av = -d.sell_orders[a]
    t = bv + av
    return (b + a) / 2.0 if t <= 0 else (a * bv + b * av) / t
def _cb(p, c, a, w): return max(0, min(w, c - (p + a)))
def _cs(p, c, a, w): return max(0, min(w, c + (p - a)))
class Trader:
    def run(self, state):
        out = {}
        try: prior = json.loads(state.traderData) if state.traderData else {}
        except: prior = {}
        fair = prior.get("f")
        pos = (state.position or {}).get(VFE, 0)
        d = (state.order_depths or {}).get(VFE)
        if d is None: return out, 0, json.dumps({"f": fair})
        m = _micro(d)
        if m is not None: fair = m if fair is None else fair * (1 - A) + m * A
        if fair is None: return out, 0, "{}"
        bid = _bb(d); ask = _ba(d)
        legs = []
        b = s = 0
        if ask is not None and ask + 1 <= fair:
            av = -d.sell_orders[ask]
            sz = _cb(pos, CAP, b, min(av, CAP))
            if sz > 0: legs.append(Order(VFE, ask, sz)); b += sz
        if bid is not None and bid - 1 >= fair:
            av = d.buy_orders[bid]
            sz = _cs(pos, CAP, s, min(av, CAP))
            if sz > 0: legs.append(Order(VFE, bid, -sz)); s += sz
        inv = max(-1.0, min(1.0, (pos + b - s) / CAP))
        bp = int(math.floor(fair - 1))
        sp = int(math.ceil(fair + 1))
        if bid is not None: bp = min(bp, bid + 1)
        if ask is not None: bp = min(bp, ask - 1); sp = max(sp, ask - 1)
        if bid is not None: sp = max(sp, bid + 1)
        bsz = _cb(pos, CAP, b, max(0, int(round(SIZE * max(0.0, 1 - 1.5 * inv)))))
        ssz = _cs(pos, CAP, s, max(0, int(round(SIZE * max(0.0, 1 + 1.5 * inv)))))
        if bsz > 0 and (ask is None or bp < ask): legs.append(Order(VFE, bp, bsz))
        if ssz > 0 and (bid is None or sp > bid): legs.append(Order(VFE, sp, -ssz))
        if legs: out[VFE] = legs
        return out, 0, json.dumps({"f": round(fair, 4)})
    def bid(self): return 20
