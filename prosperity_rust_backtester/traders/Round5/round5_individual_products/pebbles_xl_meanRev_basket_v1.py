import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState


# ============= BEGIN HELPERS FOR PEBBLES_XL (BASKET RESIDUAL) =======================
PEBBLES_XL = "PEBBLES_XL"
PEBBLES_BASKET = ["PEBBLES_XS", "PEBBLES_S", "PEBBLES_M", "PEBBLES_L"]

LIMITS = {
    PEBBLES_XL: 10,
}

LOOKBACK = 200
ENTRY_Z = 1.4
EXIT_Z = 0.35
TAKE_EDGE = 2.0
MAX_TAKE_SIZE = 4
PASSIVE_SIZE = 3


def best_bid(depth: OrderDepth) -> Optional[int]:
    return max(depth.buy_orders) if depth.buy_orders else None


def best_ask(depth: OrderDepth) -> Optional[int]:
    return min(depth.sell_orders) if depth.sell_orders else None


def simple_mid(depth: OrderDepth) -> Optional[float]:
    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return None
    return (bid + ask) / 2.0


def add_buy(orders: List[Order], product: str, price: int, quantity: int, budget: int) -> int:
    size = min(quantity, budget)
    if size > 0:
        orders.append(Order(product, int(price), int(size)))
        budget -= size
    return budget


def add_sell(orders: List[Order], product: str, price: int, quantity: int, budget: int) -> int:
    size = min(quantity, budget)
    if size > 0:
        orders.append(Order(product, int(price), -int(size)))
        budget -= size
    return budget


def trade_pebbles_xl_basket(
    state: TradingState,
    position: int,
    px_state: Dict[str, object],
) -> Tuple[List[Order], Dict[str, object]]:
    orders: List[Order] = []

    if PEBBLES_XL not in state.order_depths:
        return orders, px_state

    depth = state.order_depths[PEBBLES_XL]
    bid = best_bid(depth)
    ask = best_ask(depth)
    xl_mid = simple_mid(depth)
    if bid is None or ask is None or xl_mid is None:
        return orders, px_state

    # Mids for the basket; require all four to be present this tick.
    basket_mids: List[float] = []
    for sym in PEBBLES_BASKET:
        d = state.order_depths.get(sym)
        if d is None:
            return orders, px_state
        m = simple_mid(d)
        if m is None:
            return orders, px_state
        basket_mids.append(m)

    basket_mid = sum(basket_mids) / len(basket_mids)
    # Residual = XL mid minus the equal-weighted basket of the other 4 sizes.
    # Robust to the whole family trending together; fires only on idiosyncratic XL moves.
    resid = xl_mid - basket_mid

    resids = px_state.get("resids", [])
    if not isinstance(resids, list):
        resids = []
    resids.append(float(resid))
    if len(resids) > LOOKBACK:
        resids = resids[-LOOKBACK:]
    px_state["resids"] = resids

    if len(resids) < 50:
        return orders, px_state

    mean = sum(resids) / len(resids)
    var = sum((x - mean) ** 2 for x in resids) / max(1, len(resids) - 1)
    std = math.sqrt(var)
    if std < 1e-9:
        return orders, px_state

    z = (resid - mean) / std
    px_state["last_z"] = z
    px_state["mean"] = mean
    px_state["std"] = std
    px_state["resid"] = resid

    # Fair value for XL mid = basket_mid + mean residual.
    fair = basket_mid + mean

    buy_budget = max(0, LIMITS[PEBBLES_XL] - position)
    sell_budget = max(0, LIMITS[PEBBLES_XL] + position)

    # Aggressive take when residual is stretched.
    if z <= -ENTRY_Z:
        edge = fair - ask
        if edge >= TAKE_EDGE:
            qty = min(-depth.sell_orders[ask], MAX_TAKE_SIZE)
            buy_budget = add_buy(orders, PEBBLES_XL, ask, qty, buy_budget)
    elif z >= ENTRY_Z:
        edge = bid - fair
        if edge >= TAKE_EDGE:
            qty = min(depth.buy_orders[bid], MAX_TAKE_SIZE)
            sell_budget = add_sell(orders, PEBBLES_XL, bid, qty, sell_budget)

    # Inventory exit when residual has reverted toward its mean.
    if position > 0 and z >= -EXIT_Z:
        qty = min(position, depth.buy_orders[bid], MAX_TAKE_SIZE)
        sell_budget = add_sell(orders, PEBBLES_XL, bid, qty, sell_budget)
    if position < 0 and z <= EXIT_Z:
        qty = min(-position, -depth.sell_orders[ask], MAX_TAKE_SIZE)
        buy_budget = add_buy(orders, PEBBLES_XL, ask, qty, buy_budget)

    # Passive quotes inside the spread on the same side as the signal.
    if z <= -ENTRY_Z and buy_budget > 0:
        px = min(bid + 1, ask - 1)
        if px < ask:
            buy_budget = add_buy(
                orders, PEBBLES_XL, px, min(PASSIVE_SIZE, buy_budget), buy_budget
            )
    if z >= ENTRY_Z and sell_budget > 0:
        px = max(ask - 1, bid + 1)
        if px > bid:
            sell_budget = add_sell(
                orders, PEBBLES_XL, px, min(PASSIVE_SIZE, sell_budget), sell_budget
            )

    return orders, px_state

# ============= END HELPERS FOR PEBBLES_XL (BASKET RESIDUAL) =======================


class Trader:
    def run(self, state: TradingState):
        raw_state: Dict[str, Dict[str, object]] = {}
        if state.traderData:
            try:
                decoded = json.loads(state.traderData)
                if isinstance(decoded, dict):
                    raw_state = decoded
            except Exception:
                raw_state = {}

        pebbles_xl_state = raw_state.get("pebbles_xl", {})

        result: Dict[str, List[Order]] = {}
        result[PEBBLES_XL], pebbles_xl_state = trade_pebbles_xl_basket(
            state,
            int(state.position.get(PEBBLES_XL, 0)),
            pebbles_xl_state,
        )

        trader_data = json.dumps({
            "pebbles_xl": pebbles_xl_state,
        })
        return result, 0, trader_data
