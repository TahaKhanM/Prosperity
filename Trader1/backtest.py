"""
Lightweight Python backtester for Prosperity 4 tutorial data.
Simulates the matching engine including resting-order fills.

Strategy flow per tick:
  1. Trader sees book, submits orders
  2. Orders that cross existing book are filled immediately (taking)
  3. Remaining orders rest
  4. Resting orders get filled if market trades at that timestamp would
     have crossed them (using trade CSV as a proxy for bot demand)
"""

import csv
import json
import math
import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# ── Minimal datamodel ────────────────────────────────────────────────

class Listing:
    def __init__(self, symbol, product, denomination):
        self.symbol = symbol
        self.product = product
        self.denomination = denomination

class OrderDepth:
    def __init__(self):
        self.buy_orders: Dict[int, int] = {}
        self.sell_orders: Dict[int, int] = {}

class Order:
    def __init__(self, symbol: str, price: int, quantity: int):
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
    def __repr__(self):
        return f"Order({self.symbol}, {self.price}, {self.quantity})"

class Trade:
    def __init__(self, symbol, price, quantity, buyer=None, seller=None, timestamp=0):
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.buyer = buyer
        self.seller = seller
        self.timestamp = timestamp

class Observation:
    def __init__(self):
        self.plainValueObservations = {}
        self.conversionObservations = {}

class TradingState:
    def __init__(self, traderData, timestamp, listings, order_depths,
                 own_trades, market_trades, position, observations):
        self.traderData = traderData
        self.timestamp = timestamp
        self.listings = listings
        self.order_depths = order_depths
        self.own_trades = own_trades
        self.market_trades = market_trades
        self.position = position
        self.observations = observations

# ── CSV parsing ──────────────────────────────────────────────────────

def load_prices(path: str) -> List[dict]:
    with open(path) as f:
        return list(csv.DictReader(f, delimiter=";"))

def load_trades(path: str) -> Dict[int, List[dict]]:
    """Load market trades grouped by timestamp."""
    by_ts: Dict[int, List[dict]] = defaultdict(list)
    with open(path) as f:
        for row in csv.DictReader(f, delimiter=";"):
            ts = int(row["timestamp"])
            by_ts[ts].append(row)
    return by_ts

def build_order_depth(rows_at_ts: List[dict]) -> Dict[str, OrderDepth]:
    depths = {}
    for row in rows_at_ts:
        product = row["product"]
        od = OrderDepth()
        for i in range(1, 4):
            bp, bv = row.get(f"bid_price_{i}", ""), row.get(f"bid_volume_{i}", "")
            if bp and bv and bp.strip() and bv.strip():
                od.buy_orders[int(bp)] = int(bv)
            ap, av = row.get(f"ask_price_{i}", ""), row.get(f"ask_volume_{i}", "")
            if ap and av and ap.strip() and av.strip():
                od.sell_orders[int(ap)] = -int(av)
        depths[product] = od
    return depths

# ── Matching engine ──────────────────────────────────────────────────

LIMITS = {"EMERALDS": 80, "TOMATOES": 80}

def match_taking_orders(
    orders: List[Order],
    depth: OrderDepth,
    position: int,
    product: str,
) -> Tuple[List[Trade], List[Order], int, float]:
    """
    Match trader orders against the book (immediate fills).
    Returns (fills, resting_orders, new_position, realized_pnl).
    """
    limit = LIMITS.get(product, 50)
    fills = []
    resting = []
    pnl = 0.0

    for order in orders:
        remaining_qty = order.quantity

        if remaining_qty > 0:  # buy
            max_buy = limit - position
            if max_buy <= 0:
                continue
            remaining_qty = min(remaining_qty, max_buy)

            for ask_price in sorted(depth.sell_orders.keys()):
                if ask_price > order.price or remaining_qty <= 0:
                    break
                available = -depth.sell_orders[ask_price]
                fill_qty = min(remaining_qty, available)
                if fill_qty > 0:
                    fills.append(Trade(product, ask_price, fill_qty, "SUBMISSION", "", 0))
                    position += fill_qty
                    pnl -= ask_price * fill_qty
                    depth.sell_orders[ask_price] += fill_qty
                    if depth.sell_orders[ask_price] == 0:
                        del depth.sell_orders[ask_price]
                    remaining_qty -= fill_qty

            if remaining_qty > 0:
                resting.append(Order(product, order.price, remaining_qty))

        elif remaining_qty < 0:  # sell
            max_sell = limit + position
            if max_sell <= 0:
                continue
            remaining_qty = max(-max_sell, remaining_qty)

            for bid_price in sorted(depth.buy_orders.keys(), reverse=True):
                if bid_price < order.price or remaining_qty >= 0:
                    break
                available = depth.buy_orders[bid_price]
                fill_qty = min(available, -remaining_qty)
                if fill_qty > 0:
                    fills.append(Trade(product, bid_price, -fill_qty, "", "SUBMISSION", 0))
                    position -= fill_qty
                    pnl += bid_price * fill_qty
                    depth.buy_orders[bid_price] -= fill_qty
                    if depth.buy_orders[bid_price] == 0:
                        del depth.buy_orders[bid_price]
                    remaining_qty += fill_qty

            if remaining_qty < 0:
                resting.append(Order(product, order.price, remaining_qty))

    return fills, resting, position, pnl


def simulate_resting_fills(
    resting_orders: List[Order],
    market_trades_at_ts: List[dict],
    position: int,
    product: str,
) -> Tuple[List[Trade], int, float]:
    """
    Simulate fills on resting orders using market trades as demand proxy.
    If a market buy trade happened at price P, a resting sell at price <= P
    would have been filled. Similarly for sells.
    """
    limit = LIMITS.get(product, 50)
    fills = []
    pnl = 0.0

    # Separate market trades into buy-side and sell-side demand
    buy_demand = []  # bots buying -> fills our resting sells
    sell_demand = []  # bots selling -> fills our resting buys

    for mt in market_trades_at_ts:
        if mt["symbol"] != product:
            continue
        price = float(mt["price"])
        qty = int(mt["quantity"])
        # A trade at the ask side means a buyer crossed -> buy demand
        # A trade at the bid side means a seller crossed -> sell demand
        # We don't always know direction, so use both
        buy_demand.append((price, qty))
        sell_demand.append((price, qty))

    # Fill resting sell orders (bot buying demand)
    resting_sells = sorted(
        [o for o in resting_orders if o.quantity < 0],
        key=lambda o: o.price  # cheapest sell first
    )
    for demand_price, demand_qty in sorted(buy_demand, key=lambda x: -x[0]):
        for order in resting_sells:
            if order.quantity >= 0:
                continue  # already fully filled
            if order.price > demand_price:
                continue
            max_sell = limit + position
            if max_sell <= 0:
                break
            fill_qty = min(-order.quantity, demand_qty, max_sell)
            if fill_qty > 0:
                fills.append(Trade(product, order.price, -fill_qty, "", "SUBMISSION", 0))
                position -= fill_qty
                pnl += order.price * fill_qty
                order.quantity += fill_qty
                demand_qty -= fill_qty

    # Fill resting buy orders (bot selling demand)
    resting_buys = sorted(
        [o for o in resting_orders if o.quantity > 0],
        key=lambda o: -o.price  # highest buy first
    )
    for demand_price, demand_qty in sorted(sell_demand, key=lambda x: x[0]):
        for order in resting_buys:
            if order.quantity <= 0:
                continue
            if order.price < demand_price:
                continue
            max_buy = limit - position
            if max_buy <= 0:
                break
            fill_qty = min(order.quantity, demand_qty, max_buy)
            if fill_qty > 0:
                fills.append(Trade(product, order.price, fill_qty, "SUBMISSION", "", 0))
                position += fill_qty
                pnl -= order.price * fill_qty
                order.quantity -= fill_qty
                demand_qty -= fill_qty

    return fills, position, pnl


# ── Mark-to-market ───────────────────────────────────────────────────

def mark_to_market(position: Dict[str, int], depths: Dict[str, OrderDepth]) -> float:
    mtm = 0.0
    for product, pos in position.items():
        if pos == 0 or product not in depths:
            continue
        od = depths[product]
        bb = max(od.buy_orders) if od.buy_orders else None
        ba = min(od.sell_orders) if od.sell_orders else None
        if bb is not None and ba is not None:
            mid = (bb + ba) / 2
        elif bb is not None:
            mid = bb
        elif ba is not None:
            mid = ba
        else:
            mid = 0
        mtm += pos * mid
    return mtm


# ── Run backtest ─────────────────────────────────────────────────────

def run_backtest(price_files: List[str], trade_files: List[str]):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    import types
    dm = types.ModuleType("datamodel")
    dm.Order = Order
    dm.OrderDepth = OrderDepth
    dm.Trade = Trade
    dm.TradingState = TradingState
    dm.Listing = Listing
    dm.Observation = Observation
    sys.modules["datamodel"] = dm

    from trader import Trader
    trader_instance = Trader()

    position: Dict[str, int] = {}
    cash = 0.0
    trader_data = ""
    own_trades: Dict[str, List[Trade]] = {}

    total_fills = 0
    total_take_fills = 0
    total_rest_fills = 0
    pnl_by_product: Dict[str, float] = {}

    for price_file, trade_file in zip(price_files, trade_files):
        day_label = os.path.basename(price_file)
        print(f"\n{'='*60}")
        print(f"  DAY: {day_label}")
        print(f"{'='*60}")

        price_rows = load_prices(price_file)
        market_trades_by_ts = load_trades(trade_file)

        ts_map: Dict[int, List[dict]] = {}
        for row in price_rows:
            ts = int(row["timestamp"])
            ts_map.setdefault(ts, []).append(row)

        day_fills = 0
        day_take = 0
        day_rest = 0
        day_pnl = 0.0

        for ts in sorted(ts_map.keys()):
            rows = ts_map[ts]
            depths = build_order_depth(rows)

            listings = {}
            for product in depths:
                listings[product] = Listing(product, product, "XIRECS")

            state = TradingState(
                traderData=trader_data,
                timestamp=ts,
                listings=listings,
                order_depths=depths,
                own_trades=own_trades,
                market_trades={},
                position=dict(position),
                observations=Observation(),
            )

            result, conversions, trader_data = trader_instance.run(state)

            # Fresh depth for matching
            depths_for_match = build_order_depth(rows)
            tick_own_trades: Dict[str, List[Trade]] = {}
            mt_at_ts = market_trades_by_ts.get(ts, [])

            for product, orders in result.items():
                if product not in depths_for_match:
                    continue

                # Phase 1: immediate fills (taking)
                take_fills, resting, new_pos, take_pnl = match_taking_orders(
                    orders, depths_for_match[product],
                    position.get(product, 0), product,
                )

                # Phase 2: resting order fills (via market trade proxy)
                rest_fills, new_pos, rest_pnl = simulate_resting_fills(
                    resting, mt_at_ts, new_pos, product,
                )

                position[product] = new_pos
                realized = take_pnl + rest_pnl
                cash += realized
                day_pnl += realized
                day_fills += len(take_fills) + len(rest_fills)
                day_take += len(take_fills)
                day_rest += len(rest_fills)
                total_fills += len(take_fills) + len(rest_fills)
                total_take_fills += len(take_fills)
                total_rest_fills += len(rest_fills)
                pnl_by_product.setdefault(product, 0.0)
                pnl_by_product[product] += realized

                all_fills = take_fills + rest_fills
                if all_fills:
                    tick_own_trades[product] = all_fills

            own_trades = tick_own_trades

        last_ts = max(ts_map.keys())
        final_depths = build_order_depth(ts_map[last_ts])
        mtm = mark_to_market(position, final_depths)

        print(f"  Fills: {day_fills} (take={day_take}, resting={day_rest})")
        print(f"  Position: {dict(position)}")
        print(f"  Cash: {cash:.2f}")
        print(f"  MTM: {mtm:.2f}")
        print(f"  PnL: {cash + mtm:.2f}")

    # Final summary
    print(f"\n{'='*60}")
    print(f"  FINAL SUMMARY")
    print(f"{'='*60}")

    last_rows = load_prices(price_files[-1])
    last_ts = max(int(r["timestamp"]) for r in last_rows)
    last_ts_rows = [r for r in last_rows if int(r["timestamp"]) == last_ts]
    final_depths = build_order_depth(last_ts_rows)
    mtm = mark_to_market(position, final_depths)

    print(f"  Total fills: {total_fills} (take={total_take_fills}, resting={total_rest_fills})")
    print(f"  Final position: {dict(position)}")
    print(f"  Cash: {cash:.2f}")
    print(f"  MTM: {mtm:.2f}")
    print(f"  Total PnL: {cash + mtm:.2f}")

    print("\n  PnL by product (realized + MTM):")
    for product in sorted(pnl_by_product.keys()):
        pos = position.get(product, 0)
        prod_mtm = 0.0
        if product in final_depths and pos != 0:
            od = final_depths[product]
            bb = max(od.buy_orders) if od.buy_orders else 0
            ba = min(od.sell_orders) if od.sell_orders else 0
            mid = (bb + ba) / 2 if bb and ba else 0
            prod_mtm = pos * mid
        total = pnl_by_product[product] + prod_mtm
        print(f"    {product}: realized={pnl_by_product[product]:.2f}, mtm={prod_mtm:.2f}, total={total:.2f}")


if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "TUTORIAL_ROUND_1")

    def day_key(fname):
        base = os.path.basename(fname)
        parts = base.replace(".csv", "").split("_")
        return int(parts[-1])

    price_files = sorted(
        [os.path.join(data_dir, f) for f in os.listdir(data_dir)
         if f.startswith("prices_") and f.endswith(".csv")],
        key=day_key,
    )
    trade_files = sorted(
        [os.path.join(data_dir, f) for f in os.listdir(data_dir)
         if f.startswith("trades_") and f.endswith(".csv")],
        key=day_key,
    )
    run_backtest(price_files, trade_files)
