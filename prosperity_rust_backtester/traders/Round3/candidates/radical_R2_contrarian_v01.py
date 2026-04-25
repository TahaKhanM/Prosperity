"""R2 Contrarian: 3-tick reversion. If price moved +6+ last 3 ticks, SELL (expect reversion).
Size 80. Opposite direction of R1."""
import json, math
from datamodel import Order, OrderDepth, TradingState
HYD = "HYDROGEL_PACK"; CAP = 200; SIZE = 80; TRIG = 6
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
        try: prior = json.loads(state.traderData) if state.traderData else {}
        except: prior = {}
        hist = prior.get("h", [])
        pos = (state.position or {}).get(HYD, 0)
        d = (state.order_depths or {}).get(HYD)
        if d is None: return out, 0, json.dumps({"h": hist})
        m = _mid(d)
        if m is not None:
            hist.append(round(m, 2))
            if len(hist) > 4: hist = hist[-4:]
        if len(hist) >= 4:
            mom = hist[-1] - hist[-4]
            bid = _bb(d); ask = _ba(d)
            legs = []
            # CONTRARIAN: sell on rally, buy on drop
            if mom >= TRIG and bid is not None:
                av = d.buy_orders[bid]
                sz = _cs(pos, CAP, 0, min(av, SIZE))
                if sz > 0: legs.append(Order(HYD, bid, -sz))
            elif mom <= -TRIG and ask is not None:
                av = -d.sell_orders[ask]
                sz = _cb(pos, CAP, 0, min(av, SIZE))
                if sz > 0: legs.append(Order(HYD, ask, sz))
            if abs(pos) > 150:
                if pos > 0 and ask is not None: legs.append(Order(HYD, ask - 1, -min(pos, 40)))
                elif pos < 0 and bid is not None: legs.append(Order(HYD, bid + 1, min(-pos, 40)))
            if legs: out[HYD] = legs
        return out, 0, json.dumps({"h": hist})
    def bid(self): return 20
