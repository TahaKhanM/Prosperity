import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


HYD = "HYDROGEL_PACK"
VFE = "VELVETFRUIT_EXTRACT"

LIMITS = {
    HYD: 200,
    VFE: 200,
}

# =========================
# HYDROGEL main strategy
# =========================

HYD_ANCHOR = 10000.0

# From notebook: best HYD result was anchor edge 8.
HYD_TAKE_EDGE = 8.0
HYD_QUOTE_EDGE = 8.0
HYD_SIZE = 40
HYD_SOFT_CAP = 120

# =========================
# VFE small side strategy
# =========================

VFE_EMA_ALPHA = 0.20
VFE_TAKE_EDGE = 3.0
VFE_QUOTE_EDGE = 3.0
VFE_SIZE = 20
VFE_IMB_K = 8.0
VFE_SKEW_CAP = 2.0
VFE_SOFT_CAP = 80


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def best_bid(depth: OrderDepth) -> Optional[int]:
    return max(depth.buy_orders) if depth.buy_orders else None


def best_ask(depth: OrderDepth) -> Optional[int]:
    return min(depth.sell_orders) if depth.sell_orders else None


def mid_price(depth: OrderDepth) -> Optional[float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return None
    return (bid + ask) / 2.0


def microprice(depth: OrderDepth) -> Optional[float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return None

    bid_vol = depth.buy_orders[bid]
    ask_vol = -depth.sell_orders[ask]
    total = bid_vol + ask_vol

    if total <= 0:
        return (bid + ask) / 2.0

    # More bid volume pushes microprice toward ask.
    return (ask * bid_vol + bid * ask_vol) / total


def imbalance_l1(depth: OrderDepth) -> float:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return 0.0

    bid_vol = depth.buy_orders[bid]
    ask_vol = -depth.sell_orders[ask]
    total = bid_vol + ask_vol

    if total <= 0:
        return 0.0

    return (bid_vol - ask_vol) / total


def imbalance_k2(depth: OrderDepth) -> float:
    if not depth.buy_orders or not depth.sell_orders:
        return 0.0

    bids = sorted(depth.buy_orders.items(), key=lambda x: -x[0])[:2]
    asks = sorted(depth.sell_orders.items(), key=lambda x: x[0])[:2]

    bid_vol = sum(v for _, v in bids)
    ask_vol = sum(-v for _, v in asks)
    total = bid_vol + ask_vol

    if total <= 0:
        return 0.0

    return (bid_vol - ask_vol) / total


def add_buy(
    orders: List[Order],
    product: str,
    price: int,
    quantity: int,
    budget: int,
) -> int:
    size = min(quantity, budget)
    if size > 0:
        orders.append(Order(product, int(price), int(size)))
        budget -= size
    return budget


def add_sell(
    orders: List[Order],
    product: str,
    price: int,
    quantity: int,
    budget: int,
) -> int:
    size = min(quantity, budget)
    if size > 0:
        orders.append(Order(product, int(price), -int(size)))
        budget -= size
    return budget


def ema(prev: Optional[float], value: float, alpha: float) -> float:
    if prev is None:
        return value
    return (1.0 - alpha) * prev + alpha * value


# ============================================================
# HYDROGEL: anchor stat-arb + market making
# ============================================================

def hyd_fair_and_state(
    depth: OrderDepth,
    hyd_state: Dict[str, float],
) -> Tuple[float, Dict[str, float], Dict[str, float]]:
    mid = mid_price(depth)
    micro = microprice(depth)

    if mid is None:
        mid = HYD_ANCHOR
    if micro is None:
        micro = mid

    last_mid = float(hyd_state.get("last_mid", mid))
    ret1 = mid - last_mid

    # Keep fair mostly anchored.
    # Micro/fade are small only; anchor is dominant.
    micro_bias = clamp(micro - mid, -1.5, 1.5)
    fade_bias = clamp(-0.25 * ret1, -1.5, 1.5)

    fair = HYD_ANCHOR + 0.20 * micro_bias + 0.35 * fade_bias

    hyd_state["last_mid"] = mid
    hyd_state["last_fair"] = fair

    diagnostics = {
        "mid": mid,
        "micro": micro,
        "ret1": ret1,
        "micro_bias": micro_bias,
        "fade_bias": fade_bias,
    }

    return fair, hyd_state, diagnostics


def trade_hyd(
    depth: OrderDepth,
    position: int,
    hyd_state: Dict[str, float],
    timestamp: int,
) -> Tuple[List[Order], Dict[str, float]]:
    fair, hyd_state, diag = hyd_fair_and_state(depth, hyd_state)

    orders: List[Order] = []

    bid = best_bid(depth)
    ask = best_ask(depth)

    buy_budget = max(0, LIMITS[HYD] - position)
    sell_budget = max(0, LIMITS[HYD] + position)

    temp_pos = position

    # -------------------------
    # 1. Aggressive anchor arb
    # -------------------------
    # Buy if ask is clearly below anchor fair.
    if ask is not None and ask <= fair - HYD_TAKE_EDGE:
        qty = -depth.sell_orders[ask]
        before = buy_budget
        buy_budget = add_buy(
            orders,
            HYD,
            ask,
            min(qty, HYD_SIZE),
            buy_budget,
        )
        temp_pos += before - buy_budget

    # Sell if bid is clearly above anchor fair.
    if bid is not None and bid >= fair + HYD_TAKE_EDGE:
        qty = depth.buy_orders[bid]
        before = sell_budget
        sell_budget = add_sell(
            orders,
            HYD,
            bid,
            min(qty, HYD_SIZE),
            sell_budget,
        )
        temp_pos -= before - sell_budget

    # -------------------------
    # 2. Inventory clearing
    # -------------------------
    # If too long, become more willing to sell.
    if temp_pos > HYD_SOFT_CAP:
        for px in sorted(depth.buy_orders.keys(), reverse=True):
            if px < fair - 1:
                break
            before = sell_budget
            sell_budget = add_sell(
                orders,
                HYD,
                px,
                min(depth.buy_orders[px], HYD_SIZE),
                sell_budget,
            )
            temp_pos -= before - sell_budget
            if temp_pos <= HYD_SOFT_CAP:
                break

    # If too short, become more willing to buy.
    if temp_pos < -HYD_SOFT_CAP:
        for px in sorted(depth.sell_orders.keys()):
            if px > fair + 1:
                break
            before = buy_budget
            buy_budget = add_buy(
                orders,
                HYD,
                px,
                min(-depth.sell_orders[px], HYD_SIZE),
                buy_budget,
            )
            temp_pos += before - buy_budget
            if temp_pos >= -HYD_SOFT_CAP:
                break

    # -------------------------
    # 3. Passive MM around anchor
    # -------------------------
    # Inventory skew:
    # long -> lower ask / reduce bid
    # short -> raise bid / reduce ask
    inv = clamp(temp_pos / LIMITS[HYD], -1.0, 1.0)
    skew = 3.0 * inv

    quote_fair = fair - skew

    bid_px = int(math.floor(quote_fair - HYD_QUOTE_EDGE))
    ask_px = int(math.ceil(quote_fair + HYD_QUOTE_EDGE))

    if bid is not None:
        bid_px = min(bid_px, bid + 1)
    if ask is not None:
        bid_px = min(bid_px, ask - 1)

    if ask is not None:
        ask_px = max(ask_px, ask - 1)
    if bid is not None:
        ask_px = max(ask_px, bid + 1)

    buy_size = HYD_SIZE
    sell_size = HYD_SIZE

    if temp_pos > 80:
        buy_size = max(5, HYD_SIZE // 3)
        sell_size = HYD_SIZE + 20
    elif temp_pos < -80:
        buy_size = HYD_SIZE + 20
        sell_size = max(5, HYD_SIZE // 3)

    if ask is None or bid_px < ask:
        if fair - bid_px >= 1.0:
            buy_budget = add_buy(
                orders,
                HYD,
                bid_px,
                buy_size,
                buy_budget,
            )

    if bid is None or ask_px > bid:
        if ask_px - fair >= 1.0:
            sell_budget = add_sell(
                orders,
                HYD,
                ask_px,
                sell_size,
                sell_budget,
            )

    return orders, hyd_state


# ============================================================
# VFE: small EMA + imbalance market making
# ============================================================

def vfe_fair_and_state(
    depth: OrderDepth,
    vfe_state: Dict[str, float],
) -> Tuple[Optional[float], Dict[str, float], Dict[str, float]]:
    mid = mid_price(depth)
    micro = microprice(depth)

    if mid is None:
        return None, vfe_state, {}

    if micro is None:
        micro = mid

    prev_ema = vfe_state.get("ema")
    fair_ema = ema(float(prev_ema) if prev_ema is not None else None, micro, VFE_EMA_ALPHA)

    imb = imbalance_k2(depth)
    imb_skew = clamp(VFE_IMB_K * imb, -VFE_SKEW_CAP, VFE_SKEW_CAP)

    fair = fair_ema + imb_skew

    vfe_state["ema"] = fair_ema
    vfe_state["last_mid"] = mid
    vfe_state["last_fair"] = fair

    diagnostics = {
        "mid": mid,
        "micro": micro,
        "ema": fair_ema,
        "imbalance": imb,
        "imb_skew": imb_skew,
    }

    return fair, vfe_state, diagnostics


def trade_vfe(
    depth: OrderDepth,
    position: int,
    vfe_state: Dict[str, float],
    timestamp: int,
) -> Tuple[List[Order], Dict[str, float]]:
    fair, vfe_state, diag = vfe_fair_and_state(depth, vfe_state)

    orders: List[Order] = []

    if fair is None:
        return orders, vfe_state

    bid = best_bid(depth)
    ask = best_ask(depth)

    buy_budget = max(0, LIMITS[VFE] - position)
    sell_budget = max(0, LIMITS[VFE] + position)

    temp_pos = position

    # Conservative taker.
    if ask is not None and ask <= fair - VFE_TAKE_EDGE:
        qty = -depth.sell_orders[ask]
        before = buy_budget
        buy_budget = add_buy(
            orders,
            VFE,
            ask,
            min(qty, VFE_SIZE),
            buy_budget,
        )
        temp_pos += before - buy_budget

    if bid is not None and bid >= fair + VFE_TAKE_EDGE:
        qty = depth.buy_orders[bid]
        before = sell_budget
        sell_budget = add_sell(
            orders,
            VFE,
            bid,
            min(qty, VFE_SIZE),
            sell_budget,
        )
        temp_pos -= before - sell_budget

    # Passive quote.
    inv = clamp(temp_pos / LIMITS[VFE], -1.0, 1.0)
    skew = 2.0 * inv

    quote_fair = fair - skew

    bid_px = int(math.floor(quote_fair - VFE_QUOTE_EDGE))
    ask_px = int(math.ceil(quote_fair + VFE_QUOTE_EDGE))

    if bid is not None:
        bid_px = min(bid_px, bid + 1)
    if ask is not None:
        bid_px = min(bid_px, ask - 1)

    if ask is not None:
        ask_px = max(ask_px, ask - 1)
    if bid is not None:
        ask_px = max(ask_px, bid + 1)

    buy_size = VFE_SIZE
    sell_size = VFE_SIZE

    if temp_pos > VFE_SOFT_CAP:
        buy_size = max(2, VFE_SIZE // 4)
        sell_size = VFE_SIZE + 10
    elif temp_pos < -VFE_SOFT_CAP:
        buy_size = VFE_SIZE + 10
        sell_size = max(2, VFE_SIZE // 4)

    if ask is None or bid_px < ask:
        if fair - bid_px >= 1.0:
            buy_budget = add_buy(
                orders,
                VFE,
                bid_px,
                buy_size,
                buy_budget,
            )

    if bid is None or ask_px > bid:
        if ask_px - fair >= 1.0:
            sell_budget = add_sell(
                orders,
                VFE,
                ask_px,
                sell_size,
                sell_budget,
            )

    return orders, vfe_state


class Trader:
    def run(self, state: TradingState):
        raw_state: Dict[str, Dict[str, float]] = {}

        if state.traderData:
            try:
                decoded = json.loads(state.traderData)
                if isinstance(decoded, dict):
                    raw_state = decoded
            except Exception:
                raw_state = {}

        hyd_state = raw_state.get("hyd", {})
        vfe_state = raw_state.get("vfe", {})

        result: Dict[str, List[Order]] = {}

        if HYD in state.order_depths:
            result[HYD], hyd_state = trade_hyd(
                state.order_depths[HYD],
                int(state.position.get(HYD, 0)),
                hyd_state,
                int(state.timestamp),
            )

        if VFE in state.order_depths:
            result[VFE], vfe_state = trade_vfe(
                state.order_depths[VFE],
                int(state.position.get(VFE, 0)),
                vfe_state,
                int(state.timestamp),
            )

        trader_data = json.dumps(
            {
                "hyd": hyd_state,
                "vfe": vfe_state,
            }
        )

        return result, 0, trader_data