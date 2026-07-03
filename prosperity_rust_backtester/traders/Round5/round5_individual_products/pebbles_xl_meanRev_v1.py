import json
import math
from typing import Dict, List, Optional, Tuple

from datamodel import Order, OrderDepth, TradingState

PEBBLES_XL = "PEBBLES_XL"

SNACKPACKS = [
    "SNACKPACK_CHOCOLATE",
    "SNACKPACK_PISTACHIO",
    "SNACKPACK_RASPBERRY",
    "SNACKPACK_STRAWBERRY",
    "SNACKPACK_VANILLA",
]

LIMITS = {
    PEBBLES_XL: 10,
    "SNACKPACK_CHOCOLATE": 10,
    "SNACKPACK_PISTACHIO": 10,
    "SNACKPACK_RASPBERRY": 10,
    "SNACKPACK_STRAWBERRY": 10,
    "SNACKPACK_VANILLA": 10,
}


# ============= BEGIN HELPERS FOR PEBBLES_XL =======================




LOOKBACK = 200
ENTRY_Z = 1.4
EXIT_Z = 0.35
TAKE_EDGE = 2.0
MAX_TAKE_SIZE = 4
PASSIVE_SIZE = 3


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


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


def trade_pebbles_xl(
    depth: OrderDepth,
    position: int,
    px_state: Dict[str, object],
) -> Tuple[List[Order], Dict[str, object]]:
    orders: List[Order] = []

    bid = best_bid(depth)
    ask = best_ask(depth)
    mid = simple_mid(depth)

    if bid is None or ask is None or mid is None:
        return orders, px_state

    # Keep rolling mid history.
    mids = px_state.get("mids", [])
    if not isinstance(mids, list):
        mids = []

    mids.append(float(mid))
    if len(mids) > LOOKBACK:
        mids = mids[-LOOKBACK:]

    px_state["mids"] = mids

    # Need enough history before trading.
    if len(mids) < 50:
        return orders, px_state

    mean = sum(mids) / len(mids)
    var = sum((x - mean) ** 2 for x in mids) / max(1, len(mids) - 1)
    std = math.sqrt(var)

    if std < 1e-9:
        return orders, px_state

    z = (mid - mean) / std
    px_state["last_z"] = z
    px_state["mean"] = mean
    px_state["std"] = std

    buy_budget = max(0, LIMITS[PEBBLES_XL] - position)
    sell_budget = max(0, LIMITS[PEBBLES_XL] + position)

    # Fair value is the rolling mean.
    fair = mean

    # -------------------------
    # 1. Aggressive mean reversion
    # -------------------------
    # If too cheap: buy asks.
    if z <= -ENTRY_Z:
        edge = fair - ask
        if edge >= TAKE_EDGE:
            qty = min(-depth.sell_orders[ask], MAX_TAKE_SIZE)
            buy_budget = add_buy(orders, PEBBLES_XL, ask, qty, buy_budget)

    # If too expensive: sell bids.
    elif z >= ENTRY_Z:
        edge = bid - fair
        if edge >= TAKE_EDGE:
            qty = min(depth.buy_orders[bid], MAX_TAKE_SIZE)
            sell_budget = add_sell(orders, PEBBLES_XL, bid, qty, sell_budget)

    # -------------------------
    # 2. Inventory exit near mean
    # -------------------------
    # If long and z has reverted, sell to flatten.
    if position > 0 and z >= -EXIT_Z:
        qty = min(position, depth.buy_orders[bid], MAX_TAKE_SIZE)
        sell_budget = add_sell(orders, PEBBLES_XL, bid, qty, sell_budget)

    # If short and z has reverted, buy to flatten.
    if position < 0 and z <= EXIT_Z:
        qty = min(-position, -depth.sell_orders[ask], MAX_TAKE_SIZE)
        buy_budget = add_buy(orders, PEBBLES_XL, ask, qty, buy_budget)

    # -------------------------
    # 3. Passive quotes
    # -------------------------
    # If cheap, quote a bid inside the spread.
    if z <= -ENTRY_Z and buy_budget > 0:
        px = min(bid + 1, ask - 1)
        if px < ask:
            buy_budget = add_buy(
                orders,
                PEBBLES_XL,
                px,
                min(PASSIVE_SIZE, buy_budget),
                buy_budget,
            )

    # If expensive, quote an ask inside the spread.
    if z >= ENTRY_Z and sell_budget > 0:
        px = max(ask - 1, bid + 1)
        if px > bid:
            sell_budget = add_sell(
                orders,
                PEBBLES_XL,
                px,
                min(PASSIVE_SIZE, sell_budget),
                sell_budget,
            )

    return orders, px_state

# ============= END HELPERS FOR PEBBLES_XL =======================


# ============== BEGIN HELPERS FOR SNACKPACK MARKET MAKING =====

for s in SNACKPACKS:
    LIMITS[s] = 60

def trade_snackpack_mm(product: str, depth: OrderDepth, position: int) -> List[Order]:
    orders: List[Order] = []

    bid = best_bid(depth)
    ask = best_ask(depth)
    if bid is None or ask is None:
        return orders

    spread = ask - bid
    limit = LIMITS[product]

    buy_budget = max(0, limit - position)
    sell_budget = max(0, limit + position)

    inv_skew = position / limit
    mid = (bid + ask) / 2.0
    fair = mid - inv_skew * 2.0

    # Take obviously good prices, but small size.
    if ask <= fair - 3 and buy_budget > 0:
        qty = min(-depth.sell_orders[ask], buy_budget, 2)
        orders.append(Order(product, ask, qty))
        buy_budget -= qty

    if bid >= fair + 3 and sell_budget > 0:
        qty = min(depth.buy_orders[bid], sell_budget, 2)
        orders.append(Order(product, bid, -qty))
        sell_budget -= qty

    # Passive market making.
    if spread >= 4:
        buy_px = min(int(fair - 1), ask - 1)
        sell_px = max(int(fair + 1), bid + 1)

        if buy_budget > 0 and buy_px < ask:
            qty = min(2, buy_budget)
            orders.append(Order(product, buy_px, qty))
            buy_budget -= qty

        if sell_budget > 0 and sell_px > bid:
            qty = min(2, sell_budget)
            orders.append(Order(product, sell_px, -qty))
            sell_budget -= qty

    return orders

#=================== END HELPERS FOR SNACKPACK MARKET MAKING ===========
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

        if PEBBLES_XL in state.order_depths:
            result[PEBBLES_XL], pebbles_xl_state = trade_pebbles_xl(
                state.order_depths[PEBBLES_XL],
                int(state.position.get(PEBBLES_XL, 0)),
                pebbles_xl_state,
            )

        for product in SNACKPACKS:
            if product in state.order_depths:
                result[product] = trade_snackpack_mm(
                    product,
                    state.order_depths[product],
                    int(state.position.get(product, 0)),
                )

        trader_data = json.dumps({
            "pebbles_xl": pebbles_xl_state,
        })

        return result, 0, trader_data