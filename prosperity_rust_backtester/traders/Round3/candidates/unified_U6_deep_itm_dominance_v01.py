"""U6 deep-ITM dominance: voucher-only (VEV_4000 + VEV_4500) at max scale. No HYD, no VFE.
Escapes: Product-Isolation, Passive-MM Comfort traps.
Mechanism: pure deep-ITM voucher identity arbs + aggressive accumulation to cap 300 each.
No other modules to dilute."""
import json, math
from datamodel import Order, OrderDepth, TradingState

CAP = 300
ACC_STRIKES = [4000, 4500]
ACC_SLACK = 5
ACC_SIZE = 80
EXIT_SLACK = 10

def _bb(d): return max(d.buy_orders) if d.buy_orders else None
def _ba(d): return min(d.sell_orders) if d.sell_orders else None
def _mid(d):
    b, a = _bb(d), _ba(d)
    return None if b is None or a is None else (b + a) / 2.0
def _strike(s):
    if s.startswith("VEV_"):
        try: return int(s[4:])
        except: return None
    return None
def _cb(p, c, ad, w): return max(0, min(w, c - (p + ad)))
def _cs(p, c, ad, w): return max(0, min(w, c + (p - ad)))

class Trader:
    def run(self, state):
        out = {}
        positions = state.position or {}
        depths = state.order_depths or {}
        VFE = "VELVETFRUIT_EXTRACT"
        vd = depths.get(VFE)
        ref = _mid(vd) if vd is not None else None
        for sym in depths:
            k = _strike(sym)
            if k is None or k not in ACC_STRIKES: continue
            d_ = depths.get(sym)
            if d_ is None or ref is None: continue
            bid = _bb(d_); ask = _ba(d_)
            pos = positions.get(sym, 0)
            intr = max(ref - k, 0.0)
            legs = []
            # identity: buy below intrinsic
            if ask is not None and ask + 1 < intr:
                av = -d_.sell_orders[ask]
                sz = _cb(pos, CAP, 0, min(av, CAP))
                if sz > 0: legs.append(Order(sym, ask, sz))
            # accumulate when ask <= intrinsic + slack
            if ask is not None and ask <= intr + ACC_SLACK:
                av = -d_.sell_orders[ask]
                sz = _cb(pos, CAP, 0, min(av, ACC_SIZE))
                if sz > 0: legs.append(Order(sym, ask, sz))
            # exit when rich
            if bid is not None and bid >= intr + EXIT_SLACK and pos > 0:
                av = d_.buy_orders[bid]
                sz = _cs(pos, CAP, 0, min(av, min(pos, 60)))
                if sz > 0: legs.append(Order(sym, bid, -sz))
            if legs: out[sym] = legs
        return out, 0, "{}"
    def bid(self): return 20
