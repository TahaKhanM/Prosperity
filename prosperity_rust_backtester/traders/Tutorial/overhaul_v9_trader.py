"""v9: v8 base + stronger imbalance (0.8) + pen 0.045 for D-1 boost."""
import json
from datamodel import Order, OrderDepth, TradingState
from typing import Dict, List, Optional, Tuple

LIMITS = {"EMERALDS": 80, "TOMATOES": 80}

EMR_FAIR = 10000
EMR_TAKE_EDGE = 2
EMR_OFFSETS = (7, 6, 5)
EMR_SIZES = (25, 20, 20)

TOM_FAST_ALPHA = 2.0 / 6.0
TOM_SLOW_ALPHA = 2.0 / 21.0
TOM_MICRO_W = 0.4
TOM_FAST_W = 0.75
TOM_INV_PENALTY = 0.045
TOM_RET1_W = -0.4
TOM_IMBAL_W = 0.8
TOM_TAKE_EDGE = 1.0
TOM_SOFT_CAP = 40
TOM_CAP_EXTRA = 2.5
TOM_MIN_EDGE = 0.5
TOM_PASSIVE = [(1, 12), (2, 7)]

def best_bid(od): return max(od.buy_orders) if od.buy_orders else None
def best_ask(od): return min(od.sell_orders) if od.sell_orders else None
def mid(od):
    bb, ba = best_bid(od), best_ask(od)
    return (bb + ba) / 2.0 if bb is not None and ba is not None else None
def microprice(od):
    bb, ba = best_bid(od), best_ask(od)
    if bb is None or ba is None: return None
    bv, av = od.buy_orders[bb], -od.sell_orders[ba]
    return (bb * av + ba * bv) / (bv + av) if bv + av > 0 else (bb + ba) / 2.0
def book_imbalance(od):
    total_bid = sum(od.buy_orders.values()) if od.buy_orders else 0
    total_ask = sum(-v for v in od.sell_orders.values()) if od.sell_orders else 0
    total = total_bid + total_ask
    return (total_bid - total_ask) / total if total > 0 else 0.0
def add_buy(orders, sym, price, qty, budget):
    fill = min(qty, budget)
    if fill > 0: orders.append(Order(sym, int(price), fill)); budget -= fill
    return budget
def add_sell(orders, sym, price, qty, budget):
    fill = min(qty, budget)
    if fill > 0: orders.append(Order(sym, int(price), -fill)); budget -= fill
    return budget

def trade_emeralds(od, pos):
    orders = []
    bb_left = LIMITS["EMERALDS"] - pos
    sb_left = LIMITS["EMERALDS"] + pos
    for ap in sorted(od.sell_orders):
        if ap > EMR_FAIR - EMR_TAKE_EDGE: break
        bb_left = add_buy(orders, "EMERALDS", ap, -od.sell_orders[ap], bb_left)
    for bp in sorted(od.buy_orders, reverse=True):
        if bp < EMR_FAIR + EMR_TAKE_EDGE: break
        sb_left = add_sell(orders, "EMERALDS", bp, od.buy_orders[bp], sb_left)
    for off, sz in zip(EMR_OFFSETS, EMR_SIZES):
        bb_left = add_buy(orders, "EMERALDS", EMR_FAIR - off, sz, bb_left)
    for off, sz in zip(EMR_OFFSETS, EMR_SIZES):
        sb_left = add_sell(orders, "EMERALDS", EMR_FAIR + off, sz, sb_left)
    return orders

def trade_tomatoes(od, pos, fast_ema, slow_ema, prev_mid):
    m = mid(od)
    mp = microprice(od)
    imbal = book_imbalance(od)
    if m is not None:
        raw = m if mp is None else (1 - TOM_MICRO_W) * m + TOM_MICRO_W * mp
    else:
        raw = fast_ema if fast_ema is not None else 5000.0
    if fast_ema is None:
        nf, ns = raw, raw
    else:
        nf = TOM_FAST_ALPHA * raw + (1 - TOM_FAST_ALPHA) * fast_ema
        ns = TOM_SLOW_ALPHA * raw + (1 - TOM_SLOW_ALPHA) * slow_ema
    ret1 = 0.0
    if m is not None and prev_mid is not None:
        ret1 = m - prev_mid
    fair = (TOM_FAST_W * nf + (1 - TOM_FAST_W) * ns
            + TOM_RET1_W * ret1 + TOM_IMBAL_W * imbal
            - TOM_INV_PENALTY * pos)
    orders = []
    limit = LIMITS["TOMATOES"]
    bb_left = limit - pos
    sb_left = limit + pos
    for ap in sorted(od.sell_orders):
        edge = fair - ap
        if edge < TOM_TAKE_EDGE: break
        if pos >= TOM_SOFT_CAP and edge < TOM_TAKE_EDGE + TOM_CAP_EXTRA: continue
        bb_left = add_buy(orders, "TOMATOES", ap, -od.sell_orders[ap], bb_left)
    for bp in sorted(od.buy_orders, reverse=True):
        edge = bp - fair
        if edge < TOM_TAKE_EDGE: break
        if pos <= -TOM_SOFT_CAP and edge < TOM_TAKE_EDGE + TOM_CAP_EXTRA: continue
        sb_left = add_sell(orders, "TOMATOES", bp, od.buy_orders[bp], sb_left)
    bb = best_bid(od)
    ba = best_ask(od)
    if bb is not None and ba is not None and bb < ba:
        for off, base_sz in TOM_PASSIVE:
            p_bid = bb + off
            p_ask = ba - off
            if pos > 0:
                buy_sz = max(0, round(base_sz * max(0.0, (TOM_SOFT_CAP - pos) / TOM_SOFT_CAP)))
            else:
                buy_sz = base_sz
            if pos < 0:
                sell_sz = max(0, round(base_sz * max(0.0, (TOM_SOFT_CAP + pos) / TOM_SOFT_CAP)))
            else:
                sell_sz = base_sz
            if p_bid < ba and fair - p_bid >= TOM_MIN_EDGE and buy_sz > 0:
                bb_left = add_buy(orders, "TOMATOES", p_bid, buy_sz, bb_left)
            if p_ask > bb and p_ask - fair >= TOM_MIN_EDGE and sell_sz > 0:
                sb_left = add_sell(orders, "TOMATOES", p_ask, sell_sz, sb_left)
    new_mid = m if m is not None else prev_mid
    return orders, nf, ns, new_mid

class Trader:
    def bid(self): return 0
    def run(self, state):
        data = {}
        if state.traderData:
            try: data = json.loads(state.traderData)
            except: pass
        fe = data.get("fe")
        se = data.get("se")
        pm = data.get("pm")
        if fe is not None: fe = float(fe)
        if se is not None: se = float(se)
        if pm is not None: pm = float(pm)
        result = {}
        if "EMERALDS" in state.order_depths:
            result["EMERALDS"] = trade_emeralds(state.order_depths["EMERALDS"], state.position.get("EMERALDS", 0))
        if "TOMATOES" in state.order_depths:
            orders, fe, se, pm = trade_tomatoes(state.order_depths["TOMATOES"], state.position.get("TOMATOES", 0), fe, se, pm)
            result["TOMATOES"] = orders
        out = {}
        if fe is not None: out["fe"] = round(fe, 2)
        if se is not None: out["se"] = round(se, 2)
        if pm is not None: out["pm"] = round(pm, 2)
        return result, 0, json.dumps(out) if out else ""
