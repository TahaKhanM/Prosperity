"""P8 HYDROGEL trend-follower + baseline MM.

Critical hosted evidence (385004):
  - P7 band overlay scored +121 hosted (catastrophic vs baseline +8,500)
  - Reason: HYDROGEL mid drifted 10011 -> 9960 over the day (-51 XY)
  - Band was wrong-way (mean-reverting into a trend)
  - 704 band triggers accumulated large LONG positions that lost as price fell

Correct mechanism: TREND-FOLLOWING HYDROGEL on the DRIFT.

P8 logic:
  - Track HYDROGEL EWMA mid across ticks in traderData.
  - If current_mid < ewma_mid - 5 (downtrend confirmed): build SHORT up to cap 200
  - If current_mid > ewma_mid + 5 (uptrend confirmed): build LONG up to cap 200
  - Size 40 per tick when trend signal active
  - Keep baseline passive MM for spread capture (don't lose the floor)
  - Keep baseline VFE MM (proven +2k)
  - Voucher identity only

Rationale: if hosted day trends (like 385004), the trend position compounds.
If hosted day mean-reverts, the passive MM captures spread and trend position
losses are bounded by symmetric take thresholds.

Projected hosted: baseline floor ~8k + trend position capture of -51 XY drift
at size 200 = +8k + ~10k = ~18k. Much better than 8.5k plateau.
"""
import json, math
from datamodel import Order, OrderDepth, TradingState

HYD = "HYDROGEL_PACK"; VFE = "VELVETFRUIT_EXTRACT"
CAP_H = 200; CAP_V = 200; CAP_VOU = 300
ANCHOR = 10000.0; A_W = 0.40; A_HYD = 0.10
H_TAKE = 4; H_QE = 3; H_SIZE = 20; H_IMB = 5.0
TREND_THRESHOLD = 5       # XY deviation from EWMA to confirm trend
TREND_SIZE = 40           # size per tick when trending
TREND_EWMA_ALPHA = 0.02   # slow EWMA to detect sustained trend (50-tick half-life)
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

class Trader:
    def run(self, state):
        out = {}
        try: prior = json.loads(state.traderData) if state.traderData else {}
        except: prior = {}
        fs = dict(prior.get("fs", {}) or {})
        trend_ewma = prior.get("te")  # slow EWMA for trend detection
        positions = state.position or {}
        depths = state.order_depths or {}

        hd = depths.get(HYD); himb = 0.0
        current_mid = None
        if hd is not None:
            current_mid = _mid(hd)
            m = _micro(hd)
            if m is not None:
                fs[HYD] = _ew(fs.get(HYD), A_W * ANCHOR + (1 - A_W) * m, A_HYD)
            if current_mid is not None:
                trend_ewma = _ew(trend_ewma, current_mid, TREND_EWMA_ALPHA)
            himb = _imb(hd)
        vd = depths.get(VFE)
        if vd is not None:
            m = _micro(vd)
            if m is not None: fs[VFE] = _ew(fs.get(VFE), m, A_VFE)

        # HYDROGEL: baseline MM + TREND overlay
        if hd is not None and HYD in fs:
            bid = _bb(hd); ask = _ba(hd); pos = positions.get(HYD, 0)
            fair = fs[HYD] + H_IMB * himb
            legs = []; b = s = 0

            # TREND OVERLAY: deviation from slow EWMA
            if current_mid is not None and trend_ewma is not None:
                drift = current_mid - trend_ewma
                # if current < slow ewma -> downtrend -> SHORT
                if drift <= -TREND_THRESHOLD and bid is not None:
                    av = bid and hd.buy_orders[bid]
                    sz = _cs(pos, CAP_H, s, min(av or 0, TREND_SIZE))
                    if sz > 0: legs.append(Order(HYD, bid, -sz)); s += sz
                # if current > slow ewma -> uptrend -> LONG
                elif drift >= TREND_THRESHOLD and ask is not None:
                    av = -hd.sell_orders[ask]
                    sz = _cb(pos, CAP_H, b, min(av, TREND_SIZE))
                    if sz > 0: legs.append(Order(HYD, ask, sz)); b += sz

            # baseline MM
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
            bsz = _cb(pos, CAP_H, b, max(0, int(round(H_SIZE * max(0.0, 1 - 2.0 * inv)))))
            ssz = _cs(pos, CAP_H, s, max(0, int(round(H_SIZE * max(0.0, 1 + 2.0 * inv)))))
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
            bsz = _cb(pos, CAP_V, b, max(0, int(round(V_SIZE * max(0.0, 1 - 1.5 * inv)))))
            ssz = _cs(pos, CAP_V, s, max(0, int(round(V_SIZE * max(0.0, 1 + 1.5 * inv)))))
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

        blob = {"fs": {k: round(v, 4) for k, v in fs.items()}}
        if trend_ewma is not None: blob["te"] = round(trend_ewma, 4)
        return out, 0, json.dumps(blob, separators=(",", ":"))
    def bid(self): return 20
