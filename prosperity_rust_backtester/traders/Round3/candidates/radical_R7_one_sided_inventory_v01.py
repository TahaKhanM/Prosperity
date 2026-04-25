"""R7 One-sided long-bias: build long HYDROGEL when mid < 10000, hold.
Systematic long-bias. Size 30 per tick when mid<9990. Exit when mid>10010."""
import json, math
from datamodel import Order, OrderDepth, TradingState
HYD = "HYDROGEL_PACK"; CAP = 200
def _bb(d): return max(d.buy_orders) if d.buy_orders else None
def _ba(d): return min(d.sell_orders) if d.sell_orders else None
def _mid(d):
    b, a = _bb(d), _ba(d)
    return None if b is None or a is None else (b + a) / 2.0
def _cb(p, c, a, w): return max(0, min(w, c - (p + a)))
def _cs(p, c, a, w): return max(0, min(w, c + (p - a)))
class Trader:
    def run(self, state):
        out = {}
        pos = (state.position or {}).get(HYD, 0)
        d = (state.order_depths or {}).get(HYD)
        if d is None: return out, 0, "{}"
        bid = _bb(d); ask = _ba(d)
        m = _mid(d)
        if m is None: return out, 0, "{}"
        legs = []
        if m < 9990 and ask is not None:
            av = -d.sell_orders[ask]
            sz = _cb(pos, CAP, 0, min(av, 30))
            if sz > 0: legs.append(Order(HYD, ask, sz))
        elif m > 10010 and bid is not None and pos > 0:
            av = d.buy_orders[bid]
            sz = _cs(pos, CAP, 0, min(av, 30, pos))
            if sz > 0: legs.append(Order(HYD, bid, -sz))
        if legs: out[HYD] = legs
        return out, 0, "{}"
    def bid(self): return 20
