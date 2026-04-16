import importlib.util
from pathlib import Path
from typing import Dict, List


BASE = (
    Path(__file__).resolve().parents[3]
    / "traders"
    / "Round1"
    / "work"
    / "pepper_carry"
    / "unvalidated"
    / "round1_pepper_dual_carry_v13.py"
)
spec = importlib.util.spec_from_file_location("base_v13", BASE)
base = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(base)


ASH = base.ASH
PEPPER = base.PEPPER
Order = base.Order

clamp = base.clamp
best_bid = base.best_bid
best_ask = base.best_ask
add_buy = base.add_buy
add_sell = base.add_sell
ash_fair_and_state = base.ash_fair_and_state
trade_pepper = base.trade_pepper


def trade_ash(depth, position: int, ash_state: Dict[str, float], timestamp: int):
    fair, ash_state, diag = ash_fair_and_state(depth, ash_state)
    shock = bool(diag["shock"])

    long_cap = 80
    short_cap = 80
    progress = clamp(timestamp / 999900.0, 0.0, 1.0)
    soft_cap = 20 if progress < 0.18 else 12

    take_edge = 1.75 if not shock else 1.25
    clear_edge = 0.5
    skew = clamp(position * 0.04, -2.0, 2.0)

    buy_budget = max(0, min(base.LIMITS[ASH], long_cap) - position)
    sell_budget = max(0, position + min(base.LIMITS[ASH], short_cap))
    temp_position = position
    orders: List[Order] = []

    best_ask_level = best_ask(depth)
    if best_ask_level is not None and best_ask_level <= fair - take_edge:
        before = buy_budget
        buy_budget = add_buy(
            orders,
            ASH,
            best_ask_level,
            -depth.sell_orders[best_ask_level],
            buy_budget,
        )
        temp_position += before - buy_budget

    best_bid_level = best_bid(depth)
    if best_bid_level is not None and best_bid_level >= fair + take_edge:
        before = sell_budget
        sell_budget = add_sell(
            orders,
            ASH,
            best_bid_level,
            depth.buy_orders[best_bid_level],
            sell_budget,
        )
        temp_position -= before - sell_budget

    clear_reference = fair
    if temp_position > soft_cap:
        for bid_price in sorted(depth.buy_orders, reverse=True):
            if bid_price < clear_reference - clear_edge:
                break
            before = sell_budget
            sell_budget = add_sell(
                orders,
                ASH,
                bid_price,
                depth.buy_orders[bid_price],
                sell_budget,
            )
            temp_position -= before - sell_budget
            if temp_position <= soft_cap:
                break
    if temp_position < -soft_cap:
        for ask_price in sorted(depth.sell_orders):
            if ask_price > clear_reference + clear_edge:
                break
            before = buy_budget
            buy_budget = add_buy(
                orders,
                ASH,
                ask_price,
                -depth.sell_orders[ask_price],
                buy_budget,
            )
            temp_position += before - buy_budget
            if temp_position >= -soft_cap:
                break

    bid = best_bid(depth)
    ask = best_ask(depth)
    spread = (ask - bid) if bid is not None and ask is not None else 16
    quote_fair = float(diag.get("quote_fair", fair)) - skew
    prefer_inside_buy = spread >= 15
    prefer_inside_sell = spread >= 15

    disregard_edge = 1.2 if not shock else 1.6
    join_edge = 5.0 if spread >= 18 else 4.0
    default_edge = 3.8 if spread <= 16 else 4.2
    deep_step = 2 if spread <= 16 else 3

    asks_above_fair = [
        price for price in depth.sell_orders if price > quote_fair + disregard_edge
    ]
    bids_below_fair = [
        price for price in depth.buy_orders if price < quote_fair - disregard_edge
    ]

    base_bid = int(base.math.floor(quote_fair - default_edge))
    if bids_below_fair:
        best_bid_below_fair = max(bids_below_fair)
        inside_bid = best_bid_below_fair + 1
        if (
            prefer_inside_buy
            and ask is not None
            and inside_bid < ask
            and fair - inside_bid >= 1.0
        ):
            base_bid = inside_bid
        elif quote_fair - best_bid_below_fair <= join_edge:
            base_bid = best_bid_below_fair
        else:
            base_bid = best_bid_below_fair + 1

    base_ask = int(base.math.ceil(quote_fair + default_edge))
    if asks_above_fair:
        best_ask_above_fair = min(asks_above_fair)
        inside_ask = best_ask_above_fair - 1
        if (
            prefer_inside_sell
            and bid is not None
            and inside_ask > bid
            and inside_ask - fair >= 1.0
        ):
            base_ask = inside_ask
        elif best_ask_above_fair - quote_fair <= join_edge:
            base_ask = best_ask_above_fair
        else:
            base_ask = best_ask_above_fair - 1

    if position > 28:
        base_ask -= 1
    elif position < -28:
        base_bid += 1

    buy_prices = [base_bid, base_bid - deep_step]
    sell_prices = [base_ask, base_ask + deep_step]
    if spread >= 21:
        buy_sizes = [18, 16] if not shock else [13, 12]
        sell_sizes = [18, 16] if not shock else [13, 12]
    elif spread >= 19:
        buy_sizes = [16, 15] if not shock else [12, 11]
        sell_sizes = [16, 15] if not shock else [12, 11]
    elif spread >= 18:
        buy_sizes = [14, 12] if not shock else [11, 9]
        sell_sizes = [14, 12] if not shock else [11, 9]
    else:
        buy_sizes = [12, 8] if not shock else [9, 6]
        sell_sizes = [12, 8] if not shock else [9, 6]

    if prefer_inside_buy:
        buy_sizes[0] += 1

    if not shock and spread >= 18 and abs(position) <= 16:
        buy_sizes[0] += 2
        sell_sizes[0] += 2

    seen = set()
    buy_plan = list(zip(buy_prices, buy_sizes))[:1]
    for idx, (price, size) in enumerate(buy_plan):
        if bid is not None and idx == 0:
            price = min(price, bid + 1)
        if ask is not None and price >= ask:
            price = ask - 1
        if price in seen or (ask is not None and price >= ask) or fair - price < 1.0:
            continue
        seen.add(price)
        buy_budget = add_buy(orders, ASH, price, size, buy_budget)

    seen.clear()
    sell_plan = list(zip(sell_prices, sell_sizes))[:1]
    for idx, (price, size) in enumerate(sell_plan):
        if ask is not None and idx == 0:
            price = max(price, ask - 1)
        if bid is not None and price <= bid:
            price = bid + 1
        if price in seen or (bid is not None and price <= bid) or price - fair < 1.0:
            continue
        seen.add(price)
        sell_budget = add_sell(orders, ASH, price, size, sell_budget)

    return orders, ash_state


class Trader:
    def run(self, state):
        raw_state: Dict[str, Dict[str, float]] = {}
        if state.traderData:
            try:
                decoded = base.json.loads(state.traderData)
                if isinstance(decoded, dict):
                    raw_state = decoded
            except Exception:
                raw_state = {}

        ash_state = raw_state.get("ash", {})
        pepper_state = raw_state.get("pepper", {})

        result: Dict[str, List[Order]] = {}

        if ASH in state.order_depths:
            result[ASH], ash_state = trade_ash(
                state.order_depths[ASH],
                int(state.position.get(ASH, 0)),
                ash_state,
                int(state.timestamp),
            )

        if PEPPER in state.order_depths:
            result[PEPPER], pepper_state = trade_pepper(
                state.order_depths[PEPPER],
                int(state.position.get(PEPPER, 0)),
                pepper_state,
                list(state.market_trades.get(PEPPER, [])),
                int(state.timestamp),
            )

        trader_data = base.json.dumps(
            {
                "ash": ash_state,
                "pepper": pepper_state,
            }
        )
        return result, 0, trader_data
