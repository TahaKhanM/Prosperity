"""
Prosperity 4 — EMERALDS & TOMATOES
V3: Optimized from V1/V2 fill-level evidence.

Key learnings applied:
  EMERALDS: Most PnL comes from ±4 to ±6 levels, not extremes. Don't take at fair (0 edge).
  TOMATOES: ±4 spread got 2.5x more fills than ±6, overwhelming the edge difference.
            Microprice fair is strictly better than simple mid.
"""

import json
import math
from datamodel import Order, OrderDepth, TradingState
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════════

LIMITS = {"EMERALDS": 80, "TOMATOES": 80}
EM_FAIR = 10_000
TOM_EMA_SPAN = 5
TOM_MICRO_WT = 0.6   # weight on microprice vs simple mid

# ═══════════════════════════════════════════════════════════════════════
# Order book utilities
# ═══════════════════════════════════════════════════════════════════════

def best_bid(od: OrderDepth) -> Optional[int]:
    return max(od.buy_orders) if od.buy_orders else None

def best_ask(od: OrderDepth) -> Optional[int]:
    return min(od.sell_orders) if od.sell_orders else None

def mid(od: OrderDepth) -> Optional[float]:
    bb, ba = best_bid(od), best_ask(od)
    if bb is not None and ba is not None:
        return (bb + ba) / 2.0
    return None

def microprice(od: OrderDepth) -> Optional[float]:
    bb, ba = best_bid(od), best_ask(od)
    if bb is None or ba is None:
        return None
    bv = od.buy_orders[bb]
    av = -od.sell_orders[ba]
    total = bv + av
    if total == 0:
        return (bb + ba) / 2.0
    return (bb * av + ba * bv) / total

# ═══════════════════════════════════════════════════════════════════════
# Position-safe order builder
# ═══════════════════════════════════════════════════════════════════════

def build_orders(
    symbol: str,
    position: int,
    limit: int,
    take_buys: List[Tuple[int, int]],
    take_sells: List[Tuple[int, int]],
    passive_buys: List[Tuple[int, int]],
    passive_sells: List[Tuple[int, int]],
) -> List[Order]:
    buy_budget = limit - position
    sell_budget = limit + position
    orders = []  # type: List[Order]

    for price, qty in take_buys:
        fill = min(qty, buy_budget)
        if fill > 0:
            orders.append(Order(symbol, price, fill))
            buy_budget -= fill

    for price, qty in take_sells:
        fill = min(qty, sell_budget)
        if fill > 0:
            orders.append(Order(symbol, price, -fill))
            sell_budget -= fill

    for price, qty in passive_buys:
        fill = min(qty, buy_budget)
        if fill > 0:
            orders.append(Order(symbol, price, fill))
            buy_budget -= fill

    for price, qty in passive_sells:
        fill = min(qty, sell_budget)
        if fill > 0:
            orders.append(Order(symbol, price, -fill))
            sell_budget -= fill

    return orders

# ═══════════════════════════════════════════════════════════════════════
# EMERALDS
#
# V1 fill analysis (Day -2, PnL=3104):
#   Buy fills: 9993(42), 9994(300), 9995(570), 9996(428), 9997(270),
#              9998(112), 9999(95), 10000(0)  → total buy edge 1817
#   Sell fills: 10001(133), 10002(120), 10003(264), 10004(356),
#               10005(345), 10006(24), 10007(63) → total sell edge 1287
#
# V2 (wide ±7 only, took at 10000): EMERALDS PnL rose to 4030 but
#   most fills were 0-edge takes at 10000. Passive fills barely happened.
#
# V3 approach: multi-level quoting, no 0-edge takes, budget priority to
#   levels with proven fill rates and good edge.
# ═══════════════════════════════════════════════════════════════════════

def trade_emeralds(od: OrderDepth, position: int) -> List[Order]:
    fair = EM_FAIR
    limit = LIMITS["EMERALDS"]

    take_buys = []   # type: List[Tuple[int, int]]
    take_sells = []  # type: List[Tuple[int, int]]

    # Take only when edge >= 2 (price <= 9998 to buy, >= 10002 to sell)
    for ap in sorted(od.sell_orders.keys()):
        if ap > fair - 2:
            break
        vol = -od.sell_orders[ap]
        take_buys.append((ap, vol))

    for bp in sorted(od.buy_orders.keys(), reverse=True):
        if bp < fair + 2:
            break
        vol = od.buy_orders[bp]
        take_sells.append((bp, vol))

    # Inventory skew: gentle, just enough to flatten over time
    skew = round(position * 0.06)

    # Multi-level passive quotes, budget-prioritized by edge
    # Wider levels (more edge) get budget first
    passive_buys = [
        (fair - 7 - skew, 12),   # 9993: edge=7
        (fair - 6 - skew, 12),   # 9994: edge=6
        (fair - 5 - skew, 15),   # 9995: edge=5 (sweet spot from V1 data)
        (fair - 4 - skew, 12),   # 9996: edge=4
        (fair - 3 - skew, 10),   # 9997: edge=3
    ]  # type: List[Tuple[int, int]]

    passive_sells = [
        (fair + 7 - skew, 12),   # 10007: edge=7
        (fair + 6 - skew, 12),   # 10006: edge=6
        (fair + 5 - skew, 15),   # 10005: edge=5
        (fair + 4 - skew, 12),   # 10004: edge=4
        (fair + 3 - skew, 10),   # 10003: edge=3
    ]  # type: List[Tuple[int, int]]

    return build_orders("EMERALDS", position, limit,
                        take_buys, take_sells, passive_buys, passive_sells)


# ═══════════════════════════════════════════════════════════════════════
# TOMATOES
#
# V1 (spread=±4, rolling avg fair): 5152 PnL, 1136 units, edge=9.12
# V2 (spread=±6, microprice fair): 2831 PnL, 454 units, edge=12.45
# V1 won because 2.5x more fills > 1.4x edge improvement.
#
# V3: Use microprice fair (better estimator) but with V1-style tight spread.
#   Primary: ±4 from fair, secondary: ±6 wider capture
# ═══════════════════════════════════════════════════════════════════════

def trade_tomatoes(od: OrderDepth, position: int, ema_fair: Optional[float]) -> Tuple[List[Order], float]:
    limit = LIMITS["TOMATOES"]

    # Fair value: microprice weighted with simple mid
    mp = microprice(od)
    sm = mid(od)
    if mp is not None and sm is not None:
        raw_fair = mp * TOM_MICRO_WT + sm * (1 - TOM_MICRO_WT)
    elif mp is not None:
        raw_fair = mp
    elif sm is not None:
        raw_fair = sm
    else:
        raw_fair = ema_fair if ema_fair is not None else 5000.0

    # Light EMA smoothing
    alpha = 2.0 / (TOM_EMA_SPAN + 1)
    if ema_fair is not None:
        fair = alpha * raw_fair + (1 - alpha) * ema_fair
    else:
        fair = raw_fair

    take_buys = []   # type: List[Tuple[int, int]]
    take_sells = []  # type: List[Tuple[int, int]]

    # Only take extreme mispricings (half-spread or more from fair)
    for ap in sorted(od.sell_orders.keys()):
        if ap > fair - 7:
            break
        vol = -od.sell_orders[ap]
        take_buys.append((ap, vol))

    for bp in sorted(od.buy_orders.keys(), reverse=True):
        if bp < fair + 7:
            break
        vol = od.buy_orders[bp]
        take_sells.append((bp, vol))

    # Inventory skew
    skew = round(position * 0.10)
    fair_floor = math.floor(fair)
    fair_ceil = math.ceil(fair)

    # Primary ±4, secondary ±6 for wider capture
    passive_buys = [
        (fair_floor - 4 - skew, 20),
        (fair_floor - 6 - skew, 15),
    ]  # type: List[Tuple[int, int]]

    passive_sells = [
        (fair_ceil + 4 - skew, 20),
        (fair_ceil + 6 - skew, 15),
    ]  # type: List[Tuple[int, int]]

    orders = build_orders("TOMATOES", position, limit,
                          take_buys, take_sells, passive_buys, passive_sells)
    return orders, fair


# ═══════════════════════════════════════════════════════════════════════
# Trader
# ═══════════════════════════════════════════════════════════════════════

class Trader:
    def bid(self):
        return 0

    def run(self, state: TradingState) -> Tuple[Dict[str, List[Order]], int, str]:
        data = {}
        if state.traderData:
            try:
                data = json.loads(state.traderData)
            except Exception:
                data = {}

        tom_fair = data.get("tf")  # type: Optional[float]
        result = {}  # type: Dict[str, List[Order]]

        if "EMERALDS" in state.order_depths:
            pos = state.position.get("EMERALDS", 0)
            result["EMERALDS"] = trade_emeralds(state.order_depths["EMERALDS"], pos)

        if "TOMATOES" in state.order_depths:
            pos = state.position.get("TOMATOES", 0)
            orders, tom_fair = trade_tomatoes(state.order_depths["TOMATOES"], pos, tom_fair)
            result["TOMATOES"] = orders

        out = {}  # type: Dict[str, float]
        if tom_fair is not None:
            out["tf"] = round(tom_fair, 2)

        return result, 0, json.dumps(out)
