"""Family F1 — max-aggression pure signal-driven trader.

Radical changes vs current model:
  - HYDROGEL passive MM completely removed. Only aggressive signal takes.
  - VFE: signal take + MM. Lower imbalance threshold.
  - Vouchers: inside-book passive at size 100 on all 10 strikes + identity arbs.
  - No anchor. No regime guard. No vol gate. Pure signal + capacity.

Hypothesis: 383147 showed signal-take added trades but HYDROGEL PnL regressed
(6072 -> 5863). Maybe passive MM was actually useful and signal-take alone
is not the edge. Test: STRIP passive MM entirely and only trade on strong
imbalance, prove the signal-only approach either works or fails. If it fails
badly, we confirm passive MM matters and can drop this family.
"""

import json
import math
from typing import Dict, List, Optional, Tuple
from datamodel import Order, OrderDepth, TradingState

HYDROGEL = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"
CAP_HYDROGEL = 200
CAP_VFE = 200
CAP_VOUCHER = 300

# aggressive signal params
HYD_SIGNAL_THRESHOLD = 0.40     # lowered from 0.55
HYD_SIGNAL_SIZE = 100           # up from 40
VFE_SIGNAL_THRESHOLD = 0.35
VFE_SIGNAL_SIZE = 80
VFE_TAKE_EDGE = 1
VFE_QUOTE_SIZE = 40
VOUCHER_PASSIVE_SIZE = 100      # massive voucher passive
TV_A = 55.0
TV_W = 400.0
TV_POW = 1.8
TV_OTM_FLOOR = 0.5
VOUCHER_MKT_W = 0.7
VOUCHER_MDL_W = 0.3


def _best_bid(d): return max(d.buy_orders) if d.buy_orders else None
def _best_ask(d): return min(d.sell_orders) if d.sell_orders else None
def _mid(d):
    b, a = _best_bid(d), _best_ask(d)
    return None if b is None or a is None else (b + a) / 2.0
def _micro(d):
    b = _best_bid(d); a = _best_ask(d)
    if b is None or a is None: return None
    bv = d.buy_orders[b]; av = -d.sell_orders[a]
    t = bv + av
    return (b + a) / 2.0 if t <= 0 else (a * bv + b * av) / t
def _imb(d):
    b = _best_bid(d); a = _best_ask(d)
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
def _clip_b(p, cap, ad, w): return max(0, min(w, cap - (p + ad)))
def _clip_s(p, cap, ad, w): return max(0, min(w, cap + (p - ad)))

def _tv(S, K):
    d = abs(S - K)
    if d >= TV_W: return TV_OTM_FLOOR
    x = 1.0 - d / TV_W
    return max(TV_OTM_FLOOR, TV_A * (x ** TV_POW)) if x > 0 else TV_OTM_FLOOR

def _vfair(S, K, vmid):
    intr = max(S - K, 0.0)
    model = intr + _tv(S, K)
    model = max(0.0, min(model, S))
    if vmid is None: return model
    return max(intr, min(VOUCHER_MKT_W * vmid + VOUCHER_MDL_W * model, S))


class Trader:
    def run(self, state: TradingState):
        out = {}
        try: prior = json.loads(state.traderData) if state.traderData else {}
        except: prior = {}
        positions = state.position or {}
        depths = state.order_depths or {}

        # HYDROGEL: pure signal taker, no passive MM
        hd = depths.get(HYDROGEL)
        if hd is not None:
            imb = _imb(hd)
            pos = positions.get(HYDROGEL, 0)
            pos_ratio = pos / CAP_HYDROGEL
            bid = _best_bid(hd); ask = _best_ask(hd)
            legs = []
            if imb > HYD_SIGNAL_THRESHOLD and pos_ratio < 0.8 and ask is not None:
                avail = -hd.sell_orders[ask]
                sz = _clip_b(pos, CAP_HYDROGEL, 0, min(avail, HYD_SIGNAL_SIZE))
                if sz > 0: legs.append(Order(HYDROGEL, ask, sz))
            elif imb < -HYD_SIGNAL_THRESHOLD and pos_ratio > -0.8 and bid is not None:
                avail = hd.buy_orders[bid]
                sz = _clip_s(pos, CAP_HYDROGEL, 0, min(avail, HYD_SIGNAL_SIZE))
                if sz > 0: legs.append(Order(HYDROGEL, bid, -sz))
            # inventory-flatten passive quote only when at extreme position
            if abs(pos_ratio) > 0.6:
                # flatten toward zero
                if pos > 0 and ask is not None:
                    legs.append(Order(HYDROGEL, ask - 1, -min(pos, 20)))
                elif pos < 0 and bid is not None:
                    legs.append(Order(HYDROGEL, bid + 1, min(-pos, 20)))
            if legs: out[HYDROGEL] = legs

        # VFE: signal take + tight MM
        vd = depths.get(VFE)
        if vd is not None:
            imb = _imb(vd)
            m = _micro(vd)
            pos = positions.get(VFE, 0)
            bid = _best_bid(vd); ask = _best_ask(vd)
            legs = []
            bought = sold = 0
            # signal take
            if imb > VFE_SIGNAL_THRESHOLD and pos < CAP_VFE * 0.8 and ask is not None:
                avail = -vd.sell_orders[ask]
                sz = _clip_b(pos, CAP_VFE, bought, min(avail, VFE_SIGNAL_SIZE))
                if sz > 0:
                    legs.append(Order(VFE, ask, sz)); bought += sz
            elif imb < -VFE_SIGNAL_THRESHOLD and pos > -CAP_VFE * 0.8 and bid is not None:
                avail = vd.buy_orders[bid]
                sz = _clip_s(pos, CAP_VFE, sold, min(avail, VFE_SIGNAL_SIZE))
                if sz > 0:
                    legs.append(Order(VFE, bid, -sz)); sold += sz
            # passive MM around microprice
            if m is not None:
                inv = (pos + bought - sold) / CAP_VFE
                buy_px = int(math.floor(m - 1))
                sell_px = int(math.ceil(m + 1))
                if bid is not None: buy_px = min(buy_px, bid + 1)
                if ask is not None:
                    buy_px = min(buy_px, ask - 1)
                    sell_px = max(sell_px, ask - 1)
                if bid is not None: sell_px = max(sell_px, bid + 1)
                bsz = _clip_b(pos, CAP_VFE, bought, max(0, int(round(VFE_QUOTE_SIZE * max(0.0, 1 - 1.5 * inv)))))
                ssz = _clip_s(pos, CAP_VFE, sold, max(0, int(round(VFE_QUOTE_SIZE * max(0.0, 1 + 1.5 * inv)))))
                if bsz > 0 and (ask is None or buy_px < ask):
                    legs.append(Order(VFE, buy_px, bsz))
                if ssz > 0 and (bid is None or sell_px > bid):
                    legs.append(Order(VFE, sell_px, -ssz))
            if legs: out[VFE] = legs

        # VFE ref for vouchers
        vfe_mid = _mid(vd) if vd is not None else None
        ref = vfe_mid

        # Vouchers: massive passive + identity
        entries = []
        for sym in depths:
            if sym in (HYDROGEL, VFE): continue
            if not _is_vev(sym): continue
            k = _strike(sym)
            if k is None: continue
            entries.append((k, sym))
        entries.sort()

        for strike, sym in entries:
            vd_ = depths.get(sym)
            if vd_ is None or ref is None: continue
            bid_ = _best_bid(vd_); ask_ = _best_ask(vd_)
            pos = positions.get(sym, 0)
            vmid = _mid(vd_)
            intr = max(ref - strike, 0.0)
            fair = _vfair(ref, strike, vmid)
            legs = []
            bought = sold = 0

            # identity: buy below intrinsic
            if ask_ is not None and ask_ + 1 < intr:
                avail = -vd_.sell_orders[ask_]
                sz = _clip_b(pos, CAP_VOUCHER, bought, min(avail, CAP_VOUCHER))
                if sz > 0:
                    legs.append(Order(sym, ask_, sz)); bought += sz
            # identity: sell above upper bound
            if bid_ is not None and bid_ - 1 > ref:
                avail = vd_.buy_orders[bid_]
                sz = _clip_s(pos, CAP_VOUCHER, sold, min(avail, CAP_VOUCHER))
                if sz > 0:
                    legs.append(Order(sym, bid_, -sz)); sold += sz

            # aggressive passive quoting INSIDE book
            if bid_ is not None and ask_ is not None and ask_ > bid_ + 1:
                # quote at bid+1 / ask-1 if fair supports
                bp = bid_ + 1
                sp = ask_ - 1
                if bp + 1 <= fair:
                    bsz_raw = VOUCHER_PASSIVE_SIZE
                    bsz = _clip_b(pos, CAP_VOUCHER, bought, bsz_raw)
                    if bsz > 0: legs.append(Order(sym, bp, bsz))
                if sp >= fair + 1 and sp > bp:
                    ssz_raw = VOUCHER_PASSIVE_SIZE
                    ssz = _clip_s(pos, CAP_VOUCHER, sold, ssz_raw)
                    if ssz > 0: legs.append(Order(sym, sp, -ssz))

            if legs: out[sym] = legs

        td = "{}"
        return out, 0, td

    def bid(self) -> int:
        return 20
