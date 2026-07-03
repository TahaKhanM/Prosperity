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

VOUCHER_LIMIT = 300
VOUCHER_STRIKES = [5000, 5100, 5200, 5300, 5400]
VOUCHER_MR_SIZE = 1
VOUCHER_MR_EDGE = 1.0
VOUCHER_MR_MAX_SPREAD = 6
VOUCHER_MR_EMA_ALPHA = 0.15

def strike_from_symbol(sym: str) -> Optional[int]:
    if not sym.startswith("VEV_"):
        return None
    try:
        return int(sym[4:])
    except Exception:
        return None
    

def trade_voucher_mean_reversion(
    product: str,
    depth: OrderDepth,
    position: int,
    voucher_state: Dict[str, float],
) -> Tuple[List[Order], Dict[str, float]]:
    orders: List[Order] = []

    bid = best_bid(depth)
    ask = best_ask(depth)
    mid = mid_price(depth)

    if bid is None or ask is None or mid is None:
        return orders, voucher_state

    spread = ask - bid
    if spread > VOUCHER_MR_MAX_SPREAD:
        return orders, voucher_state

    # EMA fair of voucher mid.
    key = product + "_ema"
    prev = voucher_state.get(key)
    fair = ema(float(prev) if prev is not None else None, mid, VOUCHER_MR_EMA_ALPHA)
    voucher_state[key] = fair

    buy_budget = max(0, VOUCHER_LIMIT - position)
    sell_budget = max(0, VOUCHER_LIMIT + position)

    # If voucher is cheap vs its own EMA, buy.
    if mid <= fair - VOUCHER_MR_EDGE:
        qty = min(-depth.sell_orders[ask], VOUCHER_MR_SIZE)
        buy_budget = add_buy(orders, product, ask, qty, buy_budget)

    # If voucher is rich vs its own EMA, sell.
    if mid >= fair + VOUCHER_MR_EDGE:
        qty = min(depth.buy_orders[bid], VOUCHER_MR_SIZE)
        sell_budget = add_sell(orders, product, bid, qty, sell_budget)

    return orders, voucher_state

# =========================
# HYDROGEL main strategy
# =========================

HYD_ANCHOR = 10000.0

# From notebook: best HYD result was anchor edge 8.
HYD_TAKE_EDGE = 6.0
HYD_QUOTE_EDGE = 3.0
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
    orders: List[Order] = []

    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return orders, hyd_state

    mid = (bid + ask) / 2.0
    micro = microprice(depth) or mid
    spread = ask - bid

    last_mid = float(hyd_state.get("last_mid", mid))
    ret1 = mid - last_mid
    hyd_state["last_mid"] = mid

    # Strong anchor, tiny book adjustment.
    micro_bias = clamp(micro - mid, -1.0, 1.0)
    fade_bias = clamp(-0.35 * ret1, -1.5, 1.5)
    fair = HYD_ANCHOR + 0.25 * micro_bias + 0.35 * fade_bias
    hyd_state["last_fair"] = fair

    buy_budget = max(0, LIMITS[HYD] - position)
    sell_budget = max(0, LIMITS[HYD] + position)
    temp_pos = position

    # 1. Take only obvious anchor mispricings.
    # Wider than quote edge because crossing pays spread.
    if ask <= fair - 7.0:
        qty = min(-depth.sell_orders[ask], 30)
        before = buy_budget
        buy_budget = add_buy(orders, HYD, ask, qty, buy_budget)
        temp_pos += before - buy_budget

    if bid >= fair + 7.0:
        qty = min(depth.buy_orders[bid], 30)
        before = sell_budget
        sell_budget = add_sell(orders, HYD, bid, qty, sell_budget)
        temp_pos -= before - sell_budget

    # 2. Passive inside-spread MM.
    inv = clamp(temp_pos / LIMITS[HYD], -1.0, 1.0)

    # If long, move fair down -> more likely to sell.
    # If short, move fair up -> more likely to buy.
    quote_fair = fair - 4.0 * inv

    # Join/improve inside spread.
    if spread >= 10:
        bid_px = bid + 1
        ask_px = ask - 1
    else:
        bid_px = bid
        ask_px = ask

    # Do not quote stupid prices relative to fair.
    # Need at least tiny edge.
    buy_edge = quote_fair - bid_px
    sell_edge = ask_px - quote_fair

    # Avoid quoting both sides when the market is already far from anchor.
    # In those cases only quote the reversion side.
    far_above = mid >= HYD_ANCHOR + 6
    far_below = mid <= HYD_ANCHOR - 6

    base_size = 12

    buy_size = base_size
    sell_size = base_size

    if temp_pos > 80:
        buy_size = 5
        sell_size = 45
    elif temp_pos < -80:
        buy_size = 45
        sell_size = 5

    if temp_pos > 140:
        buy_size = 0
        sell_size = 60
    elif temp_pos < -140:
        buy_size = 60
        sell_size = 0

    # Quote both sides only if they still have positive edge.
    if not far_above and buy_size > 0 and bid_px < ask and buy_edge >= 1.0:
        buy_budget = add_buy(orders, HYD, bid_px, buy_size, buy_budget)

    if not far_below and sell_size > 0 and ask_px > bid and sell_edge >= 1.0:
        sell_budget = add_sell(orders, HYD, ask_px, sell_size, sell_budget)

    # 3. Emergency inventory flattening.
    if temp_pos > 160 and bid >= fair - 2:
        add_sell(orders, HYD, bid, min(depth.buy_orders[bid], 40), sell_budget)

    if temp_pos < -160 and ask <= fair + 2:
        add_buy(orders, HYD, ask, min(-depth.sell_orders[ask], 40), buy_budget)

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
        voucher_state = raw_state.get("voucher", {})

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

        for product, depth in state.order_depths.items():
            k = strike_from_symbol(product)
            if k not in VOUCHER_STRIKES:
                continue

            orders, voucher_state = trade_voucher_mean_reversion(
                product,
                depth,
                int(state.position.get(product, 0)),
                voucher_state,
            )

            if orders:
                result[product] = orders

        trader_data = json.dumps(
            {
                "hyd": hyd_state,
                "vfe": vfe_state,
                "voucher": voucher_state
            }
        )

        return result, 0, trader_data