"""R8 Extreme selectivity: only trade HYDROGEL when |imb|>0.85 AND spread>=12. Size 150.
No MM. Pure rare-event taker."""
import json, math
from datamodel import Order, OrderDepth, TradingState
HYD = "HYDROGEL_PACK"; CAP = 200; SIZE = 150; IMB_TRIG = 0.85; SPR_TRIG = 12
def _bb(d): return max(d.buy_orders) if d.buy_orders else None
def _ba(d): return min(d.sell_orders) if d.sell_orders else None
def _imb(d):
    b, a = _bb(d), _ba(d)
    if b is None or a is None: return 0.0
    bv = d.buy_orders[b]; av = -d.sell_orders[a]
    t = bv + av
    return 0.0 if t <= 0 else (bv - av) / t
def _cb(p, c, a, w): return max(0, min(w, c - (p + a)))
def _cs(p, c, a, w): return max(0, min(w, c + (p - a)))
class Trader:
    def run(self, state):
        out = {}
        pos = (state.position or {}).get(HYD, 0)
        d = (state.order_depths or {}).get(HYD)
        if d is None: return out, 0, "{}"
        bid = _bb(d); ask = _ba(d)
        if bid is None or ask is None: return out, 0, "{}"
        imb = _imb(d)
        spread = ask - bid
        legs = []
        if abs(imb) >= IMB_TRIG and spread >= SPR_TRIG:
            if imb > 0:
                av = -d.sell_orders[ask]
                sz = _cb(pos, CAP, 0, min(av, SIZE))
                if sz > 0: legs.append(Order(HYD, ask, sz))
            else:
                av = d.buy_orders[bid]
                sz = _cs(pos, CAP, 0, min(av, SIZE))
                if sz > 0: legs.append(Order(HYD, bid, -sz))
        # flatten stale positions
        if abs(pos) > 100:
            if pos > 0: legs.append(Order(HYD, bid + 1, -min(pos, 30)))
            elif pos < 0: legs.append(Order(HYD, ask - 1, min(-pos, 30)))
        if legs: out[HYD] = legs
        return out, 0, "{}"
    def bid(self): return 20
